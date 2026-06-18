#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
exp02_F_failclosed_coverage.py  (E2 -> F3)

Confirms the certified filling fraction F is FAIL-CLOSED: it constructs exactly
when (x_C >= 0) AND (ceiling admissible) AND (0 <= x_C/U <= 1), and RAISES
otherwise -- with no silent clipping. Sweeps a stress grid and reports the
accept/reject coverage table.
"""
from __future__ import annotations

from reference_formalism import (
    DepartureProfile, BudgetSpec, CertifiedFillingFraction, FormalismError,
)


def make_profile(xc_target: float) -> DepartureProfile:
    """Build a profile whose x_C equals xc_target (sign-clean via shear, or
    negative via a vorticity-dominated sector)."""
    if xc_target >= 0:
        comps = {"Sigma2_std": xc_target, "W2_std": 0.0,
                 "Omega_tilt": 0.0, "Omega_k_aniso": 0.0}
    else:
        comps = {"Sigma2_std": 0.0, "W2_std": -xc_target,  # W2 enters at -1
                 "Omega_tilt": 0.0, "Omega_k_aniso": 0.0}
    return DepartureProfile(comps)


def main() -> None:
    U = 1.0e-2
    cases = [
        # (label, x_C, policy, admissible)
        ("valid: 0<=F<=1, MES admissible",        5e-3, "MES_linear", True),
        ("valid: F=1 boundary",                   1e-2, "MES_linear", True),
        ("valid: F=0 boundary",                   0.0,  "MES_linear", True),
        ("reject: x_C<0 (vortical/cancellation)", -3e-3, "MES_linear", True),
        ("reject: super-ceiling F>1",             2e-2, "MES_linear", True),
        ("reject: ceiling not admissible",        5e-3, "MES_linear", False),
        ("reject: external policy certifying",    5e-3, "external_transfer", True),
        ("reject: observational policy certify",  5e-3, "observational", True),
    ]
    print("=" * 78)
    print("E2  F fail-closed coverage  (U=%.1e)" % U)
    print("=" * 78)
    print(f"  {'case':42s} {'outcome':12s} detail")
    ok = True
    for label, xc, policy, adm in cases:
        expect_construct = label.startswith("valid")
        try:
            budget = BudgetSpec(denominator_value=U, policy=policy,
                                is_admissible_ceiling=adm)
            F = CertifiedFillingFraction((make_profile(xc),), (budget,))
            outcome, detail = "CONSTRUCTED", f"F={F.F_value:.3f}  M={F.magnitude_companion:.3f}"
            got_construct = True
        except FormalismError as e:
            outcome, detail = "RAISED", str(e)[:46]
            got_construct = False
        correct = (got_construct == expect_construct)
        ok = ok and correct
        flag = "" if correct else "  <-- UNEXPECTED"
        print(f"  {label:42s} {outcome:12s} {detail}{flag}")
    print()
    print(f"  coverage correct: {'YES' if ok else 'NO'}  "
          "(valid cases construct; invalid cases raise; no clipping)")
    print("  FINDING: F is a fail-closed certificate (F3) -- it refuses rather "
          "than\n           returning a clipped or sign-dirty occupancy.")


if __name__ == "__main__":
    main()
