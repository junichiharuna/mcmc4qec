"""Explicit finite-state contracts; no decoder-output inference."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, Protocol
import hashlib
import json

import numpy as np


def binary(value, *, ndim=None, shape=None, name="array"):
    if hasattr(value, "toarray"):
        value = value.toarray()
    a = np.asarray(value)
    if ndim is not None and a.ndim != ndim:
        raise ValueError(f"{name} must have {ndim} dimensions")
    if shape is not None and a.shape != shape:
        raise ValueError(f"{name} shape {a.shape} != {shape}")
    if not np.all((a == 0) | (a == 1)):
        raise ValueError(f"{name} must be binary")
    return a.astype(np.uint8, copy=True)


def positive_integer(value, name, *, zero=False):
    if isinstance(value, (bool, np.bool_)) or not isinstance(value, (int, np.integer)):
        raise ValueError(f"{name} must be an integer")
    if value < (0 if zero else 1):
        raise ValueError(f"invalid {name}")
    return int(value)


def categorical(value, alphabets, *, name="state"):
    """Validate one finite categorical vector; zero is the identity category."""
    alphabets = np.asarray(alphabets)
    if (alphabets.ndim != 1 or alphabets.dtype.kind not in "iu" or
            np.any(alphabets < 2) or np.any(alphabets > 256)):
        raise ValueError("alphabets must contain integer category counts in [2, 256]")
    a = np.asarray(value)
    if a.shape != alphabets.shape or a.dtype.kind not in "buif":
        raise ValueError(f"{name} must be a categorical vector of shape {alphabets.shape}")
    if not np.all(np.isfinite(a)) or np.any(a != np.floor(a)) or np.any(a < 0) or np.any(a >= alphabets):
        raise ValueError(f"{name} has an invalid category")
    return a.astype(np.uint8, copy=True)


def json_value(value):
    """Copy JSON-compatible metadata, rejecting opaque or nonfinite values."""
    def encode(x):
        if isinstance(x, np.ndarray):
            return x.tolist()
        if isinstance(x, np.generic):
            return x.item()
        raise TypeError(f"metadata is not JSON serializable: {type(x).__name__}")
    return json.loads(json.dumps(value, default=encode, allow_nan=False))


def identified(data):
    data = json_value(data)
    payload = json.dumps(data, sort_keys=True, separators=(",", ":")).encode()
    return {**data, "sha256": hashlib.sha256(payload).hexdigest()}


def gf2_rank(a):
    a = a.copy()
    r = 0
    for c in range(a.shape[1]):
        rows = np.flatnonzero(a[r:, c])
        if not len(rows):
            continue
        j = r + rows[0]
        a[[r, j]] = a[[j, r]]
        for j in range(r + 1, len(a)):
            if a[j, c]:
                a[j] ^= a[r]
        r += 1
        if r == len(a):
            break
    return r


class Model(Protocol):
    """Finite latent-state model supplied to Problem.

    n is the number of coordinates and alphabets lists their category counts.
    validate_state returns a validated array; syndrome and observables return
    decoder input and binary logical truth for one whole experiment.
    metadata returns JSON-compatible identity and settings. Implementations
    should raise ValueError for invalid states; no per-round rate is implied.
    """
    n: int
    alphabets: tuple[int, ...]
    def validate_state(self, state) -> np.ndarray: ...
    def syndrome(self, state) -> np.ndarray: ...
    def observables(self, state) -> np.ndarray: ...
    def metadata(self) -> dict: ...


class Noise(Protocol):
    """Normalized distribution on n coordinates for a Model's state space.

    sample(p, rng) returns one state using the supplied NumPy generator.
    log_prob(state, p) returns its natural log probability, including all
    normalization constants, or -inf outside support. p may be a scalar or an
    explicitly documented parameter object. metadata returns JSON-compatible
    identity and settings. Invalid parameters should raise ValueError.
    """
    n: int
    def sample(self, p, rng: np.random.Generator) -> np.ndarray: ...
    def log_prob(self, state, p) -> float: ...
    def metadata(self) -> dict: ...


class Decoder(Protocol):
    """Deterministic logical prediction contract, independent of output size.

    predict(syndrome) returns a binary vector matching Model.observables;
    physical corrections must first be mapped to logical observables.
    metadata returns JSON-compatible decoder identity and configuration.
    Invalid inputs and decoder failures propagate to the caller.
    """
    def predict(self, syndrome) -> np.ndarray: ...
    def metadata(self) -> dict: ...


class BinaryLinearModel:
    """Map latent bits to syndrome H @ state and observables L @ state mod 2.

    H and L are binary matrices with the same positive number n of columns.
    Optional stabilizers are binary rows preserving both maps; identifier is
    recorded in metadata. Invalid shapes, entries, or stabilizers raise
    ValueError. Arrays are copied and made read-only. Observable mismatch is
    defined for the complete experiment described by the matrices.
    """
    def __init__(self, H, L, *, stabilizers=None, identifier="binary-linear"):
        self.H = binary(H, ndim=2, name="H")
        self.L = binary(L, ndim=2, name="L")
        self.n = self.H.shape[1]
        self.alphabets = (2,) * self.n
        positive_integer(self.n, "n")
        if self.L.shape[1] != self.n:
            raise ValueError("H and L must have the same number of columns")
        self.stabilizers = binary(
            np.zeros((0, self.n), dtype=int) if stabilizers is None else stabilizers,
            ndim=2, name="stabilizers")
        if self.stabilizers.shape[1] != self.n:
            raise ValueError("stabilizers must have n columns")
        if np.any(self.H @ self.stabilizers.T % 2) or np.any(self.L @ self.stabilizers.T % 2):
            raise ValueError("stabilizers must preserve syndrome and logical observables")
        self.identifier = str(identifier)
        for a in (self.H, self.L, self.stabilizers):
            a.flags.writeable = False

    def validate_state(self, state):
        return binary(state, shape=(self.n,), name="state")

    def syndrome(self, state):
        return self.H @ self.validate_state(state) % 2

    def observables(self, state):
        return self.L @ self.validate_state(state) % 2

    def metadata(self):
        return identified(dict(type=type(self).__name__, identifier=self.identifier,
                               H=self.H, L=self.L, stabilizers=self.stabilizers,
                               state_space="binary", n=self.n))


class CSSCode:
    """Validated complete logical bases for a static CSS code.

    The four binary matrices have n columns; lx and lz have k rows. By
    default ``logical_basis='paired'`` requires lx @ lz.T = I over GF(2).
    Explicit ``'independent'`` accepts any nonsingular logical commutation
    matrix, preserving supplied row order without rebasing. In that mode,
    row i of lx need not flip only observable i of lz. Observable coordinates
    remain defined by the supplied matrices in both modes.

    Raises ValueError for invalid matrices, incomplete logical bases, or an
    unknown basis convention. Arrays are copied and made read-only.
    """
    def __init__(self, hx, hz, lx, lz, *, logical_basis="paired"):
        if logical_basis not in ("paired", "independent"):
            raise ValueError("logical_basis must be 'paired' or 'independent'")
        self.logical_basis = logical_basis
        self.hx, self.hz, self.lx, self.lz = [binary(a, ndim=2, name=name)
            for a, name in zip((hx, hz, lx, lz), ("hx", "hz", "lx", "lz"))]
        self.n = self.hx.shape[1]
        positive_integer(self.n, "n")
        if any(a.shape[1] != self.n for a in (self.hz, self.lx, self.lz)):
            raise ValueError("all CSS matrices must have n columns")
        if self.lx.shape != self.lz.shape:
            raise ValueError("lx and lz must be paired")
        if np.any(self.hx @ self.hz.T % 2):
            raise ValueError("CSS stabilizers do not commute")
        if np.any(self.hz @ self.lx.T % 2) or np.any(self.hx @ self.lz.T % 2):
            raise ValueError("logical operators do not commute with stabilizers")
        k = self.n - gf2_rank(self.hx) - gf2_rank(self.hz)
        commutation = self.lx @ self.lz.T % 2
        if len(self.lx) != k or gf2_rank(commutation) != k:
            raise ValueError("lx/lz must be complete independent logical bases")
        if logical_basis == "paired" and not np.array_equal(commutation, np.eye(k, dtype=int)):
            raise ValueError("paired lx/lz must be anticommuting logical pairs")
        for a in (self.hx, self.hz, self.lx, self.lz):
            a.flags.writeable = False

    def bit_flip_model(self):
        return BinaryLinearModel(self.hz, self.lz, stabilizers=self.hx, identifier="css-bit-flip")


class CallableDecoder:
    """Wrap a deterministic function returning *logical observables*.

    function receives a copy of the syndrome and returns a one-dimensional
    binary vector. identifier is a required nonempty provenance label;
    settings is optional JSON-compatible metadata. Invalid arguments or
    predictions raise ValueError; exceptions from the function propagate.
    Physical corrections require DecoderAdapter with an explicit logical map.
    """
    def __init__(self, function: Callable, *, identifier: str, settings=None):
        if not callable(function) or not identifier:
            raise ValueError("a callable and nonempty decoder identifier are required")
        self.function = function
        self.identifier = identifier
        self.settings = json_value({} if settings is None else settings)

    def predict(self, syndrome):
        return binary(self.function(np.array(syndrome, copy=True)), ndim=1, name="prediction")

    def metadata(self):
        return dict(type="CallableDecoder", identifier=self.identifier,
                    settings=self.settings, deterministic=True,
                    version=None, provenance="user-supplied identifier and settings")


class CallableFailure:
    """A deterministic predicate shared by exact, direct MC, and MCMC.

    function(state, predicted, truth) must return a boolean for one complete
    experiment. identifier is required; settings is optional JSON-compatible
    metadata. Invalid arguments or nonboolean answers raise ValueError.
    Stabilizer invariance and invariance under a logical change of basis are
    never inferred for user predicates.
    """
    def __init__(self, function: Callable, *, identifier: str, settings=None):
        if not callable(function) or not identifier:
            raise ValueError("a callable and nonempty failure identifier are required")
        self.function = function
        self.identifier = identifier
        self.settings = json_value({} if settings is None else settings)

    def __call__(self, state, predicted, truth):
        answer = self.function(state, predicted, truth)
        if not isinstance(answer, (bool, np.bool_)):
            raise ValueError("failure predicate must return a boolean")
        return bool(answer)

    def metadata(self):
        return dict(type="CallableFailure", identifier=self.identifier, settings=self.settings)


@dataclass
class Problem:
    """Bind compatible model, normalized noise, decoder, and failure predicate.

    model and noise must share dimension and alphabets. decoder.predict must
    return binary logical observables. Optional failure(state, predicted,
    truth) overrides the default any-observable-mismatch event; each component
    supplies JSON-compatible metadata. Invalid dimensions, model-bound noise,
    states, densities, or decoder outputs raise ValueError. is_faulty returns
    one boolean for the whole experiment, without conversion to a per-round
    event. No invariance of an arbitrary failure predicate is assumed.
    """
    model: Model
    noise: Noise
    decoder: Decoder
    failure: Any = None

    def __post_init__(self):
        positive_integer(self.model.n, "model.n")
        self.alphabets = tuple(getattr(self.model, "alphabets", (2,) * self.model.n))
        categorical(np.zeros(self.model.n, dtype=int), self.alphabets)
        if self.model.n != self.noise.n:
            raise ValueError("model and noise dimensions differ")
        if hasattr(self.noise, "alphabets") and tuple(self.noise.alphabets) != self.alphabets:
            raise ValueError("model and noise categorical state spaces differ")
        bound_model = getattr(self.noise, "model", None)
        if bound_model is not None and json_value(bound_model.metadata()) != json_value(self.model.metadata()):
            raise ValueError("model-bound noise belongs to a different model")
        for component in (self.model, self.noise, self.decoder):
            json_value(component.metadata())
        if self.failure is not None:
            json_value(self.failure.metadata())

    def state(self, state):
        state = categorical(state, self.alphabets)
        return categorical(self.model.validate_state(state), self.alphabets)

    def log_prob(self, state, p):
        lp = float(self.noise.log_prob(self.state(state), p))
        if np.isnan(lp) or lp == np.inf or lp > 1e-12:
            raise ValueError("noise.log_prob must be a normalized log probability or -inf")
        return lp

    def is_faulty(self, state):
        state = self.state(state)
        predicted = binary(self.decoder.predict(self.model.syndrome(state.copy())), ndim=1,
                           name="prediction")
        truth = binary(self.model.observables(state.copy()), ndim=1, name="observables")
        if predicted.shape != truth.shape:
            raise ValueError("decoder prediction and observable dimensions differ")
        if self.failure is None:
            return bool(np.any(predicted != truth))
        answer = self.failure(state.copy(), predicted.copy(), truth.copy())
        if not isinstance(answer, (bool, np.bool_)):
            raise ValueError("failure predicate must return a boolean")
        return bool(answer)

    def metadata(self):
        return json_value(dict(model=self.model.metadata(), noise=self.noise.metadata(),
            decoder=self.decoder.metadata(), failure=(self.failure.metadata() if self.failure
                is not None else dict(identifier="logical-observable-mismatch-v1"))))
