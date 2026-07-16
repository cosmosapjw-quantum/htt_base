# Next Session Prompt

Continue from `/home/cosmosapjw/Dropbox/bianchi/htt_base` at PR-123. Read:

- `AGENTS.md`
- `.agents/skills/htt-dag-orchestrator/SKILL.md`
- `.agents/skills/htt-claim-firewall/SKILL.md`
- `.agents/skills/htt-claim-provenance-ledger/SKILL.md`
- `.agents/skills/htt-adversarial-review-loop/SKILL.md`
- `docs/PR_DELTAS/pr-122.md`
- `docs/research_program/long_horizon_rescue/pr122_spec.yaml`
- `docs/codex_handoff/research_remediation_state.yaml`
- `docs/codex_handoff/authorized_principals.yaml`
- `docs/research_program/LONG_HORIZON_RESCUE_PR_ROADMAP_20260714.md`
- `docs/audits/jcap_prd_adversarial_audit_20260714/criticism_response_matrix.json`

## Current state

- Active DAG: 113 total, 69 completed, 36 pending, 8 dormant external.
  Progress is 61.06% by count, 54.05% dependency weighted, and 48.21% on the
  current critical-path proxy. These are bookkeeping only.
- Exactly `PR-119..166` are active. `PR-167..183` are absent and remain owned
  by the later PR-167 intake.
- All 102 findings remain `OPEN`; rescued count is zero. Response dispositions
  are historical recommendations, not scientific status.
- PR-123 is the sole runnable next card.
- Checkpoint 065 is immutable. The next five-completion checkpoint is 70.

## PR-123 objective

Build independent small numerical references and a mutation laboratory for the
registered CF4, GRF, DESI, K6, ACT, and JWST defect classes. The K6 lane must be
catalog-independent and use analytic solid-body, potential, mixed Helmholtz,
and manufactured-boundary fields across at least four grids and two stencil
orders, with continuum extrapolation, boundary/interpolation/amplitude-gradient
decomposition, and the analytic `sqrt(2)` residual lock. Production and oracle
lineage must be distinct and recorded; a mechanics pass is not matched
data/null/covariance validation or cosmological inference.

Run the required four-role divergence, SPEC review, focused tests, claim scans,
adversarial review, commit, status receipt, and checkpoint 070 refresh.

## Persistent execution constraint

- PR3/FFP10 E2E download is complete.
- PR4/NPIPE is not downloaded.
- At PR-150, skip every PR4 download/reduction/data-analysis action. Emit a
  scope receipt only. Do not produce PR4 numbers or combined PR3+PR4 results.
- The original joint `roadmap_rescue_v1:C3` gate remains unavailable; the
  active PR-150 ceiling is PR3-conditional diagnostic
  `roadmap_rescue_v1:C2`.

## Hard boundaries

- Do not implement or simulate the external native low-ell solver.
- Do not relabel external/AniCLASS/proxy transfer output as native.
- Shape-only status records never unlock post-native work; exact
  `native_low_ell_delivery` scope, a hash-bound typed receipt, a registered
  independent provider, and an injected trusted verifier are required.
- Keep MIO diagnostics separate from HTT posterior/evidence semantics.
- Never infer scientific promotion from DAG completion or a terminal receipt.
- No family/geometry identification before native atlas plus matched
  mask/null/covariance/equivalence/rank/external gates.

## Immediate verification

```bash
venv/bin/python -B scripts/codex_harness/sync_pr_dag_mirrors.py --check
venv/bin/python -B scripts/codex_harness/validate_pr_dag.py docs/codex_handoff/pr_backlog.yaml --status docs/codex_handoff/pr_status.yaml --strict-rescue-slice
PYTHONPATH=htt/src venv/bin/python -B scripts/codex_harness/validate_research_remediation.py --check
venv/bin/python -B scripts/codex_harness/progress_report.py docs/codex_handoff/pr_backlog.yaml docs/codex_handoff/pr_status.yaml --checkpoint-every 5 --json
venv/bin/python -B scripts/audits/jcap_prd_20260714.py validate --final
```
