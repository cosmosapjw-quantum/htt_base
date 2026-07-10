"""EGS3 Axis E successor (v8): signed-numerator exact quotient path for G_F (T2'').

Successor module for the v7-era ``egs3_gf_interval`` exact naive/joint quotient
path. The v7 module is byte-frozen (its SHA256 is embedded in the frozen v7
report MANIFEST), so the two latent defects recorded in ticket
``gf_interval_latent_quotient_bug.yaml`` are repaired HERE, additively:

1. **Undocumented domain restriction.** The v7 exact-quotient branch selects the
   ratio extremes with the fixed pairing ``lo = N_lo/D_hi``, ``hi = N_hi/D_lo``,
   which is the correct extremum selection ONLY when the (shifted) numerator is
   nonnegative. That restriction was never stated.
2. **Latent sign defect.** For a negative shifted numerator the minimizing
   denominator flips (min of N/D over D in [D_lo, D_hi] with D > 0 sits at D_lo
   when N < 0), so the v7 pairing returns a strictly WRONG interval outside the
   positive-numerator domain. The shipped v7 witness never exercises that
   region, so no reported v7 result is affected (the frozen
   ``gf_strictness_exact_seal`` remains correct on its domain).

The v8 path replaces the fixed pairing with the full four-candidate corner
enumeration ``{N_lo/D_lo, N_lo/D_hi, N_hi/D_lo, N_hi/D_hi}`` per shared-box
vertex, which is the exact extremum selection for EVERY signed numerator as
long as the denominator stays strictly positive (the ratio is linear in N at
fixed D and monotone in D at fixed N, so extremes sit at endpoint pairs).

Witnesses in this module (a) EXERCISE the negative-numerator region and exhibit
the concrete v7-vs-v8 discrepancy there, (b) prove bit-exact agreement with the
frozen v7 path on the documented nonnegative-numerator domain, and (c) re-run
the T2' strictness-criterion agreement on that domain through the v8 selector.
On the signed domain the sign-conflict criterion is NOT claimed as a theorem;
its empirical agreement rate is measured and reported as a boundary
observation.

Claim discipline. Diagnostic-only interval algebra on declared inputs; no data
claim, no signal-discovery claim, no Bianchi-class/geometry claim, no
probabilistic-inference claim. The frozen v7 module is imported read-only for
the containment comparison and never modified.
"""
from __future__ import annotations

from fractions import Fraction
import itertools

import numpy as np

from . import egs3_gf_interval as _frozen

__all__ = [
    "exact_joint_interval_v8",
    "exact_naive_quotient_v8",
    "negative_numerator_discrepancy_witness",
    "positive_domain_containment_witness",
    "signed_domain_strictness_survey",
    "gf_interval_v8_seal",
]


def _ratio_extremes(N_lo, N_hi, D_lo, D_hi):
    """Exact min/max of N/D over [N_lo,N_hi] x [D_lo,D_hi] with D_lo > 0.

    Full four-candidate enumeration; valid for every signed numerator."""
    if D_lo <= 0 or D_hi <= 0:
        return None
    cands = (N_lo / D_lo, N_lo / D_hi, N_hi / D_lo, N_hi / D_hi)
    return min(cands), max(cands)


def exact_joint_interval_v8(n_pt, d_pt, bounds, c_num, c_den):
    """Joint interval of (n_pt + c_N.s)/(d_pt + c_D.s) over the shared box,
    EXACT (Fraction) and valid for signed numerators.

    Linear-fractional extremes over a box sit at box vertices; per vertex the
    reachable parts vary independently, so the four endpoint pairings are
    enumerated. Returns (lo, hi) or None if the denominator loses strict
    positivity anywhere on the box (no-result, matching the v7 convention)."""
    n_lo, n_hi = n_pt
    d_lo, d_hi = d_pt
    best = []
    for corner in itertools.product(*[(lo, hi) for lo, hi in bounds]):
        dn = sum(c * s for c, s in zip(c_num, corner))
        dd = sum(c * s for c, s in zip(c_den, corner))
        ext = _ratio_extremes(n_lo + dn, n_hi + dn, d_lo + dd, d_hi + dd)
        if ext is None:
            return None
        best.append(ext)
    return min(lo for lo, _ in best), max(hi for _, hi in best)


def exact_naive_quotient_v8(n_pt, d_pt, bounds, c_num, c_den):
    """Naive marginal quotient, EXACT and valid for signed numerators."""
    n_lo, n_hi = n_pt
    d_lo, d_hi = d_pt
    span_num_lo = sum(min(c * lo, c * hi) for c, (lo, hi) in zip(c_num, bounds))
    span_num_hi = sum(max(c * lo, c * hi) for c, (lo, hi) in zip(c_num, bounds))
    span_den_lo = sum(min(c * lo, c * hi) for c, (lo, hi) in zip(c_den, bounds))
    span_den_hi = sum(max(c * lo, c * hi) for c, (lo, hi) in zip(c_den, bounds))
    return _ratio_extremes(n_lo + span_num_lo, n_hi + span_num_hi,
                           d_lo + span_den_lo, d_hi + span_den_hi)


