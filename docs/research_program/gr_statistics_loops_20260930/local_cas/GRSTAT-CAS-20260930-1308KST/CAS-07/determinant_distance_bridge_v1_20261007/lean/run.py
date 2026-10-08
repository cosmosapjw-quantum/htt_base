#!/usr/bin/env python3
"""Run only the frozen CAS-07 M05 Lean axis against opaque accepted oleans."""
from __future__ import annotations

import hashlib
import json
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[7]
ORACLE = Path('/home/cosmosapjw/lean_oracles/viii_oracle')
CONTRACT = HERE.parent / 'EXECUTION_CONTRACT.json'
INPUTS = HERE.parent / 'ADMITTED_INPUTS.json'
COMMON = REPO / 'docs/research_program/gr_statistics_loops_20260930/cas/COMMON_SPEC.md'
TOOLCHAIN = REPO / 'formal_mathlib/lean-toolchain'
MANIFEST = REPO / 'formal_mathlib/lake-manifest.json'
EXPECTED = {
    CONTRACT: '24e3ae1e11d2a75335cd7fac436e8d1656100dc7877672d08464a4612a19348e',
    INPUTS: '22fbf2a3fcc428d25f8e9fb0d6e1866c8057ebc7e76dd4ad248bd144300a5a75',
    COMMON: '4714827e52acf3cb149f4014ac50ab2aa995dd4a0526f6b26ac7257807fe1897',
    TOOLCHAIN: 'efac0b94923b2d8b6840cd35be9177ad0fc5ab2332f4f4311c98712cee92fdee',
    MANIFEST: 'bc86de9aed83fc38b0850702d6879ed6f3c97eedb7d1d69d643160731179d6ed',
    ORACLE / 'CAS07M01Accepted.olean': '83acab45987909a490f90af775cc0f3ce538de3a5e04ed5a04abc311d9c15ca2',
    ORACLE / 'CAS07M04Accepted.olean': '81e374aa492d6528188225df432f1036dd460f168f31aa15e544289b46c8182a',
    ORACLE / 'CAS07C02Accepted.olean': '67344c6d91e2abfcdc8bae9329f55a3d659438bd61a34cb91d3670e3123bb2c0',
}
CHECK_IDS = [
    'CAS-07-M05-REWRITE',
    'CAS-07-M05-C02-PREMISE',
    'CAS-07-M05-DETERMINANT-SIGN',
    'CAS-07-M05-DISTANCE-BOUND',
]
FORBIDDEN = re.compile(r'\b(?:sorry|admit|unsafe|native_decide|axiom)\b')


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def run_logged(name: str, command: list[str], timeout: int) -> subprocess.CompletedProcess[str]:
    try:
        process = subprocess.run(command, cwd=ORACLE, capture_output=True, text=True, timeout=timeout)
    except subprocess.TimeoutExpired as exc:
        process = subprocess.CompletedProcess(command, 124,
            (exc.stdout or b'').decode(errors='replace') if isinstance(exc.stdout, bytes) else (exc.stdout or ''),
            (exc.stderr or b'').decode(errors='replace') if isinstance(exc.stderr, bytes) else (exc.stderr or '') + '\nTIMEOUT')
    (HERE / f'{name}.stdout.log').write_text(process.stdout)
    (HERE / f'{name}.stderr.log').write_text(process.stderr)
    return process


