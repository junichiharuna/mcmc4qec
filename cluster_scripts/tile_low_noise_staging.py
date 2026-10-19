"""Seal a complete single-PBS sampling copy without changing execution provenance."""
import argparse
import hashlib
import importlib.util
import json
import math
import os
from pathlib import Path
import re
import shlex
import shutil
import socket
import subprocess
import sys
import time

import calibration as c
import tile_low_noise_analysis as a
import tile_low_noise_study as low

REPLICATES=192
WARNING='Byte-preserving copy and saved provenance only; no sampling, decoder replay, mixing, accuracy or coverage certification.'
ANALYSIS_NAMES={'analysis','analysis-submissions','analysis-partitions','partition-collection','preflight-analysis',
                'analysis_manifest.json','partition_analysis_manifest.json','analysis-execution-intent.json','analysis-summary.json'}


def require(ok,message):
    if not ok:raise ValueError(message)


def write_new(path,value):
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
    with path.open('xb') as stream:
        stream.write(c.canonical(value)+b'\n');stream.flush();os.fsync(stream.fileno())


def absolute(path):
    path=Path(path).absolute()
    require(path.resolve()==path,'symlinked or noncanonical root')
    return path


def regular(path):
    path=Path(path)
    require(path.resolve()==path and path.is_file(),'nonregular or symlinked input: '+str(path))
    return path


def tree(root,*,exclude=()):
    root=absolute(root);result={}
    for current,dirs,files in os.walk(root,followlinks=False):
        current=Path(current)
        for name in list(dirs):
            item=current/name;relative=item.relative_to(root)
            require(item.resolve()==item and not item.is_symlink(),'symlinked directory')
            if relative.parts[0] in exclude:dirs.remove(name)
        for name in files:
            item=regular(current/name);relative=item.relative_to(root)
            if relative.parts[0] not in exclude:result[relative.as_posix()]=item
    return result


def hashes(paths):return {name:c.file_hash(path) for name,path in paths.items()}


def json_snapshot(path):
    """Bind the exact bytes consumed, then reject a change during the read."""
    path=regular(path);data=path.read_bytes();digest=hashlib.sha256(data).hexdigest()
    require(c.file_hash(regular(path))==digest,'JSON evidence changed during snapshot read')
    return json.loads(data),digest


def software_snapshot():
    modules=(c,a,low,low.t,low.native,low.native.trace_audit,low.native.native_probe)
    paths={str(Path(module.__file__).resolve()):Path(module.__file__).resolve() for module in modules}
    paths[str(Path(__file__).resolve())]=Path(__file__).resolve()
    package=Path(low.qec.__file__).resolve().parent
    paths.update({str(path):path for path in package.rglob('*.py')})
    python=Path(sys.executable).resolve()
    profile=low.native.platform_inputs()['platform_profile']
    spec=importlib.util.find_spec('ldpc');require(spec is not None and spec.origin,'ldpc installation missing')
    native_root=Path(spec.origin).resolve().parent
    native={str(native_root/name):c.file_hash(native_root/name) for name in profile['native_ldpc_sha256']}
    require(list(native.values())==list(profile['native_ldpc_sha256'].values()),'native binary hashes differ from fixed profile')
    return dict(source_sha256=hashes(paths),python=str(python),python_sha256=c.file_hash(python),native_sha256=native,runtime=low.t.runtime())


def validate_binding(binding):
    require(isinstance(binding.get('source_sha256'),dict) and binding['source_sha256'],'accepted source pins required')
    require(isinstance(binding.get('source_job_id'),str) and re.fullmatch(r'\d+(?:\.[A-Za-z0-9_.-]+)?',binding['source_job_id']),'PBS job identity required')
    for name,digest in binding['source_sha256'].items():
        path=Path(name);require(path.is_absolute() and path.is_file() and c.file_hash(path)==digest,'accepted source changed')


def query_job(job):
    result=subprocess.run(['qstat','-x','-f','-F','json',job],capture_output=True,text=True,check=True,timeout=30)
    jobs=json.loads(result.stdout)['Jobs'];require(set(jobs)=={job},'PBS query identity differs')
    return {key:value for key,value in jobs[job].items() if key!='Variable_List'}


