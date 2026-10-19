"""Small metadata fixtures for real staged PBS argv, resources, and completion gates."""
import json
from pathlib import Path
import sys
import pytest
for dependency in ('ldpc','bposd','pymatching'):pytest.importorskip(dependency)
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'cluster_scripts'))
import tile_low_noise_staging_control as x


@pytest.fixture
def fixture(tmp_path,monkeypatch):
    bundle=tmp_path/'bundle';destination=bundle/'runs/staged';destination.mkdir(parents=True)
    folder=destination/'analysis-submissions/0';phase=destination/'analysis-partitions/0'
    origin=dict(sealed=True,summary_sha256='copy',copy_pbs_job_id='100.test',copy_exit_status=0,copy_elapsed_seconds=200.)
    context=dict(ledger=dict(partition=0,partition_manifest='parts',manifest='science',bundle_binding={}),
                 baseline=dict(cpus=96,memory_gb=32,workers=8,wall_seconds=3600,walltime='01:00:00',requested_nodes=1,max_nodes=2),
                 script=str(folder/'partition.sh'),phase_root=str(phase),initial_ceiling=False)
    monkeypatch.setattr(x,'plan_inputs',lambda *args,**kwargs:context)
    monkeypatch.setattr(x,'software',lambda:{'source':'fixed','python':'fixed','native':'fixed'})
    monkeypatch.setattr(x.s,'read_staged_provenance',lambda _:dict(origin))
    full=[]
    def read(_):full.append(True);return dict(origin)
    monkeypatch.setattr(x.s,'read_staged',read)
    plan=x.prepare(bundle,destination,'analysis',index=0)
    path=folder/'staging-control-plan.json';digest=x.c.file_hash(path)
    x.s.write_new(folder/'submission-intent.json',plan)
    x.s.write_new(folder/'submission.json',dict(plan,job_id='200.test'))
    receipt=x.c.file_hash(folder/'submission.json')
    job=dict(job_state='R',Submit_arguments=str(folder/'partition.sh'),run_count=1,exec_host='node/0*96',
             Resource_List=dict(select='1:ncpus=96:mem=32gb',ncpus=96,nodect=1,mem='33554432kb',walltime='02:00:00'))
    monkeypatch.setenv('PBS_JOBID','200.test');monkeypatch.setattr(x.socket,'gethostname',lambda:'node')
    for key,value in x.r.THREADS.items():monkeypatch.setenv(key,value)
    monkeypatch.setattr(x,'phase_evidence',lambda record:dict(status='success',pbs_job_id='200.test',hostname='node',groups=1,summary_sha256='summary'))
    monkeypatch.setattr(x,'run_phase',lambda record:{'done':True})
    return path,digest,receipt,job,full,context,origin


def test_actual_script_argv_and_adjusted_resources(fixture):
    path,_,_,_,_,_,_=fixture;record=json.loads(path.read_bytes());script=Path(record['command'][1]).read_text()
    assert 'walltime=02:00:00' in script and 'compute --plan' in script
    assert str(Path(x.__file__).resolve()) in script
    assert record['staging_budget']['additional_raw_hash_passes']==4
    assert record['baseline_resource']['walltime']=='01:00:00'


def test_compute_then_external_terminal(fixture):
    path,digest,receipt,job,full,_,_=fixture
    result=x.compute(path,job_query=lambda _:job)
    assert result['status']=='success' and len(full)==2
    with pytest.raises(ValueError,match='terminal'):x.read_completion(path,digest,receipt,job_query=lambda _:job)
    job.update(job_state='F',Exit_status=0)
    result=x.read_completion(path,digest,receipt,job_query=lambda _:job)
    assert result['status']=='success' and len(full)==2


