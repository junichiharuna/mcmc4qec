"""Small cohort arithmetic and explicit mocked persisted-reader boundaries."""
from copy import deepcopy
import json
from pathlib import Path
import sys

import pytest

for dependency in ("ldpc", "bposd", "pymatching"):
    pytest.importorskip(dependency)
sys.path.insert(0, str(Path(__file__).resolve().parents[1]/"cluster_scripts"))
import calibration as c
import tile_low_noise_study as low
import tile_low_noise_summary as summary
import tile_low_noise_timing_selection as selector


def numerical_inputs():
    # Explicit reduced setting fixture; all 192 planned replicates are real rows.
    plan=low.make_plan(0,0,capacity=False)
    plan.update(burns=[0],blocks=[2])
    plan["condition"].update(chains=4,steps=8,windows=[8],rungs=[.1,.01],coarse=[.1,.01])
    rows=[]
    for key in summary.expected_conditions(plan):
        for rep in range(192):
            row=dict(zip(summary.CONDITION,key))
            row.update(group=[0,0,list(plan["kernels"]).index(row["kernel"]),plan["initializations"].index(row["init"]),rep],
                replicate=rep,target_p=.01,noise="bit",n=72,estimate=.1,interval=None,
                available=False,flagged=True,undefined=True,high_rhat=False,low_ess=False,
                failure=None,reference=None,reference_available=False)
            rows.append(row)
    return plan,rows


def comparison(plan,rows,interval):
    """Real full cohort validation and bounded arithmetic; no fake WSS synthesis."""
    from collections import defaultdict
    import tile_weight_reference_comparison as bounded
    summary.summarize_rows(plan,rows)
    grouped=defaultdict(list)
    for row in rows:grouped[tuple(row[k] for k in summary.CONDITION)].append(row)
    return dict(replicates=192,conditions=[dict(zip(summary.CONDITION,key),assessment=bounded.assess_bounds(cohort,192,interval))
        for key,cohort in grouped.items()],reference=None if interval is None else dict(interval=interval),
        reference_available=interval is not None)


@pytest.mark.parametrize('interval,status',[(None,'ineligible_reference_unavailable'),([0,.1],'ineligible_reference_zero_boundary'),
    ([.01,.1],'ineligible_reference_width'),([.099,.101],'selected')])
def test_width_gate_and_all_192_diagnostics_remain(interval,status):
    plan,rows=numerical_inputs()
    result=selector.choose(plan,comparison(plan,rows,interval))
    assert len(result)==2 and all(x['status']==status for x in result)
    assert all(x['speed_ratio'] is None for x in result)
    for item in result:
        assert all(x['assessment']['metrics']['replicates']==192 for x in item['candidates'])
        assert all(x['assessment']['metrics']['undefined']==192 for x in item['candidates'])
        assert all(x['assessment']['metrics']['unavailable_intervals']==192 for x in item['candidates'])
    if status=='selected':
        assert result[0]['selected_condition']['method']=='cross_chain'
        assert result[0]['selected_condition']['kernel']=='ZH'
        assert result[0]['selected_condition']['init']=='logical_basis'


def test_width_equality_is_not_rejected():
    assert selector.width_gate([.2,.3],.2)['impossible'] is False
    assert selector.width_gate([.2,.301],.2)['impossible'] is True


def test_missing_points_and_bad_precision_never_selected():
    plan,rows=numerical_inputs()
    for row in rows:
        if row['replicate']==0:row.update(estimate=None,failure='sampling_failed')
    result=selector.choose(plan,comparison(plan,rows,[.099,.101]))
    assert all(x['status']=='unmet_empirical_precision' for x in result)
    assert all(x['classification_counts']=={'incomplete_points':16} for x in result)
    for row in rows:row.update(estimate=.2,failure=None)
    result=selector.choose(plan,comparison(plan,rows,[.099,.101]))
    assert all(x['status']=='unmet_empirical_precision' for x in result)


def test_ranking_is_fixed_and_order_independent():
    plan,rows=numerical_inputs()
    report=comparison(plan,rows,[.099,.101])
    left=selector.choose(plan,report)
    report['conditions'].reverse()
    assert selector.choose(plan,report)==left
    good=left[0]['selected_condition']
    assert selector.rank(plan,good)<selector.rank(plan,dict(good,method='block',block=2))
    assert selector.rank(plan,dict(good,method='block',block=2))<selector.rank(plan,dict(good,method='block',block=32))
    assert selector.rank(plan,good)<selector.rank(plan,dict(good,samples=80))


