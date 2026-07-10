"""KE-DYN: King-Ellis rotating-congruence dynamics (items 8-10 of the
ten-item program; v9 follow-on cycle, REV-R182).

Everything is DERIVED FIRST-PRINCIPLES in SymPy from the metric ansatz --
no literature system is transcribed. Two configurations:

  (a) the DIAGONAL class of egs3_king_ellis_frame (imported read-only) for
      the exact u-frame conservation and Raychaudhuri identities;
  (b) the OFF-DIAGONAL rotating class

        ds^2 = -dt^2 + eta_ij(t) w^i w^j,   w^1 = dx, w^2 = e^{cx} dy,
        w^3 = e^{cx} dz,   eta = [[h11,h12,0],[h12,h22,0],[0,0,h33]]

      (c = 1 type V, c = 0 type I) with the group-invariant tilted fluid
      u = (u^t, w1, w2 e^{-cx}, 0), u^t = sqrt(1 + h11 w1^2 + 2 h12 w1 w2
      + h22 w2^2) -- the class in which the tilt is OBLIQUE in the x-y
      block, so the congruence carries genuine vorticity (KE-OBS).

Item map (8-10):
  8. matter conservation in the u-frame: u(rho) + Theta[u](rho + p) = 0
     (energy) and (rho + p) A_a + D_a p = 0 (Euler) verified EXACTLY on
     the ansatz class                          -> uframe_conservation
  9. evolution equations: the Raychaudhuri identity with its omega^2 term
     DERIVED by undetermined coefficients (exact rational-point linear
     systems + symbolic verification on rotating configurations)
                                               -> raychaudhuri_identity
 10. local development: the off-diagonal system {E_xx, E_xy, E_yy, E_zz,
     div T^t, div T^x, div T^y} solved for (h11'', h12'', h22'', h33'',
     rho', w1', w2') -- a generically invertible 7x7 linear system after
     rationalizing u^t (U^2 -> 1 + norm reduction); constraint-satisfying
     NON-VACUUM rotating initial data (Newton on {E_tt, E_tx, E_ty});
     the three constraints MONITORED (never imposed) along RK45
     trajectories; omega_ab omega^ab [u] > 0 maintained
                                               -> rotating_development
     PLUS the aligned BV-DYN trajectory re-expressed in u-frame variables
     (u-frame energy conservation along the trajectory)
                                               -> aligned_uframe_trajectory
     PLUS the radiation center-manifold drift law d(beta)/d(ln a) =
     +(2/3) beta^2 (the literature-anchored reading of the R178 finding)
     corroborated on the BV-DYN system         -> radiation_center_manifold

Net verdict (the honest closure of the ten-item program): a genuine
rotating perfect-fluid development EXISTS at Omega_k > 0 (type V, single
oblique tilt; omega^2[u] > 0 maintained under monitored constraints); at
Omega_k = 0 it is DOUBLY obstructed -- the single stream by the momentum
constraint (G_ti = 0 identically for every homogeneous type-I metric in
the class) and the antipodal pair by DYNAMICAL irrotationality (the
translational Killing vectors + the barotropic Euler equation conserve
the tilt-covector direction, so the oblique kinematic vorticity modes of
KE-OBS are never entered). The T3 lower-endpoint W^2 withdrawal is
thereby upgraded from constraint-level to dynamical within this class.

Scope discipline: the comparator W^2 is defined on the SLICE NORMAL,
which stays hypersurface-orthogonal here (Frobenius), so the withdrawal
STANDS; whether W^2 should be re-attributed to the matter congruence is a
registered interpretive question, not a claim. No numeric value of the
withdrawn W^2 = 4/100 is asserted. No data claim, no signal-discovery
claim, no probabilistic inference about the sky.
"""
from __future__ import annotations

from functools import lru_cache

import numpy as np
import sympy as sp
from scipy.integrate import solve_ivp

from htt.obsstat.egs3_bianchi_v_dynamics import (
    constraint_initial_data,
    derive_field_equations,
    integrate_trajectory,
)
from htt.obsstat.egs3_king_ellis_frame import (
    _funcs,
    _geometry,
    _hyper_simplify,
    _kinematics,
    _u_vector,
    frame_kinematics,
)

__all__ = [
    "uframe_conservation",
    "raychaudhuri_identity",
    "derive_rotating_system",
    "rotating_initial_data",
    "rotating_development",
    "aligned_uframe_trajectory",
    "radiation_center_manifold",
    "king_ellis_dynamics_seal",
]

_T, _X = sp.symbols("t x", real=True)
_W = sp.Symbol("w", real=True)


