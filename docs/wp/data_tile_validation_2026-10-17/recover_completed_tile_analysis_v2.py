"""Prepare immutable PBS exports of completed tile analysis cases 0 through 3.

Default plan is local/read-only. Stage checks PBS completion before creating a
fresh remote export directory, but NEVER submits a job. The owner schedules the
printed qsub command after the coordinator terminates and within max two nodes.
Worker performs archive I/O on a PBS node. Collect is a separate explicit action.
"""
import argparse
import datetime
import hashlib
import itertools
import json
import os
from pathlib import Path,PurePosixPath
import re
import shlex
import subprocess
import sys
import tarfile
import time

BASE='/home/user/workspace/mcmc4qec'
PROD=BASE+'/20261017-tile-production-v1'
SOURCE=Path(PROD+'/runs/production')
PYTHON=PROD+'/venv/bin/python'
MANIFEST_SHA='eea71716f1e66f230ff526adfa633717f5e9dc8ce2b9b2586eae40d74494cbce'
PINNED_SHA256={
    'manifest.json':MANIFEST_SHA,
    'analysis_manifest.json':'e372d911a475e15dd86c0c9aa53839ceeab033fdabd59f8cfab44b56c76f0d72',
    'reference_summary.json':'72afbc93f9fb33d46cc967e542856a6a42031f6a0e1d2f2423c90aaf2e0a5d15'}
SOURCE_SHA256={
    'tile_bar_analysis.py':'7d22afe9b4ee554e255ca1556510b2c76d892d7817ad44ae7a423971a58505de',
    'tile_summary.py':'f8f324eac24d748639a4e55bf0f410d04800bb5b2452699379c9a4eda8769574'}
DATA=Path('docs/wp/data_tile_validation_2026-10-17')


def canonical(value):
    return json.dumps(value,sort_keys=True,separators=(',',':'),allow_nan=False).encode()


def digest_file(path):
    h=hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda:stream.read(1024*1024),b''):h.update(block)
    return h.hexdigest()


def write_new(path,value):
    with Path(path).open('x',encoding='utf-8') as stream:
        json.dump(value,stream,indent=2,sort_keys=True);stream.write('\n')


def target_root(case,tag):
    if not tag or any(c not in '0123456789abcdefghijklmnopqrstuvwxyz-' for c in tag):
        raise ValueError('tag must contain only lower-case ASCII, digits and hyphens')
    return PurePosixPath(BASE)/f'{tag}-tile-case{case}-analysis-recovery'


def digest(value):
    return hashlib.sha256(canonical(value)).hexdigest()


def expected_artifacts(plan,context,case):
    groups=itertools.product(range(len(plan['kernels'])),range(len(plan['initializations'])),range(plan['replicates']))
    return {'analysis/'+ '-'.join(map(str,(case,*group))):dict(analysis=digest(context),group=[case,*group]) for group in groups}


def rows_per_group(plan,case):
    spec=plan['cases'][case]
    return len(set((4,spec['chains'])))*len(plan['burns'])*2*sum(1+sum(block<=samples and (block!=1024 or samples>=6000) for block in plan['blocks']) for samples in spec['windows'])


def terminal_job(job_id,script,*,remote=False):
    if not isinstance(job_id,str) or not re.fullmatch(r'\d+(?:\.[A-Za-z0-9_.-]+)?',job_id):raise ValueError('invalid PBS job id')
    command=['qstat','-x','-f','-F','json',job_id]
    if remote:command=['ssh','cluster',shlex.join(command)]
    jobs=json.loads(subprocess.run(command,capture_output=True,text=True,check=True,timeout=30).stdout)['Jobs']
    if len(jobs)!=1:raise ValueError('PBS lookup is not unique')
    actual,job=next(iter(jobs.items()))
    if actual!=job_id and not (job_id.isdigit() and actual.split('.')[0]==job_id):raise ValueError('PBS identity differs')
    if job['job_state']!='F' or job.get('Exit_status')!=0:raise ValueError('PBS job not authoritatively F/exit0')
    if job.get('Submit_arguments')!=str(script):raise ValueError('PBS script binding differs')
    return {key:value for key,value in job.items() if key!='Variable_List'}


