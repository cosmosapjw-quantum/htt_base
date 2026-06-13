# Long-range Codex PR DAG for `htt_base` before native low-ell solver

This backlog is a single logical DAG. Do not execute PRs by wave alone; execute the next topologically available PR whose dependencies and checkpoint gates are green.

## Global execution rule

At each PR: web-backed brainstorming when available -> subagent steelman divergence -> metacognitive pruning -> implementation -> tests -> `/review` hostile audit -> patch -> commit. Every five completed PRs, run the progress checkpoint and update the plan if progress stalls.

## Topological order

`PR-000 -> PR-001 -> PR-003 -> PR-002 -> PR-004 -> PR-005 -> PR-020 -> PR-010 -> PR-021 -> PR-011 -> PR-013 -> PR-014 -> PR-040 -> PR-012 -> PR-022 -> PR-070 -> PR-015 -> PR-050 -> PR-041 -> PR-023 -> PR-071 -> PR-080 -> PR-030 -> PR-113 -> PR-051 -> PR-042 -> PR-072 -> PR-081 -> PR-031 -> PR-052 -> PR-043 -> PR-073 -> PR-082 -> PR-032 -> PR-053 -> PR-074 -> PR-083 -> PR-054 -> PR-075 -> PR-055 -> PR-076 -> PR-056 -> PR-060 -> PR-090 -> PR-100 -> PR-084 -> PR-061 -> PR-091 -> PR-101 -> PR-102 -> PR-062 -> PR-092 -> PR-063 -> PR-110 -> PR-064 -> PR-065 -> PR-066 -> PR-103 -> PR-111 -> PR-112 -> PR-114 -> PR-115`

## Wave 0: Intake, packaging, DAG harness, and no-science preflight

### PR-000 — Codex intake, repo snapshot, and immutable baseline inventory
- **Owner:** COMMON
- **Depends:** none
- **Verification level:** L0
- **Risk:** low
- **Primary files:**
  - `docs/PR_DELTAS/pr-000-intake.md`
  - `docs/generated/repo_inventory.json`
  - `docs/generated/test_command_matrix.md`
- **Tests / commands:**
  - `python -m pytest --collect-only htt/htt/tests htt/src htt/tsc htt/workspace htt/mio -q`
- **Definition of done:**
  - Repo roots, import paths, optional dependency failures, generated artifacts, and stale figures are inventoried
  - No scientific behavior changes
- **Kill / rollback:** If collect-only cannot run, record exact import failure and stop all non-harness PRs.

### PR-001 — Editable install and import-path stabilization
- **Owner:** COMMON
- **Depends:** PR-000
- **Verification level:** L0
- **Risk:** medium
- **Primary files:**
  - `htt/pyproject.toml`
  - `htt/conftest.py`
  - `htt/__init__.py`
  - `docs/PR_DELTAS/pr-001-packaging.md`
- **Tests / commands:**
  - `python -m pip install -e ./htt[dev]`
  - `python -m pytest --collect-only htt/htt/tests htt/src htt/tsc htt/workspace htt/mio -q`
- **Definition of done:**
  - Repo-root and temp-dir imports work without ad hoc PYTHONPATH
  - Nested htt package behavior is documented and tested
- **Kill / rollback:** Do not rename public packages without compatibility aliases and migration tests.

### PR-002 — Test markers, optional dependency skips, and smoke suite taxonomy
- **Owner:** COMMON
- **Depends:** PR-001
- **Verification level:** L0
- **Risk:** medium
- **Primary files:**
  - `htt/pytest.ini`
  - `htt/conftest.py`
  - `docs/PR_DELTAS/pr-002-test-taxonomy.md`
- **Tests / commands:**
  - `python -m pytest -m smoke -q`
  - `python -m pytest --collect-only -q`
- **Definition of done:**
  - smoke/fast/slow/requires_healpy/requires_dynesty markers exist
  - Missing optional dependencies skip with explicit reason, not collection failure
- **Kill / rollback:** Never skip silently; every skip must name the missing dependency or slow marker.

### PR-003 — PR DAG machine-readable manifest and progress engine
- **Owner:** COMMON
- **Depends:** PR-000
- **Verification level:** L0
- **Risk:** low
- **Primary files:**
  - `docs/codex_handoff/pr_backlog.yaml`
  - `docs/codex_handoff/pr_dag.mmd`
  - `scripts/codex_harness/validate_pr_dag.py`
  - `scripts/codex_harness/progress_report.py`
- **Tests / commands:**
  - `python scripts/codex_harness/validate_pr_dag.py docs/codex_handoff/pr_backlog.yaml`
  - `python scripts/codex_harness/progress_report.py docs/codex_handoff/pr_backlog.yaml docs/codex_handoff/pr_status.yaml`
- **Definition of done:**
  - DAG has no cycles
  - Every PR dependency exists
  - Progress percent can be computed reproducibly
- **Kill / rollback:** If the graph is cyclic or has missing dependency ids, no implementation PR may start.

### PR-004 — AGENTS.md, repo-scoped skills, custom subagents, and rules install
- **Owner:** COMMON
- **Depends:** PR-003
- **Verification level:** L0
- **Risk:** low
- **Primary files:**
  - `AGENTS.md`
  - `.agents/skills/**/SKILL.md`
  - `.codex/agents/*.toml`
  - `.codex/rules/default.rules`
  - `docs/codex_handoff/INSTALL.md`
- **Tests / commands:**
  - `codex execpolicy check --pretty --rules .codex/rules/default.rules -- python -m pytest -q`
  - `python scripts/codex_harness/validate_pr_dag.py docs/codex_handoff/pr_backlog.yaml`
- **Definition of done:**
  - Repo instruction, skills, agents, and rules load from documented paths
  - Install instructions are tested as file operations
- **Kill / rollback:** If AGENTS.md exceeds 32 KiB, split details into skills and keep root instructions terse.

