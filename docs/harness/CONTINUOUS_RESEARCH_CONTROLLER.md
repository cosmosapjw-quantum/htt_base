# Continuous research controller

`scripts/codex_harness/research_controller.py` adds a durable state machine around
the existing `native_routing.resolve_route`. It does not replace the native router,
restore CUH-G, run a daemon, execute shell commands, publish, or dispatch agents.
The active host repeatedly consumes its native launch packets, calls
`collaboration.spawn_agent`, acknowledges the actual returned agent ID, records
the outcome, and asks for the next action. The host must continue this loop until
all authorized acceptances have independent review or every remaining branch has
an exact unresolved input, prohibition, environment, permission, or transport hold.

## Concrete failure before this patch

Against the selected 2026-10-23 inputs, calling
`htt_open_input_packet.packet(dag, plan)` without a task/node produced:

```json
{"scientific_completed":18,"scientific_total":42,"scientific_ready":[],"available_frontier_actions":[]}
```

Calling the existing resolver with a supported escalation profile produced:

```json
{"route":"blocker_escalation","requested":{"model":"gpt-6-astra","effort":"ultra"},"transport_selected":{"model":"gpt-6-astra","effort":"ultra"},"launch_performed":false}
```

Both outputs are correct for inventory/planning. Neither component records a
launch, executes a scientific repair, waits for review, or advances a dependent
task. Treating the empty ready inventory as scientific completion or that route
as a performed escalation is the reproducible controller failure. Existing files
remain unchanged. This patch supplies the missing host protocol; tests do not
constitute actual native dispatch evidence.

## Contracts and campaign initialization

A campaign is an explicit bounded action DAG, covering work on the original
science DAG. Define `tasks` with unique `id`, `depends_on`, `goal`, unchanged
`acceptance`, `input_identity`, `kind` (`theory`, `numeric`, `code`, `input`),
and declared `owned_paths`. `input_identity` should be the hash of a frozen input
manifest containing exact source identities. An optional `implementation_route`
must name a route in the existing policy. `external_missing` does not automatically
hold a task: a public input can still have an acquisition/research action.

Example campaign:

```json
{
  "campaign_id":"R23-scientific-repair",
  "approved_scientific_repairs":["R23-GLS"],
  "tasks":[
    {"id":"contrast","depends_on":[],"kind":"numeric",
     "goal":"Compute the source-bound GLS contrast",
     "acceptance":"Frozen source conventions; finite reference and independent review",
     "input_identity":"sha256:ACTUAL_INPUT_MANIFEST_DIGEST",
     "approved_repair_id":"R23-GLS","owned_paths":["scoped/contrast.json"]},
    {"id":"consume","depends_on":["contrast"],"kind":"code",
     "goal":"Consume the reviewed contrast without scientific promotion",
     "acceptance":"Reference parity and unchanged conditional labels",
     "input_identity":"sha256:ACTUAL_INPUT_MANIFEST_DIGEST",
     "owned_paths":["scoped/summary.json"]}
  ]
}
```

Initialize once with the current user's campaign authorization. This records
authorization for the named scientific repairs; it does not require another owner
confirmation when an eligible blocker is encountered. Do not manufacture an
approval or use historical authorization for a different campaign. Existing
completed tasks may use `initial_state:"completed"` only with `reuse_evidence`.
Completion counts alone are rejected as reuse evidence.

```sh
python scripts/codex_harness/research_controller.py --state CONTROLLER_STATE.json init \
  --campaign CAMPAIGN.json --authorization 'Current owner instruction, exact scope' \
  --dag docs/research_program/observational_publication_20261015/PUBLICATION_DAG.json \
  --plan docs/research_program/observational_publication_20261015/OPEN_INPUTS_20261018/CONTINUATION_TASKS.json
```

When binding original science, supply both `--dag` and `--plan`. Their node
inventories, acceptances and dependencies must agree; cycles and unknown
dependencies are rejected. The full original DAG is frozen in campaign state.
Task completion does not modify its statuses or grant paper/scientific admission.
Omitting these options is useful for isolated harness tests, not evidence of
admission against the full scientific DAG.

## Smallest native host integration

1. Run `next` with the current transport's exact model/effort capability pairs.
   These are capabilities, not model observations. Do not populate this list from
   wishful policy defaults or an unrelated cached CLI catalog.
2. If it returns `spawn_args`, call the real native
   `collaboration.spawn_agent` with exactly those arguments. Reconcile a launch
   interrupted before acknowledgement against the native host's returned ID;
   never blindly replay it. A planned packet is returned unchanged until ack.
