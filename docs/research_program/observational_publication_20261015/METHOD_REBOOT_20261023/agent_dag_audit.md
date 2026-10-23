# Independent DAG/controller audit — 2026-10-23

Owner: common/harness. Status: DIAGNOSTIC_ONLY; proposed changes are PROPOSED, not implemented. Transfer source: none. Scope: read-only adversarial audit of research scheduling and claim/admission separation. Pinned source: `cosmosapjw-quantum/htt_base@cd2bf729f12a4229f0bb423850372a511dcff78b` (PR561). No native solver, ODE, launch, repository mutation, controller mutation, scientific promotion, or budget reset was performed. Only this report was written. Local historical copies were not treated as current authority.

## Judgment

The reported HOLD is a correct **admission decision under the current contracts**. It is not evidence that the authorized **research search space is exhausted**. The implemented controller can execute and protect a preauthored plan; it cannot discover or append alternative methodologies, represent sufficient alternative proof routes, or distinguish acceptance readiness from research readiness. This is a material mismatch with the broader autonomous research objective.

The strongest criticism is therefore not “relax validation until 42/42.” It is “stop requiring the completion of a particular full-source route before allowing a different, explicitly conditional research question to be investigated.” Preserve the original 17/42 and analytic-alternate 18/42 distinction, while appending a small number of new questions with different estimands, assumptions, or proof obligations. Their outcomes must not silently pass the old nodes.

There is one concrete scheduling defect independent of this scientific judgment: a confirmed prelaunch transport refusal cannot be resumed on restored transport alone through the current API. There is also an important representational limitation: every `enables_nodes` edge becomes an AND prerequisite, even when the actions were intended as alternative ways to supply sufficient evidence.

## Sources and verification

Read from the pinned GitHub ref: `AGENTS.md`; `scripts/codex_harness/research_controller.py`; `build_research_campaign.py`; their tests; `docs/harness/CONTINUOUS_RESEARCH_CONTROLLER.md`; `NATIVE_ROUTING_POLICY_V1.json`; publication `PUBLICATION_DAG.json`; `OPEN_INPUTS_20261018/CONTINUATION_TASKS.json`; `CONTINUOUS_RESEARCH_20261023/FRONTIER.json`; execution `CHECKPOINT_KO.md`, `CONTROLLER_FINAL_NEXT.json`, `REMAINING_BRANCHES.json`, and `REMAINING_BRANCHES_CLOSEOUT.json`. Read repo skills `htt-dag-orchestrator`, `htt-claim-firewall`, and `htt-claim-provenance-ledger`. No other reviewer's scientific verdict was used to form this audit.

The latest checkpoint is `docs/research_program/observational_publication_20261015/CONTINUOUS_RESEARCH_20261023/execution/CHECKPOINT_KO.md`. Its lines 131–150 explicitly report the 48-task HOLD, absence of running/planned work, and reopening on qualified new input or a concrete review finding. It also explicitly states that this is not a universal data-absence/no-go claim. That caution is correct; the remaining problem is operational rather than a hidden claim of 42/42.

I executed the fetched Python source in isolated in-memory modules with a stub router and receipt function. These are scheduler unit fixtures, not actual launch receipts or empirical science. No production state was loaded or altered. The outputs below were observed, not inferred.

## Findings

### 1. High: a fixed admission DAG is being used as the entire research frontier

`research_controller.py:118–131` declares a task ready only if it is in state `ready` and **every** `depends_on` task is completed. An empty set yields `HOLD_UNRESOLVED_BRANCHES`. `next_packet:151–193` only searches that set. There is no operation to append a new authorized question to the existing durable campaign; CLI construction at lines 382 onward exposes init/next/ack/record/launch-failed/resume/summary, not append or replan. `build_research_campaign.py:119–120` refuses to overwrite a frozen campaign or existing state, which is sensible preservation but leaves no supported extension path.

`resume:247–267` can reopen an existing held task; it cannot introduce a different estimand or conditional proof obligation. The final checkpoint's instruction to wait for qualified input or a review finding therefore excludes potentially useful new methodology evidence, even though `AGENTS.md:280–285` already authorizes scientific repairs and continuing independent work. **This is a search-closure error if HOLD is used to end all research, not an error in the original admission HOLD.**

A source gap for a physical likelihood does not imply that no invariant, robust bound, structural nonidentifiability theorem, conditional experiment, or falsifiable nuisance model can be researched on existing observations. Those alternatives may fail; the controller currently has no representation of their availability until a new campaign is built, which risks resetting history.