### PR-005 — Five-PR checkpoint and adaptive replan protocol
- **Owner:** COMMON
- **Depends:** PR-003
- **Verification level:** L1
- **Risk:** low
- **Primary files:**
  - `scripts/codex_harness/progress_report.py`
  - `docs/codex_handoff/checkpoint_protocol.md`
  - `docs/generated/progress_checkpoints/README.md`
- **Tests / commands:**
  - `python scripts/codex_harness/progress_report.py docs/codex_handoff/pr_backlog.yaml docs/codex_handoff/pr_status.yaml --checkpoint-every 5`
- **Definition of done:**
  - Progress percentage is numeric and reproducible
  - No-progress detection triggers adversarial replan entry
- **Kill / rollback:** If progress is not measurable, downstream automation cannot claim completion.

## Wave 1: Common SSoT contracts and semantic firewall

### PR-010 — Canonical owner, claim-tier, scope, and bundle contracts
- **Owner:** COMMON
- **Depends:** PR-003, PR-004
- **Verification level:** L2
- **Risk:** medium
- **Primary files:**
  - `htt/src/common/contracts.py`
  - `htt/workspace/contracts/ownership.py`
  - `tests/contracts/test_ownership_firewall.py`
- **Tests / commands:**
  - `python -m pytest tests/contracts/test_ownership_firewall.py -q`
- **Definition of done:**
  - Owner enum separates COMMON, HTT, MIO, BASS, OBSSTAT, TSC_LEGACY
  - ClaimTier and ImplementationScope are machine-checkable
- **Kill / rollback:** Reject if MIO can be typed as posterior owner or HTT can be typed as certificate owner.

### PR-011 — ArtifactManifest schema and artifact-first figure quarantine
- **Owner:** COMMON
- **Depends:** PR-010
- **Verification level:** L2
- **Risk:** medium
- **Primary files:**
  - `htt/src/common/artifact_manifest.py`
  - `scripts/check_artifact_manifests.py`
  - `docs/generated/quarantined_figures.md`
  - `tests/contracts/test_artifact_manifest.py`
- **Tests / commands:**
  - `python -m pytest tests/contracts/test_artifact_manifest.py -q`
  - `python scripts/check_artifact_manifests.py --dry-run`
- **Definition of done:**
  - Every result artifact has owner, scope, claim tier, config hash, input hashes, and caveats
  - Figures without manifest are quarantined
- **Kill / rollback:** Do not regenerate or reinterpret figures in this PR.

### PR-012 — StatusSnapshot and generated claim ledger pipeline
- **Owner:** COMMON
- **Depends:** PR-010, PR-011
- **Verification level:** L2
- **Risk:** medium
- **Primary files:**
  - `htt/src/common/status_snapshot.py`
  - `docs/generated/status_snapshot.json`
  - `docs/generated/claim_ledger.json`
  - `docs/generated/status_matrix.md`
  - `tests/contracts/test_status_snapshot.py`
- **Tests / commands:**
  - `python -m pytest tests/contracts/test_status_snapshot.py -q`
  - `python -m common.status_snapshot --write docs/generated/status_snapshot.json`
- **Definition of done:**
  - Manual test/module/status counts are prohibited in manuscript-facing docs
  - Snapshot is canonical for public status
- **Kill / rollback:** If generated and manuscript counts disagree, manuscript output is blocked.

### PR-013 — MIO/HTT posterior-certificate type firewall
- **Owner:** COMMON
- **Depends:** PR-010
- **Verification level:** L2
- **Risk:** high
- **Primary files:**
  - `htt/workspace/contracts/htt_posterior.py`
  - `htt/workspace/contracts/mio_certificate.py`
  - `tests/contracts/test_mio_htt_no_merge.py`
- **Tests / commands:**
  - `python -m pytest tests/contracts/test_mio_htt_no_merge.py -q`
- **Definition of done:**
  - MioCertificate is not a posterior and not a truth certificate
  - HTTPosteriorBundle cannot consume MioCertificate as a likelihood term
- **Kill / rollback:** Reject if any helper adds MIO p-values to HTT evidence.

### PR-014 — TransferFunctionSpec and transfer-provenance contract
- **Owner:** COMMON
- **Depends:** PR-010
- **Verification level:** L2
- **Risk:** high
- **Primary files:**
  - `htt/src/common/transfer_registry.py`
  - `htt/workspace/contracts/transfer.py`
  - `tests/contracts/test_transfer_registry.py`
- **Tests / commands:**
  - `python -m pytest tests/contracts/test_transfer_registry.py -q`
- **Definition of done:**
  - Every transfer-dependent result records source, family, valid range, observable kind, normalization, calibration status, caveats
  - External and future native transfers can coexist
- **Kill / rollback:** Reject if AniCLASS/external transfer can claim native BASS validation.

### PR-015 — Claim-language and banned-vocabulary linter
- **Owner:** COMMON
- **Depends:** PR-010, PR-013, PR-014
- **Verification level:** L2
- **Risk:** medium
- **Primary files:**
  - `htt/src/common/semantic_guards/no_overclaim.py`
  - `scripts/check_claim_language.py`
  - `tests/contracts/test_claim_language_lint.py`
- **Tests / commands:**
  - `python -m pytest tests/contracts/test_claim_language_lint.py -q`
  - `python scripts/check_claim_language.py docs manuscripts --dry-run`
- **Definition of done:**
  - Blocks scalar-only geometry/family-identification language
  - Blocks TSC/Teff full-solver or full-polarisation language
- **Kill / rollback:** Reject if linter only warns for forbidden production claims; production claims must fail.

## Wave 2: Test harness, optional dependencies, and CI-like local runners

### PR-020 — Harness runner for collect/smoke/fast/package subsets
- **Owner:** COMMON
- **Depends:** PR-002, PR-003
- **Verification level:** L1
- **Risk:** medium
- **Primary files:**
  - `scripts/codex_harness/run_subset.py`
  - `docs/codex_handoff/test_harness.md`
  - `tests/contracts/test_harness_runner.py`
