"""One-shot parent envelope for the unchanged low-noise selector CLI.

Only standard-library imports precede the externally pinned byte/path gate.
Accepted parent metadata is not a replacement for the selector's PBS raw reader.
"""
import argparse
import ast
import base64
import hashlib
import importlib.util
import json
import math
import os
from pathlib import Path
import re
import secrets
import shlex
import socket
import stat
import subprocess
import sys

THREADS={key:'1' for key in ('OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS')}
COORDINATES=[[case,target] for case in range(4) for target in range(3)]


def require(ok,message):
    if not ok:raise ValueError(message)


def canonical(value):
    return json.dumps(value,sort_keys=True,separators=(',',':'),allow_nan=False).encode()


def digest(value):
    return hashlib.sha256(canonical(value)).hexdigest()


def sha(path):
    value=hashlib.sha256()
    with Path(path).open('rb') as stream:
        for data in iter(lambda:stream.read(1024*1024),b''):value.update(data)
    return value.hexdigest()


def absolute(path):
    value=Path(path)
    require(value.is_absolute(),'absolute path required')
    return value.absolute()


def snapshot(path,*,regular=False):
    path=absolute(path);before=path.lstat();target=path.resolve(strict=True)
    require(path.is_file(),'regular file target required')
    if regular:require(stat.S_ISREG(before.st_mode) and target==path,'regular non-symlink control path required')
    value=sha(path);after=path.lstat()
    require((before.st_dev,before.st_ino,before.st_size,before.st_mtime_ns,before.st_mode)==
        (after.st_dev,after.st_ino,after.st_size,after.st_mtime_ns,after.st_mode)
        and path.resolve(strict=True)==target,'file changed while hashed')
    return dict(target=str(target),sha256=value,device=after.st_dev,inode=after.st_ino,mode=after.st_mode)


def safe_root(root):
    root=absolute(root)
    require(root.resolve()==root and not root.is_symlink(),'output root resolution changed')
    return root


def portable_identity(value):
    """Compare persisted cross-host evidence; keep full local snapshots intact."""
    require(isinstance(value,dict) and set(value)=={'sha256','target','device','inode','mode'},
        'exact snapshot schema required')
    return {key:value[key] for key in ('sha256','target','mode')}


class Evidence:
    """Small metadata/path snapshots, including same-byte file replacement."""
    def __init__(self):self.files={}

    def track(self,path,expected=None,*,regular=False):
        path=str(absolute(path));value=snapshot(path,regular=regular)
        require(expected is None or value['sha256']==expected,'external byte pin differs')
        require(path not in self.files or self.files[path]==value,'input path/identity/bytes changed')
        self.files[path]=value
        return value['sha256']

    def read(self,pin,*,regular=False):
        require(set(pin)=={'path','sha256'} and re.fullmatch('[0-9a-f]{64}',pin['sha256']),'exact external file pin required')
        self.track(pin['path'],pin['sha256'],regular=regular)
        data=Path(pin['path']).read_bytes()
        require(hashlib.sha256(data).hexdigest()==pin['sha256'],'consumed metadata differs')
        value=json.loads(data);self.track(pin['path'],pin['sha256'],regular=regular)
        return value

    def finish(self):
        for path,value in self.files.items():require(snapshot(path)==value,'input changed after consumption')


def pin(path):
    return dict(path=str(absolute(path)),sha256=sha(path))


def save_new(path,value):
    path=absolute(path);safe_root(path.parent)
    with path.open('xb') as stream:stream.write(canonical(value)+b'\n')
    return snapshot(path,regular=True)


def local_imports(paths):
    """Discover cluster imports by reading source bytes, never importing parents."""
    roots={Path(path).parent for path in paths if Path(path).parent.name=='cluster_scripts'}
    roots.update(Path(path) for path in sys.path if path and Path(path).name=='cluster_scripts')
    names=set()
    for path in paths:
        for node in ast.walk(ast.parse(Path(path).read_text(encoding='utf-8-sig'))):
            imports=([item.name.split('.')[0] for item in node.names] if isinstance(node,ast.Import) else
                [node.module.split('.')[0]] if isinstance(node,ast.ImportFrom) and node.module and node.level==0 else [])
            for name in imports:
                if any((root/(name+'.py')).is_file() for root in roots):names.add(name)
    return names