### 2. High representational limitation: “enables” means “must all complete”

`build_research_campaign.py:33–43` collects every enabling action for a node; line 57 concatenates the entire collection onto original dependencies. The scheduler then applies conjunction. No OR clause or claim-specific sufficient-obligation set exists.

Minimal executed fixture: original node N has no original prerequisites; R1 and R2 are two separately authored alternatives that both list `enables_nodes:["N"]`. R1 is completed and R2 is held. Result:

```text
OR_ALTERNATIVES_AS_AND: {"N_depends": ["R1", "R2"], "N_state": "ready", "ready": [], "status": "HOLD_UNRESOLVED_BRANCHES"}
```

This does **not** establish that an actual original node should be marked complete. It establishes that the representation cannot express alternatives. Current `CHECKPOINT_KO.md:136` confirms the operational consequence for B02: its state string is ready but an unfinished enabling action prevents dispatch. Such an edge is justified if the action is a necessary proof obligation; it is overstrong if it is only one attempted route. Adding more audits/actions through the same `enables_nodes` convention can make a plan strictly harder to execute even when they provide only optional evidence.

### 3. Medium, reproduced defect: restored transport is not an admissible resumption reason

`launch_failed:228–244` marks a genuine prelaunch refusal held and preserves `launch_performed:false`. `resume:257–259` subsequently requires a changed scientific input identity or an unused approved repair. It has no transport-restoration case, despite `next_packet` describing availability as live. With no unused approved repair:

```text
TRANSPORT_RESUME: new input or unused approved repair required; do not replay exhausted issue
TRANSPORT_NEXT: HOLD_UNRESOLVED_BRANCHES
```

The existing test at `test_research_controller.py:251–264` checks that refusal preserves the unused ultra budget and lets another branch run; it does not check restoration of the refused branch. The minimal fix is a separate prelaunch-resume transition requiring evidence that the particular refused transport is now available. Keep the scientific input and phase unchanged, retain the refused packet, issue a fresh attempt packet, and preserve all consumed ultra IDs. Do not use this to replay an acknowledged launch, unknown outcome, R9, or the explicitly exhausted Desktop Commander route. This defect is **not demonstrated as the cause of today's eight scientific external-input cuts**, because their held reasons are scientific input gaps.

### 4. Medium: byte identity is simultaneously too strict and too weak as novelty evidence

`resume:257–265` treats a different `input_identity` string as sufficient new-input evidence and clears the failure trigger accumulator. It does not inspect semantic difference; `_receipt:222–225` checks file existence and hashes bytes. Conversely, a new mathematical method using the same scientific input has no explicit resumption category unless an unused whitelisted repair is available.

Two additional executed unit fixtures:

```text
IDENTITY_ONLY_RESUME: ready research
SAME_UNUSED_REPAIR_RESUME: ready research
```

The first changed only an identity label, with an unchanged receipt. The second kept the input and current repair ID identical; the repair had not consumed ultra, so it was accepted. Thus the implementation does not enforce its docstring's “different preapproved repair” (`resume:249`) or the campaign's semantic requirement for a genuinely new bounded issue. Ultra consumption remains preserved; these fixtures do not reset it.

`build_research_campaign.py:61` binds an original task identity to the whole source-document identity plus node/plan content. This is appropriate as an immutable assignment seal. It is not a reliable scientific novelty test: adding explanatory evidence references elsewhere in a source can change the seal without changing the estimand, data or method.

`AGENTS.md:224,228–233` already separates source identity, scientific reproducibility, and exact replay; allows release/version/DOI provenance where bytes are irrelevant; and rejects gate/hash/PR/document counts as progress. The policy does **not** require universal byte-exact upstream reconstruction. Apply it: keep packet/config/content seals exact, but record whether a proposed scientific delta is data, method, assumption, validation counterexample, or transport. A short reviewed semantic delta is sufficient; no new universal provenance bureaucracy is needed.

### 5. The positive-route parents are overstrong for several negative or partial research outputs

The following are **candidate plan defects**, not proofs of original completion. The original acceptance text and full stated objective/output must be considered together; accepting a vacuous all-unknown result would be wrong.

