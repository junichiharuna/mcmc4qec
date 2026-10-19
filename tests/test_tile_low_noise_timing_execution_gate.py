"""Tiny immutable fixtures for the timing execution and submission boundary."""
from copy import deepcopy
import os
from pathlib import Path
import shlex
from types import SimpleNamespace

import pytest
from test_tile_low_noise_timing_execution import r,c,plans,small_plan,measurement
import submit_tile_low_noise_timing_execution as submit


def put(root,name,value):
    path=root/name
    path.write_bytes(value if isinstance(value,bytes) else c.canonical(value)+b'\n')
    return dict(path=str(path),sha256=c.file_hash(path))


def job_fixture(script,res,exit_status=0):
    return dict(job_state='F',Exit_status=exit_status,run_count=1,Submit_arguments=shlex.quote(str(script)),exec_host='node/0',
        Resource_List=dict(nodect=1,ncpus=res['cpus'],select=f"1:ncpus={res['cpus']}:mem={res['memory_gb']}gb",
            mem=f"{res['memory_gb']}gb",walltime=res['walltime']))


def census_fixture(root):
    root.mkdir(exist_ok=True)
    bundle=dict(selection={'fixture':1},selection_sha256='f'*64,registry={'fixture':2},plans={k:{'fixture':k} for k in plans.STAGES})
    source=put(root,'source.py',b'# fixed source\n');inp=put(root,'input.json',dict(fixture=3))
    counts={f'old{i}':0 for i in range(56)};counts.update({k:0 for k in plans.STAGES});counts['old0']=10000
    catalog=dict(purpose='extended_low_noise_timing_seed_catalog',timing_bundle_digest=c.digest(bundle),registry_digest=c.digest(bundle['registry']),
        selection_sha256=bundle['selection_sha256'],selection_digest=c.digest(bundle['selection']),new_plan_sha256={k:c.digest(v) for k,v in bundle['plans'].items()},
        source_sha256={source['path']:source['sha256']},baseline_input_sha256={inp['path']:inp['sha256']},
        planned_counts=counts,planned_role_counts=counts,planned_total=10000,reserved_unenumerated_stages={},expected_intentional_shared_entries=8448)
    result=dict(complete=True,planned_entries=10000,checked_entries=10000,unchecked_entries=0,unexpected_collisions=0,
        intentional_shared_entries=8448,unique_seeds=1552,checked_counts=counts,stream_sha256='e'*64)
    native=r.native.platform_inputs();profile=native['platform_profile'];fixture=native['platform_fixture']
    manifest=dict(catalog_evidence_digest=c.digest(catalog),runtime=r.t.runtime(),source_sha256=catalog['source_sha256'],
        input_sha256=catalog['baseline_input_sha256'],native_input_digests=dict(profile=c.digest(profile),fixture=c.digest(fixture)))
    descriptor={name:put(root,name+'.json',value) for name,value in [('catalog',catalog),('result',result),('manifest',manifest),('profile',profile),('fixture',fixture)]}
    descriptor['script']=put(root,'census.sh',b'#!/bin/bash\n')
    intent=dict(manifest=c.digest(manifest),command=['qsub',descriptor['script']['path']],script_sha256=descriptor['script']['sha256'],resource=r.capacity_resources())
    descriptor['intent']=put(root,'intent.json',intent)
    descriptor['submission']=put(root,'submission.json',dict(intent,job_id='123.cluster'))
    identity=dict(manifest=c.digest(manifest),pbs_job_id='123.cluster',hostname='node')
    descriptor['execution']=put(root,'execution.json',identity)
    descriptor['native']=put(root,'native.json',dict(identity,profile=profile))
    end=dict(identity,complete=True,result_sha256=descriptor['result']['sha256'],native_sha256=descriptor['native']['sha256'],execution_sha256=descriptor['execution']['sha256'])
    for label in ('input_sha256','source_sha256'):end[label]=manifest[label];end[label+'_after']=manifest[label]
    descriptor['completion']=put(root,'completion.json',end)
    descriptor['terminal']=put(root,'terminal.json',{'Jobs':{'123.cluster':job_fixture(descriptor['script']['path'],intent['resource'])}})
    return descriptor,bundle


