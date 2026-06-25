# REV-R121 - EGS2 report §7 + programme docs + package + contract expansion

owner: COMMON
implementation_scope: common
claim_tier: program_theorem_and_synthetic_mechanics
transfer_source: none
generating_command: `latexmk + build_*_audit_package.py`
git_commit_or_worktree_state: branch research/pr04-multicomponent

## Request

Land the EGS2 extension surface: report section, programme docs/tickets, contract
gate, and expand the external-audit packages. Reference the publishable-next
companion (T1-T6 already-implemented repo modules + PR08 blocker DAG + ledger).

## Changes

- `docs/final_report/main.tex` (16 -> 17 pp): new §7 "EGS-type extension theorems
  (NT2) and blocker discharges" --- NT2-A1 genuine Fisher floor (strictly below
  0.632), NT2-A2 saturation, NT2-B1 zero-excluding bracket, NT2-B2 sourced
  transport, NT2-B3 joint blind sector, and the concrete K1/K6/K5 public-data
  discharges + the interim semi-native calculator.
- `docs/research_program/egs2/`: README, THEOREM_MAP (NT2-* + T1-T6 -> modules),
  BLOCKER_DISCHARGES, PRIOR_ART (web-CRAG), CLAIM_LEDGER.yaml, NEXT_DAG.yaml,
  tickets (K5 release-matched mocks, semi-native shear->quadrupole calculator).
- `tests/contracts/test_egs2_extension.py` (5 gates): NT2-A1 floor, NT2-B1
  exclusion, NT2-B2/B3, K1/K6 discharges, and the NT-A3 registry no-overclaim.
- `scripts/build_pr04_research_audit_package.py`: +EGS2 modules, driver, gate
  tests, experiment evidence, programme docs (87 -> 147 files); deltas r108..r120.
- `scripts/build_final_report_audit_package.py`: +`egs2_experiments.json`.
- `CHANGELOG.md` + `CLAUDE.md` updated.

## Integration with the publishable-next companion

The publishable-next package's T1-T6 reuse existing repo modules
(`lowell_global_calibration`, `paper_a_closure`, `bass.kinetic.*`,
`bass.geometry.egs_rigidity`, `affine_flow`); its integration runner
(`run_next_research_experiments.py`) is confirmed green against the current repo
(+ the new EGS2 modules) and is referenced from the egs2 programme README. Its
claim ledger and PR08 blocker DAG were folded into `docs/research_program/egs2/`.

## Claim discipline

Conditional theorems + synthetic mechanics only; no detection, family/geometry,
or native-solver claim. `pdf_claim_lint` 0 failed.

## Validation

| Command | Status |
| --- | --- |
| `latexmk -pdf main.tex` | PASS; 17 pages |
| `pdf_claim_lint.py` | Failed 0, Warning 0 |
| `make egs2-gates` / pr07 / pr04 / forbidden-deps | 13 / 16 / 23 / PASS |
| contracts (egs2 + pr07 + 2 packages) | 22 passed |
| `pytest tests/obsstat` | 111 passed |
| both audit packages + `--check` | byte-deterministic (147 / 59 files) |
| publishable-next integration runner | green |
| smoke | 6 passed |
