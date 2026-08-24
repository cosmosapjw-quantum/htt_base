# Codex handoff — PR-316 reproducible theory-candidate ledger

## Mission

Implement the executable contract in:

```text
docs/codex_handoff/pr316_theory_promotion_audit_compiled_exec_plan.yaml
```

This is one bounded scientific-governance repair.  It is not a generic cleanup,
a new assurance framework, a security task, or permission to rewrite historical
proof artifacts.

The deliverables are:

1. preserve every PR-405 artifact byte-for-byte;
2. generate the candidate universe from canonical repository sources rather
   than from a manually assembled output list;
3. repair the distinction between administrative adjudication and a real proof
   or experiment attempt;
4. derive scoped child candidates mechanically;
5. separate evidence state, evidence kind, semantic-component count, and
   current release state;
6. produce portable CAS execution receipts with a correct Lean trust boundary;
7. regenerate all v2 outputs in clean CI;
8. require a fresh-context read-only reviewer before any terminal release state;
9. preserve the existing canonical DAG order and dependencies.

## Exact source of truth

```yaml
repository: cosmosapjw-quantum/htt_base
audited_pull_request: 405
audited_branch: analysis/theory-promotion-audit-20260824
audited_head: 463f0999949bf8534c60ad7973b7342705c2e3d6
audited_tree: 20eb3e3e117633bc83e743bea45ed024048441e1
plan_branch: changeset/pr316-theory-promotion-ledger-repair-plan-20260824
compiled_contract: docs/codex_handoff/pr316_theory_promotion_audit_compiled_exec_plan.yaml
adversarial_audit: docs/research_program/theory_promotion/audits/pr405_adversarial_science_audit.md
```

Read these before editing:

```text
docs/codex_handoff/pr316_theory_promotion_audit_compiled_exec_plan.yaml
docs/research_program/theory_promotion/audits/pr405_adversarial_science_audit.md
docs/research_program/theory_promotion/THEORY_PROMOTION_AUDIT_V1.md
docs/research_program/theory_promotion/THEORY_PROMOTION_MATRIX_V1.json
docs/research_program/theory_promotion/pr284_finite_path/CAS_CONTRACT.json
docs/research_program/theory_promotion/pr284_finite_path/CAS_ADJUDICATION.json
docs/research_program/theory_promotion/pr284_finite_path/CAS_RUN_SPEC.json
docs/research_program/strengthening/pr190_spec.yaml
docs/research_program/vector_tensor/proofs/**
docs/research_program/post_pr275/**
```

## Non-negotiable scientific interpretation

PR-405 contains real useful results.  Do not delete or ridicule them.

Accepted at exact scope:

```yaml
PR190_normal_vorticity_obstruction:
  status: valid_negative_result
  scope: registered Bianchi-I hypersurface-normal lower/interior targets only
  forbidden_broadening: tilted or non-normal congruences

PR284_four_atom_fixture:
  status: exact_arithmetic_correct
  scope: one registered finite rational fixture only
  values:
    centered_mean: 0
    second_moment: 5
    middle_values: [-2, -2, 2, 2]
    coarse_values: [0, 0, 0, 0]
    path_maximum_squares: [9, 4, 4, 9]
    threshold_squared: 36/5
    event_probability: 1/2
    bound: 25/36
    slack: 7/36
  forbidden_broadening:
    - general reverse-martingale iff
    - convergence
    - optional stopping
    - observed-sky calibration

restricted_cores:
  VT-T8: local chart on the nonzero-Jacobian locus, not global orbit separation
  VT-T13: invariant chain rule, not a full covariant evolution law
  VT-S14: synthetic validation, not observational evidence
```

Not accepted as terminal facts until PR-316 regenerates them:

```yaml
candidate_universe_count: 157
PROMOTED_count: 36
REFUTED_count: 1
UNRESOLVED_count: 107
DEFERRED_count: 2
NOT_ATTEMPTED_count: 11
coverage_complete: true
unique_theorem_count: any numeric value
```

The current PR-405 publication gate
`STOP_INVALID_FOR_CURRENT_PROMOTION` is correct and must remain blocked until
the successor gates pass.

## Why the current terminal counts are invalid

PR-405 defines `UNRESOLVED` as a candidate for which a real proof or experiment
was attempted.  The matrix nevertheless marks rows with missing signatures,
empty premises, title-only source identity, or a reference that was not
re-adjudicated as `scientific_attempted=true` and `UNRESOLVED`.

Do not preserve this count by inventing attempt receipts.  Implement distinct
fields:

```yaml
source_available:
administrative_adjudication_attempted:
proof_or_experiment_attempted:
proof_or_experiment_completed:
evidence_state:
evidence_kind:
current_release_state:
```