3. Run `ack` with `packet_id` and the actual returned native agent ID. Already
   launched agents can be acknowledged if their actual assignment matches that
   packet, with their preexisting receipt retained. Ack is an import of actual
   launch evidence, not a launch and not a retroactive change to the assignment.
   Requested/selected profiles and observed runtime stay separate. Leave observed
   identity `UNKNOWN` without independent runtime evidence.
4. Wait on the actual native worker. Save its raw outcome receipt and a result
   JSON, run `record`, then immediately call `next`. This schedules the exact
   research, escalation, bounded repair, independent review, or dependent action.
5. If the worker is running, continue waiting; `AWAITING_NATIVE_OUTCOME` is not
   success. On transport hold, preserve the pending opportunity and continue any
   other supported ready task. On exact branch hold, continue other ready work.

```sh
python scripts/codex_harness/research_controller.py --state CONTROLLER_STATE.json next \
  --available-profile gpt-6-sol/high --available-profile gpt-6.1-sol/medium \
  --available-profile gpt-6-astra/xhigh --available-profile gpt-6-astra/ultra
# Host actually invokes collaboration.spawn_agent(**packet['spawn_args']).
python scripts/codex_harness/research_controller.py --state CONTROLLER_STATE.json ack \
  --packet-id ACTUAL_PACKET_ID --agent-id ACTUAL_NATIVE_AGENT_ID
python scripts/codex_harness/research_controller.py --state CONTROLLER_STATE.json record \
  --result ACTUAL_WORKER_RESULT.json
python scripts/codex_harness/research_controller.py --state CONTROLLER_STATE.json summary
```

In the selected-input patch fixture only, set `PYTHONPATH` to
`inputs/scripts/codex_harness` and pass global `--policy
inputs/docs/harness/NATIVE_ROUTING_POLICY_V1.json` before the subcommand. In the
existing checkout the normal sibling router import/default policy path applies.

A successful implementation/acquisition result has this shape:

```json
{"packet_id":"EXACT_PACKET_ID","task_id":"contrast",
 "agent_id":"ACTUAL_NATIVE_AGENT_ID","input_identity":"EXACT_FROZEN_IDENTITY",
 "raw_receipt":"/absolute/path/to/actual-worker-receipt.json","outcome":"success",
 "candidate_identity":"sha256:ACTUAL_CANDIDATE_MANIFEST",
 "validation_evidence":["actual command and finite reference result"]}
```

It schedules review, not completion. A successful review additionally requires
`acceptance_met:true`, validation evidence, and the exact candidate identity.
The reviewer must be a fresh actual agent, distinct from every implementation,
research and escalation contributor. Research and escalation successes instead require a concrete
`repair_plan`; they schedule repair on the appropriate implementation route.
Astra research, review and escalation remain read-only, including the prompt.
The native host must enforce these assignment bounds in the actual environment.
Task specs may declare `contributors:["actual-parent-id","actual-prior-advisor-id"]`
for contributors predating controller initialization. These identities seed the
recorded contributor list and cannot acknowledge a later review packet for that
task. Duplicate declared IDs are deduplicated; invalid identities are rejected.

An unsuccessful result uses `outcome:"blocker"` and a precise issue:

```json
{"class":"numeric","question":"Which source covariance convention preserves this Schur contrast?",
 "exact_missing_or_defect":"Exact failing source row/operator and numerical residual",
 "input_identity":"EXACT_FROZEN_IDENTITY","substantive":true,
 "high_consequence":true,"risk":"Concrete impact on physical interpretation"}
```

The issue is the `issue` field in the same identity-bound result envelope. Supported
classes are theory, numeric, code, input, environment and permission. A genuine
external-only input sets `true_external:true`, must have class `input`, and must
include `external_payload:{"required":["exact payload"],"source_or_owner":"source",
"exhaustion_receipt":"/actual/source-intake-receipt"}`. The receipt must exist;
a scientific failure cannot be reclassified by an arbitrary external boolean.
A forbidden operation sets `prohibited:true`, must have class `permission`, and
must supply `prohibition_basis` equal to `no_native_solver_or_ode`,
`owner_explicit_prohibition`, or `auth_wall_no_bypass`. Both are held with the
exact issue preserved. Environment or
permission failures (including the remote desktop monthly quota) never imply
model-quality failures or Astra escalation.

## Escalation and continuation invariants