def test_formal_census_actual_gate_and_current_inputs(tmp_path):
    descriptor,bundle=census_fixture(tmp_path);proof=r.Evidence()
    result=r.formal_census(descriptor,bundle,proof);proof.finish()
    assert result['job_id']=='123.cluster' and len(proof.files)==14
    (tmp_path/'input.json').write_text('{}')
    with pytest.raises(ValueError):r.formal_census(descriptor,bundle,r.Evidence())


@pytest.mark.parametrize('which,field,value',[
    ('result','unchecked_entries',1),('result','complete',False),('completion','complete',False),
    ('completion','hostname','wrong'),('completion','input_sha256_after',{}),('completion','result_sha256','0'*64),
    ('manifest','runtime',{}),('catalog','registry_digest','0'*64),('catalog','new_plan_sha256',{}),
    ('catalog','baseline_input_sha256',{'unknown':'0'*64})])
def test_formal_census_rejects_rebound_invalid_envelope(tmp_path,which,field,value):
    descriptor,bundle=census_fixture(tmp_path)
    obj=r.json_read(descriptor[which]['path']);obj[field]=value
    descriptor[which]=put(tmp_path,which+'.json',obj)
    with pytest.raises(ValueError):r.formal_census(descriptor,bundle,r.Evidence())


@pytest.mark.parametrize('key,value',[('run_count',2),('Exit_status',1),('exec_host','other/0'),('Submit_arguments','other.sh')])
def test_formal_census_rejects_actual_pbs(tmp_path,key,value):
    descriptor,bundle=census_fixture(tmp_path)
    obj=r.json_read(descriptor['terminal']['path']);obj['Jobs']['123.cluster'][key]=value
    descriptor['terminal']=put(tmp_path,'terminal.json',obj)
    with pytest.raises(ValueError):r.formal_census(descriptor,bundle,r.Evidence())


def test_proof_rejects_late_change(tmp_path):
    path=tmp_path/'input';path.write_bytes(b'first');proof=r.Evidence();proof.track(path)
    path.write_bytes(b'second')
    with pytest.raises(ValueError):proof.finish()


@pytest.mark.parametrize('method',['mc','bar'])
def test_artifact_actual_payload_and_metadata_gate(tmp_path,monkeypatch,method):
    for k,v in r.THREADS.items():monkeypatch.setenv(k,v)
    monkeypatch.setattr(c,'peak_rss_mb',lambda:100.)
    plan,task=small_plan(method);record=r.run_task((str(tmp_path),plan,task))
    envelope=dict(science=plan,tasks=[list(task)])
    r.artifact_records(tmp_path,envelope,[record],r.Evidence())
    changed=deepcopy(record);changed['decoder_prior']=.9
    with pytest.raises(ValueError):r.artifact_records(tmp_path,envelope,[changed],r.Evidence())
    with pytest.raises(ValueError):r.artifact_records(tmp_path,envelope,[],r.Evidence())
    (tmp_path/'tasks'/'unexpected').write_text('x')
    with pytest.raises(ValueError):r.artifact_records(tmp_path,envelope,[record],r.Evidence())


def test_source_closure_uses_actual_module_origins():
    actual=r.source_files()
    assert actual['tile_low_noise_timing_plan']==Path(plans.__file__).absolute()
    assert actual['submit_tile_low_noise_timing_execution']==Path(submit.__file__).absolute()
    assert len(actual)>40