# ---------------------------------------------------------------- item 8
@lru_cache(maxsize=1)
def uframe_conservation() -> dict:
    """Exact u-frame conservation on the diagonal ansatz class: project
    nabla_m T^{mn} = 0 (comoving perfect fluid, p = w rho(t)) along u and
    orthogonally to u; verify the covariant forms

        u(rho) + Theta[u] (rho + p) = 0        (energy)
        (rho + p) A_a + D_a p = 0              (Euler; D_a p = h^m_a d_m p)

    hold as IDENTITIES between the computed divergence projections and
    the computed kinematic scalars (transverse and oblique rotating
    configurations included)."""
    out = {}
    for case, tilt, cvec in (
            ("bianchi_v", "transverse", (0, 1, 0)),
            ("bianchi_v", "oblique", (sp.Rational(3, 5),
                                      sp.Rational(4, 5), 0)),
            ("bianchi_i", "oblique", (sp.Rational(3, 5),
                                      sp.Rational(4, 5), 0))):
        coords, g, ginv, Gam, _, _, _, _ = _geometry(case)
        kin = frame_kinematics(case, tilt)
        u_up, u_dn = kin["u_up"], kin["u_dn"]
        rho = sp.Function("rho", positive=True)(_T)
        p = _W * rho
        T = sp.zeros(4, 4)
        for m in range(4):
            for n in range(4):
                T[m, n] = (rho + p) * u_dn[m] * u_dn[n] + p * g[m, n]
        Tud = ginv * T
        div = []
        for nu in range(4):
            term = sp.S.Zero
            for m in range(4):
                term += sp.diff(Tud[m, nu], coords[m])
                for l in range(4):
                    term += Gam[m][m][l] * Tud[l, nu] \
                        - Gam[l][m][nu] * Tud[m, l]
            div.append(sp.together(term))
        # energy: -u^nu (div T)_nu  ==  u(rho) + Theta (rho + p)
        energy_lhs = sp.together(-sum(u_up[nu] * div[nu]
                                      for nu in range(4)))
        energy_rhs = sp.together(
            sum(u_up[m] * sp.diff(rho, coords[m]) for m in range(4))
            + kin["theta"] * (rho + p))
        ok_energy = _hyper_simplify(energy_lhs - energy_rhs) == 0
        # Euler: h^nu_a (div T)_nu  ==  (rho+p) A_a + h^m_a d_m p
        hmix = kin["hmix"]
        ok_euler = True
        for a in range(4):
            lhs = sum(hmix[nu, a] * div[nu] for nu in range(4))
            rhs = ((rho + p) * kin["A_dn"][a]
                   + sum(hmix[m, a] * sp.diff(p, coords[m])
                         for m in range(4)))
            ok_euler &= _hyper_simplify(lhs - rhs) == 0
        out[f"{case}_{tilt}"] = {"energy_identity": bool(ok_energy),
                                 "euler_identity": bool(ok_euler)}
    out["all_exact"] = all(v["energy_identity"] and v["euler_identity"]
                           for v in out.values() if isinstance(v, dict))
    return out


