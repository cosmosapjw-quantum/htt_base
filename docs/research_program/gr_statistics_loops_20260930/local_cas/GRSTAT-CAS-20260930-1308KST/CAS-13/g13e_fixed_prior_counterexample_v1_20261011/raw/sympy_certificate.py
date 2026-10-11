#!/usr/bin/env python3
"""Frozen G13-E rational certificate discovery; no floating comparisons."""
import hashlib
import json
from pathlib import Path
import sys

import sympy as sp

ROOT = Path('/home/cosmosapjw/Dropbox/bianchi/htt_base')
HERE = Path(__file__).resolve().parent.parent
packet = json.loads((HERE / 'DELEGATION_PACKET.json').read_text())
u, z, y = sp.symbols('u z y')
a, b, m3, m4 = [sp.Rational(packet['accepted_inputs'][k]) for k in ('a', 'b', 'm3', 'm4')]


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


sources = {
    'TEFF_INTERVAL_SPEC.md': ROOT / 'docs/research_program/gr_statistics_loops_20260930/cas/TEFF_INTERVAL_SPEC.md',
    'TEFF_POSITIVE_BRIDGE.md': ROOT / 'docs/research_program/gr_statistics_loops_20260930/supplements/TEFF_POSITIVE_BRIDGE.md',
    'CAS-13.json': ROOT / 'docs/research_program/gr_statistics_loops_20260930/cas/contracts/CAS-13.json',
    'G13-A-bridge': HERE.parent / 'g13a_measure_extremizer_bridge_v1_20261011/MeasureExtremizerBridge.lean',
}
observed = {k: digest(p) for k, p in sources.items()}
assert observed == packet['source_identity'], (observed, packet['source_identity'])


def primitive(expr, symbol):
    return sp.Poly(expr, symbol, domain=sp.QQ).clear_denoms()[1].primitive()[1]


def rat_interval(poly, interval):
    """Termwise rational enclosure on a strictly positive interval."""
    low, high = interval
    assert 0 < low < high
    lower = upper = sp.S.Zero
    for (power,), coefficient in sp.Poly(poly, u, domain=sp.QQ).terms():
        term_lo, term_hi = coefficient * low**power, coefficient * high**power
        lower += min(term_lo, term_hi)
        upper += max(term_lo, term_hi)
    return lower, upper


def rational_interval(expr, interval):
    numerator, denominator = sp.cancel(expr).as_numer_denom()
    nl, nh = rat_interval(numerator, interval)
    dl, dh = rat_interval(denominator, interval)
    assert nl > 0 and dl > 0
    return nl / dh, nh / dl


def variations(poly, endpoint, symbol):
    values = [sp.expand(term).subs(symbol, endpoint) for term in sp.sturm(poly.as_expr(), symbol)]
    signs = [sp.sign(value) for value in values if value != 0]
    return sum(left != right for left, right in zip(signs, signs[1:])), values


secant = sp.cancel((u**4 - a**4) / (u**3 - a**3))
target = (m4 - a**4) / (m3 - a**3)
equation_num, equation_den = sp.cancel(secant - target).as_numer_denom()
P = primitive(equation_num, u)
lo, hi = sp.Rational(1078, 1000), sp.Rational(1079, 1000)
assert 0 < a < lo < hi < b and lo**3 > m3
assert P.eval(lo) < 0 < P.eval(hi)
vlo, slo = variations(P, lo, u)
vhi, shi = variations(P, hi, u)
assert vlo - vhi == 1
assert sp.Poly(P, u).count_roots(lo, hi) == 1
derivative = sp.factor(sp.diff(secant, u))
assert sp.cancel(derivative - u**2 * (3*a**2 + 2*a*u + u**2) / (a**2 + a*u + u**2)**2) == 0
assert a**3 < m3 < b**3
# Strict lower feasibility uses cubing of positive quantities, no fractional power comparison.
chord = a**4 + (m3-a**3)*(b**4-a**4)/(b**3-a**3)
assert m4 > 0 and m4**3 > m3**4 and m4 < chord
w = (m3-a**3)/(u**3-a**3)
assert m3-a**3 > 0 and lo**3 > m3
assert sp.cancel((1-w)*a**3+w*u**3-m3) == 0
fourth_gap = sp.cancel((1-w)*a**4+w*u**4-m4)
assert sp.rem(fourth_gap.as_numer_denom()[0], P.as_expr(), u) == 0

