# VERIFICATION_DESIGN (Phase 7) — minimal decisive tests per surviving candidate

Nine fields per candidate: testable claim; required inputs; expected result if correct; expected result under strongest competitor; pass criterion; kill criterion; ambiguity condition; cheapest next action; escalation path. Priority rule: tests that discriminate several hypotheses at once first; literature check + toy calculation first where possible. Drafted before the adversarial review returned; roles from that review are appended in the DECISION_LOG.

## V-1  H-1 PV-shear bridge (depth-resolved Hubble quadrupole vs ΛCDM tidal shear)

1. Testable claim: the window-resolved apparent quadrupole tensor T_w (five STF coordinates per CF4 window, already produced by the H03 machinery as Q_w) equals, within its covariance, the ΛCDM prediction of the window-weighted traceless velocity gradient (plus zero-point × footprint leakage), with eigenframe alignment and a ‖T_w‖_F that falls ≈ 4× from z_c = 0.025 to 0.080 (T-05b: 0.030 → 0.0079 rms).
2. Required inputs: existing H03 tomography outputs (four windows × 5 STF, 36 × 36 covariance; cached); an independent density/velocity reconstruction not built from CF4 distances (2M++ or BORG-type public velocity field) or the 64 CF4-selection mocks (Duangchan 2026) / SDSS PV mocks (cached, 2048 files) for a null distribution; per-method zero-point nuisance columns (already in the 19-column projection).
3. Expected if correct: per-window ‖T_w‖_F consistent with the mock/linear distribution; eigenvector of the largest |eigenvalue| within ≈ 30° of the reconstructed tidal eigenvector; method-split estimates agree after nuisance projection.
4. Expected under strongest competitor (H-1n systematics; or Kalbouneh-type persistent quadrupole): ‖T_w‖_F flat or rising with depth; eigenframe tied to the survey footprint (6dFGS/SDSS boundaries) rather than to the density field; method-split disagreement.
5. Pass: all four windows inside the mock 95 % envelope AND alignment angle < 30° in at least the two inner windows.
6. Kill (of the "S = smoothed physical shear" identification): outer-window ‖T_w‖_F exceeds the mock 99 % envelope AND eigenframe tracks the footprint under method splits — then Ŝ_app is a selection/calibration object (informative failure; H-1n promoted).
7. Ambiguity: mocks and reconstruction disagree with each other by more than the data error; or the reconstruction's depth (< 200 Mpc/h) does not cover the outer windows.
8. Cheapest next action: compute ‖T_w‖_F and eigenframes from the already-saved H03_SOURCE_TOMOGRAPHY.json; compare with T-05b numbers and with Kalbouneh's η̃_2 (converted via T-03). Zero new data.
9. Escalation: run the mocks through the exact H03 fitting operator (window weights, 250 km/s metric) to get the null distribution of T_w; then the reconstruction comparison.

Discriminates: H-1 vs H-1n vs H-7 (depth dependence is the shared observable).

## V-2  H-2 external polarized Bianchi atlas (AniLoS/AniCLASS)

1. Testable claim: AniLoS/AniCLASS output a_ℓm^{T,E,B} (ℓ ≤ 30, all m) for VII_h regular tensor and vector modes that (i) reproduce the cached T-only BIANCHI v1.1 VII_h fixture morphology after an explicit rotation/convention map, (ii) give E and B polarization of comparable power with a parity-odd TB/EB signature (Pontzen–Challinor 2007), and (iii) agree with an independent solver (BASS or lowell_bianchi_solver mode basis) to ≤ 5 % at ℓ ≤ 5.
2. Required inputs: external environment with CLASS/classy + AniLoS (GPL-3; `pip install git+https://github.com/jgvicente/AniLoS`); pre-registered admission criteria (units K_CMB vs ΔT/T, healpy a_ℓm convention, handedness, Bianchi frame); the cached T fixture; the user's BASS outputs for the same (h, Ω_K, mode, IC).
3. Expected if correct: (i)–(iii) hold; relative differences ≤ 2 % at low ℓ between AniLoS and AniCLASS as published (E-X11).
4. Expected under competitor (no admissible atlas obtainable): convention map cannot be closed (sign/handedness ambiguity), or BASS disagrees at > 10 % after all convention fixes.
5. Pass: (i) correlation > 0.99 between fixture and AniLoS T map at ℓ ≤ 10 after rotation; (ii) E/B power ratio within a factor 3 of unity with nonzero TB/EB; (iii) ≤ 5 % per-ℓ agreement with BASS at ℓ ≤ 5 for ≥ 2 modes.
6. Kill: (iii) fails for both vector and tensor modes after convention audit → AniLoS outputs are not an admissible atlas without a third solver.
7. Ambiguity: agreement in T but not in E/B (would indicate polarization-convention issues rather than physics).
8. Cheapest next action: install and run `Anilos({'sqrth':0.1,'Omega_K':1e-6}).tensor_solver(); alm_tensor(10)` in a scratch environment (blocked in this session by the execution policy on external code; the user can run it locally); record conventions from the source (`__alm_healpy`).
9. Escalation: full h × sqrth × mode × IC grid at ℓ ≤ 30 with manifest; convolve with the L03/H-4 processing; injection test for B03/B04.

