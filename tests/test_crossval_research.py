"""Fixed matrix fingerprints independently generated from RIMC/src/css_code.py.

The fixture records matrix shapes and raw bytes, retaining research row order.
RIMC arrays are int8 and mcmc4qec arrays are uint8; binary element bytes match.
"""
import hashlib
import importlib.util
import math
import os
from pathlib import Path
import sys

import numpy as np

import pytest

from mcmc4qec import codes


def _fingerprint(code):
    payload = b"".join(
        str(getattr(code, name).shape).encode("ascii") + getattr(code, name).tobytes()
        for name in ("hx", "hz", "lx", "lz")
    )
    return hashlib.sha256(payload).hexdigest()


@pytest.mark.parametrize("factory,expected", [
    (lambda: codes.make_toric_code(2), "bd8b591e864907a99e82e7705af8ccabbf0f6e596657451183b0004a6a9328ac"),
    (lambda: codes.make_toric_code(3), "bc54927b2b14a89a5f34167d6ce0a09dd318ce25482e0a339fc834739128da77"),
    (lambda: codes.make_toric_code(5), "e40d656805f71789bbe5bfcb20f3a9847720c96d9f4c35a7c73f83ddc2eb4f69"),
    (lambda: codes.make_surface_code(2), "08708bfdc7ffa6c6537cdbe8f0191f3616fd552aa061c429bbcbb255f24abe4d"),
    (lambda: codes.make_surface_code(3), "f53441180a1b5fca84b93d04e1e6b6d5c7733716d49a2c98c82a06948ab0b5d1"),
    (lambda: codes.make_asymmetric_toric_code(3, 5), "ec34745b31b5ec4cbb689c4d89e4151bb6374c5890dc9b176a3e5e93957c2d67"),
    (codes.make_hgp_hamming, "1fe2f6f185e30fecb3a8aa1945856be056dedbabfa2b33d6d3791924c4d60d00"),
    (codes.make_bb_code_72, "8023f746dbce8344f4d7135c3dea63ac8dbaeec44d415b07983c650e7ef22835"),
    (codes.make_bb_code_108, "65916c07fcbbb10f223e524360b6b2b1922a991b36d8589f71b0fa4ffe2586f2"),
    (codes.make_bb_code_144, "c76d406fc93afc5ec4057a4f6a3a6413f823e6083802d3d075aeac2b464316a5"),
    (codes.make_steane_code, "a76054125138a0af2a30fdaed69499bd6ac3fd8f0617f09a00610d590bc5dc05"),
    (lambda: codes.make_concatenated_steane_code(2), "4a3000c07cb4769666f648923e074cfdf97ce9a54cae522556fe3ebae6085afa"),
])
def test_research_matrix_bytes(factory, expected):
    if expected in {
        "bd8b591e864907a99e82e7705af8ccabbf0f6e596657451183b0004a6a9328ac",
        "bc54927b2b14a89a5f34167d6ce0a09dd318ce25482e0a339fc834739128da77",
        "e40d656805f71789bbe5bfcb20f3a9847720c96d9f4c35a7c73f83ddc2eb4f69",
        "08708bfdc7ffa6c6537cdbe8f0191f3616fd552aa061c429bbcbb255f24abe4d",
        "f53441180a1b5fca84b93d04e1e6b6d5c7733716d49a2c98c82a06948ab0b5d1",
        "ec34745b31b5ec4cbb689c4d89e4151bb6374c5890dc9b176a3e5e93957c2d67",
        "1fe2f6f185e30fecb3a8aa1945856be056dedbabfa2b33d6d3791924c4d60d00",
    }:
        pytest.importorskip("bposd")
        pytest.importorskip("ldpc")
    assert _fingerprint(factory()) == expected


def test_research_bar_value_on_identical_synthetic_weight_traces():
    from mcmc4qec.estimation import bennett_log_ratio

    # RIMC splitting_pl.estimate_pl_ladder_bar, pymbar 4.0.3, n=5,
    # p=(0.1, 0.05), these exact forward/reverse traces: log ratio below.
    broader = np.array([1, 2, 2, 3, 4, 1, 2, 3])
    rarer = np.array([1, 1, 2, 2, 2, 3, 1, 2])
    def log_ratio(weights):
        return (weights * math.log(0.05 / 0.1)
                + (5 - weights) * math.log(0.95 / 0.9))
    assert bennett_log_ratio(log_ratio(broader), log_ratio(rarer)) == pytest.approx(
        -1.2130084485394683, abs=1e-10)


@pytest.mark.parametrize("kind", ["mwpm", "bposd", "depolarizing_mwpm", "depolarizing_bposd"])
def test_live_research_decoder_all_toric_d3_syndromes(kind):
    """Optional live comparison; set RIMC_RESEARCH_ROOT to the read-only checkout."""
    root_value = os.environ.get("RIMC_RESEARCH_ROOT")
    if not root_value:
        pytest.skip("set RIMC_RESEARCH_ROOT for live research comparison")
    source = Path(root_value).resolve() / "src" / "css_code.py"
    if not source.is_file():
        pytest.fail(f"research source does not exist: {source}")
    pytest.importorskip("bposd")
    pytest.importorskip("ldpc")
    if "mwpm" in kind:
        pytest.importorskip("pymatching")

    # Import and invoke with bytecode writes disabled, including lazy imports
    # inside the research decoder factories. The research checkout is read-only.
    original = sys.dont_write_bytecode
    sys.dont_write_bytecode = True
    try:
        spec = importlib.util.spec_from_file_location("research_css_code_wp_a", source)
        research = importlib.util.module_from_spec(spec)
        sys.modules[spec.name] = research
        spec.loader.exec_module(research)
        from mcmc4qec.codes import make_toric_code
        from mcmc4qec.decoders import (
            mwpm_decoder, bposd_decoder, depolarizing_mwpm_decoder,
            depolarizing_bposd_decoder,
        )

        code = make_toric_code(3)
        reference_code = research.make_toric_code(3)
        for name in ("hx", "hz", "lx", "lz"):
            assert getattr(code, name).tobytes() == getattr(reference_code, name).tobytes()
        if kind == "mwpm":
            decoder = mwpm_decoder(code)
            reference = research.make_mwpm_decoder(reference_code)
        elif kind == "bposd":
            decoder = bposd_decoder(code, 0.05)
            reference = research.make_bposd_decoder(reference_code, 0.05)
        elif kind == "depolarizing_mwpm":
            decoder = depolarizing_mwpm_decoder(code)
            reference = research.make_depolarizing_mwpm_decoder(reference_code)
        else:
            decoder = depolarizing_bposd_decoder(code, 0.05)
            reference = research.make_depolarizing_bposd_decoder(reference_code, 0.05)

        syndromes = {tuple(np.zeros(len(code.hz), dtype=np.uint8))}
        for column in code.hz.T:
            syndromes |= {tuple(np.asarray(s, dtype=np.uint8) ^ column) for s in syndromes}
        assert len(syndromes) == 256
        for bits in syndromes:
            syndrome = np.asarray(bits, dtype=np.uint8)
            if kind.startswith("depolarizing_"):
                predicted = decoder.predict(np.concatenate((syndrome, syndrome)))
                expected = np.concatenate((
                    code.lz @ reference.decode_x(syndrome) % 2,
                    code.lx @ reference.decode_z(syndrome) % 2,
                ))
            else:
                predicted = decoder.predict(syndrome)
                expected = code.lz @ reference.decode_syndrome(syndrome) % 2
            assert np.array_equal(predicted, expected)
    finally:
        sys.modules.pop("research_css_code_wp_a", None)
        sys.dont_write_bytecode = original
