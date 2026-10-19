"""Explicit partitioned provenance reaches the final raw-payload join."""
import json
from pathlib import Path
import sys

import pytest

pytest.importorskip("ldpc")
pytest.importorskip("bposd")
pytest.importorskip("pymatching")
sys.path.insert(0, str(Path(__file__).resolve().parents[1]/"cluster_scripts"))
import calibration as c
import tile_low_noise_partitioned_collection as m
from test_tile_low_noise_audited_collection import fixture


def test_new_reader_consumes_iterator_terminal(tmp_path, monkeypatch):
    def iterator():
        yield {"first": True}
        raise ValueError("terminal collection check")
    monkeypatch.setattr(m.p, "read_collection", lambda _: ({}, iterator(), {}))
    with pytest.raises(ValueError, match="terminal"):
        m.read_audited_collection(tmp_path/"sampling", tmp_path/"audit")


def test_existing_real_group_payload_join_is_reused(tmp_path, monkeypatch):
    source, root, sampling, plan, row, analysis = fixture(tmp_path, monkeypatch)
    proof = m.Evidence((source, root))
    result = m.verify_group(source, root, plan, sampling, row, analysis, proof)
    assert result == dict(tasks=2, failed_sampling=0, redecoded_checkpoints=6)
    proof.finish()
    path = source/"traces"/(c.task_id((*row["group"], 0, 0))+".npz")
    path.write_bytes(path.read_bytes()+b"mutation")
    with pytest.raises(ValueError):
        m.verify_group(source, root, plan, sampling, row, analysis, m.Evidence((source, root)))


def report_fixture(tmp_path, monkeypatch):
    root, audit, reference = (tmp_path/name for name in ("sampling", "audit", "reference"))
    for path in (root, audit, reference): path.mkdir()
    for key, value in m.p.low.native.THREADS.items(): monkeypatch.setenv(key, value)
    monkeypatch.setenv("PBS_JOBID", "91.fixture")
    plan = dict(case=0, condition={"target": .01}, native_input_digests={"platform_profile": "native"})
    proof_path = root/"proof.json"; c.atomic_json(proof_path, {"valid": True})
    evidence = dict(evidence_sha256={str(proof_path): c.file_hash(proof_path)},
                    evidence_resolved_paths={str(proof_path): str(proof_path.resolve())}, failed_sampling=1)
    monkeypatch.setattr(m, "read_audited_collection", lambda *_: (plan, [{"available": False}], evidence))
    monkeypatch.setattr(m.description, "summarize_rows", lambda *_: dict(rows=1, population_rmse_certified=False))
    return root, audit, reference, plan, evidence


def test_summary_exclusive_output_and_input_mutation(tmp_path, monkeypatch):
    root, audit, reference, plan, evidence = report_fixture(tmp_path, monkeypatch)
    output = tmp_path/"report.json"
    result = m.run(root, audit, output)
    assert result["rows"] == 1 and result["audited_collection"] == evidence
    assert result["all_physical_states_redecoded"] is False
    with pytest.raises(ValueError, match="exists"): m.run(root, audit, output)
    with pytest.raises(ValueError, match="outside"): m.run(root, audit, root/"bad.json")
    def mutate(*args):
        c.atomic_json(root/"proof.json", {"changed": True}); return dict(rows=1)
    monkeypatch.setattr(m.description, "summarize_rows", mutate)
    with pytest.raises(ValueError, match="changed"): m.run(root, audit, tmp_path/"mutated.json")
    assert not (tmp_path/"mutated.json").exists()


