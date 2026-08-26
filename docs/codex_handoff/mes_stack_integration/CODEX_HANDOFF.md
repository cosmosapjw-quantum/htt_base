# Codex handoff — integrate and implement the recovered MES methodology

## Authority

```yaml
repository: cosmosapjw-quantum/htt_base
planning_branch: analysis/mes-methodology-stack-integration-20260826
integration_base_merge_sha: 1ace5692bb6778ee8d5b99c112fc84dc2ec8cb72

first_parent:
  PR: 412
  sha: 4733a4c6dbc638372dee7f99ac38f39dba56d933
  role: repaired current data/code stack

second_parent:
  PR: 411
  sha: 5a3825f903546891fd90e3d708481707d59babf4
  role: exact MES methodology recovery package

source_only:
  PR404_plan_head: 14bbb5bb264caa62fd47eb7cd7863f0a3367b1ea
  PR403_evidence_head: 883a7cf41116e6740b1bac9b76a5e9c6b3fd188e
```

Read in order:

```text
docs/codex_handoff/mes_stack_integration/PACKAGE_INDEX.yaml
docs/codex_handoff/mes_stack_integration/AUTHORITY_AND_ANCESTRY.yaml
docs/codex_handoff/mes_stack_integration/SOURCE_IMPORT_MANIFEST.yaml
docs/codex_handoff/mes_stack_integration/PR_DISPOSITION_LEDGER.yaml
docs/codex_handoff/mes_stack_integration/P0_P1_THREAT_CATALOG.json
docs/codex_handoff/mes_stack_integration/INVARIANT_TEST_MATRIX.yaml
docs/codex_handoff/mes_stack_integration/AUDIT_COMPILED_EXEC_PLAN.yaml
docs/codex_handoff/mes_methodology_recovery/PACKAGE_INDEX.yaml
docs/codex_handoff/mes_methodology_recovery/CODEX_HANDOFF.md
docs/codex_handoff/pr315_audit_compiled_exec_plan.yaml
docs/codex_handoff/PR315_CODEX_HANDOFF.md
docs/codex_handoff/mes_stack_integration/FRESH_CONTEXT_REVIEW_CONTRACT.yaml
```

## Mission

Do not create another planning PR. After human acceptance, start one
implementation branch from the exact accepted integration head and execute the
compiled units in order.

```text
MSI-WU-000 append-only DAG allocation
→ MSI-WU-001 theory receipts
→ MSI-WU-002 PR315 joint cut-sky repair
→ MSI-WU-003 rowwise active MES anchors
→ MSI-WU-004 direction-indexed vector/STF bridge
→ MSI-WU-005 exact 300-pair Planck MES result
→ MSI-WU-006 physical local/global responses
→ MSI-WU-007 first eligible low-z directional lane
→ MSI-WU-008 portable evidence and review
```

The `MSI-WU-*` names are planning aliases. Allocate canonical IDs from the live
DAG generator only after re-reading all open stacks.

## Hard locks

- The generic Planck 12-feature result is a benchmark control, not the MES result.
- Preserve `133/301` and the five exact PR-314 evidence files.
- Preserve the intentional SMICA-only exact-300-pair fast path.
- Do not wait for Commander or 999 CMB-only rows for Paper A.
- Do not bulk merge any source-only or superseded branch.
- Do not import legacy `planck_mes_bounds.py` into observed code.
- A scalar value cannot create a direction or STF tensor.
- PR-321 HSC SACC is not a directional low-z lane.
- Planck alone cannot identify local boost versus global tilt.
- No security, cryptographic authority, privileged launcher or anti-tamper work.
- Existing DAG nodes and edges are immutable.

## Source PR handling

Follow `PR_DISPOSITION_LEDGER.yaml`.

- PR-411 is already a merge parent; do not cherry-pick it again.
- PR-403 evidence and PR-404 plan are already exact imports.
- PR-385/386 are already ancestors.
- Do not merge PR-387/388 or PR-405..408 into the implementation branch.
- Do not close any PR automatically. Produce a human-action disposition list at
  MSI-WU-008.

## Weak-agent policy

```yaml
ask_user_questions: false
guess_across_specification_boundary: forbidden
unresolved_spec_action: BLOCKED_BY_UNRESOLVED_SPEC
change_expected_science_to_fit_code: forbidden
change_reference_outputs_without_authority: forbidden
suppress_failure: forbidden
claim_unexecuted_work: forbidden
another_planning_successor: forbidden
```

## Verification policy

Use:

```text
targeted tests
→ negative/metamorphic tests
→ directly affected integration
→ existing focused CI
```

Do not run the full repository suite unless a distinct failure class requires it.

## Low-z lane gate

Select the first lane that simultaneously has:

```yaml
direction_indexed_observable: true
depth_or_redshift_response: true
exact_data_admission: true
full_covariance_or_valid_null_contract: true
physical_local_and_global_response: true
frame_and_units_bound: true
```

PR-321 HSC SACC fails the first criterion. If no lane passes, stop:

```text
BLOCKED_NO_ELIGIBLE_DIRECTIONAL_LOWZ_LANE
```

## Completion report

```yaml
canonical_work_unit_id:
planning_alias:
starting_head:
final_head:
final_tree:
changed_files:
DAG_prefix:
imported_source_identity:
research_receipts:
PR315_result:
MES_anchor_state:
directional_moment_state:
Planck_MES_result:
local_global_response:
low_z_lane:
generic_control_preserved:
tests:
portable_evidence:
fresh_review:
P0_remaining:
P1_remaining:
unresolved_blockers:
verdict:
```
