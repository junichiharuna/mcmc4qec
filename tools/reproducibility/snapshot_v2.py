"""Finite private source/metadata snapshot with an explicit one-hop boundary.

No research imports, scheduler calls, raw/native content reads, or publication.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path, PureWindowsPath
import re
import zipfile

HEX = re.compile(r"[0-9a-f]{64}\Z")
SOURCE_SUFFIXES = {".py", ".sh", ".pbs"}


def require(ok, message):
    if not ok:
        raise ValueError(message)


def encode(value):
    return (json.dumps(value, sort_keys=True, indent=2, ensure_ascii=False, allow_nan=False) + "\n").encode()


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def valid_hash(value):
    return isinstance(value, str) and HEX.fullmatch(value) is not None


def pointer(parent, key):
    return parent + "/" + str(key).replace("~", "~0").replace("/", "~1")


def scan_references(value, location=""):
    """Index explicit pins, malformed pins, bare hashes and import path maps.

    Each malformed declaration is retained; it never hides valid siblings.
    """
    edges = []
    if isinstance(value, dict):
        consumed = set()
        pairs = [("path", "sha256")] if "path" in value and "sha256" in value else []
        pairs.extend((key, key[:-5] + "_sha256") for key in value
                     if key.endswith("_path") and key[:-5] + "_sha256" in value)
        for path_key, hash_key in pairs:
            target, checksum = value[path_key], value[hash_key]
            kind = "pin" if isinstance(target, str) and valid_hash(checksum) else "malformed_pin"
            edges.append(dict(pointer=pointer(location, path_key), kind=kind, target=target, sha256=checksum))
            consumed.update((path_key, hash_key))
        for key, item in value.items():
            child = pointer(location, key)
            if key in consumed:
                continue
            if isinstance(item, (dict, list)):
                if key in ("import_origins", "resolved_sources") and isinstance(item, dict):
                    for name, target in item.items():
                        edges.append(dict(pointer=pointer(child, name), kind="unbound_path", target=target,
                                          reason=key + " path mapping"))
                else:
                    edges.extend(scan_references(item, child))
            elif valid_hash(item):
                if "/" in key or "\\" in key or Path(key).suffix:
                    edges.append(dict(pointer=child, kind="pin", target=key, sha256=item))
                else:
                    edges.append(dict(pointer=child, kind="unbound_hash", sha256=item,
                                      reason="No explicit path paired with this hash"))
            elif location.rsplit("/", 1)[-1] in ("source_sha256", "input_sha256", "adapter_sha256", "native_binding", "sources"):
                edges.append(dict(pointer=child, kind="malformed_pin", target=key, sha256=item))
            elif isinstance(item, str) and (key == "path" or key.endswith("_path")):
                edges.append(dict(pointer=child, kind="unbound_path", target=item,
                                  reason="Path declaration has no paired hash"))
            elif key.endswith("sha256"):
                edges.append(dict(pointer=child, kind="malformed_hash", declared_value=item))
    elif isinstance(value, list):
        for index, item in enumerate(value):
            edges.extend(scan_references(item, pointer(location, index)))
    return edges


def resolve_edge(edge, relative_base):
    result = dict(edge)
    target = edge.get("target")
    if not isinstance(target, str):
        result["resolution"] = "no_valid_path"
        return result
    path = Path(target)
    if PureWindowsPath(target).is_absolute() and not path.is_absolute():
        result["resolution"] = "foreign_platform_path"
    elif path.is_absolute():
        result.update(resolution="absolute_declaration", resolved_declaration=str(path))
    elif relative_base is None:
        result["resolution"] = "relative_base_unassigned"
    else:
        base = Path(relative_base)
        require(base.is_absolute() and base.resolve() == base, "Explicit canonical relative base required")
        result.update(resolution="explicit_document_base", resolved_declaration=str(base / path))
    return result


def bounded_read(path, expected, limit):
    """Only source and explicitly included metadata may call this function."""
    require(valid_hash(expected), "Declared original hash required")
    require(type(limit) is int and limit >= 0, "Nonnegative bounded read limit required")
    with Path(path).open("rb") as stream:
        raw = stream.read(limit + 1)
    require(len(raw) <= limit, "File byte limit exceeded")
    require(digest(raw) == expected, "Original bytes differ from declared pin")
    return raw


def in_roots(path, roots):
    return any(path.is_relative_to(root) and path != root for root in roots.values())


def source_resolution(record, roots):
    path, expected = Path(record["path"]), Path(record["resolved_path"])
    require(path.is_absolute() and expected.is_absolute() and in_roots(path, roots)
            and in_roots(expected, roots) and path.suffix in SOURCE_SUFFIXES, "Explicit allowed source path and target required")
    try:
        actual = path.resolve(strict=True)
        require(expected.resolve(strict=True) == expected and actual == expected and actual.is_file(),
                "Source alias differs from its declared canonical target")
    except (OSError, RuntimeError) as error:
        raise ValueError("Source alias is missing, cyclic, or invalid") from error
    return actual


def member_name(path, roots):
    matches = [(key, root) for key, root in roots.items() if path.is_relative_to(root)]
    require(matches, "Archive path is outside declared roots")
    key, root = max(matches, key=lambda pair: len(pair[1].parts))
    relative = path.relative_to(root)
    require(".." not in relative.parts and "\\" not in str(relative), "Archive member must not traverse")
    return key + "/" + relative.as_posix()


def external_observation(declared, roots):
    """Inspect location/stat only; intentionally never open content."""
    result = dict(declared_path=declared.get("path"), declared_sha256=declared.get("sha256"),
                  category=declared.get("category", "outside_explicit_scope"),
                  reason=declared.get("reason", "Reference retained outside finite traversal boundary"),
                  original_hash_verified=False, bytes_collected=False)
    value = declared.get("path")
    if not isinstance(value, str) or not Path(value).is_absolute():
        result.update(exists=None, location_status="not_resolved_on_this_platform")
        return result
    path = Path(value)
    if not in_roots(path, roots):
        result.update(exists=None, location_status="outside_allowed_roots_not_inspected")
        return result
    try:
        resolved = path.resolve(strict=False)
        result["resolved_target"] = str(resolved)
        result["alias"] = path != resolved
        if not in_roots(resolved, roots):
            result.update(exists=None, location_status="resolved_outside_allowed_roots_not_inspected")
        else:
            result.update(exists=path.is_file(), location_status="stat_only")
            if result["exists"]:
                result["size"] = path.stat().st_size
    except (OSError, RuntimeError):
        result.update(exists=None, location_status="unresolvable_or_cyclic")
    return result


def save_new(path, raw):
    with Path(path).open("xb") as stream:
        stream.write(raw)


def write_zip(path, entries):
    with zipfile.ZipFile(path, "x", compression=zipfile.ZIP_DEFLATED) as archive:
        for name, raw in sorted(entries.items()):
            info = zipfile.ZipInfo(name, date_time=(1980, 1, 1, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o100644 << 16
            archive.writestr(info, raw)


def snapshot(request, destination):
    require(request.get("schema") == 2 and request["final_proofs_complete"] is False, "Partial finite-scope request required")
    roots = {name: Path(value) for name, value in request["roots"].items()}
    require(roots and all(re.fullmatch(r"[a-z][a-z0-9_-]*", name) and path.is_absolute() and path.resolve() == path
                          for name, path in roots.items()), "Canonical named roots required")
    destination = Path(destination)
    require(not destination.exists(), "Snapshot destination must be new")
    sources, metadata, envelope = request["sources"], request["metadata"], request["envelope"]
    require(len(sources) == request["expected_source_count"] and len(envelope) == request["expected_envelope_count"], "Declared scope denominator differs")
    source_by_path = {row["path"]: row for row in sources}
    metadata_by_path = {row["path"]: row for row in metadata}
    require(len(source_by_path) == len(sources) and len(metadata_by_path) == len(metadata)
            and not set(source_by_path) & set(metadata_by_path), "Distinct explicit source/metadata declarations required")
    require(len({row["path"] for row in envelope}) == len(envelope), "Envelope declaration denominator must not be deduplicated")
    external = list(request["external"])
    external_by_path = {row["path"]: row for row in external}
    require(len(external_by_path) == len(external), "Explicit external declarations must have unique paths")
    require(not set(external_by_path) & (set(source_by_path) | set(metadata_by_path)), "External bytes must not also be a content-read scope")
    for binding in request["bindings"]:
        origin = binding["origin"]
        if origin in source_by_path:
            record = source_by_path[origin]
            require(binding["sha256"] == record["sha256"] and binding["resolved"] == record["resolved_path"], "Source import binding differs")
        else:
            require(origin in external_by_path and binding["sha256"] == external_by_path[origin]["sha256"], "Import origin is absent from source/external declaration")
            require(str(Path(origin).resolve(strict=False)) == binding["resolved"], "External import alias target differs")
    for row in envelope:
        require(valid_hash(row["sha256"]), "Original envelope hash required")
        if row["category"] == "source":
            require(row["path"] in source_by_path and source_by_path[row["path"]]["sha256"] == row["sha256"], "Envelope source absent or pin differs")
        elif row["path"] not in metadata_by_path:
            external.append(dict(row, reason="Sealed upstream non-source entry outside explicit current metadata scope"))
        else:
            require(metadata_by_path[row["path"]]["sha256"] == row["sha256"], "Envelope metadata pin differs")
    limit = request["limits"]
    require(set(limit) == {"file_bytes", "total_bytes"} and all(type(v) is int and v > 0 for v in limit.values()), "Explicit bounded byte limits required")
    source_bytes, metadata_bytes, source_rows, metadata_rows, edges = {}, {}, [], [], []
    total = 0
    for record in sources:
        source_resolution(record, roots)
        raw = bounded_read(record["path"], record["sha256"], min(limit["file_bytes"], limit["total_bytes"] - total))
        source_resolution(record, roots)
        total += len(raw)
        name = member_name(Path(record["path"]), roots)
        require(name not in source_bytes, "Source member collision")
        source_bytes[name] = raw
        source_rows.append(dict(record, member=name, bytes=len(raw), alias=record["path"] != record["resolved_path"]))
    internal = {**source_by_path, **metadata_by_path}
    for record in metadata:
        path = Path(record["path"])
        require(path.is_absolute() and path.resolve(strict=True) == path and in_roots(path, roots)
                and path.suffix == ".json", "Explicit canonical JSON metadata required")
        raw = bounded_read(path, record["sha256"], min(limit["file_bytes"], limit["total_bytes"] - total))
        total += len(raw)
        name = member_name(path, roots)
        require(name not in metadata_bytes, "Metadata member collision")
        metadata_bytes[name] = raw
        metadata_rows.append(dict(record, member=name, bytes=len(raw)))
        for edge in scan_references(json.loads(raw)):
            observed = resolve_edge(edge, record["relative_base"])
            observed["document"] = dict(path=record["path"], sha256=record["sha256"])
            target = observed.get("resolved_declaration")
            if observed["kind"] == "pin" and target in internal:
                require(observed["sha256"] == internal[target]["sha256"], "Internal edge original pin differs")
                observed["collection"] = "explicit_scope"
            else:
                observed["collection"] = "external"
                observed["boundary_reason"] = "Outside explicit finite scope or unresolved declaration; no recursive traversal"
                if isinstance(observed.get("target"), str):
                    external.append(dict(path=target or observed["target"], sha256=observed.get("sha256"),
                                         category="one_hop_external_reference", reason=observed["boundary_reason"]))
            edges.append(observed)
    require(total <= limit["total_bytes"], "Total snapshot limit exceeded")
    # Check path/target and content again before accepting copies; never open externals.
    for record in sources:
        source_resolution(record, roots)
        bounded_read(record["path"], record["sha256"], limit["file_bytes"])
        source_resolution(record, roots)
    for record in metadata:
        require(Path(record["path"]).resolve(strict=True) == Path(record["path"]), "Metadata path changed")
        bounded_read(record["path"], record["sha256"], limit["file_bytes"])
    external_pins = {path: row["sha256"] for path, row in internal.items()}
    for row in external:
        if valid_hash(row.get("sha256")):
            require(row["path"] not in external_pins or external_pins[row["path"]] == row["sha256"], "Conflicting external original pins")
            external_pins[row["path"]] = row["sha256"]
    external_index = [external_observation(row, roots) for row in external]
    destination.mkdir(parents=True, exist_ok=False)
    write_zip(destination / "private-source.zip", source_bytes)
    write_zip(destination / "private-metadata.zip", metadata_bytes)
    for name, value in (("source-members.json", source_rows), ("metadata-members.json", metadata_rows),
                        ("one-hop-edges.json", edges), ("external-index.json", external_index), ("envelope-index.json", envelope)):
        save_new(destination / name, encode(value))
    receipt = dict(schema=2, purpose="private_finite_reproduction_snapshot", source_references=len(source_rows),
                   metadata_documents=len(metadata_rows), envelope_references=len(envelope), one_hop_edges=len(edges),
                   external_records=len(external_index), original_text_bytes=total, explicit_source_bytes_verified=True,
                   explicit_metadata_bytes_verified=True, full_dependency_closure_complete=False,
                   final_proofs_complete=False, raw_or_native_rehashed=False, publicly_distributable=False,
                   scientific_reproduction_verified=False, artifacts={})
    for path in sorted(destination.iterdir()):
        receipt["artifacts"][path.name] = dict(sha256=digest(path.read_bytes()), bytes=path.stat().st_size)
    save_new(destination / "receipt.json", encode(receipt))
    return receipt
