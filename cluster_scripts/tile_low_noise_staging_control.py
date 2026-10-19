"""Bind staged compute scripts, parent receipts, actual PBS resources and completion."""
import argparse
import json
import os
from pathlib import Path
import re
import shlex
import socket

import tile_low_noise_staging as s
import tile_low_noise_analysis_partitions as p
import tile_low_noise_trace_audit_run as r
import tile_low_noise_audited_collection as collection
import submit_tile_low_noise_analysis_partitions as ps
import submit_tile_low_noise_trace_audit as rs

c=s.c
require=s.require


def software():
    paths={str(Path(path).resolve()):Path(path).resolve() for path in [__file__,collection.__file__,*ps.source_files().values(),*rs.source_files().values()]}
    return dict(staging=s.software_snapshot(),control_sources=s.hashes(paths))


def capacity_completion(capacity_root,destination,pins):
    require(isinstance(pins,dict) and set(pins)=={'prepared_sha256','receipt_sha256'},'explicit parent capacity completion pins required')
    root=s.absolute(capacity_root);plan_path=root/'staging-control-plan.json'
    record,_=s.json_snapshot(plan_path)
    require(record['phase']=='trace-audit' and record['capacity_root'] is None and record['destination']==str(s.absolute(destination)),'independent initial capacity control required')
    completed=read_completion(plan_path,pins['prepared_sha256'],pins['receipt_sha256'])
    require(completed['status']=='success','successful capacity completion required')
    plan,sampling=r.read_plan(root,destination);summary,digest=s.json_snapshot(root/'summary.json')
    require(digest==completed['phase_evidence']['summary_sha256'],'capacity summary differs from terminal completion')
    return plan,sampling,summary,completed


def prepare_audit_full(root,destination,capacity_root,pins):
    """Plan from completed capacity metadata; leave current raw hashing to compute."""
    cap,sampling,summary,completed=capacity_completion(capacity_root,destination,pins)
    provisional=dict(cap,purpose='low_noise_trace_audit_full',replicates=192,workers=1)
    resource=rs.res.resource_plan(cap,summary,provisional)
    before=s.read_staged_provenance(destination)
    require(capacity_completion(capacity_root,destination,pins)==(cap,sampling,summary,completed),'capacity completion changed during planning')
    plan=r.prepare(root,destination,capacity=False,workers=resource['workers'])
    require(rs.res.resource_plan(cap,summary,plan)['workers']==plan['workers'] and s.read_staged_provenance(destination)==before,'full audit plan or staging provenance changed')
    return plan


def plan_inputs(bundle,destination,phase,index=None,audit_root=None,capacity_root=None,capacity_pins=None,*,fresh=False):
    bundle,destination=map(s.absolute,(bundle,destination))
    require(destination!=bundle/'runs' and destination.is_relative_to(bundle/'runs'),'staged root must lie inside bundle/runs')
    if phase=='analysis':
        wrapper=ps.checked_plan(destination,index)
        folder=ps.require_fresh(destination,wrapper,index) if fresh else destination/'analysis-submissions'/str(index)
        fixed=wrapper['resources'];part=fixed['partitions'][index]
        baseline=dict(cpus=fixed['cpus'],memory_gb=fixed['memory_gb'],workers=fixed['workers'],wall_seconds=part['wall_seconds'],walltime=part['walltime'],requested_nodes=1,max_nodes=2)
        ledger=dict(partition=index,partition_manifest=c.digest(wrapper),manifest=c.digest(wrapper['production']),bundle_binding=ps.bundle_binding(bundle,wrapper))
        script=folder/'partition.sh';phase_root=destination/'analysis-partitions'/str(index)
    else:
        require(phase=='trace-audit','unknown phase')
        audit_root=s.absolute(audit_root)
        require(audit_root!=bundle/'runs' and audit_root.is_relative_to(bundle/'runs') and not audit_root.is_relative_to(destination) and not destination.is_relative_to(audit_root),'independent audit root inside bundle/runs required')
        if fresh:rs.require_fresh(audit_root)
        if capacity_root is None:
            require(capacity_pins is None,'initial capacity must not have capacity pins')
            plan,sampling,baseline,jobs=rs.checked_plan(audit_root,destination,None)
            capacity_evidence=None
        else:
            cap,sampling,summary,capacity_evidence=capacity_completion(capacity_root,destination,capacity_pins)
            plan,again=r.read_plan(audit_root,destination)
            require(again==sampling,'capacity/full sampling differs')
            baseline=rs.res.resource_plan(cap,summary,plan)
            require(plan['workers']==baseline['workers'],'immutable full audit worker count differs from capacity')
            jobs=sorted({s.json_snapshot(destination/(phase+'-execution-intent.json'))[0]['pbs_job_id'] for phase in ('sample','anchors')})
        ledger=dict(manifest=c.digest(plan),bundle_binding=rs.bundle_binding(bundle,sampling),sampling_root=str(destination),capacity_root=None if capacity_root is None else str(capacity_root),source_pbs_jobs=jobs,resource_basis='initial_ceiling' if capacity_root is None else 'measured_capacity',capacity_completion=capacity_evidence)
        script=audit_root/'trace-audit.sh';phase_root=audit_root
    return dict(ledger=ledger,baseline=baseline,script=str(script),phase_root=str(phase_root),initial_ceiling=phase=='trace-audit' and capacity_root is None)