Only an exact proof, experiment, or counterexample attempt receipt can make
`proof_or_experiment_attempted=true`.

## First action — preserve the existing DAG

Do not touch production or generated science before the serial stack is
eligible.

1. Read the live canonical DAG and status files, not the stale plan-branch
   assumption.
2. Require exact terminal dispositions for PR-314, PR-315, and PR-405.
3. Record the full ordered old node list and old dependency map.
4. Use the existing project-owned append/sync mechanism to register PR-316 after
   the live terminal tail, with proposed serial predecessor PR-315 and PR-405's
   terminal receipt as an evidence dependency.
5. Regenerate all canonical and machine-readable mirrors.
6. Prove that the old node list is an exact prefix and every old dependency is
   unchanged.
7. If any predecessor is open, lacks a receipt, or the project-owned
   registration path cannot be resolved, stop with the exact blocker from the
   compiled contract.  Do not manually improvise a DAG edit.

The planning PR itself intentionally changes no DAG file.

## Required RED phase

Write the load-bearing tests before implementing the generator.  Run them and
retain the failing logs.

Required test names:

```text
test_manifest_discovers_every_registered_claim_or_exclusion
test_removing_one_source_entry_breaks_coverage
test_inserting_unclassified_claim_breaks_coverage
test_unresolved_requires_scientific_attempt_receipt
test_missing_signature_is_not_scientific_attempt
test_reference_resolved_not_readjudicated_is_not_scientific_attempt
test_established_and_refuted_rows_are_content_bound
test_scoped_children_are_derived_from_typed_source_fields
test_manual_scoped_child_injection_is_rejected
test_evidence_state_kind_and_release_are_orthogonal
test_synthetic_validation_never_enters_theorem_count
test_semantic_components_have_one_deterministic_representative
test_pr190_negative_scope_replays_exactly
test_pr405_frozen_inputs_are_unchanged
test_pr284_fixture_values_are_exact
test_axis_payload_values_are_derived_not_literal_only
test_fixture_claim_ceiling_is_statically_verified
test_lean_standard_three_axioms_are_allowed
test_lean_sorry_custom_and_trusted_axioms_are_rejected
test_cas_receipt_is_portable_and_content_bound
test_blocked_axis_is_not_missing_or_mathematical_conflict
test_current_replay_counts_are_derived_from_command_receipts
test_v2_outputs_are_byte_reproducible
test_repository_integrity_runs_theory_promotion_v2
test_independent_review_receipt_is_required_for_release_eligibility
```

The RED evidence must demonstrate at least:

- the PR-405 self-contained universe hash does not detect a source claim added
  outside its manually assembled list;
- a missing-signature row is currently counted as a scientific attempt;
- the current Lean runner rejects the standard three Lean axioms;
- the PR-405 outputs are not regenerated by clean CI;
- the current arithmetic axes can emit a literal
  `general_theorem_not_promoted=true` without examining any claim artifact.

Do not edit expected scientific values to make RED tests pass.

## Candidate-source generator

Create:

```text
scripts/theory_promotion/build_candidate_ledger.py
scripts/theory_promotion/verify_candidate_ledger.py
```

Required public interfaces:

```python
def discover_source_entries(repo_root: Path) -> tuple[SourceEntry, ...]: ...

def derive_candidates(
    entries: Sequence[SourceEntry],
    evidence_index: Mapping[str, object],
) -> tuple[Candidate, ...]: ...

def verify_source_coverage(
    entries: Sequence[SourceEntry],
    candidates: Sequence[Candidate],
    exclusions: Sequence[Exclusion],
) -> None: ...

def canonical_payload_sha256(payload: Mapping[str, object]) -> str: ...
```

Every source entry must bind:

```yaml
source_entry_id:
source_path:
source_locator: line range or JSON/YAML pointer
source_blob_sha256:
source_statement:
source_statement_identity_sha256:
source_kind:
discovery_rule_id:
```

Every discovered entry must be represented by a candidate relation or one typed
exclusion.  A hash of the generated list is not a coverage proof unless the
source discovery and exclusion relation are also verified.

Do not use unrestricted natural-language scanning as the only source discovery
rule.  Prefer typed registries, proof obligations, adjudication rows,
`narrow_established_core`, counterexample records, and explicitly registered
proposal sections.  If an untyped source cannot be classified without guessing,
emit:

```text
BLOCKED_BY_UNRESOLVED_SPEC: SOURCE_DISCOVERY_RULE
```

with its exact path and locator.

## Terminal-state truth table