- **Tests / commands:**
  - `python scripts/codex_harness/run_subset.py --list`
  - `python scripts/codex_harness/run_subset.py smoke --dry-run`
- **Definition of done:**
  - Codex can run deterministic test subsets by name
  - Commands are documented and do not require hidden PYTHONPATH
- **Kill / rollback:** If runner masks failures by default, reject.

### PR-021 — Optional dependency registry and skip-audit report
- **Owner:** COMMON
- **Depends:** PR-002, PR-020
- **Verification level:** L1
- **Risk:** medium
- **Primary files:**
  - `htt/src/common/optional_dependencies.py`
  - `scripts/codex_harness/optional_dep_report.py`
  - `docs/generated/optional_dependency_status.md`
  - `tests/contracts/test_optional_dependencies.py`
- **Tests / commands:**
  - `python -m pytest tests/contracts/test_optional_dependencies.py -q`
  - `python scripts/codex_harness/optional_dep_report.py`
- **Definition of done:**
  - healpy/dynesty/astropy/etc. status is explicit
  - Skipped tests are attributable
- **Kill / rollback:** Reject if missing dependency appears as import error instead of skip or documented blocker.

### PR-022 — PR delta template and review artifact generator
- **Owner:** COMMON
- **Depends:** PR-011, PR-020
- **Verification level:** L1
- **Risk:** low
- **Primary files:**
  - `scripts/codex_harness/new_pr_delta.py`
  - `docs/PR_DELTAS/TEMPLATE.md`
  - `tests/contracts/test_pr_delta_template.py`
- **Tests / commands:**
  - `python scripts/codex_harness/new_pr_delta.py PR-000 --dry-run`
  - `python -m pytest tests/contracts/test_pr_delta_template.py -q`
- **Definition of done:**
  - Every PR can emit design delta, tests run, changed files, claim impact, risk log
  - Review artifacts are standardised
- **Kill / rollback:** Reject PRs that change science code without PR_DELTA.

### PR-023 — Progress scoreboard and stagnation-triggered replanning
- **Owner:** COMMON
- **Depends:** PR-005, PR-022
- **Verification level:** L1
- **Risk:** medium
- **Primary files:**
  - `docs/codex_handoff/pr_status.yaml`
  - `scripts/codex_harness/progress_report.py`
  - `docs/generated/progress_checkpoints/`
- **Tests / commands:**
  - `python scripts/codex_harness/progress_report.py docs/codex_handoff/pr_backlog.yaml docs/codex_handoff/pr_status.yaml --json`
- **Definition of done:**
  - At least every 5 completed PRs, percent progress and blockers are generated
  - Stagnation triggers written replan, not silent continuation
- **Kill / rollback:** Reject if percent progress can be gamed by marking skipped PRs complete.

## Wave 3: Teff/TSC deprecation, legacy quarantine, and generic semantic guards

### PR-030 — Deprecate TSC as active science owner and preserve legacy imports
- **Owner:** COMMON
- **Depends:** PR-015
- **Verification level:** L2
- **Risk:** high
- **Primary files:**
  - `htt/tsc_legacy/README.md`
  - `htt/tsc/__init__.py`
  - `docs/deprecation/tsc_legacy.md`
  - `tests/tsc/test_tsc_legacy_boundary.py`
- **Tests / commands:**
  - `python -m pytest tests/tsc/test_tsc_legacy_boundary.py -q`
- **Definition of done:**
  - TSC legacy remains import-compatible where needed
  - New artifacts cannot set owner=TSC except legacy reproduction
- **Kill / rollback:** Reject if active MIO/HTT/BASS modules import TSC for new scientific claims.

### PR-031 — Generic semantic guards extracted from TSC legacy
- **Owner:** COMMON
- **Depends:** PR-030
- **Verification level:** L2
- **Risk:** high
- **Primary files:**
  - `htt/src/common/semantic_guards/admissibility_status.py`
  - `htt/src/common/semantic_guards/source_propagation_status.py`
  - `tests/contracts/test_semantic_guards.py`
- **Tests / commands:**
  - `python -m pytest tests/contracts/test_semantic_guards.py -q`
- **Definition of done:**
  - source adequacy, propagation adequacy, and observable adequacy are separate statuses
  - Trace/source caveats can attach to artifacts without TSC ownership
- **Kill / rollback:** Reject if source adequate automatically implies observable adequate.

### PR-032 — Legacy theorem-to-test map retained for audit only
- **Owner:** COMMON
- **Depends:** PR-030, PR-031
- **Verification level:** L2
- **Risk:** medium
- **Primary files:**
  - `docs/generated/theorem_to_test_map_legacy_tsc.json`
  - `docs/deprecation/theorem_to_test_map.md`
  - `tests/contracts/test_theorem_to_test_map.py`
- **Tests / commands:**
  - `python -m pytest tests/contracts/test_theorem_to_test_map.py -q`
- **Definition of done:**
  - Legacy proofs map to validation obligations, not production claims
  - Can surface why Teff was deprecated without losing audit trail
- **Kill / rollback:** Reject if legacy theorem status promotes new observation/family claims.

## Wave 4: Sky support, ZoA, axis gates, and mock calibration

### PR-040 — SkySupport, mask hash, and coordinate-frame contracts
- **Owner:** COMMON
- **Depends:** PR-010, PR-021
- **Verification level:** L2
- **Risk:** high
- **Primary files:**
  - `htt/src/common/sky_support.py`
  - `htt/src/common/sky_geometry.py`
  - `tests/htt/test_sky_support_contract.py`
- **Tests / commands:**
  - `python -m pytest tests/htt/test_sky_support_contract.py -q`
- **Definition of done:**
  - Every sky-facing artifact records coordinate frame, mask hash, sky fraction, completeness status
  - Spherical means use unit vectors, never raw mean(l),mean(b)
- **Kill / rollback:** Reject if raw longitude/latitude means survive in production summaries.

