# VER2 Phase Placeholder Index

**Authority**: `docs/ver2_upgrade/*`  
**Purpose**: D-lane skeleton map for audit placeholders, carry-forward reopen points, and manuscript/export insertion targets.

## Phase Matrix

| Phase | Skeleton anchor | Audit placeholder | Carry-forward reopen target | Manuscript/export target |
| --- | --- | --- | --- | --- |
| `VER2-V0` | `SK-00` | `audits/AUDIT_SK-00_2026-04-20.md` | already tracked in `VER2_CARRY_FORWARD_LEDGER.md` | schema barrier only; no manuscript promotion |
| `VER2-V1` | `SK-01S1` | open at first `V2-S1:` packet | reopen via `SK-01S1` / `IM-01S1` | no direct chapter text until executable outputs exist |
| `VER2-V2` | `SK-02S2` | open at first `V2-S2:` packet | reopen via `SK-02S2` / `IM-02S2` | source/propagation wording only after transport artifacts exist |
| `VER2-V3` | `SK-03S3` | open at first `V2-S3:` packet | reopen via `SK-03S3` / `IM-03S3A` | status snapshot and neutral-output wording |
| `VER2-V4` | `SK-04O` | open at first `V2-O1:` packet | reopen via `SK-04O` / `IM-04O` | result-pack A/C scaffolds |
| `VER2-V5` | `SK-05T` | open at first `V2-T1:` packet | reopen via `SK-05T` / `IM-05T` | TSC scope/source/channel snippets |
| `VER2-V6` | `SK-06H` | open at first `V2-H1:` packet | reopen via `SK-06H` / `IM-06H` | result-pack B and HTT claim-tier wording |
| `VER2-V7` | `SK-07M` | open at first `V2-M1:` packet | reopen via `SK-07M` / `IM-07M` | result-pack D and MIO wording fence |
| `VER2-V8` | `SK-08V` | open at first `V2-V1:` packet | reopen via `SK-08V` / `IM-08V` | shared `status_snapshot.json`, `claim_ledger.json`, theorem-to-test registry |
| `VER2-V9` | `SK-09D` | `audits/AUDIT_SK-09D_2026-04-21.md` | figures/exports landed via `IM-09D-FIG`; reopen via `IM-10D-MAN` for chapter wording only | `docs/manuscript/generated/*`, `figures/paper/VER2_MANIFEST_INDEX.md`, `docs/ver2_upgrade/generated/*` |

## Notes

- `SK-09D` installed the placeholder manuscript/export surfaces; `IM-09D-FIG` has now replaced those placeholders with live manifest-backed exports while leaving chapter prose upgrades to the next packet.
- `IM-08V` is the first phase allowed to emit the live `status_snapshot.json` and `claim_ledger.json` artifacts consumed by the D-lane skeleton.
- `IM-09D-FIG` has replaced the blocked D-lane placeholders with manifest-backed result-pack exports and generated figures.
- `IM-10D-MAN` still needs to upgrade manuscript wording, chapter insertions, and figure/table references against those claim-tiered exports.
