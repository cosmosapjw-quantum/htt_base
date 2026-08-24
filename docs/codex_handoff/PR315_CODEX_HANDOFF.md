# Codex handoff — PR-315 Planck SMICA scientific repair and rerun

## Mission

Implement the executable contract in:

```text
docs/codex_handoff/pr315_audit_compiled_exec_plan.yaml
```

The deliverable is not another review essay. It is a bounded scientific repair that makes the Planck SMICA low-ell result insensitive to contamination confined to the common-mask-excluded region, reruns the exact 300-pair primary ensemble, and exports a feature-level portable replay.

## Source of truth

```yaml
repository: cosmosapjw-quantum/htt_base
audited_branch: changeset/pr314-planck-pr3-attended-analysis-20260824
audited_head: 883a7cf41116e6740b1bac9b76a5e9c6b3fd188e
audited_result_sha256: 898d08fc7c70205fbb8c7580fbaef1074357a8b3255ac77afd8273b92511da97
plan_branch: changeset/pr315-pr314-post-execution-adversarial-audit-20260824
operating_profile: private_single_researcher_local_v1
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
```

## Non-negotiable interpretation

The existing result is a real executed result and must be preserved. It is provisionally invalid for scientific acceptance because the full-sky map is projected to `ell<=5` before the common mask enters the operator. A masked residual can therefore leak into retained low multipoles before the later mask inverse.

The current result remains:

```yaml
role: PR314_LEGACY_OPERATOR_PROVISIONAL_DIAGNOSTIC
family_rank: 19/43
fraction: 133/301
```

Do not delete, silently overwrite, or relabel it as a final result.

## First action: preserve the existing DAG

Before production edits:

1. Register `PR-315` as an append-only successor of `PR-314` using the existing DAG machinery.
2. Preserve every existing PR order and dependency.
3. Regenerate all canonical and machine-readable mirrors with the existing generator.
4. If `PR-314` has not merged, keep this branch stacked on its exact head. If it closes failed, bind `PR-315` to its terminal receipt rather than inventing success.
5. Run strict DAG validation before proceeding.

Do not manually reorder the backlog.

## Required RED phase

Add the following tests before changing the operator. At least the first test must fail on the audited PR-314 implementation.

```text
test_masked_region_contamination_cannot_change_primary_lowell_features
test_observation_and_null_operator_identity_is_exact
test_primary_pair_manifest_is_exact_ordered_and_hash_bound
test_raw_observation_and_pair_manifest_are_acceptance_bound
test_portable_feature_package_recomputes_exact_result
test_tail_registry_is_exact_and_not_selected_from_observed_ranks
```

The masked-contamination oracle must:

1. create a known low-ell sky;
2. add contamination only where the registered common-mask weight is zero;
3. vary contamination amplitude over at least `1, 1e2, 1e4, 1e8`;
4. prove that the repaired primary coefficients and all twelve features are invariant within a registered tolerance;
5. demonstrate that the legacy PR-314 reduction is not accepted as the primary operator.

Save the RED test log in the completion evidence.

## Required numerical implementation

Implement a chunked weighted high-resolution low-ell fit. Do not create a dense `Npix x 32` matrix at Planck resolution.

For the admitted common-mask weights `W`, first remove the weighted monopole and dipole. Then accumulate in pixel chunks:

```text
normal = sum Y_chunk.T @ W_chunk @ Y_chunk
rhs    = sum Y_chunk.T @ W_chunk @ T_chunk
```

where `Y` is the frozen real-harmonic basis for `2 <= ell <= 5`. Solve the checked system for the retained coefficients. Record:

```yaml
basis_order:
mask_hash:
normal_matrix_hash:
condition_number:
relative_singular_floor:
residual_norm:
source_beam_hash:
source_pixel_window_hash:
target_transfer_hash:
```

Apply the source-to-target beam/pixel transfer after the masked weighted fit. Observation and every primary null row must call the same function with the same configuration object.

Keep two named non-primary branches for comparison only:

```yaml
FULLSKY_DELIVERED_OR_INPAINTED_SENSITIVITY:
LEGACY_PR314_FULLSKY_BANDLIMIT_THEN_MASK:
```

Never choose the primary branch by inspecting which observed rank looks more interesting.

## Estimand policy

The PR-314 result used one two-sided tail for every feature. Preserve that exact family as:

```text
SMICA_LOWELL_12_FEATURE_TWO_SIDED_OMNIBUS_V1
```

