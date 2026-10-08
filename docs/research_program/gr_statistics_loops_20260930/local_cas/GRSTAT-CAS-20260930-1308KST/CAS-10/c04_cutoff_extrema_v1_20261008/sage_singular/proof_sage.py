"""Exact Sage proof for the frozen CAS-10-C04 cutoff component."""
import json
from sage.all import AA, QQ, PolynomialRing, factor
from sage.version import version as sage_version


P = PolynomialRing(QQ, "t")
t = P.gen()
F = 1 - 10*t**3 + 15*t**4 - 6*t**5
d1 = F.derivative()
d2 = d1.derivative()
d3 = d2.derivative()
q = 6*t**2 - 6*t + 1

# These factorizations identify every stationary point on the compact domain.
assert d1 == -30*t**2*(1-t)**2
assert d2 == -60*t*(2*t-1)*(t-1)
assert d3 == -60*q
assert F(0) == 1 and F(1) == 0
assert d1(0) == d1(1) == d2(0) == d2(1) == 0

half = QQ(1)/2
first_candidates = [QQ(0), half, QQ(1)]
first_values = [abs(d1(x)) for x in first_candidates]
assert first_values == [0, QQ(15)/8, 0]

sqrt3 = AA(3).sqrt()  # the positive real branch
minus = (3-sqrt3)/6
plus = (3+sqrt3)/6
assert 0 < minus < half < plus < 1
assert q(minus) == q(plus) == 0
second_candidates = [AA(0), minus, plus, AA(1)]
second_values = [d2(x) for x in second_candidates]
assert second_values == [0, -10/sqrt3, 10/sqrt3, 0]
assert max(abs(x) for x in second_values) == 10/sqrt3

margin = QQ(25)/24*(QQ(14)/15 + QQ(9)/400)
assert margin == QQ(1147)/1152 and margin < 1

# A differentiable function on [0,1] takes its absolute maximum at an
# endpoint, a zero, or a derivative zero. The factorizations above exhaust
# the derivative zeros. Zeros add value 0 and cannot raise these maxima.
print(json.dumps({
    "sage_version": sage_version,
    "all_exact_checks": True,
    "F": str(F),
    "D1": str(d1),
    "D2": str(d2),
    "D3": str(d3),
    "D2_factor": str(factor(d2)),
    "D3_factor": str(factor(d3)),
    "F_endpoints": [str(F(0)), str(F(1))],
    "D1_endpoint_jets": [str(d1(0)), str(d1(1))],
    "D2_endpoint_jets": [str(d2(0)), str(d2(1))],
    "D1_abs_candidate_values": [str(x) for x in first_values],
    "D2_candidate_values": ["0", "-10/sqrt(3)", "10/sqrt(3)", "0"],
    "D1_absolute_max": "15/8",
    "D1_equality_points": ["1/2"],
    "D2_absolute_max": "10/sqrt(3)",
    "D2_equality_points": ["(3-sqrt(3))/6", "(3+sqrt(3))/6"],
    "margin": str(margin),
    "margin_below_one": True,
}, sort_keys=True))