def bootstrap(config,proof):
    """Reject substituted code and executable before importing scientific modules."""
    require(config['schema']==1 and config['purpose']=='low_noise_timing_selector_parent_input','wrong parent input')
    require(not sys.flags.optimize,'optimized Python cannot enforce the execution contract')
    require(config['python_path']==str(Path(sys.executable).absolute())
        and config['pythonpath']==os.environ.get('PYTHONPATH',''),'Python invocation/import path differs')
    proof.track(config['python_path'],config['python_sha256'])
    require(config['native_binding'] and config['source_sha256'] and config['import_origins'],'fixed source/native closure required')
    require(str(Path(__file__).absolute()) in config['source_sha256'],'wrapper source pin missing')
    require(set(config['resolved_sources'])==set(config['source_sha256']),'resolved source census differs')
    core=absolute(config['core_origin']);package=core.parent
    require(core.name=='__init__.py' and str(core) in config['source_sha256'],'fixed core package origin required')
    core_files={str(path.absolute()) for path in package.rglob('*.py')}
    mapped_core={path for path in config['source_sha256'] if Path(path).is_relative_to(package)}
    require(core_files==mapped_core,'complete core source census required before import')
    origins={Path(path).stem:path for path in config['source_sha256'] if Path(path).parent.name=='cluster_scripts'}
    require(len(origins)+len(core_files)==len(config['source_sha256']),'unexpected or duplicate source module path')
    origins['mcmc4qec']=str(core)
    require(config['import_origins']==origins,'exact complete import origin census required before import')
    for mapping in (config['source_sha256'],config['native_binding']):
        for path,value in mapping.items():proof.track(path,value)
    for path,target in config['resolved_sources'].items():
        require(str(Path(path).resolve())==target,'accepted source alias target differs')
    require(local_imports(config['source_sha256']).issubset(origins),'transitive cluster import omitted from byte-pinned closure')
    for name,path in config['import_origins'].items():
        require(re.fullmatch(r'[A-Za-z_]\w*',name),'only top-level import origins are permitted')
        spec=importlib.util.find_spec(name)
        require(spec is not None and spec.origin is not None and str(Path(spec.origin).absolute())==path,
            'actual import origin differs')
    proof.finish()


def science(config):
    import tile_low_noise_timing_evaluation_report as report
    import tile_low_noise_timing_selection as selector
    actual={str(p.absolute()):sha(p) for p in report.source_files().values()}
    actual[str(Path(__file__).absolute())]=sha(__file__)
    require(actual==config['source_sha256'] and report.runtime()==config['runtime'],'actual source closure/runtime differs')
    for name,path in config['import_origins'].items():
        if name in sys.modules:require(str(Path(sys.modules[name].__file__).absolute())==path,'loaded import origin differs')
    return report,selector


def positive(value):
    return type(value) in (int,float) and math.isfinite(value) and value>0


def pbs_cost(pin_value,job_id,proof):
    """Read actual terminal costs; unavailable clocks cannot confirm resources."""
    job=proof.read(pin_value)['Jobs'][job_id]
    require(job.get('job_state')=='F' and type(job.get('Exit_status')) is int and job['Exit_status']==0,
        'successful terminal cost evidence required')
    used=job['resources_used'];clock=used['walltime']
    require(isinstance(clock,str) and re.fullmatch(r'\d+:\d{2}:\d{2}',clock),'actual PBS walltime required')
    hours,minutes,seconds=map(int,clock.split(':'))
    require(minutes<60 and seconds<60,'invalid PBS walltime')
    match=re.fullmatch(r'([0-9]+)(kb|mb|gb|tb|b)',str(used['mem']).lower())
    require(match is not None,'actual PBS peak memory required')
    memory=int(match[1])*1024**{'b':0,'kb':1,'mb':2,'gb':3,'tb':4}[match[2]]
    wall=3600*hours+60*minutes+seconds
    require(wall>0 and memory>0,'positive measured PBS costs required')
    return wall,memory,job


