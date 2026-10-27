# HTT observable-bridge research run — outcome report

Date: 2026-10-26 (KST). Target: `htt_base` @ `a55036ad` (branch `research/htt-adaptive-methods-20261023`), `docs/research_program/observational_publication_20261015/PUBLICATION_ACCELERATION_20261025/` (seven companion manuscripts, two frontiers, 29 residual HOLDs in `POST_PUBLICATION_CHECKPOINT_20261026`). Harness: `physmath-research-harness` deep cycle (evidence acquisition → claim audit → hypothesis space → independent adversarial review → physics/math validation → verification design → independent decision gate → closeout). State files: `state/`; validation script and raw output: `validation/`; reviews: `review/`.

This report distinguishes FACT (read in a primary source or computed here and reproducible), INFERENCE (our reasoning), and HYPOTHESIS (proposal to test). Nothing here changes any original-42 acceptance or any HOLD; no catalogue or map was re-fitted.

---

## 1. Bottom line

1. The HTT local optical law is exactly the O(z) term of covariant cosmography (FACT, T-01): H_u(n) = H − A·n/c + σ:nn ≡ Heinesen's 𝔥(e) = θ/3 − e·a + ee·σ, and f_μ = −κ log(1+q) is its magnitude form. So the HTT quotient tensor S = σ/H and the published "Hubble quadrupole" H_2/H_0 (Kalbouneh et al. 2026; Cowell et al. 2023) are the same object class. The familiar observable already exists; what HTT lacks is not an observable but a *covariance and a null*.
2. The single shared prerequisite for every physical statement in lanes H/K/V (HOLDs H02, H04–H06, K04, V04–V06) is a mock-derived, correlated peculiar-velocity covariance replacing the diagonal 250 km/s working metric. Until then T = 23.40 (6 df), the conditional tail 6.7e−4, η_95 = 1.289 and the significance of ‖Ŝ_app‖_F = 0.0327 are undefined as physics (INFERENCE, confirmed by the adversarial review as the strongest counter-argument).
3. Executed with zero new data (T-11): the saved H03 tomography gives per-window apparent shear amplitudes ‖Q_w‖_F/H_w = 0.027, 0.041, 0.049, 0.020 at z_c = 0.025, 0.040, 0.060, 0.080, near-pure-shear eigenstructure (middle eigenvalue ≈ 0), dipole aligned with the positive quadrupole eigen-axis (6°–27°), and axes within 16°–25° of Kalbouneh's (l,b) = (299°, 5°). A linear-ΛCDM toy (T-05b, INFERENCE) predicts 0.030, 0.017, 0.011, 0.008 for those shells: inner window consistent, middle windows 2–4× above the linear rms. This is the concrete, familiar-observable face of the HTT morphology machinery — and it is exactly the kind of statement that must wait for mocks.
4. The Bianchi lane (B02–B05, R23-ATLAS) has a public producer: AniLoS/AniCLASS (Vicente, Pereira, Pitrou 2025/26; GPL-3) outputs all-m T, E, B a_ℓm for nearly-isotropic VII_h and IX (V, VII_0 as limits), vector and tensor regular modes (FACT, code inspected). It can supply the *payload* B02 asks for only as an externally produced, pre-registered, convention-audited atlas; the conventions that matter (amplitude per unit IC, single-m frame, handedness, regular vs irregular, coupled vs decoupled) are left to the user (FACT, source lines cited in `review/ADVERSARIAL_REVIEW.md`).
5. Two lanes close negatively and should be written up as such (saves effort): astrometric proper motions cannot bound the CF4-scale S in any regime (N-001); second-order cosmography 𝔮_1 is not the H03 depth law (N-002); the HTT dipole d = −A/(cH) has no ΛCDM referent for geodesic dust — the observed dipole is observer boost + bulk flow (N-003).
6. For L03–L06, PR4/NPIPE (600 end-to-end sims, A/B splits, Sevem T+P) is the obtainable release-matched null lane, at the cost of redefining L03 (PR3 → PR4) and re-deriving the L01 SMICA results; the shared-sky-per-index property (M-01) must be quoted from NPIPE documentation before use.

---