def test_select_condition_reuses_validated_full_cohort(monkeypatch):
    plan,rows=numerical_inputs()
    calls=[]
    def compare(actual,values,condition):
        calls.append(condition)
        return comparison(actual,values,[.099,.101])
    monkeypatch.setattr(selector.comparison,'compare_rows',compare)
    assert selector.select_condition(plan,rows,{'partial_estimate':.999})[0]['status']=='selected'
    assert calls==[{'partial_estimate':.999}]
    with pytest.raises(ValueError):selector.select_condition(dict(plan,replicates=191),rows,{})
    rows.pop()
    with pytest.raises(ValueError):selector.select_condition(plan,rows,{})


def pending_manifest():
    return dict(schema=1,purpose='low_noise_timing_selection_input',source_sha256=selector.source_hashes(),
        conditions=[dict(case=case,target_index=target,status='pending',reason='calibration_incomplete')
                    for case in range(4) for target in range(3)])


def save_input(tmp_path,value):
    path=tmp_path/'input.json';path.write_bytes(c.canonical(value))
    return path,c.file_hash(path)


def test_pending_keeps_exact_24_and_does_not_read_raw(tmp_path,monkeypatch):
    value=pending_manifest();path,digest=save_input(tmp_path,value)
    monkeypatch.setattr(selector,'load_complete',lambda *args:pytest.fail('pending must not scan raw'))
    result=selector.run(path,digest,tmp_path/'out.json')
    assert [(r['case'],r['target_index'],r['epsilon_index']) for r in result['rows']]==list(selector.identities())
    assert all(r['status']=='selection_pending' and r['speed_ratio'] is None for r in result['rows'])
    assert not result['production_selection_validated']
    with pytest.raises(ValueError):selector.run(path,digest,tmp_path/'out.json')


@pytest.mark.parametrize('change',['input_hash','source','duplicate','missing','threshold','status'])
def test_manifest_and_policy_changes_rejected(tmp_path,change):
    value=pending_manifest()
    if change=='source':value['source_sha256']={}
    if change=='duplicate':value['conditions'][-1]=deepcopy(value['conditions'][0])
    if change=='missing':value['conditions'].pop()
    if change=='threshold':value['epsilons']=[.3,.1]
    if change=='status':value['conditions'][0]['status']='finished'
    path,digest=save_input(tmp_path,value)
    with pytest.raises(ValueError):selector.run(path,'0'*64 if change=='input_hash' else digest,tmp_path/'out.json')


def test_all_complete_requires_pbs_before_reader(tmp_path,monkeypatch):
    value=pending_manifest()
    for item in value['conditions']:item['status']='complete'
    path,digest=save_input(tmp_path,value)
    monkeypatch.delenv('PBS_JOBID',raising=False)
    monkeypatch.setattr(selector,'load_complete',lambda *args:pytest.fail('no PBS'))
    with pytest.raises(ValueError,match='PBS'):selector.run(path,digest,tmp_path/'out.json')


def test_ledger_terminal_identity_script_and_manifest(tmp_path):
    script=tmp_path/'run.sh';script.write_text('#!/bin/bash\n')
    ledger=dict(job_id='123.host',command=['qsub',str(script)],manifest='plan',script_sha256=c.file_hash(script))
    lp=tmp_path/'submission.json';lp.write_bytes(c.canonical(ledger))
    terminal={'Jobs':{'123.host':dict(job_state='F',Exit_status=0,Submit_arguments=str(script))}}
    from tile_low_noise_audited_collection import Evidence
    selector.check_terminal(Evidence(),terminal,lp,'123.host','plan',(0,))
    for field,bad in [('job_state','R'),('Exit_status',1),('Submit_arguments','wrong.sh')]:
        copy=deepcopy(terminal);copy['Jobs']['123.host'][field]=bad
        with pytest.raises(ValueError):selector.check_terminal(Evidence(),copy,lp,'123.host','plan',(0,))
    with pytest.raises(ValueError):selector.check_terminal(Evidence(),terminal,lp,'123.host','wrong',(0,))


def test_success_and_midread_failure_are_distinct(tmp_path,monkeypatch):
    value=pending_manifest()
    for item in value['conditions']:item['status']='complete'
    path,digest=save_input(tmp_path,value)
    monkeypatch.setenv('PBS_JOBID','123.host')
    for key,val in low.native.THREADS.items():monkeypatch.setenv(key,val)
    def loaded(item,proof):
        return [selector.base_row(item['case'],item['target_index'],eps)|dict(status='unmet_empirical_precision') for eps in range(2)],{'fixture':True}
    monkeypatch.setattr(selector,'load_complete',loaded)
    result=selector.run(path,digest,tmp_path/'out.json')
    assert len(result['rows'])==24 and result['production_selection_validated']
    def changing(item,proof):
        path.write_bytes(path.read_bytes()+b' ')
        return loaded(item,proof)
    monkeypatch.setattr(selector,'load_complete',changing)
    with pytest.raises(ValueError):selector.run(path,digest,tmp_path/'bad.json')
    assert not (tmp_path/'bad.json').exists()


