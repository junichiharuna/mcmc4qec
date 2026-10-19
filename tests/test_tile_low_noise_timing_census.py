"""Small census bridge contracts; no production catalog, pilot, SSH or qsub."""
from copy import deepcopy
import json
from pathlib import Path
import sys
from types import SimpleNamespace

import pytest
for dep in ('ldpc','bposd','pymatching'):pytest.importorskip(dep)
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'cluster_scripts'))
import calibration as c
import tile_seed_audit as old
import tile_low_noise_timing_census as b


def test_resource_uses_prior_full_census_not_only_optimistic_pilot():
    resource=b.resources(dict(seconds=.05,checked_entries=1000),3963562,100,110592)
    assert resource['wall_seconds']==2700 and resource['workers']==resource['cpus']==1
    assert resource['wall_seconds']>1800 and resource['memory_gb']==2
    assert resource['disk_required_bytes']>=4*1024**3


@pytest.mark.parametrize('value',[False,0,-1,float('nan'),float('inf')])
def test_invalid_measurement_rejected(value):
    with pytest.raises(ValueError):b.resources(dict(seconds=value,checked_entries=1000),3963562,100,110592)


def test_resource_ceiling_does_not_reduce_count():
    with pytest.raises(ValueError):b.resources(dict(seconds=100,checked_entries=1000),3963562,100,110592)
    with pytest.raises(ValueError):b.resources(dict(seconds=.05,checked_entries=1000),3963562,4000,110592)


def test_relocation_keeps_old_evidence_and_requires_both_current_bytes(tmp_path):
    first=tmp_path/'old.py';second=tmp_path/'current.py'
    first.write_bytes(b'# same source\n');second.write_bytes(first.read_bytes())
    previous=dict(source_sha256={str(first):c.file_hash(first)},planned_total=7,plan_sha256={'x':'a'*64})
    current=dict(previous,source_sha256={str(second):c.file_hash(second)})
    mapping={str(first):str(second)};frozen=deepcopy(previous)
    binding=b.relocation_binding(previous,current,mapping)
    assert previous==frozen and binding['same_source_bytes'] is True
    second.write_bytes(b'# changed\n')
    with pytest.raises(ValueError):b.relocation_binding(previous,current,mapping)


def test_relocation_rejects_non_source_change(tmp_path):
    path=tmp_path/'source.py';path.write_bytes(b'x')
    before=dict(source_sha256={str(path):c.file_hash(path)},planned_total=7)
    with pytest.raises(ValueError):b.relocation_binding(before,dict(before,planned_total=8),{str(path):str(path)})
    with pytest.raises(ValueError):b.relocation_binding(before,before,{})


def empty_bundle():
    rows=[dict(status='unmet_empirical_precision') for _ in range(24)]
    return dict(selection=dict(rows=rows),selection_sha256='a'*64,registry={},
        plans={name:dict(planned_seed_entries=0) for name in ('mc.main','mc.cap','bar.main','bar.cap')})


def test_no_op_retains_56_proof_and_never_claims_60_audited():
    result=b.allocation_state(empty_bundle(),'b'*64)
    assert result['status']=='not_required_no_allocations'
    assert result['baseline_verified_namespaces']==56 and result['new_namespaces_audited'] is False
    assert result['formal_census_descriptor'] is None
    changed=empty_bundle();changed['selection']['rows'][0]['status']='selected'
    with pytest.raises(ValueError):b.allocation_state(changed,'b'*64)


def test_no_op_does_not_rebuild_catalog_pilot_or_submit(tmp_path,monkeypatch):
    state=b.allocation_state(empty_bundle(),'b'*64)
    context=dict(state=state,config={},bundle=empty_bundle(),input_sha256={},source_sha256={},runtime={},native_input_digests={})
    monkeypatch.setattr(b,'inspect_inputs',lambda *args:context)
    monkeypatch.setattr(b,'build_catalog',lambda *args:pytest.fail('census catalog called'))
    root=tmp_path/'root'
    value=b.prepare(root,tmp_path/'input.json','c'*64)
    assert value['status']=='not_required_no_allocations'
    monkeypatch.setattr(b,'read_plan',lambda root:value)
    assert b.submit(root,execute=True,runner=lambda *a,**k:pytest.fail('scheduler'))==state
    assert b.run(root)==state and b.seal(root)==state
    assert not (root/'catalog.json').exists()


