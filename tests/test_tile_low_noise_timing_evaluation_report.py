"""Fixed-cohort bounded evaluation, with saved-input verification tested separately."""
import copy
import json
import shlex
from pathlib import Path
import sys

import pytest

pytest.importorskip("ldpc")
pytest.importorskip("bposd")
pytest.importorskip("pymatching")
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "cluster_scripts"))
import calibration as c
import tile_low_noise_timing_evaluation_report as r


def fixture():
    rows = []
    refs = {}
    cohorts = {}
    for case, target, epsilon in r.IDENTITIES:
        identity = (case, target, epsilon)
        rows.append(dict(case=case, target_index=target, epsilon_index=epsilon,
            epsilon=(.2, .1)[epsilon], target_p=(.01, .003, .001)[target],
            status="selected", planning_status="ready", reference_interval=[.0999, .1001],
            selected_condition={"case":case}))
        refs[(case,target)] = dict(interval=[.0999,.1001], partial_estimate=.099,
            omitted_mass_upper=.002, full_point_estimate=None)
        cohorts[identity] = {}
        for method, cost in (("mc",2.),("bar",1.)):
            records = [dict(task=[case,target,epsilon,i], status="ok", estimate=.1,
                interval=[.09,.11], available=True, task_wall_seconds=cost,
                cpu_seconds=cost/2, inclusive_wall_seconds=cost+.1,
                inclusive_cpu_seconds=cost/2+.01, failure=None) for i in range(192)]
            cohorts[identity][method] = dict(status="completed", allocated_tasks=192,
                records=records, partitions=[], capacity={})
    return rows, refs, cohorts


def test_full_24_rows_fixed_denominators_and_placeholder_scope():
    rows, refs, cohorts = fixture()
    result = r.assess_rows(rows, refs, cohorts)
    assert len(result) == 24
    for row in result:
        assert row["planned_replicates"] == 192
        assert row["mc"]["observed_tasks"] == 192
        assert row["ratios_mc_over_bar"]["cpu_seconds"]["value"] == 2
        assert row["bar"]["assessment"]["reference_point"] is None
        assert row["bar"]["assessment"]["metrics"]["undefined"] == 192
        assert row["diagnostic_observation"] == {"mc":"not_applicable","bar":"not_collected"}
        assert row["bar_internal_flagged_undefined_are_unobserved_placeholders"] is True
        assert row["reference"]["omitted_mass_upper"] == .002


@pytest.mark.parametrize("kind", ["above","sensitive","failed","interval_missing","point_missing",
    "cpu_missing","wall_missing","incomplete","not_started","resource_infeasible","not_selected"])
def test_states_costs_and_missing_values_keep_denominator(kind):
    rows, refs, cohorts = fixture()
    bar = cohorts[(0,0,0)]["bar"]
    if kind == "above":
        for record in bar["records"]:record["estimate"] = .2
    elif kind == "sensitive":
        refs[(0,0)]["interval"] = rows[0]["reference_interval"] = rows[1]["reference_interval"] = [.08,.12]
    elif kind == "failed":bar["records"][0].update(status="failed",failure="sampling")
    elif kind == "interval_missing":bar["records"][0].update(interval=None,available=False,status="unavailable")
    elif kind == "point_missing":bar["records"][0].update(estimate=None,interval=None,available=False,status="unavailable")
    elif kind == "cpu_missing":bar["records"][0]["cpu_seconds"] = None
    elif kind == "wall_missing":bar["records"][0]["task_wall_seconds"] = None
    else:
        bar.update(status=kind,records=[])
        if kind == "not_selected":
            rows[0].update(status="ineligible_width",planning_status="not_selected")
            for cohort in cohorts[(0,0,0)].values():cohort.update(status=kind,records=[],allocated_tasks=0)
    row = r.assess_rows(rows,refs,cohorts)[0]
    assert row["planned_replicates"] == 192
    ratios = row["ratios_mc_over_bar"]
    if kind == "interval_missing":
        assert ratios["cpu_seconds"]["value"] == 2
        assert row["bar"]["assessment"]["metrics"]["unavailable_intervals"] == 1
        assert row["bar"]["assessment"]["metrics"]["covered_reference_entire"] == 191
    elif kind == "wall_missing":
        assert ratios["cpu_seconds"]["value"] == 2
        assert ratios["task_wall_seconds"]["value"] is None
    else:assert ratios["cpu_seconds"]["value"] is None
    if kind == "cpu_missing":assert ratios["task_wall_seconds"]["value"] == 2
    if kind in ("incomplete","not_started","resource_infeasible","not_selected"):
        assert row["bar"]["observed_tasks"] is None
    if kind == "failed":
        assert row["bar"]["assessment"]["metrics"]["failures"] == {"sampling":1}
        assert row["bar"]["costs"]["cpu_seconds"]["mean"] == .5


