# 07. Next Session Prompt — HyRec-Cov-RT

Continue implementing `HyRec-Cov-RT` from the frozen SSOT and document stack in this folder.

Required reading order before touching code:

1. `00_SSOT.md`
2. `01_SCOPE_AND_PHASE_MAP.md`
3. `03_DATA_MODEL_AND_APIS.md`
4. `04_NUMERICS_AND_SOLVER_LOOP.md`
5. `05_VALIDATION_SCOREBOARD.md`
6. `06_PHASED_PR_LIST.md`

Execution rules:

1. Treat `EMLA + S_N + short-characteristics + ALI` as the only authoritative production path.
2. Keep long-characteristics strictly in the reference namespace.
3. Do not introduce Teff-like reduced manifolds into the production solver.
4. Do not introduce silent FLRW, orthogonal, or zero-tilt fallbacks.
5. Update tests and the scoreboard in the same change set as any code modification.
6. Work on exactly the next unfinished phase item unless a document explicitly marks a parallel-safe branch.
7. If a required equation or interface is ambiguous, resolve the ambiguity by editing the SSOT or API document first, then code against that edit.
8. When a phase item lands, rewrite its scoreboard status and leave a clear delta note for the next session.

Immediate next target:

1. Start with Phase 1.1 if the subtree is empty.
2. Otherwise continue from the lowest-numbered unfinished phase in `06_PHASED_PR_LIST.md`.
