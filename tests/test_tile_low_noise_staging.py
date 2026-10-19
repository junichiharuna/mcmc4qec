"""Small sealed-copy fixtures; no cluster submission or scientific simulation."""
from pathlib import Path
import json
import sys

import pytest

for dependency in ('ldpc','bposd','pymatching'):
    pytest.importorskip(dependency)
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'cluster_scripts'))
import calibration as c
import tile_low_noise_staging as s


@pytest.fixture
def fixture(tmp_path,monkeypatch):
    source=tmp_path/'sampling';source.mkdir();bundle=tmp_path/'analysis';(bundle/'runs').mkdir(parents=True)
    control=tmp_path/'copy-control';target=bundle/'runs/copied'
    monkeypatch.setattr(s,'REPLICATES',2)
    plan=dict(purpose='low_noise_production',case=2,target_index=0,replicates=2,
              condition=dict(rungs=[.1],chains=1),native_input_digests={key:c.digest({}) for key in ('platform_profile','platform_fixture')})
    c.atomic_json(source/'manifest.json',plan)
    for key in ('platform_profile','platform_fixture'):c.atomic_json(source/(key+'.json'),{})
    monkeypatch.setattr(s.a,'read_production_plan',lambda root:json.loads((Path(root)/'manifest.json').read_text()))
    monkeypatch.setattr(s.low.native.trace_audit,'validate_platform',lambda *args:None)
    software=tmp_path/'accepted.py';software.write_bytes(b'fixed source')
    plan['sources']=dict(driver=c.file_hash(software));c.atomic_json(source/'manifest.json',plan)
    monkeypatch.setattr(s,'software_snapshot',lambda:dict(python='fixture',source_sha256={str(software):c.file_hash(software)}))
    for phase in ('sample','anchors'):
        rows=[]
        for task in s.low.tasks(plan,phase):
            record=dict(task=list(task),status='ok',wall_seconds=1.,cpu_seconds=.5,peak_rss_mb=1.)
            c.save_artifact(source/('traces' if phase=='sample' else 'anchors')/c.task_id(task),dict(manifest=c.digest(plan),task=list(task)),{},record)
            rows.append(record)
        intent=dict(manifest=c.digest(plan),phase=phase,pbs_job_id='123.test',hostname='test-node')
        c.atomic_json(source/(phase+'-execution-intent.json'),intent)
        native=source/('preflight-'+phase)/'native_preflight.json'
        c.atomic_json(native,dict(manifest=c.digest(plan),pbs_job_id='123.test',hostname='test-node',profile={}))
        c.atomic_json(source/(phase+'-summary.json'),dict(manifest=c.digest(plan),phase=phase,tasks=len(rows),records=rows,failed=0,native_preflight_sha256=c.file_hash(native)))
    script=source/'low-noise.sh';script.write_bytes(b'#!/bin/bash\n')
    receipt=dict(command=['qsub',str(script)],manifest=c.digest(plan),script_sha256=c.file_hash(script),submit_source_sha256=c.file_hash(software))
    c.atomic_json(source/'submission-intent.json',receipt);c.atomic_json(source/'submission.json',dict(receipt,job_id='123.test'))
    job=dict(job_state='F',Exit_status=0,Submit_arguments=str(script),Job_Name='fixture',run_count=1,exec_host='test-node/0')
    binding=dict(source_sha256={str(software):c.file_hash(software)},source_job_id='123.test',input_sha256={name:c.file_hash(source/name) for name in ('manifest.json','submission-intent.json','submission.json','low-noise.sh')})
    copy_job=dict(job_state='F',Exit_status=0,Submit_arguments=str(control/'stage.sh'))
    query=lambda identity:dict(job if identity=='123.test' else copy_job)
    query.copy_job=copy_job
    monkeypatch.setattr(s,'query_job',query)
    monkeypatch.setenv('PBS_JOBID','456.test')
    return source,control,target,bundle,binding,query,job


