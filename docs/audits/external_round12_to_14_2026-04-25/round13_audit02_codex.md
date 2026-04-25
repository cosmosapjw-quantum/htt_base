# V5-RUNTIME Round-13 External Audit Verdict

**Auditor**: Codex external audit  
**Date**: 2026-04-25  
**Bundle SHA**: 0536f0e

## Verdict (one-line)
**PARTIALLY-CONFIRMED**

## Summary
Phase A convincingly shows that the current `N_k=12` audit is extremely low-k sensitive, but it does **not** prove that the low-k excess is only a quadrature artefact. Option A as "drop `k < 1e-3`" is not a valid physics fix for `D_2`; it removes the physical quadrupole/SW support. The strongest residual clue is not the sign of `Ψ`, but a likely normalization/source-sampling problem: `sqrt(32) = 5.66 = 4√2`.

## Step 1 — Phase A 진단 방법론 검증
**Q1.1 D5**: `projected_seed.amplitude ∝ k²` is real, but mostly irrelevant for the linear-probe path. `compute_flrw_d_ell_linear_probe` forces `unit_amplitude_normalization=False` and normalizes only by `probe_b_k_sq` in [flrw_pipeline.py](/home/cosmosapjw/Dropbox/bianchi/htt_base/htt/bass/spectrum/flrw_pipeline.py:1259). So D5 refutes a hidden division-by-seed-amplitude in this path, but it is not evidence that the transfer itself is correctly normalized.

**Q1.2 D1+D2**: D2 is mislabeled: the script prints a constraint-residual claim but never computes the residual. It only samples `sources.psi(eta)`. Also, `η_*` is effectively sampled at the first solver output point: transcript says `η_* = 260.1`, while Planck-2018 `η_*(z=1090.94) ≈ 280.14`; with `n_output=64` linear samples, recombination is not resolved. Thus D1 shows "no obvious `1/k²` blow-up in the exposed callable," not "constraint cancellation is clean."

