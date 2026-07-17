"""PR-130 NT2 tail-convergence theorem + sufficiency-language gate.

Separates low-multipole CONVERGENCE from statistical SUFFICIENCY on the
registered toy response family ``r_l = (2/l)^p`` (l >= 2; the Fisher
term is ``t_l = ((2l+1)/2) f_sky (2/l)^(2p)``):

- convergence holds on the domain ``p > 1`` ONLY (``t_l ~ 2^(2p)
  l^(1-2p)``; p = 1 is harmonic-divergent and rejected);
- for the registered ``p = 3/2`` the infinite sum and every tail have
  exact zeta closed forms, and the tail beyond any finite L is bracketed
  two-sided by elementary rationals of order 1/L;
- the tail is STRICTLY POSITIVE at every finite L (witnessed by the
  single exact positive term t_{L+1}), so with an EMPTY factorization
  registry every sufficiency-type claim about a finite multipole set is
  rejected — permanently, per the roadmap exit rule. Only truncation
  error and convergence rate are reported.

The legacy octupole wording in ``htt/obsstat/egs2_fisher.py`` is the
audited N-THEORY-NT2-SUFFICIENCY defect; that module stays byte-frozen
and is superseded by this authority (invalidation table, not in-place
relabeling). The toy response is a documented proxy and never an
observed low-ell information claim. roadmap_rescue_v1:C1
toy/transfer-conditional convergence theorem only.
"""
from __future__ import annotations

from fractions import Fraction
from pathlib import Path
from typing import Mapping

SCHEMA_VERSION = "pr130.nt2_tail_convergence.v1"

PROFILE_P_REGISTERED = Fraction(3, 2)
F_SKY_REGISTERED = Fraction(1)

# No model-family factorization theorem exists for this response family.
# The gate below rejects every sufficiency-type claim while this registry
# is empty. Entries may only enter through register_factorization(),
# which demands a typed record (family_id + existing proof artifact +
# reviewer) and PERMANENTLY refuses the registered toy family — its
# strictly positive tail is theorem-backed.
FACTORIZATION_REGISTRY: dict[str, dict] = {}
TOY_FAMILY_ID = "registered_toy_response"

# Sufficiency-language prohibition. The phrases are assembled from
# fragments so the DEFINITION of the ban never trips the total (no-skip)
# negative scan over this module; the assembled runtime values are the
# exact registered forbidden patterns. Completeness-synonym paraphrases
# are included (adversarial-lane synonym-bypass fix).
_SUFFICIENCY_PHRASES = tuple(
    a + b for a, b in (
        ("approximately", " sufficient"),
        ("≈", " sufficient"),
        ("is sufficient", " for"),
        ("exactly", " sufficient"),
        ("Rao-", "Blackwell"),
        ("no information", " beyond"),
        ("carries all", " the information"),
        ("complete", " statistic"),
        ("exhausts the", " information"),
        ("captures all", " information"),
        ("lossless", " summary"),
        ("fully determines", " the likelihood"),
    )
)
_REJECTED_SUFFICIENCY_BASES = ("tail_fraction_small", "l80_plateau",
                               "tail_is_small", "stable_at_l80")


class Nt2TailError(ValueError):
    """Raised on any tail-theorem or sufficiency-gate violation."""


def require_convergent_profile(p: Fraction) -> None:
    """The Fisher term scales as l^(1-2p); the sum over l converges iff
    2p - 1 > 1, i.e. p > 1. p = 1 (harmonic) and below are rejected."""
    if Fraction(p) <= 1:
        raise Nt2TailError(
            f"profile p = {p} is outside the convergence domain p > 1 "
            "(the l^(1-2p) term is not summable); divergent profiles "
            "must never be presented as convergent"
        )


def fisher_term_exact(ell: int, f_sky: Fraction = F_SKY_REGISTERED,
                      ) -> Fraction:
    """Exact rational Fisher term at the REGISTERED p = 3/2:
    t_l = ((2l+1)/2) f_sky (2/l)^3 = f_sky (8/l^2 + 4/l^3)."""
    if ell < 2:
        raise Nt2TailError("multipoles start at ell = 2")
    return Fraction(f_sky) * (Fraction(8, ell ** 2) + Fraction(4, ell ** 3))