def metadata(root):return tree(root,exclude=('traces','anchors'))


def inspect_source(source,binding,job_query):
    source=absolute(source);validate_binding(binding)
    plan=a.read_production_plan(source)
    require(plan['purpose']=='low_noise_production' and plan['replicates']==REPLICATES,'full production cohort required')
    require(isinstance(plan.get('sources'),dict) and plan['sources'] and set(plan['sources'].values())<=set(binding['source_sha256'].values()),'sampling scientific sources missing from accepted binding')
    evidence=a.completed_phase_evidence(source,plan)
    require(sum(1 for _ in a.groups(plan))==4*REPLICATES,'group denominator differs')
    require(evidence['anchors']['tasks']==REPLICATES,'anchor denominator differs')
    receipt=json.loads(regular(source/'submission.json').read_bytes())
    intent=json.loads(regular(source/'submission-intent.json').read_bytes())
    require({key:value for key,value in receipt.items() if key!='job_id'}==intent,'original submission receipt differs')
    script=source/'low-noise.sh';job_id=binding['source_job_id']
    require(receipt['job_id']==job_id and receipt['command']==['qsub',str(script)] and receipt['manifest']==c.digest(plan)
            and receipt['script_sha256']==c.file_hash(regular(script)),'original absolute script/receipt binding differs')
    require(receipt['submit_source_sha256'] in binding['source_sha256'].values(),'original submitter source not pinned')
    pins=binding.get('input_sha256',{})
    require({'manifest.json','submission-intent.json','submission.json','low-noise.sh'}<=set(pins),'independent source preparation/submission pins required')
    for name,digest in pins.items():
        require(Path(name).name==name and c.file_hash(regular(source/name))==digest,'independent source preparation/submission evidence changed')
    for phase in ('sample','anchors'):
        require(json.loads((source/(phase+'-execution-intent.json')).read_bytes())['pbs_job_id']==job_id,'single-PBS phase identity differs')
    job=job_query(job_id)
    require(job.get('job_state')=='F' and type(job.get('Exit_status')) is int and job.get('Submit_arguments')==str(script),'original PBS not terminal or wrong script')
    require(job.get('run_count')==1 and isinstance(job.get('exec_host'),str),'original PBS restart/host evidence differs')
    hosts={part.split('/')[0] for part in job['exec_host'].split('+')}
    for phase in ('sample','anchors'):
        require(json.loads((source/(phase+'-execution-intent.json')).read_bytes())['hostname'] in hosts,'original phase hostname differs from PBS execution host')
    failures={phase:evidence[phase]['failed'] for phase in ('sample','anchors')}
    require(job['Exit_status']==0 or sum(failures.values())>0,'nonzero PBS exit lacks recorded task failure')
    kind='normal_exit0' if job['Exit_status']==0 and sum(failures.values())==0 else 'complete_recorded_failure'
    names=metadata(source)
    require(not any(Path(name).parts[0] in ANALYSIS_NAMES or Path(name).parts[0]=='.staging' for name in names),'source already contains analysis or staging outputs')
    return dict(sampling_manifest=plan,completed_phase_evidence=evidence,metadata_sha256=hashes(names),
                source_job_id=job_id,source_exit_status=job['Exit_status'],pbs=job,completion_kind=kind,recorded_failures=failures)


def stable(value):return {key:item for key,item in value.items() if key!='pbs'}


def prepare(control_root,source_root,destination,analysis_bundle,binding,*,job_query=query_job):
    control,source,target,bundle=map(absolute,(control_root,source_root,destination,analysis_bundle))
    require(target!=bundle/'runs' and target.is_relative_to(bundle/'runs'),'destination must be inside analysis bundle/runs')
    for i,first in enumerate((control,source,target)):
        for second in (control,source,target)[i+1:]:require(not first.is_relative_to(second) and not second.is_relative_to(first),'roots must be independent')
    require(not control.exists() and not target.exists(),'fresh control and destination required')
    evidence=inspect_source(source,binding,job_query)
    value=dict(schema=1,purpose='sealed_single_pbs_sampling_copy',source_root=str(source),destination=str(target),analysis_bundle=str(bundle),
               control_root=str(control),binding=binding,software=software_snapshot(),source=evidence,warning=WARNING)
    require(stable(inspect_source(source,binding,job_query))==stable(evidence),'source changed during preparation')
    control.mkdir(parents=True);write_new(control/'plan.json',value);return value


