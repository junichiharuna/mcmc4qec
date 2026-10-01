"""Measure conditional Z/H step rates for toric d5/d7 and BB72.

Requires the codes, matching, and bposd extras. --quick uses 100 steps and
usually finishes within seconds; the default 10,000-step comparison usually
finishes within a minute on a desktop CPU. --seed, --repeats, and --out control
the runs and CSV destination. Set RIMC_RESEARCH_ROOT for read-only research
runner comparisons; without it, the script measures only this library.
Step speed does not establish mixing, convergence, or estimation accuracy.
"""
import argparse
import cProfile
import csv
import io
import os
from pathlib import Path
import pstats
import sys
import tempfile
import time

os.environ["PYTHONDONTWRITEBYTECODE"] = "1"
sys.dont_write_bytecode = True

import numpy as np
import pymatching

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from mcmc4qec.core import BinaryLinearModel, Problem
from mcmc4qec.noise import IndependentBitFlip
from mcmc4qec.adapters import PyMatchingAdapter, DecoderAdapter
from mcmc4qec.sampling import KernelConfig, SamplingConfig, sample_faulty


def research_modules(root):
    """Import research modules only when a checkout was explicitly supplied."""
    if root is None:
        return None
    source = root / "src"
    if not source.is_dir():
        raise ValueError(f"research source directory not found: {source}")
    sys.path.insert(0, str(source))
    from css_code import make_toric_code, make_bb_code_72
    from css_code import make_mwpm_decoder, make_bposd_decoder
    from runners import run_rimc_mixed
    return (make_toric_code, make_bb_code_72, make_mwpm_decoder,
            make_bposd_decoder, run_rimc_mixed)


def case(name, research=None):
    if research is None:
        from mcmc4qec.codes import make_toric_code, make_bb_code_72
    else:
        make_toric_code, make_bb_code_72 = research[:2]
    code = make_bb_code_72() if name == "bb72" else make_toric_code(int(name[1:]))
    model = BinaryLinearModel(code.hz, code.lz,
        stabilizers=code.hx, identifier="research-matrix-benchmark")
    if name == "bb72":
        from ldpc import BpOsdDecoder
        engine = BpOsdDecoder(code.hz, error_rate=.01, max_iter=100,
            bp_method="min_sum", osd_method="osd_cs", osd_order=10)
        decoder = DecoderAdapter(engine, output_kind="correction",
            identifier="benchmark-bposd", logical_map=code.lz)
    else:
        matching = pymatching.Matching(code.hz)
        matching.ensure_num_fault_ids(code.n)
        decoder = PyMatchingAdapter(matching, output_kind="correction",
            identifier="benchmark-mwpm", logical_map=code.lz,
            built_with_correlations=False)
    return code, Problem(model, IndependentBitFlip(code.n), decoder)


def benchmark(name, steps, *, seed=731, profile=False, research=None):
    code, problem = case(name, research)
    p = .01
    config = SamplingConfig(samples=steps, burn_in=0,
        kernels=KernelConfig(zanella=.7, cluster=.3, cluster_k=2, lazy=0),
        cache_cap=None, cache_policy="research_clear")
    initial = np.asarray(code.lx[0], dtype=np.uint8)
    started = time.perf_counter()
    sample_faulty(problem, p, config=config, initial_state=initial, seed=seed)
    library_seconds = time.perf_counter() - started
    research_seconds = None
    if research is not None:
        research_decoder = (research[3](code, p) if name == "bb72"
                            else research[2](code))
        started = time.perf_counter()
        research[4](p, steps, code=code, decoder=research_decoder,
            p_zanella=.7, p_cluster=.3, cluster_k=2, n_replicas=1,
            steps_per_swap=10, seed=seed, cache_cap=None)
        research_seconds = time.perf_counter() - started
    if profile:
        profiler = cProfile.Profile()
        profiler.enable()
        sample_faulty(problem, p, config=config, initial_state=initial, seed=seed)
        profiler.disable()
        stream = io.StringIO()
        pstats.Stats(profiler, stream=stream).sort_stats("cumtime").print_stats(20)
        print(f"PROFILE {name}\n{stream.getvalue()}")
    return {
        "case": name, "seed": seed, "steps": steps,
        "library_s": library_seconds, "research_s": research_seconds,
        "library_steps_s": steps / library_seconds,
        "research_steps_s": None if research_seconds is None else steps / research_seconds,
        "time_ratio": None if research_seconds is None else library_seconds / research_seconds,
    }


def output_directory(argument):
    output = (Path(argument) if argument is not None else
              Path(tempfile.gettempdir()) / "mcmc4qec" / "bench_step").resolve()
    for variable in ("RIMC_RESEARCH_ROOT", "MCMC4QEC_RESEARCH", "RESEARCH_ROOT"):
        protected = os.environ.get(variable)
        if protected and output.is_relative_to(Path(protected).resolve()):
            raise ValueError(f"--out must not be inside the research checkout ({variable})")
    output.mkdir(parents=True, exist_ok=True)
    return output


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--quick", action="store_true", help="use 100 steps by default")
    parser.add_argument("--seed", type=int, default=731)
    parser.add_argument("--out", type=Path)
    parser.add_argument("--steps", type=int)
    parser.add_argument("--repeats", type=int, default=1)
    parser.add_argument("--profile", action="store_true")
    args = parser.parse_args()
    steps = args.steps if args.steps is not None else (100 if args.quick else 10000)
    if steps <= 0 or steps % 10:
        parser.error("--steps must be a positive multiple of ten")
    if args.repeats <= 0:
        parser.error("--repeats must be positive")
    try:
        output = output_directory(args.out)
        research_root = os.environ.get("MCMC4QEC_RESEARCH") or os.environ.get("RIMC_RESEARCH_ROOT")
        research = research_modules(Path(research_root).resolve() if research_root else None)
    except ValueError as exc:
        parser.error(str(exc))
    path = output / "results.csv"
    fields = ("case", "repeat", "seed", "steps", "library_s", "research_s",
              "library_steps_s", "research_steps_s", "time_ratio")
    with path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields)
        writer.writeheader()
        for repeat in range(args.repeats):
            for name in ("d5", "d7", "bb72"):
                result = benchmark(name, steps, seed=args.seed,
                    profile=args.profile and repeat == 0, research=research)
                result["repeat"] = repeat + 1
                writer.writerow(result)
                print("\t".join(str(result[field]) for field in fields))
    print(f"CSV {path}")


if __name__ == "__main__":
    main()
