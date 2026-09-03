# PR-407 post-execution adversarial audit and survivor-closeout decision

## Exact identity

```yaml
schema: htt.pr407_post_execution_adversarial_audit.v1
repository: cosmosapjw-quantum/htt_base
audited_pull_request: 407
audited_base_sha: 179ae4216082ca9b6c685f5bdba6bb269a0e273a
audited_head_sha: bdad91a204c424030cd6d0e562232b6965a42900
audited_head_tree: c3cd19442e525aaf1b1e683c1920568513e18da5
changed_files: 6
science_code_changed: false
canonical_dag_changed: false
observed_data_used: false
operating_profile: private_single_researcher_local_v1
research_harness: physmath-research-harness-gpt56(20260824-172831)
coding_harness: physmath-coding-harness-gpt56(20260824-172831)
```

## Executive verdict

```yaml
preserve_PR407_as_planning_evidence: true
execute_PR407_as_written: false
merge_as_final_closeout_contract: false
current_scientific_release_authority: false
findings:
  P0: 3
  P1: 10
  P2: 4
decision: SPLIT_SURVIVOR_CLOSEOUT_FROM_CAMPAIGN_COMPLETION_AND_DEFER_NEW_THEORY
next_capability: EXISTING_THEORY_SURVIVOR_CLOSEOUT_WITH_TYPED_EVIDENCE_AND_FOCUSED_REPLAY
```

PR-407 is a substantial improvement over PR-405 and PR-406. It separates the
five-state campaign disposition from truth/evidence/replay/release, preserves
`NOT_ATTEMPTED != REFUTED`, rejects a mega-PR implementation, and requires
content-bound evidence, focused CI, and a fresh-context reviewer.

It is not yet the right implementation authority for the present goal. The
request is to finish already established results rather than solve the full
historical proof campaign. PR-407 still projects status before source/evidence
closure, allows established truth to generate campaign promotion, and makes
five new scientific-development tracks predecessors of survivor release.

The replacement package therefore runs the physics/mathematics research loop
first, freezes a survivor/evidence decision, and only then passes a narrower
scientific contract to the coding loop.

---

# 1. Research-loop closeout

## Research question

Which exact observation-independent results already present in the repository
are established at a bounded scope, what evidence supports them, what remains
unproved, and what is the smallest append-only implementation needed to close a
current survivor release without inventing new theory?

## In scope

- PR-284 finite four-atom fixture;
- PR-190 same-frame normal-vorticity obstruction;
- VT-T5, VT-T6, VT-T7, the restricted VT-T8 local chart, and VT-T13 chain rule;
- VT-S14 preregistered synthetic validation;
- exact source/evidence/replay/release projection;
- novelty and publication-unit triage;
- append-only DAG integration and focused regressions.

## Out of scope

- general reverse-martingale theorem;
- global orbit separation or invariant-ring completeness;
- new frame-transformation derivation;
- new branch-complete Einstein-matter constraint derivation;
- new physical moment-cone theorem;
- observed data, native transfer, geometry detection, or Bianchi-family identification;
- security, cryptographic authorization, or anti-tamper machinery.

## Hypothesis decision

```yaml
H1_EXECUTE_PR407_AS_WRITTEN: REJECT
H2_PATCH_ONLY_COMMAND_AND_DAG_DEFECTS: REJECT
H3_RESEARCH_FIRST_SURVIVOR_CLOSEOUT_THEN_BOUNDED_CODING: PROMOTE
```

H3 is the smallest path that puts evidence before decision, releases existing
survivors without exhausting unrelated proposals, and does not hide broad
failed or inconclusive parents.

---

# 2. Scientific results

## 2.1 PR-284 exact finite fixture

The registered fixture is

\[
\Omega=\{0,1,2,3\},\qquad P(i)=\frac14,\qquad
X=(-3,-1,1,3).
\]

For the fine, two-block, and one-block partitions,

\[
M_0=(-3,-1,1,3),\qquad
M_1=(-2,-2,2,2),\qquad
M_2=(0,0,0,0).
\]

