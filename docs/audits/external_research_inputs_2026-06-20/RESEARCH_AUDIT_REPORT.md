# Adversarial Research Re-Audit — HTT/Bianchi Manuscript (VER06)

Scope: research formalization and results only (physics, math, statistics, inference, claim tiers, figure interpretation, manuscript logic). Software/packaging/tests-as-software excluded. Sources: `docs/manuscript/{main,ch01..ch11,appendices}.tex`, `docs/generated/{manuscript_plot_list_index,result_pack_A/B/C,transfer_sensitivity_report,pdf_claim_lint_report}.md`, and figure manifests under `figures/`. Compiled PDF absent by design; line cites are to `.tex` and report paths.

---

## 1. Verdict

**MINOR REVISIONS.**

The structural overclaims flagged in prior rounds are gone: the manuscript now frames itself as a claim-tiered framework (`main.tex:153–158`), the Bianchi Bayes factors are consistently tiered as **legacy, transfer-conditional, dipole-restatement** numbers (not native evidence), the eleven-type `ln B` table is reframed as an **FLRW-limit continuation test** (`ch07:559–576`), the filling-fraction `BF>5×10⁴` is explicitly disclaimed as "a restatement of the >5σ dipole anomaly … not an independent discovery" (`ch07:646–653`), and observational figures are `diagnostic_only` with the correct `failed_gates`. No rejection trigger fires as a *current* claim. What remains is residual prose precision, one untraceable number, cross-chapter numeric consistency, and harmonization of `Π`/`Q`/`F` terminology with the companion formalism — none of which invalidates the main claim.

## 2. Minimal Defensible Claim

Under the premise that the matter-dipole anomaly is substantially physical, and using an explicitly legacy external/proxy transfer path, the manuscript shows that the observed dipole is re-expressible in covariant departure variables as a single tilt-like (boost) degree of freedom: a transfer-conditional, direction-marginalized model-comparison summary reaches `ln B_tilt ≈ +25.3` (`ch09:512`), this preference resides ≈100% in the tilt channel while anisotropic shear geometry is mildly *disfavoured* (`ln B = −0.87`, PDF p.159), and the corresponding budget-normalized departure is a few percent of the MES ceiling. The MES bound hierarchy is *derived* under stated assumptions (`ch04:338`), the frame structure (geometry/matter/peculiar) is explicit (`ch03:1502+`), and `x_C` is treated as a signed comparator coordinate (`ch03:1106`), not an invariant magnitude. No native low-ℓ Bianchi solver output exists; no Bianchi family is identified; no geometry is detected; MIO diagnostics are not evidence; all transfer-dependent rows are transfer-conditional.

## 3. Fatal Blockers

None. No current claim asserts an identified Bianchi family, a detected geometry, native validation of external transfer, MIO-as-evidence, scalar-only geometry evidence, or an evidence claim lacking its required null/covariance/PPC/LOOCV support. The result packs and figure manifests block these at the governance layer (`result_pack_B.md` claim boundaries; `figures/observed_current/*` `failed_gates`).

## 4. Major Findings

