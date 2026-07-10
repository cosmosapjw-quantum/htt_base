"""BV-DYN: tilted-LRS Bianchi V EVOLUTION seal (v9, REV-R178).

Executes the registered stretch item ("an expansion-normalized tilted-LRS
Bianchi V evolution check ... would upgrade the F2 constraint-algebra seal
to a dynamics seal; it is registered here, not claimed"). The system is
DERIVED FIRST-PRINCIPLES in SymPy from the metric ansatz -- no literature
system is transcribed:

    ds^2 = -dt^2 + a1(t)^2 dx^2 + a2(t)^2 e^{2x} (dy^2 + dz^2)

(LRS Bianchi type V; the homogeneity a-vector points along x) with a tilted
perfect fluid u^mu = (cosh b, sinh b / a1, 0, 0), p = w rho, kappa = 1.
SymPy computes the Einstein tensor exactly; the EVOLUTION system is
{G_xx = T_xx, G_yy = T_yy, energy conservation, x-momentum conservation}
solved for (a1'', a2'', rho', b'), and the two CONSTRAINTS

    C1 (Gauss):    G_tt - T_tt = 0
    C2 (momentum): G_tx - T_tx = 0

are NOT imposed during integration -- they are monitored along the numeric
trajectory. Constraint-satisfying initial data are constructed by declaring
rho0 > 0 (excluding the vacuous vacuum/Milne branch) and Newton-solving the
pair (H1, H2) jointly from {C1 = 0, C2 = 0} to residuals < 1e-12, and
preservation of both residuals at the integration-tolerance level over
~1.1 e-folds is the dynamics statement (contracted Bianchi identities,
verified numerically, not assumed).

Alignment with the sealed P5 constraint algebra (frozen module
``egs3_bianchi_v_constraint``): along the trajectory the expansion-normalized
variables Sigma_+ = (H1 - H2)/... , A, Omega satisfy the exact-rapidity
momentum relation, and the LEADING P5 formula's relative error scales as
beta^2 (the frozen seal's scaling law, now verified ON A DYNAMICAL
TRAJECTORY rather than at the constraint surface only).

Scope discipline: this upgrades the F2 lane (LRS Bianchi V, single tilt
along the a-vector) from constraint algebra to dynamics. It is NOT the
King-Ellis rotating-congruence item (still registered), does NOT realize the
T3 endpoints dynamically (the upper-endpoint witness uses TRANSVERSE shear,
a different configuration), and makes no data claim, no signal-discovery
claim, and no probabilistic-inference claim about the sky.
"""
from __future__ import annotations

from functools import lru_cache

import numpy as np
import sympy as sp

from htt.obsstat.egs3_bianchi_v_constraint import (
    exact_rapidity_sigma_plus_sq,
    p5_leading_sigma_plus_sq,
)

__all__ = [
    "derive_field_equations",
    "constraint_initial_data",
    "integrate_trajectory",
    "constraint_preservation_check",
    "p5_alignment_on_trajectory",
    "bianchi_v_dynamics_seal",
]


