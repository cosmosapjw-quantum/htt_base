# NEXT_SESSION_PROMPT_VER2

## 1. Read First

1. `docs/ver2_upgrade/VER2_SSoT_PARALLEL_EXECUTION_PLAN.md`
2. `docs/ver2_upgrade/VER2_PHASE_PROMPTS_01_SKELETON_PREIMPLANT.md`
3. `docs/ver2_upgrade/VER2_PHASE_PROMPTS_02_IMPLEMENTATION_FIGURES_MANUSCRIPT.md`
4. `docs/ver2_upgrade/VER2_EXECUTION_LEDGER.md`
5. `docs/ver2_upgrade/VER2_CARRY_FORWARD_LEDGER.md`
6. `docs/ver2_upgrade/VER2_PHASE_PLACEHOLDER_INDEX.md`
7. `docs/ver2_upgrade/audits/AUDIT_SK-00_2026-04-20.md`
8. `docs/ver2_upgrade/audits/AUDIT_SK-01C_2026-04-21.md`
9. `docs/ver2_upgrade/audits/AUDIT_SK-05T_2026-04-21.md`
10. `docs/ver2_upgrade/audits/AUDIT_SK-09D_2026-04-21.md`
11. `docs/ver2_upgrade/audits/AUDIT_SK-07M_2026-04-21.md`

## 2. Current State

- `SK-00` barrier docs, ledgers, audit note, and schema/owner drift tests are in place.
- Canonical shared schema now lives in `htt/src/common/contracts.py` and `htt/src/common/departure_contracts.py`.
- `workspace/contracts` wrappers accept a canonical `ArtifactManifest` hook and enforce owner consistency when manifest is present.
- Canonical VER2 contract coverage now includes `AtlasEntryLite`, `DepartureReport`, `FullCovMESReport`, `TscAdequacyOverlay`, `ClaimLedgerEntry`, and thin workspace aliases/hooks.
- `SK-05T` is now closed: `htt/tsc/*` contains domain-guard, no-overclaim, overlay-builder, advisory-adapter, and theorem-map skeletons backed by common manifests and TSC-owned reports.
- `SK-09D` is now closed: `scripts/ver2_artifact_export.py` generates placeholder D-lane outputs under `docs/ver2_upgrade/generated/*` and `docs/manuscript/generated/*`, and `figures/paper/VER2_MANIFEST_INDEX.md` now blocks legacy paper figures without manifests.
- The exporter currently reports `83` paper-figure bases and `83` missing manifests. That is the expected blocked skeleton state before `IM-09D-FIG`.
- `SK-07M` is now closed: touched MIO certificate producers attach VER2 manifest-backed production status, explicit covariance/atlas/null-mock caveats, and JSON-ready manifest payloads; `htt/mio/diagnostics/predictive_residuals.py` exists as a blocked residual-atlas shell.
- Targeted MIO verification is green: `venv/bin/python -m pytest htt/mio/tests -q` -> `153 passed`.
- Full manifest propagation is still not wired through every producer outside the M lane. That is expected at this stage.

## 3. Next Recommended Packet

`SK-01C`, `SK-05T`, `SK-07M`, and `SK-09D` are closed. Continue the remaining solver-independent shell packets now.

Prefer this order if the goal is to maximize solver-free progress:

1. `SK-06H`
2. only then `SK-01S1` -> `SK-02S2` -> `SK-03S3`

Parallel recommendation now:
- one thread: `SK-06H`

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
- Rerun `venv/bin/python scripts/ver2_artifact_export.py` after any D-lane change touching generated manuscript/export surfaces.
