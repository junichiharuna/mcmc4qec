import itertools
import numpy as np
import pytest

stim = pytest.importorskip("stim")
from mcmc4qec.stim_dem import from_stim_dem, matching_from_dem, from_stim_circuit


def test_separator_preserves_one_latent_mechanism_and_stim_replay():
    dem = stim.DetectorErrorModel("""
        error(0.1) D0 L0 ^ D1
        repeat 2 {
            error(0.2) D0
            shift_detectors 1
        }
    """)
    model, noise = from_stim_dem(dem)
    assert model.n == 3  # NOT four independent decomposition fragments.
    latent = np.array(list(itertools.product((0, 1), repeat=3)), dtype=bool)
    detectors, observables, replayed = dem.compile_sampler(seed=12).sample(
        shots=len(latent), return_errors=True, recorded_errors_to_replay=latent)
    assert np.array_equal(replayed, latent)
    assert np.array_equal(detectors, latent @ model.H.T % 2)
    assert np.array_equal(observables, latent @ model.L.T % 2)
    assert sum(np.exp(noise.log_prob(s, None)) for s in latent) == pytest.approx(1)
    det, obs, err = dem.compile_sampler(seed=13).sample(shots=5000, return_errors=True)
    assert np.array_equal(det, err @ model.H.T % 2)
    assert np.array_equal(obs, err @ model.L.T % 2)
    assert np.allclose(err.mean(axis=0), noise.probabilities(None), atol=.03)


def test_dem_family_keeps_order_maps_and_mechanism_identity():
    factory = lambda p: stim.DetectorErrorModel(f"error({p}) D0 L0 ^ D1\nerror({p/2}) D1")
    model, noise = from_stim_dem(factory(.1), dem_factory=factory, family_identifier="two-mechanism")
    assert noise.probabilities(.2) == pytest.approx([.2, .1])
    assert model.n == 2
    changed = lambda p: stim.DetectorErrorModel(f"error({p}) D1\nerror({p/2}) D0 L0 ^ D1")
    _, bad = from_stim_dem(factory(.1), dem_factory=changed, family_identifier="reordered")
    with pytest.raises(ValueError, match="identity"):
        bad.probabilities(.2)


def test_single_dem_has_no_implicit_p_parameterization():
    _, noise = from_stim_dem(stim.DetectorErrorModel("error(0.1) D0 L0"))
    with pytest.raises(ValueError, match="fixed DEM"):
        noise.probabilities(.2)
    assert noise.metadata()["distribution"] == "independent Bernoulli DEM mechanisms"


def test_matching_dem_rejects_undecomposed_hyperedge_and_correlations_agree():
    pytest.importorskip("pymatching")
    with pytest.raises(ValueError, match="hyperedge"):
        matching_from_dem(stim.DetectorErrorModel("error(0.1) D0 D1 D2 L0"))
    dem = stim.DetectorErrorModel("error(0.1) D0 D1 ^ D2 L0")
    adapter = matching_from_dem(dem, enable_correlations=True)
    assert adapter.metadata()["built_with_correlations"] is True
    assert adapter.metadata()["decode_kwargs"]["enable_correlations"] is True
    assert np.array_equal(adapter.predict([1, 1, 1]), [1])


def test_circuit_conversion_never_enables_disjoint_approximation_implicitly():
    class CircuitSpy:
        def detector_error_model(self, **kwargs):
            self.kwargs = kwargs
            return stim.DetectorErrorModel("error(0.1) D0 L0")
    circuit = CircuitSpy()
    from_stim_circuit(circuit)
    assert circuit.kwargs["approximate_disjoint_errors"] is False


def test_dem_probability_callable_is_explicit_and_validated():
    dem = stim.DetectorErrorModel("error(0.1) D0 L0")
    with pytest.raises(ValueError):
        from_stim_dem(dem, probabilities=lambda p: [p])
    _, noise = from_stim_dem(dem, probabilities=lambda p: [p], family_identifier="linear")
    assert noise.log_prob([1], 0) == -np.inf
    assert noise.log_prob([1], 1) == 0
    with pytest.raises(ValueError):
        noise.probabilities(2)
