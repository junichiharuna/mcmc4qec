"""Finite-scope preservation fixtures, intended for PBS unittest execution."""
from copy import deepcopy
import hashlib
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import zipfile

import snapshot_v2 as s


class SnapshotTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name).resolve()
        self.source = self.put("source.py", b"VALUE = 1\n")
        self.native = self.put("native.so", b"DO NOT READ NATIVE CONTENT\n")
        self.history = dict(path=str(self.root / "unavailable-history.json"), sha256="e" * 64)
        self.document = self.put("config.json", s.encode(dict(source=self.source, old=self.history, native=self.native)))
        self.request = dict(schema=2, roots={"workspace": str(self.root)},
                            sources=[dict(self.source, resolved_path=self.source["path"])],
                            metadata=[dict(self.document, category="current_config", relative_base=None)],
                            external=[dict(self.native, category="native", reason="Declared binary pin; do not rehash")],
                            bindings=[dict(module="source", origin=self.source["path"], resolved=self.source["path"], sha256=self.source["sha256"])],
                            envelope=[], expected_source_count=1, expected_envelope_count=0,
                            limits=dict(file_bytes=65536, total_bytes=1048576), final_proofs_complete=False)

    def put(self, name, raw):
        path = self.root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(raw)
        return dict(path=str(path), sha256=hashlib.sha256(raw).hexdigest())

    def run_snapshot(self, request=None):
        return s.snapshot(self.request if request is None else request, self.root / "snapshot")

    def test_source_and_metadata_preserved_with_external_edges(self):
        result = self.run_snapshot()
        self.assertEqual(result["source_references"], 1)
        self.assertTrue(result["explicit_source_bytes_verified"])
        self.assertFalse(result["full_dependency_closure_complete"])
        edges = json.loads((self.root / "snapshot/one-hop-edges.json").read_bytes())
        self.assertTrue(any(row.get("target") == self.history["path"] and row["collection"] == "external" for row in edges))

    def test_native_and_external_content_never_opened(self):
        original = s.bounded_read
        original_open = Path.open
        def guarded_open(path, *args, **kwargs):
            self.assertNotEqual(str(path), self.native["path"])
            self.assertNotEqual(str(path), self.history["path"])
            return original_open(path, *args, **kwargs)
        def guarded(path, expected, limit):
            self.assertNotEqual(str(path), self.native["path"])
            self.assertNotEqual(str(path), self.history["path"])
            return original(path, expected, limit)
        with patch.object(s, "bounded_read", side_effect=guarded), patch.object(Path, "open", guarded_open): self.run_snapshot()
        external = json.loads((self.root / "snapshot/external-index.json").read_bytes())
        self.assertTrue(all(row["original_hash_verified"] is False for row in external))

    def test_source_alias_preserves_declared_reference(self):
        alias = self.root / "alias.py"; alias.symlink_to(Path(self.source["path"]))
        req = deepcopy(self.request)
        req["sources"].append(dict(path=str(alias), sha256=self.source["sha256"], resolved_path=self.source["path"]))
        req["expected_source_count"] = 2
        result = self.run_snapshot(req)
        self.assertEqual(result["source_references"], 2)
        table = json.loads((self.root / "snapshot/source-members.json").read_bytes())
        self.assertEqual(sum(row["alias"] for row in table), 1)

    def test_alias_unexpected_target_rejected_even_same_bytes(self):
        other = self.put("other.py", Path(self.source["path"]).read_bytes())
        alias = self.root / "alias.py"; alias.symlink_to(Path(other["path"]))
        self.request["sources"][0] = dict(path=str(alias), sha256=self.source["sha256"], resolved_path=self.source["path"])
        with self.assertRaises(ValueError): self.run_snapshot()

    def test_alias_retarget_after_capture_rejected(self):
        other = self.put("other.py", Path(self.source["path"]).read_bytes())
        alias = self.root / "alias.py"; alias.symlink_to(Path(self.source["path"]))
        req = deepcopy(self.request); req["sources"][0] = dict(path=str(alias), sha256=self.source["sha256"], resolved_path=self.source["path"])
        req["bindings"] = []
        original = s.bounded_read; calls = []
        def retarget(path, expected, limit):
            raw = original(path, expected, limit)
            if str(path) == str(alias) and not calls:
                calls.append(True); alias.unlink(); alias.symlink_to(Path(other["path"]))
            return raw
        with patch.object(s, "bounded_read", side_effect=retarget), self.assertRaises(ValueError): self.run_snapshot(req)

    def test_alias_cycle_and_root_escape_rejected(self):
        alias = self.root / "alias.py"; alias.symlink_to(alias)
        self.request["sources"][0] = dict(path=str(alias), sha256=self.source["sha256"], resolved_path=str(alias))
        with self.assertRaises(ValueError): self.run_snapshot()
        alias.unlink(); alias.symlink_to(Path(self.source["path"]))
        self.request["roots"] = {"subset": str(self.root / "subset")}
        with self.assertRaises(ValueError): self.run_snapshot()

    def test_changed_source_pin_rejected(self):
        Path(self.source["path"]).write_bytes(b"changed")
        with self.assertRaises(ValueError): self.run_snapshot()

    def test_source_changes_after_capture_rejected(self):
        original = s.bounded_read; calls = []
        def mutate(path, expected, limit):
            raw = original(path, expected, limit)
            if str(path) == self.source["path"] and not calls:
                calls.append(True); Path(path).write_bytes(b"changed")
            return raw
        with patch.object(s, "bounded_read", side_effect=mutate), self.assertRaises(ValueError): self.run_snapshot()

    def test_duplicate_source_and_wrong_denominator_rejected(self):
        req = deepcopy(self.request); req["sources"].append(req["sources"][0])
        with self.assertRaises(ValueError): self.run_snapshot(req)
        req = deepcopy(self.request); req["expected_source_count"] = 2
        with self.assertRaises(ValueError): self.run_snapshot(req)

    def test_missing_import_binding_rejected(self):
        self.request["bindings"][0]["origin"] = str(self.root / "not-listed.py")
        with self.assertRaises(ValueError): self.run_snapshot()

    def test_binding_hash_and_resolution_must_match(self):
        for key, value in (("sha256", "0" * 64), ("resolved", str(self.root / "other.py"))):
            with self.subTest(key=key):
                req = deepcopy(self.request); req["bindings"][0][key] = value
                with self.assertRaises(ValueError): self.run_snapshot(req)

    def test_malformed_first_edge_does_not_hide_valid_sibling(self):
        value = dict(bad=dict(path="bad", sha256="wrong"), good=self.history)
        edges = s.scan_references(value)
        self.assertTrue(any(row["kind"] == "malformed_pin" for row in edges))
        self.assertTrue(any(row.get("target") == self.history["path"] for row in edges))

    def test_basename_hash_map_and_relative_base(self):
        edges = s.scan_references({"input_sha256": {"trace.npz": "a" * 64}})
        edge = edges[0]
        self.assertEqual(s.resolve_edge(edge, None)["resolution"], "relative_base_unassigned")
        self.assertEqual(s.resolve_edge(edge, str(self.root))["resolved_declaration"], str(self.root / "trace.npz"))

    def test_unbound_hash_and_import_origin_are_indexed(self):
        edges = s.scan_references(dict(unknown_sha256="a" * 64, import_origins=dict(mod="/module.py")))
        self.assertTrue(any(row["kind"] == "unbound_hash" for row in edges))
        self.assertTrue(any(row["kind"] == "unbound_path" for row in edges))

    def test_named_path_hash_pair_is_indexed(self):
        edges = s.scan_references(dict(environment_path="/env.json", environment_sha256="a" * 64))
        self.assertTrue(any(row.get("target") == "/env.json" and row["kind"] == "pin" for row in edges))

    def test_unpaired_path_and_malformed_map_preserve_siblings(self):
        edges = s.scan_references(dict(other_path="/unbound.json", input_sha256={"/bad.npz": "bad", "/good.npz": "a" * 64}))
        self.assertTrue(any(row["kind"] == "unbound_path" and row["target"] == "/unbound.json" for row in edges))
        self.assertTrue(any(row["kind"] == "malformed_pin" and row["target"] == "/bad.npz" for row in edges))
        self.assertTrue(any(row["kind"] == "pin" and row["target"] == "/good.npz" for row in edges))

    def test_missing_historical_file_does_not_claim_preserved(self):
        self.run_snapshot()
        external = json.loads((self.root / "snapshot/external-index.json").read_bytes())
        row = next(row for row in external if row["declared_path"] == self.history["path"])
        self.assertFalse(row["exists"])
        self.assertFalse(row["original_hash_verified"])

    def test_envelope_denominator_and_hash_preserved(self):
        req = deepcopy(self.request)
        req["envelope"] = [dict(self.source, category="source"), dict(self.history, category="historical_metadata")]
        req["expected_envelope_count"] = 2
        result = self.run_snapshot(req)
        self.assertEqual(result["envelope_references"], 2)
        rows = json.loads((self.root / "snapshot/envelope-index.json").read_bytes())
        self.assertEqual(rows[1]["sha256"], self.history["sha256"])

    def test_source_envelope_entry_must_be_collected(self):
        self.request["envelope"] = [dict(self.history, category="source")]
        self.request["expected_envelope_count"] = 1
        with self.assertRaises(ValueError): self.run_snapshot()

    def test_metadata_internal_edge_wrong_pin_rejected(self):
        new = self.put("bad-config.json", s.encode(dict(source=dict(self.source, sha256="0" * 64))))
        self.request["metadata"] = [dict(new, category="current_config", relative_base=None)]
        with self.assertRaises(ValueError): self.run_snapshot()

    def test_conflicting_external_pin_rejected(self):
        new = self.put("bad-external.json", s.encode(dict(native=dict(self.native, sha256="0" * 64))))
        self.request["metadata"] = [dict(new, category="current_config", relative_base=None)]
        with self.assertRaises(ValueError): self.run_snapshot()

    def test_historical_envelope_cannot_conflict_with_current_source(self):
        self.request["envelope"] = [dict(self.source, sha256="0" * 64, category="historical_metadata")]
        self.request["expected_envelope_count"] = 1
        with self.assertRaises(ValueError): self.run_snapshot()

    def test_current_metadata_bytes_remain_original(self):
        self.run_snapshot()
        with zipfile.ZipFile(self.root / "snapshot/private-metadata.zip") as archive:
            self.assertEqual(archive.read("workspace/config.json"), Path(self.document["path"]).read_bytes())

    def test_bounded_source_reads_and_total_limit(self):
        for limits in (dict(file_bytes=1, total_bytes=1048576), dict(file_bytes=65536, total_bytes=1)):
            req = deepcopy(self.request); req["limits"] = limits
            with self.assertRaises(ValueError): self.run_snapshot(req)

    def test_existing_destination_never_overwritten(self):
        target = self.root / "snapshot"; target.mkdir(); (target / "keep").write_bytes(b"keep")
        with self.assertRaises(ValueError): self.run_snapshot()
        self.assertEqual((target / "keep").read_bytes(), b"keep")


if __name__ == "__main__":
    unittest.main()
