# Code And Results Audit Report

owner: COMMON
implementation_scope: research_program_audit
claim_tier: diagnostic_only
transfer_source: mixed_none_external_proxy_and_public_input_pending
sky_support_status: audit_only_mixed
null_mock_status: audit_only_mixed
config_hash: sha256:d10a6916e78db3574c55f7e19201e7e06c15184471cc52ce6d35deb1f15ab1b4
generating_command: manual audit from repo-local harness commands and external-source checks, 2026-06-26
git_commit_or_worktree_state: 8e104e573d78fd515044e6c268edb3d46e4c5d51 with dirty .claude/settings.json and .codex/rules/default.rules before this report
caveats:
- Diagnostic audit only; this report does not promote any result.
- Current data rows remain blocked unless their named external inputs and provenance manifests are present.
- External/proxy transfer rows remain transfer-conditional and non-native.
- Native-atlas-dependent family language remains outside the current claim envelope.

## Input Hashes

| Input | SHA256 |
| --- | --- |
| `AGENTS.md` | `caf78d6d3cca82265b16553ef98c4d2065ace001e13e873b8f72c15d3f65453a` |
| `docs/research_program/BLOCKERS.md` | `948b22608b24b3e9aeb4cd2db896fdcec63dc35cad156045f789556197fd62c0` |
| `docs/codex_handoff/pr_backlog.yaml` | `767c978d69408bc58264991b67ad07b5435566184b136a2e36b285e7ce38b8ae` |
| `docs/codex_handoff/pr_status.yaml` | `67cbf046bd1cb45831f5a508d1f935855324d469aea87bedacace03837b0cbc8` |
| `docs/generated/egs_results_table.json` | `be0885b8e963990636f963fa9483d92d99f78a671aed076a3a510c60ac3a92df` |
| `docs/generated/egs_results_table.md` | `ef52fa6814548e3ed8fe35703d7f1bb1127ad7670000fb5e02e84956e07314b8` |
| `docs/harness/CLAIM_LEDGER.md` | `88dd78c1ac6163398fb59dfde9099e3da626939a491efb65beb756ba6757c132` |
| `docs/harness/VALIDATION_LEDGER.md` | `fa59f8e924b209fe2d7fc712bf5e631bdd846ba45985d56c5f9e467e19fb50d5` |
| `docs/research_program/pr07/BLOCKER_RESOLUTION_MATRIX.md` | `57b08112978aee95be25c68dd7d5b2560373a80ddad5fc07aeeb9affb83f1677` |
| `docs/research_program/egs2/BLOCKER_DISCHARGES.md` | `03186afca2a553f7e2dc09ab09e6164a53dac8ded1eee1d5335ab85751a94c60` |
| `docs/research_program/egs3/BLOCKER_SOLUTIONS.md` | `fa57108d69263f577efc2f7f06b7fd9827ecd09154709ab0f0555bb797cb3e9c` |
| `Makefile` | `0cbfbe14f0c73d84e236ea91ca3193f768b2f05cb535fb641056f24014b7be4c` |

External sources checked:

- Planck Legacy Archive official portal: https://pla.esac.esa.int/
- Planck PR4/NPIPE overview mirrored by the CMB-S4 data portal: https://data.cmb-s4.org/planck_pr4.html
- Hoffman et al. CF4 WF/CR paper, arXiv:2311.01340: https://arxiv.org/abs/2311.01340
- MNRAS version of the CF4 velocity-field paper: https://academic.oup.com/mnras/article/527/2/3788/7419869

## Verdict

Overall status: INTERNAL ONLY for any public measurement claim, PASS WITH BLOCKERS for the pre-solver framework.

The repository now has a complete 62-card pre-solver PR-DAG, strong contract boundaries, portable research gates, and a consolidated EGS result table. The strongest current publishable content is theorem/method content plus clearly labelled synthetic mechanics. The repo is not ready for a published calibrated measurement because the K1, K5, and K6 data rows still depend on external inputs or ownership, and several generated/provenance surfaces are stale.

Minimal allowed claim: this is a claim-tiered, manifest-backed, transfer-provenance-aware pre-solver framework with implemented gates for theorem/mechanics evidence and named blocked measurement channels.

Claims still rejected:

