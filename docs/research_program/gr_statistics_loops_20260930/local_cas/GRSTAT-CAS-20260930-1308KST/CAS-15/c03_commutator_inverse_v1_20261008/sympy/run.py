#!/usr/bin/python3
"""Independent exact SymPy certificate for frozen CAS-15-C03.

Mathematical argument accompanying the executable identities:

For any real symmetric M, choose an orthogonal eigenbasis and write
D=diag(m1,m2,m3). Orthogonal conjugation preserves so(3), Frobenius norms,
operator norms and least-squares objectives. For skew X, [D,X] is symmetric,
has zero diagonal and off-diagonal entries (mi-mj) Xij. Its three columns
are orthogonal and have squared lengths 2(mi-mj)^2. Thus, if delta>0,
the map has rank three, kernel zero, inverse Xij=Rij/(mi-mj) on its image,
and ||[M,X]||F >= delta ||X||F. An exact R=[M,W] has zero diagonal.

For symmetric Mhat with deltahat>0, let P be orthogonal Frobenius projection
onto the image of [Mhat,-]. In its orthonormal eigenbasis P takes the
symmetric off-diagonal part. The executable Pythagorean identity proves the
unique least-squares minimizer What = T_hat^{-1} P Rhat even when Rhat is an
arbitrary real matrix. Consequently,
  T_hat(What-W) = P(Rhat-T_hat W)
                  = P((Rhat-R)-[Mhat-M,W]).
Projection is contractive. For the declared positive Euclidean norms,
||[DeltaM,W]||F <= ||DeltaM W||F + ||W DeltaM||F
                <= 2 ||DeltaM||op ||W||F.
The exact gap estimate therefore gives
||What-W||F <= (epsilon_R+2 epsilon_M Wstar)/deltahat.
No division is made when deltahat=0.

For ordered eigenvalues, symmetric ||DeltaM||op<=epsilon_M means
-epsilon_M I <= DeltaM <= epsilon_M I. Courant-Fischer min-max monotonicity
then gives |mhat_i-m_i|<=epsilon_M for each i. For i<j,
mhat_j-mhat_i >= (m_j-m_i)-2 epsilon_M; taking minima gives
deltahat >= delta-2 epsilon_M. This remains true when the lower bound is
nonpositive; positivity of deltahat is separately required for inversion.

All inequalities here are universal analytic norm/min-max consequences; the
SymPy equalities below certify their finite algebraic premises. Numerical
examples are controls only and do not substitute for the universal argument.
"""

import json
import sys

import sympy as sp


OBLIGATION = "CAS-15-C03"


def eq_zero(expr):
    if isinstance(expr, sp.MatrixBase):
        return all(sp.cancel(sp.expand(v)) == 0 for v in expr)
    return sp.cancel(sp.expand(expr)) == 0


def norm_squared(a):
    return sp.trace(a.T * a)


def commutator(a, b):
    return a * b - b * a


def projection(a):
    symmetric = (a + a.T) / 2
    return symmetric - sp.diag(*[symmetric[i, i] for i in range(3)])


