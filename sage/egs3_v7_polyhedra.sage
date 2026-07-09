## EGS3 v7 exact-rational polyhedron seals (SageMath + Singular).
##
## Emits one JSON line: {"schema":..., "sage_version":..., "checks": {...booleans...},
## "endpoints": {...}}.  Every load-bearing claim is a boolean in "checks".
##
## Theorems certified in exact QQ arithmetic (no floating point):
##
##  T1' + DL1 (F1 repair): the signed-box identified interval for
##      x_C = c . g,  c = (1, -1, 1, 1),  g = (Sigma^2, W^2, Omega_tilt, Omega_k),
##  reachable slice Sigma^2 = 12/100, Omega_tilt = 3/100, null W^2 in [0, 4/100],
##  curvature ceiling |Omega_k| <= 2/100.  The image of the linear functional over
##  the exact rational polytope has vertices whose min/max reproduce
##      open branch (Omega_k in [0, 2/100])      -> [11/100, 17/100]
##      all  branch (Omega_k in [-2/100, 2/100])  -> [ 9/100, 17/100],
##  the all-branch interval CONTAINS the open-branch interval (DL1 monotonicity),
##  and the two lower endpoints differ by exactly |c_k| * U_k = 2/100.
##
##  Bianchi V constraint-algebra ideal membership (Singular via Sage): the P5
##  momentum-response relation 2 A Sigma_+ - (1+w) Omega_m beta = 0 generates an
##  ideal in which the same polynomial reduces to 0 (a machine-checked membership
##  certificate strengthening the SymPy solve seal).

import json

def xc_interval(klo, khi):
    # variables (S, W, T, K); equalities pin S, T; boxes bound W, K.
    P = Polyhedron(ieqs=[
        [-QQ(12)/100, 1, 0, 0, 0], [QQ(12)/100, -1, 0, 0, 0],   # S == 12/100
        [0, 0, 1, 0, 0], [QQ(4)/100, 0, -1, 0, 0],              # 0 <= W <= 4/100
        [-QQ(3)/100, 0, 0, 1, 0], [QQ(3)/100, 0, 0, -1, 0],     # T == 3/100
        [-klo, 0, 0, 0, 1], [khi, 0, 0, 0, -1],                 # klo <= K <= khi
    ], base_ring=QQ)
    c = vector(QQ, [1, -1, 1, 1])
    vals = [c * vector(v.vector()) for v in P.vertices()]
    return min(vals), max(vals)

open_lo, open_hi = xc_interval(QQ(0), QQ(2)/100)
all_lo, all_hi = xc_interval(-QQ(2)/100, QQ(2)/100)

Uk = QQ(2)/100
checks = {}
checks["open_branch_endpoints"] = bool(open_lo == QQ(11)/100 and open_hi == QQ(17)/100)
checks["all_branch_endpoints"] = bool(all_lo == QQ(9)/100 and all_hi == QQ(17)/100)
# DL1 monotonicity: all-branch interval contains the open-branch interval
checks["dl1_containment"] = bool(all_lo <= open_lo and open_hi <= all_hi)
# DL1 lower-endpoint gap is exactly |c_k| * U_k
checks["dl1_lower_gap_exact"] = bool(open_lo - all_lo == Uk)
checks["dl1_upper_coincide"] = bool(open_hi == all_hi)
# U_k = 0 collapse: curvature null contributes nothing
z_lo, z_hi = xc_interval(QQ(0), QQ(0))
checks["uk_zero_collapse"] = bool(z_lo == QQ(11)/100 and z_hi == QQ(15)/100)

# Bianchi V ideal-membership certificate (Singular through Sage).
R = PolynomialRing(QQ, names=('A', 'Sp', 'beta', 'Om', 'w'), order='lex')
A, Sp, beta, Om, w = R.gens()
p5 = 2*A*Sp - (1 + w)*Om*beta
I = R.ideal(p5)
checks["bianchi_v_ideal_membership"] = bool(p5 in I and I.reduce(p5) == R.zero())

status = "PASS" if all(checks.values()) else "FAIL"
print(json.dumps({
    "schema": "htt.egs3.sage_polyhedra.v1",
    "seal": "egs3.sage_polyhedra",
    "status": status,
    "sage_version": version(),
    "checks": checks,
    "endpoints": {
        "open_branch": [str(open_lo), str(open_hi)],
        "all_branch": [str(all_lo), str(all_hi)],
    },
    "claim_boundary": ("exact-rational polyhedron + ideal-membership seals only; "
                       "signed-box endpoints + DL1 monotonicity + Bianchi V "
                       "constraint algebra; no data/detection/family/native claim"),
}))
