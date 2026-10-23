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
5. While a worker runs, default `next` waits; `AWAITING_NATIVE_OUTCOME` is not
   success. The explicit `next --review-only` exception below can admit one
   disjoint read-only review beside one running acquisition. On transport hold,
   preserve the pending opportunity and continue any
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

### One read-only review during acquisition

`next --review-only` (API: `next_packet(..., review_only=True)`) may reserve one
fresh `phase=review` packet beside exactly one acknowledged running acquisition,
or when the writer slot is free. Default serial behavior remains unchanged.
It never returns an execute, repair, acquisition, research, escalation or discovery
packet. Another pending/running review, a planned acquisition, or any other
pending native work makes it wait. No eligible review means no discovery.

The review must be dependency/typed-obligation ready, have an exact current
candidate and input identity, and use a supported `review_or_research` route.
Its candidate owned paths, declared local input sources and explicit local path
records in their JSON source contracts must be known and disjoint from the
acquisition's declared owned paths. The `input_sources`, `sources` and `inputs`
declarations are followed through nested JSON contracts, with every inspected
contract sealed and rechecked at ACK. Traversal is bounded to 64 JSON contracts,
16 nested levels, 1 MiB per contract, 4 MiB total metadata and 256 declared input
paths; unresolved or over-bound scope waits. Paths resolve symlinks, with relative
nested references accepted only when their location is unambiguous. No arbitrary
prose scanning or broad repository discovery occurs.

A candidate identity label alone is insufficient. For this concurrency path its
SHA-256 must match an existing declared candidate artifact, owned file, or the
owned directory's `MANIFEST.json`/`ARTIFACT_MANIFEST.json`. A bound manifest's
`products_sha256` or `products` (with per-file `sha256`) are verified against the
actual product bytes. Declared candidate products and inspected candidate files
also receive content seals; all are checked again at ACK. Candidate verification
reads at most 64 MiB, independently of acquisition files. Missing bindings,
unmatched identities, changed nested contracts or changed candidate bytes wait
or reject ACK without state mutation. These are freshness/ownership checks,
not automatic scientific-integrity verdicts. Frozen task/spec/acceptance fields
are preserved; no acquisition data scans or numerical runs are required.

```sh
python scripts/codex_harness/research_controller.py --state STATE.json next \
  --review-only --available-profile gpt-6-astra/xhigh
```

A repeated call replays the same planned review; a running review blocks another.
Acknowledgement rechecks candidate/input/spec/source-contract identity, dependency
readiness and acquisition packet/owned-path scope, as well as existing fresh-agent
and contributor exclusions. If acquisition finishes first, the review can still
acknowledge with the writer slot free. A replacement or conflicting writer fails
closed without state mutation. The two actual outcomes may be recorded in either
order; one outcome never changes the other owner's task or packet.

The host remains the sole state-file writer and serializes all `ack`/`record`
commands. The reviewer reads only the bound candidate/inputs and returns its
outcome to the host; the host stores the raw review receipt outside candidate,
input and acquisition paths. A review failure may schedule a deterministic repair,
but that repair waits until the acquisition finishes or an explicit validated
cooperative checkpoint releases its writer slot. A refusal preserves the
acquisition. This exception does not add a scientific acceptance, reset any
allocation, or authorize a second writer or a daemon.

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
A completed same-task implementation author may be acknowledged for a planned
`repair` through `ack --followup-evidence /absolute/path/followup.json`
(API: `acknowledge(..., followup_evidence=path)`). After the host actually calls
`collaboration.followup_task`, it immediately saves dispatch evidence and acknowledges
it, before waiting for the result. The JSON contains `status:"dispatched"`,
`native_tool:"collaboration.followup_task"`, `task_id`, actual `agent_id`,
`phase:"repair"`, current `packet_id`, `input_identity`, `repair_plan_identity`
(`digest` of the recorded plan), `base_packet_id`, `base_candidate_identity`, and
exact `requested`/`transport_selected` route profiles. `host_call_receipt` and
`host_call_receipt_sha256` bind a local JSON host receipt with the same
native-tool/agent/packet/task/input fields and `dispatch_accepted:true`.

