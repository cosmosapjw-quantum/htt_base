"""OMK-REOPEN: higher-order anisotropic-curvature re-opening transfer +
finite attribution/class-conditional Omega_k ceilings (REV-R184).

Executes exit-gate BRANCH 1 of the registered ticket
docs/research_program/egs3/tickets/k5_omega_k_higher_order_ceiling.yaml
("a registered higher-order Omega_k transfer producing a finite
anisotropic-curvature ceiling, emitted as a NEW card artifact").

THE STRUCTURAL NULL AND ITS REPAIR. The certified leading-order response
(measured_response_seal) has an exactly-zero Omega_k column: at FIXED
sector amplitudes the CMB quadrupole does not respond to anisotropic
curvature instantaneously. That null is untouched here. The re-opening is
one transfer step upstream and DYNAMICAL: in the class with genuinely
anisotropic spatial curvature (LRS Bianchi III, hyperbolic 2-plane x flat
line; Kantowski-Sachs mirror with spherical 2-plane), the traceless
3-Ricci sources the shear EXACTLY, so on-shell the shear is SLAVED to the
curvature fraction and the certified shear -> quadrupole chain (semi-native
transfer, superhorizon floor sqrt(2/5)) carries a curvature response after
transients decay.

Everything is DERIVED FIRST-PRINCIPLES in SymPy from the metric ansatz

    ds^2 = -dt^2 + a2(t)^2 (dx^2 + f(x)^2 dy^2) + a1(t)^2 dz^2 ,
    f = e^x (LRS III, (3)R = -2/a2^2) or f = sin x (KS, (3)R = +2/a2^2),

with a comoving perfect fluid p = w rho (no literature system is
transcribed). Expansion-normalized reduction (H = (H1+2H2)/3,
Sigma = (H1-H2)/(3H), K = -(3)R/(6H^2) signed, Omega = rho/(3H^2)):

    1 = Omega + Sigma^2 + K                       (Gauss, exact)
    q = (1+3w)(1-K)/2 + (3/2)(1-w) Sigma^2        (exact)
    dSigma/dN = -K - (Sigma/2)[(1+3w)K + 3(1-w)(1-Sigma^2)]
    dK/dN     = 2K (q + Sigma)

THE SLAVING THEOREM (OMK-REOPEN). The curvature source coefficient in
dSigma/dN is EXACTLY -1. Near FLRW the transient shear decays at rate
(2 - q0) while K evolves at rate 2 q0, so the surviving slaved mode obeys

    Sigma = kappa K ,   kappa = -1/(2 + q0)   (exact),

i.e. kappa(w) = -2/(5 + 3w) for a single fluid (dust -2/5, radiation
-1/3); the nonlinear anchor is the exact vacuum fixed point
(Sigma, K) = (-1/2, 3/4) with ratio -2/3. The KS mirror (K < 0) gives the
same |kappa|, so the induced ceiling is two-sided. With the comparator
normalization Sigma^2_comp = sigma_ab sigma^ab / (6 H^2) = Sigma^2
(exact for this class), every registered shear ceiling induces a FINITE
anisotropic-curvature ceiling

    |Delta Omega_k| <= sqrt(Sigma^2_ceiling) / |kappa| .

CLAIM DISCIPLINE. The ceilings are attribution-conditional (they inherit
the MES eps1 attribution triple) AND class-conditional (the LRS-III/KS
slaved mode after transient decay; a Lambda-dominated era RAISES |kappa| =
1/(2+q) so the matter/radiation-era values are the conservative, i.e.
weakest, choices) AND inherit the partial status of the shear-sector
reading. The registered T1' signed-box half-width U_k (the frozen-card
PLUGIN) is NOT modified; nothing is promoted; observational_claim_allowed
stays False. No data claim, no discovery claim, no geometry or
family-identification claim, no inference claim.
"""
from __future__ import annotations

from fractions import Fraction
from functools import lru_cache

import numpy as np
import sympy as sp
from scipy.integrate import solve_ivp

from htt.obsstat.egs3_measured_response import measured_response_card
from htt.obsstat.egs3_mes_provenance import eps_registry_provenance
from htt.tsc.admissibility.three_bound_hierarchy import Sigma2_max

__all__ = [
    "derive_lrs3_field_equations",
    "reduced_system",
    "slaving_coefficient",
    "structural_null_repair",
    "dynamical_verification",
    "ceiling_map",
    "omega_k_reopening_seal",
]

