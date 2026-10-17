"""Archive recovery verifies data bytes, rather than trusting transfer success."""
import gzip
import hashlib
import io
import json
from pathlib import Path
import sys
import tarfile

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]/"cluster_scripts"))
import verify_recovery as v


def fixture(root, *, payload=b"data", include=True):
    (root/"archives").mkdir()
    path = root/"archives"/"part.tar.gz"
    with tarfile.open(path, "w:gz") as tar:
        if include:
            member = tarfile.TarInfo("production/traces/test.npz")
            member.size = len(payload)
            tar.addfile(member, io.BytesIO(payload))
    inventory = dict(path="production/traces/test.npz", sha256=hashlib.sha256(b"data").hexdigest(), bytes=4)
    with gzip.open(root/"inventory.jsonl.gz", "wt") as stream:
        stream.write(json.dumps(inventory)+"\n")
    (root/"archives.json").write_text(json.dumps([dict(path=path.name, sha256=v.sha_file(path), bytes=path.stat().st_size)]))
    (root/"audit.json").write_text(json.dumps(dict(status="verified", manifest="fixed", outputs={
        name: v.sha_file(root/name) for name in ("inventory.jsonl.gz", "archives.json")})))


def test_recovered_file_bytes(tmp_path):
    fixture(tmp_path)
    assert v.verify(tmp_path)["payloads"] == 1


def test_internally_corrupt_payload_even_with_valid_archive_hash(tmp_path):
    fixture(tmp_path, payload=b"evil")
    with pytest.raises(ValueError, match="payload checksum"):
        v.verify(tmp_path)


def test_missing_archived_payload(tmp_path):
    fixture(tmp_path, include=False)
    with pytest.raises(ValueError, match="missing recovered"):
        v.verify(tmp_path)