The existing policy controls exact model selection and allowed fallbacks. The
controller never invents a fallback. A researchable scientific blocker goes to
`blocker_escalation` only with an approved repair ID and either two distinct
preserved same-class substantive raw receipts or a documented genuinely high
consequence risk. Missing input alone, timeout, and unobserved runtime are not
escalation triggers. Non-escalated researchable issues go to `review_or_research`.
Research that cannot produce a bounded repair leaves a precise unresolved hold.

The one-ultra opportunity is reserved per approved repair across the campaign,
including tasks sharing that repair identity, but its actual launch allowance is
consumed only by acknowledgement of a real native agent ID. Missing model support
does not consume that allowance. A genuine pre-launch refusal can be checkpointed
using `launch-failed --packet-id ... --evidence ACTUAL_REFUSAL_RECEIPT --class
environment --reason 'exact provider quota/refusal'`; this holds that branch,
releases the reservation, and continues independent ready work without fabricating
a native launch. After escalation, a bounded repair
and fresh review are still required. A failed repair/review cannot silently spend
the same allowance again. Reopening a held task requires `resume --task-id ...
--evidence ACTUAL_RECEIPT --input-identity ...` with a genuinely new input identity
or an unused `--approved-repair-id` already covered by campaign authorization.
All original outcomes remain in history. New-input resumption clears only the
failure trigger accumulator; prior receipts and consumed escalation IDs persist.

`next` chooses the least recently scheduled dependency-ready task, skipping
unavailable routes, so a repeatedly repaired branch cannot starve untouched
independent work. It permits one outstanding native opportunity at a time: this
is deliberately a conservative writer policy, not a throughput scheduler.
Cycles and unknown dependencies are rejected before execution. Empty ready
sets, planned/running work, external holds, and a particular completed count are
never reported as successful termination. `CAMPAIGN_ACCEPTANCES_REVIEWED` means
all explicitly authorized campaign tasks passed review or have evidence-bound
reuse; it is not a claim that the 42 original scientific acceptances passed.

State uses atomic fsynced file replacement after planning, acknowledgement,
resumption and every recorded outcome. Each outcome also gets a content-addressed
result JSON next to the state in `<state-name>.results/`; raw receipt path/hash
and full outcome history remain in the checkpoint. Retain the referenced raw
receipts. Commands assume one host writer; do not run concurrent mutations on the
same state file. Packet/task/input/agent identities and review candidate identity
must match. Unacknowledged or stale outcomes cannot advance dependencies.
No-native-solver/no-ODE and frozen scientific acceptance remain mandatory at every
phase. This protocol does not grant release, merge or submission permission.

To keep repeated worker handoffs bounded, the prompt includes only the last two
`history_refs` (phase, packet ID, raw receipt path/hash, outcome and candidate
identity), plus `history_total` and the exact current issue/repair plan. It never
re-embeds the previous full result payloads. Complete outcomes remain in durable
state and result files; workers can inspect referenced receipts when needed.

A numeric/code blocker returned by an independent reviewer may include a
nonempty top-level string `repair_plan` in its result envelope. An eligible unused
ultra opportunity retains first precedence. Otherwise this routes one bounded
targeted closeout directly to implementation `repair`, preserving the exact
reviewer outcome and plan. It does not require redundant research when the
reviewer already supplies a concrete correction, and it does not approve the
repair's scientific result. A missing/blank plan retains the research route.
Only one reviewer-directed shortcut is allowed per task; another failed closeout
returns to normal research/escalation rather than an endless sequence of targeted
review repairs. The replacement must have a new candidate identity and then pass
a fresh independent review. Both successful and failed review outcomes must bind
the current exact candidate; a stale candidate cannot trigger a repair or pass
review. The controller records the source candidate, issue identity, packet and
concrete plan in `targeted_repairs` for the bounded closeout. Consuming the one
ultra launch does not automatically cap an already-derived deterministic fix:
a fresh explicit reviewer counterexample with a concrete numeric/code repair
plan may still take the first targeted-repair shortcut, without another ultra
call. If that shortcut has already been used, the existing consumed-budget hold
applies to otherwise unresolved repair/review outcomes. Thus escalation budget
and deterministic repair continuation remain separate decisions.

## Verification

Run `python -m unittest discover -s scripts/codex_harness -p
test_research_controller.py -v`. The tests cover multi-node blocker/research/
escalation/repair/review continuation, campaign-wide escalation limits, scoped
completion versus original science, stale result/candidate rejection, native
launch acknowledgement, exact transport availability, fairness, original contract
validation, held branch continuation, current-packet replay, atomic checkpoint
round trips, and CLI outcome/result-file persistence. Native dispatch and actual
scientific validation require the separate live host demonstration.

