"""Seed adapter tests use tiny streams, never the production census."""
from copy import deepcopy
from pathlib import Path
import sys

import pytest
for dependency in ("ldpc", "bposd", "pymatching"):
    pytest.importorskip(dependency)
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"cluster_scripts"))
import calibration as c
import tile_seed_audit as old
import tile_low_noise_timing_plan as p
import tile_low_noise_timing_seed_audit as a
from test_tile_low_noise_timing_plan import selection, bundle


def test_entry_counts_and_authoritative_seed_coordinates(selection):
    b=bundle(selection)
    for plan in b["plans"].values():
        entries=list(a.entries(plan));counts=a.planned_counts(plan)
        assert len(entries)==sum(counts.values())==plan["planned_seed_entries"]
        assert len({(e.coordinates,e.purpose) for e in entries})==len(entries)
        first=entries[0]
        assert first.coordinates==p.seed_coordinates(plan,next(p.tasks(plan)),0,0,0)
    assert sum(x["planned_seed_entries"] for x in b["plans"].values())==194*(3+2*6*4)


def test_new_small_census_and_forced_collision(tmp_path,selection):
    b=bundle(selection)
    plan=b["plans"]["low_timing.bar.capacity"]
    entries=list(a.entries(plan))
    good=old.census(iter(entries),len(entries),tmp_path/"ok.sqlite")
    assert good["unexpected_collisions"]==0 and good["intentional_shared_entries"]==0
    bad=old.census(iter(entries),len(entries),tmp_path/"bad.sqlite",seed_function=lambda *args:1)
    assert bad["unexpected_collisions"]==len(entries)-1


def test_empty_selection_four_zero_namespaces(selection):
    s=deepcopy(selection)
    # Exact full selector output for a missing reference in the only selected pair.
    import tile_low_noise_timing_selection as selector
    import tile_low_noise_study as low
    pair=s["rows"][:2]
    candidates=pair[0]["candidates"]
    compared=dict(replicates=192,reference=None,reference_available=False,
        conditions=[dict(x["condition"],assessment=x["assessment"]) for x in candidates])
    s["rows"][:2]=selector.choose(low.make_plan(0,0,capacity=False),compared)
    s["calibration_bindings"][0]["reference_interval"]=None
    result=bundle(s)
    assert len(result["plans"])==4
    assert all(not list(a.entries(plan)) and plan["planned_seed_entries"]==0 for plan in result["plans"].values())


def legacy():
    # No seed generation: metadata/factory interface fixture, not old production evidence.
    factories={str(i):(lambda:iter(())) for i in range(56)}
    counts={str(i):0 for i in range(56)};counts['0']=3963562
    evidence=dict(planned_counts=counts,planned_total=3963562,master_seed=2026101719,
        input_sha256={'/fixture/old':'a'*64},source_sha256={'/fixture/source':'b'*64},
        plan_sha256={str(i):'c'*64 for i in range(56)},reserved_unenumerated_stages={})
    return factories,evidence


def baseline_kwargs(evidence):
    result=dict(planned_entries=3963562,checked_entries=3963562,unchecked_entries=0,complete=True,
        unexpected_collisions=0,intentional_shared_entries=8448,unique_seeds=3955114,
        checked_counts={'old.fixture':3963562},stream_sha256='d'*64)
    return dict(baseline_evidence_sha256=c.digest(evidence),baseline_result=result,baseline_result_sha256=c.digest(result))


def test_extend_catalog_keeps_all_old_factories_and_hash_binding(selection):
    factories,evidence=legacy();b=bundle(selection)
    kwargs=baseline_kwargs(evidence)|dict(expected_registry_digest=c.digest(b['registry']))
    combined,proof=a.extend_catalog(factories,evidence,b,**kwargs)
    assert len(combined)==60 and all(combined[k] is v for k,v in factories.items())
    assert proof['planned_total']==3963562+9894
    assert proof['expected_intentional_shared_entries']==8448
    assert proof['submission_authorized'] is False
    with pytest.raises(ValueError):a.extend_catalog(factories,evidence,b,**(kwargs|dict(baseline_evidence_sha256='0'*64)))
    del factories['0']
    with pytest.raises(ValueError):a.extend_catalog(factories,evidence,b,**kwargs)


def test_complete_gate_rejects_old_partial_or_collision(selection):
    fs,e=legacy();b=bundle(selection)
    _,proof=a.extend_catalog(fs,e,b,**baseline_kwargs(e),expected_registry_digest=c.digest(b['registry']))
    n=proof['planned_total']
    result=dict(planned_entries=n,checked_entries=n,unchecked_entries=0,complete=True,
        unexpected_collisions=0,intentional_shared_entries=8448,unique_seeds=n-8448,
        checked_counts=proof['planned_role_counts'],stream_sha256='a'*64)
    # Old role counts must come from complete baseline evidence, not guesses.
    assert a.complete_census_gate(result,proof,expected_evidence_sha256=c.digest(proof))['submission_authorized'] is False
    for key,value in [('complete',False),('checked_entries',3963562),('unexpected_collisions',1),('intentional_shared_entries',0)]:
        changed=dict(result);changed[key]=value
        with pytest.raises(ValueError):a.complete_census_gate(changed,proof,expected_evidence_sha256=c.digest(proof))
    with pytest.raises(ValueError):a.complete_census_gate(result,proof,expected_evidence_sha256='0'*64)
