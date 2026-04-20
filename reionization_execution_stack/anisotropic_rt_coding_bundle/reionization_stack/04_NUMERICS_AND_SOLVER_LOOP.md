# 04. Numerics and Solver Loop — Anisotropic Reionization RT

## 0. Purpose

1. This file fixes the authoritative update ordering and numerical contracts.

## 1. Authoritative outer loop

1. Build geometry.
2. Build source fields.
3. Sweep UV continuum transport.
4. Sweep X-ray continuum transport.
5. Solve Lyα transport with ALI.
6. Compress radiation states into ionization and heating rates.
7. Update ionization fractions and recombination counters.
8. Update kinetic temperature.
9. Update spin temperature.
10. Compute geometry-aware `δT_b`.
11. Compute photon-budget diagnostics.
12. Cache coeval and lightcone outputs.
13. Apply scoreboard gates.

## 2. Splitting contract

1. Continuum advection is solved by short-characteristics.
2. Lyα source coupling is solved by ALI.
3. Chemistry and thermal updates occur only after transport-rate compression.
4. Brightness temperature is always a post-chemistry observable layer.
5. Photon-budget diagnostics run after chemistry and before final cache freeze.

## 3. Retarded photon-budget contract

1. The authoritative photon-budget diagnostic is built from transported directional fluxes.
2. A scalar excursion-set barrier may be computed for comparison only.
3. Any production run that derives ionization directly from a scalar barrier is non-authoritative.

## 4. Pseudocode

```text
state = initialize_run(config)

for step in redshift_grid:
    geom = build_geometry(state.background)
    src = build_sources(state.halos, state.astro, geom)

    I_uv = solve_uv(state.I_uv, src, geom, uv_grid)
    I_x  = solve_xray(state.I_x, src, geom, x_grid)
    I_lya = solve_lya_ali(state.I_lya, src, geom, lya_grid)

    rates = compress_rates(I_uv, I_x, I_lya, state.chemistry, geom)

    state.chemistry = update_ionization(state.chemistry, rates, geom, dt)
    state.thermal = update_temperature(state.thermal, rates, geom, dt)
    state.spin = update_spin_temperature(state.spin, state.chemistry, state.thermal, I_lya, geom)

    state.brightness = compute_deltaTb(state.brightness, state.chemistry, state.thermal, state.spin, geom, observer_dirs)

    state.photon_budget = compute_photon_budget(src, I_uv, state.chemistry, geom, dt)

    scoreboard = update_scoreboard(state)
    assert_gate(scoreboard)

    cache_outputs(state)
```

## 5. Short-characteristics contract

1. Production transport uses upwind interpolation.
2. Cell optical-depth increments must be computed explicitly from geometry and chemistry state.
3. Sweep order must be stored and replayable for debugging.
4. No hidden interpolation stencil changes are allowed without a dedicated regression update.

## 6. ALI contract

1. Lyα ALI must track both source-function convergence and selected rate-sensitive observables.
2. The maximum-iteration cutoff is a hard failure for authoritative runs.
3. A degraded-convergence result may be emitted only as diagnostic output.

## 7. Numerical guardrails

1. No NaN or Inf is allowed in authoritative state.
2. Ionization fractions must remain in physical ranges or the step fails hard.
3. Negative photon-budget counters are forbidden unless they are explicitly signed residuals with a defined interpretation.
4. The geometry-aware line-of-sight expansion scalar used in `δT_b` must never cross zero silently; if it does, the code must route to a controlled branch or fail explicitly.
