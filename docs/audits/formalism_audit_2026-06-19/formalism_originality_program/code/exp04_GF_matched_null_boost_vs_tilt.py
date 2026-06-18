#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
exp04_GF_matched_null_boost_vs_tilt.py  (E4 -> U4)

Turns the audit's G_F limitation (survey-systematic FPR ~ 1 under unmatched
nulls) into a forecast. A LOCAL BOOST gives a depth-INDEPENDENT G_F signature;
a GLOBAL TILT gives a depth-DEPENDENT one (it grows / changes with depth -- the
same structure as the tomographic boost-vs-tilt forecast). We build matched vs
unmatched null banks and report:
  (i)  the survey-systematic false-positive rate of a naive G_F+threshold rule
       under matched vs unmatched calibration, and
  (ii) the boost-vs-tilt separation (ROC AUC) from the G_F depth SLOPE, which is
       the discriminating statistic.

Illustrative generative model (documented; not observational).
"""
from __future__ import annotations

import random

SEED = 4040
N_MOCK = 4000
DEPTHS = (0.02, 0.06, 0.12, 0.23)          # bin centers (z)
GF_THRESHOLD = 2.2                          # the audit's naive rule threshold


def gf_profile(kind: str, rng: random.Random, *, matched: bool) -> list[float]:
    """Return G_F per depth bin for a mock of a given kind.
    - 'null'  : G_F ~ 1 with noise (no real gap)
    - 'boost' : depth-INDEPENDENT elevation (local kinematic boost)
    - 'tilt'  : depth-DEPENDENT trend (global tilt grows with depth)
    Matched calibration => smaller, well-characterized noise; unmatched => large,
    heavy-tailed noise that makes the naive threshold fire spuriously.
    """
    if matched:
        noise = lambda: rng.gauss(0.0, 0.15)
    else:
        # heavy-tailed, biased-high noise (uncharacterized systematics)
        noise = lambda: rng.gauss(0.35, 0.55) + (rng.expovariate(1.0) - 1.0) * 0.4
    out = []
    for z in DEPTHS:
        if kind == "null":
            base = 1.0
        elif kind == "boost":
            base = 1.9                       # flat in depth
        elif kind == "tilt":
            base = 1.0 + 6.0 * z             # grows with depth
        else:
            raise ValueError(kind)
        out.append(max(0.05, base + noise()))
    return out


def naive_rule_fires(gf: list[float]) -> bool:
    """Audit's naive rule: any depth bin with G_F >= threshold."""
    return any(g >= GF_THRESHOLD for g in gf)


def depth_slope(gf: list[float]) -> float:
    """Discriminating statistic: least-squares slope of G_F vs depth.
    boost -> ~0 slope; tilt -> positive slope."""
    n = len(DEPTHS)
    mx = sum(DEPTHS) / n
    my = sum(gf) / n
    num = sum((DEPTHS[i] - mx) * (gf[i] - my) for i in range(n))
    den = sum((DEPTHS[i] - mx) ** 2 for i in range(n))
    return num / den if den else 0.0


def roc_auc(pos: list[float], neg: list[float]) -> float:
    """AUC = P(score(pos) > score(neg)) via rank statistic."""
    allv = sorted([(v, 1) for v in pos] + [(v, 0) for v in neg])
    rank = 0.0
    i = 0
    n = len(allv)
    # average ranks for ties
    ranks = [0.0] * n
    while i < n:
        j = i
        while j < n and allv[j][0] == allv[i][0]:
            j += 1
        r = (i + 1 + j) / 2.0
        for k in range(i, j):
            ranks[k] = r
        i = j
    sum_pos = sum(ranks[k] for k in range(n) if allv[k][1] == 1)
    np_, nn = len(pos), len(neg)
    return (sum_pos - np_ * (np_ + 1) / 2.0) / (np_ * nn)


def fpr_under(matched: bool, rng: random.Random) -> float:
    fires = sum(1 for _ in range(N_MOCK)
                if naive_rule_fires(gf_profile("null", rng, matched=matched)))
    return fires / N_MOCK


def main() -> None:
    rng = random.Random(SEED)
    print("=" * 74)
    print("E4  G_F matched-null + boost-vs-tilt depth discrimination")
    print("=" * 74)

    fpr_unmatched = fpr_under(False, rng)
    fpr_matched = fpr_under(True, rng)
    print("  (i) survey-systematic FPR of the naive 'any-bin G_F>=%.1f' rule:"
          % GF_THRESHOLD)
    print(f"        unmatched nulls : FPR = {fpr_unmatched:.3f}   "
          f"(threshold 0.15 -> {'BLOCKED' if fpr_unmatched>0.15 else 'ok'})")
    print(f"        matched   nulls : FPR = {fpr_matched:.3f}   "
          f"(threshold 0.15 -> {'BLOCKED' if fpr_matched>0.15 else 'PASS'})")
    print()

    # (ii) discrimination via depth slope, under matched calibration
    boost_slopes = [depth_slope(gf_profile("boost", rng, matched=True))
                    for _ in range(N_MOCK)]
    tilt_slopes = [depth_slope(gf_profile("tilt", rng, matched=True))
                   for _ in range(N_MOCK)]
    auc = roc_auc(tilt_slopes, boost_slopes)
    print("  (ii) boost-vs-tilt separation from the G_F DEPTH-SLOPE "
          "(matched nulls):")
    print(f"        mean slope  boost = {sum(boost_slopes)/N_MOCK:+.2f}  "
          f"(depth-independent => ~0)")
    print(f"        mean slope  tilt  = {sum(tilt_slopes)/N_MOCK:+.2f}  "
          f"(depth-dependent => >0)")
    print(f"        ROC AUC (tilt vs boost) = {auc:.3f}")
    print()
    print("  FINDING (U4): the naive amplitude rule is non-discriminating "
          "(FPR high);")
    print("                the DEPTH SLOPE of G_F separates global tilt from "
          "local boost")
    print("                under matched calibration. Report this as a FORECAST; "
          "until")
    print("                matched nulls exist, G_F gives no boost-vs-tilt "
          "separation.")


if __name__ == "__main__":
    main()
