# HYPOTHESIS_GRAPH (Phase 4; review and validation fields appended in Phases 5–7)

Scope rule: a "bridge hypothesis" here is a proposed identification of an HTT mathematical object with a standard observable plus the data/theory needed to make the identification testable. None is a physical claim about the Universe. Six families; expression-only variants merged. Premises limited to SUPPORTED / PARTIALLY_SUPPORTED claims in CLAIM_AUDIT.md.

## H-1  PV-shear bridge (lane H/K/V; HOLDs H02, H04, K04, V04)

CORE_CLAIM: The CF4 apparent quotient tensor Ŝ_app and the H03 window dipoles are, to O(z), the window-weighted covariant Hubble-parameter multipoles 𝔥_1 = −a/H, 𝔥_2 = σ/H of Heinesen's expansion (C-OPT-01), where σ and a are the shear and acceleration of the *matter congruence smoothed on the window scale*; their ΛCDM expectation is the tidal shear and gravitational acceleration of the local peculiar-velocity field, which can be predicted from an independent density/velocity reconstruction and from mocks. The familiar observables are the depth-resolved Hubble quadrupole H_2(z) and dipole (Kalbouneh 2026; Cowell 2023; Boubel 2025; Stiskalek 2025).

MINIMAL_ASSUMPTIONS: emitters comoving with the smoothed matter congruence; small-z expansion valid in 0.01 < z < 0.1; linear-theory PV field adequate for the window scale; CF4 method zero-points modelled as nuisance (C-CF4-03).

MECHANISM: 𝔥(e) = θ/3 − e·a + ee·σ → d_L = cz/𝔥 + O(z²) → magnitude field f = −κ log(1+q). In ΛCDM, σ_ij/H = −f_growth (∂_i∂_j ∇⁻² δ)_traceless smoothed on the window; so ‖S‖_F is a draw from a known distribution (toy estimate T-05: rms ≈ 2 % at 100 h⁻¹ Mpc, decreasing with radius), and the eigenframe is set by the local density field.

EXPLANATION_RANGE: gives S and d a physical referent (smoothed kinematic shear/acceleration) without invoking background (Bianchi) anisotropy; converts the "response identity S = σ/H" assumption of R32-05 into a testable statement with a predicted eigenframe and depth trend.

KNOWN_LIMITS: cosmological (background) shear is bounded at ≲ 1e−10 by CMB (E-X10), so any percent-level S is local structure or systematics by construction; a reconstruction built from CF4 itself is circular; CF4 has no released covariance (E-X03), so a working covariance (250 km/s) stays an assumption unless mocks supply it.

DISTINCTIVE_PREDICTIONS: (i) eigenframe of Ŝ_app aligns with the eigenframe of the reconstructed tidal shear within the window; (ii) ‖S‖_F decreases with window radius roughly as σ_R (linear theory) — contrast Kalbouneh 2026's "no clear decreasing trend" of the quadrupole; (iii) method-split (FP/TF/SN) consistency after zero-point nuisance projection.

COMPETING_HYPOTHESES: H-1n (null/systematic): Ŝ_app is zero-point × footprint leakage (C-CF4-03) plus selection; H-7 (second-order cosmography) explains depth structure through 𝔮 multipoles instead.

CHEAPEST_DISCRIMINATOR: compute the window-averaged traceless velocity-gradient tensor from an independent reconstruction (2M++/BORG-type, not the CF4 Wiener filter) and compare eigenvalues/eigenframe with Ŝ_app; compute the same from the 64 CF4-selection mocks (E-X09) or SDSS PV mocks (cached) for a null distribution.

FATAL_VULNERABILITY: if no reconstruction independent of CF4 distances is available at the required depth, the test is circular and H-1 collapses to "consistent with ΛCDM scatter" without identification.

