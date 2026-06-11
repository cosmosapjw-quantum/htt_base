# Blockers

Open blockers, owner, required resolution, and PR dependency impact.

## 2026-06-12

No active PR blockers after PR-011. Progress report shows unblocked next
candidates `PR-013`, `PR-014`, `PR-040`, `PR-012`, `PR-022`, and `PR-070`;
use DAG ordering and policy priorities before selecting the next node.

Residual non-blocking risk: `docs/generated/quarantined_figures.md` lists 96
existing figure/PDF assets without valid sidecar manifests. They are
diagnostic quarantine rows only and remain non-claim-bearing until future PRs
add valid provenance.
