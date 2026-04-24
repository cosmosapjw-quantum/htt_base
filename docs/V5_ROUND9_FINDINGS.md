# V5-RUNTIME Round-9 Findings

_Round-9 ran R9-A (D_ℓ linear-probe wrapper) + R9-B (convention audit)
on top of `ac48319` (Round-8 single-k linear probe). Date: 2026-04-24.
This document captures the audit numbers and what they tell us about
the open B_K² ↔ ζ² calibration._

## 1. R9-A: `compute_flrw_d_ell_linear_probe` wrapper

Lives in `htt/bass/spectrum/flrw_pipeline.py`. Reuses
`compute_transfer_function_grid(..., bias_subtraction=True)` to dispatch
`2 × N_k` parallel solver runs (bias `b_k_sq=0` + target
`b_k_sq=probe_b_k_sq` per k), then divides each bias-subtracted
transfer function by `probe_b_k_sq` to extract α(k) and pairs α(k) with
the standard Planck-2018 P_R(k) in `assemble_cl_TT_isotropic` /
`assemble_cl_EE_isotropic` + `compute_dl`.

Wall time: `ceil(2·N_k / n_workers) × ~45 s`. For N_k=12 with 8
workers (24 tasks → 3 rounds): **82 s measured**.

### R9-A fix to `unit_amplitude_normalization`

The wrapper forces `unit_amplitude_normalization=False` because the
default `True` divides each Δ by the seed amplitude
`max(|Σ_±|, 1e-6) = 1e-6` for FLRW (Σ_± = 0). That floor — which has
nothing to do with the primordial amplitude — multiplies α by ~1e+6
and |α|² by 1e+12, and lands D_2 at ~10^17 instead of ~10^3 even after
bias subtraction. The linear-probe path's explicit
`/ probe_b_k_sq` division IS the natural normalization, so the
seed-amp-floor division is redundant + corrupting and is disabled.

## 2. R9-B: convention audit results

Setup: `compute_flrw_d_ell_linear_probe` at probe_b_k_sq=1.0, k-grid
log-spaced over `[1e-4, 1e-1] Mpc⁻¹`, Planck-2018 species,
A_s=2.1e-9 / n_s=0.9649 / k_pivot=0.05 (CLAssemblyConfig defaults).

**Reference**: Route-B `D_2 = 1002.086744 μK²`
(Rust binary `dump_dl_spectrum_sparse` MB-95 production path; ~0.17%
below CAMB-1.6.6 Planck-2018 unlensed FLRW τ=0).

| Setup | N_k | probe | unit_amp_norm | D_2 [μK²] | Ratio | conv_factor √(1/r) |
|---|---|---|---|---|---|---|
| Pre-fix | 6 | 1.0 | True (bug) | 1.008e+67 | 1.006e+64 | 9.97e-33 |
| Pre-fix | 4 | 1.0 | True (bug) | 1.669e+67 | 1.666e+64 | 7.75e-33 |
| Post-fix | 4 | 1.0 | False | 2.934e+07 | 2.928e+04 | 5.84e-03 |
| Post-fix | 4 | 0.01 | False | 5.618e+07 | 5.606e+04 | 4.22e-03 |
| Post-fix | 12 | 1.0 | False | 1.706e+07 | 1.703e+04 | 7.66e-03 |
| Post-fix | 24 | 1.0 | False | 1.358e+07 | 1.356e+04 | 8.59e-03 |

### Key observations

1. **The unit-amplitude-normalization bug accounts for ~10^60 of the
   raw 10^64 mismatch.** Disabling it brings D_2 from 10^67 to 10^7 —
   a factor 10^60 closer to Route-B (10^3).

2. **The residual 10^4 ratio is NOT a clean k-independent constant.**
   - Doubling N_k (4 → 12) shifts the ratio by ~0.6× (2.9e+4 → 1.7e+4)
   - Probe amplitude 1.0 vs 0.01 shifts the ratio by ~2× (2.9e+4 → 5.6e+4)
   - Both indicate that quadrature error + residual nonlinearity in the
     "linear regime" still contaminate the audit at the precisions
     measured.

