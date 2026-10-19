"""Bounded references preserve every low-noise BAR setting and replicate."""
from copy import deepcopy
from pathlib import Path
import sys

import pytest

for dependency in ("ldpc", "bposd", "pymatching"):
    pytest.importorskip(dependency)
sys.path.insert(0, str(Path(__file__).resolve().parents[1]/"cluster_scripts"))
import tile_low_noise_study as low
import tile_low_noise_summary as description
import tile_weight_stratified as weights
import tile_low_noise_reference_comparison as compare
import calibration as c
import tile_low_noise_analysis_partitions as partitions
import audit_tile_weight_reference as audit


def inputs():
    plan=low.make_plan(0,0,capacity=False)
    plan.update(replicates=2,burns=[0],blocks=[2])
    plan["condition"].update(chains=4,steps=8,windows=[8],rungs=[.1,.01],coarse=[.1,.01])
    rows=[]
    for key in description.expected_conditions(plan):
        for rep in range(2):
            row=dict(zip(description.CONDITION,key))
            row.update(group=[0,0,list(plan["kernels"]).index(row["kernel"]),plan["initializations"].index(row["init"]),rep],
                replicate=rep,target_p=.01,noise="bit",n=72,estimate=.02+.01*rep,
                interval=[.001,.1],available=True,flagged=False,undefined=False,high_rhat=False,low_ess=False,
                failure=None,reference=None,reference_available=False)
            rows.append(row)
    reference=weights.synthesize(72,"bit",.01,[dict(w=0,mode="enum",trials=1,failures=0),
        dict(w=1,mode="enum",trials=72,failures=1)])
    condition=dict(condition=0,case=0,physical_decoder_prior=.01,chunks=2,failed_chunks=[],
        planned_trials=73,available_trials=73,available=True,reference=reference)
    context=dict(purpose="weight_reference_production",reference=dict(runtime=plan["runtime"],
        decoder=plan["decoder"],platform_profile_digest=plan["native_input_digests"]["platform_profile"],
        conditions=[dict(case=0,physical_decoder_prior=.01)]),
        input_digests=dict(platform_profile=plan["native_input_digests"]["platform_profile"]))
    return plan,rows,condition,context


def test_every_cohort_uses_bounded_reference_without_fabricated_point():
    plan,rows,condition,_=inputs()
    result=compare.compare_rows(plan,rows,condition)
    assert result["rows"]==32 and len(result["conditions"])==16
    assert result["reference"]["partial_estimate"]>0
    assert result["reference"]["omitted_mass_upper"]>0
    assert result["reference"]["full_point_estimate"] is None
    assert result["raw_reference_audited"] is False
    for item in result["conditions"]:
        assessment=item["assessment"]
        assert assessment["metrics"]["replicates"]==2
        assert assessment["metrics"]["bias_reference_range"] is not None
        assert "coverage_reference_point" not in assessment["metrics"]
        assert assessment["nominal_coverage_certified"] is False


def test_unavailable_reference_keeps_all_bar_conditions():
    plan,rows,condition,_=inputs()
    condition.update(available=False,reference=None,failed_chunks=[[0,1,0]],available_trials=1)
    result=compare.compare_rows(plan,rows,condition)
    assert result["reference_available"] is False and len(result["conditions"])==16
    assert all(item["assessment"]["metrics"]["bias_reference_range"] is None for item in result["conditions"])


def test_failed_bar_row_does_not_shrink_reference_comparison_denominator():
    plan,rows,condition,_=inputs()
    rows[0].update(estimate=None,interval=None,available=False,failure="sampling_failed",undefined=True,flagged=True)
    result=compare.compare_rows(plan,rows,condition)
    metrics=result["conditions"][0]["assessment"]["metrics"]
    assert metrics["replicates"]==2 and metrics["unavailable_intervals"]==1
    assert metrics["point_estimates"]==1 and metrics["rmse_reference_range"] is None


@pytest.mark.parametrize("change",["missing","target","prior","counts"])
def test_wrong_or_missing_scientific_input_is_rejected(change):
    plan,rows,condition,_=inputs()
    if change=="missing": rows.pop()
    elif change=="target": rows[0]["target_p"]=.003
    elif change=="prior": condition["physical_decoder_prior"]=.003
    else: condition["reference"]["partial_estimate"]+=.01
    with pytest.raises(ValueError): compare.compare_rows(plan,rows,condition)


