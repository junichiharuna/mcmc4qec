"""Multi-PBS analysis keeps the complete cohort and explicit provenance."""
from copy import deepcopy
import json
from pathlib import Path
import sys

import pytest

pytest.importorskip("ldpc")
pytest.importorskip("bposd")
pytest.importorskip("pymatching")
sys.path.insert(0, str(Path(__file__).resolve().parents[1]/"cluster_scripts"))
import calibration as c
import tile_low_noise_partitioned_analysis as m
from test_tile_low_noise_analysis_partitions import fixture_plan, rows_fixture, raw_group_fixture


@pytest.fixture(autouse=True)
def pinned_threads(monkeypatch):
    for key, value in m.low.native.THREADS.items(): monkeypatch.setenv(key, value)


def prepared(tmp_path, monkeypatch):
    plan, resource = fixture_plan()
    root, capacity = tmp_path/"production", tmp_path/"capacity"
    root.mkdir(); capacity.mkdir()
    c.atomic_json(root/"manifest.json", plan)
    c.atomic_json(root/"sampling-proof.json", {"complete": True})
    evidence = dict(mode="partitioned_sampling", sample={"tasks": 122880, "failed": 0},
                    anchors={"tasks": 192, "failed": 0},
                    input_sha256={"sampling-proof.json": c.file_hash(root/"sampling-proof.json")},
                    source_sha256={}, pbs_jobs=[{"job_id": "1.fixture"}])
    c.atomic_json(capacity/"manifest.json", {"production": plan})
    monkeypatch.setattr(m.a, "read_production_plan", lambda _: plan)
    monkeypatch.setattr(m, "sampling_evidence", lambda *_: deepcopy(evidence))
    monkeypatch.setattr(m.cap, "measured_profile", lambda *_: resource)
    monkeypatch.setattr(m.a, "completed_phase_evidence", lambda *_: pytest.fail("legacy singleton reader"))
    return root, capacity, plan, evidence


def test_create_read_explicit_multi_pbs_plan_and_no_replacement(tmp_path, monkeypatch):
    root, capacity, plan, evidence = prepared(tmp_path, monkeypatch)
    wrapper = m.create_plan(root, capacity)
    assert wrapper["analysis_context"]["completed_phase_evidence"] == evidence
    assert m.read_plan(root) == wrapper
    reservation = json.loads((root/"analysis-execution-intent.json").read_text())
    assert reservation["mode"] == "partitioned" and "pbs_job_id" not in reservation
    with pytest.raises(ValueError, match="existing"):
        m.create_plan(root, capacity)


@pytest.mark.parametrize("change", ["input", "source", "receipt", "mode"])
def test_changed_metadata_rejected(tmp_path, monkeypatch, change):
    root, capacity, plan, evidence = prepared(tmp_path, monkeypatch)
    m.create_plan(root, capacity)
    if change == "input": c.atomic_json(root/"sampling-proof.json", {"changed": True})
    elif change == "receipt": evidence["pbs_jobs"][0]["job_id"] = "2.fixture"
    elif change == "mode": evidence["mode"] = "singleton"
    else: monkeypatch.setattr(m, "source_hashes", lambda: {"changed": "source"})
    with pytest.raises(ValueError): m.read_plan(root)


def test_group_reader_reuses_real_saved_artifact(tmp_path):
    wrapper, group, _, _ = raw_group_fixture(tmp_path)
    record, digest = m.p.read_group(tmp_path, wrapper, group)
    assert digest and len(record["rows"]) == 4 and record["failed_tasks"]


def cohort(tmp_path, monkeypatch):
    root, capacity, plan, evidence = prepared(tmp_path, monkeypatch)
    plan["condition"]["windows"] = [8]
    plan.update(burns=[0], blocks=[2], chain_counts=[4])
    c.atomic_json(capacity/"manifest.json", {"production": plan})
    m.cap.measured_profile(None, None)["production_manifest"] = c.digest(plan)
    wrapper = m.create_plan(root, capacity)
    monkeypatch.setattr(m, "read_plan", lambda _: wrapper)
    monkeypatch.setattr(m, "partition_evidence", lambda *args: ({}, "partition-proof"))
    def records(*args):
        for part in wrapper["resources"]["partitions"]:
            for group in part["groups"]:
                yield dict(rows=rows_fixture(plan, tuple(group)), failed_tasks=[["retained"]]), part["index"], "partition-proof"
    monkeypatch.setattr(m, "validated_groups", records)
    return root, wrapper