def confirmed_resource(decision,entries,proof):
    require(decision['status']=='confirmed','resource not confirmed; prepare/execute prohibited')
    resource=decision['resource']
    require(set(resource)=={'cpus','workers','memory_gb','wall_seconds','walltime','requested_nodes','max_nodes'},'exact resource fields required')
    require(all(type(resource[key]) is int for key in ('cpus','workers','memory_gb','wall_seconds','requested_nodes','max_nodes'))
        and resource['cpus']==resource['workers']==resource['requested_nodes']==1 and resource['max_nodes']==2
        and 1<=resource['memory_gb']<=340 and 1<=resource['wall_seconds']<=86400,'one-node serial resource ceiling differs')
    seconds=resource['wall_seconds']
    require(resource['walltime']==f'{seconds//3600:02d}:{seconds%3600//60:02d}:{seconds%60:02d}','resource walltime differs')
    require(all(positive(decision[key]) for key in ('wall_basis_seconds','memory_basis_gb','wall_factor','memory_factor'))
        and decision['wall_factor']>=1 and decision['memory_factor']>=1
        and type(decision['overhead_seconds']) in (int,float) and math.isfinite(decision['overhead_seconds'])
        and decision['overhead_seconds']>=0,'finite positive resource basis/factors required')
    require(seconds>=math.ceil(decision['wall_basis_seconds']*decision['wall_factor']+decision['overhead_seconds'])
        and resource['memory_gb']>=math.ceil(decision['memory_basis_gb']*decision['memory_factor']),
        'confirmed resource does not cover declared basis')
    require(isinstance(decision['scope_difference'],str) and decision['scope_difference'].strip()
        and isinstance(decision['decision'],str) and decision['decision'].strip(),'explicit scope and parent resource decision required')
    rows=decision['conditions']
    require([[row['case'],row['target_index']] for row in rows]==COORDINATES,'all twelve resource evidence rows required')
    measured_seconds=0;memory_lower_gb=0
    for row,entry in zip(rows,entries):
        require(row['reader']==entry['reader'],'resource reader scope differs')
        final=proof.read(dict(path=entry['final_report'],sha256=entry['input_sha256'][entry['final_report']]))
        terminal=dict(path=entry['terminal_receipt'],sha256=entry['input_sha256'][entry['terminal_receipt']])
        require(row['final']['terminal']==terminal and row['final']['job_id']==final['pbs_job_id'],
            'resource final job/terminal differs from accepted report')
        final_wall,final_memory,final_pbs=pbs_cost(terminal,row['final']['job_id'],proof)
        lp=entry['final_submission']
        ledger=proof.read(dict(path=lp,sha256=entry['input_sha256'][lp]))
        require(ledger['job_id']==row['final']['job_id'] and ledger['command'][0]=='qsub'
            and shlex.split(final_pbs['Submit_arguments'])==ledger['command'][1:],'resource final script/job differs')
        script=ledger['command'][1];proof.track(script,entry['input_sha256'][script])
        require(ledger['script_sha256']==entry['input_sha256'][script],'resource final script pin differs')
        collection=row['collection'];summary_path=str(Path(entry['root'])/'partition-collection/summary.json')
        require(collection['summary']==dict(path=summary_path,sha256=entry['input_sha256'][summary_path])
            and collection['terminal']==terminal,'resource collection metadata differs')
        summary=proof.read(collection['summary']);collection_job=summary.get('pbs_job_id',final['pbs_job_id'])
        require(collection['job_id']==collection_job and type(collection['included_in_final']) is bool
            and collection['included_in_final']==(collection_job==final['pbs_job_id']),
            'collection cost scope/job differs')
        collection_wall,collection_memory,_=pbs_cost(terminal,collection_job,proof)
        measured_seconds+=final_wall+(0 if collection['included_in_final'] else collection_wall)
        memory_lower_gb=max(memory_lower_gb,final_memory/1024**3,collection_memory/1024**3)
        require(type(row['hash_budget_seconds']) in (int,float) and math.isfinite(row['hash_budget_seconds'])
            and row['hash_budget_seconds']>=0,'finite hash cost basis required')
        if entry['reader']=='staged':
            require(row['staged_copy'] is not None and row['hash_budget_seconds']>0,'staged copy/hash costs required')
            copy=row['staged_copy'];copy_summary=proof.read(copy['summary'])
            origin=final['audited_collection']['staging_origin']
            require(Path(copy['summary']['path'])==Path(entry['root'])/'.staging/summary.json'
                and copy_summary['destination']==entry['root']
                and copy_summary['copy_pbs_job_id']==copy['job_id']==origin['copy_pbs_job_id']
                and copy_summary['source_unchanged'] is True and copy_summary['copy_hashes_verified'] is True
                and copy_summary['scientific_recalculation'] is False and positive(copy_summary['elapsed_seconds']),
                'staged copy receipt identity differs')
            pbs_cost(copy['terminal'],copy['job_id'],proof)
            require(type(copy['extra_hash_passes']) is int and copy['extra_hash_passes']>=2
                and positive(copy['copy_time_factor']) and copy['copy_time_factor']>=1
                and row['hash_budget_seconds']>=copy['extra_hash_passes']*copy['copy_time_factor']*copy_summary['elapsed_seconds'],
                'staged extra hash cost basis incomplete')
        else:require(row['staged_copy'] is None,'unexpected staged cost scope')
        measured_seconds+=row['hash_budget_seconds']
    require(decision['wall_basis_seconds']>=measured_seconds and decision['memory_basis_gb']>=memory_lower_gb,
        'resource basis below measured final/collection/hash costs')
    return resource


