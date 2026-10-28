"""Test the new finite scope builder in PBS, then collect fixed v9 metadata."""
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import sys
import unittest


def bounded(path):
    with Path(path).open('rb') as stream:raw=stream.read(4*1024**2+1)
    if len(raw)>4*1024**2:raise ValueError('Pinned source/authority exceeds bound')
    return raw


def main():
    stage=Path(sys.argv[1]);expected=sys.argv[2];path=stage/'staging-authority.json'
    raw=bounded(path);assert hashlib.sha256(raw).hexdigest()==expected and os.environ.get('PBS_JOBID')
    authority=json.loads(raw)
    def stable():
        assert bounded(path)==raw
        for p in authority['sources'].values():assert hashlib.sha256(bounded(p['path'])).hexdigest()==p['sha256']
        p=authority['library'];assert hashlib.sha256(bounded(p['path'])).hexdigest()==p['sha256']
    stable();folder=Path(__file__).resolve().parent;sys.path.insert(0,str(folder))
    os.environ['SNAPSHOT_FIXTURE_LIBRARY']=authority['library']['path']
    result=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.discover(str(folder),pattern='test_collect.py'))
    assert result.wasSuccessful() and result.testsRun==9;stable()
    with (stage/'scope-fixture-accepted.json').open('x') as f:
        json.dump(dict(tests_passed=9,pbs_job_id=os.environ['PBS_JOBID'],sources=authority['sources'],
            original_snapshot_library_tests_inherited=False,actual_collection_complete=False),f,indent=2)
    import collect
    sys.argv=[str(folder/'collect.py'),str(stage),authority['sources']['collect.py']['sha256']]
    collect.main();stable()


if __name__=='__main__':main()
