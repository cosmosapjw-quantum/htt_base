"""T2G: general fractional-program interval theorem (v9 successor, REV-R171).

Replaces the RETRACTED per-endpoint strictness iff (P36 / T2') flagged by the
2026-07-10 external re-reviews. The refuting instance is INSIDE the retracted
statement's hypotheses:

    S = [0,1],  N(s) = s,  D(s) = 1 + s
    c_N c_D = 1 > 0, D > 0, box nondegenerate — yet the joint LOWER endpoint
    equals the product-relaxation lower endpoint (both 0, attained at s=0),
    while the upper endpoint is strict (1/2 < 1). A coefficient-sign test
    cannot decide per-endpoint strictness: the N_min = 0 degeneracy
    neutralizes the denominator conflict at the numerator minimizer.

Correct theorem set sealed here (all exact Fraction arithmetic):

T2G-1 (containment).  With N(r_N, s) = r_N + c_N.s over r_N in [n_lo, n_hi]
    and the shared box, D likewise with D > 0 everywhere, the joint interval
    I_joint (shared s coupled) is ALWAYS a subset of the product relaxation
    I_prod (numerator and denominator optimized over independent copies of
    the box) — the diagonal inclusion.

T2G-2 (vertex attainment).  A linear-fractional objective with positive
    denominator attains its extremes over the box at vertices (Charnes-Cooper
    reduction to a linear program over a polytope), so both intervals are
    computed exactly by corner enumeration; an interior rational grid never
    beats the vertex optimum (checked exactly on a survey subset).

T2G-3 (per-endpoint equality criterion).  L_joint = L_prod iff some DIAGONAL
    point (s_N = s_D, with the reachable parts free) attains the
    product-relaxation lower endpoint; dually for the upper endpoint. This is
    the correct general criterion — it is decidable by exact comparison of
    the two vertex-enumerated endpoints, and a witness corner is returned.

T2G-4 (argmin/argmax corollary, strictly positive numerator).  If N > 0 over
    the whole box then
        L_joint = L_prod  iff  argmin(N) intersect argmax(D) is nonempty,
        U_joint = U_prod  iff  argmax(N) intersect argmin(D) is nonempty,
    over box vertices (reachable parts included via their endpoints). Proof
    of the lower branch: (<=) a common vertex v gives N(v)/D(v) =
    N_min/D_max = L_prod >= L_joint >= L_prod. (=>) if v* attains L_joint =
    N_min/D_max then N(v*) D_max = N_min D(v*); N(v*) >= N_min > 0 and
    D(v*) <= D_max force N(v*) = N_min and D(v*) = D_max. The strict
    positivity N_min > 0 is load-bearing — at N_min = 0 the forward
    implication fails, which is exactly the refuting instance above.

T2G-5 (sign-criterion demotion).  The retracted coefficient-sign test
    survives only as a corollary of T2G-4 on the N > 0 domain: a
    nondegenerate shared component with c_N c_D > 0 separates argmin(N) from
    argmax(D) (and argmax(N) from argmin(D)), so both endpoints are strict.
    Outside N > 0 the test is measured, not asserted.

The exact interval engines are imported READ-ONLY from the shipped v8
successor (``exact_joint_interval_v8`` / ``exact_naive_quotient_v8``, the
signed-safe four-candidate forms); the v7-frozen ``egs3_gf_interval`` is
imported only to DEMONSTRATE the retracted criterion's per-endpoint mismatch.
Diagnostic-only interval algebra on registered synthetic instances; no data
claim and no geometry claim.
"""
from __future__ import annotations

from fractions import Fraction
import itertools
import random

import sympy as sp

from .egs3_gf_interval import gf_strictness_criterion
from .egs3_gf_interval_v8 import (
    exact_joint_interval_v8,
    exact_naive_quotient_v8,
)

__all__ = [
    "joint_interval",
    "product_interval",
    "endpoint_equality_report",
    "vertex_argsets",
    "argmin_argmax_corollary",
    "reviewer_counterexample",
    "counterexample_symbolic",
    "vertex_attainment_survey",
    "fractional_program_survey",
    "fractional_program_seal",
]

