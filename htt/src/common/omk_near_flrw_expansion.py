"""PR-131 near-FLRW symbolic expansion + singular-boundary map.

NAMED reduced system (expansion-normalized orthonormal LRS frame,
rev-r184 OMK-REOPEN conventions, single fluid with FIXED w):

    q         = (1+3w)(1-K)/2 + (3/2)(1-w) Sigma^2          (exact)
    dSigma/dN = -K - (Sigma/2)[(1+3w)K + 3(1-w)(1-Sigma^2)]
    dK/dN     = 2K(q + Sigma)

The Bianchi III branch carries K > 0 (hyperbolic 2-plane) and the
Kantowski-Sachs mirror K < 0 (spherical 2-plane); the signature is
absorbed into the sign of K — a separated class convention, never a
new coefficient.

Near the flat FLRW fixed point (Sigma = K = 0, q0 = (1+3w)/2) the
slaved mode obeys Sigma = kappa K + c2 K^2 + O(K^3) with EXACT
class-conditional asymptotic coefficients

    kappa = -2/(5+3w),
    c2    = -2(9w^2+18w+13) / ((3w+5)^2 (9w+7)),

derived by TWO independent symbolic paths (constraint-surface
invariance equation AND metric-level Einstein reduction) and confirmed
by an arbitrary-precision finite-difference plateau as K -> 0 under a
preregistered envelope. The singular/zero-denominator boundary map is
the exact resonance family n*lambda_K = lambda_Sigma at
w_n = -(2n+3)/(6n-3) plus the marginal boundaries w = -1/3 and w = 1;
the declared domain w in (-1/3, 1) OPEN contains none of them.

Class-conditional asymptotic coefficients at fixed q0(w) ONLY — never
a global equality over backgrounds, never a finite-ceiling recovery,
never an observational value of curvature or of shear.
roadmap_rescue_v1:C2.
"""
from __future__ import annotations

from fractions import Fraction
from typing import Mapping

import sympy as sp

SCHEMA_VERSION = "pr131.omk_near_flrw_expansion.v1"

W = sp.symbols("w")
DECLARED_DOMAIN = (Fraction(-1, 3), Fraction(1))   # open interval

KAPPA_EXACT = -2 / (3 * W + 5)
C2_EXACT = -2 * (9 * W ** 2 + 18 * W + 13) / ((3 * W + 5) ** 2
                                              * (9 * W + 7))
C3_EXACT = -2 * (81 * W ** 4 + 324 * W ** 3 + 594 * W ** 2 + 460 * W
                 + 141) / ((3 * W + 5) ** 3 * (5 * W + 3) * (9 * W + 7))

# claim-language prohibition (assembled so the ban's definition never
# trips the total negative scan over this module)
_FORBIDDEN_PHRASES = tuple(
    a + b for a, b in (
        ("for all", " q"), ("for every", " q"), ("independent", " of q"),
        ("six finite", " ceilings"), ("observational", " curvature"),
        ("observed", " shear"),
    )
)


class OmkNearFlrwError(ValueError):
    """Raised on any expansion/domain/claim violation (fail-closed)."""


# ---------------------------------------------------------------------------
# Path A: registered reduced system + invariance equation
# ---------------------------------------------------------------------------

def q_exact(S, K):
    return (1 + 3 * W) * (1 - K) / 2 + sp.Rational(3, 2) * (1 - W) * S ** 2


def f_sigma(S, K):
    return -K - (S / 2) * ((1 + 3 * W) * K
                           + 3 * (1 - W) * (1 - S ** 2))


def f_k(S, K):
    return 2 * K * (q_exact(S, K) + S)


def jacobian_at_flrw() -> dict:
    """Exact linearization at Sigma = K = 0."""
    S, K = sp.symbols("Sigma K")
    J = sp.Matrix([[sp.diff(f_sigma(S, K), S), sp.diff(f_sigma(S, K), K)],
                   [sp.diff(f_k(S, K), S), sp.diff(f_k(S, K), K)]])
    J0 = sp.simplify(J.subs({S: 0, K: 0}))
    lam_sigma = J0[0, 0]
    lam_k = J0[1, 1]
    if sp.simplify(lam_sigma + sp.Rational(3, 2) * (1 - W)) != 0:
        raise OmkNearFlrwError("lambda_Sigma drifted from -(3/2)(1-w)")
    if sp.simplify(lam_k - (1 + 3 * W)) != 0:
        raise OmkNearFlrwError("lambda_K drifted from 1+3w")
    if J0[1, 0] != 0:
        raise OmkNearFlrwError("K-row shear coupling must vanish at FLRW")
    if J0[0, 1] != -1:
        raise OmkNearFlrwError(
            "the traceless curvature source coefficient must be "
            "EXACTLY -1")
    return {"J": J0, "lambda_sigma": lam_sigma, "lambda_k": lam_k}


