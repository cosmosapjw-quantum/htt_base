# Next Session Prompt — external re-audit handoff

Audit the existing candidate first; do not recreate it and do not start a new
planning successor.

## Exact checkout

- Repository: `cosmosapjw-quantum/htt_base`.
- Branch: `changeset/pr324-mes-methodology-stack-20260826`.
- Accepted integration start: `8b6028abcde18c87591789f6ba53e81157fa4eba`.
- Reviewed PR-327 candidate:
  `57c74157344c19b217b61c445f4d25c5f646cd18`.
- Reviewed tree: `9ab944440a57c66bb9cb5a56d331c757bbb483ec`.
- The branch tip also contains the status/handoff closeout for external review;
  resolve that exact tip with `git rev-parse HEAD HEAD^{tree}` after checkout.

## Audit boundary

- PR-322 through PR-327 are complete. PR-328 through PR-330 are pending and
  must not be inferred as executed.
- Primary PR-327 MES result: `98/301` (`14/43`).
- Frozen generic PR-314 benchmark control: `133/301` (`19/43`), not MES.
- Preserve the five exact PR-314 Git blobs and the SMICA-only exact-300 fast
  path. Commander and 999 CMB-only rows are not prerequisites.
- Directional state must remain `BLOCKED_DIRECTIONAL_SUPPORT`; Planck-only
  local/global state must remain `SINGLE_SHELL_LOCAL_GLOBAL_NONIDENTIFIED`.
- No legacy `planck_mes_bounds.py`, scalar-to-direction construction,
  source-only branch merge, PR close/merge, security expansion, native result,
  or family-identification claim is allowed.

## Minimum replay

```bash
PYTHONPATH=htt:htt/src:htt/htt python -m pytest -q \
  tests/integration/test_planck_mes_morphology.py \
  tests/obsstat/test_mes_row_anchor.py \
  tests/integration/test_planck_pr3_current_stack.py \
  tests/integration/test_planck_pr3_operator.py \
  tests/contracts/test_authorized_observational_program.py
python scripts/check_claim_language.py --strict-missing docs/PR_DELTAS/pr-327.md
python scripts/codex_harness/validate_pr_dag.py docs/codex_handoff/pr_backlog.yaml
git diff --check
```

The strict independent review result is
`.agent-harness/runs/pr327-final-review-20260826/results/PR327-FINAL-REVIEW.json`
(SHA-256
`5ad5047b97fad48293aa9fcfece8ac63b8b3b0a32f784c90ee11b7f807c1e190`).
It reports `P0=0`, `P1=0` for the reviewed scientific candidate.
The tracked cross-clone summary is
`docs/generated/planck_mes_morphology/external_reaudit_handoff.json`; external
reviewers must rerun the commands rather than treating that summary as an
acceptance vote.

Do not resume PR-328 until the human accepts the external re-audit. If resumed,
use the existing PR-328 card and preserve the current
`BLOCKED_FRAME_TRANSFORM_DERIVATION` receipt rather than guessing a physical
response.
