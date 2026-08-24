# PR-405 adversarial science audit

## Audit identity

```yaml
schema: htt.post_execution_adversarial_audit.v3
audited_pull_request: 405
audited_base_branch: changeset/pr300-one-command-observational-readiness-20260821
audited_base_sha: aaa87d6de692f5c47d5ea9eff963db6dd9ee5be7
audited_head_branch: analysis/theory-promotion-audit-20260824
audited_head_sha: 463f0999949bf8534c60ad7973b7342705c2e3d6
audited_head_tree: 20eb3e3e117633bc83e743bea45ed024048441e1
audited_matrix: docs/research_program/theory_promotion/THEORY_PROMOTION_MATRIX_V1.json
audited_report: docs/research_program/theory_promotion/THEORY_PROMOTION_AUDIT_V1.md
observed_data_used: false
native_solver_used: false
family_identification_allowed: false
security_or_antitamper_review: out_of_scope
```

## Final hostile verdict

```yaml
preserve_PR405_artifacts: true
merge_as_non_authoritative_audit_evidence: true
merge_as_current_scientific_terminal_ledger: false
current_publication_gate:
  value: STOP_INVALID_FOR_CURRENT_PROMOTION
  verdict: CORRECT_AND_CONSERVATIVE

P0:
  - TERMINAL_STATE_CLASSIFIER_CONTRADICTS_ITS_OWN_ATTEMPT_SEMANTICS
  - EXHAUSTIVE_CANDIDATE_UNIVERSE_IS_SELF_ASSERTED_NOT_DERIVED

P1:
  - PROMOTED_COUNT_COLLAPSES_INCOMMENSURATE_EVIDENCE_KINDS
  - SUPPLEMENTAL_SCOPED_CANDIDATES_ARE_MANUALLY_SELECTED
  - INDEPENDENT_ADJUDICATION_RECEIPT_IS_ABSENT
  - PR405_SCIENCE_OUTPUTS_ARE_NOT_REGENERATED_IN_CLEAN_CI
  - CAS_EXECUTION_EVIDENCE_IS_NOT_PORTABLY_REPRODUCIBLE
  - LEAN_STANDARD_AXIOMS_ARE_MISCLASSIFIED_AS_PROOF_FAILURE
  - CLAIM_CEILING_OBLIGATION_IS_HARDCODED_TRUE
  - CURRENT_REPLAY_COUNTS_HAVE_NO_COMMITTED_COMMAND_LOG_BUNDLE

P2:
  - CAS_CONFLICT_LABEL_CONFLATES_BLOCKED_EXECUTION_WITH_MATHEMATICAL_CONFLICT
  - SINGULAR_AND_XACT_LABELS_OVERSTATE_BACKEND_USE
  - AXIS_STATUS_SCHEMA_REPORTS_NO_MISSING_AXES_AND_NO_ERRORS_DESPITE_BLOCKERS
  - INTERPRETER_AND_MATHLIB_CACHE_PROVENANCE_ARE_NOT_FULLY_BOUND
```

PR-405 contains substantial and mostly conservative mathematical work.  The
fixed-fixture arithmetic is correct, the PR-190 negative obstruction is valid at
its registered scope, and the report correctly refuses a current publication
promotion.  The merge blocker is the new *meta-scientific terminal ledger*:
its candidate universe and terminal counts are not mechanically derived from
source evidence, and its `UNRESOLVED` rows do not consistently satisfy the
report's own definition of a real attempted proof or experiment.

## Adjudication of the scientific results

### Results accepted at their exact scope

1. **PR-190 normal-frame no-go.**  The registered lower and interior targets
   are explicitly Bianchi-I homogeneous, hypersurface-normal states with
   respectively `W2=1/25` and `W2=3/100`.  The same registered contract states
   that a Bianchi-I hypersurface-normal congruence is hypersurface orthogonal
   and has zero vorticity.  Because the broad attainability claim is
   conjunctive, failure of those required targets is a valid refutation of that
   exact broad claim.  It is not a no-go theorem for tilted or non-normal
   congruences.

