import sympy as sp

# ---- Independent structure-constant-only curl derivation ----
# Bianchi V frame: [e1,e2]=a e2, [e1,e3]=a e3, [e2,e3]=0
# C^d_{bc} (1-based -> 0-based). Antisym in (b,c).
a = sp.Symbol('a', real=True)
v = sp.symbols('v1 v2 v3', real=True)
# structure constants C[d][b][c]
C = [[[sp.Integer(0)]*3 for _ in range(3)] for _ in range(3)]
# C^2_{12}=a -> d=1(idx),b=0,c=1
C[1][0][1]=a; C[1][1][0]=-a
# C^3_{13}=a -> d=2,b=0,c=2
C[2][0][2]=a; C[2][2][0]=-a
eps = sp.LeviCivita

# Pure Lie-algebra formula: (curl v)^i = -1/2 eps^{i b c} C^d_{bc} v_d
curl_lie = []
for i in range(3):
    s = 0
    for b in range(3):
        for c in range(3):
            for d in range(3):
                s += eps(i,b,c)*C[d][b][c]*v[d]
    curl_lie.append(sp.simplify(sp.Rational(-1,2)*s))
print("Lie-algebra curl (curl^a = -1/2 eps^abc C^d_bc v_d):", curl_lie)

# ---- Code's connection formula ----
def Cl(i,j,k): return C[i][j][k]
def Gamma(i,j,k): return sp.Rational(1,2)*(Cl(i,j,k)+Cl(k,i,j)-Cl(j,k,i))
def nabla(b,c): return -sum(Gamma(d,c,b)*v[d] for d in range(3))
curl_code = [sp.simplify(sum(eps(i,j,k)*nabla(j,k) for j in range(3) for k in range(3))) for i in range(3)]
print("Code curl:", curl_code)

# ---- Check code's connection is torsion-free: Gamma^d_cb - Gamma^d_bc = C^d_bc ----
tf_ok = True
for d in range(3):
    for b in range(3):
        for c in range(3):
            lhs = Gamma(d,c,b)-Gamma(d,b,c)
            rhs = C[d][b][c]
            if sp.simplify(lhs-rhs)!=0:
                tf_ok=False
                print("TORSION FAIL", d,b,c, lhs, rhs)
print("code connection torsion-free (Gamma^d_cb - Gamma^d_bc == C^d_bc):", tf_ok)

# ---- Check metric compatibility: Gamma_{dcb} antisym in first two (d,c) ----
mc_ok = True
for d in range(3):
    for c in range(3):
        for b in range(3):
            if sp.simplify(Gamma(d,c,b)+Gamma(c,d,b))!=0:
                mc_ok=False
print("code connection metric-compatible (Gamma_{dcb}=-Gamma_{cdb}):", mc_ok)

# compare code vs lie
print("code == lie ?", [sp.simplify(curl_code[i]-curl_lie[i])==0 for i in range(3)])
print("code == -lie ?", [sp.simplify(curl_code[i]+curl_lie[i])==0 for i in range(3)])