def validate_config(config,proof):
    bootstrap(config,proof);report,selector=science(config)
    value=proof.read(config['input']);entries=value['conditions']
    require(set(value)=={'schema','purpose','source_sha256','conditions'} and value['schema']==1
        and value['purpose']=='low_noise_timing_selection_input' and value['source_sha256']==selector.source_hashes(),
        'fixed selector input/source required')
    require([[entry['case'],entry['target_index']] for entry in entries]==COORDINATES
        and all(type(entry['case']) is int and type(entry['target_index']) is int and entry['status']=='complete' for entry in entries),
        'all twelve complete calibration entries required')
    accepted=proof.read(config['acceptance'])
    require(accepted['status']=='accepted_all_twelve' and accepted['input_sha256']==config['input']['sha256']
        and [[row['case'],row['target_index']] for row in accepted['conditions']]==COORDINATES,'parent all-twelve acceptance missing')
    reference=proof.read(accepted['reference_audit'])
    require(reference['tasks']==16 and reference['failed']==0 and reference['all_conditions_audited'] is True
        and reference['terminal_binding_valid'] is True and reference['phase_failure'] is None and reference['phase_failures']==[]
        and [row['condition'] for row in reference['records']]==list(range(16))
        and all(row['status']=='ok' for row in reference['records']),'full sixteen-condition reference audit required')
    for entry,row in zip(entries,accepted['conditions']):
        require(row['entry_sha256']==digest(entry) and entry['reader'] in ('single','partitioned','staged')
            and row['final_report']['path']==entry['final_report'] and row['terminal']['path']==entry['terminal_receipt'],
            'accepted calibration binding differs')
        for key in ('root','audit_root','reference_root','reference_audit_root','final_submission'):
            absolute(entry[key])
        require(Path(accepted['reference_audit']['path'])==Path(entry['reference_audit_root'])/'summary.json',
            'accepted reference audit root differs')
        require(entry['input_sha256'] and (entry['reader']!='staged' or entry['staging_control_pins']),
            'complete metadata pins required')
        for item in (row['final_report'],row['terminal']):
            require(entry['input_sha256'].get(item['path'])==item['sha256'],'accepted external metadata pin differs')
        final=proof.read(row['final_report']);terminal=proof.read(row['terminal'])
        require(final['case']==entry['case'] and final['target_index']==entry['target_index'] and final['replicates']==192
            and final['raw_reference_audited'] is True and final['current_trace_payloads_rehashed'] is True,
            'accepted full calibration report missing')
        audited=final['audited_collection']
        require(audited['groups']==768 and audited['anchors']==192 and audited['native_platform_verified'] is True
            and audited['current_trace_payloads_rehashed'] is True,'accepted full audited collection missing')
        require(terminal.get('Jobs') and all(job.get('job_state')=='F' and type(job.get('Exit_status')) is int
            for job in terminal['Jobs'].values()),'upstream terminal evidence incomplete')
    resource=confirmed_resource(proof.read(config['resource_decision']),entries,proof)
    proof.finish()
    return report,selector,value,resource


