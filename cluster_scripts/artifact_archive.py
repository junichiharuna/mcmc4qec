"""Verify recovered tile artifact archives without filesystem extraction."""
import argparse
import hashlib
import itertools
import json
from pathlib import Path, PurePosixPath
import tarfile


def digest_stream(stream):
    h=hashlib.sha256()
    for chunk in iter(lambda:stream.read(1024*1024),b""):
        h.update(chunk)
    return h.hexdigest()


def verify(path, expected):
    hashes,markers={},{}
    seen=set()
    with tarfile.open(path,mode="r|gz") as archive:
        for member in archive:
            name=member.name
            p=PurePosixPath(name)
            if p.is_absolute() or ".." in p.parts or name!=str(p) or name in seen:
                raise ValueError(f"unsafe or duplicate archive member: {name}")
            seen.add(name)
            if member.isdir():
                continue
            if not member.isfile():
                raise ValueError(f"unexpected non-file member: {name}")
            stream=archive.extractfile(member)
            if name.endswith(".done.json"):
                payload=stream.read()
                hashes[name]=hashlib.sha256(payload).hexdigest()
                markers[name[:-len(".done.json")]]=json.loads(payload)
            else:
                hashes[name]=digest_stream(stream)
    if set(markers)!=set(expected):
        raise ValueError("missing or unexpected artifact markers")
    for stem,marker in markers.items():
        if marker["identity"]!=expected[stem] or set(marker["sha256"])!={".npz",".json"}:
            raise ValueError(f"identity or payload-set mismatch: {stem}")
        for extension,checksum in marker["sha256"].items():
            if hashes.get(stem+extension)!=checksum:
                raise ValueError(f"payload checksum mismatch: {stem}{extension}")
    if {name[:-4] for name in hashes if name.endswith(".npz")}!=set(expected):
        raise ValueError("unmarked or missing data payload")
    with Path(path).open("rb") as stream:
        archive_hash=digest_stream(stream)
    return dict(archive_sha256=archive_hash,artifacts=len(markers),files=len(hashes),
                payload_sha256=hashes,warning="Transfer/identity integrity only; not an independent scientific re-decode.")


def expected_artifacts(plan,stage,case=None,analysis=None):
    manifest=hashlib.sha256(json.dumps(plan,sort_keys=True,separators=(",",":"),allow_nan=False).encode()).hexdigest()
    if analysis is not None and stage!="production-analysis":
        raise ValueError("analysis context only applies to production-analysis")
    if stage in ("production-anchors","production-sampling","production-analysis"):
        if plan["purpose"]!="calibration" or case is None or case not in range(len(plan["cases"])):
            raise ValueError("explicit production case required")
        if stage=="production-analysis":
            if analysis is None or analysis["sampling_manifest"]!=manifest:
                raise ValueError("analysis context differs from sampling manifest")
            context_hash=hashlib.sha256(json.dumps(analysis,sort_keys=True,separators=(",",":"),allow_nan=False).encode()).hexdigest()
            groups=((case,kernel,init,rep) for kernel,init,rep in itertools.product(
                range(len(plan["kernels"])),range(len(plan["initializations"])),range(plan["replicates"])))
            return {"analysis/"+"-".join(map(str,group)):dict(analysis=context_hash,group=list(group)) for group in groups}
        expected={f"anchors/{case}-{rep}":dict(manifest=manifest,case=case,replicate=rep) for rep in range(plan["replicates"])}
        if stage=="production-sampling":
            spec=plan["cases"][case]
            jobs=((case,*tail) for tail in itertools.product(range(len(plan["kernels"])),range(len(plan["initializations"])),
                  range(plan["replicates"]),range(len(spec["rungs"])),range(spec["chains"])))
            expected.update({"traces/"+"-".join(map(str,task)):dict(manifest=manifest,task=list(task)) for task in jobs})
        return expected
    if case is not None:
        raise ValueError("case only applies to production stages")
    if stage=="pilot":
        jobs=itertools.product(range(len(plan["cases"])),range(len(plan["probabilities"])),range(plan["replicates"]))
        directory="pilot"
    elif stage=="reference":
        jobs=((case,chunk) for case,count in enumerate(plan["chunks"]) for chunk in range(count))
        directory="chunks"
    elif stage=="capacity":
        jobs=((case,kernel,init,rep,0 if rep%2==0 else len(spec["rungs"])-1,rep%spec["chains"])
              for case,spec in enumerate(plan["cases"]) for kernel,init,rep in itertools.product(range(2),range(2),range(plan["replicates"])))
        directory="traces"
    elif stage=="analysis-capacity":
        jobs=itertools.product(range(4),range(plan["replicates"]))
        return {"profiles/"+"-".join(map(str,task)):dict(manifest=manifest,task=list(task),synthetic=True) for task in jobs}
    elif stage=="weight-pilot":
        jobs=itertools.product(range(len(plan["cases"])),range(4),range(len(plan["weights"])),range(plan["replicates"]))
        directory="layers"
    else:
        raise ValueError("unsupported stage")
    return {directory+"/"+"-".join(map(str,task)):dict(manifest=manifest,task=list(task)) for task in jobs}


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--archive",type=Path,required=True)
    parser.add_argument("--manifest",type=Path,required=True)
    parser.add_argument("--stage",choices=["pilot","reference","capacity","analysis-capacity","weight-pilot","production-anchors","production-sampling","production-analysis"],required=True)
    parser.add_argument("--case",type=int)
    parser.add_argument("--analysis-manifest",type=Path)
    parser.add_argument("--output",type=Path,required=True)
    args=parser.parse_args()
    plan=json.loads(args.manifest.read_text())
    analysis=None if args.analysis_manifest is None else json.loads(args.analysis_manifest.read_text())
    result=verify(args.archive,expected_artifacts(plan,args.stage,args.case,analysis))
    with args.manifest.open("rb") as stream:
        manifest_hash=digest_stream(stream)
    if result["payload_sha256"].get("manifest.json")!=manifest_hash:
        raise ValueError("recovered manifest bytes differ from pinned manifest")
    if analysis is not None:
        with args.analysis_manifest.open("rb") as stream:
            analysis_hash=digest_stream(stream)
        if result["payload_sha256"].get("analysis_manifest.json")!=analysis_hash:
            raise ValueError("recovered analysis manifest bytes differ")
        if result["payload_sha256"].get("reference_summary.json")!=analysis["reference_summary_sha256"]:
            raise ValueError("recovered independent reference differs")
        result["analysis_manifest_sha256"]=analysis_hash
    result.update(stage=args.stage,manifest_sha256=manifest_hash)
    if args.case is not None:
        result["case"]=args.case
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(result,sort_keys=True,indent=2)+"\n",encoding="utf-8")
    print(json.dumps({k:v for k,v in result.items() if k!="payload_sha256"}))


if __name__=="__main__":
    main()
