"""Small saved-summary fixtures; no full JSONL or scientific recomputation."""
import copy
import importlib.util
import json
from pathlib import Path
import sys

import pytest

pytest.importorskip('ldpc')
pytest.importorskip('bposd')
pytest.importorskip('pymatching')
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'cluster_scripts'))
import tile_mixing_comparison_report as report
import tile_mixing_inventory as inventory


def collector():
    path = ROOT / 'docs/wp/data_tile_validation_2026-10-17/collect_mixing_full_v1.py'
    spec = importlib.util.spec_from_file_location('test_mixing_collector', path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def plan():
    return dict(purpose='calibration', replicates=192, kernels={'ZH': {}, 'ZHS': {}},
                initializations=['rejection', 'logical'], burns=[0], runtime={},
                cases=[dict(size=6, noise='bit', target=.03, rungs=[.1, .03], coarse=[.1, .03],
                            chains=4, windows=[2], steps=2) for _ in range(4)])


def saved(case=0):
    p = plan()
    keys = report.expected_keys(p, case)
    records = []
    for key in keys:
        row = dict(zip(inventory.KEY, key), replicates=192, replicate_ids=list(range(192)),
                   status_counts={'stored': 192}, undefined=0, nonfinite=0, stored_missing_fields=0,
                   stored_flag_counts={} if key[0] == 'sector' else dict(undefined=0, high_rhat=0, low_ess=0, flagged=0))
        fields = ('sector_transitions', 'unique_sectors') if key[0] == 'sector' else inventory.SCALARS + inventory.VECTORS
        row['metrics'] = {}
        for field in fields:
            n = 192 * (row['chains'] if field in inventory.VECTORS or key[0] == 'sector' else 1)
            row['metrics'][field] = dict(expected_values=n, finite_values=n, null_values=0,
                nonfinite_values=0, sum=float(n), min=1., max=1., mean=1., available_only_mean=1.)
        records.append(row)
    result = dict(schema=1, purpose='saved_mixing_inventory', case=case, groups=768, replicates=192,
                  rows=len(keys)*192, conditions=len(keys), records=records, inventory_complete=True,
                  failed_sampling=0, **{key: False for key in collector().FALSE_FLAGS})
    return p, result


def test_complete_summary_values_and_denominators():
    p, original = saved()
    rows = report.normalize(original, p, 0, collector())
    assert len(rows) == len(original['records'])
    assert all(row['replicates'] == 192 and row['replicate_ids'] == list(range(192)) for row in rows)
    assert rows[0]['metrics'] == original['records'][0]['metrics']
    assert rows[0]['status_counts']['missing_unexpected'] == 0
    assert any(row['kind'] == 'sector' and row['metrics']['unique_sectors']['expected_values'] == 768 for row in rows)
    assert all(row['p'] == p['cases'][0]['rungs'][row['rung']] for row in rows)
    assert sum(row['kind']=='sector' for row in rows) == 8
    assert len({tuple(row[k] for k in inventory.KEY) for row in rows}) == len(rows)


@pytest.mark.parametrize('mutation', ['missing', 'duplicate', 'replicate', 'status', 'metric', 'flag'])
def test_structural_rejection(mutation):
    p, original = saved()
    if mutation == 'missing': original['records'].pop()
    if mutation == 'duplicate': original['records'][-1] = copy.deepcopy(original['records'][0])
    if mutation == 'replicate': original['records'][0]['replicate_ids'][-1] = 0
    if mutation == 'status': original['records'][0]['status_counts']['stored'] = 191
    if mutation == 'metric': original['records'][0]['metrics']['mean']['expected_values'] = 191
    if mutation == 'flag': original['records'][0]['stored_flag_counts']['flagged'] = 193
    with pytest.raises(ValueError): report.normalize(original, p, 0, collector())


def test_missing_nonfinite_and_distinct_flags_retained():
    p, original = saved()
    first = original['records'][0]
    first['status_counts'] = dict(stored=190, missing_recorded_sampling_failure=1, missing_unexpected=1)
    first.update(undefined=5, nonfinite=1, stored_missing_fields=1)
    first['stored_flag_counts'] = dict(undefined=1, high_rhat=2, low_ess=3, flagged=4)
    metric = first['metrics']['rhat']
    metric.update(finite_values=189, null_values=2, nonfinite_values=1, mean=None, available_only_mean=1., sum=189.)
    original['inventory_complete'] = False
    rows = report.normalize(original, p, 0, collector())
    row = next(r for r in rows if all(r[k]==first[k] for k in inventory.KEY))
    assert row['undefined'] == 5 and row['stored_flag_counts']['undefined'] == 1
    assert row['status_counts']['stored'] == 190
    assert row['metrics']['rhat']['mean'] is None
    assert row['metrics']['rhat']['available_only_mean'] == 1.
    assert row['stored_flags_absent'] == 2


def test_overflow_sum_and_null_mean_preserved():
    p, original = saved()
    original['records'][0]['metrics']['mean'].update(sum=None, mean=None, available_only_mean=None)
    first = original['records'][0]
    row = next(r for r in report.normalize(original,p,0,collector()) if all(r[k]==first[k] for k in inventory.KEY))
    assert row['metrics']['mean']['sum'] is None


def test_evidence_uses_one_snapshot_and_rejects_changes(tmp_path):
    path = tmp_path/'value.json'; path.write_text('{"x":1}')
    evidence = report.Evidence()
    assert evidence.json(path, report.sha(path.read_bytes()))['x'] == 1
    path.write_text('{"x":2}')
    with pytest.raises(ValueError): evidence.finish()


def test_evidence_retarget(tmp_path):
    target = tmp_path/'target'; target.write_text('{}')
    path = tmp_path/'link'
    try: path.symlink_to(target)
    except OSError: pytest.skip('symlink unavailable')
    evidence = report.Evidence(); evidence.json(path)
    second = tmp_path/'other'; second.write_text('{}')
    path.unlink(); path.symlink_to(second)
    with pytest.raises(ValueError): evidence.finish()


def orchestration(tmp_path, monkeypatch):
    config = tmp_path/'config.json'; config.write_text('{}')
    proofs = []
    rows = []
    for case in range(4):
        p, original = saved(case)
        rows.extend(report.normalize(original, p, case, collector()))
        proofs.append(dict(case=case, job_id=f'{case}.PBS', collection_root=str(tmp_path/f'collection-{case}'), inventory_complete=True,
            failed_sampling=0, groups=768, replicates=192, rows=original['rows'],
            census=dict(status_counts={'stored':original['rows']},undefined=0),
            rows_reference=dict(sha256='a'*64, bytes=1, path='unopened.jsonl')))
    def load(path, digest, evidence):
        evidence.json(path,digest)
        return rows, proofs
    monkeypatch.setattr(report, 'load_inputs', load)
    return config, rows


def test_outputs_no_seed_reconstruction_or_large_reads(tmp_path, monkeypatch):
    config, rows = orchestration(tmp_path, monkeypatch)
    original_open = Path.open
    def guarded(path, *args, **kwargs):
        assert path.suffix not in ('.jsonl', '.npz')
        return original_open(path, *args, **kwargs)
    monkeypatch.setattr(Path, 'open', guarded)
    output = tmp_path/'new'
    result = report.run(config, report.sha(config.read_bytes()), output)
    assert result['scientific_diagnostics_recomputed'] is False
    assert result['jsonl_reread'] is False
    assert result['seed_level_union_evaluated'] is False
    assert len(json.loads((output/'cohorts.json').read_text())) == len(rows)
    text = (output/'report_ja.md').read_text(encoding='utf-8')
    assert '96/96' in text and '192' in text and '未評価' in text
    with pytest.raises(ValueError): report.run(config, report.sha(config.read_bytes()), output)


def test_terminal_input_change_prevents_publication(tmp_path, monkeypatch):
    config, _ = orchestration(tmp_path, monkeypatch)
    original = report.render
    def changed(*args):
        value = original(*args); config.write_text('{"changed":true}'); return value
    monkeypatch.setattr(report, 'render', changed)
    output = tmp_path/'new'
    with pytest.raises(ValueError): report.run(config, report.sha(config.read_bytes()), output)
    assert not (output/'provenance.json').exists()
    assert not (output/'report_ja.md').exists()


def metadata_fixture(tmp_path):
    """Synthetic accepted metadata with the real collector validation functions."""
    def write(path, value):
        path.parent.mkdir(parents=True,exist_ok=True)
        raw=json.dumps(value,sort_keys=True).encode() if not isinstance(value,bytes) else value
        path.write_bytes(raw)
        return {'path':str(path),'sha256':report.sha(raw)}
    p=plan(); production=write(tmp_path/'input/production.json',p)
    context=dict(sampling_manifest=inventory.c.digest(p),runtime=p['runtime'],analysis_source_sha256='e'*64)
    context_pin=write(tmp_path/'input/analysis_context.json',context)
    prepared=[]; configs=[]; verifications=[]
    names={'inventory':'tile_mixing_inventory.py','audited_results':'tile_audited_results.py',
           'calibration':'calibration.py','archive':'artifact_archive.py'}
    binding={'source_sha256':{name:'a'*64 for name in names.values()} | {'tile_bar_analysis.py':'e'*64}}
    for case in range(4):
        root=tmp_path/f'input/case-{case}'; remote=f'/accepted/full-{case}'; job=f'{case+1}.PBS'
        resource=dict(cpus=1,memory_gb=4,walltime='00:30:00')
        state=dict(production_root='/production',audited_results='/audited.json',analysis_verification='/archive.json',
                   input_files={'/production/manifest.json':['/production/manifest.json',production['sha256']],
                                '/production/analysis_manifest.json':['/production/analysis_manifest.json',context_pin['sha256']],
                                '/audited.json':['/audited.json','b'*64],'/archive.json':['/archive.json','c'*64]})
        manifest=dict(mode='full',case=case,replicates=192,planned_groups=768,snapshot=state)
        manifest_id=inventory.c.digest(manifest)
        upstream=write(root/'full/upstream-completion-at-submit.json',{'complete':True})
        dry=dict(job_id='dry-run',bundle_binding=binding,command=['qsub',remote+'/inventory.sh'])
        parent={k:v for k,v in dry.items() if k!='job_id'} | dict(job_id=job,upstream_completion_sha256=upstream['sha256'])
        intent=dict(pbs_job_id=job,manifest=manifest_id,hostname='host',submission_binding={'accepted':True})
        _, summary=saved(case)
        summary.update(input_sha256={'/production/manifest.json':production['sha256'],
                                    '/production/analysis_manifest.json':context_pin['sha256']},sampling_manifest=inventory.c.digest(p),
                       analysis_context=inventory.c.digest(context),
                       audited_results_sha256='b'*64,analysis_verification_sha256='c'*64,
                       source_sha256={k:'a'*64 for k in names},rows_sha256='d'*64)
        summary_pin=write(root/'full/inventory/summary.json',summary)
        intent_pin=write(root/'full/execution-intent.json',intent)
        execution=dict(intent,complete=True,terminal_binding_valid=True,mode='full',case=case,
            execution_intent_sha256=intent_pin['sha256'],inventory_summary_sha256=summary_pin['sha256'],
            rows_sha256='d'*64,rows=summary['rows'],replicates=192,groups=768,inventory_complete=True,
            wall_seconds=1.,cpu_seconds=.5,peak_rss_mb=10.)
        values={'manifest.json':manifest,'dry_run.json':dry,'submission-intent.json':{k:v for k,v in parent.items() if k!='job_id'},
                'submission.json':parent,'summary.json':execution,'inventory.sh':b'# script', 'inventory.out':b'', 'inventory.err':b''}
        for name,value in values.items():write(root/'full'/name,value)
        files={}
        for name in collector().FILES:
            path=root/'full'/name
            files[name]=dict(resolved_path=remote+'/'+name,sha256='d'*64,bytes=999) if name.endswith('.jsonl') else \
                dict(resolved_path=remote+'/'+name,sha256=report.sha(path.read_bytes()),bytes=path.stat().st_size)
        parent_pin=write(root/'accepted_parent_receipt.json',parent)
        stable=dict(job_state='F',Exit_status=0,run_count=1,Submit_arguments=remote+'/inventory.sh',exec_host='host/0',
                    Resource_List=dict(select='1:ncpus=1:mem=4gb',nodect=1,ncpus=1,mem='4gb',walltime='00:30:00'))
        verification=dict(case=case,job_id=job,root=remote,local_all_files_hash_verified=True,qsub_executed=False,
            scientific_diagnostics_recomputed=False,files=files,parent_receipt_sha256=parent_pin['sha256'],
            bundle_binding=binding,pbs=stable,pbs_stable=stable,
            census=collector().validate_report(summary,case,report.expected_keys(p,case),summary['rows']),native_provenance='synthetic saved provenance')
        prepared.append(dict(case=case,full_root=remote,full_manifest=manifest_id,resource=resource,
            full_files_sha256={name:files[name]['sha256'] for name in ('manifest.json','inventory.sh','dry_run.json')}))
        verifications.append((root,verification))
    prep=write(tmp_path/'input/preparation.json',{'cases':prepared})
    original=Path(collector().__file__).read_text(encoding='utf-8')
    new=original.replace(collector().PREPARATION_SHA,prep['sha256'])
    collector_pin=write(tmp_path/'input/collector.py',new.encode())
    for case,(root,verification) in enumerate(verifications):
        verification.update(collector_sha256=collector_pin['sha256'],preparation_sha256=prep['sha256'])
        configs.append(dict(case=case,root=str(root),verification=write(root/'verification.json',verification)))
    config=write(tmp_path/'input/config.json',dict(schema=1,collector=collector_pin,preparation=prep,
                                                production_plan=production,analysis_context=context_pin,cases=configs))
    return config


def test_real_metadata_reader_without_jsonl(tmp_path,monkeypatch):
    config=metadata_fixture(tmp_path)
    original=Path.open
    def guarded(path,*args,**kwargs):
        assert path.suffix not in ('.jsonl','.npz')
        return original(path,*args,**kwargs)
    monkeypatch.setattr(Path,'open',guarded)
    result=report.run(config['path'],config['sha256'],tmp_path/'output')
    assert len(result['cases'])==4
    assert result['cohorts']==4*len(report.expected_keys(plan(),0))
    assert result['cases'][0]['rows_reference']['bytes']==999


@pytest.mark.parametrize('change',['summary_bytes','verification_pin','case_order','capacity','terminal','rows_receipt'])
def test_metadata_binding_rejections(tmp_path,change):
    config=metadata_fixture(tmp_path)
    cfg=json.loads(Path(config['path']).read_bytes())
    root=Path(cfg['cases'][0]['root'])
    if change=='summary_bytes':
        path=root/'full/inventory/summary.json';path.write_bytes(path.read_bytes()+b' ')
    elif change=='verification_pin':cfg['cases'][0]['verification']['sha256']='0'*64
    elif change=='case_order':cfg['cases'][1]['case']=0
    else:
        path=root/'verification.json';v=json.loads(path.read_bytes())
        if change=='terminal':v['pbs']['run_count']=2
        if change=='rows_receipt':v['files']['inventory/rows.jsonl']['sha256']='f'*64
        if change=='capacity':
            mp=root/'full/manifest.json';m=json.loads(mp.read_bytes());m['mode']='capacity';mp.write_text(json.dumps(m))
            v['files']['manifest.json'].update(sha256=report.sha(mp.read_bytes()),bytes=mp.stat().st_size)
        path.write_text(json.dumps(v));cfg['cases'][0]['verification']['sha256']=report.sha(path.read_bytes())
    Path(config['path']).write_text(json.dumps(cfg))
    with pytest.raises(ValueError):report.run(config['path'],report.sha(Path(config['path']).read_bytes()),tmp_path/'output')
    assert not (tmp_path/'output/provenance.json').exists()


def test_sector_flags_not_applicable():
    p,original=saved()
    sector=next(row for row in report.normalize(original,p,0,collector()) if row['kind']=='sector')
    assert sector['stored_flags_applicability']=='not_applicable'
    assert sector['stored_flags_absent'] is None


@pytest.mark.parametrize('value',[True,'1',float('nan')])
def test_invalid_saved_metric_schema(value):
    p,original=saved();original['records'][0]['metrics']['mean']['sum']=value
    with pytest.raises(ValueError):report.normalize(original,p,0,collector())


def test_all_diagnostics_missing_preserves_unobserved_flag_state():
    p,original=saved();first=original['records'][0]
    first.update(status_counts={'missing_recorded_sampling_failure':192},stored_flag_counts={},undefined=192)
    for metric in first['metrics'].values():
        metric.update(finite_values=0,null_values=metric['expected_values'],nonfinite_values=0,
                      sum=0.,min=None,max=None,mean=None,available_only_mean=None)
    row=next(r for r in report.normalize(original,p,0,collector()) if all(r[k]==first[k] for k in inventory.KEY))
    assert row['stored_flags_absent']==192 and row['status_counts']['stored']==0
    assert row['stored_flag_counts']['flagged']==0
    assert row['undefined']==192


def test_source_census_change_prevents_publication(tmp_path,monkeypatch):
    config,_=orchestration(tmp_path,monkeypatch)
    source=tmp_path/'source.py';source.write_text('# before')
    paths=[source]
    monkeypatch.setattr(report,'source_paths',lambda:list(paths))
    original=report.render
    def changed(*args):
        value=original(*args);paths.append(tmp_path/'added.py');return value
    monkeypatch.setattr(report,'render',changed)
    with pytest.raises(ValueError):report.run(config,report.sha(config.read_bytes()),tmp_path/'output')
    assert not (tmp_path/'output/provenance.json').exists()


def test_analysis_context_changed_and_repinned_rejected(tmp_path):
    config=metadata_fixture(tmp_path)
    cfg=json.loads(Path(config['path']).read_bytes())
    path=Path(cfg['analysis_context']['path']);context=json.loads(path.read_bytes())
    context['added']='different accepted context';path.write_text(json.dumps(context))
    cfg['analysis_context']['sha256']=report.sha(path.read_bytes())
    Path(config['path']).write_text(json.dumps(cfg))
    with pytest.raises(ValueError,match='analysis context'):
        report.run(config['path'],report.sha(Path(config['path']).read_bytes()),tmp_path/'output')


def test_publication_failure_does_not_leave_success_report(tmp_path,monkeypatch):
    config,_=orchestration(tmp_path,monkeypatch)
    original=Path.write_text
    def fail(path,*args,**kwargs):
        if path.name=='provenance.json':raise OSError('fixture publication failure')
        return original(path,*args,**kwargs)
    monkeypatch.setattr(Path,'write_text',fail)
    output=tmp_path/'output'
    with pytest.raises(OSError):report.run(config,report.sha(config.read_bytes()),output)
    assert not (output/'report_ja.md').exists()
    assert not (output/'provenance.json').exists()
    assert (output/'cohorts.json').exists()
