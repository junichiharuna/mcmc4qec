"""Host-portable persisted identity, with strict same-process seal tracking."""
import json
from pathlib import Path
from types import SimpleNamespace

import pytest

from test_submit_tile_low_noise_timing_selection import w, prepared, submit, run_small, job_fixture


@pytest.mark.parametrize('field', ['device', 'inode'])
def test_portable_snapshot_ignores_only_host_local_identity(tmp_path, field):
    path = tmp_path / 'input'; path.write_text('fixed')
    a = w.snapshot(path); b = dict(a); b[field] += 1
    assert w.portable_identity(a) == w.portable_identity(b)


@pytest.mark.parametrize('field', ['sha256', 'target', 'mode'])
def test_portable_snapshot_retains_content_target_and_mode(tmp_path, field):
    path = tmp_path / 'input'; path.write_text('fixed')
    a = w.snapshot(path); b = dict(a)
    b[field] = b[field] + 1 if field == 'mode' else b[field] + 'different'
    assert w.portable_identity(a) != w.portable_identity(b)


@pytest.mark.parametrize('change', ['missing', 'extra'])
def test_portable_snapshot_requires_exact_schema(tmp_path, change):
    path = tmp_path / 'input'; path.write_text('fixed')
    value = w.snapshot(path)
    if change == 'missing':
        value.pop('inode')
    else:
        value['extra'] = True
    with pytest.raises(ValueError):
        w.portable_identity(value)


def simulate_other_host(monkeypatch, *, later_change=None):
    original = w.snapshot
    def changed(path, **kwargs):
        result = original(path, **kwargs)
        result['device'] += 100
        result['inode'] += 100
        if later_change and later_change['active'] and Path(path) == later_change['path']:
            result['inode'] += 1
        return result
    monkeypatch.setattr(w, 'snapshot', changed)


def test_prepared_control_can_be_read_on_another_host(tmp_path, monkeypatch):
    root, control_sha, _ = prepared(tmp_path, monkeypatch)
    simulate_other_host(monkeypatch)
    state = w.read_plan(root, control_sha)
    assert state['prepared']['input']['path']


@pytest.mark.parametrize('field', ['sha256', 'target', 'mode'])
def test_prepared_control_rejects_portable_field_change(tmp_path, monkeypatch, field):
    root, _, _ = prepared(tmp_path, monkeypatch)
    path = root / 'control.json'; control = json.loads(path.read_bytes())
    value = next(iter(control['inputs'].values()))
    value[field] = value[field] + 1 if field == 'mode' else value[field] + 'different'
    path.write_bytes(w.canonical(control))
    with pytest.raises(ValueError):
        w.read_plan(root, w.sha(path))


@pytest.mark.parametrize('change_during_seal', [False, True])
def test_terminal_seal_accepts_host_change_but_rejects_later_replacement(tmp_path, monkeypatch, change_during_seal):
    root, control_sha, _ = prepared(tmp_path, monkeypatch)
    submit(root, control_sha, lambda *a, **k: SimpleNamespace(stdout='123.cluster\n', stderr=''))
    ledger = run_small(root, control_sha, monkeypatch)
    later = dict(active=False, path=root / 'completion.json')
    simulate_other_host(monkeypatch, later_change=later)
    calls = []
    def query(job):
        calls.append(job)
        if change_during_seal:
            later['active'] = True
        return {'Jobs': {job: job_fixture(ledger['command'][1], ledger['resource'])}}
    if change_during_seal:
        with pytest.raises(ValueError):
            w.seal(root, control_sha, job_query=query)
        assert calls == [ledger['job_id']]
        assert not (root / 'descriptor.json').exists()
    else:
        result = w.seal(root, control_sha, job_query=query)
        assert result['accepted']['job_id'] == ledger['job_id']