def prepared(fixture):
    source,control,target,bundle,binding,query,_=fixture
    value=s.prepare(control,source,target,bundle,binding,job_query=query)
    script=control/'stage.sh';script.write_bytes(b'#!/bin/bash\n# copy fixture\n')
    receipt=dict(command=['qsub',str(script)],plan_sha256=c.file_hash(control/'plan.json'),script_sha256=c.file_hash(script))
    c.atomic_json(control/'submission-intent.json',receipt);c.atomic_json(control/'submission.json',dict(receipt,job_id='456.test'))
    return value


def test_complete_copy_keeps_absolute_receipt_and_denominators(fixture):
    source,control,target,_,_,query,_=fixture;prepared(fixture)
    before={str(p.relative_to(source)):p.read_bytes() for p in source.rglob('*') if p.is_file()}
    result=s.run(control,job_query=query)
    assert result['groups']==8 and result['anchors']==2 and result['sample_tasks']==8
    assert result['original_source_root']==str(source) and result['copy_pbs_job_id']=='456.test'
    assert all((target/name).read_bytes()==value==(source/name).read_bytes() for name,value in before.items())
    assert json.loads((target/'submission.json').read_text())['command'][1]==str(source/'low-noise.sh')
    assert s.read_staged(target)['sealed']
    assert s.a.completed_phase_evidence(source,s.a.read_production_plan(source))==s.a.completed_phase_evidence(target,s.a.read_production_plan(target))
    with pytest.raises(ValueError):s.run(control,job_query=query)


@pytest.mark.parametrize('state,exit_status',[('R',None),('F',1)])
def test_reject_live_or_unrecorded_job_failure(fixture,state,exit_status):
    fixture[-1].update(job_state=state,Exit_status=exit_status)
    with pytest.raises(ValueError):prepared(fixture)


def test_recorded_failure_preserves_task_and_group_denominator(fixture):
    source,control,target,_,_,query,job=fixture;plan=s.a.read_production_plan(source)
    task=list(s.low.tasks(plan,'sample'))[0];base=source/'traces'/c.task_id(task)
    record=json.loads(base.with_suffix('.json').read_text());record.update(status='failed',error='retained failure')
    for ext in ('.json','.npz','.done.json'):base.with_suffix(ext).unlink()
    c.save_artifact(base,dict(manifest=c.digest(plan),task=list(task)),{},record)
    p=source/'sample-summary.json';summary=json.loads(p.read_text());summary['records'][0]=record;summary['failed']=1;c.atomic_json(p,summary)
    job['Exit_status']=1;prepared(fixture);result=s.run(control,job_query=query)
    assert result['completion_kind']=='complete_recorded_failure' and result['recorded_failures']['sample']==1
    assert result['sample_tasks']==8 and result['groups']==8 and result['anchors']==2


@pytest.mark.parametrize('change',['missing','extra','payload','marker','summary','software','symlink'])
def test_changed_or_invalid_source_is_rejected(fixture,change,tmp_path):
    source,control,target,_,binding,query,_=fixture;prepared(fixture)
    base=source/'traces/2-0-0-0-0-0-0'
    if change=='missing':base.with_suffix('.npz').unlink()
    elif change=='extra':(source/'traces/extra.json').write_text('{}')
    elif change=='payload':base.with_suffix('.npz').write_bytes(b'changed')
    elif change=='marker':base.with_suffix('.done.json').write_text('{}')
    elif change=='summary':(source/'sample-summary.json').write_text('{}')
    elif change=='software':Path(next(iter(binding['source_sha256']))).write_bytes(b'changed')
    else:
        p=base.with_suffix('.npz');outside=tmp_path/'outside';outside.write_bytes(p.read_bytes());p.unlink()
        try:p.symlink_to(outside)
        except OSError:pytest.skip('symlink unavailable')
    with pytest.raises((ValueError,FileNotFoundError,KeyError)):s.run(control,job_query=query)
    assert not (target/'.staging/seal.json').exists()


