"""Analysis recovery retains accepted payloads and execution provenance."""
import hashlib
import json
from pathlib import Path
import sys

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'cluster_scripts'))
import tile_low_noise_analysis_export_worker as worker
from test_tile_low_noise_analysis_archive import source_fixture


def save(path, value):
    data = json.dumps(value, sort_keys=True).encode()
    path.write_bytes(data)
    return hashlib.sha256(data).hexdigest()


@pytest.fixture
def prepared(tmp_path, monkeypatch):
    source = source_fixture(tmp_path)
    folder = tmp_path / 'worker'
    folder.mkdir()
    monkeypatch.setattr(worker, '__file__', str(folder / 'worker.py'))
    monkeypatch.setenv('PBS_JOBID', '42.test')
    config = dict(source=str(source['root']), case=2, target_index=1,
        python=dict(path=str(Path(sys.executable).resolve())), source_sha256={})
    for name, path, digest in (
        ('manifest', source['root'] / 'manifest.json', source['manifest_sha256']),
        ('analysis_manifest', source['root'] / 'analysis_manifest.json', source['analysis_manifest_sha256']),
        ('sampling_index', source['sampling_index'], source['sampling_index_sha256']),
        ('accepted_index', source['file_index'], source['file_index_sha256'])):
        config[name] = dict(path=str(path), sha256=digest)
        if name in ('analysis_manifest', 'sampling_index'):
            config['source_sha256'][str(path)] = digest
    value = dict(target=str(folder), qsub_executed=False, config=config, gate={'fixed': 'gate'})
    (folder / 'export.sh').write_bytes(b'script')
    rewrite_stage(folder, value)
    monkeypatch.setattr(worker.gate, 'check', lambda _: {'fixed': 'gate'})
    monkeypatch.setattr(worker.gate, 'query_pbs', lambda _: dict(
        job_state='R', run_count=1, Submit_arguments=str(folder / 'export.sh')))
    return folder, value


def rewrite_stage(folder, value):
    digest = save(folder / 'stage.json', value)
    save(folder / 'submission-intent.json', dict(stage_sha256=digest,
        command=['qsub', str(folder / 'export.sh')], script_sha256=hashlib.sha256(b'script').hexdigest()))


def test_complete_export_once(prepared):
    folder, value = prepared
    result = worker.run_worker()
    assert result['verification']['groups'] == 8
    assert result['accepted_index_sha256'] == value['config']['accepted_index']['sha256']
    assert (folder / 'completion.json').is_file()
    with pytest.raises(ValueError):
        worker.run_worker()


@pytest.mark.parametrize('mode', ['no_pbs', 'wrong_script', 'changed_stage', 'missing_context_pin',
                                 'missing_sampling_pin', 'wrong_context_path', 'different_accepted_payload'])
def test_reject_before_completion(prepared, monkeypatch, mode):
    folder, value = prepared
    if mode == 'no_pbs':
        monkeypatch.delenv('PBS_JOBID')
    elif mode == 'wrong_script':
        monkeypatch.setattr(worker.gate, 'query_pbs', lambda _: dict(job_state='R', run_count=1, Submit_arguments='other'))
    elif mode == 'changed_stage':
        (folder / 'stage.json').write_bytes((folder / 'stage.json').read_bytes() + b' ')
    else:
        config = value['config']
        if mode in ('missing_context_pin', 'missing_sampling_pin'):
            name = 'analysis_manifest' if mode == 'missing_context_pin' else 'sampling_index'
            del config['source_sha256'][config[name]['path']]
        elif mode == 'wrong_context_path':
            config['analysis_manifest']['path'] = str(folder / 'other.json')
        else:
            index = Path(config['accepted_index']['path'])
            data = json.loads(index.read_bytes())
            data['analysis/2-1-0-0-0.npz'] = '0' * 64
            config['accepted_index']['sha256'] = save(index, data)
        rewrite_stage(folder, value)
    with pytest.raises(ValueError):
        worker.run_worker()
    assert not (folder / 'completion.json').exists()


@pytest.mark.parametrize('mode', ['stage', 'gate', 'pbs'])
def test_execution_changes_do_not_seal(prepared, monkeypatch, mode):
    folder, value = prepared
    original = worker.analysis.export_analysis
    def changed(**kwargs):
        result = original(**kwargs)
        if mode == 'stage':
            (folder / 'stage.json').write_bytes((folder / 'stage.json').read_bytes() + b' ')
        elif mode == 'gate':
            monkeypatch.setattr(worker.gate, 'check', lambda _: {'changed': True})
        else:
            monkeypatch.setattr(worker.gate, 'query_pbs', lambda _: dict(job_state='F'))
        return result
    monkeypatch.setattr(worker.analysis, 'export_analysis', changed)
    with pytest.raises(ValueError):
        worker.run_worker()
    assert (folder / 'data/export.json').exists()
    assert not (folder / 'completion.json').exists()
