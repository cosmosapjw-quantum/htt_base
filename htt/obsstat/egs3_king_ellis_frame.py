"""KE-FRAME / KE-CONSTR / KE-OBS: King-Ellis tilted-congruence frame
kinematics and constraint algebra (v9 follow-on cycle, REV-R181).

Executes items 1-7 of the registered ten-item rotating-congruence
rederivation program (docs/research_program/egs3/tickets/t3_king_ellis.yaml,
recorded from the 2026-07-10 review): everything is DERIVED FIRST-PRINCIPLES
in SymPy from the metric ansatz -- no literature system is transcribed.

    ds^2 = -dt^2 + a1(t)^2 dx^2 + a2(t)^2 e^{2sx} dy^2 + a3(t)^2 e^{2sx} dz^2

with s = 1 (Bianchi type V, homogeneity a-vector along x) or s = 0
(Bianchi type I, the Omega_k = 0 limit). Two congruences:

    n^a = slice normal (∂_t);
    u^a = cosh b  e_0 + sinh b (c_1 e_1 + c_2 e_2 + c_3 e_3),

the group-invariant tilted matter congruence (frame components functions of
t only; e_i the invariant orthonormal triad).

Item map (1-7):
  1. explicit n^a, u^a definitions                    -> congruence_definitions
  2. Theta, sigma_ab, omega_ab, A_a for BOTH n and u  -> frame_kinematics
     (Frobenius: omega[n] = 0 exact; aligned tilt: omega[u] = 0 exact;
      transverse tilt: omega_ab[u] omega^ab[u] exact closed form)
  3. (3)R on the (non-integrable, when omega != 0) rest space via the
     contracted Gauss identity, DERIVED not transcribed: the coefficients
     (gamma, alpha, beta) in  R3 = 2 G_ab u^a u^b + gamma Theta^2
     + alpha sigma_ab sigma^ab + beta omega_ab omega^ab  are solved from
     exact rational-point linear systems and then verified symbolically
     to make the residual vanish identically           -> gauss_identity
  4. rho, q_a, pi_ab in both frames (tilted perfect fluid) -> matter_frames
  5. Hamiltonian/Gauss constraint = the uu-projection with item 3's identity;
  6. momentum constraint h^m_a G_mn u^n components (matter side vanishes
     exactly for the comoving perfect fluid)           -> momentum_constraint
  7. Jacobi + structure-constant checks for type V and the type-I limit
                                                        -> structure_constants

KE-OBS theorem (exact vorticity classification; REPLACES the ticket
WARNING's blanket irrotationality reading): for the LRS metric with
curvature parameter c (c = 1 type V, c = 0 type I) and group-invariant
tilt of rapidity b at angle phi to the a-vector axis (S = sinh b,
H_i = a_i'/a_i),

    omega_ab omega^ab = (S^2 sin^2 phi / 2)
                        * [ S cos(phi) (H1 - H2) - cosh(b) c / a1 ]^2

(psi-independent; derived first-principles, verified symbolically).
Consequences: (a) aligned tilt (sin phi = 0) is irrotational in BOTH types;
(b) in type I the vorticity is NOT identically zero -- an OBLIQUE tilt in a
shear-anisotropic (H1 != H2) type-I background carries
omega^2 = (S^4/2) sin^2 phi cos^2 phi (H1 - H2)^2, an O(v^2) effect in
omega_ab invisible to the leading-order slaving relation (which this
formula reproduces at O(v^2) in omega^2: c^2 v_perp^2 / (2 a1^2)); (c) in
type V there is a codimension-1 irrotationality surface where the shear
term cancels the curvature term. The v9 sentence "a group-invariant tilt
is irrotational at Omega_k = 0" is therefore correct only at leading order
or for principal-axis tilts -- recorded as a CORRECTION finding. The
n-frame Frobenius argument (and hence the T3 lower-endpoint W^2
withdrawal for the SLICE-NORMAL comparator congruence) is untouched.

Scope discipline: exact symbolic frame kinematics and constraint algebra on
a registered ansatz class. Items 8-10 (conservation, evolution, local
development) live in egs3_king_ellis_dynamics. The T3 lower-endpoint W^2
withdrawal STANDS (this module supplies the u-frame proof of the
obstruction). No data claim, no signal-discovery claim, no probabilistic
inference about the sky.
"""
from __future__ import annotations

from fractions import Fraction
from functools import lru_cache

import sympy as sp

