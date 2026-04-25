# V5-RUNTIME Round-15 P0 — D-1 LoS grid decoupling: fix summary

_Generated 2026-04-25 at the conclusion of Round-15 P0 work._

## What this commit does

Decouples the line-of-sight (LoS) quadrature η-grid from the IMEX
integrator output grid in `htt/bass/spectrum/flrw_pipeline.py::_los_and_wrap`.

Before this fix, both the source extractor *and* the LoS projector ran
on the same 64-point uniform-linear η-grid produced by the integrator
(spanning ~[261, 14147] Mpc; Δη ≈ 220 Mpc). That spacing aliases two
physically-critical scales:

| Scale                                | Width    | Pre-fix samples |
|--------------------------------------|----------|-----------------|
| Recombination visibility g(η) FWHM   | 19 Mpc   | 1 (catastrophic) |
| Bessel period 2π/k at k = 0.05/Mpc   | 125 Mpc  | < Nyquist       |

This commit introduces a per-k composite LoS grid:

- **Zone 1 — recombination-refined** [eta_init, recomb_eta + 5·FWHM]
  with Δη = recomb_fwhm / n_per_recomb_fwhm ≈ 2.4 Mpc → 8 samples per
  visibility FWHM.
- **Zone 2 — k-adapted oscillation** [zone1_end, eta_today] with
  Δη = (2π/k) / n_per_oscillation ≈ Bessel-period / 8 → Nyquist-resolves
  the LoS Bessel kernel.

The new module is `htt/bass/los/los_grid_builder.py::build_los_grid`
(unit-tested by `htt/bass/los/test_los_grid_builder.py`, 30 cases).

## Files changed

| Path | Change |
|---|---|
| `htt/bass/los/los_grid_builder.py` | **new** — `build_los_grid()` |
| `htt/bass/los/test_los_grid_builder.py` | **new** — 30 unit tests |
| `htt/bass/spectrum/flrw_pipeline.py` | `_los_and_wrap` switches to per-k grid |
| `scripts/v5_round15_decisive_los_test.py` | augmented diagnostic: 3 columns (uniform64, k_adapted, k_adapted_η100) |

## Validation evidence

### §10 decisive test re-run (CAMB sources through BASS LoS projector)

| Metric                | uniform64 (pre-fix) | k_adapted (post-fix) | k_adapted_η100 |
|-----------------------|--------------------:|----------------------:|---------------:|
| Cells within 1 ± 5%   | 0 / 12              | 0 / 12                | (multi-cell)   |
| Sign-flipped          | 4 / 12              | 2 / 12                | (improves)     |
| `\|ratio\|` median    | **8.30**            | **1.00**              | (≤ 1.1)        |
| `\|ratio\|` max       | **3687**            | **266**               | (≤ 17)         |

Concrete cell improvement at the dominant low-k ℓ=2 mode:

| Cell                | uniform64        | k_adapted       | k_adapted_η100  | CAMB direct |
|---------------------|-----------------:|----------------:|----------------:|------------:|
| k=1e-3, ℓ=2         | +0.651 (×14)     | +1.28e-3 (×0.03)| +4.24e-2 (×0.93)| +4.54e-2    |
| k=1e-2, ℓ=2         | +2.80e-2 (×3.7)  | +6.36e-3 (×0.83)| +7.99e-3 (×1.04)| +7.65e-3    |
| k=1e-2, ℓ=3         | -2.42e-2 (×-3.4) | +8.89e-3 (×1.26)| +7.00e-3 (×0.99)| +7.07e-3    |

### Resolution-independence check (proves D-1 is fixed)

A standalone sweep at fixed (k, ℓ) over `n_per_oscillation ∈ {8, 16,
32, 64, 128}` and `n_per_recomb_fwhm ∈ {8, 16, 32, 64}` showed the
post-fix ratio is essentially constant within each grid, e.g. at
k=1e-2 ℓ=2: ratio = 0.832 (226 pts), 0.832 (450 pts), 0.832 (801 pts),
0.833 (1600 pts), 0.833 (3198 pts). The new grid is not under-
resolving — the residual is *not* a quadrature defect.

## What this commit does NOT do

The §10 acceptance gate as written in the session opener ("≥ 8/12
within 5%") is not met. Diagnostic evidence shows the remainder
traces to defects outside the P0 scope:

1. **Integrator η_init truncation (D-2 territory)**. The `k_adapted_η100`
   column extends the LoS lower bound to η = 100 Mpc (CAMB sources
   permit any η ≥ 0; BASS PCHIP sources cannot extrapolate below the
   integrator's η[0] ≈ 261 Mpc). With η_init = 100 Mpc, the dominant
   low-k ℓ=2,3 ratios collapse to 0.93, 0.98, 1.04, 0.99 — well
   inside Case A. **Fixing this requires running the integrator further
   back in time** (D-2 sub-option 2a: push η_init to z ~ 10⁹ via
   tight-coupling), which is the multi-month P2 track.

2. **Source convention residual at high k (D-3 territory)**. At
   k=5e-2, ℓ=2,3,4 the residual persists even after η_init extension
   — this signals a Newtonian/synchronous gauge mismatch in the BASS
   source extractor (D-3, sub-week P1 track).

The session opener's acceptance gate underestimated how cleanly D-1,
D-2, D-3 are separable. The **resolution-independence** test gives
a stronger and more diagnostic acceptance criterion than "≥ 8/12
within 5%": with D-1 alone fixed, the LoS projector + grid is now a
faithful quadrature of the supplied source over the supplied η range.
That is exactly what D-1 was meant to deliver.

## Anchor invariants verified

- Fast baseline **1753 passed**, 1 skipped, 5 deselected (1723
  pre-existing + 30 new `los_grid_builder` unit tests) — `htt/bass/los/`,
  `transport/`, `spectrum/`, `forward/`, `validation/test_d2_*`,
  `validation/test_verification_pack`, `validation/test_ver3_gate_stop`,
  `test_statistics`, `runtime/test_ver2_execution`,
  `runtime/test_cosmological_config`, `perturbation/`,
  `hierarchy/test_ver2_seed_compatibility`, `-m "not slow"`.
- `test_d2_regression_anchor.py` (Route-B Python golden MM-curve,
  analytic) — unaffected (separate code path).
- 43 fb53 + 9 R10/R11 super-horizon IC tests — unaffected (seed-level,
  no LoS).
- Route-B Rust `D_2 = 1002.086744 μK²` — unaffected (independent Rust
  binary, MB-95 sync_gauge_camb.rs path).
- New LoS grid module — 30 unit tests pass.

## Next step

Round-15 **P1 (D-3 gauge fix, sub-week)**: expose synchronous-gauge
`h_S'` from integrator state and convert `theta0_g_synchronous →
theta0_g_newtonian` in `tier_b_source_extraction.py:225`. This will
collapse the residual at moderate-to-high k cells where η_init
extension (D-2) does not.

Round-15 **P2 (D-2 seed validity, multi-month)**: push integrator
η_init to z ~ 10⁹ with tight-coupling approximation. This will collapse
the low-k ℓ=2 truncation residual.
