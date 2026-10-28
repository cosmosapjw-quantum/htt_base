# Convergence integration — C2/C4/C5/C6

The existing controller can carry this delivery programme without a new controller,
runtime reset, or replacement of the scientific DAG. Append six finite tasks, use
typed product prerequisites inside those six tasks, and preserve older tasks as
existing work. Ready legacy research can continue before final compilation; exact
external holds need not become prerequisites of a finite report.

## Evidence and actual defects

Inspected base `bdead6a8f51282ca647224b460b0f65de085568b`, root AGENTS, local
`htt-dag-orchestrator` and `htt-harness-engineering`, current runtime/controller
guidance, `research_controller.py`, `publication_frontier_preflight.py`,
`native_routing.py`, and controller tests. The current R36-06 archive publishes
reviewed streaming source/lifecycle tests (16-child limit, default 4), not MC100
qualification or live adoption. Its README explicitly preserves this distinction.

Two in-memory counterexamples were executed before editing:

1. With ready `R36-OLD` carrying `priority:100` and `R37-00-FIRST-REPORT` carrying
   `priority:0`, `next_packet` chose `R36-OLD`. Existing ordering is
   `(last_turn, task_id)`; arbitrary priority metadata is ignored. The builder's
   initial authored order only applies to new campaign initialization, not to
   append-frontier. Reinitializing an existing campaign would be the wrong fix.
2. With all tasks held and previously enabled adaptive research, `next_packet`
   created an `adaptive-discovery` packet. Therefore a finite-delivery handoff
   that merely says "finish" could still expand the frontier after ready work
   was exhausted.

## Implemented smallest repair

Only `scripts/codex_harness/research_controller.py` and the new focused
`test_research_controller_convergence.py` were changed by this worker.

- `next --prefer-task TASK_ID` is repeatable and ordered. It changes selection
  among eligible, route-available tasks only. A report's execute and review phases
  both get the preference while ready. Dependencies and qualified products are
  not bypassed.
- `next --defer-task TASK_ID` is repeatable. A final compilation task is considered
  after other ready tasks; if only it is executable it runs. Held tasks are not
  converted into completed prerequisites. This is scheduling, not acceptance.
- `next --no-discovery` suppresses creation of a new adaptive-discovery packet.
  It preserves adaptive history/authorization and continues existing normal tasks.
  Already planned/running discovery packets still replay/wait under their existing
  identity; an existing native outcome must be reconciled, not silently deleted.
- Unknown IDs, duplicate IDs, or the same ID in both preference/defer lists are
  rejected before state mutation. Append the frontier before selecting its IDs.
- Without these options, scheduling, packet identity and state changes are the
  previous behavior. No state migration or new persistent policy object is needed.

The Python parameters are `preferred_tasks=()`, `deferred_tasks=()` and
`allow_discovery=True`. The ordering tuple becomes
`(is_deferred, preference_index, last_turn, task_id)`; with defaults its first two
coordinates are constant. Existing pending packets, running-writer protection,
released-acquisition freshness, review-only constraints and resume reservations
are checked before candidate ordering. The controller still does not dispatch.

## Exact uptake route

Use the existing owner checkout and its actual state path. Read the active pointer
and reconcile the currently planned/running packet before integrating a new Git
revision; do not overwrite dirty work, initialize another campaign, cancel an
unknown native launch, or rewrite frozen source bindings. The remote desktop was
offline in this session; no live state or provider cache was observed or altered.

```bash
python scripts/codex_harness/publication_frontier_preflight.py \
  --state "$STATE" --frontier "$FRONTIER" --manifest "$MANIFEST"
# If APPEND_READY, append exactly once; ALREADY_APPENDED means continue.
python scripts/codex_harness/research_controller.py --state "$STATE" append-frontier \
  --frontier "$FRONTIER" --authorization '2026-10-28 owner-authorized finite report convergence'
python scripts/codex_harness/research_controller.py --state "$STATE" next \
  --prefer-task "$FIRST_REPORT_TASK" --defer-task "$FINAL_REPORT_TASK" --no-discovery \
  --available-profile gpt-6.1-sol/medium --available-profile gpt-6-sol/high \
  --available-profile gpt-6-astra/xhigh --available-profile gpt-6-astra/ultra
```