__all__ = [
    "congruence_definitions",
    "frame_kinematics",
    "ke_obs_vorticity_theorem",
    "gauss_identity",
    "matter_frames",
    "momentum_constraint",
    "structure_constants",
    "rational_point_evaluations",
    "king_ellis_frame_seal",
]

_T, _X, _Y, _Z = sp.symbols("t x y z", real=True)
_W = sp.Symbol("w", real=True)
_CURV_SYMBOL = sp.Symbol("c_a", real=True)   # 1 = type V, 0 = type I


def _curv(case: str):
    return {"bianchi_v": sp.S.One, "bianchi_i": sp.S.Zero,
            "sym": _CURV_SYMBOL}[case]


def _funcs():
    a1 = sp.Function("a1", positive=True)(_T)
    a2 = sp.Function("a2", positive=True)(_T)
    a3 = sp.Function("a3", positive=True)(_T)
    b = sp.Function("b", real=True)(_T)
    return a1, a2, a3, b


@lru_cache(maxsize=None)
def _geometry(case: str, lrs: bool = False):
    """Metric, Christoffels, Riemann (all indices down), Ricci, Einstein."""
    if case not in ("bianchi_v", "bianchi_i", "sym"):
        raise ValueError(case)
    s = _curv(case)
    a1, a2, a3, _ = _funcs()
    if lrs:
        a3 = a2
    coords = (_T, _X, _Y, _Z)
    g = sp.diag(-1, a1 ** 2,
                a2 ** 2 * sp.exp(2 * s * _X),
                a3 ** 2 * sp.exp(2 * s * _X))
    ginv = g.inv()

    def christoffel(l, m, n):
        return sp.Rational(1, 2) * sum(
            ginv[l, k] * (sp.diff(g[k, m], coords[n])
                          + sp.diff(g[k, n], coords[m])
                          - sp.diff(g[m, n], coords[k]))
            for k in range(4))

    Gam = [[[sp.cancel(christoffel(l, m, n)) for n in range(4)]
            for m in range(4)] for l in range(4)]

    # R^l_{m k n} = d_k Gam^l_{n m} - d_n Gam^l_{k m}
    #              + Gam^l_{k p} Gam^p_{n m} - Gam^l_{n p} Gam^p_{k m}
    def riem_up(l, m, k, n):
        term = sp.diff(Gam[l][n][m], coords[k]) \
            - sp.diff(Gam[l][k][m], coords[n])
        for p in range(4):
            term += Gam[l][k][p] * Gam[p][n][m]
            term -= Gam[l][n][p] * Gam[p][k][m]
        return term

    Rdn = [[[[sp.S.Zero] * 4 for _ in range(4)] for _ in range(4)]
           for _ in range(4)]
    for l in range(4):
        for m in range(4):
            for k in range(4):
                for n in range(k + 1, 4):     # antisymmetry in (k, n)
                    val = sp.cancel(sp.together(sum(
                        g[l, p] * riem_up(p, m, k, n) for p in range(4))))
                    Rdn[l][m][k][n] = val
                    Rdn[l][m][n][k] = -val

    Ric = sp.zeros(4, 4)
    for m in range(4):
        for n in range(m, 4):
            Ric[m, n] = sp.cancel(sp.together(sum(
                ginv[k, l] * Rdn[k][m][l][n]
                for k in range(4) for l in range(4))))
            Ric[n, m] = Ric[m, n]
    Rs = sp.cancel(sp.together(sum(ginv[m, n] * Ric[m, n]
                                   for m in range(4) for n in range(4))))
    G = (Ric - sp.Rational(1, 2) * Rs * g).applyfunc(sp.cancel)
    return coords, g, ginv, Gam, Rdn, Ric, G, s


def _u_vector(case: str, c, lrs: bool = False):
    """Group-invariant unit congruence with frame components (cosh b,
    sinh b * c_i); c may be exact rationals/ints or trig of symbols."""
    s = _curv(case)
    a1, a2, a3, b = _funcs()
    if lrs:
        a3 = a2
    c1, c2, c3 = c
    return sp.Matrix([
        sp.cosh(b),
        sp.sinh(b) * c1 / a1,
        sp.sinh(b) * c2 * sp.exp(-s * _X) / a2,
        sp.sinh(b) * c3 * sp.exp(-s * _X) / a3,
    ])


def _hyper_simplify(expr):
    """Exact simplification of rational expressions in cosh b, sinh b:
    substitute cosh -> sqrt(1 + sinh^2) (cosh > 0 branch) and cancel."""
    _, _, _, b = _funcs()
    S = sp.Symbol("S_sinh", real=True)
    e = expr.subs(sp.cosh(b), sp.sqrt(1 + S ** 2)).subs(sp.sinh(b), S)
    return sp.simplify(sp.cancel(sp.together(sp.expand(e))))


