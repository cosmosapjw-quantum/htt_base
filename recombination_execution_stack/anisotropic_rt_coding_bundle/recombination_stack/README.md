# HyRec-Cov-RT Execution Stack

## 0. Purpose

This stack upgrades the Teff-free recombination design into an execution-ready document set for an LLM coding agent.

## 1. Canonical project sentence

1. Build an anisotropic / inhomogeneous primordial recombination solver whose authoritative path is `EMLA + S_N angular discretization + short-characteristics line transport + ALI`, on a tetrad-based `1+3` covariant background, with long-characteristics retained only as a reference path.

## 2. Scope

1. Hydrogen recombination.
2. Helium recombination.
3. Matter temperature evolution.
4. Visibility / optical-depth history output.
5. Orthogonal and tilted Bianchi compatibility.
6. Weakly inhomogeneous extension path.
7. Deterministic line-centered radiative transfer.

## 3. Non-goals

1. Full polarization transport.
2. Final `a_lm` or `C_l` extraction.
3. General-purpose Monte Carlo transport.
4. M1 / FLD as an authoritative radiation closure.
5. Teff-like reduced manifolds as the production solver.

## 4. Coding order

1. Read `00_SSOT.md`.
2. Read `01_SCOPE_AND_PHASE_MAP.md`.
3. Implement against `03_DATA_MODEL_AND_APIS.md`.
4. Use `04_NUMERICS_AND_SOLVER_LOOP.md` as the algorithm contract.
5. Obey `05_VALIDATION_SCOREBOARD.md` before closing any PR.
6. Follow `06_PHASED_PR_LIST.md` strictly in order unless a document explicitly marks a parallel-safe branch.

## 5. Document catalogue

1. `00_SSOT.md` fixes notation, invariants, authoritative paths, frozen interfaces, and prohibited shortcuts.
2. `01_SCOPE_AND_PHASE_MAP.md` defines what this phase does and does not do, and how the phases depend on each other.
3. `02_ARCHITECTURE_SPEC.md` is the self-contained physics and software architecture reference.
4. `03_DATA_MODEL_AND_APIS.md` defines code-facing state structures and public module interfaces.
5. `04_NUMERICS_AND_SOLVER_LOOP.md` defines the update ordering, splitting, convergence logic, and pseudocode.
6. `05_VALIDATION_SCOREBOARD.md` defines the acceptance gates, scoreboard, and release freeze conditions.
7. `06_PHASED_PR_LIST.md` is the coding backlog in phase-numbered PR form.
8. `07_NEXT_SESSION_PROMPT.md` is the handoff prompt for the next implementation session.

## 6. Exit condition for the stack

1. A coding agent can open only these files and begin implementation without re-deriving conventions, file ownership, or the production-vs-diagnostic solver hierarchy.
