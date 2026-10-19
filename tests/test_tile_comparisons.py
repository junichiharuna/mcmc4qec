"""Paired contrasts retain shared-reference uncertainty and every replicate."""
import itertools
import json
import math
from pathlib import Path
import sys

import pytest

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"cluster_scripts"))
import tile_comparisons as p


REF=dict(estimate=.2,interval_999=[.18,.22],standard_error=.006)


def row(rep,value,interval=(.1,.3)):
    return dict(replicate=rep,estimate=value,interval=interval,available=interval is not None,
                flagged=False,undefined=False,high_rhat=False,low_ess=False,failure=None)


def test_shared_fluctuation_cancels_and_reference_range_is_exact():
    left=[row(0,.1),row(1,.2),row(2,.3)]
    right=[row(i,r["estimate"]+.05) for i,r in enumerate(left)]
    out=p.compare(left,right,3,REF)
    assert out["replicates"]==out["point_pairs"]==3
    assert out["mean_estimate_difference"]==pytest.approx(.05)
    assert out["estimate_difference_standard_error"]==pytest.approx(0,abs=1e-16)
    assert out["mean_squared_error_difference"]==pytest.approx(.0025)
    assert out["squared_error_difference_reference_range"]==pytest.approx([.0005,.0045])
    assert out["mean_log_ratio"]==pytest.approx(sum(math.log(b["estimate"]/a["estimate"]) for a,b in zip(left,right))/3)
    assert out["mean_log_ratio_standard_error"]>0


def test_missing_intervals_and_diagnostics_never_filter_pairs():
    left=[row(0,.1,(.1,.25)),row(1,.2,None),row(2,.3,(.3,.4))]
    right=[row(0,.2,None),row(1,.3,(.1,.3)),row(2,.4,(.1,.3))]
    right[2].update(flagged=True,undefined=True)
    out=p.compare(left,right,3,REF)
    coverage=out["coverage_reference_point"]
    assert coverage["both"]==0 and coverage["left_only"]==1 and coverage["right_only"]==2
    assert coverage["difference"]==pytest.approx(1/3)
    assert coverage["standard_error"]==pytest.approx(2/3)
    assert out["intervals_unavailable"]==dict(left=1,right=1)
    assert out["diagnostics"]["undefined"]==dict(left=0,right=1,difference=1/3)
    assert out["point_pairs"]==3


def test_missing_points_and_nonpositive_log_ratios_stay_explicit():
    left=[row(0,None,None),row(1,0.)]
    right=[row(0,.1),row(1,.2)]
    out=p.compare(left,right,2,REF)
    assert out["point_pairs"]==1 and out["positive_point_pairs"]==0
    assert out["mean_estimate_difference"] is None
    assert out["mean_squared_error_difference"] is None
    assert out["mean_log_ratio"] is None
    assert out["available_only"]["mean_estimate_difference"]==pytest.approx(.2)
    assert out["available_only"]["mean_log_ratio"] is None


@pytest.mark.parametrize("kind",["missing","duplicate","nan","invalid_interval","inconsistent_available"])
def test_invalid_fixed_cohorts_rejected(kind):
    left=[row(0,.1),row(1,.2)]
    right=[row(0,.2),row(1,.3)]
    if kind=="missing":
        right.pop()
    elif kind=="duplicate":
        right[1]["replicate"]=0
    elif kind=="nan":
        right[0]["estimate"]=float("nan")
    elif kind=="invalid_interval":
        right[0]["interval"]=(.4,.2)
    else:
        right[0]["available"]=False
    with pytest.raises(ValueError):
        p.compare(left,right,2,REF)


def test_all_and_only_one_factor_pairs_generated():
    keys=[(0,k,i,4,600,600,"coarse",m,b)
          for k,i,(m,b) in itertools.product(("ZH","ZHS"),("logical","rejection"),(("block",32),("cross_chain",None)))]
    pairs=list(p.condition_pairs(keys))
    assert len(pairs)==12
    assert {x["factor"] for x in pairs}=={"kernel","initialization","uncertainty"}
    for pair in pairs:
        changed={j for j,(a,b) in enumerate(zip(pair["left"],pair["right"])) if a!=b}
        assert changed==set(p.FACTORS[pair["factor"]])
    assert len({(x["left"],x["right"]) for x in pairs})==len(pairs)


def test_complete_file_pipeline_and_updated_hash_cannot_hide_missing_pair(tmp_path):
    import calibration as c
    import tile_summary as s
    plan=dict(replicates=2,cases=[dict(chains=4,windows=[32])],kernels={"ZH":{},"ZHS":{}},
              initializations=["logical","rejection"],burns=[0],blocks=[4])
    reference=dict(case=0,**REF)
    c.atomic_json(tmp_path/"manifest.json",plan)
    c.atomic_json(tmp_path/"reference_summary.json",dict(records=[reference]))
    context=dict(sampling_manifest=c.digest(plan),references=[reference],
                 reference_summary_sha256=c.file_hash(tmp_path/"reference_summary.json"))
    c.atomic_json(tmp_path/"analysis_manifest.json",context)
    entries=[]
    for kernel,initial in itertools.product(plan["kernels"],plan["initializations"]):
        for key in s.expected_conditions(plan,0,kernel,initial):
            for rep in range(2):
                value=.1+.01*(kernel=="ZHS")+.02*(initial=="rejection")+.001*rep
                entries.append(dict(row(rep,value),**dict(zip(s.CONDITION,key))))
    raw=tmp_path/"rows-0.jsonl"
    raw.write_bytes(b"".join(c.canonical(entry)+b"\n" for entry in entries))
    summary=dict(case=0,analysis=c.digest(context),raw_rows_sha256=c.file_hash(raw))
    c.atomic_json(tmp_path/"summary-0.json",summary)
    result=p.run(tmp_path,0,tmp_path/"comparisons.json")
    assert result["conditions"]==16 and result["contrasts"]==32
    assert json.loads((tmp_path/"comparisons.json").read_text())["records"]==result["records"]
    assert all(x["point_pairs"]==2 for x in result["records"])
    with pytest.raises(ValueError,match="already exists"):
        p.run(tmp_path,0,tmp_path/"comparisons.json")
    # A complete raw-row hash does not establish a complete scientific cohort.
    raw.write_bytes(b"".join(c.canonical(entry)+b"\n" for entry in entries[:-1]))
    summary["raw_rows_sha256"]=c.file_hash(raw)
    c.atomic_json(tmp_path/"summary-0.json",summary)
    with pytest.raises(ValueError,match="missing or duplicate"):
        p.run(tmp_path,0,tmp_path/"incomplete.json")
