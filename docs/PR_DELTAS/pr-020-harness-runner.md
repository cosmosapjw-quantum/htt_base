# PR-020 PR delta: harness runner for pytest subsets

## Goal

Implement the active `codex_handoff` PR-020: a deterministic Codex harness
runner for `collect`, `smoke`, `fast`, and `package` pytest subsets. This is
unrelated to the older PSTF scaffold file at `docs/PR_DELTAS/pr-020.md`.

This PR is COMMON L1 harness infrastructure only. It improves local command
dispatch and failure propagation; it does not change scientific code or validate
scientific readiness.

## Evidence read

- `AGENTS.md`
- `.agents/skills/htt-dag-orchestrator/SKILL.md`
- `.agents/skills/htt-harness-engineering/SKILL.md`
- `.agents/skills/htt-scientific-code-validation/SKILL.md`
- `.agents/skills/htt-claim-firewall/SKILL.md`
- `.agents/skills/htt-claim-provenance-ledger/SKILL.md`
- `.agents/skills/htt-adversarial-review-loop/SKILL.md`
- `docs/codex_handoff/pr_backlog.yaml` PR-020 card
- `docs/codex_handoff/pr_status.yaml`
- `pytest.ini`
- `htt/pytest.ini`
- `scripts/codex_harness/run_subset.py`
- `docs/PR_DELTAS/pr-020.md` to confirm old PSTF PR-name collision

## Web/doc checks

- WEB_CHECK_STATUS: done
- Python `argparse` documentation checked for CLI option parsing behavior.
  URL: https://docs.python.org/3/library/argparse.html
- Python `subprocess` documentation checked for child return-code behavior.
  URL: https://docs.python.org/3/library/subprocess.html
- Pytest marker documentation checked for `-m` marker selection behavior.
  URL: https://docs.pytest.org/en/stable/example/markers.html
- Pytest invocation documentation checked for `python -m pytest` semantics.
  URL: https://docs.pytest.org/en/stable/how-to/usage.html

## Subagent divergence

- code_cartographer:
  - Steelman: keep PR-020 to `run_subset.py`, `test_harness.md`, and
    `test_harness_runner.py`; no science packages or marker taxonomy rewrites.
  - Attack: the old generic subset names conflict with the active PR card, and
    hard-coded ambient `python` fails in this repo when the system interpreter
    lacks pytest.
- harness_engineer:
  - Steelman: expose exact dry-run commands and propagate child return codes.
  - Attack: hidden `PYTHONPATH`, broad catch-all suites, or swallowed failures
    would violate the PR kill switch.
- physics_stat_auditor:
  - Steelman: the runner can claim deterministic command dispatch only.
  - Attack: smoke, fast, collect, and package subsets are not scientific,
    solver, transfer, null, covariance, MIO, HTT, morphology, or
    family-identification evidence.
- claim_gate_reviewer:
  - Steelman: safe status language is `COMMON L1 harness infrastructure`.
  - Attack: avoid readiness/solver overclaims and old PSTF PR-020 language.
- regression_tester:
  - Steelman: test list, dry-run, unknown subset, child failure propagation,
    default venv interpreter selection, no hidden `PYTHONPATH`, and docs.
  - Attack: using only the PR-card dry-run commands would miss failure masking.

## Chosen plan

1. Write failing contract tests for the runner CLI.
2. Replace the minimal ambient-`python` command table with explicit subset
   definitions using `venv/bin/python` by default when present.
3. Add `--python` for explicit interpreter override in tests and debugging.
4. Print exact shell-quoted child commands for list and dry-run modes.
5. Run child commands from the repository root and return the child exit code.
6. Document supported subsets and scope caveats in
   `docs/codex_handoff/test_harness.md`.
7. Mark the active DAG PR-020 complete in both status files.
8. Add top-level `tests` to root pytest collection so the new contract suite is
   included by the `collect` subset.

## Files changed

- `scripts/codex_harness/run_subset.py`
- `tests/contracts/test_harness_runner.py`
- `pytest.ini`
- `docs/codex_handoff/test_harness.md`
- `docs/codex_handoff/pr_status.yaml`
- `machine_readable/pr_status.yaml`
- `docs/PR_DELTAS/pr-020-harness-runner.md`
- `docs/harness/VALIDATION_LEDGER.md`
- `docs/harness/PROJECT_STATE.md`
- `docs/harness/NEXT_SESSION_PROMPT.md`
- `docs/harness/BLOCKERS.md`

## Tests run

