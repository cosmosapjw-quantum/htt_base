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

## Closed Template

| Date closed | Original packet | Closing packet | Item |
|---|---|---|---|
| YYYY-MM-DD | <packet> | <packet> | <item> |
