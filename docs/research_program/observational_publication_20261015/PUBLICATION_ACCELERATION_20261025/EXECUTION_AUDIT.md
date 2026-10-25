# C2/C4 execution audit: additive publication outputs in the running HTT campaign

Date: 2026-10-25. Source revision requested: `0d5ab96bdb55398076629099664c77517ec33bb4`. Scope: inspect the selected source snapshot, map a safe additive update, and execute bounded in-memory controller checks. No production code, live controller, active assignment, Git ref, acceptance, or numerical source was changed. No nested agents or native campaign dispatch were performed.

## Decision

Use the existing `append-frontier` transition on the existing controller state. Add executable publication-output tasks with precise typed obligations; leave the 42-node scientific DAG, frozen campaign, original dependency edges, active packet identities, attempts, failure receipts, repair budgets and original acceptance statuses intact. No migration, rebase, replacement campaign, controller initialization, or running-job termination is necessary.

The controller already implements this mechanism. The smallest useful implementation is an additive authored publication portfolio plus its validated executable frontier and a current-session handoff. A small lowering/validation helper can prevent input/path mistakes if needed; a new scheduler or controller rewrite is not justified by this audit.

This fixes *dependency inheritance*, not general execution concurrency. Default `next` deliberately waits whenever any campaign task is running. An independent new task becomes dependency-ready immediately but executes after the current worker resolves or explicitly releases its acquisition slot. Preserve that active worker. The only existing concurrency exception is a tightly bound read-only review beside one running acquisition; it cannot launch new numerical/theory production in parallel. A broader multiwriter scheduler would be a separate change.

## Evidence and source authority

Read the PhysMath 1.3.0 `SKILL.md`, `POLICY_INTEGRATION.md`, `SUBAGENT_MODE.md`, and `CODING_LOOP.md` C2/C4 contracts. This child applies the parent-dispatched bounded audit and does not delegate recursively. Policies used: preserve original science, use actual source/function evidence, minimal constructive correction, typed identity, one verification pass, and a resumable exact next action.

Read `base/AGENTS.md`, controller code/documentation, router/policy, all 42 original node contracts, the continuation plan, authored six-action R23 frontier, and the physical package README/HANDOFF. `base` is a selected-file source snapshot, not evidence of the owner's active checkout or its live state. Its `.agents/skills/htt-dag-orchestrator`, `CURRENT_CODEX_RUNTIME.md`, live controller file, historical raw receipts, and controller test suite are not materialized here. The host must use the existing checkout's actual current instruction/skill files when executing the handoff; this missing snapshot content does not prevent the source audit.

Source SHA-256 identities:

| File under `base` | SHA-256 |
| --- | --- |
| `scripts/codex_harness/research_controller.py` | `e5bb42598026549883b66275ec79399020e7f3007eae5ee760f91469c062d3ce` |
| `scripts/codex_harness/native_routing.py` | `e42a833aab97c74e55310e91408558dfdbd05457e035438f3ec32a6917ddf68a` |
| `docs/harness/NATIVE_ROUTING_POLICY_V1.json` | `bd666489f65dcab2f5b61242ad40dc3b409d040fdfa966dbd666dbf65cee3330` |
| `docs/research_program/observational_publication_20261015/PUBLICATION_DAG.json` | `20765d81eabd79f80d11605cb637dd2eb1800a50c2eb66dfe319183bd31e579f` |
| `docs/research_program/observational_publication_20261015/OPEN_INPUTS_20261018/CONTINUATION_TASKS.json` | `107ff6c8f102735d057985eabaeab5ad21c9b64e01ad7384df2f366636b3287e` |

The physical package explicitly preserves original HOLD/UNKNOWN and external-output acceptance, and prohibits controller reinitialization. Its current scientific targets remain dimensional directional expansion/shear, rotation, acceleration and frame-relative motion; no native Boltzmann solver or ODE integration.

## Actual execution surfaces

