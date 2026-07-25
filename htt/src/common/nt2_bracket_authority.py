"""PR-128 NT2 coefficient authority (successor of the reciprocal-wrong
legacy bracket).

SPECIFICATION-FIRST (registered in ``pr128_spec.yaml`` before any
rederivation): the l=2 covariant relation is ``a2 = kappa * Sigma *
(1 + delta)`` with the registered ``kappa = 4/21`` and ``|delta| <= R < 1``
(H3 proxy ``R = a3/a2``). Solving for Sigma INVERTS kappa:

    a2 / (kappa * (1 + R))  <=  Sigma  <=  a2 / (kappa * (1 - R))

so the coefficient enters the bracket RECIPROCALLY (``1/kappa = 21/4``).
The shipped legacy ``egs2_shear_bracket.shear_lower`` uses ``a2 * kappa /
(1 + R)`` — the reciprocal of the REGISTERED relation's inversion (finding
N-THEORY-NT2-COEFFICIENT; the relation itself is a registered assumption —
only the inversion direction is derived): still a true but 441/16-weaker lower bound; the
defect was labeling it as the proved relation. The legacy module stays
byte-frozen as historical reproduction; this module is the authority.

The MES placeholder upper (``C_up * a2``) is NEVER merged with the
H3-conditional theorem bracket into one proven interval — the authority
publishes them as separate labeled objects and rejects merged intervals.

Two engines (SymPy symbolic inversion; exact-Fraction numeric) must agree
on every bracket endpoint and on the DIRECTION (the lower endpoint is
strictly decreasing in kappa). The dual-engine coverage is the INVERSION
ALGEBRA and endpoints; the rejection domain is one shared validator
(disclosed — domain checks are not engine-diverse). Closure/H3-conditional
algebraic bracket at roadmap_rescue_v1:C2 — no detection, no isotropy
statement, and no result-pack flow-through (deferred by checkpoint-075
discipline).
"""
from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction
from typing import Mapping, Sequence

SCHEMA_VERSION = "pr128.nt2_bracket_authority.v1"

# Registered (specification-first) values — the pin the mutation
# `coefficient_near_output_pick` is killed against.
KAPPA_REGISTERED = Fraction(4, 21)
# F_shear ceiling: the S2a combined-comparator value used by the legacy
# bracket AND the audit's PASS source (wolfram/egs3_bracket_constants.wls
# xmax = 925/100000000). NOT the x_C interval ceiling 17/100.
X_MAX_REGISTERED = Fraction(925, 100000000)


class Nt2AuthorityError(ValueError):
    """Raised on any NT2-authority violation (fail-closed)."""


def _domain(a2: Fraction, a3: Fraction, kappa: Fraction) -> Fraction:
    if kappa <= 0:
        raise Nt2AuthorityError(
            f"kappa must be strictly positive (got {kappa})"
        )
    if a2 <= 0:
        raise Nt2AuthorityError("a2 must be strictly positive")
    if a3 < 0:
        raise Nt2AuthorityError("a3 must be nonnegative")
    R = a3 / a2
    if R >= 1:
        raise Nt2AuthorityError(
            f"R = a3/a2 = {R} >= 1: the two-sided inversion has a zero/"
            "negative denominator — no theorem bracket exists here"
        )
    return R


def sigma_bracket(a2: Fraction, a3: Fraction,
                  kappa: Fraction = KAPPA_REGISTERED
                  ) -> tuple[Fraction, Fraction]:
    """The H3-conditional theorem bracket (exact-Fraction engine):
    a2/(kappa(1+R)) <= Sigma <= a2/(kappa(1-R))."""
    a2, a3, kappa = Fraction(a2), Fraction(a3), Fraction(kappa)
    R = _domain(a2, a3, kappa)
    lower = a2 / (kappa * (1 + R))
    upper = a2 / (kappa * (1 - R))
    return lower, upper


def sigma_bracket_sympy(a2: Fraction, a3: Fraction,
                        kappa: Fraction = KAPPA_REGISTERED
                        ) -> tuple[Fraction, Fraction]:
    """Independent SymPy engine: symbolic inversion of the registered
    relation, then exact substitution (no reuse of sigma_bracket)."""
    import sympy as sp

    a2_f, a3_f, kappa_f = Fraction(a2), Fraction(a3), Fraction(kappa)
    _domain(a2_f, a3_f, kappa_f)
    a2s, ks, sig = sp.symbols("a2 kappa Sigma", positive=True)
    delta = sp.symbols("delta", real=True)
    relation = sp.Eq(a2s, ks * sig * (1 + delta))
    solved = sp.solve(relation, sig)[0]        # a2/(kappa*(1+delta))
    R = sp.Rational(a3_f.numerator, a3_f.denominator) / sp.Rational(
        a2_f.numerator, a2_f.denominator)
    subs_common = {a2s: sp.Rational(a2_f.numerator, a2_f.denominator),
                   ks: sp.Rational(kappa_f.numerator, kappa_f.denominator)}
    lower = solved.subs({**subs_common, delta: R})
    upper = solved.subs({**subs_common, delta: -R})
    return (Fraction(int(sp.numer(lower)), int(sp.denom(lower))),
            Fraction(int(sp.numer(upper)), int(sp.denom(upper))))


