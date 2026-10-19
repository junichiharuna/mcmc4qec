"""Saved diagnostic inventory; synthetic metadata, never physical sampling."""
import copy
import itertools
import json
from pathlib import Path
import sys

import pytest

pytest.importorskip("ldpc")
pytest.importorskip("bposd")
pytest.importorskip("pymatching")
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "cluster_scripts"))
import calibration as c
import tile_audited_results as audited
import tile_mixing_inventory as inventory


def plan():
    return dict(purpose="calibration", replicates=192, kernels={"ZH": {}, "ZHS": {}},
                initializations=["rejection", "logical"], burns=[0], runtime={},
                cases=[dict(size=6, noise="bit", target=.03, rungs=[.1, .03], coarse=[.1, .03],
                            chains=4, windows=[2], steps=2) for _ in range(4)])


def record(p, group=(0, 0, 0, 0)):
    rows=[]
    for item in inventory.expected_diagnostics(p, group[0]).values():
        chains=item["chains"]
        row=dict(item, mean=.4, chain_means=[.4]*chains, chain_iat=[1.]*chains,
                 chain_ess=[2.]*chains, iat=1., ess=2.*chains, iat_mcse=.1,
                 cross_chain_se=.1, rhat=1., undefined=False, high_rhat=False,
                 low_ess=True, flagged=True)
        if not item["observable"].endswith("_bennett_edge_0"):
            row.update(sector_transitions=[1]*chains, unique_sectors=[2]*chains)
        rows.append(row)
    return dict(status="ok", group=list(group), diagnostics=rows, diagnostic_count=len(rows), failed_tasks=[])


def test_expected_full_design_counts():
    import tile_bar_study as b
    p=b.make_plan()
    assert [len(inventory.expected_diagnostics(p, case))*768 for case in range(4)] == [811008,571392,1327104,940032]


def test_all_observables_and_sector_dedup():
    p=plan()
    rows=inventory.inventory_group(p,0,(0,0,0,0),record(p))
    assert len(rows)==26
    assert sum(r["kind"]=="sector" for r in rows)==2
    assert sum(r["kind"]=="diagnostic" for r in rows)==24
    assert all(r["replicate"]==0 for r in rows)


def test_missing_nonfinite_and_undefined_retained():
    p=plan(); saved=record(p)
    saved["diagnostics"][0]["rhat"]=float("inf")
    saved["diagnostics"][0]["chain_ess"][0]=None
    saved["diagnostics"][1].pop("mean")
    removed=saved["diagnostics"].pop(2)
    saved["diagnostic_count"]-=1
    rows=inventory.inventory_group(p,0,(0,0,0,0),saved)
    assert len(rows)==26
    assert rows[0]["values"]["rhat"] is None
    assert "rhat" in rows[0]["nonfinite_paths"]
    assert rows[0]["undefined"]
    assert "mean" in rows[1]["missing_fields"]
    absent=next(r for r in rows if r["observable"]==removed["observable"] and r["rung"]==removed["rung"])
    assert absent["status"]=="missing_unexpected"
    json.dumps(rows,allow_nan=False)


def test_failed_rung_suppresses_whole_ladder_not_other_rung():
    p=plan(); saved=record(p)
    saved["failed_tasks"]=[[0,0,0,0,0,0]]
    saved["diagnostics"]=[r for r in saved["diagnostics"] if r["rung"]==1 and "bennett" not in r["observable"]]
    saved["diagnostic_count"]=len(saved["diagnostics"])
    rows=inventory.inventory_group(p,0,(0,0,0,0),saved)
    assert sum(r["status"]=="missing_recorded_sampling_failure" for r in rows)==15
    assert sum(r["status"]=="stored" for r in rows)==11


