"""Prepare a finite delta job; submit only after the original merge is terminal."""
import hashlib
import importlib.util
import json
from pathlib import Path
import shlex
import subprocess
import sys

MAX=4*1024**2


def read(p):
    with Path(p['path']).open('rb') as f:value=f.read(MAX+1)
    assert len(value)<=MAX and hashlib.sha256(value).hexdigest()==p['sha256']
    return json.loads(value)


def pin(path):
    with Path(path).open('rb') as f:value=f.read(MAX+1)
    assert len(value)<=MAX
    return dict(path=str(path),sha256=hashlib.sha256(value).hexdigest())


def save(path,value):
    raw=json.dumps(value,sort_keys=True,indent=2).encode()+b'\n';assert len(raw)<=MAX
    with path.open('xb') as f:f.write(raw)
    return pin(path)


def prepare(expected_pin):
    work=Path.home()/'workspace/mcmc4qec';remote=work/'20261024-c3t2-index-relocation-v1';folder=Path(__file__).resolve().parent
    expected=read(expected_pin);sources={name:pin(folder/name) for name in ('prepare.py','collect.py','test_collect.py','stage.py')}
    assert {name:p['sha256'] for name,p in sources.items()}==expected
    inventory=dict(path=str(folder/'inventory-v1/inventory.json'),sha256='1c2edc25c6d3b0a8ea41329600af4808d9f67834590d798f6cbfb81b5c9fa837')
    inv=read(inventory);flow=read(inv['flow'])
    stage=remote/'pipeline-submissions/reproduction-v11-control-delta-v1';stage.mkdir()
    scope=pin(remote/'output/reproduction_snapshot_v9_v2/collect.py');assert scope['sha256']=='4c2f1d728feb635e3efe9eb76ccfe4e2793211d28040d3b050c3eab80655cd68'
    request=save(stage/'request.json',dict(purpose='finite_v11_delta_collection',sources=sources,
        inventory=inventory,scope=scope,library=inv['library'],stage=str(stage)))
    policy=pin(work/'20261025-low-parallel-dispatch-policy-v4/policy.json')
    assert policy['sha256']=='ac2333a854caae961e620fd76a9e286b0840e11330df9088158c17ad58b895a9'
    vnode=read(policy)['allowed_vnodes'][1]
    script='\n'.join(['#!/bin/bash','#PBS -N m4q-v11-snapshot','#PBS -q workq',
        '#PBS -l select=1:ncpus=1:mem=2gb:vnode='+vnode,'#PBS -l walltime=00:10:00',
        '#PBS -o '+str(stage/'pbs.out'),'#PBS -e '+str(stage/'pbs.err'),'set -euo pipefail',
        'unset PYTHONPATH MCMC4QEC_CLUSTER_TRANSPORT','export PYTHONDONTWRITEBYTECODE=1 PYTHONHASHSEED=0',
        'export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 NUMEXPR_NUM_THREADS=1 VECLIB_MAXIMUM_THREADS=1',
        'exec '+shlex.join([sys.executable,'-B',str(folder/'collect.py'),request['path'],request['sha256']]),''])
    with (stage/'job.sh').open('x') as f:f.write(script)
    ledger_pin=next({k:p[k] for k in ('path','sha256')} for p in inv['metadata']
        if p['path']==str(Path(flow['merge_root'])/'submission.json'))
    ledger=read(ledger_pin);assert ledger['job_id'].split('.')[0]=='265660'
    ready=save(stage/'ready.json',dict(request=request,stage=str(stage),script=pin(stage/'job.sh'),policy=policy,
        merge_submission=ledger_pin,merge_job_id=ledger['job_id'],gate=pin(remote/'output/physical_aux_submission_v1/submit.py'),
        dispatcher=pin(remote/'output/low_parallel_dispatch_v2/dispatch.py'),deployer=sources['stage.py'],qsub_executed=False))
    print(json.dumps(dict(status='prepared_waiting_for_merge_terminal',ready=ready,qsub_executed=False)))


def submit(ready_pin):
    value=read(ready_pin);read(value['request']);ledger=read(value['merge_submission'])
    assert pin(Path(__file__).resolve())==value['deployer']
    assert ledger['job_id']==value['merge_job_id']
    response=subprocess.run(['qstat','-x','-f','-F','json',value['merge_job_id']],capture_output=True,check=True,timeout=30)
    assert len(response.stdout)<=MAX
    jobs=json.loads(response.stdout)['Jobs'];assert set(jobs)=={value['merge_job_id']}
    row=jobs[value['merge_job_id']]
    if row['job_state']!='F':
        print(json.dumps(dict(status='waiting_for_merge_terminal',qsub_executed=False)));return
    assert row['run_count']==1 and shlex.split(row['Submit_arguments'])==ledger['command'][1:]
    assert pin(value['script']['path'])==value['script'] and pin(value['gate']['path'])==value['gate']
    assert value['gate']['sha256']=='b42d80c7df9c9cc1e1bf24f32fe9421ba7e3ce0d4a8c58c7c225d5d5c72b0869'
    assert value['dispatcher']['sha256']=='fbe678962b0fbe00de43518915a8147d1c932acbf9c4e9de496a0a51d90b1f26'
    spec=importlib.util.spec_from_file_location('unchanged_snapshot_gate',value['gate']['path']);gate=importlib.util.module_from_spec(spec);spec.loader.exec_module(gate)
    result=gate.submit_script(value['stage'],value['script'],value['policy'],dispatcher_pin=value['dispatcher'],execute=True)
    print(json.dumps(result))


if __name__=='__main__':
    assert sys.argv[1] in ('prepare','submit')
    (prepare if sys.argv[1]=='prepare' else submit)(dict(path=sys.argv[2],sha256=sys.argv[3]))
