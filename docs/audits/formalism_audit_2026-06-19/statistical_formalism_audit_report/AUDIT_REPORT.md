# Adversarial Audit — `x_C / Q / Π / F / G_F` Statistical Formalism

External hostile review. Scope: the statistical and physical formalization of `x_C`, `Q`, `Π`, `F`, `G_F`, and the manuscript/result figures that use them. Software style, packaging, and CI are out of scope. Inputs read in the prescribed order; formalism code consulted where prose/manifests were insufficient.

---

## 1. Verdict

**MAJOR REVISIONS.**

The *formalism itself* (the contracts in `htt/mio/formalism/*` and `htt/src/common/departure_contracts.py`) is internally consistent, sign-aware, provenance-bearing, and test-backed; on its own it would pass with minor revisions. The verdict is driven by the **manuscript/result figures and prose that use the formalism**: the one figure dedicated to communicating the five quantities misdefines three of them, and the prose layer still calls a direction-marginalized Bayes factor a "detection." No rejection trigger fires (no geometry/family/native/posterior claim is actually made, and the governance layer blocks them), so this is not a REJECT — but the manuscript-facing semantics must be corrected before any of these figures or claims are defensible.

## 2. Minimal Defensible Claim

The repository defines a signed, comparator-explicit departure coordinate `x_C = Σ²_std − W²_std + Ω_tilt + Ω_{k,aniso}` and four MIO diagnostic functionals over it — a policy-normalized score `Q`, an empirical exceedance curve `Π`, a certified filling fraction `F`, and a depth-bin contrast `G_F`. As implemented, each carries an explicit comparator/frame/units, an explicit numerator/denominator/threshold/ceiling/bin policy, transfer provenance, and a reserved-language firewall, and each is fenced as **diagnostic-only, MIO-owned**, distinct from HTT likelihood/evidence/posterior/PPC/LOOCV. The only claims the current artifacts support are: (i) `x_C` is an *exact signed projection* of the four kinematic sources under a stated comparator (not an invariant magnitude, not isotropy evidence); (ii) `Q`, `Π`, `F`, `G_F` are *descriptive diagnostics* with explicit policies and separate provenance; (iii) under the shipped diagnostic null banks the local-null FPR (≈0.28) and survey-systematic-null FPR (≈0.94; adjusted 1.0) both **exceed** the registered 0.15 threshold, so **no local/global (boost-vs-tilt) discrimination is achieved and no global-tilt statement is licensed**; (iv) all transfer-dependent inputs are transfer-conditional and **no native low-ℓ Bianchi solver output exists**. No detection, evidence, model-ranking, posterior-odds, truth-certificate, native-validation, or Bianchi family/geometry claim is supported by any of `x_C/Q/Π/F/G_F` alone or in combination.

## 3. Fatal Blockers

These block *current manuscript use* (not the formalism itself); each is fixable without changing the contracts.

1. **The "semantic split" figure misrepresents the formalism it is meant to define.** In `docs/generated/current_science_plot_payload.json → semantic_and_vectors.semantic_split`, the canonical symbols are bound to non-canonical quantities: `Π` = "inter-policy spread across current denominator policies" (owner MIO), `F` = "one minus look-elsewhere adjusted local-null FPR" (**owner HTT**), `G_F` = "normalized log depth-response envelope from null-bank payload." The formalism defines `Π` as an exceedance curve (MIO), `F` as the certified filling fraction `x_C/U` (MIO), and `G_F` as a depth-bin ratio of certified `F` (MIO). The figure (`fig_current_qfpi_gf_semantic_split`) therefore teaches incorrect semantics for three of five symbols, including a MIO↔HTT owner swap for `F`. Until relabeled or repopulated, this figure cannot be used.
2. **"Detection" prose for a marginalized Bayes factor.** The compiled report (per `pdf_claim_lint_report.md`) still contains "the tilt detection (ln B > 5)…" (p.181), "spurious tilt detections" (p.183), and "the departure parameter detection" (p.196), while the same document concedes (p.209) that "ln B ≈ +26.3 is a direction-marginalised Bayes factor." Calling this a *detection* contradicts the formalism's own contracts (`Q`/`Π` are explicitly not detection) and is the precise semantic overreach this audit targets. The lint classifies `lnB`+language as `warn`; it must be `fail`.

## 4. Formalism Findings