def prepared_value(config,selector,root,resource):
    output=str(root/'selection.json')
    argv=[config['python_path'],str(Path(selector.__file__).absolute()),'--input',config['input']['path'],
        '--expected-sha256',config['input']['sha256'],'--output',output]
    return dict(schema=1,purpose='low_noise_timing_selector_execution',input=config['input'],report_path=output,
        selector_argv=argv,source_sha256=selector.source_hashes(),runtime=config['runtime'],
        python_path=config['python_path'],python_sha256=config['python_sha256'],native_binding=config['native_binding'],resource=resource)


def script_text(root,control_sha,prepared,config):
    resource=prepared['resource'];common=[config['python_path'],str(Path(__file__).absolute())]
    args=['--root',str(root),'--control-sha256',control_sha,'--prepared-sha256',digest(prepared)]
    return f'''#!/bin/bash
#PBS -N m4q_lowselect
#PBS -q workq
#PBS -l select=1:ncpus=1:mem={resource['memory_gb']}gb
#PBS -l walltime={resource['walltime']}
#PBS -o {root}/selector.out
#PBS -e {root}/selector.err
set -euo pipefail
: "${{PBS_JOBID:?submit with qsub}}"
cd {shlex.quote(config['bundle'])}
export PYTHONPATH={shlex.quote(config['pythonpath'])}
export PYTHONDONTWRITEBYTECODE=1 PYTHONHASHSEED=0
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 NUMEXPR_NUM_THREADS=1
{shlex.join(common+['begin']+args)}
{shlex.join(prepared['selector_argv'])}
{shlex.join(common+['finish']+args)}
'''


def prepare(root,config_path,expected_sha256):
    root=safe_root(root);require(not root.exists(),'fresh selector root required')
    proof=Evidence();config_pin=dict(path=str(absolute(config_path)),sha256=expected_sha256)
    config=proof.read(config_pin);_,selector,inp,resource=validate_config(config,proof)
    bundle=safe_root(config['bundle'])
    require(root!=bundle/'runs' and root.is_relative_to(bundle/'runs')
        and not any(ch.isspace() for path in (root,bundle) for ch in str(path)),'fresh output under bundle/runs required')
    for entry in inp['conditions']:
        for key in ('root','audit_root','reference_root','reference_audit_root'):
            require(not root.is_relative_to(Path(entry[key]).resolve()),'output inside upstream input root')
    require(not any(Path(path).resolve().is_relative_to(root) for path in proof.files),'output contains accepted input')
    prepared=prepared_value(config,selector,root,resource)
    control=dict(schema=1,purpose='low_noise_timing_selector_parent_control',root=str(root),config=config_pin,
        prepared_sha256=digest(prepared),inputs=proof.files,
        scope='Parent accepted metadata only; current raw payload validation occurs in the unchanged PBS selector.')
    proof.finish();root.mkdir(parents=True,exist_ok=False)
    save_new(root/'prepared.json',prepared);save_new(root/'control.json',control)
    control_sha=sha(root/'control.json')
    with (root/'selector.sh').open('x',newline='\n') as stream:stream.write(script_text(root,control_sha,prepared,config))
    proof.finish()
    return dict(root=str(root),control_sha256=control_sha,prepared_sha256=digest(prepared),resource=resource)