## 2. Bridge table: HTT object → standard observable → what separates them

| HTT object (repo) | Standard observable / literature estimator | Bridge status | What is missing |
|---|---|---|---|
| Local law H_u(n), magnitude field f_μ = −κ log(1+q) (R32-01, R32-05) | Covariant cosmography 𝔥(e), 𝔔(e) (Heinesen 2021 eqs 3.7, 4.1–4.3); η = log10(z/d_L) field (Kalbouneh 2026 eq. 3.1) | Identity at O(z) (T-01, PASS) | O(z²) terms (25 d.o.f.) and the observer-boost d.o.f. (Heinesen §5) are not in the HTT law |
| CF4 quotient tensor Ŝ_app (‖·‖_F = 0.0327; eigen ±2.3 %) | Hubble quadrupole H_2/H_0 = (2.8 ± 0.4) % CF4; TF 2.3 ± 0.7, FP 2.6 ± 0.9; Pantheon+ 0.0 ± 1.3 (Kalbouneh 2026 Table 4); Pantheon+ λ_1 = 0.021 ± 0.011, 2.88 % limit (Cowell 2023) | Same object class; magnitudes agree (T-03: 0.032–0.045 vs 0.0327) | Estimator equivalence (windows, nuisance projection, basis sign); correlated PV covariance; mock percentile; independent reconstruction eigenframe (0.02 < z < 0.06 only) |
| H03 window dipoles D_w, T = 23.40/6 df | Hubble dipole / zero-point dipole (Boubel 2025: 0.063 ± 0.016 mag; Stiskalek 2025: 0.087 ± 0.019 mag CF4, 0.049 ± 0.013 Pantheon+); observer velocity v_o = 188 ± 22 km/s and bulk 520 ± 91 km/s (Kalbouneh 2026) | Same observable; HTT's "constant rate dipole" + "bulk response" design is a special case | The physical null (boost + radius-dependent bulk, 1/z) with mock covariance (H-0) is absent; the dipole is NOT the acceleration −A/(cH) for dust (N-003) |
| P1 15-coefficient selected likelihood (274 rows, F(15,259) region) | Forward-model zero-point + distance-marginalised + PV-reconstruction fits (Stiskalek 2025); differential zero-point fits (Boubel 2025) | Same statistical family (GLS on magnitudes with zero-point nuisance) | Empirical parent-selection law; PV cross-law from a reconstruction or mocks; CF4 covariance (none released) |
| Low-ℓ STF morphology, chirality/contraction geometry (R32-01 Thm 1–2) | Planck low-ℓ anomaly statistics ranked on end-to-end sims (Planck 2018 VII; PR4 practice in Gimeno-Amo 2023) | Methodology import possible | Release-matched sims with fixed selection protocol (PR4 lane H-4; M-01) |
| Bounded foreground-moment identified set S_ρ(Y) (R32-04/09) | Moment-expansion component separation (Chluba 2017; Remazeilles 2021; Vacher 2022) | Construction matches the literature framework | A dimensional ρ from ℓ ≤ 5 foreground amplitudes and β/T dispersions (M-02); remainder control |
| LRS Bianchi V images, Bianchi I history degeneracy (R32-07) | Bianchi VII_h/V/VII_0/IX T+E+B transfer (Pontzen–Challinor 2007; Saadeh 2016 limits; AniLoS/AniCLASS) | Producer exists; conventions unfixed | Pre-registered external atlas with manifest; independent cross-check (BASS) with polarization; regular/irregular identity of fixtures |
| Finite optical inverse, error-radius frontier r_Q < 0.0327 (R32-05) | Not a standard observable; it is a propagation statement | Needs the same PV covariance | A qualified error radius = mock-derived covariance of Ŝ_app under the exact estimator |
| "Nonradial response" for σ, ω, A (K03/K05) | Quasar proper-motion VSH E2/E1/B1 (Darling 2014; Marcori 2018; Gaia DR3 Quaia fits) | Law exists (T-04 PASS) | No sensitivity to CF4-scale S; global S excluded at 1e−10 by CMB → close K03 with a no-sensitivity statement (N-001) |

---

## 3. Evidence base (summary; full ledger in `state/EVIDENCE_LEDGER.md`)

