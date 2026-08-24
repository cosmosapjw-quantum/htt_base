# PR-405 post-execution adversarial scientific audit

## Audit identity

```yaml
schema: htt.theory_promotion_post_execution_adversarial_audit.v1
repository: cosmosapjw-quantum/htt_base
audited_pull_request: 405
audited_base_sha: aaa87d6de692f5c47d5ea9eff963db6dd9ee5be7
audited_head_sha: 463f0999949bf8534c60ad7973b7342705c2e3d6
audited_head_tree: 20eb3e3e117633bc83e743bea45ed024048441e1
audited_changed_files: 10
observed_data_used: false
native_solver_used: false
family_identification_allowed: false
```

## Executive verdict

```yaml
preserve_as_audit_evidence: true
merge_as_authoritative_complete_promotion_matrix: false
merge_as_current_scientific_release: false
required_disposition: REPAIR_BEFORE_AUTHORITY
P0: 3
P1: 10
P2: 4
```

PR-405 recovers valuable observation-independent content and correctly refuses
a current-head publication promotion. Its exact finite PR-284 arithmetic is
correct, its PR-190 same-frame vorticity obstruction is scientifically useful,
and its distinction between broad rows and narrow surviving cores is directionally
right.

The load-bearing failures are not arithmetic mistakes. They are classification
and evidence-model failures:

1. the claimed complete 157-candidate universe is closed only over a list that
   the audit itself chose;
2. `scientific_attempted` records an adjudication/classification attempt rather
   than a genuine proof or experiment for many rows;
3. mathematical truth, evidence strength, current replay, and release eligibility
   are compressed into one terminal state.

Those failures make the aggregate counts and the PR-284 `UNRESOLVED/CAS_CONFLICT`
classification unsuitable as a durable scientific authority.

## Scientific results that survive the hostile audit

### PR-284 registered four-atom fixture

Assumptions are exact and finite:

\[
\Omega=\{0,1,2,3\},\qquad
P(i)=\frac14,\qquad
X=(-3,-1,1,3),
\]

with the registered fine, two-block, and one-block partitions. Direct
enumeration gives

\[
M_0=(-3,-1,1,3),\quad
M_1=(-2,-2,2,2),\quad
M_2=(0,0,0,0),
\]

\[
E[X]=0,\qquad E[X^2]=5.
\]

For \(\lambda=6/5\),

\[
\lambda^2E[X^2]=\frac{36}{5},\qquad
\max_j |M_j|^2=(9,4,4,9).
\]

The inclusive event selects atoms 0 and 3, hence

\[
P\!\left(\max_j |M_j|^2\ge \lambda^2E[X^2]\right)
=\frac12
\le \frac{25}{36}
=\frac1{\lambda^2},
\]

with exact slack \(7/36\).

This is an established finite fixture result. It is not a proof of the broad
reverse-martingale iff statement, convergence, optional stopping, a continuum
mask path, or observed-sky calibration.

### PR-190 exact negative core

Within the registered homogeneous Bianchi-I hypersurface-normal frame,
Frobenius implies vanishing spatial vorticity and therefore \(W^2=0\).
The same-frame targets \(W^2=1/25\) and \(W^2=3/100\) cannot be such
constraint witnesses. This supports the broad attainability failure but does
not make a statement about arbitrary tilted frames.

### Restricted exact cores

The following remain defensible only at their declared scopes:

- the VT-T8 registered rational witness has nonzero local Jacobian and therefore
  supplies a local chart on that slice; it does not prove global orbit separation;
- the VT-T13 identities
  \(\dot I_2=2\operatorname{tr}(\sigma\dot\sigma)\),
  \(\dot I_3=3\operatorname{tr}(\sigma^2\dot\sigma)\), and the registered
  quotient chain rule hold for differentiable STF \(\sigma\) with \(I_2>0\);
- 24 broad rows are exact or premise-conditional source-bound mathematical
  results, not 24 newly current-replayed theorems;
- 8 passing rows are preregistered synthetic method validations, not theorems,
  observations, or family-identification results.

