# Reproduce this convergence package

Run from the existing repository checkout. This package changes no live state.

```bash
python scripts/codex_harness/sync_pr_dag_mirrors.py --check
python scripts/codex_harness/validate_pr_dag.py docs/codex_handoff/pr_backlog.yaml --strict
python scripts/codex_harness/test_research_controller_convergence.py
python docs/research_program/observational_publication_20261015/CONVERGENCE_20261028/validation/check_convergence_package.py
bash docs/research_program/observational_publication_20261015/CONVERGENCE_20261028/baseline/BUILD_REPORT.sh /tmp/htt-convergence-report
```

The baseline uses Pandoc and XeLaTeX, with the six already-produced PDF figures. Its 10 pages were rendered and visually inspected. Rebuilding PDF/TeX may change timestamps/bytes; do not overwrite frozen source hashes or an appended frontier to hide such differences. The script requires a separate output directory and preserves the frozen baseline. Build in a task-owned output directory for later revisions and record their new identity. `BASELINE_REPORT.json` binds every displayed numeric result and figure to retained source files.

`imports/four_goals` and `imports/foundations` preserve original research bytes, including historical paths, receipts and output conventions. Those paths are evidence of the earlier run, not instructions to recreate scratch directories or rebind owner acquisition artifacts. Read the result/code pair before reuse; place new analyses and reports only under the relevant new task's owned product path. If a script contains an old output root, use a small explicit adapter in that product directory; do not rewrite or silently execute historical producer scripts against old outputs. Native Wolfram/xAct and historical tool statements remain attributed to their original receipts; this integration does not claim those engines were rerun.

The supplied user notes are at `imports/four_goals/sources/user_attachments/`. Raw observational files remain outside Git. Current qualification readers in `SOURCE_REUSE.json` must be checked at local uptake; a later qualified revision is consumed with its own source identity in the new product, without rewriting this historical manifest.

Static preflight validates 205 evidence files and the six small task source sets. It does not certify the live host, worker capabilities, current acquisition state or concurrent-review source traversal. The host performs live preflight and preserves all existing source seals, one-use allocations and active packets.
