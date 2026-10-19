"""Smoke test every top-level example against the package imported by pytest."""
import json
import os
from pathlib import Path
import subprocess
import sys

import mcmc4qec
import pytest


ROOT = Path(__file__).resolve().parents[1]
SPECS = [
    ('bit_flip.py', (), {'exact', 'pl', 'pl_interval', 'ew_exact', 'ew_chain'}),
    ('three_noise.py', (), {'cases'}),
    ('bar_ladder.py', (), {'ladder', 'bar', 'intervals', 'exact'}),
    ('toric_pymatching.py', ('pymatching', 'ldpc', 'bposd'),
     {'code', 'p', 'pl', 'pl_interval', 'ew_direct', 'ew_chain'}),
    ('stim_dem.py', ('stim',), {'mechanisms', 'exact', 'pl', 'pl_interval'}),
    ('circuit_baseline.py', ('stim', 'pymatching'),
     {'locations', 'detectors', 'pl', 'pl_interval'}),
    ('bb72_bposd.py', ('ldpc',),
     {'code', 'p', 'pl', 'pl_interval', 'ew_direct', 'ew_chain'}),
    ('tile_bposd.py', ('ldpc',),
     {'code', 'n', 'k', 'p', 'pl', 'pl_interval', 'conditional_weight'}),
    ('toric_depolarizing.py', ('pymatching', 'ldpc', 'bposd'),
     {'code', 'p', 'pl', 'pl_interval', 'ew_direct', 'ew_chain'}),
    ('phenomenological_toric.py', ('pymatching', 'ldpc', 'bposd'),
     {'code', 'rounds', 'p', 'pl', 'pl_interval'}),
    ('steane_exact.py', (), {'code', 'ladder', 'exact', 'bar', 'bar_intervals'}),
]


@pytest.mark.parametrize('script,dependencies,keys', SPECS)
def test_example(script, dependencies, keys, tmp_path):
    for dependency in dependencies:
        pytest.importorskip(dependency)
    # Point children at the same imported package, including installed-wheel runs.
    package_root = Path(mcmc4qec.__file__).resolve().parent.parent
    env = os.environ.copy()
    env['PYTHONPATH'] = str(package_root)
    out = tmp_path / Path(script).stem
    result = subprocess.run([sys.executable, str(ROOT / 'examples' / script),
                             '--quick', '--seed', '2', '--out', str(out)],
                            cwd=ROOT, env=env, text=True, capture_output=True, timeout=30)
    assert result.returncode == 0, result.stdout + result.stderr
    lines = result.stdout.splitlines()
    assert lines and lines[-1].startswith('SUMMARY '), result.stdout
    summary = json.loads(lines[-1].removeprefix('SUMMARY '))
    assert set(summary) == keys
    assert json.loads((out / 'summary.json').read_text(encoding='utf-8')) == summary


def test_research_output_is_rejected(tmp_path):
    target = tmp_path / 'research' / 'example'
    env = os.environ.copy()
    env['PYTHONPATH'] = str(Path(mcmc4qec.__file__).resolve().parent.parent)
    env['RIMC_RESEARCH_ROOT'] = str(tmp_path / 'research')
    result = subprocess.run([sys.executable, str(ROOT / 'examples' / 'bar_ladder.py'),
                             '--quick', '--out', str(target)], cwd=ROOT, env=env,
                            text=True, capture_output=True, timeout=30)
    assert result.returncode != 0
    assert 'research repository' in result.stderr
    assert not target.exists()