def script_text(record,plan_path):
    text=s.render_script(Path(record['bundle']),Path(record['destination']),Path(record['command'][1]),record['resource'],['unused'])
    lines=text.splitlines()
    lines[-1]=shlex.join([str(Path(record['bundle'])/'venv/bin/python'),str(Path(__file__).resolve()),'compute','--plan',str(plan_path)])
    return '\n'.join(lines)+'\n'


def prepare(bundle,destination,phase,*,index=None,audit_root=None,capacity_root=None,capacity_pins=None):
    bundle,destination=map(s.absolute,(bundle,destination))
    for path in (bundle,destination,audit_root or '',capacity_root or '',Path(__file__).resolve()):
        require(not any(char.isspace() for char in str(path)),'PBS paths must not contain whitespace')
    context=plan_inputs(bundle,destination,phase,index,audit_root,capacity_root,capacity_pins,fresh=True)
    origin=s.read_staged_provenance(destination);snapshot=software()
    resource,budget=s.budget_resources(context['baseline'],origin,initial_ceiling=context['initial_ceiling'])
    script=s.absolute(context['script']);plan_path=script.parent/'staging-control-plan.json'
    require(not any(path.exists() or path.is_symlink() for path in (script,plan_path,script.parent/'staging-submission-plan.json')),'fresh control script and plan required')
    record=dict(context['ledger'],command=['qsub',str(script)],resource=resource,baseline_resource=context['baseline'],staging_budget=budget,
        phase=phase,index=index,bundle=str(bundle),destination=str(destination),audit_root=None if audit_root is None else str(s.absolute(audit_root)),
        capacity_root=None if capacity_root is None else str(s.absolute(capacity_root)),capacity_pins=capacity_pins,phase_root=context['phase_root'],context=context,
        software=snapshot,staging_origin=origin,staging_helper=str(Path(s.__file__).resolve()),control_helper=str(Path(__file__).resolve()),
        submit_source_sha256=c.file_hash(__file__),compute_full_payload_gate=True,submission_ready=True)
    script.parent.mkdir(parents=True,exist_ok=True)
    with script.open('xb') as stream:stream.write(script_text(record,plan_path).encode())
    record['script_sha256']=c.file_hash(script)
    require(software()==snapshot and s.read_staged_provenance(destination)==origin,'prepare context changed')
    s.write_new(plan_path,record)
    return record


def checked(plan_path,expected_sha=None):
    plan_path=s.regular(s.absolute(plan_path));record,digest=s.json_snapshot(plan_path)
    require(expected_sha is None or digest==expected_sha,'parent prepared pin differs')
    require(record['control_helper']==str(Path(__file__).resolve()) and record['submit_source_sha256']==c.file_hash(__file__),'control source differs')
    require(record['software']==software(),'source/runtime/native/Python differs')
    origin=s.read_staged_provenance(record['destination'])
    require(origin==record['staging_origin'],'staging provenance differs')
    context=plan_inputs(record['bundle'],record['destination'],record['phase'],record['index'],record['audit_root'],record['capacity_root'],record['capacity_pins'])
    require(context==record['context'],'fixed scientific plan or baseline resource differs')
    resource,budget=s.budget_resources(context['baseline'],origin,initial_ceiling=context['initial_ceiling'])
    require(resource==record['resource'] and budget==record['staging_budget'] and context['baseline']==record['baseline_resource'],'prepared adjusted resource differs')
    require(record['command']==['qsub',context['script']] and plan_path==Path(context['script']).parent/'staging-control-plan.json','script/control path differs')
    script=s.regular(record['command'][1])
    require(c.file_hash(script)==record['script_sha256'] and script.read_bytes()==script_text(record,plan_path).encode(),'actual guarded script/argv differs')
    require(c.file_hash(plan_path)==digest,'prepared plan changed while consumed')
    return record,digest