def read_plan(root,expected_control_sha256):
    root=safe_root(root);proof=Evidence()
    control=proof.read(dict(path=str(root/'control.json'),sha256=expected_control_sha256),regular=True)
    require(control['schema']==1 and control['purpose']=='low_noise_timing_selector_parent_control' and control['root']==str(root),'fixed parent control required')
    config=proof.read(control['config']);_,selector,_,resource=validate_config(config,proof)
    for path,value in control['inputs'].items():
        require(portable_identity(proof.files.get(path))==portable_identity(value),'prepared input/source identity changed')
    require(set(control['inputs'])==set(proof.files)-{str(root/'control.json')},'prepared input census differs')
    prepared=prepared_value(config,selector,root,resource)
    require(control['prepared_sha256']==digest(prepared),'prepared semantic pin differs')
    prepared_pin=pin(root/'prepared.json');actual=proof.read(prepared_pin,regular=True)
    require(actual==prepared,'prepared execution differs')
    script=root/'selector.sh';proof.track(script,regular=True)
    require(script.read_text()==script_text(root,expected_control_sha256,prepared,config),'fixed selector script differs')
    proof.finish()
    return dict(prepared=prepared,config=config,control=control,files=proof.files)


def node_count(jobs):
    from submit_tile_capacity import requested_nodes
    return requested_nodes(jobs)


def submit(root,expected_control_sha256,*,execute=False,controller_query=None,active_query=None,runner=subprocess.run):
    root=safe_root(root);state=read_plan(root,expected_control_sha256);plan=state['prepared'];config=state['config']
    from submit import own_active_jobs
    from submit_tile_mc_time import live_controllers
    controller_query=controller_query or live_controllers;active_query=active_query or own_active_jobs
    def fresh():
        require(not any((root/name).exists() or (root/name).is_symlink() for name in
            ('submission-intent.json','submission.json','execution.json','completion.json','selection.json')),'selector submission already reserved')
    fresh();record=dict(manifest=digest(plan),command=['qsub',str(root/'selector.sh')],script_sha256=sha(root/'selector.sh'),
        resource=plan['resource'],control_sha256=expected_control_sha256)
    if not execute:return dict(record,status='prepared_not_submitted')
    lock=Path(config['bundle']).parent/'tile-low-noise-submission.lock'
    lock_state=save_new(lock,dict(root=str(root),pid=os.getpid(),token=secrets.token_hex(16)))
    def owned():require(snapshot(lock,regular=True)==lock_state,'submission lock ownership changed')
    def gate():
        owned();require(not controller_query() and node_count(active_query())+1<=2,'controller active or two-node budget exceeded')
        require(read_plan(root,expected_control_sha256)==state,'current prepared inputs/source/script changed')
    uncertain=False
    try:
        fresh();gate();fresh()
        intent=save_new(root/'submission-intent.json',record)
        gate()
        require(snapshot(root/'submission-intent.json',regular=True)==intent,'submission intent identity changed')
        owned();uncertain=True
        try:
            response=runner(record['command'],capture_output=True,text=True,check=True,timeout=30)
        except Exception as error:
            def captured(value):
                return dict(encoding='base64',data=base64.b64encode(value).decode()) if isinstance(value,bytes) else dict(encoding='text',data=value)
            save_new(root/'qsub-error.json',dict(type=type(error).__name__,message=str(error),response_uncertain=True,
                command=record['command'],returncode=getattr(error,'returncode',None),
                stdout=captured(getattr(error,'stdout',getattr(error,'output',None))),stderr=captured(getattr(error,'stderr',None))))
            raise
        save_new(root/'qsub-response.json',dict(command=record['command'],stdout=response.stdout,stderr=response.stderr))
        owned();job=response.stdout.strip()
        require(re.fullmatch(r'\d+(?:\.[A-Za-z0-9_.-]+)?',job),'ambiguous qsub response; preserve reservation')
        require(snapshot(root/'submission-intent.json',regular=True)==intent,'intent changed across qsub response')
        submitted=dict(record,job_id=job);save_new(root/'submission.json',submitted);uncertain=False
        return submitted
    finally:
        if not uncertain:owned();lock.unlink()