Primary sources read this run (20): Heinesen 2021 (arXiv:2010.06534) full equations; Kalbouneh et al. 2026 (arXiv:2510.02510) §3–6, Tables 3–4; Cowell et al. 2023 (2212.13569); Dhawan et al. 2023 (2205.12692); Boubel et al. 2025 (2412.14607); Stiskalek et al. 2025 (2509.14997); Salzano et al. 2025 (2512.02526); Duangchan et al. 2026 (A&A 708, A119); Saadeh et al. 2016 (1605.07178); Pontzen & Challinor 2007 (0706.2075); Vicente, Pereira, Pitrou 2025 (2506.07786) + AniLoS source; Darling 2014 (1404.3735); Darling et al. 2018 (1807.06670); Marcori et al. 2018 (1805.12121); Gaia DR3/Quaia VSH (2412.08605); Gaia-CRF3 (2204.12574); Tully et al. 2023 CF4 (2209.11238); Brout et al. 2022 (2112.03864); Planck 2020 LVII NPIPE (2007.04997) + Carron et al. 2022 (2206.07773); Gimeno-Amo et al. 2023 (2306.14880); Vacher et al. 2022 (2203.07246). Internal: seven manuscripts, two frontiers, PUBLICATION_DAG (42 nodes), data registry, R26 review, TEFF bridge (three extraction subagents).

Claim audit (`state/CLAIM_AUDIT.md`): 16 claims; demoted to hypothesis/inference: "running AniLoS satisfies B02" (UNSUPPORTED), "vorticity observable only vs a dynamical frame" (INFERENCE_ONLY), "few-percent ΛCDM quadrupole" (own toy estimate), "global zero-point shift is harmless to ℓ ≥ 1" (elementary inference). Conflicts kept, not resolved: Boubel vs Stiskalek (PV treatment); Kalbouneh vs Salzano (PV correction); CF4 0.147 vs 0.138 mag zero point; Gaia vs VLBI ℓ = 2 power.

Data availability (from the repo registry, E-I09): cached — Gaia DR3 CRF3 astrometry (1,614,173 rows, per-source covariances), Quaia-matched PMs (755,850), VLBA 713 PMs, Pantheon+SH0ES.dat + STAT+SYS covariance, CF4 tables (local recovery), PR3 masks/SMICA weights/HFI beams, FFP10 SMICA split noise ×4, PR4 npipe6v20 030 A/B (scoped), PR4 LoLLiPoP, SDSS PV mocks (10.6 GB, 2048 files), CF4 grouped velocity cube; absent/on-request — nominal Pantheon+ SALT2 surface/.nml/FITRES, CF4TF and combined mocks, Wang 2026 data, ANICOSMO code, Planck 2015 XVIII polarized VIIh templates.

---

## 4. Validation results (`state/VALIDATION.md`, `validation/results.json`)

- T-01 PASS: HTT law ≡ Heinesen 𝔥; f_μ = −κ log(1+q).
- T-02 PASS: R32-01 Table I reproduced independently to ≤ 1e−6 (five rows; remainders within E_2, E_3 bounds); chirality witness attains 4√2/135 exactly. Tooling note: midpoint-θ quadrature produces O(1e−6) errors that mimic bound violations; use Gauss–Legendre.
- T-03 PASS/CONCERN: normalization bridge η̃_2 = s/ln10, ‖S‖_F = s√(3/2) → Kalbouneh's shells give ‖S‖_F-equivalent 0.041, 0.032, 0.045, 0.033; HTT 0.0327; directional rms 0.0119246 reproduced. H_2 normalization in refs [44, 45] still unverified (M-07 partly closed).
- T-04 PASS: proper-motion E2 response rms H‖S‖_F/√5 = 0.22 μas/yr (peak 0.35) for Ŝ_app — but see N-001 for why this does not yield a bound.
- T-05 (toy, INFERENCE): linear-ΛCDM rms ‖σ/H‖_F at the observer: 0.028 at R = 100 h⁻¹ Mpc (0.067 at 50, 0.0076 at 240); shell-averaged apparent quadrupole for the CF4 windows: 0.030, 0.017, 0.011, 0.0079.
- T-06 PASS: Heinesen monopole → FLRW q. T-07 PASS: R32-07 ratio 9/5.
- T-08 static PASS: AniLoS API and model coverage (execution blocked in this session).
- T-11 (executed V-1 step 8): per-window table (Section 1, item 3); FP-deletion sensitivity in the repo changes the STF block by 0.02–0.036 in ‖S‖ units — the size of the signal.

