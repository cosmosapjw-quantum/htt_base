# Validation record

Commands were run from `/home/cosmosapjw/Dropbox/bianchi/htt_base` on 2026-09-29 KST.

| Scope | Command/evidence | Result |
|---|---|---|
| F2 focused tests | `python -m pytest docs/research_program/typefree_loop2_closeout_20260928/tests -q` | 6 passed |
| Safe entrypoint | `python .../db/safe_append.py --self-check` | PASS; published gzip and SQLite identities recognized |
| Real 549 MB migration | `cuhg-telemetry run ... safe_append.py --source .../THEORY_INHERITANCE_LOOP2_FINAL.sqlite.gz ...` | integrity `ok`; 3 correction + 2 review rows; all pre-existing table row hashes preserved |
| DAG | `python scripts/codex_harness/validate_pr_dag.py docs/codex_handoff/pr_backlog.yaml` | OK, 211 cards |
| Progress | `python scripts/codex_harness/progress_report.py ...` | 157/211 (74.41%); weighted 80.08%; checkpoint not due |
| Dispositions | `python .../tools/validate_dispositions.py` | PASS, 57 unique entries |
| PR #469 run 1 | run 36444766290 attempt 1, job 109004064413 | FAIL at portable projection: `2dbe0061…`, 1222-byte preimage |
| PR #469 run 2 | same run/head attempt 2, job 109006235079 | PASS: two fresh processes both `8b0aadf1…`, 1221-byte preimage |
| Issue #448 rerun | run 33718012456 attempt 3, job 109007095833 | PASS on unchanged #444 head; runner assigned and 8 steps executed |

The FTS shadow-table `WITHOUT ROWID` behavior caused the first real migration
attempt to stop before emitting outputs. The repair removed the unjustified
`rowid` assumption; the successful rerun measured the source hash before and
after. This is a migration implementation failure/repair record, not a science
engine result.

The pre-existing dirty `docs/harness/VALIDATION_LEDGER.md` was not modified, so
the user's unrelated edit remains uncommitted and preserved. This file is the
task-local validation record.