| Source | Existing broader gate | Research route currently obscured | Treatment |
|---|---|---|---|
| `PUBLICATION_DAG.json:418–432` S04 | S04 requires S03, which requires S02's admitted physical mapping (S03 lines 394–414) | S04 expressly permits a qualified narrower identifiable functional and a justified outer interval | Append a narrower target with its own source assumptions and finite/nonvacuous bound criterion. Do not renormalize unknown physical mass or claim S02 passed. |
| DAG `905–915`, `953–962` V04/V06 | All local/global information goes through H04; the final paper allows a physical nonidentifiability statement | A specified model-class null-space or invariance result can sometimes be established before a full physical posterior | Research the exact class and real-data consequence. Theorem validity on that class is not a universal no-go or original external V03 output. |
| DAG `1179–1193`, `1206–1216` K04/K05 | H04 and all sectors are positive prerequisites | Available-sector identified sets plus explicit unbounded/undefined sectors are already in the intended outputs | Split available-sector inference from cross-sector combination. A merely “all undefined” report does not satisfy a useful physical target; require a new identified combination or demonstrably informative impossibility boundary. |
| DAG `688–705` H02 | Reproduction of source null simulations is an explicit original acceptance | New conditional or robust statistical models on selected rows | A new model cannot be called H02 completion without the original source-null obligation. Treat it as an alternate empirical/model-criticism result and keep the source-null gate. |
| Original B02 and original external V03 | External physical atlas/history output, with no native/ODE implementation allowed | Adapters, equivalence proofs, or restricted analytic results | The missing producer output is a real boundary. Stop blind archive repetition; retain exact payload request and keep alternate results separately labeled. |

The actual S02 missing payload also binds a complete physical response to the existing 2048 IDs. That is justified for replaying that frozen pushforward. It should not become a universal demand that every future observational functional use those exact draws. A new joint source can be defined and validated under a new task identity; it cannot retroactively complete the frozen run.

### 6. The one-ultra limit is not the current scientific cause, but the repair protocol is narrower than research

Current `CONTROLLER_FINAL_NEXT.json` holds S02/H02/L03/K03 and R23-SN/CONGRUENCE/ATLAS as input gaps. `_record:322–334` handles true external holds **before** escalation eligibility at lines 336–345. Blaming today's empty ready set principally on ultra would be inaccurate.

The controller does correctly preserve one actual ultra launch per approved shared repair (`acknowledge:206–212`) and allows one concrete reviewer-directed numeric/code closeout even after ultra (`_record:348–357`). But after that shortcut, a new deterministic correction or distinct method can hit the consumed-budget hold unless new evidence/repair is represented. A model-call cap should bound escalation spend; it does not prove the mathematical search is finished. Preserve R23-COMMON-E1/R23-Q, all one-use records, R9 and UNKNOWN exactly. A new side task on the same underlying issue must inherit the consumed repair identity; its ordinary calculation or method work is not permission for another ultra. A genuinely distinct issue needs a concrete semantic difference, not a renamed ID.

## Small replacement for the operational plan

Use a typed AND/OR **proof-obligation overlay** for newly appended work. Keep the old 42 scientific contracts and 48-task execution history immutable. No new permanent claim registry is required.

- Nodes describe a source fact, method lemma, declared assumption, numerical validation, conditional result, or original admission claim.
- AND means all requirements are needed for the **same** claim and estimand. OR means each alternative is independently sufficient for that same obligation. Different estimands belong to different nodes, never to an OR that falsely treats them as equivalent.
- A conditional result requires its data, method and stated-assumption obligations. It can finish while the original physical admission claim stays held.
- Original admission remains a separate evaluated obligation. Promoting an original acceptance requires a reviewed mapping from new evidence to that exact acceptance, objective, output and relevant prerequisites. The new operational route does not rewrite historical completion.
- A research action needs enough evidence to execute a discriminating calculation. It does not need the final claim to be identified first.

Illustrative compact task fragment:

```json
{
  "id": "R24-NARROW-FUNCTIONAL",
  "kind": "numeric",
  "goal": "Evaluate one specified selected-row functional over a declared nuisance set",
  "acceptance": "Report a source-bound finite bound or a constructive witness that this route is vacuous; preserve all physical unknown sectors",
  "depends_on": [],
  "requires": {"all": ["E1", "X01", {"any": ["R24-NUISANCE-BOUND", "R24-INVARIANCE-LEMMA"]}]},
  "input_identity": "sha256:EXACT_NEW_ASSIGNMENT_MANIFEST",
  "contract_origin": "conditional_research",
  "original_targets": ["S04", "K04"],
  "assumptions": ["The exact admitted nuisance set, cohort and finite validity domain are part of this conditional estimand"],
  "novelty_delta": "New sufficient bound or invariant, not replay of the old fixed-covariance quotient"
}
```