def test_single_engine_combines_old_new_and_cleans_database(tmp_path):
    factories={'old':lambda:iter([old.Entry('old',(1,),0)]),
               'new':lambda:iter([old.Entry('new',(1,),0)])}
    result,measurement=b.census_stream(factories,2,tmp_path)
    assert result['unexpected_collisions']==1 and result['checked_entries']==2
    assert measurement['sqlite_bytes']>0 and measurement['sqlite_retained'] is False
    assert not list(tmp_path.rglob('*.sqlite'))


def test_database_cleanup_on_stream_error(tmp_path):
    def fail():
        yield old.Entry('old',(1,),0)
        raise RuntimeError('failure')
    with pytest.raises(RuntimeError):b.census_stream({'x':fail},2,tmp_path)
    assert not list(tmp_path.rglob('*.sqlite'))


def test_gate_uses_native_profile_keys_and_real_descriptor_fixture(tmp_path):
    from test_tile_low_noise_timing_execution_gate import census_fixture
    import tile_low_noise_timing_execution as execution
    descriptors,bundle=census_fixture(tmp_path)
    proof=execution.Evidence()
    result=b.verify_descriptor(descriptors,bundle,proof)
    assert result['job_id']=='123.cluster'
    changed=deepcopy(descriptors)
    (tmp_path/'result.json').write_text(json.dumps({'full':{'complete':True}}))
    changed['result']['sha256']=c.file_hash(tmp_path/'result.json')
    with pytest.raises(ValueError):b.verify_descriptor(changed,bundle,execution.Evidence())


def submit_fixture(tmp_path,monkeypatch):
    bundle=tmp_path/'bundle';root=bundle/'runs'/'census';root.mkdir(parents=True)
    plan=dict(status='ready',root=str(root),bundle=str(bundle),resource=b.resources(dict(seconds=.05,checked_entries=1000),3963562,100,110592),
        python_path=sys.executable,pythonpath='fixed',input_sha256={},source_sha256={},config_pin={},runtime={})
    monkeypatch.setattr(b,'read_plan',lambda root:deepcopy(plan))
    monkeypatch.setattr(b,'check_upstream',lambda *args:None)
    return bundle,root,plan


def test_submit_ambiguous_retains_intent_and_lock(tmp_path,monkeypatch):
    bundle,root,plan=submit_fixture(tmp_path,monkeypatch);seen=[]
    def runner(command,**kwargs):seen.append(command);return SimpleNamespace(stdout='unknown')
    with pytest.raises(ValueError):b.submit(root,execute=True,controller_query=lambda:[],active_query=lambda:{},runner=runner)
    assert len(seen)==1 and seen[0][0]=='qsub'
    assert (root/'submission-intent.json').exists() and (bundle.parent/'tile-low-noise-submission.lock').exists()


def test_submit_final_controller_gate_prevents_qsub(tmp_path,monkeypatch):
    bundle,root,_=submit_fixture(tmp_path,monkeypatch)
    states=iter([[],['running']])
    with pytest.raises(ValueError):b.submit(root,execute=True,controller_query=lambda:next(states),active_query=lambda:{},runner=lambda *a,**k:pytest.fail('qsub'))
    assert not (root/'submission-intent.json').exists()
    assert not (bundle.parent/'tile-low-noise-submission.lock').exists()


def test_submit_post_intent_controller_gate_retains_lock(tmp_path,monkeypatch):
    bundle,root,_=submit_fixture(tmp_path,monkeypatch)
    states=iter([[],[],['running']])
    with pytest.raises(ValueError):
        b.submit(root,execute=True,controller_query=lambda:next(states),active_query=lambda:{},runner=lambda *a,**k:pytest.fail('qsub'))
    assert (root/'submission-intent.json').exists()
    assert (bundle.parent/'tile-low-noise-submission.lock').exists()
    assert not (root/'submission.json').exists()


def test_submit_replaced_lock_is_never_removed_or_accepted(tmp_path,monkeypatch):
    bundle,root,_=submit_fixture(tmp_path,monkeypatch)
    lock=bundle.parent/'tile-low-noise-submission.lock'
    def runner(*args,**kwargs):
        lock.unlink();lock.write_bytes(b'other owner')
        return SimpleNamespace(stdout='123.cluster')
    with pytest.raises(ValueError,match='lock ownership'):
        b.submit(root,execute=True,controller_query=lambda:[],active_query=lambda:{},runner=runner)
    assert lock.read_bytes()==b'other owner'
    assert not (root/'submission.json').exists()
    assert json.loads((root/'qsub-response.json').read_bytes())['stdout']=='123.cluster'


