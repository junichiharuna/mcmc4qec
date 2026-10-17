"""Open-boundary weight-six tile code with a fixed BP-OSD decoder.

Requires the bposd extra. This is a static bit-flip example, not a syndrome
extraction circuit or a verification of the published distance lower bound.
"""
import argparse
import json
from pathlib import Path
import tempfile

from mcmc4qec import (make_tile_code, bposd_decoder, Problem, IndependentBitFlip,
                     SamplingConfig, sample_faulty, direct_mc, spawn_seeds)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--quick", action="store_true")
    parser.add_argument("--seed", type=int, default=20261017)
    parser.add_argument("--out", type=Path, default=Path(tempfile.gettempdir())/"mcmc4qec"/"tile_bposd")
    args = parser.parse_args()
    code = make_tile_code(6, 6)
    decoder = bposd_decoder(code, .03, max_iter=100, osd_order=2)
    problem = Problem(code.bit_flip_model(), IndependentBitFlip(code.n), decoder)
    mc_seed, chain_seed = spawn_seeds(args.seed, 2)
    mc = direct_mc(problem, .03, trials=100 if args.quick else 2000, seed=mc_seed)
    chain = sample_faulty(problem, .03, config=SamplingConfig(samples=64 if args.quick else 1000,
                          burn_in=16 if args.quick else 200, cache_cap=200000, cache_policy="lru"),
                          initial_state=code.lx[0], seed=chain_seed, diagnostics=True)
    args.out.mkdir(parents=True, exist_ok=True)
    (args.out/"conditional.json").write_text(chain.to_json()+"\n", encoding="utf-8")
    (args.out/"direct_mc.json").write_text(mc.to_json()+"\n", encoding="utf-8")
    summary = dict(code="tile72", n=code.n, k=len(code.lx), p=.03,
                   pl=mc.estimate, pl_interval=mc.interval, conditional_weight=chain.conditional_weight)
    (args.out/"summary.json").write_text(json.dumps(summary, indent=2)+"\n", encoding="utf-8")
    print("Conditional samples are not absolute logical error rates. Diagnostics do not certify mixing.")
    print("SUMMARY " + json.dumps(summary))


if __name__ == "__main__":
    main()