Also

\[
E[X]=0,\qquad E[X^2]=5.
\]

At \(\lambda=6/5\),

\[
\lambda^2E[X^2]=\frac{36}{5},\qquad
\max_j |M_j|^2=(9,4,4,9).
\]

The inclusive event holds on atoms zero and three, hence

\[
P\!\left(\max_j|M_j|^2\geq\lambda^2E[X^2]\right)
=\frac12\leq\frac{25}{36}=\frac1{\lambda^2},
\]

with exact slack \(7/36\). If \(X\) has unit \(U\), both quantities inside
the event have unit \(U^2\), while the probability and bound are dimensionless.

```yaml
truth_status: ESTABLISHED
evidence_modality:
  - EXACT_FINITE_ENUMERATION
  - EXACT_ENGINE_REPLAY
  - FORMAL_ARITHMETIC_REPLAY
replay_status: CURRENT_PARTIAL
publication_role: INTERNAL_REGRESSION
broad_reverse_martingale_theorem: NOT_ESTABLISHED
```

This is a useful exact example and regression fixture, not a standalone new
martingale theorem. Lean currently checks arithmetic equalities; it should be
labelled `FORMAL_ARITHMETIC_REPLAY` unless typed probability/partition semantics
already exist independently.

## 2.2 PR-190 same-frame obstruction

For the registered homogeneous Bianchi-I chart adapted to a
hypersurface-normal congruence, Frobenius gives

\[
\omega_i=0,\qquad
W^2=3\sum_i(\omega_i/\Theta)^2=0.
\]

The registered targets instead require

\[
W^2=\frac1{25},\qquad W^2=\frac3{100}
\]

in the same frame. They therefore cannot be hypersurface-normal constraint
witnesses.

```yaml
truth_status: ESTABLISHED
evidence_modality: HAND_DERIVATION_AND_EXACT_COUNTEREXAMPLE
scope: SAME_FRAME_HYPERSURFACE_NORMAL_BIANCHI_I
tiltded_or_arbitrary_frame_extension: NOT_ESTABLISHED
novelty_status: APPLICATION_SPECIFIC_UNASSESSED
publication_role: NEGATIVE_APPLICATION
```

The underlying normal-congruence vorticity fact is standard. Potential novelty
lies only in its precise registered-target application.

## 2.3 VT-T5 through VT-T8

One real symmetric trace-free \(3\times3\) tensor contributes five parameters;
four vectors contribute twelve. The generic input dimension is therefore

\[
5+4\times3=17.
\]

After quotienting a generic three-dimensional \(SO(3)\) orbit, the quotient
dimension is

\[
17-3=14,
\]

matching the fourteen declared coordinates.

The restricted local-chart Jacobian factor is

\[
-48v_{01}^4v_{02}^4v_{03}^4
(\lambda_1-\lambda_2)^5
(\lambda_1+2\lambda_2)^5
(2\lambda_1+\lambda_2)^5.
\]

At the registered witness \(\lambda=(-2,0,2)\), \(v_0=(1,1,1)\), its value is

\[
50331648\neq0.
\]

Thus the declared functions provide local coordinates on the simple-spectrum,
cyclic open locus. This proves neither global orbit separation nor invariant
ring completeness.

```yaml
VT_T5: SUPPORTING_LEMMA
VT_T6: SUPPORTING_LEMMA
VT_T7: SUPPORTING_LEMMA
VT_T8: PRIMARY_PROPOSITION_PENDING_NOVELTY
```

Broad invariant-basis and independent-invariant literature already exists for
SO(3)/O(3) vector and symmetric-tensor actions. The exact Krylov-moment chart and
factorization require a statement-level novelty comparison before publication.

## 2.4 VT-T13 chain-rule core

For differentiable STF \(\sigma\),

\[
I_2=\operatorname{tr}(\sigma^2),\qquad
I_3=\operatorname{tr}(\sigma^3),
\]