@pytest.mark.parametrize('change',['cpu','mem','wall','nodes','rerun','script','host'])
def test_actual_pbs_mismatch_rejects_before_raw_scan(fixture,change):
    path,_,_,job,full,_,_=fixture
    if change=='cpu':job['Resource_List']['ncpus']=48
    elif change=='mem':job['Resource_List']['mem']='16gb'
    elif change=='wall':job['Resource_List']['walltime']='01:00:00'
    elif change=='nodes':job['Resource_List']['nodect']=2
    elif change=='rerun':job['run_count']=2
    elif change=='script':job['Submit_arguments']='other.sh'
    else:job['exec_host']='other/0'
    with pytest.raises(ValueError):x.compute(path,job_query=lambda _:job)
    assert full==[]


def test_missing_pbs_rejects_before_io(fixture,monkeypatch):
    path,*_=fixture;monkeypatch.delenv('PBS_JOBID')
    monkeypatch.setattr(x.s,'json_snapshot',lambda _:pytest.fail('no I/O without PBS'))
    with pytest.raises(ValueError,match='PBS'):x.compute(path)


@pytest.mark.parametrize('change',['prepared','receipt','script','source','origin','context'])
def test_pinned_inputs_reject_changes(fixture,monkeypatch,change):
    path,digest,receipt,job,_,context,origin=fixture
    if change=='prepared':path.write_text('{}')
    elif change=='receipt':(path.parent/'submission.json').write_text('{}')
    elif change=='script':(path.parent/'partition.sh').write_text('other argv')
    elif change=='source':monkeypatch.setattr(x,'software',lambda:{'source':'changed'})
    elif change=='origin':origin['summary_sha256']='changed'
    else:context['baseline']['walltime']='03:00:00'
    with pytest.raises(ValueError):x.read_completion(path,digest,receipt,job_query=lambda _:job)


def test_recorded_audit_failure_keeps_completion_and_nonzero_exit(fixture,monkeypatch):
    path,digest,receipt,job,full,_,_=fixture
    monkeypatch.setattr(x,'phase_evidence',lambda record:dict(status='complete_recorded_failure',pbs_job_id='200.test',hostname='node',groups=768,failed_audit_groups=1,planned_tasks=61440,failed_sampling=7,summary_sha256='summary'))
    def fail(_):raise RuntimeError('retained audit failure')
    monkeypatch.setattr(x,'run_phase',fail)
    result=x.compute(path,job_query=lambda _:job)
    assert result['status']=='complete_recorded_failure' and len(full)==2
    job.update(job_state='F',Exit_status=1)
    complete=x.read_completion(path,digest,receipt,job_query=lambda _:job)
    assert complete['phase_evidence']['planned_tasks']==61440 and complete['phase_evidence']['failed_sampling']==7


def test_incomplete_exception_has_no_success_marker(fixture,monkeypatch):
    path,_,_,job,full,*_=fixture
    def fail(_):raise RuntimeError('partial output')
    monkeypatch.setattr(x,'run_phase',fail);monkeypatch.setattr(x,'phase_evidence',fail)
    with pytest.raises(RuntimeError):x.compute(path,job_query=lambda _:job)
    assert len(full)==2 and not (path.parent/'control-completion.json').exists()


def test_post_full_gate_failure_is_not_completion(fixture,monkeypatch):
    path,_,_,job,*_=fixture;calls=[]
    def fail(_):
        calls.append(True)
        if len(calls)==2:raise ValueError('changed raw')
        return {'before':True}
    monkeypatch.setattr(x.s,'read_staged',fail)
    with pytest.raises(ValueError):x.compute(path,job_query=lambda _:job)
    assert not (path.parent/'control-completion.json').exists()


