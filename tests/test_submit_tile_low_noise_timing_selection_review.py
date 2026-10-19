"""Focused independent-review regressions and post-compute evidence mutations."""
import base64
import json
from pathlib import Path
import subprocess
from types import SimpleNamespace

import pytest

from test_submit_tile_low_noise_timing_selection import (
    w, c, fixture, prepared, put, submit, run_small, job_fixture, report)


@pytest.mark.parametrize('field',['input','report','execution','native','source'])
def test_compute_or_seal_rejects_changes(tmp_path,monkeypatch,field):
    root,sha,config=prepared(tmp_path,monkeypatch)
    submit(root,sha,lambda *a,**k:SimpleNamespace(stdout='123.cluster',stderr=''))
    ledger=run_small(root,sha,monkeypatch)
    paths=dict(input=config['input']['path'],report=str(root/'selection.json'),execution=str(root/'execution.json'),
        native=next(iter(config['native_binding'])),source=config['acceptance']['path'])
    path=Path(paths[field]);path.write_bytes(path.read_bytes()+b' ')
    with pytest.raises(ValueError):w.seal(root,sha,job_query=lambda job:{'Jobs':{job:job_fixture(ledger['command'][1],ledger['resource'])}})
    assert not (root/'descriptor.json').exists()


@pytest.mark.parametrize('kind',['omitted','dotted','core','closure'])
def test_complete_import_census_before_science(tmp_path,monkeypatch,kind):
    root,cp,config=fixture(tmp_path,monkeypatch)
    if kind=='omitted':config['import_origins'].pop('tile_low_noise_timing_evaluation_report')
    elif kind=='dotted':config['import_origins']['bad.parent.module']='unused'
    elif kind=='core':config['core_origin']=str(tmp_path/'unapproved/__init__.py')
    else:monkeypatch.setattr(w,'local_imports',lambda paths:{'omitted_scientific_module'})
    cp=put(Path(cp['path']),config)
    monkeypatch.setattr(w,'science',lambda *a:pytest.fail('scientific import preceded the closure gate'))
    with pytest.raises(ValueError):w.prepare(root,cp['path'],cp['sha256'])
    assert not root.exists()


def test_local_ast_dependency_discovery_has_no_import_side_effect(tmp_path):
    root=tmp_path/'cluster_scripts';root.mkdir()
    (root/'entry.py').write_text('import shadow_test_dependency\nfrom .relative import ignored\n')
    (root/'shadow_test_dependency.py').write_text('raise RuntimeError("must never import")\n')
    assert w.local_imports([root/'entry.py'])=={'shadow_test_dependency'}


@pytest.mark.parametrize('kind',['arbitrary','wrong_job','included_twice','underbudget','missing_clock','staged_missing'])
def test_cost_metadata_cannot_be_arbitrary_or_unbound(tmp_path,monkeypatch,kind):
    root,cp,config=fixture(tmp_path,monkeypatch)
    decision=json.loads(Path(config['resource_decision']['path']).read_bytes());row=decision['conditions'][0]
    if kind=='arbitrary':row['final']=put(tmp_path/'arbitrary.json',{})
    elif kind=='wrong_job':row['final']['job_id']='999.unrelated'
    elif kind=='included_twice':row['collection']['included_in_final']=False
    elif kind=='underbudget':decision['wall_basis_seconds']=1
    elif kind=='missing_clock':
        data=json.loads(Path(row['final']['terminal']['path']).read_bytes())
        data['Jobs'][row['final']['job_id']]['resources_used'].pop('mem')
        # Exercise the pure cost gate without promoting changed evidence to acceptance.
        value=put(Path(row['final']['terminal']['path']),data)
        with pytest.raises((ValueError,KeyError)):w.pbs_cost(value,row['final']['job_id'],w.Evidence())
        return
    else:row['reader']='staged'
    config['resource_decision']=put(Path(config['resource_decision']['path']),decision)
    cp=put(Path(cp['path']),config)
    with pytest.raises((ValueError,KeyError)):w.prepare(root,cp['path'],cp['sha256'])
    assert not root.exists()


@pytest.mark.parametrize('kind',['timeout','exit'])
def test_partial_qsub_response_retained_without_retry(tmp_path,monkeypatch,kind):
    root,sha,config=prepared(tmp_path,monkeypatch);calls=[]
    def runner(argv,**kwargs):
        calls.append(argv)
        if kind=='timeout':raise subprocess.TimeoutExpired(argv,30,output=b'123.cluster\n',stderr=b'partial\xff')
        raise subprocess.CalledProcessError(1,argv,output='123.cluster\n',stderr='uncertain')
    with pytest.raises(subprocess.SubprocessError):submit(root,sha,runner)
    result=json.loads((root/'qsub-error.json').read_bytes())
    if kind=='timeout':
        assert base64.b64decode(result['stdout']['data'])==b'123.cluster\n'
        assert base64.b64decode(result['stderr']['data'])==b'partial\xff'
    else:
        assert result['stdout']==dict(encoding='text',data='123.cluster\n')
        assert result['stderr']['data']=='uncertain' and result['returncode']==1
    assert len(calls)==1 and (Path(config['bundle']).parent/'tile-low-noise-submission.lock').exists()
    with pytest.raises(ValueError):submit(root,sha,runner)
    assert len(calls)==1


def test_staged_copy_cost_and_separate_collection_job_are_bound(tmp_path,monkeypatch):
    _,_,config=fixture(tmp_path,monkeypatch)
    entries=json.loads(Path(config['input']['path']).read_bytes())['conditions'];entry=entries[0]
    decision=json.loads(Path(config['resource_decision']['path']).read_bytes());row=decision['conditions'][0]
    entry['reader']=row['reader']='staged';base=Path(entry['root'])
    report_value=json.loads(Path(entry['final_report']).read_bytes())
    report_value['audited_collection']['staging_origin']=dict(copy_pbs_job_id='900.copy')
    value=put(Path(entry['final_report']),report_value);entry['input_sha256'][value['path']]=value['sha256']
    collection=put(base/'partition-collection/summary.json',dict(pbs_job_id='901.collect'))
    entry['input_sha256'][collection['path']]=collection['sha256']
    terminal=json.loads(Path(entry['terminal_receipt']).read_bytes())
    terminal['Jobs']['901.collect']=dict(job_state='F',Exit_status=0,resources_used=dict(walltime='00:00:03',mem='40mb'))
    actual=put(Path(entry['terminal_receipt']),terminal);entry['input_sha256'][actual['path']]=actual['sha256']
    row['final']['terminal']=actual
    row['collection']=dict(summary=collection,terminal=actual,job_id='901.collect',included_in_final=False)
    copy=put(base/'.staging/summary.json',dict(destination=str(base),copy_pbs_job_id='900.copy',elapsed_seconds=2,
        source_unchanged=True,copy_hashes_verified=True,scientific_recalculation=False))
    copy_terminal=put(tmp_path/'copy-terminal.json',dict(Jobs={'900.copy':dict(job_state='F',Exit_status=0,
        resources_used=dict(walltime='00:00:03',mem='30mb'))}))
    row['staged_copy']=dict(summary=copy,terminal=copy_terminal,job_id='900.copy',extra_hash_passes=2,copy_time_factor=1)
    row['hash_budget_seconds']=4
    assert w.confirmed_resource(decision,entries,w.Evidence())==decision['resource']
    row['hash_budget_seconds']=3
    with pytest.raises(ValueError,match='hash cost'):w.confirmed_resource(decision,entries,w.Evidence())
