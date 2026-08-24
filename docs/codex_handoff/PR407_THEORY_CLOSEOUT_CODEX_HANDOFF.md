# Codex handoff — PR-407 existing-theory survivor closeout

## Mission

Implement the machine contract in:

```text
docs/codex_handoff/theory_promotion_closeout/AUDIT_COMPILED_EXEC_PLAN.yaml
```

This is a survivor closeout, not a new-theory programme and not a generic
repository cleanup.

The controlling order is:

```text
physics/mathematics research loop
-> frozen survivor/evidence decision
-> research-code coding loop
-> focused CI
-> fresh-context review
```

## Exact source identity

```yaml
repository: cosmosapjw-quantum/htt_base
audited_PR: 407
audited_head: bdad91a204c424030cd6d0e562232b6965a42900
audited_tree: c3cd19442e525aaf1b1e683c1920568513e18da5
operating_profile: private_single_researcher_local_v1
observed_data_used: false
```

## Read first

```text
docs/research_program/theory_promotion/audits/PR407_POST_EXECUTION_ADVERSARIAL_AUDIT.md
docs/codex_handoff/theory_promotion_closeout/RESEARCH_LOOP_CLOSEOUT.yaml
docs/codex_handoff/theory_promotion_closeout/SCIENTIFIC_CONTRACT.md
docs/codex_handoff/theory_promotion_closeout/VALIDATION_MATRIX.yaml
docs/codex_handoff/theory_promotion_closeout/CODING_LOOP_TASK_CONTRACT.yaml
docs/codex_handoff/theory_promotion_closeout/P0_P1_THREAT_CATALOG.json
docs/codex_handoff/theory_promotion_closeout/AUDIT_COMPILED_EXEC_PLAN.yaml
docs/codex_handoff/theory_promotion_closeout/FRESH_REVIEW_CONTRACT.yaml
```

Where PR-407 and this package differ, this package controls. Preserve PR-407
as audit evidence.

## First action — stop unless the stack is exact

Do not allocate a canonical PR number in advance.

1. require an exact terminal disposition for PR #407;
2. re-read the live DAG and all open stacked PRs;
3. verify PR-405, PR-406, and PR-407 ancestry with `git merge-base`;
4. snapshot the ordered node IDs, edges, and execution resolutions;
5. use the existing generator to allocate only the core closeout units;
6. prove that the old node and edge surfaces are exact prefixes;
7. stop on any drift.

Typed stops:

```text
BLOCKED_PREDECESSOR_TERMINAL_RECEIPT
BLOCKED_DAG_PREFIX_DRIFT
BLOCKED_DAG_ID_NOT_ALLOCATED
```

## Research loop — must complete before code

### Phase 1: research contract

Use the exact question and in/out scope from
`RESEARCH_LOOP_CLOSEOUT.yaml`. Do not add a new theorem to solve an old
incomplete row.

### Phase 2: evidence acquisition

For each survivor, resolve and hash:

```yaml
candidate_id:
exact_statement:
assumptions:
domain:
frame:
units:
source_path:
git_blob_sha:
fragment_or_symbol:
evidence_modality:
historical_receipt:
current_replay_receipt:
```

### Phase 3: claim-source audit

Refuse:

- broad reverse-martingale theorem from the PR-284 fixture;
- global orbit separation from VT-T8;
- full covariant dynamics from VT-T13;
- arbitrary tilted-frame no-go from PR-190;
- theorem or observation labels for VT-S14;
- unique theorem count from heterogeneous rows.

### Phase 4: hypothesis decision

The selected hypothesis is:

```text
H3_RESEARCH_FIRST_SURVIVOR_CLOSEOUT_THEN_BOUNDED_CODING
```

Do not reopen H1 or H2 without a reproduced contradiction.

### Phase 5: independent adversarial and physics/math validation

Reproduce:

```yaml
PR284:
  probability: 1/2
  bound: 25/36
  slack: 7/36

VT_T8:
  quotient_dimension: 14
  registered_witness_determinant: 50331648

VT_T13:
  derivative: 3*sqrt(6)*(I2*tr(sigma^2 sigma_dot)-I3*tr(sigma sigma_dot))/I2^(5/2)

PR190:
  normal_frame_W2: 0
  forbidden_targets: [1/25, 3/100]
```

### Phase 6: survivor freeze and decision gate

Freeze these roles:

