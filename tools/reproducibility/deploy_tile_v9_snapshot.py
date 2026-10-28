"""Submit a fresh private v9 snapshot through the accepted physical-node gate."""
import hashlib
import importlib.util
import json
from pathlib import Path
import shlex
import sys


def pin(path):return dict(path=str(path),sha256=hashlib.sha256(Path(path).read_bytes()).hexdigest())


def main():
    work=Path.home()/'workspace/mcmc4qec';remote=work/'20261024-c3t2-index-relocation-v1';folder=Path(__file__).resolve().parent
    expected=json.loads(Path(sys.argv[1]).read_bytes())
    sources={p.name:pin(p) for p in folder.glob('*.py')}
    assert {name:p['sha256'] for name,p in sources.items()}==expected
    stage=remote/'pipeline-submissions/reproduction-v9-finite-snapshot-v2';stage.mkdir()
    old=remote/'pipeline-submissions/reproduction-v8-finite-snapshot-v2/accepted.json'
    assert pin(old)['sha256']=='7e702412d2fb054b0c351d3be8e971eeb4301cce43c88c8f89dacca39bd536a2'
    library=json.loads(old.read_bytes())['library']
    assert library['sha256']=='053265218e64768d48e13871b47d9c6bb33bb659557122344b4c6b3300cdf35a'
    policy=pin(work/'20261025-low-parallel-dispatch-policy-v4/policy.json')
    assert policy['sha256']=='ac2333a854caae961e620fd76a9e286b0840e11330df9088158c17ad58b895a9'
    with (stage/'staging-authority.json').open('x') as f:
        json.dump(dict(sources=sources,library=library,policy=policy,private_snapshot_only=True,
            raw_native_content_read_authorized=False,scientific_completion_claimed=False),f,indent=2)
    authority=pin(stage/'staging-authority.json');vnode=json.loads(Path(policy['path']).read_bytes())['allowed_vnodes'][1]
    lines=['#!/bin/bash','#PBS -N m4q-v9-snapshot','#PBS -q workq',
        '#PBS -l select=1:ncpus=1:mem=2gb:vnode='+vnode,'#PBS -l walltime=00:10:00',
        '#PBS -o '+str(stage/'pbs.out'),'#PBS -e '+str(stage/'pbs.err'),'set -euo pipefail',
        'unset PYTHONPATH MCMC4QEC_CLUSTER_TRANSPORT','export PYTHONDONTWRITEBYTECODE=1 PYTHONHASHSEED=0',
        'export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 NUMEXPR_NUM_THREADS=1 VECLIB_MAXIMUM_THREADS=1',
        'exec '+shlex.join([sys.executable,'-B',str(folder/'run.py'),str(stage),authority['sha256']]),'']
    with (stage/'job.sh').open('x') as f:f.write('\n'.join(lines))
    auxiliary=remote/'output/physical_aux_submission_v1/submit.py'
    assert pin(auxiliary)['sha256']=='b42d80c7df9c9cc1e1bf24f32fe9421ba7e3ce0d4a8c58c7c225d5d5c72b0869'
    spec=importlib.util.spec_from_file_location('v9_snapshot_auxiliary',auxiliary);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
    result=m.submit_script(str(stage),pin(stage/'job.sh'),policy,
        dispatcher_pin=pin(remote/'output/low_parallel_dispatch_v2/dispatch.py'),execute=True)
    print(json.dumps(result))


if __name__=='__main__':main()