def complete_fixture(tmp_path,monkeypatch,mode='single'):
    """Real metadata/terminal joins, with raw readers and native validation mocked.

    This fixture does not claim to contain 768 scientific group artifacts.
    """
    import tile_low_noise_audited_collection as saved
    import tile_low_noise_partitioned_collection as partitioned
    import tile_weight_reference_audit_run as ar
    import audit_tile_weight_reference as audit
    import tile_low_noise_staging_control as staged
    plan,rows=numerical_inputs()
    compared=comparison(plan,rows,[.099,.101])
    paths={key:tmp_path/key for key in ('root','audit_root','reference_root','reference_audit_root')}
    for path in paths.values():path.mkdir()
    root,trace,ref,ra=[paths[k] for k in paths]
    pins={}
    def write(path,value):
        path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(c.canonical(value));pins[str(path)]=c.file_hash(path)
    context=dict(purpose='weight_reference_production',reference=dict(runtime=plan['runtime'],decoder=plan['decoder'],
        platform_profile_digest=plan['native_input_digests']['platform_profile'],conditions=[dict(case=0,physical_decoder_prior=.01)]),
        input_digests=dict(platform_profile=plan['native_input_digests']['platform_profile']))
    reference=dict(context=context,condition=dict(condition=0),input_sha256={},source_sha256={},pbs_job_id='4.host')
    audit_plan={'fixture':'trace audit'};reference_plan={'fixture':'reference audit','actual_native_profile_digest':c.digest({}),'original_pbs_job_id':'4.host'}
    metadata=[dict(condition=i,status='ok') for i in range(16)]
    record=dict(metadata[0],report=reference)
    c.save_artifact(ra/'conditions'/'0',dict(manifest=c.digest(reference_plan),condition=0),{},record)
    for ext in ('.json','.npz','.done.json'):
        path=ra/'conditions'/('0'+ext);pins[str(path)]=c.file_hash(path)
    intent=dict(manifest=c.digest(reference_plan),reference_context=c.digest(context),conditions=list(range(16)),workers=16,hostname='fixture',pbs_job_id='5.host')
    write(ra/'execution-intent.json',intent)
    write(ra/'native_preflight.json',dict(intent,profile={},original_pbs_job_id='4.host'))
    write(ra/'summary.json',dict(manifest=c.digest(reference_plan),tasks=16,failed=0,all_conditions_audited=True,
        terminal_binding_valid=True,phase_failure=None,phase_failures=[],records=metadata,pbs_job_id='5.host',
        native_preflight_sha256=pins[str(ra/'native_preflight.json')],execution_intent_sha256=pins[str(ra/'execution-intent.json')],
        condition_marker_sha256={'0':pins[str(ra/'conditions/0.done.json')]}))
    write(ra/'manifest.json',reference_plan);write(ref/'manifest.json',context);write(ref/'summary.json',dict(unavailable=0))
    write(root/'manifest.json',plan);write(trace/'manifest.json',audit_plan)
    write(root/'partition_analysis_manifest.json',dict(resources=dict(partitions=[dict(index=0)])))
    write(root/'partition-collection/summary.json',dict(fixture=True))
    write(root/'analysis-partitions/0/summary.json',dict(pbs_job_id='2.host'))
    complete=dict(sample=dict(failed=0),anchors=dict(failed=0))
    sampling_manifest=c.digest(plan)
    if mode=='partitioned':
        complete.update(pbs_jobs=[dict(job_id='1.host',phase='sample',index=0,exit_status=0)],
            collector_pbs_job=dict(job_id='7.host'),collection_manifest='partition-manifest')
        sampling_manifest='partition-manifest'
    else:
        for phase in ('sample','anchors'):write(root/(phase+'-execution-intent.json'),dict(pbs_job_id='1.host'))
    write(root/'analysis_manifest.json',dict(completed_phase_evidence=complete))
    evidence=dict(groups=768,anchors=192,native_platform_verified=True,current_trace_payloads_rehashed=True,
        evidence_sha256={},evidence_resolved_paths={},pbs_job_id='3.host')
    sources={str(Path(selector.comparison.__file__).resolve().parent/name):digest for name,digest in selector.comparison.source_hashes().items()}
    sources[str(Path(selector.__file__).resolve())]=c.file_hash(selector.__file__)
    report=dict(compared,manifest=c.digest(plan),audited_collection=evidence,reference_audit=reference,
        raw_reference_audited=True,current_trace_payloads_rehashed=True,source_sha256=sources,pbs_job_id='6.host')
    final=tmp_path/'final.json';write(final,report)
    terminals={}
    def ledger(path,job,manifest):
        script=path.parent/'run.sh';script.parent.mkdir(parents=True,exist_ok=True);script.write_text('#!/bin/bash\n')
        pins[str(script)]=c.file_hash(script)
        write(path,dict(command=['qsub',str(script)],manifest=manifest,job_id=job,script_sha256=c.file_hash(script)))
        terminals[job]=dict(job_state='F',Exit_status=0,Submit_arguments=str(script))
    ledger(root/('sampling-submissions/sample/0/submission.json' if mode=='partitioned' else 'submission.json'),'1.host',sampling_manifest)
    if mode=='partitioned':ledger(root/'sampling-collection-submission/submission.json','7.host',sampling_manifest)
    ledger(root/'analysis-submissions/0/submission.json','2.host',c.digest(plan))
    ledger(trace/'submission.json','3.host',c.digest(audit_plan))
    ledger(ref/'submission.json','4.host',c.digest(context));ledger(ra/'submission.json','5.host',c.digest(reference_plan))
    final_ledger=tmp_path/'final-job/submission.json';ledger(final_ledger,'6.host',c.digest(plan))
    receipt=tmp_path/'terminal.json';write(receipt,{'Jobs':terminals})
    entry=dict(case=0,target_index=0,status='complete',reader=mode,**{k:str(v) for k,v in paths.items()},
        final_report=str(final),final_submission=str(final_ledger),terminal_receipt=str(receipt),input_sha256=pins)
    entry['staging_control_pins']=[dict(fixture='explicit control pins')]
    monkeypatch.setattr(low,'make_plan',lambda *args,**kwargs:plan)
    monkeypatch.setattr(ar,'read_plan',lambda *args:reference_plan)
    # This reduced fixture has no source tree. Real source relocation and its
    # connection to this reader are covered in the dedicated binding tests.
    monkeypatch.setattr(selector.source_binding,'reference_context',lambda *args:dict(saved_root=ra,current_root=ra,sources={}))
    monkeypatch.setattr(selector.source_binding,'reference_sources',lambda *args:None)
    monkeypatch.setattr(ar,'report_binding',lambda *args:None)
    monkeypatch.setattr(audit,'verify_unchanged',lambda *args:None)
    monkeypatch.setattr(saved,'read_audited_collection',lambda *args:(plan,rows,evidence))
    monkeypatch.setattr(partitioned,'read_audited_collection',lambda *args:(plan,rows,evidence))
    def staged_reader(source,trace_root,control_pins):
        assert control_pins==entry['staging_control_pins']
        return plan,rows,evidence
    monkeypatch.setattr(staged,'collect',staged_reader)
    monkeypatch.setattr(selector.comparison,'compare_rows',lambda *args:compared)
    return entry,write


