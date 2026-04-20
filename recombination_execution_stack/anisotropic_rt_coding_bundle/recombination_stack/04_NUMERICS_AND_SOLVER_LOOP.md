# 04. Numerics and Solver Loop — HyRec-Cov-RT

## 0. Purpose

1. This file defines the update ordering, operator splitting, convergence contracts, and implementation pseudocode.

## 1. Authoritative outer loop

1. Build `GeometryState`.
2. Refresh continuum diagnostics if enabled.
3. Build hydrogen and helium line coefficients.
4. Execute short-characteristics sweeps for each key line.
5. Execute implicit frequency drift/diffusion solves.
6. Execute ALI iteration until source and population convergence.
7. Compress escape operators.
8. Build hydrogen interface system and solve it.
9. Build helium interface system and solve it.
10. Evaluate `rhs_xe`.
11. Evaluate `rhs_tm`.
12. Advance the history state.
13. Update visibility outputs.
14. Run diagnostics and scoreboard checks.

## 2. Splitting contract

1. Spatial-angle advection is solved by short-characteristics.
2. Frequency drift and diffusion are solved implicitly.
3. Source-function coupling is solved by ALI.
4. Interface-state systems are solved after the line update, not before it.
5. No PR may invert this order without a dedicated counterexample test.

## 3. ALI convergence contract

1. ALI convergence is tested on both source updates and selected population-sensitive moments.
2. The iteration must stop only when all required monitors pass.
3. A hard failure must be raised on maximum-iteration exhaustion.
4. A degraded-convergence flag may exist, but a production run with that flag may not be labeled authoritative.

## 4. Reference-path comparison contract

1. Selected snapshots must be re-solved by long-characteristics.
2. Short-characteristics and long-characteristics differences must be logged at the line-state level.
3. If the discrepancy exceeds the scoreboard tolerance, the production path is red.

## 5. Pseudocode

```text
state = initialize_history(config)

for step in history_grid:
    geom = build_geometry(state.background)

    cont = maybe_refresh_continuum(state, geom)

    h_line_coeff = hydrogen_coefficients(state, cont, geom)
    he_line_coeff = helium_coefficients(state, cont, geom)

    for line in key_lines:
        state.line[line] = shortchar_sweep(state.line[line], coeff[line], geom, line_grid)
        state.line[line] = solve_frequency_diffusion(state.line[line], coeff[line], geom, line_grid)

    state.line = ali_iterate(state.line, state.populations, coeff, geom, line_grid)

    escape_ops = compress_escape_ops(state.line, geom, line_grid)

    h_system = build_hydrogen_system(state, escape_ops, geom)
    h_if = solve_hydrogen_interface(h_system)

    he_system = build_helium_system(state, escape_ops, geom)
    he_if = solve_helium_interface(he_system)

    dxe = rhs_xe(state, h_if, he_if, escape_ops, geom)
    dTm = rhs_tm(state, h_if, he_if, escape_ops, geom)

    state = advance_history(state, dxe, dTm)
    state.visibility = update_visibility(state, geom)

    diagnostics = run_diagnostics(state, geom, escape_ops)
    scoreboard = update_scoreboard(state, diagnostics)
    assert_gate(scoreboard)
```

## 6. IMEX recommendation

1. Explicit treatment is allowed for slow history variables only if stiffness diagnostics remain green.
2. Implicit or semi-implicit treatment is required for frequency diffusion and any source iteration that destabilizes naive explicit updates.
3. A single global fully implicit solve is not required in phase 1.*, but the interfaces must not preclude it later.

## 7. Numerical guardrails

1. No NaN or Inf is allowed anywhere in authoritative state.
2. Interface populations must stay in admissible ranges or the step fails hard.
3. `x_e` must remain in its admissible physical interval or the step fails hard.
4. Negative optical depth increments are forbidden unless explicitly derived for a transformed variable with a test proving equivalence.
