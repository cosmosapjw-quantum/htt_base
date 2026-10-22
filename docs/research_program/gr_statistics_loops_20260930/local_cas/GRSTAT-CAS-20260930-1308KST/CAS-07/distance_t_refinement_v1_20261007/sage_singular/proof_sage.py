"""Exact polynomial certificates for CAS07 M06; run with Sage 10.9."""

import json

from sage.all import QQ, PolynomialRing


P = PolynomialRing(QQ, names=("s", "L", "dA", "M", "H", "c", "es", "et", "eL", "t", "q"))
s, L, dA, M, H, c, es, et, eL, t, q = P.gens()
F = P.fraction_field()
den = 1 - eL

# Domain: dA-s(1-eL) is a sum of admitted nonnegative terms.
domain_identity = dA - s * den == (dA - s * (1 - es)) + s * (eL - es)
ratio_identity = F(dA) / den - s == F((dA - s * (1 - es)) + s * (eL - es)) / den

# Multiplication by 2c is legal because the admitted domain has c>0.
fd1_identity = (
    M * c * (t**2 - s**2) + 2 * H * (t * et - s * es)
    == M * c * (t - s) * (t + s)
    + 2 * H * ((t - s) * et + s * (et - es))
)
fd2_identity = (
    M * c * (q**2 - t**2) + 2 * H * (q * eL - t * et)
    == M * c * (q - t) * (q + t)
    + 2 * H * ((q - t) * eL + t * (eL - et))
)
# In the K=0 branch M05's two inequalities become dA=s. Both min
# branches then give t=min(L,s)=s because s<=L.
flat_lower = s * (1 - es)
flat_upper = s * (1 + es)
flat_distance = flat_lower.subs({es: 0}) == flat_upper.subs({es: 0}) == s
flat_ratio = (F(dA) / den).subs({dA: s, eL: 0}) == s
flat_fd1 = (M * t**2 / 2 + H * t * et / c).subs({t: s, et: 0}) == M * s**2 / 2
flat_fd2 = (F(M) * dA**2 / (2 * den**2) + F(H) * dA * eL / (c * den)).subs(
    {dA: s, eL: 0}
) == F(M) * s**2 / 2

checks = {
    "domain_polynomial_identity": bool(domain_identity),
    "positive_denominator_ratio_identity": bool(ratio_identity),
    "fd1_positive_cone_identity": bool(fd1_identity),
    "fd2_positive_cone_identity": bool(fd2_identity),
    "flat_distance_from_two_sided_m05": bool(flat_distance),
    "flat_ratio": bool(flat_ratio),
    "flat_fd1": bool(flat_fd1),
    "flat_fd2": bool(flat_fd2),
}
print(json.dumps({"status": "PASS" if all(checks.values()) else "FAIL", "checks": checks}, sort_keys=True))
