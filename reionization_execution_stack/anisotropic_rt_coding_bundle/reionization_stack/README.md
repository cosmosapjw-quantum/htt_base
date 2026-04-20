# Anisotropic Reionization RT Execution Stack

## 0. Purpose

1. This stack upgrades the self-contained anisotropic reionization design into an execution-ready document set for an LLM coding agent.

## 1. Canonical project sentence

1. Build an anisotropic / inhomogeneous reionization solver whose authoritative path is `S_N angular discretization + short-characteristics continuum transport + ALI for Lyα-heavy sectors + local chemistry + geometry-aware 21-cm brightness mapping`, while retaining a 21cmFAST-like workflow and using long-characteristics only as a validation path.

## 2. Scope

1. UV ionizing continuum transport.
2. X-ray heating transport.
3. Lyα pumping transport.
4. Local ionization and thermal chemistry.
5. Spin temperature update.
6. Geometry-aware `δT_b`.
7. Orthogonal and tilted Bianchi support.
8. Weakly inhomogeneous and patchy structures.
9. Lightcone-friendly workflow.

## 3. Non-goals

1. Pure excursion-set barrier as the production ionization kernel.
2. M1-only line-centered transport as the production path.
3. Teff-like reduced manifolds as the production solver.
4. Final survey likelihood and parameter inference.
5. Full polarization transport.

## 4. Coding order

1. Read `00_SSOT.md`.
2. Read `01_SCOPE_AND_PHASE_MAP.md`.
3. Freeze code-facing structures from `03_DATA_MODEL_AND_APIS.md`.
4. Implement the outer workflow from `04_NUMERICS_AND_SOLVER_LOOP.md`.
5. Obey the validation gates in `05_VALIDATION_SCOREBOARD.md`.
6. Execute PRs in `06_PHASED_PR_LIST.md` in order unless a document marks a branch parallel-safe.

## 5. Document catalogue

1. `00_SSOT.md` freezes solver identity, authoritative path, forbidden shortcuts, and workflow invariants.
2. `01_SCOPE_AND_PHASE_MAP.md` defines phase order and hard gates.
3. `02_ARCHITECTURE_SPEC.md` defines the self-contained transport, chemistry, and observable architecture.
4. `03_DATA_MODEL_AND_APIS.md` defines state layout and module contracts.
5. `04_NUMERICS_AND_SOLVER_LOOP.md` defines sweep order, operator splitting, and pseudocode.
6. `05_VALIDATION_SCOREBOARD.md` defines regression gates and scoreboard semantics.
7. `06_PHASED_PR_LIST.md` is the coding-agent-friendly backlog in phase-number form.
8. `07_NEXT_SESSION_PROMPT.md` is the direct handoff prompt.

## 6. Exit condition for the stack

1. A coding agent can begin implementing the reionization solver from these files alone without guessing module ownership, solver authority, or the transition from source fields to `δT_b`.
