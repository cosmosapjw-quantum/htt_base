#!/usr/bin/env python3
"""Recompile the owned CAS-05 finite Lean theorems on every invocation."""
from __future__ import annotations

import datetime as dt
import hashlib
import json
import pathlib
import re
import subprocess
import sys
import uuid

HERE = pathlib.Path(__file__).resolve().parent
ROOT = pathlib.Path('/home/cosmosapjw/Dropbox/bianchi/htt_base')
PROJECT = ROOT / 'formal_mathlib'
INPUTS = {
    ROOT / 'docs/research_program/gr_statistics_loops_20260930/local_cas/GRSTAT-CAS-20260930-1308KST/CAS-05/neutral_admission_20261003/EXECUTION_CONTRACT_V3.json': 'a67bf54921c80d35865d28dfce86d0ff9670270a807d5f2f45f25e3e7029537f',
    ROOT / 'docs/research_program/gr_statistics_loops_20260930/local_cas/GRSTAT-CAS-20260930-1308KST/CAS-05/neutral_admission_20261003/NEUTRAL_INPUT.json': '0868c1f15226e71926dad034319b85c73a9ca9c7d3c72064e06ff65d0112b27b',
    ROOT / 'docs/research_program/gr_statistics_loops_20260930/cas/COMMON_SPEC.md': '4714827e52acf3cb149f4014ac50ab2aa995dd4a0526f6b26ac7257807fe1897',
    PROJECT / 'lean-toolchain': 'efac0b94923b2d8b6840cd35be9177ad0fc5ab2332f4f4311c98712cee92fdee',
    PROJECT / 'lake-manifest.json': 'bc86de9aed83fc38b0850702d6879ed6f3c97eedb7d1d69d643160731179d6ed',
}
CONTRACT_SHA = next(iter(INPUTS.values()))
SOURCES = (HERE / 'CAS05Finite.lean', HERE / 'CAS05C03.lean')
REQUIRED = {
    'CAS-05-C01': (
        'CAS05Finite.christoffel_from_metric',
        'CAS05Finite.dChristoffel_from_metric',
        'CAS05Finite.ricci_from_connection',
        'CAS05Finite.einstein_from_metric',
        'CAS05Finite.phi_exact_taylor',
        'CAS05Finite.origin_G',
        'CAS05Finite.origin_stress00',
        'CAS05Finite.origin_stressii',
        'CAS05Finite.origin_gap_pos',
        'CAS05Finite.origin_strictDEC',
        'CAS05Finite.origin_G_exact_first_jet',
        'CAS05Finite.eigenvector_differentiated_equation',
        'CAS05Finite.origin_acceleration',
        'CAS05Finite.other_eigenvector_rates_zero',
        'CAS05Finite.density_first_jet_zero',
        'CAS05Finite.nonEOS_pressure_gradient',
    ),
    'CAS-05-C02': (
        'CAS05Finite.ray_phi',
        'CAS05Finite.ray_metric_scale',
        'CAS05Finite.ray_frame_gap',
        'CAS05Finite.ray_lambda_zero',
        'CAS05Finite.ray_conditional_root',
    ),
    'CAS-05-C03': (
        'CAS05C03.S_symmetric',
        'CAS05C03.W_skew',
        'CAS05C03.H_symmetric',
        'CAS05C03.H00_zero',
        'CAS05C03.H_from_third_jet',
        'CAS05C03.H_homogeneous_cubic',
        'CAS05C03.H_origin_zero',
        'CAS05C03.j1H_origin',
        'CAS05C03.j2H_origin',
        'CAS05C03.ddGamma_derived_from_metric3jet',
        'CAS05C03.dRicci_derived_from_connection_jet',
        'CAS05C03.dEinstein_derived_from_metric3jet',
        'CAS05C03.full40_first_Einstein_coefficients',
        'CAS05C03.origin_bianchi_four',
        'CAS05C03.all_twelve_basis_0i',
        'CAS05C03.full40_for_each_of_twelve_basis',
        'CAS05C03.universal_right_inverse_0i',
        'CAS05C03.normalizedEigenvectorJet_eq_k',
        'CAS05C03.normalized_differentiated_eigen_equation',
    ),
}
ALLOWED_AXIOMS = {'propext', 'Classical.choice', 'Quot.sound'}

