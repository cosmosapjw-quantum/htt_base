# REV-R126 - EGS theorem figure deck + consolidated results table + blocker dossier + report gallery

owner: COMMON
implementation_scope: common
claim_tier: diagnostic_only_and_program_theorem
transfer_source: none
generating_command: `make` figures/table + latexmk + build_*_audit_package.py
git_commit_or_worktree_state: branch research/pr04-multicomponent

## Request

Produce every new plot + data analysis the upgraded code supports, massively
update the research report, and document the blockers separately.

## Changes

- `scripts/make_egs2_egs3_theorem_figures.py` (new): eight diagnostic-only
  theorem figures computed from the canonical modules, each with a
  content-addressed `source.json` + gated manifest (no git state -> `--check`
  stable across commits):
  fig_egs3_a1_graded_rank, fig_egs3_a3_evalue_calibration,
  fig_egs2_nt2a1_fisher_floor, fig_egs3_b1_floor_profile, fig_egs3_b2_volterra,
  fig_egs3_b3_vorticity, fig_egs2_nt2b1_bracket, fig_egs3_psd_cone. All eight
  visually inspected; A1 decluttered (sector-coloured ticks), NT2-B1 switched to
  log-y so the load-bearing lower bound is visible.
- `tests/contracts/test_egs_theorem_figures.py` (new): --check determinism +
  every manifest carries the diagnostic-only claim firewall + content-addressed
  (no git state).
- `scripts/build_egs_results_table.py` (new) -> `docs/generated/egs_results_table.{json,md}`:
  17-row consolidated table across NT-A/B, EGS2 NT2-*, EGS3 A/B/PSD, K1/K5/K6
  (14 proven = 6 symbolic + 8 gate; 3 blocked), values pulled from the
  deterministic experiment records.
- `docs/research_program/BLOCKERS.md` (new): single source of truth for every
  standing blocker -- code, exact unblock action + owner, `mechanics_ready`
  module, exit gate; covers MISSING_PR4_E2E_ACCESS (K1), MISSING_FIELD_REALIZATIONS
  (K6), MISSING_RELEASE_MOCK_OWNERSHIP (K5), BLOCKED_UPSTREAM (PR08-006),
  AWAITING_NATIVE_LOWELL_SOLVER (PR10, partial B1 discharge).
- `docs/final_report/main.tex` (18 -> 21 pp): new \S9 "Theorem figure gallery and
  consolidated results" -- five figure floats (Axis A / Axis B / PSD redesign),
  the consolidated results table, and a blocker-status paragraph pointing at
  BLOCKERS.md.
- `scripts/build_pr04_research_audit_package.py` + `build_final_report_audit_package.py`:
  +8 figures, +results table (json/md), +BLOCKERS.md, +two new scripts; research
  deltas r108..r126.

## Claim discipline

Every figure manifest is `diagnostic_only`, `family_identification:false`,
`native_solver_result:false`, `null_mock_status:synthetic_only`. The results
table and the report gallery state synthetic/analytic provenance; the three data
rows keep their registered blocker codes and emit only labelled synthetic
stand-ins. `pdf_claim_lint` 0 failed / 0 warning. No detection, family/geometry,
or native-solver claim.

## Validation

| Command | Status |
| --- | --- |
| `make_egs2_egs3_theorem_figures.py` + `--check` | 8 figures; sidecars up to date |
| `build_egs_results_table.py` + `--check` | 17 rows; up to date |
| `latexmk -pdf main.tex` | PASS; 21 pages |
| `pdf_claim_lint.py` | Failed 0, Warning 0 |
| contracts (figures + packages + egs3) | passed |
| both audit packages + `--check` | byte-deterministic |