- native low-ell solver output from this repo;
- native-atlas-dependent family/classification language;
- external/proxy transfer promoted into native status;
- MIO diagnostic content merged into HTT evidence semantics;
- global low-ell significance from local or synthetic stand-ins;
- physical vorticity inference from a curl-suppressed field.

## Evidence Summary

Code/result surface inspected:

- 1,066 code/config/data-contract files under `htt/src`, `htt/obsstat`, `htt/mio`, `htt/bass`, `htt/htt/htt`, `src`, `tests`, `research_gates`, and `scripts`.
- 485 files under `docs/research_program`, `docs/generated`, and primary current/observed/conditioned figure trees.
- 232 image/PDF assets and 144 figure manifests under `figures`.
- 104 top-level generated files under `docs/generated`.

Fresh command evidence:

| Command | Result | Audit use |
| --- | ---: | --- |
| `venv/bin/python scripts/codex_harness/validate_pr_dag.py docs/codex_handoff/pr_backlog.yaml` | PASS | 62-card DAG valid. |
| `venv/bin/python scripts/codex_harness/progress_report.py docs/codex_handoff/pr_backlog.yaml docs/codex_handoff/pr_status.yaml --checkpoint-every 5 --json` | PASS | 62/62 complete; dependency-weighted and critical-path completion both 100%. |
| `env -u PYTHONPATH venv/bin/python scripts/codex_harness/run_subset.py smoke` | PASS | 6 passed, 7750 deselected. |
| `env -u PYTHONPATH venv/bin/python scripts/codex_harness/run_subset.py collect` | PASS | 7697/7756 collected, 59 deselected. |
| `env -u PYTHONPATH venv/bin/python scripts/codex_harness/run_subset.py package` | PASS | 12 package/import tests passed. |
| `make pr04-forbidden-deps` | PASS | No forbidden PR04 dependency findings. |
| PR04 unittest gate command | PASS | 23 PR04 tests passed. |
| EGS2 unittest gate command | PASS | 13 EGS2 tests passed. |
| EGS3 unittest gate command | PASS | 20 EGS3 tests passed. |
| PR07 unittest gate command | PASS | 16 PR07 tests passed. |
| `env -u PYTHONPATH venv/bin/python -m pytest tests/contracts tests/obsstat tests/mio tests/htt tests/result_packs research_gates/egs2 research_gates/egs3 research_gates/pr07 -q` | FAIL | 852 passed, 8 failed; all failures are stale generated/provenance or manifest-policy checks. |
| `venv/bin/python scripts/check_claim_language.py --dry-run --format json docs/research_program docs/generated docs/harness README.md` | FAIL | 1 current broad-scan finding in a PR04 audit prompt. |
| `venv/bin/python .agents/skills/htt-claim-provenance-ledger/scripts/check_forbidden_claims.py docs/research_program docs/generated docs/harness README.md` | FAIL | 5 existing broad-scan findings in generated/report surfaces. |
| `venv/bin/python .agents/skills/htt-claim-provenance-ledger/scripts/check_claim_status.py docs/research_program docs/generated docs/harness README.md` | FAIL | Several existing strong-claim phrases lack nearby status markers. |
| `venv/bin/python scripts/audit_manuscript_figures.py --dry-run` | PASS with findings | 126 includegraphics refs, 126 resolved, 0 missing, 0 quarantined, 5 text risk findings. |
| `venv/bin/python scripts/check_artifact_manifests.py --dry-run` | FAIL | Several current/observed manifests miss required fields or use non-canonical sky-support labels. |
| `venv/bin/python .agents/skills/htt-scientific-code-validation/scripts/check_no_mock_results.py` | FAIL | Pre-existing calibration/mock-result markers in legacy docs/code and audit histories. |

## Code Map

The repo is structurally coherent around the intended ownership lanes:

