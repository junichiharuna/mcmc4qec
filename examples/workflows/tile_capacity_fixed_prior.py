"""Tile code-capacity BAR with a target-fixed BP-OSD decoder and independent MC.

Requires mcmc4qec[bposd]. Both budgets are workflow demonstrations, not validated
precision settings. P_any is failure of any logical observable, not P_any/k.
Depolarizing noise preserves the joint I/X/Y/Z law; sector decoding is a decoder
approximation. Changing the physical target rebuilds the decoder, whereas every
rung of one ladder shares exactly the same decoder object and failure event.
"""
import argparse
import csv
import json
from pathlib import Path
import tempfile

import numpy as np
import mcmc4qec as qec


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--quick",action="store_true")
    parser.add_argument("--seed",type=int,default=20261017)
    parser.add_argument("--out",type=Path,default=Path(tempfile.gettempdir())/"mcmc4qec/tile_capacity_fixed_prior")
    parser.add_argument("--size",type=int,choices=[6,12],default=6)
    parser.add_argument("--noise",choices=["bit","depolarizing"],default="bit")
    parser.add_argument("--initialization",choices=["rejection","logical"],default="rejection")
    parser.add_argument("--kernel",choices=["ZH","ZHS"],default="ZH")
    parser.add_argument("--uncertainty",choices=["block_bootstrap","cross_chain"],default="block_bootstrap")
    args=parser.parse_args()
    out=args.out.expanduser().resolve()
    out.mkdir(parents=True,exist_ok=True)
    print(f"Output: {out}")
    code=qec.make_tile_code(args.size,args.size)
    target=.03 if args.size==6 else .05
    ladder=[.1,.07,.05,.03] if args.size==6 else [.1,.085,.07,.06,.05]
    settings=dict(max_iter=100,bp_method="min_sum",ms_scaling_factor=1.,schedule="parallel",osd_method="osd_cs",osd_order=10)
    prior=target if args.noise=="bit" else 2*target/3
    if args.noise=="bit":
        decoder=qec.bposd_decoder(code,prior,**settings)
        problem=qec.Problem(code.bit_flip_model(),qec.IndependentBitFlip(code.n),decoder)
        starts=code.lx[:4]
    else:
        decoder=qec.depolarizing_bposd_decoder(code,prior,**settings)
        problem=qec.Problem(qec.DepolarizingModel(code),qec.DepolarizingNoise(code.n),decoder)
        starts=np.stack([code.lx[0],3*code.lz[0],code.lx[1],3*code.lz[1]])
    kernels=qec.KernelConfig() if args.kernel=="ZH" else qec.KernelConfig(zanella=.6,cluster=.3,stabilizer=.1)
    config=qec.SamplingConfig(samples=64 if args.quick else 512,burn_in=32 if args.quick else 256,
                              chains=4,kernels=kernels,cache_cap=200000,cache_policy="lru")
    anchor_seed,bar_seed,check_seed=qec.spawn_seeds(args.seed,3)
    anchor=qec.direct_mc(problem,ladder[0],trials=1024 if args.quick else 8192,seed=anchor_seed)
    check=qec.direct_mc(problem,target,trials=512 if args.quick else 4096,seed=check_seed)
    initial_states=None if args.initialization=="rejection" else [starts.copy() for _ in ladder]
    result=qec.estimate_logical_error(problem,ladder,anchor=anchor,config=config,seed=bar_seed,
        mode="fixed_failure",initial_states=initial_states,uncertainty=args.uncertainty,
        bootstrap_replicates=32 if args.quick else 200,bootstrap_block_length=8 if args.quick else 32,
        diagnostics=qec.DiagnosticsConfig(max_lag=32,block_sizes=(8,32),bootstrap_replicates=0))
    for name,value in (("anchor",anchor),("independent_mc",check),("bar",result)):
        (out/f"{name}.json").write_text(value.to_json()+"\n",encoding="utf-8")
    row=dict(code=f"tile{code.n}",noise=args.noise,target_p=target,sector_decoder_prior=prior,
             kernel=args.kernel,initialization=args.initialization,bar=result.estimates[-1],
             bar_interval=result.intervals[-1],independent_mc=check.estimate,mc_interval=check.interval,
             mc_trials=check.trials,mc_failures=check.failures,uncertainty=args.uncertainty,
             purpose="workflow demonstration; precision settings not yet validated")
    with (out/"comparison.csv").open("w",encoding="utf-8",newline="") as stream:
        writer=csv.DictWriter(stream,fieldnames=list(row))
        writer.writeheader()
        writer.writerow(row)
    (out/"summary.json").write_text(json.dumps(row,indent=2)+"\n",encoding="utf-8")
    print("Short traces and interval agreement do not certify mixing or nominal coverage.")
    print("SUMMARY "+json.dumps(row))


if __name__=="__main__":
    main()
