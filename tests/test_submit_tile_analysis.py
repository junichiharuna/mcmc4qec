"""Analysis resources and readiness cannot silently discard failed replicates."""
import itertools
from pathlib import Path
import sys
import pytest

pytest.importorskip("ldpc")
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"cluster_scripts"))
import calibration as c
import tile_bar_study as b
import tile_analysis_capacity as p
import submit_tile_analysis as s


def test_analysis_resources_require_every_capacity_group_and_matching_shapes():
    plan=b.make_plan()
    profile=p.make_plan()
    rows=[dict(task=[case,rep],status="ok",synthetic=True,analysis_seconds=10*(case+1),peak_rss_mb=250.)
          for case,rep in itertools.product(range(4),range(24))]
    data=dict(manifest=c.digest(profile),tasks=96,failed=0,synthetic=True,records=rows)
    result=s.resource_plan(plan,profile,data)
    assert len(result["cases"])==4
    assert result["cases"][0]["predicted_analysis_seconds"]==80
    assert all(r["groups"]==768 and r["cpus"]==96 and 32<=r["memory_gb"]<=340 for r in result["cases"])
    data["records"].pop()
    with pytest.raises(ValueError):
        s.resource_plan(plan,profile,data)


def test_complete_failure_records_are_analyzed_but_missing_tasks_are_not():
    plan=b.make_plan()
    plan["replicates"]=2
    case=0
    sample_rows=[dict(task=list(task),status="failed" if i==0 else "ok") for i,task in enumerate(b.tasks(plan,case))]
    anchors=[dict(case=case,replicate=rep,status="ok") for rep in range(2)]
    samples=dict(command="sample",manifest=c.digest(plan),case=case,tasks=len(sample_rows),records=sample_rows,failed=1)
    anchor=dict(command="anchors",manifest=c.digest(plan),case=case,tasks=2,records=anchors,failed=0)
    s.check_completed_case(plan,case,samples,anchor)
    samples["records"].pop()
    with pytest.raises(ValueError):
        s.check_completed_case(plan,case,samples,anchor)
