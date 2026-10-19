"""Connect real source-byte relocation checks to bounded saved-result fixtures."""
import copy
import json
from pathlib import Path
import sys

import pytest

for dependency in ('ldpc', 'bposd', 'pymatching'):
    pytest.importorskip(dependency)
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'cluster_scripts'))
import calibration as c
import tile_reference_source_binding as binding
from test_tile_reference_source_binding import sources

REAL_REFERENCE_SOURCES = binding.reference_sources


@pytest.mark.parametrize('corrupt', [False, True])
def test_selector_preserves_old_reference_and_checks_new_source_bytes(tmp_path, monkeypatch, corrupt):
    import tile_low_noise_timing_selection as selector
    import tile_weight_reference_audit_run as run
    import audit_tile_weight_reference as audit
    from test_tile_low_noise_timing_selection import complete_fixture
    entry, put = complete_fixture(tmp_path, monkeypatch)
    monkeypatch.setattr(binding, 'reference_sources', REAL_REFERENCE_SOURCES)
    old, new, before, after = sources(tmp_path / 'source-trees')
    ra = Path(entry['reference_audit_root'])
    plan = json.loads((ra / 'manifest.json').read_bytes())
    record = json.loads((ra / 'conditions' / '0.json').read_bytes())
    record['report']['source_sha256'] = before
    original = copy.deepcopy(record['report'])
    c.save_artifact(ra / 'conditions' / '0', dict(manifest=c.digest(plan), condition=0), {}, record)
    for suffix in ('.json', '.npz', '.done.json'):
        path = ra / 'conditions' / ('0' + suffix)
        entry['input_sha256'][str(path)] = c.file_hash(path)
    summary = json.loads((ra / 'summary.json').read_bytes())
    summary['condition_marker_sha256']['0'] = c.file_hash(ra / 'conditions' / '0.done.json')
    put(ra / 'summary.json', summary)
    final = json.loads(Path(entry['final_report']).read_bytes())
    final['reference_audit'] = original
    put(Path(entry['final_report']), final)
    monkeypatch.setattr(binding, 'reference_context', lambda *args: dict(saved_root=old, current_root=new, sources=after))
    checked = []
    def report_binding(saved_plan, index, report):
        assert saved_plan == plan and index == 0
        assert report == dict(original, source_sha256=after)
        checked.append(index)
    monkeypatch.setattr(run, 'report_binding', report_binding)
    monkeypatch.setattr(audit, 'verify_unchanged', lambda root, inputs, current: checked.append(current == after))
    if corrupt:
        (new / 'audit.py').write_text('changed source bytes')
        with pytest.raises(ValueError):
            selector.load_complete(entry, selector.Evidence())
    else:
        rows, proof = selector.load_complete(entry, selector.Evidence())
        assert len(rows) == 2 and checked == [0, True]
        assert proof['reference_audit_digest'] == c.digest(original)
        assert json.loads((ra / 'conditions' / '0.json').read_bytes())['report'] == original


@pytest.mark.parametrize('corrupt_last', [False, True])
def test_evaluation_checks_all_sixteen_sources_without_rewriting_reports(tmp_path, monkeypatch, corrupt_last):
    import tile_low_noise_timing_evaluation_report as report_module
    from test_tile_low_noise_timing_evaluation_report import reference_fixture
    config, selection, _ = reference_fixture(tmp_path, monkeypatch)
    monkeypatch.setattr(binding, 'reference_sources', REAL_REFERENCE_SOURCES)
    old, new, before, after = sources(tmp_path / 'source-trees')
    ra = Path(config['audit_root'])
    plan = json.loads((ra / 'manifest.json').read_bytes())
    summary = json.loads((ra / 'summary.json').read_bytes())
    originals = {}
    for index in range(16):
        record = json.loads((ra / 'conditions' / f'{index}.json').read_bytes())
        record['report']['source_sha256'] = copy.deepcopy(before)
        if corrupt_last and index == 15:
            record['report']['source_sha256'][str(old / 'audit.py')] = '0' * 64
        originals[index] = copy.deepcopy(record['report'])
        c.save_artifact(ra / 'conditions' / str(index), dict(manifest=c.digest(plan), condition=index), {}, record)
        for suffix in ('.json', '.npz', '.done.json'):
            path = ra / 'conditions' / f'{index}{suffix}'
            config['input_sha256'][str(path)] = c.file_hash(path)
        summary['condition_marker_sha256'][str(index)] = c.file_hash(ra / 'conditions' / f'{index}.done.json')
        for item in selection['calibration_bindings']:
            if item['reference_condition'] == index:
                item['reference_audit_digest'] = c.digest(originals[index])
    (ra / 'summary.json').write_bytes(c.canonical(summary))
    config['input_sha256'][str(ra / 'summary.json')] = c.file_hash(ra / 'summary.json')
    monkeypatch.setattr(binding, 'reference_source_context', lambda *args: dict(saved_root=old, current_root=new, sources=after))
    checked = []
    def report_binding(saved_plan, index, report):
        assert saved_plan == plan
        assert report == dict(originals[index], source_sha256=after)
        checked.append(index)
    monkeypatch.setattr(report_module.reference_run, 'report_binding', report_binding)
    if corrupt_last:
        with pytest.raises(ValueError):
            report_module.reference_evidence(config, selection, report_module.Evidence())
    else:
        refs, evidence = report_module.reference_evidence(config, selection, report_module.Evidence())
        assert len(refs) == 12 and checked == list(range(16))
        assert evidence['audit_report_digests'] == {str(i): c.digest(value) for i, value in originals.items()}
        assert evidence['fresh_native_probe_executed'] is False
        assert evidence['current_raw_payloads_rehashed'] is False
        assert json.loads((ra / 'conditions' / '15.json').read_bytes())['report'] == originals[15]