@lru_cache(maxsize=1)
def derive_field_equations():
    """First-principles SymPy derivation. Returns lambdified callables:
    rhs(state, w), C1(state, w), C2(state, w) with
    state = (a1, a2, da1, da2, rho, b)."""
    t, x, w = sp.symbols("t x w", real=True)
    a1 = sp.Function("a1", positive=True)(t)
    a2 = sp.Function("a2", positive=True)(t)
    rho = sp.Function("rho", positive=True)(t)
    b = sp.Function("b", real=True)(t)

    coords = (t, x, sp.Symbol("y"), sp.Symbol("z"))
    g = sp.diag(-1, a1 ** 2, a2 ** 2 * sp.exp(2 * x),
                a2 ** 2 * sp.exp(2 * x))
    ginv = g.inv()

    def christoffel(l, m, n):
        return sp.Rational(1, 2) * sum(
            ginv[l, s] * (sp.diff(g[s, m], coords[n])
                          + sp.diff(g[s, n], coords[m])
                          - sp.diff(g[m, n], coords[s]))
            for s in range(4))

    Gamma = [[[sp.simplify(christoffel(l, m, n)) for n in range(4)]
              for m in range(4)] for l in range(4)]

    def ricci(m, n):
        term = sp.S.Zero
        for l in range(4):
            term += sp.diff(Gamma[l][m][n], coords[l])
            term -= sp.diff(Gamma[l][m][l], coords[n])
            for s in range(4):
                term += Gamma[l][l][s] * Gamma[s][m][n]
                term -= Gamma[l][n][s] * Gamma[s][m][l]
        return sp.simplify(term)

    Ric = sp.zeros(4, 4)
    for m in range(4):
        for n in range(m, 4):
            Ric[m, n] = ricci(m, n)
            Ric[n, m] = Ric[m, n]
    Rs = sp.simplify(sum(ginv[m, n] * Ric[m, n]
                         for m in range(4) for n in range(4)))
    G = sp.simplify(Ric - sp.Rational(1, 2) * Rs * g)

    # tilted perfect fluid, tilt along x
    u_up = sp.Matrix([sp.cosh(b), sp.sinh(b) / a1, 0, 0])
    u_dn = g * u_up
    p = w * rho
    T = sp.zeros(4, 4)
    for m in range(4):
        for n in range(4):
            T[m, n] = (rho + p) * u_dn[m] * u_dn[n] + p * g[m, n]

    E = sp.simplify(G - T)          # field equations E_{mu nu} = 0

    # conservation equations nabla_mu T^{mu nu} = 0 (nu = t and nu = x)
    T_ud = sp.simplify(ginv * T)    # T^{mu}_{~nu} -> use mixed form
    Tup = sp.simplify(ginv * T * ginv.T)  # T^{mu nu}

    def divergence(nu):
        term = sp.S.Zero
        for m in range(4):
            term += sp.diff(Tup[m, nu], coords[m])
            for l in range(4):
                term += Gamma[m][m][l] * Tup[l, nu]
                term += Gamma[nu][m][l] * Tup[m, l]
        return sp.simplify(term)

    cons_t = divergence(0)
    cons_x = divergence(1)

    # evolution unknowns
    d2a1, d2a2, drho, db = sp.symbols("d2a1 d2a2 drho db", real=True)
    subs2 = {sp.diff(a1, t, 2): d2a1, sp.diff(a2, t, 2): d2a2,
             sp.diff(rho, t): drho, sp.diff(b, t): db}
    eqs = [sp.Eq(E[1, 1].subs(subs2), 0), sp.Eq(E[2, 2].subs(subs2), 0),
           sp.Eq(cons_t.subs(subs2), 0), sp.Eq(cons_x.subs(subs2), 0)]
    sol = sp.solve(eqs, (d2a1, d2a2, drho, db), dict=True)
    assert len(sol) == 1, "evolution system must solve uniquely"
    sol = sol[0]

    da1s, da2s = sp.symbols("da1s da2s", real=True)
    a1s, a2s, rhos, bs = sp.symbols("a1s a2s rhos bs", real=True)
    first = {sp.diff(a1, t): da1s, sp.diff(a2, t): da2s,
             a1: a1s, a2: a2s, rho: rhos, b: bs, x: 0}
    state = (a1s, a2s, da1s, da2s, rhos, bs)

    rhs_exprs = [sp.simplify(sol[k].subs(first))
                 for k in (d2a1, d2a2, drho, db)]
    C1_expr = sp.simplify(E[0, 0].subs(first))
    C2_expr = sp.simplify(E[0, 1].subs(first))

    rhs_f = sp.lambdify(state + (w,), rhs_exprs, "numpy")
    C1_f = sp.lambdify(state + (w,), C1_expr, "numpy")
    C2_f = sp.lambdify(state + (w,), C2_expr, "numpy")
    return rhs_f, C1_f, C2_f, (str(C1_expr), str(C2_expr))


