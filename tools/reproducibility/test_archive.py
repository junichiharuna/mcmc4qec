"""Small metadata-only fixtures; execute with unittest in a PBS job."""
from copy import deepcopy
import json
from pathlib import Path
import tempfile
import unittest
import zipfile

import archive as tool


class ArchiveTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name).resolve()
        self.code = self.put("worker.py", b"# pinned fixture\nVALUE = 3\n")
        self.data = self.put("trace.bin", b"raw sample fixture")
        self.config = self.put("config.json", tool.encode({"source_sha256": {self.code["path"]: self.code["sha256"]}, "trace": self.data}))
        self.request = dict(schema=1, roots={"workspace": str(self.root)},
                            seeds=[dict(scope="science", **self.config)], required_scopes=["science", "final_proofs"],
                            relative_bases={}, limits=dict(file_bytes=65536, total_bytes=1048576, files=30))
        self.policy = dict(schema=1, replacements=[dict(private=str(self.root), public="${WORKSPACE}")],
                           forbidden_literals=["private-host.example"], source_closure_manually_reviewed=False,
                           scope_review="Fixture closure only; final proofs missing.", external_access={
                               "workspace/trace.bin": dict(format="fixture bytes", custodian="fixture owner",
                                   availability="not distributed", retrieval="contact fixture owner", retention="unconfirmed")})

    def put(self, name, raw):
        path = self.root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(raw)
        return dict(path=str(path), sha256=tool.digest(raw))

    def inventory(self):
        return tool.discover(self.request)

    def test_explicit_recursive_pins_and_raw_index(self):
        inv = self.inventory()
        self.assertEqual(inv["problems"], [])
        self.assertEqual(len(inv["records"]), 3)
        raw = next(row for row in inv["records"] if row["path"] == self.data["path"])
        self.assertEqual(raw["storage"], "external")
        self.assertFalse(raw["original_hash_verified"])
        self.assertEqual(inv["missing_scopes"], ["final_proofs"])

    def test_wrong_pinned_bytes_block(self):
        Path(self.code["path"]).write_text("changed", encoding="utf8")
        inv = self.inventory()
        self.assertTrue(inv["problems"])
        with self.assertRaises(ValueError): tool.build(inv, self.policy, self.root / "bad.zip")

    def test_conflicting_pins_block(self):
        self.request["seeds"].append(dict(scope="science", path=self.code["path"], sha256="0" * 64))
        self.assertTrue(any(row["kind"] == "conflicting_pins" for row in self.inventory()["problems"]))

    def test_missing_file_block(self):
        Path(self.code["path"]).unlink()
        self.assertTrue(self.inventory()["problems"])

    def test_relative_pin_requires_document_base(self):
        self.config = self.put("config.json", tool.encode({"source_sha256": {"worker.py": self.code["sha256"]}}))
        self.request["seeds"] = [dict(scope="science", **self.config)]
        self.assertTrue(self.inventory()["problems"])
        self.request["relative_bases"][self.config["path"]] = str(self.root)
        self.assertFalse(self.inventory()["problems"])

    def test_basename_raw_map_is_included(self):
        self.config = self.put("config.json", tool.encode({"input_sha256": {"trace.bin": self.data["sha256"]}}))
        self.request["seeds"] = [dict(scope="science", **self.config)]
        self.request["relative_bases"][self.config["path"]] = str(self.root)
        self.assertEqual(len(self.inventory()["records"]), 2)

    def test_malformed_explicit_pin_blocks(self):
        self.config = self.put("config.json", tool.encode({"input": {"path": self.code["path"], "sha256": "wrong"}}))
        self.request["seeds"] = [dict(scope="science", **self.config)]
        self.assertTrue(self.inventory()["problems"])

    def test_outside_root_block(self):
        self.request["roots"] = {"subset": str(self.root / "subset")}
        self.assertTrue(self.inventory()["problems"])

    def test_source_file_limit_blocks_instead_of_externalizing(self):
        self.request["limits"]["file_bytes"] = 4
        self.request["seeds"] = [dict(scope="science", **self.code)]
        self.assertTrue(self.inventory()["problems"])

    def test_large_json_is_explicit_unscanned_external(self):
        self.request["limits"]["file_bytes"] = 4
        inv = self.inventory()
        self.assertFalse(inv["problems"])
        self.assertEqual(inv["records"][0]["reference_scan"], "not_performed")
        self.assertEqual(inv["records"][0]["storage"], "external")

    def test_total_and_file_count_limits_block(self):
        for key, limit in (("files", 1), ("total_bytes", 1)):
            with self.subTest(key=key):
                req = deepcopy(self.request); req["limits"][key] = limit
                self.assertTrue(tool.discover(req)["problems"])

    def test_public_hashes_are_distinct_from_original_pins(self):
        inv = self.inventory(); destination = self.root / "public.zip"
        receipt = tool.build(inv, self.policy, destination)
        self.assertFalse(receipt["execution_ready"])
        self.assertTrue(tool.verify(destination)["public_bytes_verified"])
        with zipfile.ZipFile(destination) as archive:
            manifest = json.loads(archive.read("manifest.json"))
            config = next(row for row in manifest["artifacts"] if row["identity"].endswith("config.json"))
            self.assertTrue(config["modified_for_publication"])
            self.assertNotEqual(config["original_sha256"], config["public_sha256"])
            self.assertNotIn(str(self.root).encode(), archive.read(config["member"]))
            self.assertFalse(manifest["source_closure_manually_reviewed"])

    def test_source_change_after_inventory_block(self):
        inv = self.inventory(); Path(self.code["path"]).write_text("late change", encoding="utf8")
        with self.assertRaises(ValueError): tool.build(inv, self.policy, self.root / "bad.zip")

    def test_external_access_terms_required(self):
        self.policy["external_access"] = {}
        with self.assertRaises(ValueError): tool.build(self.inventory(), self.policy, self.root / "bad.zip")

    def test_unmapped_root_and_forbidden_identifier_block(self):
        policy = deepcopy(self.policy); policy["replacements"] = []
        with self.assertRaises(ValueError): tool.build(self.inventory(), policy, self.root / "bad.zip")
        code = self.put("private.py", b"# private-host.example\n")
        self.request["seeds"].append(dict(scope="science", **code))
        with self.assertRaises(ValueError): tool.build(self.inventory(), self.policy, self.root / "bad.zip")

    def test_json_escaped_windows_path_redacted(self):
        private = "C:\\Users\\private-owner\\project"
        self.policy["replacements"].append(dict(private=private, public="${OTHER_WORKSPACE}"))
        text = json.dumps(dict(location=private + "\\file.py"))
        cleaned = tool.redactor(self.policy)(text)
        self.assertEqual(json.loads(cleaned)["location"], "${OTHER_WORKSPACE}\\file.py")

    def test_missing_scope_is_redacted(self):
        self.policy["replacements"].append(dict(private="private-scope", public="public-scope"))
        self.request["required_scopes"].append("private-scope")
        path = self.root / "scope.zip"; tool.build(self.inventory(), self.policy, path)
        with zipfile.ZipFile(path) as archive:
            self.assertNotIn(b"private-scope", archive.read("manifest.json"))

    def test_redaction_collision_block(self):
        self.request["seeds"].append(dict(scope="science", **self.put("other.py", b"# another fixture\n")))
        self.policy["replacements"].append(dict(private="other.py", public="worker.py"))
        with self.assertRaises(ValueError): tool.build(self.inventory(), self.policy, self.root / "bad.zip")

    def test_safe_archive_member_rejects_traversal(self):
        for name in ("../escape", "/absolute", "files/../escape", "files\\escape", "files/a:b", "files/a\x00b", "files/NUL.txt", "files/trailing."):
            with self.subTest(name=name), self.assertRaises(ValueError): tool.safe_name(name)

    def test_existing_archive_never_overwritten(self):
        target = self.root / "existing.zip"; target.write_bytes(b"keep")
        with self.assertRaises(FileExistsError): tool.build(self.inventory(), self.policy, target)
        self.assertEqual(target.read_bytes(), b"keep")

    def test_archive_deterministic_for_same_public_bytes(self):
        inv = self.inventory()
        a = tool.build(inv, self.policy, self.root / "a.zip")
        b = tool.build(inv, self.policy, self.root / "b.zip")
        self.assertEqual(a["archive_sha256"], b["archive_sha256"])

    def test_changed_member_and_unlisted_member_rejected(self):
        path = self.root / "original.zip"; tool.build(self.inventory(), self.policy, path)
        with zipfile.ZipFile(path) as source:
            originals = {name: source.read(name) for name in source.namelist()}
        for extra in (False, True):
            changed = dict(originals)
            changed["extra.txt" if extra else "files/workspace/worker.py"] = b"tampered"
            target = self.root / ("extra.zip" if extra else "changed.zip")
            with zipfile.ZipFile(target, "w") as output:
                for name, raw in changed.items(): output.writestr(name, raw)
            with self.assertRaises(ValueError): tool.verify(target)

    def test_edge_target_hash_mismatch_rejected(self):
        path = self.root / "original.zip"; tool.build(self.inventory(), self.policy, path)
        with zipfile.ZipFile(path) as source:
            contents = {name: source.read(name) for name in source.namelist()}
        manifest = json.loads(contents["manifest.json"])
        manifest["pin_edges"][0]["original_sha256"] = "0" * 64
        contents["manifest.json"] = tool.encode(manifest)
        target = self.root / "bad-edge.zip"
        with zipfile.ZipFile(target, "w") as output:
            for name, raw in contents.items(): output.writestr(name, raw)
        with self.assertRaises(ValueError): tool.verify(target)


if __name__ == "__main__":
    unittest.main()