def completion_gate(case):
    """Validate fixed output bindings without recomputing estimates or traces."""
    started=time.perf_counter()
    read=lambda name:json.loads((SOURCE/name).read_text())
    ledger=read(f'analysis_submission-{case}.json')
    script=SOURCE/f'analyze-{case}.sh'
    if ledger['command']!=['qsub',str(script)] or ledger['case']!=case:raise ValueError('submission identity differs')
    job=terminal_job(ledger['job_id'],script)
    if any(digest_file(SOURCE/name)!=sha for name,sha in PINNED_SHA256.items()):raise ValueError('fixed manifest/context/reference changed')
    source_dir=SOURCE.parent.parent/'cluster_scripts'
    if any(digest_file(source_dir/name)!=sha for name,sha in SOURCE_SHA256.items()):raise ValueError('fixed analysis/summary source changed')
    plan,context=read('manifest.json'),read('analysis_manifest.json')
    if context['sampling_manifest']!=digest(plan) or context['runtime']!=plan['runtime']:raise ValueError('context binding differs')
    if context['analysis_source_sha256']!=SOURCE_SHA256['tile_bar_analysis.py'] or context['reference_summary_sha256']!=PINNED_SHA256['reference_summary.json']:raise ValueError('context source/reference differs')
    if ledger['manifest']!=digest(plan) or ledger['script_sha256']!=digest_file(script) or ledger['analysis_manifest_sha256']!=PINNED_SHA256['analysis_manifest.json'] or ledger['resource_plan_sha256']!=digest_file(SOURCE/'analysis_resource_plan.json'):raise ValueError('submission hash binding differs')
    expected=expected_artifacts(plan,context,case)
    expected_names={stem+ext for stem in expected for ext in ('.json','.npz','.done.json')}
    if {p.relative_to(SOURCE).as_posix() for p in (SOURCE/'analysis').glob(f'{case}-*')}!=expected_names:raise ValueError('artifact set incomplete or unexpected')
    for stem,identity in expected.items():
        marker=read(stem+'.done.json')
        if marker['identity']!=identity or set(marker['sha256'])!={'.json','.npz'}:raise ValueError('artifact marker identity differs')
    analysis,summary=read(f'analysis_summary-{case}.json'),read(f'summary-{case}.json')
    planned_rows=len(expected)*rows_per_group(plan,case)
    if analysis['analysis']!=digest(context) or analysis['groups']!=len(expected) or analysis['rows']!=planned_rows:raise ValueError('analysis summary denominator differs')
    if not 0<=analysis['unavailable_intervals']<=planned_rows:raise ValueError('invalid unavailable interval count')
    conditions=rows_per_group(plan,case)*len(plan['kernels'])*len(plan['initializations'])
    if summary['case']!=case or summary['analysis']!=digest(context) or summary['conditions']!=conditions or len(summary['records'])!=conditions or any(row['replicates']!=plan['replicates'] for row in summary['records']):raise ValueError('cohort summary denominator differs')
    if summary['summary_source_sha256']!=SOURCE_SHA256['tile_summary.py'] or summary['raw_rows_sha256']!=digest_file(SOURCE/f'rows-{case}.jsonl'):raise ValueError('summary/raw rows hash differs')
    selected=['manifest.json','analysis_manifest.json','reference_summary.json','analysis_resource_plan.json',f'analysis_submission-{case}.json',f'analysis_summary-{case}.json',f'summary-{case}.json',f'rows-{case}.jsonl',*[f'analyze-{case}.{ext}' for ext in ('sh','out','err')],*sorted(expected_names)]
    if any(not (SOURCE/name).is_file() or (SOURCE/name).is_symlink() for name in selected):raise ValueError('required regular source file missing or symlinked')
    now=datetime.datetime.now(datetime.timezone.utc)
    return selected,expected,dict(observed_utc=now.isoformat(),observed_jst=now.astimezone(datetime.timezone(datetime.timedelta(hours=9))).isoformat(),case=case,job_id=ledger['job_id'],job=job,groups=len(expected),rows=planned_rows,unavailable_intervals=analysis['unavailable_intervals'],files=len(selected),source_bytes=sum((SOURCE/name).stat().st_size for name in selected),pinned_sha256=PINNED_SHA256,source_sha256=SOURCE_SHA256,summary_sha256=digest_file(SOURCE/f'summary-{case}.json'),gate_wall_seconds=time.perf_counter()-started,warning='All artifacts and raw rows retained, including failures and undefined intervals. Integrity and completion only; not numerical validation.')


