"""PR-186 W^2 identity, SymPy exact axis (standalone for the CAS envelope)."""
import sympy as sp
a,b,c,H,B = sp.symbols('a b c H B')
A = sp.Matrix([[0,a,b],[-a,0,c],[-b,-c,0]])
tensor_norm = sum(A[i,j]**2 for i in range(3) for j in range(3))
def eps(i,j,k):
    p={(0,1,2):1,(1,2,0):1,(2,0,1):1,(0,2,1):-1,(2,1,0):-1,(1,0,2):-1}
    return p.get((i,j,k),0)
w = [sp.Rational(1,2)*sum(eps(i,j,k)*A[j,k] for j in range(3) for k in range(3)) for i in range(3)]
vec_norm = sum(wi**2 for wi in w)
id_ok = sp.simplify(tensor_norm - 2*vec_norm) == 0
W2reg = sp.simplify(tensor_norm/(6*H**2))
W2vec = sp.simplify(vec_norm/(3*H**2))
reg_eq_vec = sp.simplify(W2reg - W2vec) == 0
wrong_ratio = sp.simplify((vec_norm/H**2)/W2reg)
W2max = sp.simplify((B*3*H)**2/(6*H**2))
ceil_ok = sp.simplify(W2max - sp.Rational(3,2)*B**2) == 0
print("tensor_norm=%s" % tensor_norm)
print("W2reg=%s" % W2reg)
print("identity_A_eq_2w=%s" % id_ok)
print("reg_eq_vecform=%s" % reg_eq_vec)
print("wrong_over_right=%s" % wrong_ratio)
print("ceiling_eq_three_halves=%s" % ceil_ok)
print("PR186_SYMPY_PASS" if (id_ok and reg_eq_vec and wrong_ratio==3 and ceil_ok) else "PR186_SYMPY_FAIL")