---

## 5. Hypotheses, review roles and decision gate

| ID | Bridge hypothesis | Adversarial role | Decision gate |
|---|---|---|---|
| H-0 | Physical ΛCDM null for the window dipoles: observer boost + radius-dependent bulk flow (1/z_w) under a mock-derived correlated covariance (added after review) | — (reopened) | PROMOTE → package V-0; step (a) executed (T-12), step (b) pending |
| H-1 | PV-shear bridge: Ŝ_app and T_w are the window-weighted ΛCDM tidal shear (quadrupole half); dipole half withdrawn (N-003) | TRADEOFF | REOPEN_HYPOTHESIS → restate as H-1Q (quadrupole only); V-1 step 9 unchanged |
| H-2 | External polarized Bianchi atlas via AniLoS/AniCLASS with pre-registered manifest and independent cross-check | TRADEOFF | PROMOTE (manifest before any run; Pontzen–Challinor C_ℓ/EE-BB/TB-EB as primary check; BASS optional) |
| H-3 | Astrometric nonradial law bounds S | INFORMATIVE_FAILURE | REJECT as a package; keep the literature law for K03; V-4 withdrawn |
| H-4 | PR4/NPIPE release-matched null lane for L03–L06 | DEFENDED (conditional) | REOPEN_EVIDENCE (M-01); on confirmation PROMOTE as an explicit L03-redefinition proposal |
| H-5 | Bounded foreground-moment class with physical ρ | NEEDS_MORE_EVIDENCE | REOPEN_EVIDENCE (dimensional ρ incl. ℓ ≤ 5 amplitude + remainder check) |
| H-7 | Second-order cosmography 𝔮_1 as the depth law | INFORMATIVE_FAILURE | REJECT standalone; 𝔮_1 column kept inside V-0; V-3 withdrawn |

Full review: `review/ADVERSARIAL_REVIEW.md`. Gate text: `review/DECISION_GATE.md`. Decision log: `state/DECISION_LOG.md`.

Key review corrections absorbed (FACT unless marked): (i) Heinesen's O(z) dipole is −e·a with a the emitter 4-acceleration, which vanishes for geodesic dust — the HTT dipole d = −A/(cH) has no ΛCDM referent; the observed Hubble dipole is observer boost + shell bulk flow with 1/z scaling (Heinesen §5; Kalbouneh 2026 confirms the 1/z scaling and does not fit H_1). (ii) The H03/P1/R32-05 covariance is a diagonal 250 km/s working metric; a coherent ΛCDM bulk flow produces correlated window dipoles that it does not contain, so T = 23.4 may be a covariance artefact. (iii) AniLoS outputs are transfer functions per unit initial amplitude (`betaur0[0] = 1`, `Phi_i_0 = -1`), single-m in the Bianchi frame, i^ℓ phase, fixed handedness, regular modes only (Saadeh's tightest VII_h bound is on T_irr), V as a sqrth ≈ 1e5 limit, IX at ℓ_max = 3. (iv) Quasars at Gpc do not share a window-scale shear; a global shear is excluded at 1e−10 — the astrometric lane has no constraining power on S. (v) CF4 is shared by H-1, H-7, Kalbouneh, Boubel, Stiskalek: only Pantheon+ (quadrupole 0.0 ± 1.3 %) and mocks are independent.