def worker(case,target):
    target=Path(target)
    if not os.environ.get('PBS_JOBID'):raise RuntimeError('Archive export requires a PBS allocation; do not compress on login')
    import resource
    # A compute-node /proc cannot establish login-node controller termination.
    # The submitting owner must check all live controllers and the <=2-node
    # budget on the login node immediately before qsub. This worker does not
    # claim to enforce or independently prove that global submission gate.
    started=time.perf_counter();cpu=time.process_time()
    selected,expected,gate=completion_gate(case)
    worker_sha,script_sha=digest_file(__file__),digest_file(target/'export.sh')
    write_new(target/'export-intent.json',dict(gate,pbs_job_id=os.environ['PBS_JOBID'],worker_sha256=worker_sha,export_script_sha256=script_sha))
    hashes={name:digest_file(SOURCE/name) for name in selected}
    for stem in expected:
        marker=json.loads((SOURCE/(stem+'.done.json')).read_text())
        if any(hashes[stem+ext]!=sha for ext,sha in marker['sha256'].items()):raise ValueError('source payload checksum mismatch')
    archive=target/f'production-analysis-{case}.tar.gz'
    with archive.open('xb') as raw:
        with tarfile.open(fileobj=raw,mode='w:gz',compresslevel=1) as stream:
            for name in selected:stream.add(SOURCE/name,arcname=name,recursive=False)
    after={name:digest_file(SOURCE/name) for name in selected}
    if after!=hashes:raise RuntimeError('source changed during export; partial archive retained but not accepted')
    selected_after,expected_after,gate_after=completion_gate(case)
    if selected_after!=selected or expected_after!=expected or gate_after['summary_sha256']!=gate['summary_sha256']:raise RuntimeError('completion input set changed')
    if digest_file(__file__)!=worker_sha or digest_file(target/'export.sh')!=script_sha:raise RuntimeError('export source/script changed')
    checksum=digest_file(archive)
    write_new(target/'input_sha256.json',hashes)
    record=dict(gate,archive=str(archive),bytes=archive.stat().st_size,sha256=checksum,pbs_job_id=os.environ['PBS_JOBID'],elapsed_seconds=time.perf_counter()-started,cpu_seconds=time.process_time()-cpu,peak_rss_mib=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss/1024,compression='gzip level1',source_unchanged=True,input_hashes_sha256=digest_file(target/'input_sha256.json'),worker_sha256=worker_sha,export_script_sha256=script_sha,global_controller_terminal_verified_by_worker=False,submission_gate='Owner must check login-node controllers terminal and global <=2-node budget immediately before qsub; compute-node process state cannot establish that gate.',scope='Completed analysis export and source/payload integrity only. No decoder replay or mixing/coverage claim.')
    write_new(target/'export.json',record)
    print(json.dumps(record))