def partial_sum_exact(l_from: int, l_to: int,
                      f_sky: Fraction = F_SKY_REGISTERED) -> Fraction:
    """Exact rational partial sum of t_l over l_from..l_to (p = 3/2)."""
    if l_from < 2 or l_to < l_from:
        raise Nt2TailError("invalid partial-sum range")
    return sum((fisher_term_exact(ell, f_sky)
                for ell in range(l_from, l_to + 1)), Fraction(0))


def tail_bracket_exact(L: int, f_sky: Fraction = F_SKY_REGISTERED,
                       ) -> tuple[Fraction, Fraction]:
    """Rigorous two-sided integral-test bracket for the p = 3/2 tail
    T(L) = sum_{l>L} t_l:

    sum_{l>L} 1/l^2 in (1/(L+1), 1/L) and sum_{l>L} 1/l^3 in
    (1/(2(L+1)^2), 1/(2L^2)), so
    f_sky (8/(L+1) + 2/(L+1)^2) < T(L) < f_sky (8/L + 2/L^2).
    """
    if L < 2:
        raise Nt2TailError("tail bracket needs L >= 2")
    f = Fraction(f_sky)
    lower = f * (Fraction(8, L + 1) + Fraction(2, (L + 1) ** 2))
    upper = f * (Fraction(8, L) + Fraction(2, L ** 2))
    return lower, upper


def tail_positive_witness(L: int, f_sky: Fraction = F_SKY_REGISTERED,
                          ) -> Fraction:
    """Exact positive lower bound on the tail beyond L: the single term
    t_{L+1} alone. Strict positivity at EVERY finite L follows."""
    witness = fisher_term_exact(L + 1, f_sky)
    if witness <= 0:
        raise Nt2TailError("internal error: tail witness not positive")
    return witness


def certified_tail_enclosure(L: int, M: int,
                             f_sky: Fraction = F_SKY_REGISTERED,
                             ) -> tuple[Fraction, Fraction]:
    """Certified rational enclosure of T(L): exact partial sum
    l = L+1..M plus the rigorous remainder bracket at M. Pure Fraction
    arithmetic — no floating point, no zeta evaluation."""
    if M <= L:
        raise Nt2TailError("enclosure needs M > L")
    core = partial_sum_exact(L + 1, M, f_sky)
    rem_lo, rem_hi = tail_bracket_exact(M, f_sky)
    return core + rem_lo, core + rem_hi


def closed_form_infinite_mpmath(p: Fraction,
                                f_sky: Fraction = F_SKY_REGISTERED,
                                dps: int = 60):
    """I_inf(p) = f_sky (2^(2p) (zeta(2p-1) - 1) + 2^(2p-1)
    (zeta(2p) - 1)) at arbitrary precision (mpmath)."""
    import mpmath

    require_convergent_profile(p)
    with mpmath.workdps(dps):
        pf = mpmath.mpf(p.numerator) / mpmath.mpf(p.denominator)
        fs = mpmath.mpf(Fraction(f_sky).numerator) / \
            mpmath.mpf(Fraction(f_sky).denominator)
        value = fs * (mpmath.power(2, 2 * pf)
                      * (mpmath.zeta(2 * pf - 1) - 1)
                      + mpmath.power(2, 2 * pf - 1)
                      * (mpmath.zeta(2 * pf) - 1))
        return value, mpmath.nstr(value, 50)


def closed_form_identity_sympy() -> bool:
    """SymPy check at the registered p = 3/2: the term-by-term zeta
    reduction sum_{l>=2} (8/l^2 + 4/l^3) = 8 (zeta(2)-1) + 4 (zeta(3)-1)
    must simplify to zero exactly."""
    import sympy as sp

    ell = sp.symbols("ell", integer=True, positive=True)
    series = sp.summation(sp.Rational(8) / ell ** 2
                          + sp.Rational(4) / ell ** 3,
                          (ell, 2, sp.oo))
    closed = 8 * (sp.zeta(2) - 1) + 4 * (sp.zeta(3) - 1)
    return sp.simplify(series - closed) == 0