def submit_fixture(tmp_path,monkeypatch):
    bundle=tmp_path/'bundle';root=bundle/'runs'/'cap';root.mkdir(parents=True)
    plan=dict(planning_status='ready',tasks=[[0,0,0,0],[0,0,0,1]],resource=r.capacity_resources(),
        snapshot=dict(python_path='/fixed/python',pythonpath='/stage3/cluster_scripts:/stage2/cluster_scripts:/v11/src'))
    monkeypatch.setattr(r,'read_plan',lambda _:deepcopy(plan))
    monkeypatch.setattr(submit,'bundle_binding',lambda *args:dict(fixture=1))
    monkeypatch.setattr(submit,'upstream',lambda *args:dict(Jobs={}))
    return bundle,root,plan


def test_submit_dry_run_and_success_exactly_once(tmp_path,monkeypatch):
    bundle,root,plan=submit_fixture(tmp_path,monkeypatch);calls=[]
    def runner(args,**kwargs):calls.append(args);return SimpleNamespace(stdout='123.cluster\n')
    submit.submit(bundle,root,runner=runner)
    assert not calls
    output=submit.submit(bundle,root,execute=True,controller_query=lambda:[],active_query=lambda:{},runner=runner)
    assert output['job_id']=='123.cluster' and calls==[['qsub',str(root/'timing.sh')]]
    assert "export PYTHONPATH=/stage3/cluster_scripts:/stage2/cluster_scripts:/v11/src" in (root/'timing.sh').read_text()
    with pytest.raises(ValueError):submit.submit(bundle,root,execute=True,runner=runner)
    assert len(calls)==1 and not (bundle.parent/'tile-low-noise-submission.lock').exists()


@pytest.mark.parametrize('active,controller',[(True,False),(False,True)])
def test_submit_global_node_or_controller_guard(tmp_path,monkeypatch,active,controller):
    bundle,root,plan=submit_fixture(tmp_path,monkeypatch);calls=[]
    jobs={'j':dict(Resource_List=dict(select='2:ncpus=1'))} if active else {}
    with pytest.raises(ValueError):submit.submit(bundle,root,execute=True,controller_query=lambda:controller,active_query=lambda:jobs,runner=lambda *a,**k:calls.append(a))
    assert not calls and not (root/'submission-intent.json').exists()


def test_submit_ambiguous_retains_intent_lock(tmp_path,monkeypatch):
    bundle,root,plan=submit_fixture(tmp_path,monkeypatch)
    with pytest.raises(ValueError):submit.submit(bundle,root,execute=True,controller_query=lambda:[],active_query=lambda:{},runner=lambda *a,**k:SimpleNamespace(stdout='unknown'))
    assert (root/'submission-intent.json').exists() and (bundle.parent/'tile-low-noise-submission.lock').exists()
    assert not (root/'submission.json').exists()


def test_submit_changed_lock_after_qsub_keeps_receipt(tmp_path,monkeypatch):
    bundle,root,plan=submit_fixture(tmp_path,monkeypatch)
    def response(*args,**kwargs):
        (bundle.parent/'tile-low-noise-submission.lock').write_text('other owner')
        return SimpleNamespace(stdout='123.cluster')
    with pytest.raises(ValueError):submit.submit(bundle,root,execute=True,controller_query=lambda:[],active_query=lambda:{},runner=response)
    assert (bundle.parent/'tile-low-noise-submission.lock').read_text()=='other owner'
    assert r.json_read(root/'qsub-response.json')['stdout']=='123.cluster' and (root/'submission-intent.json').exists()
    assert not (root/'submission.json').exists()


@pytest.mark.parametrize('change',['lock','plan','script','intent'])
def test_submit_final_gate_after_intent_before_qsub(tmp_path,monkeypatch,change):
    bundle,root,plan=submit_fixture(tmp_path,monkeypatch);original=r.save_new;calls=[]
    def save(path,value):
        original(path,value)
        if Path(path).name=='submission-intent.json':
            if change=='lock':(bundle.parent/'tile-low-noise-submission.lock').write_text('foreign owner')
            elif change=='plan':plan['tasks']=[]
            elif change=='script':(root/'timing.sh').write_text('changed')
            else:Path(path).write_text('{}')
    monkeypatch.setattr(r,'save_new',save)
    with pytest.raises(ValueError):submit.submit(bundle,root,execute=True,controller_query=lambda:[],active_query=lambda:{},runner=lambda *a,**k:calls.append(a))
    assert calls==[] and not (root/'submission.json').exists()
    if change=='lock':assert (bundle.parent/'tile-low-noise-submission.lock').read_text()=='foreign owner'


