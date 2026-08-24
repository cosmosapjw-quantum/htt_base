# Codex handoff — theory-promotion reconciliation repair

> **Controlling overlay:** This handoff is stacked on PR #406. Read
> `docs/codex_handoff/PR406_PLAN_HARDENING_READ_FIRST.md` and
> `docs/research_program/theory_promotion/audits/PR406_PLAN_DIFFERENTIAL_AUDIT.md`
> before the PR-405 audit. Where PR-406 differs, the stricter fail-closed rule
> in this overlay controls.


## Mission

Implement the executable contract in:

```text
docs/codex_handoff/theory_promotion_reconciliation/AUDIT_COMPILED_EXEC_PLAN.yaml
```

Read the threat catalogue first:

```text
docs/codex_handoff/theory_promotion_reconciliation/P0_P1_THREAT_CATALOG.json
```

This is not a generic cleanup task. The deliverable is a linear sequence of
small scientific-risk work units that repairs PR-405's classification/evidence
model while preserving its useful historical audit evidence.

## Exact audited identity

```yaml
repository: cosmosapjw-quantum/htt_base
pull_request: 405
base_sha: aaa87d6de692f5c47d5ea9eff963db6dd9ee5be7
head_sha: 463f0999949bf8534c60ad7973b7342705c2e3d6
head_tree: 20eb3e3e117633bc83e743bea45ed024048441e1
observed_data_used: false
```

Do not trust PR prose, status labels, or count summaries without replaying their
mechanical basis.

## Non-negotiable scientific interpretation

Preserve these results:

```yaml
PR284_REGISTERED_FINITE_FIXTURE:
  campaign_disposition: PROMOTED
  truth_status: ESTABLISHED
  evidence_status: EXACT_PROOF
  replay_status: CURRENT_BLOCKED
  release_status: BLOCKED
  scope: one exact four-atom fixture only
  broad_reverse_martingale_theorem: NOT_ESTABLISHED
  current_CAS4_release: BLOCKED_INCOMPLETE_CONTRACT

PR190_NORMAL_VORTICITY_OBSTRUCTION:
  campaign_disposition: PROMOTED
  truth_status: ESTABLISHED
  evidence_status: EXACT_NEGATIVE_RESULT
  replay_status: HISTORICAL_PASS_CURRENT_INCOMPLETE
  release_status: BLOCKED
  scope: registered homogeneous Bianchi-I hypersurface-normal frame

VT_T8_LOCAL_CHART:
  campaign_disposition: PROMOTED
  truth_status: ESTABLISHED
  evidence_status: PREMISE_CONDITIONAL_PROOF
  replay_status: HISTORICAL_PASS_CURRENT_INCOMPLETE
  release_status: BLOCKED
  scope: nonzero-Jacobian open locus
  global_orbit_separation: NOT_ESTABLISHED

VT_T13_CHAIN_RULE_CORE:
  campaign_disposition: PROMOTED
  truth_status: ESTABLISHED
  evidence_status: PREMISE_CONDITIONAL_PROOF
  replay_status: HISTORICAL_PASS_CURRENT_INCOMPLETE
  release_status: BLOCKED
  scope: differentiable STF sigma with I2 greater than zero
  full_covariant_evolution_law: NOT_ESTABLISHED
```

Do not preserve these claims as authority:

```yaml
complete_157_candidate_universe: NOT_ESTABLISHED
untyped_36_promoted_scientific_result_count: FORBIDDEN
PR284_CAS_CONFLICT_as_scientific_conflict: INVALID
classification_attempt_equals_scientific_attempt: INVALID
```

## First action — allocate DAG nodes safely

Do not use a hard-coded PR number from this document.

1. Re-read the live canonical DAG, status, machine-readable mirrors, and open
   concurrent stacked PRs.
2. Require an exact terminal receipt for PR #405.
3. Use the existing repository generator to allocate the next available nodes.
4. Preserve the entire old topological node sequence as an exact prefix.
5. Append the ten work units in the contract's declared order.
6. Run mirror sync and strict DAG validation before any production edit.

Terminate with:

```text
BLOCKED_DAG_PREFIX_DRIFT
```

if any old node is reordered or any old dependency changes.

Terminate with:

```text
BLOCKED_PREDECESSOR_TERMINAL_RECEIPT
```

if PR #405 lacks an exact terminal disposition.

## Implementation discipline

For every work unit:

1. write the named RED tests;
2. run them and preserve the failing log;
3. implement the smallest change that satisfies the invariant;
4. run the focused GREEN tests;
5. run direct regressions and `git diff --check`;
6. commit one independently reviewable scientific risk unit;
7. do not begin the next work unit until the current unit has an exact terminal
   receipt.

Never modify expected scientific outputs merely to make a test pass. If the
contract is ambiguous and the repository cannot resolve it, emit:

```text
BLOCKED_BY_UNRESOLVED_SPEC
```

with exact file/line/evidence, rather than guessing.

## Required state model

Preserve one owner-mandated campaign disposition and separate it from the four
scientific/evidence fields:

