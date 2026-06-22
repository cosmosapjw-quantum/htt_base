# Old-Version Archive Survey (VER04 / IS-22, 2026-03-15)

_Survey date: 2026-06-22. Scope: full scan of `old_version/` (local reference
archive, gitignored). Purpose: document the prior-version research code and
report so future BASS development can mine its derivations, trace anchor
provenance, and avoid re-importing claims the current claim-firewall blocks._

## 0. TL;DR for future development

- `old_version/` is the **direct ancestor** of the current BASS stack: the prior
  "HTT — Hubble Tilt Tracker" package (version **IS-22 / VER04**, dated
  2026-03-15) by Jiwon Park, Soongsil OMEG.
- It is the **provenance source of the production anchors** in `CLAUDE.md §1`:
  `ln B(FLRW_tilt) = +26.40`, `β = 1.360×10⁻³`, `F_Bayes ≈ 0.093`,
  `Q ≈ 0.090`. The old version produced them as a *Bayesian evidence pipeline*.
- The old version framed these as **"decisive evidence … odds ~10¹¹:1 … for a
  non-zero tilt"** (conditional on the matter dipole being physical). The
  current claim-firewall (`scripts/pdf_claim_lint.py` FAIL_PATTERNS) was built
  to **block exactly this phrasing**. ⇒ Mine the *physics and derivations*;
  do **not** re-import the *claim language*.
- Reusable, not-fully-carried-forward material worth mining: the **Tsagas
  bridge** (λ_J^pec, Δq, ΔH), the **η_u̇ = 1/12** frame-attribution, the
  **multi-fluid** and **H₀ self-consistency** sections, the **DCP** and
  **pushforward** appendices, the **3D (β, l, b) catalog likelihood**, and the
  **P1–P11** prediction set.

## 1. Archive contents

| File | Size | What it is |
| --- | --- | --- |
| `old_version/HTT.zip` | 8.1 MB | Prior code+data package (`HTT/`), version IS-22 / VER04. 40 `.py`, 14 `.json`, 43 figure PDFs, 237 tests. |
| `old_version/bianchi_defect_overleaf.zip` | 8.1 MB | Prior manuscript LaTeX (Overleaf project): ch01–ch10 + appendices A–F + section additions. ~190 pp. |
| `old_version/main_FINAL.pdf` | 9.4 MB | Compiled prior report: _"Tetrad-based bounds on anisotropy in Bianchi cosmologies: From CMB multipoles to FLRW departure constraints,"_ Jiwon Park, 2026-03-14. |

Extraction: `unzip old_version/HTT.zip -d <dir>` / `unzip old_version/bianchi_defect_overleaf.zip -d <dir>`.

## 2. Identity and lineage

- Prior name **HTT (Hubble Tilt Tracker)** → current **BASS (Boltzmann And
  Spectrum Solver / Bianchi Anisotropy Solver)**.
- Same master defect identity, unchanged into the current version:
  `x = Σ²_std − W²_std + Ω_tilt + Ω_{k,aniso}` (signed comparator; non-negative
  only in the irrotational sector).
- Same MES extension: three-bound hierarchy `B_σ > B_ω > B_u̇`.
- The prior `htt/evidence_models_R03a.py` survives by name in the **current**
  transfer registry: `docs/generated/transfer_sensitivity_report.md` lists
  `htt.core.evidence_models_R03a:f2_tensor`, `:shear_to_D2`, etc. The current
  transfer-conditional callables are descendants of this module.

## 3. Prior headline claims → current status (anchor provenance map)

The old report's abstract/results stated the following. The right column is the
**current** disposition under the BASS claim-firewall — this is the most
important table for avoiding regressions.