### PR-041 — ZoA ladder and selection-aware support modes
- **Owner:** HTT
- **Depends:** PR-040
- **Verification level:** L2
- **Risk:** high
- **Primary files:**
  - `htt/src/htt/zoa/selection_ladder.py`
  - `htt/src/common/healpix_selection.py`
  - `tests/htt/test_zoa_selection_ladder.py`
- **Tests / commands:**
  - `python -m pytest tests/htt/test_zoa_selection_ladder.py -q`
- **Definition of done:**
  - raw, masked, selection-aware, mock-calibrated summaries are separate modes
  - Uniform fallback forbidden in production mode
- **Kill / rollback:** Reject if diagnostic ZoA output can become default production axis.

### PR-042 — PreferredAxis production gate and downstream synthesis lock
- **Owner:** HTT
- **Depends:** PR-040, PR-041
- **Verification level:** L2
- **Risk:** high
- **Primary files:**
  - `htt/htt/htt/direction/preferred_axis.py`
  - `htt/htt/htt/zoa/axis_promotion.py`
  - `tests/htt/test_preferred_axis_gate.py`
- **Tests / commands:**
  - `python -m pytest tests/htt/test_preferred_axis_gate.py -q`
- **Definition of done:**
  - PreferredAxis.production_allowed defaults False
  - Axis promotion requires SkySupport + mask + mock coverage
- **Kill / rollback:** Reject if diagnostic axis can rotate a_lm or a_2m.

### PR-043 — Mock calibration harness for axis and direction claims
- **Owner:** HTT
- **Depends:** PR-041, PR-042
- **Verification level:** L3
- **Risk:** high
- **Primary files:**
  - `htt/src/common/mock_calibration.py`
  - `htt/src/htt/nulls/axis_nulls.py`
  - `tests/htt/test_mock_calibration_gate.py`
- **Tests / commands:**
  - `python -m pytest tests/htt/test_mock_calibration_gate.py -q`
- **Definition of done:**
  - Directional claims record retention, bias, coverage, FPR
  - Mock coverage gates production axis
- **Kill / rollback:** Reject if mock coverage is missing but claim tier exceeds diagnostic.

## Wave 5: MIO x/Q/Pi/F/G formalism and diagnostic reports

### PR-050 — DepartureBundle and comparator/frame metadata
- **Owner:** MIO
- **Depends:** PR-010, PR-014
- **Verification level:** L2
- **Risk:** medium
- **Primary files:**
  - `htt/mio/formalism/departure_bundle.py`
  - `htt/mio/formalism/component_breakdown.py`
  - `tests/mio/test_departure_bundle.py`
- **Tests / commands:**
  - `python -m pytest tests/mio/test_departure_bundle.py -q`
- **Definition of done:**
  - B_C components, comparator C, frame, units, and cancellation index are explicit
  - x_C is a signed projection, not anisotropy norm
- **Kill / rollback:** Reject if x_C is exported without comparator/frame metadata.

### PR-051 — BudgetSpec and denominator-policy sensitivity
- **Owner:** MIO
- **Depends:** PR-050, PR-014
- **Verification level:** L2
- **Risk:** high
- **Primary files:**
  - `htt/mio/formalism/budget_spec.py`
  - `tests/mio/test_budget_spec.py`
- **Tests / commands:**
  - `python -m pytest tests/mio/test_budget_spec.py -q`
- **Definition of done:**
  - MES_linear, external_transfer, atlas_quantile, observational budget policies are distinct
  - Sensitivity hooks exist
- **Kill / rollback:** Reject if denominator policy is implicit.

### PR-052 — Q normalized score implementation
- **Owner:** MIO
- **Depends:** PR-050, PR-051
- **Verification level:** L2
- **Risk:** high
- **Primary files:**
  - `htt/mio/formalism/normalized_score.py`
  - `tests/mio/test_normalized_score.py`
- **Tests / commands:**
  - `python -m pytest tests/mio/test_normalized_score.py -q`
- **Definition of done:**
  - Q carries numerator policy and denominator policy
  - Q cannot use filling/occupancy language unless certified F also exists
- **Kill / rollback:** Reject if Q is named filling fraction in artifact metadata.

### PR-053 — F certified filling fraction implementation
- **Owner:** MIO
- **Depends:** PR-051, PR-052
- **Verification level:** L2
- **Risk:** high
- **Primary files:**
  - `htt/mio/formalism/filling_fraction.py`
  - `tests/mio/test_filling_fraction.py`
- **Tests / commands:**
  - `python -m pytest tests/mio/test_filling_fraction.py -q`
- **Definition of done:**
  - F requires sign-clean sector, U>0, 0<=F<=1, sample-wise pushforward
  - F_Bayes is sample mean, not ratio of means
- **Kill / rollback:** Reject if invalid F exports as physical occupancy.

### PR-054 — Pi exceedance curve and threshold discipline
- **Owner:** MIO
- **Depends:** PR-052, PR-053
- **Verification level:** L2
- **Risk:** medium
- **Primary files:**
  - `htt/mio/formalism/exceedance.py`
  - `tests/mio/test_exceedance.py`
- **Tests / commands:**
  - `python -m pytest tests/mio/test_exceedance.py -q`
- **Definition of done:**
  - Pi is an exceedance curve, not truth probability
  - Threshold choice is metadata/pre-registered or curve-only
- **Kill / rollback:** Reject if Pi is described as probability that anisotropy is true.

### PR-055 — G_F depth gap and log-gap robustness
- **Owner:** MIO
- **Depends:** PR-053, PR-054, PR-040
- **Verification level:** L2
- **Risk:** high
- **Primary files:**
  - `htt/mio/formalism/isotropy_gap.py`
  - `tests/mio/test_isotropy_gap.py`
- **Tests / commands:**
  - `python -m pytest tests/mio/test_isotropy_gap.py -q`
- **Definition of done:**
  - G_F and log g_F handle floors, bin covariance metadata, denominator evolution split
  - G cannot be exported without depth-bin metadata