def test_full_denominator_and_iterator_terminal_validation(tmp_path, monkeypatch):
    root, wrapper = cohort(tmp_path, monkeypatch)
    monkeypatch.setenv("PBS_JOBID", "8.fixture")
    result = m.collect(root)
    assert result["groups"] == result["failed_sampling_groups"] == 768
    assert result["rows"] == result["unavailable_intervals"] == result["undefined_diagnostics"] == 3072
    plan, rows, summary = m.read_collection(root)
    assert len(list(rows)) == 3072 and summary == result
    with pytest.raises(FileExistsError): m.collect(root)


@pytest.mark.parametrize("change", ["count", "extra_row", "input_after_first_row"])
def test_collection_terminal_rejects_changes(tmp_path, monkeypatch, change):
    root, wrapper = cohort(tmp_path, monkeypatch)
    monkeypatch.setenv("PBS_JOBID", "8.fixture")
    m.collect(root)
    summary_path = root/"partition-collection/summary.json"
    if change == "count":
        value = json.loads(summary_path.read_text()); value["rows"] -= 1; c.atomic_json(summary_path, value)
    elif change == "extra_row":
        path = root/"partition-collection/rows.jsonl"
        with path.open("ab") as stream: stream.write(b"{}\n")
        value = json.loads(summary_path.read_text()); value["rows_sha256"] = c.file_hash(path); c.atomic_json(summary_path, value)
    _, rows, _ = m.read_collection(root)
    if change == "input_after_first_row":
        next(rows); c.atomic_json(root/"sampling-proof.json", {"changed": True})
    with pytest.raises(ValueError): list(rows)


def test_run_and_collect_require_pbs_before_work(tmp_path, monkeypatch):
    monkeypatch.delenv("PBS_JOBID", raising=False)
    with pytest.raises(ValueError, match="PBS"): m.run_partition(tmp_path, {}, 0)
    with pytest.raises(ValueError, match="PBS"): m.collect(tmp_path)


def terminal_fixture(tmp_path, monkeypatch):
    root, capacity, plan, evidence = prepared(tmp_path, monkeypatch)
    wrapper = m.create_plan(root, capacity)
    execution, destination = root/"analysis-partitions/0", root/"analysis-submissions/0"
    execution.mkdir(parents=True); destination.mkdir(parents=True)
    for name in ("summary.json", "execution-intent.json", "native_preflight.json"):
        c.atomic_json(execution/name, {"fixture": name})
    monkeypatch.setattr(m.p, "partition_evidence", lambda *_: ({"pbs_job_id": "123.fixture"}, "summary-proof"))
    script = destination/"partition.sh"; script.write_text("reviewed script")
    fixed, part = wrapper["resources"], wrapper["resources"]["partitions"][0]
    resource = dict(cpus=96, memory_gb=fixed["memory_gb"], workers=fixed["workers"],
                    wall_seconds=part["wall_seconds"], walltime=part["walltime"], requested_nodes=1, max_nodes=2)
    binding = dict(source_sha256={Path(name).name: digest for name,digest in wrapper["source_sha256"].items()},
                   package_sha256=plan["runtime"]["package_sha256"], python_path=str(Path(sys.executable).resolve()),
                   python_sha256=c.file_hash(sys.executable))
    record = dict(partition_manifest=c.digest(wrapper), partition=0, manifest=c.digest(plan),
                  command=["qsub", str(script)], script_sha256=c.file_hash(script), resource=resource, bundle_binding=binding)
    c.atomic_json(destination/"submission-intent.json", record)
    c.atomic_json(destination/"submission.json", dict(record, job_id="123.fixture"))
    terminal = dict(Jobs={"123.fixture": dict(job_state="F", Exit_status=0, Submit_arguments=str(script),
        Resource_List=dict(select=f"1:ncpus=96:mem={resource['memory_gb']}gb", ncpus=96,
                           mem=f"{resource['memory_gb']*1024}mb", walltime=resource["walltime"]))})
    c.atomic_json(destination/"terminal.json", terminal)
    return root, wrapper, destination, terminal