- `common/contracts` and `htt/src/common`: artifact manifests, owner/tier/scope contracts, semantic guards, transfer registry, sky support, status snapshots, mock calibration, and generated claim ledgers.
- `obsstat`: observable feature extraction, low-ell scalar/map features, morphology, BiPoSH, null ensembles, CF4 catalog/affine/bulk-flow mechanics, and EGS theorem/mechanics modules.
- `bass` / `bass_py`: current external/proxy transfer wrappers, future native schema boundaries, atlas metadata, and semi-native single-mode transfer mechanics.
- `htt`: likelihood, local/global discrimination, posterior adequacy gates, PPC/LOOCV-style support, null competition, prior sensitivity, and result-pack assembly.
- `mio`: diagnostic x/Q/Pi/F/G_F formalism, coherence reports, predictive residuals, and MIO interface surfaces.
- `tsc_legacy`: compatibility and reproduction only.
- `research_gates`: portable PR04/PR07/EGS2/EGS3 theorem/property gates.
- `src`: Rust-side legacy or future native-solver substrate; no current audit command promoted it to native low-ell solver output.

This layering is a strength. The live failures are mostly generated-surface freshness, claim wording, and figure-manifest policy drift, not core module import breakage.

## Research Results Audit

The controlling generated result surface is `docs/generated/egs_results_table.json` / `.md`.

Status counts:

- `proven_symbolic`: 6
- `proven_gate`: 8
- `blocked`: 3

Allowed interpretation:

- The 14 non-blocked rows are theorem/gate/mechanics evidence under stated assumptions.
- The 3 blocked data rows are K1, K5, and K6. They emit only labelled synthetic stand-ins or awaiting-input rows.
- `blockers_open` includes K1 E2E access, K5 release-matched mock ownership, K6 field-realization access, and the native low-ell solver ceiling.
- The result table explicitly records `native_solver_result=false` and blocks family/classification promotion.

Main scientific strengths:

- The PR04/PR07/EGS2/EGS3 gate suite passes in the portable local environment.
- The EGS result table keeps theorem rows separate from data rows.
- K1, K5, and K6 have mechanics-ready code paths, but still terminate with blocker codes.
- The research programme has explicit ticketing and dependency order for PR08 and PR10.

Main scientific limits:

- No real global K1 p-value is discharged without FFP10/NPIPE or equivalent E2E simulation ownership.
- No K6 curl/vorticity posterior is discharged without a constrained 3D field realization ensemble.
- No K5 cosmic-variance coverage is discharged without release-matched CF4 forward mocks.
- No joint PR08-006 artifact is valid until K1, K5, and K6 are separately discharged and cross-covariance/provenance is registered.
- PR10 native low-ell solver work is separate from this repo's completed pre-solver DAG.

## Major Findings

### F1. Canonical DAG complete, narrative handoff stale

Severity: high for operator handoff, low for code behavior.

Fresh progress output reports 62/62 completed PR-DAG cards and a fully complete critical path. However `docs/harness/PROJECT_STATE.md` still says the current position is PR-075 and next topological PR is PR-055. That narrative surface is stale relative to the machine-readable status and the rev-r126 research-program blocker dossier.

Required fix: regenerate or revise `docs/harness/PROJECT_STATE.md`, `docs/harness/PR_PROGRESS.md`, and adjacent handoff summaries from the same status authority used by `progress_report.py`.

### F2. Targeted research/contracts suite has stale generated artifacts

Severity: high for release packaging, medium for research execution.

The focused suite returned 852 passed and 8 failed. Failures are:

- stale CF4++ LNB provenance report;
- stale code-capability audit manifest;
- stale current manuscript figure artifacts;
- missing `promotion_blockers` in `figures/current/fig_pr04_a1_rank_ladder.manifest.json`;
- stale external research input archive/inventory hashes;
- stale PDF claim-lint report;
- stale semantic firewall fuzz report.

Required fix: run the relevant `--write` generators in a controlled PR, review the diffs, then rerun the same failing tests plus claim scanners.

### F3. Figure-manifest policy is not globally clean

Severity: high for any manuscript or external audit package.

`scripts/audit_manuscript_figures.py --dry-run` now reports 126 resolved figure references and no missing/quarantined manuscript figure references. That is a major improvement over older handoff text. But `scripts/check_artifact_manifests.py --dry-run` still fails on current and observed manifests, including missing `input_hashes`, missing git/worktree state, missing `config_hash` or `generating_command`, and non-canonical sky-support labels such as CF4-specific strings where canonical sky-support status vocabulary is required.