## P0 findings

### P0-TP-001 — candidate-universe completeness is circular

The matrix defines the universe as 152 broad adjudication rows plus five
“independently reportable scoped candidates identified by this audit.” The
coverage proof establishes only that every identifier in that selected list has
one state. It does not provide an exhaustive rule that derives every reportable
subclaim from broad non-PASS rows, registries, deltas, or proof artifacts.

Consequences:

- a sixth narrow core can be omitted without making `coverage_complete=false`;
- campaign exhaustion statements depend on an unproved universe boundary;
- `candidate_universe_sha256` binds a selection, not completeness.

Required repair:

```yaml
until_extractor_closure_is_proved:
  rename: coverage_complete -> enumerated_surface_complete
  forbid:
    - complete_candidate_universe
    - campaign_exhausted
    - no_unclassified_scientific_candidate
stop: BLOCKED_CANDIDATE_UNIVERSE_NOT_CLOSED
```

The repair must define a deterministic candidate extractor and a
source-bound scoped-candidate declaration rule. A mutation that adds a sixth
eligible scoped result must fail the old expected count.

### P0-TP-002 — “scientific attempt” is not a proof/experiment attempt

The terminal taxonomy says `UNRESOLVED` requires a real proof or experiment.
Many rows with missing signatures, unavailable source statements, empty
premises/domains, or unavailable evidence are nevertheless marked
`scientific_attempted=true` because an adjudication pass classified them.

Examples include title-only legacy signatures and rows whose source statement is
`null` or `UNAVAILABLE_SOURCE_STATEMENT`. A classification attempt is not a
scientific proof or experiment.

Consequences:

- `UNRESOLVED=107` and `NOT_ATTEMPTED=11` are not trustworthy;
- the closeout gate can silently consume unattempted science as attempted;
- missing-source rows receive a stronger epistemic status than their evidence.

Required repair:

```yaml
scientific_attempted_requires_one_of:
  - proof_execution_receipt
  - formal_proof_receipt
  - exact_counterexample_receipt
  - preregistered_experiment_receipt
  - explicit_failed_proof_attempt_with_artifact
classification_or_inventory_scan_is_not_scientific_attempt: true
stop: BLOCKED_ATTEMPT_SEMANTICS_INVALID
```

### P0-TP-003 — truth, evidence, replay, and release are conflated

One `scientific_terminal_state` mixes at least four independent questions:

1. is the exact mathematical statement true or refuted?
2. what evidence class supports it?
3. does the current head replay the evidence?
4. is the statement eligible for release under the registered assurance contract?

This causes two opposite distortions:

- historical exact results with current replay gaps are called `PROMOTED`;
- the exact PR-284 finite fixture is called `UNRESOLVED` because one engine is
  unavailable and one assurance policy rejects standard Mathlib axioms.

There is no scientific conflict in PR-284: the executed numerical/formal axes do
not return incompatible mathematical values or a counterexample. The state is
an incomplete/mismatched assurance contract, not `CAS_CONFLICT`.

Required replacement:

```yaml
truth_status:
  - ESTABLISHED
  - REFUTED
  - OPEN
  - NOT_ASSESSED
evidence_status:
  - EXACT_PROOF
  - PREMISE_CONDITIONAL_PROOF
  - EXACT_NEGATIVE_RESULT
  - PREREGISTERED_SYNTHETIC_VALIDATION
  - INCOMPLETE
  - UNAVAILABLE
replay_status:
  - CURRENT_PASS
  - HISTORICAL_PASS_CURRENT_INCOMPLETE
  - CURRENT_BLOCKED
  - CURRENT_FAIL
  - NOT_RUN
release_status:
  - ELIGIBLE
  - BLOCKED
  - NOT_APPLICABLE
```

For PR-284:

```yaml
truth_status: ESTABLISHED
scope: REGISTERED_FINITE_FOUR_ATOM_FIXTURE_ONLY
evidence_status: EXACT_ENUMERATION_AND_FORMAL_ARITHMETIC
replay_status: CURRENT_PARTIAL
release_status: BLOCKED_CAS4_CONTRACT_INCOMPLETE
aggregate_cas_status: INCOMPLETE_BLOCKED
```

