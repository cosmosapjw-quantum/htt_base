#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
exp01_cancellation_null.py  (E1 -> U1/F7, U2/F8)

How often does the SIGNED coordinate x_C under-represent total anisotropy?
Samples the four sectors from documented priors and reports the distribution of
the cancellation_index and of |x_C|/M (signed-to-total ratio). Demonstrates that
x_C~0 (and F~0) can coexist with large anisotropy, motivating the sector profile
(F7) and the magnitude companion (F8).
"""
from __future__ import annotations

import math
import random

from reference_formalism import (
    DepartureProfile, cancellation_index, absolute_component_total,
)

N = 200_000
SEED = 24061


def sample_sectors(rng: random.Random) -> dict[str, float]:
    """Log-uniform magnitudes over a wide dynamic range; tilt/curvature signed.
    Priors are illustrative (documented), not observational."""
    def logu(lo, hi):
        return 10.0 ** rng.uniform(math.log10(lo), math.log10(hi))
    return {
        "Sigma2_std": logu(1e-6, 1e-2),                 # shear^2 >= 0
        "W2_std": logu(1e-6, 1e-2),                     # vorticity^2 >= 0
        "Omega_tilt": rng.choice([-1, 1]) * logu(1e-6, 1e-2),
        "Omega_k_aniso": rng.choice([-1, 1]) * logu(1e-6, 1e-2),
    }


def main() -> None:
    rng = random.Random(SEED)
    ci_hi = ci_vhi = 0
    ratios = []
    worst = None
    for _ in range(N):
        c = sample_sectors(rng)
        ci = cancellation_index(c)
        M = absolute_component_total(c)
        p = DepartureProfile(c)
        r = abs(p.x_C) / M if M > 0 else 0.0
        ratios.append(r)
        if ci > 0.5:
            ci_hi += 1
        if ci > 0.9:
            ci_vhi += 1
        if worst is None or ci > worst[0]:
            worst = (ci, p)
    ratios.sort()

    def q(p):  # percentile
        return ratios[min(len(ratios) - 1, int(p * len(ratios)))]

    print("=" * 70)
    print("E1  cancellation null distribution  (N=%d draws)" % N)
    print("=" * 70)
    print(f"  P(cancellation_index > 0.5) = {ci_hi / N:6.3f}")
    print(f"  P(cancellation_index > 0.9) = {ci_vhi / N:6.3f}")
    print("  |x_C|/M (signed-to-total ratio) percentiles:")
    print(f"     p05={q(0.05):.3f}  p25={q(0.25):.3f}  median={q(0.5):.3f}  "
          f"p75={q(0.75):.3f}  p95={q(0.95):.3f}")
    print("  (small |x_C|/M => the signed scalar hides total anisotropy.)")
    print()
    ci, p = worst
    print("  worst-cancellation draw:")
    print(f"     cancellation_index={ci:.4f}  x_C={p.x_C:+.3e}  "
          f"total_magnitude={p.total_magnitude:.3e}")
    print(f"     signed contributions: "
          + ", ".join(f"{k}={v:+.2e}" for k, v in p.signed_contributions.items()))
    print()
    print("  FINDING: report the sector vector (F7) + total_anisotropy_magnitude "
          "(F8)\n           alongside x_C/F; x_C~0 is NOT isotropy.")


if __name__ == "__main__":
    main()