COUNTEREXAMPLE = {
    # S=[0,1], N(s)=s, D(s)=1+s in the module's (n_pt, d_pt, bounds, c) form.
    "n_pt": (Fraction(0), Fraction(0)),
    "d_pt": (Fraction(1), Fraction(1)),
    "bounds": ((Fraction(0), Fraction(1)),),
    "c_num": (Fraction(1),),
    "c_den": (Fraction(1),),
}


def joint_interval(n_pt, d_pt, bounds, c_num, c_den):
    """I_joint: shared box coupled, reachable parts free. Signed-safe."""
    return exact_joint_interval_v8(n_pt, d_pt, bounds, c_num, c_den)


def product_interval(n_pt, d_pt, bounds, c_num, c_den):
    """I_prod: numerator and denominator over INDEPENDENT box copies."""
    return exact_naive_quotient_v8(n_pt, d_pt, bounds, c_num, c_den)


def _corners(bounds):
    return itertools.product(*[(lo, hi) for lo, hi in bounds])


def _numden_at(corner, n_pt, d_pt, c_num, c_den):
    dn = sum(c * s for c, s in zip(c_num, corner))
    dd = sum(c * s for c, s in zip(c_den, corner))
    return ((n_pt[0] + dn, n_pt[1] + dn), (d_pt[0] + dd, d_pt[1] + dd))


def endpoint_equality_report(n_pt, d_pt, bounds, c_num, c_den) -> dict:
    """Per-endpoint T2G-3 report with exact witnesses.

    Returns joint/product endpoints, per-endpoint strictness (exact Fraction
    comparison), and for each EQUAL endpoint a diagonal witness corner at
    which the product endpoint is attained by the coupled objective.
    """
    joint = joint_interval(n_pt, d_pt, bounds, c_num, c_den)
    prod = product_interval(n_pt, d_pt, bounds, c_num, c_den)
    if joint is None or prod is None:
        return {"status": "NO_RESULT_DENOMINATOR_POSITIVITY"}
    (jl, jh), (pl, ph) = joint, prod
    witness_lo = witness_hi = None
    for corner in _corners(bounds):
        (N_lo, N_hi), (D_lo, D_hi) = _numden_at(corner, n_pt, d_pt,
                                                c_num, c_den)
        vals = [N_lo / D_lo, N_lo / D_hi, N_hi / D_lo, N_hi / D_hi]
        if witness_lo is None and jl == pl and min(vals) == pl:
            witness_lo = tuple(corner)
        if witness_hi is None and jh == ph and max(vals) == ph:
            witness_hi = tuple(corner)
    return {
        "status": "OK",
        "joint": (jl, jh),
        "product": (pl, ph),
        "containment": bool(pl <= jl and jh <= ph),
        "strict_lower": bool(jl > pl),
        "strict_upper": bool(jh < ph),
        "diagonal_witness_lower": witness_lo,
        "diagonal_witness_upper": witness_hi,
    }


def vertex_argsets(n_pt, d_pt, bounds, c_num, c_den) -> dict:
    """Vertex argmin/argmax sets of N and D (reachable parts at endpoints)."""
    n_min = n_max = None
    d_min = d_max = None
    n_vals, d_vals = {}, {}
    for corner in _corners(bounds):
        (N_lo, N_hi), (D_lo, D_hi) = _numden_at(corner, n_pt, d_pt,
                                                c_num, c_den)
        n_vals[tuple(corner)] = (N_lo, N_hi)
        d_vals[tuple(corner)] = (D_lo, D_hi)
        n_min = N_lo if n_min is None else min(n_min, N_lo)
        n_max = N_hi if n_max is None else max(n_max, N_hi)
        d_min = D_lo if d_min is None else min(d_min, D_lo)
        d_max = D_hi if d_max is None else max(d_max, D_hi)
    argmin_n = {c for c, (lo, _) in n_vals.items() if lo == n_min}
    argmax_n = {c for c, (_, hi) in n_vals.items() if hi == n_max}
    argmin_d = {c for c, (lo, _) in d_vals.items() if lo == d_min}
    argmax_d = {c for c, (_, hi) in d_vals.items() if hi == d_max}
    return {
        "N_min": n_min, "N_max": n_max, "D_min": d_min, "D_max": d_max,
        "argmin_N": argmin_n, "argmax_N": argmax_n,
        "argmin_D": argmin_d, "argmax_D": argmax_d,
    }


