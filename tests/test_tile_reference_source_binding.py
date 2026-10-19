"""Bounded source-relocation acceptance: no cluster, sampling, or native probe."""
import copy
import importlib.util
import json
from pathlib import Path
from types import SimpleNamespace

import pytest

spec = importlib.util.spec_from_file_location('saved_reference_source_binding', Path(__file__).resolve().parents[1] / 'cluster_scripts/tile_reference_source_binding.py')
w = importlib.util.module_from_spec(spec)
spec.loader.exec_module(w)

def sha(path):
    import hashlib
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()


class Proof:
    def __init__(self):
        self.files = {}

    def track(self, path):
        p = Path(path).absolute()
        st = p.lstat()
        value = (sha(p), str(p.resolve()), st.st_dev, st.st_ino, st.st_mode, st.st_mtime_ns)
        if str(p) in self.files and self.files[str(p)] != value:
            raise ValueError('input changed')
        self.files[str(p)] = value
        return value[0]

    def finish(self):
        for path in tuple(self.files):
            self.track(path)



def sources(tmp_path):
    old = tmp_path / 'old' / 'cluster_scripts'
    new = tmp_path / 'new' / 'cluster_scripts'
    old.mkdir(parents=True)
    new.mkdir(parents=True)
    before, after = {}, {}
    for name in ('audit.py', 'reference.py'):
        for root, mapping in ((old, before), (new, after)):
            p = root / name
            p.write_text('fixed ' + name)
            mapping[str(p)] = sha(p)
    return old, new, before, after


def test_relocated_identical_sources_keep_both_provenances(tmp_path):
    old, new, before, after = sources(tmp_path)
    original = copy.deepcopy((before, after))
    proof = Proof()
    w.reference_sources(before, after, old, new, proof)
    assert (before, after) == original
    assert set(proof.files) == set(before) | set(after)
    proof.finish()


def test_same_root_still_checks_bytes(tmp_path):
    old, _, before, _ = sources(tmp_path)
    proof = Proof()
    w.reference_sources(before, before, old, old, proof)
    (old / 'audit.py').write_text('corrupt')
    with pytest.raises(ValueError):
        proof.finish()


@pytest.mark.parametrize('change', ['hash', 'extra', 'missing', 'wrong_root', 'relative', 'non_python', 'nested', 'empty'])
def test_relocation_rejects_nonportable_differences(tmp_path, change):
    old, new, before, after = sources(tmp_path)
    first = str(new / 'audit.py')
    if change == 'hash':
        (new / 'audit.py').write_text('different')
        after[first] = sha(first)
    elif change == 'extra':
        p = new / 'extra.py'; p.write_text('extra'); after[str(p)] = sha(p)
    elif change == 'missing':
        after.pop(first)
    elif change == 'wrong_root':
        new = tmp_path / 'another'
    elif change == 'relative':
        after['audit.py'] = after.pop(first)
    elif change == 'non_python':
        p = new / 'audit.txt'; p.write_text((new / 'audit.py').read_text()); after[str(p)] = after.pop(first)
    elif change == 'nested':
        p = new / 'nested' / 'audit.py'; p.parent.mkdir(); p.write_text((new / 'audit.py').read_text()); after[str(p)] = after.pop(first)
    else:
        before = {}; after = {}
    with pytest.raises((ValueError, FileNotFoundError)):
        w.reference_sources(before, after, old, new, Proof())


@pytest.mark.parametrize('which', ['old', 'new'])
def test_source_bytes_and_mid_read_changes_rejected(tmp_path, which):
    old, new, before, after = sources(tmp_path)
    proof = Proof()
    w.reference_sources(before, after, old, new, proof)
    root = old if which == 'old' else new
    (root / 'audit.py').write_text('changed after consumption')
    with pytest.raises(ValueError):
        proof.finish()
    with pytest.raises(ValueError):
        w.reference_sources(before, after, old, new, Proof())


