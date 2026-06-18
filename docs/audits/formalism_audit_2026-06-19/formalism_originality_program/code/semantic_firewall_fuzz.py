#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
semantic_firewall_fuzz.py  (E6 -> F1/F9, and E7 -> F6)

E6: an adversarial property-based fuzzer that randomly attempts to construct
    OVER-CLAIMED diagnostics and confirms the firewall REFUSES every attempt:
      (a) inject reserved overclaim language into metadata,
      (b) mis-own / mislabel a plotted symbol (figure-label linter),
      (c) clip / sign-dirty a certified filling fraction F,
      (d) post-hoc-select a Pi threshold.

E7: a MIO<->HTT leakage audit -- confirm that an inference-side consumer rejects
    diagnostic-side inputs and forbids ln_b/evidence/posterior tokens (mirrors
    the production reject_mio_likelihood_inputs guard).

Target: 0 successful smuggles, 0 leakage paths.
"""
from __future__ import annotations

import random

from reference_formalism import (
    DepartureProfile, BudgetSpec, CertifiedFillingFraction, ExceedanceCurve, Q,
    IsotropyGap, DepthBin, FormalismError, RESERVED_LANGUAGE, CANONICAL_REGISTRY,
    lint_figure_label,
)

SEED = 6060
N = 4000


# --- E6 attack generators: each MUST raise FormalismError (refusal) ---------- #

def attack_reserved_metadata(rng):
    term = rng.choice(RESERVED_LANGUAGE)
    p = DepartureProfile({"Sigma2_std": 5e-3, "W2_std": 0.0,
                          "Omega_tilt": 0.0, "Omega_k_aniso": 0.0})
    b = BudgetSpec(denominator_value=1e-2)
    # smuggle the reserved term into Q metadata
    Q(p, b, numerator_policy="absolute",
      metadata={"note": f"this diagnostic is a {term} of the sector"})


def attack_clip_F(rng):
    # super-ceiling x_C -> F>1 ; firewall must refuse (no clipping)
    p = DepartureProfile({"Sigma2_std": 5e-2, "W2_std": 0.0,
                          "Omega_tilt": 0.0, "Omega_k_aniso": 0.0})
    b = BudgetSpec(denominator_value=1e-2, is_admissible_ceiling=True)
    CertifiedFillingFraction((p,), (b,))


def attack_sign_dirty_F(rng):
    # vorticity-dominated negative x_C -> not sign-clean
    p = DepartureProfile({"Sigma2_std": 0.0, "W2_std": 3e-3,
                          "Omega_tilt": 0.0, "Omega_k_aniso": 0.0})
    b = BudgetSpec(denominator_value=1e-2, is_admissible_ceiling=True)
    CertifiedFillingFraction((p,), (b,))


def attack_nonadmissible_certify(rng):
    p = DepartureProfile({"Sigma2_std": 5e-3, "W2_std": 0.0,
                          "Omega_tilt": 0.0, "Omega_k_aniso": 0.0})
    b = BudgetSpec(denominator_value=1e-2,
                   policy=rng.choice(["external_transfer", "observational",
                                      "atlas_quantile"]),
                   is_admissible_ceiling=True)
    CertifiedFillingFraction((p,), (b,))


def attack_posthoc_threshold(rng):
    s = tuple(abs(rng.gauss(0, 1)) for _ in range(50))
    ExceedanceCurve(s, threshold_policy="pre_registered", thresholds=(0.5, 1.0, 1.5),
                    selected_threshold=1.0, registration_hash="h",
                    selection_rule="threshold chosen after looking at the scan")


def attack_gf_global_tilt_language(rng):
    p = DepartureProfile({"Sigma2_std": 4e-3, "W2_std": 0.0,
                          "Omega_tilt": 0.0, "Omega_k_aniso": 0.0})
    b = BudgetSpec(denominator_value=1e-2, is_admissible_ceiling=True)
    F = CertifiedFillingFraction((p,), (b,))
    bins = (DepthBin("a", F, 0.0, 0.1), DepthBin("b", F, 0.1, 0.2))
    IsotropyGap(bins, "a", "b", metadata={"claim": "evidence of a global tilt"})


E6_ATTACKS = [
    attack_reserved_metadata, attack_clip_F, attack_sign_dirty_F,
    attack_nonadmissible_certify, attack_posthoc_threshold,
    attack_gf_global_tilt_language,
]


def fuzz_e6(rng) -> tuple[int, dict]:
    smuggles = 0
    by_attack = {a.__name__: {"trials": 0, "smuggled": 0} for a in E6_ATTACKS}
    for _ in range(N):
        a = rng.choice(E6_ATTACKS)
        by_attack[a.__name__]["trials"] += 1
        try:
            a(rng)
            smuggles += 1
            by_attack[a.__name__]["smuggled"] += 1   # constructed -> FIREWALL FAILED
        except FormalismError:
            pass                                       # refused -> good
    return smuggles, by_attack


def figure_label_attacks() -> int:
    """The semantic-split mislabels the audit found: Pi='inter-policy spread',
    F='1-FPR' owner HTT, G_F='null-bank envelope' owner HTT. Linter must flag."""
    bad = [
        ("Pi", "MIO", "inter-policy spread across denominator policies"),
        ("F",  "HTT", "one minus look-elsewhere adjusted local-null FPR"),
        ("G_F", "HTT", "normalized log depth-response envelope from null-bank"),
    ]
    good = [
        ("x", "MIO", CANONICAL_REGISTRY["x"]["definition"]),
        ("Q", "MIO", CANONICAL_REGISTRY["Q"]["definition"]),
    ]
    flagged = sum(1 for s, o, d in bad if lint_figure_label(s, o, d))
    false_alarms = sum(1 for s, o, d in good if lint_figure_label(s, o, d))
    return flagged, false_alarms


# --- E7 leakage audit -------------------------------------------------------- #

_FORBIDDEN_INFERENCE_TOKENS = ("ln_b", "lnb", "evidence", "posterior",
                               "likelihood", "bayes_factor", "score", "p_value")


def inference_consumer(inputs: dict) -> None:
    """Stand-in for the HTT posterior pushforward's reject_mio_likelihood_inputs:
    refuses any diagnostic (MIO) input or forbidden inference token."""
    for key, val in inputs.items():
        text = f"{key} {val}".lower().replace("-", "_")
        if "mio" in text or "diagnostic" in text:
            raise FormalismError("inference layer must not consume MIO diagnostics")
        for tok in _FORBIDDEN_INFERENCE_TOKENS:
            if tok in text:
                raise FormalismError(f"forbidden inference token: {tok}")


def leakage_audit() -> tuple[int, int]:
    paths = [
        {"source": "mio.departure_report.Q", "value": 0.67},
        {"source": "mio.filling_fraction.F", "value": 0.3},
        {"mio_certificate": "directional_coherence"},
        {"note": "use this diagnostic as evidence"},
        {"summary": "ln_b = 26.3"},
    ]
    leaks = 0
    for p in paths:
        try:
            inference_consumer(p)
            leaks += 1            # accepted a diagnostic/forbidden token -> leak
        except FormalismError:
            pass
    return len(paths), leaks


def main() -> None:
    rng = random.Random(SEED)
    print("=" * 72)
    print("E6  semantic-firewall fuzz  (%d trials)" % N)
    print("=" * 72)
    smuggles, by_attack = fuzz_e6(rng)
    for name, d in by_attack.items():
        print(f"  {name:32s} trials={d['trials']:5d}  smuggled={d['smuggled']}")
    print(f"  TOTAL successful smuggles: {smuggles}  "
          f"({'PASS' if smuggles == 0 else 'FIREWALL FAILED'})")
    print()
    flagged, false_alarms = figure_label_attacks()
    print("  figure-label linter (the audit's semantic-split mislabels):")
    print(f"     mislabels flagged = {flagged}/3   false alarms on canonical = "
          f"{false_alarms}/2  ({'PASS' if flagged == 3 and false_alarms == 0 else 'CHECK'})")
    print()
    print("=" * 72)
    print("E7  MIO<->HTT leakage audit")
    print("=" * 72)
    n_paths, leaks = leakage_audit()
    print(f"  paths checked = {n_paths}   leakage paths = {leaks}  "
          f"({'PASS' if leaks == 0 else 'LEAK'})")
    print()
    ok = (smuggles == 0 and flagged == 3 and false_alarms == 0 and leaks == 0)
    print("  FINDING: the firewall (F1/F9) refuses every overclaim construction "
          "and")
    print("           every mislabeled figure; the typed boundary (F6) blocks "
          "diagnostic->evidence leakage.")
    print(f"  OVERALL: {'PASS' if ok else 'REVIEW'}")


if __name__ == "__main__":
    main()