| Function / CLI | Implemented behavior | Safe role here |
| --- | --- | --- |
| `initialize(campaign, authorization)` / `init` | Creates fresh campaign state; CLI refuses an existing state file. | Do not use for uptake. |
| `bind_original_contracts(campaign, dag, plan)` | Checks identical original inventories, acceptance and dependency lists; freezes original science. | Test preservation against the existing bound contract; do not replace it. |
| `append_frontier(state, frontier, authorization)` / `append-frontier --frontier FILE --authorization TEXT` | Validates all new rows and combined dependency graph before mutating; adds only tasks, frontier record, append event. | Supported additive transition on the current state, including when an old task is running. |
| `_obligation_refs`, `_obligation_met` | Typed `all`/`any`; `completed` or named `qualified` product of a completed task. | Avoid importing full-law gates into unrelated conditional outputs. |
| `summary(state)` | Computes dependency-ready tasks separately from outstanding work; original science admission remains `UNCHANGED_NOT_GRANTED_BY_CONTROLLER`. | Report new output progress separately from original42 progress. |
| `route_for(task)`, `native_routing.resolve_route(...)` | Selects phase-appropriate policy route using exact current capabilities. | Reuse policy; do not silently remap a production or review route. |
| `next_packet` / `next` | One outstanding production packet; stable replay until ack; skips unavailable routes; fair ordering by `(last_turn, task_id)`. | Existing host continues the loop; newly appended rows start with `last_turn=-1`, not authored-order priority. |
| `acknowledge` / `ack` | Binds a real accepted native launch ID, then marks running; reviewer must be fresh. | Preserve actual active agent/thread; never relaunch an unknown result. |
| `record` / `record --result FILE` | Checks bound task/input/agent/packet and receipt. Success of execution schedules review; successful independent review completes task and qualifies declared subset of products. | New output is usable at its own actual evidence tier. |
| `resume` | Reopens a held task only on actual typed scientific/confirmed prelaunch transport change; preserves history and escalation use. | Use only if the *same logical existing action* is being continued. New IDs cannot evade attempts. |
| `checkpoint-acquisition`, `prepare-acquisition-resume`, `ack-acquisition-resume` | Cooperative, evidence-bound acquisition release/resume; CLI never stops processes. | Optional only when an actual acquisition naturally provides the required checkpoint. Never fake a release to prioritize publication. |
| `save` | fsynced temporary file and atomic replacement. | Host serializes state mutations; atomic replace is not concurrent-writer locking. |

There is no `migrate`, `rebase`, `reset`, task-edge replacement or running-packet rebinding operation. `build_research_campaign.py` is documented for fresh campaign construction; it is absent from this selected snapshot and should not be used to recreate a campaign for uptake. Its `actions` schema is distinct from the append command's `frontier_id` + `tasks` schema. Existing `FRONTIER.json` has six `actions`, not an append-ready `tasks` document.

## Required append contract and bounded validation

Each new row needs `id`, supported `kind`, `goal`, frozen `acceptance`, `input_identity`, `input_sources`, disjoint `owned_paths`, `contract_origin: new_conditional_research`, `promotes_original_acceptance: false`, typed `requires`, and substantive `semantic_delta` with object-valued `before`/`after`, discriminator and scope. Use no `depends_on` or `enables_nodes` on appended rows. Do not initialize a row completed. A new frontier cannot mint an ultra allowance.

Use `requires: {"all": []}` for a self-contained computation from already available frozen physical evidence. Use `{"task_id": "EXACT-ID", "evidence": "qualified", "product": "EXACT-PRODUCT"}` when actual scientific adequacy matters. `completed` alone means that task's acceptance was reviewed, which can include a precise input-gap or counterexample report; it does not mean that a physical-response/error-budget product exists. Empty `any` is invalid. `any` represents genuinely sufficient alternative routes to the same output, not a way to substitute a different estimand. Every reference must exist in old state or the same append batch, even on an alternative branch.

The lowered input manifest should bind the actual source head plus per-source path/version/hash, retained producer identity, scientific units/frame/basis, chosen estimator/response, fixed configuration and validity domain. Hash the frozen manifest for `input_identity`; a hash without retrievable source content is insufficient evidence. A manifest is justified here because the executable frontier is a downstream consumer. Output objects should carry result/surviving set, assumptions, executed checks, source identity and smallest missing input. Preserve original acceptance in a separate mapping; an output contract must not imply original-node promotion.

Important implementation boundary: append validates required nonempty path/source fields but does **not** enforce their actual filesystem existence, hashes, path disjointness or scientific adequacy. It also does not prove new semantic before/after fields are scientifically meaningful. The lowering/preflight layer and host must check these concrete matters. Resolve symlinks/relative paths against the actual checkout; reject new ownership overlapping existing active/candidate/input paths. Do not change ownership of an existing running packet to fit this check.

