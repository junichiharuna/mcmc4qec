"""Verify saved low-noise analysis groups against their accepted sampling index."""
import argparse
import itertools
import json
import os
from pathlib import Path
import re
import socket
import tarfile
import time

import tile_low_noise_archive as sampling

META_NAMES = {'manifest':'manifest.json', 'analysis_manifest':'analysis_manifest.json',
              'sampling_index':'sampling-input-sha256.json'}


def valid_hash(value):
    return isinstance(value, str) and re.fullmatch('[0-9a-f]{64}', value) is not None


def expected_analysis(plan, context, sampling_index, case, target_index, manifest_sha256):
    tasks = sampling.expected_sampling(plan, case, target_index)
    required = {'manifest.json'} | {stem+ext for stem in tasks for ext in ('.json','.npz','.done.json')}
    sampling.require(isinstance(sampling_index, dict) and set(sampling_index) == required
        and sampling_index.get('manifest.json') == manifest_sha256
        and all(valid_hash(value) for value in sampling_index.values()), 'complete fixed sampling file index required')
    sampling.require(isinstance(context, dict) and context.get('schema') == 1
        and context.get('purpose') == 'low_noise_analysis'
        and context.get('sampling_manifest') == sampling.digest(sampling.canonical(plan))
        and type(context.get('replicates')) is int and context['replicates'] == plan['replicates']
        and type(context.get('seed_stage')) is int and context['seed_stage'] == 153
        and plan.get('stages', {}).get('analysis') == 153, 'fixed production analysis context required')
    analysis = sampling.digest(sampling.canonical(context))
    result = {}
    for kernel, initial, rep in itertools.product(range(2), range(2), range(plan['replicates'])):
        group = (case, target_index, kernel, initial, rep)
        inputs = {}
        for rung, chain in itertools.product(range(len(plan['condition']['rungs'])), range(plan['condition']['chains'])):
            name = '-'.join(map(str, (*group, rung, chain)))
            inputs['sample/'+name] = sampling_index['traces/'+name+'.done.json']
        anchor = '-'.join(map(str, (case, target_index, 0, 0, rep, 0, 0)))
        inputs['anchors/'+anchor] = sampling_index['anchors/'+anchor+'.done.json']
        result['analysis/'+'-'.join(map(str, group))] = dict(
            analysis=analysis, group=list(group), input_artifact_markers=inputs)
    return result


def accepted_names(index, expected, pins):
    names = set(META_NAMES.values()) | {stem+ext for stem in expected for ext in ('.json','.npz','.done.json')}
    sampling.require(isinstance(index, dict) and set(index) == names
        and all(valid_hash(value) for value in index.values())
        and all(index[member] == pins[name] for name,member in META_NAMES.items()), 'complete fixed analysis file index required')
    return names