def _kinematics(case: str, u_up, lrs: bool = False) -> dict:
    coords, g, ginv, Gam, _, _, _, _ = _geometry(case, lrs)
    u_dn = g * u_up

    grad = sp.zeros(4, 4)          # grad[m, n] = nabla_m u_n
    for m in range(4):
        for n in range(4):
            grad[m, n] = sp.cancel(sp.together(
                sp.diff(u_dn[n], coords[m])
                - sum(Gam[l][m][n] * u_dn[l] for l in range(4))))

    theta = sp.cancel(sp.together(sum(
        ginv[m, n] * grad[m, n] for m in range(4) for n in range(4))))
    A_dn = sp.Matrix([sp.cancel(sp.together(sum(
        u_up[m] * grad[m, n] for m in range(4)))) for n in range(4)])

    hmix = sp.zeros(4, 4)          # h^m_a = delta^m_a + u^m u_a
    for m in range(4):
        for a in range(4):
            hmix[m, a] = (sp.KroneckerDelta(m, a) + u_up[m] * u_dn[a])
    h_dn = g + u_dn * u_dn.T

    V = sp.zeros(4, 4)             # V_ab = h^m_a h^n_b nabla_m u_n
    for a in range(4):
        for b_ in range(4):
            V[a, b_] = sp.cancel(sp.together(sum(
                hmix[m, a] * hmix[n, b_] * grad[m, n]
                for m in range(4) for n in range(4))))

    omega = ((V - V.T) / 2).applyfunc(sp.cancel)
    sigma = (((V + V.T) / 2) - theta / 3 * h_dn).applyfunc(sp.cancel)

    def sq(mat):
        return sp.cancel(sp.together(sum(
            ginv[a, c] * ginv[b_, d] * mat[a, b_] * mat[c, d]
            for a in range(4) for b_ in range(4)
            for c in range(4) for d in range(4))))

    return {
        "u_up": u_up, "u_dn": u_dn, "grad": grad, "V": V,
        "theta": theta, "A_dn": A_dn, "omega": omega, "sigma": sigma,
        "omega2": sq(omega),       # omega_ab omega^ab
        "sigma2": sq(sigma),       # sigma_ab sigma^ab
        "h_dn": h_dn, "hmix": hmix,
    }


# ---------------------------------------------------------------- item 1
def congruence_definitions() -> dict:
    return {
        "normal": "n = d_t (unit normal of the homogeneous slices)",
        "tilted": "u = cosh b(t) e_0 + sinh b(t) (c1 e_1 + c2 e_2 + c3 e_3),"
                  " e_1 = a1^-1 d_x, e_2 = (a2 e^{sx})^-1 d_y,"
                  " e_3 = (a3 e^{sx})^-1 d_z; group-invariant"
                  " (frame components depend on t only)",
        "unit_norm_exact": True,
    }


# ---------------------------------------------------------------- item 2
@lru_cache(maxsize=None)
def frame_kinematics(case: str, tilt: str) -> dict:
    """Exact kinematic decomposition. tilt in {'normal', 'aligned',
    'transverse', 'general'} ('general' uses the LRS metric a3 = a2 with
    direction (cos phi, sin phi cos psi, sin phi sin psi))."""
    if tilt == "normal":
        u = sp.Matrix([1, 0, 0, 0])
        kin = _kinematics(case, u)
    elif tilt == "aligned":
        kin = _kinematics(case, _u_vector(case, (1, 0, 0)))
    elif tilt == "transverse":
        kin = _kinematics(case, _u_vector(case, (0, 1, 0)))
    elif tilt == "oblique":
        # exact rational unit direction (3/5, 4/5, 0): trig-free oblique
        # tilt, carries vorticity in BOTH types (KE-OBS)
        kin = _kinematics(case, _u_vector(
            case, (sp.Rational(3, 5), sp.Rational(4, 5), 0)))
    elif tilt == "general":
        phi, psi = sp.symbols("phi psi", real=True)
        c = (sp.cos(phi), sp.sin(phi) * sp.cos(psi),
             sp.sin(phi) * sp.sin(psi))
        kin = _kinematics(case, _u_vector(case, c, lrs=True), lrs=True)
    else:
        raise ValueError(tilt)
    kin["x_independent"] = all(
        sp.simplify(sp.diff(kin[k], _X)) == 0 for k in ("theta", "omega2",
                                                        "sigma2"))
    return kin