SUPPORTING_EVIDENCE: E-I01, E-I03, E-X01, E-X03, E-X04, E-X05, E-X07.
THREATENING_EVIDENCE: E-X03 (no decreasing quadrupole trend with depth), E-X06 vs E-X07 (field disagreement on PV treatment), E-I04 (depth-slope design alone cannot bring T below threshold).

STATUS: active (serious candidate)

## H-2  External polarized Bianchi atlas via AniLoS/AniCLASS (lane B; HOLDs B02–B05, R23-ATLAS)

CORE_CLAIM: An externally produced, manifested atlas of a_ℓm^{T,E,B}(ℓ ≤ 30, all m) for nearly-isotropic Bianchi VII_h (grid in h and spiral length), VII_0, V and IX regular vector ('iso','oct' IC) and tensor modes, generated with the public AniLoS/AniCLASS codes and cross-validated against an independent solver, satisfies the *payload* part of B02/R23-ATLAS ("numeric all-m polarized T/E/B atlas with IC, history, units, frame and family/mode metadata") and unblocks B03 (convolution with release-matched processing) and B04 (equivalence classes, injection ensemble).

MINIMAL_ASSUMPTIONS: linear (nearly-isotropic) regime suffices for the amplitudes of interest ((σ/H)_0 ≲ 1e−9); regular modes are the relevant ones (irregular modes excluded, as in E-X10 only T_irr treated); CLASS background with Ω_K ≠ 0 handled by AniCLASS.

MECHANISM: AniLoS solves vector/tensor Boltzmann hierarchies (tight coupling + free streaming) in the Bianchi eigenmode basis and returns Θ_ℓ^(m), E_ℓ^(m), B_ℓ^(m) → healpy a_ℓm (E-X11, code inspected: `alm_tensor`, `alm_vector`).

EXPLANATION_RANGE: covers the VII_h family tree (VII_h, VII_0, V) and IX; does not cover Bianchi I, scalar modes, exceptional VI_{−1/9}, or non-perturbative shear; so a "verified subset" (as the scope doc prefers) not an all-11 classification.

KNOWN_LIMITS: no published validation against ABSolve/ANICOSMO (M-03); perturbative; depends on CLASS version; handedness and frame conventions must be fixed explicitly; htt_base forbids native execution, so the run must be an external product with a manifest.

DISTINCTIVE_PREDICTIONS: E/B power of comparable magnitude and parity-odd TB/EB for VII_h (E-X12); specific m-structure in the Bianchi frame; T-only amplitude consistent with the cached BIANCHI v1.1 T fixture after convention alignment.

COMPETING_HYPOTHESES: continue waiting for a released ANICOSMO/Planck template set (none public, E-I11); use the user's own BASS/lowell_bianchi_solver as the sole producer (forbidden as "native" inside htt_base, but admissible as the *independent cross-check*).

CHEAPEST_DISCRIMINATOR: install AniLoS + CLASS in an external environment; compute VII_h (h = 0.1, sqrth default) tensor and vector a_ℓm at ℓ ≤ 10; check (a) T map against the cached BIANCHI v1.1 fixture morphology after rotation, (b) peak polarization scale ~1 μK for a model matching WMAP-era temperature amplitude (E-X12), (c) agreement with BASS at ℓ ≤ 5 to a few percent.

FATAL_VULNERABILITY: convention mismatch (handedness, m-sign, spin-weight sign, K_CMB vs ΔT/T) could silently invalidate the atlas; the admission criteria for an "external" product must be written before the run (pre-registration) or the result is a retrofit.

SUPPORTING_EVIDENCE: E-X11, E-X10, E-X12, E-I11.
THREATENING_EVIDENCE: M-03 (no validation), E-I08 B02 wording ("Einstein–Boltzmann physics, recombination, IC, mode test actual").

STATUS: active (serious candidate)

## H-3  Astrometric nonradial response law (lane K; HOLDs K03, K05)