Both OR alternatives here must independently establish the same stated nuisance-robust obligation; otherwise split the conditional result into two tasks. `original_targets` is a traceability reference, not an enabling gate or PASS.

## Minimal harness changes and regression strategy

Make one coherent patch in the existing checkout. Do not rebuild the campaign. Its immediate consumer is a named R24 calculation, not another assurance report.

1. Add `append-frontier` to the existing state machine. Validate unique fresh task IDs, acyclicity, current authorization, declared semantic delta, and known repair IDs. New tasks start ready, never completed. Append their full specs and the authorization/evidence reference to an event. Preserve the original `campaign`, `campaign_identity`, all preexisting task specs/states/packets/histories, `ultra_repairs`, R9/UNKNOWN and usage. Keep the root identity as historical origin and attach a frontier-revision digest only to appended tasks. Future packets for those tasks include that revision; outstanding historical packets are unchanged.
2. Add optional `requires` for newly appended tasks. Legacy `depends_on` keeps its current AND meaning. Validate all expression leaves and cycles; do not silently change old dependencies. The following evaluator is runnable as written and is enough for readiness; reject malformed expressions instead of defaulting to true:

```python
def references(expr):
    if isinstance(expr, str):
        return {expr}
    if not isinstance(expr, dict) or len(expr) != 1:
        raise ValueError("one all/any expression required")
    op, children = next(iter(expr.items()))
    if op not in {"all", "any"} or not isinstance(children, list):
        raise ValueError("invalid dependency expression")
    if op == "any" and not children:
        raise ValueError("empty any is not an alternative")
    return set().union(*(references(x) for x in children))

def satisfied(expr, done):
    references(expr)  # validate even branches short-circuiting would skip
    if isinstance(expr, str):
        return expr in done
    op, children = next(iter(expr.items()))
    return (all if op == "all" else any)(satisfied(x, done) for x in children)

def task_ready(spec, done):
    return satisfied(spec.get("requires", {"all": spec.get("depends_on", [])}), done)

assert task_ready({"depends_on": ["A", "B"]}, {"A"}) is False
assert task_ready({"requires": {"any": ["A", "B"]}}, {"A"}) is True
assert task_ready({"requires": {"all": ["A", {"any": ["B", "C"]}]}}, {"A", "C"}) is True
```

Replace only the dependency predicate in `summary:122–123` for new tasks. The union of expression references is used for known-ID and cycle checking, not as an AND gate. Do not put a final claim's uncertainty requirements onto an exploratory action unless they are actually needed to perform its calculation.
3. Add explicit resumption evidence kinds, consumed by the scheduling decision: `input`, `method`, `assumption`, `validation_counterexample`, `prelaunch_transport`. Keep exact input seals separate from a short semantic delta. A changed hash alone must not qualify as novelty. An assumption change must create a conditional scope/version, not pass the original claim. The existing evidence file is enough; do not add several new ledgers.
4. Fix prelaunch transport restoration separately. Require the task's current packet to be a preserved refused, unacknowledged packet; retain phase and input; do not permit replay of acknowledged/unknown launches. If its phase was escalation, re-reserve the same unused repair ID only; never clear `ultra_repairs`.
5. Run the existing controller/builder tests plus focused tests: AND compatibility; OR sufficiency; malformed/unknown/cyclic OR rejection; a held alternate does not block a completed sufficient route; appended tasks can run while old original HOLDs persist; append preserves old task/packet/budget identities; same issue shares consumed ultra; changed label alone is not new evidence; a same-data methodological theorem can open a new scoped task; transport recovery preserves phase and budgets; original scientific counts and V03 distinction do not change.

One fresh reviewer should independently inspect this patch and reproduce the small scheduler counterexamples, then review the named downstream calculation. One targeted closeout suffices for concrete findings. Do not create a new layer of reviewers, a full-repository audit, or another broad assurance campaign. Existing `AGENTS.md:232–233` expressly disallows that expansion without a reproduced failure and consuming decision.

## Bounded scientific frontier, not endless alternative generation

Select **at most two** alternatives from the following, based on the retained data and the main scientific objective. Do not run all lanes reflexively.

