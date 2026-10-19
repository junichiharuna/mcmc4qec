"""Saved final reports feed the unchanged candidate policy without raw scans."""
import json
from pathlib import Path
import sys

import pytest

for dependency in ("ldpc", "bposd", "pymatching"):
    pytest.importorskip(dependency)
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "cluster_scripts"))
import calibration as c
import tile_bar_study as b
import tile_select_timing as select
import tile_timing_selection_from_final as adapter
from test_tile_select_timing import reports


def dump(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    c.atomic_json(path, value)


def refresh(root):
    proof = json.loads((root / "recovery.json").read_text())
    for value in proof["files"].values():
        value["sha256"] = c.file_hash(root / value["member"])
    dump(root / "recovery.json", proof)
    return c.file_hash(root / "recovery.json")


@pytest.fixture
def complete(tmp_path):
    production = b.make_plan()
    assessments = reports(production)
    cases = []
    for case in range(4):
        root = tmp_path / str(case)
        remote = f"/frozen/run-{case}"
        phase_names = ["audited", "comparisons", "precision", "weight"] + (["strata"] if case > 1 else [])
        files = {}
        def put(original, member, value):
            dump(root / member, value)
            files[original] = dict(member=member, sha256=c.file_hash(root / member))
        def runfile(name, value): put(remote + "/" + name, "run/" + name, value)
        input_paths = {}
        for name, value in (("manifest.json", production), ("analysis_manifest.json", {"identity": "shared"}),
                            ("reference_summary.json", {"reference": "shared"}), (f"summary-{case}.json", {})):
            original = "/production/" + name
            put(original, "inputs/" + name, value)
            input_paths[original] = files[original]["sha256"]
        context=dict(sampling_manifest=c.digest(production),reference_summary_sha256=input_paths["/production/reference_summary.json"])
        put("/production/analysis_manifest.json","inputs/analysis_manifest.json",context)
        input_paths["/production/analysis_manifest.json"]=files["/production/analysis_manifest.json"]["sha256"]
        sources = {}
        for name in set(adapter.PHASE_SOURCES.values()) | {"tile_summary.py", "tile_final_reaggregation.py"}:
            path = Path(c.__file__).parent / name
            member = "sources/" + name
            (root / member).parent.mkdir(parents=True, exist_ok=True)
            (root / member).write_bytes(path.read_bytes())
            files["/frozen/cluster_scripts/" + name] = dict(member=member, sha256=c.file_hash(path))
            sources[name] = c.file_hash(path)
        state = dict(production=production, sampling_manifest=c.digest(production), analysis_context=c.digest(context),
                     trace_audit_manifest="audit", input_sha256=input_paths, source_sha256=sources, rows_sha256="a"*64)
        plan = dict(schema=1, purpose="final_calibration_reaggregation", case=case, replicates=192, groups=768,
                    production_root="/production", phases=phase_names, snapshot=state)
        manifest = c.digest(plan)
        job = str(10 + case) + ".server"
        script = "#!/bin/bash\ntrue\n"
        (root / "run").mkdir(exist_ok=True)
        (root / "run/reaggregate.sh").write_text(script)
        files[remote+"/reaggregate.sh"] = dict(member="run/reaggregate.sh", sha256=c.file_hash(root/"run/reaggregate.sh"))
        intent = dict(command=["qsub",remote+"/reaggregate.sh"],manifest=manifest,
                      script_sha256=c.file_hash(root/"run/reaggregate.sh"))
        ledger = dict(intent,job_id=job)
        execution = dict(manifest=manifest,pbs_job_id=job)
        runfile("manifest.json", plan)
        runfile("submission-intent.json", intent)
        runfile("submission.json", ledger)
        runfile("execution-intent.json", execution)
        precision = assessments[case]
        precision.update(schema=1,purpose="empirical_relative_precision_assessment",source_sha256=sources["tile_precision_assessment.py"],
            summary_source_sha256=sources["tile_summary.py"],input_sha256=dict(
                sampling=input_paths["/production/manifest.json"],analysis=input_paths["/production/analysis_manifest.json"],
                reference=input_paths["/production/reference_summary.json"],summary=input_paths[f"/production/summary-{case}.json"],rows="a"*64))
        audited = dict(schema=1,purpose="audited_calibration_results",case=case,replicates=192,groups=768,conditions=352,
            sampling_manifest=state["sampling_manifest"],analysis_context=state["analysis_context"],trace_audit_manifest="audit",
            records=[dict(row["condition"],**row["assessment"]["metrics"]) for row in precision["records"]],
            source_sha256=sources["tile_audited_results.py"],historical_consumed_input_hashes_recorded=False,
            bar_bootstrap_recomputed=False,all_physical_states_redecoded=False,current_archived_inputs_match_audited_inputs=True,
            terminal_payload_stat_checked=True)
        phase_reports = dict(audited=audited,precision=precision)
        outcomes = []
        for phase in phase_names:
            report = phase_reports.get(phase,dict(case=case,conditions=352,source_sha256=sources[adapter.PHASE_SOURCES[phase]]))
            runfile(f"phases/{phase}.json", report)
            output_sha = files[remote+f"/phases/{phase}.json"]["sha256"]
            measure = dict(phase=phase,status="ok",manifest=manifest,pbs_job_id=job,output_sha256=output_sha)
            if phase != "audited": measure["adapter_sha256"]=files[remote+"/phases/audited.json"]["sha256"]
            runfile(f"phases/{phase}.measurement.json",measure)
            outcome = dict(phase=phase,status="ok",returncode=0,output_sha256=output_sha,measurement=measure,
                           measurement_sha256=files[remote+f"/phases/{phase}.measurement.json"]["sha256"])
            runfile(f"phases/{phase}.outcome.json",outcome)
            runfile(f"phases/{phase}.request.json",dict(phase=phase,manifest=manifest,pbs_job_id=job))
            outcomes.append(outcome)
        summary = dict(case=case,manifest=manifest,pbs_job_id=job,replicates=192,groups=768,complete=True,
                       terminal_binding_valid=True,phase_failure=None,terminal_failure=None,records=outcomes,
                       input_snapshot=c.digest(state),execution_intent_sha256=files[remote+"/execution-intent.json"]["sha256"])
        runfile("summary.json",summary)
        proof = dict(files=files,job_id=job,manifest=manifest,problems=[],pbs=dict(job_state="F",Exit_status=0,
                     Submit_arguments=remote+"/reaggregate.sh"))
        dump(root/"recovery.json",proof)
        cases.append(dict(case=case,recovered_root=str(root),recovery_sha256=c.file_hash(root/"recovery.json")))
    return cases,production,assessments,tmp_path/"selection.json"


def test_saved_final_matches_unchanged_policy_and_no_raw_scan(complete,monkeypatch):
    cases,plan,reports,output=complete
    monkeypatch.setattr(select.p,"assess_calibration",lambda *a:pytest.fail("must reuse saved assessment"))
    result=adapter.run(cases,output)
    assert result["records"]==select.choose(plan,reports)["records"]
    assert len(result["final_audit_evidence"])==4 and len(result["records"])==8
    assert result["raw_rows_recomputed"] is False
    with pytest.raises(ValueError,match="exists"):adapter.run(cases,output)


def test_semantic_metrics_mismatch_rejected_after_rebinding_phase_hashes(complete):
    cases,_,_,output=complete
    root=Path(cases[0]["recovered_root"])
    report=json.loads((root/"run/phases/precision.json").read_text())
    report["records"][0]["assessment"]["metrics"]["point_estimates"]=191
    dump(root/"run/phases/precision.json",report)
    measure=json.loads((root/"run/phases/precision.measurement.json").read_text())
    measure["output_sha256"]=c.file_hash(root/"run/phases/precision.json")
    dump(root/"run/phases/precision.measurement.json",measure)
    outcome=json.loads((root/"run/phases/precision.outcome.json").read_text())
    outcome.update(measurement=measure,output_sha256=measure["output_sha256"],
                   measurement_sha256=c.file_hash(root/"run/phases/precision.measurement.json"))
    dump(root/"run/phases/precision.outcome.json",outcome)
    summary=json.loads((root/"run/summary.json").read_text())
    summary["records"][2]=outcome
    dump(root/"run/summary.json",summary)
    cases[0]["recovery_sha256"]=refresh(root)
    with pytest.raises(ValueError,match="metrics differ"):adapter.run(cases,output)
    assert not output.exists()


@pytest.mark.parametrize("corruption",["missing_case","duplicate_case","pin","missing_phase","payload","pbs","summary","source","input","metrics","escape"])
def test_rejects_incomplete_or_changed_evidence(complete,corruption):
    cases,_,_,output=complete
    root=Path(cases[0]["recovered_root"])
    if corruption=="missing_case":cases.pop()
    elif corruption=="duplicate_case":cases[1]=cases[0]
    elif corruption=="pin":cases[0]["recovery_sha256"]="0"*64
    elif corruption=="missing_phase":(root/"run/phases/weight.json").unlink()
    elif corruption=="payload":(root/"run/phases/precision.json").write_text("{}")
    else:
        path=root/"recovery.json"
        proof=json.loads(path.read_text())
        if corruption=="pbs":proof["pbs"]["Exit_status"]=1
        elif corruption=="escape":next(iter(proof["files"].values()))["member"]="../elsewhere"
        else:
            names=dict(summary="run/summary.json",source="sources/tile_summary.py",input="inputs/reference_summary.json",metrics="run/phases/audited.json")
            changed=root/names[corruption]
            if corruption=="source":changed.write_text("changed")
            else:
                value=json.loads(changed.read_text())
                if corruption=="summary":value["complete"]=False
                elif corruption=="input":value["reference"]="different"
                else:value["records"][0]["point_estimates"]=191
                dump(changed,value)
        dump(path,proof)
        if corruption!="escape":cases[0]["recovery_sha256"]=refresh(root)
        else:cases[0]["recovery_sha256"]=c.file_hash(path)
    with pytest.raises((ValueError,FileNotFoundError)):adapter.run(cases,output)
    assert not output.exists()