def sha(path: pathlib.Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()

def utc() -> str:
    return dt.datetime.now(dt.timezone.utc).isoformat().replace('+00:00', 'Z')

def execute(argv: list[str], run_dir: pathlib.Path, label: str) -> dict:
    item = {'argv': argv, 'cmd': ' '.join(argv), 'cwd': str(PROJECT), 'started_at': utc()}
    try:
        proc = subprocess.run(argv, cwd=PROJECT, capture_output=True, text=True,
                              timeout=3600, check=False)
        item['exit_code'] = proc.returncode
        out, err = proc.stdout, proc.stderr
    except subprocess.TimeoutExpired as exc:
        item['exit_code'] = None
        item['timeout_seconds'] = 3600
        out = (exc.stdout or b'').decode(errors='replace') if isinstance(exc.stdout, bytes) else (exc.stdout or '')
        err = (exc.stderr or b'').decode(errors='replace') if isinstance(exc.stderr, bytes) else (exc.stderr or '')
    item['completed_at'] = utc()
    (run_dir / f'{label}.stdout.log').write_text(out)
    (run_dir / f'{label}.stderr.log').write_text(err)
    item['stdout_path'] = str(run_dir / f'{label}.stdout.log')
    item['stderr_path'] = str(run_dir / f'{label}.stderr.log')
    return item

def printed_axioms(stdout: str) -> dict[str, set[str]]:
    found = {}
    for name, raw in re.findall(r"'([^']+)' depends on axioms: \[([^\]]*)\]", stdout):
        found[name] = {part.strip() for part in raw.split(',') if part.strip()}
    return found

def main() -> dict:
    run_dir = HERE / 'runs' / (dt.datetime.now(dt.timezone.utc).strftime('%Y%m%dT%H%M%SZ') + '-' + uuid.uuid4().hex[:8])
    run_dir.mkdir(parents=True, exist_ok=False)
    observed = {str(path): (sha(path) if path.is_file() else None) for path in INPUTS}
    source_hashes = {str(path): (sha(path) if path.is_file() else None)
                     for path in (*SOURCES, HERE / 'run.py')}
    inputs_ok = all(observed[str(path)] == expected for path, expected in INPUTS.items())
    version = execute(['lake', 'env', 'lean', '--version'], run_dir, 'version')
    version_text = pathlib.Path(version['stdout_path']).read_text()
    manifest = json.loads((PROJECT / 'lake-manifest.json').read_text())
    revs = [item.get('rev') for item in manifest.get('packages', []) if item.get('name') == 'mathlib']
    version_ok = version['exit_code'] == 0 and '4.31.0' in version_text and revs == ['fabf563a7c95a166b8d7b6efca11c8b4dc9d911f']
    commands = [version]
    compiled = {}
    axioms = {}
    if inputs_ok and version_ok and all(path.is_file() for path in SOURCES):
        for index, source in enumerate(SOURCES, 1):
            command = execute(['lake', 'env', 'lean', '-j1', str(source)], run_dir, f'source{index}')
            commands.append(command)
            compiled[str(source)] = command['exit_code'] == 0
            axioms.update(printed_axioms(pathlib.Path(command['stdout_path']).read_text()))
    checks = {}
    for component, names in REQUIRED.items():
        source = SOURCES[0] if component != 'CAS-05-C03' else SOURCES[1]
        checks[component] = bool(inputs_ok and version_ok and compiled.get(str(source), False)
                                 and all(name in axioms and axioms[name] <= ALLOWED_AXIOMS
                                         for name in names))
    result = {
        'axis': 'lean',
        'status': 'PASS' if all(checks.values()) else 'HOLD',
        'contract_sha256': CONTRACT_SHA,
        'checks': checks,
        'domain_assumption_diff': [],
        'counterexample': None,
        'commands': commands,
        'completed_at': utc(),
        'evidence_class': 'exact',
        'input_hashes': observed,
        'source_hashes': source_hashes,
        'toolchain': {'lean_version': version_text.strip(), 'mathlib_rev': revs[0] if revs else None},
        'printed_axioms': {name: sorted(values) for name, values in axioms.items()},
        'raw_run_dir': str(run_dir),
        'scientific_admission': 'HOLD',
    }
    (run_dir / 'result.json').write_text(json.dumps(result, indent=2) + '\n')
    (HERE / 'result.json').write_text(json.dumps(result, indent=2) + '\n')
    return {'checks': checks, 'domain_assumption_diff': [], 'counterexample': None}

if __name__ == '__main__':
    try:
        output = main()
    except Exception as exc:
        output = {'checks': {name: False for name in REQUIRED},
                  'domain_assumption_diff': [], 'counterexample': None,
                  'runner_error': f'{type(exc).__name__}: {exc}'}
    sys.stdout.write(json.dumps(output, sort_keys=True, separators=(',', ':')) + '\n')
