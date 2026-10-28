"""Submit a pinned documentary archive build using the existing physical-node gate."""
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import shlex
import sys


def pin(path):
    return dict(path=str(Path(path).resolve()),sha256=hashlib.sha256(Path(path).read_bytes()).hexdigest())


def read(path,expected):
    raw=Path(path).read_bytes()
    if hashlib.sha256(raw).hexdigest()!=expected:raise ValueError('Deployment authority bytes changed')
    return json.loads(raw)


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--stage',required=True)
    parser.add_argument('--fixture',required=True);parser.add_argument('--fixture-sha256',required=True)
    parser.add_argument('--snapshot',required=True);parser.add_argument('--snapshot-sha256',required=True)
    parser.add_argument('--physical-policy',required=True);parser.add_argument('--physical-policy-sha256',required=True)
    parser.add_argument('--aux-submit',required=True);parser.add_argument('--aux-submit-sha256',required=True)
    parser.add_argument('--dispatcher',required=True);parser.add_argument('--dispatcher-sha256',required=True)
    args=parser.parse_args()
    fixture=read(args.fixture,args.fixture_sha256);snapshot=read(args.snapshot,args.snapshot_sha256)
    physical=read(args.physical_policy,args.physical_policy_sha256)
    source=Path(__file__).resolve().parent
    sources={name:fixture['sources'][name] for name in ('snapshot_v2.py','share_snapshot_v2_revision2.py','test_share_snapshot_v2_revision2.py')}
    for name in ('share_policy_v2.py','test_share_policy_v2.py','build_share_snapshot_v2.py','deploy_share_snapshot_v2.py'):
        sources[name]=pin(source/name)
    for descriptor in sources.values():
        if pin(descriptor['path'])!=descriptor:raise ValueError('Candidate source changed')
    stage=Path(args.stage);stage.mkdir(parents=False,exist_ok=False)
    request=dict(schema=1,purpose='finite_v2_revision2_sharing_candidate_build',sources=sources,
        exporter_fixture=dict(path=args.fixture,sha256=args.fixture_sha256),
        snapshot_acceptance=dict(path=args.snapshot,sha256=args.snapshot_sha256),snapshot_receipt=snapshot['snapshot_receipt'])
    request_path=stage/'request.json'
    with request_path.open('x') as stream:json.dump(request,stream,sort_keys=True,indent=2)
    command=[sys.executable,'-B',str(source/'build_share_snapshot_v2.py'),'--request',str(request_path),'--sha256',pin(request_path)['sha256']]
    script='\n'.join(['#!/bin/bash','#PBS -N m4q-share-v2','#PBS -q workq',
        '#PBS -l select=1:ncpus=1:mem=8gb:vnode='+physical['allowed_vnodes'][1],'#PBS -l walltime=00:15:00',
        '#PBS -o '+str(stage/'pbs.out'),'#PBS -e '+str(stage/'pbs.err'),'set -euo pipefail',
        'unset PYTHONPATH MCMC4QEC_CLUSTER_TRANSPORT','export PYTHONDONTWRITEBYTECODE=1 PYTHONHASHSEED=0',
        'export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 NUMEXPR_NUM_THREADS=1',
        'exec '+shlex.join(command),''])
    with (stage/'job.sh').open('x') as stream:stream.write(script)
    for path,expected in ((args.aux_submit,args.aux_submit_sha256),(args.dispatcher,args.dispatcher_sha256)):
        if pin(path)['sha256']!=expected:raise ValueError('Physical gate source changed')
    spec=importlib.util.spec_from_file_location('shared_candidate_physical_gate',args.aux_submit)
    gate=importlib.util.module_from_spec(spec);spec.loader.exec_module(gate)
    result=gate.submit_script(str(stage),pin(stage/'job.sh'),dict(path=args.physical_policy,sha256=args.physical_policy_sha256),
        dispatcher_pin=dict(path=args.dispatcher,sha256=args.dispatcher_sha256),execute=True)
    print(json.dumps(result))


if __name__=='__main__':main()
