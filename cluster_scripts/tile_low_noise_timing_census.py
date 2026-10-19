"""One-shot combined seed census bridge; old engines and scientific plans stay fixed.

No-op selections never run a pilot or authorize a timing job. A successful full
census needs a separate terminal seal before becoming a timing descriptor.
"""
import argparse
import ast
from copy import deepcopy
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
import tempfile
import time
from types import SimpleNamespace

BASE_TOTAL=3963562
BASE_SECONDS=1504.8813167447224
BASE_RESULT_SHA='b61653309ca8e87ea315ab8dd46f05c1e4ad8e2a4fa642a67da6d590dcaa4116'
BASE_MANIFEST_SHA='898647148b32c4a50151f703ac2d205af42bd4243dac4ac67ac2c1850b65c316'
BASE_VERIFICATION_SHA='a480854ea51d32056f6baa72f0720e560481e63ab1681470d52fe4e51ace214d'
WARNING='Finite planned allocations only. No mathematical stream-independence proof or executed-sampling validation.'
THREADS={key:'1' for key in ('OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS')}


def require(value,message):
    if not value:raise ValueError(message)


def canonical(value):return json.dumps(value,sort_keys=True,separators=(',',':'),allow_nan=False).encode()
def digest(value):return hashlib.sha256(canonical(value)).hexdigest()
def file_hash(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def hash_value(value):
    require(isinstance(value,str) and re.fullmatch(r'[0-9a-f]{64}',value),'SHA256 required')
    return value


class Proof:
    def __init__(self):self.files={}
    def track(self,path,expected=None):
        path=Path(path).absolute();raw=path.read_bytes();sha=hashlib.sha256(raw).hexdigest()
        require(expected is None or sha==hash_value(expected),'external input bytes changed')
        value=(str(path.resolve()),sha)
        require(self.files.setdefault(str(path),value)==value,'input changed between reads')
        return raw
    def pin(self,pin):
        require(set(pin)=={'path','sha256'} and Path(pin['path']).is_absolute(),'absolute pinned descriptor required')
        return json.loads(self.track(pin['path'],pin['sha256']))
    def finish(self):
        for path,(target,sha) in self.files.items():
            require(str(Path(path).resolve())==target and file_hash(path)==sha,'input resolution or bytes changed')


def save_new(path,value):
    with Path(path).open('xb') as stream:
        stream.write(canonical(value)+b'\n');stream.flush();os.fsync(stream.fileno())


def modules():
    # CLI callers reach here only after the externally pinned preimport gate.
    import calibration as c
    import tile_study as t
    import tile_seed_audit as old
    import tile_low_noise_timing_plan as p
    import tile_low_noise_timing_seed_audit as a
    import tile_low_noise_timing_execution as e
    return SimpleNamespace(c=c,t=t,old=old,p=p,a=a,e=e)


def source_hashes():
    pending=[Path(__file__).resolve()];found={}
    while pending:
        path=pending.pop()
        if str(path) in found:continue
        found[str(path)]=file_hash(path)
        for node in ast.walk(ast.parse(path.read_text(encoding='utf-8-sig'))):
            names=([v.name.split('.')[0] for v in node.names] if isinstance(node,ast.Import)
                else [node.module.split('.')[0]] if isinstance(node,ast.ImportFrom) and node.module else [])
            for name in names:
                spec=importlib.util.find_spec(name)
                if spec and spec.origin and Path(spec.origin).parent.name=='cluster_scripts':pending.append(Path(spec.origin).resolve())
    return found


def verify_files(mapping):
    require(isinstance(mapping,dict),'fixed file map required')
    for path,sha in mapping.items():
        require(Path(path).is_absolute() and Path(path).resolve()==Path(path),'canonical fixed source/input path required')
        require(file_hash(path)==hash_value(sha),'fixed source/input changed')


def preimport(config):
    require(config['source_sha256'] and config['core_sha256'],'nonempty fixed code maps required')
    verify_files(config['source_sha256']);verify_files(config['core_sha256'])
    require(config['source_sha256'].get(str(Path(__file__).resolve()))==file_hash(__file__),'bridge not in authority source closure')
    require(config['python_path']==str(Path(sys.executable).absolute()) and file_hash(sys.executable)==config['python_sha256'],'Python invocation or binary differs')
    require(config['pythonpath']==os.environ.get('PYTHONPATH',''),'explicit import search path differs')
    spec=importlib.util.find_spec('mcmc4qec')
    require(spec is not None and spec.origin is not None,'missing core package')
    root=Path(spec.origin).resolve().parent
    require(config['core_sha256']=={str(path):file_hash(path) for path in sorted(root.rglob('*.py'))},'complete core package census differs')


def allocation_state(bundle,baseline_result_sha256):
    selected=sum(row['status']=='selected' for row in bundle['selection']['rows'])
    number=sum(plan['planned_seed_entries'] for plan in bundle['plans'].values())
    require(type(number) is int and number>=0,'allocation count required')
    require(selected>0 or number==0,'allocations without selected rows')
    require(number>0 or selected==0,'selected rows with zero allocation require explicit planning review')
    return dict(status='ready' if number else 'not_required_no_allocations',selected_rows=selected,new_allocations=number,
        scientific_bundle_digest=digest(bundle),registry_digest=digest(bundle['registry']),selection_sha256=bundle['selection_sha256'],
        baseline_result_sha256=hash_value(baseline_result_sha256),baseline_verified_namespaces=56,
        new_namespaces_audited=False,formal_census_descriptor=None)


def relocation_binding(previous,current,mapping):
    require(set(previous)==set(current) and canonical({k:v for k,v in previous.items() if k!='source_sha256'})==
        canonical({k:v for k,v in current.items() if k!='source_sha256'}),'legacy catalog changed beyond source paths')
    old=previous['source_sha256'];new=current['source_sha256']
    require(set(mapping)==set(old) and len(set(mapping.values()))==len(mapping) and set(mapping.values())==set(new),'exact one-to-one producer mapping required')
    verify_files(old);verify_files(new)
    require(all(old[path]==new[target] for path,target in mapping.items()),'producer source bytes differ')
    return dict(previous_evidence_digest=digest(previous),current_evidence_digest=digest(current),
        source_relocation=mapping,previous_source_sha256=old,current_source_sha256=new,same_source_bytes=True)


def resources(pilot,total,rss,sqlite_bytes):
    values=(pilot['seconds'],pilot['checked_entries'],total,rss,sqlite_bytes)
    require(all(type(v) in (int,float) and math.isfinite(v) and v>0 for v in values),'positive finite pilot measurements required')
    require(type(total) is int and type(pilot['checked_entries']) is int,'integer planned/pilot counts required')
    prediction=max(2*pilot['seconds']*total/pilot['checked_entries'],1.5*BASE_SECONDS*total/BASE_TOTAL)
    seconds=300*math.ceil((prediction+300)/300);memory=max(2,math.ceil(1.5*rss/1024+1))
    require(seconds<=7200 and memory<=4,'measured census exceeds two-hour / four-GiB ceiling')
    return dict(cpus=1,workers=1,memory_gb=memory,wall_seconds=seconds,
        walltime=f'{seconds//3600:02}:{seconds%3600//60:02}:{seconds%60:02}',requested_nodes=1,max_nodes=2,
        predicted_seconds=prediction,measured_peak_rss_mb=rss,measured_sqlite_bytes=sqlite_bytes,
        disk_required_bytes=max(4*1024**3,math.ceil(2*sqlite_bytes*total/pilot['checked_entries']+1024**3)),
        warning='Pilot and prior full-runtime extrapolation, not a completion guarantee.')


def inspect_inputs(config_path,expected_sha256):
    proof=Proof();pin=dict(path=str(Path(config_path).absolute()),sha256=hash_value(expected_sha256));config=proof.pin(pin)
    require(config.get('purpose')=='low_noise_timing_census_input' and config.get('schema')==1,'fixed census input schema required')
    preimport(config)
    require(config['source_sha256']==source_hashes(),'actual import source closure differs')
    m=modules()
    selection=proof.pin(config['selection']);bundle=proof.pin(config['scientific_bundle'])
    require(digest(selection)==digest(bundle['selection']) and config['selection']['sha256']==bundle['selection_sha256'],'selection bytes/bundle differ')
    m.p.validate_plans(bundle,expected_registry_digest=config['registry_digest'])
    for key,sha in (('baseline_manifest',BASE_MANIFEST_SHA),('baseline_result',BASE_RESULT_SHA),('baseline_verification',BASE_VERIFICATION_SHA)):
        require(config[key]['sha256']==sha,'accepted baseline external pin differs')
    oldplan=proof.pin(config['baseline_manifest']);oldoutput=proof.pin(config['baseline_result']);verified=proof.pin(config['baseline_verification'])
    require(verified['job_id']=='265253.node-PRISM' and verified['source_runtime_input_bindings_verified'] is True
        and verified['submission_completion_pbs_verified'] is True and verified['result_sha256']==BASE_RESULT_SHA,'accepted baseline completion differs')
    oldevidence=oldoutput['evidence'];full=oldoutput['full']
    require(oldplan['audit_evidence']==oldevidence and len(oldevidence['planned_counts'])==56 and oldevidence['planned_total']==BASE_TOTAL,'exact old catalog required')
    m.a._full_result(full,BASE_TOTAL,full['checked_counts'],8448)
    require(sum(full['checked_counts'].values())==BASE_TOTAL,'old role census differs')
    # Pin all legacy sources, inputs and native fixtures; never rewrite their paths.
    for label in ('source_sha256','input_sha256'):
        for path,sha in oldevidence[label].items():proof.track(path,sha)
    for label in ('seed_source_sha256','input_sha256'):
        for path,sha in oldplan['binding'][label].items():proof.track(path,sha)
    profile=proof.pin(config['profile']);fixture=proof.pin(config['fixture'])
    require(profile['fixture']==digest(fixture),'profile/fixture identity differs')
    runtime=m.t.runtime();baseline=oldplan['binding']['baseline_runtime']
    require(all(baseline.get(k)==v for k,v in runtime.items()),'legacy production runtime differs')
    for path,sha in {**config['source_sha256'],**config['core_sha256']}.items():proof.track(path,sha)
    proof.finish()
    sources={**config['source_sha256'],**oldevidence['source_sha256'],**oldplan['binding']['seed_source_sha256'],**config['core_sha256']}
    require(all(proof.files[path][1]==sha for path,sha in sources.items()),'authority source collision')
    return dict(config=config,config_pin=pin,bundle=bundle,baseline_manifest=oldplan,baseline_output=oldoutput,
        state=allocation_state(bundle,BASE_RESULT_SHA),runtime=runtime,profile=profile,fixture=fixture,
        native_input_digests=dict(profile=digest(profile),fixture=digest(fixture)),
        input_sha256={path:value[1] for path,value in proof.files.items()},source_sha256=sources)


def build_catalog(context):
    m=modules();oldplan=context['baseline_manifest'];old=context['baseline_output']
    data=Path(oldplan['bundle'])/'docs/wp/data_tile_validation_2026-10-17'
    paths=[row['path'] for row in oldplan['bar_timing_manifests']]
    require(len(paths)==8 and len(set(paths))==8,'all eight prior BAR manifests required')
    factories,evidence=m.old.catalog(data,bar_timing_manifests=paths)
    relocation=relocation_binding(old['evidence'],evidence,context['config']['source_relocation'])
    combined,proof=m.a.extend_catalog(factories,evidence,context['bundle'],baseline_evidence_sha256=digest(evidence),
        baseline_result=old['full'],baseline_result_sha256=digest(old['full']),expected_registry_digest=context['config']['registry_digest'])
    require(proof['planned_total']==BASE_TOTAL+context['state']['new_allocations'],'independent combined total differs')
    return combined,proof,relocation


def census_stream(factories,total,root,*,limit=None):
    m=modules();started=time.perf_counter();cpu=time.process_time()
    with tempfile.TemporaryDirectory(prefix='census-',dir=root) as temporary:
        database=Path(temporary)/'seeds.sqlite'
        result=m.old.census(m.old.round_robin([factory() for factory in factories.values()]),total,database,limit=limit)
        size=database.stat().st_size
    return result,dict(wall_seconds=time.perf_counter()-started,cpu_seconds=time.process_time()-cpu,
        peak_rss_mb=m.c.peak_rss_mb(),sqlite_bytes=size,sqlite_retained=False)


def prepare(root,config_path,expected_sha256):
    root=Path(root).absolute();require(not root.exists() and not root.is_symlink(),'fresh immutable run root required')
    context=inspect_inputs(config_path,expected_sha256)
    require(not any(Path(path).resolve().is_relative_to(root.resolve()) or root.resolve().is_relative_to(Path(path).resolve())
        for path in context['input_sha256']),'run root overlaps fixed inputs')
    state=context['state']
    value=dict(schema=1,purpose='low_noise_timing_census',**state,root=str(root),
        config_pin=dict(path=str(Path(config_path).absolute()),sha256=expected_sha256),runtime=context['runtime'],
        input_sha256=context['input_sha256'],source_sha256=context['source_sha256'],native_input_digests=context['native_input_digests'])
    if state['status']=='not_required_no_allocations':
        root.mkdir(parents=True,exist_ok=False);save_new(root/'manifest.json',value);return value
    bundle=Path(context['config']['bundle']).resolve()
    require(root.resolve()==root and root.is_relative_to(bundle/'runs') and root!=bundle/'runs','output must be inside new bundle/runs')
    require(Path(__file__).resolve()==bundle/'cluster_scripts/tile_low_noise_timing_census.py','bridge must use its fixed bundle source')
    factories,catalog,relocation=build_catalog(context)
    root.mkdir(parents=True,exist_ok=False)
    try:
        pilot,measure=census_stream(factories,catalog['planned_total'],root,limit=1000)
        require(pilot['unexpected_collisions']==0,'pilot collision')
        res=resources(pilot,catalog['planned_total'],measure['peak_rss_mb'],measure['sqlite_bytes'])
        require(shutil.disk_usage(root).free>=res['disk_required_bytes'],'insufficient census scratch')
        verify_files(context['input_sha256']);verify_files(context['source_sha256'])
        value.update(bundle=str(bundle),resource=res,pilot=pilot,pilot_measurement=measure,
            catalog_evidence_digest=digest(catalog),relocation=relocation,
            python_path=context['config']['python_path'],pythonpath=context['config']['pythonpath'])
        save_new(root/'catalog.json',catalog);save_new(root/'manifest.json',value)
    except Exception as error:
        save_new(root/'planning-failure.json',dict(error=repr(error),status='failed',root_reusable=False));raise
    return value


def read_plan(root):
    root=Path(root).absolute();require(root.resolve()==root,'canonical run root required')
    path=root/'manifest.json';require(not path.is_symlink(),'manifest symlink forbidden')
    value=json.loads(path.read_bytes());pin=value['config_pin'];context=inspect_inputs(pin['path'],pin['sha256'])
    require(value['purpose']=='low_noise_timing_census' and value['schema']==1 and value['root']==str(root),'fixed plan identity differs')
    for key,val in context['state'].items():require(value.get(key)==val,'allocation/no-op identity differs')
    for key in ('runtime','input_sha256','source_sha256','native_input_digests'):
        require(value[key]==context[key],'plan input/source/runtime differs')
    if value['status']=='ready':
        require(value['bundle']==context['config']['bundle'] and value['python_path']==context['config']['python_path']
            and value['pythonpath']==context['config']['pythonpath'],'bundle/import binding differs')
        catalog=json.loads((root/'catalog.json').read_bytes())
        require(digest(catalog)==value['catalog_evidence_digest'] and catalog['timing_bundle_digest']==digest(context['bundle']),'catalog bytes changed')
        res=value['resource'];measure=value['pilot_measurement']
        require(res==resources(value['pilot'],catalog['planned_total'],measure['peak_rss_mb'],measure['sqlite_bytes']),'resource request differs')
        require(value['pilot']['unexpected_collisions']==0 and value['pilot']['checked_entries']==1000,'fixed clean pilot required')
        require(value['relocation']['source_relocation']==context['config']['source_relocation'],'producer mapping changed')
    return value


def state_only(plan):
    keys=('status','selected_rows','new_allocations','scientific_bundle_digest','registry_digest','selection_sha256',
          'baseline_result_sha256','baseline_verified_namespaces','new_namespaces_audited','formal_census_descriptor')
    return {key:plan[key] for key in keys}


def fresh(root,*,submission):
    names=['execution-intent.json','result.json','completion.json','failure.json','native.json','scratch']
    if submission:names+=['submission-intent.json','submission.json']
    require(not any((root/name).exists() or (root/name).is_symlink() for name in names),'existing execution/intent requires inspection')


def script_text(root,plan):
    res=plan['resource'];command=shlex.join([plan['python_path'],'-B',str(Path(__file__).resolve()),'run','--root',str(root)])
    return f'''#!/bin/bash
#PBS -N m4q_lowseed
#PBS -q workq
#PBS -l select=1:ncpus=1:mem={res['memory_gb']}gb
#PBS -l walltime={res['walltime']}
#PBS -o {root}/census.out
#PBS -e {root}/census.err
set -euo pipefail
: "${{PBS_JOBID:?submit with qsub}}"
cd {shlex.quote(plan['bundle'])}
export PYTHONPATH={shlex.quote(plan['pythonpath'])}
export PYTHONDONTWRITEBYTECODE=1 PYTHONHASHSEED=0
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 NUMEXPR_NUM_THREADS=1
{command}
'''


def check_upstream(plan,runner):
    m=modules();actual=m.e.qstat('265253.node-PRISM',runner)['Jobs']['265253.node-PRISM']
    require(actual['job_state']=='F' and type(actual['Exit_status']) is int and actual['Exit_status']==0
        and type(actual['run_count']) is int and actual['run_count']==1,'prior full census must remain F/0 once')


def submit(root,*,execute=False,controller_query=None,active_query=None,runner=subprocess.run):
    root=Path(root).absolute();plan=read_plan(root)
    if plan['status']=='not_required_no_allocations':return state_only(plan)
    from submit import own_active_jobs
    from submit_tile_capacity import requested_nodes
    from submit_tile_mc_time import live_controllers
    controller_query=controller_query or live_controllers;active_query=active_query or own_active_jobs
    bundle=Path(plan['bundle']);require(root.resolve()==root and root.is_relative_to(bundle/'runs'),'runroot escapes bundle')
    require(not any(ch.isspace() for path in (root,bundle) for ch in str(path)),'PBS paths cannot contain whitespace')
    fresh(root,submission=True);script=script_text(root,plan);path=root/'census.sh'
    if path.exists():require(not path.is_symlink() and path.read_text()==script,'existing script differs')
    else:
        with path.open('x',newline='\n') as stream:stream.write(script)
    record=dict(command=['qsub',str(path)],manifest=digest(plan),script_sha256=file_hash(path),resource=plan['resource'])
    if not execute:
        dry=dict(record,job_id='dry-run')
        if not (root/'dry-run.json').exists():save_new(root/'dry-run.json',dry)
        else:require(json.loads((root/'dry-run.json').read_bytes())==dry,'dry-run changed')
        return dry
    lock=bundle.parent/'tile-low-noise-submission.lock'
    lock_bytes=canonical(dict(root=str(root),pid=os.getpid(),nonce=os.urandom(16).hex()))+b'\n'
    with lock.open('xb') as stream:stream.write(lock_bytes)
    lock_stat=lock.stat()
    def owns_lock():
        try:
            stat=lock.stat()
            return not lock.is_symlink() and (stat.st_dev,stat.st_ino)==(lock_stat.st_dev,lock_stat.st_ino) and lock.read_bytes()==lock_bytes
        except OSError:return False
    uncertain=False
    try:
        fresh(root,submission=True)
        require(not controller_query() and requested_nodes(active_query())+1<=2,'controller active or two-node budget exceeded')
        check_upstream(plan,runner)
        require(read_plan(root)==plan and file_hash(path)==record['script_sha256'],'fixed inputs changed before qsub')
        require(not controller_query() and requested_nodes(active_query())+1<=2,'controller/allocation changed before qsub')
        require(owns_lock(),'submission lock ownership changed')
        fresh(root,submission=True);save_new(root/'submission-intent.json',record);uncertain=True
        require(read_plan(root)==plan and file_hash(path)==record['script_sha256'],'fixed inputs changed after durable intent')
        require(not controller_query() and requested_nodes(active_query())+1<=2,'controller/allocation changed after durable intent')
        require(owns_lock(),'submission lock ownership changed')
        response=runner(record['command'],capture_output=True,text=True,check=True,timeout=30)
        save_new(root/'qsub-response.json',dict(stdout=response.stdout,stderr=getattr(response,'stderr','')))
        require(owns_lock(),'submission lock ownership changed after qsub')
        job=response.stdout.strip()
        require(re.fullmatch(r'\d+(?:\.[A-Za-z0-9_.-]+)?',job),'ambiguous qsub; retain intent and lock')
        record['job_id']=job;save_new(root/'submission.json',record);uncertain=False;return record
    finally:
        if not uncertain and owns_lock():lock.unlink()


def execution_binding(root,plan):
    ledger=json.loads((root/'submission.json').read_bytes());intent=json.loads((root/'submission-intent.json').read_bytes())
    require({k:v for k,v in ledger.items() if k!='job_id'}==intent and ledger['manifest']==digest(plan)
        and ledger['resource']==plan['resource'] and ledger['command']==['qsub',str(root/'census.sh')]
        and ledger['script_sha256']==file_hash(root/'census.sh'),'actual submission/script differs')
    require((root/'census.sh').read_text()==script_text(root,plan),'actual PBS script differs from plan')
    return ledger


def work(root,*,scheduler=subprocess.run):
    root=Path(root).absolute();plan=read_plan(root)
    require(plan['status']=='ready' and os.environ.get('PBS_JOBID') and all(os.environ.get(k)==v for k,v in THREADS.items()),'PBS/single-thread full census required')
    fresh(root,submission=False);m=modules();ledger=execution_binding(root,plan);job=os.environ['PBS_JOBID'];host=socket.gethostname()
    require(ledger['job_id']==job,'actual PBS id differs')
    actual=m.e.qstat(job,scheduler);m.e.check_pbs(ledger,actual['Jobs'][job],terminal=False,hostname=host)
    save_new(root/'actual-pbs-start.json',actual)
    identity=dict(manifest=digest(plan),pbs_job_id=job,hostname=host)
    save_new(root/'execution-intent.json',dict(identity,submission_sha256=file_hash(root/'submission.json'),
        intent_sha256=file_hash(root/'submission-intent.json'),script_sha256=file_hash(root/'census.sh')))
    started=time.perf_counter();cpu=time.process_time();scratch=root/'scratch';scratch.mkdir()
    try:
        context=inspect_inputs(plan['config_pin']['path'],plan['config_pin']['sha256'])
        measured=m.e.native.native_probe.probe(context['fixture'])
        m.e.native.trace_audit.validate_platform(context['profile'],measured)
        native_keys=('fixture','source_sha256','runtime','platform','machine','python_build','byteorder','thread_environment','native_ldpc_sha256','problem_hash','repeated','fresh','decoder_probe')
        require(all(canonical(context['profile'].get(k))==canonical(measured.get(k)) for k in native_keys),'strict native profile differs')
        save_new(root/'native.json',dict(identity,profile=measured))
        factories,catalog,relocation=build_catalog(context)
        require(digest(catalog)==plan['catalog_evidence_digest'] and relocation==plan['relocation'],'reconstructed full catalog differs')
        require(shutil.disk_usage(scratch).free>=plan['resource']['disk_required_bytes'],'insufficient full census scratch')
        full,measurement=census_stream(factories,catalog['planned_total'],scratch)
        save_new(root/'result.json',full)
        m.a.complete_census_gate(full,catalog,expected_evidence_sha256=plan['catalog_evidence_digest'])
        require(read_plan(root)==plan and execution_binding(root,plan)==ledger,'plan or ledger changed during census')
        verify_files(plan['input_sha256']);verify_files(plan['source_sha256'])
        actual=m.e.qstat(job,scheduler);m.e.check_pbs(ledger,actual['Jobs'][job],terminal=False,hostname=host)
        save_new(root/'actual-pbs-end.json',actual)
        end=dict(identity,complete=True,result_sha256=file_hash(root/'result.json'),native_sha256=file_hash(root/'native.json'),
            execution_sha256=file_hash(root/'execution-intent.json'),wall_seconds=time.perf_counter()-started,
            cpu_seconds=time.process_time()-cpu,measurement=measurement)
        for label in ('input_sha256','source_sha256'):end[label]=plan[label];end[label+'_after']=plan[label]
        save_new(root/'completion.json',end);return end
    except Exception as error:
        save_new(root/'failure.json',dict(identity,complete=False,error=repr(error),wall_seconds=time.perf_counter()-started,
            cpu_seconds=time.process_time()-cpu,sqlite_residuals=[str(p) for p in scratch.rglob('*.sqlite')]))
        raise


def run(root,*,runner=subprocess.run):
    root=Path(root).absolute();plan=read_plan(root)
    if plan['status']=='not_required_no_allocations':return state_only(plan)
    require(os.environ.get('PBS_JOBID') and all(os.environ.get(k)==v for k,v in THREADS.items()),'PBS/single-thread run required')
    fresh(root,submission=False)
    command=[plan['python_path'],'-B',str(Path(__file__).resolve()),'_work','--root',str(root)]
    try:runner(command,check=True,timeout=plan['resource']['wall_seconds']-180)
    except Exception as error:
        if not (root/'failure.json').exists():save_new(root/'failure.json',dict(complete=False,error=repr(error),
            sqlite_residuals=[str(p) for p in root.rglob('*.sqlite')],automatic_retry=False))
        raise
    return json.loads((root/'completion.json').read_bytes())


def verify_descriptor(descriptor,bundle,proof):
    result=modules().e.formal_census(descriptor,bundle,proof);proof.finish();return result


def seal(root,*,scheduler=subprocess.run):
    root=Path(root).absolute();plan=read_plan(root)
    if plan['status']=='not_required_no_allocations':return state_only(plan)
    require(not (root/'descriptor.json').exists() and not (root/'terminal.json').exists(),'fresh terminal seal required')
    m=modules();ledger=execution_binding(root,plan);native=json.loads((root/'native.json').read_bytes())
    terminal=m.e.qstat(ledger['job_id'],scheduler);m.e.check_pbs(ledger,terminal['Jobs'][ledger['job_id']],terminal=True,hostname=native['hostname'])
    save_new(root/'terminal.json',terminal)
    context=inspect_inputs(plan['config_pin']['path'],plan['config_pin']['sha256'])
    names=dict(manifest='manifest.json',catalog='catalog.json',result='result.json',completion='completion.json',
        submission='submission.json',intent='submission-intent.json',execution='execution-intent.json',native='native.json',script='census.sh',terminal='terminal.json')
    descriptor={key:dict(path=str(root/name),sha256=file_hash(root/name)) for key,name in names.items()}
    descriptor.update({key:context['config'][key] for key in ('profile','fixture')})
    proof=m.e.Evidence();verify_descriptor(descriptor,context['bundle'],proof)
    require(read_plan(root)==plan and execution_binding(root,plan)==ledger,'input changed before descriptor publication')
    proof.finish()
    save_new(root/'descriptor.json',descriptor);return descriptor


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('command',choices=('plan','run','_work','submit','seal'))
    parser.add_argument('--root',type=Path,required=True);parser.add_argument('--config',type=Path)
    parser.add_argument('--config-sha256');parser.add_argument('--execute',action='store_true');args=parser.parse_args()
    if args.command=='plan':
        require(args.config is not None and args.config_sha256 is not None,'external configuration pin required')
        result=prepare(args.root,args.config,args.config_sha256)
    elif args.command=='submit':result=submit(args.root,execute=args.execute)
    else:result={'run':run,'_work':work,'seal':seal}[args.command](args.root)
    print(json.dumps(result))


if __name__=='__main__':main()
