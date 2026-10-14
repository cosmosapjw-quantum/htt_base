#!/usr/bin/python3.12
"""Frozen-argument CAS-07-C01 Lean compiler and evidence writer."""
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
from datetime import datetime, timezone

REPO = Path('/home/cosmosapjw/Dropbox/bianchi/htt_base')
AXIS = REPO / 'docs/research_program/gr_statistics_loops_20260930/local_cas/GRSTAT-CAS-20260930-1308KST/CAS-07/c01_input_aligned_v1_20261005/lean'
P = AXIS.parent
FORMAL = REPO / 'formal_mathlib'
FILES = {
    'contract': P / 'EXECUTION_CONTRACT.json',
    'admitted_inputs': P / 'ADMITTED_INPUTS.json',
    'common_spec': REPO / 'docs/research_program/gr_statistics_loops_20260930/cas/COMMON_SPEC.md',
    'formal_toolchain': REPO / 'formal/lean-toolchain',
    'mathlib_toolchain': FORMAL / 'lean-toolchain',
    'lake_manifest': FORMAL / 'lake-manifest.json',
    'source': AXIS / 'CAS07C01.lean',
}
EXPECTED = {
    'contract': 'e5342381440cb6456ad27add75a9d23faa52a01b1a0f5998599e3026452a9f1a',
    'admitted_inputs': '30bbb6fce513eedfd98a693c2acbf3308363a7098a7938f4b5abf7e9282b2e39',
    'common_spec': '4714827e52acf3cb149f4014ac50ab2aa995dd4a0526f6b26ac7257807fe1897',
    'formal_toolchain': 'efac0b94923b2d8b6840cd35be9177ad0fc5ab2332f4f4311c98712cee92fdee',
    'mathlib_toolchain': 'efac0b94923b2d8b6840cd35be9177ad0fc5ab2332f4f4311c98712cee92fdee',
    'lake_manifest': 'bc86de9aed83fc38b0850702d6879ed6f3c97eedb7d1d69d643160731179d6ed',
}
THEOREMS = [
    'hyper_zero', 'hyper_hasDerivAt', 'hyper_deriv_zero',
    'hyper_second_hasDerivAt', 'hyper_second_deriv', 'hyper_integral',
    'flat_zero', 'flat_hasDerivAt', 'flat_deriv_zero',
    'flat_second_hasDerivAt', 'flat_second_deriv', 'flat_integral',
    'hyper_tendsto_flat', 'complete_target',
]
ALLOWED_AXIOMS = {'propext', 'Classical.choice', 'Quot.sound'}

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def bindings():
    return {key: {'path': str(path.relative_to(REPO)), 'sha256': sha(path)}
            for key, path in FILES.items()}