@pytest.mark.parametrize("interval,label", [(None,"reference_unavailable"),([0.,.1],"reference_zero_boundary"),
    ([.1,.1],"empirical_within_target"),([.09,.11],"empirical_within_target")])
def test_bounds_not_partial_point(interval,label):
    rows, refs, cohorts = fixture()
    rows[0]["reference_interval"] = rows[1]["reference_interval"] = interval
    refs[(0,0)]["interval"] = interval
    refs[(0,0)]["partial_estimate"] = .8
    result = r.assess_rows(rows,refs,cohorts)[0]
    assert result["mc"]["assessment"]["precision"][0]["classification"] == label
    assert result["mc"]["assessment"]["reference_point"] is None


def test_ratio_means_and_independent_inclusive_clock():
    rows, refs, cohorts = fixture()
    records = cohorts[(0,0,0)]["bar"]["records"]
    records[0]["cpu_seconds"] = 9.5
    records[0]["inclusive_cpu_seconds"] = None
    row = r.assess_rows(rows,refs,cohorts)[0]
    assert row["ratios_mc_over_bar"]["cpu_seconds"]["value"] == pytest.approx(192/(191*.5+9.5))
    assert row["ratios_mc_over_bar"]["inclusive_cpu_seconds"]["value"] is None


@pytest.mark.parametrize("value", [float("nan"),float("inf"),-1,True])
def test_bad_cost_rejected(value):
    rows,refs,cohorts = fixture()
    cohorts[(0,0,0)]["bar"]["records"][0]["cpu_seconds"] = value
    with pytest.raises(ValueError):r.assess_rows(rows,refs,cohorts)


def test_zero_bar_cost_null_and_duplicate_replicate_rejected():
    rows,refs,cohorts = fixture()
    records = cohorts[(0,0,0)]["bar"]["records"]
    for record in records:record["cpu_seconds"] = 0
    result = r.assess_rows(rows,refs,cohorts)[0]
    assert result["ratios_mc_over_bar"]["cpu_seconds"]["reason"] == "zero_bar_mean_cost"
    records[0]["task"] = records[1]["task"]
    with pytest.raises(ValueError,match="replicate"):r.assess_rows(rows,refs,cohorts)


def test_all_unallocated_and_japanese_report(tmp_path):
    rows,refs,cohorts = fixture()
    for row in rows:
        row.update(status="ineligible_width",planning_status="not_selected")
    for methods in cohorts.values():
        for cohort in methods.values():cohort.update(status="not_selected",records=[],allocated_tasks=0)
    report = dict(purpose=r.REPORT_PURPOSE,records=r.assess_rows(rows,refs,cohorts),
        census=dict(status="not_required_no_allocations",new_namespaces_audited=False))
    text = r.report_text(report)
    assert text.count("ineligible_width") == 24
    assert "192" in text and "not_required_no_allocations" in text
    assert "未取得" in text and "共用" in text and "按分" in text
    path = tmp_path/"report.json"
    c.atomic_json(path,report)
    r.render(path,c.file_hash(path),tmp_path/"report.md")
    assert (tmp_path/"report.md").read_text(encoding="utf-8") == text
    with pytest.raises(ValueError):r.render(path,"0"*64,tmp_path/"bad.md")
    with pytest.raises(FileExistsError):r.render(path,c.file_hash(path),tmp_path/"report.md")


def test_full_report_requires_pbs_before_input_io(tmp_path,monkeypatch):
    monkeypatch.delenv("PBS_JOBID",raising=False)
    with pytest.raises(ValueError,match="PBS"):
        r.run(tmp_path/"absent","0"*64,tmp_path/"output")


def test_snapshot_reads_consumed_bytes_and_rejects_mutation(tmp_path):
    path = tmp_path/"input.json"
    c.atomic_json(path,{"sealed":True})
    proof = r.Evidence()
    pin = dict(path=str(path),sha256=c.file_hash(path))
    assert r.read_pin(pin,proof) == {"sealed":True}
    c.atomic_json(path,{"sealed":False})
    with pytest.raises(ValueError):proof.finish()


def test_partition_merge_requires_exact_fixed_tasks():
    rows,refs,cohorts = fixture()
    records = cohorts[(0,0,0)]["mc"]["records"]
    partitions = [dict(status="completed",records=records[:96]),dict(status="completed",records=records[96:])]
    assert len(r.merge_partitions((0,0,0),partitions)) == 192
    partitions[1]["records"] = records[95:]
    with pytest.raises(ValueError):r.merge_partitions((0,0,0),partitions)
    partitions[1]["records"] = records[97:]
    with pytest.raises(ValueError):r.merge_partitions((0,0,0),partitions)


