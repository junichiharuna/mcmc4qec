"""Stim DEM mechanisms remain independent bits, including correlated ^ pieces.

This is a DEM distribution, not an assertion that arbitrary physical categorical
faults are independent Bernoulli variables. Optional imports happen on use.
"""
from importlib.metadata import version
import numpy as np
from .core import BinaryLinearModel, binary, identified
from .adapters import PyMatchingAdapter


class StimDemModel(BinaryLinearModel):
    def __init__(self, dem, *, identifier="stim-dem"):
        import stim
        if not isinstance(dem, stim.DetectorErrorModel):
            raise TypeError("dem must be a stim.DetectorErrorModel")
        errors = [item for item in dem.flattened() if item.type == "error"]
        if not errors:
            raise ValueError("DEM must contain at least one error mechanism")
        H = np.zeros((dem.num_detectors, len(errors)), dtype=np.uint8)
        L = np.zeros((dem.num_observables, len(errors)), dtype=np.uint8)
        probabilities, signatures, components = [], [], []
        for i, instruction in enumerate(errors):
            probabilities.append(instruction.args_copy()[0])
            targets = instruction.targets_copy()
            signatures.append(tuple(str(t) for t in targets))
            pieces, piece = [], []
            for target in targets:
                if target.is_separator():
                    pieces.append(tuple(piece))
                    piece = []
                elif target.is_relative_detector_id():
                    H[target.val, i] ^= 1
                    piece.append(target.val)
                elif target.is_logical_observable_id():
                    L[target.val, i] ^= 1
                else:
                    raise ValueError("unsupported DEM target")
            pieces.append(tuple(piece))
            components.append(tuple(pieces))
        super().__init__(H, L, identifier=identifier)
        self.base_probabilities = np.asarray(probabilities, dtype=float)
        self.base_probabilities.flags.writeable = False
        self.error_signatures = tuple(signatures)
        self.decomposition_detector_components = tuple(components)
        self.dem_text = str(dem)
        self.stim_version = version("stim")

    def metadata(self):
        data = super().metadata()
        data.pop("sha256")
        return identified({**data, "type": "StimDemModel", "dem_text": self.dem_text,
            "error_signatures": self.error_signatures, "stim_version": self.stim_version,
            "conversion": getattr(self, "conversion", None),
            "separator_semantics": "correlated pieces of one latent mechanism"})


class StimDemNoise:
    def __init__(self, model, *, probabilities=None, dem_factory=None, family_identifier=None):
        if probabilities is not None and dem_factory is not None:
            raise ValueError("choose probabilities or dem_factory, not both")
        for fn in (probabilities, dem_factory):
            if fn is not None and (not callable(fn) or not family_identifier):
                raise ValueError("a callable probability family requires family_identifier")
        self.model = model
        self.n = model.n
        self.alphabets = (2,) * self.n
        self._probabilities = probabilities
        self.dem_factory = dem_factory
        self.family_identifier = family_identifier

    def probabilities(self, p):
        if self.dem_factory is not None:
            other = StimDemModel(self.dem_factory(p))
            if (self.model.error_signatures != other.error_signatures or
                    not np.array_equal(self.model.H, other.H) or
                    not np.array_equal(self.model.L, other.L)):
                raise ValueError("DEM family changed mechanism identity, order, or H/L")
            probabilities = other.base_probabilities
        elif self._probabilities is not None:
            probabilities = self._probabilities(p)
        else:
            if p is not None:
                raise ValueError("fixed DEM requires p=None; supply an explicit probability family")
            probabilities = self.model.base_probabilities
        probabilities = np.asarray(probabilities, dtype=float)
        if (probabilities.shape != (self.n,) or not np.all(np.isfinite(probabilities)) or
                np.any(probabilities < 0) or np.any(probabilities > 1)):
            raise ValueError("DEM probabilities must be finite values in [0, 1], one per mechanism")
        return probabilities.copy()

    def sample(self, p, rng):
        return (rng.random(self.n) < self.probabilities(p)).astype(np.uint8)

    def log_prob(self, state, p):
        state = binary(state, shape=(self.n,), name="state")
        probabilities = self.probabilities(p)
        selected = np.where(state, probabilities, 1-probabilities)
        return -np.inf if np.any(selected == 0) else float(np.log(selected).sum())

    def metadata(self):
        return identified(dict(type="StimDemNoise", model_sha256=self.model.metadata()["sha256"],
            distribution="independent Bernoulli DEM mechanisms", normalized=True,
            family_identifier=self.family_identifier,
            family_mode="dem_factory" if self.dem_factory is not None else (
                "probabilities" if self._probabilities is not None else "fixed"),
            physical_circuit_equivalence="not inferred"))