def invariance_coefficients(order: int = 3) -> dict:
    """Path A: solve the invariance equation
    dh/dK * F_K(h(K), K) = F_Sigma(h(K), K) for
    h(K) = kappa K + c2 K^2 + c3 K^3 exactly, order by order."""
    K = sp.symbols("K")
    names = sp.symbols("kappa c2 c3")[:order]
    h = sum(names[i] * K ** (i + 1) for i in range(order))
    resid = sp.expand(sp.diff(h, K) * f_k(h, K) - f_sigma(h, K))
    solution: dict = {}
    for n in range(1, order + 1):
        coeff = sp.expand(
            resid.subs(solution).series(K, 0, n + 1).removeO()
            .coeff(K, n))
        sol = sp.solve(sp.Eq(coeff, 0), names[n - 1])
        if len(sol) != 1:
            raise OmkNearFlrwError(f"order-{n} invariance not uniquely "
                                   "solvable")
        solution[names[n - 1]] = sp.simplify(sol[0])
        solution = {k: sp.simplify(v.subs(solution))
                    for k, v in solution.items()}
    kappa = sp.simplify(solution[names[0]])
    if sp.simplify(kappa - KAPPA_EXACT) != 0:
        raise OmkNearFlrwError("path-A kappa drifted from -2/(5+3w)")
    verify_kappa_candidate(kappa)   # the production invariance gate
    c2 = sp.simplify(solution[names[1]])
    if sp.simplify(c2 - C2_EXACT) != 0:
        raise OmkNearFlrwError("path-A c2 drifted from the registered form")
    out = {"kappa": kappa, "c2": c2}
    if order >= 3:
        c3 = sp.simplify(solution[names[2]])
        if sp.simplify(c3 - C3_EXACT) != 0:
            raise OmkNearFlrwError("path-A c3 drifted (envelope sizing)")
        out["c3"] = c3
    return out


def verify_kappa_candidate(candidate) -> None:
    """The order-K invariance kill: a candidate slaving coefficient
    must satisfy kappa (lambda_K - lambda_Sigma) = -1 exactly."""
    lam = jacobian_at_flrw()
    residue = sp.simplify(
        candidate * (lam["lambda_k"] - lam["lambda_sigma"]) + 1)
    if residue != 0:
        raise OmkNearFlrwError(
            f"candidate slaving coefficient fails the exact order-K "
            f"invariance equation (residue {residue})")


# ---------------------------------------------------------------------------
# Path B: metric-level Einstein reduction (both 2-plane signatures)
# ---------------------------------------------------------------------------

def _diagonal_ricci(coords, gdiag):
    """Ricci tensor for a diagonal metric, computed from first
    principles: Gamma^a_bc = (1/2) g^aa (d_b g_ac + d_c g_ab -
    d_a g_bc) with the diagonal structure applied, then
    R_bc = d_a Gamma^a_bc - d_c Gamma^a_ba
           + Gamma^a_ad Gamma^d_bc - Gamma^a_cd Gamma^d_ba."""
    n = len(coords)
    gam = [[[sp.S(0)] * n for _ in range(n)] for _ in range(n)]
    for a in range(n):
        for b in range(n):
            for c in range(n):
                expr = sp.S(0)
                if a == c:
                    expr += sp.diff(gdiag[a], coords[b])
                if a == b:
                    expr += sp.diff(gdiag[a], coords[c])
                if b == c:
                    expr -= sp.diff(gdiag[b], coords[a])
                gam[a][b][c] = sp.simplify(expr / (2 * gdiag[a]))
    ric = sp.zeros(n)
    for b in range(n):
        for c in range(n):
            expr = sp.S(0)
            for a in range(n):
                expr += sp.diff(gam[a][b][c], coords[a])
                expr -= sp.diff(gam[a][b][a], coords[c])
                for d in range(n):
                    expr += gam[a][a][d] * gam[d][b][c]
                    expr -= gam[a][c][d] * gam[d][b][a]
            ric[b, c] = sp.simplify(expr)
    return ric


