# WEEK 10-01 PACKET — C_ℓ TT/EE/TE Assembly + Route B Sentinel

**Prompt ID**: W10-01
**Type**: SOLVER-IMPL
**Think**: T3 / Extended
**Depends**: W9-02
**Status**: COMPLETE — 63/63 tests green, 1,854/1,854 full regression, 14/14 independent verification

---

## §1. Scope and intent

Consume per-k `BianchiTransferFunctions` callables (W9-02 output or synthetic stubs), weight by the primordial scalar power spectrum `P_R(k)`, and integrate over log-k to produce `C_ℓ^{TT/EE/TE/BB}` angular power spectra. Convert to `D_ℓ = ℓ(ℓ+1) C_ℓ T_CMB² / (2π)` in μK² (Planck convention).

The module is a **consumer** — no scalar mode evolution solver lives here. `bass_py` W10-01 plays two roles:

1. The Route B Michaelis-Menten **lookup sentinel** (SSOT mirror of `bass_rs/d2_convention.rs`), with anti-regression guard
2. The C_ℓ assembly **infrastructure** (isotropic, Bianchi diagonal) that downstream tests consume

First-principles reproduction of `D_2 = 0.1741 μK²` at `Σ² = 1e-8` requires scalar mode evolution (`Θ_0`, `Ψ` solver), which is `bass_rs` scope. A scope-guard stub `full_scalar_mode_evolution` redirects accordingly.

## §2. Physics core

**Isotropic (FLRW) assembly**:
$$C_\ell^{TT} = 4\pi \int d(\ln k)\, P_R(k)\, |\Delta_\ell^{T,m=0}(k)|^2$$
$$C_\ell^{EE} = 4\pi \int d(\ln k)\, P_R(k)\, |\Delta_\ell^{E,m=0}(k)|^2$$
$$C_\ell^{TE} = 4\pi \int d(\ln k)\, P_R(k)\, \Delta_\ell^{T,m=0}(k)\, \Delta_\ell^{E,m=0}(k)$$

**Anisotropic (Bianchi I) diagonal — m-summation over {0, ±2}**:
$$C_\ell^{XY,\text{diag}} = 4\pi \sum_m \int d(\ln k)\, P_R(k)\, \Delta_\ell^{X,m}(k)\,\Delta_\ell^{Y,m*}(k)$$

For Bianchi I with real shear, all `Δ` are real, so `*` is trivial. Off-diagonal `C_{ℓm,ℓ'm'}` entries (BiPoSH) are `W11+` scope.

**Primordial power spectrum** (Planck 2018 baseline, with callable injection override):
$$P_R(k) = A_s\,(k/k_*)^{n_s - 1}, \quad A_s = 2.1\times 10^{-9}, \ n_s = 0.9649, \ k_* = 0.05\text{ Mpc}^{-1}$$

**D_ℓ conversion** (Planck convention):
$$D_\ell^{XY} = \frac{\ell(\ell+1)}{2\pi}\,C_\ell^{XY}\,T_{\rm CMB}^2, \quad T_{\rm CMB} = 2.7255\text{ K}$$

**Route B Michaelis-Menten sentinel**:
$$D_2(\Sigma^2) = \frac{C_1\,\Sigma^2}{1 + C_2\,\Sigma^2}, \quad C_1 = 1.753\times 10^7,\ C_2 = 6.825\times 10^5$$

`D_2(Σ² = 1e-8) = 0.174112...` μK² (bit-exact formula identity with `bass_rs/d2_convention.rs`).

## §3. Module architecture

`bass/spectrum/cl_assembly.py` — 837 lines, 11 sections:

1. SSOT constants (`ROUTE_B_C1`, `ROUTE_B_C2`, `ROUTE_B_D2_AT_SIGMA2_1EM8`)
2. Config (`CLAssemblyConfig` — frozen; defaults to Planck 2018 + 256-point log-k grid; Simpson requires odd grid)
3. Primordial power spectrum (`primordial_power_spectrum`; callable injection via `primordial_pk_fn`)
4. log-k quadrature helper (`_integrate_log_k` — trapezoid or Simpson)
5. Isotropic C_ℓ assembly (`assemble_cl_TT/EE/TE_isotropic`)
6. Anisotropic Bianchi I diagonal C_ℓ assembly (`assemble_cl_TT/EE/TE/BB_bianchi`; BB returns zeros)
7. D_ℓ conversion (`compute_dl`, with T_CMB in Kelvin; output μK²)
8. Route B lookup sentinel (`route_b_d2_lookup`, `assert_d2_anti_regression_vs_route_b`)
9. Michaelis-Menten fitter (`fit_michaelis_menten` via `scipy.optimize.curve_fit`; returns `{C1, C2, errs, covariance, residuals, rms}`)
10. Diagnostics (`sigma_squared_scan`, `high_ell_convergence_diagnostic`)
11. Sign/sanity assertions (`assert_cl_tt_positivity`, `assert_cl_ee_ell_lt_2_zero`, `assert_b_mode_cl_zero`)
12. Scope guards (5 stubs raising `OutOfScopeError`: BiPoSH, CAMB V-gate, scalar evolution, lensing, tensor modes)

