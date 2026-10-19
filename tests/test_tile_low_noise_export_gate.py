"""The export gate binds accepted comparison evidence without reading traces."""
import hashlib
import importlib.util
import json
from pathlib import Path

import pytest

PATH = Path(__file__).resolve().parents[1]/'cluster_scripts/tile_low_noise_export_gate.py'
spec = importlib.util.spec_from_file_location('low_export_gate', PATH)
gate = importlib.util.module_from_spec(spec)
spec.loader.exec_module(gate)


def write(path, value):
    raw = json.dumps(value, sort_keys=True).encode()
    path.write_bytes(raw)
    return dict(path=str(path.resolve()), sha256=hashlib.sha256(raw).hexdigest())


@pytest.fixture
def context(tmp_path):
    source = tmp_path/'source'; source.mkdir()
    manifest = write(source/'manifest.json', dict(purpose='low_noise_production', case=2,target_index=0))
    plan = json.loads((source/'manifest.json').read_bytes())
    md = hashlib.sha256(json.dumps(plan,sort_keys=True,separators=(',',':')).encode()).hexdigest()
    completion = write(tmp_path/'completion.json',dict(job_id='20.test',manifest=md,replicates=192,groups=768,rows=67584,
        report=dict(sha256='d'*64),current_trace_payloads_rehashed=True))
    accepted = write(tmp_path/'accepted.json',dict(status='accepted',job_id='20.test',completion=completion,
        report=dict(sha256='d'*64)))
    index = write(tmp_path/'accepted-index.json',{'manifest.json':manifest['sha256']})
    runtime = tmp_path/'python'; runtime.write_bytes(b'python')
    config = dict(case=2,target_index=0,source=str(source.resolve()),manifest=manifest,
        final_completion=completion,accepted=accepted,accepted_index=index,
        python=dict(path=str(runtime.resolve()),sha256=hashlib.sha256(b'python').hexdigest()),
        source_sha256={},jobs={'10.test':str(tmp_path/'sampling.sh'),'20.test':str(tmp_path/'report.sh')},
        sampling_job='10.test',final_job='20.test',manifest_digest=md,report_sha256='d'*64)
    statuses = {job:dict(job_state='F',Exit_status=0,run_count=1,Submit_arguments=script) for job,script in config['jobs'].items()}
    return config,statuses


def test_saved_metadata_gate_has_no_trace_dependency(context):
    config,statuses=context
    value=gate.check(config, query=lambda job: statuses[job])
    assert value['case']==2 and value['target_index']==0
    assert value['pbs']==statuses and value['raw_trace_scan'] is False


@pytest.mark.parametrize('field', ['manifest','final_completion','accepted','accepted_index','python'])
def test_fixed_input_changes_rejected(context, field):
    config,statuses=context
    Path(config[field]['path']).write_bytes(b'changed')
    with pytest.raises(ValueError):gate.check(config,query=lambda job:statuses[job])


@pytest.mark.parametrize('key,value', [('job_state','R'),('Exit_status',1),('run_count',2),('Submit_arguments','other.sh')])
def test_actual_pbs_terminal_required(context,key,value):
    config,statuses=context
    statuses['20.test'][key]=value
    with pytest.raises(ValueError):gate.check(config,query=lambda job:statuses[job])


@pytest.mark.parametrize('key,value',[('case',1),('target_index',2),('manifest_digest','0'*64),('report_sha256','0'*64)])
def test_condition_and_report_are_bound(context,key,value):
    config,statuses=context
    config[key]=value
    with pytest.raises(ValueError):gate.check(config,query=lambda job:statuses[job])


def test_source_python_files_are_pinned(context,tmp_path):
    config,statuses=context
    helper=tmp_path/'helper.py';helper.write_bytes(b'fixed')
    config['source_sha256']={str(helper.resolve()):hashlib.sha256(b'fixed').hexdigest()}
    gate.check(config,query=lambda job:statuses[job])
    helper.write_bytes(b'changed')
    with pytest.raises(ValueError):gate.check(config,query=lambda job:statuses[job])