| Severity | Location | Problem | Required Fix |
|---|---|---|---|
| High | `current_science_plot_payload.json` → `semantic_and_vectors.semantic_split`; fig `fig_current_qfpi_gf_semantic_split` | `Π`, `F`, `G_F` bound to non-canonical quantities (policy spread; 1−FPR/owner HTT; null-bank envelope), contradicting the formalism definitions | Either relabel the bars with their actual quantities (e.g. "Q denominator-policy spread", "local-null survival 1−FPR (HTT)", "null-bank depth envelope") **without** reusing `Π/F/G_F`, or populate the figure with the canonical `Π`(exceedance), `F`(`x_C/U`), `G_F`(depth-`F` ratio) values from the formalism objects |
| High | Compiled report pp.181/183/196 (`pdf_claim_lint_report.md`); lint rule severity | "tilt detection" / "detection" prose for a direction-marginalized Bayes factor; lint rule treats it as `warn` | Replace "detection" wording (see §8); promote the `lnB`+strength-language lint pattern from `warn` to `fail` |
| Medium | `pdf` p.115; carried from prior VER06 audit | "the departure parameter measures, to 98% accuracy, the neutrino [...]" — unsupported precision claim | Reword to a provenance-bearing contribution statement or delete (see §8) |
| Medium | `filling_fraction.py` (name); legacy fig `root__fig_filling_fraction_posterior` | `F` named "(certified) filling fraction" — physical-occupancy connotation; one legacy figure carries "posterior" in its filename | Define `F` in text/caption as "fraction of the admissible linear-regime (MES) ceiling occupied by the *signed* projection `x_C`"; retire the `*_posterior` legacy filename from manuscript use (it is `exploratory`/conditioned, but the name must not appear) |
| Medium | `component_breakdown.py` (`x_C`, `cancellation_index`); any `x_C`/`F` figure | `x_C` is subject to inter-sector cancellation: `x_C≈0` (and hence `F≈0`) can coexist with large shear+vorticity or tilt+curvature (verified: `cancellation_index→1` with `|components|`≠0). `x_C/F` near zero is **not** isotropy | Report `cancellation_index` and the component breakdown alongside every `x_C`/`F`; add the caveat that `x_C/F` are signed projections, not total-anisotropy or isotropy measures |
| Medium | Legacy `htt_ver2_export_discrimination_matrix.json`, `mio_predictive_residuals_certificate.json` | Internally assert `atlas_available:true`, `atlas_ready`, `mock_coverage_status:adequate`, `production_candidate`/`production-grade` — all false in current state; quarantined as `prior_context_only` but stale labels persist in payloads | Over-stamp/normalize internal promotion fields to `legacy_not_current` so they cannot be surfaced as current capability |
| Low | `x_C`/`Q` figures and tables | `x_C`/`Q` are comparator-relative (`flat`/`matched`/`closed`); the contract carries the comparator, but displays must too | Require the comparator label on every `x_C`/`Q` figure/table cell |
| Low | `isotropy_gap.py` floor logic; any `G_F` figure | `G_F` uses `max(F,floor)`; when `floor_applied` a real gap is censored | Surface `floor_applied_by_bin` wherever `G_F` is shown |

## 5. Equation/Definition Audit

| Quantity | Status | Issue | Required Fix |
|---|---|---|---|
| `x_C = Σ²−W²+Ω_tilt+Ω_{k,aniso}` | **Correct, with caveat** | Sign convention matches `CANONICAL_COMPONENT_SIGNS` (W² at −1); exported as a *signed comparator projection*, never a norm (`test_signed_projection_uses_comparator_basis_not_norm`). But comparator-relative and cancellation-prone | State comparator on display; report `cancellation_index`; never describe as invariant magnitude or isotropy measure |
| `Q = numerator_policy(x_C)/U` | **Correct** | Numerator policy explicit (signed/abs/positive_part); denominator `U` positive-finite-enforced (`_positive_finite_float`); reserved-language scan bars "filling/occupancy/posterior/evidence/family/geometry" | None to the contract. Ensure signed-`Q` (which can be negative) is never plotted as if an occupancy |
| `Π` (exceedance) | **Correct in code; misrepresented in figure** | Code: empirical survival fraction of `Q`/`F` samples with threshold registration + anti-post-hoc + measure-kind gating. Figure `semantic_split` redefines `Π` as a denominator-policy spread | Fix the figure (§4 row 1); in captions/tables state `measure_kind` (exceedance ≠ p-value unless matched null ensemble) |
| `F = x_C/U` (certified filling) | **Correct in code; mis-owned in figure; naming risk** | Code: sample-wise (not ratio-of-means), sign-clean `x_C≥0` enforced, admissible ceiling required, `0≤F≤1` enforced **without clipping** (`test_f_rejects_super_ceiling_values_without_clipping`), external/atlas/observational denominators barred from certifying. Figure `semantic_split` defines `F` as `1−FPR` owner HTT | Fix the figure owner/definition (§4 row 1); define "filling fraction" precisely (§4 row 4); note `F` inherits the cancellation caveat |
| `G_F = exp(log F_cmp − log F_ref)` (floor-stabilized depth ratio) | **Correct in code; misrepresented in figure** | Code: ≥2 ordered non-overlapping bins, mandatory covariance/null/calibration + denominator-evolution split; metadata scan bars the literal phrase "global tilt." Figure redefines `G_F` as a null-bank envelope | Fix the figure (§4 row 1); surface `floor_applied_by_bin`; keep the "global tilt" prohibition in prose |

