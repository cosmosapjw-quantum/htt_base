# CLOSEOUT — HTT observable-bridge research run, cycle 1 (2026-10-26 → 2026-10-27)

Target: htt_base @ a55036ad, PUBLICATION_ACCELERATION_20261025 (seven companion manuscripts, two frontiers, 29 residual HOLDs at `POST_PUBLICATION_CHECKPOINT_20261026/README.md`, read via `git show a55036ad:<path>`). Intensity: deep (one full cycle). Compaction rule applied: only state, blockers, negative results, evidence pointers and versions are kept.

## Confirmed (FACT, reproducible)

1. HTT local optical law ≡ Heinesen 2021 O(z) effective Hubble parameter; f_μ = −κ log(1+q) (T-01, SymPy).
2. R32-01 Table I (octupole remainder bounds) reproduced independently to ≤ 1e−6; chirality witness attains 4√2/135 (T-02).
3. Normalization bridge: axisymmetric STF eigenvalue s ↔ Legendre η̃_2 = s/ln10 ↔ ‖S‖_F = s√(3/2); HTT directional rms 0.0119246 reproduced (T-03).
4. Astrometric E2 response of a shear: rms H‖S‖_F/√5 (T-04); public literature law (Darling 2014; Marcori 2018).
5. Per-window apparent shear from the saved H03 tomography (T-11; archived `validation/t11_h03_tomography.py`): ‖Q_w‖_F/H_w (debiased) 0.027, 0.041, 0.049, 0.020; near-pure-shear eigenstructure; dipole aligned with the positive quadrupole axis (6°–37°); axes 16°–25° from Kalbouneh's (299°, 5°) and 12–28° from the celestial south pole (windows 1–3).
6. No ΛCDM dipole law (bulk/boost, constant, z-growth) fits the 12 window dipoles under the inherited covariance: best 6-parameter T = 22.67 (τ = 12.59), 9-parameter T = 15.32 on 3 df (T-12). Fitted bulk 295 ± 18 km/s toward (287°, −5°). Boost and bulk columns collinear at O(z) (principal angles 5–9°).
7. AniLoS/AniCLASS (GPL-3) produce all-m T/E/B a_ℓm for nearly-isotropic VII_h and IX (V, VII_0 as limits), regular vector/tensor modes (code inspected; conventions documented at line level in `review/ADVERSARIAL_REVIEW.md`).
8. Kalbouneh 2026 Table 4: H_2/H_0 = 2.8 ± 0.4 % (CF4), 2.3 ± 0.7 (TF), 2.6 ± 0.9 (FP), 0.0 ± 1.3 (Pantheon+); Q_1 = 2.0 ± 0.4; v_o = 188 ± 22 km/s; the observer-motion dipole scales as 1/z; H_1 not fitted.

## Refuted or weakened

- The HTT dipole d = −A/(cH) as a ΛCDM observable: the O(z) dipole −e·a vanishes for geodesic dust; the observed dipole is observer boost + bulk flow (N-003).
- Astrometric bound on the CF4-scale S (N-001): no sensitivity in any regime; K03 closes with a law + no-sensitivity statement.
- 𝔮_1 (second-order) as the H03 depth law (N-002): wrong dominant trend; fails as sole law (T_⊥ = 15.3).
- "Running a public Bianchi code satisfies B02" — demoted: only an externally produced, manifested, convention-audited atlas can be proposed; T_irr, Bianchi I, scalar modes remain uncovered.
- Linear-ΛCDM toy expectation (T-05b, INFERENCE) vs CF4 windows: inner window consistent, middle windows 2–4× above the linear rms — but this statement is conditional on the inherited covariance and the toy's simplifications; not a result.

## Still uncertain