3. **Per-k α(k) is dominated by the super-horizon k=1e-4 spike**:
   `α(k=1e-4, ℓ=2) ≈ -10` (probe=1.0) versus `≈ -0.18` for k=5e-2 and
   `+0.47` for k=1e-1. The Doppler-peak region `k ≈ 0.07` is barely
   sampled by the audit grid; its under-coverage probably accounts for
   a large part of the remaining factor.

4. **Linearity check (probe sensitivity)**:
   ```
   α(p=1.00, k=1e-4, ℓ=2) = -10.45
   α(p=0.01, k=1e-4, ℓ=2) = -14.47
   ```
   A ~40% gap — bigger than the Round-8 ℓ=2 / k=1e-3 sweep predicted.
   The seed formula's quadratic B_K² correction inside `eta_cov` is
   too small (~1e-5) to explain this; the residual is presumably from
   IMEX coupling effects during evolution that Round-8's single-k
   sweep at k=1e-3 didn't reach.

### Bottom line for R9-B

The R9-B working hypothesis (that B_K² ↔ ζ² is a clean k-independent
constant — option (3) in the session opener) is **not yet
empirically established**. The data are consistent with a
quadrature-converging value somewhere in `[5e-3, 1e-2]`, but more
density (N_k ~ 50) at densely-sampled k bands AND deeper sub-horizon
linearity diagnostics are needed before baking a number in.

## 3. R9-C: deferred calibration apply

`compute_flrw_d_ell_linear_probe` exposes a `calibration_factor=1.0`
kwarg that multiplies α(k) post-extraction (so D_ℓ scales as the
square — confirmed by `test_d_ell_linear_probe_calibration_factor_scales_quadratically`).

**No default value is baked** because:
- The empirical ratio is N_k-dependent (Section 2, point 2).
- A premature default risks freezing in a quadrature artefact that
  later N_k = 50 audits would reveal as wrong.
- Downstream code that calls this wrapper at the canonical Planck-2018
  amplitude can pass an explicit `calibration_factor` once the value
  has converged.

## 4. R9-D (next): exact convention closure

To close the convention, future work should:

1. Run the audit at **N_k ≥ 50** with log-spacing biased toward the
   Doppler peak `k ∈ [0.01, 0.1]` to reduce quadrature contamination
   to <1%.
2. Add a **2-point linearity diagnostic at every k** (probe at 0.01
   AND 1.0) and compare α(k); if the gap is k-dependent it indicates
   genuine nonlinear contamination at large k·η_init that should be
   addressed at the seed level.
3. Compare to `bass/perturbation/regular_adiabatic_ic.py::_seed_formulae`
   reference: cross-check `B_K_sq` interpretation against
   Lowell §13.2 paragraphs and CAMB's `inifile_read.f90`
   `As`/`pivot_scalar` parameters. The variable `B_K_sq` in the
   docstring claims to be "primordial amplitude squared" but the
   formula treats it linearly (eta_cov = 2·B_K_sq); this naming may
   itself be the convention bug.

## 5. R9-D code archaeology (in-session 2026-04-24)

Tracing the seed→integrator wiring in
`htt/bass/hierarchy/ver2_native_integrator.py::_build_seeded_initial_state`
(lines 1581-1681) reveals that **the metric perturbation `eta_cov` is
not part of the integrator state vector** — only `photon_T`,
`photon_E`, and `neutrino_reduced` are installed into the runtime IC
(lines 1645-1650). `eta_cov`, `delta_b`, `theta_b`, `delta_c`,
`theta_c`, `Z` are unpacked into `matter_seed_observables` (metadata
dict, lines 1671-1680) and not evolved.

So the seed amplitude `B_K_sq` enters the integrator ONLY via the
photon hierarchy slots set in
`pack_regular_adiabatic_seed_from_formulae` (lines 211-214 of
`regular_adiabatic_ic.py`):

