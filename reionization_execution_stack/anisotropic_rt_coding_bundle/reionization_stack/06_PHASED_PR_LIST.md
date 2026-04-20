# 06. Phased PR List — Anisotropic Reionization RT

## 0. Rule

1. Every item below is a PR-sized unit.
2. Each PR must update tests and the scoreboard in the same change set.
3. No PR may claim a later-phase milestone without updating the scoreboard line it satisfies.

## 1. Phase 1.* — Transport and chemistry backbone

1. Phase 1.1. Create repository subtree, freeze file layout, add SSOT headers, and create placeholder modules plus placeholder tests.
2. Phase 1.2. Implement `geometry_cov_rt` and `source_model_rt` with explicit geometry and source-state outputs.
3. Phase 1.3. Implement a minimal UV continuum slab solver with `S_N` and a small group grid.
4. Phase 1.4. Upgrade continuum UV transport to production short-characteristics on the authoritative data layout.
5. Phase 1.5. Add directional photon-budget accounting and cache explicit emitted/absorbed/escaped counters.
6. Phase 1.6. Implement hydrogen ionization and recombination-counter updates driven by transported rates.
7. Phase 1.7. Implement X-ray transport and kinetic-temperature updates.
8. Phase 1.8. Implement Lyα transport with ALI and expose convergence diagnostics.
9. Phase 1.9. Implement spin-temperature updates from transported Lyα and kinetic-temperature state.

## 2. Phase 2.* — Geometry-aware observables and branches

1. Phase 2.1. Implement geometry-aware `tau21` and `δT_b`.
2. Phase 2.2. Add orthogonal Bianchi production support and orthogonal-limit regressions.
3. Phase 2.3. Add tilted Bianchi support with explicit frame transforms and `v -> 0` regressions.
4. Phase 2.4. Add weakly inhomogeneous patch mode and lightcone caching.
5. Phase 2.5. Add long-characteristics reference snapshots and short-vs-long comparison reports.

## 3. Phase 3.* — Freeze and release gates

1. Phase 3.1. Freeze scoreboard thresholds, benchmark snapshots, and photon-conservation tolerances.
2. Phase 3.2. Add adversarial shadowing, counter-rotation, and low-illumination stress tests.
3. Phase 3.3. Freeze public APIs and prohibit silent barrier fallbacks.
4. Phase 3.4. Add cross-links from public APIs to the equations in `02_ARCHITECTURE_SPEC.md`.
5. Phase 3.5. Produce the first release-candidate branch with authoritative-path-only outputs.

## 4. PR template contract

1. PR title must start with the phase number.
2. PR body must contain `Scope`, `Changed files`, `Physics contract`, `Tests added`, `Scoreboard delta`, and `Out-of-scope`.
3. PR body must state whether it touches authoritative, reference, or diagnostic paths.
