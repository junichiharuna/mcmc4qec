"""Stream-verify low-noise sampling archives against externally pinned evidence.

This is a transfer/census check only. It neither runs decoders nor establishes
successful PBS completion, numerical correctness, mixing, or interval coverage.
"""
import argparse
import hashlib
import itertools
import json
import os
from pathlib import Path
import re
import socket
import stat
import tarfile
import time

import artifact_archive as archive_check


def require(ok, message):
    if not ok:
        raise ValueError(message)


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()


def positive(value):
    return type(value) is int and value > 0


def expected_sampling(plan, case, target_index):
    require(type(case) is int and case in range(4)
            and type(target_index) is int and target_index in range(3), 'invalid condition')
    require(plan.get('purpose') == 'low_noise_production'
            and type(plan.get('case')) is int and plan['case'] == case
            and type(plan.get('target_index')) is int and plan['target_index'] == target_index,
            'production manifest condition differs')
    require(positive(plan.get('replicates')), 'positive replicate count required')
    require(set(plan.get('kernels', {})) == {'ZH', 'ZHS'}
            and plan.get('initializations') == ['logical_basis', 'logical_combination'],
            'fixed low-noise kernels/initializations required')
    spec = plan.get('condition', {})
    require(positive(spec.get('chains')) and isinstance(spec.get('rungs'), list)
            and len(spec['rungs']) > 0, 'positive chain/rung dimensions required')
    manifest = digest(canonical(plan))
    result = {}
    for rep in range(plan['replicates']):
        task = (case, target_index, 0, 0, rep, 0, 0)
        result['anchors/' + '-'.join(map(str, task))] = dict(manifest=manifest, task=list(task))
    for tail in itertools.product(range(2), range(2), range(plan['replicates']),
                                  range(len(spec['rungs'])), range(spec['chains'])):
        task = (case, target_index, *tail)
        result['traces/' + '-'.join(map(str, task))] = dict(manifest=manifest, task=list(task))
    return result


def snapshot(path):
    path = Path(path).absolute()
    value = path.lstat()
    require(stat.S_ISREG(value.st_mode) and path.resolve() == path, 'ordinary fixed file required')
    return (str(path.resolve()), value.st_dev, value.st_ino, value.st_size,
            value.st_mtime_ns, value.st_mode)


def verify(*, archive, manifest, file_index, manifest_sha256, archive_sha256,
           file_index_sha256, case, target_index):
    paths = [Path(value) for value in (archive, manifest, file_index)]
    require(len({str(path.resolve()) for path in paths}) == 3, 'distinct input files required')
    for value in (manifest_sha256, archive_sha256, file_index_sha256):
        require(isinstance(value, str) and re.fullmatch('[0-9a-f]{64}', value), 'external SHA-256 required')
    before = [snapshot(path) for path in paths]
    raw_plan = paths[1].read_bytes()
    raw_index = paths[2].read_bytes()
    require(digest(raw_plan) == manifest_sha256, 'external manifest SHA differs')
    require(digest(raw_index) == file_index_sha256, 'external file index SHA differs')
    plan, index = json.loads(raw_plan), json.loads(raw_index)
    require(isinstance(index, dict) and index.get('manifest.json') == manifest_sha256,
            'archive index must include the fixed manifest')
    require(all(isinstance(name, str) and isinstance(value, str)
                and re.fullmatch('[0-9a-f]{64}', value) for name, value in index.items()),
            'invalid file index')
    expected = expected_sampling(plan, case, target_index)
    result = archive_check.verify(paths[0], expected)
    require(result['archive_sha256'] == archive_sha256, 'external archive SHA differs')
    require(result['payload_sha256'] == index, 'archive files differ from the external file index')
    require([snapshot(path) for path in paths] == before, 'input identity changed during recovery')
    require(paths[1].read_bytes() == raw_plan and paths[2].read_bytes() == raw_index,
            'input content changed during recovery')
    return dict(case=case, target_index=target_index, archive_sha256=archive_sha256,
                manifest_sha256=manifest_sha256, file_index_sha256=file_index_sha256,
                artifacts=result['artifacts'], files=result['files'],
                manifest_digest=digest(canonical(plan)), numerical_redecode=False,
                scope='Complete planned low-noise sampling/anchor artifact census and byte integrity only; '
                      'failed artifacts retained. No decoder replay, PBS completion or accuracy/coverage guarantee.')


def file_hash(path):
    with Path(path).open('rb') as stream:
        return archive_check.digest_stream(stream)


def save_new(path, value):
    with Path(path).open('xb') as stream:
        stream.write(canonical(value) + b'\n')


def artifact_census(root):
    observed = set()
    for folder in ('anchors', 'traces'):
        directory = root / folder
        require(directory.is_dir() and directory.resolve() == directory, 'ordinary artifact directory required')
        observed.update(path.relative_to(root).as_posix() for path in directory.iterdir())
    return observed