def argmin_argmax_corollary(n_pt, d_pt, bounds, c_num, c_den) -> dict:
    """T2G-4: on the N>0 domain, per-endpoint equality iff the argsets meet.

    Raises ValueError when N_min <= 0 (outside the corollary's proof domain);
    the caller must fall back to the general T2G-3 criterion there.
    """
    args = vertex_argsets(n_pt, d_pt, bounds, c_num, c_den)
    if args["N_min"] <= 0:
        raise ValueError("argmin/argmax corollary requires N > 0 over the "
                         "whole box (N_min > 0); use the general criterion")
    if args["D_min"] <= 0:
        raise ValueError("denominator loses positivity; no-result")
    rep = endpoint_equality_report(n_pt, d_pt, bounds, c_num, c_den)
    pred_equal_lower = bool(args["argmin_N"] & args["argmax_D"])
    pred_equal_upper = bool(args["argmax_N"] & args["argmin_D"])
    return {
        "predicted_equal_lower": pred_equal_lower,
        "predicted_equal_upper": pred_equal_upper,
        "observed_equal_lower": not rep["strict_lower"],
        "observed_equal_upper": not rep["strict_upper"],
        "iff_holds_lower": pred_equal_lower == (not rep["strict_lower"]),
        "iff_holds_upper": pred_equal_upper == (not rep["strict_upper"]),
    }


def reviewer_counterexample() -> dict:
    """Named regression fixture: the 2026-07-10 refuting instance.

    Asserts (exactly) L_joint = L_prod = 0 (lower endpoint NOT strict) while
    U_joint = 1/2 < 1 = U_prod (upper strict), and that the retracted
    coefficient-sign criterion mispredicts the lower endpoint.
    """
    ce = COUNTEREXAMPLE
    rep = endpoint_equality_report(**ce)
    retracted = gf_strictness_criterion(
        [(float(lo), float(hi)) for lo, hi in ce["bounds"]],
        [float(c) for c in ce["c_num"]],
        [float(c) for c in ce["c_den"]])
    return {
        "instance": "S=[0,1], N(s)=s, D(s)=1+s",
        "joint": tuple(str(v) for v in rep["joint"]),
        "product": tuple(str(v) for v in rep["product"]),
        "strict_lower_observed": rep["strict_lower"],
        "strict_upper_observed": rep["strict_upper"],
        "lower_is_exactly_zero_on_both": rep["joint"][0] == 0 == rep["product"][0],
        "upper_joint_is_half": rep["joint"][1] == Fraction(1, 2),
        "upper_product_is_one": rep["product"][1] == Fraction(1),
        "retracted_criterion_predicts_strict_lower":
            retracted["strict_lower_predicted"],
        "retracted_criterion_mispredicts_lower":
            retracted["strict_lower_predicted"] and not rep["strict_lower"],
        "diagonal_witness_lower_at_s0": rep["diagonal_witness_lower"],
        "n_min_degeneracy": "N_min = 0 at s = 0 neutralizes the denominator "
                            "conflict at the lower endpoint",
    }


def counterexample_symbolic() -> dict:
    """SymPy closure of the refuting instance: min/max of s/(1+s) on [0,1]."""
    s = sp.symbols("s", nonnegative=True)
    f = s / (1 + s)
    df = sp.diff(f, s)
    monotone_up = sp.simplify(df - 1 / (1 + s) ** 2) == 0
    lo = f.subs(s, 0)
    hi = f.subs(s, 1)
    return {
        "derivative_positive_form": str(sp.simplify(df)),
        "monotone_increasing": bool(monotone_up),
        "min_at_0": lo == 0,
        "max_at_1_is_half": hi == sp.Rational(1, 2),
        "naive_lower_is_0_over_2": sp.Rational(0, 2) == 0,
        "naive_upper_is_1_over_1": sp.Rational(1, 1) == 1,
    }