def test_capacity_failed_envelope_never_shortens_budget():
    data=measurement();data['execution_infeasible_capacity_envelope']=True
    assert r.resource_plan(data)['status']=='execution_infeasible_capacity_envelope'


def test_all_24_rows_and_192_infeasible_denominator(monkeypatch):
    role='low_timing.mc.benchmark';science,task=small_plan('mc',replicates=192)
    science['rows'] += [dict(case=case,target_index=target,epsilon_index=epsilon,status='not_selected',planning_status='not_selected')
        for case in range(4) for target in range(3) for epsilon in range(2) if (case,target,epsilon)!=(0,0,0)]
    cap=deepcopy(science);cap['purpose']='low_timing.mc.capacity';snapshot=dict(native_input_digests={})
    bundle=dict(plans={role:science,'low_timing.mc.capacity':cap})
    monkeypatch.setattr(r,'inputs',lambda _: (bundle,snapshot))
    monkeypatch.setattr(r,'accepted_capacity',lambda *a,**k:dict(summary=measurement(t=43000)))
    monkeypatch.setattr(r,'json_read',lambda _:dict(role='low_timing.mc.capacity',identity=[0,0,0],snapshot=snapshot,science=cap))
    out=r.envelope_value({},role,[0,0,0],dict(root='/cap',terminal={},manifest_sha256='f'*64))
    assert len(out['outcomes'])==24 and out['planned_replicates']==192 and out['tasks']==[]
    assert out['unexecuted_replicates']==list(range(192)) and out['resource'] is None


def execution_fixture(tmp_path,monkeypatch):
    plan,task=small_plan('mc')
    envelope=dict(science=plan,tasks=[list(task),list((*task[:3],1))],planning_status='ready',mode='capacity',
        role=plan['purpose'],identity=list(task[:3]),
        resource=r.resource(2,1,340,86400),snapshot=dict(fixture=1,files={}),outcomes=[dict(identity=i) for i in range(24)])
    actual_native=r.native.platform_inputs()
    envelope['native_input_digests']={k:c.digest(v) for k,v in actual_native.items()}
    envelope['snapshot']['native_input_digests']=envelope['native_input_digests']
    for key,value in actual_native.items():put(tmp_path,key+'.json',value)
    manifest=put(tmp_path,'manifest.json',envelope)
    script=put(tmp_path,'timing.sh',b'#!/bin/bash\n');upstream=put(tmp_path,'upstream-completion-at-submit.json',dict(Jobs={}))
    ledger=dict(manifest=c.digest(envelope),resource=envelope['resource'],command=['qsub',script['path']],upstream_completion_sha256=upstream['sha256'])
    put(tmp_path,'submission-intent.json',ledger);put(tmp_path,'submission.json',dict(ledger,job_id='123.cluster'))
    monkeypatch.setattr(r,'read_plan',lambda _:deepcopy(envelope))
    monkeypatch.setattr(r,'execution_binding',lambda *a,**k:dict(fixture=1))
    monkeypatch.setattr(r,'current_runtime',lambda _:None)
    monkeypatch.setattr(r.socket,'gethostname',lambda:'node')
    monkeypatch.setattr(c,'peak_rss_mb',lambda:100.)
    monkeypatch.setenv('PBS_JOBID','123.cluster')
    for key,value in r.THREADS.items():monkeypatch.setenv(key,value)
    def preflight(root,value):
        put(root,'native_preflight.json',dict(manifest=c.digest(value),pbs_job_id='123.cluster',hostname='node',profile=actual_native['platform_profile']))
    monkeypatch.setattr(r.native,'native_preflight',preflight)
    def scheduler(*args,**kwargs):
        job=job_fixture(script['path'],envelope['resource']);job['job_state']='R'
        return SimpleNamespace(stdout=r.json.dumps({'Jobs':{'123.cluster':job}}))
    return envelope,manifest,script,scheduler


