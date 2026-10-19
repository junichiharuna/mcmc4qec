"""The worker accepts only an archive matching the prior comparison index."""
import hashlib
import json
from pathlib import Path
import sys

import pytest

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'cluster_scripts'))
import tile_low_noise_export_worker as worker
from test_tile_low_noise_archive import source_fixture


def save(path,value):
    raw=json.dumps(value,sort_keys=True).encode();path.write_bytes(raw)
    return hashlib.sha256(raw).hexdigest()


@pytest.fixture
def prepared(tmp_path,monkeypatch):
    source=source_fixture(tmp_path)
    root=tmp_path/'worker';root.mkdir()
    (root/'worker.py').write_bytes(b'fixture')
    monkeypatch.setattr(worker,'__file__',str(root/'worker.py'))
    monkeypatch.setenv('PBS_JOBID','42.test')
    index=tmp_path/'input_sha256.json'
    config=dict(source=str(source['root']),case=2,target_index=1,
        manifest=dict(path=str(source['root']/'manifest.json'),sha256=source['manifest_sha256']),
        accepted_index=dict(path=str(index),sha256=hashlib.sha256(index.read_bytes()).hexdigest()),
        python=dict(path=str(Path(sys.executable).resolve())))
    stage=dict(target=str(root),qsub_executed=False,config=config,gate={'fixed':'gate'})
    stage_sha=save(root/'stage.json',stage)
    (root/'export.sh').write_bytes(b'script')
    save(root/'submission-intent.json',dict(stage_sha256=stage_sha,command=['qsub',str(root/'export.sh')],
        script_sha256=hashlib.sha256(b'script').hexdigest()))
    monkeypatch.setattr(worker.gate,'check',lambda _: {'fixed':'gate'})
    monkeypatch.setattr(worker.gate,'query_pbs',lambda _:dict(job_state='R',run_count=1,Submit_arguments=str(root/'export.sh')))
    return root,stage


def test_worker_accepts_external_index_and_seals_once(prepared):
    root,stage=prepared
    result=worker.run_worker()
    assert result['status']=='complete' and result['verification']['artifacts']==34
    assert result['accepted_index_sha256']==stage['config']['accepted_index']['sha256']
    assert (root/'completion.json').exists()
    with pytest.raises(ValueError):worker.run_worker()


def test_self_consistent_export_cannot_replace_accepted_data(prepared):
    root,stage=prepared
    index=Path(stage['config']['accepted_index']['path'])
    value=json.loads(index.read_bytes());value['traces/2-1-0-0-0-0-0.npz']='0'*64
    stage['config']['accepted_index']['sha256']=save(index,value)
    stage_sha=save(root/'stage.json',stage)
    intent=json.loads((root/'submission-intent.json').read_bytes());intent['stage_sha256']=stage_sha
    save(root/'submission-intent.json',intent)
    with pytest.raises(ValueError):worker.run_worker()
    assert (root/'data/export.json').exists()
    assert not (root/'completion.json').exists()


@pytest.mark.parametrize('mode',['no_pbs','changed_stage','wrong_script'])
def test_worker_rejects_bad_execution_context(prepared,monkeypatch,mode):
    root,stage=prepared
    if mode=='no_pbs':monkeypatch.delenv('PBS_JOBID')
    elif mode=='changed_stage':(root/'stage.json').write_bytes((root/'stage.json').read_bytes()+b' ')
    else:monkeypatch.setattr(worker.gate,'query_pbs',lambda _:dict(job_state='R',run_count=1,Submit_arguments='wrong.sh'))
    with pytest.raises(ValueError):worker.run_worker()
    assert not (root/'completion.json').exists()