Acknowledgement makes the packet running; UNKNOWN runtime/outcome is never
replayed while waiting. The later result additionally names `base_packet_id`
and `base_candidate_identity`, a new candidate on success, and a new
`raw_receipt`. That raw JSON must bind packet/task/agent/input/base/outcome/candidate
fields to the result. A blocker may be recorded without pretending a candidate
exists. The original completed-receipt import protocol remains compatible:
omit `status`, provide the different `candidate_identity`, `raw_receipt` and
`raw_receipt_sha256` at acknowledgement; subsequent record must match them.

The base packet must be a successful recorded implementation by this author
under the current input/candidate. Every prior packet for that thread must have
a recorded implementation outcome for this task. Original and repair routes must
be implementation-compatible (`subagent_specialist`, `general_code`, or
`routine_mechanical`) with identical requested and selected model/effort profiles.
Read-only theory/research/escalation threads cannot become repair workers.
Stale identities, profiles and receipts fail closed. Old packets, contributors
and escalation accounting remain unchanged. Review still requires a fresh
independent agent; followup evidence is not runtime model observation.

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
independent work. By default it permits one outstanding native opportunity at a
time. The explicit review-only exception permits one read-only reviewer beside
one running acquisition, while retaining a single host writer of controller state.
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
The first concrete reviewer-directed closeout remains compatible with old results.
A subsequent closeout additionally needs a nonempty structured `counterexample`
with meaningful scientific fields (for example the input matrix, expected rank
and observed rank). Its counterexample/repair signature must be new. Renaming a
candidate, receipt or note does not replay an already used counterexample. Each
closeout retains its source candidate, issue, packet, counterexample signature and
plan cumulatively in `targeted_repairs`, produces a new candidate, and returns to
fresh independent review. An eligible unused ultra diagnosis still has first
precedence; deterministic fixes never replenish that allowance. Missing or
repeated counterexamples retain the normal research/hold decision. New method
search after an exact hold is available through opt-in adaptive discovery below.

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

### Append conditional research without restarting a campaign

`append-frontier` extends the current state. It retains the frozen `campaign`,
`campaign_identity`, original tasks, packets, receipts, turns and ultra accounting.
The appended specs and authorization are retained under `frontiers`, with a
content identity and append event. It neither edits original enabling edges nor
promotes original scientific acceptance. A planning `METHOD_FRONTIER.json` is not
an executable spec: lower each question to the existing theory/numeric/code/input
kind, exact input sources and identity, acceptance, and owned paths first.

```sh
python scripts/codex_harness/research_controller.py --state STATE.json append-frontier \
  --frontier lowered-frontier.json --authorization 'Owner-authorized solver-free methods campaign'
```

Example lowered document (paths and source identities must be bound before use):

```json
{
  "frontier_id": "R24-distance-methods",
  "tasks": [{
    "id": "R24-DISTANCE-MODELS",
    "kind": "numeric",
    "goal": "Compare calibration/PV and optical distance models on one cohort",
    "acceptance": "Reviewed source-specific discriminator or exact source gap; no original acceptance promotion",
    "input_identity": "bound-cohort-and-config-identity",
    "input_sources": ["bound release and selected cohort"],
    "owned_paths": ["execution/distance/"],
    "contract_origin": "new_conditional_research",
    "promotes_original_acceptance": false,
    "requires": {"all": []},
    "semantic_delta": {
      "kind": "method",
      "before": {"method": "retained summaries"},
      "after": {"method": "matched-cohort competing nuisance projections"},
      "discriminator": "Compare projected residuals under declared covariance",
      "scope": "Conditional observational distance result"
    }
  }]
}
```

Python uses `append_frontier(state, lowered_document, authorization)`. Appends are
validated atomically, including unknown references and cycles across all/any
branches. New tasks use `requires`, with `all`/`any` expression nodes and leaves
`{"task_id":"R24-X","evidence":"completed"}` or
`{"task_id":"R24-X","evidence":"qualified","product":"confidence_bundle"}`.
An empty `all` is independent; an empty `any` is invalid. Use `any` only for
sufficient routes to the same obligation. Separate estimands remain separate.
Original `depends_on` semantics remain unchanged.