| Candidate | What would actually be new | Required stopping result |
|---|---|---|
| Nuisance-robust selected-row functional | Derive a finite, source-supported sensitivity envelope or exact invariant that is valid beyond the already tested fixed covariance; compare the same estimand | Useful bound with assumptions and independent numerical reference, or a constructive vacuity witness explaining the exact additional condition needed. An arbitrary finite prior is not source support. |
| Physical/observational quotient in a finite domain | Ask whether any retained contrast remains distinguishable across a declared **physically admissible** parameter/nuisance domain | Stable surviving combination, or explicit rank/confounding witness over that domain. A formal fit outside the small-velocity domain, as in K03_PM, cannot be counted as physical separation. |
| Distance-model criticism and one alternative | Use the R23-DISTANCE residual failure to specify a different correlated-error/selection model and one falsifiable comparison, without tuning the old null after seeing its p | Prespecified adequacy comparison and uncertainty/sensitivity report, or rejection of that new model. New conditional calibration is not reproduction of the unavailable H02 source nulls. |
| Split-map robust morphology | Turn the retained deterministic split-span response into a carefully stated sensitivity problem, with a justified uncertainty envelope if obtainable | An observable robustness interval or an explicit statement that an uncontrolled common component makes it vacuous. A projection of one realization is not a stochastic covariance or calibrated p-value. |

Each action must state, before execution: one target estimand; the delta from the last failed route; one mathematical or empirical discriminator; a finite resource cap; and a stopping criterion. Finish that action when it yields an independently checked informative result or when the discriminator shows the route fails. Allow one concrete correction within that bounded action. After two distinct failed methodological alternatives for the same missing obligation, replan the remaining questions and priorities; this is not a hard cap or permanent stopping rule. The current owner explicitly authorizes continuing research whenever a genuinely new, discriminating method, input, assumption, or counterexample is available. Park a route only when it has no executable new question or reaches an actual binding resource/prohibition limit, retaining its exact re-entry trigger and continuing independent work. Do not regenerate equivalent models under new names or keep searching archives without a new source hypothesis. A failed but discriminating result is research progress.

Follow-up correction: the owner declined the original audit's two-method parking heuristic as a research termination rule. The paragraph above incorporates that instruction. The four isolated pinned-source scheduler fixtures are now preserved offline in `HARNESS_FIXTURES.py`; run `python HARNESS_FIXTURES.py`. The embedded source files are verified against their Git blob identities before execution; no production state is used.

The immediately executable next action is therefore: append one source-specific conditional proof/experiment with a concrete semantic delta, consuming the retained sufficient statistics and valid-domain constraints, and execute its discriminator. Do not start with another whole-DAG status audit. Source acquisition for the genuine external atlas/history can remain dormant until a new endpoint, producer payload, or expressly authorized contact exists.

## Metrics and claim audit

Keep four separate numbers or short statements in the existing checkpoint:

1. Original acceptance: 17/42 external-output policy, 18/42 analytic-alternate policy, unchanged unless an original acceptance is explicitly reviewed.
2. New interpretable results: count accepted conditional estimates/bounds and constructive counterexamples, naming their assumptions. Count a failed model-adequacy test as information, not a PASS.
3. Decision impact: which uncertainty width, admissible parameter domain, nuisance ambiguity, or original proof obligation changed. A rank increase outside the valid domain is not progress toward a physical estimate.
4. Unresolved triggers and spend: exact payload/method evidence needed, and cumulative actual launches/one-use usage. Never use audit volume, hashes, test count, agent count, or PR count as scientific progress.

| Claim | Owner | Status | Evidence | Risk | Required treatment |
|---|---|---|---|---|---|
| Current scheduler has no ready authored task | common | VALIDATED as checkpoint/code fact | Pinned final next + source | Mistaking inventory closure for search closure | Preserve HOLD; state its fixed-plan scope |
| Transport-only restoration is rejected | common | VALIDATED in isolated fixture | Executed pinned source | New science identity demanded for non-scientific recovery | Targeted transition fix |
| Enabling alternatives are treated conjunctively | common | VALIDATED in isolated fixture | Builder + executed fixture | Optional research increases blockers | Typed alternatives for new tasks |
| New methods can pass original acceptances | htt | PROPOSED only | None yet | Silent scope promotion | Require explicit original-acceptance mapping after actual results |
| Current original scientific completion increased | htt | Not asserted | Counts unchanged | Inflated completion | Keep 17/42 versus 18/42 |

No scientific claims were upgraded. No hidden external transfer was promoted to native transfer. No manuscript/publication readiness was granted. Needed status update: this scoped audit and the next executed scientific action only; no new permanent ledger rows beyond what an actual consumer needs.
