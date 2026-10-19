"""Bounded multi-PBS metadata fixtures; no production sampling or scheduler."""
from collections import defaultdict
from copy import deepcopy
import json
import shlex
from pathlib import Path
import sys
from types import SimpleNamespace
import pytest
for dependency in ("ldpc", "bposd", "pymatching"):
    pytest.importorskip(dependency)
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"cluster_scripts"))
import calibration as c
import tile_low_noise_sampling_partitions as p
import submit_tile_low_noise_sampling_partitions as submit


def completed_fixture(root, monkeypatch):
    """All 192 replicates/768 groups, with explicitly synthetic one-rung metadata."""
    plan=p.low.make_plan(0,0,capacity=False)
    plan["condition"]["chains"]=1
    plan["condition"]["rungs"]=plan["condition"]["rungs"][:1]
    resources={}
    for phase in p.PHASES:
        per_rep=4 if phase=="sample" else 1
        parts=[dict(index=i,replicate_range=[i*96,(i+1)*96],tasks=96*per_rep,
                    predicted_seconds=1.,wall_seconds=1800,walltime="00:30:00") for i in range(2)]
        resources[phase]=dict(workers=96,cpus=96,memory_gb=32,requested_nodes=1,max_nodes=2,partitions=parts)
    wrapper=dict(production=plan,resources=resources,source_sha256={"fixture":"fixed"})
    monkeypatch.setattr(p,"read_plan",lambda _:wrapper)
    monkeypatch.setattr(p,"source_hashes",lambda:{"fixture":"fixed"})
    monkeypatch.setattr(submit,"bundle_binding",lambda *args:{"fixture":"fixed"})
    monkeypatch.setattr(p.low.native.trace_audit,"validate_platform",lambda *args:None)
    root.mkdir(parents=True,exist_ok=True)
    for name,value in (("manifest.json",plan),("sampling_partition_manifest.json",wrapper),
                       ("platform_profile.json",{}),("platform_fixture.json",{})):
        c.atomic_json(root/name,value)
    for phase in p.PHASES:
        c.atomic_json(root/f"{phase}-execution-intent.json",dict(mode="partitioned",phase=phase,
                      manifest=c.digest(plan),partition_manifest=c.digest(wrapper)))
    tasks=[]; groups=defaultdict(list); anchors={}; jobs=[]; phase_counts={}
    for phase in (*p.PHASES,"collect"):
        indices=range(2) if phase!="collect" else [None]
        for index in indices:
            sub=p.submission_directory(root,phase,index); sub.mkdir(parents=True)
            script=sub/"partition.sh";script.write_text("#!/bin/bash\ntrue\n")
            job=f"{100+len(jobs)}.cluster" if phase!="collect" else "200.cluster"
            resource=p.partition_resource(wrapper,phase,index)
            ledger=dict(manifest=c.digest(wrapper),phase=phase,partition=index,resource=resource,
                        command=["qsub",str(script)],script_sha256=c.file_hash(script),bundle=str(root.parent),
                        bundle_binding={"fixture":"fixed"})
            c.atomic_json(sub/"submission-intent.json",ledger)
            c.atomic_json(sub/"submission.json",dict(ledger,job_id=job))
            terminal=dict(job_id=job,job=dict(job_state="F",Exit_status=2 if phase!="collect" else 0,
                Submit_arguments=shlex.quote(str(script)),Resource_List=dict(select=f"1:ncpus={resource['cpus']}:mem=32gb",walltime=resource["walltime"])))
            c.atomic_json(sub/"terminal.json",terminal)
            if phase=="collect":continue
            selected=p.tasks_for_partition(wrapper,phase,index)
            directory=p.partition_directory(root,phase,index);directory.mkdir(parents=True)
            intent=dict(manifest=c.digest(plan),partition_manifest=c.digest(wrapper),phase=phase,partition=index,
                        tasks=len(selected),task_digest=c.digest(selected),resource=resource,pbs_job_id=job,hostname="fixture",
                        submission_sha256=c.file_hash(sub/"submission.json"))
            c.atomic_json(directory/"execution-intent.json",intent)
            native={key:intent[key] for key in ("manifest","pbs_job_id","hostname")}|dict(profile={})
            c.atomic_json(directory/"native_preflight.json",native)
            records=[];markers={}
            for task in selected:
                row=dict(task=list(task),status="failed",wall_seconds=1.,cpu_seconds=1.,peak_rss_mb=1.)
                if phase=="anchors":row["error"]="synthetic recorded task failure"
                records.append(row);markers[c.task_id(task)]="marker-"+c.task_id(task)
                tasks.append(dict(phase=phase,partition=index,task=list(task),status="failed",
                    sha256={".done.json":markers[c.task_id(task)],".json":"record",".npz":"payload"}))
                if phase=="sample":groups[c.task_id(task[:5])].append(row)
                else:anchors[c.task_id(task)]=c.digest(row)
            records.sort(key=lambda row:row["task"])
            c.atomic_json(directory/"summary.json",dict(**intent,complete=True,completion_class="recorded_task_failures",exit_status=2,
                records=records,failed=len(records),observed_tasks=len(records),missing_tasks=0,marker_sha256=markers,errors=[],
                native_preflight_sha256=c.file_hash(directory/"native_preflight.json"),
                execution_intent_sha256=c.file_hash(directory/"execution-intent.json"),phase_wall_seconds=2.))
            jobs.append(dict(phase=phase,index=index,job_id=job,exit_status=2,completion_class="recorded_task_failures"))
        if phase!="collect":
            count=sum(1 for _ in p.low.tasks(plan,phase));phase_counts[phase]=dict(tasks=count,failed=count)
    phase_counts["sample"]["group_record_digests"]={key:c.digest(sorted(rows,key=lambda row:row["task"][5:])) for key,rows in groups.items()}
    phase_counts["anchors"]["record_digests"]=anchors
    directory=root/"sampling-collection";directory.mkdir()
    sub=p.submission_directory(root,"collect",None)
    intent=dict(mode="partitioned_sampling_collection",manifest=c.digest(plan),partition_manifest=c.digest(wrapper),
                pbs_job_id="200.cluster",hostname="fixture",resource=p.partition_resource(wrapper,"collect",None),
                submission_sha256=c.file_hash(sub/"submission.json"))
    c.atomic_json(directory/"execution-intent.json",intent)
    c.atomic_json(directory/"native_preflight.json",{key:intent[key] for key in ("manifest","pbs_job_id","hostname")}|dict(profile={}))
    with (directory/"tasks.jsonl").open("wb") as stream:
        for row in tasks:stream.write(c.canonical(row)+b"\n")
    summary=dict(**intent,complete=True,errors=[],records=phase_counts,pbs_jobs=jobs,source_sha256=p.source_hashes(),
                 input_sha256={name:c.file_hash(root/name) for name in p.proof_paths(wrapper)},
                 native_preflight_sha256=c.file_hash(directory/"native_preflight.json"),
                 execution_intent_sha256=c.file_hash(directory/"execution-intent.json"),tasks_sha256=c.file_hash(directory/"tasks.jsonl"))
    c.atomic_json(directory/"summary.json",summary)
    return plan,wrapper


