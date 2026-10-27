# Independent adversarial review (Phase 5) — report of the `physmath-research-harness:adversarial-reviewer` subagent, 2026-10-26

Inputs read by the reviewer: state/HYPOTHESIS_GRAPH.md, state/EVIDENCE_LEDGER.md, state/CLAIM_AUDIT.md; AniLoS source /home/claude/jgvicente/anilos/src/anilos/anilos.py. No files edited by the reviewer. No promote/kill decisions.

## H-1 PV-shear bridge — ROLE: TRADEOFF

- Quadrupole half is coherent: S = σ/H ↔ window-weighted traceless velocity gradient is standard linear theory, the ±2.3 % eigenvalues sit at the ΛCDM few-percent expectation (E-X05; T-05 is own inference, not literature), and a mock null (SDSS PV mocks cached; 64 CF4-selection mocks, E-X09) plus an eigenframe comparison is a real, cheap test. Not a relabel: adds an eigenframe and depth prediction to the R32-05 "response identity" assumption.
- Dipole half is physically mis-specified. In Heinesen's expansion the O(z) dipole is −e·a with a the 4-acceleration of the congruence; for geodesic (dust) matter a = 0 identically, smoothed or not. "Gravitational acceleration of the PV field" is Newtonian intuition imported into a covariant term that vanishes. The ΛCDM referent of a Hubble dipole is the observer boost / shell bulk flow (Heinesen §5, 3 d.o.f.; E-X02 already flags this), which scales as 1/z, not as an O(z⁰) coefficient.
- "Are ... the covariant multipoles" upgrades C-OPT-04 (PARTIALLY_SUPPORTED) to an identity. Narrative ahead of evidence.
- Novelty is modest: the interpretation is the L2 lineage's default (Dhawan 2023, Cowell 2023, Kalbouneh 2026 §6 — unread, M-07; Stiskalek 2025 method). The local shear eigenframe from CF2/CF3 Wiener filters is itself published (Hoffman et al. 2015/2017) and would be circular w.r.t. CF4; only 2M++/BORG-type fields are independent, and they do not reach the z ≈ 0.1 windows.
- Regime: inner windows (z < 0.02) are nonlinear and Taylor-expansion-unsafe; outer windows lack an independent reconstruction; the testable band is roughly 0.02–0.06.
- The listed threat E-X03 ("no decreasing quadrupole trend") is weaker than stated: 1.45 ± 0.17 → 1.17 ± 0.52 (×10⁻²) is compatible with a factor-2 decrease at ~1σ. Prediction (ii) is not yet discriminating at CF4 depth.

Strongest counter-argument: the H03 discrepancy T = 23.40 (6 df) is computed with a diagonal 250 km/s per-row metric. A ΛCDM bulk flow coherent over the window (≈ 200–300 km/s rms at 100 h⁻¹ Mpc) induces a correlated dipole of several percent at z ≈ 0.02 that the covariance does not contain. Until a PV covariance from mocks replaces the working metric, the object H-1 bridges may be a covariance artifact, and the quadrupole significance (‖S‖_F = 0.0327 without covariance) is undefined.

Minimal evidence to resolve: (1) forward-model Ŝ_app through the exact R32-05 estimator (same 35,970 group positions, 19 nuisance columns, D metric) on (a) a CF4-independent linear-theory velocity field (2M++/Carrick-type or BORG) and (b) the cached SDSS PV mocks / 64 CF4 mocks; report eigenframe misalignment angle and ‖S‖_F percentile; compute the "window-averaged gradient" by the estimator itself. (2) Replace the 𝔥_1 = −a/H dipole identification with a boost/bulk 1/z_w column and a mock-derived correlated covariance; re-evaluate T.

## H-2 External polarized Bianchi atlas (AniLoS/AniCLASS) — ROLE: TRADEOFF

