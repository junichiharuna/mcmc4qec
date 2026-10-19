"""Finite seed namespace and provenance audit contracts."""
from pathlib import Path
import sys

import pytest

for dependency in ("ldpc", "bposd", "pymatching"):
    pytest.importorskip(dependency)

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"cluster_scripts"))
import tile_seed_audit as audit
import tile_study as t
import tile_low_noise_study as low


def entries():
    yield audit.Entry("a",(1,2),0)
    yield audit.Entry("b",(1,3),0)
    yield audit.Entry("c",(1,2),0)


def test_same_input_different_role_is_collision(tmp_path):
    result=audit.census(entries(),3,tmp_path/"seen.sqlite")
    assert result["complete"]
    assert result["unexpected_collisions"]==1
    assert result["collision_examples"][0]["kind"]=="same_input_different_role"
    (tmp_path/"seen.sqlite").unlink()  # Connection must close on Windows as well.


def test_different_inputs_same_seed(tmp_path):
    result=audit.census(entries(),3,tmp_path/"seen.sqlite",seed_function=lambda task,purpose:4)
    assert result["unexpected_collisions"]==2
    assert result["collision_examples"][0]["kind"]=="different_input_same_seed"


def test_partial_keeps_full_denominator(tmp_path):
    result=audit.census(entries(),3,tmp_path/"seen.sqlite",limit=1)
    assert not result["complete"]
    assert result["planned_entries"]==3 and result["checked_entries"]==1
    assert result["unchecked_entries"]==2


def test_intentional_share_requires_exact_input_and_roles(tmp_path):
    rows=[audit.Entry("calibration.bootstrap",(33,0),0),audit.Entry("synthetic.bootstrap",(33,0),0)]
    result=audit.census(iter(rows),2,tmp_path/"seen.sqlite")
    assert result["intentional_shared_entries"]==1
    assert result["unexpected_collisions"]==0


def test_repeated_alias_is_not_silently_allowed(tmp_path):
    rows=[audit.Entry("calibration.bootstrap",(33,0),0),audit.Entry("synthetic.bootstrap",(33,0),0),audit.Entry("synthetic.bootstrap",(33,0),0)]
    result=audit.census(iter(rows),3,tmp_path/"seen.sqlite")
    assert result["intentional_shared_entries"]==1
    assert result["unexpected_collisions"]==1


def test_low_noise_namespace_matches_driver_and_separates_targets():
    plans=[low.make_plan(0,j,capacity=True) for j in (0,1)]
    generated=[]
    for p in plans:
        rows=list(audit.low_entries(p,include_analysis=False))
        first=rows[0]
        task=next(low.tasks(p))
        assert t.seed(first.coordinates,first.purpose)==low.task_seed(p,task,"sample",0)
        assert any(e.coordinates[0]==154 for e in rows)
        generated.append({t.seed(e.coordinates,e.purpose) for e in rows})
    assert not generated[0]&generated[1]


def test_no_silent_short_stream(tmp_path):
    import pytest
    with pytest.raises(ValueError,match="planned count"):
        audit.census(entries(),4,tmp_path/"seen.sqlite")


def test_production_bootstrap_matches_actual_low_helper():
    import tile_low_noise_analysis as analysis
    plan=low.make_plan(3,2,capacity=False)
    group=(3,2,1,1,191)
    for chains,burn,samples,ladder,_,_,block in analysis.analysis_settings(plan):
        expected=t.seed((153,*group,chains,burn,samples,ladder,block or 0),0)
        assert analysis.bootstrap_seed(plan,group,chains,burn,samples,ladder,block)==expected


def test_catalog_bound_cohort_counts_and_source_provenance():
    data=Path(__file__).resolve().parents[1]/"docs/wp/data_tile_validation_2026-10-17"
    factories,evidence=audit.catalog(data)
    counts=evidence["planned_counts"]
    assert counts["calibration"]==2*190464
    assert counts["anchors"]==4*192
    assert counts["reference"]==1248
    assert counts["mc.capacity"]==8*96
    assert counts["mc.benchmark"]==8*192
    assert counts["low.0.0.True"]==2*(2*2*2*10)+2
    assert evidence["source_sha256"] and evidence["input_sha256"]
    assert set(counts)==set(factories)


def test_synthetic_capacity_uses_purpose_two_and_separate_bootstrap():
    import tile_low_noise_analysis_capacity as capacity
    import tile_low_noise_analysis as analysis
    plan=capacity.make_plan(0,0)
    compute=capacity.compute_plan(plan)
    rows=list(audit.low_capacity_entries(plan))
    keys={(row.coordinates,row.purpose) for row in rows}
    assert len(keys)==len(rows)
    assert {row.coordinates[0] for row in rows}=={155}
    assert {row.purpose for row in rows}=={0,2}
    group=next(iter(capacity.groups(plan)))
    assert t.seed(rows[0].coordinates,rows[0].purpose)==capacity.synthetic_seed(plan,group,0,0)
    chains,burn,samples,ladder,_,_,block=next(iter(analysis.analysis_settings(compute)))
    seed=analysis.bootstrap_seed(compute,group,chains,burn,samples,ladder,block)
    first=next(row for row in rows if row.role=="low.synthetic.bootstrap")
    assert seed==t.seed(first.coordinates,first.purpose)