def test_full_cohort_metadata_keeps_failed_denominators(tmp_path,monkeypatch):
    plan,wrapper=completed_fixture(tmp_path,monkeypatch)
    result=p.completed_partition_evidence(tmp_path,plan)
    assert result["sample"]["tasks"]==result["sample"]["failed"]==768
    assert result["anchors"]["tasks"]==result["anchors"]["failed"]==192
    assert len(result["sample"]["group_record_digests"])==768
    assert len(result["anchors"]["record_digests"])==192
    assert result["collector_pbs_job"]["job_id"]=="200.cluster" and len(result["pbs_jobs"])==4
    assert result["raw_payloads_rehashed"] is False


@pytest.mark.parametrize("name",["sampling-partitions/sample/0/summary.json","sampling-submissions/anchors/0/partition.sh",
                                 "sampling-collection/tasks.jsonl","sampling-collection-submission/terminal.json"])
def test_changed_completed_input_rejected(tmp_path,monkeypatch,name):
    plan,wrapper=completed_fixture(tmp_path,monkeypatch)
    path=tmp_path/name
    path.write_text(path.read_text()+" ")
    if name.endswith("terminal.json"):
        value=p.read_json(path);value["job"]["Exit_status"]=1;c.atomic_json(path,value)
    with pytest.raises(ValueError):p.completed_partition_evidence(tmp_path,plan)


def test_terminal_receipt_rejects_running_without_saving(tmp_path,monkeypatch):
    plan,wrapper=completed_fixture(tmp_path,monkeypatch)
    path=p.submission_directory(tmp_path,"sample",0)/"terminal.json";path.unlink()
    runner=lambda *args,**kwargs:SimpleNamespace(stdout=json.dumps({"Jobs":{"102.cluster":dict(job_state="R")}}))
    with pytest.raises(ValueError):p.partition_evidence(tmp_path,wrapper,"sample",0,runner=runner)
    assert not path.exists()