@pytest.mark.parametrize('status,exitcode',[('success',1),('complete_recorded_failure',0),('complete_recorded_failure',271)])
def test_terminal_exit_contract(fixture,monkeypatch,status,exitcode):
    path,digest,receipt,job,*_=fixture
    monkeypatch.setattr(x,'phase_evidence',lambda _:dict(status=status,pbs_job_id='200.test',hostname='node',summary_sha256='summary'))
    if status!='success':monkeypatch.setattr(x,'run_phase',lambda _:(_ for _ in ()).throw(RuntimeError('audit')))
    x.compute(path,job_query=lambda _:job);job.update(job_state='F',Exit_status=exitcode)
    with pytest.raises(ValueError,match='exit'):x.read_completion(path,digest,receipt,job_query=lambda _:job)


def test_pre_submit_is_readonly_and_no_retry(fixture):
    path,digest,*_=fixture
    with pytest.raises(ValueError,match='existing'):x.pre_submit(path,digest)


def test_all_partitions_and_full_audit_are_mandatory(tmp_path,monkeypatch):
    monkeypatch.setattr(x.p,'read_plan',lambda _:dict(resources=dict(partitions=[dict(index=0),dict(index=1)])))
    with pytest.raises(ValueError,match='census'):x.read_all(tmp_path,tmp_path/'audit',[],job_query=lambda _:None)


@pytest.mark.parametrize('function',['pre_submit','read_completion'])
def test_parent_pins_are_not_optional(fixture,function):
    path,*_=fixture
    with pytest.raises(ValueError,match='explicit parent'):
        x.pre_submit(path,None) if function=='pre_submit' else x.read_completion(path,None,None)


def test_control_intent_mutation_during_compute_rejects(fixture,monkeypatch):
    path,_,_,job,*_=fixture
    def mutate(record):(path.parent/'control-execution-intent.json').write_text('{}')
    monkeypatch.setattr(x,'run_phase',mutate)
    with pytest.raises(ValueError,match='intent changed'):x.compute(path,job_query=lambda _:job)
    assert not (path.parent/'control-completion.json').exists()


def test_real_audit_metadata_preserves_failure_denominator(tmp_path,monkeypatch):
    root=tmp_path/'audit';root.mkdir();sampling=dict(condition=dict(rungs=[.03,.05],chains=2))
    plan=dict(case=2,target_index=0,replicates=2,workers=8)
    monkeypatch.setattr(x.r,'read_plan',lambda *_:(plan,sampling))
    groups=x.r.groups(plan)
    rows=[dict(group=list(group),planned_tasks=4,failed_sampling=1,status='failed' if index==0 else 'ok') for index,group in enumerate(groups)]
    identity=dict(manifest=x.c.digest(plan),sampling_manifest=x.c.digest(sampling),workers=8,pbs_job_id='200.test',hostname='node')
    x.s.write_new(root/'execution-intent.json',identity)
    x.s.write_new(root/'platform_profile.json',{});x.s.write_new(root/'platform_fixture.json',{})
    native=dict(identity,evidence=dict(native_platform_verified=True,platform_profile=x.c.digest({}),platform_fixture=x.c.digest({}),actual_profile='a'*64))
    x.s.write_new(root/'native_preflight.json',native)
    summary=dict(manifest=x.c.digest(plan),groups=8,records=rows,planned_tasks=32,failed_sampling=8,input_changes=[],failed_audit_groups=1,
                 context_error=None,native_preflight_sha256=x.c.file_hash(root/'native_preflight.json'),native_platform_verified=True,all_physical_states_redecoded=False)
    x.s.write_new(root/'summary.json',summary)
    record=dict(phase='trace-audit',phase_root=str(root),destination=str(tmp_path/'source'))
    result=x.phase_evidence(record)
    assert result['status']=='complete_recorded_failure' and result['groups']==8 and result['planned_tasks']==32 and result['failed_sampling']==8
    summary['records'].pop();(root/'summary.json').write_bytes(x.c.canonical(summary))
    with pytest.raises(ValueError,match='census'):x.phase_evidence(record)