## Whole original DAG and authored frontier integration

`scripts/codex_harness/build_research_campaign.py` binds every original node,
not just a hand-selected scoped demonstration. Its inputs are the existing
`PUBLICATION_DAG.json`, `CONTINUATION_TASKS.json`, and an authored new frontier:

```json
{"campaign_id":"R23-whole-dag",
 "approved_scientific_repairs":["R23-GLS","R23-K03"],
 "original_node_repairs":{"K03":"R23-K03"},
 "actions":[{"id":"R23-new-contrast","depends_on":[],"kind":"numeric",
   "goal":"Test the newly supported source-bound contrast hypothesis",
   "acceptance":"Frozen calculation, meaningful finite reference, fresh review",
   "input_identity":"sha256:ACTUAL_SOURCE_MANIFEST","owned_paths":["scoped/contrast.json"],
   "approved_repair_id":"R23-GLS","enables_nodes":["K03"]}]}
```

Each action must be a new authored ready task. Original IDs and previously
recorded acquisition/frontier campaign IDs cannot be reused as new action IDs.
`enables_nodes` creates explicit runtime prerequisite edges from the action to
the listed original nodes. It does not replace original scientific dependencies,
weaken acceptance, or mark those nodes accepted. A cycle between an action and
its proposed original consumer is rejected. Completed originals cannot be
reopened through enabling edges. An optional `original_node_repairs` mapping
registers exact original-node repair IDs covered by current campaign
authorization; every mapped repair must occur in `approved_scientific_repairs`.

For the selected source documents, the builder produces all **42 original task
contracts** and exactly **18 source-recorded completed-scoped reuses**, plus the
new actions. Reuse requires both an original completed-scoped node with nonempty
existing evidence and a matching completed-scoped continuation-plan entry.
Source document hashes, node/plan identities, and original evidence references
are retained. This is source-bound reuse, not a claim of fresh payload
revalidation. The original full science contract is stored separately unchanged.
Each runtime task also retains the original node, original plan entry,
`original_depends_on`, external inputs, missing inputs and mapped input routes.

Pending original nodes remain unresolved tasks. Missing public/physical inputs
select acquisition, while other research obligations select read-only scientific
work. Neither an old `external_missing` annotation nor a reviewed scoped
enabling action makes the original complete. Original submission-gate tasks
remain subject to the existing campaign's no-submission/no-merge policy.

The old inventory has zero ready science/frontier entries because it describes
the old frozen campaigns and their missing inputs. New source-supported
hypotheses must therefore be authored explicitly in the new frontier; they are
not inferred by reopening those completed campaigns.

One command creates the bound campaign, initializes durable state with the
current authorization, and emits its first native launch packet:

```sh
python scripts/codex_harness/build_research_campaign.py \
  --dag docs/research_program/observational_publication_20261015/PUBLICATION_DAG.json \
  --plan docs/research_program/observational_publication_20261015/OPEN_INPUTS_20261018/CONTINUATION_TASKS.json \
  --frontier R23_FRONTIER.json --output R23_CAMPAIGN.json \
  --state R23_CONTROLLER_STATE.json --authorization 'Current owner instruction, exact scope' \
  --next --available-profile gpt-6-sol/high --available-profile gpt-6-astra/xhigh \
  --available-profile gpt-6-astra/ultra
```

The builder refuses to overwrite an existing campaign or state. Without `--state`
it generates only the validated campaign. For live initialization use the builder
with `--state`: it gives authored new actions the first scheduling opportunity
(`last_turn=-len(actions)-1+index`, originals `-1`) before mechanically relaunching known blocked
original nodes. Thus the frontier author's action order decides initial priority,
including when IDs sort differently; the highest-value first action need not have
the lexicographically smallest ID. Subsequent ordering uses the existing fair controller rule and
exact dependencies. Merely initializing its generated campaign with the generic
controller does not install this initial authored-frontier preference.

Continue using the same state with the existing controller's `ack`, `record`,
`next`, `launch-failed`, `resume` and `summary` commands. There is no second
dispatcher. Authored action review can expose an original obligation, but that
original still needs its own unchanged acceptance and independent review. Run
`python -m unittest discover -s scripts/codex_harness -p 'test_*research*.py' -v`
to include the whole-DAG and single-command initialization regressions.