2. **PR-284 four-atom arithmetic.**  For equal masses, target
   `(-3,-1,1,3)`, middle partition `{0,1}|{2,3}`, and `lambda=6/5`, the exact
   values are

   ```text
   E[X] = 0
   E[X^2] = 5
   M1 = (-2,-2,2,2)
   M2 = (0,0,0,0)
   max_j |M_j|^2 = (9,4,4,9)
   lambda^2 E[X^2] = 36/5
   event probability = 1/2
   1/lambda^2 = 25/36
   slack = 7/36
   ```

   These values were recomputed independently during this audit.  They prove
   one finite fixture only.  They do not prove the broad reverse-martingale
   iff, convergence, optional stopping, continuum-mask calibration, or an
   observational claim.

3. **Exact algebraic and conditional-linear-algebra cores.**  The stated
   normalization identities, gauge equivariance and polar duality,
   trace-free `3x3` Cayley-Hamilton reduction, shear discriminant identity,
   Krylov determinant factorization, parity typing, supported nuisance
   quotient, principal-angle identity, and invariant chain-rule core are
   mathematically consistent at their declared assumptions.  Duplicate or
   overlapping statements remain duplicates; this audit does not convert row
   counts into unique-theorem counts.

4. **Restricted cores inside broader non-PASS rows.**  The registered `VT-T8`
   nonzero Jacobian supports a local chart on the open locus where that
   Jacobian remains nonzero, not global orbit separation.  The `VT-T13`
   derivative identities support the registered chain-rule core, not the full
   covariant evolution system.  The `VT-S14` positive cell is a synthetic
   method validation inside a data-blocked programme, not an observational
   result.

### Results not accepted as currently stated

The following PR-405 headline outputs are not yet auditable scientific facts:

```yaml
scientific_candidate_universe_count: 157
scientific_terminal_state_counts:
  PROMOTED: 36
  REFUTED: 1
  UNRESOLVED: 107
  DEFERRED: 2
  NOT_ATTEMPTED: 11
coverage_complete: true
```

The broad evidence inventory may well contain the intended rows, but those
numbers are presently generated inside the output artifact rather than derived
by a checked source-to-ledger transformation.  The safe interpretation before
repair is:

```yaml
broad_PASS_rows_reported: 32
  exact_or_premise_conditional_rows_reported: 24
  preregistered_synthetic_validation_rows_reported: 8
scoped_children_reported:
  exact_or_negative_mathematical_cores: 3
  synthetic_subresults: 1
unique_theorem_count: UNRESOLVED
terminal_counts_under_attempt_semantics: UNVERIFIED
current_release_or_publication_promotion: BLOCKED
```

The sentence `No scientific result survived.` remains correctly forbidden.
That correct refusal does not validate the new terminal counts.

## P0-001 — terminal state contradicts the declared meaning of “attempted”

The report defines `UNRESOLVED` as a candidate for which a **real proof or
experiment was attempted** but did not settle the statement.  The matrix then
assigns `scientific_attempted=true` and `UNRESOLVED` to many rows whose own
fields state, for example:

```yaml
proof_record_verdict: INCONCLUSIVE_MISSING_SIGNATURE
premises: []
domains: []
statement_relation: SOURCE_TITLE_ONLY_NO_PREMISE_INVENTION
```

Other rows are marked `REFERENCE_RESOLVED_NOT_READJUDICATED` while still being
counted as scientifically attempted.  An administrative attempt to classify a
row is not a proof or experimental attempt on its proposition.  Missing source
text, missing premises, or a resolved citation without re-adjudication cannot
by itself establish `UNRESOLVED` under the taxonomy frozen by PR-405.

This directly invalidates the reported `107/11` split.  The repair must use
orthogonal fields:

```yaml
source_available: true|false
administrative_adjudication_attempted: true|false
proof_or_experiment_attempted: true|false
proof_or_experiment_completed: true|false
evidence_state: ESTABLISHED|REFUTED|UNRESOLVED|DEFERRED|NOT_ATTEMPTED
evidence_kind: EXACT_THEOREM|CONDITIONAL_THEOREM|NEGATIVE_THEOREM|SYNTHETIC_VALIDATION|OTHER
current_release_state: ELIGIBLE|BLOCKED|HISTORICAL_ONLY
```

Required rules include:

- `UNRESOLVED` requires `proof_or_experiment_attempted=true` and a concrete
  attempt receipt;
- source-title inspection or missing-signature adjudication is not a scientific
  attempt;