def test_routing_reservation_blocks_old_runner_before_preflight(tmp_path,monkeypatch):
    plan,wrapper=completed_fixture(tmp_path,monkeypatch)
    monkeypatch.setenv("PBS_JOBID","300.cluster")
    for key,value in p.low.native.THREADS.items():monkeypatch.setenv(key,value)
    monkeypatch.setattr(p.low.native,"native_preflight",lambda *args:pytest.fail("old native ran"))
    monkeypatch.setattr(p.low,"make_plan",lambda *args,**kwargs:plan)
    with pytest.raises(FileExistsError):p.low.run_phase(tmp_path,plan,"sample",96)


def test_collector_terminal_strips_environment(tmp_path,monkeypatch):
    plan,wrapper=completed_fixture(tmp_path,monkeypatch)
    path=p.submission_directory(tmp_path,"collect",None)/"terminal.json"
    value=p.read_json(path);path.unlink();value["job"]["Variable_List"]={"secret":"unused"}
    runner=lambda *args,**kwargs:SimpleNamespace(stdout=json.dumps({"Jobs":{value["job_id"]:value["job"]}}))
    p.collector_terminal(tmp_path,wrapper,runner=runner)
    assert "Variable_List" not in p.read_json(path)["job"]


def fresh_run_fixture(root,monkeypatch):
    plan=p.low.make_plan(0,0,capacity=False)
    plan["native_input_digests"]={}
    selected=[(0,0,0,0,0,0,0),(0,0,0,0,0,0,1)]
    wrapper=dict(production=plan,resources=dict(sample=dict(workers=2,cpus=96,memory_gb=32,requested_nodes=1,max_nodes=2,
                   partitions=[dict(wall_seconds=1800,walltime="00:30:00")])))
    monkeypatch.setattr(p,"read_plan",lambda _:wrapper)
    monkeypatch.setattr(p,"tasks_for_partition",lambda *args:selected)
    monkeypatch.setattr(p,"submission_evidence",lambda *args,**kwargs:{"job_id":"20.cluster"})
    sub=p.submission_directory(root,"sample",0);sub.mkdir(parents=True)
    c.atomic_json(sub/"submission.json",{"job_id":"20.cluster"})
    monkeypatch.setenv("PBS_JOBID","20.cluster")
    for key,value in p.low.native.THREADS.items():monkeypatch.setenv(key,value)
    monkeypatch.setattr(p.low.t,"build_problem",lambda *args:(None,None))
    def native(directory,plan):
        c.atomic_json(directory/"native_preflight.json",dict(manifest=c.digest(plan),pbs_job_id="20.cluster",hostname="fixture",profile={}))
        return c.file_hash(directory/"native_preflight.json")
    monkeypatch.setattr(p.low.native,"native_preflight",native)
    records={task:dict(task=list(task),status="failed",wall_seconds=1.,cpu_seconds=1.,peak_rss_mb=1.) for task in selected}
    monkeypatch.setattr(p,"artifact_record",lambda root,plan,phase,task,problem:(records[task],{".done.json":"marker"}))
    monkeypatch.setattr(c,"parallel_map",lambda *args:list(records.values()))
    return wrapper,selected,records


def test_run_all_recorded_failures_exit_two_and_preserved(tmp_path,monkeypatch):
    wrapper,selected,records=fresh_run_fixture(tmp_path,monkeypatch)
    result=p.run_partition(tmp_path,"sample",0)
    assert result["complete"] and result["failed"]==2 and result["exit_status"]==2
    with pytest.raises(ValueError,match="existing"):p.run_partition(tmp_path,"sample",0)


def test_pool_crash_preserves_existing_outcome_without_inventing_missing(tmp_path,monkeypatch):
    wrapper,selected,records=fresh_run_fixture(tmp_path,monkeypatch)
    base=tmp_path/"traces"/c.task_id(selected[0]);base.parent.mkdir()
    def crash(*args):
        c.atomic_json(base.with_suffix(".done.json"),{})
        raise RuntimeError("pool crashed after first saved outcome")
    monkeypatch.setattr(c,"parallel_map",crash)
    result=p.run_partition(tmp_path,"sample",0)
    assert result["exit_status"]==1 and not result["complete"]
    assert result["observed_tasks"]==1 and result["failed"]==1 and result["missing_tasks"]==1


def test_terminal_context_failure_still_saves_every_outcome(tmp_path,monkeypatch):
    wrapper,selected,records=fresh_run_fixture(tmp_path,monkeypatch)
    calls=[]
    def changed(_):
        calls.append(1)
        if len(calls)>1:raise ValueError("changed source")
        return wrapper
    monkeypatch.setattr(p,"read_plan",changed)
    result=p.run_partition(tmp_path,"sample",0)
    assert result["exit_status"]==1 and result["observed_tasks"]==2 and result["missing_tasks"]==0
    assert (tmp_path/"sampling-partitions/sample/0/summary.json").exists()


