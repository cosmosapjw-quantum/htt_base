import json,sympy as s
L,U,m,t=s.symbols("L U m t",real=True)
a=2*L*U/(L+U);r=(U-L)/(L+U)
# Symbolic certificates of endpoint identities and bounds. The universal implication is reasoned from positive multipliers; SymPy does not quantify it here.
cert={"lower_candidate":s.factor(a-(1-r)*U),"upper_candidate":s.factor(a-(1+r)*L),"endpoint_L":s.factor((a-L)/L-r),"endpoint_U":s.factor((U-a)/U-r),"lower_m":s.factor((1+r)*(m-L)),"upper_m":s.factor((1-r)*(U-m))}
assert all(cert[k]==0 for k in ("lower_candidate","upper_candidate","endpoint_L","endpoint_U"))
print(json.dumps({"checks":{"CAS13-C04-RELATIVE-MINIMAX":True},"domain_assumption_diff":["Symbolic identities and sign certificate ingredients checked; universal implication not discharged by this SymPy program"],"counterexample":None,"computed":{k:str(v) for k,v in cert.items()},"sympy_version":s.__version__}))
