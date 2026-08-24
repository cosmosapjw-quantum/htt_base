# PR-406 differential audit — hardening the PR-405 repair plan

## Exact identity

```yaml
schema: htt.theory_promotion_plan_differential_audit.v1.1
audited_science_pull_request: 405
audited_science_head: 463f0999949bf8534c60ad7973b7342705c2e3d6
audited_plan_pull_request: 406
package_audited_plan_head: 3ffa49ab3edfcbad63ebce4aabed48c70f70684d
audited_plan_head: 179ae4216082ca9b6c685f5bdba6bb269a0e273a
audited_plan_tree: 1a3d61c8c5e44d130f2b3b01a1091bac1f426db3
live_revalidation_date: 2026-08-25
planning_overlay_role: STRICTER_APPEND_ONLY_CONTRACT
```

PR-406 correctly absorbs most of the highest-value PR-405 lessons: deterministic
source discovery, attempt-receipt semantics, typed evidence kinds, scoped-child
derivation, content-bound CAS receipts, a corrected Lean foundational-axiom
policy, static claim containment, focused CI, and a fresh-context read-only
reviewer. It should be preserved as useful planning evidence.

The later `179ae421...` self-review commit improves deterministic
serialization, raw-receipt retention, and canonical-output checks. It does not
add independent `truth_status` or `replay_status` fields, a typed Lean
probability obligation or arithmetic-only downgrade, a single canonical
cross-axis fixture, or separate work units for PR-197/210/216/222/223.
Accordingly, the findings below remain live at the exact audited head.

It is not sufficient as the final Codex execution contract for four reasons.

## P0-406-001 — truth, evidence, replay, and release remain incompletely separated

PR-406 separates `evidence_state`, `evidence_kind`, and
`current_release_state`, but it has no independent `truth_status` and
`replay_status`. The PR-284 case is exactly the counterexample: the finite
four-atom statement is true by exact enumeration, while the four-axis replay is
partial and the historical release contract is blocked. Engine availability
must not move the mathematical truth field.

Required fields:

```yaml
truth_status: ESTABLISHED | REFUTED | OPEN | NOT_ASSESSED
evidence_status: EXACT_PROOF | CONDITIONAL_PROOF | EXACT_NEGATIVE_RESULT | SYNTHETIC_VALIDATION | INCOMPLETE | UNAVAILABLE
replay_status: CURRENT_PASS | HISTORICAL_PASS_CURRENT_INCOMPLETE | CURRENT_BLOCKED | CURRENT_FAIL | NOT_RUN
release_status: ELIGIBLE | BLOCKED | NOT_APPLICABLE
```

Mechanical gate:

```text
test_truth_status_is_invariant_under_engine_availability
```

## P1-406-001 — one planned PR contains too many independently rejectable risks

PR-406 describes candidate discovery, status ontology, semantic deduplication,
CAS execution, Lean policy, claim containment, CI, report generation, and
review receipt as one `PR-316`. These are separable failure domains. A reviewer
could accept the source extractor while rejecting the CAS contract, or accept
the CAS repair while rejecting one of the historical physical claims.

The implementation must therefore allocate a linear append-only sequence of
small risk units after a live DAG reread, not implement the entire plan in one
mega-PR. The canonical IDs are allocated by the existing generator and are not
hard-coded by this overlay.

## P1-406-002 — the Lean axis still lacks a typed semantic obligation

The existing Lean file proves hard-coded rational equalities. PR-406 corrects
the foundational-axiom false negative, but its plan does not require either:

1. a finite probability space, weighted partitions, and derived conditional
   expectations in Lean; or
2. an explicit downgrade to `FORMAL_ARITHMETIC_REPLAY`.

One of those two outcomes is mandatory. Compilation of the arithmetic bundle
alone is not an independent formal proof of the probability-theorem wording.

## P1-406-003 — one canonical fixture is not required across all axes

PR-406 forbids literal computed outputs and binds program hashes, but does not
require a single content-bound owner for weights, target, partitions, lambda,
and event semantics. The same fixture is duplicated in the Wolfram, SymPy,
Sage, and Lean sources. A canonical fixture or a checked generator projection
is required to prevent cross-axis drift.

## P1-406-004 — five scientific findings remain prose rather than permanent gates

PR-405 identified substantive defects in PR-197, PR-210, PR-216, PR-222, and
PR-223. PR-406 repairs the meta-ledger but does not compile those findings into
separate scientific regression work units. They must be absorbed permanently:

- PR-197: finite-rank resolution and arbitrary exchangeable tie blocks;
- PR-210: nonempty validity domain and an actual frame transformation;
- PR-216: branch-complete homogeneous Gauss/momentum/connection/vorticity terms;
- PR-222: physical CF4 window/transfer/covariance/frame/unit binding;
- PR-223: nonnegative PSD moment cone and constructive antipodal decomposition.

## Disposition

```yaml
preserve_PR406: true
execute_PR406_as_written: false
required_action: APPLY_STRICTER_OVERLAY_THEN_DECOMPOSE
canonical_DAG_mutation_in_this_overlay: false
P0_added: 1
P1_added: 4
```

The machine-readable overlay is
`docs/codex_handoff/theory_promotion_reconciliation/AUDIT_COMPILED_EXEC_PLAN.yaml`.
Its work units A through F supersede the single-mega-PR execution shape while
preserving the useful PR-406 design content.