@pytest.mark.parametrize('mode',['single','partitioned','staged'])
def test_complete_reader_metadata_joins_all_phase_jobs(tmp_path,monkeypatch,mode):
    entry,_=complete_fixture(tmp_path,monkeypatch,mode)
    from tile_low_noise_audited_collection import Evidence
    proof=Evidence();rows,evidence=selector.load_complete(entry,proof);proof.finish()
    assert len(rows)==2 and all(row['status']=='selected' for row in rows)
    assert len(evidence['terminals'])==(7 if mode=='partitioned' else 6)


@pytest.mark.parametrize('change',['native','prior','source','terminal','missing_pin','changed_pin','report','denominator','audit_native','source_closure'])
def test_completed_input_validation_failures_are_not_ineligible(tmp_path,monkeypatch,change):
    entry,write=complete_fixture(tmp_path,monkeypatch)
    root=Path(entry['reference_root']);path=root/'manifest.json'
    if change in ('native','prior'):
        value=json.loads(path.read_bytes())
        if change=='native':value['input_digests']['platform_profile']='wrong'
        else:value['reference']['conditions'][0]['physical_decoder_prior']=.003
        write(path,value)
    elif change in ('source','source_closure'):
        path=Path(entry['final_report']);value=json.loads(path.read_bytes());value['source_sha256'][str(Path(selector.__file__).resolve())]='0'*64;write(path,value)
        if change=='source_closure':
            value['source_sha256']={str(Path(selector.__file__).resolve()):c.file_hash(selector.__file__)};write(path,value)
    elif change=='terminal':
        path=Path(entry['terminal_receipt']);value=json.loads(path.read_bytes());value['Jobs']['3.host']['job_state']='R';write(path,value)
    elif change=='missing_pin':entry['input_sha256'].pop(str(path))
    elif change=='changed_pin':entry['input_sha256'][str(path)]='0'*64
    elif change=='report':
        path=Path(entry['final_report']);value=json.loads(path.read_bytes());value['reference_available']=False;write(path,value)
    elif change=='denominator':
        path=Path(entry['reference_audit_root'])/'summary.json';value=json.loads(path.read_bytes());value['tasks']=15;write(path,value)
    else:
        path=Path(entry['reference_audit_root'])/'native_preflight.json';value=json.loads(path.read_bytes());value['profile']={'wrong':True};write(path,value)
    from tile_low_noise_audited_collection import Evidence
    with pytest.raises(ValueError):selector.load_complete(entry,Evidence())