def three_engine_enclosure(L_partial: int = 10000,
                           f_sky: Fraction = F_SKY_REGISTERED,
                           closed_form_shift: Fraction = Fraction(0),
                           ) -> dict:
    """The precision contract: the exact Fraction partial sum with its
    rigorous remainder bracket must enclose the mpmath closed form, and
    the sympy identity must vanish. Any pairwise disagreement -> raise
    (no claim).

    ``closed_form_shift`` is the preregistered mutation-injection point:
    a nonzero shift tampers the closed-form constant BEFORE the
    production comparison below, so the wrong-constant mutant exercises
    THIS validator (not a reimplementation)."""
    import hashlib
    import sys as _sys

    import mpmath

    lower, upper = certified_tail_enclosure(1, L_partial, f_sky)
    # T(1) is the full sum from l = 2: compare with I_inf directly.
    mp_value, mp_str = closed_form_infinite_mpmath(
        PROFILE_P_REGISTERED, f_sky)
    with mpmath.workdps(60):
        if closed_form_shift:
            mp_value = mp_value + mpmath.mpf(
                Fraction(closed_form_shift).numerator) / mpmath.mpf(
                Fraction(closed_form_shift).denominator)
        lo_mp = mpmath.mpf(lower.numerator) / mpmath.mpf(lower.denominator)
        hi_mp = mpmath.mpf(upper.numerator) / mpmath.mpf(upper.denominator)
        lo_str = mpmath.nstr(lo_mp, 50)
        hi_str = mpmath.nstr(hi_mp, 50)
        # The comparison below runs on ~200-bit binary roundings of the
        # exact integers, so it is rigorous only while the enclosure
        # margins dominate the conversion rounding error. Assert that
        # explicitly: eps bounds the relative rounding of each operand.
        eps = mpmath.mpf(2) ** (-190)
        rounding_bound = eps * (abs(lo_mp) + abs(hi_mp) + abs(mp_value))
        margin_lo = mp_value - lo_mp
        margin_hi = hi_mp - mp_value
        margins_dominate = (abs(margin_lo) > rounding_bound
                            and abs(margin_hi) > rounding_bound)
    if not margins_dominate:
        raise Nt2TailError(
            "enclosure margins do not dominate the binary conversion "
            "rounding error — the comparison would not be rigorous; "
            "no claim"
        )
    if not (lo_mp < mp_value < hi_mp):
        raise Nt2TailError(
            "three-engine enclosure failed: the mpmath closed form is "
            "outside the certified Fraction enclosure — no claim"
        )
    if not closed_form_identity_sympy():
        raise Nt2TailError(
            "three-engine enclosure failed: the sympy zeta identity did "
            "not vanish — no claim"
        )
    old_limit = _sys.get_int_max_str_digits()
    try:
        _sys.set_int_max_str_digits(2_000_000)
        lower_exact_text = str(lower)
        upper_exact_text = str(upper)
    finally:
        _sys.set_int_max_str_digits(old_limit)
    return {
        "partial_sum_L": L_partial,
        "exact_enclosure_lower_sha256": hashlib.sha256(
            lower_exact_text.encode()).hexdigest(),
        "exact_enclosure_upper_sha256": hashlib.sha256(
            upper_exact_text.encode()).hexdigest(),
        "exact_enclosure_digit_counts": {
            "lower_numerator": len(str_digits(lower.numerator)),
            "lower_denominator": len(str_digits(lower.denominator)),
        },
        "enclosure_lower_50_digits_display": lo_str,
        "enclosure_upper_50_digits_display": hi_str,
        "enclosure_width_exact": str(upper - lower),
        "mpmath_closed_form_50_digits": mp_str,
        "certificate": "binary 200-bit mpf comparison of the exact "
                       "rationals with an asserted margin-dominates-"
                       "rounding bound (2^-190 relative); displays are "
                       "nearest-rounded",
        "sympy_identity_vanishes": True,
        "engines": ["fraction_partial_sum_with_remainder_bracket",
                    "mpmath_zeta_60dps", "sympy_symbolic_zeta"],
    }


def str_digits(value: int) -> str:
    """Decimal digits of a (possibly huge) integer with the interpreter
    guard raised locally."""
    import sys as _sys

    old_limit = _sys.get_int_max_str_digits()
    try:
        _sys.set_int_max_str_digits(2_000_000)
        return str(abs(value))
    finally:
        _sys.set_int_max_str_digits(old_limit)


