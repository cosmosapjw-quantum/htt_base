import sys; sys.path.insert(0,'htt'); sys.path.insert(0,'htt/src')
from fractions import Fraction as F
from common.joint_feasible_set import analyze, exact_support
A=[[-1,0],[1,0],[0,-1],[0,1],[1,1]]; b=[0,1,0,1,1]
joint=exact_support([F(1),F(1)],[[F(x) for x in r] for r in A],[F(x) for x in b])
prod_sup = 2
fact=exact_support([F(1),F(1)],[[F(x) for x in r] for r in A[:4]],[F(x) for x in b[:4]])
js=joint['exact_hi']; fs=fact['exact_hi']
print("joint_sup=%s"%js); print("product_sup=%s"%prod_sup); print("strict_1_lt_2=%s"%(js<prod_sup)); print("factorized_joint_sup=%s"%fs)
print("PR189_SYMPY_PASS" if (js==1 and prod_sup==2 and js<prod_sup and fs==2) else "PR189_SYMPY_FAIL")
