import sympy as s
v = s.symbols('v', positive=True)
streams = [(s.Integer(1), s.Matrix([v,0,0])), (s.Integer(1), s.Matrix([-v,0,0]))]
F = sum((w*x for w,x in streams), s.zeros(3,1))
K = sum((w*(x*x.T) for w,x in streams), s.zeros(3,3))
tr = s.trace(K)
Pi = s.simplify(K - tr/3*s.eye(3))
iso = tr/3*s.eye(3); iso_aniso = s.simplify(iso - s.trace(iso)/3*s.eye(3))
ok = (F == s.zeros(3,1)) and (s.simplify(tr) != 0) and (Pi != s.zeros(3,3)) and (iso_aniso == s.zeros(3,3))
# integer normalization at v=1
Pi3 = s.simplify(3*Pi.subs(v,1))
print("first_moment=", list(F))
print("trace_K=", s.simplify(tr))
print("aniso_3Pi_diag=", [Pi3[i,i] for i in range(3)])
print("PR223_SYMPY_PASS" if ok and Pi3[0,0]==4 and Pi3[1,1]==-2 and s.trace(Pi3)==0 else "PR223_SYMPY_FAIL")