- an inaccessible required source with an explicit recovery dependency is
  `DEFERRED`; without an actual proof attempt it is not `UNRESOLVED`;
- `NOT_ATTEMPTED` remains distinct from both failure and source unavailability.

## P0-002 — candidate-universe coverage is circular

The matrix defines the scientific universe as the 152 PR-285/PR-286 broad rows
plus five independently reportable scoped candidates, hashes that assembled
list, and then reports zero omissions from the same list.  A content hash proves
integrity of an assembled list; it does not prove that every candidate in the
repository was discovered.

PR-405 records that hundreds of deltas, refs, subjects, registries, and PR
objects were searched, but it commits no deterministic extractor, source
manifest, line or JSON-pointer map, exclusion ledger, or omission mutation
test.  The five scoped additions are selected manually.  Another narrow core or
negative sub-result could be omitted while the self-contained coverage proof
still reports `coverage_complete=true`.

The repair must generate the candidate universe from an explicit canonical
source manifest.  Every discovered source entry must terminate as exactly one
of:

```yaml
classified_candidate:
  candidate_id:
  source_path:
  source_pointer_or_line_range:
  source_blob_sha256:
  statement_identity_sha256:

excluded_entry:
  source_path:
  source_pointer_or_line_range:
  source_blob_sha256:
  exclusion_reason:
  exclusion_rule_id:
```

Deletion of one source candidate, insertion of a new theorem-like source entry,
or removal of one exclusion row must make the verifier fail.

## P1-001 — `PROMOTED=36` mixes different scientific objects

The count combines exact mathematical theorems, premise-conditional linear
algebra, finite preregistered synthetic experiments, a negative theorem, and a
synthetic sub-result.  PR-405 does disclose these categories elsewhere, but
one headline `PROMOTED` count is too lossy for scientific reuse.

The successor must report a two-dimensional classification:

```yaml
evidence_state: ESTABLISHED|REFUTED|UNRESOLVED|DEFERRED|NOT_ATTEMPTED
evidence_kind: EXACT_THEOREM|CONDITIONAL_THEOREM|NEGATIVE_THEOREM|SYNTHETIC_VALIDATION
```

It must also report deduplicated semantic components separately from source-row
counts.  No theorem count is emitted until every duplicate/overlap component
has an explicit representative rule.

## P1-002 — scoped children are selected post hoc rather than derived

`VT-T8`, `VT-T13`, the PR-190 obstruction, and the `VT-S14` positive cell are
reasonable scoped children, but there is no mechanical rule showing why those
four and no others become supplemental candidates.  The successor generator
must derive children from typed source fields, for example:

- every non-null `narrow_established_core` creates one child;
- every blocked row with a separately preregistered positive synthetic cell
  creates one synthetic child;
- a child must bind its parent, statement identity, evidence kind, scope, and
  nonpromotion boundary;
- manually adding or removing a child outside these rules fails verification.

## P1-003 — independent adjudication is asserted without a receipt

The contract names an `independent_non_author_reviewer`, while the PR has no
review object, review thread, or committed independent-review receipt.  The
CAS contract itself discloses that the main writer authored all four engine
programs.  Engine diversity is useful, but it is not an independent human or
fresh-context adjudication.

The final successor must have a read-only first-pass reviewer that receives
only the exact base/head, generated ledger, source manifest, contract, diff,
and verification logs.  The receipt must contain exact hashes and
`P0/P1/P2/P3 + file/line + violated invariant + reproducer`.  The first pass
must not edit code.

## P1-004 — green CI does not run the PR-405 science

The successful Repository-integrity workflow executes generic repository
contracts and the PR-304, PR-309, PR-310, and PR-311 cells.  It does not parse
or regenerate the theory-promotion matrix, verify the candidate universe,
validate evidence fragments, replay the PR-284 axes, or compare generated
outputs with committed artifacts.

The successor must add one bounded step to the existing workflow.  It must not
create another workflow or an assurance framework.

## P1-005 — CAS execution evidence is not portable

The adjudication JSON records local subprocess output but does not bind a
committed generator/adjudicator implementation, full axis-program hashes,
complete transcript artifacts, imported package-tree identities, or a
portable command receipt.  The SymPy preflight names an absolute local virtual
environment while the recorded execution argv is `python3`.  The Lean runner
may borrow a Mathlib cache from the primary worktree after checking only the
manifest and toolchain files.