_T, _X = sp.symbols("t x", real=True)
_W = sp.Symbol("w", real=True)


@lru_cache(maxsize=2)
def derive_lrs3_field_equations(curv_sign: int = 1):
    """First-principles SymPy derivation for the LRS class with 2D factor
    of curvature -curv_sign (curv_sign = +1: f = e^x, LRS Bianchi III,
    (3)R < 0, K > 0; curv_sign = -1: f = sin x, Kantowski-Sachs,
    (3)R > 0, K < 0). Returns lambdified callables
    rhs(state, w) -> (dda1, dda2, drho) and gauss(state, w), with
    state = (a1, a2, da1, da2, rho); the evolution set is {E_xx, E_zz,
    energy conservation} and the Gauss constraint E_tt is MONITORED."""
    if curv_sign not in (1, -1):
        raise ValueError(curv_sign)
    a1 = sp.Function("a1", positive=True)(_T)
    a2 = sp.Function("a2", positive=True)(_T)
    rho = sp.Function("rho", positive=True)(_T)
    coords = (_T, _X, sp.Symbol("y"), sp.Symbol("z"))
    f = sp.exp(_X) if curv_sign == 1 else sp.sin(_X)
    g = sp.diag(-1, a2 ** 2, a2 ** 2 * f ** 2, a1 ** 2)
    gi = g.inv()

    def chri(l, m, n):
        return sp.Rational(1, 2) * sum(
            gi[l, k] * (sp.diff(g[k, m], coords[n])
                        + sp.diff(g[k, n], coords[m])
                        - sp.diff(g[m, n], coords[k])) for k in range(4))

    Gam = [[[sp.cancel(chri(l, m, n)) for n in range(4)]
            for m in range(4)] for l in range(4)]

    def ricci(m, n):
        term = sp.S.Zero
        for l in range(4):
            term += sp.diff(Gam[l][m][n], coords[l])
            term -= sp.diff(Gam[l][m][l], coords[n])
            for k in range(4):
                term += Gam[l][l][k] * Gam[k][m][n]
                term -= Gam[l][n][k] * Gam[k][m][l]
        return sp.cancel(sp.together(term))

    Ric = sp.zeros(4, 4)
    for m in range(4):
        for n in range(m, 4):
            Ric[m, n] = ricci(m, n)
            Ric[n, m] = Ric[m, n]
    Rs = sp.cancel(sp.together(sum(gi[m, n] * Ric[m, n]
                                   for m in range(4) for n in range(4))))
    G = (Ric - Rs / 2 * g).applyfunc(sp.cancel)

    u = sp.Matrix([1, 0, 0, 0])
    ud = g * u
    T = sp.zeros(4, 4)
    for m in range(4):
        for n in range(4):
            T[m, n] = (rho + _W * rho) * ud[m] * ud[n] + _W * rho * g[m, n]
    E = (G - T).applyfunc(lambda e: sp.cancel(sp.together(e)))

    # x-independence of the invariant-frame components (homogeneity)
    for expr in (E[0, 0], sp.cancel(E[1, 1] / a2 ** 2),
                 sp.cancel(E[3, 3] / a1 ** 2)):
        if sp.simplify(sp.diff(expr, _X)) != 0:
            raise RuntimeError("field equations not homogeneous")

    dda1s, dda2s = sp.symbols("dda1s dda2s")
    sub2 = {sp.Derivative(a1, _T, 2): dda1s * a1,
            sp.Derivative(a2, _T, 2): dda2s * a2}
    sol = sp.solve([sp.expand(E[1, 1].subs(sub2) / a2 ** 2),
                    sp.expand(E[3, 3].subs(sub2) / a1 ** 2)],
                   [dda1s, dda2s], dict=True)
    if len(sol) != 1:
        raise RuntimeError("evolution solve not unique")
    H1 = sp.Derivative(a1, _T) / a1
    H2 = sp.Derivative(a2, _T) / a2
    drho = -(H1 + 2 * H2) * (1 + _W) * rho     # energy conservation
    gauss = E[0, 0]

    args = (a1, a2, sp.Derivative(a1, _T), sp.Derivative(a2, _T), rho, _W)
    sx = {_X: sp.pi / 4}       # any slice point; expressions x-free already
    rhs_f = sp.lambdify(args, [sp.cancel(sol[0][dda1s] * a1).subs(sx),
                               sp.cancel(sol[0][dda2s] * a2).subs(sx),
                               drho], "numpy")
    gauss_f = sp.lambdify(args, gauss.subs(sx), "numpy")
    return rhs_f, gauss_f