- Feasibility evidence solid (E-X11, code inspected). The hypothesis is procedural (admissible payload, not a physical result). "Distinctive predictions" are model-class properties (Pontzen–Challinor 2007) or calibrations, not tests.
- Source-verified convention risks: outputs are transfer functions per unit initial mode amplitude (tensor `betaur0[0] = 1`, line 471; vector `self.Phi_i_0 = -1.`, lines 795, 828) with no map to (σ/H)_0 or (ω/H)_0; K_CMB vs ΔT/T is a further factor. Only one m populated in the Bianchi frame (m = 2 tensor, m = 1 vector; `__alm_healpy` lines 330–333); docstrings (lines 310, 571) stale ("m = 0"). An all-m Galactic-frame atlas exists only after a rotation whose Euler convention must be declared. Phase `(1j)**ℓ √(4π(2ℓ+1))` (lines 615, 1127); handedness fixed by `nu = m/spiraling_length + 1j/curvature_radius` (line 287) with no handedness parameter. Bianchi V is a numerical limit (sqrth ≈ 1e5, line 107); IX is forced to ℓ_max = 3 (lines 589–593).
- Scope inconsistency: AniLoS is regular-only; Saadeh 2016 bounds S, V, T_reg and T_irr and the tightest VII_h bound (3.4e−10) is on T_irr. Whether the classic Jaffe/Planck VII_h template (and the cached BIANCHI v1.1 fixture) is a regular or irregular tensor mode must be settled before any morphology comparison.
- Coupled (CLASS Ω_K) vs decoupled fits: the manifest must state which; a coupled atlas cannot be compared to a decoupled fixture without running the fixture's background.
- Cross-validation: AniLoS–AniCLASS ≤ 2 % agreement is same-authors, same background, same conventions (M-03 stands). BASS/lowell_bianchi_solver is a meaningful cross-check only if it produces polarized Einstein–Boltzmann output for VII_h; E-I07's LRS Bianchi V kinematic images cannot validate E/B or recombination-era physics.

Strongest counter-argument: the atlas can satisfy the letter of B02 while the quantity that matters for B04/B05 — amplitude in (σ/H)_0 units and handedness/mode identity relative to the Planck comparator — is exactly what the code leaves to the user, with no public reference solution; a silently wrong normalization or parity would propagate into every injection in B04 undetected.

Minimal evidence: (1) pre-registered manifest fixing amplitude convention (β_init → (σ/H)_0 via nteb_tensor at η_0), T_CMB factor, frame/Euler convention, phase, handedness map, coupled/decoupled background, mode identity, IC; (2) convention-light validation against Pontzen–Challinor 2007: C_ℓ^{TT,EE,BB} shapes, EE/BB ratio, TB/EB sign; (3) mode identity of the cached BIANCHI v1.1 fixture from provenance.

## H-3 Astrometric nonradial response law — ROLE: INFORMATIVE_FAILURE

