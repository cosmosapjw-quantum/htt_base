# REV-R083 - Joint rest-frame identifiability harness

## Scope

- Owner: HTT.
- Plan source: `docs/superpowers/plans/2026-06-20-external-audit-research-program-integration.md`.
- Canonical PR DAG status remains complete at `62/62`; canonical `PR-083` is unrelated budget-ceiling work. This supplemental delta tracks the revision-slice task named `REV-R083`.
- Claim ceiling: `diagnostic_only`.

## Evidence read

- `AGENTS.md`
- `.agents/skills/htt-dag-orchestrator/SKILL.md`
- `.agents/skills/htt-local-global-discrimination/SKILL.md`
- `.agents/skills/htt-physics-math-audit/SKILL.md`
- `.agents/skills/htt-harness-engineering/SKILL.md`
- `.agents/skills/htt-claim-firewall/SKILL.md`
- `.agents/skills/htt-scientific-code-validation/SKILL.md`
- `.agents/skills/htt-adversarial-review-loop/SKILL.md`
- `htt/htt/htt/infer/nuisance_rank.py`
- `htt/htt/htt/departure/response_overlap.py`
- `htt/htt/htt/departure/local_global_mixture.py`
- `htt/htt/htt/rest_frame/cf4_likelihood.py`
- `htt/htt/htt/rest_frame/__init__.py`
- `tests/htt/test_nuisance_rank.py`
- `tests/htt/test_response_overlap.py`
- `htt/test_packaging_imports.py`

## Web/doc checks

- WEB_CHECK_STATUS: done.
- NumPy SVD documentation checked for singular-value semantics: <https://numpy.org/doc/stable/reference/generated/numpy.linalg.svd.html>.
- NumPy `eigh` documentation checked for symmetric covariance eigendecomposition: <https://numpy.org/doc/stable/reference/generated/numpy.linalg.eigh.html>.
- NumPy `matrix_rank` documentation checked for SVD-rank/tolerance semantics: <https://numpy.org/doc/stable/reference/generated/numpy.linalg.matrix_rank.html>.

## Divergence and review

- code cartographer:
  - Steelman: mirror `nuisance_projected_rank` rank geometry in `htt.rest_frame`, export the new modules from `htt.rest_frame`, and add package smoke coverage.
  - Attack: duplicate rank implementations can drift; the new harness should remain a small diagnostic wrapper, not an inference surface.
- harness engineer:
  - Steelman: red-test missing `joint_model` and `validation`, then run focused rank/validation/nuisance tests, package imports, claim scan, smoke, collect-only, and DAG checks.
  - Attack: canonical `PR-083` status is not this revision task; docs and delta must explicitly track REV-R083.
- physics/statistics auditor:
  - Steelman: whitening by `C^{-1/2}`, nuisance projection, SVD-rank, channel ablation, and survey-axis overlap are the right pre-inference checks.
  - Attack: all validation statuses passing must not automatically become evidence-grade authorization; rank candidate is still diagnostic only. Post-fix review also required separate input rank tolerance versus computed rank threshold, unique channel labels for ablation keys, and explicit survey-axis sky/mask/covariance/null/provenance metadata.
- claim-gate reviewer:
  - Steelman: safe claim is `pre_inference_rank_candidate` or `no_claim_rank_deficient`.
  - Attack: no family/geometry/native/MIO/evidence language can appear in payloads or docs.
- regression tester:
  - Steelman: protect `tests/htt/test_nuisance_rank.py`, `tests/htt/test_response_overlap.py`, REV-R081 CF4 likelihood, and package imports.
  - Attack: committing `__init__.py` without the new modules would break `htt.rest_frame` imports.

Subagents closed: code cartographer, harness engineer, physics/statistics auditor, claim-gate reviewer, and post-fix physics/statistics reviewer.

## Implemented changes

- Added `htt.rest_frame.cross_survey_covariance`:
  - positive-definite covariance validation,
  - inverse square-root covariance helper.
- Added `htt.rest_frame.joint_model`:
  - `RestFrameResponseBlocks`,
  - `evaluate_joint_rest_frame_rank_gate`,
  - `JointRestFrameRankAudit`,
  - separate input `rank_tolerance` and computed `rank_threshold`,
  - unique channel-label validation,
  - channel-ablation stability,
  - survey-axis overlap plus sky/mask/covariance/null/provenance metadata.
- Added `htt.rest_frame.validation`:
  - `RestFrameValidationSummary`,
  - prior/matched-null/PPC/leave-one-out/covariance-sensitivity status blockers,
  - `validation_preconditions_passed` separate from `evidence_grade_allowed`.
- Updated `htt.rest_frame` package exports and package import smoke.
- Added tests:
  - `tests/htt/test_joint_rest_frame_model.py`
  - `tests/htt/test_rest_frame_validation.py`
- Added design artifact:
  - `docs/generated/joint_rest_frame_model_design.md`
- Added revision checkpoint:
  - `docs/generated/progress_checkpoints/revision_checkpoint_rev_r083.md`

## Artifact metadata

