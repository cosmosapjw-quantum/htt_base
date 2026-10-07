"""Frozen CAS14 Sage/Singular axis runner; prints one gate-compatible JSON."""

import datetime as dt
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys

BASE = Path(__file__).resolve().parent
TASK = BASE.parent
SINGULAR = Path('/home/cosmosapjw/opt/sage/local/bin/Singular')
EXPECTED = {
    'contract': 'afee8b0f823bb89f9a1507a5c8fbcff97c95f152296f88e55e15cdcdbce21639',
    'inputs': 'ed8d777bf74f3b35af925e807a90842af9530355a6f392dab5d5e0bbcf1a7591',
    'singular': '9430832b7c972b6b26d29ded4d91a3e1df8fd87d67f4b8d3f14d8201a75f923c',
}

def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def dump(path, value):
    Path(path).write_text(json.dumps(value, indent=2, sort_keys=True) + '\n')

def run(name, argv, timeout):
    result = subprocess.run(argv, cwd=BASE, text=True, capture_output=True,
                            timeout=timeout, check=False)
    (BASE / (name + '.stdout.log')).write_text(result.stdout)
    (BASE / (name + '.stderr.log')).write_text(result.stderr)
    return {'argv':argv, 'cwd':str(BASE), 'exit_code':result.returncode,
            'stdout_path':str(BASE/(name+'.stdout.log')),
            'stderr_path':str(BASE/(name+'.stderr.log'))}

def main():
    source = {name:sha(BASE/name) for name in ('Main.py','Main.sing','PROOF.md','run.py')}
    binding = {'contract':sha(TASK/'EXECUTION_CONTRACT.json'),
               'inputs':sha(TASK/'ADMITTED_INPUTS.json'),
               'singular':sha(SINGULAR)}
    commands = []
    problems = []
    for key in EXPECTED:
        if binding[key] != EXPECTED[key]:
            problems.append(f'{key} SHA mismatch: {binding[key]}')
    if not problems:
        commands.append(run('sage_version',['sage','--version'],30))
        commands.append(run('singular_version',[str(SINGULAR),'--version'],30))
        commands.append(run('sage',['sage','-python',str(BASE/'Main.py')],1800))
        commands.append(run('singular',[str(SINGULAR),'-q',str(BASE/'Main.sing')],1800))
    for command in commands:
        if command['exit_code'] != 0:
            problems.append(f"nonzero exit: {command['argv']}: {command['exit_code']}")
    sage_math = None
    if not problems:
        try:
            sage_math = json.loads((BASE/'sage.stdout.log').read_text())
        except (json.JSONDecodeError, OSError) as exc:
            problems.append('Sage output parse: '+str(exc))
        expected_singular = ('C01_projection_remainders:\n0\n0\n0\n'
                             'C02_cross_norm_remainder:\n0\n'
                             'C02_determinant_remainder:\n0\n'
                             'C03_frobenius_remainder:\n0')
        singular_raw = (BASE/'singular.stdout.log').read_text()
        singular_err = (BASE/'singular.stderr.log').read_text()
        if singular_raw.strip() != expected_singular:
            problems.append('Singular raw output differs from exact zero-certificate transcript')
        if singular_err.strip():
            problems.append('Singular stderr nonempty: '+singular_err.strip())
    checks = {k:bool(sage_math and sage_math.get('checks',{}).get(k)) and not problems
              for k in ('CAS-14-C01','CAS-14-C02','CAS-14-C03')}
    if sage_math is not None:
        dump(BASE/'math_result.json',sage_math)
    completed = dt.datetime.now(dt.timezone.utc).isoformat()
    result = {
        'axis':'sage_singular','status':'PASS' if all(checks.values()) else 'INCONCLUSIVE',
        'contract_sha256':binding['contract'],'admitted_inputs_sha256':binding['inputs'],
        'evidence_class':'exact','completed_at':completed,'commands':commands,
        'source_sha256':source,'toolchain_binding':{
            'sage_version_stdout':(BASE/'sage_version.stdout.log').read_text() if commands else None,
            'singular_binary':str(SINGULAR),'singular_binary_sha256':binding['singular'],
            'singular_version_stdout_sha256':sha(BASE/'singular_version.stdout.log') if commands else None},
        'domain_assumption_diff':sage_math.get('domain_assumption_diff',[]) if sage_math else [],
        'counterexample':sage_math.get('counterexample') if sage_math else None,
        'checks':checks,'errors':problems,
        'launch_id':None,'authority_status':'UNAVAILABLE',
        'requested_model':None,'observed_model':'UNKNOWN','observed_effort':'UNKNOWN',
        'claim_ceiling':'finite_vorticity_inverse_math_only_no_observation_or_science',
        'historical_first_failure':'failures/attempt1_sage_vector_reduction/',
    }
    dump(BASE/'result.json',result)
    dump(BASE/'execution.json',{'commands':commands,'source_sha256':source,
                                'binding':binding,'completed_at':completed,
                                'first_failure':'failures/attempt1_sage_vector_reduction/',
                                'errors':problems})
    print(json.dumps({'status':result['status'],'checks':checks,
                      'domain_assumption_diff':result['domain_assumption_diff'],
                      'counterexample':result['counterexample'],
                      'result_path':str(BASE/'result.json')},sort_keys=True))
    return 0 if all(checks.values()) else 1

if __name__ == '__main__':
    sys.exit(main())