def verify(*, archive, manifest, analysis_manifest, sampling_index, file_index,
           archive_sha256, manifest_sha256, analysis_manifest_sha256,
           sampling_index_sha256, file_index_sha256, case, target_index):
    paths = dict(archive=Path(archive), manifest=Path(manifest), analysis_manifest=Path(analysis_manifest),
                 sampling_index=Path(sampling_index), file_index=Path(file_index))
    pins = dict(archive=archive_sha256, manifest=manifest_sha256, analysis_manifest=analysis_manifest_sha256,
                sampling_index=sampling_index_sha256, file_index=file_index_sha256)
    sampling.require(all(valid_hash(value) for value in pins.values()), 'external SHA-256 pins required')
    sampling.require(len({str(path.resolve()) for path in paths.values()}) == len(paths), 'distinct inputs required')
    before = {name:sampling.snapshot(path) for name,path in paths.items()}
    raw = {name:path.read_bytes() for name,path in paths.items() if name != 'archive'}
    sampling.require(all(sampling.digest(value) == pins[name] for name,value in raw.items()), 'external metadata hash differs')
    values = {name:json.loads(value) for name,value in raw.items()}
    expected = expected_analysis(values['manifest'], values['analysis_manifest'], values['sampling_index'],
                                 case, target_index, manifest_sha256)
    index = values['file_index']
    accepted_names(index, expected, pins)
    result = sampling.archive_check.verify(paths['archive'], expected)
    sampling.require(result['archive_sha256'] == archive_sha256, 'external archive hash differs')
    sampling.require(result['payload_sha256'] == index, 'archive differs from accepted analysis index')
    sampling.require({name:sampling.snapshot(path) for name,path in paths.items()} == before,
                     'input identity changed during analysis recovery')
    sampling.require(all(paths[name].read_bytes() == value for name,value in raw.items()),
                     'input content changed during analysis recovery')
    return dict(case=case, target_index=target_index, archive_sha256=archive_sha256,
        manifest_sha256=manifest_sha256, analysis_manifest_sha256=analysis_manifest_sha256,
        sampling_index_sha256=sampling_index_sha256, file_index_sha256=file_index_sha256,
        groups=len(expected), files=result['files'], sampling_payloads_rehashed=False, numerical_reanalysis=False,
        scope='Complete saved analysis groups and bytes, tied to every accepted sampling/anchor marker. '
              'The accepted sampling index is an external boundary; no raw sampling rehash, decoder, ACF or BAR execution.')


def analysis_census(root):
    folder = root/'analysis'
    sampling.require(folder.is_dir() and folder.resolve() == folder, 'ordinary analysis directory required')
    return {path.relative_to(root).as_posix() for path in folder.iterdir()}


