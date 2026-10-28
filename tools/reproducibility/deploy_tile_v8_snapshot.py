"""Stage one finite v8 private collection under the shared physical PBS gate."""
import hashlib
import importlib.util
import json
from pathlib import Path
import shlex
import sys


def pin(path):
    return dict(path=str(path),sha256=hashlib.sha256(Path(path).read_bytes()).hexdigest())


def main():
    work=Path.home()/'workspace/mcmc4qec';remote=work/'20261024-c3t2-index-relocation-v1'
    collector=Path(__file__).with_name('collect_tile_v8_snapshot.py').resolve();source=pin(collector)
    assert source['sha256']==sys.argv[1]
    stage=remote/'pipeline-submissions/reproduction-v8-finite-snapshot-v2';stage.mkdir()
    policy=pin(work/'20261025-low-parallel-dispatch-policy-v4/policy.json')
    assert policy['sha256']=='ac2333a854caae961e620fd76a9e286b0840e11330df9088158c17ad58b895a9'
    vnode=json.loads(Path(policy['path']).read_bytes())['allowed_vnodes'][1]
    script='\n'.join(['#!/bin/bash','#PBS -N m4q-v8-snapshot','#PBS -q workq',
        '#PBS -l select=1:ncpus=1:mem=2gb:vnode='+vnode,'#PBS -l walltime=00:10:00',
        '#PBS -o '+str(stage/'pbs.out'),'#PBS -e '+str(stage/'pbs.err'),'set -euo pipefail',
        'unset PYTHONPATH MCMC4QEC_CLUSTER_TRANSPORT','export PYTHONDONTWRITEBYTECODE=1 PYTHONHASHSEED=0',
        'export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 NUMEXPR_NUM_THREADS=1 VECLIB_MAXIMUM_THREADS=1',
        'exec '+shlex.join([sys.executable,'-B',str(collector),'--stage',str(stage),'--self-sha256',source['sha256']]),''])
    with (stage/'job.sh').open('x') as stream:stream.write(script)
    with (stage/'staging-authority.json').open('x') as stream:
        json.dump(dict(collector=source,deployer=pin(Path(__file__).resolve()),policy=policy,
            private_snapshot_only=True,raw_native_content_read_authorized=False),stream,indent=2)
    submit=remote/'output/physical_aux_submission_v1/submit.py'
    assert pin(submit)['sha256']=='b42d80c7df9c9cc1e1bf24f32fe9421ba7e3ce0d4a8c58c7c225d5d5c72b0869'
    spec=importlib.util.spec_from_file_location('v8_snapshot_physical_submit',submit);module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    result=module.submit_script(str(stage),pin(stage/'job.sh'),policy,
        dispatcher_pin=pin(remote/'output/low_parallel_dispatch_v2/dispatch.py'),execute=True)
    print(json.dumps(result))


if __name__=='__main__':main()
