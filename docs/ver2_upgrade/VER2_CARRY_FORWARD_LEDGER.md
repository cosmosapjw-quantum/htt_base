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

## Closed Template

| Date closed | Original packet | Closing packet | Item |
|---|---|---|---|
| YYYY-MM-DD | <packet> | <packet> | <item> |