def census(source,plan):
    files=tree(source);raw={};failures={};sampling=plan['sampling_manifest']
    for phase,directory in (('sample','traces'),('anchors','anchors')):
        summary=json.loads((source/(phase+'-summary.json')).read_bytes());rows={tuple(row['task']):row for row in summary['records']}
        failed=0;expected=set()
        for task in low.tasks(sampling,phase):
            stem=directory+'/'+c.task_id(task)
            for ext in ('.json','.npz','.done.json'):expected.add(stem+ext)
            marker=json.loads(regular(source/(stem+'.done.json')).read_bytes())
            require(marker.get('identity')==dict(manifest=c.digest(sampling),task=list(task)) and set(marker.get('sha256',{}))=={'.json','.npz'},'raw marker identity/checksum census differs')
            for ext,digest in marker['sha256'].items():require(c.file_hash(regular(source/(stem+ext)))==digest,'raw payload changed')
            record=json.loads(regular(source/(stem+'.json')).read_bytes())
            require({key:record.get(key) for key in rows[task]}==rows[task] and record['status'] in ('ok','failed'),'raw record differs from complete summary')
            if record['status']=='failed':require(bool(record.get('error')),'recorded failure reason missing');failed+=1
        require({name for name in files if name.startswith(directory+'/')}==expected,'raw task census differs')
        require(failed==summary['failed'],'recorded failure count differs')
        raw.update({name:files[name] for name in expected});failures[phase]=failed
    require({name for name in files if name not in raw}==set(plan['metadata_sha256']),'metadata census changed')
    require(hashes({name:files[name] for name in plan['metadata_sha256']})==plan['metadata_sha256'],'metadata changed')
    return files


def copy_file(source,destination):
    destination.parent.mkdir(parents=True,exist_ok=True)
    with source.open('rb') as incoming,destination.open('xb') as outgoing:shutil.copyfileobj(incoming,outgoing,1024*1024)


def copy_execution(control,plan_hash,job_id,*,terminal,job_query):
    names=('stage.sh','submission-intent.json','submission.json')
    before={name:c.file_hash(regular(control/name)) for name in names}
    receipt=json.loads((control/'submission.json').read_bytes());intent=json.loads((control/'submission-intent.json').read_bytes())
    command=['qsub',str(control/'stage.sh')]
    require({key:value for key,value in receipt.items() if key!='job_id'}==intent and receipt.get('job_id')==job_id
            and receipt.get('command')==command and receipt.get('plan_sha256')==plan_hash
            and receipt.get('script_sha256')==before['stage.sh'],'copy submission receipt/script/plan differs')
    job=job_query(job_id)
    require(job.get('Submit_arguments')==command[1],'copy PBS script differs')
    if terminal:require(job.get('job_state')=='F' and job.get('Exit_status')==0,'copy PBS must finish F/exit0 before downstream use')
    else:require(job.get('job_state') in ('R','E','F') and (job.get('job_state')!='F' or job.get('Exit_status')==0),'copy allocation not running or failed')
    require(before=={name:c.file_hash(regular(control/name)) for name in names},'copy submission evidence changed')
    return dict(files_sha256=before,command=command,pbs_job_id=job_id,pbs=job)