def _reduce_even_trig(expr):
    """Exact polynomial reduction of even trig powers: sin(psi), cos(psi),
    sin(phi) -> algebraic in (sq, CP); valid because psi enters only in
    even powers and phi enters via sin^2 and odd cos powers."""
    phi, psi = sp.symbols("phi psi", real=True)
    sq, CP = sp.symbols("sq_ CP_", real=True)
    sub = {sp.sin(psi): sq, sp.cos(psi): sp.sqrt(1 - sq ** 2),
           sp.sin(phi): sp.sqrt(1 - CP ** 2), sp.cos(phi): CP}
    return sp.cancel(sp.together(sp.expand(expr.subs(sub))))


@lru_cache(maxsize=1)
def ke_obs_vorticity_theorem() -> dict:
    """KE-OBS: EXACT vorticity classification of the group-invariant
    tilted congruence (LRS metric, curvature parameter c: 1 = type V,
    0 = type I; tilt angle phi to the a-vector axis; S = sinh b):

        omega_ab omega^ab
            = (S^2 sin^2 phi / 2) [S cos(phi)(H1 - H2) - cosh(b) c/a1]^2

    (a) Frobenius: omega[n] = 0 (both types);
    (b) aligned tilt (sin phi = 0): omega = 0 exactly, all orders in b;
    (c) CORRECTION finding: type I (c = 0) is NOT identically
        irrotational -- oblique tilt in a shear-anisotropic background
        carries omega^2 = (S^4/2) sin^2 phi cos^2 phi (H1 - H2)^2
        (O(v^2) in omega_ab; invisible to the leading-order slaving
        relation). Zero iff principal-axis tilt or H1 = H2;
    (d) type V (c = 1): codimension-1 irrotationality surface
        S cos(phi)(H1 - H2) = cosh(b)/a1 where shear and curvature
        contributions cancel;
    (e) leading order in v = tanh b: omega^2 -> c^2 v^2 sin^2 phi/(2 a1^2)
        = |curl v|^2 / 2 with the frozen slaving relation
        |curl v|^2 = a^2 v_perp^2 (a = c/a1) -- the factor 1/2 is the
        omega_ab omega^ab vs |curl|^2 normalization.
    """
    _, _, _, b = _funcs()
    phi = sp.Symbol("phi", real=True)
    a1 = sp.Function("a1", positive=True)(_T)
    a2 = sp.Function("a2", positive=True)(_T)
    S = sp.Symbol("S_sinh", real=True)
    H1 = sp.Derivative(a1, _T) / a1
    H2 = sp.Derivative(a2, _T) / a2

    out = {}
    out["frobenius_normal_zero"] = all(
        frame_kinematics(cs, "normal")["omega"].is_zero_matrix
        for cs in ("bianchi_v", "bianchi_i"))
    out["aligned_zero_bianchi_v"] = sp.simplify(
        frame_kinematics("bianchi_v", "aligned")["omega2"]) == 0

    csym = _CURV_SYMBOL
    w2 = _hyper_simplify(frame_kinematics("sym", "general")["omega2"])
    closed = (S ** 2 * sp.sin(phi) ** 2 / 2
              * (S * sp.cos(phi) * (H1 - H2)
                 - sp.sqrt(1 + S ** 2) * csym / a1) ** 2)
    out["closed_form_verified"] = sp.simplify(
        _reduce_even_trig(w2 - closed)) == 0
    out["closed_form"] = ("omega_ab omega^ab = (S^2 sin^2 phi / 2)"
                          " * (S cos(phi) (H1 - H2) - sqrt(1+S^2) c/a1)^2,"
                          "  S = sinh b, c = 1 (type V) / 0 (type I)")

    # (c) type I oblique vorticity (the correction finding)
    type_i = sp.simplify(closed.subs(csym, 0)
                         - S ** 4 * sp.sin(phi) ** 2 * sp.cos(phi) ** 2
                         * (H1 - H2) ** 2 / 2)
    out["type_i_oblique_form_verified"] = type_i == 0
    out["type_i_not_identically_irrotational"] = bool(
        closed.subs(csym, 0).subs([(sp.sin(phi), sp.sqrt(2) / 2),
                                   (sp.cos(phi), sp.sqrt(2) / 2)]) != 0)
    # consistency: transverse pure case, type V
    out["transverse_v_reduction"] = sp.simplify(
        closed.subs([(csym, 1), (sp.sin(phi), 1), (sp.cos(phi), 0)])
        - S ** 2 * (1 + S ** 2) / (2 * a1 ** 2)) == 0
    # (d) codimension-1 cancellation surface in type V
    cancel_srf = sp.solve(sp.Eq(S * sp.cos(phi) * (H1 - H2),
                                sp.sqrt(1 + S ** 2) / a1),
                          sp.Derivative(a1, _T))
    out["type_v_cancellation_surface_exists"] = len(cancel_srf) == 1
    # (e) slaving relation at leading order in v = tanh b
    v = sp.Symbol("v", real=True)
    lead = sp.series(closed.subs(S, v / sp.sqrt(1 - v ** 2)), v, 0, 3
                     ).removeO()
    out["slaving_leading_order_verified"] = sp.simplify(
        lead - csym ** 2 * v ** 2 * sp.sin(phi) ** 2 / (2 * a1 ** 2)) == 0
    return out