- **Kill / rollback:** Reject if G_F alone triggers global tilt claim.

### PR-056 — MIO report-card generator for x/Q/Pi/F/G
- **Owner:** MIO
- **Depends:** PR-050, PR-051, PR-052, PR-053, PR-054, PR-055, PR-011
- **Verification level:** L3
- **Risk:** medium
- **Primary files:**
  - `htt/mio/reports/departure_report.py`
  - `tests/mio/test_departure_report.py`
- **Tests / commands:**
  - `python -m pytest tests/mio/test_departure_report.py -q`
- **Definition of done:**
  - DepartureReport emits manifest, claim tier, caveats, transfer provenance, F status, G status
  - HTT and MIO outputs remain separate
- **Kill / rollback:** Reject if report card collapses all scores into one headline number.

## Wave 6: HTT local/global inference, null competition, and adequacy diagnostics

### PR-060 — Response-overlap and rank audit for local/global discrimination
- **Owner:** HTT
- **Depends:** PR-014, PR-040, PR-055
- **Verification level:** L3
- **Risk:** high
- **Primary files:**
  - `htt/src/htt/departure/response_overlap.py`
  - `tests/htt/test_response_overlap.py`
- **Tests / commands:**
  - `python -m pytest tests/htt/test_response_overlap.py -q`
- **Definition of done:**
  - Computes rho_LB_GT and nuisance-projected rank
  - Rank deficiency yields no-claim status
- **Kill / rollback:** Reject if posterior/evidence runs when rank audit says no identifiable direction.

### PR-061 — Local boost and local-structure null models
- **Owner:** HTT
- **Depends:** PR-043, PR-060
- **Verification level:** L3
- **Risk:** high
- **Primary files:**
  - `htt/htt/htt/nulls/local_boost_depth_null.py`
  - `htt/htt/htt/nulls/clustering_dipole_depth.py`
  - `tests/htt/test_local_boost_nulls.py`
- **Tests / commands:**
  - `python -m pytest tests/htt/test_local_boost_nulls.py -q`
- **Definition of done:**
  - Local boost-only mocks produce G_F/direction distributions
  - Null FPR is available before global-tilt claim
- **Kill / rollback:** Reject if global tilt claim lacks local-boost null FPR.

### PR-062 — Survey-axis and selection-response null models
- **Owner:** HTT
- **Depends:** PR-043, PR-061
- **Verification level:** L3
- **Risk:** high
- **Primary files:**
  - `htt/htt/htt/nulls/selection_response_depth.py`
  - `htt/htt/htt/nulls/survey_axis_coherence.py`
  - `tests/htt/test_survey_nulls.py`
- **Tests / commands:**
  - `python -m pytest tests/htt/test_survey_nulls.py -q`
- **Definition of done:**
  - Survey/systematic nulls can mimic direction/depth signals in calibration
  - Selection metadata is carried through
- **Kill / rollback:** Reject if survey nulls are only narrative and not runnable mocks.

### PR-063 — Local/global mixture likelihood skeleton
- **Owner:** HTT
- **Depends:** PR-060, PR-061, PR-062
- **Verification level:** L3
- **Risk:** high
- **Primary files:**
  - `htt/htt/htt/departure/local_global_mixture.py`
  - `tests/htt/test_local_global_mixture.py`
- **Tests / commands:**
  - `python -m pytest tests/htt/test_local_global_mixture.py -q`
- **Definition of done:**
  - Mixture model separates LB, GT, systematics, noise blocks
  - F/G are generated functionals, not primitive parameters
- **Kill / rollback:** Reject if local and global tilt share a single beta field.

### PR-064 — Matched-complexity null competition harness
- **Owner:** HTT
- **Depends:** PR-063
- **Verification level:** L3
- **Risk:** high
- **Primary files:**
  - `htt/htt/htt/infer/matched_complexity.py`
  - `htt/htt/htt/infer/null_competition.py`
  - `tests/htt/test_matched_nulls.py`
- **Tests / commands:**
  - `python -m pytest tests/htt/test_matched_nulls.py -q`
- **Definition of done:**
  - Alternative and null flexibility are reported
  - Evidence claims require matched null status
- **Kill / rollback:** Reject Bayes factor headline without matched-complexity report.

### PR-065 — Prior sweep, PPC, and LOOCV gates for HTT claims
- **Owner:** HTT
- **Depends:** PR-063, PR-064
- **Verification level:** L3
- **Risk:** high
- **Primary files:**
  - `htt/htt/htt/infer/prior_sweep.py`
  - `htt/htt/htt/infer/posterior_predictive.py`
  - `htt/htt/htt/infer/loocv.py`
  - `tests/htt/test_inference_adequacy_gates.py`
- **Tests / commands:**
  - `python -m pytest tests/htt/test_inference_adequacy_gates.py -q`
- **Definition of done:**
  - HTT evidence bundles carry prior-sensitivity, PPC, LOOCV status
  - Failure downgrades claim tier
- **Kill / rollback:** Reject decisive evidence language without PPC/LOOCV/prior-sweep status.

### PR-066 — Posterior pushforward for Q/F/Pi/G without MIO leakage
- **Owner:** HTT
- **Depends:** PR-056, PR-063, PR-065
- **Verification level:** L3
- **Risk:** medium
- **Primary files:**
  - `htt/htt/htt/departure/posterior_pushforward.py`
  - `tests/htt/test_posterior_pushforward.py`
- **Tests / commands:**
  - `python -m pytest tests/htt/test_posterior_pushforward.py -q`
- **Definition of done:**
  - HTT posterior samples push forward to Q/F/Pi/G with transfer provenance
  - MIO certificate is not an input
- **Kill / rollback:** Reject if posterior pushforward consumes MIO certificate outputs.

## Wave 7: Observer/statistics interface and morphology features

