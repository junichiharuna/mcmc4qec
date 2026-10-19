"""Small deterministic planning fixtures; no persisted production or census run."""
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
import tile_low_noise_timing_selection as select
import tile_low_noise_summary as summary
import tile_low_noise_timing_plan as p


@pytest.fixture(scope="module")
def selection():
    rows=[];bindings=[]
    for case in range(4):
        for target in range(3):
            plan=low.make_plan(case,target,capacity=False)
            interval=[.1,.1] if (case,target)==(0,0) else None
            conditions=[]
            for key in summary.expected_conditions(plan):
                a=dict(metrics=dict(replicates=192,point_estimates=192),
                    relative_rmse_reference_range=[.15,.15],precision=[
                        dict(epsilon=.2,classification="empirical_within_target"),
                        dict(epsilon=.1,classification="empirical_above_target")])
                conditions.append(dict(zip(summary.CONDITION,key),assessment=a))
            rows.extend(select.choose(plan,dict(replicates=192,conditions=conditions,
                reference_available=interval is not None,reference=None if interval is None else dict(interval=interval))))
            bindings.append(dict(manifest=c.digest(plan),analysis="a"*64,
                expected_conditions=list(summary.expected_conditions(plan)),reference_context="b"*64,
                reference_condition=case*3+target,reference_interval=interval,
                reference_audit_digest="c"*64,audited_collection_digest="d"*64,
                terminals=[dict(job_id="123.cluster",exit_status=0,ledger_sha256="e"*64)]))
    return dict(schema=1,purpose="low_noise_independent_timing_selection",conditions=24,rows=rows,
        input_manifest_sha256="1"*64,input_sha256={"/fixture/raw":"2"*64},input_resolved={"/fixture/raw":"/fixture/raw"},
        source_sha256=select.source_hashes(),calibration_bindings=bindings,production_selection_validated=True,
        independent_timing_performed=False,population_rmse_certified=False,nominal_coverage_certified=False,warning="fixture")


def bundle(selection):
    return p.make_plans(selection,selection_sha256="f"*64)


def test_all_rows_four_roles_and_full_dimensions(selection):
    result=bundle(selection)
    p.validate_plans(result,expected_registry_digest=c.digest(result["registry"]))
    assert set(result["plans"])==set(p.STAGES)
    for role,plan in result["plans"].items():
        cap=role.endswith("capacity")
        assert len(plan["rows"])==24 and plan["replicates"]==(2 if cap else 192)
        assert plan["capacity_workers"]==(2 if cap else None)
        assert len(list(p.tasks(plan)))==(2 if cap else 192)
        assert all(row["planning_status"]=="not_selected" for row in plan["rows"][1:])
        row=plan["rows"][0]
        assert row["initialization_stride"]==16
        assert row["condition"]["method"]=="cross_chain"
        assert row["anchor_trials"]==16384 and row["bootstrap_replicates"]==1000
        assert row["rungs"]==[.1,.07,.05,.03,.015,.01]
        assert row["fine_rung_indices"]==[0,2,4,6,8,9]


@pytest.mark.parametrize("ei,raw,rounded",[(1,9900,9920),(0,2475,2496)])
def test_exact_budget(ei,raw,rounded):
    result=p.mc_budget([.01,.01],ei)
    assert result["unrounded_trials"]==raw and result["trials"]==rounded


@pytest.mark.parametrize("interval",[[0,.1],[float('nan'),.1],[True,1],[.2,.1],[.1,1.1]])
def test_invalid_budget(interval):
    with pytest.raises(ValueError):p.mc_budget(interval,0)


def test_budget_large_and_degenerate():
    assert p.mc_budget([1e-100,1e-100],1)["trials"]>10**100
    assert p.mc_budget([1,1],1)["planning_status"]=="ineligible_degenerate_reference"
    assert p.mc_budget([.2,.2],0)["trials"]==128
    with pytest.raises(ValueError):p.mc_budget([.1,.1],True)


@pytest.mark.parametrize("change",["pending","identity","source","binding","selected","rank","replicates"])
def test_selection_tampering_rejected(selection,change):
    s=deepcopy(selection)
    if change=="pending":s["production_selection_validated"]=False
    if change=="identity":s["rows"][1]["epsilon_index"]=0
    if change=="source":s["source_sha256"]={"fake":"0"*64}
    if change=="binding":s["calibration_bindings"][0]["manifest"]="0"*64
    if change=="selected":s["rows"][0]["selected_condition"]["chains"]=16
    if change=="rank":s["rows"][0]["rank"][0]=0
    if change=="replicates":s["rows"][0]["calibration_replicates"]=191
    with pytest.raises(ValueError):bundle(s)


def test_read_pinned_snapshot_does_not_scan_raw(tmp_path,selection):
    path=tmp_path/"selection.json"
    path.write_bytes(c.canonical(selection))
    report,proof=p.read_selection(path,c.file_hash(path))
    assert report["conditions"]==24 and proof["raw_inputs_rehashed"] is False
    assert proof["submission_authorized"] is False
    with pytest.raises(ValueError):p.read_selection(path,"0"*64)


def test_coordinates_purposes_and_logical_stride(selection):
    result=bundle(selection)
    bar=result["plans"]["low_timing.bar.benchmark"]
    task=(0,0,0,191)
    assert p.seed_coordinates(bar,task,1,3,2)==(162,0,0,0,191,0,0,1,3)
    assert p.logical_index(bar["rows"][0],191,3)==191*16+3
    assert len({p.task_seed(bar,task,0,0,k) for k in range(4)})==4
    with pytest.raises(ValueError):p.seed_coordinates(bar,task,1,0,0)
    with pytest.raises(ValueError):p.seed_coordinates(bar,task,0,0,4)
    with pytest.raises(ValueError):p.seed_coordinates(bar,(0,0,1,0),0,0,0)
    mc=result["plans"]["low_timing.mc.capacity"]
    assert p.seed_coordinates(mc,(0,0,0,1),0,0,0)==(161,0,0,0,1)
    with pytest.raises(ValueError):p.seed_coordinates(mc,(0,0,0,2),0,0,0)


def test_manifest_rebind_or_mutation_rejected(selection):
    result=bundle(selection)
    result["plans"]["low_timing.mc.capacity"]["replicates"]=96
    with pytest.raises(ValueError):p.validate_plans(result,expected_registry_digest=c.digest(result["registry"]))


def test_external_registry_rejects_reselection_even_with_self_consistent_bundle(selection):
    first=bundle(selection)
    other=deepcopy(selection);other["warning"]="different frozen selection"
    second=bundle(other)
    with pytest.raises(ValueError,match="stage reuse"):
        p.validate_plans(second,expected_registry_digest=c.digest(first["registry"]))


def test_partial_point_is_not_a_budget_input(selection):
    s=deepcopy(selection)
    s["rows"][0]["partial_estimate"]=.999
    assert bundle(s)["plans"]["low_timing.mc.benchmark"]["rows"][0]["mc_budget"]==bundle(selection)["plans"]["low_timing.mc.benchmark"]["rows"][0]["mc_budget"]