| Quantity | Old value | Old framing | Current BASS status |
| --- | --- | --- | --- |
| `ln B(FLRW_tilt)` | **+26.4** (odds ~10¹¹:1) | "decisive evidence for non-zero tilt over FLRW," conditional on dipole physical | **Blocked headline.** Transfer-conditional / premise-conditioned amplitude fit only; amplitude-matched contamination null FPR = 0.95 blocks source-ID; "decisive evidence"/"odds exceeding"/"conditional evidence for global tilt" are now forbidden lint patterns. |
| Evidence decomposition | shear **−0.86**, tilt **+26.40**, interaction −0.04, total **+25.50** (additive to 0.00) | "103% of signal from tilt, not geometry" | Kept as a *diagnostic* decomposition; not an evidence claim. |
| Tilt rapidity `β` | **(1.36 ± 0.18)×10⁻³** | "5–6 models converge; 2% agreement with CF4" | Carried as the `β = 1.360×10⁻³` anchor; directional/source claim blocked. |
| Occupancy `Q` | **0.090 ± 0.002** | "9% of MES algebraic ceiling" | Diagnostic-only scalar; does not classify geometry. |
| Filling `F` | **≈ 6.3%** | "occupied anisotropy budget" | `F_Bayes ≈ 0.093` anchor; diagnostic-only. |
| Bianchi V | `ln B` **−24.5** | "excluded by momentum-constraint quadrupole overproduction" | Family-level selection blocked pre native morphology atlas. |
| Null FPR | **0/100** (SS), **0/20** (catalog) | "pipeline calibration, zero false positives" | Superseded by amplitude-matched contamination null (FPR 0.95) which *fails* — the key scientific update. |
| FLRW null recovery | **4.38×10⁻¹¹** | numerical FLRW limit | Analogue of the current D₂ FLRW-limit regression discipline. |
| `η_u̇` | **1/12 ≈ 8.3%** | acceleration contribution to CMB dipole (frame attribution) | Reference derivation; not a current headline. |
| Tsagas `λ_J^pec` | **≈ 300 Mpc** | scale below which tilted observers see apparent acceleration | Reference derivation (not in current honest envelope). |
| Scale-dependent `H₀` | **~4%** at SH0ES depth | three-term deceleration decomposition (tilt vs age-bias) | Reference derivation. |
| CatWISE significance | **3.3–3.6σ** (2025 reassessment); multi-survey ≥5σ | dipole-anomaly input | Input provenance; the "physical" premise is exactly what the current contamination null does not grant. |
| Predictions | **P1–P11** (2027–2037: Euclid, Rubin, SKA) | testable programme | Reference roadmap. |

## 4. Prior code capabilities (`HTT/htt/`, 12 core modules)

A lean, fully self-contained Bayesian evidence pipeline (7,663 Python lines,
237 tests). Module → role → current successor:

| Old module (MANIFEST name) | Lines | Role | Current successor area |
| --- | ---: | --- | --- |
| `ssot.py` | 112 | constants, conversions, SSOT namespace | `htt/src/common` + `htt.core.ssot` |
| `bounds.py` | 277 | MES hierarchy, defect variables, algebraic bounds | `htt/htt` observational bounds; `htt/bass` closure |
| `evidence_models_R03a.py` | 808 | **16 Bianchi model classes, 7-channel likelihood, MODEL_AUDIT** | `htt.core.evidence_models_R03a` (still referenced by the transfer registry) |
| `teff_extended.py` | 473 | nonlinear `T_eff`: moment map, ℓ-mixing, ODE, defect propagation | `htt/bass` T_eff / current ch05 material |
| `analysis_extended.py` | 456 | filling fraction, scenarios, summary tables | `htt/htt` statistics, result packs |
| `departure_posteriors.py` | 420 | three-layer inference x → Q → Π, derived `v_tilt`, `q0` | `htt/htt/departure`, `htt/mio` reports |
| `catalog_velocity_likelihood.py` | 350 | 3D (β, l, b) distance-modulus catalog likelihood + directional posterior | `htt/htt` catalog; CF4 drivers |
| `tilted_flrw.py` | 363 | tilted-FLRW kinematics: King–Ellis boost, Tsagas bridge, `η_u̇` | `htt/bass` tilt/background |
| `H0_sensitivity_analysis.py` | 280 | scale-dependent H₀ correction, age-bias decomposition | (not fully carried forward — mine for new work) |
| `run_all.py` (`pipeline.py`) | 520 | **10-phase orchestrator**: bounds → evidence → departure → robustness → catalog → null → figures | BASS has no single monolithic orchestrator; closest is the script drivers |
| `analysis`/`plot_style.py` | 143 | Wong (2011) palette, shared conventions | `figures/` style |

**Observational inputs shipped** (`HTT/data/*.json`): `obs_defaults.json`
(Planck, CF4, CatWISE, Saadeh), `obs_defaults_tilted.json`,
`obs_age_bias_pipeline.json` + `obs_son2025_age_bias.json` (Son et al. 2025
age-bias), `obs_deceleration_compilation.json` (20+ q₀ measurements). These
document the canonical observational numbers behind the anchors.