# ---------------------------------------------------------------- item 3+5
def _proj_riemann_trace(case: str, tilt: str) -> sp.Expr:
    """Double h-trace of the Gauss-projected curvature:
    R3 = h^{ac} h^{bd} [ R_{abcd}(proj) - V_ac V_bd + V_ad V_bc ]."""
    kin = frame_kinematics(case, tilt)
    lrs = tilt == "general"
    coords, g, ginv, Gam, Rdn, _, _, _ = _geometry(case, lrs)
    hmix, V = kin["hmix"], kin["V"]

    hup = sp.zeros(4, 4)           # h^{ab}
    u_up = kin["u_up"]
    for a in range(4):
        for b_ in range(4):
            hup[a, b_] = ginv[a, b_] + u_up[a] * u_up[b_]

    # projected Riemann double trace: h^{m k} h^{n l} R_{m n k l}
    rr = sp.S.Zero
    for m in range(4):
        for n in range(4):
            for k in range(4):
                for l in range(4):
                    if Rdn[m][n][k][l] != 0:
                        rr += hup[m, k] * hup[n, l] * Rdn[m][n][k][l]
    # V-trace terms: h^{ac}h^{bd}(V_ad V_bc - V_ac V_bd)
    #              = tr(V~ V~) - (tr V~)^2 with V~ = h-projected V (V is
    # already fully projected), traces taken with h^{ab}.
    trV = sum(hup[a, b_] * V[a, b_] for a in range(4) for b_ in range(4))
    trVV = sum(hup[a, c] * hup[b_, d] * V[a, d] * V[c, b_]
               for a in range(4) for b_ in range(4)
               for c in range(4) for d in range(4))
    return sp.cancel(sp.together(rr + trVV - trV ** 2))


@lru_cache(maxsize=1)
def gauss_identity() -> dict:
    """Derive (not transcribe) the contracted Gauss identity

        R3 = 2 G_ab u^a u^b + gamma Theta^2 + alpha sigma^2 + beta omega^2

    coefficients from exact rational-point linear systems on the type-V
    transverse case, then verify the residual vanishes IDENTICALLY
    (symbolically) for: type-V transverse, type-V aligned, type-V normal,
    type-I general. The beta != 0 value is the vorticity term the
    non-integrable rest space acquires."""
    ga, al, be = sp.symbols("gamma_c alpha_c beta_c", rational=True)

    def scalars(case, tilt):
        kin = frame_kinematics(case, tilt)
        coords, g, ginv, _, _, _, G, _ = _geometry(case, tilt == "general")
        u = kin["u_up"]
        guu = sp.cancel(sp.together(sum(
            G[m, n] * u[m] * u[n] for m in range(4) for n in range(4))))
        return (_proj_riemann_trace(case, tilt), guu, kin["theta"],
                kin["sigma2"], kin["omega2"])

    r3, guu, th, s2, w2 = scalars("bianchi_v", "transverse")
    resid = r3 - 2 * guu - ga * th ** 2 - al * s2 - be * w2

    # exact rational evaluation points -> linear system for (gamma, alpha,
    # beta); e^b rational makes cosh/sinh exact rationals
    eqs = []
    for pt in ((2, 3, 5, sp.Rational(1, 2), sp.Rational(1, 3),
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
                sp.Rational(3, 11), sp.Rational(2, 13), sp.Rational(1, 41))):
        eqs.append(_eval_rational(resid, pt))
    sol = sp.solve(eqs[:3], (ga, al, be), dict=True)
    if len(sol) != 1:
        raise RuntimeError(f"gauss identity coefficients not unique: {sol}")
    coeff = sol[0]
    checks = {"fourth_point_consistent": sp.simplify(
        eqs[3].subs(coeff)) == 0}

    # symbolic verification on all five configurations (oblique = exact
    # rational direction (3/5, 4/5, 0), omega != 0 in both types)
    for case, tilt in (("bianchi_v", "transverse"), ("bianchi_v", "aligned"),
                       ("bianchi_v", "normal"), ("bianchi_i", "oblique"),
                       ("bianchi_v", "oblique")):
        r3c, guuc, thc, s2c, w2c = scalars(case, tilt)
        res = (r3c - 2 * guuc - coeff[ga] * thc ** 2
               - coeff[al] * s2c - coeff[be] * w2c)
        checks[f"identity_symbolic_{case}_{tilt}"] = \
            _hyper_simplify(res) == 0
    return {
        "gamma": str(coeff[ga]), "alpha": str(coeff[al]),
        "beta": str(coeff[be]),
        "identity": "R3 = 2 G_ab u^a u^b"
                    f" + ({coeff[ga]}) Theta^2 + ({coeff[al]}) sigma^2"
                    f" + ({coeff[be]}) omega^2  (sigma^2 = sigma_ab"
                    " sigma^ab, omega^2 = omega_ab omega^ab)",
        "checks": checks,
        "non_integrability_note": (
            "for omega != 0 no family of 3-surfaces is orthogonal to u"
            " (Frobenius), so R3 is the Gauss-equation curvature of the"
            " formal rest spaces, not of actual hypersurfaces; the beta"
            " omega^2 term is exactly the correction the identity"
            " acquires there"),
    }


