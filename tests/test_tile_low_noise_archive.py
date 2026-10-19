"""Low-noise archive recovery binds the full task census and external hashes."""
import hashlib
import io
import json
from pathlib import Path
import sys
import tarfile

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'cluster_scripts'))
import tile_low_noise_archive as a


def encoded(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':')).encode()


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def plan():
    return dict(purpose='low_noise_production', case=2, target_index=1,
                replicates=2, kernels={'ZH': {}, 'ZHS': {}},
                initializations=['logical_basis', 'logical_combination'],
                condition=dict(chains=2, rungs=[.1, .003]))


def fixture(tmp_path, *, omit=None, corrupt=False, duplicate=False, extra=False):
    p = plan()
    data = {'manifest.json': encoded(p)}
    expected = a.expected_sampling(p, 2, 1)
    for i, (stem, identity) in enumerate(expected.items()):
        payload = {'.json': encoded({'status': 'failed' if i == 0 else 'ok'}), '.npz': b'trace'}
        marker = dict(identity=identity, sha256={ext: sha(raw) for ext, raw in payload.items()})
        data.update({stem + ext: raw for ext, raw in payload.items()})
        data[stem + '.done.json'] = encoded(marker)
    index = {name: sha(raw) for name, raw in data.items()}
    if omit:
        del data[omit]
    if corrupt:
        data['anchors/2-1-0-0-0-0-0.npz'] = b'changed'
    if extra:
        data['unregistered.txt'] = b'extra'
    archive = tmp_path / 'archive.tar.gz'
    with tarfile.open(archive, 'w:gz') as stream:
        entries = list(data.items())
        if duplicate:
            entries.append(('manifest.json', data['manifest.json']))
        for name, raw in entries:
            info = tarfile.TarInfo(name)
            info.size = len(raw)
            stream.addfile(info, io.BytesIO(raw))
    manifest = tmp_path / 'manifest.json'
    manifest.write_bytes(encoded(p))
    inputs = tmp_path / 'input_sha256.json'
    inputs.write_bytes(encoded(index))
    return dict(archive=archive, manifest=manifest, file_index=inputs,
                manifest_sha256=sha(manifest.read_bytes()),
                archive_sha256=sha(archive.read_bytes()),
                file_index_sha256=sha(inputs.read_bytes()), case=2, target_index=1)


def test_complete_census_and_failed_artifact_retained(tmp_path):
    args = fixture(tmp_path)
    result = a.verify(**args)
    assert result['artifacts'] == 34
    assert result['files'] == 103
    assert result['case'] == 2 and result['target_index'] == 1
    assert result['numerical_redecode'] is False


@pytest.mark.parametrize('option', ['corrupt', 'duplicate', 'extra', 'omit'])
def test_rejects_incomplete_or_changed_archive(tmp_path, option):
    args = fixture(tmp_path, **{option: 'anchors/2-1-0-0-1-0-0.npz' if option == 'omit' else True})
    with pytest.raises(ValueError):
        a.verify(**args)


@pytest.mark.parametrize('key', ['manifest_sha256', 'archive_sha256', 'file_index_sha256'])
def test_external_pin_must_match(tmp_path, key):
    args = fixture(tmp_path)
    args[key] = '0' * 64
    with pytest.raises(ValueError):
        a.verify(**args)


@pytest.mark.parametrize('key,value', [('case', 0), ('target_index', 2)])
def test_explicit_condition_binding(tmp_path, key, value):
    args = fixture(tmp_path)
    args[key] = value
    with pytest.raises(ValueError):
        a.verify(**args)


@pytest.mark.parametrize('change', [dict(purpose='low_noise_capacity'), dict(replicates=0),
                                  dict(case=True), dict(target_index=-1), dict(kernels={'ZH': {}})])
def test_invalid_plan_cannot_define_production_census(change):
    p = dict(plan(), **change)
    with pytest.raises(ValueError):
        a.expected_sampling(p, p['case'], p['target_index'])


def test_census_matches_actual_driver():
    pytest.importorskip('ldpc')
    import tile_low_noise_study as driver
    p = plan()
    expected = a.expected_sampling(p, 2, 1)
    actual = {}
    for phase, folder in [('sample', 'traces'), ('anchors', 'anchors')]:
        for task in driver.tasks(p, phase):
            actual[folder + '/' + '-'.join(map(str, task))] = dict(manifest=sha(encoded(p)), task=list(task))
    assert expected == actual


def test_extra_index_entry_rejected(tmp_path):
    args = fixture(tmp_path)
    value = json.loads(args['file_index'].read_bytes())
    value['missing.txt'] = '0' * 64
    args['file_index'].write_bytes(encoded(value))
    args['file_index_sha256'] = sha(args['file_index'].read_bytes())
    with pytest.raises(ValueError):
        a.verify(**args)


def test_manifest_required_in_archive_index(tmp_path):
    args = fixture(tmp_path)
    value = json.loads(args['file_index'].read_bytes())
    del value['manifest.json']
    args['file_index'].write_bytes(encoded(value))
    args['file_index_sha256'] = sha(args['file_index'].read_bytes())
    with pytest.raises(ValueError):
        a.verify(**args)


