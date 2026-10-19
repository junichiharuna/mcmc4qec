"""Validate saved WSS source provenance across immutable deployment roots."""
from pathlib import Path
import re
import stat


def require(condition, message):
    if not condition:
        raise ValueError(message)


def reference_sources(saved, current, saved_root, current_root, proof):
    """Check both byte sets and preserve both original absolute-path bindings."""
    relative_maps = []
    for mapping, root in ((saved, saved_root), (current, current_root)):
        root = Path(root)
        require(root.is_absolute() and root.name == 'cluster_scripts', 'explicit absolute source root required')
        require(root.resolve(strict=True) == root and not root.is_symlink(), 'source root alias differs')
        require(isinstance(mapping, dict) and bool(mapping), 'nonempty reference source map required')
        relative = {}
        for name, expected in mapping.items():
            require(isinstance(name, str) and isinstance(expected, str)
                    and re.fullmatch('[0-9a-f]{64}', expected), 'exact source path/hash pin required')
            path = Path(name)
            require(path.is_absolute() and '..' not in path.parts and path.parent == root
                    and path.suffix == '.py', 'source path outside direct Python children')
            before = path.lstat()
            require(stat.S_ISREG(before.st_mode) and path.resolve(strict=True) == path,
                    'regular non-symlink source required')
            actual = proof.track(path)
            after = path.lstat()
            fields = ('st_dev', 'st_ino', 'st_size', 'st_mtime_ns', 'st_mode')
            require(all(getattr(before, field) == getattr(after, field) for field in fields)
                    and path.resolve(strict=True) == path, 'source changed while consumed')
            require(actual == expected, 'source bytes differ from saved pin')
            require(path.name not in relative, 'duplicate source relative name')
            relative[path.name] = expected
        relative_maps.append(relative)
    require(relative_maps[0] == relative_maps[1], 'reference source content or relative census differs')


def reference_source_context(saved_sources, current_sources, audit_root, api, proof):
    """Metadata-only mapping; never call a native probe or read raw payloads."""
    saved_root = Path(audit_root).parent.parent / 'cluster_scripts'
    current_root = Path(api.reference.__file__).resolve().parent
    reference_sources(saved_sources, current_sources, saved_root, current_root, proof)
    sources = dict(api.audit.source_hashes())
    require(bool(sources) and all(current_sources.get(path) == value for path, value in sources.items()),
            'current audit sources outside checked source plan')
    return dict(saved_root=saved_root, current_root=current_root, sources=sources)


def reference_context(saved, audit_root, root, api, proof):
    """Replay the existing native/metadata contract, permitting only source paths."""
    current = api.reference.make_plan(root, api.audit.read_evidence(root))
    binding = reference_source_context(saved['source_sha256'], current['source_sha256'], audit_root, api, proof)
    require(api.c.canonical(dict(current, source_sha256=saved['source_sha256'])) == api.c.canonical(saved),
            'saved WSS context differs beyond proven source relocation')
    return binding