certificates = {}
for p in (5, 6):
    frame = sp.Rational(packet['accepted_inputs'][f'frame_m{p}'])
    assert frame == m4**(p-3) / m3**(p-4)
    endpoint = sp.cancel((1-w)*a**p + w*u**p)
    c0, c3, c4 = sp.symbols('c0 c3 c4')
    q = c0+c3*y**3+c4*y**4
    coefficients = sp.solve([q.subs(y, a)-a**p, q.subs(y, u)-u**p,
                             sp.diff(q, y).subs(y, u)-p*u**(p-1)], (c0,c3,c4))
    assert len(coefficients) == 3
    q = sp.cancel(q.subs(coefficients))
    assert sp.cancel(q.subs(y,a)-a**p) == 0
    assert sp.cancel(q.subs(y,u)-u**p) == 0
    assert sp.cancel(sp.diff(q,y).subs(y,u)-p*u**(p-1)) == 0
    q_moments = sp.cancel(coefficients[c0]+coefficients[c3]*m3+coefficients[c4]*m4)
    q_gap = sp.cancel(q_moments-endpoint)
    assert sp.rem(q_gap.as_numer_denom()[0], P.as_expr(), u) == 0

    gap_num, gap_den = sp.cancel(endpoint-frame).as_numer_denom()
    numerator_bounds = rat_interval(gap_num, (lo,hi))
    denominator_bounds = rat_interval(gap_den, (lo,hi))
    assert numerator_bounds[0] > 0 and denominator_bounds[0] > 0
    strict_gap_bound = numerator_bounds[0] / denominator_bounds[1]
    assert strict_gap_bound > 0
    endpoint_interval = rational_interval(endpoint, (lo,hi))
    assert endpoint_interval[0] > frame
    endpoint_num, endpoint_den = endpoint.as_numer_denom()
    algebraic_equation = primitive(sp.resultant(P.as_expr(), z*endpoint_den-endpoint_num, u), z)
    evlo, eslo = variations(algebraic_equation, endpoint_interval[0], z)
    evhi, eshi = variations(algebraic_equation, endpoint_interval[1], z)
    assert evlo-evhi == 1
    certificates[str(p)] = {
        'endpoint_expression': str(endpoint),
        'weight_expression': str(w),
        'hermite_coefficients': {str(k):str(v) for k,v in coefficients.items()},
        'q_moment_expression': str(q_moments),
        'q_moment_minus_node_endpoint_numerator_remainder_mod_P': '0',
        'endpoint_algebraic_equation': str(algebraic_equation.as_expr()),
        'endpoint_rational_isolating_interval': [str(t) for t in endpoint_interval],
        'endpoint_sturm_variations': [evlo,evhi],
        'endpoint_sturm_values': [[str(t) for t in eslo],[str(t) for t in eshi]],
        'frame_value': str(frame),
        'gap_numerator': str(gap_num), 'gap_denominator': str(gap_den),
        'gap_numerator_interval': [str(t) for t in numerator_bounds],
        'gap_denominator_interval': [str(t) for t in denominator_bounds],
        'strict_positive_gap_lower_bound': str(strict_gap_bound),
        'strict_comparison_certified': True,
    }

result = {
    'task_id': packet['task_id'], 'status': 'EXACT_RATIONAL_CERTIFICATE_PASS',
    'claim_ceiling': 'certificate discovery only; no Lean theorem, full G13-E completion, FD/BE inversion, scientific admission or four-axis adjudication',
    'runtime': {'requested_model':'gpt-6.1-sol','requested_effort':'medium',
                'observed_model':'UNKNOWN','observed_effort':'UNKNOWN',
                'python_executable':sys.executable,'python_version':sys.version,
                'sympy_version':sp.__version__},
    'source_identity_verified': observed,
    'packet_sha256': digest(HERE/'DELEGATION_PACKET.json'),
    'script_sha256': digest(Path(__file__)),
    'node': {'secant_expression':str(secant), 'target':str(target),
             'equation':str(P.as_expr()), 'secant_difference_denominator':str(equation_den),
             'isolating_interval':[str(lo),str(hi)],
             'polynomial_endpoint_values':[str(P.eval(lo)),str(P.eval(hi))],
             'sturm_variations':[vlo,vhi], 'sturm_values':[[str(t) for t in slo],[str(t) for t in shi]],
             'lower_endpoint_cube_minus_m3':str(lo**3-m3),
             'monotone_secant_derivative':str(derivative),
             'uniqueness_domain':'positiveCubeRoot(m3)<u<b; derivative strictly positive there',
             'weight_strict_between_zero_and_one':True,
             'moments_match_mod_P':True},
    'strict_interior': {'a3_lt_m3_lt_b3':True,'m4_positive':True,
                        'm4_cube_minus_m3_fourth':str(m4**3-m3**4),
                        'chord_minus_m4':str(chord-m4)},
    'certificate_method':'exact QQ polynomial elimination, Sturm root counts, and termwise rational interval inequalities on a positive node interval; no decimals or numerical root comparisons',
    'certificates': certificates,
}
print(json.dumps(result, indent=2))