- owner: HTT
- implementation_scope: `htt`
- claim_tier: `diagnostic_only`
- transfer_source: `none`
- sky_support_status: `not_bound`
- mask_status: `not_bound`
- covariance_status: `supplied_positive_definite_required`
- null_mock_status: `not_bound`
- production_status: `pre_inference_gate`
- native_solver_result: false
- family_identification: false
- caveats:
  - pre-inference diagnostic rank gate only
  - matched nulls, PPC, LOOCV, and covariance sensitivity remain separate gates
  - survey-axis metadata may be unbound or toy unless supplied by caller
  - not evidence-grade output
  - not native solver validation
  - not family or geometry identification
- config_hash: `sha256:99579b5db3b5c36927e19a1008d8dbd7105c1202746a3c1f3eca9fc4a8b4df29`
- input_hashes:
  - `sha256:c681cef2a8b3d3bc7551cf4cf42134b0b6ea35ef9ef2c4f0af9635885d4bf13a`
  - `sha256:43a0d59c6159f3f9daf3c872840c862bae71c7f9cd26e1b769ea354b8e43d13f`
  - `sha256:04c28cb31c8f97cb54b56f491d8b80f19ce9422c94766fd03ee2429a9a8e68d1`
  - `sha256:c5a68f2cb5ad2425e21a3329b4b1f574021e7ecbe8c2146a4e505d9d30a29da8`
- generating_command: `Codex apply_patch REV-R083; focused pytest and claim scan commands below`
- git_commit_or_worktree_state: `6092034+dirty`

## Validation

| Command | Result | Notes |
|---|---:|---|
| `venv/bin/python -B -m pytest -p no:cacheprovider -q tests/htt/test_joint_rest_frame_model.py tests/htt/test_rest_frame_validation.py tests/htt/test_nuisance_rank.py` before implementation | FAIL | Red phase: `6 failed, 3 passed`, missing `joint_model` and `validation`. |
| `venv/bin/python -B -m pytest -p no:cacheprovider -q tests/htt/test_joint_rest_frame_model.py tests/htt/test_rest_frame_validation.py tests/htt/test_nuisance_rank.py` | PASS | `9 passed`; joint rank, validation, nuisance-rank regression. |
| `venv/bin/python -B -m pytest -p no:cacheprovider -q tests/htt/test_joint_rest_frame_model.py tests/htt/test_rest_frame_validation.py tests/htt/test_nuisance_rank.py htt/test_packaging_imports.py` | PASS | `21 passed`; includes package import smoke after reviewer fixes. |
| `venv/bin/python -B -m py_compile htt/htt/htt/rest_frame/joint_model.py htt/htt/htt/rest_frame/validation.py htt/htt/htt/rest_frame/cross_survey_covariance.py htt/htt/htt/rest_frame/__init__.py tests/htt/test_joint_rest_frame_model.py tests/htt/test_rest_frame_validation.py` | PASS | Touched Python files compile. |
| `venv/bin/python -B -m pytest -p no:cacheprovider -q tests/htt/test_response_overlap.py tests/htt/test_cf4_likelihood.py tests/htt/test_local_global_mixture.py tests/htt/test_inference_adequacy_gates.py htt/test_packaging_imports.py` | PASS | `43 passed`; adjacent HTT local/global, CF4, adequacy, and package regression. |
| `venv/bin/python -B -m pytest -p no:cacheprovider -m smoke -q` | PASS | `6 passed, 7588 deselected`. |
| `venv/bin/python -B -m pytest -p no:cacheprovider --collect-only -q` | PASS | `7535/7594 tests collected, 59 deselected`. |
| `venv/bin/python -B scripts/codex_harness/validate_pr_dag.py docs/codex_handoff/pr_backlog.yaml` | PASS | `OK: 62 PRs, DAG valid`. |
| `venv/bin/python -B scripts/codex_harness/progress_report.py docs/codex_handoff/pr_backlog.yaml docs/codex_handoff/pr_status.yaml --checkpoint-every 5` | PASS | Canonical DAG remains `62/62 = 100.0%`; this REV-R083 slice is supplemental and tracked by `revision_checkpoint_rev_r083.md`. |
| `venv/bin/python -B scripts/check_claim_language.py --dry-run ...REV-R083 files...` | PASS | No forbidden claim language detected in code, tests, delta, design, or checkpoint. |
| `git diff --check` | PASS | No whitespace errors. |

## Review loop

- Initial review loop found missing modules/docs and one rank-fixture mismatch; fixed by adding implementation, docs, package exports, and independent global-response fixture.
- Post-fix physics/statistics review found three blockers:
  - `rank_tolerance` exposed the computed threshold instead of the input tolerance,
  - channel-ablation statuses could collapse under duplicate channel labels,
  - survey-axis diagnostics lacked explicit directional/statistical provenance.
- Final patch:
  - keeps `rank_tolerance=1.0e-10`,
  - adds `rank_threshold`,
  - rejects duplicate `channel_labels`,
  - adds `survey_axis_metadata` with axis vector, frame, provenance, sky support, mask, covariance, and null/mock statuses.

## Claim-tier impact

This revision creates no HTT evidence term, no posterior odds, no MIO certificate, no native solver result, no observed local/global result, and no Bianchi family-identification support. It creates a pre-inference HTT diagnostic rank/validation gate.

Residual blockers:

- matched null artifacts not bound here,
- PPC and leave-one-probe/bin-out artifacts not bound here,
- covariance-sensitivity artifacts not bound here,
- local/global result interpretation remains blocked without downstream gates,
- native morphology atlas absent.