Completed counterexample or input-gap research is useful but does not supply a
confidence bundle. Qualified products are opt-in: the implementation result lists
`qualified_products`, and the independent, candidate-bound successful review must
explicitly qualify a subset of those names. Review acceptance and validation
remain mandatory. The default qualified set is empty, including reused old work.
The controller checks structured declarations; scientific adequacy belongs to the
independent reviewer, not to string matching or receipt hashes.

### Resume on scientific meaning or a confirmed prelaunch restoration

`resume --evidence FILE` now reads a JSON semantic delta with `kind`, object-valued
`before` and `after`, `discriminator`, and `scope` as above. Scientific kinds are
`input`, `method`, `assumption`, and `validation_counterexample`. Same data with a
new method is allowed; identity/hash/label changes alone are rejected. Reusing the
same semantic delta for the same task is rejected. A changed repair ID must be a
different, unused repair already authorized in the frozen campaign. Appending a
frontier cannot mint or reset ultra allowances. Receipts retain exact bytes, but
semantic adequacy still requires review.

`prelaunch_transport` additionally requires `packet_id` matching the current
confirmed refused, unacknowledged packet, unchanged scientific input and repair,
and meaningful before/after transport status. It restores that phase, retains the
refused packet, and lets `next` issue a new attempt packet; acknowledgment consumes
the same previously unused escalation allowance. Acknowledged or unknown outcomes
are never automatically replayed. This does not authorize retrying an exhausted
transport. No CLI command launches a worker: the host still performs actual
spawn/followup, acknowledgment, result recording, independent review, and `next`.

Accepted resume evidence remains active on the task as `resume_evidence` and is
included in subsequent packets and worker assignments: the full semantic delta,
receipt path/hash, and canonical semantic identity travel together. Replay checks
use the typed semantic projection (`kind`, meaningful `before`/`after`,
`discriminator`, `scope`, plus the refused packet for transport); additional
labels, hashes, identities and metadata cannot make an exhausted delta new.
Raw resume events and receipts remain intact.

Future packets for appended tasks additionally bind `frontier_identity` and
`task_spec_identity` in their packet identity. This prevents different methods or
acceptances with the same task/input/attempt from sharing a packet ID. Existing
planned/running packets and all historical packet IDs are preserved exactly;
original campaign packet identity construction remains unchanged.

Scientific and transport continuations also occupy separate active fields,
`scientific_resume` and `transport_resume`, delivered together in packets and
worker prompts. A method resume followed by a confirmed prelaunch refusal and
transport restoration therefore retains the method, discriminator and scientific
receipt. `resume_evidence` remains the latest accepted transition for compatibility;
a genuinely new scientific resume clears stale active transport context.

### Adaptive discovery after the fixed frontier stalls

The current owner may enable adaptive continuation on the existing state; do not
reinitialize or replace the campaign:

```sh
python scripts/codex_harness/research_controller.py --state STATE.json enable-adaptive \
  --authorization 'Current owner solver-free adaptive methods scope'
```

When no task is ready and no native outcome is outstanding, `next` emits one
idempotent read-only discovery packet through `review_or_research` (Astra/xhigh).
The host must perform actual native dispatch, then use the same `ack` and `record`
protocol. The packet references the state file for detailed source intake; its
compact inventory is not evidence that those sources were read. An acknowledged
UNKNOWN outcome remains outstanding and is never replayed.

Discovery returns `outcome: proposal` or `no_action`, with nonempty lists
`examined_branches` (existing task IDs), `methods`, `source_refs` (existing local
files or explicit HTTP(S) references), and `exact_residuals`, plus ordinary
packet/task/input/agent identities and `raw_receipt`. Proposal adds `frontier`
using the executable append-frontier schema above. Validation is atomic; no
proposal qualifies products, passes science or mints an escalation allowance.
Proposed numerical/code analysis must actually execute via the existing lower
tier routes and receive independent candidate review before its own acceptance.
A URL is a source locator, not proof of retrieval or scientific adequacy.

