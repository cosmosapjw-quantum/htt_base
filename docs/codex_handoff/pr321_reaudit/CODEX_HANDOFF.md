# Codex handoff — PR-321 bounded HSC SACC repair

## Mission

Repair PR #412 before starting the MES-methodology recovery implementation.
Do not create a new DAG card.

## Read order

```text
docs/research_program/post_pr275/audits/pr321_hsc_sacc_reaudit.md
docs/codex_handoff/pr321_reaudit/REVIEW_DELTA_20260825.md
docs/codex_handoff/pr321_reaudit/P0_P1_THREAT_CATALOG.json
docs/codex_handoff/pr321_reaudit/AUDIT_COMPILED_EXEC_PLAN.yaml
docs/codex_handoff/pr321_reaudit/EXPECTED_RESULT_SCHEMA.yaml
docs/codex_handoff/pr321_reaudit/MES_PLAN_INTEGRATION_DELTA.yaml
docs/codex_handoff/pr321_reaudit/OFFICIAL_REFERENCE_MATRIX.yaml
docs/codex_handoff/pr321_reaudit/FRESH_CONTEXT_REVIEW_CONTRACT.yaml
```

The review delta controls wherever it is more specific than the initial audit.

## Scientific interpretation

The exact 170-element HSC release vector and full covariance are preserved as a
release-snapshot readiness surface.  They are not the fiducial science vector.

```yaml
ell_rule: 300 < ell < 1800
selected_centers_per_pair: [350, 500, 700, 900, 1200, 1600]
selected_columns_per_pair_zero_based: [2, 3, 4, 5, 6, 7]
pair_count: 10
fiducial_vector_length: 60
fiducial_covariance_shape: [60, 60]
```

The four tracer `z` and `nz` arrays are required theory inputs and must be
validated and content-bound without silent normalization.

## MES boundary

```yaml
mes_methodology_role: SCALAR_TOMOGRAPHIC_CONTROL_ONLY
directional_support_status: NONE_COMPRESSED_ROTATION_INVARIANT_POWER_SPECTRA
vector_tensor_moment_eligibility: FORBIDDEN_NO_DIRECTION_INDEXED_FIELD
local_boost_global_tilt_eligibility: NOT_APPLICABLE_NO_DIRECTIONAL_RESPONSE
CMB_MES_anchor_compatibility: BLOCKED_CROSS_CHANNEL_NO_PHYSICAL_TRANSFER
```

This product cannot create MES vector/STF moments or local/global evidence.  A
future HSC directional lane requires admitted map/object-level inputs.

## Observed-state semantics

Reading and hashing `payload.mean` means the released observed summary statistic
was seen.  This is distinct from computing an HTT statistic or inference.

```yaml
observed_statistic_seen: true
htt_derived_statistic_computed: false
observed_science_inference_executed: false
```

## Required portable identities

Bind exact window support/weights, ordered fiducial indices, selected data-vector
bytes and selected covariance bytes.  The exact official-file local rerun is
mandatory; synthetic CI is not a substitute.

## Cross-stack gate

After repair, the MES implementation branch must descend from the repaired
PR-321 head and contain the exact accepted PR-411 package.  Otherwise stop with:

```text
BLOCKED_MES_PLAN_NOT_DESCENDED_FROM_REPAIRED_PR321
```

## Implementer policy

```yaml
ask_user_questions: false
guess_across_specification_boundary: forbidden
unresolved_spec_action: BLOCKED_BY_UNRESOLVED_SPEC
change_science_expectations_to_fit_code: forbidden
suppress_failure: forbidden
claim_unexecuted_rerun: forbidden
security_or_cryptographic_infrastructure: forbidden
```

Write the named RED tests before production edits.  Do not promote the compact
result until the exact local SACC rerun executes.

## Completion report

```yaml
base_sha:
final_sha:
final_tree:
changed_files:
nz_binding:
fiducial_indices:
fiducial_vector_hash:
fiducial_covariance:
window_digests:
ordering_crosscheck:
observed_state:
mes_methodology_role:
cross_channel_anchor_status:
status_url_repair:
exact_local_rerun:
focused_tests:
DAG_prefix_preserved:
PR411_package_identity:
P0_remaining:
P1_remaining:
unresolved_blockers:
verdict:
```
