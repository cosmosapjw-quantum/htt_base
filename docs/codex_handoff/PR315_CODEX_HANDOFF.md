# Codex handoff — PR-315 Planck SMICA joint cut-sky robustness and rerun

## Mission

Implement the executable contract in:

```text
docs/codex_handoff/pr315_audit_compiled_exec_plan.yaml
```

This is not a generic cleanup or assurance task. It is one bounded scientific
repair and robustness comparison following the intentional PR-314 SMICA-only,
300-pair fast path.

The deliverables are:

1. preserve the exact PR-314 result as executed evidence;
2. implement a joint cut-sky monopole/dipole plus `ell=2..5` estimator;
3. rerun the same exact 300-pair SMICA fast slice;
4. export a feature-level portable replay;
5. report the frozen old/new comparison;
6. preserve the existing DAG order.

## Source of truth

```yaml
repository: cosmosapjw-quantum/htt_base
audited_branch: changeset/pr314-planck-pr3-attended-analysis-20260824
audited_head: 883a7cf41116e6740b1bac9b76a5e9c6b3fd188e
audited_tree: de7b83aac8a5357e9cfee518924ab6c0a0972fb3
audited_result_sha256: 898d08fc7c70205fbb8c7580fbaef1074357a8b3255ac77afd8273b92511da97
plan_branch: changeset/pr315-pr314-post-execution-adversarial-audit-20260824
operating_profile: private_single_researcher_local_v1
fast_path: SMICA_ONLY_EXACT_300_PAIR_USER_APPROVED
```

Read before editing:

```text
docs/research_program/post_pr275/audits/pr314_post_execution_adversarial_audit.md
docs/codex_handoff/pr315_audit_compiled_exec_plan.yaml
docs/PR_DELTAS/pr-314.md
docs/research_program/post_pr275/pr314_spec.yaml
docs/research_program/post_pr275/pr314_existing_data_analysis_report.md
scripts/observed_runs/prepare_planck_pr3_admission.py
scripts/observed_runs/run_planck_pr3.py
htt/obsstat/planck_pr3_operator.py
htt/obsstat/planck_post275_lane.py
tests/integration/test_planck_pr3_admission_preparation.py
tests/integration/test_planck_pr3_current_stack.py
tests/integration/test_planck_pr3_operator.py
```

## Non-negotiable interpretation

PR-314 is a real executed result:

```yaml
role: DELIVERED_FULLSKY_SMICA_300PAIR_CONDITIONAL_NEGATIVE_DIAGNOSTIC
family_rank_fraction: 133/301
family_rank_reduced: 19/43
```

Do not delete, overwrite or call it fabricated. It is valid for its exact
delivered-product operator and conditional simulation ensemble.

It is not a mask-conditioned, Commander-robust, unconditional, global,
Bayesian, cross-probe or Bianchi result.

PR-315 does not select a new primary branch because of its observed rank. It
adds a separately named joint cut-sky branch and reports the comparison.

## First action — preserve DAG order

After PR-314 receives an exact terminal disposition:

1. register PR-315 as an append-only successor of PR-314 using the existing DAG
   generator;
2. preserve every existing node order and dependency;
3. regenerate canonical and machine-readable mirrors;
4. if PR-314 closes without merge, bind its exact terminal receipt rather than
   inventing success;
5. run strict DAG validation before production edits.

Do not manually reorder or rewrite the backlog.

## Required RED phase

Add these tests before changing production code:

```text
test_joint_cutsky_fit_recovers_known_lowell_with_arbitrary_monopole_dipole
test_joint_cutsky_fit_abstains_on_rank_condition_or_plane_failure
test_masked_region_contamination_cannot_change_joint_cutsky_features
test_observation_and_null_joint_operator_identity_is_exact
test_primary_pair_manifest_is_exact_ordered_and_hash_bound
test_raw_observation_and_pair_manifest_are_acceptance_bound
test_portable_feature_package_recomputes_exact_result
test_branch_and_tail_registry_are_frozen_before_rerun
```

Expected RED evidence:

- the current sequential nuisance path fails the joint known-alm oracle;
- the current delivered-full-sky branch fails the zero-mask contamination
  oracle;
- missing raw pair manifest and feature replay tests fail.

Keep the RED logs.

## Numerical implementation

### Joint estimator

Do not first fit monopole/dipole and then fit the retained band as two unrelated
cut-sky systems.

Build one real harmonic design:

```text
D = [Y_lm for ell=0..5]
columns = 36
nuisance columns = ell=0,1
retained columns = ell=2..5
```

Accumulate in bounded high-resolution pixel chunks:

```text
normal += D_chunk.T @ W_chunk @ D_chunk
rhs    += D_chunk.T @ W_chunk @ T_chunk
```

Solve the checked joint system and retain only `ell=2..5`.

An FWL implementation is allowed only if it residualizes **both** the data and
the retained design against the nuisance design and passes the dense joint-fit
oracle.

Record:

```yaml
basis_order:
mask_sha256:
normal_matrix_sha256:
condition_number:
relative_singular_floor:
weighted_residual_norm:
source_beam_sha256:
source_pixel_window_sha256:
target_transfer_sha256:
```

Apply the source-to-target beam/pixel transfer to retained coefficients after
the joint masked fit.

Observation and every primary null row must call the same function and the same
immutable configuration object.