def stage(case,target):
    """Explicit future staging only. Never calls qsub."""
    started=time.perf_counter()
    local=Path(__file__).resolve()
    command=PYTHON+' - --case '+str(case)+' --action check'
    result=subprocess.run(['ssh','cluster',command],input=local.read_bytes(),capture_output=True,check=True,timeout=60)
    gate_ssh_wall_seconds=time.perf_counter()-started
    gate=json.loads(result.stdout)
    write_new(DATA/f'production_analysis_export_gate_case{case}_{target.name}.json',dict(target=str(target),completion=gate,gate_ssh_wall_seconds=gate_ssh_wall_seconds,worker_sha256=digest_file(local),qsub_executed=False))
    subprocess.run(['ssh','cluster','mkdir '+shlex.quote(str(target))],check=True)
    subprocess.run(['scp',str(local),'cluster:'+str(target/'recover_completed_tile_analysis.py')],check=True)
    script=f'''#!/bin/bash
#PBS -N m4q_export{case}
#PBS -q workq
#PBS -l select=1:ncpus=1:mem=4gb
#PBS -l walltime=01:00:00
#PBS -o {target}/export.out
#PBS -e {target}/export.err
set -euo pipefail
: "${{PBS_JOBID:?submit with qsub}}"
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 NUMEXPR_NUM_THREADS=1
{PYTHON} {target}/recover_completed_tile_analysis.py --case {case} --action worker --tag {target.name.split('-tile-case')[0]}
'''
    write_remote_script(target,script.encode('utf-8'))
    verification='import hashlib,json; from pathlib import Path; r=Path('+repr(str(target))+'); print(json.dumps({n:hashlib.sha256((r/n).read_bytes()).hexdigest() for n in ("recover_completed_tile_analysis.py","export.sh")}))'
    hashes=json.loads(subprocess.run(['ssh','cluster',PYTHON+' -c '+shlex.quote(verification)],capture_output=True,text=True,check=True).stdout)
    assert hashes=={'recover_completed_tile_analysis.py':digest_file(local),'export.sh':hashlib.sha256(script.encode()).hexdigest()}
    write_new(DATA/f'production_analysis_export_stage_case{case}_{target.name}.json',dict(target=str(target),completion=gate,sha256=hashes,gate_ssh_wall_seconds=gate_ssh_wall_seconds,stage_wall_seconds=time.perf_counter()-started,qsub_executed=False,next_command=['qsub',str(target/'export.sh')],gate='Owner must verify controller terminal and global maximum two nodes before invoking qsub. One-hour PBS request is an initial ceiling, not a measured completion bound.'))
    print(json.dumps(dict(staged=str(target),qsub_executed=False,next_command=['qsub',str(target/'export.sh')])))


def write_remote_script(target,payload):
    code='from pathlib import Path; import sys; p=Path('+repr(str(target/'export.sh'))+'); f=p.open("xb"); f.write(sys.stdin.buffer.read()); f.close()'
    subprocess.run(['ssh','cluster',PYTHON+' -c '+shlex.quote(code)],input=payload,check=True)


def verify_archive(path,plan,context,case):
    sys.path.insert(0,str(Path('cluster_scripts').resolve()))
    import artifact_archive as audit
    verified=audit.verify(path,audit.expected_artifacts(plan,'production-analysis',case,context))
    for name,sha in PINNED_SHA256.items():
        if verified['payload_sha256'].get(name)!=sha:raise ValueError('archive pinned manifest/context/reference differs')
    if context['sampling_manifest']!=digest(plan) or context['reference_summary_sha256']!=PINNED_SHA256['reference_summary.json']:raise ValueError('archive context binding differs')
    verified.update(stage='production-analysis',case=case,manifest_sha256=PINNED_SHA256['manifest.json'],analysis_manifest_sha256=PINNED_SHA256['analysis_manifest.json'])
    return verified