def selector_fixture(tmp_path, monkeypatch):
    def pin(name,value):
        path=tmp_path/name
        path.write_bytes(value if isinstance(value,bytes) else c.canonical(value)+b"\n")
        return dict(path=str(path),sha256=c.file_hash(path))
    source=pin("source.py",b"# fixed selector\n")
    native=pin("native.json",dict(fixed=True))
    sources={source["path"]:source["sha256"]}
    monkeypatch.setattr(r.selector,"source_hashes",lambda:sources)
    monkeypatch.setattr(r,"runtime",lambda:dict(fixture=True))
    inp=pin("input.json",dict(fixed=True))
    report=pin("selection.json",dict(input_manifest_sha256=inp["sha256"],source_sha256=sources))
    resource=r.execution.capacity_resources()
    argv=[sys.executable,str(Path(r.selector.__file__).absolute()),"--input",inp["path"],
        "--expected-sha256",inp["sha256"],"--output",report["path"]]
    prepared=dict(schema=1,purpose="low_noise_timing_selector_execution",input=inp,report_path=report["path"],
        selector_argv=argv,source_sha256=sources,runtime=r.runtime(),python_path=sys.executable,
        python_sha256=c.file_hash(sys.executable),native_binding={native["path"]:native["sha256"]},resource=resource)
    script=pin("selector.sh",("#!/bin/bash\n"+shlex.join(argv)+"\n").encode())
    intent=dict(manifest=c.digest(prepared),command=["qsub",script["path"]],script_sha256=script["sha256"],resource=resource)
    submit=dict(intent,job_id="123.cluster")
    actual=dict(manifest=c.digest(prepared),pbs_job_id=submit["job_id"],hostname="node",input_sha256=inp["sha256"],
        selector_argv=argv,source_sha256=sources,runtime=r.runtime(),python_path=sys.executable,
        python_sha256=prepared["python_sha256"],native_binding=prepared["native_binding"])
    completed=dict(actual,report_sha256=report["sha256"],complete=True)
    from test_tile_low_noise_timing_execution_gate import job_fixture
    terminal={"Jobs":{submit["job_id"]:job_fixture(script["path"],resource)}}
    desc={key:pin(key+".json",value) for key,value in (("prepared",prepared),("intent",intent),
        ("submission",submit),("execution",actual),("completion",completed),("terminal",terminal))}
    desc["script"]=script
    return desc,report,inp,pin


def test_selector_descriptor_binds_actual_execution(tmp_path,monkeypatch):
    desc,report,inp,_=selector_fixture(tmp_path,monkeypatch)
    result=r.selector_evidence(desc,report,r.Evidence())
    assert result["job_id"]=="123.cluster"
    assert result["fresh_native_probe_claimed"] is False
    assert result["input_sha256"]==inp["sha256"]


@pytest.mark.parametrize("which,field,value",[("terminal","run_count",2),("terminal","Exit_status",1),
    ("completion","report_sha256","0"*64),("completion","native_binding",{}),
    ("execution","hostname","other"),("submission","script_sha256","0"*64),
    ("prepared","selector_argv",["wrong"])])
def test_selector_descriptor_rejects_rebound_metadata(tmp_path,monkeypatch,which,field,value):
    desc,report,_,pin=selector_fixture(tmp_path,monkeypatch)
    obj=json.loads(Path(desc[which]["path"]).read_bytes())
    target=obj["Jobs"]["123.cluster"] if which=="terminal" else obj
    target[field]=value
    desc[which]=pin(which+".json",obj)
    with pytest.raises(ValueError):r.selector_evidence(desc,report,r.Evidence())


def test_no_allocation_census_requires_bound_bridge_and_zero_plans(tmp_path,monkeypatch):
    bundle=dict(selection={"rows":[dict(status="ineligible") for _ in range(24)]},
        selection_sha256="a"*64,registry={"fixture":1},plans={role:dict(planned_seed_entries=0)
        for role in r.plans.STAGES})
    plan=dict(status="not_required_no_allocations",selected_rows=0,new_allocations=0,
        scientific_bundle_digest=c.digest(bundle),registry_digest=c.digest(bundle["registry"]),
        selection_sha256=bundle["selection_sha256"],baseline_result_sha256="b"*64,
        baseline_verified_namespaces=56,new_namespaces_audited=False,formal_census_descriptor=None)
    root=tmp_path/"census";root.mkdir();c.atomic_json(root/"manifest.json",plan)
    monkeypatch.setattr(r,"bridge_noop_state",lambda *args:copy.deepcopy(plan))
    desc=dict(root=str(root),manifest=dict(path=str(root/"manifest.json"),sha256=c.file_hash(root/"manifest.json")))
    assert r.census_evidence(desc,bundle,r.Evidence())["new_namespaces_audited"] is False
    bundle["plans"][next(iter(bundle["plans"]))]["planned_seed_entries"]=1
    with pytest.raises(ValueError):r.census_evidence(desc,bundle,r.Evidence())