def metric_path_reduction(signature: int, rhs_tamper=0) -> dict:
    """Path B: from the diagonal LRS metric
    ds^2 = -dt^2 + A(t)^2 dx^2 + B(t)^2 (dy^2 + f(y)^2 dz^2),
    f = sinh y (signature +1, Bianchi III) or sin y (signature -1,
    Kantowski-Sachs), derive the expansion-normalized reduced RHS and
    verify it equals the registered path-A RHS exactly.

    ``rhs_tamper`` is the preregistered mutation-injection point: a
    nonzero sympy expression is added to the derived dK/dN BEFORE the
    production equality comparison, so the path-disagreement mutant
    exercises THIS gate (not a reimplementation)."""
    if signature not in (1, -1):
        raise OmkNearFlrwError("signature must be +1 (BIII) or -1 (KS)")
    t, x, y, z = sp.symbols("t x y z")
    A = sp.Function("A", positive=True)(t)
    B = sp.Function("B", positive=True)(t)
    f = sp.sinh(y) if signature == 1 else sp.sin(y)
    coords = (t, x, y, z)
    gdiag = (sp.S(-1), A ** 2, B ** 2, B ** 2 * f ** 2)
    ric = _diagonal_ricci(coords, gdiag)
    g = sp.diag(*gdiag)
    ginv = sp.diag(*[1 / gi for gi in gdiag])
    rs = sp.simplify(sum(ginv[i, i] * ric[i, i] for i in range(4)))
    G = sp.zeros(4)
    for i in range(4):
        G[i, i] = sp.simplify(ric[i, i] - rs * g[i, i] / 2)

    rho = sp.simplify(G[0, 0])                 # G_tt with g_tt = -1
    p_x = sp.simplify(G[1, 1] / A ** 2)
    p_y = sp.simplify(G[2, 2] / B ** 2)
    # perfect fluid p = w rho: two independent evolution equations
    sol = sp.solve([sp.Eq(p_x, W * rho), sp.Eq(p_y, W * rho)],
                   [sp.diff(A, t, 2), sp.diff(B, t, 2)], dict=True)
    if len(sol) != 1:
        raise OmkNearFlrwError("Einstein evolution not uniquely solvable")
    accel = sol[0]

    H1 = sp.diff(A, t) / A
    H2 = sp.diff(B, t) / B
    H = (H1 + 2 * H2) / 3
    Sigma_expr = (H1 - H2) / (3 * H)
    K_expr = sp.Rational(1, 1) * signature / (3 * B ** 2 * H ** 2)

    dSigma_dt = sp.simplify(sp.diff(Sigma_expr, t).subs(accel))
    dK_dt = sp.simplify(sp.diff(K_expr, t).subs(accel))

    # to expansion time N (dN = H dt), then to (Sigma, K) variables:
    S, K = sp.symbols("Sigma K", real=True)
    a1, b1 = sp.symbols("a1 b1")               # H1, H2 placeholders
    Bs = sp.symbols("Bsym", positive=True)
    subs_first = {sp.diff(A, t): a1 * A, sp.diff(B, t): b1 * B, B: Bs}
    Hs = (a1 + 2 * b1) / 3

    def to_reduced(expr):
        e = sp.expand(sp.simplify(expr).subs(subs_first))
        e = sp.simplify(e / Hs)                # d/dN = (1/H) d/dt
        # H1 = H(1+2 Sigma), H2 = H(1-Sigma); K = signature/(3 B^2 H^2)
        # so 1/Bs^2 = 3 * signature * H^2 * K (Bs enters only through
        # even powers, so the sqrt is a bookkeeping device).
        Hsym = sp.symbols("Hsym", positive=True)
        e = e.subs({a1: Hsym * (1 + 2 * S), b1: Hsym * (1 - S)})
        e = sp.expand(sp.simplify(e))
        e = e.subs({Bs: 1 / sp.sqrt(3 * signature * Hsym ** 2 * K)})
        e = sp.simplify(sp.expand(e))
        if e.has(Hsym):
            e = sp.simplify(sp.cancel(e))
        if e.has(Hsym):
            raise OmkNearFlrwError(
                "reduced RHS is not expansion-normalized (H survives)")
        return sp.simplify(e)

    dSigma_dN = to_reduced(dSigma_dt)
    dK_dN = to_reduced(dK_dt) + rhs_tamper

    diff_sigma = sp.simplify(sp.expand(dSigma_dN - f_sigma(S, K)))
    diff_k = sp.simplify(sp.expand(dK_dN - f_k(S, K)))
    if diff_sigma != 0 or diff_k != 0:
        raise OmkNearFlrwError(
            f"path-B reduced RHS disagrees with the registered path-A "
            f"RHS (signature {signature}): dSigma residue {diff_sigma}, "
            f"dK residue {diff_k}")
    return {
        "signature": signature,
        "dSigma_dN": sp.sstr(dSigma_dN),
        "dK_dN": sp.sstr(dK_dN),
        "matches_path_a": True,
    }


