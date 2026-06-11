# PR-000 Test Command Matrix

Generated: 2026-06-12T03:31:14+09:00

This matrix records command behavior for PR-000 intake only. It does not validate
scientific outputs, transfer functions, likelihoods, posteriors, MIO
certificates, or Bianchi family assignments.

## Artifact Metadata

| Field | Value |
| --- | --- |
| owner | COMMON |
| implementation_scope | pre_solver_repo_inventory |
| claim_tier | C0_inventory_only |
| transfer_source | none |
| config_hash | `b1d6e976d2e73a0ae0cf19f6f9fba56f0b79d141b3aef2c5f440820bf956562f` |
| input_hashes | `AGENTS.md=caf78d6d3cca82265b16553ef98c4d2065ace001e13e873b8f72c15d3f65453a`; `docs/codex_handoff/pr_backlog.yaml=c4546aa93fc58e61120ad725e126b6f4a047b5038689d9a7989a6073fe3c91ba`; `docs/codex_handoff/pr_status.yaml=7b3c25e11f50cf52e976ece1d96e37ca32e3f42f9e00055e5f31cbce44f8a2b1`; `htt/pyproject.toml=927ea6652b6a120126fea5f24f8280bdc45be0e77994fda8e08d33396febe6a0`; `htt/htt/setup.py=6894b4f948a8f1cc9218f922aeef6d36f1c072676469f8ae2be34e01a12440f3` |
| sky_support_status | not_applicable_to_command_matrix |
| null_mock_status | not_applicable_to_command_matrix |
| caveats | Inventory-only command matrix; no scientific result is generated or promoted. |
| generating_command | Codex apply_patch creation after running the commands listed below. |
| git_commit_or_worktree_state | `fd746ec31c5b51334c8b5e201d6bc40cd6322062` with preexisting dirty worktree plus PR-000 artifact edits. |

| Command | CWD | Interpreter | Purpose | Observed result | PR-000 interpretation |
| --- | --- | --- | --- | --- | --- |
| `python scripts/codex_harness/validate_pr_dag.py docs/codex_handoff/pr_backlog.yaml` | repo root | `/usr/bin/python` | Validate DAG before selecting PR-000 | exit 0; `OK: 62 PRs, DAG valid` | DAG can be followed in topological order. |
| `python scripts/codex_harness/progress_report.py docs/codex_handoff/pr_backlog.yaml docs/codex_handoff/pr_status.yaml` | repo root | `/usr/bin/python` | Establish baseline progress | exit 0; `Completed 0/62 = 0.0%`; unblocked next `PR-000` | PR-000 is first unblocked PR. |
| `python scripts/codex_harness/progress_report.py docs/codex_handoff/pr_backlog.yaml docs/codex_handoff/pr_status.yaml` | repo root | `/usr/bin/python` | Verify status after marking PR-000 complete | exit 0; `Completed 1/62 = 1.61%`; unblocked next `PR-001, PR-003` | PR-000 completion is reflected in the DAG status. |
| `python -m pytest --collect-only htt/htt/tests htt/src htt/tsc htt/workspace htt/mio -q` | repo root | `/usr/bin/python` | Required PR-000 collect-only command | exit 1; `/usr/bin/python: No module named pytest` | Environment prerequisite failure. Record exactly; stop non-harness PRs until packaging/interpreter stabilization. |
| `venv/bin/python -m pytest --collect-only htt/htt/tests htt/src htt/tsc htt/workspace htt/mio -q` | repo root | `venv/bin/python` | Same collection under available repo venv | exit 0; `1541 tests collected in 1.28s` | Repository target set is collectable under the venv; next harness PR should stabilize how this is invoked. |
| `python -m pip show pytest` | repo root | `/usr/bin/python` | Confirm literal command failure source | exit 1; `WARNING: Package(s) not found: pytest` | Confirms missing system-Python pytest. |
| `venv/bin/python -m pip show pytest` | repo root | `venv/bin/python` | Confirm venv test runner | exit 0; `Version: 9.0.3` | Venv has pytest. |
| `python scripts/codex_harness/new_pr_delta.py PR-000 --dry-run` | repo root | `/usr/bin/python` | Confirm delta scaffold script availability | exit 0; emits `docs/PR_DELTAS/PR-000.md` template | Script exists, but current DAG requires `docs/PR_DELTAS/pr-000-intake.md`; avoid overwriting legacy `pr-000.md`. |

## Optional Dependency Probe

| Module | `/usr/bin/python` | `venv/bin/python` | PR-000 impact |
| --- | --- | --- | --- |
| `numpy` | present | present | Available in both tested interpreters. |
| `scipy` | present | present | Available in both tested interpreters. |
| `pytest` | missing | present | Literal PR command fails; venv collection succeeds. |
| `emcee` | missing | present | Declared runtime dependency unavailable to system Python. |
| `healpy` | present | present | Available in both tested interpreters. |
| `dynesty` | missing | present | Environment fact only for PR-000. |
| `classy` | missing | present | Environment fact only for PR-000. |
| `astropy` | present | present | Available in both tested interpreters. |
| `getdist` | present | present | Available in both tested interpreters. |
| `cobaya` | present | present | Available in both tested interpreters. |
| `jax` | missing | missing | No collection impact observed for PR-000 targets. |
| `matplotlib` | present | present | Available in both tested interpreters. |
| `yaml` | present | present | Available in both tested interpreters. |

## Kill-Switch Note

The required command fails as written because system Python lacks `pytest`.
PR-000 records that failure and may close as an immutable intake snapshot, but
non-harness implementation PRs should not proceed until PR-001 or equivalent
packaging work stabilizes the interpreter/import path. Harness and packaging PRs
may proceed because they address this prerequisite directly.