def test_copy_time_mutation_keeps_partial_copy_and_intent(fixture,monkeypatch):
    source,control,target,_,_,query,_=fixture;prepared(fixture);original=s.copy_file
    def mutate(src,dst):
        original(src,dst)
        if src.name.endswith('.npz'):src.write_bytes(b'changed during copy')
    monkeypatch.setattr(s,'copy_file',mutate)
    with pytest.raises(ValueError):s.run(control,job_query=query)
    assert (control/'execution-intent.json').exists() and target.exists() and not (target/'.staging/seal.json').exists()


@pytest.mark.parametrize('change',['payload','extra','metadata','seal'])
def test_staged_reader_rejects_changes(fixture,change):
    _,control,target,_,_,query,_=fixture;prepared(fixture);s.run(control,job_query=query)
    path={'payload':'traces/2-0-0-0-0-0-0.npz','extra':'traces/extra.json','metadata':'submission.json','seal':'.staging/seal.json'}[change]
    (target/path).write_bytes(b'{}')
    with pytest.raises((ValueError,KeyError)):s.read_staged(target)


def test_missing_pbs_and_existing_destination_rejected(fixture,monkeypatch):
    _,control,target,_,_,query,_=fixture;prepared(fixture);monkeypatch.delenv('PBS_JOBID')
    with pytest.raises(ValueError):s.run(control,job_query=query)
    monkeypatch.setenv('PBS_JOBID','456.test');target.mkdir()
    with pytest.raises(ValueError):s.run(control,job_query=query)


def test_fixed_production_denominators():
    plan=dict(purpose='low_noise_production',case=2,target_index=0,replicates=192,condition=dict(rungs=list(range(10)),chains=8))
    assert len(list(s.a.groups(plan)))==768 and len(list(s.low.tasks(plan,'anchors')))==192
    assert len(list(s.low.tasks(plan,'sample')))==61440


def test_staging_reader_rejects_payload_change_during_metadata_read(fixture,monkeypatch):
    _,control,target,_,_,query,_=fixture;prepared(fixture);s.run(control,job_query=query)
    original=s.a.completed_phase_evidence
    def mutate(*args):
        result=original(*args);(target/'traces/2-0-0-0-0-0-0.npz').write_bytes(b'changed');return result
    monkeypatch.setattr(s.a,'completed_phase_evidence',mutate)
    with pytest.raises(ValueError,match='changed during read'):s.read_staged(target)


def test_independent_control_record_is_required(fixture):
    _,control,target,_,_,query,_=fixture;prepared(fixture);s.run(control,job_query=query)
    (control/'summary.json').write_text('{}')
    with pytest.raises(ValueError,match='control record'):s.read_staged(target)


@pytest.mark.parametrize('name',['plan_analysis','submit_analysis','plan_trace_audit','submit_trace_audit','read_staged_audited_collection'])
def test_downstream_entry_rejects_unsealed_root(fixture,name):
    _,_,target,bundle,_,_,_=fixture
    arguments={'plan_analysis':(target,Path('capacity')),'submit_analysis':(bundle,target,0),
               'plan_trace_audit':(target,Path('audit')),'submit_trace_audit':(bundle,target,Path('audit')),
               'read_staged_audited_collection':(target,Path('audit'))}[name]
    kwargs=dict(capacity=True,workers=8) if name=='plan_trace_audit' else {}
    with pytest.raises((ValueError,FileNotFoundError)):getattr(s,name)(*arguments,**kwargs)


def test_guarded_analysis_allows_outputs_and_rechecks_inputs(fixture):
    _,control,target,_,_,query,_=fixture;prepared(fixture);s.run(control,job_query=query)
    def analysis():
        (target/'analysis_manifest.json').write_text('{}');(target/'analysis').mkdir();(target/'analysis/example.json').write_text('{}');return 'done'
    assert s.guarded(target,analysis)=='done'
    def corrupt(): (target/'manifest.json').write_text('{}')
    with pytest.raises(ValueError):s.guarded(target,corrupt)


