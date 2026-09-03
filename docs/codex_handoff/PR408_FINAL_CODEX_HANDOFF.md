# Codex handoff — final PR-408 survivor closeout

## Controlling surfaces

Read in this order:

```text
docs/research_program/theory_promotion/audits/PR408_FINAL_ADVERSARIAL_AUDIT.md
docs/codex_handoff/pr408_final/PACKAGE_INDEX.yaml
docs/codex_handoff/pr408_final/WU-001.yaml
docs/codex_handoff/pr408_final/WU-002.yaml
docs/codex_handoff/pr408_final/WU-003.yaml
docs/codex_handoff/pr408_final/WU-004.yaml
docs/codex_handoff/pr408_final/WU-005.yaml
docs/codex_handoff/pr408_final/WU-006.yaml
docs/codex_handoff/pr408_final/WU-007.yaml
```

The older PR-408 package remains planning evidence. Where it differs, this
final package controls. Do not create another planning successor.

## Mission

Close already-present observation-independent results without developing new
theory, silently omitting eligible survivors, or claiming campaign exhaustion.

## Start gate

1. Resolve the exact human-approved terminal commit and tree of PR #408.
2. Start from that exact commit or a descendant.
3. Prove `bdad91a204c424030cd6d0e562232b6965a42900` is an ancestor.
4. Re-read the live DAG and all open stacked PRs.
5. Snapshot existing ordered node IDs, edges, resolutions, and hashes.
6. Allocate canonical IDs using the existing generator.
7. Append WU-001 through WU-007 in order.
8. Prove old nodes, edges, and resolutions are exact prefixes.

Do not require a separate PR-407 human terminal receipt once the approved
PR-408 terminal and PR-407 ancestry are established.

## Research before code

WU-001 is triage only. It may not assign truth, novelty, or publication roles.
Every research unit may return:

```text
RETAIN
NARROW
DEFER
EXCLUDE
BLOCKED_BY_UNRESOLVED_SPEC
```

Do not preserve a role merely because an earlier audit expected it.

## Scientific boundaries

### PR-284

Allowed: one exact equal-weight four-atom finite example.

Forbidden: a general reverse-martingale theorem or a typed Lean probability
proof unless independently present. The current Lean default is
`FORMAL_ARITHMETIC_REPLAY`.

### VT-T8

Allowed without additional evidence: full-rank Jacobian of fourteen invariant
functions on the registered slice.

Allowed only with a resolved transverse-slice argument: local coordinates on
the simple-spectrum cyclic SO(3) quotient.

Forbidden: global orbit separation, integrity-basis completeness, or a global
quotient atlas.

### PR-190

Allowed: same-frame hypersurface-normal Bianchi-I obstruction.

Forbidden: tilted-frame or all-Bianchi no-go.

### VT-S14

Allowed: preregistered synthetic method validation.

Forbidden: theorem, observation, or family identification.

## Novelty gate

For VT-T8 and PR-190 produce:

```yaml
candidate_statement:
search_date:
queries:
sources:
nearest_results:
comparison_dimensions:
  - representation_and_group_action
  - tensor_and_vector_content
  - invariant_family
  - local_or_global_scope
  - generating_or_separating_claim
  - explicit_chart_or_factorization
overlap:
difference:
novelty_decision:
reviewer:
```

Seed sources:

```text
arXiv:1810.10397
arXiv:1511.01311
arXiv:1807.04817
arXiv:gr-qc/9812046
```

These are search seeds, not automatic novelty decisions.

## Agent policy

```yaml
ask_user_questions: false
guessing_across_spec_boundary: forbidden
unresolved_spec_action: BLOCKED_BY_UNRESOLVED_SPEC
change_expected_science_to_fit_code: forbidden
rewrite_historical_receipts: forbidden
invent_canonical_PR_ids: forbidden
new_theory_on_closeout_path: forbidden
security_or_antitamper_work: forbidden
partial_success_reported_complete: forbidden
same_agent_final_authority: false
```

## Completion

```yaml
registered_survivor_surface_closed: true
all_included_candidates_have_research_decision_receipts: true
all_excluded_or_deferred_candidates_have_reasons: true
overlay_replays_deterministically: true
load_bearing_clean_CI: PASS
fresh_context_review:
  P0: 0
  P1: 0
final_differential_audit:
  P0: 0
  P1: 0
```

A precise blocker is a valid terminal. A plan or partial implementation is not
completion.
