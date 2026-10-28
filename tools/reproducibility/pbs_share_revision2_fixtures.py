"""Pinned synthetic exporter fixtures, authorized PBS execution only."""
import hashlib
import json
import os
from pathlib import Path
import sys
import unittest


def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    path=Path(sys.argv[1]);raw=path.read_bytes();assert hashlib.sha256(raw).hexdigest()==sys.argv[2]
    assert os.environ.get('PBS_JOBID') and not sys.flags.optimize
    request=json.loads(raw)
    def stable():
        assert path.read_bytes()==raw
        for pin in request['sources'].values():assert sha(pin['path'])==pin['sha256']
    stable();folder=Path(__file__).resolve().parent;sys.path.insert(0,str(folder))
    suite=unittest.defaultTestLoader.discover(str(folder),pattern='test_share_snapshot_v2_revision2.py')
    result=unittest.TextTestRunner(verbosity=2).run(suite);stable()
    assert result.wasSuccessful() and result.testsRun==29
    accepted=dict(purpose='share_snapshot_v2_revision2_fixture_acceptance',pbs_job_id=os.environ['PBS_JOBID'],
        tests_passed=result.testsRun,success=True,sources=request['sources'],
        request=dict(path=str(path),sha256=sys.argv[2]),actual_private_snapshot_exported=False,
        production_external_raw_native_files_read=False,scientific_reproduction_verified=False,public_distribution_performed=False)
    with path.with_name('accepted.json').open('x') as stream:json.dump(accepted,stream,indent=2)


if __name__=='__main__':main()
