"""Collect a parent-identified completed full inventory, never submit or recompute."""
import argparse
from collections import Counter
import hashlib
import itertools
import json
from pathlib import Path
import re
import shlex
import subprocess
import sys
import time

D=Path(__file__).resolve().parent
PREPARATION_SHA='011aef0ef043c6f36d94b82e14079c31c12e64b4502c8d18132a9b14a88a350d'
KEY=('kind','case','kernel','init','chains','burn','samples','rung','observable')
SCALARS=('mean','iat','ess','iat_mcse','cross_chain_se','rhat')
VECTORS=('chain_means','chain_iat','chain_ess')
SECTOR=('sector_transitions','unique_sectors')
FALSE_FLAGS=('diagnostics_recomputed','acf_arrays_rechecked','bootstrap_recomputed','decoder_reexecuted','native_probe_reexecuted','current_all_payloads_reaudited')
FILES=('manifest.json','dry_run.json','submission-intent.json','submission.json','execution-intent.json','inventory.sh','inventory.out','inventory.err','summary.json','upstream-completion-at-submit.json','inventory/summary.json','inventory/rows.jsonl')
OBSERVER_TIMEOUT_SECONDS=600

def require(ok,message):
    if not ok:raise ValueError(message)

def sha(path):
    digest=hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda:stream.read(1024*1024),b''):digest.update(block)
    return digest.hexdigest()

def read(path):return json.loads(Path(path).read_bytes())

def preimport(bundle,binding,executable=None):
    """Verify accepted source, package aggregate and Python using stdlib only."""
    bundle=Path(bundle).resolve()
    for name,digest in binding['source_sha256'].items():
        path=bundle/'cluster_scripts'/name
        require(Path(name).name==name and path.resolve().is_relative_to(bundle) and sha(path)==digest,'accepted source changed before import')
    package=bundle/'src/mcmc4qec';digest=hashlib.sha256();files=sorted(package.rglob('*.py'))
    require(bool(files),'missing accepted core package before import')
    for path in files:
        require(path.resolve().is_relative_to(package.resolve()),'package escaped before import')
        digest.update(path.relative_to(package).as_posix().encode()+b'\0');digest.update(path.read_bytes())
    require(digest.hexdigest()==binding['package_sha256'],'accepted core package changed before import')
    actual=Path(executable or sys.executable).resolve()
    require(str(actual)==binding['python_path'] and sha(actual)==binding['python_sha256'],'accepted Python path/hash differs before import')
    return dict(package_sha256=digest.hexdigest(),python_path=str(actual),python_sha256=sha(actual),source_files=len(binding['source_sha256']))

def preparation():
    path=D/'mixing_execution_full_preparation_v1.json'
    raw=path.read_bytes();require(hashlib.sha256(raw).hexdigest()==PREPARATION_SHA,'fixed preparation changed')
    result=json.loads(raw)
    require([row['case'] for row in result['cases']]==list(range(4)),'four fixed cases required')
    for row in result['cases']:
        prior=D/f"mixing_execution_capacity_case{row['case']}_evidence_v1"/'full'
        for name,digest in row['full_files_sha256'].items():require(sha(prior/name)==digest,'accepted preparation file differs')
    return result

def files_snapshot(root):
    result={}
    for name in FILES:
        path=Path(root)/name
        require(path.is_file() and path.resolve()==path.absolute(),'collected output must be a regular fixed path')
        result[name]=dict(sha256=sha(path),bytes=path.stat().st_size,resolved_path=str(path.resolve()))
    return result

def memory(value):
    match=re.fullmatch(r'(\d+)(b|kb|mb|gb|tb)',str(value).lower())
    require(match is not None,'PBS memory format')
    return int(match[1])*1024**('b','kb','mb','gb','tb').index(match[2])