CORE_CLAIM: The nonradial response K03 asks for is the direction-drift law μ(n) = −H ⊥(S·n) − ⊥ v̇_o/c + (frame rotation) (E-X13, E-X14): a distance-independent E2 pattern for shear, an E1 glide for observer acceleration, a B1 rotation for frame/vorticity. With cached Gaia DR3 CRF3 proper motions and VLBA PMs, S can be bounded independently of distances.

MINIMAL_ASSUMPTIONS: quasars comoving with the matter congruence on average (no net transverse peculiar velocity pattern at ℓ ≤ 2); straight geodesics; frame tied to quasars (so B1 is unobservable as cosmology).

MECHANISM: Bianchi I / small-shear covariant drift; VSH decomposition (Mignard–Klioner).

EXPLANATION_RANGE: supplies the missing "source-matched ω/curl response" statement: the curl response of comoving sources vanishes except for a global rotation that the quasar frame absorbs (C-PM-03, INFERENCE_ONLY).

KNOWN_LIMITS: predicted E2 amplitude for ‖S‖_F ≈ 0.033 is ≈ 0.5 μas/yr (T-04), an order of magnitude below Gaia DR3 systematics (≈ 12 μas/yr at > 15°; √P2^E ≈ 9 μas/yr) and below VLBI (≈ 1 μas/yr ↔ 7 %); vorticity sensitivity relative to a dynamical frame is not quantified in sources read.

DISTINCTIVE_PREDICTIONS: an upper bound ‖S‖_F ≲ 0.07 (VLBI) now; Gaia DR4/DR5 could reach a few μas/yr systematics → ‖S‖_F ≲ 0.1–0.2 unless systematics drop further (INFERENCE).

COMPETING_HYPOTHESES: none needed; this is a response-law hypothesis, the competitor is "no usable nonradial law exists".

CHEAPEST_DISCRIMINATOR: fit E1+B1+E2+B2 VSH to the cached CRF3 sample with the per-source covariances; compare E2 amplitude with 0.5 μas/yr; if E2 ≫ 1 μas/yr, systematics dominate and the lane yields only a bound.

FATAL_VULNERABILITY: Gaia PM systematics at ℓ = 2 are not characterised well enough to subtract; a bound ≥ 7 % adds nothing to the CF4 lane.

SUPPORTING_EVIDENCE: E-X13, E-X14, E-X15, E-I09.
THREATENING_EVIDENCE: E-X15 (Gaia √P2 ≈ 9 μas/yr).

STATUS: active (tradeoff candidate)

## H-4  PR4 release-matched null lane (lane L; HOLDs L03–L06)

CORE_CLAIM: NPIPE/PR4 (Sevem T+P, Commander T) with its 600 end-to-end simulations and A/B detector splits provides the release-matched null that L03 requires, if (M-01) the CMB+foreground sky is shared across A/B/full per index; morphology-statistic ranks and look-elsewhere corrections (L04) are then computable with a predeclared selection protocol following the PR4 anomaly-paper practice (E-X19).

MINIMAL_ASSUMPTIONS: the morphology statistic's coverage can be calibrated on 600 sims (p-value floor 1/600); the low-ℓ E transfer function is correctable for the statistic; foreground residual realism of the Commander-model component is adequate at ℓ ≤ 5.

MECHANISM: same pipeline on data and sims; A−B differences as noise/systematics null (not independent skies).

KNOWN_LIMITS: PR4 is a different release than the PR3 SMICA products used so far (all retained L01 results would need re-derivation); non-Gaussian systematics not simulated (E-X19); 600 sims limit tail resolution.

DISTINCTIVE_PREDICTIONS: rank of the observed morphology statistic among 600 sims with a fixed protocol; A/B consistency.

COMPETING_HYPOTHESES: FFP10 full-mission-only null (Planck 2018 VII practice) with split differences as diagnostics only.

CHEAPEST_DISCRIMINATOR: read NPIPE §5 / NERSC README to settle M-01; then compute the retained SMICA-equivalent statistic on 50 PR4 sims as a pilot.

FATAL_VULNERABILITY: if A/B/full do not share realizations per index, the "same-realization genealogy" is again unavailable and L03 stays HOLD.