## 6. Statistical Semantics Audit

| Item | Status | Issue | Required Fix |
|---|---|---|---|
| `x_C` invariance | Pass | Treated as comparator projection, not invariant; tests enforce | Maintain; add cancellation caveat |
| `Q` occupancy/probability leakage | Pass | `_FORBIDDEN_Q_METADATA_TERMS` + `test_q_artifact_payload_never_uses_filling_or_occupancy_language` | Maintain |
| `Π` truth/detection probability | Pass (code) / Fail (figure) | Code bars "probability/posterior/evidence/bayes factor/truth certificate"; figure relabels `Π` | Fix figure; state `measure_kind` so exceedance is not read as significance |
| `Π` look-elsewhere / threshold registration | Pass | `ThresholdPolicy.PRE_REGISTERED` requires `registration_hash`+`selection_rule`, bars post-hoc; payload records `look_elsewhere_trials:3` | Maintain; report the trials factor wherever a threshold is selected |
| `F` clipping / sign-clean / admissible ceiling | Pass | Raises on `F∉[0,1]`, `x_C<0`, non-admissible/external ceiling | Maintain |
| `F` "certified filling" semantics | Partial | Object is `x_C/(MES-linear ceiling)`, not a physical volume occupancy; name connotes more | Define precisely (§8) |
| `G_F` global-tilt competition | Partial | Local-null FPR ≈0.28 and survey-systematic FPR ≈0.94 (adjusted 1.0; 180/192) both exceed 0.15 → discrimination **blocked**; metadata bars "global tilt" | State explicitly that `G_F` currently yields **no** local/global separation; never attach tilt-evolution meaning |
| `G_F` denominator-evolution confound | Pass | `_denominator_split_payload` exposes `x_C`-vs-ceiling evolution; `mean_summary_is_decompositional:False` | Maintain; show the split when `G_F` is shown |
| MIO/HTT separation | Pass | `NormalizedScore/ExceedanceCurve/...` pinned owner MIO, `claim_tier=diagnostic_only`; result packs forbid ranking; HTT `posterior_pushforward` rejects MIO inputs (`reject_mio_likelihood_inputs`, `_FORBIDDEN_MIO_TOKENS` incl. `ln_b`,`evidence`,`posterior`,`score`) | Maintain |
| Readiness-label hygiene (legacy VER2) | Partial | Legacy payloads assert `atlas_available:true`/`production-grade`; quarantined but stale | Over-stamp as `legacy_not_current` (§4) |

## 7. Figure Interpretation Audit

Only figures whose interpretation overreaches are listed.

- **`fig_current_qfpi_gf_semantic_split` (appendix-conditioned, diagnostic-only).** Overreach by *misdefinition*, not by claim tier: the very figure meant to show the semantic split binds `Π`, `F`, `G_F` to unrelated current-code proxies and swaps `F`'s owner to HTT (§3.1, §4 row 1). The `must_state_distinct_semantics` caption policy is *satisfied in form but defeated in substance* — the bars show "distinct" quantities under the wrong names. Must be relabeled or repopulated before appendix use.
- **`fig_current_mio_depth_residual_vectors` (right panel, `G_F` depth envelopes).** Acceptable only as a null-bank envelope diagnostic. Because the survey-systematic FPR for the `G_F`+direction rule is ≈1.0, the panel must not be captioned or read as evidence of depth/tilt structure; add an explicit "no local/global separation at current FPR" statement and surface `floor_applied`.
- **`root__fig_filling_fraction_posterior` (conditioned-legacy, exploratory).** Filename embeds "posterior"; `F` is not a posterior. The sidecar correctly tiers it as appendix-only conditioned diagnostic, but the filename must not surface in the manuscript.
- **`fig_current_local_global_rank_fpr`.** Interpretation is acceptable *as a blocked gate-stress plot*; ensure the caption states that both null FPRs exceed threshold (blocked), not merely that it is a "gate stress" diagnostic.

## 8. Claim-Tier Corrections (exact wording to replace)