`SCIENTIFIC_CONFLICT` must require incompatible computed values, a valid
counterexample to the exact statement, or incompatible domain assumptions.

## P1 findings

### P1-TP-001 — the untyped `36 PROMOTED` aggregate is not a scientific result count

The total combines exact theorems, premise-conditional linear algebra,
synthetic validation, and a negative theorem. The matrix already admits that a
unique-theorem count is unavailable and records only a partial semantic-link
graph.

Required repair: make the result class the primary key and forbid an untyped
promotion total in publication-facing output until equivalence/subsumption
components are adjudicated.

### P1-TP-002 — load-bearing PR-405 files are absent from clean CI

The exact-head workflow is green, but it runs generic repository contracts,
package smoke, Rust compile, and pre-existing lane cells. It does not execute a
validator for the 157-row matrix, the candidate coverage rules, the CAS contract,
all four axis programs, or a scientific-projection hash.

Required repair: add one focused current workflow step; do not create a second
workflow or require a local full-suite run.

### P1-TP-003 — CAS axis relevance is overstated

- Wolfram loads xAct but performs no xAct tensor calculation.
- Sage queries the Singular version, while all obligations are ordinary `QQ`
  arithmetic.
- SymPy, Sage, and Wolfram replay essentially the same enumerative algorithm.
- The main writer authored all four programs; engine diversity is not independent
  human proof authorship.

This is useful cross-engine replay, but not four substantively independent proof
methods. Axis metadata must state `ENGINE_REPLAY_SAME_ALGORITHM` unless a backend
does indispensable work.

### P1-TP-004 — `general_theorem_not_promoted` is a literal constant

SymPy, Sage, and Wolfram set this obligation to `True`; the Lean runner emits it
as `true` after compilation. No axis verifies the matrix/report claim boundary.

Required repair: remove this from numerical axes and implement one independent
scope validator that compares the exact contract statement, exclusions, result
row, report prose, and release surface.

### P1-TP-005 — the Lean axiom rule is incompatible with the selected stack

The contract requires a Mathlib proof “without axioms,” while the runner rejects
any transitive axioms. Standard Mathlib rational proofs commonly report
`propext`, `Classical.choice`, and `Quot.sound`. This is a policy mismatch, not
evidence against the finite statement.

Required repair: preregister separate lists for allowed foundational axioms and
forbidden source/domain axioms. Continue to forbid source `axiom`,
`native_decide`, `sorry`, and unbound scientific assumptions.

### P1-TP-006 — the Lean file proves arithmetic equalities, not typed probability semantics

The Lean source does not define a finite probability space, weighted conditional
expectation, partitions, sigma-algebras, or a tower operator. It proves the
hard-coded rational equalities that those objects should produce.

Either:

- formalize the finite probability/partition semantics and derive the vectors;
  or
- label the axis `FORMAL_ARITHMETIC_REPLAY`, not an independent probability
  theorem.

### P1-TP-007 — the fixture is duplicated across programs

Weights, target, partitions, expected vectors, threshold, and expected outputs
are repeated in four sources. Contract drift can survive when the runner does
not verify every source against one canonical fixture.

Required repair: one content-bound fixture file; every executable axis must
parse it or consume generated language-specific constants whose generator hash
is checked.

### P1-TP-008 — row evidence references are not fully content-bound

Most rows cite paths/fragments or test names. The current exact-head replay
already reports stale metadata/hash/input bindings. The matrix does not prove
that every fragment resolves to the stated proposition at the audited head.

Required repair: a per-candidate evidence manifest with path, blob/hash,
fragment or symbol, statement identity, evidence class, and replay receipt.

### P1-TP-009 — current replay failures are prose, not completion evidence

The 48/8 and 357/4 results appear in the audit, but the exact commands,
environment, logs, failed-node identities, and expected remediation hashes are
not a machine-enforced completion bundle.