def test_complete_execution_terminal_proof_and_summary_tamper(tmp_path,monkeypatch):
    envelope,manifest,script,scheduler=execution_fixture(tmp_path,monkeypatch)
    summary=r.run(tmp_path,scheduler=scheduler)
    assert summary['execution_complete'] and len(summary['records'])==2
    terminal=put(tmp_path,'terminal.json',{'Jobs':{'123.cluster':job_fixture(script['path'],envelope['resource'])}})
    proof=r.completed(tmp_path,terminal,expected_manifest_sha256=manifest['sha256'])
    assert proof['summary']==summary and proof['input_files']
    obj=r.json_read(tmp_path/'scientific-summary.json');obj['recorded_tasks']=1
    put(tmp_path,'scientific-summary.json',obj)
    with pytest.raises(ValueError):r.completed(tmp_path,terminal,expected_manifest_sha256=manifest['sha256'])


def test_recorded_scientific_failures_are_complete_not_available(tmp_path,monkeypatch):
    envelope,manifest,script,scheduler=execution_fixture(tmp_path,monkeypatch)
    monkeypatch.setattr(r.qec,'direct_mc',lambda *a,**k:(_ for _ in ()).throw(RuntimeError('decoder fixture')))
    summary=r.run(tmp_path,scheduler=scheduler)
    assert summary['execution_complete'] and summary['failed']==2 and summary['unavailable']==2
    assert r.resource_plan(summary)['status']=='capacity_failed'


def test_broken_pool_retains_all_unknown_cost_tasks(tmp_path,monkeypatch):
    envelope,manifest,script,scheduler=execution_fixture(tmp_path,monkeypatch)
    monkeypatch.setattr(c,'parallel_map',lambda *a,**k:(_ for _ in ()).throw(RuntimeError('worker killed')))
    with pytest.raises(RuntimeError):r.run(tmp_path,scheduler=scheduler)
    summary=r.json_read(tmp_path/'summary.json')
    assert not summary['execution_complete'] and len(summary['records'])==2
    assert all(row['status']=='interrupted' and row['started']=='unknown' and row['task_wall_seconds'] is None for row in summary['records'])
    terminal=put(tmp_path,'terminal.json',{'Jobs':{'123.cluster':job_fixture(script['path'],envelope['resource'],271)}})
    proof=r.completed(tmp_path,terminal,expected_manifest_sha256=manifest['sha256'])
    assert r.resource_plan(proof['summary'])['status']=='execution_infeasible_capacity_envelope'
    assert proof['summary']['costs_complete'] is False


def test_false_native_rejected_before_pool(tmp_path,monkeypatch):
    envelope,manifest,script,scheduler=execution_fixture(tmp_path,monkeypatch)
    monkeypatch.setattr(r.native,'native_preflight',lambda *a,**k:(_ for _ in ()).throw(ValueError('native mismatch')))
    with pytest.raises(RuntimeError):r.run(tmp_path,scheduler=scheduler)
    summary=r.json_read(tmp_path/'summary.json')
    assert summary['native_sha256'] is None and not summary['execution_complete']
    assert not (tmp_path/'tasks').exists()


def test_pool_death_recovers_saved_cost_without_inventing_outer_clock(tmp_path,monkeypatch):
    envelope,manifest,script,scheduler=execution_fixture(tmp_path,monkeypatch)
    def partial(function,jobs,workers):
        function(jobs[0]);raise RuntimeError('second worker killed')
    monkeypatch.setattr(c,'parallel_map',partial)
    with pytest.raises(RuntimeError):r.run(tmp_path,scheduler=scheduler)
    summary=r.json_read(tmp_path/'summary.json');first,last=summary['records']
    assert first['status']=='ok' and first['recovered_from_complete_artifact'] and first['task_wall_seconds']>0
    assert first['inclusive_wall_seconds'] is None and last['status']=='interrupted'
    assert summary['known_task_wall_seconds_lower_bound']==first['task_wall_seconds'] and not summary['costs_complete']


