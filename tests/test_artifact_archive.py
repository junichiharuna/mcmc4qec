"""Archive verification detects corrupt, missing and duplicate payloads."""
import hashlib
import io
import json
from pathlib import Path
import sys
import tarfile

import pytest

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"cluster_scripts"))
import artifact_archive as a


def fixture_archive(path, *, corrupt=False, missing=False, duplicate=False):
    identity={"manifest":"abc","task":[0]}
    data={"pilot/0.npz":b"test-data", "pilot/0.json":b'{"status":"ok"}'}
    marker={"identity":identity,"sha256":{ext:hashlib.sha256(data["pilot/0"+ext]).hexdigest() for ext in (".npz",".json")}}
    data["pilot/0.done.json"]=json.dumps(marker).encode()
    if corrupt:
        data["pilot/0.npz"]=b"corruption"
    if missing:
        del data["pilot/0.npz"]
    with tarfile.open(path,"w:gz") as archive:
        for name,payload in list(data.items())+([("pilot/0.json",b"duplicate")] if duplicate else []):
            info=tarfile.TarInfo(name)
            info.size=len(payload)
            archive.addfile(info,io.BytesIO(payload))
    return {"pilot/0":identity}


def test_archive_checks_both_payloads_and_expected_keys(tmp_path):
    path=tmp_path/"data.tar.gz"
    expected=fixture_archive(path)
    assert a.verify(path,expected)["artifacts"]==1
    with pytest.raises(ValueError):
        a.verify(path,{})
    for option in ("corrupt","missing","duplicate"):
        fixture_archive(path,**{option:True})
        with pytest.raises(ValueError):
            a.verify(path,expected)


def test_production_anchor_subset_requires_explicit_case_and_exact_identity():
    plan=dict(purpose="calibration",replicates=2,cases=[{},{}])
    result=a.expected_artifacts(plan,"production-anchors",case=1)
    assert set(result)=={"anchors/1-0","anchors/1-1"}
    for rep in range(2):
        identity=result[f"anchors/1-{rep}"]
        assert identity["case"]==1 and identity["replicate"]==rep
        assert set(identity)=={"manifest","case","replicate"}
    for case in (None,-1,2):
        with pytest.raises(ValueError):
            a.expected_artifacts(plan,"production-anchors",case=case)


def production_plan():
    return dict(purpose="calibration",replicates=2,initializations=["rejection","logical"],
                kernels={"ZH":{},"ZHS":{}},cases=[dict(rungs=[.1,.03],chains=3),dict(rungs=[.1,.07,.05],chains=2)])


def test_production_sampling_matches_actual_task_generator():
    pytest.importorskip("ldpc")
    import tile_bar_study as b
    plan=production_plan()
    expected=a.expected_artifacts(plan,"production-sampling",case=1)
    trace_keys={"traces/"+"-".join(map(str,task)) for task in b.tasks(plan,1)}
    assert set(expected)==trace_keys|{"anchors/1-0","anchors/1-1"}
    assert len(trace_keys)==48
    for key in trace_keys:
        assert expected[key]==dict(manifest=b.c.digest(plan),task=list(map(int,key.split("/")[1].split("-"))))
    for case in (None,-1,2):
        with pytest.raises(ValueError):
            a.expected_artifacts(plan,"production-sampling",case=case)


def test_production_analysis_context_is_bound_to_sampling():
    plan=production_plan()
    digest=hashlib.sha256(json.dumps(plan,sort_keys=True,separators=(",",":"),allow_nan=False).encode()).hexdigest()
    context=dict(sampling_manifest=digest,references=[{"case":0},{"case":1}])
    expected=a.expected_artifacts(plan,"production-analysis",case=1,analysis=context)
    assert len(expected)==8
    analysis_digest=hashlib.sha256(json.dumps(context,sort_keys=True,separators=(",",":"),allow_nan=False).encode()).hexdigest()
    assert expected["analysis/1-1-0-1"]==dict(analysis=analysis_digest,group=[1,1,0,1])
    for wrong in (None,dict(context,sampling_manifest="other")):
        with pytest.raises(ValueError):
            a.expected_artifacts(plan,"production-analysis",case=1,analysis=wrong)
    with pytest.raises(ValueError):
        a.expected_artifacts(plan,"production-sampling",case=1,analysis=context)