def run(control_root,*,job_query=query_job):
    control=absolute(control_root);plan_path=regular(control/'plan.json');plan,plan_hash=json_snapshot(plan_path)
    source,target=map(absolute,(plan['source_root'],plan['destination']))
    job=os.environ.get('PBS_JOBID');require(job and re.fullmatch(r'\d+(?:\.[A-Za-z0-9_.-]+)?',job),'PBS allocation required')
    require(str(control)==plan['control_root'] and not target.exists(),'fresh destination and fixed control required')
    require(not (control/'execution-intent.json').exists() and not (control/'summary.json').exists(),'existing staging intent; no automatic retry')
    write_new(control/'execution-intent.json',dict(plan_sha256=plan_hash,pbs_job_id=job,hostname=socket.gethostname()))
    started=time.perf_counter()
    copy_before=copy_execution(control,plan_hash,job,terminal=False,job_query=job_query)
    require(software_snapshot()==plan['software'],'copy runtime/source/native/Python changed')
    before_evidence=inspect_source(source,plan['binding'],job_query)
    require(stable(before_evidence)==stable(plan['source']),'prepared source evidence changed')
    files=census(source,before_evidence);before=hashes(files);sizes={name:path.stat().st_size for name,path in files.items()}
    target.mkdir(parents=True,exist_ok=False)
    for name,path in sorted(files.items()):copy_file(path,target/name)
    copied=tree(target);require(set(copied)==set(files) and hashes(copied)==before,'copied full file census/hash differs')
    require({name:path.stat().st_size for name,path in copied.items()}==sizes,'copied sizes differ')
    after=census(source,before_evidence)
    require(set(after)==set(files) and hashes(after)==before,'source changed during copy')
    require(stable(inspect_source(source,plan['binding'],job_query))==stable(before_evidence) and software_snapshot()==plan['software'],'terminal provenance changed')
    require(c.file_hash(plan_path)==plan_hash and hashes(tree(target))==before,'plan or copied payload changed before seal')
    require(stable(copy_execution(control,plan_hash,job,terminal=False,job_query=job_query))==stable(copy_before),'copy submission changed before seal')
    sampling=plan['source']['sampling_manifest'];evidence=plan['source']['completed_phase_evidence']
    result=dict(original_source_root=str(source),destination=str(target),copy_pbs_job_id=job,original_pbs=before_evidence['pbs'],
        original_job_id=before_evidence['source_job_id'],original_exit_status=before_evidence['source_exit_status'],completion_kind=before_evidence['completion_kind'],
        recorded_failures=before_evidence['recorded_failures'],groups=4*sampling['replicates'],anchors=evidence['anchors']['tasks'],sample_tasks=evidence['sample']['tasks'],
        source_sha256=before,source_bytes=sizes,source_unchanged=True,copy_hashes_verified=True,elapsed_seconds=time.perf_counter()-started,
        plan_sha256=plan_hash,copy_submission=copy_before,scientific_recalculation=False,warning=WARNING)
    write_new(target/'.staging/plan.json',plan);write_new(target/'.staging/summary.json',result)
    write_new(control/'summary.json',result)
    seal=dict(plan_sha256=c.file_hash(target/'.staging/plan.json'),summary_sha256=c.file_hash(target/'.staging/summary.json'),sealed=True)
    write_new(target/'.staging/seal.json',seal)
    return result