def collect(case,target):
    """Download a finished export into an exclusive local directory and verify it."""
    stage_path=DATA/f'production_analysis_export_stage_case{case}_{target.name}.json'
    stage_bytes=stage_path.read_bytes()
    stage_hash=hashlib.sha256(stage_bytes).hexdigest()
    accepted=json.loads(stage_bytes)
    if accepted['target']!=str(target) or accepted['completion']['case']!=case or accepted['completion']['pinned_sha256']!=PINNED_SHA256 or accepted['qsub_executed'] is not False:raise ValueError('fixed stage evidence binding differs')
    accepted_hashes=accepted['sha256']
    if set(accepted_hashes)!={'recover_completed_tile_analysis.py','export.sh'}:raise ValueError('fixed stage source/script set differs')
    destination=Path('output/tile_validation_recovery')/target.name
    destination.mkdir(exist_ok=False)
    subprocess.run(['scp','cluster:'+str(target/'export.json'),str(destination/'export.json')],check=True)
    record=json.loads((destination/'export.json').read_text())
    if record['worker_sha256']!=accepted_hashes['recover_completed_tile_analysis.py'] or record['export_script_sha256']!=accepted_hashes['export.sh']:raise ValueError('export source/script differs from accepted stage')
    export_job=terminal_job(record['pbs_job_id'],target/'export.sh',remote=True)
    write_new(destination/'export_pbs_completion.json',export_job)
    for name in ('recover_completed_tile_analysis.py','input_sha256.json','export.sh','export.out','export.err'):
        subprocess.run(['scp','cluster:'+str(target/name),str(destination/name)],check=True)
    assert digest_file(destination/'recover_completed_tile_analysis.py')==record['worker_sha256']
    assert digest_file(destination/'export.sh')==record['export_script_sha256']
    subprocess.run(['scp','cluster:'+str(target/f'production-analysis-{case}.tar.gz'),str(destination/f'production-analysis-{case}.tar.gz')],check=True)
    archive=destination/f'production-analysis-{case}.tar.gz'
    assert record['case']==case and record['source_unchanged'] and record['pinned_sha256']==PINNED_SHA256
    assert archive.stat().st_size==record['bytes'] and digest_file(archive)==record['sha256']
    assert digest_file(destination/'input_sha256.json')==record['input_hashes_sha256']
    if digest_file(DATA/'production_manifest.json')!=PINNED_SHA256['manifest.json'] or digest_file(DATA/'production_analysis_manifest.json')!=PINNED_SHA256['analysis_manifest.json']:raise ValueError('local fixed manifest/context changed')
    plan=json.loads((DATA/'production_manifest.json').read_text())
    context=json.loads((DATA/'production_analysis_manifest.json').read_text())
    verified=verify_archive(archive,plan,context,case)
    assert verified['payload_sha256']==json.loads((destination/'input_sha256.json').read_text())
    if stage_path.read_bytes()!=stage_bytes:raise ValueError('fixed stage evidence changed during collection')
    with (destination/'accepted_stage.json').open('xb') as stream:stream.write(stage_bytes)
    write_new(destination/'archive_verification.json',verified)
    write_new(DATA/f'production_analysis_recovery_case{case}_{target.name}.json',dict(export=record,accepted_stage_sha256=stage_hash,export_pbs_completion_sha256=digest_file(destination/'export_pbs_completion.json'),recovered_worker_sha256=digest_file(destination/'recover_completed_tile_analysis.py'),verification_sha256=digest_file(destination/'archive_verification.json'),local_directory=str(destination.resolve()),scope='Export PBS terminal/exit0, accepted stage worker/script and archive identity/checksum integrity only; numerical trace audit remains separate.'))
    print(json.dumps(dict(verified=True,local_directory=str(destination))))


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--case',type=int,choices=range(4),required=True)
    parser.add_argument('--action',choices=('plan','check','stage','worker','collect'),default='plan')
    parser.add_argument('--tag',default='20261018-v1')
    args=parser.parse_args();target=target_root(args.case,args.tag)
    if args.action=='check':print(json.dumps(completion_gate(args.case)[2]))
    elif args.action=='worker':worker(args.case,target)
    elif args.action=='stage':stage(args.case,target)
    elif args.action=='collect':collect(args.case,target)
    else:print(json.dumps(dict(case=args.case,target=str(target),planned_groups=768,pbs_required=True,qsub_executed=False,warning='No timing guarantee. Source capacity is measured by the completion gate only after the analysis job is terminal. Owner verifies login controller termination and global <=2 nodes before qsub.')))


if __name__=='__main__':main()