# ---------------------------------------------------------------- item 9
@lru_cache(maxsize=1)
def raychaudhuri_identity() -> dict:
    """Derive (not transcribe) the Raychaudhuri identity

        u(Theta) = -Theta^2/3 + alpha sigma^2 + beta omega^2
                   + gamma A^2 + delta divA + epsilon R_uu

    (sigma^2 = sigma_ab sigma^ab, omega^2 = omega_ab omega^ab,
    A^2 = A_a A^a, divA = nabla_m A^m, R_uu = R_ab u^a u^b) by exact
    rational-point linear systems on the rotating type-V oblique
    configuration, then verify the residual vanishes identically on
    three configurations (two rotating)."""
    al, be, ga, de, ep = sp.symbols(
        "alpha_r beta_r gamma_r delta_r epsilon_r", rational=True)

    def scalars(case, tilt):
        coords, g, ginv, Gam, _, Ric, _, _ = _geometry(case)
        kin = frame_kinematics(case, tilt)
        u = kin["u_up"]
        uTheta = sp.together(sum(u[m] * sp.diff(kin["theta"], coords[m])
                                 for m in range(4)))
        A_up = ginv * kin["A_dn"]
        divA = sp.S.Zero
        for m in range(4):
            divA += sp.diff(A_up[m], coords[m])
            divA += sum(Gam[m][m][l] * A_up[l] for l in range(4))
        A2 = sum(ginv[a, b] * kin["A_dn"][a] * kin["A_dn"][b]
                 for a in range(4) for b in range(4))
        ruu = sum(Ric[m, n] * u[m] * u[n] for m in range(4)
                  for n in range(4))
        return (uTheta, kin["theta"], kin["sigma2"], kin["omega2"],
                A2, sp.together(divA), sp.together(ruu))

    uTh, th, s2, w2, A2, divA, ruu = scalars("bianchi_v", "oblique")
    resid = (uTh + th ** 2 / 3 - al * s2 - be * w2 - ga * A2
             - de * divA - ep * ruu)

    from htt.obsstat.egs3_king_ellis_frame import _eval_rational
    pts = ((2, 3, 5, sp.Rational(1, 2), sp.Rational(1, 3),
            sp.Rational(1, 5), sp.Rational(1, 7), sp.Rational(3, 2),
            sp.Rational(1, 11), sp.Rational(1, 13), sp.Rational(1, 17)),
           (3, 2, 7, sp.Rational(2, 5), sp.Rational(1, 9),
            sp.Rational(2, 3), sp.Rational(2, 7), sp.Rational(5, 3),
            sp.Rational(1, 19), sp.Rational(1, 23), sp.Rational(1, 29)),
           (5, 7, 2, sp.Rational(3, 7), sp.Rational(4, 9),
            sp.Rational(1, 6), sp.Rational(3, 8), sp.Rational(7, 4),
            sp.Rational(2, 21), sp.Rational(1, 31), sp.Rational(1, 37)),
           (7, 5, 3, sp.Rational(1, 4), sp.Rational(2, 9),
            sp.Rational(5, 6), sp.Rational(1, 8), sp.Rational(4, 3),
            sp.Rational(3, 11), sp.Rational(2, 13), sp.Rational(1, 41)),
           (2, 5, 3, sp.Rational(3, 5), sp.Rational(1, 8),
            sp.Rational(2, 9), sp.Rational(5, 8), sp.Rational(6, 5),
            sp.Rational(1, 43), sp.Rational(1, 47), sp.Rational(1, 53)),
           (3, 7, 5, sp.Rational(1, 6), sp.Rational(3, 8),
            sp.Rational(4, 7), sp.Rational(2, 11), sp.Rational(9, 7),
            sp.Rational(2, 43), sp.Rational(3, 47), sp.Rational(1, 59)))
    eqs = [_eval_rational(resid, pt) for pt in pts]
    sol = sp.solve(eqs[:5], (al, be, ga, de, ep), dict=True)
    if len(sol) != 1:
        raise RuntimeError(f"raychaudhuri coefficients not unique: {sol}")
    coeff = sol[0]
    checks = {"sixth_point_consistent":
              sp.simplify(eqs[5].subs(coeff)) == 0}
    for case, tilt in (("bianchi_v", "oblique"), ("bianchi_v", "aligned"),
                       ("bianchi_i", "oblique")):
        uThc, thc, s2c, w2c, A2c, divAc, ruuc = scalars(case, tilt)
        res = (uThc + thc ** 2 / 3 - coeff[al] * s2c - coeff[be] * w2c
               - coeff[ga] * A2c - coeff[de] * divAc - coeff[ep] * ruuc)
        checks[f"identity_symbolic_{case}_{tilt}"] = \
            _hyper_simplify(res) == 0
    return {
        "alpha_sigma2": str(coeff[al]), "beta_omega2": str(coeff[be]),
        "gamma_A2": str(coeff[ga]), "delta_divA": str(coeff[de]),
        "epsilon_Ruu": str(coeff[ep]),
        "identity": ("u(Theta) = -Theta^2/3 "
                     f"+ ({coeff[al]}) sigma_ab sigma^ab "
                     f"+ ({coeff[be]}) omega_ab omega^ab "
                     f"+ ({coeff[ga]}) A_a A^a + ({coeff[de]}) div A "
                     f"+ ({coeff[ep]}) R_ab u^a u^b"),
        "checks": checks,
    }