def require_two_path_agreement(path_b_reports: list[dict]) -> None:
    """Coefficient claims need BOTH signature branches of path B to
    match path A exactly; one-path claims are rejected."""
    signatures = {r.get("signature") for r in path_b_reports
                  if r.get("matches_path_a") is True}
    if signatures != {1, -1}:
        raise OmkNearFlrwError(
            "two-path agreement incomplete: both 2-plane signatures "
            "must match the registered RHS exactly — one-path claims "
            "are rejected")


# ---------------------------------------------------------------------------
# System checks
# ---------------------------------------------------------------------------

def system_checks() -> dict:
    """FLRW fixed point, exact vacuum anchor stationarity, sign check,
    and the KS mirror as a pure sign convention."""
    S, K = sp.symbols("Sigma K")
    flrw = (sp.simplify(f_sigma(0, 0)) == 0
            and sp.simplify(f_k(0, 0)) == 0)
    anchor_sigma = sp.simplify(
        f_sigma(sp.Rational(-1, 2), sp.Rational(3, 4)))
    anchor_k = sp.simplify(f_k(sp.Rational(-1, 2), sp.Rational(3, 4)))
    vacuum = anchor_sigma == 0 and anchor_k == 0
    sign = sp.simplify(f_sigma(0, K) + K) == 0   # coefficient exactly -1
    # the RHS is a polynomial in (Sigma, K); the KS branch is the SAME
    # polynomial evaluated at K < 0 — no separate mirror coefficients.
    # A REAL normalization audit: the RHS must be polynomial with free
    # symbols exactly within {Sigma, K, w} (a residual H, B, or t would
    # fail either condition).
    try:
        allowed = {S, K, W}
        dimensionless = (
            f_sigma(S, K).free_symbols <= allowed
            and f_k(S, K).free_symbols <= allowed
            and sp.Poly(f_sigma(S, K), S, K) is not None
            and sp.Poly(f_k(S, K), S, K) is not None)
    except sp.PolynomialError:
        dimensionless = False
    if not (flrw and vacuum and sign and dimensionless):
        raise OmkNearFlrwError(
            f"system checks failed: flrw={flrw} vacuum={vacuum} "
            f"sign={sign} dimensionless={dimensionless}")
    return {"flrw_fixed_point": True, "vacuum_anchor_stationary": True,
            "curvature_source_coefficient_minus_one": True,
            "expansion_normalized_dimensionless": True,
            "ks_mirror_is_sign_convention": True}


# ---------------------------------------------------------------------------
# Singular map + domain validation
# ---------------------------------------------------------------------------

def resonance_w(n: int) -> Fraction:
    """Order-n resonance n*lambda_K = lambda_Sigma at
    w_n = -(2n+3)/(6n-3)."""
    if n < 1:
        raise OmkNearFlrwError("resonance order starts at 1")
    return Fraction(-(2 * n + 3), 6 * n - 3)