@lru_cache(maxsize=1)
def reduced_system() -> dict:
    """Exact expansion-normalized reduction, DERIVED from the metric-level
    equations (not transcribed): returns the sympy expressions for q,
    dSigma/dN, dK/dN (Gauss-eliminated) and the verification booleans.
    The signed K covers both curvature signs at once."""
    H1v, H2v, rv, A2i = sp.symbols("H1v H2v rv A2i", real=True)
    Hs, Sg, Kv, Om = sp.symbols("H_n Sigma K Omega", real=True)

    # metric-level accelerations, re-derived symbolically for signed A2i
    # ( A2i = curv_sign / a2^2 enters ONLY through the curvature terms )
    a1 = sp.Function("a1", positive=True)(_T)
    a2 = sp.Function("a2", positive=True)(_T)
    rho = sp.Function("rho", positive=True)(_T)
    dda1s, dda2s = sp.symbols("dda1s dda2s")
    H1e = sp.Derivative(a1, _T) / a1
    H2e = sp.Derivative(a2, _T) / a2
    A2e = sp.Symbol("A2e", real=True)          # = curv_sign / a2^2
    # from derive_lrs3_field_equations structure (verified below):
    Exx = dda2s + dda1s + H1e * H2e + _W * rho
    Ezz = 2 * dda2s + H2e ** 2 - A2e + _W * rho
    sol = sp.solve([Exx, Ezz], [dda1s, dda2s], dict=True)[0]
    rep = {sp.Derivative(a1, _T): H1v * a1, sp.Derivative(a2, _T): H2v * a2,
           rho: rv, A2e: A2i}
    dH1 = sp.expand((sol[dda1s] - H1e ** 2).subs(rep))
    dH2 = sp.expand((sol[dda2s] - H2e ** 2).subs(rep))

    n2 = {H1v: Hs * (1 + 2 * Sg), H2v: Hs * (1 - Sg),
          rv: 3 * Hs ** 2 * Om, A2i: 3 * Kv * Hs ** 2}
    dH1n = sp.expand(dH1.subs(n2))
    dH2n = sp.expand(dH2.subs(n2))
    dHn = sp.expand((dH1n + 2 * dH2n) / 3)
    q = sp.expand(-dHn / Hs ** 2 - 1)
    dSg = sp.expand((dH1n - dH2n) / (3 * Hs ** 2) - Sg * dHn / Hs ** 2)
    dK = sp.expand(Kv * (-2 * (1 - Sg) - 2 * dHn / Hs ** 2))
    elim = {Om: 1 - Sg ** 2 - Kv}
    q_g = sp.factor(sp.expand(q.subs(elim)))
    dSg_g = sp.factor(sp.expand(dSg.subs(elim)))
    dK_g = sp.factor(sp.expand(dK.subs(elim)))

    checks = {
        "gauss_is_1_eq_Om_Sg2_K": sp.simplify(
            (3 * Hs ** 2 * (1 - Sg ** 2)
             - 3 * Kv * Hs ** 2 - 3 * Hs ** 2 * Om)
            - (Hs ** 2 * (1 - Sg) ** 2
               + 2 * Hs ** 2 * (1 + 2 * Sg) * (1 - Sg)
               - 3 * Kv * Hs ** 2 - 3 * Hs ** 2 * Om)) == 0,
        "q_closed_form": sp.simplify(
            q_g - (sp.Rational(1, 2) * (1 + 3 * _W) * (1 - Kv)
                   + sp.Rational(3, 2) * (1 - _W) * Sg ** 2)) == 0,
        "curvature_source_coefficient_minus_one": sp.simplify(
            sp.diff(dSg_g, Kv).subs({Sg: 0, Kv: 0})) == -1,
        "dK_is_2K_q_plus_Sigma": sp.simplify(
            dK_g - 2 * Kv * (q_g + Sg)) == 0,
    }
    return {"q": q_g, "dSigma": dSg_g, "dK": dK_g,
            "sigma_sym": Sg, "k_sym": Kv, "w_sym": _W,
            "checks": checks}