# --------------------------------------------------------------- item 10
@lru_cache(maxsize=4)
def derive_rotating_system(curv: int = 1, streams: int = 1):
    """First-principles derivation of the off-diagonal rotating system
    (curv = 1 type V, curv = 0 type I; streams = 1 single tilted fluid,
    streams = 2 the antipodal pair +-(w1, w2) with each stream separately
    conserved). Returns callables rhs(state, w), constraints(state, w) ->
    (C1, C2, C3), and kin(state, dw1, dw2, w) -> (Theta, sigma2, omega2,
    A2) for the + stream, with
    state = (h11, h12, h22, h33, dh11, dh12, dh22, dh33, rho, w1, w2)."""
    t, x = _T, _X
    h11 = sp.Function("h11", positive=True)(t)
    h12 = sp.Function("h12", real=True)(t)
    h22 = sp.Function("h22", positive=True)(t)
    h33 = sp.Function("h33", positive=True)(t)
    rho = sp.Function("rho", positive=True)(t)
    w1 = sp.Function("w1", real=True)(t)
    w2 = sp.Function("w2", real=True)(t)
    U = sp.Function("ut", positive=True)(t)
    coords = (t, x, sp.Symbol("y"), sp.Symbol("z"))
    ex = sp.exp(curv * x)
    g = sp.Matrix([[-1, 0, 0, 0],
                   [0, h11, h12 * ex, 0],
                   [0, h12 * ex, h22 * ex ** 2, 0],
                   [0, 0, 0, h33 * ex ** 2]])
    ginv = g.inv()

    def chri(l, m, n):
        return sp.Rational(1, 2) * sum(
            ginv[l, k] * (sp.diff(g[k, m], coords[n])
                          + sp.diff(g[k, n], coords[m])
                          - sp.diff(g[m, n], coords[k])) for k in range(4))

    Gam = [[[sp.cancel(chri(l, m, n)) for n in range(4)]
            for m in range(4)] for l in range(4)]

    def ricci(m, n):
        term = sp.S.Zero
        for l in range(4):
            term += sp.diff(Gam[l][m][n], coords[l])
            term -= sp.diff(Gam[l][m][l], coords[n])
            for s in range(4):
                term += Gam[l][l][s] * Gam[s][m][n]
                term -= Gam[l][n][s] * Gam[s][m][l]
        return sp.cancel(sp.together(term))

    Ric = sp.zeros(4, 4)
    for m in range(4):
        for n in range(m, 4):
            Ric[m, n] = ricci(m, n)
            Ric[n, m] = Ric[m, n]
    Rs = sp.cancel(sp.together(sum(ginv[m, n] * Ric[m, n]
                                   for m in range(4) for n in range(4))))
    G = (Ric - Rs / 2 * g).applyfunc(sp.expand)

    u_up = sp.Matrix([U, w1, w2 / ex, 0])
    p = _W * rho
    if streams == 1:
        u_dn = g * u_up
        T = sp.zeros(4, 4)
        for m in range(4):
            for n in range(4):
                T[m, n] = (rho + p) * u_dn[m] * u_dn[n] + p * g[m, n]
        T_cons = T             # the (single) conserved stream
    else:
        # antipodal pair: streams +-(w1, w2), each of density rho/2 and
        # pressure p/2, separately conserved (non-interacting); the total
        # energy flux T_ti cancels exactly (odd in the tilt) while each
        # stream keeps its oblique tilt and hence its vorticity
        u_m = sp.Matrix([U, -w1, -w2 / ex, 0])
        T = sp.zeros(4, 4)
        for uu in (u_up, u_m):
            ud = g * uu
            for m in range(4):
                for n in range(4):
                    T[m, n] += (rho / 2 + p / 2) * ud[m] * ud[n] \
                        + p / 2 * g[m, n] / 2 * 0
        T = T + p * g          # pressures add: p/2 + p/2
        ud_p = g * u_up
        T_cons = sp.zeros(4, 4)
        for m in range(4):
            for n in range(4):
                T_cons[m, n] = (rho / 2 + p / 2) * ud_p[m] * ud_p[n] \
                    + p / 2 * g[m, n]
    E = (G - T).applyfunc(sp.expand)
    Tud = ginv * T_cons

    def divT(nu):
        term = sp.S.Zero
        for m in range(4):
            term += sp.diff(Tud[m, nu], coords[m])
            for l in range(4):
                term += Gam[m][m][l] * Tud[l, nu] - Gam[l][m][nu] * Tud[m, l]
        return sp.expand(term)

    norm = h11 * w1 ** 2 + 2 * h12 * w1 * w2 + h22 * w2 ** 2
    dU_expr = sp.expand(sp.diff(1 + norm, t)) / (2 * U)

    def reduce_u(e):
        e = sp.expand(e.subs(sp.Derivative(U, t), dU_expr))
        for _ in range(6):
            e2 = sp.expand(e.subs(U ** 2, 1 + norm))
            if e2 == e:
                break
            e = e2
        return e

    eqs = [reduce_u(E[1, 1]), reduce_u(E[1, 2] / ex),
           reduce_u(E[2, 2] / ex ** 2), reduce_u(E[3, 3] / ex ** 2),
           reduce_u(divT(0)), reduce_u(divT(1)), reduce_u(divT(2))]
    unks = [sp.Derivative(f, t, 2) for f in (h11, h12, h22, h33)] \
        + [sp.Derivative(f, t) for f in (rho, w1, w2)]
    Amat, bvec = sp.linear_eq_to_matrix(eqs, unks)
    # the symbolic LU solution of the 7x7 system explodes; lambdify the
    # matrix and right-hand side instead and solve NUMERICALLY per step
    cons = [reduce_u(E[0, 0]), reduce_u(E[0, 1]),
            reduce_u(sp.expand(E[0, 2] / ex))]   # invariant-frame E_ty

    args = (h11, h12, h22, h33,
            sp.Derivative(h11, t), sp.Derivative(h12, t),
            sp.Derivative(h22, t), sp.Derivative(h33, t),
            rho, w1, w2, U, _W)
    subs_x0 = {x: 0}
    Amat_f = sp.lambdify(args, Amat.subs(subs_x0), "numpy")
    bvec_f = sp.lambdify(args, list(bvec.subs(subs_x0)), "numpy")
    con_f = sp.lambdify(args, [e.subs(subs_x0) for e in cons], "numpy")

    # kinematics: lambdify grad / metric / u componentwise, contract
    # numerically (the symbolic scalar contractions are prohibitively big)
    dw1s, dw2s = sp.symbols("dw1_s dw2_s", real=True)
    u_dn = g * u_up
    grad = sp.zeros(4, 4)
    for m in range(4):
        for n in range(4):
            e = sp.diff(u_dn[n], coords[m]) \
                - sum(Gam[l][m][n] * u_dn[l] for l in range(4))
            grad[m, n] = e.subs(sp.Derivative(U, t), dU_expr)
    kin_sub = {sp.Derivative(w1, t): dw1s, sp.Derivative(w2, t): dw2s}
    kin_args = args + (dw1s, dw2s)
    grad_f = sp.lambdify(kin_args, grad.subs(kin_sub).subs(subs_x0),
                         "numpy")
    g_f = sp.lambdify(args, g.subs(subs_x0), "numpy")
    ginv_f = sp.lambdify(args, ginv.subs(subs_x0), "numpy")
    u_up_f = sp.lambdify(args, list(u_up.subs(subs_x0)), "numpy")

    def _u(state):
        H11, H12, H22 = state[0], state[1], state[2]
        W1, W2 = state[9], state[10]
        return float(np.sqrt(1 + H11 * W1 ** 2 + 2 * H12 * W1 * W2
                             + H22 * W2 ** 2))

    def rhs(state, w):
        a = (*state[:11], _u(state), w)
        return np.linalg.solve(np.array(Amat_f(*a), dtype=float),
                               np.array(bvec_f(*a), dtype=float))

    def constraints(state, w):
        return np.array(con_f(*state[:11], _u(state), w), dtype=float)

    def kinematics(state, dw1, dw2, w):
        a = (*state[:11], _u(state), w)
        gr = np.array(grad_f(*a, dw1, dw2), dtype=float)
        gm = np.array(g_f(*a), dtype=float)
        gi = np.array(ginv_f(*a), dtype=float)
        uu = np.array(u_up_f(*a), dtype=float)
        ud = gm @ uu
        hmix = np.eye(4) + np.outer(uu, ud)
        h_dn = gm + np.outer(ud, ud)
        V = np.einsum("ma,nb,mn->ab", hmix, hmix, gr)
        theta = float(np.einsum("mn,mn->", gi, gr))
        A_dn = np.einsum("m,mn->n", uu, gr)
        omega = (V - V.T) / 2
        sigma = (V + V.T) / 2 - theta / 3 * h_dn
        sq = lambda M: float(np.einsum("ac,bd,ab,cd->", gi, gi, M, M))
        A2 = float(np.einsum("ab,a,b->", gi, A_dn, A_dn))
        return np.array([theta, sq(sigma), sq(omega), A2])

    return rhs, constraints, kinematics