| Command | CWD | Result | Notes |
| --- | --- | --- | --- |
| `venv/bin/python -m pytest tests/contracts/test_harness_runner.py -q` before implementation | repo root | FAIL | Red phase: six expected failures for old subsets, missing `--python`, ambient interpreter use, and unknown-subset message. |
| `venv/bin/python -m pytest tests/contracts/test_harness_runner.py -q` before root collection fix | repo root | FAIL | Red phase: top-level `tests` was absent from root `pytest.ini` `testpaths`, so the contract suite was not covered by `collect`. |
| `venv/bin/python -m pytest tests/contracts/test_harness_runner.py -q` | repo root | PASS | `8 passed`; covers list, dry-run, package target, unknown subset, failure propagation, venv default, no hidden `PYTHONPATH`, docs, and root collect visibility. |
| `python scripts/codex_harness/run_subset.py --list` | repo root | PASS | Lists `collect`, `fast`, `package`, and `smoke` with exact commands. |
| `python scripts/codex_harness/run_subset.py collect --dry-run` | repo root | PASS | Prints venv-backed collection command. |
| `python scripts/codex_harness/run_subset.py smoke --dry-run` | repo root | PASS | Prints venv-backed smoke command without running it. |
| `python scripts/codex_harness/run_subset.py fast --dry-run` | repo root | PASS | Prints venv-backed fast marker command. |
| `python scripts/codex_harness/run_subset.py package --dry-run` | repo root | PASS | Prints `htt/test_packaging_imports.py` package smoke command. |
| `venv/bin/python -m pytest scripts/codex_harness/test_pytest_taxonomy.py -q` | repo root | PASS | `8 passed`; marker taxonomy remains compatible with runner commands. |
| `python scripts/codex_harness/validate_pr_dag.py docs/codex_handoff/pr_backlog.yaml` | repo root | PASS | `OK: 62 PRs, DAG valid`. |
| `env -u PYTHONPATH venv/bin/python -m py_compile scripts/codex_harness/run_subset.py` | repo root | PASS | Runner compiles with no `PYTHONPATH`. |
| `env -u PYTHONPATH venv/bin/python -m pytest --collect-only tests/contracts/test_harness_runner.py scripts/codex_harness/test_pytest_taxonomy.py -q` | repo root | PASS | `16 tests collected`. |
| `env -u PYTHONPATH venv/bin/python -m pytest tests/contracts/test_harness_runner.py scripts/codex_harness/test_pytest_taxonomy.py -q` | repo root | PASS | `16 passed`. |
| `env -u PYTHONPATH venv/bin/python scripts/codex_harness/run_subset.py collect` | repo root | PASS | `6785/6844 tests collected (59 deselected)`; includes top-level contract tests. |
| `env -u PYTHONPATH venv/bin/python scripts/codex_harness/run_subset.py smoke` | repo root | PASS | `6 passed, 6838 deselected`. |
| `env -u PYTHONPATH venv/bin/python scripts/codex_harness/run_subset.py fast` | repo root | PASS | `6 passed, 6838 deselected`. |
| `env -u PYTHONPATH venv/bin/python scripts/codex_harness/run_subset.py package` | repo root | PASS | `5 passed`. |
| `env -u PYTHONPATH venv/bin/python scripts/codex_harness/run_subset.py not-a-subset` | repo root | EXPECTED FAIL | Exit `2`; prints `unknown subset: not-a-subset` and does not run pytest. |
| `env -u PYTHONPATH venv/bin/python scripts/codex_harness/run_subset.py smoke --python /bin/false` | repo root | EXPECTED FAIL | Exit `1`; child return code propagates. |
| `python scripts/codex_harness/progress_report.py docs/codex_handoff/pr_backlog.yaml docs/codex_handoff/pr_status.yaml --checkpoint-every 5 --json` | repo root | PASS | After marking PR-020 complete: `7/62 = 11.29%`; checkpoint not due; unblocked next `PR-010`, `PR-021`. |
| `cmp -s docs/codex_handoff/pr_status.yaml machine_readable/pr_status.yaml; printf 'status_cmp=%s\n' "$?"` | repo root | PASS | `status_cmp=0`. |
| `python .agents/skills/htt-claim-provenance-ledger/scripts/check_forbidden_claims.py <PR-020 docs>` | repo root | PASS | No forbidden claim patterns detected. |
| `python .agents/skills/htt-claim-provenance-ledger/scripts/check_claim_status.py <PR-020 docs>` before wording fix | repo root | FAIL | Flagged a quoted overclaim term in the PR delta. |
| `python .agents/skills/htt-claim-provenance-ledger/scripts/check_claim_status.py <PR-020 docs>` | repo root | PASS | No unmarked strong claims detected after wording fix. |

## Review findings and fixes

- Finding: deleting/re-adding the runner changed its executable mode. Fix:
  restore executable mode because the previous script had it, even though docs
  invoke it through `python`.
- Finding: PR-020 name collides with older PSTF scaffold deltas. Fix: use
  `docs/PR_DELTAS/pr-020-harness-runner.md` and explicitly disambiguate active
  `codex_handoff` PR-020.
- Finding: list output changed from names only to names plus exact commands.
  Fix: document that behavior and test only the deterministic subset names plus
  absence of `PYTHONPATH` mutation.
- Finding: new top-level contract tests were not discoverable by the root
  `collect` subset. Fix: add `tests` to root `pytest.ini` `testpaths` and test
  that visibility explicitly.
- Finding: claim-status scan flagged a quoted overclaim term in reviewer-output
  prose. Fix: replace that quote with neutral readiness/solver-overclaim
  wording.
- Subagents used and closed: code cartographer, harness engineer,
  physics/statistics auditor, claim-gate reviewer, and regression tester.

## Claim hygiene and scientific scope

Numerical/scientific impact: none; harness runner only.

Artifact/claim-tier impact: COMMON L1 harness metadata. These subset commands
provide deterministic pytest dispatch and failure propagation only. They do not
validate native solver behavior, transfer calibration, HTT posterior/evidence,
MIO diagnostics, null/mask/covariance adequacy, morphology compatibility, rank
sufficiency, equivalence-class separation, or family-identification evidence.

## Residual risks

- The `fast` subset depends on tests being marked `fast`; it is a deterministic
  marker subset, not a comprehensive fast-suite guarantee.
- The `package` subset is intentionally narrow and only checks
  `htt/test_packaging_imports.py`.