def pre_submit(plan_path,expected_sha):
    require(isinstance(expected_sha,str) and re.fullmatch(r'[0-9a-f]{64}',expected_sha),'explicit parent prepared SHA pin required')
    record,digest=checked(plan_path,expected_sha);folder=Path(plan_path).parent
    require(not any((folder/name).exists() or (folder/name).is_symlink() for name in ('submission-intent.json','submission.json','control-execution-intent.json','control-completion.json')),'existing intent/receipt/execution; never retry')
    require(not Path(record['phase_root'],'execution-intent.json').exists(),'existing phase execution')
    return dict(prepared_sha256=digest,command=record['command'],resource=record['resource'],qsub_executed=False,
                warning='Parent must hold the shared submission lock, reject live controllers, count queued nodes and submit once.')


def receipt(plan_path,record,expected_sha=None):
    folder=Path(plan_path).parent
    intent,ih=s.json_snapshot(folder/'submission-intent.json');submitted,rh=s.json_snapshot(folder/'submission.json')
    require(expected_sha is None or rh==expected_sha,'parent receipt pin differs')
    require(intent==record and {k:v for k,v in submitted.items() if k!='job_id'}==record,'parent submission record differs')
    job=submitted.get('job_id')
    require(isinstance(job,str) and re.fullmatch(r'\d+(?:\.[A-Za-z0-9_.-]+)?',job),'actual PBS job ID required')
    return dict(job_id=job,intent_sha256=ih,receipt_sha256=rh)


def memory_bytes(value):
    match=re.fullmatch(r'(\d+)(b|kb|mb|gb|tb)',str(value).lower())
    require(match is not None,'PBS memory format differs')
    return int(match[1])*1024**('b','kb','mb','gb','tb').index(match[2])


def pbs(record,job,*,terminal,hostname):
    resource=record['resource'];actual=job.get('Resource_List',{})
    require(job.get('Submit_arguments')==record['command'][1] and job.get('run_count')==1,'actual PBS script or run_count differs')
    require(actual.get('nodect')==1 and actual.get('ncpus')==resource['cpus'] and resource['cpus']==96,'actual PBS CPU/node resources differ')
    require(memory_bytes(actual.get('mem'))==resource['memory_gb']*1024**3 and actual.get('walltime')==resource['walltime'],'actual PBS memory/walltime differs')
    select=str(actual.get('select','')).split(':')
    require(select[0]=='1' and '+' not in str(actual.get('select')),'actual PBS select node count differs')
    selected=dict(item.split('=',1) for item in select[1:])
    require(selected.get('ncpus')==str(resource['cpus']) and memory_bytes(selected.get('mem'))==resource['memory_gb']*1024**3,'actual PBS select resource differs')
    hosts={value.split('/')[0] for value in str(job.get('exec_host','')).split('+')}
    require(hostname in hosts and len(hosts)==1,'actual PBS execution host differs')
    require(job.get('job_state')=='F' if terminal else job.get('job_state')=='R','PBS must be terminal F' if terminal else 'PBS must be running')
    if terminal:require(type(job.get('Exit_status')) is int,'actual PBS exit status required')
    return dict(job_state=job['job_state'],exit_status=job.get('Exit_status'),run_count=job['run_count'],resource=actual,exec_host=job['exec_host'],script=job['Submit_arguments'])