```yaml
VT_T8: PRIMARY_PROPOSITION_PENDING_NOVELTY
VT_T5_T6_T7_T13: SUPPORTING_LEMMAS
PR190: NEGATIVE_APPLICATION_PENDING_NOVELTY
PR284: INTERNAL_EXACT_EXAMPLE_AND_REGRESSION
VT_S14: SYNTHETIC_VALIDATION
```

The campaign remains `OPEN`; survivor release may still proceed.

## Coding loop

### Phase 0: task contract

Write and commit failing tests before implementation. The user-visible goal is
one current survivor overlay with exact evidence and no new theory.

### Phase 1: reproduction

Preserve byte hashes of PR-405, PR-406, and PR-407 artifacts. Reproduce current
state and exact arithmetic.

### Phase 2: repository localization

Trace:

```text
source statement
-> evidence receipt
-> matrix/overlay projection
-> publication-facing output
-> CI consumer
```

Do not infer truth from status prose.

### Phase 3: bounded design

Compare at most three options. The selected design must be the smallest that:

- binds existing survivors;
- separates campaign and release;
- preserves history;
- adds focused tests;
- does not implement PR-210/216/223 theory.

### Phase 4–5: plan and implementation

Execute core work units A through E in order. Each unit:

1. writes RED tests;
2. records failure;
3. implements the minimal change;
4. runs GREEN tests;
5. runs direct regression and `git diff --check`;
6. commits one independently reviewable risk unit;
7. receives an exact terminal receipt before the next unit.

### Phase 6: software validation

Run import/parse, targeted tests, executable command checks, DAG snapshot
comparison, and existing workflow integration.

### Phase 7: scientific validation

Run statement/domain, exact formula, broad-parent/narrow-child, novelty-role,
and forbidden-claim tests separately.

### Phase 8: numerical and reproducibility validation

Exact arithmetic has zero tolerance. Hash every source/evidence/replay artifact.
Repeated execution must reproduce canonical projections byte-for-byte after
declared timestamp/host fields are removed.

### Phase 9: independent diff review

Use a new context. The first pass is read-only and follows
`FRESH_REVIEW_CONTRACT.yaml`.

### Phase 10: promote, hold, or close

```yaml
promote:
  requires: P0=0 and P1=0 and all survivor evidence closed

hold:
  when: novelty or current replay remains blocked

close_with_blocker:
  accepted: true
  condition: exact blocker evidence exists
```

Never report partial success as completion.

## Core scientific boundaries

### PR-284

```yaml
allowed: exact four-atom finite example
forbidden: general reverse-martingale theorem
Lean_default: FORMAL_ARITHMETIC_REPLAY
new_probability_formalization_required: false
```

### VT-T8

```yaml
allowed: local chart on simple-spectrum cyclic locus
forbidden:
  - global orbit separation
  - invariant-ring completeness
```

### PR-190

```yaml
allowed: same-frame hypersurface-normal obstruction
forbidden: arbitrary tilted-frame or all-Bianchi no-go
```

### VT-S14

```yaml
allowed: preregistered synthetic method validation
forbidden:
  - theorem
  - observation
  - family identification
```

## Deferred work — do not implement

```text
PR197
PR210
PR216
PR222
PR223
```

Record existing findings and exclusions only. These require separate future
decisions and are not dependencies of survivor closeout.

## Agent behavior

```yaml
ask_user_questions: false
guessing_across_spec_boundary: forbidden
unresolved_spec_action: BLOCKED_BY_UNRESOLVED_SPEC
change_expected_science_to_fit_code: forbidden
suppress_failure: forbidden
rewrite_historical_receipts: forbidden
invent_DAG_ids: forbidden
security_or_antitamper_infrastructure: forbidden
new_theory_on_core_path: forbidden
same_agent_final_authority: false
```

## Completion report

```yaml
exact_PR407_terminal_receipt:
allocated_DAG_node_ids:
old_DAG_snapshot_hashes:
new_DAG_snapshot_hashes:
old_surface_exact_prefix:
base_sha:
final_sha:
final_tree:
changed_files:
net_LOC:
research_contract_hash:
evidence_manifest_hash:
survivor_manifest_hash:
status_projection_hash:
PR284_replay:
VT_T8_replay:
VT_T13_replay:
PR190_replay:
novelty_table:
survivor_overlay_hash:
campaign_completion_status:
survivor_release_statuses:
RED_logs:
GREEN_logs:
clean_CI_run_ids:
fresh_review_receipt:
unresolved_blockers:
P0_remaining:
P1_remaining:
verdict:
```
