# VER2 Carry-Forward Ledger

**Purpose**: explicit unresolved items and intentionally deferred work for the VER2 program.

## Open Items

| Date | Packet | Severity | Item | Why deferred | Reopen at |
|---|---|---|---|---|---|
| 2026-04-20 | SK-00 | P1 | `workspace/contracts` wrappers now accept `manifest`, but full manifest plumbing is not yet wired through all producers | barrier phase only; implementation belongs to later lane packets | `IM-03S3A`, `IM-04O`, `IM-05T`, `IM-06H`, `IM-07M` |
| 2026-04-20 | SK-00 | P1 | `docs/status_matrix.md` and `docs/claim_ledger.md` are stubs, not generated from live artifacts yet | generation logic belongs after more lanes become executable | `IM-08V`, `IM-09D-FIG`, `IM-10D-MAN` |
| 2026-04-20 | SK-00 | P2 | shared-schema barrier is frozen in `common.contracts`, but package-specific wrappers still contain legacy provenance fields alongside `manifest` | non-breaking migration chosen to avoid premature breakage | later wrapper-tightening packet under `C/O/H/M` |
| 2026-04-21 | SK-01C | P1 | `ClaimLedgerEntry` and `StatusSnapshotEntry` exist, but no packet generates live rows yet | skeleton phase only; generation belongs after executable artifacts exist | `IM-08V`, `IM-09D-FIG`, `IM-10D-MAN` |
| 2026-04-21 | SK-01C | P1 | `DepartureReport`, `FullCovMESReport`, and `MioCertificate` now expose `tsc_overlay_ref`, but no producer attaches a real overlay yet | attachment depends on `SK-05T` plus downstream O/M integration | `SK-05T`, `IM-04O`, `IM-07M` |
| 2026-04-21 | SK-01C | P2 | `AtlasEntryLite`, `DepartureReport`, and TSC overlay contracts are canonical, but producer-side adapters do not exist yet | this packet is contract-only by design | `SK-04O`, `IM-04O`, `IM-05T` |
| 2026-04-21 | SK-05T | P1 | TSC overlay builder and advisory adapters exist, but no BASS/HTT/MIO producer consumes or attaches them yet | cross-package wiring belongs to the downstream lane owners | `SK-06H`, `SK-07M`, `SK-09D`, `IM-04O`, `IM-05T`, `IM-06H`, `IM-07M` |
| 2026-04-21 | SK-05T | P1 | Common `SourceStatus` / `PropagationStatus` remain coarse base statuses; richer TSC semantics currently live in combined labels and caveat vocabulary | write scope excluded `htt/src/common/*`; local reconciliation chosen to avoid reopening shared schema during T-lane skeleton work | future `C/O/T` schema-tightening packet if later lanes prove a shared-enum upgrade is necessary |
| 2026-04-21 | SK-05T | P2 | No-overclaim registry is code-resident in `htt/tsc/audit/no_overclaim.py`, not yet mirrored into generated docs/claim ledgers | packet write scope stayed inside `htt/tsc/*` plus required ver2 ledgers; docs export belongs later | `SK-09D`, `IM-08V`, `IM-10D-MAN` |
| 2026-04-21 | SK-09D | P1 | `docs/manuscript/generated/*` and `docs/ver2_upgrade/generated/*` are wired as D-lane consumers, but `status_snapshot.json` and `claim_ledger.json` do not exist yet | live generated ledgers belong to validation/audit phase, not skeleton D-lane work | `IM-08V`, `IM-10D-MAN` |
| 2026-04-21 | SK-09D | P1 | `figures/paper/VER2_MANIFEST_INDEX.md` reports 83 legacy paper-figure bases and all are `blocked_no_manifest` | SK-09D installs the gate only; manifest-backed figure promotion belongs after validation artifacts exist | `IM-09D-FIG` |
| 2026-04-21 | SK-09D | P2 | TSC manuscript caveat snippets now have insertion points in `docs/manuscript/ch11_error_hierarchy.tex`, but no live overlay-derived wording is attached yet | real TSC advisory text depends on `SK-05T` / `IM-05T` artifact production | `IM-05T`, `IM-10D-MAN` |
| 2026-04-21 | SK-07M | P1 | MIO producers now emit manifest-backed production status, but no MIO artifact is `production_validated` yet | SK-07M is skeleton-only and intentionally stops at prerequisite/caveat plumbing rather than calibrated science promotion | `IM-07M`, `IM-08V` |
| 2026-04-21 | SK-07M | P1 | `mio.diagnostics.predictive_residuals` is a residual-atlas shell that packages caller-supplied summaries only; it does not yet generate residual maps from live model/data products | packet scope allowed the shell and manifest gate, not the full HTT/BASS-coupled residual pipeline | `IM-07M`, `IM-08V`, `IM-10D-MAN` |
| 2026-04-21 | SK-07M | P1 | Directional coherence, z-binned coherence, shear extraction, and FLRW tension now expose explicit covariance/atlas/null-mock gates, but the production-ready inputs themselves are still absent in the current workspace | exact calibrated covariance, sky-support, atlas, and null-ensemble producers live outside this packet or remain future executable work | `SK-04O`, `SK-06H`, `IM-04O`, `IM-07M`, `IM-08V` |
| 2026-04-21 | SK-07M | P2 | MIO certificates reserve `tsc_overlay_ref`, but no MIO producer attaches a live TSC overlay yet | real overlay attachment depends on downstream TSC artifact emission and later MIO/HTT integration | `IM-05T`, `IM-06H`, `IM-07M` |

## Closed Template

| Date closed | Original packet | Closing packet | Item |
|---|---|---|---|
| YYYY-MM-DD | <packet> | <packet> | <item> |
