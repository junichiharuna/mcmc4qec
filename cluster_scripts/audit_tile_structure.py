"""Finite matrix evidence for tile parameters and stabilizer-generated fibers."""
import argparse
import json
from pathlib import Path

import numpy as np
from mcmc4qec.core import gf2_rank

import calibration as c
import tile_study as t


def binary_components(states,noise):
    states=np.asarray(states,dtype=np.uint8)
    if noise=="bit":
        return states.copy()
    if noise!="depolarizing":
        raise ValueError("unsupported noise")
    return np.concatenate(((states==1)|(states==2),(states==2)|(states==3)),axis=1).astype(np.uint8)


def audit_case(size,noise,prior):
    code,problem=t.build_problem(size,noise,prior)
    eye=np.eye(code.n,dtype=np.uint8)
    basis=eye if noise=="bit" else np.concatenate((eye,3*eye))
    h=np.array([problem.model.syndrome(row) for row in basis],dtype=np.uint8).T
    logical=np.array([problem.model.observables(row) for row in basis],dtype=np.uint8).T
    stabilizers=binary_components(problem.model.stabilizers,noise)
    rank_s=gf2_rank(stabilizers)
    joint_rank=gf2_rank(np.vstack((h,logical)))
    invariant=not np.any(h@stabilizers.T%2) and not np.any(logical@stabilizers.T%2)
    spans=invariant and rank_s==len(basis)-joint_rank
    zero_prediction=np.asarray(problem.decoder.predict(np.zeros(h.shape[0],dtype=np.uint8)))
    if not spans or np.any(zero_prediction):
        raise ValueError("tile structure/fixed-decoder baseline differs from study assumptions")
    arrays=dict(hx=code.hx,hz=code.hz,lx=code.lx,lz=code.lz,
                syndrome_map=h,logical_map=logical,stabilizer_binary=stabilizers)
    record=dict(size=size,noise=noise,physical_decoder_prior=prior,n=code.n,k=len(code.lx),
                input_binary_dimension=len(basis),rank_hx=gf2_rank(code.hx),rank_hz=gf2_rank(code.hz),
                rank_stabilizers=rank_s,rank_joint_map=joint_rank,nullity_joint_map=len(basis)-joint_rank,
                stabilizers_preserve_maps=invariant,same_map_fiber_generated_by_stabilizers=spans,
                zero_syndrome_prediction_is_zero=not bool(np.any(zero_prediction)),
                paired_logical_basis=bool(np.array_equal(code.lx@code.lz.T%2,np.eye(len(code.lx)))),
                logical_basis_weights_x=code.lx.sum(axis=1).tolist(),logical_basis_weights_z=code.lz.sum(axis=1).tolist(),
                check_row_weights_x=sorted(set(code.hx.sum(axis=1).tolist())),check_row_weights_z=sorted(set(code.hz.sum(axis=1).tolist())),
                max_check_column_weight_x=int(code.hx.sum(axis=0).max()),max_check_column_weight_z=int(code.hz.sum(axis=0).max()),
                problem_hash=c.digest(problem.metadata()),decoder=problem.decoder.metadata(),
                full_failure_support_connectivity="not established",
                independent_distance_certification="not performed for tile72/tile288",
                warning="Fiber connectivity assumes the built-in linear CSS maps, standard residual-logical failure, a fixed deterministic syndrome-only decoder, positive product-noise support, and a positive stabilizer mixture. It does not prove full failure-support connectivity, backend determinism for all inputs, mixing time or interval coverage.")
    return record,arrays


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out",type=Path,required=True)
    args=parser.parse_args()
    args.out.mkdir(parents=True,exist_ok=False)
    context=dict(source_sha256=c.file_hash(__file__),runtime=t.runtime())
    records=[]
    for case,(size,noise) in enumerate(t.CASES):
        record,arrays=audit_case(size,noise,.03 if size==6 else .05)
        c.save_artifact(args.out/f"case-{case}",dict(context=context,case=case),arrays,record)
        records.append(record)
    c.atomic_json(args.out/"summary.json",dict(context=context,records=records))
    print(json.dumps([dict(n=row["n"],noise=row["noise"],rank_stabilizers=row["rank_stabilizers"],
                           nullity_joint_map=row["nullity_joint_map"]) for row in records]))


if __name__=="__main__":
    main()