### PR-070 — Create obsstat package and ObservableVector contract
- **Owner:** OBSSTAT
- **Depends:** PR-010, PR-011
- **Verification level:** L2
- **Risk:** medium
- **Primary files:**
  - `htt/obsstat/__init__.py`
  - `htt/obsstat/observable_vector.py`
  - `tests/obsstat/test_observable_vector.py`
- **Tests / commands:**
  - `python -m pytest tests/obsstat/test_observable_vector.py -q`
- **Definition of done:**
  - obsstat owns feature extraction, not inference
  - ObservableVector can hold alm, templates, covariance, scalar/morphology/null features
- **Kill / rollback:** Reject if obsstat imports HTT likelihood or MIO certificate.

### PR-071 — Harmonic and spin convention registry
- **Owner:** OBSSTAT
- **Depends:** PR-070
- **Verification level:** L2
- **Risk:** high
- **Primary files:**
  - `htt/obsstat/alm_conventions.py`
  - `tests/obsstat/test_alm_conventions.py`
- **Tests / commands:**
  - `python -m pytest tests/obsstat/test_alm_conventions.py -q`
- **Definition of done:**
  - Reality condition, spin convention, coordinate frame, normalization metadata enforced
  - Invalid metadata blocks feature export
- **Kill / rollback:** Reject if harmonic coefficients are accepted without convention metadata.

### PR-072 — Low-ell scalar summaries as features, not evidence
- **Owner:** OBSSTAT
- **Depends:** PR-071
- **Verification level:** L2
- **Risk:** medium
- **Primary files:**
  - `htt/obsstat/scalar_lowell.py`
  - `tests/obsstat/test_scalar_lowell.py`
- **Tests / commands:**
  - `python -m pytest tests/obsstat/test_scalar_lowell.py -q`
- **Definition of done:**
  - C_l, S_1/2, parity, planarity computed with explicit definitions
  - Stats are tagged feature_only unless null-calibrated
- **Kill / rollback:** Reject if low-ell feature triggers geometry claim.

### PR-073 — Morphology axes and alignment features
- **Owner:** OBSSTAT
- **Depends:** PR-071, PR-042
- **Verification level:** L2
- **Risk:** high
- **Primary files:**
  - `htt/obsstat/morphology.py`
  - `tests/obsstat/test_morphology.py`
- **Tests / commands:**
  - `python -m pytest tests/obsstat/test_morphology.py -q`
- **Definition of done:**
  - Alignment and planarity features separate diagnostic axis from production axis
  - Look-elsewhere metadata supported
- **Kill / rollback:** Reject if morphology axis bypasses PreferredAxis gate.

### PR-074 — Template-fit diagnostics with orientation scan metadata
- **Owner:** OBSSTAT
- **Depends:** PR-071, PR-073
- **Verification level:** L3
- **Risk:** high
- **Primary files:**
  - `htt/obsstat/template_fit.py`
  - `tests/obsstat/test_template_fit.py`
- **Tests / commands:**
  - `python -m pytest tests/obsstat/test_template_fit.py -q`
- **Definition of done:**
  - Template fit emits amplitude, DeltaChi2, orientation scan volume, covariance assumption
  - Template mean branch is distinct from covariance branch
- **Kill / rollback:** Reject if deterministic template and covariance anomaly are collapsed into one statistic.

### PR-075 — BiPoSH/sparse covariance feature extraction
- **Owner:** OBSSTAT
- **Depends:** PR-071, PR-074
- **Verification level:** L3
- **Risk:** high
- **Primary files:**
  - `htt/obsstat/biposh_features.py`
  - `tests/obsstat/test_biposh_features.py`
- **Tests / commands:**
  - `python -m pytest tests/obsstat/test_biposh_features.py -q`
- **Definition of done:**
  - BiPoSH norms are rotation-aware and convention-tagged
  - Mask/beam/systematic caveat hooks exist
- **Kill / rollback:** Reject if nonzero BiPoSH directly maps to Bianchi geometry claim.

### PR-076 — Null ensembles and look-elsewhere bookkeeping
- **Owner:** OBSSTAT
- **Depends:** PR-072, PR-073, PR-074, PR-075
- **Verification level:** L3
- **Risk:** high
- **Primary files:**
  - `htt/obsstat/null_ensembles.py`
  - `tests/obsstat/test_null_ensembles.py`
- **Tests / commands:**
  - `python -m pytest tests/obsstat/test_null_ensembles.py -q`
- **Definition of done:**
  - FLRW+mask+noise, local/systematic, and injected-template nulls can be represented
  - Look-elsewhere metadata attaches to feature vectors
- **Kill / rollback:** Reject if p-values are produced without null ensemble provenance.

## Wave 8: Transfer provenance, external AniCLASS adapter, and future native solver bridge

### PR-080 — External transfer registry wrapper for current AniCLASS-calibrated path
- **Owner:** BASS_PY
- **Depends:** PR-014, PR-070
- **Verification level:** L2
- **Risk:** high
- **Primary files:**
  - `htt/bass/transfer/aniclass_adapter.py`
  - `htt/bass/transfer/registry.py`
  - `tests/bass/test_external_transfer_registry.py`
- **Tests / commands:**
  - `python -m pytest tests/bass/test_external_transfer_registry.py -q`
- **Definition of done:**
  - Current transfer-dependent paths record AniCLASS_external or empirical_proxy status
  - Claim tier is transfer-conditional
- **Kill / rollback:** Reject if external transfer output is labeled native.

### PR-081 — Future native low-ell adapter stubs with no fake solver implementation
- **Owner:** BASS_PY
- **Depends:** PR-080
- **Verification level:** L2
- **Risk:** medium
- **Primary files:**
  - `htt/bass/transfer/native_adapter.py`
  - `htt/bass/transfer/native_schema.py`
  - `tests/bass/test_native_adapter_stub.py`
- **Tests / commands:**
  - `python -m pytest tests/bass/test_native_adapter_stub.py -q`
- **Definition of done:**
  - Native adapter schema is ready for future solver output
  - No synthetic/native numbers are generated silently