| Severity | Location | Problem | Why It Matters | Required Fix |
|---|---|---|---|---|
| Medium | `ch09:497` | The 98.4% neutrino-quadrupole result is called "the discovery", though it issues from the FLRW oracle/legacy transfer that `ch09:543` itself calls "a toy model, not a production tool" and not native solver output | "Discovery" reads as a validated finding; contradicts the toy/transfer-conditional status and the no-native-solver boundary | Downgrade to "the legacy transfer path indicates …"; mark transfer-conditional; remove "discovery" |
| Medium | `ch08 §8.19`; PDF p.158 | The CF4++ headline `ln B ≈ +44` is self-described as "untraceable from the canonical VER05 JSON; a dedicated rerun is recommended before publication" | A headline-adjacent evidence number with no reproducible provenance cannot stand in a results/discussion chapter | Reproduce from source and bind a config/input hash, or remove the `+44` figure pending the rerun |
| Medium | `ch01:152`, `ch02:485` vs `ch03:1112` vs `ch07:632` (+ ch09 TOC "F≈6.3%") | The headline departure number is quoted inconsistently: `F_Bayes=0.093±0.025` (intro/abstract), `Q̄=0.092` HPD[0.035,0.19] (ch03), `FF=0.063 (w=0)/0.084 (w=1/3)` (ch07); `Q̄=0.092 ≈ F_Bayes=0.093` invites Q/F conflation | A reader cannot trace the abstract's number to the results chapter; Q (occupancy ratio) and F (filling fraction / budget-normalized score) are distinct but numerically merged | Reconcile to one scenario per quantity; state the abstract number's exact scenario/EoS and whether it is Q, F, or F_Bayes; cross-reference |
| Medium | `ch03:1124` (`eq:Pi-def`) | `Π(q*) := P(Q>q*|D)` defines Π as a *posterior exceedance probability*, while the companion formalism defines Π as an *empirical exceedance fraction* explicitly barred from "probability/posterior" language; the disclaimer "not a truth probability" (`ch03:1133`) sits on a quantity written as `P(·|D)` | Same symbol, two incompatible definitions across the paper and its formalism; internal-consistency and reviewer-confusion risk | Either present Π as the empirical exceedance curve (match the formalism) or state explicitly that the manuscript Π is a model-conditional posterior exceedance probability, distinct from the MIO diagnostic Π |
| Low–Med | `ch03:1106–1112`; `ch07:625` | Manuscript calls `Q` an "occupancy" with a "posterior mean" and gives `F` a "Monte Carlo posterior" — terms the companion formalism bars for the MIO `Q`/`F` diagnostics | Terminology collision between the physics narrative and the diagnostic formalism of the same program | Add one line distinguishing the dipole-premise physics filling-ratio interpretation from the MIO diagnostic `Q`/`F` (which carry no occupancy/posterior semantics), or harmonize wording |
| Low | `ch07:566–574` (`tab:fb7_lnB_11types`) | `NO_FLRW_LIMIT_EXPLICIT` rows still print `ln B` values down to `−1.9×10⁸` | Those are artifacts of forcing an FLRW comparison where no limit exists, not interpretable Bayes factors; spurious precision invites misreading | Replace the numeric entry for no-limit rows with "N/A (no FLRW limit)"; keep the status flag |
| Low | `ch07:666`, `ch07:684` | "detection window"/"detectable" for the growing-mode shear, while `ch07:672` uses "sensitivity window" | "Detection" wording for a forecast sensitivity band can read as a current detection | Use "sensitivity window" consistently |

## 5. Physics/Math Audit

| Item | Status | Issue | Required Fix |
|---|---|---|---|
| `x_C = Σ²−W²+Ω_tilt+Ω_{k,aniso}` as signed comparator coordinate | OK | Treated as signed; `x<0 ⇒ Q<0` (`ch03:1106`); not called an invariant magnitude | Optionally surface the cancellation caveat (`x_C≈0 ≠ isotropy`) at first use |
| MES bound hierarchy | OK | Derived from the covariant Boltzmann hierarchy (`ch04:14`, `ch04:338`), theorem tagged `[Conditional]` | None |
| Frame conventions (geometry/matter/peculiar, tilt rapidity β) | OK | Explicit and consistent (`ch03:1502+`, `ch03:1513`) | Add a one-line frame glossary cross-ref where `ln B_tilt` is first stated (rest-frame vs observer-frame, `ch07:526`) |
| FLRW / no-tilt / boost-only / tilt-only / zero-denominator / rank-deficient limits | OK | FLRW-limit phase-gate `|ln B|<0.1` for I/V/VII₀ (`ch07:551`); zero-denominator and rank-deficient → blocked states (`result_pack_B.md` rank/FPR scenarios) | Confirm the boost-only and tilt-only analytic limits are each stated once in ch03/ch04 prose |
| Deterministic transfer template vs anisotropic covariance | Partial | Transfer template `D₂(Σ²)` is external/proxy-calibrated (`transfer_sensitivity_report.md`); separation from anisotropic covariance is implied but not foregrounded | State once that the deterministic template effect and the anisotropic-covariance effect are modeled separately, with the transfer template flagged external/proxy |
| Neutrino anisotropic-stress feedback / shear growth | OK | Robustness checks report no spurious anisotropic-geometry preference (`ch08:78`, `ch08:875`) | None (rests on the corrected sign convention; keep the robustness cross-ref) |
| `N₂/F₂=28`, Thomson-suppression mechanism | OK | Physical mechanism stated (`ch09:500–513`, Prop. nu-dominance) | Tie the 98.4% to its transfer-conditional status (see §8) |