Duplicate action detection compares the semantic projection and task kind, deliberately ignoring IDs, owned paths, locators and administrative seals. A proposed publication wrapper with a renamed ID but the same method action is not a new research task. Reuse the existing action and its evidence or resume it on genuine new meaning. Give a new publication assembly action a concrete different transformation/acceptance, such as producing a specified conditional-result table and its independently reviewed unit/claim mapping.

## Scientific dependency correction

The frozen graph has 42 nodes and 18 `completed_scoped` source reuses. Strong original chains include `H02 -> H04 -> H05 -> H06`, `H04 -> V04 -> V05 -> V06`, `S02 -> S03 -> S04 -> S05 -> S06`, and `B02 -> B03 -> B04 -> B05`. For example H06 requires an actual full law, competing models, independent data validation or informative null; B02 requires actual Einstein/Boltzmann physics, recombination, constraints, IC and mode tests. These scientific obligations remain valid and unresolved where evidence is absent.

Their *inheritance by every new result* is unnecessary. A source-supported conditional tensor/error frontier, a full-covariance structured-mean rejection set, or a CMB spectral-response surviving set can have its own finite acceptance and publication output without asserting H06/B02. The physical package already supplies concrete finite targets:

| New bounded output | Immediate source/equation obligation | Dependencies that should remain local to the stronger original claim |
| --- | --- | --- |
| CF4 apparent tensor and response-error frontier | Sealed dimensionless five-vector, matrix/basis, exact calibration; distinguish measured jointly qualified radius from sensitivity value. | Full CF4 parent targeting/quality law unless used for that output's claim. |
| H03 structured-mean compatibility | Saved full 12D covariance and means; keep cross-window blocks; compare physical model against the 23.3967/6 df combined residual. | Full global-tilt identification or unrestricted full-law posterior. |
| CMB response/surviving-set result | Full signed 24-coordinate blocks, released bandpass/common spatial response, exact first/second-order nuisance conditions. | Native polarized atlas/family identification, or unsupported independent frequency from SMICA. |
| Transverse response qualification | Actual source-centroid/frame/moving-lens calibration and response product; exact gap if absent. | A measured vorticity/global tilt statement until the response qualifies it. |
| LRS Bianchi V conditional geometry | Momentum plus normal constraints, oriented axis, expanding H, normalization and speed/rapidity conventions. | An inferred CMB shear ceiling without its actual history response. |

Give each output its own publication gate and product names. A missing transverse calibration must not hold a CF4 conditional result. A CMB non-identifiability/counterexample object can qualify a scoped response result, while it cannot qualify `physical_shear_confidence` or `family_identification`. Do not create a single final manuscript task requiring every speculative new branch: that reconstructs the serial whole-law bottleneck. Append a paper-build task only after its exact chosen source products are frozen, or define independent paper scopes with exact sufficient typed routes. Publication assembly still needs the claim firewall, provenance and actual manuscript/figure build checks; scientific task completion alone is not submission authorization.

## Current-session handoff: no reset or job interruption

1. In the existing active host, identify the canonical checkout and actual controller path from its resume anchor. Read its current summary and retain one compact pre-append checkpoint/identity. Compare source revision with the pinned head and relevant file hashes; reconcile a later legitimate version instead of overwriting it. Do not probe the exhausted Desktop Commander transport.
2. Retain outstanding packet/agent mapping, task attempts/history, authors/contributors, escalation reservations/use, acquisition lifecycle and original scientific contract. Do not edit an issued assignment prompt. Stage additive source/manifest/frontier files with disjoint ownership in the current checkout; no new clone/worktree is needed.
3. Preflight a **copy in memory**, using the actual existing state's task IDs and candidate/owned paths. Verify input identities, graph references/cycles, new semantics and exact42 preservation. The preflight is an audit, not native launch or scientific admission. If a live outcome arrives, the host records that outcome first or appends first in a serialized order, then reloads current state; never write an old state copy over it.
4. The current host performs exactly one serialized additive transition using the existing controller:

   ```sh
   python scripts/codex_harness/research_controller.py --state "$HTT_CURRENT_STATE" append-frontier \
     --frontier "$HTT_PUBLICATION_FRONTIER" --authorization 'Current owner publication-output DAG alongside unchanged original physical goals'
   ```

   The two shell variables are explicit bindings the active host must supply from its real current resume anchor and reviewed frontier, not paths inferred by this audit. The command changes durable state; this audit did not run it.