@pytest.mark.parametrize("change",[None,"runtime","decoder","profile","context_profile","duplicate","purpose"])
def test_compatibility_requires_same_fixed_failure_definition(change):
    plan,_,_,context=inputs()
    context=deepcopy(context)
    if change=="runtime": context["reference"]["runtime"]["package_sha256"]="changed"
    elif change=="decoder": context["reference"]["decoder"]["max_iter"]=17
    elif change=="profile": context["reference"]["platform_profile_digest"]="changed"
    elif change=="context_profile": context["input_digests"]["platform_profile"]="changed"
    elif change=="duplicate": context["reference"]["conditions"]*=2
    elif change=="purpose": context["purpose"]="pilot"
    if change is None: assert compare.compatible_condition(plan,context)==0
    else:
        with pytest.raises(ValueError): compare.compatible_condition(plan,context)


def saved_fixture(tmp_path, monkeypatch):
    plan,rows,condition,context=inputs()
    root=tmp_path/"reference"
    root.mkdir()
    (root/"manifest.json").write_bytes(c.canonical(context))
    report=dict(context=context,context_digest=c.digest(context),reference_plan_digest=c.digest(context["reference"]),
        native_profile_digest=plan["native_input_digests"]["platform_profile"],
        native_platform_verified=True,raw_reference_audited=True,all_labels_redecoded=False,condition=condition)
    monkeypatch.setattr(partitions,"read_collection",lambda _: (plan,iter(rows),dict(rows=len(rows))))
    calls=[]
    def read(_,index):
        calls.append(index)
        return report
    monkeypatch.setattr(audit,"audit_saved_condition",read)
    monkeypatch.setenv("PBS_JOBID","123.node")
    for key,value in low.native.THREADS.items(): monkeypatch.setenv(key,value)
    return plan,rows,report,root,tmp_path/"result.json",calls


def test_saved_run_binds_audit_once_and_retains_partial_scope(tmp_path,monkeypatch):
    _,_,_,root,output,calls=saved_fixture(tmp_path,monkeypatch)
    result=compare.run(tmp_path/"bar",root,output)
    assert calls==[0] and output.exists()
    assert result["raw_reference_audited"] and result["native_decoder_revalidated"]
    assert not result["all_reference_labels_redecoded"] and not result["all_mcmc_states_redecoded"]
    assert result["pbs_job_id"]=="123.node"
    assert {"tile_precision_assessment.py","tile_summary.py","tile_comparisons.py","tile_reference.py"} <= set(result["source_sha256"])
    with pytest.raises(ValueError): compare.run(tmp_path/"bar",root,output)
    assert calls==[0]


@pytest.mark.parametrize("change",["pbs","threads","context","digest","profile","raw","native","index","iterator","count","changed_file"])
def test_saved_run_rejects_incomplete_or_changed_evidence_without_output(tmp_path,monkeypatch,change):
    plan,rows,report,root,output,_=saved_fixture(tmp_path,monkeypatch)
    if change=="pbs": monkeypatch.delenv("PBS_JOBID")
    elif change=="threads": monkeypatch.setenv("OMP_NUM_THREADS","2")
    elif change=="context": report["context"]=dict(report["context"],purpose="changed")
    elif change=="digest": report["reference_plan_digest"]="changed"
    elif change=="profile": report["native_profile_digest"]="changed"
    elif change=="raw": report["raw_reference_audited"]=False
    elif change=="native": report["native_platform_verified"]=False
    elif change=="index": report["condition"]["condition"]=1
    elif change=="iterator":
        def bad_rows():
            yield from rows
            raise ValueError("final collection check failed")
        monkeypatch.setattr(partitions,"read_collection",lambda _: (plan,bad_rows(),dict(rows=len(rows))))
    elif change=="count":
        monkeypatch.setattr(partitions,"read_collection",lambda _: (plan,iter(rows),dict(rows=len(rows)+1)))
    elif change=="changed_file":
        def altered(*_):
            (root/"manifest.json").write_bytes(b"{}")
            return report
        monkeypatch.setattr(audit,"audit_saved_condition",altered)
    with pytest.raises(ValueError): compare.run(tmp_path/"bar",root,output)
    assert not output.exists()


def test_numeric_source_change_during_audit_prevents_publication(tmp_path,monkeypatch):
    _,_,report,root,output,_=saved_fixture(tmp_path,monkeypatch)
    digest={"numeric.py":"before"}
    monkeypatch.setattr(compare,"source_hashes",lambda:dict(digest))
    def changed(*_):
        digest["numeric.py"]="after"
        return report
    monkeypatch.setattr(audit,"audit_saved_condition",changed)
    with pytest.raises(ValueError,match="source changed"):
        compare.run(tmp_path/"bar",root,output)
    assert not output.exists()