@pytest.mark.parametrize("change", [None, "job", "exit", "wall", "memory", "script", "bundle"])
def test_analysis_partition_terminal_binding(tmp_path, monkeypatch, change):
    root, wrapper, destination, terminal = terminal_fixture(tmp_path, monkeypatch)
    job = terminal["Jobs"]["123.fixture"]
    if change == "job": terminal["Jobs"] = {"999.fixture": job}
    elif change == "exit": job["Exit_status"] = 1
    elif change == "wall": job["Resource_List"]["walltime"] = "24:00:00"
    elif change == "memory": job["Resource_List"]["mem"] = "1gb"
    elif change == "script": (destination/"partition.sh").write_text("changed")
    elif change == "bundle":
        for name in ("submission.json", "submission-intent.json"):
            value = json.loads((destination/name).read_text()); value["bundle_binding"]["package_sha256"] = "wrong"
            c.atomic_json(destination/name, value)
    c.atomic_json(destination/"terminal.json", terminal)
    if change:
        with pytest.raises(ValueError): m.partition_evidence(root, wrapper, 0)
    else:
        assert m.partition_evidence(root, wrapper, 0)[1] == "summary-proof"


@pytest.mark.parametrize("mutate", [False, True])
def test_actual_short_group_through_new_runner(tmp_path, monkeypatch, mutate):
    from test_tile_low_noise_analysis import short_group
    plan, group = short_group(tmp_path)
    _, records, anchor, _ = m.a.load_group(tmp_path, plan, group)
    reduced = [{key: records[index][key] for key in ("task", "status", "wall_seconds", "cpu_seconds", "peak_rss_mb")}
               for index in sorted(records)]
    c.atomic_json(tmp_path/"sampling-proof.json", {"fixed": True})
    evidence = dict(mode="partitioned_sampling", pbs_jobs=[{"job_id": "1.fixture"}], source_sha256={},
        input_sha256={"sampling-proof.json": c.file_hash(tmp_path/"sampling-proof.json")},
        sample={"group_record_digests": {c.task_id(group): c.digest(reduced)}},
        anchors={"record_digests": {c.task_id(anchor["task"]): c.digest(anchor)}})
    context = m.a.analysis_context(plan, evidence)
    wrapper = dict(production=plan, analysis_context=context, source_sha256=m.source_hashes(),
                   resources=dict(workers=1, partitions=[dict(index=0, groups=[list(group)])]))
    for name,value in (("manifest", plan), ("analysis_manifest", context), ("partition_analysis_manifest", wrapper),
                       ("analysis-execution-intent", {"fixture": True})):
        c.atomic_json(tmp_path/(name+".json"), value)
    for key,value in m.low.native.platform_inputs().items(): c.atomic_json(tmp_path/(key+".json"), value)
    monkeypatch.setattr(m, "read_plan", lambda _: wrapper)
    monkeypatch.setattr(m.low.native, "native_preflight", lambda *_: "explicit-native-fixture")
    def parallel(function, jobs, workers):
        result = [function(job) for job in jobs]
        if mutate: c.atomic_json(tmp_path/"sampling-proof.json", {"changed": True})
        return result
    monkeypatch.setattr(c, "parallel_map", parallel)
    monkeypatch.setenv("PBS_JOBID", "8.fixture")
    if mutate:
        with pytest.raises(ValueError, match="changed"): m.run_partition(tmp_path, wrapper, 0)
        assert not (tmp_path/"analysis-partitions/0/summary.json").exists()
    else:
        result = m.run_partition(tmp_path, wrapper, 0)
        record, _ = m.p.read_group(tmp_path, wrapper, group)
        assert result["rows"] == len(record["rows"]) == 4
        with pytest.raises(ValueError, match="existing"): m.run_partition(tmp_path, wrapper, 0)