def _read_staged(destination,*,full,job_query=None):
    if full:require(bool(os.environ.get('PBS_JOBID')),'full staged-payload scan requires PBS allocation')
    job_query=query_job if job_query is None else job_query
    target=absolute(destination)
    seal,seal_hash=json_snapshot(target/'.staging/seal.json')
    require(seal.get('sealed') is True,'copy seal absent')
    for name in ('plan','summary'):require(c.file_hash(regular(target/f'.staging/{name}.json'))==seal[name+'_sha256'],'staging sidecar changed')
    plan=json.loads((target/'.staging/plan.json').read_bytes());summary=json.loads((target/'.staging/summary.json').read_bytes())
    require(plan['destination']==str(target)==summary['destination'] and summary['plan_sha256']==seal['plan_sha256']
            and summary['source_unchanged'] is True and summary['copy_hashes_verified'] is True and summary['scientific_recalculation'] is False,'staging identity differs')
    control=absolute(plan['control_root'])
    require(c.file_hash(regular(control/'plan.json'))==seal['plan_sha256'] and c.file_hash(regular(control/'summary.json'))==seal['summary_sha256'],'independent control record changed')
    execution=regular(control/'execution-intent.json');execution_hash=c.file_hash(execution);intent=json.loads(execution.read_bytes())
    require(intent['plan_sha256']==seal['plan_sha256'] and intent['pbs_job_id']==summary['copy_pbs_job_id'],'copy execution identity differs')
    copied=copy_execution(control,seal['plan_sha256'],summary['copy_pbs_job_id'],terminal=True,job_query=job_query)
    require(stable(copied)==stable(summary['copy_submission']),'copy submission changed after sealing')
    validate_binding(plan['binding']);require(software_snapshot()==plan['software'],'staging reader runtime/source/native changed')
    excluded=('.staging',*ANALYSIS_NAMES) if full else ('.staging','traces','anchors',*ANALYSIS_NAMES)
    expected=summary['source_sha256'] if full else plan['source']['metadata_sha256']
    files=tree(target,exclude=excluded)
    require(hashes(files)==expected and {name:path.stat().st_size for name,path in files.items()}=={name:summary['source_bytes'][name] for name in expected},'staged payload/census differs')
    sampling=a.read_production_plan(target)
    require(c.canonical(sampling)==c.canonical(plan['source']['sampling_manifest']) and a.completed_phase_evidence(target,sampling)==plan['source']['completed_phase_evidence'],'copied completed phase evidence differs')
    require(hashes(tree(target,exclude=excluded))==expected,'staged input changed during read')
    validate_binding(plan['binding']);require(software_snapshot()==plan['software'],'staging runtime changed during read')
    require(c.file_hash(regular(control/'plan.json'))==seal['plan_sha256'] and c.file_hash(regular(control/'summary.json'))==seal['summary_sha256'] and c.file_hash(regular(execution))==execution_hash,'independent control evidence changed during read')
    require(stable(copy_execution(control,seal['plan_sha256'],summary['copy_pbs_job_id'],terminal=True,job_query=job_query))==stable(copied),'copy PBS/submission changed during read')
    require(c.file_hash(target/'.staging/seal.json')==seal_hash and all(c.file_hash(target/f'.staging/{name}.json')==seal[name+'_sha256'] for name in ('plan','summary')),'staging evidence changed during read')
    return dict(sealed=True,seal_sha256=seal_hash,summary_sha256=seal['summary_sha256'],original_source_root=plan['source_root'],original_job_id=summary['original_job_id'],
                original_exit_status=summary['original_exit_status'],completion_kind=summary['completion_kind'],groups=summary['groups'],anchors=summary['anchors'],sample_tasks=summary['sample_tasks'],
                copy_pbs_job_id=summary['copy_pbs_job_id'],copy_exit_status=0,copy_elapsed_seconds=summary['elapsed_seconds'],
                copy_submission_sha256=copied['files_sha256']['submission.json'],current_payloads_rehashed=full,warning=WARNING)


def read_staged(destination,*,job_query=None):
    """Full raw-payload verification; compute allocation required before any I/O."""
    return _read_staged(destination,full=True,job_query=job_query)


def read_staged_provenance(destination,*,job_query=None):
    """Login-safe metadata gate; explicitly does not rehash current raw payloads."""
    return _read_staged(destination,full=False,job_query=job_query)


def guarded(destination,operation):
    before=read_staged(destination);result=operation();require(read_staged(destination)==before,'staging seal changed across downstream operation');return result


def guarded_metadata(destination,operation):
    before=read_staged_provenance(destination);result=operation();require(read_staged_provenance(destination)==before,'staging metadata changed across downstream operation');return result


def plan_analysis(destination,capacity_root):
    import tile_low_noise_analysis_partitions as partitions
    return guarded_metadata(destination,lambda:partitions.create_plan(destination,capacity_root))


def submit_analysis(bundle,destination,index,**kwargs):
    """Prepare the actual guarded script/record only; parent alone invokes qsub."""
    require(not kwargs,'staging prepares scripts only; parent must submit once')
    return prepare_downstream(bundle,destination,'analysis',index=index)


def plan_trace_audit(destination,audit_root,*,capacity,workers):
    import tile_low_noise_trace_audit_run as audit
    return guarded_metadata(destination,lambda:audit.prepare(audit_root,destination,capacity=capacity,workers=workers))


def submit_trace_audit(bundle,destination,audit_root,**kwargs):
    """Prepare the actual guarded audit script/record without submitting."""
    capacity_root=kwargs.pop('capacity_root',None);require(not kwargs,'staging prepares scripts only; parent must submit once')
    return prepare_downstream(bundle,destination,'trace-audit',audit_root=audit_root,capacity_root=capacity_root)


