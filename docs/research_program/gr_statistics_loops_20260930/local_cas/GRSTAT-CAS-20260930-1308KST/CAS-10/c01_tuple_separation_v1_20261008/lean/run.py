#!/usr/bin/env python3
"""Compile the frozen CAS-10-C01 Lean component under the pinned mathlib tree."""

import hashlib
import json
import pathlib
import re
import subprocess
import sys
from datetime import datetime, timezone

HERE = pathlib.Path(__file__).resolve().parent
ENV = pathlib.Path('/home/cosmosapjw/lean_oracles/viii_oracle')
SOURCE = HERE / 'CAS10C01.lean'
CONTRACT_HASH = 'e438beb0e304e7a84e062cb5ab5946829951e035b3f6ac2923c28e07fd25f08d'
INPUT_HASH = '704403a7e717c1ff60e8be86d73e359621f0478b7b2a231b9df07ab3d99a2f3b'
MATHLIB_REV = 'fabf563a7c95a166b8d7b6efca11c8b4dc9d911f'
THEOREMS = (
    'u_unit', 'B1_u_zero', 'B2_u', 'b2_orthogonal', 'b2_norm',
    'b2_norm_pos', 'b2_nonzero', 'tuple1_powers', 'tuple2_powers',
    'H_zero_polynomial_controls', 'H_zero_not_strict',
    'H_one_b2_explicit', 'H_one_control',
)


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def command(argv, stem):
    completed = subprocess.run(argv, cwd=ENV, capture_output=True, check=False)
    stdout = HERE / f'{stem}.stdout.log'
    stderr = HERE / f'{stem}.stderr.log'
    stdout.write_bytes(completed.stdout)
    stderr.write_bytes(completed.stderr)
    return {
        'argv': [str(x) for x in argv],
        'cwd': str(ENV),
        'exit_code': completed.returncode,
        'stdout_path': str(stdout),
        'stdout_sha256': digest(stdout),
        'stderr_path': str(stderr),
        'stderr_sha256': digest(stderr),
    }, completed.stdout.decode('utf-8', errors='replace')


def main():
    commands = []
    version, version_text = command(['lake', 'env', 'lean', '--version'], 'version')
    commands.append(version)
    compile_cmd, compile_text = command(['lake', 'env', 'lean', str(SOURCE)], 'compile')
    commands.append(compile_cmd)
    manifest = json.loads((ENV / 'lake-manifest.json').read_text())
    mathlib = next(p for p in manifest['packages'] if p['name'] == 'mathlib')
    source_text = SOURCE.read_text()
    axiom_lines = [line for line in compile_text.splitlines() if 'depends on axioms:' in line]
    covered = all(f"'CAS10C01.{name}' depends on axioms:" in compile_text for name in THEOREMS)
    safe_axioms = covered and all('sorryAx' not in line for line in axiom_lines)
    safe_source = re.search(r'\b(?:sorry|admit)\b', source_text) is None
    pinned = (
        version['exit_code'] == 0
        and 'Lean (version 4.31.0,' in version_text
        and mathlib['rev'] == MATHLIB_REV
        and (ENV / 'lean-toolchain').read_text().strip() == 'leanprover/lean4:v4.31.0'
    )
    passed = compile_cmd['exit_code'] == 0 and pinned and safe_source and safe_axioms
    compact = {
        'checks': {'CAS-10-C01': passed},
        'domain_assumption_diff': [],
        'counterexample': None,
    }
    common = {
        'axis': 'lean',
        'status': 'PASS' if passed else 'FAIL',
        'contract_sha256': CONTRACT_HASH,
        'admitted_inputs_sha256': INPUT_HASH,
        'evidence_class': 'exact',
        'commands': commands,
        'source_path': str(SOURCE),
        'source_sha256': digest(SOURCE),
        'runner_path': str(HERE / 'run.py'),
        'runner_sha256': digest(HERE / 'run.py'),
        'lean_version': version_text.strip(),
        'mathlib_revision': mathlib['rev'],
        'toolchain_path': str(ENV / 'lean-toolchain'),
        'toolchain_sha256': digest(ENV / 'lean-toolchain'),
        'mathlib_manifest_path': str(ENV / 'lake-manifest.json'),
        'mathlib_manifest_sha256': digest(ENV / 'lake-manifest.json'),
        'axiom_lines': axiom_lines,
        'source_scan_no_sorry_admit': safe_source,
        'axiom_scan_no_sorryAx': safe_axioms,
        'checked_theorems': list(THEOREMS),
        'domain_assumption_diff': [],
        'counterexample': None,
        'launch_id': None,
        'authority': 'UNAVAILABLE',
        'observed_model': 'UNKNOWN',
        'observed_effort': 'UNKNOWN',
        'completed_at': datetime.now(timezone.utc).isoformat(),
    }
    result = {**common, **compact}
    (HERE / 'result.json').write_text(json.dumps(result, indent=2, sort_keys=True) + '\n')
    axis = {**common, 'result_path': str(HERE / 'result.json'),
            'result_sha256': digest(HERE / 'result.json'), 'checks': compact['checks']}
    (HERE / 'axis_result.json').write_text(json.dumps(axis, indent=2, sort_keys=True) + '\n')
    print(json.dumps(compact, separators=(',', ':'), sort_keys=True))
    return 0 if passed else 1


if __name__ == '__main__':
    sys.exit(main())