def validate_pbs(job,script,resource,host):
    require(job.get('job_state')=='F' and type(job.get('Exit_status')) is int and job['Exit_status']==0,'PBS F exit zero required')
    require(job.get('run_count')==1 and shlex.split(job.get('Submit_arguments',''))==[script],'PBS script/rerun differs')
    actual=job['Resource_List'];select=actual['select'].split(':')
    require(select[0]=='1' and '+' not in actual['select'],'PBS one node required')
    selected=dict(item.split('=',1) for item in select[1:])
    require(actual['nodect']==1 and actual['ncpus']==resource['cpus']==int(selected['ncpus']),'PBS CPU differs')
    require(memory(actual['mem'])==memory(selected['mem'])==resource['memory_gb']*1024**3 and actual['walltime']==resource['walltime'],'PBS memory/wall differs')
    require({item.split('/')[0] for item in job['exec_host'].split('+')}=={host},'PBS host differs')
    return {key:job[key] for key in ('job_state','Exit_status','run_count','Submit_arguments','Resource_List','exec_host')}

def validate_report(report,case,expected,expected_rows):
    require(report['schema']==1 and report['purpose']=='saved_mixing_inventory' and report['case']==case,'inventory identity differs')
    require(report['groups']==768 and report['replicates']==192 and report['rows']==expected_rows,'full denominator differs')
    records=report['records'];keys=[tuple(row[k] for k in KEY) for row in records]
    require(len(keys)==len(set(keys))==len(expected)==report['conditions'] and set(keys)==set(expected),'complete observable cohort census required')
    require(type(report['inventory_complete']) is bool and type(report['failed_sampling']) is int and report['failed_sampling']>=0,'explicit inventory status required')
    require(all(report[k] is False for k in FALSE_FLAGS),'unexpected scientific recomputation claim')
    statuses=Counter();observables=Counter();missing=undefined=nonfinite=sector=0
    for row in records:
        require(row['replicates']==192 and row['replicate_ids']==list(range(192)),'replicate denominator differs')
        counts=row['status_counts']
        require(set(counts)<= {'stored','missing_recorded_sampling_failure','missing_unexpected'} and all(type(v) is int and v>=0 for v in counts.values()) and sum(counts.values())==192,'status denominator differs')
        require(all(type(row[k]) is int and 0<=row[k]<=192 for k in ('undefined','nonfinite','stored_missing_fields')),'diagnostic count differs')
        fields=SECTOR if row['kind']=='sector' else SCALARS+VECTORS
        require(set(row['metrics'])==set(fields),'all scientific metric fields required')
        for name,value in row['metrics'].items():
            n=192*(row['chains'] if name in VECTORS+SECTOR else 1)
            require(value['expected_values']==n and all(type(value[k]) is int and value[k]>=0 for k in ('finite_values','null_values','nonfinite_values')) and sum(value[k] for k in ('finite_values','null_values','nonfinite_values'))==n,'metric/sector denominator differs')
        statuses.update(counts);observables[row['observable']]+=1
        undefined+=row['undefined'];nonfinite+=row['nonfinite'];missing+=row['stored_missing_fields'];sector+=row['kind']=='sector'
    complete=not (statuses['missing_unexpected'] or nonfinite or missing)
    require(report['inventory_complete']==complete,'inventory completeness flag differs')
    return dict(cohorts=len(records),rows=expected_rows,replicates=192,sector_cohorts=sector,observables=dict(observables),status_counts=dict(statuses),undefined=undefined,nonfinite=nonfinite,stored_missing_fields=missing,failed_sampling=report['failed_sampling'],inventory_complete=report['inventory_complete'])

