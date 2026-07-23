# PR-186 W^2 convention identity, SageMath + Singular
R.<a,b,c,H,B> = QQ[]
A = matrix(R, [[0,a,b],[-a,0,c],[-b,-c,0]])
tensor_norm = sum((A[i,j])^2 for i in range(3) for j in range(3))  # A_ij A_ij
# dual vector w_i = (1/2) eps_ijk A_jk ; eps_123=1 etc.
def eps(i,j,k):
    p={(0,1,2):1,(1,2,0):1,(2,0,1):1,(0,2,1):-1,(2,1,0):-1,(1,0,2):-1}
    return p.get((i,j,k),0)
w = [ (1/2)*sum(eps(i,j,k)*A[j,k] for j in range(3) for k in range(3)) for i in range(3)]
vec_norm = sum(wi^2 for wi in w)
id_ok = (tensor_norm - 2*vec_norm) == 0
# W^2 registered vs vector form (as rational functions)
FR = FractionField(R)
W2reg = FR(tensor_norm)/(6*H^2)
W2vec = FR(vec_norm)/(3*H^2)
reg_eq_vec = (W2reg - W2vec) == 0
wrong_ratio = (FR(vec_norm)/H^2) / W2reg
W2max = FR((B*3*H)^2)/(6*H^2)
ceil_ok = (W2max - (3/2)*B^2) == 0
# Singular cross-check: factor the identity polynomial (must be zero)
sing_zero = singular.eval('ring r=0,(a,b,c),dp; poly p = %s; p;' % (tensor_norm - 2*vec_norm))
print("singular_version=%s" % singular.eval('system("version");'))
print("tensor_norm=%s" % tensor_norm)
print("vec_norm=%s" % vec_norm)
print("identity_A_eq_2w=%s" % id_ok)
print("W2reg=%s" % W2reg)
print("reg_eq_vecform=%s" % reg_eq_vec)
print("wrong_over_right=%s" % wrong_ratio)
print("ceiling_eq_three_halves=%s" % ceil_ok)
print("singular_identity_poly=%s" % sing_zero.strip())
ok = id_ok and reg_eq_vec and wrong_ratio == 3 and ceil_ok and sing_zero.strip()=="0"
print("PR186_SAGE_PASS" if ok else "PR186_SAGE_FAIL")