Required fix: repair manifests, not captions. Each promoted figure needs owner, scope, claim tier, transfer source, config hash, input hashes, sky/mask status, null/mock status, caveats, generating command, and git/worktree state.

### F4. Broad claim scanners still find unsafe or underspecified text

Severity: high for public-facing docs, medium for internal archives.

Broad scans over `docs/research_program`, `docs/generated`, `docs/harness`, and `README.md` fail. Some findings are likely scanner-overbroad because they appear inside negative guardrails or blocked/proposed rows, but they are still real audit debt because public scanners cannot infer intent reliably.

Required fix: either downword the flagged text into scanner-safe phrasing, or add narrow path/row-level exemptions only where the document is generated, hash-bound, and explicitly diagnostic-only.

### F5. Mock-result leakage checker remains noisy

Severity: medium.

The mock/leakage checker fails on historical calibration-factor and mock-result markers in old audit docs, legacy scripts, tests, and generated figures. Several PR deltas already document this as pre-existing. The risk is not that these entries are new, but that repo-wide check failure weakens future gating unless scoped.

Required fix: split the checker into active production surfaces versus archived/historical surfaces, then require active-surface zero findings.

### F6. Blocker dossier is scientifically honest but operationally incomplete

Severity: high for execution planning.

`docs/research_program/BLOCKERS.md` correctly separates theorem/mechanics evidence from measured content and keeps K1/K5/K6 blocked. It also correctly keeps PR10 as a separate native solver project. What it does not yet provide is an operator-grade runbook with exact acquisition manifests, summary schemas, command order, storage layout, expected output rows, and failure taxonomy for each blocker discharge.

Required fix: use `docs/research_program/BLOCKER_RESOLUTION_PLAN.md` as the operational companion to the blocker dossier.

## Role-Based Review

Code mapper:

- The module boundaries mostly match the repo contract. The most important architectural risk is duplicated status authority: generated status says one thing, narrative handoff docs can lag.

Harness engineer:

- Smoke, collect, package, DAG, and portable research-gate checks pass.
- The failing checks are freshness/provenance checks and should be fixed before any external audit package.

Physics/statistics auditor:

- The theorem rows are credible only as theorem/gate/mechanics rows.
- The data rows are not calibrated measurements until their input ensembles are owned and hash-bound.
- Synthetic stand-ins must stay visible as synthetic.

Claim-gate reviewer:

- The claim envelope is mostly encoded correctly, but broad scanners still fail.
- Scanner-safe wording should be treated as a release requirement, not a cosmetic cleanup.

Manuscript/figure reviewer:

- Manuscript figure references resolve, but artifact manifests still fail globally.
- The five theorem-extension figure text risk findings need repair or documented quarantine before freeze.

Skeptical native-atlas reviewer:

- There is no current basis for native-atlas-dependent family/classification language.
- Semi-native single-mode shear transfer is useful bridge work, not a full morphology atlas.

## Recommended Audit PRs

1. Stale generated-surface repair PR:
   - run the named stale generators;
   - commit regenerated JSON/Markdown/manifests only after review;
   - rerun the 8 failing tests.

2. Manifest policy repair PR:
   - update invalid current/observed manifests;
   - normalize sky-support labels;
   - rerun `scripts/check_artifact_manifests.py --dry-run`.

3. Claim-scan cleanup PR:
   - repair broad-scan findings in active report surfaces;
   - add narrow generated-surface exemptions only when hash-bound;
   - rerun claim-language, forbidden-claim, and claim-status scanners.

4. Handoff authority repair PR:
   - regenerate stale narrative project-state docs from the current status authority;
   - preserve the 62/62 DAG result and current research-program blockers.

5. Data-discharge preparation PR:
   - create exact K1/K5/K6 input manifests and summary schemas before downloading or processing external data.

## Release Decision

Do not publish a calibrated measurement yet.

The current repo is suitable for internal audit, theorem/mechanics review, and blocker-discharge preparation. It is not suitable for a public measurement package until:

- the 8 focused stale/provenance test failures are fixed;
- artifact manifest dry-run passes or quarantines all remaining invalid surfaces;
- broad active-claim scans pass;
- K1/K5/K6 input ownership and provenance are present;
- PR08-006 is assembled only from discharged component rows.