def test_bundle_binds_actual_pythonpath_and_core(monkeypatch):
    snapshot=dict(source_sha256=r.source_hashes(),runtime=r.t.runtime(),pythonpath=os.environ.get('PYTHONPATH',''),
        core_path=str(Path(r.qec.__file__).absolute()),python_path=str(Path(r.sys.executable).absolute()),python_sha256=c.file_hash(r.sys.executable))
    bundle=Path(r.__file__).resolve().parents[1]
    assert submit.bundle_binding(bundle,dict(snapshot=snapshot))==snapshot
    monkeypatch.setenv('PYTHONPATH','different')
    with pytest.raises(ValueError):submit.bundle_binding(bundle,dict(snapshot=snapshot))


def test_source_snapshot_mutation_rejected_at_terminal(tmp_path,monkeypatch):
    envelope,manifest,script,scheduler=execution_fixture(tmp_path,monkeypatch)
    source=put(tmp_path,'authority.py',b'# fixed\n')
    envelope['snapshot']['files']={source['path']:[str(Path(source['path']).resolve()),source['sha256']]}
    manifest=put(tmp_path,'manifest.json',envelope)
    r.run(tmp_path,scheduler=scheduler)
    terminal=put(tmp_path,'terminal.json',{'Jobs':{'123.cluster':job_fixture(script['path'],envelope['resource'])}})
    Path(source['path']).write_text('# changed')
    with pytest.raises(ValueError):r.completed(tmp_path,terminal,expected_manifest_sha256=manifest['sha256'])


@pytest.mark.parametrize('change',['final','syndrome','sector','dtype'])
def test_reviewer_compact_mutations_rejected(tmp_path,monkeypatch,change):
    for key,value in r.THREADS.items():monkeypatch.setenv(key,value)
    plan,task=small_plan();r.run_task((str(tmp_path),plan,task))
    arrays,record=c.load_artifact(tmp_path/'tasks'/c.task_id(task),dict(manifest=c.digest(plan),task=list(task)))
    if change=='final':arrays['final'].fill(0)
    elif change=='syndrome':arrays['syndrome_weight'].fill(65535)
    elif change=='sector':arrays['sector'].fill(2**31)
    else:arrays['weight']=r.np.full(arrays['weight'].shape,-1.,dtype=float)
    with pytest.raises(ValueError):r.validate_record(plan,task,arrays,record)


def test_recovery_pin_before_consumption(tmp_path,monkeypatch):
    envelope,manifest,script,scheduler=execution_fixture(tmp_path,monkeypatch)
    r.run_task((str(tmp_path),envelope['science'],tuple(envelope['tasks'][0])))
    original=c.load_artifact
    def changed(stem,*args,**kwargs):
        saved=original(stem,*args,**kwargs);path=Path(stem).with_suffix('.json');path.write_bytes(path.read_bytes()+b'\n');return saved
    monkeypatch.setattr(c,'load_artifact',changed)
    with pytest.raises(ValueError):r.recover_records(tmp_path,envelope,[])


