"""Independent exact Sage check of the frozen PORT-CAS-01 finite algebra."""

import json
from sage.all import AA, QQ, PolynomialRing, diagonal_matrix, identity_matrix, matrix, vector

R = PolynomialRing(QQ, names=("b1", "b2", "b3", "g", "h"))
b1, b2, b3, g, h = R.gens()
b = (b1, b2, b3)
s = sum(x * x for x in b)
J = R.ideal(g * g * (1 - s) - 1, h * (g + 1) - g * g)
eta = diagonal_matrix(R, [-1, 1, 1, 1])


def boost(sign):
    def entry(i, j):
        if i == j == 0:
            return g
        if i == 0:
            return sign * g * b[j - 1]
        if j == 0:
            return sign * g * b[i - 1]
        return (1 if i == j else 0) + h * b[i - 1] * b[j - 1]
    return matrix(R, 4, 4, entry)


L = boost(1)
Lm = boost(-1)
metric_residual = L.transpose() * eta * L - eta
inverse_residual = L * Lm - identity_matrix(R, 4)
u = L * vector(R, (1, 0, 0, 0))
shell_residual = (u * eta * u) + 1
assert tuple(u) == (g, g * b1, g * b2, g * b3)
residuals = metric_residual.list() + inverse_residual.list() + [shell_residual]
remainders = [J.reduce(p) for p in residuals]
assert len(remainders) == 33
assert all(p == 0 for p in remainders), [str(p) for p in remainders if p]

# The ideal reduction proves the rational polynomial identities. The real
# inequalities are separate: s<1 implies 1-s>0, g=1/sqrt(1-s)>0, g+1>0.
# Thus h is defined and the positive branch is selected.
for beta in ((QQ(0), QQ(0), QQ(0)), (QQ(1)/5, -QQ(1)/10, QQ(1)/20)):
    sval = sum(x*x for x in beta)
    assert sval < 1
    gamma = 1 / (AA(1) - AA(sval)).sqrt()
    assert gamma > 0
    assert gamma*gamma*(1-AA(sval)) == 1
    hv = gamma*gamma/(gamma+1)
    vals = {b1: beta[0], b2: beta[1], b3: beta[2], g: gamma, h: hv}
    assert all(AA(p(*[vals[v] for v in R.gens()])) == 0 for p in residuals)

z0, z1, z2, z3 = QQ(5)/4, QQ(3)/4, QQ(0), QQ(0)
assert z0 >= 1 and z0*z0-z1*z1-z2*z2-z3*z3 == 1
beta = (z1/z0, z2/z0, z3/z0)
sbeta = sum(x*x for x in beta)
assert sbeta == 1 - 1/(z0*z0) and sbeta < 1
assert 1/(AA(1)-AA(sbeta)).sqrt() == AA(z0)
assert tuple(AA(z0)*AA(x) for x in beta) == tuple(AA(x) for x in (z1,z2,z3))

# General converse over the fraction field, modulo precisely the mass-shell
# premise. zeta0>=1 separately licenses division and fixes sqrt(zeta0^2)=zeta0.
Z = PolynomialRing(QQ, names=("z0", "z1", "z2", "z3"))
zz0, zz1, zz2, zz3 = Z.gens()
F = Z.fraction_field()
shell = zz0**2 - zz1**2 - zz2**2 - zz3**2 - 1
IZ = Z.ideal(shell)
sz = F(zz1**2 + zz2**2 + zz3**2) / F(zz0**2)
branch_residual = F(zz0**2) * (1 - sz) - 1
assert IZ.reduce(branch_residual.numerator()) == 0
assert all(F(zz0) * (F(zi)/F(zz0)) == F(zi) for zi in (zz1, zz2, zz3))
# On the real future domain, 1-sz=1/zeta0^2>0, hence sz<1 and the
# positive gamma is 1/sqrt(1-sz)=sqrt(zeta0^2)=zeta0.
print(json.dumps({"sage_exact_remainder_count": len(remainders), "all_zero": True,
                  "branch_controls": ["s<1", "g>0", "g+1>0", "zeta0>=1"],
                  "converse": "symbolic fraction-field identity modulo mass-shell premise; future branch"},
                 sort_keys=True))