def export_analysis(*, root, output, manifest_sha256, analysis_manifest_sha256,
                    sampling_index, sampling_index_sha256, file_index, file_index_sha256, case, target_index):
    job = os.environ.get('PBS_JOBID', '')
    sampling.require(re.fullmatch(r'\d+(?:\.[A-Za-z0-9_.-]+)?', job), 'PBS allocation required')
    root, output = Path(root).absolute(), Path(output).absolute()
    sampling.require(root.is_dir() and root.resolve() == root, 'ordinary source root required')
    sampling.require(not output.exists() and not output.is_symlink() and output.resolve() == output, 'fresh output required')
    sampling.require(not output.is_relative_to(root) and not root.is_relative_to(output), 'separate export directory required')
    start, cpu = time.perf_counter(), time.process_time()
    paths = dict(manifest=root/'manifest.json', analysis_manifest=root/'analysis_manifest.json',
                 sampling_index=Path(sampling_index).absolute(), file_index=Path(file_index).absolute())
    pins = dict(manifest=manifest_sha256, analysis_manifest=analysis_manifest_sha256,
                sampling_index=sampling_index_sha256, file_index=file_index_sha256)
    sampling.require(all(valid_hash(value) for value in pins.values()), 'external metadata pins required')
    sampling.require(len({str(path.resolve()) for path in paths.values()}) == len(paths), 'distinct metadata inputs required')
    meta_before = {name:sampling.snapshot(path) for name,path in paths.items()}
    raw = {name:path.read_bytes() for name,path in paths.items()}
    sampling.require(all(sampling.digest(value) == pins[name] for name,value in raw.items()), 'fixed metadata differs')
    values = {name:json.loads(value) for name,value in raw.items()}
    expected = expected_analysis(values['manifest'], values['analysis_manifest'], values['sampling_index'],
                                 case, target_index, manifest_sha256)
    index = values['file_index']
    names = accepted_names(index, expected, pins)
    artifact_names = names - set(META_NAMES.values())
    code = [Path(__file__), Path(sampling.__file__), Path(sampling.archive_check.__file__)]
    code_before = {str(path.resolve()):dict(identity=sampling.snapshot(path),sha256=sampling.file_hash(path)) for path in code}
    output.mkdir()
    sampling.save_new(output/'export-intent.json', dict(pbs_job_id=job,hostname=socket.gethostname(),
        source=str(root),case=case,target_index=target_index,metadata_sha256=pins,source_pins=code_before,qsub=False))
    sampling.require(analysis_census(root) == artifact_names, 'analysis artifact census differs')
    source_paths = {name:root/name for name in artifact_names}
    source_paths.update({member:paths[name] for name,member in META_NAMES.items()})
    before = {name:sampling.snapshot(path) for name,path in source_paths.items()}
    sampling.require({name:sampling.file_hash(path) for name,path in source_paths.items()} == index,
                     'source differs from accepted final analysis index')
    for stem, identity in expected.items():
        marker = json.loads((root/(stem+'.done.json')).read_bytes())
        sampling.require(marker.get('identity') == identity and set(marker.get('sha256', {})) == {'.json','.npz'}
            and all(index[stem+ext] == value for ext,value in marker['sha256'].items()), 'analysis marker/input binding differs')
    archive = output/'analysis.tar.gz'
    with archive.open('xb') as compressed:
        with tarfile.open(fileobj=compressed, mode='w:gz', compresslevel=1) as stream:
            for name in sorted(names):stream.add(source_paths[name],arcname=name,recursive=False)
    sampling.require({name:sampling.snapshot(path) for name,path in source_paths.items()} == before,
                     'source identity changed during compression')
    sampling.require({name:sampling.file_hash(path) for name,path in source_paths.items()} == index,
                     'source bytes changed during compression')
    for name,member in META_NAMES.items():
        with (output/member).open('xb') as stream:stream.write(raw[name])
    with (output/'input_sha256.json').open('xb') as stream:stream.write(raw['file_index'])
    checked = verify(archive=archive, manifest=output/'manifest.json', analysis_manifest=output/'analysis_manifest.json',
        sampling_index=output/'sampling-input-sha256.json', file_index=output/'input_sha256.json',
        archive_sha256=sampling.file_hash(archive), manifest_sha256=manifest_sha256,
        analysis_manifest_sha256=analysis_manifest_sha256, sampling_index_sha256=sampling_index_sha256,
        file_index_sha256=file_index_sha256, case=case, target_index=target_index)
    sampling.require(analysis_census(root) == artifact_names
        and {name:sampling.snapshot(path) for name,path in source_paths.items()} == before,
        'source changed during final archive verification')
    sampling.require({name:sampling.snapshot(path) for name,path in paths.items()} == meta_before
        and all(path.read_bytes() == raw[name] for name,path in paths.items()), 'metadata changed during export')
    sampling.require({str(path.resolve()):dict(identity=sampling.snapshot(path),sha256=sampling.file_hash(path)) for path in code} == code_before,
                     'export source code changed')
    result = dict(case=case,target_index=target_index,source=str(root),pbs_job_id=job,hostname=socket.gethostname(),
        verification=checked,accepted_file_index_sha256=file_index_sha256,archive_bytes=archive.stat().st_size,
        source_unchanged=True,pbs_terminal_verified=False,
        source_sha256={name:item['sha256'] for name,item in code_before.items()},
        wall_seconds=time.perf_counter()-start,cpu_seconds=time.process_time()-cpu,
        scope='All accepted saved analysis bytes and sampling-marker links exported. '
              'Upstream provenance, PBS terminal and local transfer still require separate acceptance; no numerical reanalysis.')
    sampling.save_new(output/'export.json',result)
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('archive','manifest','analysis-manifest','sampling-index','file-index'):
        parser.add_argument('--'+name, type=Path, required=True)
        parser.add_argument('--'+name+'-sha256', required=True)
    parser.add_argument('--case', type=int, required=True)
    parser.add_argument('--target-index', type=int, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = vars(parser.parse_args())
    output = args.pop('output')
    sampling.require(not output.exists() and not output.is_symlink(), 'existing verification output')
    result = verify(**args)
    sampling.save_new(output, result)
    print(json.dumps(result))


if __name__ == '__main__':
    main()