def render_script(bundle,destination,script,resource,arguments):
    helper=Path(__file__).resolve();python=Path(bundle)/'venv/bin/python'
    require(not any(char.isspace() for path in (bundle,destination,script,helper) for char in str(path)),'PBS paths must not contain whitespace')
    invocation=shlex.join([str(python),str(helper),*arguments,'--destination',str(destination)])
    return f'''#!/bin/bash
#PBS -N m4q_staged
#PBS -q workq
#PBS -l select=1:ncpus={resource['cpus']}:mem={resource['memory_gb']}gb
#PBS -l walltime={resource['walltime']}
#PBS -o {script.parent}/{script.stem}.out
#PBS -e {script.parent}/{script.stem}.err
set -euo pipefail
: "${{PBS_JOBID:?submit with qsub}}"
cd {shlex.quote(str(bundle))}
export PYTHONPATH={shlex.quote(str(Path(bundle)/'src')+':'+str(Path(bundle)/'cluster_scripts'))}
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 NUMEXPR_NUM_THREADS=1 PYTHONHASHSEED=0 PYTHONDONTWRITEBYTECODE=1
{invocation}
'''


def budget_resources(baseline,origin,*,initial_ceiling=False):
    """Estimate guarded I/O headroom from the already measured copy, not a bound."""
    measured=origin.get('copy_elapsed_seconds')
    require(origin.get('sealed') is True and origin.get('copy_exit_status')==0 and origin.get('copy_pbs_job_id')
            and isinstance(measured,(int,float)) and not isinstance(measured,bool) and math.isfinite(measured) and measured>0,
            'completed measured copy required before downstream resources are ready')
    h,m,s=(int(value) for value in baseline['walltime'].split(':'));base=h*3600+m*60+s
    require(0<base<=86400 and baseline.get('wall_seconds',base)==base,'baseline walltime differs')
    passes,factor,metadata=4,2,300
    extra=max(1800,math.ceil((passes*factor*measured+metadata)/1800)*1800)
    total=base if initial_ceiling else base+extra
    require(total<=86400 and (not initial_ceiling or extra<base),'staging I/O budget exceeds 24h or consumes the initial ceiling; prepare a new allocation')
    result=dict(baseline,wall_seconds=total,walltime=f'{total//3600:02d}:{total%3600//60:02d}:00')
    evidence=dict(copy_summary_sha256=origin['summary_sha256'],copy_pbs_job_id=origin['copy_pbs_job_id'],copy_elapsed_seconds=measured,
        full_reader_calls=2,raw_hash_passes_per_reader=2,additional_raw_hash_passes=passes,copy_time_proxy_factor=factor,
        metadata_allowance_seconds=metadata,rounded_staging_budget_seconds=extra,baseline_wall_seconds=base,total_wall_seconds=total,
        initial_ceiling=initial_ceiling,baseline_reserved_seconds=base-extra if initial_ceiling else base,
        method='Measured whole-copy elapsed time reused as a per-pass proxy with a factor of two; rounded upward to 30 minutes.',
        warning='Resource estimate only. Copy elapsed is not a bound on later scans; storage load may change. No completion guarantee or scientific accuracy claim.')
    return result,evidence


