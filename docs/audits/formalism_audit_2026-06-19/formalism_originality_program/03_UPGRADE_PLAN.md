# 03 — Upgrade Plan: Audit Findings → Stronger Formalism

Five upgrades. Each takes an audit finding and yields a stronger, novel object with a method and an acceptance criterion. Reference implementation and demos in `code/`.

---

## U1 — Sector-resolved departure profile + first-class cancellation  (cures the `x_C≈0≠isotropy` trap → F7)

**Audit finding (Medium):** `x_C` is a signed projection; `x_C≈0` (and hence `F≈0`) can coexist with large shear+vorticity or tilt+curvature. The shipped `cancellation_index` exposes this but is not first-class.

**Upgrade.** Emit, alongside every `x_C`/`F`, the signed component vector `(Σ², −W², Ω_tilt, Ω_{k,aniso})`, the `absolute_component_total`, and `cancellation_index`. Define a **sector-resolved departure profile** object that is the canonical reported unit (not the bare scalar). Captions/tables show the profile; the scalar is derived.

**Method:** `code/reference_formalism.py::DepartureProfile`; demo in `code/exp01_cancellation_null.py`.

**Acceptance:** no figure/table reports `x_C` or `F` without the component vector + `cancellation_index`; a worked counter-example (`x_C≈0`, large sectors) appears in the methods text.

---

## U2 — Total-anisotropy magnitude companion to `F`  (cures the "filling fraction" naming → F8)

**Audit finding (Medium):** "(certified) filling fraction" connotes physical volume occupancy; the object is `x_C/(MES-linear ceiling)`, sign-clean, in `[0,1]`.

**Upgrade.** Report beside `F`: (a) a precise definition ("fraction of the admissible linear-regime ceiling occupied by the *signed* projection"), and (b) an unsigned **total-anisotropy magnitude** `M = (Σ²+W²+|Ω_tilt|+|Ω_{k,aniso}|)/U` (or a documented sector-norm). `F` and `M` diverge exactly under cancellation — the informative case.

**Method:** `reference_formalism.py::total_anisotropy_magnitude`; demo in `exp01`.

**Acceptance:** every `F` is accompanied by `M` and the precise definition; "filling fraction" never appears un-defined; the legacy `*_posterior` filename is retired from manuscript use.

---

## U3 — Semantic-firewall specification + adversarial fuzzer  (generalizes the semantic-split fix → F9)

**Audit finding (High):** the semantic-split figure rebound `Π`/`F`/`G_F` to non-canonical quantities (and swapped `F`/`G_F` owner to HTT). The firewall guards *object metadata* but not *figure labels*.

**Upgrade.** (a) Extend the firewall to a **portable specification** (reserved-language sets, owner/tier rules, fail-closed gates, symbol↔definition↔owner registry). (b) Add a **property-based fuzzer** that randomly attempts to (i) inject reserved language, (ii) mis-own a quantity, (iii) clip/sign-dirty `F`, (iv) post-hoc-select a `Π` threshold, and confirms refusal. (c) Add a **figure-label check** that compares each plotted symbol's definition/owner against the canonical registry (the audit's `verify_formalism_claims.py` is the seed).

**Method:** `code/semantic_firewall_fuzz.py` + `reference_formalism.py::CANONICAL_REGISTRY`.

**Acceptance:** the fuzzer reports 0 successful smuggles; a figure-label linter passes on every manuscript figure that displays `x_C/Q/Π/F/G_F`; the semantic-split figure is relabeled or repopulated with canonical objects.

---

## U4 — Matched-null + depth-template discrimination for `G_F`  (turns the FPR limitation into a forecast)

**Audit finding (High/Medium):** under the shipped null banks, the `G_F`+direction rule has local-null FPR ≈0.28 and survey-systematic FPR ≈0.94 (adjusted 1.0); discrimination is correctly **blocked**.

**Upgrade.** Replace `diagnostic_unmatched_*` null/covariance with `matched_calibrated_*`, and add a **depth-template discriminant**: a local boost gives a depth-*independent* `G_F` signature, a global tilt gives a depth-*dependent* one (sign change at a transition depth — the same structure as the tomographic forecast in the physics program). Report a ROC / Fisher separation of boost vs tilt as a function of depth coverage and null calibration.

**Method:** `code/exp04_GF_matched_null_boost_vs_tilt.py`.

**Acceptance:** both FPRs driven below the registered threshold under matched calibration; a quantitative boost-vs-tilt separation (ROC AUC or Fisher σ) reported as a *forecast*; until then, `G_F` is stated to give no boost-vs-tilt separation.

---

## U5 — Comparator-multiverse reporting for `x_C`/`Q`  (formalizes the specification-curve link)

**Audit finding (Low):** `x_C`/`Q` are comparator-relative (flat/matched/closed); displays must show the comparator.

**Upgrade.** Report `x_C`/`Q` as a **comparator-multiverse**: the value under each admissible comparator, with the spread as an explicit uncertainty — a specification-curve over the comparator degree of freedom. This both satisfies the display requirement and operationalizes the multiverse positioning (`06`).

**Method:** `code/exp05_comparator_sensitivity.py`.

**Acceptance:** every `x_C`/`Q` is shown with its comparator and the across-comparator spread; the comparator is never implicit.

---

## Upgrade → novelty map

| Upgrade | Audit finding cured | New object | Novelty |
|---|---|---|---|
| U1 sector profile + cancellation | `x_C≈0≠isotropy` (Medium) | `DepartureProfile` | F7 |
| U2 magnitude companion | `F` naming (Medium) | total-anisotropy `M` | F8 |
| U3 firewall spec + fuzzer | semantic-split mislabel (High) | portable spec + fuzzer + label linter | F9 |
| U4 matched-null depth discrimination | `G_F` FPR≈1 (High) | boost-vs-tilt ROC/Fisher forecast | upgrades F5 |
| U5 comparator-multiverse | comparator display (Low) | comparator specification-curve | strengthens F2 |

All five are achievable with the reference implementation in `code/`; none requires a native low-ℓ solver. Plus the two pure corrections (retire "detection"/"98% accuracy" prose; over-stamp legacy VER2 readiness labels as `legacy_not_current`).
