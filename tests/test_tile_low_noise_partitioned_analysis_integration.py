"""Real completed metadata reader joins BAR plans; no physical full-cohort claim."""
from copy import deepcopy
import json
from pathlib import Path
import sys

import pytest

for dependency in ("ldpc", "bposd", "pymatching"):
    pytest.importorskip(dependency)
sys.path.insert(0, str(Path(__file__).resolve().parents[1]/"cluster_scripts"))
import calibration as c
import tile_low_noise_partitioned_analysis as a
import tile_low_noise_sampling_partitions as sampling
from test_tile_low_noise_sampling_partition_evidence import completed_fixture


def joined_fixture(tmp_path, monkeypatch):
    """Keep real completed reader and BAR wrapper; fixture plan/native/capacity only."""
    root, capacity = tmp_path/"sampling", tmp_path/"capacity"
    plan, sampling_wrapper = completed_fixture(root, monkeypatch)
    # The shared fixture has synthetic one-rung records and fixed-plan/native
    # boundary stubs. Supply a real absolute source identity to the downstream
    # metadata binder; this does not claim a complete deployed closure.
    sources = {str(Path(sampling.__file__).resolve()): c.file_hash(sampling.__file__)}
    monkeypatch.setattr(sampling, "source_hashes", lambda: dict(sources))
    summary_path = root/"sampling-collection/summary.json"
    summary = json.loads(summary_path.read_bytes())
    summary["source_sha256"] = sources
    c.atomic_json(summary_path, summary)
    monkeypatch.setattr(a.low, "make_plan", lambda *_args, **_kw: deepcopy(plan))
    monkeypatch.setattr(a.a, "completed_phase_evidence", lambda *_: pytest.fail("legacy singleton reader used"))
    capacity_plan = a.cap.make_plan(plan["case"], plan["target_index"])
    capacity.mkdir()
    c.atomic_json(capacity/"manifest.json", capacity_plan)
    records = [dict(group=list(group), status="ok", synthetic=True, wall_seconds=1., peak_rss_mb=32.)
               for group in a.cap.groups(capacity_plan)]
    resource = a.cap.resource_plan(capacity_plan,
        dict(manifest=c.digest(capacity_plan), synthetic=True, tasks=len(records), failed=0, records=records))
    monkeypatch.setattr(a.cap, "measured_profile", lambda *_: deepcopy(resource))
    return root, capacity, plan, sampling_wrapper


def test_completed_reader_reaches_real_analysis_context_and_reader(tmp_path, monkeypatch):
    root, capacity, production, _ = joined_fixture(tmp_path, monkeypatch)
    wrapper = a.create_plan(root, capacity)
    proof = wrapper["analysis_context"]["completed_phase_evidence"]
    assert proof == sampling.completed_partition_evidence(root, production)
    assert proof["sample"]["tasks"] == proof["sample"]["failed"] == 768
    assert proof["anchors"]["tasks"] == proof["anchors"]["failed"] == 192
    assert len(proof["sample"]["group_record_digests"]) == 768
    assert len(proof["anchors"]["record_digests"]) == 192
    assert len(proof["pbs_jobs"]) == 4 and all(job["exit_status"] == 2 for job in proof["pbs_jobs"])
    assert proof["collector_pbs_job"] == dict(phase="collect", job_id="200.cluster", exit_status=0)
    assert proof["raw_payloads_rehashed"] is False
    groups = [tuple(group) for part in wrapper["resources"]["partitions"] for group in part["groups"]]
    assert groups == list(a.a.groups(production)) and len(groups) == 768
    assert {group[-1] for group in groups} == set(range(192))
    assert a.read_plan(root) == wrapper


@pytest.mark.parametrize("relative", ["sampling-collection-submission/terminal.json", "sampling-submissions/sample/0/partition.sh"])
def test_actual_upstream_receipt_or_script_mutation_rejected(tmp_path, monkeypatch, relative):
    root, capacity, _, _ = joined_fixture(tmp_path, monkeypatch)
    a.create_plan(root, capacity)
    path = root/relative
    if path.suffix == ".json":
        value = json.loads(path.read_bytes()); value["job"]["Exit_status"] = 1; c.atomic_json(path, value)
    else: path.write_text(path.read_text()+"\n# changed\n")
    with pytest.raises(ValueError): a.read_plan(root)


def test_metadata_only_completion_cannot_supply_absent_scientific_payloads(tmp_path, monkeypatch):
    root, capacity, _, _ = joined_fixture(tmp_path, monkeypatch)
    wrapper = a.create_plan(root, capacity)
    monkeypatch.setenv("PBS_JOBID", "999.fixture")
    for key, value in a.low.native.THREADS.items(): monkeypatch.setenv(key, value)
    monkeypatch.setattr(a.low.native, "native_preflight", lambda *_: "explicit-native-fixture")
    monkeypatch.setattr(c, "parallel_map", lambda function, jobs, workers: [function(job) for job in jobs])
    with pytest.raises(ValueError, match="missing"):
        a.run_partition(root, wrapper, 0)
    assert (root/"analysis-partitions/0/execution-intent.json").exists()
    assert not (root/"analysis-partitions/0/summary.json").exists()
    assert not (root/"partition-collection/summary.json").exists()