def test_real_production_readers_preserve_192_768_metadata_after_copy(tmp_path):
    source=tmp_path/'original';target=tmp_path/'copied';source.mkdir();target.mkdir()
    plan=s.low.make_plan(2,0,capacity=False)
    c.atomic_json(source/'manifest.json',plan)
    inputs=s.low.native.platform_inputs()
    for name,value in inputs.items():c.atomic_json(source/(name+'.json'),value)
    for phase in ('sample','anchors'):
        intent=dict(manifest=c.digest(plan),phase=phase,pbs_job_id='123.test',hostname='fixture')
        c.atomic_json(source/(phase+'-execution-intent.json'),intent)
        native=source/('preflight-'+phase)/'native_preflight.json'
        c.atomic_json(native,dict(manifest=c.digest(plan),pbs_job_id='123.test',hostname='fixture',profile=inputs['platform_profile']))
        rows=[dict(task=list(task),status='ok',wall_seconds=1.,cpu_seconds=1.,peak_rss_mb=1.) for task in s.low.tasks(plan,phase)]
        c.atomic_json(source/(phase+'-summary.json'),dict(manifest=c.digest(plan),phase=phase,tasks=len(rows),records=rows,failed=0,native_preflight_sha256=c.file_hash(native)))
    before=s.a.completed_phase_evidence(source,s.a.read_production_plan(source))
    for name,path in s.tree(source).items():s.copy_file(path,target/name)
    assert s.a.read_production_plan(target)==plan
    assert s.a.completed_phase_evidence(target,plan)==before
    assert before['sample']['tasks']==61440 and before['anchors']['tasks']==192
    assert len(before['sample']['group_record_digests'])==768


@pytest.mark.parametrize('change',['running','failed','wrong_pbs_script','receipt','script','intent'])
def test_copy_job_terminal_and_receipt_required_for_downstream(fixture,change):
    _,control,target,_,_,query,_=fixture;prepared(fixture);s.run(control,job_query=query)
    if change=='running':query.copy_job['job_state']='R'
    elif change=='failed':query.copy_job['Exit_status']=1
    elif change=='wrong_pbs_script':query.copy_job['Submit_arguments']='wrong.sh'
    else:
        name={'receipt':'submission.json','script':'stage.sh','intent':'submission-intent.json'}[change]
        (control/name).write_text('{}')
    with pytest.raises((ValueError,KeyError)):s.read_staged(target)


def test_copy_worker_requires_parent_receipt(fixture):
    _,control,target,_,_,query,_=fixture;prepared(fixture);(control/'submission.json').unlink()
    with pytest.raises((ValueError,FileNotFoundError)):s.run(control,job_query=query)
    assert not target.exists() and (control/'execution-intent.json').exists()


def test_full_reader_rejects_login_before_io(fixture,monkeypatch):
    monkeypatch.delenv('PBS_JOBID')
    monkeypatch.setattr(s,'tree',lambda *a,**kw:pytest.fail('no raw scan on login'))
    with pytest.raises(ValueError,match='requires PBS'):s.read_staged(fixture[2])


def test_login_metadata_gate_does_not_read_raw(fixture,monkeypatch):
    _,control,target,_,_,query,_=fixture;prepared(fixture);s.run(control,job_query=query)
    monkeypatch.delenv('PBS_JOBID');original=c.file_hash
    def hash_path(path):
        assert not Path(path).is_relative_to(target/'traces') and not Path(path).is_relative_to(target/'anchors')
        return original(path)
    monkeypatch.setattr(c,'file_hash',hash_path)
    assert s.read_staged_provenance(target)['current_payloads_rehashed'] is False


@pytest.mark.parametrize('phase',['analysis','trace-audit'])
def test_actual_pbs_invocation_selects_guarded_compute_entry(phase,tmp_path):
    import shlex
    root=tmp_path/'bundle';destination=root/'runs/copied';script=destination/'job.sh'
    arguments=['run-analysis','--partition','2'] if phase=='analysis' else ['run-trace-audit','--audit-root',str(root/'runs/audit')]
    content=s.render_script(root,destination,script,dict(cpus=96,memory_gb=32,walltime='01:00:00'),arguments)
    argv=shlex.split(content.splitlines()[-1])
    assert argv[1]==str(Path(s.__file__).resolve()) and argv[2:2+len(arguments)]==arguments
    assert argv[-2:]==['--destination',str(destination)]
    assert 'tile_low_noise_analysis_partitions.py' not in content and 'tile_low_noise_trace_audit_run.py' not in content