def singular_map() -> dict:
    """The exact singular/zero-denominator boundary map."""
    entries = [
        {"w": str(resonance_w(1)), "mechanism":
            "order-1 resonance = kappa pole 2+q0 = 0 = eigenvalue "
            "collision lambda_K = lambda_Sigma"},
        {"w": str(resonance_w(2)), "mechanism":
            "order-2 resonance 2*lambda_K = lambda_Sigma (c2 "
            "denominator factor 9w+7)"},
        {"w": str(resonance_w(3)), "mechanism":
            "order-3 resonance 3*lambda_K = lambda_Sigma (c3 "
            "denominator factor 5w+3)"},
        {"w": "-1/3", "mechanism":
            "lambda_K = 0 (curvature mode marginal; expansion "
            "parameter degenerates)"},
        {"w": "1", "mechanism":
            "lambda_Sigma = 0 (transient marginal; slaving decay "
            "vanishes)"},
    ]
    # verify the resonance formula against the actual denominators via
    # real polynomial divisibility: each registered factor must divide
    # the corresponding coefficient denominator with zero remainder.
    if resonance_w(1) != Fraction(-5, 3) or \
            resonance_w(2) != Fraction(-7, 9) or \
            resonance_w(3) != Fraction(-3, 5):
        raise OmkNearFlrwError("resonance family formula drifted")
    for expr, factor in ((KAPPA_EXACT, 3 * W + 5),
                         (C2_EXACT, 9 * W + 7),
                         (C3_EXACT, 5 * W + 3)):
        denominator = sp.Poly(sp.denom(sp.together(sp.cancel(expr))), W)
        _quot, rem = sp.div(denominator, sp.Poly(factor, W), W)
        if not rem.is_zero:
            raise OmkNearFlrwError(
                f"denominator of {sp.sstr(expr)} is not divisible by "
                f"the registered resonance factor {factor}")
    return {"entries": entries,
            "resonance_family": "w_n = -(2n+3)/(6n-3), n >= 1, "
                                "contained in [-5/3, -1/3) (w_1 is the "
                                "order-1 member), accumulating at -1/3"}


def _family_point_in_open_interval(lo: Fraction,
                                   hi: Fraction) -> Fraction | None:
    """EXACT decision (no truncated scan): does any resonance
    w_n = -(2n+3)/(6n-3), n >= 1, lie in (lo, hi)? The family is
    strictly increasing from w_1 = -5/3 toward -1/3, so it suffices to
    find the smallest n with w_n > lo (monotone binary search in exact
    Fractions) and test that single point against hi."""
    if hi <= Fraction(-5, 3) or lo >= Fraction(-1, 3):
        return None
    if resonance_w(1) > lo:
        first = 1
    else:
        # binary search the least n with w_n > lo; w_n -> -1/3 so such
        # n exists exactly when lo < -1/3.
        if lo >= Fraction(-1, 3):
            return None
        lo_n, hi_n = 1, 2
        while resonance_w(hi_n) <= lo:
            hi_n *= 2
        while hi_n - lo_n > 1:
            mid = (lo_n + hi_n) // 2
            if resonance_w(mid) <= lo:
                lo_n = mid
            else:
                hi_n = mid
        first = hi_n
    candidate = resonance_w(first)
    return candidate if lo < candidate < hi else None


def validate_declared_domain(domain: tuple[Fraction, Fraction]) -> None:
    """Every singular-map entry — the ENTIRE infinite resonance family
    plus the marginal boundaries — must lie OUTSIDE the declared OPEN
    domain; an in-domain singularity triggers the roadmap kill rule."""
    lo, hi = Fraction(domain[0]), Fraction(domain[1])
    if not lo < hi:
        raise OmkNearFlrwError("empty declared domain")
    inside = _family_point_in_open_interval(lo, hi)
    if inside is not None:
        raise OmkNearFlrwError(
            f"declared domain ({lo}, {hi}) contains the singular "
            f"resonance w = {inside} (and, by accumulation, possibly "
            "infinitely many more) — shrink the domain or abandon "
            "(roadmap exit rule)")
    for point in (Fraction(-1, 3), Fraction(1)):
        if lo < point < hi:
            raise OmkNearFlrwError(
                f"declared domain ({lo}, {hi}) contains the marginal "
                f"boundary w = {point} — shrink the domain or abandon "
                "(roadmap exit rule)")


def _require_w_in_declared_domain(w_value: Fraction) -> Fraction:
    """Return a fixed background only when it lies in the open domain."""

    wv = Fraction(w_value)
    validate_declared_domain(DECLARED_DOMAIN)
    if not DECLARED_DOMAIN[0] < wv < DECLARED_DOMAIN[1]:
        raise OmkNearFlrwError(
            f"w = {wv} is outside the declared open domain"
        )
    return wv