def prepare_downstream(bundle,destination,phase,*,index=None,audit_root=None,capacity_root=None):
    bundle,destination=map(absolute,(bundle,destination))
    require(not any(char.isspace() for path in (bundle,destination,audit_root or '') for char in str(path)),'PBS paths must not contain whitespace')
    require(destination!=bundle/'runs' and destination.is_relative_to(bundle/'runs'),'staged analysis root must lie inside bundle/runs')
    before=read_staged_provenance(destination)
    if phase=='analysis':
        import submit_tile_low_noise_analysis_partitions as submitter
        wrapper=submitter.checked_plan(destination,index);folder=submitter.require_fresh(destination,wrapper,index)
        fixed=wrapper['resources'];part=fixed['partitions'][index]
        resource=dict(cpus=fixed['cpus'],memory_gb=fixed['memory_gb'],workers=fixed['workers'],wall_seconds=part['wall_seconds'],walltime=part['walltime'],requested_nodes=1,max_nodes=2)
        script=folder/'partition.sh';arguments=['run-analysis','--partition',str(index)]
        record=dict(partition=index,partition_manifest=c.digest(wrapper),manifest=c.digest(wrapper['production']),resource=resource,
                    bundle_binding=submitter.bundle_binding(bundle,wrapper))
    elif phase=='trace-audit':
        import submit_tile_low_noise_trace_audit as submitter
        audit_root=absolute(audit_root)
        require(audit_root!=bundle/'runs' and audit_root.is_relative_to(bundle/'runs') and not audit_root.is_relative_to(destination) and not destination.is_relative_to(audit_root),'independent audit root inside bundle/runs required')
        submitter.require_fresh(audit_root)
        plan,sampling,resource,jobs=submitter.checked_plan(audit_root,destination,capacity_root)
        script=audit_root/'trace-audit.sh';arguments=['run-trace-audit','--audit-root',str(audit_root)]
        record=dict(manifest=c.digest(plan),resource=resource,bundle_binding=submitter.bundle_binding(bundle,plan),sampling_root=str(destination),
                    capacity_root=None if capacity_root is None else str(capacity_root),source_pbs_jobs=jobs,
                    resource_basis='initial_ceiling' if capacity_root is None else 'measured_capacity')
    else:raise ValueError('unknown downstream phase')
    baseline=dict(resource)
    resource,budget=budget_resources(baseline,before,initial_ceiling=phase=='trace-audit' and capacity_root is None)
    record.update(resource=resource,baseline_resource=baseline,staging_budget=budget,submission_ready=True)
    require(not script.exists(),'fresh guarded PBS script required')
    script.parent.mkdir(parents=True,exist_ok=True)
    with script.open('xb') as stream:stream.write(render_script(bundle,destination,script,resource,arguments).encode())
    record.update(command=['qsub',str(script)],script_sha256=c.file_hash(script),submit_source_sha256=c.file_hash(__file__),
                  staging_origin=before,staging_helper=str(Path(__file__).resolve()),compute_full_payload_gate=True)
    require(read_staged_provenance(destination)==before,'staging metadata changed during script preparation')
    write_new(script.parent/'staging-submission-plan.json',record)
    return record


def run_analysis(destination,index):
    import tile_low_noise_analysis_partitions as partitions
    return guarded(destination,lambda:partitions.run_partition(destination,partitions.read_plan(destination),index))


def run_trace_audit(destination,audit_root):
    import tile_low_noise_trace_audit_run as audit
    return guarded(destination,lambda:audit.run(audit_root,destination))


def read_staged_audited_collection(destination,audit_root):
    import tile_low_noise_audited_collection as collection
    before=read_staged(destination)
    sampling,rows,evidence=collection.read_audited_collection(destination,audit_root)
    require(read_staged(destination)==before,'staging evidence changed across final collection')
    return sampling,rows,dict(evidence,staging_origin=before)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action',choices=('prepare','run','verify','verify-metadata','plan-analysis','plan-trace-audit','prepare-analysis-job','prepare-trace-audit-job','run-analysis','run-trace-audit'))
    for name in ('control-root','source-root','destination','analysis-bundle','binding','capacity-root','audit-root'):parser.add_argument('--'+name,type=Path)
    parser.add_argument('--capacity',action='store_true');parser.add_argument('--workers',type=int,default=8)
    parser.add_argument('--partition',type=int)
    args=parser.parse_args()
    if args.action=='prepare':value=prepare(args.control_root,args.source_root,args.destination,args.analysis_bundle,json.loads(args.binding.read_bytes()))
    elif args.action=='run':value=run(args.control_root)
    elif args.action=='verify':value=read_staged(args.destination)
    elif args.action=='verify-metadata':value=read_staged_provenance(args.destination)
    elif args.action=='plan-analysis':value=plan_analysis(args.destination,args.capacity_root)
    elif args.action=='plan-trace-audit':value=plan_trace_audit(args.destination,args.audit_root,capacity=args.capacity,workers=args.workers)
    elif args.action=='prepare-analysis-job':value=submit_analysis(args.analysis_bundle,args.destination,args.partition)
    elif args.action=='prepare-trace-audit-job':value=submit_trace_audit(args.analysis_bundle,args.destination,args.audit_root,capacity_root=args.capacity_root)
    elif args.action=='run-analysis':value=run_analysis(args.destination,args.partition)
    else:value=run_trace_audit(args.destination,args.audit_root)
    print(json.dumps(value))


if __name__=='__main__':main()