### Frozen branches

```yaml
PR314_DELIVERED_FULLSKY_LEGACY:
  role: frozen executed result
  may_be_overwritten: false

PR315_JOINT_CUTSKY_PRIMARY_ROBUSTNESS:
  role: separately registered robustness estimator

OPTIONAL_DELIVERED_MAP_SENSITIVITY:
  role: comparison only
```

Freeze these roles before evaluating new observed ranks.

## Fast-path boundary

Do not broaden the task:

```yaml
SMICA_only: true
primary_rows: 300
Commander_required: false
CMB_only_999_required: false
other_lanes: out_of_scope
```

The 999 CMB-only ensemble may be prepared later as a separately labelled
sensitivity tier. It is not a blocker and must never be pooled with the primary
300 rows.

## Tail estimand

Preserve PR-314 exactly as:

```text
SMICA_LOWELL_12_FEATURE_TWO_SIDED_OMNIBUS_V1
```

A directed-tail sensitivity must have a pre-existing physical/literature basis
and a separate identifier. If that cannot be frozen without inspecting new
ranks, emit:

```text
BLOCKED_BY_UNRESOLVED_SPEC: FEATURE_TAIL_DIRECTION
```

and complete the two-sided joint cut-sky comparison.

## Raw-input manifest

Before attended execution, create one ordered manifest containing:

- raw observed SMICA SHA-256;
- common mask SHA-256;
- 300 ordered raw CMB file hashes;
- 300 ordered raw noise file hashes;
- exact pair mapping and pair-manifest hash;
- beam/window/pixwin helper hashes;
- candidate commit/tree;
- plan and worker hashes.

Bind the manifest digest in the acceptance payload. This is scientific
reproducibility, not cryptographic authorization. Add no keys, signatures,
nonce ledgers, root launchers or anti-tamper framework.

## Portable feature replay

Export:

```yaml
format: PLANCK_SMICA_FEATURE_REPLAY_V1
observed_feature_vector: shape [12]
null_feature_matrix: shape [300,12]
row_ids: exact 300 ordered strings
feature_order: exact 12 strings
feature_units: exact 12 strings
covariance: shape [12,12]
tail_registry:
branch_id:
operator_hashes:
raw_input_manifest_hash:
```

It must recompute:

- covariance rank and condition diagnostics;
- all 12 local finite ranks;
- family rank;
- scientific projection hashes.

Mutating one row, feature, tail, order entry or matrix cell must fail replay.

## Clean CI

Add one step to the existing Repository-integrity workflow. Do not create a new
workflow. Run:

```text
tests/integration/test_planck_pr3_admission_preparation.py
tests/integration/test_planck_pr3_current_stack.py
tests/integration/test_planck_pr3_operator.py
portable feature replay verification
```

Keep all existing gates.

## Actual rerun

After RED→GREEN and a clean candidate:

1. process the exact 300 paired rows with the joint cut-sky estimator;
2. process observed SMICA with the identical estimator;
3. compute the frozen two-sided omnibus;
4. preserve/replay PR-314 unchanged;
5. produce an old/new table for all 12 feature values and local ranks;
6. report both family ranks, covariance diagnostics, runtime and RSS;
7. do not tune a threshold or tolerance to recover `19/43`;
8. do not choose the branch with a more interesting result.

## Claim boundary

Allowed:

```text
PR-314 delivered-product SMICA conditional rank
PR-315 joint cut-sky SMICA conditional rank
operator-order and mask-robustness comparison
exact 300-pair empirical calibration
```

Forbidden:

```text
unconditional p-value
Commander robustness
joint Planck result
global anisotropy or source attribution
Bayesian evidence without a registered model
native transfer or Bianchi family identification
cross-probe result
```

## Agent policy

```yaml
ask_user_questions: false
guess_across_scientific_spec_boundary: forbidden
unresolved_spec_action: BLOCKED_BY_UNRESOLVED_SPEC
change_expected_science_to_fit_code: forbidden
suppress_failure: forbidden
security_infrastructure: forbidden
Rust_without_profiled_leaf: forbidden
broaden_fast_path: forbidden
```

A precise blocker is a valid terminal. Partial success is not completion.

## Fresh-context review gate

The implementation session is not final authority. Give a fresh reviewer only:

```text
base SHA
final SHA
compiled contract
final diff
RED logs
GREEN logs
clean CI logs
old/new result table
portable feature package
```

First-pass output only:

```yaml
severity:
file_and_line:
violated_invariant:
reproducer:
missing_test:
```

Merge requires:

```yaml
P0: 0
P1: 0
```

## Completion report

```yaml
base_sha:
final_sha:
final_tree:
DAG_registration:
changed_files:
net_LOC:
RED_joint_nuisance_oracle:
RED_mask_oracle:
GREEN_joint_nuisance_oracle:
GREEN_mask_oracle:
joint_operator_identity_observation_vs_null:
raw_input_manifest_sha256:
portable_feature_package_sha256:
PR314_result_sha256: 898d08fc7c70205fbb8c7580fbaef1074357a8b3255ac77afd8273b92511da97
PR314_family_rank: 133/301
PR315_family_rank:
feature_delta_table:
runtime_and_RSS:
clean_CI_run_ids:
observed_statistic_seen:
observed_science_executed:
P0_remaining:
P1_remaining:
verdict:
```