5. Check canonical-content preservation of the entire pre-existing state projection: campaign and identity, every existing task object, every old packet, old event prefix, turn, budgets, lifecycle and discovery fields. The allowed change is new task rows, one `frontiers` entry and one append event. Record the new frontier identity and owner authorization. Snapshot full original42 acceptance/dependency tuples before/after; they must match exactly.
6. If the old task is running, let it continue with its original packet and agent. Its identity-bound outcome remains recordable. Default `next` reports waiting while that outcome is outstanding. Do not call `launch-failed`, `resume`, or reset state merely to make a new publication task runnable.
7. Continue the existing actual `next -> native call -> ack -> outcome -> record -> next` host loop with current supported profile pairs and real raw receipts. The new `next` packet binds `frontier_identity` and `task_spec_identity`; old packet ID construction remains unchanged. On a branch hold, progress other ready outputs. Use only actual independent review to qualify products. Record exact missing inputs for the still-unresolved original scientific targets.

The repository policy's `default_parallelism: 3` is an allowed routing guard, not a claim that `next_packet` dispatches three workers. Likewise this handoff does not establish installation or live activation on the owner's computer. This session lacks the actual local active state/host observation; those steps remain a concrete host uptake obligation, not a scientific blocker.

## Executed bounded verification

Executed one `PYTHONDONTWRITEBYTECODE=1 python` heredoc against the actual `base/scripts/codex_harness/research_controller.py` and policy, importing no modified controller code. Exit code **0**. All fixture state stayed in memory; no native dispatch, live state write, scientific computation or qualification was simulated as real evidence.

Passed cases:

- Append beside a synthetic acknowledged running old packet leaves all existing task/campaign/packet/history/turn/ultra fields unchanged; new independent rows are dependency-ready while ordinary `next` reports `AWAITING_NATIVE_OUTCOME`.
- Duplicate frontier ID, existing task ID, unknown typed reference, combined cycle and renamed identical semantic action each reject without mutating input state.
- A completed gap-only task satisfies `completed` but cannot satisfy a named qualified product; a sufficient-route `any` succeeds only when its actual product is present; empty `any` rejects.
- The real 42-node DAG/continuation-plan pair binds; a changed original acceptance rejects.
- Once the synthetic prior task is held, a new packet includes exact frontier/spec digests; the old packet object remains unchanged; repeated `next` returns the same planned packet.

The full repository controller suite is **NOT_RUN** because its test files are not present in this selected snapshot. On implementation, use the existing repository's `python -m unittest discover -s scripts/codex_harness -p 'test_research_controller*.py' -v` when controller behavior changes. For data-only frontier/lowering updates, run the focused cases above plus actual manifest/path/ownership checks; do not repeat historical numerical campaigns without a changed scientific input.

Additional implementation regression targets: rejection of input hash mismatch and active-path overlap by the proposed preflight; semantic equivalence to already-existing actions; preservation when an old running outcome is recorded after append; no old task acquiring a new enabling edge; physical strong-product consumers remain blocked after a completed scoped gap result; one independent output's hold does not change another's typed readiness; serialization protects against stale whole-file replacement. These are requirements for the additive deliverable, not claims of executed live uptake.

## Constructive findings and remaining obligation

1. **Dependency issue, FIX_SOON:** reusing whole-law original task dependencies for every conditional paper output needlessly suppresses valid bounded outputs. Correct by additive tasks with their own scientific acceptance and exact typed product requirements. Keep every original42 dependency and acceptance unchanged.
2. **No API gap for additive uptake:** append functionality and old/new packet identity separation already exist and passed focused checks. A reset/migration layer would add risk without solving an observed defect.
3. **Concrete preflight gap, FIX_SOON for new artifacts:** current append does not prove path disjointness or source identity. Add/check those at frontier lowering and host uptake before any task writes.
4. **Runtime limitation, explicit:** an indefinitely unknown active worker still occupies the current production slot. Publication DAG independence does not override this identity/ownership rule. Preserve and reconcile the real native outcome; broader production concurrency is outside this minimal change.

Next action: author the smallest scientifically distinct publication-output frontier and source manifest against the actual current task inventory, then let the already-running host append it once and continue the same loop. Completion of this audit is C2/C4 design evidence only.
