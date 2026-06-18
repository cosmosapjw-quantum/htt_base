# 02 — Reframe & Reorganization (Methods-Paper Framing)

How to present the formalism so its architectural novelty is unmistakable and the audit's honesty corrections are built in. Includes a model abstract, the contribution paragraph, a claim ladder, and a section plan for a standalone methods paper (or the methods backbone of the physics paper).

---

## A. Model abstract (drop-in; ~170 words)

> Tests of the cosmological principle increasingly rest on contested anomaly signals, where the dominant failure mode is not a wrong number but an over-claimed one — a diagnostic relabeled as evidence, a transformed significance called a detection, a signed coordinate read as an isotropy magnitude. We present a claim-tiered diagnostic algebra for quantifying departure from FLRW in which the definitions, provenance, and *anti-overclaim guarantees* are encoded as machine-checked contracts. A single signed comparator projection `x_C` unifies shear, vorticity, tilt, and anisotropic curvature, carrying a cancellation diagnostic that prevents `x_C≈0` from being mistaken for isotropy; four functionals over it — a policy-normalized score, a registered-threshold exceedance curve, a fail-closed certified filling fraction, and a denominator-evolution-split depth gap — are each constructible only under explicit, recorded policies. A typed boundary separates these diagnostics from inference, and a semantic firewall refuses to construct any object that mislabels itself as evidence, occupancy, geometry, or family identification. We demonstrate the guarantees with an adversarial test suite and quantify the cancellation, certification, threshold, and depth behaviours numerically. The framework makes no detection claim.

*Why it works:* leads with the failure mode the framework solves (overclaim), centers the architecture (F1/F2/F6), states the non-detection up front, and ends on the adversarial validation.

## B. Contribution paragraph (end of introduction)

> Our contributions are: (i) a signed, comparator-explicit departure coordinate with a built-in cancellation diagnostic; (ii) four diagnostic functionals — `Q`, `Π`, `F`, `G_F` — each defined by explicit numerator/denominator/threshold/ceiling/bin policies and constructible only when those policies and certification gates hold; (iii) a semantic firewall that refuses to construct an over-claimed diagnostic (reserved-language refusal, owner/tier pinning, fail-closed gates), validated by an adversarial fuzzer; (iv) a typed diagnostic↔inference boundary that prevents diagnostics from being laundered into evidence; and (v) a sector-resolved departure profile and a total-anisotropy magnitude that make signed-vs-total distinctions explicit. We claim no detection, and we release every quantity under explicit provenance tiers.

## C. Claim ladder (boxed table, early)

| Statement | Tier | Guaranteed by |
|---|---|---|
| `x_C` is the exact signed projection under a stated comparator | **Exact** | constraint algebra; `test_signed_projection_uses_comparator_basis_not_norm` |
| `x_C≈0` does not imply isotropy (cancellation) | **Exact** | `cancellation_index`; sector vector (F7) |
| `Q/Π/F/G_F` are diagnostic-only, owner-pinned MIO | **Exact** | owner/tier pins; semantic firewall (F1) |
| `F` is a certified ceiling-occupancy in `[0,1]` (sign-clean, no clipping) | **Supported** | fail-closed gates (F3) |
| `Π` is a registered-threshold exceedance curve (not a p-value) | **Supported** | threshold registration + `measure_kind` (F4) |
| `G_F` separates numerator- from denominator-evolution | **Supported** | denominator-evolution split (F5) |
| no diagnostic identifies geometry/family or constitutes evidence | **Forbidden** | semantic firewall + MIO↔HTT boundary (F1/F6) |
| boost-vs-tilt depth discrimination | **Forecast** | matched-null + depth template (U4/E4) |

## D. Section plan (standalone methods paper)

| § | Content |
|---|---|
| 1. Introduction | The overclaim failure mode in anomaly cosmology; contribution paragraph (B); claim ladder (C) |
| 2. The signed departure coordinate | `x_C`, comparator dependence, sign/sector structure, the cancellation diagnostic + sector vector (F2/F7) |
| 3. Diagnostic functionals | `Q` (policy-normalized), `Π` (registered-threshold exceedance), `F` (fail-closed certified, + magnitude companion F8), `G_F` (denominator-split depth gap) |
| 4. The enforcement layer | The semantic firewall (F1), owner/tier pinning, fail-closed gates, the typed MIO↔HTT boundary (F6); the adversarial fuzzer (F9) |
| 5. Relation to reproducibility methods | Blinding, pre-registration, multiverse/specification-curve analysis — what is encoded vs added (see `06`) |
| 6. Numerical demonstrations | Cancellation null (E1), `F` fail-closed coverage (E2), threshold bias (E3), comparator sensitivity (E5), firewall fuzz (E6), MIO↔HTT leakage (E7); the matched-null depth discrimination forecast (E4) |
| 7. Limitations | No detection; `G_F` gives no current boost-vs-tilt separation (FPRs exceed threshold); transfer-conditional; no native solver |
| App. | The firewall specification (reserved sets, owner/tier rules, gates) as a portable artifact |

## E. Title options

- *(framework)* "A Claim-Tiered, Contract-Enforced Diagnostic Algebra for Quantifying FLRW Departure"
- *(firewall-forward)* "Diagnostics That Cannot Overclaim: A Semantic-Firewall Formalism for Anisotropy Statistics"
- *(method-forward)* "Encoding Reproducibility: Signed Departure, Fail-Closed Certification, and a Typed Diagnostic↔Inference Boundary"

## F. Editor cover note (if submitted as methods)

> This manuscript presents the statistical-methodology layer underlying our FLRW-departure work as a self-contained contribution: a signed departure coordinate and four functionals whose anti-overclaim guarantees are machine-checked. In response to an external audit we have (a) removed all detection wording, (b) promoted the cancellation diagnostic and added a sector-resolved departure profile, (c) added a total-anisotropy magnitude companion to the certified filling fraction, and (d) packaged the semantic firewall as a specification with an adversarial fuzzer. The framework makes no detection, evidence, or family-identification claim; its contribution is the architecture and its guarantees.

*Net effect:* the reader meets the architecture and the non-detection stance within the first two pages, and every novelty item in `01` is visible.
