"""Fixed-prior low-noise plans, logical initialization and raw task provenance."""
from copy import deepcopy
from pathlib import Path
import sys
from types import SimpleNamespace

import numpy as np
import pytest

pytest.importorskip("ldpc")
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"cluster_scripts"))
import calibration as c
import tile_study as t
import tile_low_noise_study as low


@pytest.mark.parametrize("case",range(4))
@pytest.mark.parametrize("target",range(3))
def test_fixed_grid_prior_and_capacity_strata(case,target):
    p=low.make_plan(case,target,capacity=True)
    spec=p["condition"]
    assert spec["target"]==[.01,.003,.001][target]
    assert spec["rungs"][-1]==spec["target"]
    assert set(spec["coarse"])<=set(spec["rungs"])
    tasks=list(low.tasks(p))
    assert len(tasks)==8*len(spec["rungs"])
    assert {x[5] for x in tasks}==set(range(len(spec["rungs"])))
    assert {x[6] for x in tasks}=={0,1}
    assert all(x[:2]==(case,target) for x in tasks)


def test_seed_stages_targets_purposes_and_old_driver_are_disjoint():
    seen=set()
    for capacity in (False,True):
        for target in range(3):
            p=low.make_plan(0,target,capacity=capacity)
            for phase in ("sample","anchors"):
                for rep in range(2):
                    task=(0,target,0,0,rep,0,0)
                    for purpose in (0,1):
                        seed=low.task_seed(p,task,phase,purpose)
                        assert seed not in seen
                        seen.add(seed)
                        assert seed!=t.seed((31,*task),purpose)
    assert len(seen)==48


def test_nonzero_combination_enumerates_all_binary_logicals():
    code=SimpleNamespace(lx=np.eye(3,dtype=np.uint8))
    class Fixed:
        def __init__(self,value): self.value=value
        def integers(self,low,high):
            assert (low,high)==(1,8)
            return self.value
    states=[]
    for value in range(1,8):
        state,coeff=low.logical_state(code,"bit","logical_combination",0,Fixed(value))
        assert np.array_equal(state,coeff)
        states.append(tuple(state))
    assert len(set(states))==7 and (0,0,0) not in states


def test_pauli_basis_interleaves_and_combines_into_y():
    code=SimpleNamespace(lx=np.array([[1,0]],dtype=np.uint8),lz=np.array([[1,0]],dtype=np.uint8))
    x,_=low.logical_state(code,"depolarizing","logical_basis",0,None)
    z,_=low.logical_state(code,"depolarizing","logical_basis",1,None)
    assert x.tolist()==[1,0] and z.tolist()==[3,0]
    rng=SimpleNamespace(integers=lambda low,high:3)
    y,coeff=low.logical_state(code,"depolarizing","logical_combination",0,rng)
    assert y.tolist()==[2,0] and coeff.tolist()==[1,1]


@pytest.mark.parametrize("case",range(4))
def test_actual_short_trace_has_fixed_prior_and_complete_initial_provenance(tmp_path,case):
    p=low.make_plan(case,2,capacity=True)
    p["condition"]["steps"]=8
    task=(case,2,1,1,1,len(p["condition"]["rungs"])-1,1)
    record=low.sample_task((str(tmp_path),p,task))
    assert record["status"]=="ok",record
    assert record["physical_p"]==record["decoder_prior"]==.001
    assert record["metadata"]["sampling_p"]==.001
    arrays,saved=c.load_artifact(tmp_path/"traces"/c.task_id(task),dict(manifest=c.digest(p),task=list(task)))
    assert len(arrays["weight"])==8 and np.all(arrays["sector"]>0)
    assert np.count_nonzero(arrays["initial_coefficients"])>0
    assert np.count_nonzero(arrays["initial_syndrome"])==0
    assert record["initial_sector"]>0
    assert record["checked_saved_states"]==8
    assert low.sample_task((str(tmp_path),p,task))==saved
    high_task=(*task[:5],0,task[6])
    high=low.sample_task((str(tmp_path),p,high_task))
    assert high["status"]=="ok",high
    assert high["physical_p"]==.1 and high["decoder_prior"]==.001
    assert high["problem_hash"]==record["problem_hash"]


def test_anchor_samples_high_p_with_low_target_decoder(tmp_path):
    p=low.make_plan(0,2,capacity=True)
    p["anchor_trials"]=8
    task=(0,2,0,0,0,0,0)
    record=low.anchor_task((str(tmp_path),p,task))
    assert record["status"]=="ok",record
    assert record["physical_p"]==.1 and record["decoder_prior"]==.001
    assert record["metadata"]["sampling_p"]==.1
    assert record["metadata"]["rng"]["entropy"]==record["seed"]


def test_initialization_failure_is_recorded_with_seeds(tmp_path,monkeypatch):
    p=low.make_plan(0,0,capacity=True)
    p["condition"]["steps"]=4
    monkeypatch.setattr(low,"logical_state",lambda *args:(np.zeros(72,dtype=np.uint8),np.zeros(8,dtype=np.uint8)))
    task=next(low.tasks(p))
    record=low.sample_task((str(tmp_path),p,task))
    assert record["status"]=="failed"
    assert record["init_seed"]==low.task_seed(p,task,"sample",0)
    assert record["physical_p"]==.1
    assert record["wall_seconds"]>=0


