"""Run-spec preparation and synthetic execution; no scientific claims or engine probes."""
from pathlib import Path
import importlib.util
import hashlib
import json
import subprocess
import sys

import pytest

# This file belongs at tests/contracts/test_cas_script_launch.py in htt_base.
ROOT = Path(__file__).resolve().parents[2]
SCRIPTS = ROOT / '.agent-harness/scripts'
sys.path.insert(0, str(SCRIPTS))
spec = importlib.util.spec_from_file_location('cas_gate_script_launch', SCRIPTS / 'cas_gate.py')
gate = importlib.util.module_from_spec(spec)
spec.loader.exec_module(gate)
prepare_spec = importlib.util.spec_from_file_location(
    "cas_run_spec_preparation", SCRIPTS / "cas_prepare_run_spec.py"
)
preparer = importlib.util.module_from_spec(prepare_spec)
prepare_spec.loader.exec_module(preparer)


def prepare_and_validate(repo, run_spec, required):
    prepared, errors = preparer.prepare_run_spec(repo, run_spec, required)
    if errors:
        return {}, errors
    return gate._validate_run_spec(repo, prepared, required)


def make_spec(**entry):
    return {'schema_version': 1, 'axes': {'sage_singular': {'timeout_seconds': 30, **entry}}}


def test_sage_python_script_uses_sage_and_repo_cwd(tmp_path):
    (tmp_path / 'axis').mkdir()
    script = tmp_path / 'axis/run.py'
    script.write_text('from sage.all import QQ\n')
    config, errors = prepare_and_validate(tmp_path, make_spec(python_script='axis/run.py'), ['sage_singular'])
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
    configs, errors = prepare_and_validate(tmp_path, spec, ['wolfram_xact'])
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
    configs, errors = prepare_and_validate(tmp_path, spec, ['sympy'])
    assert not errors
    assert configs['sympy']['argv'][0] == str(python)


def test_legacy_argv_and_explicit_cwd_are_not_rewritten(tmp_path):
    (tmp_path / 'axis').mkdir()
    original = ['/usr/bin/python3', '-B', 'run.py']
    config, errors = prepare_and_validate(tmp_path, make_spec(argv=original, cwd='axis'), ['sage_singular'])
    assert not errors
    assert config['sage_singular']['argv'] == original
    assert config['sage_singular']['cwd'] == tmp_path / 'axis'
    _, errors = prepare_and_validate(tmp_path, make_spec(argv=original), ['sage_singular'])
    assert errors  # Legacy explicit invocation still requires explicit cwd.


@pytest.mark.parametrize('value', ['', '../outside.py', '/tmp/outside.py', 'missing.py', 'run.txt', None])
def test_script_mode_rejects_invalid_entrypoints(tmp_path, value):
    (tmp_path / 'run.txt').write_text('')
    _, errors = prepare_and_validate(tmp_path, make_spec(python_script=value), ['sage_singular'])
    assert errors


def test_script_mode_rejects_mixed_argv_shell_and_escape(tmp_path):
    (tmp_path / 'run.py').write_text('')
    for entry in ({'argv': ['python3', 'run.py']}, {'shell': False}, {'cwd': '..'}):
        _, errors = prepare_and_validate(tmp_path, make_spec(python_script='run.py', **entry), ['sage_singular'])
        assert errors
    (tmp_path / 'escape.py').symlink_to(__file__)
    _, errors = prepare_and_validate(tmp_path, make_spec(python_script='escape.py'), ['sage_singular'])
    assert errors


def prepare_cli(repo, contract, source, output):
    return subprocess.run(
        [sys.executable, '-B', str(SCRIPTS / 'cas_prepare_run_spec.py'),
         '--repo-root', str(repo), '--contract', str(contract),
         '--run-spec', str(source), '--out', str(output)],
        capture_output=True, text=True, check=False,
    )


@pytest.mark.parametrize('check, expected', [(True, 'PASS'), (False, 'FAIL')])
def test_prepare_cli_to_unchanged_adjudicator(tmp_path, check, expected):
    original = (SCRIPTS / 'cas_gate.py').read_bytes()
    assert hashlib.sha1(b'blob ' + str(len(original)).encode() + b'\0' + original).hexdigest() == (
        'a0d5ed80f8714a061b464f0cd179b3dc12fb6942'
    )
    contract = {'risk_tier': 'R1', 'required_axes': ['wolfram_xact'],
                'proof_obligations': ['runtime']}
    contract_file = tmp_path / 'contract.json'
    contract_file.write_text(json.dumps(contract))
    (tmp_path / 'axis').mkdir()
    script = tmp_path / 'axis/run.py'
    payload = {'checks': {'runtime': check}, 'domain_assumption_diff': [], 'counterexample': None}
    script.write_text('from pathlib import Path\n'
                      'assert Path.cwd() == Path(__file__).parent.parent\n'
                      f'print({json.dumps(payload)!r})\n')
    source = tmp_path / 'script-spec.json'
    source.write_text(json.dumps({'schema_version': 1, 'axes': {
        'wolfram_xact': {'python_script': 'axis/run.py', 'timeout_seconds': 30}}}))
    before = source.read_bytes()
    output = tmp_path / 'legacy-spec.json'
    completed = prepare_cli(tmp_path, contract_file, source, output)
    assert completed.returncode == 0, completed.stderr
    prepared = json.loads(output.read_text())
    assert prepared['axes']['wolfram_xact'] == {
        'argv': [sys.executable, '-B', str(script)], 'cwd': '.', 'timeout_seconds': 30,
    }
    assert source.read_bytes() == before
    # Exercise the original parser, subprocess execution and payload adjudication.
    # This synthetic fixture does not probe engines or establish a science claim.
    configs, errors = gate._validate_run_spec(tmp_path, prepared, ['wolfram_xact'])
    assert not errors
    observed = gate._execute_axis(contract, ['runtime'], 'wolfram_xact',
                                  configs['wolfram_xact'], {'fixture_only': True})
    assert observed['exit_code'] == 0
    assert observed['derived_status'] == expected
    assert observed['payload'] == payload


def test_prepare_cli_preserves_legacy_bytes_and_refuses_overwrite(tmp_path):
    contract = tmp_path / 'contract.json'
    contract.write_text(json.dumps({'risk_tier': 'R1', 'required_axes': ['sage_singular']}))
    source = tmp_path / 'source.json'
    legacy = make_spec(argv=['python3', '-B', 'run.py'], cwd='.')
    source.write_text(json.dumps(legacy, indent=4) + '\n\n')
    output = tmp_path / 'prepared.json'
    completed = prepare_cli(tmp_path, contract, source, output)
    assert completed.returncode == 0, completed.stderr
    assert output.read_bytes() == source.read_bytes()
    output.write_text('existing evidence\n')
    completed = prepare_cli(tmp_path, contract, source, output)
    assert completed.returncode == 2
    assert output.read_text() == 'existing evidence\n'


def test_prepare_cli_invalid_input_creates_no_output(tmp_path):
    contract = tmp_path / 'contract.json'
    contract.write_text(json.dumps({'risk_tier': 'R1', 'required_axes': ['sage_singular']}))
    source = tmp_path / 'source.json'
    source.write_text(json.dumps(make_spec(python_script='../outside.py')))
    output = tmp_path / 'prepared.json'
    completed = prepare_cli(tmp_path, contract, source, output)
    assert completed.returncode == 2
    assert 'python_script' in completed.stderr
    assert not output.exists()