def test_full_join_control_flow_with_explicit_io_and_group_fixtures(tmp_path,monkeypatch):
    # Group payload checks and the real collection iterator are tested separately.
    # This test exercises the 768-group orchestration, not a real full census.
    source=(tmp_path/"source").resolve();root=(tmp_path/"audit").resolve()
    sampling=dict(case=0,target_index=0,replicates=192)
    plan=dict(mode="partitioned_sampling",purpose="low_noise_trace_audit_full",case=0,target_index=0,replicates=192,workers=8,
              input_sha256={"manifest.json":"fixture"},completed_phase_evidence={"pbs_jobs":[{"job_id":"1.fixture"}],"anchors":{"record_digests":{}}})
    group_list=m.r.groups(plan)
    anchors={c.task_id((0,0,0,0,rep,0,0)):dict(task=[0,0,0,0,rep,0,0],status="failed") for rep in range(192)}
    plan["completed_phase_evidence"]["anchors"]["record_digests"]={name:c.digest(value) for name,value in anchors.items()}
    identity=dict(manifest=c.digest(plan),sampling_manifest=c.digest(sampling),workers=8,pbs_job_id="123.fixture",hostname="fixture")
    native=dict(native_platform_verified=True,fixture=True)
    summary=dict(manifest=c.digest(plan),groups=768,records=[dict(group=list(group)) for group in group_list],
                 failed_audit_groups=0,input_changes=[],context_error=None,native_platform_verified=True,
                 all_physical_states_redecoded=False,native_preflight_sha256="fixture",planned_tasks=1536,failed_sampling=768)
    ledger=dict(manifest=c.digest(plan),command=["qsub",str(root/"trace-audit.sh")],script_sha256="fixture")
    values={"summary.json":summary,"execution-intent.json":identity,"native_preflight.json":dict(identity,evidence=native),
            "platform_profile.json":{},"platform_fixture.json":{},"submission-intent.json":ledger,
            "submission.json":dict(ledger,job_id="123.fixture")}
    calls=dict(iterator=0,group=0,finish=0)
    class FixtureEvidence:
        def __init__(self,*args):self.hashes={};self.targets={}
        def track(self,path):
            self.hashes[str(path)]="fixture";self.targets[str(path)]=str(path);return "fixture"
        def read(self,path):self.track(path);return values[Path(path).name]
        def artifact(self,base,identity):return {},anchors[base.name]
        def finish(self):calls["finish"]+=1
    def collection(_):
        def iterator():
            for group in group_list:yield dict(group=list(group),available=False)
            calls["iterator"]+=1
        return sampling,iterator(),dict(rows=768)
    def group_read(_,wrapper,group):
        name=c.task_id((0,0,0,0,group[4],0,0))
        return dict(group=list(group),input_artifact_markers={"anchors/"+name:"fixture"}),"fixture"
    def verify(*args):
        calls["group"]+=1
        return dict(tasks=2,failed_sampling=1,redecoded_checkpoints=3)
    monkeypatch.setattr(m,"Evidence",FixtureEvidence)
    monkeypatch.setattr(m.r,"read_plan",lambda *args:(plan,sampling))
    monkeypatch.setattr(m.r.audit,"validate_native_environment",lambda *args,**kwargs:native)
    monkeypatch.setattr(m.p,"read_collection",collection)
    monkeypatch.setattr(m.p,"read_plan",lambda *args:dict(resources=dict(partitions=[dict(index=0)])))
    monkeypatch.setattr(m.p.p,"read_group",group_read)
    monkeypatch.setattr(m.p,"partition_evidence",lambda *args:None)
    monkeypatch.setattr(m.r,"read_terminal",lambda *args:dict(job_id="123.fixture",input_sha256={"terminal.json":"fixture"}))
    monkeypatch.setattr(m,"verify_group",verify)
    actual,rows,evidence=m.read_audited_collection(source,root)
    assert actual==sampling and len(rows)==768 and calls==dict(iterator=2,group=768,finish=1)
    assert evidence["planned_tasks"]==1536 and evidence["failed_sampling"]==768 and evidence["anchors"]==192
    assert evidence["analysis_trace_markers_matched"] and evidence["current_trace_payloads_rehashed"]
    assert not evidence["reference_audited"] and not evidence["anchor_mc_replayed"] and not evidence["all_physical_states_redecoded"]
    summary["failed_sampling"]-=1
    with pytest.raises(ValueError,match="denominator"):
        m.read_audited_collection(source,root)


@pytest.mark.parametrize("change", [None, "source", "reference_file", "prior"])
def test_bounded_reference_audited_once_and_never_full_point(tmp_path, monkeypatch, change):
    import audit_tile_weight_reference as audit
    from test_tile_low_noise_reference_comparison import inputs
    real_summary = m.description.summarize_rows
    root, audit_root, reference, _, evidence = report_fixture(tmp_path, monkeypatch)
    plan, rows, condition, context = inputs()
    c.atomic_json(reference/"manifest.json", context)
    monkeypatch.setattr(m, "read_audited_collection", lambda *_: (plan, rows, evidence))
    # Use the actual numerical helper, not the summary fixture from report_fixture.
    monkeypatch.setattr(m.description, "summarize_rows", real_summary)
    report = dict(context=context, context_digest=c.digest(context), reference_plan_digest=c.digest(context["reference"]),
        native_profile_digest=plan["native_input_digests"]["platform_profile"], native_platform_verified=True,
        raw_reference_audited=True, all_labels_redecoded=False, condition=condition,
        input_sha256={"manifest.json": c.file_hash(reference/"manifest.json")}, source_sha256=audit.source_hashes())
    calls = []
    sources = {"fixture-source": "fixed"}
    monkeypatch.setattr(m, "source_hashes", lambda: dict(sources))
    def reference_auditor(*args):
        calls.append(args[1])
        if change == "source": sources["fixture-source"] = "changed"
        if change == "reference_file": c.atomic_json(reference/"manifest.json", {"changed": True})
        return report
    monkeypatch.setattr(audit, "audit_saved_condition", reference_auditor)
    if change == "prior": condition["physical_decoder_prior"] = .02
    output = tmp_path/"reference-comparison.json"
    if change:
        with pytest.raises(ValueError): m.run(root, audit_root, output, reference_root=reference)
        assert not output.exists()
    else:
        result = m.run(root, audit_root, output, reference_root=reference)
        assert result["rows"] == len(rows) == 32 and result["raw_reference_audited"]
        assert result["reference"]["full_point_estimate"] is None
        assert result["reference"]["omitted_mass_upper"] > 0
        assert result["nominal_coverage_certified"] is result["all_physical_states_redecoded"] is False
    assert calls == [0]