## §4. Cross-check paths

**Path α (sentinel bit-exact formula identity)**: `route_b_d2_lookup(1e-8)` returns `0.174112 μK²` matching the literal arithmetic `1.753e7 × 1e-8 / (1 + 6.825e5 × 1e-8)` at machine precision (`diff == 0.0`, not "below rtol").

**Path β (FLRW recovery via diagonal = isotropic)**: Using a transfer function with `m=±2` channels identically zero, `assemble_cl_TT_bianchi` returns the same array as `assemble_cl_TT_isotropic` bit-exact. Verified at `max |diff| == 0.0`.

**Path γ (A_s linearity)**: Doubling `A_s` in the config doubles `C_ℓ^{TT}` at `max_rel < 1e-13` for ℓ ∈ [2, 10] (machine-precision linear weighting by P_R(k)).

**Path δ (D_ℓ conversion identity)**: For `C_ℓ = 1`, `D_2 = 2·3·T_CMB_μK²/(2π) = 7.0936 × 10¹² μK²`. Measured match with `rel_err == 0.0`. `T_CMB → 2·T_CMB` gives `D_ℓ × 4` at machine precision (quadratic scaling).

**Path ε (M-M fitter synthetic ground truth)**: Sample Route B formula at 8 logarithmically spaced σ² values, fit → `C1 rel_err = 2.13e-16`, `C2 rel_err = 0.00e+00` (exact floating-point recovery — the fit converges to the generating parameters because there's no noise and the function is well-conditioned in that σ² range).

**Path ζ (σ² ladder analytic)**: Decade ratio `D_2(σ²=1e-8) / D_2(σ²=1e-10)` = 99.328905, matching the exact formula prediction `(1e-8/(1+6.825e-3)) / (1e-10/(1+6.825e-5))` at `rel_err < 1e-10`.

## §5. Test inventory — 63 tests across 13 classes

| Class | Tests | Focus |
|---|---|---|
| TestCLAssemblyConfig | 7 | Validation, frozenness, Simpson-requires-odd, Planck defaults |
| TestPrimordialPowerSpectrum | 4 | Amplitude at pivot, log-log slope, A_s linearity, callable injection |
| TestIsotropicTT | 5 | Shape, positivity, zero-source, A_s linearity, const-Δ uniformity |
| TestIsotropicEE | 4 | Shape, Δ_E=0 zero, positivity, linearity in Δ_E² |
| TestIsotropicTE | 3 | Δ_E=0 zero, sign from product, product factorization |
| TestBianchiDiagonalTT | 5 | FLRW recovery bit-exact, m-sum, shape, zero-source, quadratic linearity |
| TestBianchiDiagonalEE | 3 | FLRW recovery, shape/positivity, ℓ<2 via bianchi sum |
| TestBianchiDiagonalTE | 2 | FLRW recovery, m-sum structure |
| TestBianchiDiagonalBB | 2 | Always-zero, assertion catches injection |
| TestDlConversion | 4 | Unit-Cℓ exact, ℓ=0 zero, T_CMB² scaling, linearity |
| TestRouteBSentinel | 7 | Formula identity, SSOT constants, anti-regression helper, vector, negative σ², zero σ² |
| TestMichaelisMentenFitter | 5 | Ground-truth recovery, Route B parameter recovery, validation, output structure |
| TestSigmaSquaredScan | 3 | Per-σ² returns, invalid which, BB path |
| TestHighEllConvergence | 2 | Plateau detection shape, convergence trend |
| TestScopeGuards | 5 | BiPoSH, CAMB V-gate, scalar evolution, lensing, tensor modes |
| TestEndToEndWithRealW902 | 2 | Real W9-02 propagator end-to-end, FLRW-iso bianchi-equals-iso |

Runtime: 4.03s isolated, 43.27s in full `bass/ + tsc/` regression (+12s over W9-02-only baseline).

## §6. Dependencies satisfied and downstream readiness

**Satisfied inputs** (all verified passing):
- W9-02: `BianchiTransferFunctions`, `matrix_propagator_m0_m2`, `BianchiSourceTerms`, `BianchiProjectorConfig`
- W9-01: `OutOfScopeError` (re-imported as the shared scope-guard exception)
- `bass.observational.planck_mes_bounds.T_CMB_K` (Fixsen 2009 canonical value)
- `scipy.integrate.simpson`, `scipy.optimize.curve_fit`, `numpy`

**Exports for downstream**:
- `route_b_d2_lookup(σ²)`: the production sentinel; call anywhere the Route B predicted `D_2` is needed
- `assert_d2_anti_regression_vs_route_b(computed, σ², rtol=0.005)`: the 0.5% guard floor for first-principles candidates
- `assemble_cl_TT/EE/TE_bianchi`: consumes W9-02, produces W10-02 V-gate input
- `compute_dl`: μK² output for direct comparison with Planck Commander reference values (`PlanckLowL_Commander` already defined in `bass.observational.planck_mes_bounds`)

## §7. Correction cycles

One (1) tolerance correction:
- `test_vectorized_input` initially asserted `|D_2(σ²=1e-10) - C1·σ²| / D_2 < 1e-6`. This was too tight — the `C2·σ²` correction at `σ²=1e-10` is `6.825e-5`, so the "linear limit" naturally has that level of deviation. Fix: compare to the exact formula vector instead of the naive linear approximation, and retain the `<1e-4` bound as a looser linear-regime check.

All other 62 tests passed on first run. Total dev cycles are lower than W9-01 (3 cycles) and equal to W9-02 (0 cycles for physics, 1 cycle for test tolerance) — the design pattern of delegating-to-W9-XX plus mocked-transfer testing held up well.

## §8. Scope declarations (what this module is NOT)

Five scope guards raise `OutOfScopeError` with explicit redirects:

- `off_diagonal_biposh` → W11+ (direction-dependent Wigner-3j weighting)
- `camb_v_gate_comparison` → W10-02 (real CAMB comparison)
- `full_scalar_mode_evolution` → bass_rs (Θ_0, Ψ solver — enables first-principles D_2)
- `lensing_cl` → future (unlensed → lensed mapping)
- `tensor_mode_contribution` → W11+ (primordial GW channel, distinct from Bianchi shear)

B-mode power: Bianchi I has `ψ' = 0` → `Δ_ℓ^{B,m} = 0` identically at the W9-02 projector level → `C_ℓ^{BB} = 0` identically at the W10-01 assembly level. This is encoded via `assemble_cl_BB_bianchi` returning zeros and `assert_b_mode_cl_zero` enforcing the floor. Not "in the future" — structurally absent.

Temperature evolution `(Θ_0(k, η), Ψ(k, η))` solver: out of scope by design. The module accepts any user-supplied transfer-function callable, so caller-side solvers (real bass_rs data, synthetic analytics, CAMB data table lookups) all compose cleanly.

## §9. Session statistics and production readiness

| Metric | Pre-W10-01 | Post-W10-01 |
|---|---|---|
| bass/ tests | 1,355 | 1,418 (1,355 + 63) |
| bass + tsc tests | 1,791 | 1,854 |
| Roadmap phase | W9 ✓ | W10 in progress (1 of 2) |
| spectrum/ subpackage | did not exist | 837-line module + 799-line tests |
| Independent verification | W8-03 + W9-01 + W9-02 blocks | + W10-01 8 blocks (14 checks) |

**Critical-path status**: W10-01 delivers the Route B sentinel + assembly infrastructure. **W10-02 (CAMB V-gate)** is the next blocker — compares `compute_dl` output on a chosen transfer function against CAMB reference spectra. `TestEndToEndWithRealW902::test_real_w902_produces_finite_cl` demonstrates the W9-02 → W10-01 pipeline end-to-end and is the fixture W10-02 will extend with real CAMB outputs.

First-principles `D_2 = 0.1741 μK²` reproduction at `Σ² = 1e-8` remains `bass_rs` scope (scalar mode evolution requirement). When that becomes available, `assert_d2_anti_regression_vs_route_b` is the comparison hook — no changes to W10-01 needed. The 0.5% tolerance matches the `d2_convention.rs` guard floor.

---

**Next**: W10-02 CAMB V-gate consumer. Depends W10-01 ✓. Requires real CAMB `D_ℓ` reference data for Planck 2018 ΛCDM baseline.
