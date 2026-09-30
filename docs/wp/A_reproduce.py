"""Reproduce WP-A numerical comparisons without changing the RIMC checkout.

Run with the Python 3.11 interpreter from the repository root, for example:
    python docs/wp/A_reproduce.py exact --research-root C:/dev/RIMC
    python docs/wp/A_reproduce.py direct --code bb72
    python docs/wp/A_reproduce.py zh --code toric5
    python docs/wp/A_reproduce.py decoders --research-root C:/dev/RIMC

The exact/direct/Z+H cases are intentionally outside the normal pytest suite.
Use --output outside the research checkout to retain the full Result JSON.
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import math
import os
from pathlib import Path
import sys

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

import numpy as np

from mcmc4qec.codes import make_bb_code_72, make_toric_code
from mcmc4qec.core import Problem
from mcmc4qec.decoders import (
    bposd_decoder, depolarizing_bposd_decoder, depolarizing_mwpm_decoder,
    mwpm_decoder,
)
from mcmc4qec.estimation import bennett_log_ratio
from mcmc4qec.noise import IndependentBitFlip
from mcmc4qec.sampling import KernelConfig, SamplingConfig, direct_mc, exact, sample_faulty


def _research_module(root: Path, relative: str, name: str):
    source = root / relative
    if not source.is_file():
        raise FileNotFoundError(source)
    spec = importlib.util.spec_from_file_location(name, source)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def _problem(name: str):
    if name == "toric5":
        code = make_toric_code(5)
        decoder = mwpm_decoder(code)
    elif name == "bb72":
        code = make_bb_code_72()
        decoder = bposd_decoder(code, 0.01)
    else:
        raise ValueError(f"unknown code: {name}")
    return code, Problem(code.bit_flip_model(), IndependentBitFlip(code.n), decoder)


def _syndromes(checks):
    found = {tuple(np.zeros(checks.shape[0], dtype=np.uint8))}
    for column in checks.T:
        found |= {tuple(np.asarray(s, dtype=np.uint8) ^ column) for s in found}
    return [np.asarray(s, dtype=np.uint8) for s in sorted(found)]


def _decoders(root: Path):
    research = _research_module(root, "src/css_code.py", "research_css_code_wp_a_reproduce")
    code = make_toric_code(3)
    reference_code = research.make_toric_code(3)
    syndromes = _syndromes(code.hz)
    factories = (
        ("mwpm", mwpm_decoder(code), research.make_mwpm_decoder(reference_code)),
        ("bposd", bposd_decoder(code, 0.05), research.make_bposd_decoder(reference_code, 0.05)),
        ("depolarizing_mwpm", depolarizing_mwpm_decoder(code),
         research.make_depolarizing_mwpm_decoder(reference_code)),
        ("depolarizing_bposd", depolarizing_bposd_decoder(code, 0.05),
         research.make_depolarizing_bposd_decoder(reference_code, 0.05)),
    )
    mismatches = {}
    for name, decoder, reference in factories:
        count = 0
        for syndrome in syndromes:
            if name.startswith("depolarizing_"):
                predicted = decoder.predict(np.concatenate((syndrome, syndrome)))
                expected = np.concatenate((
                    code.lz @ reference.decode_x(syndrome) % 2,
                    code.lx @ reference.decode_z(syndrome) % 2,
                ))
            else:
                predicted = decoder.predict(syndrome)
                expected = code.lz @ reference.decode_syndrome(syndrome) % 2
            count += int(not np.array_equal(predicted, expected))
        mismatches[name] = count
    return dict(syndromes=len(syndromes), mismatches=mismatches)


def _bar():
    broader = np.array([1, 2, 2, 3, 4, 1, 2, 3])
    rarer = np.array([1, 1, 2, 2, 2, 3, 1, 2])

    def delta(weights):
        return weights * math.log(0.05 / 0.1) + (5 - weights) * math.log(0.95 / 0.9)

    return dict(log_ratio=bennett_log_ratio(delta(broader), delta(rarer)),
                research_log_ratio=-1.2130084485394683)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("case", choices=("exact", "direct", "zh", "decoders", "bar"))
    parser.add_argument("--code", choices=("toric5", "bb72"), default="toric5")
    parser.add_argument("--research-root", type=Path,
                        default=Path(os.environ["RIMC_RESEARCH_ROOT"]) if "RIMC_RESEARCH_ROOT" in os.environ else None)
    parser.add_argument("--output", type=Path, help="write the full library Result JSON")
    parser.add_argument("--smoke", action="store_true", help="short direct/Z+H wiring check, not the recorded estimate")
    args = parser.parse_args()
    root = None if args.research_root is None else args.research_root.resolve()
    if args.output is not None and root is not None and args.output.resolve().is_relative_to(root):
        parser.error("--output must be outside the read-only research checkout")
    if args.case in ("exact", "decoders") and root is None:
        parser.error("--research-root or RIMC_RESEARCH_ROOT is required")

    result = None
    if args.case == "decoders":
        summary = _decoders(root)
    elif args.case == "bar":
        summary = _bar()
    elif args.case == "exact":
        code = make_toric_code(3)
        problem = Problem(code.bit_flip_model(), IndependentBitFlip(code.n), mwpm_decoder(code))
        result = exact(problem, 0.01)
        reference = _research_module(root, "compare/exact_ew.py", "research_exact_ew_wp_a_reproduce")
        ref_ew, _, ref_pl = reference.exact_ew_d3(0.01)
        summary = dict(case="exact", code="toric3", p=0.01, library_p_l=result.estimate,
                       library_ew=result.conditional_weight, research_p_l=ref_pl,
                       research_ew=ref_ew, elapsed_seconds=result.elapsed_seconds)
    elif args.case == "direct":
        code, problem = _problem(args.code)
        trials = 64 if args.smoke else 100000
        result = direct_mc(problem, 0.01, trials=trials, seed=20260930)
        summary = dict(case="direct", code=args.code, p=0.01, seed=20260930,
                       trials=trials, failures=result.failures, p_l=result.estimate,
                       wilson95=result.interval, ew=result.conditional_weight,
                       elapsed_seconds=result.elapsed_seconds, smoke=args.smoke)
    else:
        code, problem = _problem(args.code)
        initial_index = 0 if args.code == "toric5" else int(np.argmin(code.lx.sum(axis=1)))
        config = SamplingConfig(samples=16 if args.smoke else 3000,
                                burn_in=4 if args.smoke else 500,
                                kernels=KernelConfig(zanella=0.7, cluster=0.3, cluster_k=2))
        result = sample_faulty(problem, 0.01, config=config, seed=20260930,
                               initial_state=code.lx[initial_index])
        weights = np.count_nonzero(result.states, axis=-1).ravel()
        ess = result.diagnostics["ess"]
        se = None if ess is None else float(weights.std(ddof=1) / math.sqrt(ess))
        interval = None if se is None else [float(weights.mean() - 1.96*se),
                                            float(weights.mean() + 1.96*se)]
        summary = dict(case="zh", code=args.code, p=0.01, seed=20260930,
                       samples=config.samples, burn_in=config.burn_in, thin=config.thin,
                       chains=config.chains, kernels=config.kernels.__dict__,
                       initial_lx_row=initial_index, ew=float(weights.mean()),
                       ess=ess, heuristic95=interval,
                       elapsed_seconds=result.elapsed_seconds, smoke=args.smoke)
    if args.output is not None:
        if result is None:
            parser.error("--output is available only for exact, direct, or zh")
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(result.to_json(), encoding="utf-8")
        summary["result_json"] = str(args.output.resolve())
    print(json.dumps(summary, ensure_ascii=False, sort_keys=True))


if __name__ == "__main__":
    main()
