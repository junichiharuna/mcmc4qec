"""Small parent-envelope acceptance; scientific raw readers remain mocked."""
from copy import deepcopy
import json
import os
from pathlib import Path
import shlex
import subprocess
import sys
from types import SimpleNamespace

import pytest

for dependency in ('ldpc', 'bposd', 'pymatching'):
    pytest.importorskip(dependency)
sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'cluster_scripts'))
import calibration as c
import tile_low_noise_timing_evaluation_report as report
import tile_low_noise_timing_selection as selector
import submit_tile_low_noise_timing_selection as w
from test_tile_low_noise_timing_execution_gate import job_fixture
from test_tile_low_noise_timing_selection import numerical_inputs, comparison


def put(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(value if isinstance(value, bytes) else c.canonical(value)+b'\n')
    return dict(path=str(path.absolute()), sha256=c.file_hash(path))


def fixture(tmp_path, monkeypatch):
    bundle=tmp_path/'bundle'; root=bundle/'runs'/'selector'; upstream=tmp_path/'upstream'
    # Reduced source closure keeps each boundary test light; production resolves
    # the complete accepted closure through the unchanged real source_files API.
    modules={Path(module.__file__).stem:Path(module.__file__) for module in (report,selector,c)}
    core=tmp_path/'fixture_core'/'__init__.py';put(core,b'# mock core origin; scientific functions already imported\n')
    monkeypatch.setattr(c.qec,'__file__',str(core))
    modules['package/__init__.py']=core
    real_find=w.importlib.util.find_spec
    monkeypatch.setattr(w.importlib.util,'find_spec',lambda name,*a,**k:SimpleNamespace(origin=str(core)) if name=='mcmc4qec' else real_find(name,*a,**k))
    monkeypatch.setattr(report,'source_files',lambda:modules)
    monkeypatch.setattr(w,'local_imports',lambda paths:set())
    monkeypatch.setattr(selector,'source_hashes',lambda:{str(Path(selector.__file__).resolve()):c.file_hash(selector.__file__)})
    sources={str(p.absolute()):c.file_hash(p) for p in report.source_files().values()}
    sources[str(Path(w.__file__).absolute())]=c.file_hash(w.__file__)
    origins={k:str(p.absolute()) for k,p in report.source_files().items() if '/' not in k}
    origins[Path(w.__file__).stem]=str(Path(w.__file__).absolute());origins['mcmc4qec']=str(core)
    entries=[]; accepted=[]; costs=[]
    for case in range(4):
        for target in range(3):
            base=upstream/f'{case}-{target}'
            job=f'{case}{target}.host';script=put(base/'final.sh',b'#!/bin/bash\n')
            ledger=put(base/'submission.json',dict(job_id=job,command=['qsub',script['path']],script_sha256=script['sha256']))
            collection=put(base/'root/partition-collection/summary.json',dict(fixture=True))
            final=put(base/'final.json',dict(case=case,target_index=target,replicates=192,
                pbs_job_id=job,
                raw_reference_audited=True,current_trace_payloads_rehashed=True,
                audited_collection=dict(groups=768,anchors=192,native_platform_verified=True,
                    current_trace_payloads_rehashed=True)))
            terminal=put(base/'terminal.json',dict(Jobs={job:dict(job_state='F',Exit_status=0,
                Submit_arguments=shlex.quote(script['path']),resources_used=dict(walltime='00:00:02',mem='30mb'))}))
            entry=dict(case=case,target_index=target,status='complete',reader='single',root=str(base/'root'),
                audit_root=str(base/'audit'),reference_root=str(upstream/'reference'),
                reference_audit_root=str(upstream/'reference-audit'),final_report=final['path'],
                final_submission=str(base/'submission.json'),terminal_receipt=terminal['path'],
                input_sha256={value['path']:value['sha256'] for value in (final,terminal,ledger,script,collection)})
            entries.append(entry)
            accepted.append(dict(case=case,target_index=target,entry_sha256=c.digest(entry),
                final_report=final,terminal=terminal))
            costs.append(dict(case=case,target_index=target,reader='single',final=dict(terminal=terminal,job_id=job),
                collection=dict(terminal=terminal,job_id=job,summary=collection,included_in_final=True),
                staged_copy=None,hash_budget_seconds=0))
    inp=put(upstream/'selector-input.json',dict(schema=1,purpose='low_noise_timing_selection_input',
        source_sha256=selector.source_hashes(),conditions=entries))
    reference=put(upstream/'reference-audit'/'summary.json',dict(tasks=16,failed=0,all_conditions_audited=True,
        terminal_binding_valid=True,phase_failure=None,phase_failures=[],records=[dict(condition=i,status='ok') for i in range(16)]))
    acceptance=put(upstream/'accepted.json',dict(status='accepted_all_twelve',input_sha256=inp['sha256'],
        conditions=accepted,reference_audit=reference))
    resource=dict(cpus=1,workers=1,memory_gb=32,wall_seconds=1800,walltime='00:30:00',requested_nodes=1,max_nodes=2)
    decision=put(upstream/'resource.json',dict(status='confirmed',resource=resource,conditions=costs,
        wall_basis_seconds=100,memory_basis_gb=8,wall_factor=2,memory_factor=2,overhead_seconds=60,
        scope_difference='Tiny mocked cost evidence only; not production measurements.',
        decision='Fixture decision; no actual resource approval.'))
    native=put(upstream/'native.json',dict(fixture=True))
    config=dict(schema=1,purpose='low_noise_timing_selector_parent_input',input=inp,acceptance=acceptance,
        resource_decision=decision,bundle=str(bundle),python_path=str(Path(sys.executable).absolute()),
        python_sha256=c.file_hash(sys.executable),pythonpath=os.environ.get('PYTHONPATH',''),
        runtime=report.runtime(),source_sha256=sources,import_origins=origins,
        core_origin=str(core),
        resolved_sources={p:str(Path(p).resolve()) for p in sources},native_binding={native['path']:native['sha256']})
    cp=put(upstream/'config.json',config)
    return root,cp,config


def prepared(tmp_path,monkeypatch):
    root,cp,config=fixture(tmp_path,monkeypatch)
    result=w.prepare(root,cp['path'],cp['sha256'])
    return root,result['control_sha256'],config


def submit(root,sha,runner):
    return w.submit(root,sha,execute=True,controller_query=lambda:[],active_query=lambda:{},runner=runner)


def run_small(root,sha,monkeypatch):
    plan=w.read_plan(root,sha)['prepared']
    ledger=json.loads((root/'submission.json').read_bytes())
    monkeypatch.setenv('PBS_JOBID',ledger['job_id'])
    for key,val in w.THREADS.items():monkeypatch.setenv(key,val)
    monkeypatch.setenv('PYTHONHASHSEED','0');monkeypatch.setenv('PYTHONDONTWRITEBYTECODE','1')
    def query(job):
        actual=job_fixture(ledger['command'][1],plan['resource']);actual['job_state']='R'
        return {'Jobs':{job:actual}}
    w.begin(root,sha,c.digest(plan),job_query=query,hostname='node')
    actual_plan,rows=numerical_inputs()
    bounded=comparison(actual_plan,rows,[.099,.101])
    def loaded(entry,proof):
        copied=deepcopy(actual_plan);copied.update(case=entry['case'],target_index=entry['target_index'])
        # Real selector ranking and all 192 per-setting denominators, reduced settings.
        compared=deepcopy(bounded)
        for item in compared['conditions']:item['case']=entry['case']
        selected=selector.choose(copied,compared)
        return selected,dict(fixture=True)
    monkeypatch.setattr(selector,'load_complete',loaded)
    selector.run(plan['input']['path'],plan['input']['sha256'],plan['report_path'])
    w.finish(root,sha,c.digest(plan),job_query=query,hostname='node')
    return ledger


def test_actual_small_selector_and_stage4_exact_descriptor(tmp_path,monkeypatch):
    root,sha,_=prepared(tmp_path,monkeypatch)
    calls=[]
    submit(root,sha,lambda argv,**kw:(calls.append(argv) or SimpleNamespace(stdout='123.cluster\n',stderr='')))
    ledger=run_small(root,sha,monkeypatch)
    result=w.seal(root,sha,job_query=lambda job:{'Jobs':{job:job_fixture(ledger['command'][1],ledger['resource'])}})
    proof=report.Evidence()
    accepted=report.selector_evidence(result['descriptor'],result['selection'],proof);proof.finish()
    saved=json.loads(Path(result['selection']['path']).read_bytes())
    assert len(calls)==1 and accepted['job_id']=='123.cluster'
    assert len(saved['rows'])==24 and saved['production_selection_validated']
    assert all(row['speed_ratio'] is None for row in saved['rows'])
    assert all(candidate['assessment']['metrics']['replicates']==192 for row in saved['rows'] for candidate in row['candidates'])
    assert len(saved['calibration_bindings'])==12


@pytest.mark.parametrize('change',['pending','missing','duplicate','unaccepted','reference_audit','resource','cost_missing','native','source','python'])
def test_prepare_rejects_unready_without_output(tmp_path,monkeypatch,change):
    root,cp,config=fixture(tmp_path,monkeypatch)
    if change in ('pending','missing','duplicate'):
        inp=json.loads(Path(config['input']['path']).read_bytes())
        if change=='pending':inp['conditions'][0]['status']='pending'
        if change=='missing':inp['conditions'].pop()
        if change=='duplicate':inp['conditions'][-1]=deepcopy(inp['conditions'][0])
        config['input']=put(Path(config['input']['path']),inp)
    elif change=='unaccepted':config['acceptance']=put(Path(config['acceptance']['path']),dict(status='pending'))
    elif change=='reference_audit':
        record=json.loads(Path(config['acceptance']['path']).read_bytes())
        value=json.loads(Path(record['reference_audit']['path']).read_bytes());value['failed']=1
        record['reference_audit']=put(Path(record['reference_audit']['path']),value)
        config['acceptance']=put(Path(config['acceptance']['path']),record)
    elif change in ('resource','cost_missing'):
        decision=json.loads(Path(config['resource_decision']['path']).read_bytes())
        if change=='resource':decision['status']='unconfirmed'
        else:decision['conditions'].pop()
        config['resource_decision']=put(Path(config['resource_decision']['path']),decision)
    elif change=='native':config['native_binding'][next(iter(config['native_binding']))]='0'*64
    elif change=='source':config['source_sha256'][str(Path(w.__file__).absolute())]='0'*64
    else:config['python_sha256']='0'*64
    cp=put(Path(cp['path']),config)
    with pytest.raises((ValueError,KeyError)):w.prepare(root,cp['path'],cp['sha256'])
    assert not root.exists()


def test_exact_cli_once_and_metadata_only_prepare(tmp_path,monkeypatch):
    monkeypatch.setattr(selector,'load_complete',lambda *a:pytest.fail('prepare must not scan raw'))
    root,sha,_=prepared(tmp_path,monkeypatch)
    plan=w.read_plan(root,sha)['prepared']
    assert (root/'selector.sh').read_text().splitlines().count(shlex.join(plan['selector_argv']))==1
    with pytest.raises((ValueError,FileExistsError)):w.prepare(root,'absent','0'*64)


@pytest.mark.parametrize('change',['intent_bytes','intent_symlink','lock_symlink','script','source','foreign_lock'])
def test_post_intent_mutation_never_calls_qsub(tmp_path,monkeypatch,change):
    root,sha,config=prepared(tmp_path,monkeypatch);calls=[]
    original=w.save_new
    def saving(path,value):
        original(path,value)
        if Path(path).name!='submission-intent.json':return
        target=Path(path)
        if change in ('intent_symlink','lock_symlink'):
            if change=='lock_symlink':target=Path(config['bundle']).parent/'tile-low-noise-submission.lock'
            other=target.with_suffix('.target');other.write_bytes(target.read_bytes());target.unlink();target.symlink_to(other)
        elif change=='intent_bytes':target.write_bytes(b'{}')
        elif change=='script':(root/'selector.sh').write_text('changed')
        elif change=='source':
            cfg=Path(config['acceptance']['path']);cfg.write_bytes(cfg.read_bytes()+b' ')
        else:
            lock=Path(config['bundle']).parent/'tile-low-noise-submission.lock';lock.write_bytes(b'foreign')
    monkeypatch.setattr(w,'save_new',saving)
    with pytest.raises(ValueError):submit(root,sha,lambda *a,**k:calls.append(a))
    assert not calls
    if change in ('lock_symlink','foreign_lock'):
        assert (Path(config['bundle']).parent/'tile-low-noise-submission.lock').exists()


@pytest.mark.parametrize('kind',['ambiguous','timeout','two_nodes','controller'])
def test_submission_limits_and_uncertain_response(tmp_path,monkeypatch,kind):
    root,sha,config=prepared(tmp_path,monkeypatch);calls=[]
    def runner(*a,**k):
        calls.append(a)
        if kind=='timeout':raise TimeoutError('unknown qsub result')
        return SimpleNamespace(stdout='not-a-job',stderr='')
    active=lambda:{}
    if kind=='two_nodes':monkeypatch.setattr(w,'node_count',lambda jobs:2)
    with pytest.raises((ValueError,TimeoutError)):
        w.submit(root,sha,execute=True,controller_query=lambda:['busy'] if kind=='controller' else [],active_query=active,runner=runner)
    assert len(calls)==(1 if kind in ('ambiguous','timeout') else 0)
    if calls:assert (Path(config['bundle']).parent/'tile-low-noise-submission.lock').exists()


def test_bootstrap_hash_failure_precedes_scientific_import(tmp_path,monkeypatch):
    root,cp,config=fixture(tmp_path,monkeypatch)
    config['python_sha256']='0'*64;cp=put(Path(cp['path']),config)
    monkeypatch.setattr(w,'science',lambda *a:pytest.fail('import must follow byte gate'))
    with pytest.raises(ValueError):w.prepare(root,cp['path'],cp['sha256'])