- Whether ‖Ŝ_app‖_F = 0.0327 and T = 23.4 are physics, covariance artefacts (missing correlated PV/cosmic variance), or method × footprint leakage. Decisive step: mocks through the exact H03/R32-05 operator (V-0(b)/V-1 step 9).
- NPIPE shared-sky-per-index property (M-01); dimensional ρ for the bounded moment class (M-02); AniLoS validation vs ABSolve (M-03); vorticity response for tilted observers (M-04); public location of the nominal Pantheon+ surface (M-05); cause of the CF4 0.147 vs 0.138 mag shift (M-06); H_2 normalization in refs [44, 45] (M-07); regular/irregular and coupled/decoupled identity of the cached BIANCHI v1.1 fixture (M-08); CF4-footprint-aware mocks (M-09).

## Missing evidence (carried forward)

M-01 … M-09 as above (EVIDENCE_LEDGER.md, RESEARCH_STATE.md).

## Negative results preserved

N-001 … N-005 in NEGATIVE_RESULTS.md (astrometric S bound; 𝔮_1 depth law; acceleration-dipole referent; free second-order moment class; in-session execution of external code blocked).

## Decisions (DECISION_LOG.md)

H-0 PROMOTE (V-0; (a) executed → informative, (b) pending); H-1 REOPEN_HYPOTHESIS → H-1Q (quadrupole only); H-2 PROMOTE (manifest-first); H-3 REJECT; H-4 REOPEN_EVIDENCE (M-01); H-5 REOPEN_EVIDENCE (dimensional ρ); H-7 REJECT (𝔮_1 column kept inside V-0). Programme-level: HOLD — no candidate approaches a physical claim.

## HOLD mapping (gate): DATA 5 (B02, H02, H05, H06, R23-ATLAS); THEORY 2 (K03, K04); REDEF 16 (B03–B05, H04, K05–K06, L03–L06, R23-CONGRUENCE, R23-SN, R26-CF4, V04–V06); PROC 6 (R25 ×4, R26 ×2). Owner decisions required: L03 (PR4 lane) and H04/V04 (public Pantheon+ parameters in place of the nominal SALT2 binding).

## Next primary RQ (cycle 2)

"Under a mock-derived correlated covariance for the CF4 window multipoles (exact H03/R32-05 operators), do the ΛCDM physical null (boost + bulk) and the ΛCDM tidal-shear distribution account for (D_w, Q_w)? If not, is the residual tied to the method footprints (H-1n) or depth-independent (physics)?" — ordered actions 1–8 in `review/DECISION_GATE.md` §3 (item 1 executed as T-12; item 5 partly done via T-11 archive).

## Reusable insights

- Sphere quadrature for magnitude-field multipoles needs Gauss–Legendre in cos θ (midpoint rule fakes remainder-bound violations).
- `H03_SOURCE_TOMOGRAPHY.json` stores the per-window 3×3 STF matrix and the 9×3 bulk-response design; the 36×36 covariance is ordered [H, D_x, D_y, D_z, STF5] per window; the saved R_w blocks are the window-weighted 1/d boost/bulk columns.
- Linear-theory kernels for the shell-averaged apparent quadrupole (T-05b: C_2 = f² (2/π) ∫ dk P(k) [∫ W(r) j_2'(kr)/r dr]²; ‖S‖_eq² = (15/8π)·5C_2) give the ΛCDM scale for any window; replace by mocks for inference.
- AniLoS convention facts (per-unit-IC normalization, single-m Bianchi frame, i^ℓ phase, fixed handedness, V as sqrth ≈ 1e5 limit, IX ℓ_max = 3) for any future BASS-vs-AniLoS comparison.

## Assumptions to discard

- "The constant rate dipole / calibration dipole measures A_a" (invalid for dust).
- "A nonradial law from astrometry can qualify S" (no sensitivity).
- "A free second-order moment class is physical" (degenerate with the CMB).
- "Agreement among CF4-based analyses is independent support" (same catalogue; only Pantheon+ and mocks are independent).

External memory: upload the updated `state/` files, `review/`, `validation/` and `RESEARCH_RUN_REPORT.md` to the project knowledge store; next cycle starts with `research-contract` (V-0(b) mock-covariance contract) or `research-run deep`.
