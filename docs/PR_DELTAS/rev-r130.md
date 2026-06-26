# REV-R130 - Hygiene: all 7 residual contract failures fixed (git_state content-addressing + manuscript relabel)

owner: COMMON
implementation_scope: common
claim_tier: diagnostic_only
transfer_source: none
git_commit_or_worktree_state: branch research/pr04-multicomponent

## Request

Finish the 7 residual hygiene contract failures (and all doable items).

## Root cause + fix

The 7 were **not** stale-content; they were structural:

1. **git_state churn (6 of 7).** Two generators embedded a HEAD-tracking
   `git_commit_or_worktree_state: <HEAD>+dirty` in their emitted artifacts, so any
   commit re-staled the file and cascaded into every downstream report/registry that
   hashes it. Fixed by switching the provenance to **content-addressed** (a fixed
   sentinel), keeping `config_hash` + `input_hashes` as the real provenance (the audit
   F2/F5 recommendation):
   - `scripts/make_current_manuscript_figures.py:_git_state` -> constant
     (fixes `current_science_plot_payload.json` -> cf4pp + current-figures cascade);
   - `scripts/generate_revision_experiment_assets.py:_git_state` -> constant
     (fixes `revision_experiment_assets.json` -> cf4pp).
   Then regenerated the affected artifacts and updated the hand-pinned hash registries
   (`pr_dag_research_program.yaml`, `research_program_experiment_registry.yaml`,
   `research_program_theorem_registry.yaml`) to the current content hashes.
2. **Manuscript pdf-lint (1 of 7).** The manuscript PDF still carried two phrases the
   rev-r119 claim firewall forbids: "EGS identity" and "cosmic-variance floor". Applied
   the same relabel the code/reports already use:
   - `docs/manuscript/appendices.tex`: "Quadrupole--filling EGS identity" ->
     "...EGS-type identity";
   - `docs/manuscript/ch07_results.tex`: "cosmic-variance floor" -> "cosmic-variance limit".
   Recompiled the manuscript (362 pp), refreshed
   `docs/generated/manuscript_pdf/htt_base_research_report.pdf` + the blessed
   `pdf_claim_lint_report.md` (now Failed 0, sha 66778a8), and the publication-claim-freeze.

Regenerated/rebuilt all downstream provenance artifacts (inventory, semantic-firewall,
code-capability, current figures, and every audit package + freeze).

## Result

`pytest tests/contracts/` = **348 passed, 0 failed** (was 8 failed at session start).
The figure claim-lane failure was fixed in rev-r128; the remaining 7 here.

## Claim discipline

The manuscript relabels remove forbidden overclaim phrasing (stronger firewall, not
weaker). Content-addressing keeps full provenance via config/input hashes. No
generated number changed; no claim-tier change.

## Validation

| Command | Status |
| --- | --- |
| `pytest tests/contracts/` | 348 passed, 0 failed |
| `pdf_claim_lint` (manuscript) | Failed 0 |
| `check_publication_claim_freeze` | passes |
| all audit packages `--check` | byte-deterministic |