**Outputs shipped** (`HTT/outputs/*.json`): `VER04_integrated_results.json`
(master: 16-model evidence + departure posteriors + robustness + identifiability
audit), `robustness_sweeps_integrated.json` (5 sweeps: ρ, σ_sys, prior,
channels, comparator), `null_test_integrated.json` (100 SS + 20 catalog),
`ppc_results.json`, `IS07_cross_pipeline.json` (Hellinger H = 0.10).

## 5. Prior manuscript structure (mine for derivations)

`main.tex` → ch01 intro · ch02 framework (+ sec7 tilted kinematics, sec8
multi-fluid) · ch03 Bianchi bounds · ch04 dipole · ch05 T_eff · ch06 pipeline ·
ch07 results · ch07b robustness · ch08 discussion (+ sec83 Tsagas expanded, H₀
self-consistency) · ch09 future (tilted predictions P1–P11) · ch10 conclusion.
Appendices: **A** proofs (incl. the x-sign proposition with the BIX signed
counterexample) · **B** code · **C** DCP derivations · **D** evidence technical ·
**E** catalog likelihood · **F** pushforward.

Derivation content that is **distinctive vs the current manuscript** and worth
re-using for new analytic work (e.g. extending the NT-/registry theorem set):
the Tsagas bridge (λ_J^pec, Δq, ΔH, scale-dependent corrections), the
`η_u̇ = 1/12` frame-attribution, the multi-fluid extension, the H₀
self-consistency / age-bias three-term decomposition, the DCP derivations
(appendix C), and the pushforward formalism (appendix F).

## 6. Prior self-audit trail (reusable QA artefacts)

`HTT/docs/` contains the prior version's own adversarial-review record:
`IS22_hostile_review.md` (four-agent: FLRW advocate / post-FLRW advocate /
statistician / observational cosmologist), `IS_final_math_audit.md`,
`IS_math_audit_verification.md`, `IS_overall_audit_verification.md`,
`code_data_audit_report.md`.

Notable: the prior reviews **already flagged the framing problems the current
firewall now enforces** —
- the "three non-negative terms" presentation of x before the `−W²` term
  (P1, ch01) — the x-must-be-signed discipline;
- a residual "model-independent at the algebraic level" overclaim (P1, ch01)
  contradicting the perfect-fluid `w > −1` assumption.

The code/data audit verdict was **"DEFENSIBLE — no computational errors affect
any manuscript claim,"** reproducing every stated number (evidence decomposition
additive to 0.00 nats; FLRW null 4.38×10⁻¹¹; the eps2/eps3 discrepancy bounded
to <0.06% because the dipole channel carries 99.4% of the shear bound). ⇒ The
old numbers are **arithmetically trustworthy**; what changed is the **inferential
license** to call them evidence.

## 7. Old → current scientific progression (one paragraph)

The old version *asserted* a tilt detection (`ln B ≈ +26.4`) conditional on the
matter dipole being physical, with a clean null calibration (0 false positives).
The current BASS version *tests that premise harder* — an amplitude-matched
contamination null returns FPR ≈ 0.95, and there is still no native low-ℓ
morphology atlas — so it **blocks** the source-ID / family / geometry headline
and keeps the same physics numbers only as **transfer-conditional, diagnostic**
quantities. The codebase grew from ~40 Python files (evidence pipeline) to
~1000 Python files plus a Rust `bass_rs` MB-95 solver and a PSTF/tetrad-native
hierarchy, i.e. from *fitting an evidence model* to *building the native
solver* that the old claims would need in order to be promoted.

## 8. How to use this archive going forward

- **Cite provenance**: when the current report uses `26.40 / β / Q / F`, the
  numbers originate in VER04; cite the archive, not a new computation.
- **Mine derivations**: Tsagas, η_u̇, multi-fluid, H₀ self-consistency, DCP,
  pushforward, and the catalog 3D(β,l,b) likelihood are reference-grade analytic
  material for new theorems/diagnostics.
- **Do not regress the claim language**: "decisive evidence", "odds exceeding",
  "conditional evidence for global tilt", "data support a tilt-like degree of
  freedom" are forbidden by `pdf_claim_lint`; they come from this old abstract.
- **Transfer lineage**: `evidence_models_R03a` is the ancestor of the current
  transfer-registry callables — start here when extending transfer paths.
- **Reuse observational SSoT**: `HTT/data/obs_defaults*.json` document the
  canonical Planck/CF4/CatWISE/Saadeh/Son2025 inputs.

## 9. Archive handling

`old_version/` is a **local reference archive** and is gitignored (25 MB of
zips + PDF), consistent with keeping large binary references out of git. This
survey doc is the committed, in-repo record of its contents.
