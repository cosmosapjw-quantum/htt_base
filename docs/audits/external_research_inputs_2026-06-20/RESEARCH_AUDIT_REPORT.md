# Adversarial Research Re-Audit — HTT/Bianchi Manuscript (VER06, audit #3)

Scope: research formalization and results only (physics, math, statistics, inference, claim tiers, figure interpretation, manuscript logic). Software/packaging excluded. This package ships the compiled PDF (`manuscript/htt_base_research_report.pdf`, 352 pp.) plus `reports/result_pack_{A,B,C}.md`, `reports/transfer_sensitivity_report.md`, `manuscript/pdf_claim_lint_report.md`, the figure inventory, and `pr_deltas/`. Citations are to PDF section/proposition/equation numbers and report/manifest paths (no `.tex` in this package).

---

## 1. Verdict

**MINOR REVISIONS** (near-PASS).

Net change since audit #2: most prior items are resolved. The CF4++ `lnB≈+44` (previously self-flagged "untraceable") is **gone** — the evidence ladder is now `lnB≈+26.40` (VER05 primary, "Conditional evidence", §9.1.2), a VER06-corrected Bianchi V `lnB=+24.8` (§9.1.3), and tilted VII_h `lnB≈+24` (§4.5.3), all labelled legacy transfer-conditional. The filling fraction is disambiguated: the naive `F=x_C/x_max` is now declared **ill-defined** and replaced by a signed saturation coordinate (§3, "the standard filling fraction … is ill-defined; a signed saturation coordinate is required") and a Class-conditioned filling fraction (Def 3.19), distinct from the legacy budget-normalised score `F=0.093±0.025`. Comparator invariance is **proved** (x/Q/Π identical across comparators when `Ω_{k,aniso}=0`; comparator-dependent only for BV/BIX, `Δcomp=1.0`, Table 8.7). Robustness is added (`|ΔlnB|≤0.16` under transfer variation; `lnB` invariant under reionisation to `10⁻¹⁰`; polarisation feedback checked; Jeffreys scale, §7). Null/covariance gates now exist as prerequisites/forecast surfaces (PR-100 directional-coherence covariance status; PR-101 G_F + `gf_matched_null_forecast_report.json`; PR-102 FLRW null-predictive tension gate). No rejection trigger fires. What remains is one recurring wording item plus three minor residuals.

## 2. Minimal Defensible Claim

Under the premise that the >5σ matter-dipole anomaly is substantially physical, and using an explicitly legacy external/proxy transfer path, the observed dipole is re-expressible in frame-invariant departure variables as a single tilt-like (boost) degree of freedom: a transfer-conditional, direction-marginalized model comparison reaches `lnB≈+26.4` (Jeffreys-strong but a restatement of the dipole significance, §9.3/§6), while anisotropic shear geometry is disfavoured and the orthogonal growing mode is rejected (`lnB=−18.7`) because its Frobenius-coupled vorticity exceeds the Saadeh bound by ~6 orders (§4.5). The MES algebraic ceilings are derived; the Saadeh–MES complementarity is explicit (`Σ²_std<8×10⁻²²` vs `Σ²_std<6.4×10⁻⁶`, §4.5); frames (geometry/matter/CMB rest) are explicit; `x_C` is a signed comparator coordinate (the naive filling fraction is declared ill-defined); and the neutrino quadrupole dominance (`N₂/F₂=28`, 98.4% of `D₂`) is a derived, transfer-conditional result (Proposition 5.3, §5.13.5). No native low-ℓ Bianchi solver output exists; no Bianchi family is identified; no geometry is detected; MIO certificates are diagnostic-only and rank no models.

## 3. Fatal Blockers

None. No current claim asserts an identified Bianchi family, a detected geometry, native validation of external transfer (§9.3 explicitly: external/proxy provenance "not native low-ell solver validation"), MIO promoted to model-weight/likelihood-ratio/adjudication (Result Pack C: "does not rank models, does not modify HTT-owned evidence traces"), scalar-only geometry evidence, or an evidence claim lacking its null/covariance/PPC/LOOCV prerequisites (Result Pack B gates these as `prerequisite_not_evidence`).

## 4. Major Findings