SUPPORTING_EVIDENCE: E-X18, E-X19.
THREATENING_EVIDENCE: M-01.

STATUS: active

## H-5  Physically bounded foreground-moment class (lane L/P2; R31 rank-0 result)

CORE_CLAIM: Replacing the free nine-moment class by a bounded class with ρ set from measured sky dispersions of β_d, T_d, β_s (Planck 2018 XI; Vacher 2022 framework) turns the rank-0 free second-order relaxation into an informative identified set S_ρ(Y) whose radius √(ρ² − J_0)/ℓ_M is below the signed24 target norm.

MINIMAL_ASSUMPTIONS: moment coefficients scale with within-beam/line-of-sight variances of β and T; no blackbody-mimicking contaminant.

MECHANISM: E-I06 identified set with externally justified ρ.

KNOWN_LIMITS: numerical dispersions not yet extracted (M-02); moment truncation remainder unbounded without a model.

DISTINCTIVE_PREDICTIONS: identified-set radius as a function of ρ; comparison with the retained SMICA held-out-B norm 0.379 μK.

COMPETING_HYPOTHESES: full parametric component separation (Commander) as the standard route.

CHEAPEST_DISCRIMINATOR: literature lookup of β_d/T_d dispersions → ρ → radius; one linear-algebra evaluation with the retained ℓ_M.

FATAL_VULNERABILITY: ρ implied by real dust variations gives a radius larger than the target norm → no information (informative failure).

SUPPORTING_EVIDENCE: E-I06, E-X20.
THREATENING_EVIDENCE: Vacher 2022 β-2 degeneracy.

STATUS: active

## H-7  Second-order covariant cosmography as the depth law (lane H/V/K; HOLDs H04, K02 scope, V04)

CORE_CLAIM: Extending the HTT local law from O(z) to O(z²) with Heinesen's effective deceleration multipoles 𝔔(e) (25 d.o.f.) supplies the missing *physical depth response* for the H03 four-window dipoles (the window dependence of D_w is the 𝔮_1 dipole term) and introduces radial sensitivity to vorticity through 𝔮_1 ∋ a^ν ω_{μν} and 𝔮_2 ∋ −2σ·ω (E-X01 eq. 4.3), which the first-order radial law lacks (K02: n·ω·n = 0).

MINIMAL_ASSUMPTIONS: small-z expansion to O(z²) valid to z ≈ 0.1; emitters comoving; 𝔥 ≠ 0 along rays.

MECHANISM: d_L = z/𝔥 + (1 − 𝔔) z²/(2𝔥) + O(z³); 𝔔 multipoles as listed in E-X01.

EXPLANATION_RANGE: connects the H03 "structured discrepancy frontier" (D η term) to a named physical response (𝔮_1 ∝ z); the published Q_1 = 2.0 ± 0.4 (E-X03) and q_dip (E-X04) are its familiar observables.

KNOWN_LIMITS: the pure depth-slope design in R32-03 (rank 3) leaves T_⊥ = 15.316 > τ = 12.59 (E-I04), so a linear-in-z dipole alone does not explain the H03 residual under the inherited covariance; vorticity enters only multiplied by a or σ (second-order small).

DISTINCTIVE_PREDICTIONS: window dipoles D_w = d_0 + z_w 𝔮_1-term with a fixed sign pattern; joint fit of (𝔥_1, 𝔮_1) across windows; a boosted observer changes 𝔮_1 by the known boost correction (E-X01 §5).

COMPETING_HYPOTHESES: H-1n systematics; H03's FP-fraction design (sample composition).

CHEAPEST_DISCRIMINATOR: re-express the R32-03 depth-slope column as the 𝔮_1 response with Heinesen's coefficient and check whether the joint (𝔥_1, 𝔮_1, bulk) fit reaches τ; compare fitted 𝔮_1 with Kalbouneh's Q_1 = 2.0 ± 0.4.