def phase_evidence(record):
    root=Path(record['phase_root']);destination=Path(record['destination'])
    if record['phase']=='analysis':
        snapshots={str(root/name):s.json_snapshot(root/name)[1] for name in ('summary.json','execution-intent.json','native_preflight.json')}
        wrapper=p.read_plan(destination);summary,digest=p.partition_evidence(destination,wrapper,record['index'])
        require(s.hashes({path:Path(path) for path in snapshots})==snapshots and snapshots[str(root/'summary.json')]==digest,'analysis metadata changed while consumed')
        return dict(status='success',pbs_job_id=summary['pbs_job_id'],hostname=summary['hostname'],summary_sha256=digest,
                    groups=len(summary['groups']),rows=summary['rows'],native_sha256=summary['native_preflight_sha256'],intent_sha256=summary['execution_intent_sha256'])
    plan,sampling=r.read_plan(root,destination)
    summary,summary_hash=s.json_snapshot(root/'summary.json');intent,ih=s.json_snapshot(root/'execution-intent.json');native,nh=s.json_snapshot(root/'native_preflight.json')
    expected=r.groups(plan);rows=summary['records']
    require(summary['manifest']==c.digest(plan) and summary['groups']==len(expected) and [tuple(row['group']) for row in rows]==expected,'audit group census incomplete')
    tasks=len(sampling['condition']['rungs'])*sampling['condition']['chains']
    require(all(row['planned_tasks']==tasks and row['status'] in ('ok','failed') and type(row['failed_sampling']) is int and 0<=row['failed_sampling']<=tasks for row in rows),'audit per-group task census differs')
    require(summary['planned_tasks']==len(expected)*tasks and summary['failed_sampling']==sum(row['failed_sampling'] for row in rows),'audit task denominator differs')
    changed={tuple(row['group']) for row in summary['input_changes']}
    require(changed.issubset(set(expected)),'audit changed-group census differs')
    failed={tuple(row['group']) for row in rows if row['status']!='ok'}|changed
    require(summary['failed_audit_groups']==len(failed),'audit failed-group census differs')
    identity=dict(manifest=c.digest(plan),sampling_manifest=c.digest(sampling),workers=plan['workers'],pbs_job_id=intent.get('pbs_job_id'),hostname=intent.get('hostname'))
    require(intent==identity and intent['pbs_job_id'] and intent['hostname'] and {k:v for k,v in native.items() if k!='evidence'}==intent and nh==summary['native_preflight_sha256'],'audit native execution identity differs')
    profile,ph=s.json_snapshot(root/'platform_profile.json');fixture,fh=s.json_snapshot(root/'platform_fixture.json')
    evidence=native['evidence']
    require(evidence.get('native_platform_verified') is True and evidence['platform_profile']==c.digest(profile) and evidence['platform_fixture']==c.digest(fixture) and re.fullmatch(r'[0-9a-f]{64}',evidence['actual_profile']),'saved audit native evidence differs')
    require(summary['native_platform_verified'] is True and summary['all_physical_states_redecoded'] is False,'audit native/completeness flag differs')
    for path,digest in ((root/'summary.json',summary_hash),(root/'execution-intent.json',ih),(root/'native_preflight.json',nh),(root/'platform_profile.json',ph),(root/'platform_fixture.json',fh)):
        require(c.file_hash(path)==digest,'audit metadata changed while consumed')
    return dict(status='complete_recorded_failure' if failed or summary['context_error'] is not None else 'success',
        pbs_job_id=intent['pbs_job_id'],hostname=intent['hostname'],groups=len(expected),planned_tasks=summary['planned_tasks'],
        failed_sampling=summary['failed_sampling'],failed_audit_groups=len(failed),context_error=summary['context_error'],summary_sha256=summary_hash,native_sha256=nh,intent_sha256=ih)


def run_phase(record):
    if record['phase']=='analysis':return p.run_partition(Path(record['destination']),p.read_plan(record['destination']),record['index'])
    return r.run(Path(record['audit_root']),Path(record['destination']))


def compute(plan_path,*,job_query=None):
    require(os.environ.get('PBS_JOBID'),'PBS required before any compute I/O')
    require(all(os.environ.get(key)==value for key,value in r.THREADS.items()),'pinned compute thread environment required')
    job_query=job_query or s.query_job
    record,digest=checked(plan_path);submitted=receipt(plan_path,record)
    require(submitted['job_id']==os.environ['PBS_JOBID'],'compute job differs from parent receipt')
    host=socket.gethostname();pbs(record,job_query(submitted['job_id']),terminal=False,hostname=host)
    folder=Path(plan_path).parent
    require(not any((folder/name).exists() for name in ('control-execution-intent.json','control-completion.json')),'existing control execution; no rerun')
    intent=dict(prepared_sha256=digest,**submitted,hostname=host,software=record['software'])
    s.write_new(folder/'control-execution-intent.json',intent)
    intent_hash=c.file_hash(folder/'control-execution-intent.json')
    before=s.read_staged(record['destination']);error=None
    try:run_phase(record)
    except Exception as caught:error=caught
    after=s.read_staged(record['destination']);require(before==after,'full staging evidence changed across compute')
    evidence=phase_evidence(record)
    require(evidence['pbs_job_id']==submitted['job_id'] and evidence['hostname']==host,'phase job/hostname differs')
    require(evidence['status'] in ('success','complete_recorded_failure'),'unknown completion status')
    require((error is None)==(evidence['status']=='success'),'phase exception and complete recorded failure differ')
    again,ah=checked(plan_path,digest)
    require(again==record and receipt(plan_path,record)==submitted,'compute context or receipt changed')
    require(s.json_snapshot(folder/'control-execution-intent.json')==(intent,intent_hash),'control execution intent changed during compute')
    result=dict(intent,status=evidence['status'],phase_evidence=evidence,full_gate_digest=c.digest(before),
                exception=None if error is None else repr(error),control_intent_sha256=intent_hash)
    s.write_new(folder/'control-completion.json',result)
    return result