## 6. Statistics/Inference Audit

| Item | Status | Issue | Required Fix |
|---|---|---|---|
| Bianchi `ln B` tiering | OK | Consistently labeled legacy transfer-conditional / dipole-restatement (`ch07:646–653`, PDF pp.152–155) | None |
| Tilt-vs-shear decomposition | OK | Tilt ≈100%, shear `ln B=−0.87` (disfavoured), interaction ≈0 (PDF pp.158–159) | None — this is the correct honest result |
| Channel ablation / waterfall | OK | DIPOLE/NO-D2/FULL/CMB/D2+D3 waterfall; matter-dipole-alone `ln B≈+29`, Ferreira–Quartin penalty `−2.5` (PDF p.154) | None |
| Look-elsewhere / threshold registration | OK | `Π` requires registered thresholds + look-elsewhere/null metadata (`ch03:1145`) | Keep; ensure any selected threshold cites its registration |
| PPC / LOOCV / null competition / matched mask+covariance | OK (blocked, honestly) | Prerequisite gates largely `blocked_missing_covariance/null` and reported as such (`result_pack_B.md`, `result_pack_C.md`); no evidence claimed where blocked | Maintain; do not let the CF4++ `+44` (untraceable) imply a closed gate |
| `BF(F>0) > 5×10⁴` | OK | Disclaimed as dipole-restatement, not native evidence/geometry/family (`ch07:646–653`) | None |
| Observed-data figures as descriptive (Planck low-ℓ, DESI, CF4) | OK | `diagnostic_only`; manifests carry `matched_nulls_not_bound`, `full_covariance_not_bound`, etc.; residual bars explicitly not full-covariance/mask-coupled p-values | None |
| Bootstrap/jackknife intervals | OK | Long-run jackknife/bootstrap treated as diagnostics (`observed_longrun_analysis.md`; manifests `diagnostic_only`) | Verify no p-value/posterior phrasing in ch08 long-run prose |
| `Π` posterior-probability definition | See §4 | `eq:Pi-def` posterior vs formalism empirical exceedance | Reconcile (see §4) |
| CF4++ `ln B≈+44` provenance | Blocker-adjacent | Untraceable from canonical JSON (PDF p.158) | Reproduce or remove (see §4) |

## 7. Figure/Result Audit

Only figures/tables whose interpretation is wrong, under-supported, or overclaimed:

- **`tab:fb7_lnB_11types` (`ch07:566–574`).** Under-supported numeric entries for `NO_FLRW_LIMIT_EXPLICIT` rows (`ln B` to `−1.9×10⁸`); not interpretable Bayes factors. Mark "N/A (no FLRW limit)".
- **`fig_cf4pp_sensitivity` (`figures/conditioned_legacy/root__fig_cf4pp_sensitivity.manifest.json`, `exploratory`).** The figure itself is correctly tiered legacy/exploratory; the problem is the *prose* number it anchors (`ln B≈+44`) being untraceable (PDF p.158). Fix the prose, not the tier.
- No other current/observed figure overreaches: `fig_observed_planck_lowell_residual`, `fig_observed_cf4_velocity_density`, `fig_observed_planck_lensing_bandpowers`, `fig_observed_desi_footprint_depth` are `diagnostic_only` with correct `failed_gates` and descriptive captions.

(Acceptable: the conditioned-legacy evidence-bar/posterior-triangle gallery in App. H is consistently marked hypothesis-conditioned legacy and is not promoted to current evidence.)

## 8. Claim-Tier Corrections (exact wording to downgrade or remove)