Each packet freezes `eligible_branches`: every currently unresolved campaign task.
A no-action result must examine that exact set; reporting only one held branch
cannot suppress research on an unseen sibling. Partial no-action is rejected
atomically, leaving the actual acknowledged packet pending for a complete result.

No-action suppresses only the stable fingerprint of frozen task specifications,
latest actual outcomes, candidate/products, holds and explicit source/method
deltas. Turns, events and discovery itself cannot trigger another discovery. A
new actual result/candidate or registered scientific delta reopens research.
`adaptive-evidence --evidence DELTA.json` accepts the typed semantic delta schema
with `source_refs`; renaming a seal does not make a new method. The state retains
all raw discovery outcomes. `summary.planning` counts planning packets/checkpoints
separately from scientific task completion and unchanged original science.
This is a host protocol, not a daemon, installation or live activation proof.

Run `python -m unittest discover -s scripts/codex_harness -p
'test_research_controller*.py' -v` for the fixed and adaptive controller regressions.

### Authorize a genuinely distinct repair issue without rebinding old budgets

`authorize-repair --issue ISSUE_AUTH.json --authorization CURRENT_SCOPE` appends
a top-level `repair_authorizations` entry. It does not edit the frozen campaign.
The issue object supplies a new `repair_id`, `issue` (class theory/numeric/code,
question and exact_missing_or_defect), `operative_question` equal to its question,
`scope`, `issue_identity` equal to `digest(_semantic_meaning(issue))`,
`evidence_refs` (including actual local evidence), and `cumulative_budget_link`
equal to the existing `campaign_identity`. It also binds `origin_task_id`,
`origin_issue_identity` (the semantic digest of its current or recorded issue),
`claim_target` equal to that task's unchanged acceptance, and bounded typed
`semantic_delta` with the same scope. Question/defect wording alone is rejected.
A new unapproved task may first execute and expose its concrete issue; first
registration of that current issue remains possible without a registration cycle.

Use the already-needed Astra research/discovery decision, not another approval
ladder. `research_decision_receipt` references its recorded actual raw JSON with
`decision:"distinct_scoped_issue"`, actual `agent_id`, `packet_id`, and exact
origin-task/origin-issue/new-issue/claim-target/cumulative-budget bindings plus
`semantic_delta_identity` (`digest(_semantic_projection(semantic_delta))`).
The packet must have an actual acknowledged Astra research/discovery/escalation
launch, its raw outcome already recorded, and its author must not have implemented
the target. Requested and observed runtime are retained separately. The machine
checks receipt and lineage bindings; the researcher assesses source adequacy and
scientific distinctness. No text hash can establish novelty by itself.

Current owner solver-free authorization covers a bounded distinct issue. Existing
approved/consumed/reserved IDs and operative approved defects cannot be replenished
through new aliases or risk annotations. R23-COMMON-E1/R23-Q histories remain
consumed. Attribution follows the operative issue actually bound to an allowance's
reservation or acknowledged expenditure, rather than every later defect reported
by that task. Thus a covariance expenditure for I1 does not charge a distinct,
previously unspent tensor-support I2. New receipts retain the issue identity;
historical receipts use their exact escalation assignment or preceding outcome
history without rewriting old expenditure IDs. Exact I1 aliases remain blocked.
An extension can be referenced by append-frontier or a held-task resume;
for its origin task, effective repair lookup binds the new exact issue without
rewriting the frozen spec's old approved ID. Resume, append, reservation and actual
escalation acknowledgement recheck exact task/issue/claim/delta scope. An allowance
registered for A cannot fund OLD's consumed issue through an active-ID override.
Future packets seal the authorization identity and deliver its reviewed contract.

Successors are opt-in: the same actual Astra decision and authorization must both
contain identical `successor_bindings`. Each item binds `task_id`, full
`task_spec_identity` (`digest` of the exact proposed spec), `claim_target`,
`issue_identity` and `semantic_delta_identity`. Appending another task with only
the registered repair ID is rejected. An explicitly bound successor can execute
before observing a defect, but only the exact authorized operative issue can
reserve or acknowledge its shared allowance; it does not receive another budget.
 Eligibility rules still apply; only actual native ultra acknowledgement