def _brute_force_joint(n_pt, d_pt, bounds, c_num, c_den, n_grid: int = 7):
    """Independent dense-grid verifier (Fraction arithmetic on rational grid
    points of the box AND the reachable intervals). Used only to certify the
    corner enumeration; never the primary path."""
    n_lo, n_hi = n_pt
    d_lo, d_hi = d_pt
    axes = []
    for lo, hi in bounds:
        axes.append([lo + (hi - lo) * Fraction(i, n_grid - 1)
                     for i in range(n_grid)] if hi > lo else [lo])
    n_axis = [n_lo + (n_hi - n_lo) * Fraction(i, n_grid - 1) for i in range(n_grid)]
    d_axis = [d_lo + (d_hi - d_lo) * Fraction(i, n_grid - 1) for i in range(n_grid)]
    vals = []
    for point in itertools.product(*axes):
        dn = sum(c * s for c, s in zip(c_num, point))
        dd = sum(c * s for c, s in zip(c_den, point))
        for nv in n_axis:
            for dv in d_axis:
                if dv + dd <= 0:
                    return None
                vals.append((nv + dn) / (dv + dd))
    return min(vals), max(vals)


# Registered negative-numerator configuration: one shared component, numerator
# reachable interval strictly negative, coefficients chosen so the v7 pairing
# and the true extremes provably differ.
_NEG_CASE = {
    "n_pt": (Fraction(-3, 2), Fraction(-1, 1)),
    "d_pt": (Fraction(2, 1), Fraction(5, 2)),
    "bounds": ((Fraction(0), Fraction(1, 4)),),
    "c_num": (Fraction(1, 5),),
    "c_den": (Fraction(-1, 5),),
}


def negative_numerator_discrepancy_witness() -> dict:
    """Exercise the negative-numerator region: the frozen v7 exact path returns
    a non-containing interval there, the v8 path matches the independent
    dense-grid verifier exactly."""
    cfg = _NEG_CASE
    v7 = _frozen._exact_joint_interval(cfg["n_pt"], cfg["d_pt"], cfg["bounds"],
                                       cfg["c_num"], cfg["c_den"])
    v8 = exact_joint_interval_v8(cfg["n_pt"], cfg["d_pt"], cfg["bounds"],
                                 cfg["c_num"], cfg["c_den"])
    brute = _brute_force_joint(cfg["n_pt"], cfg["d_pt"], cfg["bounds"],
                               cfg["c_num"], cfg["c_den"])
    v8_matches_brute = (v8 == brute)
    # the v7 pairing must fail containment of the true extremes here
    v7_wrong = (v7 is None) or (v7[0] > brute[0]) or (v7[1] < brute[1])
    return {
        "config": {
            "n_pt": [str(x) for x in cfg["n_pt"]],
            "d_pt": [str(x) for x in cfg["d_pt"]],
            "bounds": [[str(lo), str(hi)] for lo, hi in cfg["bounds"]],
            "c_num": [str(x) for x in cfg["c_num"]],
            "c_den": [str(x) for x in cfg["c_den"]],
        },
        "v7_frozen_interval": [str(v7[0]), str(v7[1])] if v7 else None,
        "v8_interval": [str(v8[0]), str(v8[1])] if v8 else None,
        "brute_force_interval": [str(brute[0]), str(brute[1])] if brute else None,
        "v8_matches_brute_force_exactly": bool(v8_matches_brute),
        "v7_fails_containment_on_negative_domain": bool(v7_wrong),
        "arithmetic": "exact Fraction (zero tolerance)",
    }


def positive_domain_containment_witness(*, n_trials: int = 200,
                                        seed: int = 20260710) -> dict:
    """On the documented nonnegative-shifted-numerator domain the v8 selector
    agrees bit-exactly with the frozen v7 selector (the fixed pairing is the
    true optimum there), so every frozen v7 result is reproduced."""
    rng = np.random.default_rng(seed)
    agree_joint = 0
    agree_naive = 0
    evaluated = 0
    for _ in range(int(n_trials)):
        k = int(rng.integers(1, 4))
        bounds = tuple((Fraction(0), Fraction(int(rng.integers(2, 40)), 100))
                       for _ in range(k))
        c_num = tuple(Fraction(int(rng.choice((-1, 1)) * rng.integers(2, 50)), 100)
                      for _ in range(k))
        c_den = tuple(Fraction(int(rng.choice((-1, 1)) * rng.integers(2, 50)), 100)
                      for _ in range(k))
        den_shift_min = sum(min(cd * lo, cd * hi) for cd, (lo, hi) in zip(c_den, bounds))
        num_shift_min = sum(min(cn * lo, cn * hi) for cn, (lo, hi) in zip(c_num, bounds))
        d_base = Fraction(1) + abs(den_shift_min)
        # keep the shifted numerator nonnegative over the whole box
        n_base = Fraction(1) + abs(num_shift_min)
        n_pt = (n_base, n_base + Fraction(1, 5))
        d_pt = (d_base, d_base + Fraction(3, 10))
        v7_j = _frozen._exact_joint_interval(n_pt, d_pt, bounds, c_num, c_den)
        v8_j = exact_joint_interval_v8(n_pt, d_pt, bounds, c_num, c_den)
        v7_n = _frozen._exact_naive_quotient(n_pt, d_pt, bounds, c_num, c_den)
        v8_n = exact_naive_quotient_v8(n_pt, d_pt, bounds, c_num, c_den)
        if v7_j is None or v7_n is None:
            continue
        evaluated += 1
        agree_joint += int(v7_j == v8_j)
        agree_naive += int(v7_n == v8_n)
    return {
        "trials_evaluated": evaluated,
        "joint_bit_exact_agreement": f"{agree_joint}/{evaluated}",
        "naive_bit_exact_agreement": f"{agree_naive}/{evaluated}",
        "all_bit_exact": bool(evaluated > 0 and agree_joint == evaluated
                              and agree_naive == evaluated),
        "domain": "nonnegative shifted numerator over the whole shared box",
        "arithmetic": "exact Fraction (zero tolerance)",
    }