- The law is correct literature (Darling 2014; Marcori et al. 2018); novelty zero, acceptable for answering K03 "does a nonradial law exist" (yes).
- "S can be bounded independently of distances with Gaia/VLBA" fails under both readings of S: local window shear (≲ 300 h⁻¹ Mpc) gives no distance-independent E2 response for Gpc quasars; galaxies inside the window are astrometrically hopeless (≈ 0.45 μas/yr per galaxy vs ≈ 0.6 μas/yr random PV noise, before Gaia's limits). Global shear: tracers valid but the attainable bound (≈ 7 % now, ≈ 0.03 at Gaia-DR5 optimism) is 8–9 orders weaker than (σ/H)_0 ≲ 1e−10.
- T-04's 0.5 μas/yr multiplies a local amplitude into a global-shear law.
- EXPLANATION_RANGE uses C-PM-03 (INFERENCE_ONLY) as payload; vorticity sensitivity relative to a dynamical frame unquantified (M-04). The declared competitor is a strawman; the real competitor ("the law exists but has no constraining power on S in any regime") wins.

Minimal evidence: one paragraph on the PM response to a shear confined to R_w ≪ D; one line comparing the best astrometric bound with 1e−10; then close K03 with the literature law and a no-sensitivity statement.

## H-4 PR4 release-matched null lane — ROLE: DEFENDED (conditional)

- Strongest evidence in the set (E-X18, E-X19); worked template (Gimeno-Amo 2023); methodology import without novelty, appropriate for a null lane.
- Conditions: L03 as written asks for PR3 FULL/HM/OE — H-4 redefines the HOLD (record as such; cost: all L01 SMICA/PR3 results re-derived in Sevem/Commander PR4). Sims carry a single Commander foreground model (zero foreground variance; ranks are a CMB+noise+systematics pipeline null). Low-ℓ E transfer function is a per-realization suppression. 600 sims apply to Sevem T+P only (Commander T: 100) → p-floor 1/600 or 1/100 (≈ 3σ / 2.3σ cap). Data transfer cost unacknowledged. Selection protocol must be predeclared.

Strongest counter-argument: even with M-01 confirmed, the foreground genealogy is satisfied only degenerately (identical foreground in every sim).

Minimal evidence: (1) quoted NPIPE §5 / NERSC README statement that A/B/full sims of one index share the CMB and foreground input sky; (2) 50-sim pilot with input-vs-output a_ℓm at ℓ ≤ 5 quantifying the E suppression on the statistic.

## H-5 Physically bounded foreground-moment class — ROLE: NEEDS_MORE_EVIDENCE (single decisive number missing)

- Construction sound; legitimate partial-identification idea. ρ is a norm bound in the metric M = diag(d_i²): second-order moments scale as (foreground amplitude) × Var(β) × ln²(ν/ν₀); σ(β_d) alone does not give ρ without the dust/synchrotron amplitude at ℓ ≤ 5 in the mask, so a sky (or published ℓ ≤ 5 amplitude) must be consumed.
- Overformalization risk: exact radius for the truncated class while the remainder (third-order moments, multi-component dust, CO/free-free/AME, synchrotron curvature) is unbounded; at ℓ ≤ 5 dispersions are large and non-Gaussian.
- Reviewer's expectation (not evidence): Δβ_d ≈ 0.1–0.2, ln(353/143) ≈ 0.9 → second-order term ≈ 1 % of dust amplitude (tens of μK at ℓ ≤ 5 outside a 70 % mask at 143 GHz) → radius of order 0.1–1 μK vs the 0.379 μK target; informative failure is a live outcome.

Minimal evidence: (1) dimensional ρ from Commander/GNILC amplitudes + σ(β_d), σ(T_d), σ(β_s) (Planck 2018 XI; Planck Int. XXII) → radius vs 0.379 μK; (2) one PySM d1/s1 remainder check through the 7-channel design.

## H-7 Second-order covariant cosmography as the depth law — ROLE: INFORMATIVE_FAILURE

- Heinesen 2021 verbatim; as sole law refuted by E-I04 (T_⊥ = 15.316 > 12.59). Functional form wrong for the dominant structure: the CF4 dipole falls with depth (2.19 ± 0.13 → 0.25 ± 0.25 ×10⁻²) as a boost/bulk 1/z term does, whereas 𝔮_1 grows ∝ z; H-7 contains the subdominant term and omits the dominant one.
- Vorticity terms are products of two small quantities; no observational content in any regime.
- The 9-parameter joint fit on 12 coordinates reaches τ by parameter count; only cross-dataset (Pantheon+ q_dip) is non-circular. Series convergence to z ≈ 0.1 with O(z³) terms (61 d.o.f.) of relative size ≈ 1 % is assumed, not checked.

Minimal evidence: fit D_w with {constant dipole, 1/z_w boost/bulk, z_w 𝔮_1} under inherited and mock-derived covariance; report which column carries the T reduction and v_o vs 188 ± 22 km/s; compare 𝔮_1 only with Pantheon+.

## Cross-hypothesis issues

1. Shared diagonal-covariance assumption (H-1, H-7): a mock-derived covariance must precede any physical bridge.
2. Missing physical null: observer boost + radius-dependent bulk flow (1/z_w column) is absent from the hypothesis space; it is the most likely explanation of the depth structure.
3. CF4 double counting across H-1, H-7, E-X03, E-X06, E-X07; independent data: Pantheon+ (λ_1 = 0.021 ± 0.011, consistent with zero at 2σ) and mocks. Default reading of ‖Ŝ_app‖_F = 0.0327: ΛCDM PV scatter plus systematics until a mock percentile says otherwise.
4. H-1 vs H-3 contradiction on the referent of S.
5. Dipole referent mismatch: 𝔥_1 = −a/H vanishes for dust; boost d.o.f. implemented in no hypothesis.
6. H-2 convention/scope risks as above; E-I07 kinematic images are not the same physics as an AniLoS V-limit atlas.
7. Pre-registration/retrofit risk shared by H-2 and H-4.
8. H-4 and H-5 not combinable as independent foreground statements.
9. Audit-rule compliance: C-PM-03 (INFERENCE_ONLY) used in H-3; T-05 own inference; M-07.
10. Upstream data-integrity HOLDs (R25/R26, 0.147 vs 0.138 mag): constant per-method offsets are projected out by the 19 nuisance columns; position-dependent method offsets are not, and no hypothesis tests them with mocks including the CF4 method footprints.

Metacognitive summary: elegance mistaken for evidence (H-7, H-5, H-3); explanation vs fitting (H-7 discriminator; H-2 "amplitude consistency after alignment"); strawman competitors (H-1n as the only null; H-3's "no law exists"); narrative ahead of evidence (programme-wide framing of ‖Ŝ_app‖_F = 0.0327 and T = 23.4 as signals to be bridged while the only independent dataset and the only reconstruction-based analysis return nulls and the covariance is a working metric).

Reusable facts: AniLoS normalization/single-m/docstring/phase/handedness lines (anilos.py 287, 310, 330–333, 471, 571, 615, 795, 828, 1127) for any future BASS-vs-AniLoS comparison.