def test_real_analysis_partition_metadata_reader(tmp_path,monkeypatch):
    root=tmp_path/'source';phase=root/'analysis-partitions/0';phase.mkdir(parents=True)
    group=[2,0,0,0,0];plan={'example':True};wrapper=dict(production=plan,resources=dict(workers=8,partitions=[dict(groups=[group])]))
    monkeypatch.setattr(x.p,'read_plan',lambda _:wrapper)
    monkeypatch.setattr(x.p.a,'analysis_settings',lambda _:iter([None]))
    monkeypatch.setattr(x.p.low.native.trace_audit,'validate_platform',lambda *_:None)
    x.s.write_new(root/'platform_profile.json',{})
    intent=dict(partition_manifest=x.c.digest(wrapper),partition=0,groups=[group],workers=8,manifest=x.c.digest(plan),pbs_job_id='200.test',hostname='node')
    x.s.write_new(phase/'execution-intent.json',intent)
    native=dict(manifest=intent['manifest'],pbs_job_id='200.test',hostname='node',profile={})
    x.s.write_new(phase/'native_preflight.json',native)
    summary=dict(intent,execution_intent_sha256=x.c.file_hash(phase/'execution-intent.json'),native_preflight_sha256=x.c.file_hash(phase/'native_preflight.json'),group_marker_sha256={x.c.task_id(group):'marker'},rows=1)
    x.s.write_new(phase/'summary.json',summary)
    record=dict(phase='analysis',index=0,destination=str(root),phase_root=str(phase))
    assert x.phase_evidence(record)['rows']==1
    summary['rows']=0;(phase/'summary.json').write_bytes(x.c.canonical(summary))
    with pytest.raises(ValueError,match='denominator'):x.phase_evidence(record)


def test_read_all_calls_every_partition_and_full_audit(tmp_path,monkeypatch):
    audit=tmp_path/'audit';source=tmp_path/'source'
    monkeypatch.setattr(x.p,'read_plan',lambda _:dict(resources=dict(partitions=[dict(index=0),dict(index=1)])))
    monkeypatch.setattr(x.r,'read_plan',lambda *_:(dict(purpose='low_noise_trace_audit_full',replicates=192),{}))
    paths=[source/'analysis-submissions/0/staging-control-plan.json',source/'analysis-submissions/1/staging-control-plan.json',audit/'staging-control-plan.json']
    pins=[dict(plan=str(path),prepared_sha256='a'*64,receipt_sha256='b'*64) for path in paths];calls=[]
    def completion(path,*args,**kwargs):calls.append(path);return dict(job_id=str(len(calls)),status='success')
    monkeypatch.setattr(x,'read_completion',completion)
    result=x.read_all(source,audit,pins)
    assert set(result)==set(map(str,paths)) and len(calls)==3


def test_full_resource_uses_terminal_capacity_metadata_without_raw_scan(tmp_path,monkeypatch):
    bundle=tmp_path/'bundle';source=bundle/'runs/source';audit=bundle/'runs/full';caproot=bundle/'runs/capacity'
    source.mkdir(parents=True);audit.mkdir();caproot.mkdir()
    cap=dict(case=2,target_index=0,purpose='low_noise_trace_audit_capacity',replicates=2,workers=8,sampling_manifest='sample')
    full=dict(cap,purpose='low_noise_trace_audit_full',replicates=192,workers=96)
    rows=[dict(group=list(group),status='ok',failed_audits=0,failed_sampling=0,summary_group_digest_verified=True,planned_tasks=4,redecoded_checkpoints=8,wall_seconds=1.,cpu_seconds=1.,peak_rss_mb=10.) for group in x.r.groups(cap)]
    summary=dict(manifest=x.c.digest(cap),groups=8,records=rows,failed_audit_groups=0,failed_sampling=0,context_error=None,input_changes=[],native_platform_verified=True,planned_tasks=32,phase_wall_seconds=2.)
    completed=dict(status='success',job_id='cap.test',completion_sha256='fixed')
    monkeypatch.setattr(x,'capacity_completion',lambda *_:(cap,{},summary,completed))
    monkeypatch.setattr(x.r,'read_plan',lambda *_:(full,{}))
    monkeypatch.setattr(x.rs,'bundle_binding',lambda *_:{})
    monkeypatch.setattr(x.rs,'checked_plan',lambda *_:pytest.fail('old full checked_plan scans raw'))
    monkeypatch.setattr(x.rs.res,'measured_capacity',lambda *_:pytest.fail('no old raw reader on login'))
    monkeypatch.setattr(x.r,'verify_group_inputs',lambda *_:pytest.fail('no raw source walk'))
    for phase in ('sample','anchors'):x.s.write_new(source/(phase+'-execution-intent.json'),dict(pbs_job_id='original.test'))
    result=x.plan_inputs(bundle,source,'trace-audit',audit_root=audit,capacity_root=caproot,capacity_pins={})
    assert result['baseline']['workers']==96 and result['ledger']['capacity_completion']==completed
    summary['failed_sampling']=1
    with pytest.raises(ValueError,match='without sampling failures'):x.plan_inputs(bundle,source,'trace-audit',audit_root=audit,capacity_root=caproot,capacity_pins={})