- `photon_T[ℓ=0, m=0] = δ_γ/4 = (B_K_sq/12)·x²`
- `photon_T[ℓ=1, m=0] = θ_γ = (B_K_sq/27)·x³`
- `photon_T[ℓ=2, m=0] = π_γ ∝ k·τ_c·θ_γ`
- `photon_E[ℓ=2, m=0] = π_γ/4`
- `neutrino_reduced[0] = δ_ν = δ_γ`
- `neutrino_reduced[1] = θ_ν = (B_K_sq/27)·((4R_ν+23)/denom)·x³`
- `neutrino_reduced[2] = π_ν = -(4/(3·denom))·x²` (B_K_sq INDEPENDENT)
- `neutrino_reduced[3] = G_3 = -(4/(21·denom))·x³` (B_K_sq INDEPENDENT)

The amplitude-independent neutrino quadrupole + octupole are the
mathematical origin of the Round-6/8 visibility-source bias floor:
even at `b_k_sq = 0` the ν tower carries non-zero
`π_ν = -4·x²/(3·denom)` and `G_3 = -4·x³/(21·denom)`, which propagate
through the Boltzmann hierarchy and produce a constant
`Δ_T ≈ -3.34e-3` regardless of seed amplitude. This is by design (the
Lowell-§13.2 leading-order formulas were derived with these set as
constants) but it is *the* reason `compute_linear_probe_transfer_function`
needs the explicit bias subtraction step.

**Convention implication for the missing factor of ~10⁴ in
`D_2_probe / D_2_RouteB`**: with `B_K_sq = 1.0` the photon δ_γ
initial value at `(k=1e-4, η_init=261)` is `(1.0/3)·(0.0261)² ≈
2.27e-4`. The Planck-2018 physical equivalent at `ζ ≈ 4.6e-5` would
be `(4.6e-5/3)·(0.0261)² ≈ 1.04e-8`. The probe injects perturbations
that are `~2.18e+4` times larger than the physical seed. Squared,
this gives `~4.75e+8` — an order of magnitude *larger* than the
empirical ratio `1.7e+4`. So either (a) the IMEX evolution damps the
super-horizon mode by ~10² before recombination, or (b) the LoS
projector / visibility weighting absorbs the rest. Disambiguation is
beyond what code reading alone can resolve; needs a single-k
diagnostic that compares Δ at the end of evolution against the
predicted T(k)·ζ.

## 6. R9-D residuals deferred

The N_k = 24 dense audit (added 2026-04-24) extends the convergence
trajectory: ratios 2.93e+4 → 1.70e+4 → 1.36e+4 as N_k 4 → 12 → 24,
with conv factor 5.84e-3 → 7.66e-3 → 8.59e-3. The trajectory is slowly
decreasing but the ratio has not stabilized — every doubling of N_k
shifts the answer by ~25-40%. The dominant contribution is the
super-horizon spike at k = 1e-4 (`α[ℓ=2] ≈ -10.45`, vs |α| ≲ 1.3 at
sub-horizon k); as more k-points sample around it, the trapezoid
weight on that spike falls and the ratio compresses.

The above code archaeology (Section 5) resolves the *mechanism* (eta_cov
is metadata; only photon ℓ≤2 + ν reduced moments matter; ν π/G_3 floor
explains bias) but does not pin a single calibration factor. True
closure requires either:
- a forward derivation of the IMEX → LoS damping factor between seed
  amplitude and `Δ_T(η_today)`, or
- a **per-k diagnostic** that compares Δ at the end of evolution
  against an analytically-predicted T(k)·ζ at a single k, isolated
  from the sum over k in the C_ℓ assembly. This bypasses the
  N_k-dependent quadrature artefact entirely.

Both are punted to a follow-up Round-10. The empirical "throw N_k at
it" path (point 1 in Section 4) appears to converge slowly enough
that the per-k diagnostic is the more productive next step.

## 5. Files touched

- `htt/bass/spectrum/flrw_pipeline.py` — added
  `compute_flrw_d_ell_linear_probe`, `_scale_transfer_function`
- `htt/bass/spectrum/test_flrw_pipeline.py` — added 4 tests (2 fast
  validation + 2 slow integration)
- `scripts/v5_round9_convention_audit.py` — R9-B audit script
- `docs/V5_ROUND9_FINDINGS.md` — this file
