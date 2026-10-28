"""Stage pinned exporter fixtures through the two-physical-node admission gate."""
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
    assert {p.name:pin(p)['sha256'] for p in folder.glob('*.py')}==expected
    stage=remote/'pipeline-submissions/share-snapshot-v2-fixtures-v2';stage.mkdir()
    request=dict(purpose='share_snapshot_v2_fixture_request',sources={p.name:pin(p) for p in folder.glob('*.py')})
    with (stage/'request.json').open('x') as stream:json.dump(request,stream,indent=2)
    request_pin=pin(stage/'request.json')
    policy=pin(work/'20261025-low-parallel-dispatch-policy-v4/policy.json')
    assert policy['sha256']=='ac2333a854caae961e620fd76a9e286b0840e11330df9088158c17ad58b895a9'
    vnode=json.loads(Path(policy['path']).read_bytes())['allowed_vnodes'][1]
    script='\n'.join(['#!/bin/bash','#PBS -N m4q-share-test','#PBS -q workq',
        '#PBS -l select=1:ncpus=1:mem=2gb:vnode='+vnode,'#PBS -l walltime=00:10:00',
        '#PBS -o '+str(stage/'pbs.out'),'#PBS -e '+str(stage/'pbs.err'),'set -euo pipefail',
        'unset PYTHONPATH MCMC4QEC_CLUSTER_TRANSPORT','export PYTHONDONTWRITEBYTECODE=1 PYTHONHASHSEED=0',
        'exec '+shlex.join([sys.executable,'-B',str(folder/'worker.py'),request_pin['path'],request_pin['sha256']]),''])
    with (stage/'job.sh').open('x') as stream:stream.write(script)
    submit=remote/'output/physical_aux_submission_v1/submit.py'
    assert pin(submit)['sha256']=='b42d80c7df9c9cc1e1bf24f32fe9421ba7e3ce0d4a8c58c7c225d5d5c72b0869'
    spec=importlib.util.spec_from_file_location('share_fixture_submit',submit);module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    result=module.submit_script(str(stage),pin(stage/'job.sh'),policy,
        dispatcher_pin=pin(remote/'output/low_parallel_dispatch_v2/dispatch.py'),execute=True)
    print(json.dumps(result))


if __name__=='__main__':main()
