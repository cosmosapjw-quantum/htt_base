# 06. Phased PR List — HyRec-Cov-RT

## 0. Rule

1. Every item below is a coding-agent-friendly PR unit.
2. Each PR must update tests and the scoreboard in the same change set.
3. No PR may claim completion of a later phase requirement early unless the scoreboard line for that requirement is updated.

## 1. Phase 1.* — Foundation

1. Phase 1.1. Create repository subtree, freeze file layout, add SSOT file headers, add placeholder modules and placeholder tests.
2. Phase 1.2. Implement `geometry_cov_rt.build_geometry`, tetrad construction, kinematic fields, and frame-labeled geometry diagnostics.
3. Phase 1.3. Implement hydrogen interface-state data structures, effective-rate containers, and hydrogen linear-system assembly with FLRW-compatible inputs.
4. Phase 1.4. Implement a single-line toy transport solver on a fixed slab with `S_N` angular quadrature and a minimal line grid.
5. Phase 1.5. Upgrade the toy line solver to production-style short-characteristics sweeps on the authoritative data layout.
6. Phase 1.6. Add `reference_longchar.solve_snapshot` and the first short-vs-long snapshot comparison harness.
7. Phase 1.7. Add implicit frequency drift/diffusion support and the first ALI loop for a single line.
8. Phase 1.8. Couple hydrogen EMLA to the authoritative line solver and freeze the first hydrogen-only history path.

## 2. Phase 2.* — Full recombination backbone

1. Phase 2.1. Add helium interface-state systems, H-continuum-opacity hooks, and helium effective-rate compression.
2. Phase 2.2. Add `history_cov_rt` orchestration, `rhs_xe`, `rhs_tm`, and visibility output.
3. Phase 2.3. Add orthogonal Bianchi production support and orthogonal-limit regression tests.
4. Phase 2.4. Add tilted Bianchi support, explicit baryon-vs-normal frame transforms, and `v -> 0` regression tests.
5. Phase 2.5. Add weakly inhomogeneous patch mode and patch-level asymmetry diagnostics.

## 3. Phase 3.* — Freeze and release gates

1. Phase 3.1. Freeze the regression matrix, snapshot set, and scoreboard thresholds.
2. Phase 3.2. Add adversarial NaN/Inf, negative-population, and invalid-frame stress tests.
3. Phase 3.3. Freeze public APIs and reject all silent fallback branches.
4. Phase 3.4. Add documentation cross-links from every public API to the governing equations in `02_ARCHITECTURE_SPEC.md`.
5. Phase 3.5. Produce the first release-candidate branch with authoritative-path-only outputs.

## 4. PR template contract

1. PR title must start with the phase number.
2. PR body must contain `Scope`, `Changed files`, `Physics contract`, `Tests added`, `Scoreboard delta`, and `Out-of-scope`.
3. PR body must state whether it touches authoritative, reference, or diagnostic paths.