def require_engine_consensus(results: Mapping[str, tuple]) -> tuple:
    """The REAL consensus gate: BOTH named engines present with identical
    exact endpoints; one-engine claims and disagreements are blocked."""
    expected_engines = {"fraction_numeric", "sympy_symbolic"}
    if set(results) != expected_engines:
        raise Nt2AuthorityError(
            f"bracket claims require BOTH engines {sorted(expected_engines)}; "
            f"got {sorted(results)}"
        )
    values = set()
    for engine, endpoints in results.items():
        if (
            isinstance(endpoints, (str, bytes))
            or not isinstance(endpoints, Sequence)
            or len(endpoints) != 2
        ):
            raise Nt2AuthorityError(
                f"{engine} must return exactly two bracket endpoints"
            )
        try:
            pair = tuple(Fraction(endpoint) for endpoint in endpoints)
        except (OverflowError, TypeError, ValueError, ZeroDivisionError) as exc:
            raise Nt2AuthorityError(
                f"{engine} returned non-rational bracket endpoints"
            ) from exc
        if pair[0] > pair[1]:
            raise Nt2AuthorityError(
                f"{engine} returned reversed bracket endpoints"
            )
        values.add(pair)
    if len(values) != 1:
        raise Nt2AuthorityError(
            f"engines disagree on the bracket endpoints: {sorted(values)}"
        )
    return values.pop()


def require_bracket_agreement(a2: Fraction, a3: Fraction,
                              kappa: Fraction = KAPPA_REGISTERED
                              ) -> tuple[Fraction, Fraction]:
    """Both engines must produce identical exact endpoints (routed through
    the real consensus gate)."""
    return require_engine_consensus({
        "fraction_numeric": sigma_bracket(a2, a3, kappa),
        "sympy_symbolic": sigma_bracket_sympy(a2, a3, kappa),
    })


def require_direction(kappa: Fraction = KAPPA_REGISTERED) -> None:
    """The registered DIRECTION check that kills the reciprocal-wrong form:
    the lower endpoint must be strictly DECREASING in kappa (reciprocal
    entry). The legacy a2*kappa form is strictly increasing and fails."""
    a2, a3 = Fraction(1, 1000), Fraction(1, 2000)
    lo_small, _ = sigma_bracket(a2, a3, kappa)
    lo_large, _ = sigma_bracket(a2, a3, kappa * 2)
    if not lo_small > lo_large:
        raise Nt2AuthorityError(
            "direction check failed: the lower endpoint must be strictly "
            "decreasing in kappa (reciprocal coefficient entry)"
        )


def require_claimed_lower_direction(lower_at_kappa: Fraction,
                                    lower_at_2kappa: Fraction) -> None:
    """Validate an externally claimed lower-endpoint pair: increasing in
    kappa is the registered reciprocal-wrong defect."""
    if Fraction(lower_at_2kappa) >= Fraction(lower_at_kappa):
        raise Nt2AuthorityError(
            "claimed lower endpoint is non-decreasing in kappa — the "
            "reciprocal-wrong coefficient direction is rejected"
        )


def f_lo(a2: Fraction, a3: Fraction, kappa: Fraction = KAPPA_REGISTERED,
         x_max: Fraction = X_MAX_REGISTERED) -> Fraction:
    """The corrected lower F endpoint: F_lo = Sigma_lo^2 / x_max."""
    lower, _ = require_bracket_agreement(a2, a3, kappa)
    if Fraction(x_max) <= 0:
        raise Nt2AuthorityError("x_max must be strictly positive")
    return lower * lower / Fraction(x_max)