def test_real_wss_synthesis_is_checked_not_partial_point(monkeypatch):
    import tile_weight_stratified as weight
    plan,rows=numerical_inputs()
    reference=weight.synthesize(72,'bit',.01,[dict(w=0,mode='enum',trials=1,failures=0),dict(w=1,mode='enum',trials=72,failures=1)])
    condition=dict(condition=0,case=0,physical_decoder_prior=.01,chunks=2,failed_chunks=[],planned_trials=73,available_trials=73,available=True,reference=reference)
    result=selector.select_condition(plan,rows,condition)
    assert all(x['status']=='ineligible_reference_width' for x in result)
    condition['reference']['partial_estimate']+=.01
    with pytest.raises(ValueError):selector.select_condition(plan,rows,condition)


def test_pending_does_not_hide_an_invalid_complete_declaration(tmp_path):
    value=pending_manifest();value['conditions'][0]['status']='complete'
    path,digest=save_input(tmp_path,value)
    with pytest.raises(ValueError,match='pinned metadata'):selector.run(path,digest,tmp_path/'result.json')


def test_output_resolved_target_change_is_rejected(tmp_path,monkeypatch):
    value=pending_manifest();path,digest=save_input(tmp_path,value)
    output=tmp_path/'result.json'
    actual=Path.resolve;changed=False
    def resolve(self,*args,**kwargs):
        if self==output and changed:return tmp_path/'input-root'/'result.json'
        return actual(self,*args,**kwargs)
    finish=selector.Evidence.finish
    def finishing(self):
        nonlocal changed
        finish(self);changed=True
    monkeypatch.setattr(Path,'resolve',resolve);monkeypatch.setattr(selector.Evidence,'finish',finishing)
    with pytest.raises(ValueError,match='output target changed'):selector.run(path,digest,output)
    assert not output.exists()


def test_all_twelve_production_setting_censuses_are_preserved():
    for case in range(4):
        for target in range(3):
            plan=low.make_plan(case,target,capacity=False)
            keys=list(summary.expected_conditions(plan))
            assert plan['replicates']==192 and len(keys)==len(set(keys))==352


@pytest.mark.parametrize('change',[None,'path','bytes'])
def test_split_root_closure_and_unapproved_import_change(tmp_path,monkeypatch,change):
    first=tmp_path/'selector'/'cluster_scripts';second=tmp_path/'shared'/'cluster_scripts'
    first.mkdir(parents=True);second.mkdir(parents=True)
    entry=first/'selector_fixture.py';entry.write_text('import timing_fixture_dependency\n')
    dependency=second/'timing_fixture_dependency.py';dependency.write_text('VALUE=1\n')
    monkeypatch.syspath_prepend(str(second));monkeypatch.syspath_prepend(str(first))
    monkeypatch.setattr(selector,'__file__',str(entry))
    before=selector.source_hashes()
    assert before=={str(entry):c.file_hash(entry),str(dependency):c.file_hash(dependency)}
    value=pending_manifest();path,digest=save_input(tmp_path,value)
    if change=='path':
        other=tmp_path/'unapproved'/'cluster_scripts';other.mkdir(parents=True)
        (other/dependency.name).write_bytes(dependency.read_bytes())
        monkeypatch.syspath_prepend(str(other))
    elif change=='bytes':dependency.write_text('VALUE=2\n')
    if change is None:
        assert len(selector.run(path,digest,tmp_path/'result.json')['rows'])==24
    else:
        with pytest.raises(ValueError,match='source closure'):selector.run(path,digest,tmp_path/'result.json')