def test_prefix_external_failure_and_invalid_identity():
    p=plan(); p["cases"][0]["chains"]=8
    saved=record(p); saved["failed_tasks"]=[[0,0,0,0,0,7]]
    saved["diagnostics"]=[r for r in saved["diagnostics"] if r["chains"]==4 or (r["rung"]==1 and "bennett" not in r["observable"])]
    saved["diagnostic_count"]=len(saved["diagnostics"])
    rows=inventory.inventory_group(p,0,(0,0,0,0),saved)
    assert all(r["status"]=="stored" for r in rows if r["chains"]==4)
    for mutation in (lambda r:r["diagnostics"].append(copy.deepcopy(r["diagnostics"][0])),
                     lambda r:r["diagnostics"][0].update(rung=99),
                     lambda r:r["diagnostics"][0].update(chain_ess=[1.])):
        broken=copy.deepcopy(saved); mutation(broken); broken["diagnostic_count"]=len(broken["diagnostics"])
        with pytest.raises(ValueError): inventory.inventory_group(p,0,(0,0,0,0),broken)


def test_full_seed_statistics_keep_missing_nonfinite_and_failed():
    p=plan(); base=inventory.inventory_group(p,0,(0,0,0,0),record(p))[0]
    cohorts={}
    for rep in range(192):
        row=copy.deepcopy(base); row["replicate"]=rep
        if rep in (0,1,2):
            row["values"]["mean"]=None; row["undefined"]=True
        if rep==0: row["nonfinite_paths"]=["mean"]
        if rep==1: row["status"]="missing_recorded_sampling_failure"
        if rep==2: row["status"]="missing_unexpected"
        inventory._add(cohorts,row)
    result=inventory._summaries(cohorts,192)[0]
    assert result["replicate_ids"]==list(range(192)) and result["undefined"]==3
    assert result["metrics"]["mean"]["finite_values"]==189
    assert result["metrics"]["mean"]["nonfinite_values"]==1
    assert result["metrics"]["mean"]["null_values"]==2
    assert result["metrics"]["mean"]["mean"] is None
    assert result["metrics"]["mean"]["available_only_mean"]==pytest.approx(.4)


def test_failed_diagnostic_present_rejected():
    p=plan(); saved=record(p); saved["failed_tasks"]=[[0,0,0,0,0,0]]
    with pytest.raises(ValueError,match="despite"): inventory.inventory_group(p,0,(0,0,0,0),saved)


@pytest.fixture(scope="module")
def saved_base(tmp_path_factory):
    tmp_path=tmp_path_factory.mktemp("mixing-inventory")
    root=tmp_path/"production"; root.mkdir()
    p=plan(); context=dict(sampling_manifest=c.digest(p),runtime=p["runtime"],analysis_source_sha256=c.file_hash(audited.bar.__file__))
    c.atomic_json(root/"manifest.json",p); c.atomic_json(root/"analysis_manifest.json",context)
    payload={"manifest.json":c.file_hash(root/"manifest.json"),"analysis_manifest.json":c.file_hash(root/"analysis_manifest.json")}
    for group in itertools.product((0,),range(2),range(2),range(192)):
        stem="analysis/"+c.task_id(group)
        value=record(p,group)
        value["diagnostics"]=value["diagnostics"][:1]; value["diagnostic_count"]=1
        path=root/(stem+".json"); path.parent.mkdir(exist_ok=True)
        path.write_bytes(c.canonical(value))
        digest=c.file_hash(path)
        marker=dict(identity=dict(analysis=c.digest(context),group=list(group)),sha256={".json":digest,".npz":"unused-array-hash"})
        (root/(stem+".done.json")).write_bytes(c.canonical(marker))
        payload.update({stem+".json":digest,stem+".npz":"unused-array-hash",stem+".done.json":c.file_hash(root/(stem+".done.json"))})
    verification=tmp_path/"verification.json"
    c.atomic_json(verification,dict(stage="production-analysis",case=0,archive_sha256="archive",artifacts=768,
                                  manifest_sha256=payload["manifest.json"],payload_sha256=payload))
    report=tmp_path/"audited.json"
    c.atomic_json(report,dict(schema=1,purpose="audited_calibration_results",case=0,replicates=192,groups=768,
        sampling_manifest=c.digest(p),analysis_context=c.digest(context),failed_sampling=0,
        current_archived_inputs_match_audited_inputs=True,historical_consumed_input_hashes_recorded=False,
        terminal_payload_stat_checked=True,source_sha256=c.file_hash(audited.__file__),
        source_hashes={"adapter":c.file_hash(audited.__file__)},
        input_sha256={str(path):c.file_hash(path) for path in (root/"manifest.json",root/"analysis_manifest.json",verification)}))
    return dict(root=root,audited_results=report,analysis_verification=verification,case=0,output=tmp_path/"new-report")