def rotating_initial_data(*, w: float, curv: int = 1, streams: int = 1,
                          rho0: float = 0.3,
                          w1_0: float = 0.03, w2_0: float = 0.04,
                          h: tuple = (1.0, 0.0, 1.3, 1.7)) -> np.ndarray:
    """Constraint-satisfying NON-VACUUM rotating initial data: rho0 > 0 is
    DECLARED (the vacuum branch, on which preservation is vacuous, is
    excluded); the OBLIQUE tilt (w1_0, w2_0 both nonzero) and the
    x-y-anisotropic metric (h11 != h22) make omega^2[u] > 0. Newton
    solves the expansion rates from the structurally nonzero constraints:
    single stream -- (dh11, dh12, dh22) from {E_tt, E_tx, E_ty};
    antipodal pair in type I -- dh11 from {E_tt} alone (the momentum
    constraints hold identically: G_ti = 0 for every homogeneous type-I
    metric and the pair cancels T_ti exactly)."""
    if rho0 <= 0:
        raise ValueError("rho0 must be > 0 (vacuum branch excluded)")
    _, constraints, _ = derive_rotating_system(curv, streams)
    h11, h12, h22, h33 = h
    pair_type_i = (curv == 0 and streams == 2)
    n_unk = 1 if pair_type_i else 3

    def state_of(v):
        if pair_type_i:
            dh11, dh12, dh22 = v[0], 0.05, 1.0
        else:
            dh11, dh12, dh22 = v
        dh33 = 0.9 * h33          # mean-expansion pin (free gauge choice)
        return np.array([h11, h12, h22, h33, dh11, dh12, dh22, dh33,
                         rho0, w1_0, w2_0])

    def active(c):
        return c[:1] if pair_type_i else c

    v = np.array([0.8, 0.05, 1.0])[:n_unk]
    for _ in range(80):
        c = active(constraints(state_of(v), w))
        if np.max(np.abs(c)) < 1e-13:
            break
        eps = 1e-7
        J = np.zeros((n_unk, n_unk))
        for j in range(n_unk):
            dv = v.copy()
            dv[j] += eps
            J[:, j] = (active(constraints(state_of(dv), w)) - c) / eps
        v = v - np.linalg.solve(J, c)
    state = state_of(v)
    resid = constraints(state, w)
    if np.max(np.abs(resid)) > 1e-10:
        raise RuntimeError(f"rotating initial data did not converge: {resid}")
    return state