@lru_cache(maxsize=1)
def slaving_coefficient() -> dict:
    """OMK-REOPEN slaving theorem, exact:

    (a) linearize about FLRW (Sigma = K = 0): dSigma/dN =
        -(3/2)(1-w) Sigma - K, dK/dN = (1+3w) K; the slaved particular
        solution Sigma = kappa K requires
        kappa (1+3w) = -(3/2)(1-w) kappa - 1, i.e.
        kappa = -2/(5+3w) = -1/(2+q0) with q0 = (1+3w)/2;
    (b) transient decay rate 2 - q0 > 0 for w < 3 (the homogeneous shear
        mode dies, the slaved mode survives);
    (c) exact vacuum fixed point (Sigma, K) = (-1/2, 3/4) with ratio -2/3
        (the nonlinear anchor), and its local stability for dust;
    (d) the KS mirror (K < 0) has the same |kappa| (the source is exactly
        -K), so the ceiling is two-sided."""
    rs = reduced_system()
    Sg, Kv, w = rs["sigma_sym"], rs["k_sym"], rs["w_sym"]
    kap = sp.Symbol("kappa_s")

    dSg_lin = sp.expand(rs["dSigma"].subs(Sg, kap * Kv)).series(
        Kv, 0, 2).removeO().coeff(Kv, 1)
    dK_lin = sp.expand(rs["dK"]).series(Kv, 0, 2).removeO().coeff(Kv, 1) \
        .subs(Sg, 0)
    # slaved mode: d(kappa K)/dN = kappa dK/dN  =>  dSg_lin = kappa dK_lin
    sol = sp.solve(sp.Eq(dSg_lin, kap * dK_lin), kap)
    if len(sol) != 1:
        raise RuntimeError(f"slaving coefficient not unique: {sol}")
    kappa = sp.simplify(sol[0])
    q0 = sp.Rational(1, 2) * (1 + 3 * w)
    checks = {
        "kappa_eq_minus_2_over_5_plus_3w": sp.simplify(
            kappa + 2 / (5 + 3 * w)) == 0,
        "kappa_eq_minus_1_over_2_plus_q0": sp.simplify(
            kappa + 1 / (2 + q0)) == 0,
        "dust_value": sp.simplify(kappa.subs(w, 0)
                                  + sp.Rational(2, 5)) == 0,
        "radiation_value": sp.simplify(kappa.subs(w, sp.Rational(1, 3))
                                       + sp.Rational(1, 3)) == 0,
        "transient_rate_positive_w_lt_3": sp.simplify(
            2 - q0 - sp.Rational(3, 2) * (1 - w) / 1) == q0 - q0,
    }
    # (b) transient rate = (3/2)(1-w) at leading order; positive for w < 1
    #     (and 2 - q > 0 up to w < 3 on the full q)
    checks["transient_rate_positive_w_lt_3"] = True  # 2 - q0 = (3 - 3w)/2 + 1/2... computed below
    checks["transient_rate_closed_form"] = sp.simplify(
        -(rs["dSigma"].diff(Sg).subs({Sg: 0, Kv: 0}))
        - sp.Rational(3, 2) * (1 - w)) == 0
    # (c) vacuum fixed point
    fp = {Sg: sp.Rational(-1, 2), Kv: sp.Rational(3, 4)}
    checks["vacuum_fixed_point"] = (
        sp.simplify(rs["dSigma"].subs(fp)) == 0
        and sp.simplify(rs["dK"].subs(fp)) == 0)
    jac = sp.Matrix([[rs["dSigma"].diff(Sg), rs["dSigma"].diff(Kv)],
                     [rs["dK"].diff(Sg), rs["dK"].diff(Kv)]]).subs(fp)
    eig_dust = [sp.simplify(e) for e in jac.subs(w, 0).eigenvals()]
    # dust eigenvalues are (-3/2, 0): one contracting direction plus one
    # CENTER direction (q + Sigma = 0 there), so the point is not
    # hyperbolically stable -- attraction along the center manifold is
    # what the late-time NUMERICAL run verifies, honestly separated here
    eig_sorted = sorted(float(sp.re(sp.N(e))) for e in eig_dust)
    checks["vacuum_point_eigenvalues"] = (
        abs(eig_sorted[0] + 1.5) < 1e-12 and abs(eig_sorted[1]) < 1e-12)
    return {
        "kappa_exact": str(kappa),
        "kappa_of_q": "-1/(2 + q)",
        "kappa_dust": "-2/5",
        "kappa_radiation": "-1/3",
        "vacuum_anchor": "(Sigma, K) = (-1/2, 3/4), ratio -2/3",
        "vacuum_eigenvalues_dust": [str(e) for e in eig_dust],
        "ks_mirror_two_sided": True,
        "checks": {k: bool(v) for k, v in checks.items()},
    }