def write_production_archive(path,expected,*,omit=None,wrong_identity=False,extra_files=None):
    with tarfile.open(path,"w:gz") as archive:
        for index,(stem,identity) in enumerate(expected.items()):
            if stem==omit:
                continue
            payloads={".npz":b"numeric-payload",".json":json.dumps({"status":"failed" if index==0 else "ok"}).encode()}
            marker=dict(identity=dict(identity,extra="wrong") if wrong_identity and index==0 else identity,
                        sha256={ext:hashlib.sha256(data).hexdigest() for ext,data in payloads.items()})
            payloads[".done.json"]=json.dumps(marker).encode()
            for ext,data in payloads.items():
                info=tarfile.TarInfo(stem+ext)
                info.size=len(data)
                archive.addfile(info,io.BytesIO(data))
        for name,data in (extra_files or {}).items():
            info=tarfile.TarInfo(name)
            info.size=len(data)
            archive.addfile(info,io.BytesIO(data))


def test_complete_sampling_archive_retains_failed_tasks_and_rejects_missing_or_other_case(tmp_path):
    plan=production_plan()
    expected=a.expected_artifacts(plan,"production-sampling",case=1)
    path=tmp_path/"sampling.tar.gz"
    write_production_archive(path,expected)
    assert a.verify(path,expected)["artifacts"]==50
    with pytest.raises(ValueError):
        a.verify(path,a.expected_artifacts(plan,"production-sampling",case=0))
    for missing in ("traces/1-0-0-0-0-0","anchors/1-1"):
        write_production_archive(path,expected,omit=missing)
        with pytest.raises(ValueError):
            a.verify(path,expected)
    write_production_archive(path,expected,wrong_identity=True)
    with pytest.raises(ValueError):
        a.verify(path,expected)


def test_analysis_cli_checks_both_manifests_and_reference_bytes(tmp_path,monkeypatch):
    plan=production_plan()
    plan_bytes=json.dumps(plan,sort_keys=True,separators=(",",":"),allow_nan=False).encode()
    reference=b'{"records":[]}'
    context=dict(sampling_manifest=hashlib.sha256(plan_bytes).hexdigest(),
                 reference_summary_sha256=hashlib.sha256(reference).hexdigest())
    context_bytes=json.dumps(context).encode()
    manifest=tmp_path/"manifest.json"
    manifest.write_bytes(plan_bytes)
    analysis=tmp_path/"analysis_manifest.json"
    analysis.write_bytes(context_bytes)
    archive=tmp_path/"analysis.tar.gz"
    output=tmp_path/"verification.json"
    expected=a.expected_artifacts(plan,"production-analysis",case=1,analysis=context)
    files={"manifest.json":plan_bytes,"analysis_manifest.json":context_bytes,"reference_summary.json":reference}
    monkeypatch.setattr(sys,"argv",["artifact_archive.py","--archive",str(archive),"--manifest",str(manifest),
                        "--analysis-manifest",str(analysis),"--stage","production-analysis","--case","1","--output",str(output)])
    write_production_archive(archive,expected,extra_files=files)
    a.main()
    record=json.loads(output.read_text())
    assert record["artifacts"]==8 and record["case"]==1
    assert record["analysis_manifest_sha256"]==hashlib.sha256(context_bytes).hexdigest()
    original=output.read_bytes()
    for name in files:
        write_production_archive(archive,expected,extra_files=dict(files,**{name:b"changed"}))
        with pytest.raises(ValueError):
            a.main()
        assert output.read_bytes()==original
    omitted=dict(files)
    del omitted["reference_summary.json"]
    write_production_archive(archive,expected,extra_files=omitted)
    with pytest.raises(ValueError):
        a.main()
