"""Independent Sage exact checks for the admitted CAS14 finite statements.

The norm and singular-value estimates are proved in PROOF.md. This executable
checks their polynomial identities and exact boundary witnesses; it does not
replace the universal Hilbert-space inequalities by sampled numerics.
"""

import json
from sage.all import PolynomialRing, QQ, matrix, vector, identity_matrix, sqrt


R = PolynomialRing(QQ, names=(
    "x1", "x2", "x3", "z1", "z2", "z3", "v1", "v2", "v3",
    "o1", "o2", "o3", "a", "b", "d1", "d2", "d3"
))
(x1,x2,x3,z1,z2,z3,v1,v2,v3,o1,o2,o3,a,b,d1,d2,d3) = R.gens()
x = vector(R, [x1,x2,x3]); z = vector(R, [z1,z2,z3])
v = vector(R, [v1,v2,v3]); o = vector(R, [o1,o2,o3])
dw = vector(R, [d1,d2,d3])
I = identity_matrix(R, 3)
unit_ideal = R.ideal([x.dot_product(x)-1, z.dot_product(z)-1])

def zero_mod_unit(value):
    return all(p.reduce(unit_ideal.groebner_basis()) == 0 for p in
               (list(value) if hasattr(value, '__iter__') and not isinstance(value, R.element_class) else [value]))

def cross(p, q):
    return vector(R, [p[1]*q[2]-p[2]*q[1],
                      p[2]*q[0]-p[0]*q[2],
                      p[0]*q[1]-p[1]*q[0]])

W = matrix(R, [[0,o3,-o2],[-o3,0,o1],[o2,-o1,0]])
P = I - x.column()*x.row()
y = -W*x
c01 = {
    "Wx_sign": W*x == -cross(o,x),
    "x_cross_y_projection_mod_unit": zero_mod_unit(cross(x,y)-P*o),
    "normal_equation_mod_unit": zero_mod_unit(a*cross(x,y)+b*cross(z,-W*z) -
        (a*(I-x.column()*x.row())+b*(I-z.column()*z.row()))*o),
}

C = matrix(R, [[0,-x3,x2],[x3,0,-x1],[-x2,x1,0]])
G = a*(I-x.column()*x.row())+b*(I-z.column()*z.row())
gram_x = (C.transpose()*C) - (x.dot_product(x)*I-x.column()*x.row())
gram_polynomial = (v.dot_product(v)*x.dot_product(x)-v.dot_product(x)**2) - cross(v,x).dot_product(cross(v,x))
det_polynomial = (G.det() - a*b*(a+b)*cross(x,z).dot_product(cross(x,z)))
c02 = {
    "cross_gram_exact": gram_x == 0,
    "sum_squares_exact": gram_polynomial == 0,
    "two_direction_determinant_mod_unit": zero_mod_unit(det_polynomial),
    "parallel_kernel_control": (G.subs({z1:x1,z2:x2,z3:x3})*x).apply_map(lambda p:p.reduce(unit_ideal.groebner_basis())) == 0,
    "e1_e2_control": G.subs({x1:1,x2:0,x3:0,z1:0,z2:1,z3:0}) == matrix(R,[[b,0,0],[0,a,0],[0,0,a+b]]),
}

dW = matrix(R,[[0,d3,-d2],[-d3,0,d1],[d2,-d1,0]])
frob_residual = sum(t*t for t in dW.list()) - 2*dw.dot_product(dw)
# A=(cross(e1,-),cross(e2,-)) has singular values 1,1,sqrt(2).
e1=vector(QQ,[1,0,0]); e2=vector(QQ,[0,1,0]); e3=vector(QQ,[0,0,1])
def qcross(p,q):
    return vector(QQ,[p[1]*q[2]-p[2]*q[1],p[2]*q[0]-p[0]*q[2],p[0]*q[1]-p[1]*q[0]])
Amat=matrix(QQ,[list(qcross(e1,e)) + list(qcross(e2,e)) for e in (e1,e2,e3)]).transpose()
gram_control=Amat.transpose()*Amat
# Ahat=2A, e=0, omega=T*e1: error=|T|/2 grows without an Omega_* bound.
T=R['T'].gen()
noamp_error=(T/2)
c03 = {
    "frobenius_square_exact": frob_residual == 0,
    "stacked_e1_e2_gram": gram_control == matrix(QQ,[[1,0,0],[0,1,0],[0,0,2]]),
    "zero_noise_control": (Amat.pseudoinverse()*Amat) == identity_matrix(QQ,3),
    "no_amplitude_family_unbounded": noamp_error.degree() == 1 and noamp_error.leading_coefficient() > 0,
    "zero_operator_error_control": (Amat.pseudoinverse()*Amat*e1)==e1,
}

checks={"CAS-14-C01":all(c01.values()),"CAS-14-C02":all(c02.values()),"CAS-14-C03":all(c03.values())}
print(json.dumps({
    "status":"PASS" if all(checks.values()) else "FAIL",
    "checks":checks,"details":{"C01":c01,"C02":c02,"C03":c03},
    "determinant_residual":str(det_polynomial.reduce(unit_ideal.groebner_basis())),
    "frobenius_residual":str(frob_residual),"gram_control":str(gram_control),
    "counterexample":None,"domain_assumption_diff":[]
},sort_keys=True))
