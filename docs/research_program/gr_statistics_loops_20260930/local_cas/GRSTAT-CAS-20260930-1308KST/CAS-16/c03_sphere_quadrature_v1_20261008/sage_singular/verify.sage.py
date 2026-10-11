"""Exact finite CAS-16-C03 Sage certificate; run with `sage -python`."""

import json
from math import comb

from sage.all import AA, QQ, PolynomialRing


def fourier_numerator(a, b):
    # Numerator of (t+t^-1)^a (t-t^-1)^b, before 2^-d i^-b.
    coeff = {}
    for k in range(a + 1):
        for l in range(b + 1):
            e = a + b - 2 * (k + l)
            coeff[e] = coeff.get(e, 0) + comb(a, k) * comb(b, l) * (-1) ** l
    return coeff


s70 = AA(70).sqrt()
s107 = (AA(10) / 7).sqrt()
r1 = (AA(5) - 2 * s107).sqrt() / 3
r2 = (AA(5) + 2 * s107).sqrt() / 3
w0 = AA(128) / 225
w1 = (AA(322) + 13 * s70) / 900
w2 = (AA(322) - 13 * s70) / 900
nodes_weights = [(AA(0), w0), (r1, w1), (-r1, w1), (r2, w2), (-r2, w2)]
assert all(w > 0 for _, w in nodes_weights)
assert sum(w for _, w in nodes_weights) == 2
assert r1 > 0 and r2 > r1 and r2 < 1


def gl5_moment(k):
    return sum(w * x**k for x, w in nodes_weights)


for k in range(9):
    assert gl5_moment(k) == (QQ(2) / (k + 1) if k % 2 == 0 else QQ(0)), k

R = PolynomialRing(QQ, "mu")
mu = R.gen()
triples = []
zero_angular = 0
for a in range(9):
    for b in range(9 - a):
        coeff = fourier_numerator(a, b)
        d = a + b
        assert sum(v for e, v in coeff.items() if e % 9 == 0) == coeff.get(0, 0)
        for c in range(9 - d):
            triples.append((a, b, c))
            if d % 2:
                assert coeff.get(0, 0) == 0
                zero_angular += 1
                continue
            if b % 2:
                assert coeff.get(0, 0) == 0
                zero_angular += 1
                continue
            angular = QQ(((-1) ** (b // 2)) * coeff.get(0, 0)) / (2**d)
            radial = (1 - mu**2) ** (d // 2) * mu**c
            assert radial.degree() <= 8
            q = angular * sum(w * radial(x) for x, w in nodes_weights) / 2
            integral = angular * sum(
                v * (QQ(1) / (k + 1) if k % 2 == 0 else QQ(0))
                for k, v in enumerate(radial.list())
            )
            assert q == integral, (a, b, c, q, integral)

assert len(triples) == 165

# Standard four-point GL roots and paired weights; unnormalized witness.
s65 = (AA(6) / 5).sqrt()
s30 = AA(30).sqrt()
u_plus = (AA(3) + 2 * s65) / 7
u_minus = (AA(3) - 2 * s65) / 7
gl4_m8 = 2 * ((AA(18) - s30) / 36 * u_plus**4 + (AA(18) + s30) / 36 * u_minus**4)
gl4_diff = gl4_m8 - AA(2) / 9
assert gl4_diff == -QQ(128) / 11025
assert gl4_diff / 2 == -QQ(64) / 11025

cos8 = fourier_numerator(8, 0)
azimuth8_diff = QQ(sum(v for e, v in cos8.items() if e % 8 == 0) - cos8[0]) / 256
assert azimuth8_diff == QQ(1) / 128

print(json.dumps({
    "status": "PASS", "axis": "sage_singular", "scope": "CAS-16-C03 finite scalar product grid",
    "sage_version": __import__("sage.version", fromlist=["version"]).version,
    "monomials_exact": len(triples), "angular_zero_cases": zero_angular,
    "gl5_moments_exact": 9, "gl4_mu8_difference": "-128/11025",
    "gl4_mu8_normalized_difference": "-64/11025", "nphi8_cos8_difference": "1/128",
    "branches": "nonnegative real square roots", "method": "AA algebraic nodes; exact Fourier coefficients; QQ polynomial integration"
}, sort_keys=True))