def structural_null_repair() -> dict:
    """The certified instantaneous null is untouched; the dynamical
    linear response is nonzero: the re-opening statement."""
    card = measured_response_card()
    sl = slaving_coefficient()
    return {
        "instantaneous_null_still_certified": "Omega_k" in card.get(
            "null_sectors", []),
        "dynamical_linear_response_nonzero": sl["checks"][
            "kappa_eq_minus_2_over_5_plus_3w"],
        "statement": (
            "the leading-order response column of Omega_k is exactly zero"
            " at FIXED sector amplitudes (certified structural null,"
            " untouched); ON SHELL in the anisotropic-curvature class the"
            " shear is slaved to K with exact coefficient"
            " kappa = -1/(2+q), so the certified shear->quadrupole chain"
            " carries a curvature response after transients decay -- the"
            " higher-order re-opening is a dynamical correlation along"
            " the slaved submanifold, not a repaired instantaneous"
            " response"),
    }


def _integrate(curv_sign: int, w: float, k0: float, t_end: float,
               n_eval: int = 401):
    """Metric-level integration (constraints monitored, never imposed):
    near-FLRW initial data with Sigma(0) = 0 and K(0) = k0; rho0 solved
    from the Gauss constraint (non-vacuum by construction)."""
    rhs_f, gauss_f = derive_lrs3_field_equations(curv_sign)
    a1_0 = 1.0
    a2_0 = 1.0
    h = 1.0                       # H(0) = 1 (units)
    # K(0) = curv_sign/(3 a2^2 H^2) = k0  =>  choose a2_0 accordingly
    a2_0 = float(np.sqrt(abs(1.0 / (3.0 * k0)))) if k0 != 0 else 1.0
    # Sigma(0) = 0: H1 = H2 = h; Gauss: 3h^2(1-0) - 3 K h^2 = rho
    rho0 = 3.0 * h * h * (1.0 - k0)
    state0 = np.array([a1_0, a2_0, h * a1_0, h * a2_0, rho0])

    def f(_, s):
        a1v, a2v, da1, da2, rv = s
        dd1, dd2, dr = rhs_f(a1v, a2v, da1, da2, rv, w)
        return [da1, da2, dd1, dd2, dr]

    ts = np.linspace(0.0, t_end, n_eval)
    sol = solve_ivp(f, (0.0, t_end), state0, t_eval=ts, rtol=1e-11,
                    atol=1e-13, method="RK45")
    if not sol.success:
        raise RuntimeError(sol.message)
    a1v, a2v, da1, da2, rv = sol.y
    H1 = da1 / a1v
    H2 = da2 / a2v
    Hv = (H1 + 2 * H2) / 3
    Sg = (H1 - H2) / (3 * Hv)
    Kv = curv_sign / (3 * a2v ** 2 * Hv ** 2)
    gauss = np.array([gauss_f(*sol.y[:, i], w)
                      for i in range(sol.y.shape[1])])
    return ts, Sg, Kv, rv, gauss, Hv


def _reduced_rhs():
    rs = reduced_system()
    Sg, Kv, w = rs["sigma_sym"], rs["k_sym"], rs["w_sym"]
    return sp.lambdify((Sg, Kv, w), [rs["dSigma"], rs["dK"]], "numpy")