def from_stim_dem(dem, *, probabilities=None, dem_factory=None,
                  identifier="stim-dem", family_identifier=None):
    """Return (model, noise) for a Stim DetectorErrorModel distribution.

    Each error instruction is one Bernoulli mechanism; separator pieces stay
    correlated. With no callback, sampling requires p=None. Either
    probabilities(p) supplies one probability per mechanism, or dem_factory(p)
    supplies a DEM with unchanged mechanism ordering and H/L maps. A callback
    requires family_identifier; identifier labels the model. Conflicting
    callbacks, missing identity, empty DEMs, and invalid families raise
    ValueError; a wrong DEM type raises TypeError. Stim is optional on import.
    Failure rates describe the complete DEM experiment; physical-circuit
    equivalence or per-round conversion is not inferred.
    """
    model = StimDemModel(dem, identifier=identifier)
    return model, StimDemNoise(model, probabilities=probabilities, dem_factory=dem_factory,
                              family_identifier=family_identifier)


def from_stim_circuit(circuit, *, decompose_errors=False,
                     approximate_disjoint_errors=False, identifier="circuit-dem"):
    """Explicit conversion controls, recorded in model provenance.

    circuit is a stim.Circuit; return (model, noise) for its fixed DEM using
    p=None in sampling. decompose_errors and approximate_disjoint_errors are
    passed to Stim, and identifier labels the resulting model. Stim conversion
    errors propagate; invalid or empty DEMs are rejected by from_stim_dem.
    Default conversion fails if disjoint errors need an approximation. Choosing
    that approximation is an explicit caller decision, never an automatic retry.
    The resulting failure rate concerns the complete DEM experiment, with no
    automatic interpretation as a physical circuit rate or a per-round rate.
    """
    dem = circuit.detector_error_model(decompose_errors=decompose_errors,
                                       approximate_disjoint_errors=approximate_disjoint_errors)
    model, noise = from_stim_dem(dem, identifier=identifier)
    # Store conversion provenance separately from the immutable DEM map.
    model.conversion = dict(decompose_errors=decompose_errors,
                            approximate_disjoint_errors=approximate_disjoint_errors)
    return model, noise


def matching_from_dem(dem, *, enable_correlations=False, identifier="dem-matching"):
    """Return a PyMatchingAdapter predicting the DEM's logical observables.

    dem is a stim.DetectorErrorModel. enable_correlations is used consistently
    when building and decoding; identifier is retained in provenance. Each
    decomposition piece must be graphlike, otherwise ValueError is raised
    instead of silently dropping a hyperedge. Stim and PyMatching are required
    on use; their construction and decoding errors propagate. The output is
    a logical prediction vector, not a probability or a physical correction.
    """
    import pymatching
    model = StimDemModel(dem)
    for mechanism in model.decomposition_detector_components:
        for component in mechanism:
            odd = {d for d in component if component.count(d) % 2}
            if len(odd) > 2:
                raise ValueError("undecomposed DEM hyperedge would be lost by matching")
    matching = pymatching.Matching.from_detector_error_model(
        dem, enable_correlations=enable_correlations)
    matching.ensure_num_fault_ids(dem.num_observables)
    return PyMatchingAdapter(matching, output_kind="observable", identifier=identifier,
        built_with_correlations=enable_correlations,
        settings=dict(dem_sha256=model.metadata()["sha256"], dem=str(dem)))