@pytest.mark.parametrize('status',['success','complete_recorded_failure'])
def test_capacity_terminal_pins_and_failure_policy(tmp_path,monkeypatch,status):
    root=tmp_path/'cap';root.mkdir();source=tmp_path/'source'
    x.s.write_new(root/'staging-control-plan.json',dict(phase='trace-audit',capacity_root=None,destination=str(source)))
    x.s.write_new(root/'summary.json',{})
    calls=[]
    def complete(path,prepared,receipt):
        calls.append((path,prepared,receipt))
        return dict(status=status,phase_evidence=dict(summary_sha256=x.c.file_hash(root/'summary.json')))
    monkeypatch.setattr(x,'read_completion',complete);monkeypatch.setattr(x.r,'read_plan',lambda *_:({},{}))
    pins=dict(prepared_sha256='a'*64,receipt_sha256='b'*64)
    if status=='success':assert x.capacity_completion(root,source,pins)[2]=={}
    else:
        with pytest.raises(ValueError,match='successful capacity'):x.capacity_completion(root,source,pins)
    assert calls==[(root/'staging-control-plan.json','a'*64,'b'*64)]


def test_compute_wrong_threads_rejects_before_io(fixture,monkeypatch):
    path,*_=fixture;monkeypatch.setenv('OMP_NUM_THREADS','2')
    monkeypatch.setattr(x.s,'json_snapshot',lambda _:pytest.fail('no I/O before thread gate'))
    with pytest.raises(ValueError,match='thread'):x.compute(path)


@pytest.mark.parametrize('field',['rerun','resources'])
def test_terminal_pbs_change_at_end_rejects(fixture,field):
    path,digest,receipt,job,*_=fixture
    x.compute(path,job_query=lambda _:job);job.update(job_state='F',Exit_status=0)
    calls=[]
    def query(_):
        calls.append(True)
        result=json.loads(json.dumps(job))
        if len(calls)==2:
            if field=='rerun':result['run_count']=2
            else:result['Resource_List']['walltime']='01:00:00'
        return result
    with pytest.raises(ValueError):x.read_completion(path,digest,receipt,job_query=query)
    assert len(calls)==2


def test_fresh_pre_submit_returns_fixed_command_without_qsub(fixture,monkeypatch):
    path,digest,_,_,full,*_=fixture
    (path.parent/'submission-intent.json').unlink();(path.parent/'submission.json').unlink()
    monkeypatch.setattr(x.s.subprocess,'run',lambda *_a,**_k:pytest.fail('read-only pre-submit must not call qsub'))
    result=x.pre_submit(path,digest)
    assert result['qsub_executed'] is False and result['resource']['walltime']=='02:00:00' and full==[]