so

\[
\dot I_2=2\operatorname{tr}(\sigma\dot\sigma),\qquad
\dot I_3=3\operatorname{tr}(\sigma^2\dot\sigma).
\]

For \(I_2>0\) and
\(J_\sigma=\sqrt6 I_3/I_2^{3/2}\),

\[
\dot J_\sigma=
3\sqrt6\,
\frac{I_2\operatorname{tr}(\sigma^2\dot\sigma)
-I_3\operatorname{tr}(\sigma\dot\sigma)}{I_2^{5/2}}.
\]

This is an exact supporting lemma, not the requested full covariant evolution
law involving Weyl, stress, acceleration, and vorticity variables.

## 2.5 VT-S14

The positive synthetic cell and proportional-design negative control remain a
preregistered method-validation result only.

```yaml
evidence_modality: PREREGISTERED_SYNTHETIC_EXPERIMENT
publication_role: SYNTHETIC_VALIDATION
theorem: false
observational_result: false
family_identification: false
```

## 2.6 Aggregate counts

`36 PROMOTED` mixes broad exact/conditional rows, narrow cores, one negative
result, and synthetic validation. It is not a theorem count, novelty count, or
publication count. Likewise the 157-ID surface is closed only relative to its
registered extractor; it is not the universe of every reportable mathematical
consequence.

---

# 3. P0 findings

## P0-407-001 — decision precedes evidence closure

PR-407 orders status ontology before candidate/source/evidence closure. A
receipt type can classify provenance but cannot establish the exact statement
or its truth.

Required order:

```text
survivor/source freeze
-> content-bound evidence ledger
-> claim-source and semantic audit
-> physics/math validation
-> status/release projection
```

Gate: `test_status_projection_refuses_without_closed_evidence_manifest`.

Stop: `BLOCKED_DECISION_BEFORE_EVIDENCE`.

## P0-407-002 — truth can generate campaign promotion

The plan says campaign disposition is orthogonal to truth but also contains an
`ESTABLISHED -> PROMOTED` mapping. Mathematical truth cannot rewrite a
historical campaign outcome. Any current campaign disposition requires an
exact campaign decision receipt.

The broad PR-284 reverse-martingale row and the narrow finite-fixture child are
different candidate IDs. The child may receive a new decision only after a
source-bound child declaration; the broad parent remains unresolved.

Gates:

```text
test_truth_does_not_imply_historical_campaign_promotion
test_campaign_disposition_requires_exact_campaign_receipt
test_pr284_broad_and_finite_child_are_distinct_candidates
```

Stop: `BLOCKED_TRUTH_CAMPAIGN_CONFLATION`.

## P0-407-003 — registered surface is called a universal candidate universe

A deterministic extractor proves closure of a declared registry or source
manifest. It cannot prove that every reportable narrower mathematical
consequence has been identified unless those consequences are themselves part
of the source schema.

Use `REGISTERED_CANDIDATE_SURFACE_CLOSED`, never
`ALL_REPORTABLE_SCIENTIFIC_CANDIDATES_EXHAUSTED`.

Gate: `test_registered_surface_closure_never_emits_universal_candidate_claim`.

Stop: `BLOCKED_UNIVERSAL_CANDIDATE_OVERCLAIM`.

---

# 4. P1 findings

1. **Campaign exhaustion versus survivor release.** Zero `NOT_ATTEMPTED` is a
   valid campaign-completion condition, not a prerequisite for releasing an
   independently established survivor.

2. **New theory on the critical path.** PR-210, PR-216, and PR-223 require new
   derivations; PR-197 and PR-222 also exceed a pure closeout if treated
   broadly. They must be deferred, not mandatory predecessors.

3. **Stale predecessor.** Future implementation must require the exact PR-407
   terminal, not merely PR-405.

4. **Ambiguous base checks.** Distinct ancestor identities require
   `git merge-base --is-ancestor`; one `git rev-parse HEAD` command cannot prove
   three historical bases.