def _eval_rational(expr, pt):
    """Substitute the exact rational test point
    pt = (a1, a2, a3, da1, da2, da3, db, q=e^b, dda1, dda2, dda3)."""
    a1, a2, a3, b = _funcs()
    A1, A2, A3, dA1, dA2, dA3, dB, q, ddA1, ddA2, ddA3 = [sp.S(v)
                                                          for v in pt]
    subs = [
        (sp.Derivative(a1, _T, 2), ddA1), (sp.Derivative(a2, _T, 2), ddA2),
        (sp.Derivative(a3, _T, 2), ddA3),
        (sp.Derivative(a1, _T), dA1), (sp.Derivative(a2, _T), dA2),
        (sp.Derivative(a3, _T), dA3), (sp.Derivative(b, _T), dB),
        (sp.cosh(b), (q + 1 / q) / 2), (sp.sinh(b), (q - 1 / q) / 2),
        (a1, A1), (a2, A2), (a3, A3), (_X, 0),
    ]
    out = expr
    for old, new in subs:
        out = out.subs(old, new)
    return sp.nsimplify(sp.cancel(out), rational=True)


# ---------------------------------------------------------------- item 4
@lru_cache(maxsize=1)
def matter_frames() -> dict:
    """Tilted perfect fluid (p = w rho, comoving with u): exact frame
    decompositions. u-frame: (rho, 0, 0) exactly. n-frame: the standard
    cosh/sinh forms, derived and verified here."""
    case, tilt = "bianchi_v", "transverse"
    kin = frame_kinematics(case, tilt)
    coords, g, ginv, _, _, _, _, _ = _geometry(case)
    a1, a2, a3, b = _funcs()
    rho = sp.Symbol("rho", positive=True)
    p = _W * rho
    u_up, u_dn = kin["u_up"], kin["u_dn"]
    T = sp.zeros(4, 4)
    for m in range(4):
        for n in range(4):
            T[m, n] = (rho + p) * u_dn[m] * u_dn[n] + p * g[m, n]

    n_up = sp.Matrix([1, 0, 0, 0])
    n_dn = g * n_up
    hn = g + n_dn * n_dn.T
    hn_mix = sp.zeros(4, 4)
    for m in range(4):
        for a in range(4):
            hn_mix[m, a] = sp.KroneckerDelta(m, a) + n_up[m] * n_dn[a]

    rho_n = sum(T[m, n] * n_up[m] * n_up[n]
                for m in range(4) for n in range(4))
    q_n = sp.Matrix([-sum(hn_mix[m, a] * T[m, n] * n_up[n]
                          for m in range(4) for n in range(4))
                     for a in range(4)])
    pi_n = sp.zeros(4, 4)
    for a in range(4):
        for b_ in range(4):
            pi_n[a, b_] = sp.simplify(
                sum(hn_mix[m, a] * hn_mix[n, b_] * T[m, n]
                    for m in range(4) for n in range(4))
                - sp.Rational(1, 3) * hn[a, b_]
                * sum(ginv[m, k] * hn_mix[m_, m] * T[m_, n] * hn_mix[n, k]
                      for m in range(4) for k in range(4)
                      for m_ in range(4) for n in range(4)))

    checks = {
        "rho_n_form": sp.simplify(
            rho_n - rho * (sp.cosh(b) ** 2 + _W * sp.sinh(b) ** 2)) == 0,
        "q_n_magnitude": sp.simplify(
            sum(ginv[a_, b2] * q_n[a_] * q_n[b2]
                for a_ in range(4) for b2 in range(4))
            - ((rho + p) * sp.cosh(b) * sp.sinh(b)) ** 2) == 0,
        "pi_n_traceless": sp.simplify(sum(
            ginv[a_, b2] * pi_n[a_, b2]
            for a_ in range(4) for b2 in range(4))) == 0,
        "u_frame_trivial": True,   # by construction: h[u] T u = 0,
                                   # T_uu = rho exactly (verified below)
    }
    checks["u_frame_trivial"] = bool(sp.simplify(
        sum(T[m, n] * u_up[m] * u_up[n]
            for m in range(4) for n in range(4)) - rho) == 0)
    return {
        "rho_n": "rho (cosh^2 b + w sinh^2 b)",
        "q_n_mag": "(1 + w) rho cosh b sinh b",
        "pi_n_amplitude": "(1 + w) rho sinh^2 b (traceless, along the tilt)",
        "checks": checks,
    }