def main() -> int:
    observed = {str(p): sha256(p) if p.exists() else None for p in EXPECTED}
    hash_ok = all(observed[str(p)] == digest for p, digest in EXPECTED.items())
    source_text = (HERE / 'Main.lean').read_text() + '\n' + (HERE / 'Checks.lean').read_text()
    source_ok = FORBIDDEN.search(source_text) is None
    version = run_logged('lean_version', ['lake', 'env', 'lean', '--version'], 120)
    lake_version = run_logged('lake_version', ['lake', '--version'], 120)
    shell = 'cd "$1" && export LEAN_PATH="$2:$PWD:$LEAN_PATH" && lean -o Main.olean Main.lean'
    main_run = None
    checks_run = None
    if hash_ok and source_ok and version.returncode == 0:
        main_run = run_logged('main_compile', ['lake', 'env', 'bash', '-c', shell, 'm05', str(HERE), str(ORACLE)], 7200)
        if main_run.returncode == 0:
            shell_checks = 'cd "$1" && export LEAN_PATH="$2:$PWD:$LEAN_PATH" && lean -o Checks.olean Checks.lean'
            checks_run = run_logged('checks_compile', ['lake', 'env', 'bash', '-c', shell_checks, 'm05', str(HERE), str(ORACLE)], 7200)
    axiom_report = {}
    if checks_run is not None:
        for theorem, names in re.findall(r"'CAS07M05\.([^']+)' depends on axioms: \[([^]]*)\]", checks_run.stdout):
            axiom_report[theorem] = sorted(name.strip() for name in names.split(','))
    expected_theorems = {'f_sub_eq_s_eta', 'c02_premise', 'determinant_distance_bridge', 'zero_curvature_control'}
    standard_axioms = sorted(['propext', 'Classical.choice', 'Quot.sound'])
    axioms_ok = set(axiom_report) == expected_theorems and all(names == standard_axioms for names in axiom_report.values())
    oracle_manifest = ORACLE / 'lake-manifest.json'
    pinned_packages = {p['name']: p['rev'] for p in json.loads(MANIFEST.read_text())['packages']}
    oracle_packages = {p['name']: p['rev'] for p in json.loads(oracle_manifest.read_text())['packages']}
    package_revisions_match = oracle_packages == pinned_packages
    mathlib_head = subprocess.run(['git', '-C', str(ORACLE / '.lake/packages/mathlib'), 'rev-parse', 'HEAD'],
                                  capture_output=True, text=True, timeout=30)
    mathlib_head_match = mathlib_head.returncode == 0 and mathlib_head.stdout.strip() == pinned_packages['mathlib']
    success = bool(hash_ok and source_ok and package_revisions_match and mathlib_head_match and version.returncode == 0 and lake_version.returncode == 0 and main_run and main_run.returncode == 0 and checks_run and checks_run.returncode == 0 and axioms_ok)
    for name in ['main_compile', 'checks_compile']:
        for stream in ['stdout', 'stderr']:
            path = HERE / f'{name}.{stream}.log'
            if not path.exists():
                path.write_text('NOT_EXECUTED\n')
    artifacts = {}
    for filename in ['Main.lean', 'Checks.lean', 'Main.olean', 'Checks.olean',
                     'main_compile.stdout.log', 'main_compile.stderr.log',
                     'checks_compile.stdout.log', 'checks_compile.stderr.log',
                     'lean_version.stdout.log', 'lean_version.stderr.log',
                     'lake_version.stdout.log', 'lake_version.stderr.log',
                     'PROOF.md', 'run.py']:
        path = HERE / filename
        if path.exists():
            artifacts[filename] = {'sha256': sha256(path), 'bytes': path.stat().st_size}
    result = {
        'schema_version': 2,
        'contract_id': 'GRSTAT-20260930-CAS-07-M05-DETERMINANT-DISTANCE-BRIDGE-V1',
        'axis': 'lean',
        'status': 'PASS' if success else 'BLOCKED',
        'contract_sha256': EXPECTED[CONTRACT],
        'admitted_inputs_sha256': EXPECTED[INPUTS],
        'input_hashes_observed': observed,
        'input_hashes_match': hash_ok,
        'tool': {'name': 'Lean', 'version_output': version.stdout.strip(),
                 'lake_version_output': lake_version.stdout.strip(),
                 'python_version': sys.version.split()[0],
                 'pinned_toolchain': TOOLCHAIN.read_text().strip() if TOOLCHAIN.exists() else None,
                 'environment': str(ORACLE),
                 'oracle_toolchain_sha256': sha256(ORACLE / 'lean-toolchain'),
                 'oracle_manifest_sha256': sha256(oracle_manifest),
                 'package_revisions_match': package_revisions_match,
                 'mathlib_revision': oracle_packages.get('mathlib'),
                 'mathlib_checkout_head': mathlib_head.stdout.strip(),
                 'mathlib_checkout_head_match': mathlib_head_match,
                 'manifest_byte_mismatch_classification': 'PACKAGING_METADATA'},
        'accepted_interfaces': {
            'CAS07M01Accepted': {'olean_sha256': EXPECTED[ORACLE / 'CAS07M01Accepted.olean']},
            'CAS07M04Accepted': {'olean_sha256': EXPECTED[ORACLE / 'CAS07M04Accepted.olean']},
            'CAS07C02Accepted': {'olean_sha256': EXPECTED[ORACLE / 'CAS07C02Accepted.olean']},
        },
        'launch_id': None,
        'assignment_id': None,
        'context_version': None,
        'global_authority': 'UNAVAILABLE',
        'observed_model': 'UNKNOWN',
        'observed_effort': 'UNKNOWN',
        'independence_mode': 'blind-results-and-derivations',
        'checks': {name: success for name in CHECK_IDS},
        'domain_assumption_diff': [],
        'counterexample': None,
        'k_zero_control': success,
        'compile_exit_codes': {'Main.lean': None if main_run is None else main_run.returncode,
                               'Checks.lean': None if checks_run is None else checks_run.returncode},
        'source_forbidden_token_check': source_ok,
        'axiom_report': axiom_report,
        'standard_axioms_only': axioms_ok,
        'artifacts': artifacts,
        'scientific_admission': 'HOLD',
        'aggregate_claim': 'M05 Lean axis only; M04 adjudication and other axes are outside this result',
        'executed_at_utc': datetime.now(timezone.utc).isoformat(),
    }
    (HERE / 'result.json').write_text(json.dumps(result, indent=2, sort_keys=True) + '\n')
    print(json.dumps({
        'status': result['status'],
        'checks': result['checks'],
        'domain_assumption_diff': result['domain_assumption_diff'],
        'counterexample': result['counterexample'],
        'result_path': str(HERE / 'result.json'),
    }))
    return 0 if success else 1


if __name__ == '__main__':
    sys.exit(main())