5. **Non-executable heredoc.** Every machine-plan command needs a syntax test;
   the folded inline heredoc is invalid shell.

6. **DAG prefix assertion lacks a comparator.** Freeze ordered node IDs, edges,
   and resolution hashes before append and compare them exactly after append,
   then run the generic validator.

7. **Evidence modality is too coarse.** Separate hand derivation, finite
   enumeration, symbolic identity, formal proof, arithmetic replay,
   counterexample, and synthetic experiment.

8. **PR-407 documents are not load-bearing CI.** Existing generic CI is green,
   but a successor must parse and cross-check the closeout package in the
   existing Repository-integrity workflow.

9. **Novelty and publication role are absent.** Truth is not novelty. Any
   publication-ready result needs statement-level literature comparison.

10. **Research-to-coding handoff is implicit.** Durable research contract,
    evidence ledger, decision gate, scientific contract, validation matrix, and
    fresh-review contract are required.

---

# 5. P2 findings

1. release state needs exact target and blockers;
2. the PR-405 -> PR-406 -> PR-407 precedence chain needs one controlling
   read-first surface;
3. the next implementation must avoid another meta-framework expansion;
4. current xAct/Singular labels are stronger than their executed mathematical
   use and should be treated as historical labels or honest engine replay.

---

# 6. Survivor-only development decision

## Core track

```yaml
A: research survivor and evidence freeze
B: status and survivor-release projection
C: exact replay of existing results only
D: novelty and publication-role overlay
E: focused CI and fresh-context review
```

## Deferred track

```yaml
PR197: DEFERRED
PR210: DEFERRED_NEW_TRANSFORMATION
PR216: DEFERRED_NEW_PHYSICS_DERIVATION
PR222: DEFERRED_PHYSICAL_BINDING
PR223: DEFERRED_NEW_THEOREM
```

These are not dependencies of existing-result closeout and receive no new DAG
node without a later explicit decision.

## Release candidate A — invariant and local quotient geometry

```yaml
primary: VT-T8 restricted local chart
support:
  - VT-T5
  - VT-T6
  - VT-T7
  - VT-T13 chain rule
required_before_release:
  - exact current evidence binding
  - semantic deduplication
  - statement-level novelty comparison
  - independent mathematical review
forbidden:
  - global orbit separation
  - invariant-ring completeness
  - full covariant dynamics
```

## Release candidate B — scoped negative obstruction

```yaml
primary: PR-190 same-frame normal-vorticity obstruction
role: NEGATIVE_APPLICATION
novelty_status: APPLICATION_SPECIFIC_UNASSESSED
forbidden:
  - arbitrary tilted-frame no-go
  - all-Bianchi no-go
```

## Internal artifacts

```yaml
PR284: INTERNAL_EXACT_EXAMPLE_AND_REGRESSION
VT_S14: SYNTHETIC_METHOD_VALIDATION
```

---

# 7. DAG rule

This audit PR changes no canonical DAG or status mirror.

Future implementation must:

1. obtain the exact PR-407 terminal receipt;
2. re-read the live DAG and open stacked PRs;
3. snapshot ordered node IDs, edges, resolutions, and hashes;
4. allocate IDs with the existing generator;
5. prove the old nodes, edges, and resolutions are exact prefixes;
6. append core A through E only;
7. stop on predecessor or prefix drift.

```yaml
stops:
  - BLOCKED_PREDECESSOR_TERMINAL_RECEIPT
  - BLOCKED_DAG_PREFIX_DRIFT
  - BLOCKED_DAG_ID_NOT_ALLOCATED
```

## Final disposition

```yaml
decision: PRESERVE_PR407_BUT_SUPERSEDE_ITS_EXECUTION_ORDER
implementation_authority: docs/codex_handoff/theory_promotion_closeout/AUDIT_COMPILED_EXEC_PLAN.yaml
research_loop_required_first: true
coding_loop_required_second: true
fresh_context_review_required: true
merge_gate:
  P0: 0
  P1: 0
```