Required portable evidence:

```yaml
contract_sha256:
run_spec_sha256:
runner_sha256:
adjudicator_sha256:
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

Blocked and nonexecuted axes remain blocked; they are never represented by an
empty missing-axis list.

## P1-006 — Lean’s standard axioms are a false-negative gate

The Lean source compiles its typed exact fixture.  The runner then rejects any
transitive `#print axioms` output, including `propext`, `Classical.choice`, and
`Quot.sound`.  Lean’s own proof-validation documentation identifies precisely
these three as standard benign axioms and recommends rejecting `sorryAx` and
`Lean.trustCompiler` rather than rejecting the standard three.

A future pre-registered contract must allow exactly:

```text
propext
Classical.choice
Quot.sound
```

and reject, at minimum:

```text
sorryAx
Lean.trustCompiler
custom project axioms
native_decide or equivalent trusted native evaluation when forbidden
partial or unsafe proof-bearing declarations
```

The old PR-405 contract remains historical and must not be rewritten into a
post-hoc PASS.  The successor may rerun the same theorem under a new explicitly
versioned contract.

## P1-007 — the claim-ceiling CAS obligation is hard-coded

Every arithmetic axis emits `general_theorem_not_promoted=true` as a literal.
That does not mechanically inspect the report, matrix, claim schema, or output
surface.  Claim containment belongs in a static verifier that scans the exact
generated artifacts and rejects broadened statements, absent exclusions, or a
fixture result relabelled as a general theorem.

## P1-008 — replay counts have no durable command/log bundle

The report states `48 passes / 8 failures` and `357 passes / 4 failures` for
current-head slices.  The PR does not commit an exact command matrix, raw logs,
exit codes, selected-test identities, or output hashes for those counts.
These figures may remain narrative evidence but cannot gate a current
scientific release until reproduced by a committed runner and clean CI.

## P2 findings

- `CAS_CONFLICT` is misleading when no two engines disagree mathematically.
  The actual state is an incomplete four-axis replay plus a contract-policy
  mismatch.
- The Wolfram program loads xAct but performs finite rational arithmetic without
  xAct tensor operations.  The Sage program probes Singular’s version but does
  not use Singular to derive the result.  These are Wolfram and Sage arithmetic
  axes with backend-availability probes, not independent xAct/Singular proofs.
- `missing_axes=[]` and top-level `errors=[]` are inconsistent with a blocked
  Wolfram axis and a failed Lean runner.  Execution, applicability, blockage,
  absence, and mathematical disagreement need distinct typed states.

## Constructive development decision

```yaml
decision: REPAIR_LEDGER_GENERATION_AND_RERUN_BEFORE_TERMINAL_SCIENCE_ACCEPTANCE
preserve_PR405_artifacts: true
PR405_artifact_role: NONAUTHORITATIVE_AUDIT_INPUT
next_work_unit: PR-316
next_capability: REPRODUCIBLE_THEORY_CANDIDATE_LEDGER_AND_TYPED_EVIDENCE_PROMOTION
```

The successor must not rewrite the frozen PR-405 matrix, report, or CAS
adjudication.  It must generate versioned v2 outputs beside them, explain every
numerical delta, and stop without a terminal ledger if source coverage,
attempt semantics, evidence identity, or independent review cannot be closed.

## DAG integration rule

This planning branch changes no canonical DAG file.  The implementation work
must first read the live canonical DAG after PR-405 receives an exact terminal
receipt.  PR-314 and the proposed PR-315 belong to an already ordered stacked
sequence; they must not be reordered or bypassed.  Register PR-316 only through
the existing generator, append it after the live terminal tail, preserve every
existing node and dependency byte-for-byte, and bind PR-405’s exact terminal
head or failed receipt as an evidence dependency.

```yaml
planning_PR_DAG_mutation: none
future_PR316_registration:
  mode: append_only_after_live_tail
  serial_predecessor: PR-315
  evidence_dependency: PR-405 exact terminal receipt
  forbidden:
    - reorder existing nodes
    - rewrite existing dependencies
    - pretend an open or failed predecessor succeeded
    - manually edit only one DAG mirror
```
