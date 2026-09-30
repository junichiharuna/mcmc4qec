"""Named results with strict, portable JSON and explicit provenance."""
from dataclasses import asdict, dataclass, field
import json
import platform
from pathlib import Path
import hashlib
import numpy as np
from .core import json_value

VERSION = "0.1.0.dev1"
REFERENCE_COMMIT = "69efcfcc86af3bf24ca977a098dab0f348601aff"


@dataclass
class Result:
    """Sampling or exact-enumeration result with provenance and uncertainty.

    kind identifies the method; metadata records model, parameters and config;
    elapsed_seconds is wall time. estimate/log_estimate are the whole
    experiment's failure probability/natural logarithm. interval is a 95%
    fixed-trial Wilson interval for direct MC, not a per-round rate.
    trials/failures count independent MC trials; conditional_weight is the
    mean number of nonidentity coordinates conditional on failure.
    states has shape (chains, saved samples, coordinates) for MCMC, including
    repeated states. acceptance, diagnostics and warnings describe the run.
    Unavailable optional quantities are None. to_json rejects nonfinite or
    opaque metadata; from_json rejects unsupported schemas or invalid states
    with ValueError. Neither method reconstructs executable user callables.
    """
    kind: str
    metadata: dict
    elapsed_seconds: float
    estimate: float | None = None
    log_estimate: float | None = None
    interval: tuple[float, float] | None = None
    trials: int | None = None
    failures: int | None = None
    conditional_weight: float | None = None
    states: np.ndarray | None = None
    acceptance: dict = field(default_factory=dict)
    diagnostics: dict = field(default_factory=dict)
    warnings: list[str] = field(default_factory=list)

    def to_json(self, *, indent=2):
        data = asdict(self)
        data["schema_version"] = 1
        if self.states is not None:
            data["states"] = dict(values=self.states.tolist(), dtype=str(self.states.dtype),
                                  shape=list(self.states.shape))
        return json.dumps(json_value(data), indent=indent, allow_nan=False)

    @classmethod
    def from_json(cls, payload):
        data = json.loads(payload)
        if data.pop("schema_version", None) != 1:
            raise ValueError("unsupported result schema")
        if data.get("states") is not None:
            descriptor = data["states"]
            if descriptor["dtype"] != "uint8":
                raise ValueError("unsupported state dtype")
            values = np.asarray(descriptor["values"])
            # dev0 results used an implicitly binary state space.
            alphabets = np.asarray(data["metadata"].get("state_space", {}).get(
                "alphabets", [2] * descriptor["shape"][-1]))
            from .core import categorical
            categorical(np.zeros(alphabets.size, dtype=int), alphabets, name="serialized alphabets")
            if (values.ndim != 3 or values.shape != tuple(descriptor["shape"]) or
                    values.shape[-1] != len(alphabets) or values.dtype.kind not in "buif" or
                    not np.all(np.isfinite(values)) or np.any(values != np.floor(values)) or
                    np.any(values < 0) or np.any(values >= alphabets)):
                raise ValueError("invalid serialized categorical states")
            data["states"] = values.astype(np.uint8)
        if data.get("interval") is not None:
            data["interval"] = tuple(data["interval"])
        json_value({k: v for k, v in data.items() if k != "states"})
        return cls(**data)


def metadata(problem, p, config, seed_sequence=None, children=()):
    fingerprint = hashlib.sha256()
    package_root = Path(__file__).parent
    for source in sorted(package_root.rglob("*.py")):
        fingerprint.update(source.relative_to(package_root).as_posix().encode())
        fingerprint.update(b"\0")
        fingerprint.update(source.read_bytes())
    return json_value({**problem.metadata(), "sampling_p": p, "config": config,
        "state_space": {"alphabets": problem.alphabets, "identity_category": 0},
        "library_version": VERSION, "python_version": platform.python_version(),
        "numpy_version": np.__version__, "source_commit": None,
        "source_commit_reason": "commit is not embedded in this package; use package_source_sha256",
        "research_reference_commit": REFERENCE_COMMIT,
        "package_source_sha256": fingerprint.hexdigest(),
        "decoder_prior": problem.decoder.metadata().get("settings", {}).get("decoder_prior"),
        "rng": None if seed_sequence is None else dict(
            bit_generator="PCG64", entropy=seed_sequence.entropy,
            spawn_key=seed_sequence.spawn_key,
            child_spawn_keys=[c.spawn_key for c in children]),
        "assumptions": ["normalized noise on a fixed finite categorical state space",
                        "deterministic decoder and failure predicate"]})