def constraint_initial_data(*, beta0: float, w: float, rho0: float = 0.3,
                            a10: float = 1.0, a20: float = 1.0) -> np.ndarray:
    """Exact constraint-satisfying NON-VACUUM initial data: the matter
    density rho0 > 0 is DECLARED (fixing it excludes the trivial vacuum/Milne
    solution, on which both constraints hold for any tilt), and the two
    expansion rates (H1, H2) are solved from {C1 = 0, C2 = 0} by Newton on
    the exact expressions; residuals verified < 1e-12."""
    if rho0 <= 0.0:
        raise ValueError("non-vacuum witness requires rho0 > 0")
    _, C1_f, C2_f, _ = derive_field_equations()

    def residuals(vec):
        h1, h2 = vec
        st = (a10, a20, h1 * a10, h2 * a20, rho0, beta0)
        return np.array([C1_f(*st, w), C2_f(*st, w)])

    vec = np.array([1.0, 1.0])
    for _ in range(60):
        r = residuals(vec)
        eps = 1e-7
        J = np.column_stack([
            (residuals(vec + np.array([eps, 0])) - r) / eps,
            (residuals(vec + np.array([0, eps])) - r) / eps])
        vec = vec - np.linalg.solve(J, r)
        if np.max(np.abs(residuals(vec))) < 1e-13:
            break
    h1, h2 = vec
    st = np.array([a10, a20, h1 * a10, h2 * a20, rho0, beta0])
    assert np.max(np.abs(residuals(vec))) < 1e-12, "IC solve failed"
    assert st[4] > 0.0
    return st


def integrate_trajectory(state0: np.ndarray, *, w: float, t_end: float = 2.0,
                         n_eval: int = 81, rtol: float = 1e-10,
                         atol: float = 1e-12):
    """Integrate the derived evolution system (constraints NOT imposed)."""
    from scipy.integrate import solve_ivp
    rhs_f, _, _, _ = derive_field_equations()

    def rhs(_t, y):
        a1v, a2v, da1, da2, rhov, bv = y
        d2a1, d2a2, drho, db = rhs_f(a1v, a2v, da1, da2, rhov, bv, w)
        return [da1, da2, d2a1, d2a2, drho, db]

    ts = np.linspace(0.0, t_end, n_eval)
    sol = solve_ivp(rhs, (0.0, t_end), state0, t_eval=ts,
                    rtol=rtol, atol=atol, method="RK45")
    assert sol.success, sol.message
    return sol.t, sol.y


def constraint_preservation_check(*, beta0: float = 0.05, w: float = 0.0,
                                  t_end: float = 2.0) -> dict:
    """Gauss + momentum residuals monitored (not imposed) along the
    trajectory; preservation at integration tolerance is the dynamics
    statement."""
    _, C1_f, C2_f, _ = derive_field_equations()
    st0 = constraint_initial_data(beta0=beta0, w=w)
    ts, ys = integrate_trajectory(st0, w=w, t_end=t_end)
    c1 = np.array([abs(C1_f(*ys[:, i], w)) for i in range(ts.size)])
    c2 = np.array([abs(C2_f(*ys[:, i], w)) for i in range(ts.size)])
    efolds = float(np.log(ys[1, -1] / ys[1, 0]))
    return {
        "beta0": beta0, "w": w, "t_end": t_end,
        "e_folds_a2": round(efolds, 4),
        "initial_residuals": [float(c1[0]), float(c2[0])],
        "max_gauss_residual": float(c1.max()),
        "max_momentum_residual": float(c2.max()),
        "preserved_at_tolerance": bool(c1.max() < 1e-8 and c2.max() < 1e-8),
        "rho_initial": float(ys[4, 0]),
        "rho_final": float(ys[4, -1]),
        "nonvacuum_throughout": bool(np.all(ys[4, :] > 0.0)),
        "shear_initial_h1_minus_h2": float(ys[2, 0] / ys[0, 0]
                                           - ys[3, 0] / ys[1, 0]),
        "beta_final": float(ys[5, -1]),
        "tilt_decays": bool(abs(ys[5, -1]) < abs(beta0)),
    }


