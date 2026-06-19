# REV-R078: stage research program DAG

owner: COMMON
implementation_scope: research_program_proposal
claim_tier: diagnostic_only
transfer_source: none
config_hash: sha256:89ecfc70f3f8b8a7dd40897aaae76db56d7bb7f9611556b70f2b66c670b82ed9
input_hashes:
- path: docs/audits/external_research_inputs_2026-06-20/RESEARCH_AUDIT_REPORT.md
  sha256: c2e57931109cdbdeb40c2a469db50a64626bb85d05c266f53fad369494d0a065
- path: docs/generated/external_research_input_response_matrix.md
  sha256: d0b5860d8f7657ba7bbb4e498c1821a1e3de0584d1249a9d7c9286c0258cb8ac
- path: docs/codex_handoff/pr_dag_research_program.yaml
  sha256: 63dd73215f0e0eb9e60bac3dff70a5177db74c3d9cef936d6ad90ef64e557aeb
- path: docs/generated/research_program_experiment_registry.yaml
  sha256: 819a43c500b0e9751c2cb9581633feff90f1217b161933c2801d42eb24014b04
- path: docs/generated/research_program_theorem_registry.yaml
  sha256: 983a63166479e06ada83790941313344dc3cb2f5022be4c1529006e2469013b7
sky_support_status: not_directional
null_mock_status: not_statistical
generating_command: manual REV-R078 research program proposal staging
git_commit_or_worktree_state: pending_rev_r078_commit
caveats:
- proposal only; not canonical DAG completion
- no native low-ell solver implementation
- no family identification before native morphology atlas support
- external/proxy transfer remains non-native and transfer-conditional
- MIO diagnostics do not merge into HTT evidence

## Intent

Import the external audit/research-program suggestions as a proposal DAG, not as
completed canonical work.  This creates a staged map for the next implementation
slice while preserving the completed `docs/codex_handoff/pr_status.yaml`
canonical DAG.

## Evidence Gathering

- Read `docs/superpowers/plans/2026-06-20-external-audit-research-program-integration.md`
  Task 5.
- Read the existing proposed-only revision DAG at
  `docs/codex_handoff/pr_dag_revision.yaml`.
- Read generated revision crosswalk, novelty ledger, and claim lanes to keep
  proposal registry semantics consistent with current repo policy.
- Web/documentation evidence had already been gathered for this plan slice:
  CF4 grouped-data sources and current survey/data documentation support staging
  CF4/DESI/BOSS/eBOSS work as observed-input contracts, not native transfer or
  family-identification evidence.

## Divergence And Selection

- Code cartographer steelman: import the PR-N list so the next development
  steps have explicit dependencies.  Attack: never add PR-N rows to canonical
  `pr_status.yaml` or count them as complete.
- Harness engineer steelman: a simple YAML/test gate is enough if it validates
  ordering, owners, and blocked statuses.  Attack: registries must also cover
  experiment/theorem links so future PRs do not drift.
- Physics/statistics auditor steelman: the research program can be ambitious
  if status labels stay proposal/design/diagnostic/external-audit only.  Attack:
  native solver, family-ID, morphology compatibility, and evidence-grade claims
  remain blocked.
- Claim-gate reviewer steelman: proposal registries are safe audit artifacts.
  Attack: `PR-N50` must be schema-only and `PR-N51` must be blocked until native
  solver/atlas gates exist.
- Regression tester steelman: targeted YAML tests plus canonical DAG validation
  cover this PR.  Attack: claim-language scan must include all new proposal
  files.

## Changes

- Added `docs/codex_handoff/pr_dag_research_program.yaml` with PR-N00 through
  PR-N51, explicit topological dependencies, proposal-only status, restored
  PR-N11/PR-N13/PR-N31 calibration rows, native low-ell solver implementation
  disabled, and family-identification blocked before native atlas support plus
  mask/covariance/null/equivalence/PPC/held-out/prior/look-elsewhere gates.
- Added `docs/generated/research_program_experiment_registry.yaml`, mapping the
  proposed experiments E0-E8 to PR-N rows and blocked-claim gates.
- Added `docs/generated/research_program_theorem_registry.yaml`, mapping theorem
  tracks T1-T6 to PR-N rows while keeping scalar and morphology/family claims
  blocked where required.
- Added `tests/contracts/test_research_program_dag.py` to validate structure,
  dependencies, registry coverage, and canonical status non-mutation.

## Verification

- `PYTHONDONTWRITEBYTECODE=1 venv/bin/python -m pytest -p no:cacheprovider -q tests/contracts/test_research_program_dag.py`
  - result: 6 passed.
- `venv/bin/python scripts/codex_harness/validate_pr_dag.py docs/codex_handoff/pr_backlog.yaml`
  - result: OK, 62 PRs, DAG valid.
- `venv/bin/python scripts/check_claim_language.py docs/codex_handoff/pr_dag_research_program.yaml docs/generated/research_program_experiment_registry.yaml docs/generated/research_program_theorem_registry.yaml tests/contracts/test_research_program_dag.py --dry-run --format json`
  - result: 0 issues.
- `venv/bin/python scripts/check_claim_language.py docs/codex_handoff/pr_dag_research_program.yaml docs/generated/research_program_experiment_registry.yaml docs/generated/research_program_theorem_registry.yaml tests/contracts/test_research_program_dag.py docs/PR_DELTAS/rev-r078.md --dry-run --format json`
  - result: 0 issues.

## Review Status

- `/review` loop 1 found metadata, duplicate-key, canonical-promotion, registry
  coverage, T2 `mio_evidence`, and forecast-lane gaps.
- Patched YAML artifact metadata, strict duplicate-key parsing, PR-ID uniqueness,
  canonical status/backlog PR-N exclusion, full registry PR coverage, T2
  `mio_evidence` blocking, and removed forecast as an accepted proposal use.
- Physics/statistics `/review` found topology-level promotion risks: missing
  CF4, spectroscopic, and Planck calibration rows; weak family-equivalence
  blockers; jackknife-as-null risk; insufficient PR-N22/PR-N40 row gates; and
  unsafe BiPoSH compatibility wording.
- Patched the proposal DAG to restore PR-N11, PR-N13, and PR-N31 from the
  external program topology; retargeted PR-N20/PR-N32 through those calibration
  rows; expanded PR-N22/PR-N40 required gates; made PR-N51 depend on the
  relevant null/PPC/covariance rows and require native morphology atlas,
  convergence, external cross-check, exact masks, full covariance,
  response-rank/nuisance-projection gates, matched-complexity alternatives,
  family-equivalence separation, prior stability, PPC, held-out morphology
  prediction, and orientation look-elsewhere correction.
- `/review` loop 2 found that metadata was still path-listed rather than
  hash-bound, the PR delta test count was stale, and rank/nuisance gates were
  not explicit on all promotion surfaces.
- Patched YAML and PR delta metadata to use real `sha256:<64-hex>` config hashes
  plus `{path, sha256}` input entries, and strengthened the contract test to
  verify file existence and digest matches.  Also recorded the authoritative
  pytest command under `venv/bin/python`; `/usr/bin/python -m pytest` is not the
  repo validation surface in this environment because system Python lacks
  pytest.

## Known Residuals

- PR-N rows are proposal/planning rows only.  They do not replace the completed
  canonical DAG and do not satisfy dependencies for implementation PRs until
  explicitly selected in a future revision slice.
- `PR-N50` is schema-only and `PR-N51` remains blocked until a native low-ell
  morphology atlas exists.