# ---------------------------------------------------------------------------
# Finite-difference plateau (independent numeric path)
# ---------------------------------------------------------------------------

def fd_plateau(w_value: Fraction, probes=(Fraction(1, 100000),
                                          Fraction(1, 10000),
                                          Fraction(1, 1000)),
               k0: Fraction = Fraction(1, 10 ** 8), dps: int = 30,
               branch: int = 1) -> dict:
    """Integrate the exact ODE forward from the LINEAR-ONLY slaved
    seed Sigma0 = kappa K0 (independent of c2) and read the
    finite-difference coefficients as K -> 0, on the requested branch
    (branch = +1: Bianchi III, K > 0; branch = -1: KS mirror, K < 0 —
    both are covered so the mirror is numerically exercised, not just
    claimed symbolically). K0 sits three decades below the smallest
    probe because the linear seed's off-manifold transient contaminates
    the order-2 ratio by ~ |c2| K0^2 (K/K0)^(s/g) / K^2, which at
    K0 = 1e-8 is provably below every preregistered envelope. The
    envelopes are checked here — a miss raises (a fit is never a
    derivation)."""
    import mpmath

    wv = _require_w_in_declared_domain(w_value)
    if branch not in (1, -1):
        raise OmkNearFlrwError("branch must be +1 (BIII) or -1 (KS)")
    if not probes:
        raise OmkNearFlrwError(
            "finite-difference plateau needs at least one probe"
        )
    kappa = Fraction(-2, 1) / (3 * wv + 5)
    c2 = C2_EXACT.subs(W, sp.Rational(wv))
    c2_frac = Fraction(sp.Rational(c2).p, sp.Rational(c2).q)

    with mpmath.workdps(dps):
        wf = mpmath.mpf(wv.numerator) / mpmath.mpf(wv.denominator)

        def rhs(_n, y):
            S, K = y[0], y[1]
            q = (1 + 3 * wf) * (1 - K) / 2 + mpmath.mpf(3) / 2 \
                * (1 - wf) * S ** 2
            dS = -K - (S / 2) * ((1 + 3 * wf) * K
                                 + 3 * (1 - wf) * (1 - S ** 2))
            dK = 2 * K * (q + S)
            return [dS, dK]

        k_start = branch * mpmath.mpf(k0.numerator) / mpmath.mpf(
            k0.denominator)
        kap_f = mpmath.mpf(kappa.numerator) / mpmath.mpf(
            kappa.denominator)
        c2_f = mpmath.mpf(c2_frac.numerator) / mpmath.mpf(
            c2_frac.denominator)
        y = mpmath.odefun(rhs, 0, [kap_f * k_start, k_start], tol=10 **
                          (-(dps - 5)))
        rows = []
        for probe in probes:
            target = mpmath.mpf(probe.numerator) / mpmath.mpf(
                probe.denominator)
            # locate N with |K(N)| = target: walk forward in unit steps
            # to the FIRST crossing (never integrating far past it —
            # the KS branch is unbounded, so a fixed far bracket would
            # push odefun through the blowup), then bisect.
            lo_n = mpmath.mpf(0)
            hi_n = mpmath.mpf(1)
            while abs(y(hi_n)[1]) < target:
                lo_n = hi_n
                hi_n += 1
                if hi_n > 200:
                    raise OmkNearFlrwError(
                        "probe |K| never reached along the trajectory")
            for _ in range(200):
                mid = (lo_n + hi_n) / 2
                if abs(y(mid)[1]) < target:
                    lo_n = mid
                else:
                    hi_n = mid
            S_val, K_val = y((lo_n + hi_n) / 2)
            r1 = S_val / K_val
            r2 = (S_val - kap_f * K_val) / K_val ** 2
            env1 = 5 * abs(K_val) + abs(c2_f) * abs(K_val) \
                * mpmath.mpf(3) / 2
            env2 = 5 * abs(K_val)
            ok1 = abs(r1 - kap_f) <= env1
            ok2 = abs(r2 - c2_f) <= env2
            if not (ok1 and ok2):
                raise OmkNearFlrwError(
                    f"finite-difference plateau at K = {probe} misses "
                    f"the analytic coefficient under the preregistered "
                    f"envelope (order1 ok={ok1}, order2 ok={ok2}) — "
                    "roadmap kill rule: a fit is never a derivation")
            rows.append({
                "K": str(probe),
                "sigma_over_k": mpmath.nstr(r1, 20),
                "order2_ratio": mpmath.nstr(r2, 20),
                "abs_dev_kappa": mpmath.nstr(abs(r1 - kap_f), 8),
                "abs_dev_c2": mpmath.nstr(abs(r2 - c2_f), 8),
                "within_envelopes": True,
            })
    return {
        "w": str(wv),
        "branch": "biii_K_positive" if branch == 1 else "ks_K_negative",
        "kappa_exact": str(kappa),
        "c2_exact": str(c2_frac),
        "k0": str(k0 * branch),
        "dps": dps,
        "probes": rows,
        "envelope_rule": "order1 <= 5|K| + |c2|*1.5|K|; order2 <= 5|K|; "
                         "preregistered, never widened",
    }