consumes its one opportunity. Registration itself neither launches nor reserves
ultra, and result admission still needs the usual fresh independent review.

Cross-frontier duplicate detection compares typed semantic action meaning and
kind, excluding task/frontier IDs, owned paths, input locator names and packaging
bytes. The seen-signature set includes earlier rows in the same proposed batch;
a batch containing aliases is rejected before any task is added. Identical input copied to a new path, or changed wrapper metadata, cannot
reset the same question. A genuinely new source/cohort/observable must appear in
the semantic before/after (for example `source_release` or `cohort`), with its real
source evidence. Historical frontiers remain unchanged. Semantic comparison drops
exact administrative keys (names, notes, timestamps, seals), retaining scientific
fields such as `classification_labels`. Structural change permits a proposal; it
is not proof of novelty or scientific adequacy.

### Read-only startup recovery hint

After source review the host may install the ignored
`.agent-harness/runtime/ACTIVE_CONTROLLER.json` pointer with `state_path`,
`campaign_id` and exact `campaign_identity`. The state file must reside under
this checkout's `.agent-harness/runtime`. SessionStart validates that binding and
reads a bounded task-count/pending-packet/actual-agent snapshot. With no valid
pointer it reports no active observation. It never initializes, records, dispatches,
replays, installs a pointer, or updates a campaign. Reconcile pending native calls
from actual host receipts before continuation; UNKNOWN acknowledged outcomes need
reconciliation, not replay. Hook source tests are not live-session activation.
The current context pack describes this capability without claiming live HEAD,
DAG or status computation. Historical pack/index bytes remain unchanged.

### Restore a refused adaptive discovery launch

`restore-discovery --packet-id EXACT_REFUSED_PACKET --evidence DELTA.json` is a
transport-only transition. DELTA is typed `prelaunch_transport`, with the exact
`packet_id`, unchanged `fingerprint`, meaningful transport `before`/`after`,
`scope`, `discriminator`, and `restoration_receipt`. That local actual host receipt
must bind `packet_id`, `fingerprint`, `native_tool`, `transport_available:true`
and `retry_permitted:true`. The previous packet must be refused, unacknowledged,
non-exhausted and have no agent. An outstanding native opportunity or changed
science fingerprint rejects restoration atomically.

Restoration retains the original refusal and scientific objects, records the
identity-bound evidence, and makes `next` issue a distinct unlaunched packet for
the same fingerprint. It does not change scientific evidence or replay an
acknowledged UNKNOWN result. `launch-failed --retry-prohibited` preserves an
explicit no-retry refusal; an exhausted/monthly-quota reason is also retained as
prohibited. Such discovery transport remains held even if science evidence
changes. Restoration never authorizes retrying an exhausted transport. All
provider/availability assertions must come from actual host observations, not a
model catalog or a planned route.

## Explicit cooperative acquisition checkpoint

A long acquisition can hand off its writer ownership without a scientific
outcome. The controller never requests, observes, signals, stops or resumes OS
processes. The actual native acquisition worker first drains/reconciles its
identified task-owned controllers, shell continuations, children and queues,
preserves all output/attempts, and returns an actual no-further-writes handoff.
The host independently corroborates process exits, executing source versions,
retained bytes and complete accounting. Missing, dormant, queued, stale or
ambiguous ownership keeps the task running. A checkpoint is not a failure,
qualification, completed task, new allocation or scientific evidence delta.

Host-only transitions (save each before any subsequent action):