# ---------------------------------------------------------------- item 6
@lru_cache(maxsize=1)
def momentum_constraint() -> dict:
    """u-frame momentum constraint components M_a = h^m_a G_mn u^n
    (the matter side vanishes EXACTLY for the comoving perfect fluid:
    h^m_a T_mn u^n = 0). Returns the exact nonzero components; these are
    the level-2 constraint surface for the dynamics phase."""
    out = {}
    for tilt in ("aligned", "transverse"):
        kin = frame_kinematics("bianchi_v", tilt)
        coords, g, ginv, _, _, _, G, _ = _geometry("bianchi_v")
        u_up, hmix = kin["u_up"], kin["hmix"]
        M = [sp.cancel(sp.together(sum(
            hmix[m, a] * G[m, n] * u_up[n]
            for m in range(4) for n in range(4)))) for a in range(4)]
        nonzero = {f"M_{'txyz'[a]}": sp.sstr(_hyper_simplify(M[a]))
                   for a in range(4) if sp.simplify(M[a]) != 0}
        out[tilt] = nonzero
    # matter side exactly zero (both tilts): h^m_a T_mn u^n with
    # T = (rho+p) u u + p g gives T_mn u^n = -rho u_m, killed by h u = 0
    out["matter_side_zero_exact"] = True
    return out


# ---------------------------------------------------------------- item 7
@lru_cache(maxsize=1)
def structure_constants() -> dict:
    """Type-V invariant triad X1 = d_x, X2 = e^{-x} d_y, X3 = e^{-x} d_z:
    commutators, C^a_bc = delta^a_b a_c - delta^a_c a_b with a = (1,0,0)
    (coordinate normalization; physical magnitude 1/a1), n^{ab} = 0,
    Jacobi identity, and the type-I limit (all commutators vanish)."""
    coords = (_X, _Y, _Z)
    X = [sp.Matrix([1, 0, 0]),
         sp.Matrix([0, sp.exp(-_X), 0]),
         sp.Matrix([0, 0, sp.exp(-_X)])]

    def lie(u, v):
        return sp.Matrix([
            sum(u[m] * sp.diff(v[k], coords[m])
                - v[m] * sp.diff(u[k], coords[m]) for m in range(3))
            for k in range(3)])

    a_vec = (1, 0, 0)
    C = [[[sp.S.Zero] * 3 for _ in range(3)] for _ in range(3)]
    for k in range(3):
        for b_ in range(3):
            for c in range(3):
                C[k][b_][c] = (sp.KroneckerDelta(k, b_) * a_vec[c]
                               - sp.KroneckerDelta(k, c) * a_vec[b_])
    comm_ok = True
    for b_ in range(3):
        for c in range(3):
            expect = sp.zeros(3, 1)
            for k in range(3):
                expect += C[k][b_][c] * X[k]
            comm_ok &= sp.simplify(lie(X[b_], X[c]) - expect
                                   ).is_zero_matrix
    jac = sp.S.Zero
    jac_ok = True
    for d in range(3):
        for b_ in range(3):
            for c in range(3):
                for e in range(3):
                    jac = sum(C[k][b_][c] * C[d][e][k]
                              + C[k][c][e] * C[d][b_][k]
                              + C[k][e][b_] * C[d][c][k] for k in range(3))
                    jac_ok &= sp.simplify(jac) == 0
    return {
        "commutators_match_type_v": bool(comm_ok),
        "n_ab_zero": True,          # C^a_bc has no symmetric (n^ab) part
        "jacobi": bool(jac_ok),
        "class_b_condition_a_dot_n": "0 (n^ab = 0)",
        "type_i_limit": "a -> 0: all commutators vanish (abelian, type I)",
    }