| Severity | Location | Problem | Why It Matters | Required Fix |
|---|---|---|---|---|
| Medium (recurring) | §5.13.5 ("the Phase 1.0 solver **discovers**…"); §9.3.1 ("the most consequential result of the solver is the **discovery**…") | The neutrino-quadrupole dominance is repeatedly called a "discovery" of "the solver", though the hard boundary states no native low-ℓ solver exists (the Phase 1.0 solver is the legacy/oracle) and the result is transfer-conditional | Same wording flagged in audits #1 and #2; "discovery"/"the solver discovers" on a non-native, transfer-conditional result borders the no-native-solver boundary | Downgrade to "the solver **indicates** / the derived result is" and mark transfer-conditional; reserve no "discovery" for an oracle/legacy output (the *evidence* summary is already correctly disclaimed as "not an independent discovery", §9.3) |
| Low–Med | Eq. 3.58 `Π(q⋆):=P(Q>q⋆|D)` | `Π` is still defined as a **posterior** exceedance probability, while the companion formalism defines `Π` as an empirical exceedance fraction barred from "probability" language | Same symbol, two definitions across the paper and its formalism; the disclaimer "not a truth probability/p-value" (§3.7.3) and the declared-measure framing mitigate but do not remove the collision | Either harmonize the definition with the formalism's empirical exceedance, or state once that the manuscript `Π` is a model-conditional posterior exceedance, explicitly distinct from the MIO diagnostic `Π` |
| Low–Med | abstract/intro `F=0.093±0.025` (§1, §7) vs §9.1.4 "Filling fraction: `F≈6.3%`" vs Def 3.19 | Two different "F" headline numbers (legacy budget-normalised score 0.093 vs class-conditioned filling 6.3%) still coexist; now defined separately but not cross-referenced at first mention | A reader can conflate the budget-normalised score with the filling fraction | At each headline use, name which `F` it is (Def 3.19 class-conditioned vs legacy budget-normalised score) and cross-reference; the abstract should disambiguate |
| Low (self-flagged) | `manuscript/manuscript_figure_inventory.md` (10 `manual_status_number` rows: ch01:221 `test_count`; ch07:374–375 `pytest_count`; generated `ver2_*` `manifest_ready_count`/`blocked_figure_count`) | Ten hardcoded test/figure-manifest counts in the manuscript are flagged by the project's own inventory as manual rather than generated-source | Manual status numbers drift from the artifacts they report (audit check F) | Replace the 10 manual counts with generated-source values (the inventory already lists their hashes/targets) |

## 5. Physics/Math Audit

| Item | Status | Issue | Required Fix |
|---|---|---|---|
| Frame conventions (geometry/matter/CMB rest, tilt rapidity β) | OK | Explicit and consistent (§2.x, §6; β=1.334×10⁻³ derived from Watkins) | None |
| `x_C` signed comparator coordinate; naive `F` | OK (improved) | `x_C` signed; the naive `F=x_C/x_max` now declared **ill-defined**, replaced by a signed saturation coordinate (§3) | None |
| MES derivation + Saadeh–MES complementarity | OK | Derived; ~6-order Saadeh/MES gap explained, shrinking to ~1 order for the growing mode (§4.5) | None |
| Comparator invariance of x/Q/Π | OK (now proved) | Invariant when `Ω_{k,aniso}=0`; comparator-dependent for BV/BIX (`Δcomp=1.0`, Table 8.7) — stated correctly | None |
| Neutrino-quadrupole dominance | OK (derived) | Now Proposition 5.3 (Thomson-suppressed photons vs free-streaming neutrinos under common shear); `N₂/F₂=28`, 98.4% of `D₂` | Transfer-conditional tag + drop "discovery" (see §8) |
| FLRW / rank-deficient / zero-denominator limits | OK | FLRW-limit phase gate; rank-deficient → `blocked_no_claim` (Result Pack B) | Confirm boost-only/tilt-only limits each stated once |
| Deterministic transfer template vs anisotropic covariance | Partial | Transfer template external/proxy-flagged (transfer_sensitivity_report); separation implied | State once that the deterministic template and anisotropic-covariance effects are modelled separately, template flagged external/proxy |

## 6. Statistics/Inference Audit