def test_metadata_capacity_does_not_read_payload_and_requires_exact_evidence(tmp_path,monkeypatch):
    envelope,manifest,script,scheduler=execution_fixture(tmp_path,monkeypatch)
    r.run(tmp_path,scheduler=scheduler)
    terminal=put(tmp_path,'terminal.json',{'Jobs':{'123.cluster':job_fixture(script['path'],envelope['resource'])}})
    ref=dict(root=str(tmp_path),terminal=terminal,manifest_sha256=manifest['sha256'],
        summary_sha256=c.file_hash(tmp_path/'summary.json'),submission_sha256=c.file_hash(tmp_path/'submission.json'))
    original=c.load_artifact
    monkeypatch.setattr(c,'load_artifact',lambda *a,**k:(_ for _ in ()).throw(AssertionError('payload consumed during prepare')))
    proof=r.accepted_capacity(ref)
    assert proof['payloads_rehashed_now'] is False and proof['summary']['execution_complete']
    monkeypatch.setattr(c,'load_artifact',original)
    r.revalidate_capacity(dict(capacity_reference=ref,capacity_proof=proof))
    stem=tmp_path/'tasks'/c.task_id(envelope['tasks'][0]);arrays,record=original(stem,dict(manifest=c.digest(envelope['science']),task=envelope['tasks'][0]))
    record['extra']='mutated and marker rebound'
    c.save_artifact(stem,dict(manifest=c.digest(envelope['science']),task=envelope['tasks'][0]),arrays,record)
    # Saved evidence is an accepted history, not a current raw audit.
    assert r.accepted_capacity(ref)['payloads_rehashed_now'] is False
    with pytest.raises(ValueError):r.revalidate_capacity(dict(capacity_reference=ref,capacity_proof=proof))


@pytest.mark.parametrize('change',['flag','count','missing'])
def test_metadata_capacity_rejects_changed_summary_evidence(tmp_path,monkeypatch,change):
    envelope,manifest,script,scheduler=execution_fixture(tmp_path,monkeypatch);r.run(tmp_path,scheduler=scheduler)
    terminal=put(tmp_path,'terminal.json',{'Jobs':{'123.cluster':job_fixture(script['path'],envelope['resource'])}})
    summary=r.json_read(tmp_path/'summary.json')
    if change=='flag':summary['payload_verification']['verified']=False
    elif change=='count':summary['payload_verification']['task_count']=1
    else:summary['payload_verification']['files'].pop(next(iter(summary['payload_verification']['files'])))
    put(tmp_path,'summary.json',summary)
    ref=dict(root=str(tmp_path),terminal=terminal,manifest_sha256=manifest['sha256'],summary_sha256=c.file_hash(tmp_path/'summary.json'),submission_sha256=c.file_hash(tmp_path/'submission.json'))
    with pytest.raises(ValueError):r.accepted_capacity(ref)


def test_main_compute_stops_before_new_tasks_when_capacity_payload_changed(tmp_path,monkeypatch):
    caproot=tmp_path/'cap';caproot.mkdir()
    cap,manifest,script,scheduler=execution_fixture(caproot,monkeypatch);r.run(caproot,scheduler=scheduler)
    terminal=put(caproot,'terminal.json',{'Jobs':{'123.cluster':job_fixture(script['path'],cap['resource'])}})
    ref=dict(root=str(caproot),terminal=terminal,manifest_sha256=manifest['sha256'],summary_sha256=c.file_hash(caproot/'summary.json'),submission_sha256=c.file_hash(caproot/'submission.json'))
    proof=r.accepted_capacity(ref)
    mainroot=tmp_path/'main';mainroot.mkdir()
    main,_,_,scheduler=execution_fixture(mainroot,monkeypatch)
    main.update(mode='benchmark',capacity_reference=ref,capacity_proof=proof)
    monkeypatch.setattr(r,'read_plan',lambda root:deepcopy(cap if Path(root)==caproot else main))
    stem=caproot/'tasks'/c.task_id(cap['tasks'][0]);arrays,record=c.load_artifact(stem,dict(manifest=c.digest(cap['science']),task=cap['tasks'][0]))
    record['mutated']=True;c.save_artifact(stem,dict(manifest=c.digest(cap['science']),task=cap['tasks'][0]),arrays,record)
    calls=[]
    monkeypatch.setattr(r.qec,'direct_mc',lambda *a,**k:calls.append('new task'))
    monkeypatch.setattr(r.native,'native_preflight',lambda *a,**k:calls.append('new native'))
    with pytest.raises(RuntimeError):r.run(mainroot,scheduler=scheduler)
    assert calls==[] and not (mainroot/'tasks').exists()


