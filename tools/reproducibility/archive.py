"""Inventory pinned research artifacts and build a documentary public archive.

This module never imports research code, runs a calculation, or submits a job.
Run collection through PBS; source roots and inventories remain private.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path, PurePosixPath
import re
import zipfile

HEX = re.compile(r"[0-9a-f]{64}\Z")
TEXT_SUFFIXES = {".py", ".sh", ".pbs", ".json", ".md", ".txt", ".toml", ".yaml", ".yml", ".ini", ".cfg"}
SOURCE_SUFFIXES = {".py", ".sh", ".pbs"}


def require(ok, message):
    if not ok:
        raise ValueError(message)


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def encode(value):
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2, allow_nan=False) + "\n").encode("utf8")


def read_json(path):
    return json.loads(Path(path).read_bytes())


def write_new(path, raw):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("xb") as stream:
        stream.write(raw)


def pinned_references(value, pointer=""):
    """Recognize explicit path/hash records and path-keyed SHA-256 maps.

    Relative references require a caller-supplied base for that document.
    A bare hash has no uniquely recoverable file identity and is not followed.
    """
    found = []
    if isinstance(value, dict):
        if "path" in value and "sha256" in value:
            require(isinstance(value["path"], str) and isinstance(value["sha256"], str)
                    and HEX.fullmatch(value["sha256"]), "Malformed explicit path/SHA-256 pin")
            found.append((value["path"], value["sha256"], pointer))
        for key, item in value.items():
            child = pointer + "/" + str(key).replace("~", "~0").replace("/", "~1")
            if isinstance(item, str) and HEX.fullmatch(item) and ("/" in key or "\\" in key or Path(key).suffix):
                found.append((key, item, child))
            elif isinstance(item, (dict, list)):
                found.extend(pinned_references(item, child))
    elif isinstance(value, list):
        for index, item in enumerate(value):
            found.extend(pinned_references(item, pointer + "/" + str(index)))
    return found


def canonical_roots(mapping):
    require(mapping and all(re.fullmatch(r"[a-z][a-z0-9_-]*", key) for key in mapping), "Named source roots required")
    roots = {key: Path(value) for key, value in mapping.items()}
    require(all(path.is_absolute() and path.resolve() == path for path in roots.values()), "Canonical absolute source roots required")
    require(len(set(roots.values())) == len(roots), "Distinct source roots required")
    return roots


def identity(path, roots):
    candidates = [(key, root) for key, root in roots.items() if path.is_relative_to(root)]
    require(candidates, "Pinned path lies outside explicitly allowed roots")
    key, root = max(candidates, key=lambda pair: len(pair[1].parts))
    return key + "/" + path.relative_to(root).as_posix()


def discover(request):
    """Read only bounded, hash-checked text; index large/raw files without hashing."""
    require(request.get("schema") == 1, "Inventory request schema 1 required")
    roots = canonical_roots(request["roots"])
    limits = request["limits"]
    require(set(limits) == {"file_bytes", "total_bytes", "files"}
            and all(type(v) is int and v > 0 for v in limits.values()), "Positive collection limits required")
    relative_bases = request.get("relative_bases", {})
    queue, edges, records, problems = [], [], {}, []
    for seed in request["seeds"]:
        require(set(seed) == {"scope", "path", "sha256"} and HEX.fullmatch(seed["sha256"]), "Explicit seed scope and byte pin required")
        queue.append((seed["path"], seed["sha256"]))
    total = 0
    while queue:
        raw_path, expected = queue.pop(0)
        path = Path(raw_path)
        if str(path) in records:
            if records[str(path)]["original_sha256"] != expected:
                problems.append({"kind": "conflicting_pins", "path": str(path)})
            continue
        if len(records) >= limits["files"]:
            problems.append({"kind": "file_limit", "path": str(path)})
            break
        record = {"path": str(path), "original_sha256": expected, "original_hash_verified": False}
        records[str(path)] = record
        try:
            require(path.is_absolute() and path.resolve() == path and path.is_file(), "Missing, symlinked, or noncanonical file")
            record["identity"] = identity(path, roots)
            record["size"] = path.stat().st_size
            is_source = path.suffix in SOURCE_SUFFIXES
            if path.suffix not in TEXT_SUFFIXES or record["size"] > limits["file_bytes"]:
                require(not is_source, "Source exceeds collection limit; enlarge reviewed limit")
                record.update(storage="external", reason="binary_or_large_input", reference_scan="not_performed")
                continue
            require(total + record["size"] <= limits["total_bytes"], "Total collection byte limit reached")
            raw = path.read_bytes()
            require(len(raw) == record["size"] and digest(raw) == expected, "Pinned bytes differ")
            raw.decode("utf8")
            total += len(raw)
            record.update(storage="archive", original_hash_verified=True, reference_scan="not_json")
            if path.suffix == ".json":
                references = pinned_references(json.loads(raw))
                record["reference_scan"] = "explicit_json_pins_only"
                for target, checksum, pointer in references:
                    resolved = Path(target)
                    if not resolved.is_absolute():
                        require(str(path) in relative_bases, "Relative pin requires an explicit per-document base")
                        resolved = Path(relative_bases[str(path)]) / resolved
                    require(resolved.is_absolute() and resolved.resolve() == resolved, "Noncanonical dependency path")
                    edges.append({"from": str(path), "pointer": pointer, "to": str(resolved), "original_sha256": checksum})
                    queue.append((str(resolved), checksum))
        except (ValueError, OSError, UnicodeError, json.JSONDecodeError) as exc:
            record["storage"] = "blocked"
            problems.append({"kind": "unresolved", "path": str(path), "reason": str(exc)})
    covered = sorted({seed["scope"] for seed in request["seeds"]})
    return dict(schema=1, purpose="private_reproduction_inventory", roots=request["roots"],
                seeds=request["seeds"], limits=limits, records=list(records.values()), edges=edges,
                problems=problems, missing_scopes=sorted(set(request["required_scopes"]) - set(covered)),
                collection_bytes=total, scientific_reproduction_verified=False,
                discovery_limit="Explicit JSON pins only; unpinned dynamic imports and bare hashes require a reviewed supplemental seed list.")


def redactor(policy):
    require(policy.get("schema") == 1 and isinstance(policy["replacements"], list), "Public policy schema 1 required")
    pairs = [(row["private"], row["public"]) for row in policy["replacements"]]
    require(all(isinstance(old, str) and isinstance(new, str) and old and new and old != new for old, new in pairs), "Nonempty explicit redactions required")
    require(len({old for old, _ in pairs}) == len(pairs), "Unique private tokens required")
    require(all(old not in new for old, _ in pairs for _, new in pairs), "Replacement text must not reintroduce private tokens")
    # Textual logs/source can contain JSON-escaped paths or Unicode identifiers.
    pairs = list(dict.fromkeys([*pairs, *[(json.dumps(old, ensure_ascii=ascii_only)[1:-1],
                                         json.dumps(new, ensure_ascii=ascii_only)[1:-1])
                                        for old, new in pairs for ascii_only in (False, True)]]))
    forbidden = [*policy["forbidden_literals"], *(old for old, _ in pairs)]
    require(all(isinstance(token, str) and token for token in forbidden), "Nonempty forbidden tokens required")
    def redact(text):
        for old, new in sorted(pairs, key=lambda pair: len(pair[0]), reverse=True):
            text = text.replace(old, new)
        require(not any(token in text for token in forbidden), "Forbidden identifier remains after redaction")
        require(not re.search(r"(?:/home/[^/\s\"']+|[A-Za-z]:[\\/](?:Users|dev)[\\/])", text), "Unmapped personal absolute path remains")
        return text
    return redact


def safe_name(name):
    path = PurePosixPath(name)
    require(not path.is_absolute() and ".." not in path.parts and "\\" not in name
            and name == str(path) and len(path.parts) > 1
            and not re.search(r'[\x00-\x1f<>:"|?*]', name)
            and all(not part.endswith((".", " ")) and not re.fullmatch(r"(?i:CON|PRN|AUX|NUL|COM[1-9]|LPT[1-9])(?:\..*)?", part)
                    for part in path.parts), "Safe archive-relative member required")
    return name


def build(inventory, policy, archive_path):
    """Write new ZIP with separate original/public hashes; never rewrite sources."""
    require(inventory.get("purpose") == "private_reproduction_inventory" and not inventory["problems"], "Resolve all inventory problems before packaging")
    redact = redactor(policy)
    require(set(inventory["roots"].values()) <= {row["private"] for row in policy["replacements"]}, "Every source root needs an explicit public replacement")
    files, rows, names = {}, [], set()
    by_path = {row["path"]: row for row in inventory["records"]}
    for row in inventory["records"]:
        public_id = redact(row["identity"])
        name = safe_name("files/" + public_id)
        require(name not in names, "Redaction caused a public path collision")
        names.add(name)
        exported = dict(identity=public_id, original_sha256=row["original_sha256"], size=row["size"],
                        original_hash_verified=row["original_hash_verified"], storage=row["storage"],
                        reference_scan=row["reference_scan"])
        if row["storage"] == "archive":
            raw = Path(row["path"]).read_bytes()
            require(len(raw) == row["size"] and digest(raw) == row["original_sha256"], "Source changed after inventory")
            public = redact(raw.decode("utf8")).encode("utf8")
            files[name] = public
            exported.update(member=name, public_sha256=digest(public), public_size=len(public),
                            modified_for_publication=raw != public,
                            modification_reason="explicit_identifier_redaction" if raw != public else "unchanged")
        else:
            require(row["storage"] == "external", "Blocked artifact cannot be packaged")
            access = policy["external_access"].get(row["identity"])
            require(isinstance(access, dict) and set(access) == {"format", "custodian", "availability", "retrieval", "retention"}
                    and all(isinstance(v, str) and v.strip() for v in access.values()), "Each external artifact needs explicit format/access/retention terms")
            exported["access"] = json.loads(redact(encode(access).decode()))
            exported["original_hash_verified"] = False
        rows.append(exported)
    edges = []
    for edge in inventory["edges"]:
        require(edge["to"] in by_path, "Dependency absent from inventory")
        edges.append(dict(source=redact(by_path[edge["from"]]["identity"]), pointer=redact(edge["pointer"]),
                          target=redact(by_path[edge["to"]]["identity"]), original_sha256=edge["original_sha256"]))
    manifest = dict(schema=1, purpose="documentary_reproduction_archive", artifacts=rows, pin_edges=edges,
                    missing_scopes=[redact(scope) for scope in inventory["missing_scopes"]], discovered_pin_edges_resolved=True,
                    unscanned_json_inputs=[row["identity"] for row in rows if row["identity"].endswith(".json") and row["reference_scan"] == "not_performed"],
                    scientific_reproduction_verified=False, execution_ready=False,
                    source_closure_manually_reviewed=policy.get("source_closure_manually_reviewed") is True,
                    scope_review=redact(policy["scope_review"]),
                    warnings=["Embedded pins identify private original bytes, not redacted public bytes.",
                              "Do not feed redacted environments or receipts to original frozen validators.",
                              "External file hashes are declared upstream pins; this collection did not rehash raw data.",
                              "Dynamic imports, binaries and raw data require the documented supplemental audit."])
    files["manifest.json"] = encode(manifest)
    files["README.txt"] = ("Documentary archive, not an executable snapshot. Verify with archive.py verify.\n"
                           "Use the repository tools/reproducibility/README.md for relocation and pin regeneration scope.\n").encode()
    for raw in files.values():
        require(redact(raw.decode("utf8")) == raw.decode("utf8"), "Final public document still needs redaction")
    archive_path = Path(archive_path)
    archive_path.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(archive_path, "x", compression=zipfile.ZIP_DEFLATED) as archive:
        for name, raw in sorted(files.items()):
            info = zipfile.ZipInfo(name, date_time=(1980, 1, 1, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o100644 << 16
            archive.writestr(info, raw)
    return dict(archive_sha256=digest(archive_path.read_bytes()), manifest_sha256=digest(files["manifest.json"]),
                artifacts=len(rows), scientific_reproduction_verified=False, execution_ready=False)


def verify(archive_path):
    with zipfile.ZipFile(archive_path) as archive:
        names = archive.namelist()
        infos = archive.infolist()
        require(len(infos) <= 4002 and all(info.file_size <= 16 * 1024 * 1024 for info in infos)
                and sum(info.file_size for info in infos) <= 128 * 1024 * 1024, "Archive verification size limit exceeded")
        require(len(names) == len(set(names)), "Duplicate ZIP members")
        manifest = json.loads(archive.read("manifest.json"))
        require(manifest["purpose"] == "documentary_reproduction_archive" and manifest["execution_ready"] is False
                and manifest["scientific_reproduction_verified"] is False, "Documentary-only archive required")
        expected = {"manifest.json", "README.txt"}
        identities = set()
        original_pins = {}
        for row in manifest["artifacts"]:
            require(row["identity"] not in identities, "Duplicate artifact identity")
            identities.add(row["identity"])
            original_pins[row["identity"]] = row["original_sha256"]
            require(HEX.fullmatch(row["original_sha256"]), "Original pin required")
            if row["storage"] == "archive":
                name = safe_name(row["member"])
                require(name not in expected, "Duplicate artifact member")
                expected.add(name)
                raw = archive.read(name)
                require(digest(raw) == row["public_sha256"] and len(raw) == row["public_size"], "Public bytes differ")
                require(row["modified_for_publication"] == (row["original_sha256"] != row["public_sha256"]), "Original/public hash distinction differs")
            else:
                require(row["storage"] == "external" and row["original_hash_verified"] is False and row["access"], "Explicit unverified external input required")
        require(set(names) == expected, "Archive has missing or unlisted members")
        for edge in manifest["pin_edges"]:
            require(edge["source"] in identities and edge["target"] in identities, "Unresolved public dependency edge")
            require(edge["original_sha256"] == original_pins[edge["target"]], "Edge and original target pin differ")
        return dict(public_bytes_verified=True, artifacts=len(identities), execution_ready=False,
                    scientific_reproduction_verified=False, missing_scopes=manifest["missing_scopes"])


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    scan = sub.add_parser("discover")
    scan.add_argument("--request", required=True)
    scan.add_argument("--inventory", required=True)
    package = sub.add_parser("build")
    package.add_argument("--inventory", required=True)
    package.add_argument("--policy", required=True)
    package.add_argument("--archive", required=True)
    check = sub.add_parser("verify")
    check.add_argument("--archive", required=True)
    args = parser.parse_args()
    if args.command == "discover":
        inventory = discover(read_json(args.request))
        write_new(args.inventory, encode(inventory))
        print(json.dumps(dict(files=len(inventory["records"]), problems=len(inventory["problems"]), missing_scopes=inventory["missing_scopes"])))
    elif args.command == "build":
        print(json.dumps(build(read_json(args.inventory), read_json(args.policy), args.archive)))
    else:
        print(json.dumps(verify(args.archive)))


if __name__ == "__main__":
    main()