def plan_fixture(tmp_path):
    old, new, before, after = sources(tmp_path)
    plan = dict(source_sha256=before, actual_native_profile_digest='native', native_profile_digest='saved-native',
                reference_context={'condition': 'fixed'}, input_sha256={'input': 'sha'},
                original_pbs_job_id='1.host', conditions=list(range(16)), workers=16,
                required_threads={'OMP_NUM_THREADS': '1'}, resources={'cpus': 96})
    current = dict(copy.deepcopy(plan), source_sha256=after)
    calls = []
    audit = SimpleNamespace(read_evidence=lambda root: calls.append(('read', root)) or {'fixed': True},
                            source_hashes=lambda: {str(new / 'audit.py'): after[str(new / 'audit.py')]})
    def make_plan(root, evidence):
        assert evidence == {'fixed': True}
        calls.append(('make', root))
        return current
    api = SimpleNamespace(audit=audit, reference=SimpleNamespace(make_plan=make_plan, __file__=str(new / 'reference.py')),
                          c=SimpleNamespace(canonical=canonical))
    audit_root = old.parent / 'runs' / 'audit'
    reference_root = tmp_path / 'reference'
    return plan, current, audit_root, reference_root, api, calls


def test_reference_context_allows_only_proven_source_relocation(tmp_path):
    plan, current, audit_root, root, api, calls = plan_fixture(tmp_path)
    original = copy.deepcopy(plan)
    proof = Proof()
    binding = w.reference_context(plan, audit_root, root, api, proof)
    assert binding['sources'] == api.audit.source_hashes()
    assert calls == [('read', root), ('make', root)]
    assert plan == original
    proof.finish()


@pytest.mark.parametrize('field', ['actual_native_profile_digest', 'native_profile_digest', 'reference_context', 'input_sha256',
                                   'original_pbs_job_id', 'conditions', 'workers', 'required_threads', 'resources'])
def test_reference_context_rejects_every_other_plan_difference(tmp_path, field):
    plan, current, audit_root, root, api, _ = plan_fixture(tmp_path)
    current[field] = 'changed'
    with pytest.raises(ValueError):
        w.reference_context(plan, audit_root, root, api, Proof())


def test_current_audit_sources_must_be_in_checked_plan(tmp_path):
    plan, current, audit_root, root, api, _ = plan_fixture(tmp_path)
    api.audit.source_hashes = lambda: {'unbound.py': 'a' * 64}
    with pytest.raises(ValueError):
        w.reference_context(plan, audit_root, root, api, Proof())


def test_metadata_source_context_does_not_probe_native(tmp_path):
    plan, current, audit_root, _, api, _ = plan_fixture(tmp_path)
    api.audit.read_evidence = lambda *args: pytest.fail('metadata preparation must not probe native or scan raw')
    proof = Proof()
    binding = w.reference_source_context(plan['source_sha256'], current['source_sha256'], audit_root, api, proof)
    assert binding['sources'] == api.audit.source_hashes()
    proof.finish()


def test_change_during_source_consumption_is_rejected(tmp_path):
    old, new, before, after = sources(tmp_path)
    class ChangingProof(Proof):
        def track(self, path):
            result = super().track(path)
            Path(path).write_text('changed during read')
            return result
    with pytest.raises(ValueError):
        w.reference_sources(before, after, old, new, ChangingProof())


def test_symlink_source_is_rejected(tmp_path):
    old, new, before, after = sources(tmp_path)
    target = tmp_path / 'external.py'; target.write_text('fixed audit.py')
    alias = new / 'audit.py'; alias.unlink()
    try:
        alias.symlink_to(target)
    except OSError:
        pytest.skip('Host does not permit creating a symlink; exercised on Linux')
    assert sha(alias) == after[str(alias)]
    with pytest.raises(ValueError):
        w.reference_sources(before, after, old, new, Proof())


def test_directory_named_python_file_is_rejected(tmp_path):
    old, new, before, after = sources(tmp_path)
    path = new / 'audit.py'; path.unlink(); path.mkdir()
    with pytest.raises(ValueError):
        w.reference_sources(before, after, old, new, Proof())


