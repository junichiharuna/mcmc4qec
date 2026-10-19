"""Small API/consistency probe for decoder selection, not an LER benchmark.

Use 19 fixed bit-flip errors per code: zero, two single errors, eight draws at
p=.03 and eight at p=.1. Repeat decoding, reverse call order, and reconstruct
the decoder. Record syndrome consistency separately from logical mismatch.
Neither these sample counts nor elapsed times rank accuracy or throughput.
"""
import argparse
import hashlib
from importlib.metadata import version
import json
from pathlib import Path
import platform
import sys
import time

import ldpc
import numpy as np
import mcmc4qec as qec


def constructors(checks):
    common=dict(error_rate=.03,max_iter=100,bp_method="minimum_sum",
                ms_scaling_factor=1.,schedule="parallel",omp_thread_count=1)
    yield "bp",ldpc.BpDecoder,dict(common,input_vector_type="syndrome"),{}
    yield "bp_osd0",ldpc.BpOsdDecoder,dict(common,osd_method="osd_0",osd_order=0),{}
    yield "bp_lsd0",ldpc.BpLsdDecoder,dict(common,lsd_method="lsd_0",lsd_order=0,bits_per_step=1),{}
    yield "belief_find_inversion",ldpc.BeliefFindDecoder,dict(common,uf_method="inversion",bits_per_step=1),{}
    # ldpc 2.4.1's Cython annotation requires str, then assigns to a C++ bool.
    # These are explicit compatibility probes, not recommended public options.
    yield "uf_inversion_compat_string",ldpc.UnionFindDecoder,dict(uf_method="inversion"),dict(bits_per_step=1)
    if np.max(checks.sum(axis=0))<=2:
        yield "uf_peeling_compat_string",ldpc.UnionFindDecoder,dict(uf_method=""),dict(bits_per_step=1)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output",type=Path,required=True)
    args=parser.parse_args()
    args.output.mkdir(parents=True,exist_ok=False)
    factories=[("toric3",lambda:qec.make_toric_code(3)),("surface3",lambda:qec.make_surface_code(3)),
               ("steane",qec.make_steane_code),("hgp_hamming",qec.make_hgp_hamming),
               ("bb72",qec.make_bb_code_72),("tile72",lambda:qec.make_tile_code(6,6)),
               ("tile288",lambda:qec.make_tile_code(12,12))]
    records=[]
    for index,(name,factory) in enumerate(factories):
        code=factory();checks=code.hz
        seed=2026101800+index
        rng=np.random.default_rng(seed)
        errors=np.zeros((19,code.n),dtype=np.uint8)
        errors[1,0]=1;errors[2,-1]=1
        errors[3:11]=(rng.random((8,code.n))<.03)
        errors[11:]=(rng.random((8,code.n))<.1)
        syndromes=(errors@checks.T)%2
        np.savez_compressed(args.output/f"{name}-inputs.npz",errors=errors,syndromes=syndromes,hz=checks,lz=code.lz)
        degree,counts=np.unique(checks.sum(axis=0),return_counts=True)
        for label,cls,settings,decode_kw in constructors(checks):
            started=time.perf_counter()
            record=dict(code=name,n=code.n,k=len(code.lx),checks=len(checks),seed=seed,samples=len(errors),
                        column_degree_counts={str(int(d)):int(n) for d,n in zip(degree,counts)},
                        decoder=label,settings=settings,decode_kwargs=decode_kw,status="ok")
            try:
                decoder=cls(checks,**settings)
                def decode_all(obj,sequence):
                    return np.array([obj.decode(s.copy(),**decode_kw).copy() for s in sequence])
                base=decode_all(decoder,syndromes)
                repeated=decode_all(decoder,syndromes)
                reverse=decode_all(decoder,syndromes[::-1])[::-1]
                fresh=decode_all(cls(checks,**settings),syndromes)
                if base.shape!=errors.shape or not np.all((base==0)|(base==1)):
                    raise ValueError("invalid correction shape or alphabet")
                invalid=np.any((base@checks.T)%2!=syndromes,axis=1)
                logical=np.any(((errors^base.astype(np.uint8))@code.lz.T)%2!=0,axis=1)
                record.update(syndrome_mismatches=int(invalid.sum()),logical_mismatches=int(logical.sum()),
                    syndrome_or_logical_failures=int((invalid|logical).sum()),
                    invalid_corrections_missed_by_logical_only=int((invalid&~logical).sum()),
                    repeated_correction_mismatches=int(np.any(base!=repeated,axis=1).sum()),
                    reversed_correction_mismatches=int(np.any(base!=reverse,axis=1).sum()),
                    fresh_correction_mismatches=int(np.any(base!=fresh,axis=1).sum()))
                np.savez_compressed(args.output/f"{name}-{label}.npz",corrections=base,repeated=repeated,reverse=reverse,fresh=fresh)
            except Exception as error:
                record.update(status="error",error=repr(error))
            record["probe_wall_seconds"]=time.perf_counter()-started
            records.append(record)
    artifacts={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in args.output.glob("*.npz")}
    native={}
    for cls in (ldpc.BpDecoder,ldpc.BpOsdDecoder,ldpc.BpLsdDecoder,ldpc.BeliefFindDecoder,ldpc.UnionFindDecoder):
        path=Path(sys.modules[cls.__module__].__file__)
        native[cls.__name__]=dict(file=path.name,sha256=hashlib.sha256(path.read_bytes()).hexdigest())
    result=dict(schema=1,purpose="decoder_api_consistency_survey",python=sys.version,platform=platform.platform(),native=native,
                packages={name:version(name) for name in ("ldpc","numpy","bposd","pymatching")},
                source_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),records=records,artifact_sha256=artifacts,
                warning="19 fixed mixed-purpose errors per code, bit-flip X sector only. Local reproducibility probes, not a proof of determinism, cross-platform agreement, logical error rates or performance ranking. Standalone UF uses a version-specific string workaround for the ldpc 2.4.1 Cython bool/str mismatch; this is not a supported library factory.")
    (args.output/"summary.json").write_text(json.dumps(result,indent=2)+"\n",encoding="utf-8")
    print(json.dumps(dict(records=len(records),errors=sum(r["status"]!="ok" for r in records),
                         summary=str(args.output/"summary.json"))))


if __name__=="__main__":main()