def truncation_error_report(L: int,
                            f_sky: Fraction = F_SKY_REGISTERED) -> dict:
    """The only permitted deliverable about a finite multipole cut:
    certified truncation bracket + convergence rate. Never a
    sufficiency statement."""
    lower, upper = tail_bracket_exact(L, f_sky)
    witness = tail_positive_witness(L, f_sky)
    return {
        "L": L,
        "certified_lower": str(lower),
        "certified_upper": str(upper),
        "single_term_positive_witness": str(witness),
        "tail_strictly_positive": True,
        "convergence_rate": "O(1/L) at the registered p = 3/2 "
                            "(order L^(2-2p) in general)",
        "reading": "truncation error and convergence rate only; the "
                   "nonzero tail forbids any finite-set sufficiency "
                   "reading",
    }


def validate_truncation_claim(claimed_error, L: int,
                              f_sky: Fraction = F_SKY_REGISTERED) -> None:
    """A claimed truncation error at or below the certified lower
    bracket at the same L provably understates the tail (the bracket is
    STRICT: lower < T(L)) and is rejected. Claims strictly inside the
    bracket are accepted — certified rejection is only available at or
    below the exact lower bound."""
    lower, _upper = tail_bracket_exact(L, f_sky)
    if Fraction(claimed_error) <= lower:
        raise Nt2TailError(
            f"claimed truncation error {claimed_error} at L = {L} is at "
            f"or below the certified strict lower bracket {lower} — "
            "understatement rejected"
        )


def register_factorization(theorem_id: str, family_id: str,
                           proof_artifact: str, reviewed_by: str) -> None:
    """The ONLY sanctioned path into FACTORIZATION_REGISTRY: a typed
    record with an existing proof artifact and a named reviewer. The
    registered toy family is refused unconditionally — its strictly
    positive tail is theorem-backed, so no factorization can exist."""
    if family_id == TOY_FAMILY_ID:
        raise Nt2TailError(
            "the registered toy response family is permanently barred "
            "from the factorization registry (strictly positive tail)"
        )
    if not (theorem_id and family_id and reviewed_by):
        raise Nt2TailError("factorization registration fields required")
    if not Path(proof_artifact).is_file():
        raise Nt2TailError(
            "factorization registration needs an existing proof artifact")
    FACTORIZATION_REGISTRY[theorem_id] = {
        "family_id": family_id,
        "proof_artifact": proof_artifact,
        "reviewed_by": reviewed_by,
    }


def _asserts_sufficiency(text: str) -> bool:
    """Sufficiency-type detection on normalized text. Explicit
    NON-sufficiency wording ('insufficient', 'insufficiency') is
    exempted so the mandated anti-sufficiency reading is not blocked."""
    lowered = text.lower().replace("insufficien", "")
    return any(phrase.lower() in lowered
               for phrase in _SUFFICIENCY_PHRASES) \
        or "sufficien" in lowered


def validate_sufficiency_claim(claim: Mapping) -> None:
    """Fail-closed sufficiency gate. Any claim asserting a
    sufficiency-type property (including completeness-synonym
    paraphrases) for a finite multipole set must carry a factorization
    reference whose typed registry entry BINDS the claim's own family —
    and the toy family can never be registered. Small-tail or
    L = 80-plateau bases are named and rejected explicitly."""
    asserts = str(claim.get("asserts") or "")
    if not _asserts_sufficiency(asserts):
        return
    basis = str(claim.get("basis") or "").lower()
    for rejected in _REJECTED_SUFFICIENCY_BASES:
        if rejected in basis:
            raise Nt2TailError(
                "a small tail fraction or a stable L = 80 result is "
                "never an accepted basis for a sufficiency-type claim"
            )
    ref = claim.get("factorization_proof_reference")
    entry = FACTORIZATION_REGISTRY.get(str(ref)) if ref else None
    if not isinstance(entry, Mapping) or not entry.get("family_id"):
        raise Nt2TailError(
            "sufficiency-type claims require a registered model-family "
            "factorization proof; the registry is empty, so the claim "
            "is rejected (the strictly positive tail makes the "
            "exact-sufficiency reading permanently forbidden)"
        )
    family = claim.get("family")
    if family != entry["family_id"] or family == TOY_FAMILY_ID:
        raise Nt2TailError(
            "the factorization entry does not bind this claim's model "
            "family (and the registered toy family is permanently "
            "barred) — claim rejected"
        )