def read_completion(plan_path,prepared_sha,receipt_sha,*,job_query=None):
    require(all(isinstance(value,str) and re.fullmatch(r'[0-9a-f]{64}',value) for value in (prepared_sha,receipt_sha)),'explicit parent prepared and receipt SHA pins required')
    job_query=job_query or s.query_job
    record,digest=checked(plan_path,prepared_sha);submitted=receipt(plan_path,record,receipt_sha)
    folder=Path(plan_path).parent;complete,ch=s.json_snapshot(folder/'control-completion.json');intent,ih=s.json_snapshot(folder/'control-execution-intent.json')
    expected=dict(prepared_sha256=digest,**submitted,hostname=complete['hostname'],software=record['software'])
    require(intent==expected and all(complete[key]==value for key,value in expected.items()) and complete['control_intent_sha256']==ih,'compute completion identity differs')
    evidence=phase_evidence(record);require(evidence==complete['phase_evidence'] and evidence['pbs_job_id']==submitted['job_id'] and evidence['hostname']==complete['hostname'] and evidence['status']==complete['status'],'phase completion differs')
    actual=pbs(record,job_query(submitted['job_id']),terminal=True,hostname=complete['hostname'])
    expected_exit=0 if complete['status']=='success' else 1
    require(actual['exit_status']==expected_exit,'PBS exit differs from completed phase contract')
    require(checked(plan_path,digest)[0]==record and receipt(plan_path,record,receipt_sha)==submitted,'terminal context changed')
    require(c.file_hash(folder/'control-completion.json')==ch and c.file_hash(folder/'control-execution-intent.json')==ih,'terminal marker changed')
    require(pbs(record,job_query(submitted['job_id']),terminal=True,hostname=complete['hostname'])==actual,'terminal PBS evidence changed while consumed')
    return dict(status=complete['status'],phase_evidence=evidence,pbs=actual,job_id=submitted['job_id'],prepared_sha256=digest,receipt_sha256=receipt_sha,completion_sha256=ch)


def read_all(destination,audit_root,pins,*,job_query=None):
    destination,audit_root=map(s.absolute,(destination,audit_root));wrapper=p.read_plan(destination)
    expected={str(destination/'analysis-submissions'/str(part['index'])/'staging-control-plan.json') for part in wrapper['resources']['partitions']}
    expected.add(str(audit_root/'staging-control-plan.json'))
    require(len(pins)==len(expected) and {row['plan'] for row in pins}==expected,'all-partition/audit pin census differs')
    plan,_=r.read_plan(audit_root,destination);require(plan['purpose']=='low_noise_trace_audit_full' and plan['replicates']==192,'full 192-replicate audit required')
    result={row['plan']:read_completion(row['plan'],row['prepared_sha256'],row['receipt_sha256'],job_query=job_query) for row in pins}
    require(len({row['job_id'] for row in result.values()})==len(result),'PBS job reused across independent phases')
    return result


def collect(destination,audit_root,pins,*,job_query=None):
    require(os.environ.get('PBS_JOBID'),'PBS required before collection I/O')
    before=read_all(destination,audit_root,pins,job_query=job_query)
    require(all(row['status']=='success' for row in before.values()),'recorded audit failure retained; successful audited collection unavailable')
    result=s.read_staged_audited_collection(destination,audit_root)
    require(read_all(destination,audit_root,pins,job_query=job_query)==before,'terminal PBS evidence changed across collection')
    return result[0],result[1],dict(result[2],staged_control_completion=before)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action',choices=('compute','pre-submit','read-completion'))
    parser.add_argument('--plan',type=Path,required=True);parser.add_argument('--prepared-sha256');parser.add_argument('--receipt-sha256')
    args=parser.parse_args()
    if args.action=='compute':
        result=compute(args.plan);print(json.dumps(dict(status=result['status'],job_id=result['job_id'])))
        raise SystemExit(0 if result['status']=='success' else 1)
    if args.action=='pre-submit':result=pre_submit(args.plan,args.prepared_sha256)
    else:result=read_completion(args.plan,args.prepared_sha256,args.receipt_sha256)
    print(json.dumps(result))


if __name__=='__main__':main()