FATAL_VULNERABILITY: already partly falsified as a sole explanation (T_⊥ = 15.3); survives only as a component of the response design.

SUPPORTING_EVIDENCE: E-X01, E-X03, E-X04, E-I04.
THREATENING_EVIDENCE: E-I04 depth-slope result.

STATUS: active (theory extension)

## Merged / not opened

- H-6 (zero-point × footprint leakage) merged into H-1 as its null competitor H-1n.
- "Rotating templates" for Bianchi families: rejected earlier in repo (cannot supply missing modes/history) — not reopened.

---

## Phase 5 — independent adversarial review (subagent `physmath-research-harness:adversarial-reviewer`, 2026-10-26)

Roles assigned (verbatim role labels; justifications condensed, full text in `review/ADVERSARIAL_REVIEW.md`):

- H-1 → TRADEOFF. Quadrupole half coherent and testable (mock null + eigenframe); dipole half mis-specified: Heinesen's O(z) dipole is −e·a with a the 4-acceleration, which vanishes identically for geodesic dust, smoothed or not; the ΛCDM referent of a Hubble dipole is the observer boost / shell bulk flow (1/z scaling, Heinesen §5), not an O(z⁰) coefficient. C-OPT-04 must stay PARTIALLY_SUPPORTED (same object class, not identity). Strongest counter: the H03 discrepancy T = 23.40 uses a diagonal 250 km/s metric with no correlated PV / cosmic-variance term; a coherent ΛCDM bulk flow produces exactly such a term, so the object being bridged may be a covariance artifact. Minimal evidence: (1) forward-model Ŝ_app through the exact R32-05/H03 estimator on an independent linear-theory field (2M++/BORG-type) and on the cached mocks; (2) replace the 𝔥_1 column by a boost/bulk 1/z_w column with a mock-derived covariance and re-evaluate T.
- H-2 → TRADEOFF. Feasibility solid; "predictions" are model-class properties or calibrations. Source-verified convention risks: per-unit-IC normalization (`betaur0[0] = 1`, `Phi_i_0 = -1`; no map to (σ/H)_0), single populated m in the Bianchi frame (m = 2 tensor, m = 1 vector; docstrings stale), phase `(1j)**ℓ √(4π(2ℓ+1))`, fixed handedness with no parameter, Bianchi V only as the sqrth ≈ 1e5 limit, IX forced to ℓ_max = 3, regular modes only whereas the tightest Saadeh bound is on T_irr, coupled (CLASS Ω_K) background vs likely decoupled fixtures. Minimal evidence: pre-registered manifest (amplitude convention via nteb_tensor at η_0, T_CMB factor, Euler convention, phase, handedness map, coupled/decoupled, mode identity, IC); convention-light validation of C_ℓ shapes, EE/BB ratio and TB/EB sign against Pontzen–Challinor 2007; mode identity (regular/irregular) of the cached BIANCHI v1.1 fixture from provenance.
- H-3 → INFORMATIVE_FAILURE. The law is correct literature (zero novelty, acceptable for K03). The bound claim fails under both readings of S: local window shear has no distance-independent PM response at Gpc quasar distances; global (Bianchi) shear is excluded at 1e−10 by CMB, 8–9 orders below any astrometric reach. T-04's 0.5 μas/yr multiplies a local amplitude into a global-shear law. Resolution: one paragraph on PM response to a shear confined to R_w ≪ D, one line comparing astrometric reach with 1e−10; close K03 with the literature law and a no-sensitivity statement instead of a VSH fit.
- H-4 → DEFENDED (conditional). Strongest evidence in the set; conditions to record: H-4 redefines L03 (PR4 instead of PR3 FULL/HM/OE) with the cost of re-deriving L01 results; sims carry a single Commander foreground model (zero foreground variance; ranks are a CMB+noise+systematics pipeline null, not a sky null); the low-ℓ E transfer function is a per-realization suppression; 600 sims apply to Sevem T+P only (Commander T: 100) → p-floor 1/600 or 1/100; data transfer cost; selection protocol must be predeclared. Minimal evidence: quoted NPIPE/NERSC statement on shared input sky per index (M-01); 50-sim pilot with input-vs-output a_ℓm at ℓ ≤ 5.
- H-5 → NEEDS_MORE_EVIDENCE (one decisive number). ρ is a norm bound in the metric M = diag(d_i²) and needs the ℓ ≤ 5 foreground amplitude in the mask, not only σ(β_d); truncation remainder (third-order moments, multi-component dust, CO/free-free/AME) unbounded at ℓ ≤ 5; reviewer's expectation: radius of order 0.1–1 μK vs the 0.379 μK target, so the informative-failure outcome is live. Minimal evidence: dimensional ρ from Commander/GNILC amplitudes + Planck 2018 XI dispersions; one PySM d1/s1 remainder check through the 7-channel design.
- H-7 → INFORMATIVE_FAILURE. Heinesen verbatim; as sole depth law already refuted by E-I04 (T_⊥ = 15.3 > 12.59); functional form wrong for the dominant structure (CF4 dipole falls with depth as a boost/bulk 1/z term, 𝔮_1 grows ∝ z); vorticity terms are products of small quantities with no observational content; the 9-parameter joint fit reaches τ by parameter count. Resolution: fit {constant dipole, 1/z_w boost/bulk, z_w 𝔮_1} under inherited and mock covariance, report which column carries the reduction and v_o vs 188 ± 22 km/s; cross-dataset check only with Pantheon+ (E-X04).