Profile arguments above are examples matching current routing policy. The host
must supply only profiles actually available through its transport. Source
policy requests and independently observed author/reviewer identity remain
different. Actual spawn, ack, raw result, record, independent review, record and
next continue under the existing protocol. Keep these convergence options on
subsequent `next` calls; they do not persist in the state or silently alter later
unrelated runs.

Use the actual current task IDs in `$FIRST_REPORT_TASK` and `$FINAL_REPORT_TASK`.
The report task need not depend on older external source gates: its contract is
a source-bound synthesis of already available results. The four analytical tasks
require the first report product. The final task also requires that baseline
product, consumes every accepted analytical product, and preserves exact held
analysis obligations without an all-analysis-success barrier. A stronger empirical claim remains a separately named product
with its original source requirements. Never qualify a missing empirical result
by renaming its source-gap note.

## Ownership, dependencies and stop conditions

The selected-frontier preflight requires input_sources with repo-relative `path`
and SHA-256, a manifest `files` list, and task ownership under
`<frontier-directory>/products/<task-id>`. Existing older dependencies can be
consumed as versioned files/products where already qualified. Do not create
typed leaves referencing absent live task IDs: static preflight constructs an
anchor-only state and correctly rejects such unknown references.

`append-frontier` retains campaign identity, old task specs/states/histories,
packets, event prefixes, cumulative turns and ultra accounting. Appended tasks
must start ready, carry real semantic delta and actual later execution/review.
Pre-existing report bytes are inputs to a new synthesis task, not a reason to
forge its controller completion.

For long acquisition, normal `next` retains the one-writer rule. If work can
cooperatively yield, use the already implemented `checkpoint-acquisition` with
actual worker and independent host quiescence evidence. Never fabricate that
evidence to free a report slot. A read-only review may use `--review-only` only
under the existing disjointness/freshness gate. No new concurrency policy is
needed for this convergence change.

After the first report, execute and independently review each feasible analytical
product, finish remaining executable known tasks that can improve the report,
and compile the final source-bound reports. An analysis that remains genuinely
held is listed with its exact residual obligation and is never counted complete. With `--defer-task FINAL`, such ready
tasks are considered before final compilation. Once the final deliverable is verified and no
authorized known action can improve it, return the final documents plus exact
remaining original input obligations. Do not launch a new discovery cycle merely
to make a 42-node counter increase. Final report completion and original physical
acceptance remain separate fields. Current READY and counts must come from the
actual state; this read-only source snapshot cannot supply live completion counts.

## Validation actually performed

- New focused suite: 13 tests, all PASS. Covers CLI, argument rejection, default
  equivalence, preference/review ordering, prerequisites, legacy continuation,
  deferred final, active packet/running writer preservation, existing discovery,
  adaptive state preservation, and acquisition-resume exclusivity.
- Existing core suite: 30 tests, all PASS.
- Existing acquisition-checkpoint suite: 24 run, 23 PASS, 1 owner-live-fixture SKIP.
- Broad controller discovery: 198 run; 173 PASS, 13 SKIP, 12 ERROR. Ten errors
  require absent owner `/mnt/extdrive` frozen fixtures; one requires the
  sparse-checkout-omitted `.codex/hooks/session_start_context.py`; one is a
  pre-existing test import identity collision. `BlindRepairTests` imports frontier
  tests that replace the base test module's `rc` with a second controller module;
  the caught `ControllerError` class and thrown class then differ.
- The same single import-collision failure was reproduced using the exact
  unmodified HEAD controller in a temporary fixture. Production binding correctly
  rejects the foreign repair. It is not a new scheduler regression; no historical
  tests or validators were modified to turn it green.

Logs are `convergence_work/HARNESS_*_TEST.log`. The parent's final validation must
record any later materialization/targeted rerun separately. No live acquisition,
scientific refit, native solver/ODE, push, or task-status promotion was performed
by this worker.

## Skill context used

`WORK_PACKET.md` actual PhysMath 1.3.0 C2/C4/C5/C6 and integrated policy excerpts;
repo AGENTS, local DAG/harness skills, current native routing/controller docs.
One production verification pass; no recursive children or review-of-review.