def reference_fixture(tmp_path,monkeypatch):
    root=tmp_path/'reference';audit=tmp_path/'audit';root.mkdir();audit.mkdir()
    pins={}
    def put(path,value):
        path.parent.mkdir(parents=True,exist_ok=True)
        path.write_bytes(value if isinstance(value,bytes) else c.canonical(value)+b'\n')
        pins[str(path)]=c.file_hash(path)
        return pins[str(path)]
    source=tmp_path/'source.py';put(source,b'# fixed audit\n')
    sources={str(source):c.file_hash(source)}
    monkeypatch.setattr(r.reference_run,'source_hashes',lambda:sources)
    monkeypatch.setattr(r.reference_run,'report_binding',lambda *args:None)
    # This fixture models saved metadata, not an immutable deployment tree.
    # Dedicated source-binding and reader-connection tests use real trees.
    monkeypatch.setattr(r.source_binding,'reference_source_context',lambda *args:dict(saved_root=tmp_path,current_root=tmp_path,sources=sources))
    monkeypatch.setattr(r.source_binding,'reference_sources',lambda *args:None)
    context={'purpose':'test_reference'};put(root/'manifest.json',context)
    put(root/'summary.json',dict(unavailable=0))
    raw=root/'chunks'/'raw.bin';put(raw,b'raw input')
    profile=dict(fixture=True)
    plan=dict(reference_root=str(root.resolve()),reference_context=context,source_sha256=sources,
        input_sha256={},original_pbs_job_id='1.cluster',actual_native_profile_digest=c.digest(profile))
    put(audit/'manifest.json',plan)
    intent=dict(manifest=c.digest(plan),reference_context=c.digest(context),conditions=list(range(16)),workers=16,
        hostname='node',pbs_job_id='2.cluster')
    put(audit/'execution-intent.json',intent)
    native=dict(intent,profile=profile,original_pbs_job_id='1.cluster');put(audit/'native_preflight.json',native)
    records=[];markers={};bindings=[]
    for i in range(16):
        case=i//4;target=i%4;prior=((.03 if case%2==0 else .05),.01,.003,.001)[target]
        size,noise=r.bounded.study.CASES[case]
        reference=r.bounded.weight.synthesize(2*size*size,noise,prior,[dict(w=0,mode='enum',trials=1,failures=0)],.001)
        cond=dict(condition=i,case=case,physical_decoder_prior=prior,planned_trials=1,available_trials=1,
            available=True,failed_chunks=[],reference=reference)
        report=dict(condition=cond,input_sha256={'chunks/raw.bin':c.file_hash(raw)},source_sha256=sources)
        record=dict(condition=i,status='ok',report=report)
        base=audit/'conditions'/str(i)
        c.save_artifact(base,dict(manifest=c.digest(plan),condition=i),{},record)
        for ext in ('.json','.npz','.done.json'):pins[str(base.with_suffix(ext))]=c.file_hash(base.with_suffix(ext))
        markers[str(i)]=c.file_hash(base.with_suffix('.done.json'))
        records.append({key:value for key,value in record.items() if key!='report'})
        if target:bindings.append(dict(reference_condition=i,reference_context=c.digest(context),
            reference_audit_digest=c.digest(report),reference_interval=reference['interval']))
    summary=dict(manifest=c.digest(plan),tasks=16,failed=0,all_conditions_audited=True,terminal_binding_valid=True,
        phase_failure=None,phase_failures=[],records=records,pbs_job_id='2.cluster',condition_marker_sha256=markers,
        execution_intent_sha256=c.file_hash(audit/'execution-intent.json'),native_preflight_sha256=c.file_hash(audit/'native_preflight.json'))
    put(audit/'summary.json',summary)
    jobs={}
    for base,job,manifest in ((root,'1.cluster',c.digest(context)),(audit,'2.cluster',c.digest(plan))):
        script=base/'run.sh';put(script,b'#!/bin/bash\n')
        ledger=dict(manifest=manifest,command=['qsub',str(script)],script_sha256=c.file_hash(script))
        put(base/'submission-intent.json',ledger);put(base/'submission.json',dict(ledger,job_id=job))
        jobs[job]=dict(job_state='F',Exit_status=0,Submit_arguments=str(script))
    terminal=tmp_path/'terminal.json';put(terminal,dict(Jobs=jobs))
    config=dict(root=str(root),audit_root=str(audit),input_sha256=pins,
        terminal=dict(path=str(terminal),sha256=c.file_hash(terminal)))
    return config,dict(calibration_bindings=bindings),raw


