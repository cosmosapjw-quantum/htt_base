#!/usr/bin/env python3
"""Compile the finite C01 source and capture compiler/statement/axiom evidence.

This validates this successor only. It does not run a historical CAS adjudicator.
"""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parent
REPO = ROOT.parents[6]
ORACLE = Path('/home/cosmosapjw/lean_oracles/viii_oracle')
CONTRACT = ROOT.parent / 'EXECUTION_CONTRACT.json'
COMMON = REPO / 'docs/research_program/gr_statistics_loops_20260930/cas/COMMON_SPEC.md'
EXPECTED_CONTRACT = 'c35359e6b5b34c9b2dd085050acb21f737f6646c95e8abd8b69c6a1d7b694a21'
EXPECTED_COMMON = '4714827e52acf3cb149f4014ac50ab2aa995dd4a0526f6b26ac7257807fe1897'
EXPECTED_MATHLIB = 'fabf563a7c95a166b8d7b6efca11c8b4dc9d911f'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def run(argv, cwd):
    result = subprocess.run(argv, cwd=cwd, text=True, capture_output=True, timeout=180)
    return {'argv': argv, 'cwd': str(cwd), 'exit_code': result.returncode,
            'stdout': result.stdout, 'stderr': result.stderr}


def main():
    assert sha(CONTRACT) == EXPECTED_CONTRACT, 'IMMUTABLE_CONTRACT_BYTE_MISMATCH'
    assert sha(COMMON) == EXPECTED_COMMON, 'IMMUTABLE_COMMON_SPEC_BYTE_MISMATCH'
    mathlib = run(['git', 'rev-parse', 'HEAD'], ORACLE / '.lake/packages/mathlib')
    assert mathlib['exit_code'] == 0 and mathlib['stdout'].strip() == EXPECTED_MATHLIB
    version = run(['lake', 'env', 'lean', '--version'], ORACLE)
    assert version['exit_code'] == 0 and 'version 4.31.0,' in version['stdout']
    source = ROOT / 'lean/FiniteAdjoint.lean'
    attempt = 3
    while (ROOT / f'compile_attempt_{attempt:02d}.json').exists():
        attempt += 1
    output = ROOT / f'compile_attempt_{attempt:02d}'
    argv = ['lake', 'env', 'lean', str(source)]
    started = datetime.now(timezone.utc).isoformat()
    result = run(argv, ORACLE)
    (output.with_suffix('.stdout.log')).write_text(result['stdout'])
    (output.with_suffix('.stderr.log')).write_text(result['stderr'])
    result.update({'started_utc': started, 'finished_utc': datetime.now(timezone.utc).isoformat(),
                   'source_sha256': sha(source), 'execution_contract_sha256': sha(CONTRACT),
                   'common_spec_sha256': sha(COMMON), 'lean_version': version,
                   'mathlib_rev': mathlib['stdout'].strip(),
                   'toolchain_file_sha256': sha(ORACLE / 'lean-toolchain'),
                   'lake_manifest_sha256': sha(ORACLE / 'lake-manifest.json'),
                   'requested_author_runtime': {'model': 'gpt-6.1-sol', 'effort': 'high'},
                   'observed_author_runtime': 'UNKNOWN'})
    stdout = result['stdout']
    if result['exit_code'] == 0:
        statements = stdout.split('BEGIN_THEOREM_STATEMENTS\n', 1)[1].split('END_THEOREM_STATEMENTS', 1)[0]
        audit = stdout.split('BEGIN_AXIOM_AUDIT\n', 1)[1].split('END_AXIOM_AUDIT', 1)[0]
        assert 'sorryAx' not in audit, 'UNACCEPTED_AXIOM'
        allowed = {'propext', 'Classical.choice', 'Quot.sound'}
        for line in audit.splitlines():
            if 'depends on axioms:' in line:
                names = set(line.split('[', 1)[1].rstrip(']').split(', '))
                assert names <= allowed, f'UNEXPECTED_AXIOMS: {names - allowed}'
        (ROOT / 'THEOREM_STATEMENTS.txt').write_text(statements)
        (ROOT / 'AXIOM_AUDIT.txt').write_text(audit)
        result['theorem_statements_sha256'] = sha(ROOT / 'THEOREM_STATEMENTS.txt')
        result['axiom_audit_sha256'] = sha(ROOT / 'AXIOM_AUDIT.txt')
        result['successor_status'] = 'KERNEL_CHECKED_FINITE_C01_PENDING_INDEPENDENT_REVIEW'
    else:
        result['successor_status'] = 'COMPILE_FAILED'
    result['historical_four_axis_adjudication'] = 'NOT_RUN_UNCHANGED'
    result['scientific_admission'] = 'HOLD'
    output.with_suffix('.json').write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps({k: result[k] for k in ('exit_code', 'source_sha256', 'successor_status')}, indent=2))
    raise SystemExit(result['exit_code'])


if __name__ == '__main__':
    main()