def ledger_state(root,state,proof):
    ledger=proof.read(pin(root/'submission.json'),regular=True)
    intent=proof.read(pin(root/'submission-intent.json'),regular=True)
    require({key:value for key,value in ledger.items() if key!='job_id'}==intent
        and intent==dict(manifest=digest(state['prepared']),command=['qsub',str(root/'selector.sh')],
            script_sha256=sha(root/'selector.sh'),resource=state['prepared']['resource'],control_sha256=sha(root/'control.json')),
        'actual submission/intent differs')
    require(re.fullmatch(r'\d+(?:\.[A-Za-z0-9_.-]+)?',ledger['job_id']),'invalid actual PBS receipt')
    response=proof.read(pin(root/'qsub-response.json'),regular=True)
    require(response['command']==ledger['command'] and response['stdout'].strip()==ledger['job_id'],
        'actual qsub response differs from submission')
    return ledger


def compute_state(root,control_sha,prepared_sha,job_query,hostname):
    require(re.fullmatch(r'\d+(?:\.[A-Za-z0-9_.-]+)?',os.environ.get('PBS_JOBID',''))
        and all(os.environ.get(key)==val for key,val in THREADS.items())
        and os.environ.get('PYTHONHASHSEED')=='0' and os.environ.get('PYTHONDONTWRITEBYTECODE')=='1',
        'PBS and fixed process environment required before compute imports')
    root=safe_root(root);state=read_plan(root,control_sha);plan=state['prepared']
    require(digest(plan)==prepared_sha,'external prepared pin differs')
    report,_=science(state['config']);proof=Evidence();ledger=ledger_state(root,state,proof)
    require(ledger['job_id']==os.environ['PBS_JOBID'],'PBS job differs from qsub receipt')
    host=hostname or socket.gethostname();query=job_query or report.execution.qstat
    pbs=query(ledger['job_id']);report.execution.check_pbs(ledger,pbs['Jobs'][ledger['job_id']],terminal=False,hostname=host)
    proof.finish()
    wanted=dict(manifest=digest(plan),pbs_job_id=ledger['job_id'],hostname=host,input_sha256=plan['input']['sha256'],
        selector_argv=plan['selector_argv'],**{key:plan[key] for key in
            ('source_sha256','runtime','python_path','python_sha256','native_binding')})
    return root,state,proof,wanted,pbs


def begin(root,control_sha,prepared_sha,*,job_query=None,hostname=None):
    root,state,proof,wanted,pbs=compute_state(root,control_sha,prepared_sha,job_query,hostname)
    require(not any((root/name).exists() or (root/name).is_symlink() for name in
        ('execution.json','begin-proof.json','selection.json','completion.json')),'fresh selector execution required')
    save_new(root/'actual-pbs-start.json',pbs)
    execution=save_new(root/'execution.json',wanted)
    save_new(root/'begin-proof.json',dict(control_sha256=control_sha,files=state['files']|proof.files,
        execution=execution,start_pbs=snapshot(root/'actual-pbs-start.json',regular=True)))
    return wanted


def finish(root,control_sha,prepared_sha,*,job_query=None,hostname=None):
    root,state,proof,wanted,pbs=compute_state(root,control_sha,prepared_sha,job_query,hostname)
    require(not (root/'completion.json').exists() and not (root/'completion.json').is_symlink(),'completion already exists')
    begin_record=proof.read(pin(root/'begin-proof.json'),regular=True)
    require(begin_record['control_sha256']==control_sha and snapshot(root/'execution.json',regular=True)==begin_record['execution']
        and snapshot(root/'actual-pbs-start.json',regular=True)==begin_record['start_pbs'],'begin execution binding changed')
    for path,value in begin_record['files'].items():require(snapshot(path)==value,'input changed since compute begin')
    require(proof.read(pin(root/'execution.json'),regular=True)==wanted,'compute start/end runtime differs')
    plan=state['prepared'];result=proof.read(pin(root/'selection.json'),regular=True)
    require(result['purpose']=='low_noise_independent_timing_selection' and result['conditions']==24
        and [[row['case'],row['target_index'],row['epsilon_index']] for row in result['rows']]==
            [[case,target,epsilon] for case,target in COORDINATES for epsilon in range(2)]
        and result['production_selection_validated'] is True and len(result['calibration_bindings'])==12
        and result['input_manifest_sha256']==plan['input']['sha256'] and result['source_sha256']==plan['source_sha256']
        and result['nominal_coverage_certified'] is False and result['population_rmse_certified'] is False
        and result['independent_timing_performed'] is False and all(row['speed_ratio'] is None for row in result['rows']),
        'full fixed selection output differs')
    allowed={'selected','unmet_empirical_precision','ineligible_reference_unavailable',
        'ineligible_reference_zero_boundary','ineligible_reference_width'}
    for row in result['rows']:
        require(row['status'] in allowed and row['calibration_replicates']==192
            and row['planned_conditions']==len(row['candidates']) and row['planned_conditions']>0
            and row['diagnostics_filter_applied'] is False and row['coverage_filter_applied'] is False
            and all(candidate['assessment']['metrics']['replicates']==192 for candidate in row['candidates']),
            'selection candidate census or denominator differs')
    require(read_plan(root,control_sha)==state,'end input/source binding changed');proof.finish()
    save_new(root/'actual-pbs-end.json',pbs)
    completion=dict(wanted,report_sha256=sha(root/'selection.json'),complete=True)
    complete_state=save_new(root/'completion.json',completion)
    save_new(root/'finish-proof.json',dict(control_sha256=control_sha,files=state['files']|proof.files,
        completion=complete_state,end_pbs=snapshot(root/'actual-pbs-end.json',regular=True)))
    return completion