def test_reference_full_synthesis_and_consumed_current_hash(tmp_path,monkeypatch):
    config,selection,raw=reference_fixture(tmp_path,monkeypatch)
    refs,evidence=r.reference_evidence(config,selection,r.Evidence())
    assert len(refs)==12 and evidence['audit_reports']==16
    assert evidence['current_raw_payloads_rehashed'] is False
    monkeypatch.setenv('PBS_JOBID','3.cluster')
    proof=r.Evidence()
    assert r.reference_evidence(config,selection,proof,full=True)[1]['current_raw_payloads_rehashed'] is True
    raw.write_bytes(b'changed')
    with pytest.raises(ValueError):proof.finish()
    with pytest.raises(ValueError):r.reference_evidence(config,selection,r.Evidence(),full=True)


def test_reference_selection_digest_and_pbs_guard(tmp_path,monkeypatch):
    config,selection,raw=reference_fixture(tmp_path,monkeypatch)
    monkeypatch.delenv('PBS_JOBID',raising=False)
    with pytest.raises(ValueError,match='PBS'):r.reference_evidence(config,selection,r.Evidence(),full=True)
    selection['calibration_bindings'][0]['reference_audit_digest']='0'*64
    with pytest.raises(ValueError):r.reference_evidence(config,selection,r.Evidence())


def test_reference_rejects_unexpected_raw_chunk_member(tmp_path,monkeypatch):
    config,selection,raw=reference_fixture(tmp_path,monkeypatch)
    monkeypatch.setenv('PBS_JOBID','3.cluster')
    raw.with_name('extra.bin').write_bytes(b'unconsumed')
    with pytest.raises(ValueError,match='census'):r.reference_evidence(config,selection,r.Evidence(),full=True)


def test_metadata_snapshot_never_calls_recursive_completed_reader(tmp_path,monkeypatch):
    root=tmp_path/'main';root.mkdir()
    role='low_timing.mc.benchmark';science={'fixed':True}
    envelope=dict(purpose='low_noise_independent_timing_execution',role=role,identity=[0,0,0],science=science,mode='benchmark')
    c.atomic_json(root/'manifest.json',envelope)
    monkeypatch.setattr(r.execution,'read_plan',lambda *a:(_ for _ in ()).throw(AssertionError('would scan capacity')))
    monkeypatch.setattr(r.execution,'completed',lambda *a,**k:(_ for _ in ()).throw(AssertionError('payload scan forbidden')))
    proof=r.Evidence()
    result=r.root_snapshot(dict(root=str(root),manifest_sha256=c.file_hash(root/'manifest.json')),role,(0,0,0),dict(plans={role:science}),proof)
    assert result['state']=='not_started' and set(proof.hashes)=={str(root/'manifest.json')}


@pytest.mark.parametrize('failed',[False,True])
def test_real_two_task_capacity_reader_connection(tmp_path,monkeypatch,failed):
    from test_tile_low_noise_timing_execution_gate import execution_fixture,put,job_fixture
    envelope,manifest,script,scheduler=execution_fixture(tmp_path,monkeypatch)
    if failed:
        monkeypatch.setattr(r.execution.qec,'direct_mc',lambda *a,**k:(_ for _ in ()).throw(RuntimeError('synthetic decoder failure')))
    summary=r.execution.run(tmp_path,scheduler=scheduler)
    terminal=put(tmp_path,'terminal.json',dict(Jobs={'123.cluster':job_fixture(script['path'],envelope['resource'])}))
    item=dict(root=str(tmp_path),terminal=terminal,manifest_sha256=manifest['sha256'])
    proof=r.Evidence();result=r.load_execution(item,dict(state='complete_candidate'),proof);proof.finish()
    assert len(result['records'])==2 and result['summary']==summary
    assert result['status']==('completed_with_recorded_task_failures' if failed else 'completed')
    assert all(row['task_wall_seconds']>0 for row in result['records'])
    if failed:assert r.execution.resource_plan(result['summary'])['status']=='capacity_failed'
    path=tmp_path/'tasks'/ (c.task_id(envelope['tasks'][0])+'.json')
    path.write_bytes(path.read_bytes()+b' ')
    with pytest.raises(ValueError):r.load_execution(item,dict(state='complete_candidate'),r.Evidence())