def export_sampling(*, root, output, manifest_sha256, case, target_index):
    job = os.environ.get('PBS_JOBID', '')
    require(re.fullmatch(r'\d+(?:\.[A-Za-z0-9_.-]+)?', job), 'PBS allocation required for export')
    root, output = Path(root).absolute(), Path(output).absolute()
    require(root.is_dir() and root.resolve() == root, 'ordinary source directory required')
    require(not output.exists() and not output.is_symlink() and output.resolve() == output,
            'fresh ordinary export directory required')
    require(not output.is_relative_to(root) and not root.is_relative_to(output),
            'source and export directories must be separate')
    start, cpu = time.perf_counter(), time.process_time()
    sources = [Path(__file__), Path(archive_check.__file__)]
    source_pins = {str(path.resolve()): dict(identity=snapshot(path), sha256=file_hash(path)) for path in sources}
    manifest = root / 'manifest.json'
    manifest_before = snapshot(manifest)
    raw_manifest = manifest.read_bytes()
    require(digest(raw_manifest) == manifest_sha256, 'external manifest SHA differs')
    expected = expected_sampling(json.loads(raw_manifest), case, target_index)
    output.mkdir()
    save_new(output/'export-intent.json', dict(pbs_job_id=job, hostname=socket.gethostname(),
        source=str(root), case=case, target_index=target_index, manifest_sha256=manifest_sha256,
        source_pins=source_pins, worker_sha256=source_pins[str(Path(__file__).resolve())]['sha256'], qsub=False))
    names = {stem + ext for stem in expected for ext in ('.json', '.npz', '.done.json')}
    require(artifact_census(root) == names, 'source artifact census differs')
    selected = ['manifest.json', *sorted(names)]
    before = {name: snapshot(root/name) for name in selected}
    require(before['manifest.json'] == manifest_before, 'source manifest changed')
    hashes = {name: file_hash(root/name) for name in selected}
    require(hashes['manifest.json'] == manifest_sha256, 'source manifest changed')
    for stem, identity in expected.items():
        marker = json.loads((root/(stem+'.done.json')).read_bytes())
        require(marker.get('identity') == identity and set(marker.get('sha256', {})) == {'.json', '.npz'},
                'source artifact marker differs')
        require(all(hashes[stem+ext] == value for ext, value in marker['sha256'].items()),
                'source artifact payload checksum differs')
    archive = output / 'sampling.tar.gz'
    with archive.open('xb') as raw:
        with tarfile.open(fileobj=raw, mode='w:gz', compresslevel=1) as stream:
            for name in selected:
                stream.add(root/name, arcname=name, recursive=False)
    require({name: snapshot(root/name) for name in selected} == before,
            'source identity changed during compression')
    require({name: file_hash(root/name) for name in selected} == hashes,
            'source content changed during compression')
    require({name: snapshot(root/name) for name in selected} == before,
            'source identity changed during final hash pass')
    index = output / 'input_sha256.json'
    save_new(index, hashes)
    with (output/'manifest.json').open('xb') as stream:
        stream.write(raw_manifest)
    checksum = file_hash(archive)
    checked = verify(archive=archive, manifest=output/'manifest.json', file_index=index,
        manifest_sha256=manifest_sha256, archive_sha256=checksum, file_index_sha256=file_hash(index),
        case=case, target_index=target_index)
    require(artifact_census(root) == names, 'source artifact census changed during export')
    require({str(path.resolve()): dict(identity=snapshot(path), sha256=file_hash(path)) for path in sources} == source_pins,
            'export source code changed')
    record = dict(case=case, target_index=target_index, source=str(root), archive=str(archive),
        archive_bytes=archive.stat().st_size, verification=checked, source_unchanged=True,
        source_identity_digest=digest(canonical(before)), pbs_job_id=job, hostname=socket.gethostname(),
        pbs_terminal_verified=False, source_sha256={path: pin['sha256'] for path, pin in source_pins.items()},
        worker_sha256=source_pins[str(Path(__file__).resolve())]['sha256'],
        wall_seconds=time.perf_counter()-start, cpu_seconds=time.process_time()-cpu,
        scope='Byte-preserving sampling/anchor export; submitter must separately bind sources and verify '
              'PBS terminal state. No decoder replay, numerical reanalysis, or scientific guarantee.')
    save_new(output/'export.json', record)
    return record


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('archive', 'manifest', 'file-index', 'output'):
        parser.add_argument('--' + name, type=Path, required=True)
    for name in ('manifest-sha256', 'archive-sha256', 'file-index-sha256'):
        parser.add_argument('--' + name, required=True)
    parser.add_argument('--case', type=int, required=True)
    parser.add_argument('--target-index', type=int, required=True)
    args = vars(parser.parse_args())
    output = args.pop('output')
    require(not output.exists() and not output.is_symlink(), 'existing recovery output')
    result = verify(**args)
    with output.open('x', encoding='utf8', newline='\n') as stream:
        json.dump(result, stream, sort_keys=True, indent=2)
        stream.write('\n')
    print(json.dumps(result))


if __name__ == '__main__':
    main()
