#!/usr/bin/env python3
"""Independent O4 polynomial identities; stdout is one cas_gate JSON payload.

No production implementation or sibling axis is imported. All components and
six index/vector permutations are explicitly checked over QQ(i)[A,u,v,w,z].
No division by vector norms, amplitude, or polynomial roots is performed.
"""
from datetime import datetime, timezone
from hashlib import sha256
from itertools import permutations, product
import json
from pathlib import Path
import platform
import sys
import time

import sympy as sp

CONTRACT_SHA256 = '430f325399b7caf0e7513cccec64e5bdae114ecafa5ce039747e373936c82f9d'
CONTEXT_VERSION = '2aadf7ee464f3801564eb811ce842dacce78a59d68206d10d6304fbb79a13fa4'
ROOT = Path(__file__).resolve().parents[5]
CONTRACT_PATH = ROOT / '.agent-harness/runs/R8-B-20260909/CAS_CONTRACT.json'
OBLIGATIONS = (
    'O4_STF2_trace_sign_permutation',
    'O4_STF3_trace_sign_permutation',
    'O4_null_cone_and_trace_removal',
)


def main():
    started = datetime.now(timezone.utc).isoformat()
    clock_start = time.monotonic()
    raw = CONTRACT_PATH.read_bytes()
    if sha256(raw).hexdigest() != CONTRACT_SHA256:
        raise RuntimeError('Frozen CAS contract mismatch')
    contract = json.loads(raw)
    if contract['target']['exact_test_obligations'] != list(OBLIGATIONS):
        raise RuntimeError('Contract obligation drift')
    if sp.__version__ != '1.14.0':
        raise RuntimeError('SymPy pin mismatch: ' + sp.__version__)
    for source in contract['identity']['source_input_hashes']:
        if sha256((ROOT / source['path']).read_bytes()).hexdigest() != source['sha256']:
            raise RuntimeError('Frozen input mismatch: ' + source['path'])
    A = sp.Symbol('A', real=True)
    u = sp.symbols('u0:3', real=True)
    v = sp.symbols('v0:3', real=True)
    w = sp.symbols('w0:3', real=True)
    z = sp.Symbol('z')  # arbitrary complex, no conjugation
    generators = (A, *u, *v, *w, z)
    delta = lambda i, j: sp.Integer(i == j)
    dot = lambda x, y: sum(x[i] * y[i] for i in range(3))
    ij = list(product(range(3), repeat=2))
    ijk = list(product(range(3), repeat=3))
    perms = list(permutations(range(3)))

    def stf2(amplitude, x, y):
        return {(i, j): amplitude * ((x[i]*y[j] + y[i]*x[j])/2
                - delta(i, j)*dot(x, y)/3) for i, j in ij}

    def stf3(amplitude, x, y, t):
        vectors = (x, y, t)
        b = tuple((dot(x,y)*t[k] + dot(x,t)*y[k] + dot(y,t)*x[k])/3
                  for k in range(3))
        out = {}
        for indices in ijk:
            i, j, k = indices
            raw_sym = sum(vectors[p[0]][i]*vectors[p[1]][j]*vectors[p[2]][k]
                          for p in perms)/6
            out[indices] = amplitude * (raw_sym - (
                delta(i,j)*b[k] + delta(i,k)*b[j] + delta(j,k)*b[i])/5)
        return out

    details = {key: {} for key in OBLIGATIONS}
    counterexamples = []

    def zero(obligation, label, expression):
        # Coefficient equality in an exact polynomial ring, no sampled fixtures.
        polynomial = sp.Poly(sp.expand(expression), *generators, domain=sp.QQ_I)
        passed = polynomial.is_zero is True
        details[obligation][label] = passed
        if not passed:
            counterexamples.append({'obligation': obligation, 'check': label,
                                    'nonzero_residual': str(polynomial.as_expr())})

    q = stf2(A, u, v)
    q_swap = stf2(A, v, u)
    q_sign = stf2(-A, tuple(-x for x in u), v)
    q_zero = stf2(sp.Integer(0), u, v)
    key = OBLIGATIONS[0]
    for i, j in ij:
        zero(key, f'index_symmetry_{i}{j}', q[i,j]-q[j,i])
        zero(key, f'vector_swap_{i}{j}', q[i,j]-q_swap[i,j])
        zero(key, f'amplitude_vector_sign_{i}{j}', q[i,j]-q_sign[i,j])
        zero(key, f'zero_amplitude_{i}{j}', q_zero[i,j])
    zero(key, 'trace', sum(q[i,i] for i in range(3)))

    o = stf3(A, u, v, w)
    o_sign = stf3(-A, tuple(-x for x in u), v, w)
    o_zero = stf3(sp.Integer(0), u, v, w)
    key = OBLIGATIONS[1]
    vectors = (u, v, w)
    for p in perms:
        o_permuted_vectors = stf3(A, *(vectors[j] for j in p))
        for indices in ijk:
            permuted_indices = tuple(indices[j] for j in p)
            zero(key, f'index_permutation_{p}_{indices}',
                 o[indices]-o[permuted_indices])
            zero(key, f'vector_permutation_{p}_{indices}',
                 o[indices]-o_permuted_vectors[indices])
    for indices in ijk:
        zero(key, f'amplitude_vector_sign_{indices}', o[indices]-o_sign[indices])
        zero(key, f'zero_amplitude_{indices}', o_zero[indices])
    for k in range(3):
        zero(key, f'trace_{k}', sum(o[i,i,k] for i in range(3)))

    key = OBLIGATIONS[2]
    n = (1-z*z, sp.I*(1+z*z), 2*z)
    zero(key, 'bilinear_null_cone', dot(n,n))
    zero(key, 'rank2_trace_removal',
         sum(q[i,j]*n[i]*n[j] for i,j in ij) - A*dot(u,n)*dot(v,n))
    zero(key, 'rank3_trace_removal',
         sum(o[i,j,k]*n[i]*n[j]*n[k] for i,j,k in ijk)
         - A*dot(u,n)*dot(v,n)*dot(w,n))
    checks = {key: all(details[key].values()) for key in OBLIGATIONS}
    payload = {
        'schema_version': 2,
        'axis': 'sympy',
        'contract_id': contract['identity']['contract_id'],
        'contract_sha256': CONTRACT_SHA256,
        'context_version': CONTEXT_VERSION,
        'checks': checks,
        'domain_assumption_diff': [],
        'counterexample': counterexamples or None,
        'evidence_class': 'exact',
        'tool_versions': {'python': platform.python_version(), 'sympy': sp.__version__,
                          'python_executable': sys.executable},
        'method': 'All residual polynomial coefficients vanish in QQ(i)[A,u,v,w,z]; full component multiplicity.',
        'component_checks': details,
        'component_check_counts': {key: len(values) for key, values in details.items()},
        'exact_zero_residual_count': sum(sum(values.values()) for values in details.values()),
        'started_at': started,
        'completed_at': datetime.now(timezone.utc).isoformat(),
        'elapsed_seconds': time.monotonic()-clock_start,
        'claim_ceiling': contract['identity']['claim_ceiling'],
    }
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0 if all(checks.values()) else 1


if __name__ == '__main__':
    sys.exit(main())
