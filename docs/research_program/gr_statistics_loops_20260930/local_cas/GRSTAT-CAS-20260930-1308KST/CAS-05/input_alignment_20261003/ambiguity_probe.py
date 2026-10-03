"""Exploratory input-ambiguity witness; no CAS05 component is certified.

Compare two possible completions differing only by h_00=(x1)^3, using
signature (-,+,+,+) and the neutral curvature convention. This difference
is NOT a proposed or admitted value for the campaign's missing H_00.
No campaign source, result, or proof is imported.
"""
import hashlib
import json
import platform
from pathlib import Path

import sympy as s

x = s.symbols('x0:4', real=True)
eta = s.diag(-1, 1, 1, 1)
h = s.zeros(4)
h[0, 0] = x[1]**3
# Coefficient of the perturbation parameter in the Levi-Civita connection.
# The metric derivative is already first order; its inverse factor is eta.
gamma = [[[s.expand(sum(eta[a, d] * (
    s.diff(h[d, c], x[b]) + s.diff(h[d, b], x[c])
    - s.diff(h[b, c], x[d])) / 2 for d in range(4)))
    for c in range(4)] for b in range(4)] for a in range(4)]
# Gamma*Gamma has zero coefficient at first order about constant eta.
ricci = s.Matrix(4, 4, lambda a, b: s.expand(sum(
    s.diff(gamma[m][a][b], x[m]) - s.diff(gamma[m][a][m], x[b])
    for m in range(4))))
scalar = s.expand(sum(eta[a, b] * ricci[a, b]
                      for a in range(4) for b in range(4)))
einstein = s.simplify(ricci - eta * scalar / 2)
expected = s.diag(0, 0, -3*x[1], -3*x[1])
residuals = [s.expand(v) for v in einstein - expected]
divergence = [s.expand(sum(eta[a, a] * s.diff(einstein[a, b], x[a])
                          for a in range(4))) for b in range(4)]
origin = dict.fromkeys(x, 0)
jet = [h[0, 0].subs(origin)]
jet += [s.diff(h[0, 0], v).subs(origin) for v in x]
jet += [s.diff(h[0, 0], v, w).subs(origin) for v in x for w in x]
assert all(v == 0 for v in residuals + divergence + jet)
assert all(einstein[0, i] == 0 for i in range(1, 4))
assert einstein[2, 2] != 0
print(json.dumps({
    'status': 'EXACT_AMBIGUITY_WITNESS',
    'scope': 'Exploratory flat linear-jet difference; not a CAS05 axis rerun',
    'scientific_admission': 'HOLD', 'cas05_component_pass': False,
    'runtime': {'python': platform.python_version(), 'sympy': s.__version__,
                'sympy_origin': s.__file__},
    'source_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
    'difference_h00': str(h[0, 0]),
    'linear_ricci': [[str(v) for v in row] for row in ricci.tolist()],
    'linear_scalar': str(scalar),
    'linear_einstein': [[str(v) for v in row] for row in einstein.tolist()],
    'expected_residuals': [str(v) for v in residuals],
    'linear_bianchi_divergence': [str(v) for v in divergence],
    'origin_j2_h00': [str(v) for v in jet],
    'interpretation': 'Specifying j2H=0 and the 0i target cannot determine '
                      'the omitted 00 component or all differentiated Einstein jets.'
}, indent=2))