- **Kill / rollback:** Reject if stub returns fake native science values.

### PR-082 — AtlasEntryLite and transfer side-by-side comparison schema
- **Owner:** BASS_PY
- **Depends:** PR-080, PR-081, PR-070
- **Verification level:** L2
- **Risk:** medium
- **Primary files:**
  - `htt/bass/atlas/atlas_entry.py`
  - `tests/bass/test_atlas_entry_lite.py`
- **Tests / commands:**
  - `python -m pytest tests/bass/test_atlas_entry_lite.py -q`
- **Definition of done:**
  - External and future native AtlasEntryLite objects can coexist
  - Atlas membership is not empirical data or posterior
- **Kill / rollback:** Reject if AtlasEntry is consumed as observed data.

### PR-083 — Budget ceiling optimizer policy interface
- **Owner:** BASS_PY
- **Depends:** PR-051, PR-082
- **Verification level:** L3
- **Risk:** high
- **Primary files:**
  - `htt/bass/atlas/budget_ceiling_optimizer.py`
  - `tests/bass/test_budget_ceiling_optimizer.py`
- **Tests / commands:**
  - `python -m pytest tests/bass/test_budget_ceiling_optimizer.py -q`
- **Definition of done:**
  - Ceiling policies output U_C with provenance and valid range
  - MIO F/G can reference ceiling policy explicitly
- **Kill / rollback:** Reject if ceiling policy hides transfer source or prior/admissible set.

### PR-084 — Transfer sensitivity report for current results
- **Owner:** COMMON
- **Depends:** PR-080, PR-082, PR-083, PR-056
- **Verification level:** L3
- **Risk:** medium
- **Primary files:**
  - `scripts/generate_transfer_sensitivity_report.py`
  - `docs/generated/transfer_sensitivity_report.md`
  - `tests/contracts/test_transfer_sensitivity_report.py`
- **Tests / commands:**
  - `python -m pytest tests/contracts/test_transfer_sensitivity_report.py -q`
  - `python scripts/generate_transfer_sensitivity_report.py --dry-run`
- **Definition of done:**
  - Reports which claims depend on external transfer
  - Downstream result cards show transfer-conditional status
- **Kill / rollback:** Reject if external-transfer sensitivity is absent from public report.

## Wave 9: Full-covariance MES synthetic programme

### PR-090 — Full-covariance MES template branch synthetic harness
- **Owner:** COMMON
- **Depends:** PR-074, PR-076, PR-082
- **Verification level:** L3
- **Risk:** high
- **Primary files:**
  - `htt/htt/htt/statistics/mes_template_bound.py`
  - `tests/htt/test_mes_template_bound.py`
- **Tests / commands:**
  - `python -m pytest tests/htt/test_mes_template_bound.py -q`
- **Definition of done:**
  - Template-mean branch computes synthetic bound and no-claim gates
  - Does not replace diagonal MES theorem
- **Kill / rollback:** Reject if template branch is called universal MES.

### PR-091 — Full-covariance MES covariance/BiPoSH branch synthetic harness
- **Owner:** COMMON
- **Depends:** PR-075, PR-076, PR-090
- **Verification level:** L3
- **Risk:** high
- **Primary files:**
  - `htt/htt/htt/statistics/mes_cov_bound.py`
  - `tests/htt/test_mes_cov_bound.py`
- **Tests / commands:**
  - `python -m pytest tests/htt/test_mes_cov_bound.py -q`
- **Definition of done:**
  - Covariance branch uses response rank/singular values and nuisance projection
  - Rank deficiency emits no-claim
- **Kill / rollback:** Reject if rank-deficient response yields finite physical bound.

### PR-092 — Morphological information gain report
- **Owner:** COMMON
- **Depends:** PR-090, PR-091, PR-011
- **Verification level:** L3
- **Risk:** medium
- **Primary files:**
  - `htt/htt/htt/statistics/mes_information_gain.py`
  - `tests/htt/test_mes_information_gain.py`
- **Tests / commands:**
  - `python -m pytest tests/htt/test_mes_information_gain.py -q`
- **Definition of done:**
  - I_morph = B_diag/B_final is computed only when both bounds valid
  - Report distinguishes diag/template/cov/dyn branches
- **Kill / rollback:** Reject if no-gain or invalid bounds are plotted as improvements.

## Wave 10: MIO certificate suite and cross-check outputs

### PR-100 — MIO directional coherence certificate with covariance status
- **Owner:** MIO
- **Depends:** PR-013, PR-040, PR-076
- **Verification level:** L3
- **Risk:** high
- **Primary files:**
  - `htt/mio/coherence/directional.py`
  - `htt/mio/interface/mio_certificate.py`
  - `tests/mio/test_directional_coherence_certificate.py`
- **Tests / commands:**
  - `python -m pytest tests/mio/test_directional_coherence_certificate.py -q`
- **Definition of done:**
  - MIO coherence certificate records covariance/sky support/null status
  - Diagnostic-only status if covariance incomplete
- **Kill / rollback:** Reject if certificate claims truth or posterior odds.

### PR-101 — Redshift-binned coherence and G_F certificate bridge
- **Owner:** MIO
- **Depends:** PR-055, PR-100
- **Verification level:** L3
- **Risk:** high
- **Primary files:**
  - `htt/mio/coherence/redshift_binned.py`
  - `tests/mio/test_redshift_binned_coherence.py`
- **Tests / commands:**
  - `python -m pytest tests/mio/test_redshift_binned_coherence.py -q`
- **Definition of done:**
  - Depth-bin covariance and selection metadata required for production-grade G/coherence
  - Descriptive fallback is explicit
- **Kill / rollback:** Reject if binned coherence ignores bin covariance.

### PR-102 — FLRW tension diagnostic with null predictive distribution gate
- **Owner:** MIO
- **Depends:** PR-076, PR-100
- **Verification level:** L3
- **Risk:** high
- **Primary files:**
  - `htt/mio/tension/flrw_tension.py`
  - `tests/mio/test_flrw_tension_gate.py`