def orchestration_fixture(tmp_path,monkeypatch):
    rows,refs,cohorts=fixture()
    for row in rows:row.update(status='ineligible_width',planning_status='not_selected')
    source=tmp_path/'fixed.py';source.write_text('# accepted\n')
    dependency=tmp_path/'accepted.json';c.atomic_json(dependency,dict(fixed=True))
    source_sha=c.file_hash(source);dep_sha=c.file_hash(dependency)
    config=dict(reference={key:str(tmp_path/key) for key in ('root','audit_root')},census={},
        cohorts=[dict(identity=list(key),mc=dict(capacity=None,partitions=[]),bar=dict(capacity=None,partitions=[])) for key in r.IDENTITIES])
    path=tmp_path/'config.json';c.atomic_json(path,config)
    snapshots=[dict(identity=list(key),mc=dict(capacity=None,partitions=[]),bar=dict(capacity=None,partitions=[])) for key in r.IDENTITIES]
    context=dict(bundle=dict(selection={'rows':rows},registry={'fixture':True}),rows=rows,references=refs,
        snapshots=snapshots,selector=dict(job_id='1.cluster'),census=dict(status='not_required_no_allocations',new_namespaces_audited=False))
    def load(config,proof):
        assert r.read_pin(dict(path=str(dependency),sha256=dep_sha),proof)==dict(fixed=True)
        return copy.deepcopy(context)
    monkeypatch.setattr(r,'sources',lambda proof:{str(source):proof.track(source)})
    monkeypatch.setattr(r,'runtime',lambda:dict(fixture=True))
    monkeypatch.setattr(r,'inputs',load)
    monkeypatch.setattr(r,'reference_evidence',lambda *a,**k:(refs,dict(audit_reports=16,current_raw_payloads_rehashed=k.get('full',False))))
    monkeypatch.setenv('PBS_JOBID','321.cluster')
    for key,value in r.execution.THREADS.items():monkeypatch.setenv(key,value)
    plan=tmp_path/'plan.json'
    r.prepare(path,c.file_hash(path),plan)
    return plan,source,dependency,context


def test_no_allocation_report_publication_keeps_all_outcomes(tmp_path,monkeypatch):
    plan,_,_,_=orchestration_fixture(tmp_path,monkeypatch)
    result=r.run(plan,c.file_hash(plan),tmp_path/'report')
    assert len(result['records'])==24 and result['census']['status']=='not_required_no_allocations'
    assert all(row['mc']['allocated_tasks']==0 and row['bar']['allocated_tasks']==0 for row in result['records'])
    assert all(value['value'] is None for row in result['records'] for value in row['ratios_mc_over_bar'].values())
    assert result['report_terminal_externally_confirmed'] is False
    assert result['all_physical_states_redecoded'] is False and 'physical_states_redecoded' not in result
    assert 'initial/final' in result['timing_checkpoint_validation_scope']
    assert result['japanese_report_sha256']==c.file_hash(tmp_path/'report'/'report_ja.md')
    with pytest.raises(ValueError):r.run(plan,c.file_hash(plan),tmp_path/'report')


@pytest.mark.parametrize('which',['source','dependency','snapshot'])
def test_late_input_changes_never_publish_success(tmp_path,monkeypatch,which):
    plan,source,dependency,context=orchestration_fixture(tmp_path,monkeypatch)
    original=r.assess_rows
    def changed(*args):
        result=original(*args)
        if which=='snapshot':context['snapshots'][0]['mc']['capacity']={'unexpected':True}
        else:(source if which=='source' else dependency).write_text('changed')
        return result
    monkeypatch.setattr(r,'assess_rows',changed)
    output=tmp_path/'report'
    with pytest.raises(ValueError):r.run(plan,c.file_hash(plan),output)
    assert not (output/'report.json').exists()
    assert json.loads((output/'validation_failure.json').read_bytes())['success_report_published'] is False