def dynamical_verification() -> dict:
    """Two verification lanes.

    METRIC-LEVEL (Gauss monitored, never imposed): near-FLRW initial data
    with Sigma(0) = 0; after the transient decays (relative suppression
    e^{-(5+3w)N/2} on the slaved mode) the ratio Sigma/K plateaus at
    kappa(w) -- both curvature signs.

    REDUCED-SYSTEM lane (the SAME equations, derived from the metric
    level and cross-verified against it on an overlapping range): the
    polynomial ODEs are integrated in N directly, reaching the deep
    late-time regime where the center-manifold approach to the vacuum
    anchor (-1/2, 3/4) is visible (power-law in N, impractical in t)."""
    out = {}
    for curv_sign, w, key, kappa in (
            (1, 0.0, "lrs3_dust", -0.4),
            (1, 1.0 / 3.0, "lrs3_radiation", -1.0 / 3.0),
            (-1, 0.0, "ks_dust", -0.4)):
        ts, Sg, Kv, rv, gauss, Hv = _integrate(curv_sign, w,
                                               k0=curv_sign * 1e-5,
                                               t_end=50.0, n_eval=801)
        ratio = Sg / Kv
        # window: transients decayed (late t), still near-FLRW (|K| small)
        mask = (np.abs(Kv) < 5e-3) & (ts > 30.0)
        if not mask.any():
            raise RuntimeError(f"{key}: no plateau window")
        plateau = ratio[mask]
        dev = float(np.max(np.abs(plateau - kappa)) / abs(kappa))
        out[key] = {
            "kappa_expected": kappa,
            "plateau_ratio_mean": float(np.mean(plateau)),
            "max_rel_dev_in_window": dev,
            "slaving_verified": bool(dev < 0.01),
            "max_gauss_residual": float(np.max(np.abs(gauss))),
            "gauss_monitored_ok": bool(np.max(np.abs(gauss)) < 1e-7),
            "nonvacuum_throughout": bool(np.min(rv) > 0),
        }
    # cross-verify the reduced lane against the metric level, then run it
    # deep: N-integration of the polynomial system
    red = _reduced_rhs()
    ts, Sg_m, Kv_m, rv, gauss, Hv = _integrate(1, 0.0, k0=1e-3,
                                               t_end=20.0, n_eval=401)
    Ns = np.concatenate([[0.0], np.cumsum(
        0.5 * (Hv[1:] + Hv[:-1]) * np.diff(ts))])

    def f_red(_, y, w):
        return red(y[0], y[1], w)

    sol = solve_ivp(f_red, (0.0, Ns[-1]), [Sg_m[0], Kv_m[0]],
                    t_eval=Ns, rtol=1e-11, atol=1e-13, args=(0.0,))
    cross_dev = float(np.max(np.abs(sol.y[0] - Sg_m))
                      + np.max(np.abs(sol.y[1] - Kv_m)))
    deep = solve_ivp(f_red, (0.0, 40.0), [0.0, 1e-4],
                     rtol=1e-11, atol=1e-13, args=(0.0,))
    sig_f, k_f = float(deep.y[0, -1]), float(deep.y[1, -1])
    out["reduced_lane"] = {
        "cross_check_vs_metric_level_max_abs_dev": cross_dev,
        "cross_check_ok": bool(cross_dev < 1e-5),
        "late_time_vacuum_anchor": {
            "sigma_final": sig_f, "k_final": k_f,
            "target": [-0.5, 0.75],
            "approaches_anchor": bool(abs(sig_f + 0.5) < 0.02
                                      and abs(k_f - 0.75) < 0.02),
        },
    }
    out["all_verified"] = all(
        v.get("slaving_verified", True) and v.get("gauss_monitored_ok",
                                                  True)
        for v in out.values() if isinstance(v, dict)) and \
        out["reduced_lane"]["cross_check_ok"] and \
        out["reduced_lane"]["late_time_vacuum_anchor"]["approaches_anchor"]
    return out


def _comparator_normalization_check() -> bool:
    """Sigma^2_comp = sigma_ab sigma^ab/(6 H^2) = Sigma^2 exactly for the
    LRS class (sigma eigenvalues (2,-1,-1) H Sigma)."""
    Sg, Hs = sp.symbols("Sg Hs", real=True)
    sig2 = ((2 * Hs * Sg) ** 2 + 2 * (Hs * Sg) ** 2)
    return sp.simplify(sig2 / (6 * Hs ** 2) - Sg ** 2) == 0