@pytest.fixture
def saved(tmp_path,saved_base,monkeypatch):
    # The real diagnostic grid is tested separately; this explicit fixture
    # isolates the 768-group orchestration from the size of that grid.
    actual=inventory.expected_diagnostics
    def small_grid(p,case):
        expected=actual(p,case); key=next(iter(expected))
        return {key:expected[key]}
    monkeypatch.setattr(inventory,"expected_diagnostics",small_grid)
    args=dict(saved_base,output=tmp_path/"new-report")
    paths=(args["root"]/"analysis/0-0-0-0.json",args["audited_results"],args["analysis_verification"])
    original={path:path.read_bytes() for path in paths}
    yield args
    for path,data in original.items():
        if path.read_bytes()!=data: path.write_bytes(data)


def test_complete_192_cohort_streams_only_json(saved,monkeypatch):
    monkeypatch.setattr(audited,"read_results",lambda *a,**k:pytest.fail("must not repeat full audit"))
    result=inventory.run(**saved)
    assert result["groups"]==768 and result["rows"]==768*2 and result["inventory_complete"]
    assert len(result["records"])==4*2
    assert all(r["replicates"]==192 and r["replicate_ids"]==list(range(192)) for r in result["records"])
    assert not result["diagnostics_recomputed"] and not result["acf_arrays_rechecked"]
    assert not result["current_all_payloads_reaudited"]
    assert result["rows_sha256"]==c.file_hash(saved["output"]/"rows.jsonl")
    assert not list(saved["root"].glob("**/*.npz"))
    with pytest.raises(ValueError): inventory.run(**saved)


@pytest.mark.parametrize("change",["payload","verification","report","inside"])
def test_binding_and_output_rejection(saved,change):
    if change=="payload": (saved["root"]/"analysis/0-0-0-0.json").write_text("{}")
    if change=="verification": saved["analysis_verification"].write_text("{}")
    if change=="report":
        value=json.loads(saved["audited_results"].read_text()); value["groups"]=1; c.atomic_json(saved["audited_results"],value)
    if change=="inside": saved["output"]=saved["root"]/"new-report"
    with pytest.raises(ValueError): inventory.run(**saved)
    assert not (saved["output"]/"summary.json").exists()


@pytest.mark.parametrize("changed",["input","source"])
def test_terminal_input_change_refuses_summary(saved,monkeypatch,tmp_path,changed):
    source=tmp_path/"source.py"; source.write_text("# initial")
    if changed=="source": monkeypatch.setattr(inventory,"__file__",str(source))
    original=inventory.inventory_group
    def mutate(*args,**kwargs):
        rows=original(*args,**kwargs)
        if args[2]==(0,1,1,191):
            path=source if changed=="source" else saved["root"]/"analysis/0-0-0-0.json"
            path.write_text("{}")
        return rows
    monkeypatch.setattr(inventory,"inventory_group",mutate)
    with pytest.raises(ValueError,match="changed"): inventory.run(**saved)
    assert not (saved["output"]/"summary.json").exists()


def test_evidence_rejects_escape_and_same_byte_symlink_retarget(tmp_path):
    root=tmp_path/"root"; root.mkdir()
    one=root/"one.json"; two=root/"two.json"
    one.write_text("{}"); two.write_text("{}")
    alias=root/"alias.json"
    try: alias.symlink_to(one)
    except OSError as error: pytest.skip(str(error))
    evidence=inventory.Evidence(root); evidence.json(alias,production=True)
    alias.unlink(); alias.symlink_to(two)
    with pytest.raises(ValueError,match="changed"): evidence.finish()
    outside=tmp_path/"outside.json"; outside.write_text("{}")
    alias.unlink(); alias.symlink_to(outside)
    with pytest.raises(ValueError,match="escaped"): inventory.Evidence(root).json(alias,production=True)
