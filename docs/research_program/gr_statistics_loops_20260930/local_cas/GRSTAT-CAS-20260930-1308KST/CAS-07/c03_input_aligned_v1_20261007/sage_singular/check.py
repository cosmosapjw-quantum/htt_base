"""Blind Sage axis: exact conditional FD1/FD2/FD3 ordered-real algebra.

Run with ``sage -python check.py``.  No target inequality is assumed.  The
positive-cone variables below encode supplied premise gaps, and all rational
denominators are strictly positive under the frozen contract.
"""

import json
from sage.all import PolynomialRing, QQ


R = PolynomialRing(QQ, names=("s", "p", "q", "eta", "u", "v", "c", "M2", "h"))
s, p, q, eta, u, v, c, M2, h = R.gens()
I = R.ideal(eta + u + v - 1, p + q - 2 * s * eta)
E = u + v                    # 1-eta, strictly positive
D = v                        # 1-etaL, strictly positive
etaL = eta + u
dA = s * E + p               # p = dA-s*(1-eta) >= 0


def congruent(lhs, rhs):
    return I.reduce(R(lhs - rhs)) == 0


def cone(poly):
    """Every monomial has a nonnegative rational coefficient.

    The primitive variables s,p,q,eta,u,v,c,M2,h are nonnegative; s,v,c
    are strictly positive.  This is an exact ordered-real certificate.
    """
    return all(a >= 0 for a in R(poly).dict().values())


checks = {}
details = {}

# From p,q >= 0 and p+q=2*s*eta, both signed displacement bounds follow:
# s*eta-(dA-s)=q and s*eta+(dA-s)=p.  Then |dA-s|<=s*eta.
# With r=Z-Z0-H0*s/c, |r|<=M2*s^2/2, the real triangle inequality gives
# |r-H0*(dA-s)/c|<=M2*s^2/2+h*s*eta/c, where h=|H0|.
fd1_gaps = [congruent(s * eta - (dA - s), q),
            congruent(s * eta + (dA - s), p),
            cone(p), cone(q), cone(M2), cone(h), cone(c)]
checks["CAS-07-C03-FD1"] = all(fd1_gaps)
details["FD1"] = {"screen_gap_identities": fd1_gaps,
                  "ordered_real_rule": "absolute-value triangle inequality; c>0"}

# FD2, M2 part: after multiplication by 2*D^2>0, the RHS difference is
# M2*(dA^2-s^2*D^2).  It is a nonnegative-coefficient polynomial in the
# primitive nonnegative variables.  The H0 part has difference
# h*(dA*etaL-s*eta*D)/(c*D), with c*D>0.
fd2_m_poly = dA**2 - s**2 * D**2
fd2_h_poly = dA * etaL - s * eta * D
fd2_m_identity = (dA - s * E) * (dA + s * E) + s**2 * u * (E + D)
fd2_h_identity = (dA - s * E) * etaL + s * u
fd2_gaps = [congruent(fd2_m_poly, fd2_m_identity),
            congruent(fd2_h_poly, fd2_h_identity),
            cone(fd2_m_identity), cone(fd2_h_identity),
            cone(D), cone(E), cone(dA), cone(c), cone(M2), cone(h)]
checks["CAS-07-C03-FD2"] = checks["CAS-07-C03-FD1"] and all(fd2_gaps)
details["FD2"] = {"denominator_cleared_gap_identities": fd2_gaps,
                  "positive_denominators": ["2*v^2", "c*v"]}

# FD3 is (c/dA) times FD1.  The two RHS gaps are exactly
# c*M2*s*p/(2*E*dA) and h*eta*p/(E*dA), respectively.  These are
# nonnegative because E,dA>0.  The LHS equality uses c/dA>0.
fd3_m_num = s * dA - s**2 * E
fd3_h_num = eta * dA - s * eta * E
fd3_gaps = [congruent(fd3_m_num, s * p),
            congruent(fd3_h_num, eta * p),
            cone(s * p), cone(eta * p), cone(E), cone(dA), cone(c),
            cone(M2), cone(h)]
checks["CAS-07-C03-FD3"] = checks["CAS-07-C03-FD1"] and all(fd3_gaps)
details["FD3"] = {"denominator_cleared_gap_identities": fd3_gaps,
                  "positive_denominators": ["2*(u+v)*dA", "(u+v)*dA"],
                  "lhs_rule": "|c*(Z-Z0)/dA-H0|=(c/dA)*|Z-Z0-H0*dA/c|"}

print(json.dumps({"checks": checks, "details": details,
                  "assumption_encoding": {
                      "p": "dA-s*(1-eta)>=0", "q": "s*(1+eta)-dA>=0",
                      "u": "etaL-eta>=0", "v": "1-etaL>0",
                      "relation": ["eta+u+v=1", "p+q=2*s*eta"],
                      "strictly_positive": ["s", "v", "c", "u+v", "dA"]}},
                 sort_keys=True))
