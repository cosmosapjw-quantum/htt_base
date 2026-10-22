# Exact LP (PPL backend over QQ) for the frozen polytope fibre instance; primal and dual values.
import json, sys
res = {}
for sense in ("max", "min"):
    p = MixedIntegerLinearProgram(maximization=(sense == "max"), solver="PPL")
    x = p.new_variable(real=True, nonnegative=False)
    p.add_constraint(x[0] + x[1] <= 1)
    p.add_constraint(x[0] >= 0); p.add_constraint(x[1] >= 0)
    p.add_constraint(x[0] <= 1); p.add_constraint(x[1] <= 1)
    p.add_constraint(x[0] - x[1] == 0)
    p.set_objective(x[0] + 2*x[1])
    val = p.solve()
    res[sense] = {"value": str(QQ(val)), "argopt": [str(QQ(v)) for v in p.get_values([x[0], x[1]])]}
# dual for max: minimize lam*b s.t. A^T lam = c, lam >= 0 (rows: x0+x1<=1, -x0<=0, -x1<=0, x0<=1, x1<=1, x0-x1<=0, -x0+x1<=0)
A = matrix(QQ, [[1,1],[-1,0],[0,-1],[1,0],[0,1],[1,-1],[-1,1]]); b = vector(QQ, [1,0,0,1,1,0,0]); c = vector(QQ, [1,2])
d = MixedIntegerLinearProgram(maximization=False, solver="PPL")
l = d.new_variable(real=True, nonnegative=True)
for j in range(2):
    d.add_constraint(sum(A[i,j]*l[i] for i in range(7)) == c[j])
d.set_objective(sum(b[i]*l[i] for i in range(7)))
dv = d.solve()
res["dual_max"] = {"value": str(QQ(dv)), "lambda": [str(QQ(d.get_values(l[i]))) for i in range(7)]}
open(sys.argv[1], "w").write(json.dumps(res, indent=1) + "\n"); print(res)
