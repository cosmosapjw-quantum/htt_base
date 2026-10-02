"""Runtime launch regressions; no mathematical adjudication or stored-result reuse."""
from pathlib import Path
import importlib.util
import sys

import pytest

# This file belongs at tests/contracts/test_cas_script_launch.py in htt_base.
ROOT = Path(__file__).resolve().parents[2]
SCRIPTS = ROOT / '.agent-harness/scripts'
sys.path.insert(0, str(SCRIPTS))
spec = importlib.util.spec_from_file_location('cas_gate_script_launch', SCRIPTS / 'cas_gate.py')
gate = importlib.util.module_from_spec(spec)
spec.loader.exec_module(gate)


def make_spec(**entry):
    return {'schema_version': 1, 'axes': {'sage_singular': {'timeout_seconds': 30, **entry}}}


def test_sage_python_script_uses_sage_and_repo_cwd(tmp_path):
    (tmp_path / 'axis').mkdir()
    script = tmp_path / 'axis/run.py'
    script.write_text('from sage.all import QQ\n')
    config, errors = gate._validate_run_spec(tmp_path, make_spec(python_script='axis/run.py'), ['sage_singular'])
    assert not errors
    assert config['sage_singular']['argv'] == ['sage', '-python', '-B', str(script)]
    assert config['sage_singular']['cwd'] == tmp_path
    assert config['sage_singular']['cwd_label'] == '.'


def test_wolfram_wrapper_runs_from_repo_not_script_directory(tmp_path):
    (tmp_path / 'axis').mkdir()
    script = tmp_path / 'axis/run.py'
    script.write_text('import pathlib\nassert pathlib.Path.cwd() == pathlib.Path(__file__).parent.parent\n'
                      'print(\'{"checks":{"runtime":true},"counterexample":null,"domain_assumption_diff":[]}\')\n')
    spec = {'schema_version': 1, 'axes': {'wolfram_xact': {'python_script': 'axis/run.py', 'timeout_seconds': 30}}}
    configs, errors = gate._validate_run_spec(tmp_path, spec, ['wolfram_xact'])
    assert not errors
    observed = gate._execute_axis({}, ['runtime'], 'wolfram_xact', configs['wolfram_xact'], {'status': 'PASS'})
    assert observed['exit_code'] == 0
    assert observed['derived_status'] == 'PASS'
    assert observed['payload']['checks'] == {'runtime': True}


def test_sympy_keeps_logical_project_venv_path(tmp_path):
    python = tmp_path / 'venv/bin/python'
    python.parent.mkdir(parents=True)
    python.symlink_to(sys.executable)
    (tmp_path / 'run.py').write_text('')
    spec = {'schema_version': 1, 'axes': {'sympy': {'python_script': 'run.py', 'timeout_seconds': 30}}}
    configs, errors = gate._validate_run_spec(tmp_path, spec, ['sympy'])
    assert not errors
    assert configs['sympy']['argv'][0] == str(python)


def test_legacy_argv_and_explicit_cwd_are_not_rewritten(tmp_path):
    (tmp_path / 'axis').mkdir()
    original = ['/usr/bin/python3', '-B', 'run.py']
    config, errors = gate._validate_run_spec(tmp_path, make_spec(argv=original, cwd='axis'), ['sage_singular'])
    assert not errors
    assert config['sage_singular']['argv'] == original
    assert config['sage_singular']['cwd'] == tmp_path / 'axis'
    _, errors = gate._validate_run_spec(tmp_path, make_spec(argv=original), ['sage_singular'])
    assert errors  # Legacy explicit invocation still requires explicit cwd.


@pytest.mark.parametrize('value', ['', '../outside.py', '/tmp/outside.py', 'missing.py', 'run.txt', None])
def test_script_mode_rejects_invalid_entrypoints(tmp_path, value):
    (tmp_path / 'run.txt').write_text('')
    _, errors = gate._validate_run_spec(tmp_path, make_spec(python_script=value), ['sage_singular'])
    assert errors


def test_script_mode_rejects_mixed_argv_shell_and_escape(tmp_path):
    (tmp_path / 'run.py').write_text('')
    for entry in ({'argv': ['python3', 'run.py']}, {'shell': False}, {'cwd': '..'}):
        _, errors = gate._validate_run_spec(tmp_path, make_spec(python_script='run.py', **entry), ['sage_singular'])
        assert errors
    (tmp_path / 'escape.py').symlink_to(__file__)
    _, errors = gate._validate_run_spec(tmp_path, make_spec(python_script='escape.py'), ['sage_singular'])
    assert errors