- `ch09:497` — replace "the **discovery** that neutrinos contribute 98.4% of the total `D₂`" → "the legacy transfer path **indicates** that neutrinos account for ≈98% of the modelled `D₂`" (transfer-conditional; toy-oracle, not native solver).
- `ch09:513` — replace "`T₂ ≈ T_{2,ν}` to **98% accuracy**" → "`T₂ ≈ T_{2,ν}` in the modelled transfer, with a ≈1.6% photon correction (transfer-conditional)"; "98% accuracy" is not a measured accuracy.
- `ch08 §8.19` / PDF p.158 — for `ln B ≈ +44`: append "(currently untraceable to canonical inputs; pending a dedicated rerun)" or remove until reproduced.
- `ch03:1124` — either redefine `Π(q*)` as the empirical exceedance fraction (matching the formalism) or annotate: "`Π` here is a model-conditional posterior exceedance probability, distinct from the MIO diagnostic exceedance curve of the same symbol."
- `ch03:1112`, `ch07:625` — qualify "occupancy"/"posterior" for `Q`/`F` as the dipole-premise physics interpretation, distinct from the MIO `Q`/`F` diagnostics (which carry no occupancy/posterior semantics).
- Abstract/`ch01:152` — state the exact scenario and identity of the headline departure number (`F_Bayes` vs `Q̄` vs `FF`) so it matches `ch07`.

## 9. Additional Analyses Required (before stronger claims)

1. **Reproduce the CF4++ `ln B≈+44`** from canonical inputs with a bound hash, or drop it; no transfer-conditional headline should be untraceable.
2. **Reconcile the filling/occupancy numbers** (`F_Bayes`, `Q̄`, `FF`) into one provenance-traceable scenario table spanning intro→ch03→ch07.
3. **Matched-calibrated nulls + covariance** for the directional/depth (`G_F`) gates before any local/global (boost-vs-tilt) statement beyond "candidate"; the `gf_matched_null_forecast_report.json` path is the right vehicle — report it explicitly as a *forecast*, not a result.
4. **Foreground the deterministic-template vs anisotropic-covariance separation** with the transfer template flagged external/proxy at each use.
5. **Observer-frame marginalization (FB-8)**: state plainly that all current `ln B` are rest-frame and that observer-motion marginalization is pending; do not let rest-frame numbers read as observed-frame evidence.
6. **Π/Q/F harmonization** with the companion formalism (definitions and reserved-language), so the paper and its formalism use the symbols identically.

## 10. Claims That Are Safe

- `x_C` is the exact signed comparator projection of shear, vorticity, tilt, and anisotropic curvature; not an invariant magnitude or isotropy measure.
- The MES bound hierarchy is derived under stated assumptions and yields the conditional shear/vorticity/tilt ceilings.
- Under the dipole premise and a legacy external/proxy transfer path, the observed dipole is re-expressible as a single tilt-like (boost) degree of freedom; the transfer-conditional `ln B_tilt ≈ +25.3` is a restatement of the >5σ dipole significance, not independent evidence.
- Anisotropic shear *geometry* is mildly disfavoured (`ln B=−0.87`); the preference resides in the tilt channel.
- The budget-normalized departure is a few percent of the MES ceiling (state the exact scenario/quantity).
- Bianchi types I/V/VII₀ have an honest FLRW limit (`|ln B|<0.1`); other types are carried as explicit no-FLRW-limit or curved-reference rows.
- Observed-data figures (Planck low-ℓ residual, lensing bandpowers, DESI footprint, CF4 velocity/density) are descriptive diagnostics with matched-null/full-covariance gates unbound.
- MIO directional/depth/predictive-residual surfaces are diagnostic cross-checks, not HTT evidence or model rankings.
- No native low-ℓ Bianchi solver output exists; external/AniCLASS/legacy transfer is transfer-conditional; no Bianchi family is identified and no geometry is detected.

---

*Net change since prior rounds: the family-ID/geometry-detection claims and the native-evidence reading of `ln B` are removed and consistently tiered; MES is derived, frames explicit, observational figures correctly gated. Outstanding items are prose precision ("discovery", "98% accuracy"), one untraceable legacy number (CF4++ `+44`), cross-chapter numeric consistency (filling fraction), and `Π`/`Q`/`F` harmonization with the companion formalism. Verdict MINOR REVISIONS.*