@dataclass(frozen=True)
class Nt2AuthorityBracket:
    """The authority object: theorem bracket + SEPARATE placeholder upper."""

    a2: Fraction
    a3: Fraction
    kappa: Fraction
    sigma_lo: Fraction
    sigma_hi_theorem: Fraction
    f_lo: Fraction
    mes_placeholder_upper: Fraction | None
    mes_placeholder_provenance: str

    def __post_init__(self) -> None:
        if self.mes_placeholder_upper is not None and (
                self.mes_placeholder_provenance != "placeholder_not_merged"):
            raise Nt2AuthorityError(
                "the MES placeholder upper must carry the "
                "placeholder_not_merged provenance label"
            )

    def as_payload(self) -> dict:
        return {
            "a2": str(self.a2), "a3": str(self.a3),
            "kappa": str(self.kappa),
            "sigma_lo": str(self.sigma_lo),
            "sigma_hi_theorem": str(self.sigma_hi_theorem),
            "f_lo": str(self.f_lo),
            "mes_placeholder_upper": (
                None if self.mes_placeholder_upper is None
                else str(self.mes_placeholder_upper)),
            "mes_placeholder_provenance": self.mes_placeholder_provenance,
            "merged": False,
        }


def build_authority_bracket(a2: Fraction, a3: Fraction,
                            kappa: Fraction = KAPPA_REGISTERED,
                            c_up_placeholder: Fraction | None = None
                            ) -> Nt2AuthorityBracket:
    lower, upper = require_bracket_agreement(a2, a3, kappa)
    return Nt2AuthorityBracket(
        a2=Fraction(a2), a3=Fraction(a3), kappa=Fraction(kappa),
        sigma_lo=lower, sigma_hi_theorem=upper,
        f_lo=f_lo(a2, a3, kappa),
        mes_placeholder_upper=(
            None if c_up_placeholder is None
            else Fraction(c_up_placeholder) * Fraction(a2)),
        mes_placeholder_provenance="placeholder_not_merged",
    )


def validate_interval_claim(claim: Mapping) -> None:
    """Reject any interval object that MERGES the MES placeholder upper
    with the theorem bracket into one proven interval."""
    if bool(claim.get("merged")):
        raise Nt2AuthorityError(
            "a merged placeholder+theorem interval is forbidden: the MES "
            "placeholder upper and the H3-conditional theorem bracket are "
            "separate labeled objects"
        )
    hi = claim.get("proven_upper")
    placeholder = claim.get("mes_placeholder_upper")
    if hi is not None and placeholder is not None:
        try:
            same_endpoint = Fraction(str(hi)) == Fraction(str(placeholder))
        except (ValueError, ZeroDivisionError) as exc:
            raise Nt2AuthorityError(
                "interval endpoints must be exact finite rational values"
            ) from exc
        if same_endpoint:
            raise Nt2AuthorityError(
                "the proven upper endpoint may not be the MES placeholder"
            )


def validate_theorem_upper(claimed_upper: Fraction, a2: Fraction,
                           a3: Fraction,
                           kappa: Fraction = KAPPA_REGISTERED) -> None:
    """An interval whose upper endpoint sits BELOW the theorem upper
    excludes admissible Sigma values and is invalid (the frozen legacy
    two-sided object with C_up = 9 fails this for R > 5/12)."""
    _, theorem_upper = sigma_bracket(a2, a3, kappa)
    if Fraction(claimed_upper) < theorem_upper:
        raise Nt2AuthorityError(
            f"claimed upper endpoint {Fraction(claimed_upper)} < theorem "
            f"upper {theorem_upper}: the interval excludes admissible "
            "Sigma values under the registered relation"
        )


def require_registered_kappa(kappa: Fraction) -> None:
    """The specification pin: kappa was registered BEFORE derivation; a
    coefficient picked to reproduce legacy outputs is rejected."""
    if Fraction(kappa) != KAPPA_REGISTERED:
        raise Nt2AuthorityError(
            f"kappa {Fraction(kappa)} != the specification-first registered "
            f"{KAPPA_REGISTERED} — coefficients are never chosen to match "
            "existing outputs"
        )


def seeded_admissible_draws(seeds: int, kappa: Fraction = KAPPA_REGISTERED
                            ) -> list[dict]:
    """Deterministic seeded admissible (Sigma, delta) draws with
    a2 = kappa*Sigma*(1+delta); every draw must be bracket-contained."""
    draws = []
    value = 246813579
    for _ in range(seeds):
        value = (1103515245 * value + 12345) % (2**31)
        sigma = Fraction(value % 887 + 1, 10**6)
        value = (1103515245 * value + 12345) % (2**31)
        # |delta| < R < 1: draw delta in (-1/2, 1/2), then take R STRICTLY
        # larger than |delta| so containment is tested in the interior of
        # the bracket, never only at a saturated endpoint.
        delta = Fraction((value % 799) - 399, 800)
        R = min(abs(delta) + Fraction(1, 16), Fraction(15, 16))
        a2 = kappa * sigma * (1 + delta)
        a3 = R * a2
        draws.append({"sigma": sigma, "delta": delta, "R": R,
                      "a2": a2, "a3": a3})
    return draws
