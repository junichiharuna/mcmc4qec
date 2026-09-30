"""Short local step-rate comparison with read-only research RIMC imports."""
import argparse
import cProfile
import io
import os
from pathlib import Path
import pstats
import sys
import time

os.environ["PYTHONDONTWRITEBYTECODE"] = "1"
sys.dont_write_bytecode = True

import numpy as np
import pymatching

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
RESEARCH = Path("C:/dev/RIMC/src")
sys.path.insert(0, str(RESEARCH))

from css_code import make_toric_code as research_toric, make_bb_code_72 as research_bb
from css_code import make_mwpm_decoder as research_mwpm
from css_code import make_bposd_decoder as research_bposd
from runners import run_rimc_mixed

from mcmc4qec.core import BinaryLinearModel, Problem
from mcmc4qec.noise import IndependentBitFlip
from mcmc4qec.adapters import PyMatchingAdapter, DecoderAdapter
from mcmc4qec.sampling import KernelConfig, SamplingConfig, sample_faulty


def case(name):
    reference = research_bb() if name == "bb72" else research_toric(int(name[1:]))
    model = BinaryLinearModel(reference.hz, reference.lz,
        stabilizers=reference.hx, identifier="research-matrix-benchmark")
    if name == "bb72":
        from ldpc import BpOsdDecoder
        engine = BpOsdDecoder(reference.hz, error_rate=.01, max_iter=100,
            bp_method="min_sum", osd_method="osd_cs", osd_order=10)
        decoder = DecoderAdapter(engine, output_kind="correction",
            identifier="benchmark-bposd", logical_map=reference.lz)
    else:
        matching = pymatching.Matching(reference.hz)
        matching.ensure_num_fault_ids(reference.n)
        decoder = PyMatchingAdapter(matching, output_kind="correction", identifier="benchmark-mwpm",
            logical_map=reference.lz, built_with_correlations=False)
    return reference, Problem(model, IndependentBitFlip(reference.n), decoder)


def benchmark(name, steps, *, profile=False):
    reference, problem = case(name)
    p = .01
    research_decoder = research_bposd(reference, p) if name == "bb72" else research_mwpm(reference)
    config = SamplingConfig(samples=steps, burn_in=0,
        kernels=KernelConfig(zanella=.7, cluster=.3, cluster_k=2, lazy=0),
        cache_cap=None, cache_policy="research_clear")
    started = time.perf_counter()
    ours = sample_faulty(problem, p, config=config,
        initial_state=code_initial(reference), seed=731)
    ours_elapsed = time.perf_counter() - started
    started = time.perf_counter()
    run_rimc_mixed(p, steps, code=reference, decoder=research_decoder,
        p_zanella=.7, p_cluster=.3, cluster_k=2, n_replicas=1,
        steps_per_swap=10, seed=731, cache_cap=None)
    research_elapsed = time.perf_counter() - started
    print(f"{name}\t{steps}\t{ours_elapsed:.6f}\t{research_elapsed:.6f}"
          f"\t{steps / ours_elapsed:.1f}\t{steps / research_elapsed:.1f}"
          f"\t{ours_elapsed / research_elapsed:.2f}")
    if profile:
        profiler = cProfile.Profile()
        profiler.enable()
        sample_faulty(problem, p, config=config,
            initial_state=code_initial(reference), seed=731)
        profiler.disable()
        stream = io.StringIO()
        pstats.Stats(profiler, stream=stream).sort_stats("cumtime").print_stats(18)
        print(stream.getvalue())
    return ours


def code_initial(code):
    return np.asarray(code.lx[0], dtype=np.uint8)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--steps", type=int, default=300)
    parser.add_argument("--profile", action="store_true")
    args = parser.parse_args()
    if args.steps <= 0 or args.steps % 10:
        parser.error("--steps must be a positive multiple of ten")
    print("case\tsteps\tlibrary_s\tresearch_s\tlibrary_steps_s\tresearch_steps_s\ttime_ratio")
    for name in ("d5", "d7", "bb72"):
        benchmark(name, args.steps, profile=args.profile)