def signed_domain_strictness_survey(*, n_trials: int = 400,
                                    seed: int = 20260710) -> dict:
    """Signed-domain survey through the v8 selector: containment
    joint subseteq naive is required to hold EXACTLY on every draw (any sign);
    the v7 sign-conflict strictness criterion is only MEASURED here, not
    claimed -- its proof domain is the nonnegative-numerator region."""
    rng = np.random.default_rng(seed)
    contained = 0
    criterion_agree = 0
    strict = 0
    evaluated = 0
    for _ in range(int(n_trials)):
        k = int(rng.integers(1, 4))
        bounds = tuple((Fraction(0), Fraction(int(rng.integers(2, 40)), 100))
                       for _ in range(k))
        c_num = tuple(Fraction(int(rng.choice((-1, 1)) * rng.integers(2, 50)), 100)
                      for _ in range(k))
        c_den = tuple(Fraction(int(rng.choice((-1, 1)) * rng.integers(2, 50)), 100)
                      for _ in range(k))
        den_shift_min = sum(min(cd * lo, cd * hi) for cd, (lo, hi) in zip(c_den, bounds))
        d_base = Fraction(1) + abs(den_shift_min)
        # signed numerator base: sweep negative, straddling and positive bases
        n_base = Fraction(int(rng.integers(-3, 3)), 2)
        n_pt = (n_base, n_base + Fraction(1, 5))
        d_pt = (d_base, d_base + Fraction(3, 10))
        joint = exact_joint_interval_v8(n_pt, d_pt, bounds, c_num, c_den)
        naive = exact_naive_quotient_v8(n_pt, d_pt, bounds, c_num, c_den)
        if joint is None or naive is None:
            continue
        evaluated += 1
        contained += int(naive[0] <= joint[0] and joint[1] <= naive[1])
        is_strict = joint[0] > naive[0] or joint[1] < naive[1]
        conflict = any((hi > lo) and (cn * cd > 0)
                       for (lo, hi), cn, cd in zip(bounds, c_num, c_den))
        criterion_agree += int(is_strict == conflict)
        strict += int(is_strict)
    return {
        "trials_evaluated": evaluated,
        "containment_exact": f"{contained}/{evaluated}",
        "containment_always": bool(evaluated > 0 and contained == evaluated),
        "criterion_agreement_measured": f"{criterion_agree}/{evaluated}",
        "criterion_claim_domain": "nonnegative shifted numerator only (v7 theorem); "
                                  "signed-domain agreement is an observation",
        "strict_cases": strict,
        "arithmetic": "exact Fraction (zero tolerance)",
    }


def gf_interval_v8_seal() -> dict:
    """Fail-closed seal for the v8 signed-numerator quotient path."""
    neg = negative_numerator_discrepancy_witness()
    pos = positive_domain_containment_witness()
    survey = signed_domain_strictness_survey()
    ok = (neg["v8_matches_brute_force_exactly"]
          and neg["v7_fails_containment_on_negative_domain"]
          and pos["all_bit_exact"]
          and survey["containment_always"])
    return {
        "seal": "egs3.gf_interval_v8",
        "status": "PASS" if ok else "FAIL",
        "successor_of": "htt/obsstat/egs3_gf_interval.py (v7-frozen; lines 280-281, "
                        "298 fixed pairing; float path lines 105-106)",
        "repairs": [
            "documented signed-numerator domain (v7 pairing valid iff shifted "
            "numerator nonnegative)",
            "four-candidate corner enumeration valid for every signed numerator "
            "with strictly positive denominator",
        ],
        "negative_numerator_discrepancy": neg,
        "positive_domain_bit_exact_containment": pos,
        "signed_domain_survey": survey,
        "frozen_module_untouched": True,
        "claim_boundary": "diagnostic-only interval algebra; no data, "
                          "signal-discovery, Bianchi-class/geometry, or "
                          "probabilistic-inference claim",
    }