@pytest.mark.parametrize("task",[(1,0,0,0,0,0,0),(0,0,3,0,0,0,0),(0,0,0,0,0,99,0)])
def test_wrong_task_rejected_before_artifact_write(tmp_path,task):
    with pytest.raises(ValueError,match="task"):
        low.sample_task((str(tmp_path),low.make_plan(0,0,capacity=True),task))
    assert not (tmp_path/"traces").exists()


def test_run_requires_qsub_and_fixed_threads(tmp_path,monkeypatch):
    monkeypatch.delenv("PBS_JOBID",raising=False)
    with pytest.raises(ValueError,match="qsub"):
        low.run_phase(tmp_path,low.make_plan(0,0,capacity=True),"sample",96)


def test_changed_manifest_rejected_before_workers(tmp_path,monkeypatch):
    p=low.make_plan(0,0,capacity=True)
    p["anchor_trials"]+=1
    monkeypatch.setenv("PBS_JOBID","fixture")
    for key,value in low.native.THREADS.items(): monkeypatch.setenv(key,value)
    with pytest.raises(ValueError,match="manifest"):
        low.run_phase(tmp_path,p,"anchors",96)


def phase_environment(monkeypatch):
    monkeypatch.setenv("PBS_JOBID","fixture")
    for key,value in low.native.THREADS.items(): monkeypatch.setenv(key,value)


@pytest.mark.parametrize("failure",[False,True])
def test_phase_preflight_precedes_workers_and_failed_cohort_is_saved(tmp_path,monkeypatch,failure):
    phase_environment(monkeypatch)
    p=low.make_plan(0,0,capacity=True)
    order=[]
    def probe(root,plan,phase):
        assert (root/"anchors-execution-intent.json").exists()
        order.append("probe")
        return "a"*64
    def workers(function,jobs,count):
        assert order==["probe"] and count==96
        order.append("workers")
        return [dict(task=list(task),status="failed" if failure and task[4]==0 else "ok") for _,_,task in jobs]
    monkeypatch.setattr(low,"preflight",probe)
    monkeypatch.setattr(c,"parallel_map",workers)
    if failure:
        with pytest.raises(RuntimeError,match="retained"):
            low.run_phase(tmp_path,p,"anchors",96)
    else:
        low.run_phase(tmp_path,p,"anchors",96)
    import json
    summary=json.loads((tmp_path/"anchors-summary.json").read_text())
    assert summary["tasks"]==2 and summary["failed"]==int(failure)
    assert summary["native_preflight_sha256"]=="a"*64
    with pytest.raises(ValueError,match="rerun"):
        low.run_phase(tmp_path,p,"anchors",96)
    assert order==["probe","workers"]


def test_native_mismatch_stops_before_workers_and_preserves_intent(tmp_path,monkeypatch):
    phase_environment(monkeypatch)
    p=low.make_plan(0,0,capacity=True)
    def probe(*args): raise ValueError("native mismatch")
    def forbidden(*args): pytest.fail("workers started despite mismatch")
    monkeypatch.setattr(low,"preflight",probe)
    monkeypatch.setattr(c,"parallel_map",forbidden)
    with pytest.raises(ValueError,match="native"):
        low.run_phase(tmp_path,p,"sample",96)
    assert (tmp_path/"sample-execution-intent.json").exists()
    with pytest.raises(FileExistsError):
        low.run_phase(tmp_path,p,"sample",96)


def test_preflight_keeps_plan_and_execution_evidence_separate(tmp_path,monkeypatch):
    p=low.make_plan(0,0,capacity=True)
    for key,value in low.native.platform_inputs().items(): c.atomic_json(tmp_path/(key+".json"),value)
    visited=[]
    def probe(root,plan):
        visited.append(root.name)
        c.atomic_json(root/"native_preflight.json",dict(manifest=c.digest(plan)))
        return c.file_hash(root/"native_preflight.json")
    monkeypatch.setattr(low.native,"native_preflight",probe)
    low.preflight(tmp_path,p,"plan")
    low.preflight(tmp_path,p,"sample")
    assert visited==["preflight-plan","preflight-sample"]
    assert (tmp_path/"preflight-plan/native_preflight.json").exists()
    with pytest.raises(FileExistsError): low.preflight(tmp_path,p,"sample")
    (tmp_path/"platform_fixture.json").write_text("{}")
    with pytest.raises(ValueError,match="input"):
        low.preflight(tmp_path,p,"anchors")


def test_production_tasks_include_all_chains_and_fixed_replicates():
    p=low.make_plan(3,0,capacity=False)
    jobs=list(low.tasks(p))
    assert len(jobs)==2*2*192*10*8
    assert {row[4] for row in jobs}==set(range(192))
    assert {row[6] for row in jobs}==set(range(8))
    assert len(list(low.tasks(p,"anchors")))==192


def test_actual_metadata_mismatch_is_a_recorded_failure(tmp_path,monkeypatch):
    p=low.make_plan(0,0,capacity=True)
    p["anchor_trials"]=2
    original=low.qec.direct_mc
    def wrong(*args,**kwargs):
        result=original(*args,**kwargs)
        result.metadata["sampling_p"]=.2
        return result
    monkeypatch.setattr(low.qec,"direct_mc",wrong)
    record=low.anchor_task((str(tmp_path),p,next(low.tasks(p,"anchors"))))
    assert record["status"]=="failed" and "differs" in record["error"]
