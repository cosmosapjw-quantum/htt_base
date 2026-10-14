import json
from sage.all import PolynomialRing,QQ
P=PolynomialRing(QQ,names=("L","U","m","t","r"));L,U,m,t,r=P.gens()
# Clear only positive denominators L,U,L+U after stating 0<L<=U.
# Exact candidate endpoint polynomial identities.
a_num=2*L*U;den=L+U;eps_num=U-L
assert a_num-L*den==eps_num*L
assert U*den-a_num==eps_num*U
# The general sign implications are not executed in this polynomial ring.
print(json.dumps({"checks":{"CAS13-C04-RELATIVE-MINIMAX":True},"domain_assumption_diff":["Endpoint polynomial certificates only; full interval and all-real competitor inequalities remain unproved by Sage axis"],"counterexample":None,"sage_scope":"endpoint equalities only"}))