Required repair: retain focused logs and require every failed node to be either
repaired or explicitly superseded before current release eligibility.

### P1-TP-010 — five historical science failures were not absorbed into regression gates

PR-405 correctly identifies the issues, but prose alone will allow recurrence.

Permanent gates are required for:

1. PR-216: complete branch-specific Gauss/momentum/connection/vorticity terms;
2. PR-223: nonnegative weights and a PSD moment-cone constructive theorem;
3. PR-197: finite-rank resolution \(1/(n+1)\le\alpha\) and arbitrary tie blocks;
4. PR-210: nonempty validity domain and an actual frame transformation;
5. PR-222: physical CF4 window/transfer/covariance/frame/unit bindings.

Each is a separate scientific risk unit and must not be bundled into one
cleanup PR.

## P2 findings

1. `CAS_CONFLICT` should be reserved for contradictory scientific outputs.
2. “Doob theorem” wording should be restricted to a registered finite maximal
   inequality instance unless a general theorem is separately linked.
3. `PROMOTED` is too release-like a word for a truth/evidence state even when a
   separate release field exists.
4. A generic green CI badge should not be quoted as validation of files it did
   not execute.

## Constructive repair sequence

The implementation must use separate, reviewable risk units.

### Work unit A — status ontology corrigendum

Split truth, evidence, replay, and release status. Reclassify rows from actual
receipts. Preserve historical artifacts and PR-405 as failed/provisional audit
evidence.

### Work unit B — candidate extraction and semantic graph

Generate the broad universe deterministically. Introduce a scoped-candidate
declaration registry, relation graph, and mutation tests. Until closure is
proved, report only `enumerated_surface_complete`.

### Work unit C — PR-284 CAS contract repair

Create one canonical fixture, repair axis applicability and Lean axiom policy,
derive conditional expectations from the fixture, replace the literal scope
boolean with a real validator, and use a non-conflict incomplete state when an
axis is blocked.

### Work unit D — evidence binding and focused CI

Bind every promoted/established row to exact evidence and current replay. Add
the focused validator and CAS package to the existing workflow.

### Work units E1–E5 — permanent scientific regression repairs

One work unit each for PR-197, PR-210, PR-216, PR-222, and PR-223. No combined
generic assurance PR.

### Work unit F — current downstream overlay

After A–E close, generate a downstream overlay over frozen PR-275/285/286
history. Publish exact theorem, conditional theorem, exact negative result, and
synthetic validation in separate sections. Do not publish a unique-theorem
count until the semantic graph closes.

## DAG preservation

This audit package intentionally assigns no canonical PR number.

At implementation time:

1. re-read the live canonical DAG and status from the target branch;
2. resolve the exact PR-405 terminal receipt and any concurrent post-freeze
   stacked work;
3. allocate the next available IDs using the existing generator;
4. require the complete pre-existing topological order to be an exact prefix of
   the regenerated order;
5. append A, B, C, D, E1, E2, E3, E4, E5, F in that order;
6. reject any modified historical dependency, reordered existing node, or
   manually guessed PR number.

```yaml
stop_if_prefix_changes: BLOCKED_DAG_PREFIX_DRIFT
stop_if_id_is_guessed: BLOCKED_DAG_ID_NOT_ALLOCATED
stop_if_predecessor_unresolved: BLOCKED_PREDECESSOR_TERMINAL_RECEIPT
```

## Merge gate

```yaml
required:
  P0: 0
  P1: 0
  exact_existing_DAG_prefix_preserved: true
  PR405_historical_evidence_preserved: true
  PR284_finite_fixture_truth_status: ESTABLISHED
  PR284_general_theorem_status: NOT_ESTABLISHED
  scoped_candidate_extractor_closed_or_completeness_wording_removed: true
  untyped_promoted_total_publication_forbidden: true
  focused_clean_CI: PASS
  fresh_context_review: PASS
forbidden:
  observed_result: true
  native_transfer_claim: true
  Bianchi_family_identification: true
  new_security_framework: true
```