- p.181 — replace: "The tilt detection (ln B > 5) survives all tested perturbations except…" → **"The conditional, direction-marginalized diagnostic preference for a nonzero tilt-like degree of freedom (ln B > 5) persists under all tested perturbations except…; this is a re-expression of the dipole/bulk-flow significance, not a detection of anisotropic geometry."**
- p.183 — replace: "the pipeline does not generate spurious tilt detections" → **"the pipeline does not generate spurious tilt-preference signals under structured nulls (diagnostic only)."**
- p.196 — replace: "does not invalidate the departure parameter detection" → **"does not invalidate the departure-parameter diagnostic; it constrains its interpretation."**
- p.115 — replace: "the departure parameter measures, to 98% accuracy, the neutrino [anisotropic stress]" → **"under the recorded single-fluid transfer assumption, ≈98% of the modelled `D₂` contribution originates in the neutrino anisotropic stress (transfer-conditional; not a measurement-accuracy statement)."**
- Figure `semantic_split` labels — replace the symbols `Π`, `F`, `G_F` with **"Q-denominator-policy spread"**, **"local-null survival (1−FPR), HTT"**, **"null-bank depth envelope"** respectively (or repopulate with canonical values).
- Any `x_C`/`F` caption — add: **"`x_C` is a signed comparator projection; `x_C≈0` (or `F≈0`) reflects inter-sector cancellation, not isotropy — see component breakdown / cancellation index."**
- `F` definition (first use) — **"`F` is the certified fraction of the admissible linear-regime (MES) ceiling occupied by the signed departure projection `x_C`; it is not a physical volume-filling fraction."**

## 9. Additional Analyses Required (before any stronger claim)

1. **Matched-calibrated null and covariance for `G_F`.** Replace `diagnostic_unmatched_*` statuses with `matched_calibrated_*`, and drive both the local-null and survey-systematic FPRs below the registered threshold, before any depth-gap is described as anything beyond a diagnostic contrast. At present the depth-gap rule is fully degenerate against the survey-systematic null.
2. **Repopulate or relabel the semantic-split figure** with the canonical `Π`/`F`/`G_F` objects (or non-canonical labels), and add a figure-level unit/owner table.
3. **Cancellation reporting.** Emit `cancellation_index` and the signed component breakdown next to every `x_C`/`F` summary; add a worked counter-example showing `x_C≈0` with large sectors.
4. **`Π` measure-kind disclosure.** For every exceedance curve shown, state `measure_kind` and (if `null_ensemble`) the calibration/covariance status, so the curve is not read as a significance/p-value curve.
5. **Promote the lint rule.** Make `lnB`-numeric-with-strength-language a `fail`, not a `warn`, in `pdf_claim_lint`; re-run to zero failures.
6. **Legacy-label normalization.** Over-stamp the VER2 export payloads' `atlas_available`/`atlas_ready`/`production_candidate`/`production-grade` fields as `legacy_not_current`.
7. **(For any local/global statement at all)** the HTT-owned posterior pushforward + matched-null + PPC/LOOCV path must close — `posterior_pushforward.py` already enumerates the required `_EXPECTED_STATUSES`; none may be assumed ready while the FPR gates fail.

## 10. Safe Claims

- `x_C` is an **exact** signed projection of shear, vorticity, tilt, and anisotropic curvature under a stated comparator; it is a bookkeeping coordinate, not an invariant magnitude or an isotropy measure.
- `Q`, `Π`, `F`, `G_F` are **MIO diagnostic-only** functionals with explicit numerator/denominator/threshold/ceiling/bin policies, separate provenance, and reserved-language firewalls; they are test-backed.
- `F` is a certified ratio in `[0,1]` (sign-clean, admissible MES-linear ceiling, no clipping); external/atlas/observational denominators are correctly barred from certifying it.
- `Π` is an empirical exceedance curve with threshold registration and anti-post-hoc guards; it is not a truth/detection probability or posterior odds.
- `G_F` is a floor-stabilized depth-bin ratio of certified `F` with mandatory covariance/null/calibration metadata and a denominator-evolution split; under the current null banks it provides **no** local/global discrimination (both FPRs exceed threshold) and licenses **no** global-tilt statement.
- All transfer-dependent inputs are **transfer-conditional**; no native low-ℓ Bianchi solver output exists; external transfer is not validated as native.
- MIO diagnostics are kept separate from HTT evidence/posterior/PPC/LOOCV; result packs forbid model ranking; the HTT pushforward rejects MIO inputs.
- None of `x_C/Q/Π/F/G_F`, alone or combined, identifies a Bianchi family or geometry, or constitutes a detection, evidence, posterior odds, or truth certificate.

---

*Audit basis: `READINESS_CHECKLIST.md`; `main.tex` (+ generated TeX snippets); `current_science_plot_payload.json`; result packs A/B/C; transfer-sensitivity, publication-claim-freeze, pdf-claim-lint, revision-claim-lanes, plot-list reports; VER2 generated artifacts; figure manifests (current, conditioned-legacy, paper/ver2); and the formalism sources `htt/mio/formalism/{budget_spec,normalized_score,exceedance,filling_fraction,isotropy_gap,component_breakdown}.py`, `htt/src/common/departure_contracts.py`, `htt/htt/htt/departure/posterior_pushforward.py`, with `tests/mio/*` and `tests/htt/test_posterior_pushforward.py` consulted for enforced guards.*