```yaml
campaign_disposition: PROMOTED | REFUTED | UNRESOLVED | DEFERRED | NOT_ATTEMPTED
truth_status: ESTABLISHED | REFUTED | OPEN | NOT_ASSESSED
evidence_status: EXACT_PROOF | PREMISE_CONDITIONAL_PROOF | EXACT_NEGATIVE_RESULT | PREREGISTERED_SYNTHETIC_VALIDATION | INCOMPLETE | UNAVAILABLE
replay_status: CURRENT_PASS | HISTORICAL_PASS_CURRENT_INCOMPLETE | CURRENT_BLOCKED | CURRENT_FAIL | NOT_RUN
release_status: ELIGIBLE | BLOCKED | NOT_APPLICABLE
```

Engine availability may change `replay_status` or `release_status`. It may not
change `truth_status`.

A classification or inventory scan is not a proof/experiment receipt.

Map the live PR-406 five-state evidence model without collapsing any state:

```yaml
ESTABLISHED: PROMOTED
REFUTED: REFUTED
UNRESOLVED: UNRESOLVED
DEFERRED: DEFERRED
NOT_ATTEMPTED: NOT_ATTEMPTED
```

`NOT_ATTEMPTED != REFUTED` is a mandatory tested invariant. The sentence “No
scientific result survived.” additionally requires deterministic candidate
coverage, zero `NOT_ATTEMPTED` rows, and zero `PROMOTED` rows.

## Candidate surface

Until a deterministic extractor and scoped-candidate declaration registry are
closed, use:

```text
enumerated_surface_complete
```

not:

```text
complete_candidate_universe
```

The candidate graph must type relations as:

```yaml
- EQUIVALENT
- SUBSUMES
- NARROWER_CORE
- NEGATIVE_SUPPORT
- SYNTHETIC_SUBRESULT
```

Do not emit a unique theorem count while an established node lacks semantic
relation adjudication.

## PR-284 repair

One canonical fixture must own:

- four rational weights;
- target values;
- fine/middle/coarse partitions;
- lambda;
- inclusive event rule.

All axes must consume that fixture or generated constants bound to its hash.

Do not retain decorative backend names:

- xAct must perform scientifically relevant xAct work or the axis is `wolfram`;
- Singular must perform scientifically relevant Singular work or the axis is
  `sage`;
- identical algorithms across engines must be disclosed as same-algorithm
  engine replay.

Remove the literal `general_theorem_not_promoted=true` obligation. Validate
scope by comparing contract exclusions with matrix/report/release output.

Lean must either define and derive the finite probability/partition semantics,
or be labelled `FORMAL_ARITHMETIC_REPLAY`. Preregister allowed foundational
axioms separately from forbidden scientific/source axioms. Continue to forbid
`sorry`, source `axiom`, `native_decide`, and undeclared premises.

Use:

```yaml
COMPLETE_PASS:
INCOMPLETE_BLOCKED:
CONTRACT_MISMATCH:
SCIENTIFIC_CONFLICT:
```

`SCIENTIFIC_CONFLICT` requires incompatible mathematical outputs,
counterexample, or domain assumptions.

## Permanent scientific regressions

Implement each as a separate work unit:

- PR-197 finite rank resolution and arbitrary ties;
- PR-210 nonempty, derived frame transformation;
- PR-216 branch-complete homogeneous constraints;
- PR-222 physical CF4 component binding;
- PR-223 nonnegative PSD moment cone and constructive antipodal decomposition.

Do not combine them into one assurance or cleanup PR.

## Evidence and CI

Every established or refuted candidate must have:

```yaml
candidate_id:
campaign_disposition:
statement_identity_sha256:
path:
git_blob_or_sha256:
fragment_or_symbol:
evidence_class:
evidence_status:
replay_receipt:
truth_status:
replay_status:
release_status:
```

Add the focused matrix/CAS/evidence validators to the existing Repository
integrity workflow. Keep all existing steps intact. A local full suite is not
required unless a changed dependency makes it directly relevant.

## Fresh-context review

The implementation context is not final authority.

After the candidate is sealed, start a new context with only:

```text
base SHA
final SHA/tree
compiled contract
threat catalogue
final diff
RED/GREEN logs
clean CI logs
state-transition table
candidate graph
PR-284 fixture and axis receipts
content-bound evidence manifest
```

The first reviewer pass may not edit code. It outputs only:

```yaml
severity:
file_and_line:
violated_invariant:
reproducer:
missing_test_or_assertion:
```

P0 or P1 returns the work unit to the implementation context. Mergeability
requires:

```yaml
P0: 0
P1: 0
```

## Completion report

```yaml
allocated_DAG_node_ids:
predecessor_terminal_receipt:
original_DAG_order_hash:
regenerated_DAG_order_hash:
existing_order_exact_prefix:
base_sha:
final_sha:
final_tree:
changed_files:
net_LOC:
V1_artifact_preservation_hashes:
V2_matrix_sha256:
candidate_surface_status:
campaign_disposition_counts:
campaign_closeout_coverage_proof:
not_attempted_count:
semantic_graph_status:
PR284_fixture_sha256:
PR284_campaign_disposition:
PR284_truth_status:
PR284_evidence_status:
PR284_replay_status:
PR284_release_status:
PR284_general_theorem_status:
evidence_manifest_sha256:
RED_logs:
GREEN_logs:
clean_CI_run_ids:
observed_data_used:
native_solver_used:
P0_remaining:
P1_remaining:
unresolved_blockers:
verdict:
```

Do not report completion after partial success. An exact blocker with evidence
is a valid terminal result.