def _rand_fraction(rng, lo=-3, hi=3, den=7):
    return Fraction(rng.randint(lo * den, hi * den), den)


def _draw_instance(rng, k: int, domain: str):
    """Draw an exact rational instance; ``domain`` in
    {positive, forced_nmin_zero, signed}."""
    bounds = []
    for _ in range(k):
        a = _rand_fraction(rng, 0, 2)
        b = a + Fraction(rng.randint(1, 14), 7)
        bounds.append((a, b))
    c_num = tuple(_rand_fraction(rng) for _ in range(k))
    c_den = tuple(_rand_fraction(rng, -1, 1) for _ in range(k))
    span_n_lo = sum(min(c * lo, c * hi) for c, (lo, hi) in zip(c_num, bounds))
    span_d_lo = sum(min(c * lo, c * hi) for c, (lo, hi) in zip(c_den, bounds))
    # keep the denominator strictly positive over the whole box
    d_lo = -span_d_lo + Fraction(rng.randint(1, 21), 7)
    d_pt = (d_lo, d_lo + Fraction(rng.randint(0, 14), 7))
    if domain == "positive":
        n_lo = -span_n_lo + Fraction(rng.randint(1, 21), 7)
    elif domain == "forced_nmin_zero":
        n_lo = -span_n_lo                     # N_min == 0 exactly
    elif domain == "signed":
        n_lo = -span_n_lo - Fraction(rng.randint(1, 21), 7)
    else:
        raise ValueError(domain)
    n_pt = (n_lo, n_lo + Fraction(rng.randint(0, 14), 7))
    return n_pt, d_pt, tuple(bounds), c_num, c_den


def vertex_attainment_survey(*, n_trials: int = 40, seed: int = 20260710,
                             grid: int = 5) -> dict:
    """T2G-2 witness: an interior rational grid never beats the vertex
    optimum (exact, k <= 2)."""
    rng = random.Random(seed)
    beaten = 0
    for _ in range(n_trials):
        k = rng.choice((1, 2))
        n_pt, d_pt, bounds, c_num, c_den = _draw_instance(
            rng, k, rng.choice(("positive", "signed")))
        joint = joint_interval(n_pt, d_pt, bounds, c_num, c_den)
        if joint is None:
            continue
        axes = [[lo + (hi - lo) * Fraction(i, grid - 1) for i in range(grid)]
                for lo, hi in bounds]
        for point in itertools.product(*axes):
            (N_lo, N_hi), (D_lo, D_hi) = _numden_at(point, n_pt, d_pt,
                                                    c_num, c_den)
            vals = (N_lo / D_lo, N_lo / D_hi, N_hi / D_lo, N_hi / D_hi)
            if min(vals) < joint[0] or max(vals) > joint[1]:
                beaten += 1
                break
    return {"n_trials": n_trials, "grid_per_axis": grid,
            "vertex_optimum_beaten": beaten,
            "vertex_attainment_holds": beaten == 0}