- **Tests / commands:**
  - `python -m pytest tests/mio/test_flrw_tension_gate.py -q`
- **Definition of done:**
  - PPP/tension metrics require calibrated null predictive distribution
  - No PPP claim without null mocks
- **Kill / rollback:** Reject if a raw anomaly p-value is exported as FLRW tension.

### PR-103 — Predictive residual atlas and evidence anatomy without merge
- **Owner:** MIO
- **Depends:** PR-013, PR-065, PR-100
- **Verification level:** L3
- **Risk:** medium
- **Primary files:**
  - `htt/mio/diagnostics/predictive_residuals.py`
  - `htt/mio/decomposition/evidence_anatomy.py`
  - `tests/mio/test_mio_evidence_anatomy_no_merge.py`
- **Tests / commands:**
  - `python -m pytest tests/mio/test_mio_evidence_anatomy_no_merge.py -q`
- **Definition of done:**
  - MIO can summarize residuals and decompose HTT evidence trace narratively
  - No single combined MIO+HTT score
- **Kill / rollback:** Reject if MIO evidence anatomy modifies HTT evidence.

## Wave 11: Result packs, manuscript/figure integration, and external audit freeze

### PR-110 — Result Pack A: scalar-to-morphology upgrade report
- **Owner:** COMMON
- **Depends:** PR-056, PR-076, PR-092
- **Verification level:** L4
- **Risk:** medium
- **Primary files:**
  - `scripts/result_packs/generate_pack_A_scalar_to_morphology.py`
  - `docs/generated/result_pack_A.md`
  - `tests/result_packs/test_pack_A.py`
- **Tests / commands:**
  - `python -m pytest tests/result_packs/test_pack_A.py -q`
  - `python scripts/result_packs/generate_pack_A_scalar_to_morphology.py --dry-run`
- **Definition of done:**
  - Report compares scalar Q/F/Pi with morphology/MES features under caveats
  - No geometry detection claim
- **Kill / rollback:** Reject if report states Bianchi geometry detection.

### PR-111 — Result Pack B: local/global discrimination report
- **Owner:** COMMON
- **Depends:** PR-066, PR-100, PR-101
- **Verification level:** L4
- **Risk:** high
- **Primary files:**
  - `scripts/result_packs/generate_pack_B_local_global.py`
  - `docs/generated/result_pack_B.md`
  - `tests/result_packs/test_pack_B.py`
- **Tests / commands:**
  - `python -m pytest tests/result_packs/test_pack_B.py -q`
  - `python scripts/result_packs/generate_pack_B_local_global.py --dry-run`
- **Definition of done:**
  - Report includes rank audit, local/systematic null FPR, depth gap, directional coherence
  - Global tilt claim tier is conditional at most
- **Kill / rollback:** Reject if rank-deficient cases produce global-tilt candidate language.

### PR-112 — Result Pack C: MIO observatory certificates
- **Owner:** COMMON
- **Depends:** PR-100, PR-101, PR-102, PR-103
- **Verification level:** L4
- **Risk:** medium
- **Primary files:**
  - `scripts/result_packs/generate_pack_C_mio_certificates.py`
  - `docs/generated/result_pack_C.md`
  - `tests/result_packs/test_pack_C.py`
- **Tests / commands:**
  - `python -m pytest tests/result_packs/test_pack_C.py -q`
  - `python scripts/result_packs/generate_pack_C_mio_certificates.py --dry-run`
- **Definition of done:**
  - MIO certificates are gathered with statuses and caveats
  - Diagnostic-only vs production-grade is explicit
- **Kill / rollback:** Reject if certificates are ranked as model posterior odds.

### PR-113 — Manuscript/figure provenance inventory and quarantine updates
- **Owner:** MANUSCRIPT
- **Depends:** PR-011, PR-012, PR-015
- **Verification level:** L3
- **Risk:** medium
- **Primary files:**
  - `scripts/audit_manuscript_figures.py`
  - `docs/generated/manuscript_figure_inventory.md`
  - `docs/generated/missing_figure_references.md`
- **Tests / commands:**
  - `python scripts/audit_manuscript_figures.py --dry-run`
- **Definition of done:**
  - Every includegraphics path is classified resolved/missing/quarantined
  - Manual status numbers and forbidden phrases are found
- **Kill / rollback:** Reject final manuscript freeze while missing figure references remain unexplained.

### PR-114 — External audit package generator
- **Owner:** COMMON
- **Depends:** PR-110, PR-111, PR-112, PR-113
- **Verification level:** L4
- **Risk:** medium
- **Primary files:**
  - `scripts/build_external_audit_package.py`
  - `docs/audit_prompts/`
  - `tests/contracts/test_audit_package_generator.py`
- **Tests / commands:**
  - `python -m pytest tests/contracts/test_audit_package_generator.py -q`
  - `python scripts/build_external_audit_package.py --dry-run`
- **Definition of done:**
  - Audit zip includes code snapshot, reports, manifests, figures inventory, PR status, prompts
  - Auditors can verify local/global, framework, manuscript, and future solver interfaces
- **Kill / rollback:** Reject if audit package omits claim ledger or transfer provenance.

### PR-115 — Publication claim freeze and final hostile review loop
- **Owner:** COMMON
- **Depends:** PR-114
- **Verification level:** L4
- **Risk:** high
- **Primary files:**
  - `docs/generated/publication_claim_freeze.md`
  - `docs/generated/hostile_review_response_matrix.md`
  - `scripts/check_publication_claim_freeze.py`
- **Tests / commands:**
  - `python scripts/check_publication_claim_freeze.py --dry-run`
- **Definition of done:**
  - Every public claim maps to artifact, manifest, tests, caveats, and owner
  - Forbidden claims are blocked before submission
- **Kill / rollback:** Reject if any C5/C6 family-identification claim appears before native low-ell solver morphology atlas.