Discriminates: B02/R23-ATLAS payload existence; feeds B03–B05.

## V-3  H-7 second-order cosmography as depth law

1. Testable claim: replacing the ad hoc depth-slope column D_z of R32-03 by the Heinesen 𝔮_1 response (dipole coefficient × (1 − 𝔔)z/(2𝔥) weighting per window) and fitting (bulk b, 𝔥_1, 𝔮_1) jointly reduces the 12-coordinate discrepancy T below τ = χ²_{6−Δdf,0.95}, with fitted 𝔮_1 consistent with Kalbouneh's Q_1 = 2.0 ± 0.4.
2. Required inputs: saved H03 dipoles and covariance (cached); Heinesen eq. (3.7)–(4.3) coefficients; window redshift weights.
3. Expected if correct: T_min ≤ τ with 𝔮_1 ≈ 2 ± 1.
4. Expected under competitor (systematics/FP composition): T_min stays > τ (as for D_z: T_⊥ = 15.3) and 𝔮_1 is unphysical (|𝔮_1| ≫ 10).
5. Pass: T_min ≤ τ and |𝔮_1 − 2.0| < 1.5.
6. Kill: T_min > τ with the 𝔮_1 column → second-order cosmography alone does not explain the H03 residual (already indicated by the D_z result).
7. Ambiguity: T_min ≤ τ only when the FP-fraction column is also included (joint design) — then depth and composition are degenerate.
8. Cheapest next action: one 12 × 1 column change in the existing R32-03 profiling code; minutes.
9. Escalation: joint fit with per-window monopoles and the P1 selected likelihood.

## V-4  H-3 astrometric nonradial law

1. Testable claim: the VSH E2 amplitude of the cached Gaia DR3 CRF3 proper motions, after E1/B1 removal and magnitude-dependent systematics modelling, bounds ‖S‖_F below the VLBI 7 % level; the predicted signal for Ŝ_app is 0.22 μas/yr rms (T-04).
2. Required inputs: cached CRF3 PM table with 2 × 2 covariances; VSH basis (Mignard–Klioner); systematics model.
3. Expected if correct (law usable): E2 upper bound ≲ 1–2 μas/yr → ‖S‖_F ≲ 0.15–0.3; no detection.
4. Expected under competitor (systematics floor): √P2^E ≈ 9 μas/yr as in arXiv:2412.08605 → no cosmological information.
5. Pass: a 95 % bound ‖S‖_F < 0.07 (beats VLBI).
6. Kill: bound > 0.3 → lane yields nothing beyond VLBI; keep only as a law statement for K03.
7. Ambiguity: bound between 0.07 and 0.3.
8. Cheapest next action: weighted VSH fit to the cached sample (one script; data already local on the owner's machine).
9. Escalation: Gaia DR4 (2026-12 expected) with longer baseline; joint VLBI–Gaia fit.

## V-5  H-4 PR4 null lane

1. Testable claim: for a fixed index i, NPIPE A_i, B_i and full_i simulations share the CMB (and foreground) sky, so A_i − B_i is a pure noise/systematics null and full_i is a release-matched total-field null.
2. Required inputs: NPIPE paper §5 text or NERSC README; 2–3 simulation triplets at Nside 16.
3. Expected if correct: (A_i − B_i) has no CMB power at ℓ ≤ 5 (cross-spectrum with full_i consistent with zero).
4. Expected under competitor: nonzero CMB residual in A_i − B_i → independent realizations.
5. Pass: |C_ℓ^{(A−B)×full}| < 1 % of C_ℓ^{full} at ℓ ≤ 5 for all triplets.
6. Kill: ≥ 10 % → L03 remains HOLD under PR4 too.
7. Ambiguity: 1–10 %.
8. Cheapest next action: read the documentation (M-01); then download three triplets at low resolution (already partly cached: npipe6v20 030 A/B mc_00200).
9. Escalation: 600-sim pilot of the retained morphology statistic.

## V-6  H-5 bounded-moment class

1. Testable claim: with ρ set from Planck-measured β_d, T_d, β_s dispersions, the identified-set radius √(ρ² − J_0)/ℓ_M is below the signed24 target norm.
2. Required inputs: Planck 2018 XI / Planck Int. XXII dispersions (M-02); retained ℓ_M = 3.1177–3.1184 (E-I06).
3. Expected if correct: radius < target norm (informative set).
4. Expected under competitor: radius ≥ target norm (no information).
5. Pass/Kill: as stated, with the retained numbers.
6. Ambiguity: ρ depends strongly on pivot choice (β_s = −3, β_d = 1.5, T_d = 20 K).
7. Cheapest next action: literature lookup + one line of algebra.
8. Escalation: Commander-style parametric separation comparison.

## Immediate executable list (zero new data)

1. V-1 step 8 (H03 saved tomography → ‖T_w‖_F, eigenframes; compare to T-05b and Kalbouneh η̃_2).
2. V-3 step 8 (𝔮_1 column swap in R32-03 profiling).
3. V-5 step 8 (M-01 documentation check).
4. V-6 step 7 (dispersion lookup → ρ → radius).
5. V-2 step 8 (AniLoS smoke run in an external environment; blocked here).