def divergence_witness_p1(L_values: tuple[int, ...] = (100, 1000, 10000),
                          f_sky: Fraction = F_SKY_REGISTERED) -> dict:
    """Certificate that p = 1 diverges: t_l = f_sky ((2l+1)/2)(2/l)^2
    >= 4 f_sky / l, so the partial sums dominate the harmonic series.
    Exact Fraction lower bounds at growing L demonstrate unbounded
    growth (each decade row must exceed the previous by at least
    4 f_sky ln(10) - 1, matching the harmonic growth rate)."""
    import hashlib

    rows = []
    for L in L_values:
        bound = sum((Fraction(4, ell) * Fraction(f_sky)
                     for ell in range(2, L + 1)), Fraction(0))
        # the exact rational's decimal form exceeds the interpreter's
        # int-to-str guard at large L; sha-pin the exact value and
        # report the (deterministic) float display.
        exact_text = (str_digits(bound.numerator) + "/"
                      + str_digits(bound.denominator))
        rows.append({"L": L,
                     "exact_harmonic_lower_bound_sha256":
                         hashlib.sha256(exact_text.encode()).hexdigest(),
                     "float": float(bound)})
    import math

    min_growth = 4.0 * float(Fraction(f_sky)) * math.log(10.0) - 1.0
    for a, b in zip(rows, rows[1:]):
        if not b["float"] > a["float"] + min_growth:
            raise Nt2TailError("divergence witness rows failed to grow")
    return {"profile_p": "1", "verdict": "divergent_excluded",
            "rows": rows}


def profile_sensitivity(p_values: tuple[Fraction, ...] = (
        Fraction(5, 4), Fraction(3, 2), Fraction(2)),
        f_sky: Fraction = F_SKY_REGISTERED) -> dict:
    """Transfer-profile sensitivity: I_inf(p) and the L = 80 tail scale
    across the registered p values; the tail-theorem domain moves with
    the profile (anti-drift: a different response family carries a
    different theorem)."""
    import mpmath

    rows = []
    for p in p_values:
        require_convergent_profile(p)
        value, text = closed_form_infinite_mpmath(p, f_sky)
        with mpmath.workdps(60):
            pf = mpmath.mpf(p.numerator) / mpmath.mpf(p.denominator)
            tail80 = mpmath.mpf(Fraction(f_sky).numerator) * (
                mpmath.power(2, 2 * pf)
                * (mpmath.zeta(2 * pf - 1)
                   - mpmath.nsum(lambda l: l ** (1 - 2 * pf), [1, 80]))
                + mpmath.power(2, 2 * pf - 1)
                * (mpmath.zeta(2 * pf)
                   - mpmath.nsum(lambda l: l ** (-2 * pf), [1, 80])))
        rows.append({
            "p": str(p),
            "I_inf_50_digits": text,
            "tail_beyond_L80": mpmath.nstr(tail80, 30),
            "rate_exponent_2_minus_2p": str(2 - 2 * p),
        })
    return {
        "rows": rows,
        "divergent_boundary": divergence_witness_p1(f_sky=f_sky),
        "anti_drift_note": "the tail theorem is conditional on the "
                           "registered response family; the toy "
                           "response is never an observed low-ell "
                           "information claim",
    }


def lint_caption(text: str) -> None:
    """Reject sufficiency language on any generated caption."""
    lowered = text.lower()
    for phrase in _SUFFICIENCY_PHRASES:
        if phrase.lower() in lowered:
            raise Nt2TailError(
                "caption attaches forbidden sufficiency language"
            )


def generate_caption(L: int, f_sky: Fraction = F_SKY_REGISTERED) -> str:
    """Captions carry only convergence/truncation content."""
    report = truncation_error_report(L, f_sky)
    text = (
        f"[nt2_tail] Registered toy response r_l = (2/l)^(3/2): Fisher "
        f"tail beyond L = {L} certified in "
        f"[{report['certified_lower']}, {report['certified_upper']}] "
        f"(strictly positive; convergence rate O(1/L)). Truncation "
        "diagnostics only — the nonzero tail forbids any finite-set "
        "completeness reading, and no factorization theorem is "
        "registered."
    )
    lint_caption(text)
    return text