def remote(payload):
    """Read-only verifier; invoked twice, before and after transfer."""
    row=payload['row'];root=Path(row['full_root']);bundle=Path(payload['bundle']);jobid=payload['job_id'];parent=payload['parent_receipt']
    def query():
        raw=json.loads(subprocess.run(['qstat','-x','-f','-F','json',jobid],capture_output=True,text=True,check=True,timeout=30).stdout)['Jobs'][jobid]
        fields=('job_state','Exit_status','run_count','Submit_arguments','Resource_List','resources_used','exec_host','stime','mtime','obittime')
        return {k:raw[k] for k in fields if k in raw}
    observed=query()
    require(observed.get('job_state')=='F' and observed.get('Exit_status')==0,'PBS not successful terminal; no collection')
    for name,digest in row['full_files_sha256'].items():require(sha(root/name)==digest,'prepared file changed')
    preimport_proof=preimport(bundle,payload['dry_run']['bundle_binding'])
    import tile_mixing_execution as r
    import submit_tile_mixing_execution as s
    import tile_mixing_inventory as inv
    plan=r.read_plan(root);require(plan['mode']=='full' and plan['case']==row['case'] and r.c.digest(plan)==row['full_manifest'],'full plan differs')
    require(read(root/'submission.json')==parent and parent['job_id']==jobid,'parent receipt differs')
    require(s.bundle_binding(bundle,plan)==parent['bundle_binding']==payload['dry_run']['bundle_binding'],'bundle binding differs')
    bound=r.binding(root,plan,jobid);summary=read(root/'summary.json');intent=read(root/'execution-intent.json')
    require(summary['complete'] is True and summary['terminal_binding_valid'] is True and summary['mode']=='full','incomplete execution')
    require(summary['manifest']==intent['manifest']==r.c.digest(plan) and summary['pbs_job_id']==intent['pbs_job_id']==jobid,'execution identity differs')
    require(summary['submission_binding']==intent['submission_binding']==bound and summary['execution_intent_sha256']==sha(root/'execution-intent.json') and summary['hostname']==intent['hostname'],'execution receipt differs')
    stable=validate_pbs(observed,str(root/'inventory.sh'),row['resource'],intent['hostname'])
    before=files_snapshot(root)
    report=read(root/'inventory/summary.json');production=read(Path(plan['snapshot']['production_root'])/'manifest.json')
    diagnostics=inv.expected_diagnostics(production,row['case']);templates=[('diagnostic',*key) for key in diagnostics]
    templates += [('sector',*key,'sector') for key in sorted({key[:4] for key in diagnostics if '_bennett_edge_' not in key[4]})]
    expected=[(kind,row['case'],kernel,init,chains,burn,samples,rung,name) for kernel,init in itertools.product(production['kernels'],production['initializations']) for kind,chains,burn,samples,rung,name in templates]
    census=validate_report(report,row['case'],expected,row['expected_full_rows_including_sector'])
    require(summary['groups']==768 and summary['replicates']==192 and summary['rows']==report['rows'] and summary['inventory_complete']==report['inventory_complete'],'execution/report summary differs')
    require(summary['inventory_summary_sha256']==before['inventory/summary.json']['sha256'] and summary['rows_sha256']==report['rows_sha256']==before['inventory/rows.jsonl']['sha256'],'report output hash differs')
    state=plan['snapshot'];audited=read(state['audited_results'])
    expected_source={name:sha(path) for name,path in (('inventory',inv.__file__),('audited_results',r.audited.__file__),('calibration',r.c.__file__),('archive',r.audited.archive.__file__))}
    require(report['source_sha256']==expected_source,'inventory source map differs')
    require(report['audited_results_sha256']==sha(state['audited_results']) and report['analysis_verification_sha256']==sha(state['analysis_verification']) and report['failed_sampling']==audited['failed_sampling'],'upstream audit binding differs')
    require(report['sampling_manifest']==r.c.digest(production) and report['analysis_context']==r.c.digest(read(Path(state['production_root'])/'analysis_manifest.json')),'production/context binding differs')
    require(r.read_plan(root)==plan and r.binding(root,plan,jobid)==bound,'terminal source/input binding changed')
    require(before==files_snapshot(root),'collected bytes changed during read')
    require(validate_pbs(query(),str(root/'inventory.sh'),row['resource'],intent['hostname'])==stable,'terminal PBS changed')
    return dict(case=row['case'],job_id=jobid,root=str(root),pbs=observed,pbs_stable=stable,files=before,census=census,bundle_binding=parent['bundle_binding'],preimport=preimport_proof,native_provenance='Pinned upstream runtime/native audit; no fresh native probe',scientific_diagnostics_recomputed=False)

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--case',type=int,choices=range(4),required=True);parser.add_argument('--job',required=True)
    parser.add_argument('--receipt',type=Path,required=True);parser.add_argument('--receipt-sha256',required=True)
    parser.add_argument('--collect',action='store_true');parser.add_argument('--tag',default='v1')
    args=parser.parse_args();require(re.fullmatch(r'\d+(?:\.[A-Za-z0-9_.-]+)?',args.job),'explicit actual job ID required')
    require(re.fullmatch(r'[A-Za-z0-9_-]+',args.tag),'simple new tag required')
    prep=preparation();row=prep['cases'][args.case]
    receipt_bytes=args.receipt.read_bytes();require(hashlib.sha256(receipt_bytes).hexdigest()==args.receipt_sha256,'parent receipt bytes differ')
    dry_path=D/f'mixing_execution_capacity_case{args.case}_evidence_v1/full/dry_run.json'
    dry_bytes=dry_path.read_bytes();require(hashlib.sha256(dry_bytes).hexdigest()==row['full_files_sha256']['dry_run.json'],'accepted dry-run bytes differ')
    parent=json.loads(receipt_bytes);dry=json.loads(dry_bytes)
    require(parent['job_id']==args.job and {k:v for k,v in parent.items() if k not in ('job_id','upstream_completion_sha256')}=={k:v for k,v in dry.items() if k!='job_id'},'parent receipt differs from fixed dry-run')
    payload=dict(row=row,bundle=prep['bundle'],job_id=args.job,parent_receipt=parent,dry_run=dry)
    if not args.collect:
        print(json.dumps(dict(case=args.case,job_id=args.job,remote_root=row['full_root'],remote_executed=False,qsub_executed=False)));return
    dest=D/f'mixing_execution_full_case{args.case}_evidence_{args.tag}';dest.mkdir(exist_ok=False)
    helper=Path(__file__).read_bytes();helper_sha=hashlib.sha256(helper).hexdigest();(dest/'collector.py').write_bytes(helper);(dest/'accepted_parent_receipt.json').write_bytes(receipt_bytes)
    env=['env','PYTHONPATH='+prep['bundle']+'/src:'+prep['bundle']+'/cluster_scripts','PYTHONDONTWRITEBYTECODE=1','PYTHONHASHSEED=0','OMP_NUM_THREADS=1','OPENBLAS_NUM_THREADS=1','MKL_NUM_THREADS=1','NUMEXPR_NUM_THREADS=1',prep['bundle']+'/venv/bin/python','-']
    program="ns={'__name__':'observer','__file__':'observer.py'}\nexec("+repr(helper.decode())+",ns)\nprint(ns['json'].dumps(ns['remote']("+repr(payload)+")))\n"
    (dest/'remote_verifier.py').write_bytes(program.encode());started=time.perf_counter()
    def observe(label):
        run=subprocess.run(['ssh','cluster',shlex.join(env)],input=program.encode(),capture_output=True,timeout=OBSERVER_TIMEOUT_SECONDS)
        (dest/(label+'.stdout.json')).write_bytes(run.stdout);(dest/(label+'.stderr.txt')).write_bytes(run.stderr)
        require(run.returncode==0,'remote verification failed; preserved evidence, no automatic retry')
        return json.loads(run.stdout)
    before=observe('before')
    for name,expected in before['files'].items():
        require(name in FILES,'unexpected transfer name');target=dest/'full'/name;target.parent.mkdir(parents=True,exist_ok=True)
        subprocess.run(['scp','cluster:'+row['full_root']+'/'+name,str(target)],check=True,timeout=3600)
        require(target.stat().st_size==expected['bytes'] and sha(target)==expected['sha256'],'transfer hash/size mismatch')
    after=observe('after')
    require(all(before[k]==after[k] for k in before if k!='pbs'),'remote evidence changed across transfer')
    require(sha(args.receipt)==args.receipt_sha256 and sha(__file__)==helper_sha and sha(dry_path)==row['full_files_sha256']['dry_run.json'] and sha(D/'mixing_execution_full_preparation_v1.json')==PREPARATION_SHA,'local accepted inputs changed')
    require(all(sha(dest/'full'/name)==item['sha256'] for name,item in before['files'].items()),'local payload changed')
    result=dict(before,collection_seconds=time.perf_counter()-started,collector_sha256=helper_sha,preparation_sha256=PREPARATION_SHA,parent_receipt_sha256=args.receipt_sha256,local_all_files_hash_verified=True,qsub_executed=False,warning='Transfer and saved metadata validation only; no new diagnostics/native probe/raw trace audit. Full JSONL values are retained without numerical recomputation.')
    with (dest/'verification.json').open('x') as stream:json.dump(result,stream,indent=2)
    print(json.dumps(dict(case=args.case,job_id=args.job,output=str(dest),census=result['census'])))

if __name__=='__main__':main()
