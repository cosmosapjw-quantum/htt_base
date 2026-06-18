#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
exp03_Pi_threshold_bias.py  (E3 -> F4)

Quantifies the garden-of-forking-paths inflation that Pi's threshold
PRE-REGISTRATION removes. Under a null sample bank, a post-hoc analyst can pick
the threshold that maximizes the apparent exceedance "signal"; a pre-registered
threshold cannot. We compare:
  (a) exceedance at a fixed pre-registered threshold, vs
  (b) the maximum exceedance achievable by scanning thresholds post-hoc,
across many null realizations, and report the inflation.
"""
from __future__ import annotations

import random

from reference_formalism import ExceedanceCurve

SEED = 700
N_REAL = 2000
N_SAMP = 200


def null_samples(rng: random.Random) -> list[float]:
    """Nonnegative null diagnostic samples (|standard normal|-like)."""
    return [abs(rng.gauss(0.0, 1.0)) for _ in range(N_SAMP)]


def main() -> None:
    rng = random.Random(SEED)
    prereg_threshold = 1.64   # fixed in advance (e.g. ~95th pct of |N(0,1)|)
    thr_grid = [i / 10 for i in range(5, 30)]  # 0.5 .. 2.9

    prereg_exc = []
    posthoc_exc = []
    for _ in range(N_REAL):
        s = null_samples(rng)
        cur = ExceedanceCurve(tuple(s), source_score_label="Q",
                              measure_kind="null_ensemble",
                              thresholds=tuple(thr_grid))
        prereg_exc.append(cur.exceedance_fraction(prereg_threshold))
        # post-hoc: pick the threshold giving the largest "surviving fraction"
        # in a target band (mimics choosing the most favorable cut after looking)
        band = [t for t in thr_grid if 1.0 <= t <= 2.5]
        posthoc_exc.append(max(cur.exceedance_fraction(t) for t in band))

    def mean(x):
        return sum(x) / len(x)

    # "false alarm": exceedance fraction above a nominal alpha
    alpha = 0.05
    fa_prereg = mean([1.0 if e > alpha else 0.0 for e in prereg_exc])
    fa_posthoc = mean([1.0 if e > alpha else 0.0 for e in posthoc_exc])

    print("=" * 70)
    print("E3  Pi threshold-registration bias  (null bank; %d realizations)"
          % N_REAL)
    print("=" * 70)
    print(f"  pre-registered threshold = {prereg_threshold}")
    print(f"  mean exceedance  pre-registered = {mean(prereg_exc):.4f}")
    print(f"  mean exceedance  post-hoc (best-of-band) = {mean(posthoc_exc):.4f}")
    print(f"  inflation factor = {mean(posthoc_exc) / max(mean(prereg_exc),1e-9):.2f}x")
    print()
    print(f"  P(exceedance > {alpha})  pre-registered = {fa_prereg:.3f}")
    print(f"  P(exceedance > {alpha})  post-hoc       = {fa_posthoc:.3f}")
    print()
    print("  FINDING: post-hoc threshold picking inflates apparent exceedance;")
    print("           Pi's pre_registered policy (registration_hash + anti-post-hoc)")
    print("           structurally removes this degree of freedom (F4).")
    # demonstrate the contract refuses a post-hoc selection_rule
    from reference_formalism import FormalismError
    try:
        ExceedanceCurve(tuple(null_samples(rng)), threshold_policy="pre_registered",
                        thresholds=tuple(thr_grid), selected_threshold=thr_grid[0],
                        registration_hash="abc123",
                        selection_rule="chosen after looking at the data")
        print("  [contract check] post-hoc rule ACCEPTED  <-- UNEXPECTED")
    except FormalismError as e:
        print(f"  [contract check] post-hoc rule correctly REFUSED: {str(e)[:48]}")


if __name__ == "__main__":
    main()