def main():
    m = sp.symbols("m1 m2 m3", real=True)
    x = sp.symbols("x12 x13 x23", real=True)
    a = sp.symbols("a11 a12 a13 a21 a22 a23 a31 a32 a33", real=True)
    d = sp.diag(*m)
    xmat = sp.Matrix([[0, x[0], x[1]], [-x[0], 0, x[2]], [-x[1], -x[2], 0]])
    amat = sp.Matrix(3, 3, a)
    t = commutator(d, xmat)
    gaps = [m[0] - m[1], m[0] - m[2], m[1] - m[2]]

    checks = {}
    details = {}
    checks["map_symmetric_zero_diagonal"] = eq_zero(t - t.T) and all(t[i, i] == 0 for i in range(3))
    checks["map_offdiagonal"] = all(eq_zero(t[i, j] - (m[i] - m[j]) * xmat[i, j]) for i in range(3) for j in range(i + 1, 3))
    cols = [sp.Matrix([sp.diff(v, q) for v in t]) for q in x]
    matrix = sp.Matrix.hstack(*cols)
    gram = matrix.T * matrix
    expected_gram = sp.diag(*[2 * gap**2 for gap in gaps])
    checks["rank_kernel_gap_gram"] = eq_zero(gram - expected_gram)
    checks["rank_det_factor"] = eq_zero(sp.factor(gram.det()) - 8 * sp.prod(gap**2 for gap in gaps))
    checks["norm_gap_identity"] = eq_zero(norm_squared(t) - 2 * sum(gaps[k]**2 * x[k]**2 for k in range(3))) and eq_zero(norm_squared(xmat) - 2 * sum(q**2 for q in x))
    details["gram_diagonal"] = [str(sp.factor(gram[i, i])) for i in range(3)]
    details["gram_determinant"] = str(sp.factor(gram.det()))

    r12, r13, r23 = sp.symbols("r12 r13 r23", real=True)
    r = sp.Matrix([[0, r12, r13], [r12, 0, r23], [r13, r23, 0]])
    inverse = sp.Matrix([[0, r12/gaps[0], r13/gaps[1]], [-r12/gaps[0], 0, r23/gaps[2]], [-r13/gaps[1], -r23/gaps[2], 0]])
    checks["exact_inverse"] = eq_zero(commutator(d, inverse) - r) and eq_zero(inverse + inverse.T)

    p = projection(amat)
    z = sp.Matrix([[0, p[0, 1]/gaps[0], p[0, 2]/gaps[1]], [-p[0, 1]/gaps[0], 0, p[1, 2]/gaps[2]], [-p[0, 2]/gaps[1], -p[1, 2]/gaps[2], 0]])
    checks["projection_image"] = eq_zero(commutator(d, z) - p)
    checks["projection_orthogonality"] = eq_zero(sp.trace((amat-p).T*t))
    checks["projection_idempotent"] = eq_zero(projection(p)-p)
    # Exact Pythagoras for every real A and every skew X. The residual
    # ||T(Z)-A|| is retained and is not silently fit.
    objective_difference = norm_squared(t-amat) - norm_squared(commutator(d, z)-amat) - norm_squared(commutator(d, xmat-z))
    checks["least_squares_pythagoras"] = eq_zero(objective_difference)
    checks["unique_minimizer_gap"] = eq_zero(norm_squared(commutator(d, xmat-z)) - 2*sum(gaps[k]**2 * (x[k]-z[[0,0,1][k], [1,2,2][k]])**2 for k in range(3)))

    # Generic symmetric perturbation; this identity fixes the sign in the
    # projection/minimality perturbation argument.
    u = sp.symbols("u11 u12 u13 u22 u23 u33", real=True)
    dm = sp.Matrix([[u[0], u[1], u[2]], [u[1], u[3], u[4]], [u[2], u[4], u[5]]])
    e = sp.Matrix(3, 3, sp.symbols("e11 e12 e13 e21 e22 e23 e31 e32 e33", real=True))
    mhat = d + dm
    rhat = commutator(d, xmat) + e
    checks["perturbation_sign_identity"] = eq_zero(rhat - commutator(mhat, xmat) - (e - commutator(dm, xmat)))
    checks["perturbation_commutator_symmetric"] = eq_zero(commutator(dm, xmat)-commutator(dm, xmat).T)
    # Scalar algebra used after the ordered-eigenvalue min-max inequality.
    eps, e1, e2, e3 = sp.symbols("epsilon_M e1 e2 e3", real=True)
    errors = (e1, e2, e3)
    checks["ordered_gap_algebra"] = all(eq_zero(((m[j]+errors[j])-(m[i]+errors[i])) - (m[j]-m[i]) - (errors[j]-errors[i])) for i in range(3) for j in range(i+1, 3))
    details["ordered_gap_reason"] = "|e_i|<=epsilon_M from symmetric operator norm and Courant-Fischer; e_j-e_i>=-2epsilon_M"

    repeated = sp.diag(1,1,3)
    isotropic = sp.eye(3)*5
    basis12 = sp.Matrix([[0,1,0],[-1,0,0],[0,0,0]])
    checks["repeated_eigenvalue_kernel_control"] = eq_zero(commutator(repeated,basis12)) and not eq_zero(basis12)
    checks["isotropic_zero_map_control"] = eq_zero(commutator(isotropic,xmat))
    checks["perturbed_zero_gap_exclusion_control"] = eq_zero(commutator(repeated,basis12))
    diag_residual = sp.diag(1,0,0)
    checks["diagonal_residual_control"] = eq_zero(projection(diag_residual)) and norm_squared(diag_residual) == 1

    all_good = all(checks.values())
    payload = {
        "checks": {OBLIGATION: all_good},
        "domain_assumption_diff": [],
        "counterexample": None,
        "sympy_version": sp.__version__,
        "python_version": sys.version.split()[0],
        "exact_subchecks": checks,
        "details": details,
        "claim_ceiling": "C03_finite_commutator_inverse_and_perturbation_only",
        "scientific_admission": "HOLD",
    }
    print(json.dumps(payload, sort_keys=True))
    return 0 if all_good else 1


if __name__ == "__main__":
    raise SystemExit(main())