@pytest.mark.parametrize('changed_path', ['archive', 'manifest', 'file_index'])
def test_input_mutation_during_stream_rejected(tmp_path, monkeypatch, changed_path):
    args = fixture(tmp_path)
    original = a.archive_check.verify
    def changed(*positional):
        value = original(*positional)
        args[changed_path].write_bytes(args[changed_path].read_bytes() + b' ')
        return value
    monkeypatch.setattr(a.archive_check, 'verify', changed)
    with pytest.raises(ValueError, match='changed'):
        a.verify(**args)


def test_cli_writes_new_result_and_refuses_overwrite(tmp_path, monkeypatch):
    args = fixture(tmp_path)
    output = tmp_path / 'verification.json'
    argv = ['tile_low_noise_archive.py', '--output', str(output)]
    for key, value in args.items():
        argv += ['--' + key.replace('_', '-'), str(value)]
    monkeypatch.setattr(sys, 'argv', argv)
    a.main()
    raw = output.read_bytes()
    assert json.loads(raw)['artifacts'] == 34
    with pytest.raises(ValueError, match='existing'):
        a.main()
    assert output.read_bytes() == raw


def source_fixture(tmp_path):
    args = fixture(tmp_path)
    root = tmp_path / 'source'
    root.mkdir()
    with tarfile.open(args['archive'], 'r:gz') as archive:
        for member in archive:
            target = root / member.name
            target.parent.mkdir(exist_ok=True)
            target.write_bytes(archive.extractfile(member).read())
    return dict(root=root, output=tmp_path/'export', manifest_sha256=args['manifest_sha256'], case=2, target_index=1)


def test_export_requires_pbs_and_fresh_output(tmp_path, monkeypatch):
    args = source_fixture(tmp_path)
    monkeypatch.delenv('PBS_JOBID', raising=False)
    with pytest.raises(ValueError, match='PBS'):
        a.export_sampling(**args)
    monkeypatch.setenv('PBS_JOBID', '123.test')
    args['output'].mkdir()
    with pytest.raises(ValueError, match='fresh'):
        a.export_sampling(**args)


def test_export_roundtrip_preserves_failed_and_all_artifacts(tmp_path, monkeypatch):
    args = source_fixture(tmp_path)
    monkeypatch.setenv('PBS_JOBID', '123.test')
    result = a.export_sampling(**args)
    assert result['verification']['artifacts'] == 34
    assert result['source_unchanged'] is True
    assert result['pbs_job_id'] == '123.test'
    assert result['pbs_terminal_verified'] is False
    assert json.loads((args['output']/'export.json').read_bytes()) == result
    assert (args['output']/'export-intent.json').is_file()
    with pytest.raises(ValueError):
        a.export_sampling(**args)


@pytest.mark.parametrize('mode', ['missing', 'extra', 'corrupt'])
def test_export_rejects_invalid_source_artifacts(tmp_path, monkeypatch, mode):
    args = source_fixture(tmp_path)
    monkeypatch.setenv('PBS_JOBID', '123.test')
    path = args['root']/'traces/2-1-0-0-0-0-0.npz'
    if mode == 'missing':
        path.unlink()
    elif mode == 'extra':
        (args['root']/'traces/extra.npz').write_bytes(b'extra')
    else:
        path.write_bytes(b'corrupt')
    with pytest.raises(ValueError):
        a.export_sampling(**args)
    assert not (args['output']/'export.json').exists()


def test_export_rejects_source_mutation_during_compression(tmp_path, monkeypatch):
    args = source_fixture(tmp_path)
    monkeypatch.setenv('PBS_JOBID', '123.test')
    original = tarfile.TarFile.add
    modified = False
    def changed(self, name, *positional, **keywords):
        nonlocal modified
        result = original(self, name, *positional, **keywords)
        if not modified and str(name).endswith('.npz'):
            modified = True
            Path(name).write_bytes(b'changed')
        return result
    monkeypatch.setattr(tarfile.TarFile, 'add', changed)
    with pytest.raises(ValueError, match='changed'):
        a.export_sampling(**args)
    assert modified and not (args['output']/'export.json').exists()


@pytest.mark.parametrize('mode', ['new_artifact', 'worker_changed'])
def test_export_rechecks_file_census_and_worker_bytes(tmp_path, monkeypatch, mode):
    args = source_fixture(tmp_path)
    monkeypatch.setenv('PBS_JOBID', '123.test')
    worker = tmp_path/'worker.py'
    worker.write_bytes(Path(a.__file__).read_bytes())
    monkeypatch.setattr(a, '__file__', str(worker))
    original = tarfile.TarFile.add
    modified = False
    def changed(self, name, *positional, **keywords):
        nonlocal modified
        result = original(self, name, *positional, **keywords)
        if not modified:
            modified = True
            if mode == 'new_artifact':
                (args['root']/'traces/extra.npz').write_bytes(b'extra')
            else:
                worker.write_bytes(worker.read_bytes() + b'\n# changed\n')
        return result
    monkeypatch.setattr(tarfile.TarFile, 'add', changed)
    with pytest.raises(ValueError):
        a.export_sampling(**args)
    assert modified and not (args['output']/'export.json').exists()