```bash
python scripts/codex_harness/research_controller.py --state "$STATE" checkpoint-acquisition \
  --task-id "$TASK" --worker-receipt "$WORKER_RECEIPT" --host-evidence "$HOST_EVIDENCE"
# Normal next may now select the already READY independent SMICA assignment.
python scripts/codex_harness/research_controller.py --state "$STATE" prepare-acquisition-resume \
  --task-id "$TASK" --checkpoint-identity "$CHECKPOINT" --resume-plan "$RESUME_PLAN"
# Only after that reservation is durable: actual same-agent followup, WAIT ONLY.
python scripts/codex_harness/research_controller.py --state "$STATE" ack-acquisition-resume \
  --task-id "$TASK" --reservation-identity "$RESERVATION" --dispatch-evidence "$ACTUAL_DISPATCH"
```

The APIs are `acquisition_binding(state, task_id, sequence)`,
`checkpoint_acquisition(state, task_id, worker_receipt, host_evidence)`,
`prepare_acquisition_resume(state, task_id, checkpoint_identity, resume_plan)`,
and `acknowledge_acquisition_resume(state, task_id, reservation_identity,
dispatch_evidence, observed="UNKNOWN")`. Binding construction is a read-only
identity aid, not a checkpoint request or evidence of quiescence. Host chooses
request and receipt paths outside frozen candidate/input scopes; no controller
request-file watcher, daemon, native call or automatic lifecycle exists.

The per-task `acquisition_lifecycle` sidecar holds monotonically numbered
checkpoints. Only task `state` becomes `checkpointed`, then `resume_pending`,
then `running`. Original phase, task/spec, packet/agent/input, authors, attempts,
scientific histories, source acceptances, caps and consumed ultra remain intact.
Each later checkpoint retains the prefix of actual attempt receipts, all
completed product identities, nondecreasing partial sizes and cumulative numeric
accounting. Later partial/completed products must retain the actual previous
prefix (streamed first-old-size hash), source release and previous source refs;
same-size replacement is rejected. Lifecycle alone leaves `adaptive_fingerprint` unchanged and cannot
make the checkpointed acquisition a discovery branch. Independent eligible
branches can still use existing adaptive research opportunities under the same
fingerprint and consumed-checkpoint rules; no global discovery freeze is added.

The worker receipt is JSON with the following exact fields:

- `binding`: the output of `acquisition_binding`. It binds campaign identity,
  task, original packet, frozen input/spec, original acknowledged packet digest,
  digest of the task excluding only `state`, original agent and positive integer
  `sequence` (first 1). It is supplied by the host, never invented by a helper.
- `handoff_complete:true`, `inventory_complete:true`, and `raw_evidence`:
  nonempty sealed actual HTTP/error/output/handoff records.
- `snapshot`: `sources`, `processes`, `queued_writers:[]`,
  `future_launchers:[]`, `attempt_receipts`, `completed_products`,
  `partial_products`, and `accounting`. Sources, processes and actual attempt
  receipts must be nonempty. Accounting is a nonempty map of all applicable
  cumulative nonnegative finite numeric counters, including actual attempts,
  elapsed time and bytes; completeness is established by worker/host evidence.

A file seal is `{path,sha256,size_bytes}` against actual local bytes. Files are
hashed in 1 MiB chunks without a scientific-input size cap or a large copy.
Validation wall time is retained in the lifecycle row. Resume/next/ACK freshness
checks can hash again; the host must account for that cost. Size or a path label
alone is not a content check. These are provenance checks, not scientific
admission. Tests use small real files and never hash external gigabyte inputs.

Each process record has positive integer `pid`, actual nonempty `start_identity`
(for example boot identity plus observed `/proc` start ticks), integer
`parent_pid`, nonempty `session_id`, exact `command` string list, absolute `cwd`,
`role` (`controller`, `launcher`, `transfer`, `child` or `continuation`),
`state:"exited"`, integer `exit_code`, and nonempty `source_refs` naming sealed
sources. Include dormant launchers, wrappers and successors, not just curl.
Native agent infrastructure is not an exited acquisition helper: the original
native thread is separately bound by the completed handoff and must stop issuing
writes. A helper cannot attest its own future exit. Its actual exit is established
before the final worker return and independent host corroboration are assembled.

