"""Ancillary SymPy export (card tool_task 'sympy'): finite linear-combination identities used in T4,
over a symbolic weighted inner product on N sample points (weights w_k symbolic).  Not a proof of the
infinite-dimensional statement (Lean T3/T4 is); exact symbolic identities only."""
import sympy as sp, sys
N, n = 4, 3
w = sp.symbols(f"w0:{N}", positive=True)
r = [[sp.Symbol(f"r{j}_{k}") for k in range(N)] for j in range(n)]
z = sp.symbols(f"z0:{N}")
a = sp.symbols(f"a0:{n}")
ip = lambda u, v: sum(w[k] * u[k] * v[k] for k in range(N))
e = [ip(r[j], z) for j in range(n)]                      # e_j = <r_j, z>  (after matching)
R = sp.Matrix(n, n, lambda i, j: ip(r[i], r[j]))         # R_ij = <r_i, r_j>
u = [sum(a[j] * r[j][k] for j in range(n)) for k in range(N)]
id1 = sp.expand(sum(a[j] * e[j] for j in range(n)) - ip(u, z))
id2 = sp.expand((sp.Matrix([a]) * R * sp.Matrix(a))[0, 0] - ip(u, u))
# duplicated kernels: r_1 = r_0 -> R (1,-1) = 0 and e_0 = e_1
sub = {r[1][k]: r[0][k] for k in range(N)}
Rd = R.subs(sub); ed = [x.subs(sub) for x in e]
id3 = sp.simplify(Rd * sp.Matrix([1, -1, 0]))
id4 = sp.simplify(ed[0] - ed[1])
print("sympy", sp.__version__)
print("a.e - <sum a_j r_j, z> =", id1)
print("a^T R a - ||sum a_j r_j||^2 =", id2)
print("dup: R(1,-1,0)^T =", list(id3), " e0-e1 =", id4)
ok = id1 == 0 and id2 == 0 and all(x == 0 for x in id3) and id4 == 0
print("ALL_IDENTITIES_ZERO" if ok else "FAIL")
sys.exit(0 if ok else 1)
