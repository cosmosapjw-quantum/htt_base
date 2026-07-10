import sympy as sp
# Ground-truth Levi-Civita for orthonormal invariant frame via Koszul.
# 2<nabla_{e_b} e_c, e_a> = <[e_b,e_c],e_a> - <[e_b,e_a],e_c> - <[e_c,e_a],e_b>
# with <[e_x,e_y],e_z> = C^z_{xy} = Cl(z,x,y).
a = sp.Symbol('a', real=True)
v = sp.symbols('v1 v2 v3', real=True)
C = [[[sp.Integer(0)]*3 for _ in range(3)] for _ in range(3)]
C[1][0][1]=a; C[1][1][0]=-a       # C^2_12=a
C[2][0][2]=a; C[2][2][0]=-a       # C^3_13=a
def Cl(z,x,y): return C[z][x][y]   # C^z_{xy}
eps=sp.LeviCivita

# Gamma^a_{cb} := <nabla_{e_b} e_c, e_a>  (b = derivative index)
def Gam_up(a_,c,b):
    return sp.Rational(1,2)*(Cl(a_,b,c) - Cl(c,b,a_) - Cl(b,c,a_))

# torsion-free check: nabla_{e_b} e_c - nabla_{e_c} e_b = [e_b,e_c]
# => Gam_up(d,c,b) - Gam_up(d,b,c) = C^d_{bc}
tf=all(sp.simplify(Gam_up(d,c,b)-Gam_up(d,b,c)-Cl(d,b,c))==0 for d in range(3) for b in range(3) for c in range(3))
# metric-compat: Gam_up(a,c,b) antisym in (a,c)
mc=all(sp.simplify(Gam_up(x,y,b)+Gam_up(y,x,b))==0 for x in range(3) for y in range(3) for b in range(3))
print("Koszul torsion-free:", tf, " metric-compat:", mc)

# 1-form covariant deriv of invariant field: (nabla_b v)_c = -Gamma^d_{cb} v_d
def nabla(b,c): return -sum(Gam_up(d,c,b)*v[d] for d in range(3))
curl=[sp.simplify(sum(eps(i,j,k)*nabla(j,k) for j in range(3) for k in range(3))) for i in range(3)]
print("Ground-truth Levi-Civita curl:", curl)
print("curl_sq:", sp.simplify(sum(c**2 for c in curl)))