def collection_fixture(root,monkeypatch):
    plan,wrapper=completed_fixture(root,monkeypatch)
    directory=root/"sampling-collection"
    original=p.read_json(directory/"summary.json")
    # Preserve the synthetic completed metadata separately to exercise a fresh collector.
    directory.rename(root/"fixture-completed-metadata")
    monkeypatch.setenv("PBS_JOBID","200.cluster")
    for key,value in p.low.native.THREADS.items():monkeypatch.setenv(key,value)
    monkeypatch.setattr(p.low.t,"build_problem",lambda *args:(None,None))
    def native(directory,plan):
        c.atomic_json(directory/"native_preflight.json",dict(manifest=c.digest(plan),pbs_job_id="200.cluster",hostname=p.socket.gethostname(),profile={}))
        return c.file_hash(directory/"native_preflight.json")
    monkeypatch.setattr(p.low.native,"native_preflight",native)
    rows={}
    for phase in p.PHASES:
        for index in range(2):
            for row in p.read_json(p.partition_directory(root,phase,index)/"summary.json")["records"]:
                rows[tuple(row["task"]),phase]=row
    def artifact(root,plan,phase,task,problem):
        return rows[tuple(task),phase],{".done.json":"marker-"+c.task_id(task),".json":"record",".npz":"payload"}
    monkeypatch.setattr(p,"artifact_record",artifact)
    real_hash=c.file_hash
    def file_hash(path):
        path=Path(path)
        if path.parent.name in ("traces","anchors"):
            if path.name.endswith(".done.json"):return "marker-"+path.name.removesuffix(".done.json")
            return "record" if path.suffix==".json" else "payload"
        return real_hash(path)
    monkeypatch.setattr(c,"file_hash",file_hash)
    def runner(command,**kwargs):
        job=command[-1]
        for phase in p.PHASES:
            for index in range(2):
                value=p.read_json(p.submission_directory(root,phase,index)/"terminal.json")
                if value["job_id"]==job:return SimpleNamespace(stdout=json.dumps({"Jobs":{job:value["job"]}}))
        raise ValueError("unknown synthetic job")
    return plan,wrapper,original,runner,artifact


def test_full_collect_and_real_reader_preserve_all_failed_groups(tmp_path,monkeypatch):
    plan,wrapper,original,runner,artifact=collection_fixture(tmp_path,monkeypatch)
    result=p.collect(tmp_path,runner=runner)
    assert result["complete"] and result["records"]==original["records"]
    evidence=p.completed_partition_evidence(tmp_path,plan)
    assert evidence["sample"]["failed"]==768 and evidence["anchors"]["failed"]==192


def test_collection_proof_change_retains_all_outcomes_but_fails(tmp_path,monkeypatch):
    plan,wrapper,original,runner,artifact=collection_fixture(tmp_path,monkeypatch)
    called=[]
    def changed(*args):
        result=artifact(*args)
        if not called:
            path=p.partition_directory(tmp_path,"anchors",0)/"summary.json"
            path.write_text(path.read_text()+" ");called.append(True)
        return result
    monkeypatch.setattr(p,"artifact_record",changed)
    with pytest.raises(RuntimeError,match="incomplete"):p.collect(tmp_path,runner=runner)
    result=p.read_json(tmp_path/"sampling-collection/summary.json")
    assert not result["complete"] and result["records"]==original["records"]


@pytest.mark.parametrize("name",["sampling-collection/summary.json","sampling-collection/tasks.jsonl",
                                 "sampling-collection-submission/terminal.json"])
def test_consumed_collection_metadata_change_rejected(tmp_path,monkeypatch,name):
    plan,wrapper=completed_fixture(tmp_path,monkeypatch)
    original=p.partition_evidence
    def changed(root,wrapper,phase,index,**kwargs):
        result=original(root,wrapper,phase,index,**kwargs)
        if phase=="sample" and index==1:
            path=root/name;path.write_text(path.read_text()+" ")
        return result
    monkeypatch.setattr(p,"partition_evidence",changed)
    with pytest.raises(ValueError,match="changed while reading"):
        p.completed_partition_evidence(tmp_path,plan)


def test_same_hash_resolved_target_change_rejected(tmp_path,monkeypatch):
    path=tmp_path/"metadata.json";path.write_text("{}")
    initial=p.snapshot_paths(tmp_path,["metadata.json"])
    # Windows may lack symlink privilege; model only the resolved-target observation.
    real_resolve=Path.resolve
    def resolve(self,*args,**kwargs):
        if self==path:return tmp_path/"same-bytes-elsewhere.json"
        return real_resolve(self,*args,**kwargs)
    monkeypatch.setattr(Path,"resolve",resolve)
    with pytest.raises(ValueError,match="changed while reading"):p.verify_snapshot(tmp_path,initial)