Executed V-0(a) (T-12, conditional on the inherited covariance): no ΛCDM dipole law fits the 12 saved window dipoles — bulk R_w b: T = 79.99 (9 df); constant: 94.60; bulk + constant: 23.40 (6 df, τ = 12.59); pure 1/z_w + constant: 39.46; bulk + z_w 𝔮_1: 22.67; all three: 15.32 (3 df, τ = 7.81). Fitted bulk 295 ± 18 km/s toward (l,b) = (287°, −5°) (Kalbouneh: 520 ± 91 km/s toward (299°, 5°)); boost and bulk columns collinear at O(z) (principal angles 5–9°). Reading: the residual is either under-estimated correlated errors, window-dependent composition/systematics (R32-03's FP-fraction design), or physics — only the mock-derived covariance (V-0(b)) separates these.

---

## 6. Requirements per residual HOLD (data + theory)

Legend: DATA = obtainable product; THEORY = established result to import; REDEFINE = the HOLD as written cannot be met and should be re-contracted; PROC = procedural/irreversible; — = not addressed here.

| HOLD | Needs (data) | Needs (theory) | Class |
|---|---|---|---|
| B02 numeric all-m polarized T/E/B atlas | External AniLoS/AniCLASS run (VII_h grid, VII_0, V-limit, IX ℓ ≤ 3), manifest with IC/history/frame/units; cached BIANCHI v1.1 fixture provenance (regular/irregular) | Pontzen–Challinor 2007 polarization transfer; Saadeh 2016 mode taxonomy (S/V/T_reg/T_irr); AniLoS convention map (amplitude per unit IC → (σ/H)_0 via nteb at η_0; handedness; Euler convention) | DATA + THEORY (regular modes only; T_irr not covered → partial) |
| B03 atlas × release-matched processing | H-4 lane products (PR4 Sevem/Commander maps, masks, beams, 600 sims) | none beyond B02 | DATA (after B02, H-4) |
| B04 family response, injection ensemble, Bayes evidence | B03 + injection pipeline | Saadeh 2016 priors/likelihood structure as comparator | DATA (after B03) |
| B05 calibrated identification with Planck likelihood | Planck low-ℓ T+P likelihood (public) | — | DATA (after B04) |
| H02 parent selection, calibration ancestry, PV cross-law, source nulls | CF4-selection mocks (64, Duangchan 2026 — on request) or SDSS PV mocks (cached) run through the exact estimator; independent reconstruction (2M++/BORG) for z ≲ 0.06; CF4 method-footprint maps | Linear-theory PV covariance (T-05 formulas); forward model of Stiskalek 2025 type | DATA + THEORY |
| H04 false-positive/PPC calibration, physical response | H02 outputs; Pantheon+ as independent dataset | Heinesen §5 boost law (1/z) replacing the "constant rate dipole" as the physical null (H-0) | THEORY first, then DATA |
| H05 source-matched covariance/window/calibration comparison | same mocks; Kalbouneh/Cowell estimator re-implementation on CF4 | normalization map of H_2 (refs [44, 45]) | DATA |
| H06 full law + competing models + independent validation | Pantheon+ (null 0.0 ± 1.3) as the independent check | — | DATA (after H04/H05) |
| K03 nonradial law, Gaia cross-source covariance, ω response | none needed | Darling 2014 / Marcori 2018 law + explicit no-sensitivity statement (N-001) | REDEFINE (close as "law exists, no constraining power") |
| K04 physical radial law + common-frame transfer | H04 + mock covariance | geodesic-dust statement A = 0 (N-003); boost composition (Maartens 2024) | THEORY + DATA |
| K05 matched source clock / observer frame / shared-sky cross-law | — | redshift already contains dτ_s/dτ_o (repo note); boost law | THEORY (partly REDEFINE) |
| K06 joint identified combinations + error budget | after K04 | — | DATA (after K04) |
| L03 PR3 same-realization FULL/HM/OE genealogy | NPIPE 600 sims + A/B (NERSC); documentation quote for shared sky (M-01) | — | REDEFINE (PR3 unobtainable; PR4 substitute) |
| L04 finite-MC rarity + look-elsewhere | H-4 pilot (50 sims) then 600 | predeclared selection protocol | DATA (after L03') |
| L05 no independent-sky multiplication | — | A/B differences as noise nulls only | THEORY |
| L06 qualified sims + novelty over Planck VII | after L04/L05 | — | DATA |
| R23-ATLAS | as B02 | as B02 | DATA + THEORY |
| R23-CONGRUENCE | mock covariance; Pantheon+ released parameters | Heinesen §5 boost; redshift/clock double-count note | THEORY + DATA |
| R23-SN nominal PS1.nml / SALT2 surface / FITRES parity | not public (Brout 2022 names "B21" only) | — | REDEFINE (use released Pantheon+ parameters and covariance as the data object, as all published anisotropy analyses do) or author request |
| R25-DISTANCE-CONDITIONAL-EVIDENCE | — | — | PROC |
| R25-GAIA-RELEASE-TAG-ASSOCIATION | — | — | PROC |
| R25-PR3-FREQUENCY-TENSOR-CROSSPREDICTION | — | — | PROC |
| R25-PR3-STAGED4-TENSOR-CONTRAST | — | — | PROC |
| R26-CF4-FINAL-GROUP-CALIBRATION-RESPONSE (0.147 vs 0.138) | EDD/CF4 documentation or author query (M-06) | constant per-method offsets are projected out by the nuisance columns; position-dependent offsets are not (H-1n) | DATA (provenance) + THEORY (harmless to ℓ ≥ 1 if constant) |
| R26-FULL7-STREAMED-SPIN2-QUADRATURE | — | — | PROC |
| R26-SMICA-EXACT-PR3-IMPLICIT-ROW-PROJECTION | — | — | PROC |
| V04 no identification from a normalised null column | mock covariance; two physically distinct transfer kernels | boost vs history degeneracy (R32-06) | THEORY + DATA |
| V05 calibrated null/prior/injection | after V04 | — | DATA |
| V06 real-data significance | after V05 | — | DATA |

---

## 7. Follow-up research programme (ordered; from the decision gate, with status)

1. **V-0(a) — done (T-12).** Refit of the 12 saved dipole coordinates with {constant, 1/z_w boost/bulk, z_w 𝔮_1}: no design reaches τ under the inherited covariance; bulk 295 ± 18 km/s toward (287°, −5°). Pre-registered pass for V-0 stays: T_min ≤ τ AND v_o within 2σ of 188 ± 22 km/s AND bulk compatible with 520 ± 91 km/s — under the mock covariance of step (b).
2. **Ledger/audit repair (hours, literature only).** Quote the boost-dipole law (Heinesen §5 eqs 5.1–5.7; read Maartens et al. 2024 in full); extract the H_2 normalization from Kalbouneh's refs [44, 45] (M-07) → add C-OPT-06 (boost law, 1/z_w term plus O(z⁰) aberration term) and C-H03-02 (T-11 window results, conditional) to the claim audit.
3. **V-5 (M-01) — hours plus a small download.** Quote the NPIPE §5 / NERSC README statement on whether A/B/full simulations of one index share the CMB and foreground input sky; then compute |C_ℓ^{(A−B)×full}| at ℓ ≤ 5 on 2–3 Nside-16 triplets (npipe6v20 030 mc_00200 A/B partly cached). Pass < 1 %, kill ≥ 10 %. Outcome feeds a written L03-redefinition proposal (owner decision).
4. **V-6 (amended) — hours to a day.** Dimensional ρ = (ℓ ≤ 5 dust/synchrotron amplitude in the mask) × Var(β), Var(T) × ln²(ν/ν₀) in the metric M (Planck 2018 XI, Planck Int. XXII; Commander/GNILC amplitudes) → identified-set radius √(ρ² − J_0)/ℓ_M vs the 0.379 μK held-out-B norm; one PySM d1/s1 remainder pass through the 7-channel design. Informative failure is a live outcome.
5. **Restate H-1 as H-1Q (hours).** Quadrupole only; C-OPT-04 as "same object class"; H-1n (method × footprint) as co-equal competitor; T-11 table as the baseline; dipole content moved to H-0.
6. **V-2 manifest and smoke run (owner's machine; a day).** Pre-register: amplitude convention (β_init → (σ/H)_0 via `nteb_tensor` at η_0), T_CMB factor, Euler convention for the Bianchi → Galactic rotation, i^ℓ phase, handedness parity map (flips B and the TB/EB sign), coupled (CLASS Ω_K) vs decoupled background, regular/irregular mode identity, IC ('iso'/'oct'); establish the regular/irregular and coupled/decoupled identity of the cached BIANCHI v1.1 fixture from provenance; then run `Anilos({'sqrth':0.1,'Omega_K':1e-6}).tensor_solver(); alm_tensor(10)` (and `vector_solver`) and validate convention-light observables (C_ℓ^{TT,EE,BB} shapes, EE/BB ratio, TB/EB sign) against Pontzen–Challinor 2007; BASS cross-check only if it emits polarized VII_h Einstein–Boltzmann output. Deliverable: an external, manifested atlas proposal for B02/R23-ATLAS (regular VII_h/IX subset; T_irr, Bianchi I, scalars explicitly out of scope).
7. **V-0(b) / V-1 step 9 — days plus data request; decisive for H-0 vs H-1Q vs H-1n.** Run mocks through the exact H03 and R32-05 operators (same 35,970 group positions, 19 nuisance columns, D metric, four Gaussian windows): SDSS PV mocks now (footprint caveat), request the 64 CF4-selection mocks (Duangchan et al. 2026) and the CF4TF/combined mocks; derive the correlated covariance of (H_w, D_w, Q_w) and the null distribution of ‖Q_w‖_F and of T; then compare eigenframes with a CF4-independent reconstruction (2M++/BORG-type; z ≲ 0.06) and with the survey footprint (method splits). Pass/kill as in V-1 (mock 95 % envelope; alignment < 30° in the inner two windows).
8. **K03 closure note (hours).** Record the literature nonradial law (Darling 2014; Marcori et al. 2018), the no-sensitivity statement for window-scale and global S (T-04 vs Gaia/VLBI systematics; CMB 1e−10), and one paragraph on vorticity being unobservable against a quasar-tied frame; withdraw V-4; do not spend the cached CRF3 sample on an S bound.

Owner decisions flagged by the gate (not research actions): (a) whether to redefine L03 from PR3 FULL/HM/OE to the PR4 lane (cost: re-derive L01 SMICA results; p-floor 1/600); (b) whether to redefine H04/V04/R23-SN to use the released Pantheon+ light-curve parameters and covariance as the data object instead of the unobtainable nominal SALT2 binding (or to request the files from the authors).

---

## 8. Theoretical foundations to build or import

1. Correlated PV covariance for magnitude/velocity tensors: linear-theory kernels (T-05 formulas) → mock-calibrated covariance of (H_w, D_w, Q_w) under the exact HTT estimator. This is a methods result in its own right and the prerequisite for every H/K/V statement.
2. Physical null for the dipole: observer boost + shell bulk flow (Heinesen 2021 §5 eqs 5.1–5.7; Maartens et al. 2024), 1/z scaling, as a design column; the HTT "constant rate dipole" is not a physical law for dust (A = 0).
3. Shear–quadrupole normalization map: η̃_2 (Legendre) ↔ STF eigenvalue ↔ Frobenius norm (T-03) ↔ Kalbouneh's H_2/H_0 (refs [44, 45] to be read).
4. Second-order terms as subdominant columns only (𝔮_1 ∝ z), with convergence of the anisotropic series to z ≈ 0.1 checked against simulations (Macpherson–Heinesen type), not assumed.
5. Atlas convention contract for the Bianchi lane: amplitude per unit IC → (σ/H)_0; m-structure in the Bianchi frame and Euler rotation; i^ℓ phase; handedness parity map (flips B and TB/EB sign); regular vs irregular identity; coupled vs decoupled background.
6. Bounded foreground-moment class: dimensional ρ = (ℓ ≤ 5 foreground amplitude) × Var(β,T) × ln²(ν/ν₀) in the metric M, with a remainder check (third-order, multi-component).
7. Closure statements that are theory, not data: K03/K05 (astrometric law exists, no sensitivity; vorticity visible only relative to a dynamical frame), L05 (same-sky splits are not independent skies).

---

## 9. Negative results and limitations of this run

- N-001 astrometric S bound; N-002 𝔮_1 depth law; N-003 d = −A/(cH) referent; N-004 free second-order moments (literature); N-005 AniLoS execution blocked here (`state/NEGATIVE_RESULTS.md`).
- Access limits: arXiv API and CDS/VizieR unreachable from the sandbox (web fetch used instead; CF4 ReadMe column definitions not read); the NPIPE paper's §5 text was not extractable (M-01 open); one extraction subagent was interrupted by a rate limit and resumed.
- All ΛCDM expectations quoted (T-05) are linear-theory toy numbers with Gaussian radial windows and full-sky coverage; they are not a substitute for mocks and must not be cited as literature.
- CF4 appears in H-1, H-7, Kalbouneh, Boubel and Stiskalek: agreement among them is not independent support; Pantheon+ (null quadrupole 0.0 ± 1.3 %) and mocks are the independent checks.

---

## Sources

- Heinesen, A. (2021), JCAP 05, 008, arXiv:2010.06534 — https://arxiv.org/abs/2010.06534
- Maartens, R. et al. (2024), JCAP 09, 070, arXiv:2312.09875 — https://arxiv.org/abs/2312.09875
- Kalbouneh, B. et al. (2026), JCAP 03, 084, arXiv:2510.02510 — https://arxiv.org/html/2510.02510v1
- Cowell, J. A., Dhawan, S., Macpherson, H. J. (2023), MNRAS, arXiv:2212.13569 — https://arxiv.org/abs/2212.13569
- Dhawan, S. et al. (2023), MNRAS, arXiv:2205.12692 — https://arxiv.org/abs/2205.12692
- Boubel, P. et al. (2025), JCAP 03, 066, arXiv:2412.14607 — https://arxiv.org/abs/2412.14607
- Stiskalek, R., Desmond, H., Lavaux, G. (2025), MNRAS, arXiv:2509.14997 — https://arxiv.org/abs/2509.14997
- Salzano, V. et al. (2025/26), arXiv:2512.02526 — https://arxiv.org/abs/2512.02526
- Duangchan, C. et al. (2026), A&A 708, A119 — https://www.aanda.org/articles/aa/pdf/2026/04/aa56645-25.pdf
- Saadeh, D. et al. (2016), PRL 117, 131302, arXiv:1605.07178 — https://arxiv.org/abs/1605.07178
- Pontzen, A., Challinor, A. (2007), arXiv:0706.2075 — https://arxiv.org/abs/0706.2075
- Vicente, J. G., Pereira, T. S., Pitrou, C. (2025/26), arXiv:2506.07786 — https://arxiv.org/abs/2506.07786 ; code https://github.com/jgvicente/anilos
- Darling, J. (2014), arXiv:1404.3735 — https://arxiv.org/abs/1404.3735
- Darling, J., Truebenbach, A., Paine, J. (2018), arXiv:1807.06670 — https://arxiv.org/abs/1807.06670
- Marcori, O. H., Pitrou, C., Uzan, J.-P., Pereira, T. S. (2018), PRD 98, 023517, arXiv:1805.12121 — https://arxiv.org/abs/1805.12121
- Gaia DR3 / Quaia VSH and astrometric Hellings–Downs (2024), arXiv:2412.08605 — https://arxiv.org/abs/2412.08605
- Gaia Collaboration, Klioner, S. A. et al. (2022), Gaia-CRF3, arXiv:2204.12574 — https://arxiv.org/abs/2204.12574
- Tully, R. B. et al. (2023), ApJ 944, 94, arXiv:2209.11238 — https://arxiv.org/abs/2209.11238
- Brout, D. et al. (2022), arXiv:2112.03864 — https://arxiv.org/abs/2112.03864
- Planck Collaboration (2020), Planck intermediate results LVII (NPIPE), arXiv:2007.04997 — https://arxiv.org/abs/2007.04997
- Carron, J., Mirmelstein, M., Lewis, A. (2022), arXiv:2206.07773 — https://arxiv.org/abs/2206.07773
- Gimeno-Amo, C. et al. (2023), arXiv:2306.14880 — https://arxiv.org/abs/2306.14880
- Chluba, J., Hill, J. C., Abitbol, M. H. (2017), MNRAS 472, 1195, arXiv:1701.00274 — https://arxiv.org/abs/1701.00274
- Vacher, L. et al. (2022), arXiv:2203.07246 — https://arxiv.org/abs/2203.07246