def seal(root,control_sha,*,job_query=None):
    root=safe_root(root);require(not (root/'descriptor.json').exists(),'descriptor already sealed')
    state=read_plan(root,control_sha);report,_=science(state['config']);proof=Evidence()
    ledger=ledger_state(root,state,proof);end=proof.read(pin(root/'finish-proof.json'),regular=True)
    require(end['control_sha256']==control_sha,'completion control proof changed')
    persisted=[(root/'completion.json',end['completion'],True),(root/'actual-pbs-end.json',end['end_pbs'],True)]
    persisted.extend((Path(path),value,False) for path,value in end['files'].items())
    for path,value,regular in persisted:
        proof.track(path,regular=regular)
        require(portable_identity(proof.files[str(absolute(path))])==portable_identity(value),'completed input/artifact changed')
    actual=proof.read(pin(root/'execution.json'),regular=True);query=job_query or report.execution.qstat
    terminal=query(ledger['job_id']);report.execution.check_pbs(ledger,terminal['Jobs'][ledger['job_id']],terminal=True,hostname=actual['hostname'])
    proof.finish();save_new(root/'terminal.json',terminal)
    names=dict(prepared='prepared.json',intent='submission-intent.json',submission='submission.json',script='selector.sh',
        execution='execution.json',completion='completion.json',terminal='terminal.json')
    descriptor={key:pin(root/name) for key,name in names.items()};selection=pin(root/'selection.json')
    accepted_proof=report.Evidence();accepted=report.selector_evidence(descriptor,selection,accepted_proof);accepted_proof.finish()
    require(read_plan(root,control_sha)==state,'seal input/source changed');proof.finish()
    for path in end['files']:require(snapshot(path)==proof.files[str(absolute(path))],'completed evidence changed during seal')
    value=dict(descriptor=descriptor,selection=selection,accepted=accepted,control_sha256=control_sha,
        scope='Accepted selector execution; seal reads metadata and hashes only, not trace payloads.')
    save_new(root/'descriptor.json',value)
    return value


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action',choices=('prepare','submit','begin','finish','seal'))
    parser.add_argument('--root',type=Path,required=True);parser.add_argument('--config',type=Path)
    parser.add_argument('--expected-sha256');parser.add_argument('--control-sha256');parser.add_argument('--prepared-sha256')
    parser.add_argument('--execute',action='store_true');args=parser.parse_args()
    if args.action=='prepare':value=prepare(args.root,args.config,args.expected_sha256)
    elif args.action=='submit':value=submit(args.root,args.control_sha256,execute=args.execute)
    elif args.action=='seal':value=seal(args.root,args.control_sha256)
    else:value=globals()[args.action](args.root,args.control_sha256,args.prepared_sha256)
    print(json.dumps(value))


if __name__=='__main__':main()