@pytest.mark.parametrize('entry',['analysis','trace-audit'])
def test_compute_entry_full_gate_precedes_old_runner(fixture,monkeypatch,entry):
    target=fixture[2];calls=[]
    def gate(*args,**kwargs):calls.append('full-gate');raise ValueError('bad seal')
    monkeypatch.setattr(s,'read_staged',gate)
    if entry=='analysis':
        import tile_low_noise_analysis_partitions as module
        monkeypatch.setattr(module,'run_partition',lambda *args:pytest.fail('old runner before full gate'))
        operation=lambda:s.run_analysis(target,0)
    else:
        import tile_low_noise_trace_audit_run as module
        monkeypatch.setattr(module,'run',lambda *args:pytest.fail('old runner before full gate'))
        operation=lambda:s.run_trace_audit(target,Path('audit'))
    with pytest.raises(ValueError,match='bad seal'):operation()
    assert calls==['full-gate']


@pytest.mark.parametrize('change',['rerun','host','receipt_pin'])
def test_original_execution_independent_pins(fixture,change):
    source,_,_,_,binding,_,job=fixture
    if change=='rerun':job['run_count']=2
    elif change=='host':job['exec_host']='other-node/0'
    else:binding['input_sha256']['submission.json']='wrong'
    with pytest.raises(ValueError):prepared(fixture)


@pytest.mark.parametrize('location',['seal','plan'])
def test_exact_consumed_json_bytes_are_hash_bound(fixture,monkeypatch,location):
    _,control,target,_,_,query,_=fixture;prepared(fixture)
    if location=='seal':s.run(control,job_query=query);path=target/'.staging/seal.json'
    else:path=control/'plan.json'
    original=Path.read_bytes
    def mutate(self):
        value=original(self)
        if self==path:
            changed=json.loads(value)
            if location=='seal':changed['sealed']=False
            else:changed['destination']='changed'
            self.write_bytes(c.canonical(changed))
        return value
    monkeypatch.setattr(Path,'read_bytes',mutate)
    with pytest.raises(ValueError,match='snapshot read'):
        s.read_staged(target) if location=='seal' else s.run(control,job_query=query)


def test_analysis_submission_prepares_actual_guarded_script_only(fixture,monkeypatch):
    import shlex
    import submit_tile_low_noise_analysis_partitions as old
    import tile_low_noise_analysis_partitions as terminal
    _,control,target,bundle,_,query,_=fixture;prepared(fixture);s.run(control,job_query=query);monkeypatch.delenv('PBS_JOBID')
    group=[2,0,0,0,0]
    resource=dict(cpus=96,memory_gb=32,workers=8,partitions=[dict(wall_seconds=3600,walltime='01:00:00',groups=[group])])
    wrapper=dict(production=s.a.read_production_plan(target),resources=resource)
    monkeypatch.setattr(old,'checked_plan',lambda *args:wrapper)
    monkeypatch.setattr(old,'require_fresh',lambda *args:target/'analysis-submissions/0')
    monkeypatch.setattr(old,'bundle_binding',lambda *args:{'fixture':True})
    monkeypatch.setattr(s.subprocess,'run',lambda *args,**kwargs:pytest.fail('preparation must not execute qsub'))
    record=s.submit_analysis(bundle,target,0);script=Path(record['command'][1]);argv=shlex.split(script.read_text().splitlines()[-1])
    assert record['command']==['qsub',str(target/'analysis-submissions/0/partition.sh')]
    assert c.file_hash(script)==record['script_sha256'] and record['compute_full_payload_gate'] is True
    assert argv[1:5]==[str(Path(s.__file__).resolve()),'run-analysis','--partition','0']
    assert record['staging_origin']['current_payloads_rehashed'] is False
    assert record['resource']['wall_seconds']>record['baseline_resource']['wall_seconds']
    c.atomic_json(script.parent/'submission-intent.json',record);c.atomic_json(script.parent/'submission.json',dict(record,job_id='789.test'))
    phase=target/'analysis-partitions/0'
    intent=dict(partition_manifest=c.digest(wrapper),partition=0,groups=[group],workers=8,manifest=c.digest(wrapper['production']),pbs_job_id='789.test',hostname='fixture')
    c.atomic_json(phase/'execution-intent.json',intent);c.atomic_json(phase/'native_preflight.json',dict(manifest=intent['manifest'],pbs_job_id='789.test',hostname='fixture',profile={}))
    summary=dict(intent,rows=1,execution_intent_sha256=c.file_hash(phase/'execution-intent.json'),native_preflight_sha256=c.file_hash(phase/'native_preflight.json'),group_marker_sha256={c.task_id(group):'fixture'})
    c.atomic_json(phase/'summary.json',summary)
    monkeypatch.setattr(terminal.a,'analysis_settings',lambda _:iter([None]))
    accepted,_=terminal.partition_evidence(target,wrapper,0)
    assert accepted['pbs_job_id']=='789.test' and accepted['rows']==1