Cross-hypothesis issues recorded: (1) shared diagonal-covariance assumption under H-1/H-7 — a mock-derived correlated covariance must precede any physical bridge; (2) the standard ΛCDM competitor (observer boost + radius-dependent bulk flow, 1/z_w column) is absent from the hypothesis space; (3) CF4 double counting across H-1, H-7, E-X03, E-X06, E-X07 — only Pantheon+ (E-X04/05) and mocks are independent; (4) H-1/H-3 contradiction on the referent of S; (5) dipole referent mismatch (−a/H vanishes for dust); (6) H-2 convention/scope risks as above; (7) pre-registration needed for H-2 and H-4; (8) H-4 and H-5 not combinable as independent foreground statements; (9) audit-rule compliance (C-PM-03 INFERENCE_ONLY used in H-3; T-05 own inference; M-07); (10) position-dependent method offsets (H-1n) untested by mocks with CF4 method footprints.

## H-0  (added after review; reopened hypothesis space) — Standard ΛCDM physical null for the window dipoles

CORE_CLAIM: The H03 window dipoles D_w are explained by an observer boost relative to the sources' frame plus a radius-dependent bulk flow (1/z_w-type columns, the bulk response R_w b already present in R32-03 plus a boost term), under a covariance that includes correlated peculiar-velocity / cosmic-variance terms derived from mocks; with that covariance T falls below τ and no "structured discrepancy" remains to be bridged.
MINIMAL_ASSUMPTIONS: ΛCDM linear/quasi-linear velocity field; CF4 selection as in mocks.
MECHANISM: Heinesen §5 boost (3 d.o.f.) + shell bulk flow; mock covariance replaces the diagonal 250 km/s metric.
DISTINCTIVE_PREDICTIONS: fitted v_o compatible with 188 ± 22 km/s (E-X03) and bulk 520 ± 91 km/s; T_min ≤ τ.
COMPETING_HYPOTHESES: H-1n (systematics), H-7 (depth law).
CHEAPEST_DISCRIMINATOR: re-fit the saved 12 dipole coordinates with {constant dipole, 1/z_w boost/bulk} under (a) inherited and (b) mock-derived covariance.
FATAL_VULNERABILITY: no mock set reproduces the CF4 method footprints and depth selection (then the covariance is again a model choice).
STATUS: active (strongest competitor; required before H-1/H-7 can be judged)