def test_bridge_readonly_subprocess_uses_fixed_invocation(tmp_path,monkeypatch):
    from types import SimpleNamespace
    root=tmp_path/'bridge';root.mkdir()
    source=Path(r.census.__file__).resolve()
    core=tmp_path/'core.py';core.write_text('# core\n')
    config=dict(purpose='low_noise_timing_census_input',python_path=sys.executable,python_sha256=c.file_hash(sys.executable),
        pythonpath='fixed:path',source_sha256={str(source):c.file_hash(source)},core_sha256={str(core):c.file_hash(core)})
    c.atomic_json(root/'config.json',config)
    plan=dict(config_pin=dict(path=str(root/'config.json'),sha256=c.file_hash(root/'config.json')))
    calls=[]
    def runner(argv,**kwargs):
        calls.append((argv,kwargs));return SimpleNamespace(stdout='{"status":"not_required_no_allocations"}',stderr='')
    monkeypatch.setattr(r.subprocess,'run',runner)
    result=r.bridge_noop_state(root,plan,r.Evidence())
    assert result['status']=='not_required_no_allocations' and len(calls)==1
    argv,kwargs=calls[0]
    assert argv[0]==sys.executable and 'state_only(b.read_plan' in argv[2]
    assert 'b.submit' not in argv[2] and 'b.run' not in argv[2]
    assert kwargs['env']['PYTHONPATH']=='fixed:path' and kwargs['timeout']==30


@pytest.mark.parametrize('mode',['complete','missing_partition','incomplete','wrong_resource','duplicate_task'])
def test_main_partition_aggregation_and_resource_binding(monkeypatch,mode):
    rows,refs,cohorts=fixture();key=(0,0,0);row=rows[0]
    capref=dict(root='/capacity',terminal={'path':'/terminal','sha256':'a'*64},manifest_sha256='b'*64,
        summary_sha256='c'*64,submission_sha256='d'*64)
    capitem=dict(capref,submission={'path':'/capacity/submission.json','sha256':'d'*64})
    resource={'cpus':96};decision=dict(status='ready',partitions=[dict(index=i,replicates=list(range(i*96,(i+1)*96)),resource=resource) for i in range(2)])
    snapshot=dict(capacity={'state':'complete_candidate'},partitions=[])
    item=dict(capacity=capitem,partitions=[])
    for i in range(2):
        manifest=dict(partition_index=i,tasks=[[*key,rep] for rep in decision['partitions'][i]['replicates']],resource=resource,
            resource_decision=decision,capacity_reference=capref)
        snapshot['partitions'].append(dict(state='complete_candidate',manifest=manifest))
        item['partitions'].append(dict(index=i))
    records=cohorts[key]['mc']['records']
    def loaded(entry,*args):
        if 'index' not in entry:return dict(summary={},status='completed',records=[])
        chunk=copy.deepcopy(records[entry['index']*96:(entry['index']+1)*96])
        if mode=='duplicate_task' and entry['index']==1:chunk[0]['task']=[0,0,0,95]
        return dict(status='completed',records=chunk,summary=dict(execution_wall_seconds=3.))
    monkeypatch.setattr(r,'load_execution',loaded)
    monkeypatch.setattr(r.execution,'resource_plan',lambda _:decision)
    if mode=='missing_partition':snapshot['partitions'].pop()
    if mode=='incomplete':snapshot['partitions'][1]['state']='incomplete'
    if mode=='wrong_resource':snapshot['partitions'][1]['manifest']['resource']={'cpus':1}
    if mode in ('missing_partition','wrong_resource','duplicate_task'):
        with pytest.raises(ValueError):r.load_method(key,'mc',row,item,snapshot,r.Evidence())
    else:
        result=r.load_method(key,'mc',row,item,snapshot,r.Evidence())
        assert result['allocated_tasks']==192
        if mode=='complete':assert len(result['records'])==192 and result['status']=='completed'
        else:
            assert result['records']==[] and result['status']=='incomplete'
            assert result['verified_partial']['observed_tasks']==96


def test_actual_plan_builder_connects_metadata_without_payload_scan(tmp_path,monkeypatch):
    from test_tile_low_noise_timing_plan import selection as fixed_selection
    selection=fixed_selection.__wrapped__()
    selectpath=tmp_path/'selection.json';c.atomic_json(selectpath,selection)
    bundle=r.plans.make_plans(selection,selection_sha256=c.file_hash(selectpath))
    bundlepath=tmp_path/'bundle.json';c.atomic_json(bundlepath,bundle)
    refs={(row['case'],row['target_index']):dict(interval=row['reference_interval']) for row in selection['rows']}
    entries=[]
    for row in bundle['plans']['low_timing.mc.benchmark']['rows']:
        key=r.identity(row);entry=dict(identity=list(key))
        for method in ('mc','bar'):
            entry[method]=dict(capacity=dict(root=str(tmp_path/(method+'-capacity'))) if row['planning_status']=='ready' else None,partitions=[])
        entries.append(entry)
    config=dict(scientific_bundle=dict(path=str(bundlepath),sha256=c.file_hash(bundlepath)),
        selection=dict(path=str(selectpath),sha256=c.file_hash(selectpath)),registry_digest=c.digest(bundle['registry']),
        selector_execution={},census={},reference={},cohorts=entries)
    monkeypatch.setattr(r,'selector_evidence',lambda *args:{'fixture':True})
    monkeypatch.setattr(r,'census_evidence',lambda *args:{'fixture':True})
    monkeypatch.setattr(r,'reference_evidence',lambda *args,**kwargs:(refs,{}))
    monkeypatch.setattr(r.execution,'completed',lambda *a,**k:(_ for _ in ()).throw(AssertionError('no full payload I/O')))
    context=r.inputs(config,r.Evidence())
    assert len(context['rows'])==24 and context['snapshots'][0]['mc']['capacity']['state']=='not_prepared'
    config['cohorts'][0]['bar']['capacity']=config['cohorts'][0]['mc']['capacity']
    with pytest.raises(ValueError,match='disjoint'):r.inputs(config,r.Evidence())


