"""Reproduce a saved decoder discrepancy while recording OS and native binaries."""
import argparse
import json
import os
from pathlib import Path
import platform
import sys

import ldpc
import numpy as np
import calibration as c
import tile_study as t


def probe(fixture):
    if (fixture["size"],fixture["noise"],fixture["physical_decoder_prior"])!=(12,"depolarizing",.05):
        raise ValueError("unexpected fixed discrepancy fixture")
    state=np.asarray(fixture["state"])
    if state.shape!=(288,) or not np.issubdtype(state.dtype,np.integer) or np.any(state<0) or np.any(state>3):
        raise ValueError("invalid fixture physical state")
    state=state.astype(np.uint8)
    _,problem=t.build_problem(12,"depolarizing",.05)
    def prediction(problem):
        syndrome=problem.model.syndrome(state)
        observed=problem.model.observables(state)
        predicted=problem.decoder.predict(syndrome).copy()
        sector=sum(int(value)<<bit for bit,value in enumerate(observed^predicted))
        return dict(predicted=predicted.tolist(),sector=sector,failure=bool(problem.is_faulty(state)))
    repeated=[prediction(problem) for _ in range(10)]
    fresh=[prediction(t.build_problem(12,"depolarizing",.05)[1]) for _ in range(4)]
    checks=t.decoder_probe(12,"depolarizing",.05,np.stack([state]*4),priors=[])
    root=Path(ldpc.__file__).parent
    binaries={path.relative_to(root).as_posix():c.file_hash(path) for path in sorted(root.rglob("*"))
              if path.is_file() and path.suffix in (".so",".pyd",".dll")}
    return dict(fixture=c.digest(fixture),source_sha256=c.file_hash(__file__),runtime=t.runtime(),
                platform=platform.platform(),machine=platform.machine(),python_build=platform.python_build(),
                byteorder=sys.byteorder,thread_environment={key:os.environ.get(key) for key in
                  ("OMP_NUM_THREADS","OPENBLAS_NUM_THREADS","MKL_NUM_THREADS","NUMEXPR_NUM_THREADS")},
                native_ldpc_sha256=binaries,problem_hash=c.digest(problem.metadata()),
                repeated=repeated,fresh=fresh,decoder_probe=checks,
                agrees_with_stored_sector=all(row["sector"]==fixture["stored_sector"] for row in repeated+fresh),
                warning="One selected state only. Agreement within these repetitions is not a universal determinism proof. Different OS/native binaries can differ even when package version strings match; the mechanism has not been isolated by this probe.")


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--fixture",type=Path,required=True)
    parser.add_argument("--output",type=Path,required=True)
    args=parser.parse_args()
    if args.output.exists():
        raise ValueError("use a new output path")
    result=probe(json.loads(args.fixture.read_text()))
    c.atomic_json(args.output,result)
    print(json.dumps({key:result[key] for key in ("platform","agrees_with_stored_sector","decoder_probe")}))


if __name__=="__main__":
    main()