def validate_plateau_report(report: Mapping) -> None:
    """A plateau report claiming a coefficient that disagrees with the
    analytic value under the envelope is rejected."""
    import mpmath

    c2_claim = mpmath.mpf(str(report.get("claimed_c2")))
    if not mpmath.isfinite(c2_claim):
        raise OmkNearFlrwError(
            "plateau claim must carry a finite coefficient"
        )
    w_value = _require_w_in_declared_domain(
        Fraction(str(report.get("w")))
    )
    c2 = C2_EXACT.subs(W, sp.Rational(w_value))
    c2_exact = mpmath.mpf(sp.Rational(c2).p) / mpmath.mpf(
        sp.Rational(c2).q)
    probe = Fraction(str(report.get("probe_K")))
    if probe <= 0:
        raise OmkNearFlrwError(
            "plateau claim must carry a strictly positive probe magnitude"
        )
    envelope = 5 * mpmath.mpf(probe.numerator) / mpmath.mpf(
        probe.denominator)
    if abs(c2_claim - c2_exact) > envelope:
        raise OmkNearFlrwError(
            "plateau claim disagrees with the analytic coefficient "
            "under the preregistered envelope — a fitted line is not "
            "a derivation")


# ---------------------------------------------------------------------------
# Claim/caption gates
# ---------------------------------------------------------------------------

_CEILING_IMPLICATION_MARKERS = ("recover", "restor", "follow", "impl",
                                "deriv", "reinstat", "yield", "entail")


def validate_claim(claim: Mapping) -> None:
    """Reject global-equality and ceiling-implication readings (any
    wording combining the ceiling table with an implication verb)."""
    text = " ".join(str(claim.get(k) or "")
                    for k in ("asserts", "scope")).lower()
    if "ceiling" in text and any(marker in text
                                 for marker in
                                 _CEILING_IMPLICATION_MARKERS):
        raise OmkNearFlrwError(
            "the finite-ceiling program is NOT recovered, restored, or "
            "implied by the asymptotic coefficients — claim rejected")
    fixed = claim.get("fixed_background")
    if not fixed or "q0" not in str(fixed):
        raise OmkNearFlrwError(
            "coefficient claims must fix the background (q0/w); a "
            "claim without a fixed background is a forbidden global "
            "equality")


def lint_caption(text: str) -> None:
    lowered = text.lower()
    for phrase in _FORBIDDEN_PHRASES:
        if phrase.lower() in lowered:
            raise OmkNearFlrwError(
                "caption carries forbidden global-equality/ceiling/"
                "observational language")


def generate_caption(w_value: Fraction) -> str:
    wv = _require_w_in_declared_domain(w_value)
    kappa = Fraction(-2, 1) / (3 * wv + 5)
    c2 = C2_EXACT.subs(W, sp.Rational(wv))
    text = (
        f"[omk_near_flrw] Named LRS-III/KS reduced system at fixed "
        f"w = {wv} (q0 = {(Fraction(1) + 3 * wv) / 2}): slaved-mode "
        f"expansion Sigma = kappa K + c2 K^2 + O(K^3) with exact "
        f"kappa = {kappa}, c2 = {sp.Rational(c2)}. Class-conditional "
        "asymptotic coefficients on the declared open domain "
        "w in (-1/3, 1); two-path symbolic derivation + "
        "finite-difference plateau; no observational value is implied."
    )
    lint_caption(text)
    validate_claim({"asserts": "asymptotic coefficient",
                    "fixed_background": f"q0 = {(1 + 3 * wv) / 2}"})
    return text
