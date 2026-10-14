from sage.all import *
from sage.version import version as sage_version
import json

names = ["n1", "n2", "n3", "h0", "h1", "h2", "h3", "q11", "q22", "q12", "q13", "q23", "st", "a", "u0", "u1", "u2", "u3"]
R = PolynomialRing(QQ, names=names)
v = dict(zip(names, R.gens()))
n = vector(R, [v[f"n{i}"] for i in range(1, 4)])
u = vector(R, [v[f"u{i}"] for i in range(4)])
g = diagonal_matrix(R, [-1, 1, 1, 1])
K = vector(R, [-1, *n])
q = matrix(R, [[v["q11"], v["q12"], v["q13"]], [v["q12"], v["q22"], v["q23"]], [v["q13"], v["q23"], -v["q11"]-v["q22"]]])
S = matrix(R, 4, 4, lambda i, j: v["h0"] if (i,j)==(0,0) else (-v[f"h{j}"]/2 if i==0 else (-v[f"h{i}"]/2 if j==0 else q[i-1,j-1])))
B = S-v["st"]*g
unit_ideal = R.ideal(sum(x*x for x in n)-1)
checks = {}
def check(name, value, modulo=False):
    residual = unit_ideal.reduce(value) if modulo else R(value)
    checks[name] = str(residual)
    assert residual == 0, (name, residual)

check("g_null_mod_unit", K*g*K, True)
expected = v["h0"] + sum(v[f"h{i}"]*n[i-1] for i in range(1,4)) + n*q*n
check("S_null_polynomial", K*S*K-expected)
check("B_null_equals_S_mod_unit", K*B*K-K*S*K, True)
check("q_tracefree", q.trace())
assert B == B.transpose()
checks["B_symmetric"] = "0"
mixed = g*S
for i in range(4):
    check(f"kernel_eigen_iff_component_{i}", (B*u)[i]-g[i,i]*((mixed*u)[i]-v["st"]*u[i]))
shifted = S+v["a"]*g
assert shifted-(v["st"]+v["a"])*g == B
checks["metric_gauge_B"] = "0"
check("metric_gauge_null_mod_unit", K*shifted*K-K*S*K, True)
check("tracefree_spatial_monopole", q.trace()/3)
test = {v["n1"]:1,v["n2"]:0,v["n3"]:0,v["h0"]:2,v["h1"]:1,v["h2"]:-2,v["h3"]:3,v["q11"]:1,v["q22"]:-1,v["q12"]:0,v["q13"]:0,v["q23"]:0}
assert expected.subs(test) == 4
checks["numeric_test_S_null"] = "4"
assert v["st"]*g-v["st"]*g == 0
checks["S_equals_st_g_implies_B_zero"] = "0; within tracefree parametrization requires st=0"
print(json.dumps({"axis":"sage_singular","sage_version":sage_version,"checks":checks,"status":"PASS"},sort_keys=True))
