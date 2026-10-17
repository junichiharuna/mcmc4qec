"""Verify downloaded archives and every inventoried payload without extraction."""
import argparse
import gzip
import hashlib
import json
from pathlib import Path
import tarfile
import time


def sha_stream(stream):
    h = hashlib.sha256()
    for block in iter(lambda: stream.read(1024*1024), b""):
        h.update(block)
    return h.hexdigest()


def sha_file(path):
    with Path(path).open("rb") as stream:
        return sha_stream(stream)


def verify(root):
    root = Path(root)
    start = time.perf_counter()
    audit = json.loads((root/"audit.json").read_text())
    if audit["status"] != "verified":
        raise ValueError("remote audit incomplete")
    for name, expected in audit["outputs"].items():
        if sha_file(root/name) != expected:
            raise ValueError(f"downloaded audit output checksum: {name}")
    with gzip.open(root/"inventory.jsonl.gz", "rt", encoding="utf-8") as stream:
        inventory = [json.loads(line) for line in stream]
    expected = {r["path"]: r for r in inventory}
    if len(expected) != len(inventory):
        raise ValueError("duplicate inventory")
    seen = set()
    archives = json.loads((root/"archives.json").read_text())
    for record in archives:
        path = root/"archives"/record["path"]
        if path.stat().st_size != record["bytes"] or sha_file(path) != record["sha256"]:
            raise ValueError(f"archive checksum: {path}")
        with tarfile.open(path, "r|gz") as tar:
            for member in tar:
                if member.name not in expected:
                    continue
                if member.name in seen or not member.isfile():
                    raise ValueError(f"duplicate/nonregular payload {member.name}")
                item = expected[member.name]
                if member.size != item["bytes"] or sha_stream(tar.extractfile(member)) != item["sha256"]:
                    raise ValueError(f"recovered payload checksum: {member.name}")
                seen.add(member.name)
    if seen != set(expected):
        raise ValueError(f"missing recovered payloads: {len(set(expected)-seen)}")
    result = dict(status="verified", manifest=audit["manifest"], remote_audit_sha256=sha_file(root/"audit.json"),
                  archives=len(archives), payloads=len(seen), archive_bytes=sum(x["bytes"] for x in archives),
                  elapsed_seconds=time.perf_counter()-start, archive_directory=str((root/"archives").resolve()))
    (root/"recovery.json").write_text(json.dumps(result, indent=2)+"\n", encoding="utf-8")
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("root", type=Path)
    args = parser.parse_args()
    print(json.dumps(verify(args.root)))
