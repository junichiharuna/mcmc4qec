"""Submit one fixed full-estimator timing partition with explicit source roots."""
import argparse
import os
from pathlib import Path
import re
import secrets
import shlex
import subprocess

import calibration as c
import tile_low_noise_timing_execution as r
from submit import own_active_jobs
from submit_tile_capacity import requested_nodes
from submit_tile_mc_time import live_controllers


def fresh(root):
    r.require(not any((Path(root)/name).exists() for name in ('submission-intent.json','submission.json','execution-intent.json','tasks','summary.json')),'fresh execution required')


def bundle_binding(bundle,plan):
    bundle=Path(bundle).resolve();snapshot=plan['snapshot'];sources=r.source_hashes()
    r.require(sources==snapshot['source_sha256'],'actual source paths/hash differ')
    for name in ('tile_low_noise_timing_execution','submit_tile_low_noise_timing_execution'):
        r.require(r.source_files()[name].resolve()==bundle/'cluster_scripts'/(name+'.py'),'runner/submitter outside bundle')
    r.require(snapshot['runtime']==r.t.runtime() and snapshot['pythonpath']==os.environ.get('PYTHONPATH','')
        and snapshot['core_path']==str(Path(r.qec.__file__).absolute())
        and snapshot['python_path']==str(Path(r.sys.executable).absolute())
        and snapshot['python_sha256']==c.file_hash(r.sys.executable),'Python/core/import path differs')
    return {key:snapshot[key] for key in ('source_sha256','runtime','pythonpath','core_path','python_path','python_sha256')}


def script_text(bundle,root,plan):
    bundle=Path(bundle).resolve();root=Path(root).resolve();res=plan['resource']
    command=shlex.join([plan['snapshot']['python_path'],str(bundle/'cluster_scripts/tile_low_noise_timing_execution.py'),'run','--root',str(root)])
    return f'''#!/bin/bash
#PBS -N m4q_lowtime
#PBS -q workq
#PBS -l select=1:ncpus={res['cpus']}:mem={res['memory_gb']}gb
#PBS -l walltime={res['walltime']}
#PBS -o {root}/timing.out
#PBS -e {root}/timing.err
set -euo pipefail
: "${{PBS_JOBID:?submit with qsub}}"
cd {shlex.quote(str(bundle))}
export PYTHONPATH={shlex.quote(plan['snapshot']['pythonpath'])}
export PYTHONDONTWRITEBYTECODE=1 PYTHONHASHSEED=0
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 NUMEXPR_NUM_THREADS=1
{command}
'''


def upstream(plan,runner):
    descriptors=plan['config']['census'];ledger=r.json_read(descriptors['submission']['path'])
    actual=r.qstat(ledger['job_id'],runner)
    r.check_pbs(ledger,actual['Jobs'][ledger['job_id']],terminal=True,hostname=r.json_read(descriptors['native']['path'])['hostname'])
    if plan['capacity_reference']:
        root=Path(plan['capacity_reference']['root']);ledger=r.json_read(root/'submission.json')
        record=r.qstat(ledger['job_id'],runner)
        r.check_pbs(ledger,record['Jobs'][ledger['job_id']],terminal=True,hostname=r.json_read(root/'native_preflight.json')['hostname'])
        actual['Jobs'].update(record['Jobs'])
    return actual


def submit(bundle,root,*,execute=False,controller_query=live_controllers,active_query=own_active_jobs,runner=subprocess.run):
    bundle=Path(bundle).resolve();root=Path(root).resolve()
    r.require(root!=bundle/'runs' and root.is_relative_to(bundle/'runs')
        and not any(ch.isspace() for path in (bundle,root) for ch in str(path)),'new output under bundle/runs required')
    fresh(root);plan=r.read_plan(root)
    r.require(plan['planning_status']=='ready' and plan['tasks'],'ineligible execution cannot submit')
    binding=bundle_binding(bundle,plan);script=script_text(bundle,root,plan);path=root/'timing.sh'
    if path.exists():r.require(path.read_text()==script,'existing script differs')
    else:
        with path.open('x',newline='\n') as stream:stream.write(script)
    record=dict(command=['qsub',str(path)],manifest=c.digest(plan),resource=plan['resource'],bundle_binding=binding,
        script_sha256=c.file_hash(path),submit_source_sha256=c.file_hash(__file__))
    if not execute:
        c.atomic_json(root/'dry_run.json',dict(record,job_id='dry-run'));return dict(record,job_id='dry-run')
    lock=bundle.parent/'tile-low-noise-submission.lock'
    with lock.open('xb') as stream:stream.write(c.canonical(dict(root=str(root),pid=os.getpid(),token=secrets.token_hex(16)))+b'\n')
    lock_hash=c.file_hash(lock)
    def owned():r.require(lock.exists() and c.file_hash(lock)==lock_hash,'submission lock ownership changed')
    uncertain=False
    try:
        fresh(root)
        owned()
        r.require(not controller_query() and requested_nodes(active_query())+1<=2,'controller active or two-node budget exceeded')
        actual=upstream(plan,runner)
        r.require(r.read_plan(root)==plan and bundle_binding(bundle,plan)==binding and c.file_hash(path)==record['script_sha256'],'inputs/source/script changed')
        r.require(not controller_query() and requested_nodes(active_query())+1<=2,'controller or allocation changed')
        fresh(root);owned();r.save_new(root/'upstream-completion-at-submit.json',actual)
        record['upstream_completion_sha256']=c.file_hash(root/'upstream-completion-at-submit.json')
        r.save_new(root/'submission-intent.json',record)
        # The persisted intent is itself part of the final pre-qsub boundary.
        owned()
        r.require(not controller_query() and requested_nodes(active_query())+1<=2,'final controller or allocation changed')
        r.require(r.read_plan(root)==plan and bundle_binding(bundle,plan)==binding
            and c.file_hash(path)==record['script_sha256']
            and c.file_hash(root/'upstream-completion-at-submit.json')==record['upstream_completion_sha256']
            and c.file_hash(root/'submission-intent.json')==r.hashlib.sha256(c.canonical(record)+b'\n').hexdigest(),
            'final input/source/script/intent changed')
        owned();uncertain=True
        job=runner(record['command'],capture_output=True,text=True,check=True,timeout=30).stdout.strip()
        r.save_new(root/'qsub-response.json',dict(command=record['command'],stdout=job))
        owned()
        r.require(re.fullmatch(r'\d+(?:\.[A-Za-z0-9_.-]+)?',job),'ambiguous qsub; retain lock and intent')
        record['job_id']=job;r.save_new(root/'submission.json',record);uncertain=False
        return record
    finally:
        if not uncertain:
            owned();lock.unlink()


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--bundle',type=Path,required=True);parser.add_argument('--root',type=Path,required=True)
    parser.add_argument('--execute',action='store_true');args=parser.parse_args()
    print(r.json.dumps(submit(args.bundle,args.root,execute=args.execute)))


if __name__=='__main__':main()
