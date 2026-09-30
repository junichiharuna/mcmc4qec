"""Run the workflow examples against the package already imported by pytest."""

import ast
import csv
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys

import mcmc4qec
import pytest


ROOT = Path(__file__).resolve().parents[1]
WORKFLOWS = ROOT / 'examples' / 'workflows'
CASES = (
    ('pl_curve.py', {'codes', 'ladder', 'estimates', 'intervals', 'checks'}, 'matching'),
    ('conditional_weight.py', {'code', 'ps', 'ew_direct', 'ew_chain'}, 'matching'),
    ('convergence_check.py', {'code', 'p', 'checks', 'verdict', 'warnings'}, 'matching'),
    ('p_dependent_decoder.py', {'code', 'ladder', 'fixed', 'approx'}, 'codes'),
)


def run_example(script, out, *, extra=(), env_extra=None, seed=2026):
    env = os.environ.copy()
    package_parent = Path(mcmc4qec.__file__).resolve().parent.parent
    env['PYTHONPATH'] = os.pathsep.join([*(env_extra or []), str(package_parent)])
    completed = subprocess.run(
        [sys.executable, str(WORKFLOWS / script), '--quick', '--seed', str(seed),
         '--out', str(out), *extra],
        cwd=ROOT, env=env, capture_output=True, text=True, timeout=30,
    )
    assert completed.returncode == 0, completed.stdout + completed.stderr
    assert completed.stdout.splitlines()[0].startswith('Output: ')
    line = completed.stdout.splitlines()[-1]
    assert line.startswith('SUMMARY '), completed.stdout
    return json.loads(line.removeprefix('SUMMARY ')), completed.stdout


@pytest.mark.parametrize('script,keys,extra_name', CASES)
def test_workflow_quick(script, keys, extra_name, tmp_path):
    if extra_name == 'matching':
        pytest.importorskip('pymatching')
        pytest.importorskip('ldpc')
        pytest.importorskip('bposd')
    else:
        pytest.importorskip('ldpc')
        pytest.importorskip('bposd')
    summary, output = run_example(script, tmp_path / script.removesuffix('.py'),
                                  extra=('--demo-overlap',) if script == 'pl_curve.py' else ())
    assert set(summary) == keys
    directory = tmp_path / script.removesuffix('.py')
    assert list(directory.glob('*.csv'))
    if script in ('pl_curve.py', 'conditional_weight.py'):
        if importlib.util.find_spec('matplotlib') is not None:
            assert list(directory.glob('*.png'))
        else:
            assert 'matplotlib unavailable' in output
    if script == 'pl_curve.py':
        assert 'OverlapError from estimate_logical_error' in output
        with (directory / 'pl_curve.csv').open(newline='', encoding='utf-8') as stream:
            rows = list(csv.DictReader(stream))
        assert all(row['intervals_overlap'] in ('True', 'False') for row in rows)
        if any(row['intervals_overlap'] == 'False' for row in rows):
            assert 'WARNING: d=' in output


@pytest.mark.parametrize('script', ('pl_curve.py', 'conditional_weight.py'))
def test_plot_fallback_keeps_csv(script, tmp_path):
    pytest.importorskip('pymatching')
    pytest.importorskip('ldpc')
    pytest.importorskip('bposd')
    shadow = tmp_path / 'shadow'
    shadow.mkdir()
    (shadow / 'sitecustomize.py').write_text(
        'import builtins\n'
        '_original_import = builtins.__import__\n'
        'def _without_pyplot(name, *args, **kwargs):\n'
        '    if name == "matplotlib.pyplot":\n'
        '        raise ImportError("simulated missing plot extra")\n'
        '    return _original_import(name, *args, **kwargs)\n'
        'builtins.__import__ = _without_pyplot\n', encoding='utf-8')
    out = tmp_path / 'result'
    _, output = run_example(script, out, env_extra=[str(shadow)])
    assert (out / script.replace('.py', '.csv')).is_file()
    assert not list(out.glob('*.png'))
    assert 'matplotlib unavailable; PNG omitted' in output


def test_research_repository_is_rejected():
    pytest.importorskip('pymatching')
    pytest.importorskip('ldpc')
    pytest.importorskip('bposd')
    package_parent = Path(mcmc4qec.__file__).resolve().parent.parent
    env = os.environ.copy()
    env['PYTHONPATH'] = str(package_parent)
    completed = subprocess.run(
        [sys.executable, str(WORKFLOWS / 'pl_curve.py'), '--quick',
         '--out', 'C:/dev/RIMC/mcmc4qec_example_forbidden'],
        cwd=ROOT, env=env, capture_output=True, text=True, timeout=10,
    )
    assert completed.returncode != 0
    assert 'Refusing to write into the read-only RIMC repository' in completed.stderr


@pytest.mark.parametrize('variable', ('RIMC_RESEARCH_ROOT', 'RESEARCH_ROOT'))
def test_configured_research_root_is_rejected(variable, tmp_path):
    package_parent = Path(mcmc4qec.__file__).resolve().parent.parent
    env = os.environ.copy()
    env['PYTHONPATH'] = str(package_parent)
    env[variable] = str(tmp_path / 'research')
    completed = subprocess.run(
        [sys.executable, str(WORKFLOWS / 'pl_curve.py'), '--quick',
         '--out', str(tmp_path / 'research' / 'forbidden')],
        cwd=ROOT, env=env, capture_output=True, text=True, timeout=10,
    )
    assert completed.returncode != 0
    assert 'Refusing to write into the read-only RIMC repository' in completed.stderr
    assert not (tmp_path / 'research').exists()


@pytest.mark.parametrize('seed', (0, 1, 2, 3, 4, 5, 7, 8, 9))
def test_convergence_initial_populations_are_distinct(seed, tmp_path):
    pytest.importorskip('pymatching')
    pytest.importorskip('ldpc')
    pytest.importorskip('bposd')
    _, output = run_example('convergence_check.py', tmp_path / str(seed), seed=seed)
    sectors = []
    for line in output.splitlines():
        if line.startswith(('minimum initial', 'random_sector initial', 'maximum initial')):
            sectors.append(tuple(ast.literal_eval(line.split('observable sector=', 1)[1])))
    assert len(sectors) == 3
    assert len(set(sectors)) == 3