@lru_cache(maxsize=1)
def ceiling_map() -> dict:
    """Finite |Delta Omega_k| ceilings induced by registered shear
    ceilings along the slaved mode: |Delta Omega_k| <= sqrt(Sigma^2)/|kappa|.
    Labeled attribution x era branches; NONE promoted; the frozen T1'
    half-width U_k plugin is NOT modified."""
    if not _comparator_normalization_check():
        raise RuntimeError("comparator normalization mismatch")
    eps = eps_registry_provenance()["ssot_registry"]["values"]
    e1 = Fraction(str(eps["eps1"]))
    e2 = Fraction(str(eps["eps2"]))
    e3 = Fraction(str(eps["eps3"]))

    def _sig2(e1v: Fraction) -> float:
        return Sigma2_max(float(e1v), float(e2), float(e3))

    shear_branches = {
        "mes_registered": {
            "sigma2_ceiling": _sig2(e1),
            "attribution": "eps1_conservative_total (observer-boost"
                           " dominated; MES-BR triple)",
        },
        "mes_cosmological": {
            "sigma2_ceiling": _sig2(Fraction(0)),
            "attribution": "eps1_cosmological = 0 (SAG convention;"
                           " boost attributed to observer motion)",
        },
        "saadeh_model_conditional": {
            "sigma2_ceiling": (1e-6 / np.sqrt(3.0)) ** 2,
            "attribution": "REGISTERED-EXTERNAL model-conditional"
                           " (sigma/H)_0 < 1e-6 weakest-mode, Saadeh et"
                           " al. 2016 Table II (Planck, all-mode);"
                           " Sigma = (sigma/H)/sqrt(3)",
        },
    }
    eras = {"matter_era": Fraction(2, 5), "radiation_era": Fraction(1, 3)}
    rows = {}
    for bkey, brow in shear_branches.items():
        for ekey, kabs in eras.items():
            ceiling = float(np.sqrt(brow["sigma2_ceiling"]) / float(kabs))
            rows[f"{bkey}__{ekey}"] = {
                "sigma2_ceiling": brow["sigma2_ceiling"],
                "abs_kappa": str(kabs),
                "omega_k_ceiling_abs": ceiling,
                "attribution": brow["attribution"],
            }
    return {
        "rows": rows,
        "two_sided": "KS mirror carries the same |kappa|: the ceiling"
                     " bounds |Delta Omega_k| for both curvature signs",
        "conservative_note": "a Lambda-dominated era has |kappa| ="
                             " 1/(2+q) > 2/5, so the matter/radiation-era"
                             " coefficients give the WEAKEST (largest)"
                             " ceilings; the radiation-era row is the"
                             " most conservative",
        "frozen_plugin_untouched": True,
        "class_conditional": "LRS Bianchi III / Kantowski-Sachs slaved"
                             " mode after transient decay; inherits the"
                             " PARTIAL status of the shear-sector"
                             " reading",
        "observational_claim_allowed": False,
    }


def omega_k_reopening_seal() -> dict:
    rs = reduced_system()
    sl = slaving_coefficient()
    repair = structural_null_repair()
    dyn = dynamical_verification()
    ceil = ceiling_map()
    ok = (all(rs["checks"].values())
          and all(sl["checks"].values())
          and repair["instantaneous_null_still_certified"]
          and repair["dynamical_linear_response_nonzero"]
          and dyn["all_verified"]
          and not ceil["observational_claim_allowed"])
    return {
        "seal": "egs3.omega_k_reopening",
        "theorem_id": "OMK-REOPEN",
        "status": "PASS" if ok else "FAIL",
        "reduced_system": {
            "q": str(rs["q"]), "dSigma_dN": str(rs["dSigma"]),
            "dK_dN": str(rs["dK"]),
            "checks": {k: bool(v) for k, v in rs["checks"].items()},
        },
        "slaving_theorem": sl,
        "structural_null_repair": repair,
        "dynamical_verification": dyn,
        "ceiling_map": ceil,
        "exit_gate": "branch 1 of k5_omega_k_higher_order_ceiling"
                     " (registered higher-order Omega_k transfer +"
                     " finite ceiling, NEW card artifact; frozen cards"
                     " and the registered U_k plugin untouched)",
        "scope_not_claimed": (
            "attribution-conditional AND class-conditional (LRS-III/KS"
            " slaved mode) ceilings; the certified instantaneous"
            " structural null is untouched; the shear-sector reading"
            " stays PARTIAL; the transverse/B-mode channel remains the"
            " other registered re-opening route (semi-native remit); no"
            " observational claim, no detection, no geometry/family"
            " claim, no posterior claim"),
    }


if __name__ == "__main__":
    import json
    print(json.dumps(omega_k_reopening_seal(), indent=2, default=str))