@lru_cache(maxsize=1)
def type_i_single_stream_obstruction() -> dict:
    """KE-DYN obstruction theorem (exact): for EVERY homogeneous type-I
    metric in this class (arbitrary h11, h12, h22, h33 and rates) the
    Einstein tensor has G_tx = G_ty = 0 identically, so the momentum
    constraints of a SINGLE group-invariant tilted perfect fluid read
    T_tx = T_ty = 0, which forces zero tilt (for rho (1 + w) u^t != 0).
    A single-stream rotating development at Omega_k = 0 is therefore
    EXCLUDED; the antipodal pair evades the obstruction by cancelling
    T_ti exactly while each stream keeps its oblique tilt (and hence its
    vorticity)."""
    t, x = _T, _X
    h11 = sp.Function("h11", positive=True)(t)
    h12 = sp.Function("h12", real=True)(t)
    h22 = sp.Function("h22", positive=True)(t)
    h33 = sp.Function("h33", positive=True)(t)
    coords = (t, x, sp.Symbol("y"), sp.Symbol("z"))
    g = sp.Matrix([[-1, 0, 0, 0], [0, h11, h12, 0],
                   [0, h12, h22, 0], [0, 0, 0, h33]])
    ginv = g.inv()

    def chri(l, m, n):
        return sp.Rational(1, 2) * sum(
            ginv[l, k] * (sp.diff(g[k, m], coords[n])
                          + sp.diff(g[k, n], coords[m])
                          - sp.diff(g[m, n], coords[k])) for k in range(4))

    Gam = [[[sp.cancel(chri(l, m, n)) for n in range(4)]
            for m in range(4)] for l in range(4)]

    def ricci(m, n):
        term = sp.S.Zero
        for l in range(4):
            term += sp.diff(Gam[l][m][n], coords[l])
            term -= sp.diff(Gam[l][m][l], coords[n])
            for s in range(4):
                term += Gam[l][l][s] * Gam[s][m][n]
                term -= Gam[l][n][s] * Gam[s][m][l]
        return sp.cancel(sp.together(term))

    g_tx_zero = sp.simplify(ricci(0, 1)) == 0
    g_ty_zero = sp.simplify(ricci(0, 2)) == 0
    # (G_ti = R_ti here since g_ti = 0)
    return {
        "g_tx_identically_zero": bool(g_tx_zero),
        "g_ty_identically_zero": bool(g_ty_zero),
        "consequence": "momentum constraint forces T_ti = 0: a single"
                       " group-invariant tilted perfect fluid is EXCLUDED"
                       " at Omega_k = 0 (tilt flux cannot be supported);"
                       " the antipodal pair cancels T_ti exactly and is"
                       " NOT excluded",
        "obstruction_established": bool(g_tx_zero and g_ty_zero),
    }


def type_i_dynamical_irrotationality(*, w: float = 1.0 / 3.0,
                                     n_states: int = 50,
                                     seed: int = 20260711) -> dict:
    """KE-DYN second obstruction (structural identity): in type I the
    translational Killing symmetry plus the isotropic-pressure Euler
    equation conserve the DIRECTION of the tilt covector u_i
    (A_i = -[dp/dtau / (rho+p)] u^t u_i is parallel to u_i), so the
    bilinear u_x du_y/dt - u_y du_x/dt vanishes ALONG THE DERIVED
    DYNAMICS at every state -- not only on the constraint surface. A
    group-invariant perfect-fluid stream at Omega_k = 0 is therefore
    DYNAMICALLY irrotational for every w with rho + p != 0, even though
    oblique kinematic vorticity modes exist (KE-OBS): the dynamics never
    enters them. (At w = 0 the covector is conserved EXACTLY -- du_i = 0
    -- so the direction is trivially conserved; the normalization below
    detects that case instead of dividing round-off by round-off, an
    adversarial-lane fix, REV-R183.) Verified on random states for the
    antipodal-pair system."""
    rhs, _, _ = derive_rotating_system(0, 2)
    rng = np.random.default_rng(seed)
    worst = 0.0
    for _ in range(n_states):
        h11v, h22v, h33v = rng.uniform(0.5, 2.0, 3)
        h12v = rng.uniform(-0.3, 0.3)
        state = np.array([h11v, h12v, h22v, h33v,
                          *rng.uniform(-0.5, 1.5, 4),
                          rng.uniform(0.05, 0.8),
                          rng.uniform(-0.2, 0.2), rng.uniform(-0.2, 0.2)])
        d = rhs(state, w)
        dh11v, dh12v, dh22v = state[4], state[5], state[6]
        w1v, w2v = state[9], state[10]
        dw1v, dw2v = d[5], d[6]
        ux = h11v * w1v + h12v * w2v
        uy = h12v * w1v + h22v * w2v
        dux = dh11v * w1v + h11v * dw1v + dh12v * w2v + h12v * dw2v
        duy = dh12v * w1v + h12v * dw1v + dh22v * w2v + h22v * dw2v
        u_mag = float(np.hypot(ux, uy))
        du_mag = float(np.hypot(dux, duy))
        if du_mag <= 1e-12 * u_mag:
            continue    # covector exactly conserved (w = 0): trivial
        worst = max(worst, abs(ux * duy - uy * dux) / (u_mag * du_mag))
    return {
        "w": w,
        "max_rel_bilinear_residual": float(worst),
        "covector_direction_conserved": bool(worst < 1e-10),
        "analytic_reason": "translational Killing vectors + barotropic"
                           " Euler with spatially homogeneous pressure:"
                           " A_i is parallel to u_i, so the tilt covector"
                           " direction never rotates",
    }