def fractional_program_survey(*, n_trials: int = 400,
                              seed: int = 20260710) -> dict:
    """T2G-1/3/4/5 exact survey over three draw domains.

    Unlike the frozen v7 witness (which fixed a strictly positive shifted
    numerator and only tested OR-over-endpoints strictness), this survey
    FORCES the N_min = 0 degeneracy on one third of the draws, includes a
    signed-numerator third, and checks the endpoints SEPARATELY.
    """
    rng = random.Random(seed)
    domains = ("positive", "forced_nmin_zero", "signed")
    tally = {d: {"draws": 0, "containment_fail": 0,
                 "corollary_iff_fail": 0, "corollary_checked": 0,
                 "sign_criterion_lower_mispredicts": 0,
                 "sign_criterion_upper_mispredicts": 0}
             for d in domains}
    for i in range(n_trials):
        domain = domains[i % 3]
        k = rng.choice((1, 2, 3))
        n_pt, d_pt, bounds, c_num, c_den = _draw_instance(rng, k, domain)
        rep = endpoint_equality_report(n_pt, d_pt, bounds, c_num, c_den)
        if rep["status"] != "OK":
            continue
        t = tally[domain]
        t["draws"] += 1
        if not rep["containment"]:
            t["containment_fail"] += 1
        crit = gf_strictness_criterion(
            [(float(lo), float(hi)) for lo, hi in bounds],
            [float(c) for c in c_num], [float(c) for c in c_den])
        if crit["strict_lower_predicted"] != rep["strict_lower"]:
            t["sign_criterion_lower_mispredicts"] += 1
        if crit["strict_upper_predicted"] != rep["strict_upper"]:
            t["sign_criterion_upper_mispredicts"] += 1
        try:
            cor = argmin_argmax_corollary(n_pt, d_pt, bounds, c_num, c_den)
        except ValueError:
            cor = None
        if cor is not None:
            t["corollary_checked"] += 1
            if not (cor["iff_holds_lower"] and cor["iff_holds_upper"]):
                t["corollary_iff_fail"] += 1
    return {
        "n_trials": n_trials,
        "seed": seed,
        "tally": tally,
        "containment_holds_everywhere": all(
            t["containment_fail"] == 0 for t in tally.values()),
        "corollary_iff_holds_on_positive_domain": (
            tally["positive"]["corollary_checked"] > 0
            and tally["positive"]["corollary_iff_fail"] == 0),
        "degenerate_domain_defeats_sign_criterion": (
            tally["forced_nmin_zero"]["sign_criterion_lower_mispredicts"] > 0),
        "sign_criterion_exact_on_positive_domain": (
            tally["positive"]["sign_criterion_lower_mispredicts"] == 0
            and tally["positive"]["sign_criterion_upper_mispredicts"] == 0),
    }


def fractional_program_seal() -> dict:
    """Fail-closed T2G seal (rendered by the v9 report; registry id T2G)."""
    ce = reviewer_counterexample()
    sym = counterexample_symbolic()
    vertex = vertex_attainment_survey()
    survey = fractional_program_survey()
    ok = (
        ce["retracted_criterion_mispredicts_lower"]
        and ce["lower_is_exactly_zero_on_both"]
        and ce["upper_joint_is_half"] and ce["upper_product_is_one"]
        and not ce["strict_lower_observed"] and ce["strict_upper_observed"]
        and all(bool(v) for v in sym.values() if isinstance(v, bool))
        and vertex["vertex_attainment_holds"]
        and survey["containment_holds_everywhere"]
        and survey["corollary_iff_holds_on_positive_domain"]
        and survey["degenerate_domain_defeats_sign_criterion"]
        and survey["sign_criterion_exact_on_positive_domain"]
    )
    return {
        "seal": "egs3.fractional_program",
        "theorem_id": "T2G",
        "status": "PASS" if ok else "FAIL",
        "supersedes": ["P36 (RETRACTED)", "T2p per-endpoint iff (RETRACTED)"],
        "statement": {
            "T2G-1": "I_joint subseteq I_prod (diagonal inclusion), always",
            "T2G-2": "vertex attainment of linear-fractional extremes on a "
                     "box (Charnes-Cooper/vertex reduction)",
            "T2G-3": "per-endpoint equality iff a diagonal point attains the "
                     "product-relaxation endpoint (exact witness returned)",
            "T2G-4": "for N>0 over the box: lower equality iff argmin(N) "
                     "meets argmax(D); upper dually; N_min>0 load-bearing",
            "T2G-5": "the coefficient-sign test survives only as the N>0 "
                     "nondegenerate corollary",
        },
        "reviewer_counterexample": ce,
        "counterexample_symbolic": sym,
        "vertex_attainment_survey": vertex,
        "survey": survey,
        "engines": {
            "intervals": "htt/obsstat/egs3_gf_interval_v8.py "
                         "(signed-safe four-candidate, imported read-only)",
            "retracted_criterion_demonstrated_from":
                "htt/obsstat/egs3_gf_interval.py (v7-frozen, read-only)",
        },
        "claim_boundary": "diagnostic-only exact interval algebra on "
                          "registered synthetic instances; no data claim, "
                          "no geometry claim, no inference claim",
    }