def test_terminal_runtime_gate_rejects_core_and_import_change(monkeypatch):
    snapshot=dict(source_sha256=r.source_hashes(),runtime=r.t.runtime(),pythonpath=os.environ.get('PYTHONPATH',''),
        core_path=str(Path(r.qec.__file__).absolute()),python_path=str(Path(r.sys.executable).absolute()),python_sha256=c.file_hash(r.sys.executable))
    r.current_runtime(snapshot)
    changed=deepcopy(snapshot);changed['runtime']['package_sha256']='0'*64
    with pytest.raises(ValueError):r.current_runtime(changed)
    monkeypatch.setenv('PYTHONPATH','changed')
    with pytest.raises(ValueError):r.current_runtime(snapshot)


def test_failed_capacity_metadata_path_preserves_unknown_cost(tmp_path,monkeypatch):
    envelope,manifest,script,scheduler=execution_fixture(tmp_path,monkeypatch)
    monkeypatch.setattr(c,'parallel_map',lambda *a,**k:(_ for _ in ()).throw(RuntimeError('killed')))
    with pytest.raises(RuntimeError):r.run(tmp_path,scheduler=scheduler)
    terminal=put(tmp_path,'terminal.json',{'Jobs':{'123.cluster':job_fixture(script['path'],envelope['resource'],271)}})
    full=r.completed(tmp_path,terminal,expected_manifest_sha256=manifest['sha256'])
    failure=put(tmp_path,'accepted-failure.json',full)
    ref=dict(root=str(tmp_path),terminal=terminal,manifest_sha256=manifest['sha256'],submission_sha256=c.file_hash(tmp_path/'submission.json'),failure_evidence=failure)
    monkeypatch.setattr(c,'load_artifact',lambda *a,**k:(_ for _ in ()).throw(AssertionError('raw read')))
    accepted=r.accepted_capacity(ref)
    assert not accepted['payloads_rehashed_now'] and not accepted['summary']['costs_complete']
    assert r.resource_plan(accepted['summary'])['status']=='execution_infeasible_capacity_envelope'


def test_actual_main_prepare_uses_metadata_only_capacity(tmp_path,monkeypatch):
    caproot=tmp_path/'cap';caproot.mkdir()
    cap,manifest,script,scheduler=execution_fixture(caproot,monkeypatch);r.run(caproot,scheduler=scheduler)
    terminal=put(caproot,'terminal.json',{'Jobs':{'123.cluster':job_fixture(script['path'],cap['resource'])}})
    ref=dict(root=str(caproot),terminal=terminal,manifest_sha256=manifest['sha256'],summary_sha256=c.file_hash(caproot/'summary.json'),submission_sha256=c.file_hash(caproot/'submission.json'))
    science,task=small_plan('mc',replicates=192);role=science['purpose']
    bundle=dict(plans={role:science,cap['science']['purpose']:cap['science']})
    monkeypatch.setattr(r,'inputs',lambda config:(bundle,cap['snapshot']))
    monkeypatch.setattr(r,'completed',lambda *a,**k:(_ for _ in ()).throw(AssertionError('full completed during prepare')))
    monkeypatch.setattr(c,'load_artifact',lambda *a,**k:(_ for _ in ()).throw(AssertionError('payload consumed during prepare')))
    config={key:dict(path=str(caproot/(key+'.json')),sha256=c.file_hash(caproot/(key+'.json'))) for key in ('platform_profile','platform_fixture')}
    prepared=r.prepare(tmp_path/'main',config,role,[0,0,0],capacity=ref,partition_index=0)
    assert prepared['planning_status']=='ready' and len(prepared['tasks'])==192
    assert prepared['capacity_proof']['payloads_rehashed_now'] is False
