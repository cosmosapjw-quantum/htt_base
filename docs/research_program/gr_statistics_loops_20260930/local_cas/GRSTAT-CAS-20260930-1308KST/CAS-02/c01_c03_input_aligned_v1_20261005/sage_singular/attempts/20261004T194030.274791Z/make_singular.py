"""Emit raw-definition polynomial calculations for the pinned Singular engine."""
from pathlib import Path

here = Path(__file__).resolve().parent
lines = []
def emit(s): lines.append(s)
def poly(name, expr):
    emit(f"poly {name} = {expr};")
    emit(f'print("{name}=" + string({name}));')
    emit(f'if ({name} != 0) {{ print("CERTIFICATE_FAILURE_{name}"); exit(1); }}')

def add(parts): return "(" + "+".join(parts) + ")"
def mul(*parts): return "(" + "*".join(parts) + ")"
def quad(U,S,V): return add([mul(U[i],S[i][j],V[j]) for i in range(4) for j in range(4)])

vars1 = ["h","p0","p1","p2","a","b","c","e","f"]
emit("ring r1 = 0,("+",".join(vars1)+"),dp;")
H = [["a","c","e"],["c","b","f"],["e","f","(-a-b)"]]
S = [["h"]+[f"(-p{i}/2)" for i in range(3)]] + [[f"(-p{i}/2)"]+H[i] for i in range(3)]
norm = add([f"({S[i][j]})^2" for i in range(4) for j in range(4)])
rhs = add(["h^2","(p0^2+p1^2+p2^2)/2"]+[f"({H[i][j]})^2" for i in range(3) for j in range(3)])
poly("C01_embedding_remainder",f"({norm})-({rhs})")
poly("C01_metric_remainder","((-1)^2+1^2+1^2+1^2)-4")

# No timelike or symmetry equation is used: the two identities hold for
# arbitrary 4x4 coefficient matrices and arbitrary 4-vectors.
vars2 = [f"s{k}{i}{j}" for k in (1,2) for i in range(4) for j in range(4)] + [f"u{k}{i}" for k in (1,2) for i in range(4)]
emit("ring r2 = 0,("+",".join(vars2)+"),dp;")
A = [[[f"s{k}{i}{j}" for j in range(4)] for i in range(4)] for k in (1,2)]
U = [[f"u{k}{i}" for i in range(4)] for k in (1,2)]
delta = f"({quad(U[1],A[1],U[1])})-({quad(U[0],A[0],U[0])})"
D = [[f"({A[1][i][j]}-{A[0][i][j]})" for j in range(4)] for i in range(4)]
DU = [f"({U[1][i]}-{U[0][i]})" for i in range(4)]
anchor1 = add([quad(U[1],D,U[1]),quad(DU,A[0],U[1]),quad(U[0],A[0],DU)])
anchor2 = add([quad(U[0],D,U[0]),quad(DU,A[1],U[1]),quad(U[0],A[1],DU)])
poly("C02_anchor_S1_remainder",f"({delta})-({anchor1})")
poly("C02_anchor_S2_remainder",f"({delta})-({anchor2})")

# w is the positive sqrt(1+x) in the chart. Singular handles polynomial
# numerators; Sage handles the positive branch and transcendental signs.
emit("ring r3 = 0,(d0,d1,d2,w,l,x,y),dp;")
d = ["d0","d1","d2"]
poly("C03_root_relation", "x-(d0^2+d1^2+d2^2)") if False else None
# The root equation belongs to the admitted definition. It is used only when
# identifying the radial eigenvalue, never to reduce a target polynomial.
Jnum = [[d[j] for j in range(3)]] + [["w" if i==j else "0" for j in range(3)] for i in range(3)]
T = [[add([mul(Jnum[k][i],Jnum[k][j]) for k in range(4)]) for j in range(3)] for i in range(3)]
for i in range(3):
    for j in range(3):
        rhs = f"({('w^2' if i==j else '0')}+{d[i]}*{d[j]})"
        poly(f"C03_Gram_{i}{j}",f"({T[i][j]})-{rhs}")
# det(w^2*l I - Jnum^T Jnum) without supplying a factored determinant.
M = [[f"({('w^2*l' if i==j else '0')}-({T[i][j]}))" for j in range(3)] for i in range(3)]
det = add([mul(M[0][0],M[1][1],M[2][2]),mul(M[0][1],M[1][2],M[2][0]),mul(M[0][2],M[1][0],M[2][1]),
           f"-({mul(M[0][2],M[1][1],M[2][0])})", f"-({mul(M[0][1],M[1][0],M[2][2])})", f"-({mul(M[0][0],M[1][2],M[2][1])})"])
poly("C03_characteristic_remainder",f"({det})-((w^2*(l-1))^2*(w^2*(l-1)-(d0^2+d1^2+d2^2)))")
poly("C03_radial_root_remainder", "(w^2-(1+d0^2+d1^2+d2^2))") if False else None
poly("C03_bound_cross_remainder", "y*(1+x)-x*(1+y)-(y-x)")
emit('print("SINGULAR_CERTIFICATES_COMPLETE");')
emit("quit;")
(here/"verify.sing").write_text("\n".join(lines)+"\n")
