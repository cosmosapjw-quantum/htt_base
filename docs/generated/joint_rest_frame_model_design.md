# Joint Rest-Frame Identifiability Harness Design

owner: HTT
implementation_scope: htt
claim_tier: diagnostic_only
transfer_source: none
sky_support_status: not_bound
mask_status: not_bound
covariance_status: supplied_positive_definite_required
null_mock_status: not_bound
production_status: pre_inference_gate
native_solver_result: false
family_identification: false
caveats:
- pre-inference diagnostic rank gate only
- matched nulls, PPC, LOOCV, and covariance sensitivity remain separate gates
- survey-axis metadata may be unbound or toy unless supplied by caller
- not evidence-grade output
- not native solver validation
- not family or geometry identification
config_hash: `sha256:99579b5db3b5c36927e19a1008d8dbd7105c1202746a3c1f3eca9fc4a8b4df29`
input_hashes:
- `sha256:c681cef2a8b3d3bc7551cf4cf42134b0b6ea35ef9ef2c4f0af9635885d4bf13a`
- `sha256:43a0d59c6159f3f9daf3c872840c862bae71c7f9cd26e1b769ea354b8e43d13f`
- `sha256:04c28cb31c8f97cb54b56f491d8b80f19ce9422c94766fd03ee2429a9a8e68d1`
- `sha256:c5a68f2cb5ad2425e21a3329b4b1f574021e7ecbe8c2146a4e505d9d30a29da8`
input_sources:
- `docs/superpowers/plans/2026-06-20-external-audit-research-program-integration.md`
- `htt/htt/htt/rest_frame/joint_model.py`
- `htt/htt/htt/rest_frame/validation.py`
- `htt/htt/htt/rest_frame/cross_survey_covariance.py`
generating_command: `Codex apply_patch REV-R083; venv/bin/python -B -m pytest -p no:cacheprovider -q tests/htt/test_joint_rest_frame_model.py tests/htt/test_rest_frame_validation.py tests/htt/test_nuisance_rank.py htt/test_packaging_imports.py`
git_commit_or_worktree_state: `6092034+dirty`
artifact_path: docs/generated/joint_rest_frame_model_design.md

## Scope

REV-R083 adds a pre-inference HTT identifiability harness for joint rest-frame response blocks. It evaluates whether a global rest-frame offset response remains identifiable after whitening by covariance and projecting out observer-CMB boost, local-flow basis, and survey/systematic nuisance responses.

The rank-gate expression is:

```text
R_g_perp = P_nuis_perp C^{-1/2} R_g
```

The output is a diagnostic rank gate with singular values, projected rank, rank tolerance, computed rank threshold, channel-ablation stability, survey-axis overlap metadata, and no-claim reasons. It is not an HTT evidence term and does not authorize a public local/global result.

Survey-axis metadata is carried separately from the overlap scalar:

- axis vector in response-channel space,
- axis frame,
- axis provenance,
- sky-support status,
- mask status,
- covariance status,
- null/mock status.

Toy or unbound survey-axis metadata remains explicitly marked as not externally interpreted, and therefore cannot promote a local/global interpretation.

## Validation Summary

The validation summary records:

- prior-support sensitivity status,
- matched-null status,
- PPC status,
- leave-one-probe/bin-out status,
- covariance-sensitivity status.

All statuses passing clears the validation blocker list and records `validation_preconditions_passed=true`, but `evidence_grade_allowed` remains false in this harness. Evidence-grade use still requires a downstream claim-tier gate with bound artifacts, not only status strings.

## Promotion Blockers

- response rank deficient after nuisance projection,
- channel ablation unstable,
- survey-axis overlap not externally interpreted,
- matched nulls absent or failed,
- PPC absent or failed,
- leave-one-probe/bin-out validation absent or failed,
- covariance sensitivity absent or failed,
- no native morphology atlas and no native low-ell solver output.

## Safe Use

This artifact may be used as a pre-inference rank and validation precondition report. It must not be used as a likelihood, posterior, evidence term, MIO certificate, native solver validation, geometry claim, or Bianchi family-identification result.
