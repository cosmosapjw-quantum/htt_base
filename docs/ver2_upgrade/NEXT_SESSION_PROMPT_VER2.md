# NEXT_SESSION_PROMPT_VER2

## 1. Read First

1. `docs/ver2_upgrade/VER2_SSoT_PARALLEL_EXECUTION_PLAN.md`
2. `docs/ver2_upgrade/VER2_PHASE_PROMPTS_01_SKELETON_PREIMPLANT.md`
3. `docs/ver2_upgrade/VER2_PHASE_PROMPTS_02_IMPLEMENTATION_FIGURES_MANUSCRIPT.md`
4. `docs/ver2_upgrade/VER2_EXECUTION_LEDGER.md`
5. `docs/ver2_upgrade/VER2_CARRY_FORWARD_LEDGER.md`
6. `docs/ver2_upgrade/audits/AUDIT_SK-00_2026-04-20.md`
7. `docs/ver2_upgrade/audits/AUDIT_SK-01C_2026-04-21.md`

## 2. Current State

- `SK-00` barrier docs, ledgers, audit note, and schema/owner drift tests are in place.
- Canonical shared schema now lives in `htt/src/common/contracts.py` and `htt/src/common/departure_contracts.py`.
- `workspace/contracts` wrappers accept a canonical `ArtifactManifest` hook and enforce owner consistency when manifest is present.
- Canonical VER2 contract coverage now includes `AtlasEntryLite`, `DepartureReport`, `FullCovMESReport`, `TscAdequacyOverlay`, `ClaimLedgerEntry`, and thin workspace aliases/hooks.
- Full manifest propagation is not yet wired through every producer. That is expected at this stage.

## 3. Next Recommended Packet

`SK-01C` is closed. Start the solver-independent shell packets now.

Prefer this order if the goal is to maximize solver-free progress:

1. `SK-05T`
2. `SK-06H`
3. `SK-07M`
4. `SK-09D`
5. only then `SK-01S1` -> `SK-02S2` -> `SK-03S3`

Parallel recommendation now:
- one thread: `SK-05T`
- one thread: `SK-06H`
- one thread: `SK-07M`
- one thread: `SK-09D`

Defer until solver surfaces exist:
- `SK-04O`
- `SK-08V`

## 4. Hard Reminders

- `docs/ver2_upgrade/*` is the only semantic SSOT.
- Do not widen write scopes.
- Do not redefine base enums or manifests outside `htt/src/common/*`.
- Do not let TSC own runtime allow/block.
- Do not merge MIO certificate semantics into HTT or BASS.
- Do not generate figures or manuscript claims from non-manifest artifacts.