def test_submit_dry_run_and_once(tmp_path,monkeypatch):
    bundle,root,_=submit_fixture(tmp_path,monkeypatch)
    dry=b.submit(root)
    assert dry['job_id']=='dry-run' and '#PBS -l select=1:ncpus=1:mem=2gb' in (root/'census.sh').read_text()
    done=b.submit(root,execute=True,controller_query=lambda:[],active_query=lambda:{},runner=lambda *a,**k:SimpleNamespace(stdout='123.cluster'))
    assert done['job_id']=='123.cluster'
    with pytest.raises(ValueError):b.submit(root,execute=True)


def test_preimport_rejects_changed_source_before_cluster_modules(tmp_path,monkeypatch):
    source=tmp_path/'source.py';source.write_bytes(b'fixed')
    config=dict(schema=1,purpose='low_noise_timing_census_input',source_sha256={str(source):c.file_hash(source)},
        core_sha256={str(source):c.file_hash(source)})
    path=tmp_path/'config.json';path.write_bytes(c.canonical(config))
    source.write_bytes(b'changed')
    monkeypatch.setattr(b,'modules',lambda:pytest.fail('cluster modules imported before rejection'))
    with pytest.raises(ValueError):b.inspect_inputs(path,c.file_hash(path))


def test_shadow_import_resolution_rejected_before_cluster_imports(tmp_path,monkeypatch):
    config=dict(schema=1,purpose='low_noise_timing_census_input',source_sha256={'fixed.py':'a'*64})
    path=tmp_path/'config.json';path.write_bytes(c.canonical(config))
    monkeypatch.setattr(b,'preimport',lambda config:None)
    monkeypatch.setattr(b,'source_hashes',lambda:{'shadow.py':'a'*64})
    monkeypatch.setattr(b,'modules',lambda:pytest.fail('shadow module imported before closure rejection'))
    with pytest.raises(ValueError,match='actual import source closure differs'):
        b.inspect_inputs(path,c.file_hash(path))


@pytest.mark.parametrize('state',['Q','R'])
def test_queued_and_running_two_nodes_reject(tmp_path,monkeypatch,state):
    _,root,_=submit_fixture(tmp_path,monkeypatch)
    jobs={'1':dict(job_state=state,Resource_List=dict(select='2:ncpus=1:mem=2gb'))}
    with pytest.raises(ValueError):b.submit(root,execute=True,controller_query=lambda:[],active_query=lambda:jobs,runner=lambda *a,**k:pytest.fail('qsub'))


