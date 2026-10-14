"""Frozen CAS-15-C04 Sage+Singular axis runner; write only this axis."""
import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
UNIT = HERE.parent
ROOT = Path(__file__).resolve().parents[8]
CONTRACT_SHA = '67422619e47fda896d7516d48e980ec693d878f3c63e5d61e0c151ffaef65ed8'
INPUT_SHA = '1b98962616a8a43aca614c18a7e69304653c84f0d1b54846a81811642d2491d8'
SINGULAR_SHA = '9430832b7c972b6b26d29ded4d91a3e1df8fd87d67f4b8d3f14d8201a75f923c'
SINGULAR = Path('/home/cosmosapjw/opt/sage/local/bin/Singular')


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def run(argv, timeout=1800):
    return subprocess.run(argv, cwd=ROOT, text=True, capture_output=True, timeout=timeout)


def write_atomic(path, value):
    temp = path.with_name(path.name + '.tmp')
    temp.write_text(json.dumps(value, indent=2, sort_keys=True) + '\n')
    os.replace(temp, path)


def main():
    binding = {
        'contract': sha(UNIT / 'EXECUTION_CONTRACT.json'),
        'inputs': sha(UNIT / 'ADMITTED_INPUTS.json'),
        'singular_binary': sha(SINGULAR),
    }
    expected = {'contract': CONTRACT_SHA, 'inputs': INPUT_SHA, 'singular_binary': SINGULAR_SHA}
    if binding != expected:
        raise RuntimeError(f'frozen input/toolchain mismatch: {binding}')

    sage_argv = ['sage', '-python', str(HERE / 'check.py')]
    sage_version = run(['sage', '--version'], timeout=30)
    singular_version = run([str(SINGULAR), '--version'], timeout=30)
    (HERE / 'sage_version.stdout.log').write_text(sage_version.stdout)
    (HERE / 'sage_version.stderr.log').write_text(sage_version.stderr)
    (HERE / 'singular_version.stdout.log').write_text(singular_version.stdout)
    (HERE / 'singular_version.stderr.log').write_text(singular_version.stderr)

    process = run(sage_argv)
    (HERE / 'sage_stdout.log').write_text(process.stdout)
    (HERE / 'sage_stderr.log').write_text(process.stderr)
    details = {}
    if process.returncode == 0:
        try:
            details = json.loads(process.stdout.strip())
        except json.JSONDecodeError:
            details = {'parse_error': 'Sage stdout was not one JSON document'}
    exact_checks = details.get('checks', {})
    needed = {
        'generic_gram_identity',
        'axis_commutator_and_gram',
        'single_axis_rank_and_isotropic_zero',
        'two_axis_determinant_and_parallel_control',
        'singular_polynomial_certificate',
    }
    diagnostics = (HERE / 'singular_stdout.log', HERE / 'singular_stderr.log')
    singular_stdout = diagnostics[0].read_text() if diagnostics[0].exists() else ''
    singular_stderr = diagnostics[1].read_text() if diagnostics[1].exists() else ''
    diagnostics_ok = (
        details.get('singular_exit_code') == 0
        and not singular_stderr.strip()
        and '// **' not in singular_stdout
        and '? ' not in singular_stdout
    )
    passed = (
        sage_version.returncode == 0
        and singular_version.returncode == 0
        and 'SageMath version 10.9' in sage_version.stdout
        and 'version 4.4.1 (44100' in singular_version.stdout
        and process.returncode == 0
        and all(exact_checks.get(k) is True for k in needed)
        and diagnostics_ok
    )
    sources = {name: sha(HERE / name) for name in ('run.py', 'check.py', 'check.sing', 'PROOF.md')}
    logs = {p.name: sha(p) for p in (
        HERE / 'sage_stdout.log', HERE / 'sage_stderr.log',
        HERE / 'singular_stdout.log', HERE / 'singular_stderr.log',
        HERE / 'sage_version.stdout.log', HERE / 'sage_version.stderr.log',
        HERE / 'singular_version.stdout.log', HERE / 'singular_version.stderr.log',
    ) if p.exists()}
    result = {
        'axis': 'sage_singular',
        'status': 'PASS' if passed else 'FAIL',
        'evidence_class': 'exact',
        'checks': {'CAS-15-C04': passed},
        'detailed_checks': exact_checks,
        'domain_assumption_diff': [],
        'counterexample': None,
        'contract_sha256': CONTRACT_SHA,
        'inputs_sha256': INPUT_SHA,
        'toolchain': {
            'sage_version': sage_version.stdout.strip(),
            'sage_version_exit': sage_version.returncode,
            'singular_version': '4.4.1/44100' if 'version 4.4.1 (44100' in singular_version.stdout else 'UNKNOWN',
            'singular_version_exit': singular_version.returncode,
            'singular_binary': str(SINGULAR),
            'singular_binary_sha256': SINGULAR_SHA,
        },
        'execution': {
            'sage_argv': sage_argv,
            'sage_exit_code': process.returncode,
            'singular_argv': details.get('singular_argv'),
            'singular_exit_code': details.get('singular_exit_code'),
            'singular_diagnostics_ok': diagnostics_ok,
            'cwd': str(ROOT),
        },
        'source_sha256': sources,
        'raw_log_sha256': logs,
        'independence': {
            'mode': 'blind-results-and-derivations',
            'sibling_sources_or_results_read': False,
            'llm_family_correlation': 'Codex family shared with other axes; actual model/effort UNKNOWN',
        },
        'runtime': {'launch_id': None, 'authority_status': 'UNAVAILABLE', 'observed_model': 'UNKNOWN', 'observed_effort': 'UNKNOWN'},
        'statement_alignment': {
            'exact_component': 'CAS-15-C04',
            'real_symmetric_finite_stack': True,
            'unit_axes': True,
            'nonzero_beta_and_nonparallel_required_for_pd': True,
            'claim_ceiling': 'C04_finite_commutant_only_no_transport_or_science',
        },
    }
    write_atomic(HERE / 'result.json', result)
    print(json.dumps({
        'status': result['status'],
        'checks': result['checks'],
        'domain_assumption_diff': [],
        'counterexample': None,
        'result_path': str(HERE / 'result.json'),
    }, sort_keys=True))
    return 0 if passed else 1


if __name__ == '__main__':
    sys.exit(main())
