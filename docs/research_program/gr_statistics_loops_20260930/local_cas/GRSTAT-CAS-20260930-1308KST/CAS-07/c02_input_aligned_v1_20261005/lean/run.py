#!/usr/bin/python3.12
"""Frozen, no-argument Lean axis runner for CAS-07-C02."""
from __future__ import annotations

import datetime as dt
import hashlib
import json
import os
from pathlib import Path
import re
import resource
import shutil
import subprocess
import sys
import uuid

REPO = Path('/home/cosmosapjw/Dropbox/bianchi/htt_base')
V = REPO / 'docs/research_program/gr_statistics_loops_20260930/local_cas/GRSTAT-CAS-20260930-1308KST/CAS-07/c02_input_aligned_v1_20261005'
HERE = V / 'lean'
MATHLIB_ROOT = REPO / 'formal_mathlib'
TASK = 'GRSTAT-CAS-20260930-1308KST-CAS-07-C02-V1-LEAN'
EXPECTED = {
    'EXECUTION_CONTRACT.json': '367ea2b4221c2ef10c93d1c49ef75d40d0f030bf79ec429a0fe1dbfeb44c219a',
    'ADMITTED_INPUTS.json': '84e20f628abcc4879446c6987dec21416934dece1c94e23076d6ce491939e6b0',
    'COMMON_SPEC.md': '4714827e52acf3cb149f4014ac50ab2aa995dd4a0526f6b26ac7257807fe1897',
    'formal/lean-toolchain': 'efac0b94923b2d8b6840cd35be9177ad0fc5ab2332f4f4311c98712cee92fdee',
    'formal_mathlib/lean-toolchain': 'efac0b94923b2d8b6840cd35be9177ad0fc5ab2332f4f4311c98712cee92fdee',
    'formal_mathlib/lake-manifest.json': 'bc86de9aed83fc38b0850702d6879ed6f3c97eedb7d1d69d643160731179d6ed',
}
PATHS = {
    'EXECUTION_CONTRACT.json': V / 'EXECUTION_CONTRACT.json',
    'ADMITTED_INPUTS.json': V / 'ADMITTED_INPUTS.json',
    'COMMON_SPEC.md': REPO / 'docs/research_program/gr_statistics_loops_20260930/cas/COMMON_SPEC.md',
    'formal/lean-toolchain': REPO / 'formal/lean-toolchain',
    'formal_mathlib/lean-toolchain': MATHLIB_ROOT / 'lean-toolchain',
    'formal_mathlib/lake-manifest.json': MATHLIB_ROOT / 'lake-manifest.json',
}
CORE_AXIOMS = ['propext', 'Classical.choice', 'Quot.sound']

def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()

def now() -> str:
    return dt.datetime.now(dt.timezone.utc).isoformat()

def meminfo() -> dict[str, int | None]:
    data = {}
    for line in Path('/proc/meminfo').read_text().splitlines():
        if line.startswith(('MemAvailable:', 'MemTotal:', 'SwapFree:', 'SwapTotal:')):
            key, value, *_ = line.split()
            data[key[:-1] + '_kib'] = int(value)
    return data

def run(argv: list[str], cwd: Path, out: Path, err: Path, timeout: int) -> dict:
    started = now()
    try:
        p = subprocess.run(argv, cwd=cwd, env={**os.environ, 'ELAN_TOOLCHAIN': 'leanprover/lean4:v4.31.0'},
                           stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=timeout, check=False)
        stdout, stderr, code, timed_out = p.stdout, p.stderr, p.returncode, False
    except subprocess.TimeoutExpired as exc:
        stdout, stderr, code, timed_out = exc.stdout or b'', exc.stderr or b'', 124, True
    out.write_bytes(stdout)
    err.write_bytes(stderr)
    return {'argv': argv, 'cwd': str(cwd), 'started_at': started, 'completed_at': now(),
            'exit_code': code, 'timed_out': timed_out, 'stdout_path': str(out),
            'stderr_path': str(err), 'stdout_sha256': sha(out), 'stderr_sha256': sha(err),
            'stdout': stdout.decode('utf-8', 'replace'), 'stderr': stderr.decode('utf-8', 'replace')}