def rotating_development(*, w: float, curv: int = 1, streams: int = 1,
                         t_span: float = 1.0) -> dict:
    """Integrate the rotating system; MONITOR (never impose) the three
    constraints; track omega^2[u] of the (+) stream along the
    trajectory."""
    rhs, constraints, kinematics = derive_rotating_system(curv, streams)
    state0 = rotating_initial_data(w=w, curv=curv, streams=streams)

    def f(_, s):
        d = rhs(s, w)
        return np.concatenate([s[4:8], d[:4], d[4:7]])

    ts = np.linspace(0.0, t_span, 81)
    sol = solve_ivp(f, (0.0, t_span), state0, t_eval=ts, rtol=1e-10,
                    atol=1e-12, method="RK45")
    if not sol.success:
        raise RuntimeError(sol.message)
    cons = np.array([constraints(sol.y[:, i], w) for i in range(len(ts))])
    om2 = []
    for i in range(len(ts)):
        d = rhs(sol.y[:, i], w)
        om2.append(kinematics(sol.y[:, i], d[4 + 1], d[4 + 2], w)[2])
    om2 = np.array(om2)
    vol0 = (state0[0] * state0[2] - state0[1] ** 2) * state0[3]
    volT = (sol.y[0, -1] * sol.y[2, -1] - sol.y[1, -1] ** 2) * sol.y[3, -1]
    return {
        "curvature_class": "bianchi_v" if curv == 1 else "bianchi_i",
        "streams": "single" if streams == 1 else "antipodal_pair",
        "w": w,
        "initial_constraint_residuals": [float(abs(c))
                                         for c in cons[0]],
        "max_constraint_residuals": [float(np.max(np.abs(cons[:, j])))
                                     for j in range(3)],
        "preserved_at_tolerance": bool(np.max(np.abs(cons)) < 1e-8),
        "nonvacuum_throughout": bool(np.min(sol.y[8]) > 0),
        "omega2_initial": float(om2[0]),
        "omega2_final": float(om2[-1]),
        "omega2_positive_throughout": bool(np.min(om2) > 0),
        "e_folds_volume": float(np.log(volT / vol0) / 3.0),
        "tilt_initial": [float(state0[9]), float(state0[10])],
        "tilt_final": [float(sol.y[9, -1]), float(sol.y[10, -1])],
    }


def aligned_uframe_trajectory() -> dict:
    """Item 10a: the R178 BV-DYN aligned dust trajectory re-expressed in
    u-frame variables -- verify the u-frame energy conservation
    d rho/d tau + Theta[u] (rho + p) = 0 numerically ALONG the trajectory
    (Theta[u] evaluated from the exact symbolic u-frame expansion of the
    aligned congruence; d tau = dt / cosh b along u)."""
    a1, a2, a3, b = _funcs()
    kin = frame_kinematics("bianchi_v", "aligned")
    th_args = (a1, a2, a3, b, sp.Derivative(a1, _T),
               sp.Derivative(a2, _T), sp.Derivative(a3, _T),
               sp.Derivative(b, _T))
    theta_f = sp.lambdify(th_args, kin["theta"].subs(_X, 0), "numpy")

    rhs_f, _, _, _ = derive_field_equations()
    w = 0.0
    state0 = constraint_initial_data(beta0=0.05, w=w)
    ts, ys = integrate_trajectory(state0, w=w, t_end=1.0, n_eval=201)
    a1v, a2v, da1, da2, rhov, bv = ys
    # b' along the trajectory from the derived RHS
    dbv = np.array([rhs_f(*ys[:, i], w)[3] for i in range(ys.shape[1])])
    th_u = theta_f(a1v, a2v, a2v, bv, da1, da2, da2, dbv)
    # u-frame energy conservation: u(rho) = cosh b * drho/dt (+ 0 spatial)
    drho = np.gradient(rhov, ts)
    resid = np.cosh(bv) * drho + th_u * rhov * (1 + w)
    rel = np.max(np.abs(resid[2:-2])) / np.max(np.abs(th_u * rhov))
    return {
        "u_frame_energy_conservation_max_rel_residual": float(rel),
        "holds_at_grid_accuracy": bool(rel < 5e-4),   # np.gradient is O(h^2)
        "theta_u_initial": float(th_u[0]),
        "theta_u_final": float(th_u[-1]),
    }


