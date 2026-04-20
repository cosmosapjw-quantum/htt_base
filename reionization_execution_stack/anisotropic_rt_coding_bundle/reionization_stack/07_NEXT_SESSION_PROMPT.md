# 07. Next Session Prompt — Anisotropic Reionization RT

Continue implementing the anisotropic reionization solver from the frozen document stack in this folder.

Required reading order before touching code:

1. `00_SSOT.md`
2. `01_SCOPE_AND_PHASE_MAP.md`
3. `03_DATA_MODEL_AND_APIS.md`
4. `04_NUMERICS_AND_SOLVER_LOOP.md`
5. `05_VALIDATION_SCOREBOARD.md`
6. `06_PHASED_PR_LIST.md`

Execution rules:

1. Treat `S_N + short-characteristics + ALI + local chemistry + geometry-aware brightness` as the only authoritative production path.
2. Keep long-characteristics in the reference namespace only.
3. Do not reintroduce a scalar excursion-set barrier as the authoritative ionization kernel.
4. Do not demote photon-budget accounting to a post-hoc fit.
5. Update tests and the scoreboard in the same change set as any code modification.
6. Work on exactly the next unfinished phase item unless a document explicitly marks a parallel-safe branch.
7. If an ambiguity appears, edit the SSOT or API document first, then code against the edited contract.
8. When a phase item lands, update the scoreboard immediately and leave a delta note for the next session.

Immediate next target:

1. Start with Phase 1.1 if the subtree is empty.
2. Otherwise continue from the lowest-numbered unfinished phase in `06_PHASED_PR_LIST.md`.
