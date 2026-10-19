"""Recompute counts and compare common-input probes from the two saved archives."""
import hashlib
import io
import json
from pathlib import Path
import tarfile

import numpy as np


def read_archive(path):
    with tarfile.open(path) as tar:
        data=json.load(tar.extractfile("results/summary.json"))
        arrays={}
        for name,digest in data["artifact_sha256"].items():
            payload=tar.extractfile("results/"+name).read()
            assert hashlib.sha256(payload).hexdigest()==digest
            with np.load(io.BytesIO(payload),allow_pickle=False) as stored:
                arrays[name]={key:stored[key] for key in stored.files}
        assert hashlib.sha256(tar.extractfile("decoder_survey_probe.py").read()).hexdigest()==data["source_sha256"]
    return data,arrays


def main():
    root=Path(__file__).resolve().parent
    platforms=[read_archive(root/name) for name in ("windows_artifacts.tar.gz","linux_artifacts.tar.gz")]
    assert platforms[0][0]["source_sha256"]==platforms[1][0]["source_sha256"]
    assert platforms[0][0]["packages"]==platforms[1][0]["packages"]
    metrics=[]
    for data,arrays in platforms:
        predictions={}
        for row in data["records"]:
            assert row["status"]=="ok"
            key=(row["code"],row["decoder"])
            inputs=arrays[row["code"]+"-inputs.npz"]
            outputs=arrays["-".join(key)+".npz"]
            e,h,l,s=[inputs[k] for k in ("errors","hz","lz","syndromes")]
            assert np.array_equal(e@h.T%2,s)
            base=outputs["corrections"].astype(np.uint8)
            invalid=np.any(base@h.T%2!=s,axis=1)
            logical=np.any((e^base)@l.T%2!=0,axis=1)
            expected=dict(syndrome_mismatches=int(invalid.sum()),logical_mismatches=int(logical.sum()),
                          syndrome_or_logical_failures=int((invalid|logical).sum()),
                          invalid_corrections_missed_by_logical_only=int((invalid&~logical).sum()))
            assert all(row[k]==value for k,value in expected.items())
            for label,field in (("repeated","repeated_correction_mismatches"),("reverse","reversed_correction_mismatches"),("fresh","fresh_correction_mismatches")):
                assert row[field]==int(np.any(base!=outputs[label],axis=1).sum())
            predictions[key]=(base,base@l.T%2,invalid|logical)
        metrics.append(predictions)
    assert metrics[0].keys()==metrics[1].keys()
    differences=[]
    for key,left in metrics[0].items():
        right=metrics[1][key]
        a=platforms[0][1][key[0]+"-inputs.npz"];b=platforms[1][1][key[0]+"-inputs.npz"]
        assert a.keys()==b.keys() and all(np.array_equal(a[k],b[k]) for k in a)
        differences.append(dict(code=key[0],decoder=key[1],samples=len(left[0]),
            correction_differences=int(np.any(left[0]!=right[0],axis=1).sum()),
            logical_prediction_differences=int(np.any(left[1]!=right[1],axis=1).sum()),
            failure_label_differences=int((left[2]!=right[2]).sum())))
    result=dict(records=differences,raw_counts_recomputed=True,inputs_equal=True,
                package_versions_equal=True,source_sha256=platforms[0][0]["source_sha256"],
                audit_source_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                warning="Finite common-input comparison only. Physical correction differences need not change logical predictions or failure labels. No LER, performance or general determinism guarantee.")
    path=root/"comparison.json"
    with path.open("x",encoding="utf-8") as stream:json.dump(result,stream,indent=2);stream.write("\n")
    print(json.dumps([row for row in differences if row["failure_label_differences"]]))


if __name__=="__main__":main()
