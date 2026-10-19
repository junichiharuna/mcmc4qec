"""Read-only metadata gate for exporting a formally compared low-noise case."""
import hashlib
import json
from pathlib import Path
import re
import stat
import subprocess


def require(ok, message):
    if not ok:
        raise ValueError(message)


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()


def identity(path):
    path = Path(path)
    require(path.is_absolute() and path.resolve() == path, 'fixed absolute file path required')
    value = path.lstat()
    require(stat.S_ISREG(value.st_mode), 'regular input required')
    return (value.st_dev, value.st_ino, value.st_size, value.st_mtime_ns, value.st_mode)


def query_pbs(job):
    require(isinstance(job, str) and re.fullmatch(r'\d+(?:\.[A-Za-z0-9_.-]+)?', job), 'invalid PBS job id')
    result = subprocess.run(['qstat','-x','-f','-F','json',job], capture_output=True, check=True, timeout=30)
    raw = json.loads(result.stdout)['Jobs'][job]
    return {key: raw.get(key) for key in ('job_state','Exit_status','run_count','Submit_arguments')}


def check(config, *, query=query_pbs):
    require(type(config.get('case')) is int and config['case'] in range(4)
            and type(config.get('target_index')) is int and config['target_index'] in range(3), 'invalid condition')
    pins = {item['path']: item['sha256'] for item in
            (config[name] for name in ('manifest','final_completion','accepted','accepted_index','python'))}
    for path, value in config['source_sha256'].items():
        require(path not in pins or pins[path] == value, 'conflicting input pins')
        pins[path] = value
    before, payload = {}, {}
    for path, expected in pins.items():
        require(isinstance(expected, str) and re.fullmatch('[0-9a-f]{64}', expected), 'external file SHA required')
        before[path] = identity(path)
        raw = Path(path).read_bytes()
        require(digest(raw) == expected and identity(path) == before[path], 'fixed metadata/source changed')
        payload[path] = raw
    plan = json.loads(payload[config['manifest']['path']])
    require(Path(config['source']).is_absolute() and Path(config['source']).resolve() == Path(config['source'])
            and config['manifest']['path'] == str(Path(config['source'])/'manifest.json'), 'source manifest path differs')
    require(plan.get('purpose') == 'low_noise_production' and plan.get('case') == config['case']
            and plan.get('target_index') == config['target_index']
            and digest(canonical(plan)) == config['manifest_digest'], 'fixed production manifest differs')
    accepted = json.loads(payload[config['accepted']['path']])
    completed = json.loads(payload[config['final_completion']['path']])
    require(accepted.get('status') == 'accepted' and accepted.get('job_id') == config['final_job']
            and accepted.get('completion') == config['final_completion']
            and accepted.get('report', {}).get('sha256') == config['report_sha256'], 'formal acceptance differs')
    require(completed.get('job_id') == config['final_job'] and completed.get('manifest') == config['manifest_digest']
            and completed.get('report', {}).get('sha256') == config['report_sha256']
            and completed.get('replicates') == 192 and completed.get('groups') == 768
            and completed.get('rows') == 67584, 'formal completion differs')
    require(config['sampling_job'] in config['jobs'] and config['final_job'] in config['jobs'], 'both upstream jobs required')
    pbs = {}
    for job, script in config['jobs'].items():
        value = query(job)
        require(value.get('job_state') == 'F' and value.get('Exit_status') == 0
                and value.get('run_count') == 1 and value.get('Submit_arguments') == script,
                'upstream PBS terminal/script differs')
        pbs[job] = value
    for path, expected in pins.items():
        require(identity(path) == before[path] and digest(Path(path).read_bytes()) == expected,
                'metadata/source changed during gate')
    require({job: query(job) for job in config['jobs']} == pbs, 'PBS terminal changed during gate')
    return dict(case=config['case'], target_index=config['target_index'], source=config['source'],
                manifest=config['manifest_digest'], files=pins, pbs=pbs, raw_trace_scan=False,
                scope='Saved final comparison/acceptance and upstream terminal metadata only; '
                      'export must separately verify every archive member against the accepted file index.')