@pytest.fixture
def worker_fixture(tmp_path,monkeypatch):
    """Real three-entry engine/output/PBS-reader path; science/native boundary stubbed."""
    import tile_low_noise_timing_execution as execution
    import tile_low_noise_timing_seed_audit as seeds
    from test_tile_low_noise_timing_execution_gate import put,job_fixture
    root=tmp_path/'bundle'/'runs'/'census';root.mkdir(parents=True)
    bundle=dict(selection={'fixture':1},selection_sha256='f'*64,registry={'fixture':2},plans={k:{'fixture':k} for k in execution.plans.STAGES})
    data=put(root,'input.json',dict(fixed=1));source=put(root,'source.py',b'# source\n')
    platform=execution.native.platform_inputs()
    profile=platform['platform_profile'];fixture=platform['platform_fixture']
    profile_pin=put(root,'profile.json',profile);fixture_pin=put(root,'fixture.json',fixture)
    counts={f'old{i}':0 for i in range(56)};counts.update({k:0 for k in execution.plans.STAGES});counts['old0']=2;counts['low_timing.mc.capacity']=1
    role_counts={'calibration.bootstrap':1,'synthetic.bootstrap':1,'low_timing.mc.capacity.sample':1}
    catalog=dict(purpose='extended_low_noise_timing_seed_catalog',timing_bundle_digest=c.digest(bundle),registry_digest=c.digest(bundle['registry']),
        selection_sha256=bundle['selection_sha256'],selection_digest=c.digest(bundle['selection']),new_plan_sha256={k:c.digest(v) for k,v in bundle['plans'].items()},
        source_sha256={source['path']:source['sha256']},baseline_input_sha256={data['path']:data['sha256']},
        planned_counts=counts,planned_role_counts=role_counts,planned_total=3,reserved_unenumerated_stages={},expected_intentional_shared_entries=1)
    resource=b.resources(dict(seconds=.05,checked_entries=1000),3963562,100,110592)
    plan=dict(status='ready',catalog_evidence_digest=c.digest(catalog),runtime=execution.t.runtime(),source_sha256=catalog['source_sha256'],
        input_sha256=catalog['baseline_input_sha256'],native_input_digests=dict(profile=c.digest(profile),fixture=c.digest(fixture)),
        config_pin=dict(path=str(root/'config.json'),sha256='a'*64),resource=resource,relocation={},
        python_path=sys.executable,pythonpath='fixture',bundle=str(root.parents[1]))
    put(root,'manifest.json',plan);put(root,'catalog.json',catalog)
    script=b.script_text(root,plan);script_pin=put(root,'census.sh',script.encode())
    intent=dict(manifest=c.digest(plan),command=['qsub',str(root/'census.sh')],script_sha256=script_pin['sha256'],resource=resource)
    put(root,'submission-intent.json',intent);put(root,'submission.json',dict(intent,job_id='123.cluster'))
    context=dict(profile=profile,fixture=fixture,bundle=bundle,config=dict(profile=profile_pin,fixture=fixture_pin))
    factories={'old':lambda:iter([old.Entry('calibration.bootstrap',(33,0),0),old.Entry('synthetic.bootstrap',(33,0),0)]),
        'new':lambda:iter([old.Entry('low_timing.mc.capacity.sample',(161,0,0,0,0),0)])}
    monkeypatch.setattr(b,'read_plan',lambda root:deepcopy(plan))
    monkeypatch.setattr(b,'inspect_inputs',lambda *args:context)
    monkeypatch.setattr(b,'build_catalog',lambda ctx:(factories,catalog,{}))
    monkeypatch.setattr(b.socket,'gethostname',lambda:'node')
    monkeypatch.setattr(b.shutil,'disk_usage',lambda *args:SimpleNamespace(free=10**12))
    monkeypatch.setattr(execution.native.native_probe,'probe',lambda fixture:deepcopy(profile))
    monkeypatch.setattr(seeds,'INTENTIONAL_SHARED',1)
    monkeypatch.setenv('PBS_JOBID','123.cluster')
    for key,value in b.THREADS.items():monkeypatch.setenv(key,value)
    def scheduler(state):
        job=job_fixture(root/'census.sh',resource);job['job_state']=state
        return lambda *args,**kwargs:SimpleNamespace(stdout=json.dumps({'Jobs':{'123.cluster':job}}))
    return root,plan,bundle,scheduler


def test_small_worker_completion_and_seal_reach_real_formal_reader(worker_fixture):
    root,plan,bundle,scheduler=worker_fixture
    end=b.work(root,scheduler=scheduler('R'))
    assert end['complete'] and end['measurement']['sqlite_retained'] is False
    assert not list((root/'scratch').rglob('*.sqlite'))
    descriptor=b.seal(root,scheduler=scheduler('F'))
    assert len(descriptor)==12 and (root/'descriptor.json').exists()
    assert b.verify_descriptor(descriptor,bundle,b.modules().e.Evidence())['job_id']=='123.cluster'


def test_worker_input_change_is_failure_not_success(worker_fixture,monkeypatch):
    root,plan,_,scheduler=worker_fixture
    original=b.census_stream
    def changed(*args,**kwargs):
        result=original(*args,**kwargs)
        (root/'input.json').write_text('{}')
        return result
    monkeypatch.setattr(b,'census_stream',changed)
    with pytest.raises(ValueError):b.work(root,scheduler=scheduler('R'))
    assert (root/'failure.json').exists() and not (root/'completion.json').exists()


def test_seal_final_payload_recheck_rejects_change(worker_fixture,monkeypatch):
    root,plan,_,scheduler=worker_fixture
    b.work(root,scheduler=scheduler('R'))
    original=b.verify_descriptor
    def changed(*args,**kwargs):
        result=original(*args,**kwargs)
        (root/'result.json').write_text('{}')
        return result
    monkeypatch.setattr(b,'verify_descriptor',changed)
    with pytest.raises(ValueError):b.seal(root,scheduler=scheduler('F'))
    assert not (root/'descriptor.json').exists()