The sign claim is also wrong. In CAMB/MB convention with `χ0=-1`, CAMB Notes give `Ψ = -10/(4Rν+15)` for the adiabatic mode, i.e. about `-0.601`, not `+0.6` ([CAMB Notes, eq. 9.9](https://cosmologist.info/notes/CAMB.pdf)). BASS `Ψ ≈ -0.34` has the expected sign but low magnitude.

**Q1.3 D3**: The sweep uses a new 12-point `logspace(k_min, 1e-1)` grid each time, not the same canonical grid with low-k points removed. Therefore the result proves low-k sensitivity, but not a clean "95% contribution" decomposition. Raising `k_min` also deletes the physical `ℓ=2` region: `k_peak ~ 2/(η0-η*) ≈ 1.4e-4`.

**Q1.4 D4**: The monkey patch is not a valid IMEX projection test. `ConstraintProjectionPolicy.every_n_steps` is passed into the runtime control block, but actual execution calls `integrator.run(checkpoint_every_n_steps=...)`; the constraint cadence is not used as an integration-time projection cadence. The bit-identical result therefore does not refute projection drift. It mostly shows the toggle is not wired into the solver loop.

## Step 2 — 32× 잔여 root cause 분석
**Q2.1**: BASS `psi` is intended to be the MB conformal-Newtonian time potential. MB define the conformal Newtonian metric with `ψ` in `g00` and `φ` in spatial curvature ([Ma & Bertschinger 1995, eq. 5](https://arxiv.org/pdf/astro-ph/9506072)); their anisotropic-stress relation is `k²(φ−ψ)=12πGa²(ρ+P)σ` ([eq. 23d](https://arxiv.org/pdf/astro-ph/9506072)). BASS reconstructs `psi = phi + stress` in [tier_b_source_extraction.py](/home/cosmosapjw/Dropbox/bianchi/htt_base/htt/bass/spectrum/tier_b_source_extraction.py:291), which is a sign-risk unless its PSTF `θ2` convention is opposite MB's.

**Q2.2**: The `0.34/0.60 ≈ 0.567` magnitude is not naturally `R_b` or `Rν/(1+Rν)`. It is almost exactly `4√2 / 10 = 0.5657`. With Planck `Rν≈0.40874`, CAMB predicts `10/(4Rν+15)=0.601`; BASS measures approximately `4√2/(4Rν+15)=0.340`. That is a strong fingerprint of a PSTF/spherical-harmonic normalization factor.

**Q2.3**: The high-k `α_meas/α_SW` blow-up does not by itself prove a bug because SW is invalid in the acoustic/Doppler regime. But BASS computes Doppler as `np.gradient(g*v_b, eta_grid)` on a very coarse linear grid in [flrw_bessel_projector.py](/home/cosmosapjw/Dropbox/bianchi/htt_base/htt/bass/los/flrw_bessel_projector.py:451). Seljak-Zaldarriaga explicitly require multiple samples across recombination and note visibility-derivative cancellation errors if undersampled ([1996, §3.4](https://arxiv.org/pdf/astro-ph/9603033)). This is a real suspect.

**Q2.4**: Quantitative factor match:
`16/3 = 5.33` weak; `(4Rν+15)/3 = 5.54` close; `4√2 = 5.657` exact for `sqrt(32)`. The best candidate is a missing/extra `4√2` transfer normalization, likely in PSTF tower slot → MB scalar multipole conversion or in the linear-probe calibration, not in `C_ℓ` assembly. The `C_ℓ = 4π∫P_R|Δ|²dlnk` and `D_ℓ` conversion look standard.

## Step 3 — Option A 검증
**Q3.1**: Pure `k_min` clipping is a numerical patch. CAMB does not discard super-horizon modes; it uses regular `kτ` initial-condition expansions and evolves stable synchronous variables ([CAMB Notes definitions and ICs](https://cosmologist.info/notes/CAMB.pdf)). A low-k analytic SW branch is acceptable only as a controlled continuation with no double counting.

**Q3.2**: Dense `N_k` is mandatory before accepting the artefact claim. Sparse `N_k=12` dependence is consistent with quadrature error, but also with a bad low-k source. Need fixed-grid refinement and `n_output` refinement.

**Q3.3**: Correct implementation is not `(a)` alone. Use `(c)` piecewise: numerical integration where the source is validated, analytic SW continuation below a documented switch, assembled in the quadrature layer so physical low-k power remains included.

**Q3.4**: `1e-3` is not physically justified for `D_2` clipping. Natural scales are `1/η*≈3.57e-3` for horizon-at-recombination and `ℓ/(η0−η*)≈1.4e-4` for quadrupole support. If using a super-horizon analytic switch, test `kη* < 0.1` to `0.3` (`~3.6e-4` to `1e-3`) with overlap convergence.

## Step 4 — 최종 판정 + Round-12 closure 권장
Do **not** close Round-12 with Option A as currently evidenced. Accept D3 only as "low-k localization." Before rollout, run one script with:

1. `n_output = 64, 256, 1024` temporal convergence.
2. SW/ISW/Doppler/polter component ablation.
3. `anisotropic_stress=True/False` and stress-sign flip.
4. apply trial `/ (4√2)` transfer normalization and check whether `32×` collapses.

## Step 5 — 교차 검증
**Q5.1**: Route-B Rust path should be unaffected by a Python wrapper kwarg. I confirmed `_d2_anchor_golden.json` records `1002.086744 μK²` as `bass_rs dump_dl_spectrum_sparse`, documented-only from Python. A cargo filter attempt built successfully but matched 0 tests in this tree, so I did not get a fresh binary D2 printout.

**Q5.2**: The 43 CAMB seed cross-checks should be unaffected if Option A defaults to `None` and does not touch seed formulas. Not verified by applying the patch.

**Q5.3**: The anchor is Rust-side, not Python PSTF-derived: `_d2_anchor_golden.json` says the Python-side golden is only the MM curve, while `1002.086744` is a Rust-side reference.

## Confidence and caveats
High confidence that pure clipping is not a valid `D_2` physics fix and that D4 is ineffective. Medium confidence that the residual `32×` is a `4√2` normalization issue, with Doppler/source time sampling as a second major suspect. Low confidence in any single-line fix until the component and temporal convergence diagnostics are run.