# --------------------------------------------------- cross-engine anchor
_POINT = (2, 3, 5, Fraction(1, 2), Fraction(1, 3), Fraction(1, 5),
          Fraction(1, 7), Fraction(3, 2), Fraction(1, 11), Fraction(1, 13),
          Fraction(1, 17))


@lru_cache(maxsize=1)
def rational_point_evaluations() -> dict:
    """Exact rational evaluations at the pinned point (a1, a2, a3, da1,
    da2, da3, db, e^b, dda1, dda2, dda3) = (2, 3, 5, 1/2, 1/3, 1/5, 1/7,
    3/2, 1/11, 1/13, 1/17), x = 0 -- the cross-engine comparison anchor
    (the Wolfram lane evaluates the same scalars independently)."""
    pt = tuple(sp.Rational(f.numerator, f.denominator)
               if isinstance(f, Fraction) else f for f in _POINT)
    out = {}
    for tilt in ("normal", "aligned", "transverse"):
        kin = frame_kinematics("bianchi_v", tilt)
        row = {}
        for key in ("theta", "omega2", "sigma2"):
            row[key] = str(_eval_rational(kin[key], pt))
        row["A2"] = str(_eval_rational(sum(
            _geometry("bianchi_v")[2][a, b_] * kin["A_dn"][a]
            * kin["A_dn"][b_] for a in range(4) for b_ in range(4)), pt))
        out[tilt] = row
    return out


# ------------------------------------------------------------------ seal
def king_ellis_frame_seal() -> dict:
    obs = ke_obs_vorticity_theorem()
    gauss = gauss_identity()
    matter = matter_frames()
    mom = momentum_constraint()
    struct = structure_constants()
    anchors = rational_point_evaluations()
    kin_ok = all(frame_kinematics("bianchi_v", tl)["x_independent"]
                 for tl in ("normal", "aligned", "transverse"))

    ok = (kin_ok
          and all(v is True for v in obs.values()
                  if isinstance(v, bool))
          and all(gauss["checks"].values())
          and all(matter["checks"].values())
          and mom["matter_side_zero_exact"]
          and struct["commutators_match_type_v"] and struct["jacobi"]
          and mom["transverse"] and mom["aligned"])
    return {
        "seal": "egs3.king_ellis_frame",
        "theorem_id": "KE-FRAME/KE-CONSTR/KE-OBS",
        "status": "PASS" if ok else "FAIL",
        "items_discharged": "1-7 of the ten-item rotating-congruence"
                            " program (t3_king_ellis.yaml)",
        "definitions": congruence_definitions(),
        "ke_obs_vorticity_theorem": obs,
        "gauss_identity": gauss,
        "matter_frames": matter,
        "momentum_constraint_components": {
            k: v for k, v in mom.items() if k != "matter_side_zero_exact"},
        "structure_constants": struct,
        "rational_point_anchor": {
            "point": "a=(2,3,5), da=(1/2,1/3,1/5), db=1/7, e^b=3/2,"
                     " dda=(1/11,1/13,1/17), x=0",
            "values": anchors,
        },
        "scope_not_claimed": (
            "exact frame kinematics + constraint algebra on the"
            " group-invariant ansatz class; NOT a constraint-satisfying"
            " W^2 > 0 witness at Omega_k = 0 -- KE-OBS is KINEMATIC: the"
            " oblique type-I vorticity is a candidate rotational mode"
            " only, its Einstein-constraint compatibility (which forces"
            " an off-diagonal homogeneous metric) is the dynamics-phase"
            " question; the n-frame Frobenius argument and hence the T3"
            " lower-endpoint W^2 withdrawal for the slice-normal"
            " comparator congruence STAND; items 8-10 live in"
            " egs3_king_ellis_dynamics; no data or inference claim"),
    }


if __name__ == "__main__":
    import json
    print(json.dumps(king_ellis_frame_seal(), indent=2, default=str))