def p5_alignment_on_trajectory(*, w: float = 0.0,
                               betas=(1e-3, 3e-3, 1e-2, 3e-2)) -> dict:
    """Along DYNAMICAL trajectories the expansion-normalized (Sigma_+, A,
    Omega) satisfy the exact-rapidity momentum relation, and the leading P5
    formula's relative error scales as beta^2 (frozen-seal law, now on
    trajectories)."""
    _, C1_f, C2_f, _ = derive_field_equations()
    rel_errors = []
    exact_resid = []
    for beta0 in betas:
        st0 = constraint_initial_data(beta0=beta0, w=w)
        ts, ys = integrate_trajectory(st0, w=w, t_end=1.0, n_eval=5)
        i = ts.size - 1
        a1v, a2v, da1, da2, rhov, bv = ys[:, i]
        h1, h2 = da1 / a1v, da2 / a2v
        H = (h1 + 2 * h2) / 3.0
        sigma_plus_sq = ((h1 - h2) / (3.0 * H)) ** 2  # (Sigma_+)^2, HW norm
        A = 1.0 / (a1v * H)                            # curvature a-vector
        omega = rhov / (3.0 * H ** 2)
        lead = p5_leading_sigma_plus_sq(bv, A=A, w=w, Omega_m=omega)
        exact = exact_rapidity_sigma_plus_sq(bv, A=A, w=w, Omega_m=omega)
        rel_errors.append(abs(lead - exact) / exact)
        exact_resid.append(abs(sigma_plus_sq - exact) / exact)
    logb = np.log(np.asarray(betas))
    loge = np.log(np.asarray(rel_errors))
    slope = float(np.polyfit(logb, loge, 1)[0])
    return {
        "betas": list(betas),
        "leading_vs_exact_rel_errors": [float(v) for v in rel_errors],
        "loglog_slope": round(slope, 4),
        "beta_sq_scaling_on_trajectory": bool(abs(slope - 2.0) < 0.1),
        "trajectory_matches_exact_constraint_rel": [
            float(v) for v in exact_resid],
        "trajectory_satisfies_exact_relation": bool(
            max(exact_resid) < 1e-6),
    }


def bianchi_v_dynamics_seal() -> dict:
    """Fail-closed BV-DYN seal (registry id BV-DYN; upgrades the F2 lane
    from constraint algebra to dynamics)."""
    dust = constraint_preservation_check(beta0=0.05, w=0.0)
    rad = constraint_preservation_check(beta0=0.05, w=1.0 / 3.0)
    align = p5_alignment_on_trajectory(w=0.0)
    ok = (dust["preserved_at_tolerance"] and rad["preserved_at_tolerance"]
          and dust["nonvacuum_throughout"] and rad["nonvacuum_throughout"]
          and abs(dust["shear_initial_h1_minus_h2"]) > 1e-6
          and align["beta_sq_scaling_on_trajectory"]
          and align["trajectory_satisfies_exact_relation"]
          and dust["tilt_decays"])
    return {
        "seal": "egs3.bianchi_v_dynamics",
        "theorem_id": "BV-DYN",
        "status": "PASS" if ok else "FAIL",
        "discharges": "the v9 report's registered stretch item: tilted-LRS "
                      "Bianchi V EVOLUTION check upgrading the F2 "
                      "constraint-algebra seal to a dynamics seal",
        "derivation": "first-principles SymPy Einstein tensor for "
                      "ds^2=-dt^2+a1^2 dx^2+a2^2 e^{2x}(dy^2+dz^2) with a "
                      "tilted perfect fluid; evolution = {E_xx, E_yy, "
                      "energy conservation, x-momentum conservation}; "
                      "constraints E_tt, E_tx MONITORED, never imposed",
        "constraint_preservation_dust": dust,
        "constraint_preservation_radiation": rad,
        "p5_alignment_on_trajectory": align,
        "scope_not_claimed": "NOT the King-Ellis rotating-congruence item; "
                             "NOT a dynamical realization of the T3 "
                             "endpoints (transverse-shear configuration); "
                             "no data, signal-discovery, Bianchi-class-"
                             "identification-of-the-sky, or probabilistic-"
                             "inference claim",
    }