Any physically directed tails must live in a separate registry whose source is prior literature or a pre-existing repository claim, not the observed PR-314/315 ranks. If the directional registry cannot be justified without inspecting the data, emit:

```text
BLOCKED_BY_UNRESOLVED_SPEC: FEATURE_TAIL_DIRECTION
```

and finish the two-sided rerun only.

## Input provenance

Before attended execution, bind:

- raw observed SMICA SHA-256;
- common mask SHA-256;
- exact 300 ordered CMB source hashes;
- exact 300 ordered noise source hashes;
- exact pair mapping and pair-manifest hash;
- beam/window/helper-data hashes;
- candidate commit/tree;
- plan and worker hashes.

This is scientific reproducibility, not a cryptographic authorization system. Do not add keys, signatures, nonce ledgers, root launchers, or anti-tamper infrastructure.

## Portable feature replay

Export a compact package sufficient to recompute the result without any raw Planck map:

```yaml
format: PLANCK_SMICA_FEATURE_REPLAY_V1
observed_feature_vector: shape [12]
null_feature_matrix: shape [300,12]
row_ids: exact 300 ordered strings
feature_order: exact 12 strings
covariance: shape [12,12]
tail_registry:
operator_hashes:
raw_input_manifest_hash:
```

The package must reproduce:

- covariance rank and condition diagnostics;
- all twelve local finite ranks;
- family rank;
- old/new scientific projection hashes.

A corrupted row order, feature order, tail entry, or matrix cell must fail replay.

## Clean CI

Add one step to the existing Repository-integrity workflow. Do not create another workflow. It must execute:

```text
tests/integration/test_planck_pr3_admission_preparation.py
tests/integration/test_planck_pr3_current_stack.py
tests/integration/test_planck_pr3_operator.py
portable feature replay verification
```

Keep the current package, PR-304, PR-309, PR-310, and PR-311 gates intact.

## Actual rerun

After GREEN tests and clean candidate seal:

1. process exactly 300 paired rows;
2. process the observed SMICA map with the same primary operator;
3. compute the frozen two-sided omnibus;
4. run the two named sensitivity branches;
5. produce a table for each of twelve features:
   - PR-314 value and local rank;
   - repaired-primary value and local rank;
   - full-sky/inpainted sensitivity value and rank;
6. report family-rank changes and Monte Carlo resolution;
7. report wall time and maximum RSS;
8. preserve the original PR-314 files unchanged.

If the repaired result changes materially, mark PR-314 as superseded by operator repair. Do not hide the change or tune tolerances to recover `19/43`.

## Claim boundary

Allowed:

```text
SMICA-only mask-conditioned conditional finite-rank diagnostic
operator-order sensitivity statement
exact 300-pair empirical calibration statement
```

Forbidden:

```text
unconditional p-value
Commander robustness
joint Planck result
global anisotropy or source attribution
Bayesian evidence without a registered model
native Bianchi transfer or family identification
cross-probe result
```

## Agent behavior

```yaml
ask_user_questions: false
guess_across_scientific_spec_boundary: forbidden
unresolved_spec_action: BLOCKED_BY_UNRESOLVED_SPEC
change_expected_science_to_fit_code: forbidden
suppress_failure: forbidden
security_infrastructure: forbidden
Rust_without_profiled_leaf: forbidden
```

Do not report completion after partial success. A blocker with exact evidence is a valid terminal.

## Fresh-context review gate

The implementing session must not be the final reviewer. Start a fresh context and provide only:

```text
base SHA
final SHA
audit-compiled contract
final diff
RED log
GREEN log
clean CI logs
old/new result table
portable feature package
```

The first review pass may not edit code. It must output only:

```yaml
severity:
file_and_line:
violated_invariant:
reproducer:
missing_test:
```

Mergeability requires:

```yaml
P0: 0
P1: 0
```

## Required completion report

```yaml
base_sha:
final_sha:
final_tree:
DAG_registration:
changed_files:
net_LOC:
RED_mask_oracle:
GREEN_mask_oracle:
primary_operator:
operator_identity_observation_vs_null:
raw_input_manifest_sha256:
portable_feature_package_sha256:
PR314_family_rank: 19/43
PR315_family_rank:
feature_delta_table:
sensitivity_branches:
clean_CI_run_ids:
observed_statistic_seen:
observed_science_executed:
P0_remaining:
P1_remaining:
verdict:
```