def test_render_rejects_pbs_whitespace(tmp_path):
    with pytest.raises(ValueError,match='whitespace'):
        s.render_script(tmp_path/'bad path',tmp_path/'root',tmp_path/'job.sh',dict(cpus=1,memory_gb=4,walltime='01:00:00'),['run-analysis'])


def test_copy_measurement_budget_adds_four_pass_estimate():
    origin=dict(sealed=True,copy_exit_status=0,copy_pbs_job_id='456.test',copy_elapsed_seconds=200.,summary_sha256='fixed')
    resource,evidence=s.budget_resources(dict(cpus=96,walltime='02:00:00',wall_seconds=7200),origin)
    assert resource['wall_seconds']==10800 and resource['walltime']=='03:00:00'
    assert evidence['additional_raw_hash_passes']==4 and evidence['full_reader_calls']==2
    assert evidence['copy_summary_sha256']=='fixed' and 'not a bound' in evidence['warning']


def test_initial_ceiling_reserves_explicit_io_budget():
    origin=dict(sealed=True,copy_exit_status=0,copy_pbs_job_id='456.test',copy_elapsed_seconds=200.,summary_sha256='fixed')
    resource,evidence=s.budget_resources(dict(walltime='24:00:00'),origin,initial_ceiling=True)
    assert resource['walltime']=='24:00:00' and evidence['baseline_reserved_seconds']==82800
    with pytest.raises(ValueError,match='exceeds 24h'):s.budget_resources(dict(walltime='24:00:00'),origin)


@pytest.mark.parametrize('elapsed',[None,0.,float('nan'),float('inf'),-1.])
def test_unmeasured_copy_cannot_make_submission_ready(elapsed):
    origin=dict(sealed=True,copy_exit_status=0,copy_pbs_job_id='456.test',copy_elapsed_seconds=elapsed,summary_sha256='fixed')
    with pytest.raises(ValueError,match='completed measured copy'):s.budget_resources(dict(walltime='01:00:00'),origin)


