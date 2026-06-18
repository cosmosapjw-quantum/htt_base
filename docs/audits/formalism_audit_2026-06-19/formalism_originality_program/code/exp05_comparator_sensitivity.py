#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
exp05_comparator_sensitivity.py  (E5 -> U5/F2)

x_C and Q are comparator-RELATIVE (flat/matched/closed). An implicit comparator
is a hidden researcher degree of freedom (a fork in the garden). This reports
x_C/Q as a comparator MULTIVERSE / specification-curve: the value under each
admissible comparator and the across-comparator spread, for representative
configurations.

Illustrative comparator offsets (documented): different comparators shift the
curvature/normalization reference, modeled here as additive offsets to
Omega_k_aniso and a multiplicative rescale of the std-normalized sectors.
"""
from __future__ import annotations

from reference_formalism import DepartureProfile, BudgetSpec, Q, COMPARATORS

# documented comparator transforms applied to a "raw" sector set
COMPARATOR_TRANSFORM = {
    "flat":    {"k_offset": 0.0,    "scale": 1.00},
    "matched": {"k_offset": -8e-4,  "scale": 0.92},
    "closed":  {"k_offset": +1.2e-3, "scale": 1.08},
}

CONFIGS = {
    "shear-dominated":  {"Sigma2_std": 6e-3, "W2_std": 1e-3,
                         "Omega_tilt": 5e-4, "Omega_k_aniso": 8e-4},
    "near-cancellation": {"Sigma2_std": 3e-3, "W2_std": 3e-3,
                          "Omega_tilt": 4e-4, "Omega_k_aniso": -4e-4},
    "tilt-dominated":   {"Sigma2_std": 1e-3, "W2_std": 5e-4,
                         "Omega_tilt": 5e-3, "Omega_k_aniso": 6e-4},
}
U = 1.0e-2


def transform(raw: dict, comp: str) -> dict:
    t = COMPARATOR_TRANSFORM[comp]
    return {
        "Sigma2_std": raw["Sigma2_std"] * t["scale"],
        "W2_std": raw["W2_std"] * t["scale"],
        "Omega_tilt": raw["Omega_tilt"] * t["scale"],
        "Omega_k_aniso": raw["Omega_k_aniso"] + t["k_offset"],
    }


def main() -> None:
    print("=" * 74)
    print("E5  comparator multiverse for x_C / Q  (specification-curve)")
    print("=" * 74)
    for name, raw in CONFIGS.items():
        xs, qs = {}, {}
        for comp in COMPARATORS:
            c = transform(raw, comp)
            p = DepartureProfile(c, comparator=comp)
            b = BudgetSpec(denominator_value=U, policy="MES_linear",
                           is_admissible_ceiling=True, comparator=comp)
            xs[comp] = p.x_C
            qs[comp] = Q(p, b, numerator_policy="absolute")
        x_spread = max(xs.values()) - min(xs.values())
        q_spread = max(qs.values()) - min(qs.values())
        x_rel = x_spread / (abs(sum(xs.values()) / len(xs)) + 1e-30)
        print(f"\n  config: {name}")
        print("     comparator   x_C          Q(|.|)")
        for comp in COMPARATORS:
            print(f"       {comp:8s}  {xs[comp]:+.3e}   {qs[comp]:.3e}")
        print(f"     x_C spread = {x_spread:.3e}  "
              f"(relative {x_rel:.1%})   Q spread = {q_spread:.3e}")
    print()
    print("  FINDING (U5): x_C/Q vary materially across comparators; the "
          "comparator")
    print("                must never be implicit. Report the comparator + the")
    print("                across-comparator spread as an explicit uncertainty.")


if __name__ == "__main__":
    main()