def test_actual_source_closure_includes_all_bound_readers():
    found=r.source_files()
    assert {'tile_low_noise_timing_evaluation_report','tile_low_noise_timing_execution','tile_low_noise_timing_census',
        'tile_weight_reference_comparison','tile_precision_assessment','tile_weight_reference_audit_run'}<=set(found)
    assert found['tile_low_noise_timing_execution']==Path(r.execution.__file__).absolute()
    assert any(name.startswith('package/') for name in found)


def test_mc_point_available_without_interval_is_not_discarded():
    rows,refs,cohorts=fixture()
    cohorts[(0,0,0)]['mc']['records'][0].update(available=True,interval=None)
    row=r.assess_rows(rows,refs,cohorts)[0]
    assert row['mc']['assessment']['metrics']['point_estimates']==192
    assert row['mc']['assessment']['metrics']['unavailable_intervals']==1
    assert row['ratios_mc_over_bar']['cpu_seconds']['value']==2


@pytest.mark.parametrize('status',['capacity_failed','capacity_unavailable','execution_infeasible_memory_policy',
    'execution_infeasible_wall_policy','execution_infeasible_capacity_envelope'])
def test_capacity_infeasible_keeps_main_goal_but_zero_allocated_tasks(monkeypatch,status):
    rows,_,_=fixture()
    monkeypatch.setattr(r,'load_execution',lambda *a:dict(summary={},records=[{},{}]))
    monkeypatch.setattr(r.execution,'resource_plan',lambda _:dict(status=status,partitions=[]))
    result=r.load_method((0,0,0),'mc',rows[0],dict(capacity={},partitions=[]),
        dict(capacity={'state':'complete_candidate'},partitions=[]),r.Evidence())
    assert result['allocated_tasks']==0 and result['status']==status and len(result['capacity']['records'])==2
    value=r.assess_cohort('mc',(0,0,0),result,[.0999,.1001],.2)
    assert value['planned_replicates']==192 and value['observed_tasks'] is None


def test_prepare_rejects_output_target_change_before_writing(tmp_path,monkeypatch):
    plan,_,_,_=orchestration_fixture(tmp_path,monkeypatch)
    value=json.loads(plan.read_bytes());output=tmp_path/'new-plan.json'
    original_gate=r.outside_inputs;original_resolve=Path.resolve
    def gate(path,config,proof):
        original_gate(path,config,proof)
        monkeypatch.setattr(Path,'resolve',lambda self,*a,**k:tmp_path/'root'/'new-plan.json'
            if self==output else original_resolve(self,*a,**k))
    monkeypatch.setattr(r,'outside_inputs',gate)
    with pytest.raises(ValueError,match='target changed'):
        r.prepare(value['config_pin']['path'],value['config_pin']['sha256'],output)
    assert not output.exists() and not (tmp_path/'root'/'new-plan.json').exists()


def test_failure_record_rejects_output_retarget_after_mkdir(tmp_path,monkeypatch):
    plan,_,_,_=orchestration_fixture(tmp_path,monkeypatch)
    output=tmp_path/'report'
    monkeypatch.setattr(r,'assess_rows',lambda *a:(_ for _ in ()).throw(ValueError('fixture evaluation failure')))
    original_mkdir=Path.mkdir;original_resolve=Path.resolve
    def mkdir(path,*args,**kwargs):
        original_mkdir(path,*args,**kwargs)
        if path==output:
            monkeypatch.setattr(Path,'resolve',lambda self,*a,**k:tmp_path/'root'/'report'
                if self==output else original_resolve(self,*a,**k))
    monkeypatch.setattr(Path,'mkdir',mkdir)
    with pytest.raises(ValueError,match='target changed'):
        r.run(plan,c.file_hash(plan),output)
    assert not (output/'validation_failure.json').exists() and not (output/'report.json').exists()
