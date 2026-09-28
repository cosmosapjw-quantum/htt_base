# SageMath/Singular symbolic, unclassified three-dimensional Lie algebra.
# Contract: ../CLAIM_CONTRACT.json (same input hash as other axes).
R = PolynomialRing(QQ, [f"c{i}{j}{k}" for i,j in [(0,1),(0,2),(1,2)] for k in range(3)])
v = R.gens()
def C(i,j,k):
    if i == j: return R.zero()
    pair = tuple(sorted((i,j)))
    idx = [(0,1),(0,2),(1,2)].index(pair)*3+k
    return v[idx] if i < j else -v[idx]
J = [sum(C(0,1,m)*C(m,2,k)+C(1,2,m)*C(m,0,k)+C(2,0,m)*C(m,1,k) for m in range(3)) for k in range(3)]
I = R.ideal(J)
GB = I.groebner_basis(algorithm="singular:std")
print("SAGE_VERSION", version())
print("STRUCTURE_VARIABLES", R.variable_names())
print("JACOBI", [str(j) for j in J])
print("SINGULAR_GROEBNER_SIZE", len(GB))
print("ZERO_STRUCTURE_REAL_FEASIBLE", all(j.subs({x:0 for x in v})==0 for j in J))

# A rational semialgebraic image example, not an asserted physical solution:
# q=(u,v), u^2+v^2<=1, denominator d=1+v^2>0,
# image coordinate y=u/d. Coupling retains u,v and the same d.
# Elimination is algebraic; the real inequalities are separately necessary.
S = PolynomialRing(QQ, names=("u","w","d","y","h"))
u,w,d,y,h = S.gens()
eq = S.ideal([d-(1+w*w), d*y-u, h*d-1])
elim = eq.elimination_ideal([u,w,d,h])
print("RATIONAL_DENOMINATOR", d, "= 1+w^2 > 0 over real w")
print("ELIMINATION_IDEAL_Y", [str(z) for z in elim.gens()])
print("REAL_IMAGE_BOUND", "-1 <= y <= 1 follows from |u|<=1 and d>=1")
print("REAL_FEASIBILITY_NOT_FROM_IDEAL", True)
print("SINGULAR_STRATUM_EXAMPLE", "for y=u/w, w=0 is excluded; clearing w*y-u=0 alone adds (u,w)=(0,0) with arbitrary y")
P = PolynomialRing(QQ, names=("g11","g12","g13","g22","g23","g33","N","be1","be2","be3"))
g11,g12,g13,g22,g23,g33,N,be1,be2,be3 = P.gens()
g = matrix(P, [[g11,g12,g13],[g12,g22,g23],[g13,g23,g33]])
be = vector(P,[be1,be2,be3])
beta2 = be.dot_product(g*be)
print("METRIC_POSITIVITY", "g11>0;", str(g11*g22-g12*g12)+">0;", str(g.det())+">0")
print("LAPSE_AND_TILT", "N>0;", str(1-beta2)+">0")
print("REQUIRED_JETS", "g_ij(t), N(t), shift(t), beta^i(t), first velocity jets; curvature/stress require higher metric jets")
print("LIE_ALGEBRA_ALONE_NO_MAGNITUDE_BOUND", True)