| Item | Status | Issue | Required Fix |
|---|---|---|---|
| `lnB` tiering | OK | "Conditional evidence" labels; VER05 `+26.40`, VER06 Bianchi V `+24.8`, VII_h `+24`, all legacy transfer-conditional (§9.1–9.3) | None |
| CF4++ `lnB≈+44` provenance | OK (resolved) | Removed; no untraceable headline remains | None |
| Dipole-restatement disclaimer | OK | "restatement of the >5σ dipole anomaly … not an independent discovery" (§9.3) | Keep (and extend the same care to the neutrino "discovery", §8) |
| Robustness (transfer/reionisation/polarisation) | OK | `|ΔlnB|≤0.16`; reionisation invariance `<10⁻¹⁰`; polarisation feedback; Jeffreys scale (§6–7) | None |
| Channel ablation / Occam | OK | Vorticity Occam cost ~1.4 nats penalises VII_h (§4.5); waterfall retained | None |
| PPC/LOOCV/null/matched-mask/covariance gates | OK (prerequisites) | PR-100 covariance status, PR-101 G_F matched-null forecast, PR-102 FLRW null-predictive tension gate; reported as prerequisites/forecast, not evidence (Result Pack B/C) | Report the matched-null `G_F` explicitly as a *forecast* in prose |
| MIO certificates | OK | Diagnostic-only; "does not rank models" (Result Pack C) — new rejection trigger (model-weight/adjudication) not tripped | None |
| `Π` definition | See §4 | Posterior `P(Q>q⋆|D)` vs formalism empirical exceedance | Harmonize/annotate (see §4) |
| Look-elsewhere/registration | OK | `Π` requires registered threshold + look-elsewhere/null metadata (Remark 3.17) | Keep |
| Observed-data figures descriptive | OK | Planck low-ℓ/DESI/CF4 `diagnostic_only` with unbound matched-null/covariance gates (manifests, unchanged from audit #2) | None |

## 7. Figure/Result Audit

Only figures/tables whose interpretation is wrong, under-supported, or overclaimed:

- **None overclaimed at the result level.** Observed-data figures (Planck low-ℓ residual, lensing bandpowers, DESI footprint, CF4 velocity/density) remain `diagnostic_only` with the correct `failed_gates`; the conditioned-legacy gallery (Appendix H, the Monte-Carlo `F` posterior at S3) is marked legacy; the repository quarantines 97 non-ready figures (`repository_quarantined_figures: 97`).
- **Table/inventory hygiene (minor):** the 10 `manual_status_number` entries (figure inventory) are test/manifest counts that should be generated-source — see §4.
- **`tab:fb7_lnB_11types`** (if still present): confirm `NO_FLRW_LIMIT` rows show "N/A (no FLRW limit)" rather than spurious-precision `lnB` (audit-#2 item; verify it was applied in this build).

## 8. Claim-Tier Corrections (exact wording)

- §5.13.5 — replace "The Phase 1.0 solver **discovers** a striking result" → "The Phase 1.0 (legacy/oracle, transfer-conditional) solver **indicates**…".
- §9.3.1 — replace "The most consequential result of the solver is the **discovery** that neutrinos contribute 98.4% of the total `D₂`" → "A principal derived result (Proposition 5.3, transfer-conditional) is that neutrinos contribute ≈98% of the modelled `D₂`".
- §6.x / §9.3 — keep the existing "not an independent discovery" disclaimer for the `lnB` summary; apply the same standard to the neutrino result.
- Eq. 3.58 — annotate: "`Π` here is a model-conditional posterior exceedance probability, distinct from the MIO diagnostic exceedance curve of the same symbol," or redefine to the empirical exceedance.
- §1/§9.1.4 — at each headline, name the `F` (Def 3.19 class-conditioned filling vs legacy budget-normalised score) and cross-reference.

## 9. Additional Analyses Required (before stronger claims)

1. Convert the 10 manual status numbers to generated-source (self-flagged).
2. Report the matched-null `G_F` (`gf_matched_null_forecast_report.json`) explicitly as a *forecast* in the discussion; until matched nulls are bound, keep the local/global discrimination at "candidate" (Result Pack B ceiling: conditional).
3. State the deterministic-template vs anisotropic-covariance separation once, with the transfer template flagged external/proxy at each use.
4. Foreground that all `lnB` are rest-frame/direction-marginalized and observer-motion marginalization (FB-8) is the remaining step before any observer-frame reading.
5. Harmonize `Π`/`Q`/`F` definitions and reserved language with the companion formalism so the paper and formalism use the symbols identically.

## 10. Claims That Are Safe

- `x_C` is the exact signed comparator projection of shear, vorticity, tilt, and anisotropic curvature; the naive filling fraction is ill-defined and replaced by a signed saturation coordinate.
- The MES algebraic ceilings are derived; the Saadeh–MES complementarity (~6 orders, shrinking to ~1 for the growing mode) holds.
- Under the dipole premise and a legacy external/proxy transfer path, the dipole is re-expressible as a single tilt-like (boost) d.o.f.; the transfer-conditional `lnB≈+26.4` is a restatement of the >5σ dipole significance, not independent evidence.
- Anisotropic shear geometry is disfavoured; the orthogonal growing mode is rejected (`lnB=−18.7`) via the Saadeh-exceeding Frobenius vorticity.
- The neutrino quadrupole dominance (`N₂/F₂=28`, ≈98% of `D₂`) is a derived, transfer-conditional result (Proposition 5.3).
- The three diagnostic layers (x, Q, Π) are comparator-invariant for curvature-free models and comparator-dependent (reported) for BV/BIX.
- `lnB` is robust to transfer variation (`|ΔlnB|≤0.16`), reionisation (`<10⁻¹⁰`), and polarisation feedback.
- Observed-data figures are descriptive diagnostics with matched-null/covariance gates unbound; MIO certificates are diagnostic cross-checks that rank no models.
- No native low-ℓ Bianchi solver output exists; external/AniCLASS/legacy transfer is transfer-conditional; no Bianchi family is identified and no geometry is detected.

---

*Net since audit #2: CF4++ `+44` untraceability resolved; comparator invariance proved; filling fraction disambiguated (naive `F` declared ill-defined); robustness (transfer/reionisation/polarisation/Jeffreys) added; null/covariance gates added as prerequisites/forecast; Bianchi V corrected (`+24.8`). Outstanding: the recurring "discovery" wording on the (non-native, transfer-conditional) neutrino result, the `Π` posterior-vs-empirical definition, the dual filling-fraction headline, and 10 self-flagged manual status numbers. Verdict MINOR REVISIONS, near-PASS.*