def test_guarded_audit_submission_record_is_accepted_by_actual_terminal_reader(tmp_path,monkeypatch):
    """Real generated script/ledger and terminal control flow; large group I/O is synthetic."""
    import tile_low_noise_audited_collection as terminal
    import submit_tile_low_noise_trace_audit as submitter
    bundle=(tmp_path/'bundle').resolve();source=bundle/'runs/source';root=bundle/'runs/audit'
    source.mkdir(parents=True);root.mkdir(parents=True)
    sampling=dict(case=0,target_index=0,replicates=192)
    plan=dict(purpose='low_noise_trace_audit_full',case=0,target_index=0,replicates=192,workers=8,
              input_sha256={'manifest.json':'fixture'},completed_phase_evidence={'anchors':{'record_digests':{}}})
    groups=terminal.r.groups(plan)
    anchors={c.task_id((0,0,0,0,rep,0,0)):dict(task=[0,0,0,0,rep,0,0],status='failed') for rep in range(192)}
    plan['completed_phase_evidence']['anchors']['record_digests']={name:c.digest(value) for name,value in anchors.items()}
    origin=dict(sealed=True,copy_exit_status=0,copy_pbs_job_id='456.test',copy_elapsed_seconds=200.,summary_sha256='fixed')
    monkeypatch.setattr(s,'read_staged_provenance',lambda _:origin)
    monkeypatch.setattr(submitter,'require_fresh',lambda _:None)
    monkeypatch.setattr(submitter,'checked_plan',lambda *args:(plan,sampling,dict(cpus=96,memory_gb=32,workers=8,wall_seconds=3600,walltime='01:00:00'),['123.source']))
    monkeypatch.setattr(submitter,'bundle_binding',lambda *args:{'fixture':True})
    ledger=s.submit_trace_audit(bundle,source,root,capacity_root=tmp_path/'capacity')
    assert ledger['resource']['walltime']=='02:00:00' and ledger['baseline_resource']['walltime']=='01:00:00'
    assert ledger['staging_budget']['additional_raw_hash_passes']==4
    c.atomic_json(root/'submission-intent.json',ledger);c.atomic_json(root/'submission.json',dict(ledger,job_id='789.test'))
    identity=dict(manifest=c.digest(plan),sampling_manifest=c.digest(sampling),workers=8,pbs_job_id='789.test',hostname='fixture')
    native=dict(native_platform_verified=True,fixture=True)
    summary=dict(manifest=c.digest(plan),groups=768,records=[dict(group=list(group)) for group in groups],failed_audit_groups=0,
        input_changes=[],context_error=None,native_platform_verified=True,all_physical_states_redecoded=False,native_preflight_sha256='fixture',
        planned_tasks=1536,failed_sampling=768)
    values={'summary.json':summary,'execution-intent.json':identity,'native_preflight.json':dict(identity,evidence=native),
            'platform_profile.json':{},'platform_fixture.json':{}}
    class Proof:
        def __init__(self,*args):self.hashes={};self.targets={};self.actual={}
        def track(self,path):
            path=Path(path);digest=c.file_hash(path) if path in (root/'trace-audit.sh',root/'submission.json',root/'submission-intent.json') else 'fixture'
            self.hashes[str(path)]=digest;self.targets[str(path)]=str(path)
            if digest!='fixture':self.actual[path]=digest
            return digest
        def read(self,path):
            self.track(path)
            return json.loads(Path(path).read_bytes()) if Path(path).name in ('submission.json','submission-intent.json') else values[Path(path).name]
        def artifact(self,base,identity):return {},anchors[base.name]
        def finish(self):assert all(c.file_hash(path)==digest for path,digest in self.actual.items())
    monkeypatch.setattr(terminal,'Evidence',Proof)
    monkeypatch.setattr(terminal.r,'read_plan',lambda *args:(plan,sampling))
    monkeypatch.setattr(terminal.r.audit,'validate_native_environment',lambda *args,**kwargs:native)
    monkeypatch.setattr(terminal.p,'read_collection',lambda _:(sampling,iter([dict(group=list(group),available=False) for group in groups]),dict(rows=768)))
    monkeypatch.setattr(terminal.p,'read_plan',lambda *args:dict(resources=dict(partitions=[dict(index=0)])))
    monkeypatch.setattr(terminal.p,'read_group',lambda _,wrapper,group:(dict(group=list(group),input_artifact_markers={'anchors/'+c.task_id((0,0,0,0,group[4],0,0)):'fixture'}),'fixture'))
    monkeypatch.setattr(terminal,'verify_group',lambda *args:dict(tasks=2,failed_sampling=1,redecoded_checkpoints=3))
    _,rows,evidence=terminal.read_audited_collection(source,root)
    assert len(rows)==768 and evidence['pbs_job_id']=='789.test' and evidence['anchors']==192
    assert evidence['evidence_sha256'][str(root/'trace-audit.sh')]==ledger['script_sha256']
    (root/'trace-audit.sh').write_text('changed guarded argv')
    with pytest.raises(ValueError,match='script differs'):terminal.read_audited_collection(source,root)