Implement this exact logic unless an existing stronger typed contract is found:

```yaml
- when:
    proof_or_experiment_attempted: false
    explicit_dependency_blocker: false
  evidence_state: NOT_ATTEMPTED

- when:
    proof_or_experiment_attempted: false
    explicit_dependency_blocker: true
  evidence_state: DEFERRED

- when:
    proof_or_experiment_attempted: true
    attempt_settled: false
  evidence_state: UNRESOLVED

- when:
    proof_or_experiment_attempted: true
    exact_statement_passed: true
  evidence_state: ESTABLISHED

- when:
    proof_or_experiment_attempted: true
    exact_statement_refuted: true
  evidence_state: REFUTED
```

An administrative adjudication receipt may prove that someone inspected a row.
It does not prove that the proposition was attempted.

## Evidence-kind and release separation

Use separate enums:

```yaml
evidence_kind:
  - EXACT_THEOREM
  - CONDITIONAL_THEOREM
  - NEGATIVE_THEOREM
  - SYNTHETIC_VALIDATION
  - NUMERICAL_EXAMPLE
  - OTHER

current_release_state:
  - ELIGIBLE
  - BLOCKED_STALE_BINDING
  - BLOCKED_INCOMPLETE_REPLAY
  - BLOCKED_REQUIRED_CAPABILITY
  - BLOCKED_INDEPENDENT_REVIEW
  - HISTORICAL_ONLY
```

Never emit a headline theorem count that includes synthetic validation.  Report:

1. source-row counts;
2. evidence-state by evidence-kind counts;
3. semantic-component counts after deterministic deduplication;
4. current release-state counts.

If semantic equivalence is not closed for all members, report
`unique_theorem_count: UNRESOLVED`.

## Scoped child derivation

Do not maintain a handwritten supplemental candidate list.

Generate children by typed rules:

```yaml
RULE-NARROW-CORE:
  input: non-null narrow_established_core with exact statement and evidence
  output: one child candidate bound to its parent

RULE-SYNTHETIC-SUBRESULT:
  input: blocked broad row with a separately preregistered passing synthetic cell
  output: one SYNTHETIC_VALIDATION child bound to its parent

RULE-NEGATIVE-OBSTRUCTION:
  input: failed broad conjunctive statement with an exact scoped counterexample or obstruction
  output: one NEGATIVE_THEOREM child with explicit non-broadening exclusions
```

Adding or removing a child outside these rules must fail verification.

## CAS evidence runner

Create:

```text
scripts/theory_promotion/run_cas_evidence.py
```

Each receipt must bind:

```yaml
contract_sha256:
run_spec_sha256:
runner_sha256:
axis_program_sha256:
argv:
cwd:
environment_allowlist:
tool_versions:
dependency_tree_identity:
stdout_sha256:
stderr_sha256:
exit_code:
derived_status:
```

Statuses are distinct:

```yaml
EXECUTED_PASS:
EXECUTED_FAIL:
EXECUTED_INCONCLUSIVE:
BLOCKED_PLATFORM_OR_LICENSE:
BLOCKED_DEPENDENCY_UNAVAILABLE:
NOT_APPLICABLE:
MISSING_REQUIRED_AXIS:
MATHEMATICAL_CONFLICT:
```

Do not call a blocked engine a conflict.  Do not serialize a blocked engine as
an absent-free four-axis run.

### Lean trust policy

For the new versioned contract, allow exactly:

```text
propext
Classical.choice
Quot.sound
```

Reject:

```text
sorryAx
Lean.trustCompiler
custom project axioms
native_decide when the contract forbids trusted native evaluation
partial declarations
unsafe declarations
```

The PR-405 Lean result remains historical `INCONCLUSIVE` under its literal old
contract.  Do not rewrite it.  Rerun the same theorem under a new contract and
record the changed trust rule explicitly.

### Wolfram, xAct, Sage, and Singular labels

The current Wolfram script performs rational enumeration after loading xAct;
the current Sage script performs Sage rational arithmetic and only probes a
Singular version.  Record their actual roles honestly:

```yaml
wolfram:
  mathematical_role: exact rational replay
  xact_role: availability disclosure unless an xAct tensor operation is executed

sage:
  mathematical_role: exact rational replay
  singular_role: availability disclosure unless a Singular computation is executed
```

Do not add artificial xAct or Singular calculations merely to preserve a label.

## Claim containment

Remove `general_theorem_not_promoted` from the list of mathematical CAS
obligations.  A literal boolean is not a proof of claim containment.

The static verifier must inspect the generated ledger and report and reject:

