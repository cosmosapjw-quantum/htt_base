"""PR-132 interval remainder certification + uncertainty propagation.

Certifies the PR-131 slaved-mode prediction on the COMPACT declared
domain ``omk_domain_v1`` (|K| <= 1/10, w in [0, 1/2], both 2-plane
branches):

    |Sigma - (kappa K + c2 K^2)| <= M |K|^3 ,   M = 1  (exact),

as a FORWARD-INVARIANT trapping tube WHILE |K| stays in the domain:
on each Sigma-boundary curve the registered reduced flow points
inward, so a trajectory can leave only through the |K| = k_abs_max
faces (|K| grows on both branches, so no bound is claimed once |K|
exits). The boundary sign conditions
reduce to exact rational polynomials (positive denominators
``2(3w+5)^6 (9w+7)^3`` on the box; lowest K-power factored exactly)
and are proven UNIFORMLY by monomial-wise exact-Fraction interval
bounds with conclusive branch-and-bound bisection — finite grid
sampling is never accepted as proof.

The remainder propagates downstream as an EXPLICIT uncertainty
component. Four typed components stay SEPARATE and are never folded
into the central value: numerical_enclosure, source_convention,
physical_model_form (UNQUANTIFIED_CONDITIONAL, never numeric zero),
and inhouse_conservative_rule. The domain API refuses evaluation
outside the compact domain and refuses post-hoc expansion; a shrink
mints a new version. An admissible in-domain state escaping the
enclosure blocks the claim immediately.

Class-conditional asymptotic theorem with explicit remainder at fixed
q0(w) only. roadmap_rescue_v1:C2.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from fractions import Fraction
from typing import Mapping

import sympy as sp

from common.omk_near_flrw_expansion import (
    C2_EXACT,
    C3_EXACT,
    KAPPA_EXACT,
    W,
    f_k,
    f_sigma,
)

SCHEMA_VERSION = "pr132.omk_remainder_certificate.v1"

DOMAIN_VERSION = "omk_domain_v1"
W_BOX = (Fraction(0), Fraction(1, 2))
K_ABS_MAX = Fraction(1, 10)
M_TRAP = Fraction(1)
MAX_BISECTION_DEPTH = 14

REQUIRED_COMPONENTS = ("numerical_enclosure", "source_convention",
                       "physical_model_form", "inhouse_conservative_rule")


class OmkRemainderError(ValueError):
    """Raised on any certificate/domain/propagation violation."""


class ClaimBlockError(OmkRemainderError):
    """The immediate claim block: an admissible state escaped the
    enclosure (roadmap exit rule)."""


# ---------------------------------------------------------------------------
# Compact domain API (fail-closed)
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class CompactDomain:
    version: str = DOMAIN_VERSION
    w_lo: Fraction = W_BOX[0]
    w_hi: Fraction = W_BOX[1]
    k_abs_max: Fraction = K_ABS_MAX

    def __post_init__(self) -> None:
        version = str(self.version).strip()
        w_lo = Fraction(self.w_lo)
        w_hi = Fraction(self.w_hi)
        k_abs_max = Fraction(self.k_abs_max)
        if not version:
            raise OmkRemainderError("compact domain version is required")
        if w_lo > w_hi:
            raise OmkRemainderError(
                "compact domain bounds must be ordered w_lo <= w_hi"
            )
        if k_abs_max <= 0:
            raise OmkRemainderError(
                "compact domain k_abs_max must be positive"
            )
        if (
            w_lo < W_BOX[0]
            or w_hi > W_BOX[1]
            or k_abs_max > K_ABS_MAX
        ):
            raise OmkRemainderError(
                "compact domain exceeds the registered domain — "
                "post-hoc expansion is refused"
            )
        bounds = (w_lo, w_hi, k_abs_max)
        registered_bounds = (W_BOX[0], W_BOX[1], K_ABS_MAX)
        if bounds == registered_bounds and version != DOMAIN_VERSION:
            raise OmkRemainderError(
                "an unchanged domain must retain the registered version"
            )
        if bounds != registered_bounds and version == DOMAIN_VERSION:
            raise OmkRemainderError(
                "a domain shrink must mint a NEW version string"
            )
        object.__setattr__(self, "version", version)
        object.__setattr__(self, "w_lo", w_lo)
        object.__setattr__(self, "w_hi", w_hi)
        object.__setattr__(self, "k_abs_max", k_abs_max)

    def require_inside(self, w: Fraction, k: Fraction) -> None:
        wv, kv = Fraction(w), Fraction(k)
        if not (self.w_lo <= wv <= self.w_hi and
                abs(kv) <= self.k_abs_max and kv != 0):
            raise OmkRemainderError(
                f"state (w = {wv}, K = {kv}) is outside the compact "
                f"declared domain {self.version} (|K| <= "
                f"{self.k_abs_max}, w in [{self.w_lo}, {self.w_hi}], "
                "K != 0) — out-of-domain evaluation is refused")


REGISTERED_DOMAIN = CompactDomain()


def register_domain(version: str, w_lo: Fraction, w_hi: Fraction,
                    k_abs_max: Fraction) -> CompactDomain:
    """Only SHRINKS of the registered domain are acceptable, and every
    shrink must mint a NEW version string. Post-hoc expansion — the
    classic fit-to-observation drift — is refused."""
    w_lo, w_hi = Fraction(w_lo), Fraction(w_hi)
    k_abs_max = Fraction(k_abs_max)
    base = REGISTERED_DOMAIN
    if (w_lo < base.w_lo or w_hi > base.w_hi
            or k_abs_max > base.k_abs_max):
        raise OmkRemainderError(
            "proposed domain is not a subset of the registered "
            f"{base.version} — post-hoc expansion is refused")
    if (w_lo, w_hi, k_abs_max) != (base.w_lo, base.w_hi,
                                   base.k_abs_max) \
            and version == base.version:
        raise OmkRemainderError(
            "a domain shrink must mint a NEW version string")
    return CompactDomain(version, w_lo, w_hi, k_abs_max)


# ---------------------------------------------------------------------------
# Exact interval prover (uniform; grid sampling never accepted)
# ---------------------------------------------------------------------------

def _poly_bounds(poly: sp.Poly, xbox: tuple[Fraction, Fraction],
                 ybox: tuple[Fraction, Fraction],
                 ) -> tuple[Fraction, Fraction]:
    """Exact monomial-wise bounds of a bivariate polynomial with
    rational coefficients over a box with NONNEGATIVE endpoints."""
    if xbox[0] < 0 or ybox[0] < 0:
        raise OmkRemainderError("interval evaluator needs a nonnegative "
                                "box (substitute variables first)")
    if xbox[0] > xbox[1] or ybox[0] > ybox[1]:
        raise OmkRemainderError(
            "interval evaluator needs ordered box endpoints"
        )
    lo = Fraction(0)
    hi = Fraction(0)
    for (a, b), coeff in poly.terms():
        c = Fraction(int(sp.numer(coeff)), int(sp.denom(coeff)))
        mmin = Fraction(xbox[0]) ** a * Fraction(ybox[0]) ** b
        mmax = Fraction(xbox[1]) ** a * Fraction(ybox[1]) ** b
        if c >= 0:
            lo += c * mmin
            hi += c * mmax
        else:
            lo += c * mmax
            hi += c * mmin
    return lo, hi


def prove_polynomial_sign(expr, want_negative: bool,
                          xbox: tuple[Fraction, Fraction],
                          ybox: tuple[Fraction, Fraction],
                          x_symbol, y_symbol,
                          depth: int = 0,
                          stats: dict | None = None) -> dict:
    """Conclusive branch-and-bound sign proof. Returns
    {proved: bool, ...}; an inconclusive tree (depth cap hit) or a
    disproving sub-box FAILS CLOSED with a concrete rational
    counterexample when one exists."""
    if stats is None:
        stats = {"boxes": 0, "max_depth": 0}
    stats["boxes"] += 1
    stats["max_depth"] = max(stats["max_depth"], depth)
    poly = sp.Poly(expr, x_symbol, y_symbol)
    lo, hi = _poly_bounds(poly, xbox, ybox)
    if want_negative and hi < 0:
        return {"proved": True, "stats": stats}
    if (not want_negative) and lo > 0:
        return {"proved": True, "stats": stats}
    # try a concrete counterexample at the box midpoint
    xm = (Fraction(xbox[0]) + Fraction(xbox[1])) / 2
    ym = (Fraction(ybox[0]) + Fraction(ybox[1])) / 2
    value = Fraction(sp.Rational(expr.subs({x_symbol: sp.Rational(xm),
                                            y_symbol: sp.Rational(ym)})))
    if (want_negative and value > 0) or \
            ((not want_negative) and value < 0):
        return {"proved": False, "stats": stats,
                "counterexample": {"x": str(xm), "y": str(ym),
                                   "value": str(value)}}
    if depth >= MAX_BISECTION_DEPTH:
        return {"proved": False, "stats": stats,
                "reason": "inconclusive at the depth cap (fail-closed; "
                          "grid sampling is never substituted)"}
    for xb in ((xbox[0], xm), (xm, xbox[1])):
        for yb in ((ybox[0], ym), (ym, ybox[1])):
            sub = prove_polynomial_sign(expr, want_negative, xb, yb,
                                        x_symbol, y_symbol, depth + 1,
                                        stats)
            if not sub["proved"]:
                return sub
    return {"proved": True, "stats": stats}


# ---------------------------------------------------------------------------
# Trapping-region certificate
# ---------------------------------------------------------------------------

def _boundary_condition(branch: int, side: int, m_value: Fraction):
    """The inward-flow polynomial for one boundary curve. Returns
    (cofactor_expr, k_power, denominator, substituted_symbol) with the
    K variable mapped to a nonnegative symbol on both branches."""
    K = sp.symbols("K")
    h = KAPPA_EXACT * K + C2_EXACT * K ** 2
    abs_k_cubed = K ** 3 if branch == 1 else -(K ** 3)
    boundary = h + side * sp.Rational(m_value) * abs_k_cubed
    G = sp.together(f_sigma(boundary, K)
                    - sp.diff(boundary, K) * f_k(boundary, K))
    num, den = sp.fraction(sp.cancel(G))
    J = sp.symbols("Jpos", nonnegative=True)
    if branch == -1:
        num = sp.expand(num.subs(K, -J))
        den = sp.expand(den.subs(K, -J))
        var = J
    else:
        num = sp.expand(num.subs(K, J))
        den = sp.expand(den.subs(K, J))
        var = J
    poly = sp.Poly(num, var)
    min_power = min(m[0] for m in poly.as_dict())
    cofactor = sp.expand(num / var ** min_power)
    return cofactor, min_power, den, var


def prove_trapping_certificate(m_value: Fraction = M_TRAP,
                               domain: CompactDomain = REGISTERED_DOMAIN,
                               ) -> dict:
    """Prove forward invariance of |Sigma - h(K)| <= M |K|^3 on the
    compact domain, both branches, by conclusive interval proof of the
    boundary sign conditions. Any failure carries the counterexample
    (the wrong-constant mutant exercises exactly this path)."""
    results = []
    for branch in (1, -1):
        for side in (1, -1):
            cofactor, k_power, den, var = _boundary_condition(
                branch, side, Fraction(m_value))
            den_lo, den_hi = _poly_bounds(
                sp.Poly(den, var, W),
                (Fraction(0), domain.k_abs_max),
                (domain.w_lo, domain.w_hi))
            if not den_lo > 0:
                raise OmkRemainderError(
                    "boundary denominator not proven positive on the "
                    "box — certificate unavailable")
            want_negative = side == 1
            proof = prove_polynomial_sign(
                cofactor, want_negative,
                (Fraction(0), domain.k_abs_max),
                (domain.w_lo, domain.w_hi), var, W)
            if not proof["proved"]:
                detail = proof.get("counterexample") or proof.get(
                    "reason")
                raise OmkRemainderError(
                    f"trapping boundary sign proof FAILED (branch "
                    f"{branch}, side {side}, M = {m_value}): {detail}")
            results.append({
                "branch": branch,
                "side": "upper" if side == 1 else "lower",
                "k_power_factored": k_power,
                "boxes_examined": proof["stats"]["boxes"],
                "max_bisection_depth": proof["stats"]["max_depth"],
                "proved": True,
            })
    return {
        "domain_version": domain.version,
        "M_exact": str(Fraction(m_value)),
        "w_box": [str(domain.w_lo), str(domain.w_hi)],
        "k_abs_max": str(domain.k_abs_max),
        "boundaries": results,
        "method": "exact_fraction_interval_branch_and_bound",
        "grid_sampling_used": False,
    }


def validate_certificate_method(certificate: Mapping) -> None:
    """Grid sampling is never a uniform proof."""
    method = str(certificate.get("method") or "")
    if method != "exact_fraction_interval_branch_and_bound" or \
            certificate.get("grid_sampling_used") is not False:
        raise OmkRemainderError(
            "certificate rejected: only the conclusive exact interval "
            "branch-and-bound method is accepted as a UNIFORM proof — "
            "finite grid evaluation is not")


# ---------------------------------------------------------------------------
# Enclosure + claim block
# ---------------------------------------------------------------------------

def central_prediction(w: Fraction, k: Fraction) -> Fraction:
    """The bare two-term central value kappa K + c2 K^2 — remainder is
    NEVER absorbed here."""
    wv, kv = sp.Rational(Fraction(w)), sp.Rational(Fraction(k))
    value = (KAPPA_EXACT * sp.Symbol("K") + C2_EXACT * sp.Symbol("K") ** 2)
    out = sp.Rational(value.subs({W: wv, sp.Symbol("K"): kv}))
    return Fraction(int(out.p), int(out.q))


def enclosure(w: Fraction, k: Fraction,
              domain: CompactDomain = REGISTERED_DOMAIN,
              ) -> tuple[Fraction, Fraction]:
    """The certified interval [central - M|K|^3, central + M|K|^3];
    refuses out-of-domain states."""
    domain.require_inside(w, k)
    center = central_prediction(w, k)
    radius = M_TRAP * abs(Fraction(k)) ** 3
    return center - radius, center + radius


def check_admissible_state(w: Fraction, k: Fraction, sigma,
                           domain: CompactDomain = REGISTERED_DOMAIN,
                           ) -> None:
    """The roadmap exit rule: an admissible in-domain state outside
    the certified enclosure blocks the claim IMMEDIATELY."""
    lo, hi = enclosure(w, k, domain)
    value = Fraction(sigma)
    if not lo <= value <= hi:
        raise ClaimBlockError(
            f"admissible state (w = {w}, K = {k}, Sigma = {value}) "
            f"escapes the certified enclosure [{lo}, {hi}] — claim "
            "blocked immediately (roadmap exit rule)")


# ---------------------------------------------------------------------------
# Component-separated uncertainty propagation
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class UncertaintyBudget:
    """Four typed components, never collapsed."""

    numerical_enclosure: str
    source_convention: str
    physical_model_form: str
    inhouse_conservative_rule: str
    components: tuple = field(default=REQUIRED_COMPONENTS)

    def as_payload(self) -> dict:
        return {
            "numerical_enclosure": self.numerical_enclosure,
            "source_convention": self.source_convention,
            "physical_model_form": self.physical_model_form,
            "inhouse_conservative_rule": self.inhouse_conservative_rule,
            "collapsed_single_number": None,
        }


def build_budget(w: Fraction, k: Fraction) -> UncertaintyBudget:
    lo, hi = enclosure(w, k)
    c3 = sp.Rational(C3_EXACT.subs(W, sp.Rational(Fraction(w))))
    return UncertaintyBudget(
        numerical_enclosure=(
            f"remainder |R| <= {M_TRAP}*|K|^3 = "
            f"{M_TRAP * abs(Fraction(k)) ** 3} (certified interval "
            f"[{lo}, {hi}])"),
        source_convention=(
            "registered PR-125 convention channel; the legacy "
            "reproduction channel carries its own labeled delta and is "
            "never merged here"),
        physical_model_form=(
            "single-fluid fixed-w class assumption — "
            "UNQUANTIFIED_CONDITIONAL (never numeric zero)"),
        inhouse_conservative_rule=(
            f"M = {M_TRAP} chosen above the envelope-sizing |c3| = "
            f"|{c3}| (in-house margin, labeled)"),
    )


def validate_budget(payload: Mapping) -> None:
    """Reject collapsed or incomplete budgets."""
    missing = [c for c in REQUIRED_COMPONENTS
               if not isinstance(payload.get(c), str)
               or not payload[c].strip()]
    if missing:
        raise OmkRemainderError(
            f"uncertainty budget missing typed components: {missing} — "
            "component separation is mandatory")
    if payload.get("collapsed_single_number") is not None:
        raise OmkRemainderError(
            "uncertainty budget collapsed into one number — rejected")
    if "zero" in str(payload.get("physical_model_form")).lower() and \
            "unquantified" not in \
            str(payload.get("physical_model_form")).lower():
        raise OmkRemainderError(
            "physical model-form uncertainty may not be set to zero")


def validate_report_central(report: Mapping) -> None:
    """The central-value rule: remainder is never absorbed."""
    w = Fraction(str(report["w"]))
    k = Fraction(str(report["K"]))
    REGISTERED_DOMAIN.require_inside(w, k)
    central = Fraction(str(report["central"]))
    if central != central_prediction(w, k):
        raise OmkRemainderError(
            "report central value differs from the bare kappa K + "
            "c2 K^2 prediction — remainder absorption is rejected")


def propagate_to_ceiling(w: Fraction, k: Fraction) -> dict:
    """Downstream ceiling propagation: the slaving inversion
    Delta_Omega_k = Sigma/kappa maps the FULL enclosure interval, with
    components preserved (comparison-only; nothing promoted; the same
    separation applies to MES comparison consumers)."""
    lo, hi = enclosure(w, k)
    kappa = Fraction(int(sp.Rational(
        KAPPA_EXACT.subs(W, sp.Rational(Fraction(w)))).p),
        int(sp.Rational(KAPPA_EXACT.subs(W,
                        sp.Rational(Fraction(w)))).q))
    mapped = sorted((lo / kappa, hi / kappa))
    budget = build_budget(w, k)
    payload = budget.as_payload()
    validate_budget(payload)
    return {
        "w": str(Fraction(w)),
        "K": str(Fraction(k)),
        "central": str(central_prediction(w, k)),
        "sigma_enclosure": [str(lo), str(hi)],
        "delta_omega_k_enclosure": [str(mapped[0]), str(mapped[1])],
        "uncertainty_components": payload,
        "mes_consumer_note": "comparison-only rows inherit the same "
                             "component separation; nothing is "
                             "promoted and no observational value is "
                             "implied",
    }


# ---------------------------------------------------------------------------
# Caption gate
# ---------------------------------------------------------------------------

_FORBIDDEN_PHRASES = tuple(
    a + b for a, b in (
        ("uniform by", " sampling"), ("grid-verified", " proof"),
        ("absorbed into", " the central"),
        ("single combined", " uncertainty"),
        ("observed", " curvature"),
    )
)


def lint_caption(text: str) -> None:
    lowered = text.lower()
    for phrase in _FORBIDDEN_PHRASES:
        if phrase.lower() in lowered:
            raise OmkRemainderError(
                "caption carries forbidden sampling/absorption/"
                "collapse/observational language")


def generate_caption(w: Fraction, k: Fraction) -> str:
    lo, hi = enclosure(w, k)
    text = (
        f"[omk_remainder] Compact domain {DOMAIN_VERSION} (|K| <= "
        f"{K_ABS_MAX}, w in [{W_BOX[0]}, {W_BOX[1]}], both branches): "
        f"at (w = {Fraction(w)}, K = {Fraction(k)}) the certified "
        f"enclosure is Sigma in [{lo}, {hi}] — central "
        f"kappa K + c2 K^2 with explicit remainder <= {M_TRAP}|K|^3 "
        "proven by exact interval branch-and-bound. Wide bounds are a "
        "success condition; four uncertainty components stay separate; "
        "no observational value is implied."
    )
    lint_caption(text)
    return text