def main():
    if Path.cwd() != REPO:
        raise RuntimeError('runner cwd differs from frozen repo root')
    if Path(__file__).resolve().parent != AXIS:
        raise RuntimeError('runner path differs from frozen owned directory')
    pre = bindings()
    if any(pre[key]['sha256'] != value for key, value in EXPECTED.items()):
        raise RuntimeError('frozen input/toolchain hash mismatch')
    run_dir = AXIS / 'attempts' / ('runner_' + datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ'))
    run_dir.mkdir(parents=True, exist_ok=False)
    snapshot = run_dir / 'source.lean'
    if snapshot.exists():
        if snapshot.read_bytes() != FILES['source'].read_bytes():
            raise RuntimeError('immutable final source already exists with different bytes')
    else:
        snapshot.write_bytes(FILES['source'].read_bytes())
    env = os.environ.copy()
    env['ELAN_TOOLCHAIN'] = 'leanprover/lean4:v4.31.0'
    commands = []
    def execute(argv, cwd, tag, timeout):
        started = datetime.now(timezone.utc).isoformat()
        try:
            p = subprocess.run(argv, cwd=cwd, env=env, capture_output=True, text=True,
                               timeout=timeout, check=False)
            code, out, err, timed_out = p.returncode, p.stdout, p.stderr, False
        except subprocess.TimeoutExpired as exc:
            code = 124
            out = (exc.stdout or b'').decode(errors='replace') if isinstance(exc.stdout, bytes) else (exc.stdout or '')
            err = (exc.stderr or b'').decode(errors='replace') if isinstance(exc.stderr, bytes) else (exc.stderr or '')
            timed_out = True
        stdout_path, stderr_path = run_dir / f'{tag}.stdout.log', run_dir / f'{tag}.stderr.log'
        stdout_path.write_text(out)
        stderr_path.write_text(err)
        record = {'argv': argv, 'cwd': str(cwd), 'exit_code': code, 'timeout_seconds': timeout,
                  'timed_out': timed_out, 'started_at': started,
                  'completed_at': datetime.now(timezone.utc).isoformat(),
                  'stdout_path': str(stdout_path.relative_to(REPO)),
                  'stderr_path': str(stderr_path.relative_to(REPO)),
                  'stdout_sha256': sha(stdout_path), 'stderr_sha256': sha(stderr_path)}
        commands.append(record)
        return code, out, err
    rev_code, rev, rev_err = execute(['git', '-C', str(FORMAL / '.lake/packages/mathlib'), 'rev-parse', 'HEAD'], REPO, 'mathlib_rev', 30)
    version_code, version, version_err = execute(['lake', 'env', 'lean', '--version'], FORMAL, 'lean_version', 60)
    compile_argv = ['lake', 'env', 'lean', str(snapshot)]
    compile_code, out, err = execute(compile_argv, FORMAL, 'compile', 3600)
    post = bindings()
    scan = {}
    for theorem in THEOREMS:
        marker = "'CAS07C01." + theorem + "' depends on axioms: "
        lines = [line for line in out.splitlines() if line.startswith(marker)]
        axioms = []
        if len(lines) == 1 and lines[0].endswith(']'):
            axioms = [part.strip() for part in lines[0].split('[', 1)[1][:-1].split(',')]
        scan[theorem] = {'printed_lines': lines, 'axioms': axioms,
                          'within_allowed': len(lines) == 1 and set(axioms) <= ALLOWED_AXIOMS}
    matched = pre == post and all(pre[k]['sha256'] == v for k, v in EXPECTED.items())
    toolchain_ok = (rev_code == 0 and rev.strip() == 'fabf563a7c95a166b8d7b6efca11c8b4dc9d911f'
                    and version_code == 0 and 'Lean (version 4.31.0,' in version)
    source_ok = sha(snapshot) == pre['source']['sha256']
    passed = (compile_code == 0 and toolchain_ok and matched and source_ok
              and all(item['within_allowed'] for item in scan.values())
              and 'sorryAx' not in out and 'sorryAx' not in err)
    result = {
        'axis': 'lean', 'status': 'PASS' if passed else 'INCONCLUSIVE',
        'contract_sha256': EXPECTED['contract'],
        'evidence_class': 'exact',
        'checks': {'CAS-07-C01': passed},
        'subchecks': {'full_source_compiled': compile_code == 0,
                      'toolchain_pinned': toolchain_ok,
                      'source_immutable': source_ok,
                      'bindings_unchanged': matched,
                      'printed_axioms_allowed': all(item['within_allowed'] for item in scan.values())},
        'domain_assumption_diff': [],
        'counterexample': None,
        'commands': commands,
        'completed_at': datetime.now(timezone.utc).isoformat(),
        'source_input_toolchain_before': pre,
        'source_input_toolchain_after': post,
        'source_snapshot': {'path': str(snapshot.relative_to(REPO)), 'sha256': sha(snapshot)},
        'statement_alignment': {
            'component': 'CAS-07-C01',
            'actual_theorem': 'CAS07C01.complete_target',
            'domain': 'all real k > 0 and real s >= 0, including s = 0; fixed-s right k to 0+',
            'claims': ['explicit sinh/sqrt positive branch', 'zero and first derivative at zero',
                       'second derivative k times f', 'actual interval integral on 0..s',
                       'separate flat initial/ODE/integral branch', 'fixed-s right continuous limit'],
            'scope_exclusions': ['Jacobi solution majorization/existence/convergence',
                                 'physical distance', 'CAS-07-C02', 'CAS-07-C03', 'scientific admission'],
            'units': {'s': 'length', 't': 'length', 'f': 'length', 'k': 'inverse length squared'},
        },
        'axiom_scan': scan,
        'proof_scope': 'full explicit CAS-07-C01 scalar identity only',
        'raw_failure_paths': ([] if passed else [str((run_dir / 'compile.stdout.log').relative_to(REPO)),
                                                str((run_dir / 'compile.stderr.log').relative_to(REPO))]),
        'author_runtime': {'native_model': 'not observed by runner',
                           'shared_llm_family': 'OpenAI Codex; exact observed turn metadata unavailable here'},
    }
    result_path = AXIS / 'result.json'
    result_path.write_text(json.dumps(result, indent=2, sort_keys=True) + '\n')
    print(json.dumps({'checks': result['checks'], 'domain_assumption_diff': result['domain_assumption_diff'],
                      'counterexample': result['counterexample'], 'subchecks': result['subchecks']}, sort_keys=True))
    return 0 if passed else 1

if __name__ == '__main__':
    sys.exit(main())
