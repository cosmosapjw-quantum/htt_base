# REV-R115 - PR04/LR-06 research external-audit package

owner: COMMON
implementation_scope: common
claim_tier: diagnostic_only
transfer_source: mixed_none_observed_and_external_transfer_conditional
generating_command: `python scripts/build_pr04_research_audit_package.py`
git_commit_or_worktree_state: branch research/pr04-multicomponent

## Request

Produce a fresh external research-audit package reflecting the current progress
(PR04 multicomponent integration + LR-06 theorems/measurements + updated report).

## Deliverable

`scripts/build_pr04_research_audit_package.py` builds a deterministic, self-
contained research-audit bundle ->
`docs/research_program/pr04/htt_pr04_research_audit_package.{zip,_manifest.json}`
+ `htt_pr04_research_audit_prompt.md` (87 entries, ~1.5 MB). It is the reviewable
research surface for the branch, distinct from the final-report package (report
only) and the code-capability package (raw source only).

Contents (group_counts):
- report (2): `docs/final_report/main.{tex,pdf}` (the credible-claim report).
- theorem records (5): EGS + PR04 Wolfram proof records + `PAPER_THEOREM_MAP.md`.
- theorem implementations (11): PR04 overlay (STF, multicomponent blocks,
  congruence first jet, response audit, Bianchi-I moments/dynamics, fail-closed
  pushforward, canonical bridge) + the new OBSSTAT estimators (`affine_flow`,
  `bulkflow_mle`).
- driver scripts (8): the proof/figure/measurement drivers, `Makefile`, the
  `extract_cf4_full` pipeline extension, and `sources.json`.
- gate tests (6): `research_gates/pr04/tests/test_pr04_*.py`.
- measurement reports (8): K1 (Planck low-ell), K4 (CF4 apex), K5 (CF4 full-
  release bulk flow), K6 (CF4 affine flow) json+md.
- governance (6): LR-06 ticket ledger, claim/stop gates, paper exit criteria,
  data-acquisition status, Rust design, execution schedule.
- pr deltas (7): rev-r108..r114.
- figures (12 png + 12 manifests + 7 source.json).
- README + adversarial research audit prompt.

## Claim discipline

Manifest keeps `claim_tier=diagnostic_only`, `family_identification:false`,
`native_solver_result:false`, and science-promotion gates blocked
(family-ID/geometry, global-tilt-from-CF4, model-ranking/odds, native solver).
No raw datasets are bundled; reports carry release hashes. The audit prompt
enumerates the hard rejection boundaries.

## Validation

| Command | Status |
| --- | --- |
| `build_pr04_research_audit_package.py` | 87 entries; all required assertions true |
| `... --check` | byte-deterministic; up-to-date |
| `... --dry-run` | group counts as expected; no raw data |
| `pytest tests/contracts/test_pr04_research_audit_package.py` | 5 passed |
