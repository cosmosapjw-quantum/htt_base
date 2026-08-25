# Codex handoff — PR-321 bounded HSC SACC repair

## Mission

Repair PR #412 before starting the MES-methodology recovery implementation.

Read:

```text
docs/research_program/post_pr275/audits/pr321_hsc_sacc_reaudit.md
docs/codex_handoff/pr321_reaudit/P0_P1_THREAT_CATALOG.json
docs/codex_handoff/pr321_reaudit/AUDIT_COMPILED_EXEC_PLAN.yaml
```

## Scientific interpretation

The exact 170-element HSC release vector and full covariance are preserved as a
release-snapshot readiness surface.  They are not the fiducial science vector.

The official fiducial selection is:

```yaml
ell_rule: 300 < ell < 1800
selected_centers_per_pair: [350, 500, 700, 900, 1200, 1600]
selected_columns_per_pair_zero_based: [2, 3, 4, 5, 6, 7]
pair_count: 10
fiducial_vector_length: 60
fiducial_covariance_shape: [60, 60]
```

The four tracer `z` and `nz` arrays are required inputs to a theory reference.

## MES boundary

This product is:

```yaml
mes_methodology_role: SCALAR_TOMOGRAPHIC_CONTROL_ONLY
directional_information_status: PROJECTED_OUT_IN_TOMOGRAPHIC_CL_EE
```

It cannot create MES vector/STF moments or local/global evidence.  A future HSC
directional lane requires map/object-level inputs.

## Implementer rules

```yaml
ask_user_questions: false
guess_across_specification_boundary: forbidden
unresolved_spec_action: BLOCKED_BY_UNRESOLVED_SPEC
change_science_expectations_to_fit_code: forbidden
suppress_failure: forbidden
claim_unexecuted_rerun: forbidden
security_or_cryptographic_infrastructure: forbidden
```

Write the named RED tests before production edits.  Do not update the compact
result to a passing terminal until the exact local SACC rerun has executed.

## Required completion report

```yaml
base_sha:
final_sha:
final_tree:
changed_files:
nz_binding:
fiducial_indices:
fiducial_vector_hash:
fiducial_covariance:
ordering_crosscheck:
mes_methodology_role:
status_url_repair:
exact_local_rerun:
focused_tests:
DAG_prefix_preserved:
P0_remaining:
P1_remaining:
verdict:
```
