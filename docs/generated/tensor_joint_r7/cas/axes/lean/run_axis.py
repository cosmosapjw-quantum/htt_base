#!/usr/bin/env python3
"""Compile the independent Lean source and emit the frozen three-key CAS payload."""
from __future__ import annotations
import datetime
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import time

AXIS = Path(__file__).resolve().parent
ROOT = AXIS.parents[4]
RUN = ROOT / '.agent-harness/runs/TENSOR-JOINT-R7-20260908'
CONTRACT = RUN / 'CAS_CONTRACT.json'
EXPECTED_CONTRACT = '377c7be24bd070c3bd0dd0e39be003de0ac37f66fe205eaa8cb9d283019113a2'
LEAN = Path('/home/cosmosapjw/.elan/toolchains/leanprover--lean4---v4.31.0/bin/lean')
MATHLIB = Path('/mnt/sn850x2t/htt_base_e2e/lean-shared/v4.31.0/packages/mathlib')
THEOREMS = {
 'T1_trace_and_contraction': ['T1_symmetry', 'T1_trace_and_contraction'],
 'T1_no_proper_signed_stabilizer': ['T1_no_proper_signed_stabilizer'],
 'T3_normalized_derivative_and_odd_signs': ['T3_normalized_derivative', 'T3_normalized_derivative_and_odd_signs'],
 'T5_first_order_inverse_coefficient': ['T5_inverse_coefficients', 'T5_first_order_inverse_coefficient'],
 'T5_scalar_cost_implication': ['T5_scalar_cost_implication'],
 'T6_scalar_information_one_fifth': ['T6_scalar_information_one_fifth'],
 'L10_accepted_minors_and_minimal_cutoff': ['accepted_rational_positivity', 'L10_accepted_minors_and_minimal_cutoff'],
}

def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def main():
    start = time.monotonic()
    receipt = {'started_at': datetime.datetime.now(datetime.timezone.utc).isoformat(), 'engine': 'Lean + mathlib', 'failures': []}
    differences = []
    checks = dict.fromkeys(THEOREMS, False)
    if sha(CONTRACT) != EXPECTED_CONTRACT:
        differences.append('CAS contract identity differs from the registered assignment')
    contract = json.loads(CONTRACT.read_text())
    if set(contract['target']['exact_test_obligations']) != set(THEOREMS):
        differences.append('Contract obligations differ from the compiled theorem mapping')
    for item in contract['identity']['source_input_hashes']:
        if sha(ROOT / item['path']) != item['sha256']:
            differences.append('Frozen source identity mismatch: ' + item['path'])
    toolchain = (ROOT / 'formal/lean-toolchain').read_text().strip()
    if toolchain != 'leanprover/lean4:v4.31.0':
        differences.append('Repository Lean toolchain differs from v4.31.0')
    source = json.loads((ROOT / 'docs/generated/tensor_joint_r7/axial_certificate_source.json').read_text())
    sizes = [4, 4, 4, 3, 2, 1]
    if source['complex_block_ranks'] != sizes or source['real_stored_rank'] != 32:
        differences.append('Accepted block dimensions differ from the formalization')
    for m, row in enumerate(source['pivot_minors']):
        if row['m'] != m or row['source_ells'] != list(range(7, 7 + sizes[m])):
            differences.append('Accepted source-column identity differs in block ' + str(m))
    proof = AXIS / 'Proof.lean'
    proof_text = proof.read_text()
    for row in source['pivot_minors']:
        if row['determinant_squared'] not in proof_text:
            differences.append('Accepted exact rational missing from Lean source')
    for val in source['normal_block_determinants']:
        if val not in proof_text:
            differences.append('Accepted normal determinant missing from Lean source')
    if 'sorry' in proof_text or 'admit' in proof_text or '\naxiom ' in proof_text:
        differences.append('Unproved assertion token present in Lean source')
    receipt.update({'contract_sha256': sha(CONTRACT), 'proof_sha256': sha(proof), 'repository_toolchain': toolchain,
                    'theorem_mapping': THEOREMS, 'domain_assumption_diff': differences})
    if not differences:
        env = os.environ.copy()
        paths = json.loads((AXIS / 'lean_paths.json').read_text())
        env['LEAN_PATH'] = ':'.join(paths)
        argv = [str(LEAN), str(proof), '-o', str(AXIS / 'Proof.olean')]
        receipt['argv'] = argv
        receipt['lean_path'] = paths
        try:
            receipt['lean_version'] = subprocess.check_output([str(LEAN), '--version'], text=True).strip()
            receipt['mathlib_commit'] = subprocess.check_output(['git', '-C', str(MATHLIB), 'rev-parse', 'HEAD'], text=True).strip()
            result = subprocess.run(argv, cwd=ROOT, env=env, capture_output=True, text=True, timeout=3600)
            transcript = result.stdout + result.stderr
            transcript_path = AXIS / ('last_build_transcript.log' if (AXIS / 'build_transcript.log').exists() else 'build_transcript.log')
            transcript_path.write_text(transcript)
            receipt['exit_code'] = result.returncode
            receipt['build_transcript_path'] = str(transcript_path)
            receipt['build_transcript_sha256'] = sha(transcript_path)
            for name, thms in THEOREMS.items():
                checks[name] = result.returncode == 0 and all("'R7." + t + "' depends on axioms:" in transcript for t in thms) and 'sorryAx' not in transcript
            if result.returncode != 0:
                receipt['failures'].append('Lean compilation failed; transcript retained')
        except (OSError, subprocess.SubprocessError) as error:
            receipt['failures'].append(str(error))
    receipt['elapsed_seconds'] = time.monotonic() - start
    receipt['completed_at'] = datetime.datetime.now(datetime.timezone.utc).isoformat()
    receipt['checks'] = checks
    receipt_path = AXIS / ('last_build_receipt.json' if (AXIS / 'build_receipt.json').exists() else 'build_receipt.json')
    receipt_path.write_text(json.dumps(receipt, indent=2) + '\n')
    payload = {'checks': checks, 'domain_assumption_diff': differences, 'counterexample': None}
    (AXIS / 'axis_payload.json').write_text(json.dumps(payload, indent=2) + '\n')
    print(json.dumps(payload, separators=(',', ':')))
    return 0 if all(checks.values()) and not differences else 1

if __name__ == '__main__':
    sys.exit(main())