- missing exact fixture statement;
- missing exclusions;
- a fixture relabelled as a general theorem;
- a synthetic validation relabelled as a theorem or observation;
- PR-190 broadened beyond normal-frame registered targets;
- current release eligibility with stale or incomplete replay;
- geometry, transfer, or Bianchi-family promotion.

## Generated outputs

Generate versioned successors beside PR-405:

```text
docs/research_program/theory_promotion/v2/CANDIDATE_SOURCE_MANIFEST_V2.json
docs/research_program/theory_promotion/v2/CANDIDATE_LEDGER_V2.json
docs/research_program/theory_promotion/v2/CAS_EVIDENCE_INDEX_V2.json
docs/research_program/theory_promotion/v2/THEORY_PROMOTION_REPORT_V2.md
```

Do not modify:

```text
docs/research_program/theory_promotion/THEORY_PROMOTION_AUDIT_V1.md
docs/research_program/theory_promotion/THEORY_PROMOTION_MATRIX_V1.json
docs/research_program/theory_promotion/pr284_finite_path/CAS_CONTRACT.json
docs/research_program/theory_promotion/pr284_finite_path/CAS_ADJUDICATION.json
```

The v2 report must include a complete PR-405-to-PR-316 delta table.  Do not tune
rules to reproduce `36/1/107/2/11`.

## Exact CI integration

Add one bounded step to the existing
`.github/workflows/repository-integrity.yml`.  Do not add a workflow.

The step must run:

```bash
PYTHONPATH=htt:htt/src:htt/htt python -m pytest -q \
  tests/contracts/test_theory_promotion_ledger_v2.py \
  tests/integration/test_theory_promotion_cas_v2.py

python scripts/theory_promotion/build_candidate_ledger.py \
  --repo-root . \
  --output-root docs/research_program/theory_promotion/v2

python scripts/theory_promotion/verify_candidate_ledger.py \
  --repo-root . \
  --manifest docs/research_program/theory_promotion/v2/CANDIDATE_SOURCE_MANIFEST_V2.json \
  --ledger docs/research_program/theory_promotion/v2/CANDIDATE_LEDGER_V2.json \
  --cas-index docs/research_program/theory_promotion/v2/CAS_EVIDENCE_INDEX_V2.json

git diff --exit-code -- docs/research_program/theory_promotion/v2
```

Licensed or locally unavailable engines must exercise typed blocker tests; they
must not be required to produce a false CI PASS.

## Agent behavior

```yaml
ask_user_questions: false
search_repo_docs_tests_before_blocking: required
guessing_across_specification_boundary: forbidden
unresolved_spec_action: BLOCKED_BY_UNRESOLVED_SPEC
changing_scientific_expectations_to_fit_code: forbidden
weakening_or_deleting_tests: forbidden
suppressing_failures: forbidden
editing_frozen_PR405_artifacts: forbidden
security_or_antitamper_infrastructure: forbidden
new_assurance_framework: forbidden
same_agent_final_authority: false
partial_success_reporting: exact_and_nonterminal
```

Do not report completion after only generating JSON or passing targeted tests.
An exact blocker with evidence is a valid terminal result.

## Fresh-context review gate

The implementation context is not the final authority.

After sealing the candidate, start a fresh context and provide only:

```text
exact audited base/head/tree
exact final SHA/tree and diff
compiled contract
source manifest
candidate ledger
CAS evidence index and raw receipts
RED logs
GREEN logs
clean CI logs
PR-405-to-PR-316 delta tables
```

The first reviewer pass may not edit code.  It must output:

```yaml
severity:
file_and_line_or_json_pointer:
violated_invariant:
exact_reproducer:
missing_or_weak_test:
scientific_impact:
```

Terminal release eligibility requires:

```yaml
P0: 0
P1: 0
```

## Required completion report

```yaml
audited_base_sha:
audited_head_sha:
final_sha:
final_tree:
DAG_registration:
  old_order_sha256:
  new_order_sha256:
  old_dependency_map_sha256:
  new_dependency_map_sha256:
  existing_prefix_unchanged:
changed_files:
net_LOC:
PR405_frozen_blob_checks:
RED_results:
GREEN_results:
source_manifest_sha256:
candidate_ledger_sha256:
CAS_evidence_index_sha256:
generated_report_sha256:
PR405_terminal_counts:
PR316_terminal_counts:
attempt_taxonomy_delta_table:
evidence_kind_count_table:
semantic_component_count_table:
PR190_scope_replay:
PR284_fixture_replay:
blocked_axes:
clean_CI_run_ids:
independent_review_receipt_sha256:
observed_data_opened:
native_solver_executed:
P0_remaining:
P1_remaining:
unresolved_blockers:
verdict:
```