Each completed/partial product extends a file seal with `product_id`,
`source_release`, and nonempty `source_refs` to sealed executing/source versions.
Product IDs are unique across both inventories. A partial additionally has
`offset == size_bytes` for the contiguous validated retained prefix. Conflicting
or unvalidated bodies remain separate raw evidence, never silently appended.
All actual attempt receipts and raw HTTP/errors survive lifecycle migration.

Host evidence is a separate JSON with the identical `binding`, `worker_receipt`
(the controller `_receipt` object `{path,sha256}` with absolute path),
`snapshot_identity:digest(snapshot)`, `inventory_complete:true`,
`quiescence_observed:true`, a nonempty independent `observer` distinct from the
worker agent, a sealed `process_observation`, and nonempty sealed `raw_evidence`.
The process observation JSON binds the same observer/binding, complete exact
process inventory, and empty queued-writer/future-launcher inventories.
Actual OS observations and source/artifact/accounting corroboration must have
been performed by the host; matching JSON assertions cannot establish omitted
processes or truthful provenance. The controller verifies content/identity
bindings and never fabricates those observations.

`checkpoint_identity` is `digest({"worker":worker_receipt,"host":host_receipt})`;
`digest` is SHA-256 of Python `json.dumps(value, sort_keys=True,
ensure_ascii=False).encode()` with its default separators. Returned checkpoint
wrappers carry that explicit identity, binding, snapshot and both receipt seals.

A resume plan binds `binding` and `checkpoint_identity`, nonempty sealed
`sources` for the newly loaded cooperative helpers, and sealed `review_receipt`.
That actual independent review JSON must have `verdict:"SCOPED_PASS"`, an
independent `reviewer`, exact `task_id`, `packet_id`, `input_identity`, and
`source_hashes` mapping absolute helper paths to their SHA-256 values. Review
may precede the actual handoff; the later plan binds it to this checkpoint.
This consumes the existing source-review decision, not another review ladder.

Prepare reserves the sole writer before any actual same-agent call. It refuses
while any other task/discovery packet is planned, running or resume-pending.
All `next` modes and ordinary ACKs wait while resumption is ambiguous. Repeated
prepare returns the existing reservation; it never authorizes replaying an
unknown or previously accepted followup. After a host interruption, reconcile
the real call instead of repeating it. No new packet, attempt or budget appears.

Dispatch evidence and its sealed `tool_receipt` JSON both bind `binding`,
`checkpoint_identity`, `reservation_identity`, original `agent_id`,
`native_tool:"collaboration.followup_task"`, `accepted:true`, and exact original
`requested` and `transport_selected` route profiles. These documents preserve
actual accepted-call evidence; a selected profile or requested call is not
acceptance. The original acquisition uses requested gpt-5.6-terra/medium,
transport-selected gpt-6.1-sol/medium under TRANSPORT_MODEL_UNAVAILABLE;
observed runtime remains UNKNOWN unless independently observed.

The actual same-agent followup must WAIT and make no file writes until the host
validates ACK, durably saves it, and sends a sealed ACK grant. The grant is the
acknowledged sidecar `resume` object: `state:"acknowledged"`, original binding,
checkpoint/reservation identities, agent/route/plan, dispatch/tool receipt seals
and observed runtime. The worker verifies those exact grant bytes and source
review bindings before any launch. `reservation_identity` hashes the reservation
before adding that identity and before ACK fields, with `state:"pending"`.
No helper may launch merely because it received a followup, flag or profile.
This handshake prevents resumed writes racing checkpoint freshness validation.

Duplicate checkpoint/ACK calls return the existing transition without another
launch or attempt; a historical checkpoint cannot re-yield a resumed writer.
Changed actual receipts, sources, product bytes or partial offsets fail before
mutation. Current worker/host receipts and snapshot must equal the stored
checkpoint on next, ordinary ACK, prepare and resume ACK. Resume ACK also compares
the current complete plan/source/review binding with the durably reserved plan;
a coherent replacement of documents cannot revive an older identity. Final outcome still uses the original packet and agent through ordinary
`record`, followed by the unchanged independent scientific review. Actual
quiescence, real SMICA execution/review, and acquisition resumption are separate
host actions required after source review; unit tests do not claim them.