def main() -> int:
    if len(sys.argv) != 1:
        raise SystemExit('run.py accepts no arguments')
    if HERE.resolve() != Path(__file__).resolve().parent:
        raise SystemExit('wrong worktree or path')
    attempt = HERE / 'attempts' / (dt.datetime.now(dt.timezone.utc).strftime('%Y%m%dT%H%M%SZ') + '-' + uuid.uuid4().hex[:8])
    attempt.mkdir(parents=True, exist_ok=False)
    source = HERE / 'C02.lean'
    frozen_source = attempt / 'C02.lean'
    shutil.copyfile(source, frozen_source)
    before = {name: sha(path) for name, path in PATHS.items()}
    source_before = sha(source)
    memory_before = meminfo()
    commands = []
    commands.append(run(['git', 'rev-parse', 'HEAD'], REPO, attempt / 'head.stdout', attempt / 'head.stderr', 30))
    commands.append(run(['lean', '--version'], MATHLIB_ROOT, attempt / 'lean-version.stdout', attempt / 'lean-version.stderr', 30))
    commands.append(run(['lake', '--version'], MATHLIB_ROOT, attempt / 'lake-version.stdout', attempt / 'lake-version.stderr', 30))
    commands.append(run(['git', 'rev-parse', 'HEAD'], MATHLIB_ROOT / '.lake/packages/mathlib',
                        attempt / 'mathlib-rev.stdout', attempt / 'mathlib-rev.stderr', 30))
    source_text = frozen_source.read_text()
    forbidden = re.findall(r'\b(?:sorry|admit|axiom|constant|unsafe|native_decide)\b', source_text)
    setup_ok = (all(before[k] == v for k, v in EXPECTED.items())
                and commands[0]['stdout'].strip() == 'f1007dd3e41c07eccd64024dd6b44fb5a40a3612'
                and commands[1]['exit_code'] == 0
                and '4.31.0' in commands[1]['stdout']
                and commands[3]['stdout'].strip() == 'fabf563a7c95a166b8d7b6efca11c8b4dc9d911f'
                and not forbidden
                and memory_before.get('MemAvailable_kib', 0) >= 16 * 1024 * 1024)
    if setup_ok:
        commands.append(run(['lake', 'env', 'lean', str(frozen_source)], MATHLIB_ROOT,
                            attempt / 'compile.stdout', attempt / 'compile.stderr', 3600))
    else:
        (attempt / 'compile.stdout').write_text('')
        (attempt / 'compile.stderr').write_text('PRECONDITION_FAILURE; Lean was not run.\n')
    after = {name: sha(path) for name, path in PATHS.items()}
    source_after = sha(source)
    compile_cmd = commands[-1] if setup_ok else None
    output = compile_cmd['stdout'] + compile_cmd['stderr'] if compile_cmd else ''
    axiom_lines = re.findall(r"'CAS07C02\.CAS_07_C02_full' depends on axioms: \[([^]]+)\]", output)
    axioms = [x.strip() for x in axiom_lines[-1].split(',')] if axiom_lines else []
    success = (setup_ok and compile_cmd['exit_code'] == 0 and not compile_cmd['timed_out']
               and sorted(axioms) == sorted(CORE_AXIOMS)
               and 'error:' not in output and before == after and source_before == source_after
               and sha(frozen_source) == source_before)
    result = {
        'axis': 'lean', 'status': 'PASS' if success else 'INCONCLUSIVE',
        'evidence_class': 'exact',
        'contract_sha256': EXPECTED['EXECUTION_CONTRACT.json'], 'completed_at': now(),
        'checks': {'CAS-07-C02': success}, 'domain_assumption_diff': [], 'counterexample': None,
        'commands': commands,
        'details': {
            'task_id': TASK, 'claim_ceiling': 'specified_mathematical_component_only_no_scientific_admission',
            'source_path': str(frozen_source), 'source_sha256': source_before,
            'source_sha256_after': source_after, 'frozen_source_sha256': sha(frozen_source),
            'input_sha256_before': before, 'input_sha256_after': after,
            'mathlib_revision': commands[3]['stdout'].strip(),
            'toolchain': commands[1]['stdout'].strip(), 'lake_version': commands[2]['stdout'].strip(),
            'printed_axioms': axioms, 'forbidden_tokens': forbidden,
            'memory_before': memory_before, 'memory_after': meminfo(),
            'child_ru_maxrss_kib': resource.getrusage(resource.RUSAGE_CHILDREN).ru_maxrss,
            'context_peak': 'NOT_MEASURED', 'gpu_peak': 'NOT_MEASURED',
            'subchecks': {'euclidean_opnorm_vector_equivalence': success,
                          'both_singular_values_bounded': success,
                          'determinant_positivity_derived': success,
                          'positive_sqrt_determinant_bounded': success},
        },
    }
    (attempt / 'result.json').write_text(json.dumps(result, indent=2, sort_keys=True) + '\n')
    shutil.copyfile(attempt / 'result.json', HERE / 'result.json')
    print(json.dumps({'checks': {'CAS-07-C02': success}, 'domain_assumption_diff': [],
                      'counterexample': None, 'subchecks': result['details']['subchecks']}, sort_keys=True))
    return 0 if success else 1

if __name__ == '__main__':
    raise SystemExit(main())
