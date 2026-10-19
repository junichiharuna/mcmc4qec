"""PBS-only analysis export against the accepted final-comparison index."""
import argparse
import json
import os
from pathlib import Path
import re
import socket
import sys

import tile_low_noise_archive as archive
import tile_low_noise_analysis_archive as analysis
import tile_low_noise_export_gate as gate


def root():
    return Path(__file__).resolve().parent


def stage():
    folder = root()
    value = json.loads((folder / 'stage.json').read_bytes())
    archive.require(value['target'] == str(folder) and value['qsub_executed'] is False,
                    'fixed stage root required')
    return value


def check():
    config = stage()['config']
    archive.require(config['analysis_manifest']['path'] == str(Path(config['source']) / 'analysis_manifest.json'),
                    'analysis context path differs')
    for name in ('analysis_manifest', 'sampling_index'):
        pin = config[name]
        archive.require(config['source_sha256'].get(pin['path']) == pin['sha256'],
                        'analysis metadata missing from fixed gate')
    return gate.check(config)


def stable_gate(value):
    return value


def run_worker():
    job = os.environ.get('PBS_JOBID', '')
    archive.require(re.fullmatch(r'\d+(?:\.[A-Za-z0-9_.-]+)?', job), 'PBS allocation required')
    folder = root()
    archive.require(not any((folder / name).exists() or (folder / name).is_symlink()
        for name in ('execution.json', 'completion.json', 'data')), 'existing export execution; no automatic retry')
    prepared = stage()
    config = prepared['config']
    stage_sha = archive.file_hash(folder / 'stage.json')
    intent = json.loads((folder / 'submission-intent.json').read_bytes())
    archive.require(intent['stage_sha256'] == stage_sha
        and intent['command'] == ['qsub', str(folder / 'export.sh')]
        and intent['script_sha256'] == archive.file_hash(folder / 'export.sh'), 'fixed submission intent differs')
    archive.require(str(Path(sys.executable).resolve()) == config['python']['path'], 'running Python differs')
    own_pbs = gate.query_pbs(job)
    archive.require(own_pbs.get('job_state') == 'R' and own_pbs.get('run_count') == 1
        and own_pbs.get('Submit_arguments') == str(folder / 'export.sh'), 'own PBS execution differs')
    before = check()
    archive.require(before == prepared['gate'], 'prepared upstream gate changed')
    archive.save_new(folder / 'execution.json', dict(job_id=job, hostname=socket.gethostname(),
        stage_sha256=stage_sha, submission_intent_sha256=archive.file_hash(folder / 'submission-intent.json'),
        own_pbs=own_pbs, upstream=before))
    exported = analysis.export_analysis(root=config['source'], output=folder / 'data',
        manifest_sha256=config['manifest']['sha256'],
        analysis_manifest_sha256=config['analysis_manifest']['sha256'],
        sampling_index=config['sampling_index']['path'], sampling_index_sha256=config['sampling_index']['sha256'],
        file_index=config['accepted_index']['path'], file_index_sha256=config['accepted_index']['sha256'],
        case=config['case'], target_index=config['target_index'])
    after = check()
    archive.require(after == before and archive.file_hash(folder / 'stage.json') == stage_sha,
                    'prepared evidence changed during export')
    archive.require(gate.query_pbs(job) == own_pbs, 'own PBS execution changed during export')
    result = dict(status='complete', job_id=job, stage_sha256=stage_sha,
        verification=exported['verification'], accepted_index_sha256=config['accepted_index']['sha256'],
        export_sha256=archive.file_hash(folder / 'data/export.json'),
        execution_sha256=archive.file_hash(folder / 'execution.json'), upstream=after,
        scope='Archive matches the accepted final comparison analysis index and sampling-marker links. '
              'PBS terminal acceptance and local recovery are still required; no numerical reanalysis.')
    archive.save_new(folder / 'completion.json', result)
    return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=('check', 'worker'))
    args = parser.parse_args()
    print(json.dumps(check() if args.action == 'check' else run_worker()))