def radiation_center_manifold() -> dict:
    """The literature-anchored reading of the R178 radiation finding
    (adversarial-audit lane, REV-R179): at the gamma = 4/3 transcritical
    point the tilt drifts as d beta / d ln a = +(2/3) beta^2. Corroborate
    on the BV-DYN system (dust decays at the 3 gamma - 4 = -1 linear rate;
    radiation follows the quadratic law)."""
    out = {}
    for w, key in ((0.0, "dust"), (1.0 / 3.0, "radiation")):
        state0 = constraint_initial_data(beta0=0.05, w=w)
        ts, ys = integrate_trajectory(state0, w=w, t_end=2.0, n_eval=401)
        a2v, bv = ys[1], ys[5]
        ln_a = np.log(a2v)
        dbeta_dlna = np.gradient(bv, ln_a)
        if key == "radiation":
            law = (2.0 / 3.0) * bv ** 2
            mid = slice(50, -50)
            rel = np.max(np.abs(dbeta_dlna[mid] - law[mid])) \
                / np.max(law[mid])
            out[key] = {"max_rel_dev_from_two_thirds_beta_sq": float(rel),
                        "matches_quadratic_drift": bool(rel < 0.1)}
        else:
            rate = dbeta_dlna[50:-50] / bv[50:-50]
            out[key] = {"mean_linear_rate": float(np.mean(rate)),
                        "close_to_minus_one": bool(
                            abs(np.mean(rate) + 1.0) < 0.1)}
    return out


def king_ellis_dynamics_seal() -> dict:
    cons = uframe_conservation()
    ray = raychaudhuri_identity()
    rot_v = rotating_development(w=0.0, curv=1)
    rot_v_rad = rotating_development(w=1.0 / 3.0, curv=1)
    obstruction = type_i_single_stream_obstruction()
    irrot = type_i_dynamical_irrotationality()
    rot_i_pair = rotating_development(w=0.0, curv=0, streams=2)
    pair_irrotational = (abs(rot_i_pair["omega2_initial"]) < 1e-25
                         and abs(rot_i_pair["omega2_final"]) < 1e-25)

    ok = (cons["all_exact"]
          and all(ray["checks"].values())
          and obstruction["obstruction_established"]
          and irrot["covector_direction_conserved"]
          and all(r["preserved_at_tolerance"] and r["nonvacuum_throughout"]
                  for r in (rot_v, rot_v_rad, rot_i_pair))
          and rot_v["omega2_positive_throughout"]
          and rot_v_rad["omega2_positive_throughout"]
          and pair_irrotational)
    aligned = aligned_uframe_trajectory()
    cm = radiation_center_manifold()
    ok = (ok and aligned["holds_at_grid_accuracy"]
          and cm["radiation"]["matches_quadratic_drift"]
          and cm["dust"]["close_to_minus_one"])
    return {
        "seal": "egs3.king_ellis_dynamics",
        "theorem_id": "KE-DYN",
        "status": "PASS" if ok else "FAIL",
        "items_discharged": "8-10 of the ten-item rotating-congruence"
                            " program (t3_king_ellis.yaml)",
        "uframe_conservation": cons,
        "raychaudhuri_identity": ray,
        "rotating_development_bianchi_v_dust": rot_v,
        "rotating_development_bianchi_v_radiation": rot_v_rad,
        "type_i_single_stream_obstruction": obstruction,
        "type_i_dynamical_irrotationality": irrot,
        "rotating_development_bianchi_i_antipodal_pair": rot_i_pair,
        "aligned_uframe_trajectory": aligned,
        "radiation_center_manifold": cm,
        "net_verdict": (
            "a genuine rotating perfect-fluid development EXISTS at"
            " Omega_k > 0 (type V, single oblique tilt: omega^2[u] > 0"
            " maintained under monitored constraints); at Omega_k = 0 it"
            " is DOUBLY obstructed -- the single stream by the momentum"
            " constraint (G_ti = 0 identically) and the antipodal pair by"
            " dynamical irrotationality (Killing + Euler conserve the"
            " tilt-covector direction; omega^2 = 0 along the pair"
            " development to machine precision). The T3 lower-endpoint"
            " W^2 withdrawal is thereby upgraded from constraint-level to"
            " DYNAMICAL within this class: only inhomogeneous or"
            " non-perfect-fluid rotational modes remain"),
        "scope_not_claimed": (
            "the comparator W^2 is defined on the SLICE NORMAL, which"
            " remains hypersurface-orthogonal (Frobenius), so the T3"
            " lower-endpoint W^2 withdrawal STANDS and no value of the"
            " withdrawn W^2 = 4/100 is asserted; the type-V rotating"
            " development is matter-congruence vorticity at Omega_k > 0,"
            " NOT a lower-endpoint witness; re-attributing W^2 to the"
            " matter congruence is a registered interpretive question;"
            " NOT a Bianchi-class sky claim; no data or inference claim"),
    }


if __name__ == "__main__":
    import json
    print(json.dumps(king_ellis_dynamics_seal(), indent=2, default=str))
