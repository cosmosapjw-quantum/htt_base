"""Sage and actual Singular process on CAS-07/09 finite polynomial identities."""
from sage.all import QQ, PolynomialRing, matrix, identity_matrix
from sage.interfaces.singular import singular

R = PolynomialRing(QQ, names=("known", "undefined", "exceed"))
known, undefined, exceed = R.gens()
assert (known + exceed) - known == exceed
assert (known + undefined) - (known + exceed) == undefined - exceed
print("SAGE_CAS07_INTERVAL_DIFFERENCES=PASS_CONDITIONAL_NONNEGATIVE_INPUTS")

H = matrix(QQ, [[1, 0, 0], [-1, 1, 0], [0, -1, 1]])
assert H.det() == 1
assert H.inverse() * H == identity_matrix(QQ, 3)
print("SAGE_CAS09_DEPTH_INVERSE=PASS")

singular.eval("ring r=0,(known,undefined,exceed),dp;")
singular.eval("poly lower=(known+exceed)-known-exceed;")
singular.eval("poly upper=(known+undefined)-(known+exceed)-(undefined-exceed);")
singular.eval("ideal I=lower,upper;")
assert singular.eval("reduce(lower,I);").splitlines()[-1].strip() == "0"
assert singular.eval("reduce(upper,I);").splitlines()[-1].strip() == "0"
print("SINGULAR_CAS07_POLYNOMIAL_IDENTITIES=PASS")
