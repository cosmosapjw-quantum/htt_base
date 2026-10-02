#!/usr/bin/env python3
"""Independent Lean axis; checks are true only for complete contracted components."""
import json
import os
from pathlib import Path
import subprocess

here = Path(__file__).resolve().parent
repo = here.parents[6]
contract = json.loads((here.parent / 'EXECUTION_CONTRACT.json').read_text())
obligations = contract['target']['exact_test_obligations']
argv = ['lake', 'env', 'lean', str(here / 'Main.lean')]
env = dict(os.environ, ELAN_TOOLCHAIN='leanprover/lean4:v4.31.0')
v = subprocess.run(['lake', 'env', 'lean', '--version'], cwd=repo / 'formal_mathlib',
                   env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
(here / 'lean.version.log').write_text(v.stdout + v.stderr)
p = subprocess.run(argv, cwd=repo / 'formal_mathlib', env=env,
                   stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
(here / 'lean.stdout.log').write_text(p.stdout)
(here / 'lean.stderr.log').write_text(p.stderr)
(here / 'lean.exit.txt').write_text(str(p.returncode) + '\n')
(here / 'lean.argv.json').write_text(json.dumps({'argv': argv, 'cwd': str(repo / 'formal_mathlib'),
  'ELAN_TOOLCHAIN': env['ELAN_TOOLCHAIN']}, indent=2) + '\n')
result = {'axis': 'lean', 'checks': {k: False for k in obligations},
                  'domain_assumption_diff': ['Only beta-gamma mass-shell algebra proved; Gram construction, scaling, conformal connection and coordinate invariance remain open.'], 'counterexample': None,
                  'compiler_exit': p.returncode,
                  'axioms': [line for line in p.stdout.splitlines() if 'depends on axioms' in line],
                  'statement_alignment': 'Only necessary sublemma(s), where present; no complete contracted component certified.'}
(here / 'result.json').write_text(json.dumps(result, indent=2) + '\n')
print(json.dumps(result))
