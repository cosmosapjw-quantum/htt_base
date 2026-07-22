# Run-directory retention policy (PR-124 preflight, 2026-07-17)

Governing verdict: `docs/audits/shared_context_cas_harness_final_audit_20260717/`
(§7 artifact retention). Raw generic review logs and duplicate result
envelopes are summarised, not versioned.

## Rules

1. **Historical runs (13 dirs through `post-pr123-paused-20260717`) stay
   git-tracked and frozen.** `scripts/codex_harness/run_pr123_oracle_lab.py`
   pins the sha256 of specific result files; do not edit or delete them.
   Each carries a `RUN_SUMMARY.json` with `disposition: historical_frozen`.
2. **Future runs are NOT committed by default.** `.gitignore` excludes
   `.agent-harness/runs/` going forward (tracked historical files are
   unaffected by ignore rules).
3. Close a run with
   `python3 .agent-harness/scripts/close_run.py --run-id <RUN_ID>`.
   Normal close first validates the run, then generates `RUN_SUMMARY.json`
   with `{path, sha256, bytes}` for every result plus the merged output, and
   finally clears the ignored local active-run pointer. It never deletes the
   run directory.
4. **Load-bearing artifacts are promoted individually**: claim-load-bearing
   CAS scripts/engine outputs, compiled proof receipts, decisive
   counterexamples, and final adjudications. Promote with
   `git add -f <path>` and append one JSON line to the tracked
   `RETENTION_LEDGER.jsonl`:
   `{"run_id": ..., "summary_sha256": ..., "promoted_paths": [...], "date": ...}`.
5. Result JSON must reference raw logs as `{path, sha256, bytes, producer,
   command_fingerprint}` instead of inlining them; routine results should
   stay under 64 KiB. Failed raw output keeps exactly one content-addressed
   blob (`.agent-harness/scripts/evidence_store.py`).
