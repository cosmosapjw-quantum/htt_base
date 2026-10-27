# Execution and DAG audit — 27 October 2026

Scope: R6/C4/C9, read-only assessment and disposable controller tests. Source is the selected API-file baseline at `a55036ad09c53a9215dee3282e425d37cfb95443`, not a newly created repository checkout or the user's live runtime. The tested controller SHA-256 is `e5bb42598026549883b66275ec79399020e7f3007eae5ee760f91469c062d3ce`.

## Decision

Use the existing `append-frontier` interface for the new, source-bound observable-bridge questions. The controller already separates conditional task completion from original scientific admission and preserves earlier task histories. A new scheduler, an initialized replacement state, another generic discovery loop, or a relaxed original gate is unnecessary.

The effective stall has two distinct causes. The original physical inferences lack specified empirical laws/products; that is a scientific dependency. After nine R32 companion products were completed, the discovery input did not change, so the controller correctly stopped repeating the same discovery. The present recovered internal derivations and external report add actual new content: they can define explicit bounded questions without pretending that CF4 targeting, a PR3 joint null, or a physical Bianchi atlas has appeared.

## Actual source and implementation findings

1. **The R32 publication work did progress.** `docs/codex_handoff/pr_status.yaml` lists all nine R32 cards as completed. The post-publication checkpoint states the same. `OUTPUT_DAG.json` records 0/9 under an explicitly historical `counts_scope`; this is not evidence that those nine products are absent. Add a separate current projection sourced from the PR status/checkpoint, and retain the historical design counts. Original 17/42 external-output acceptance versus 18/42 analytic-alternate remains a separate quantity.

2. **No automatic execution exists in the controller.** `next_packet` prepares one opportunity, records `launch_performed:false`, and returns `spawn_args`. The host must actually spawn, acknowledge, record, obtain the independent review, record it, and call `next` again. Source push alone cannot fix an inactive local host. The handoff should state this operational loop once and make the host continue after each return, rather than introduce another daemon or claim activation from a packet.

3. **One writer is intentional.** Default `next_packet` waits while another task is running. Independent read-only research can be delegated separately with disjoint outputs. The existing `next --review-only` path admits a specifically bounded disjoint review during acquisition; it is not general permission for parallel producer writes or multiple state-file writers. All state changes remain host-serialized. A waiting transport/acquisition is not scientific failure.

4. **Direct append and adaptive discovery have different source shapes.** `append_frontier` accepts the R32 `input_sources:[{path,sha256,role}]` shape. `_adaptive_record` first passes each new task's `input_sources` to `_source_refs`, which accepts only strings naming existing files or HTTP(S) URLs. A R32-style structured frontier thus cannot be submitted unchanged as an adaptive proposal. This mismatch was reproduced using the unchanged functions. Use the direct, reviewed `append-frontier` route for this integration; do not silently relabel the source shape or remove its hashes. A future normalization fix would need tests for both entry points, but does not block this publication.

5. **Preflight is necessary and presently R32-specific.** The controller's append validates structure, semantic delta, dependency graph and preservation; it does not hash source files or verify disjoint paths. The existing `publication_frontier_preflight.py` supplies those checks, but hardcodes the R32 `REL`, frontier and evidence manifest. The minimum useful code patch is to parameterize that existing preflight with optional `--frontier` and `--manifest`, preserving its current defaults and all checks. Resolve ownership against the selected frontier's product directory (or an explicit contract-owned root), not arbitrary path prefixes. Reject absolute/traversal/symlink escapes as today. This lets the new source-bound tasks use the existing controller without another scheduler.

6. **Original metadata locator is inconsistent.** `PUBLICATION_DAG.json.canonical_pr_backlog` names `docs/codex_handoff/pr_backlog.json`; AGENTS and the active orchestrator designate `docs/codex_handoff/pr_backlog.yaml`. Correct that locator and maintain mirrors. This is a representation repair, not a scientific node change.

7. **Semantic identity is evidence-assisted, not a theorem prover.** The controller rejects a changed task ID/path/input hash with the same semantic delta, and rejects before/after objects differing only by stripped metadata. It cannot decide whether differently worded physical questions are genuinely new. Each proposed action must therefore name its concrete changed map, input, estimator, or counterexample and its predecessor. A renamed title, another report, another audit, or a promise of a stronger model is not a new scientific action. The final scientific review already provides the necessary judgment; no new mandatory novelty gate is needed.

## The 29 HOLDs do not share one closure rule

The external DATA/THEORY/REDEF/PROC count is a useful search index, but it is not an executable acceptance verdict. In particular, a literature mean-response formula does not supply the measurement/selection/cross-source law demanded by K03; a partial regular-mode atlas is not a completed B02 family inventory; and availability of mock velocities alone does not certify the source selection/calibration law. Physical details of those proposed bridges are adjudicated in the companion scientific audits.

Use the following routes while preserving the original strings and statuses:

| Branch group | Present distinction | Productive action |
|---|---|---|
| B02, R23-ATLAS | Numeric physical atlas intake; code availability is a separate fact | Inspect exact external numeric exports and mode/history coverage; complete an adapter or partial-family experiment under an explicit separate scope |
| B03–B05 | Downstream physical response plus processing/null calibration | Run a partial-family conditional experiment only when its own inputs exist; retain the original full-family obligations |
| H02 | Parent selection, shared calibration and source covariance | Construct and test the exact selected-statistic operator; acquire and qualify the source law separately |
| H04–H06 | Mean response, covariance/PPC and independent comparison | Separate operator/working-law studies from source-qualified physical inference; consume matching mocks through the same operator when obtained |
| K03–K06, R23-CONGRUENCE | Mathematical response plus actual centroid/frame/depth/cross-law | Integrate corrected response laws and joint-budget tests; do not close empirical requirements with a universal no-sensitivity assertion |
| L03–L06 | Original PR3 same-realization law versus PR4 alternate experiment | Preserve original acceptance and register a separate PR4 estimator/configuration if its genealogy is established |
| R23-SN, V04–V06 | Frozen nominal training binding versus released-observable analysis | Keep nominal-binding failure; create a distinct public-product estimand with its own response and covariance |
| R26-CF4-FINAL-GROUP-CALIBRATION-RESPONSE | Frozen equation is falsified by retained release values | Preserve counterexample; use release-aware corrected response only as a different validated question |
| Six R25/R26 procedural entries | Historical resource/order/timing admissibility | Retain failed/unknown invocation status and consumed allocations; reuse already qualified scientific outputs; do not make retroactive timing recovery a prerequisite for unrelated new work |

The six procedural entries are `R25-DISTANCE-CONDITIONAL-EVIDENCE`, `R25-GAIA-RELEASE-TAG-ASSOCIATION`, `R25-PR3-FREQUENCY-TENSOR-CROSSPREDICTION`, `R25-PR3-STAGED4-TENSOR-CONTRAST`, `R26-FULL7-STREAMED-SPIN2-QUADRATURE`, and `R26-SMICA-EXACT-PR3-IMPLICIT-ROW-PROJECTION`. Their historical verdicts must not be marked PASS by a fresh run, nor generalized into a prohibition on genuinely different science.

## Minimal concrete task decomposition

Use completed internal outputs directly as inputs; a new controller task should perform their new consuming operation rather than redo their derivation solely to earn a status.

1. **Covariance operator product:** export the exact H03/R32-05 window/projection operator and a function transporting a declared source covariance through it, preserving common calibration/PV ownership. Complete deterministic and structured-covariance tests immediately. A missing empirical covariance then blocks only the physical inference consumer.
2. **Joint optical test product:** implement the shared Hubble dipole/octupole budget with uncertain S and the proper finite-redshift order, using retained tensors where the interpretation is valid. Test the existing 0.8/0.8 separate-pass counterexample and joint correlated regions. Do not identify an observed bulk dipole with congruence acceleration by naming.
3. **Radiation-moment product:** consume the v15 calibrated moment interface and exact stress boost-null in a finite, validated likelihood/confidence-image construction. Keep polarization E morphology and intensity stress as separate typed carriers. Real-sky constraints require their own calibrated intensity law.
4. **Simulation-genealogy product:** qualify exact PR4 same-sky/split/noise products and prepare a registered low-ell null statistic. Qualification is an executable source test; download planning is not that product.
5. **Foreground-radius product:** turn the bounded-moment frontier into a dimensioned bound using an explicit observed/source model or a stated sensitivity family, rather than a free radius called physical.
6. **External-atlas product:** inspect numeric exports and conventions, then run supported finite-family equivalence/response tests. No native solver/ODE is introduced in HTT.
7. **Independent released-observable comparison:** use the qualified released SN observable/covariance and its declared mean model to compare with CF4; retain exact overlap/covariance assumptions and do not claim to have reproduced the frozen SALT2 training pipeline.

These are proposed task boundaries, not seven claims of completed empirical results. Their dependencies should connect exact products, rather than every original upstream acceptance. Parent-selected IDs and the final frontier are authoritative.

## Exact append contract

A direct frontier has `frontier_id`, `authorization`, and nonempty `tasks`. Each new task needs:

```json
{
  "id": "ACTUAL_NEW_TASK_ID",
  "kind": "numeric",
  "goal": "Concrete consuming calculation with a distinct estimator or input",
  "acceptance": "Frozen scope, reference checks and exact product criteria",
  "input_identity": "sha256:ACTUAL_INPUT_CONTRACT_HASH",
  "contract_origin": "new_conditional_research",
  "promotes_original_acceptance": false,
  "initial_state": "ready",
  "requires": {"all": []},
  "input_sources": [{"path": "ACTUAL_REPOSITORY_RELATIVE_PATH", "sha256": "ACTUAL_SHA256", "role": "source-bound inputs"}],
  "owned_paths": ["ACTUAL_DISJOINT_PRODUCT_DIRECTORY"],
  "semantic_delta": {
    "kind": "method",
    "before": {"response": "explicit retained predecessor"},
    "after": {"response": "explicit new consuming map"},
    "discriminator": "The calculation or counterexample deciding the change",
    "scope": "Conditional research; original acceptance unchanged"
  },
  "implementation_route": "subagent_specialist",
  "qualified_product_expected": "EXACT_PRODUCT_NAME"
}
```

`depends_on` and `enables_nodes` must not appear as new frontier edges. Use typed `requires`. A consumer requiring a scientific product uses:

```json
{"all":[{"task_id":"PRODUCER_ID","evidence":"qualified","product":"EXACT_PRODUCT_NAME"}]}
```

A completed task with an empty `qualified_products` list cannot unblock that consumer. New frontier tasks cannot start `completed`, even if they consume old reviewed results; the new synthesis/implementation must be executed and reviewed. Do not rewrite the frozen R32 frontier to insert new tasks. Add the new frontier and link it from the existing publication route and canonical PR backlog/mirrors.

## Uptake and host loop

At the current local host checkpoint, preserve active packets and dirty work, inspect the incoming integration diff, and apply it in the existing checkout. Read the actual current state; do not infer it from this remote baseline. Run the parameterized read-only preflight under the same single-writer host ownership as append. On `ALREADY_APPENDED`, continue the existing tasks. On `APPEND_READY`, append once. On ownership conflict, finish/checkpoint the actual writer first; never cancel it merely to reorder research.

```bash
# Use the already-owned state path; do not initialize or replace it.
STATE=.agent-harness/runtime/r23-continuous/STATE.json
# FRONTIER and MANIFEST are the exact paths in the reviewed integration.
.venv/bin/python scripts/codex_harness/publication_frontier_preflight.py \
  --state "$STATE" --frontier "$FRONTIER" --manifest "$MANIFEST"
# Run only after APPEND_READY at the same stable host checkpoint.
.venv/bin/python scripts/codex_harness/research_controller.py --state "$STATE" append-frontier \
  --frontier "$FRONTIER" \
  --authorization 'Owner 2026-10-27: integrate new research, audit recommendations, and continue solver-free observable-bridge tasks; preserve original acceptance and historical allocations.'
.venv/bin/python scripts/codex_harness/research_controller.py --state "$STATE" summary
.venv/bin/python scripts/codex_harness/research_controller.py --state "$STATE" next \
  --available-profile gpt-6.1-sol/medium --available-profile gpt-6-sol/high \
  --available-profile gpt-6-astra/xhigh --available-profile gpt-6-astra/ultra
```

The `--frontier`/`--manifest` preflight flags above are implemented in the accompanying small candidate patch; they are not present in the audited baseline. Use only profiles actually exposed in the live session. Host execution remains `next → actual native spawn → ack → raw result → record → independent candidate review → record → next`. A theory/numerical/code blocker can enter the existing research/escalation route with its operative issue and existing approved allowance. Missing data or an unavailable transport is not evidence for an ultra scientific repair. Do not reset consumed repair IDs or claim the requested model is the observed model.

If every executable root is exhausted, record branch-local missing inputs and stop that branch. Do not repeat an unchanged adaptive fingerprint. New source content or a genuine counterexample permits the corresponding typed semantic resume. The terminal campaign criterion is either all specified acceptances met or exact unresolved branch holds after feasible actions, never a promise that unavailable empirical inputs will appear.

## Verification performed

`python lanes/harness_tests/check_controller_append.py` exited 0 with 11 checks. The script executes unchanged function bodies from the pinned controller; it omits only the unavailable `native_routing` import and `__main__` invocation. It exercises preservation of existing task/history/ultra state, transactional duplicate rejection, exact qualified-product readiness, false-promotion/completed-import rejection, renamed-action and metadata-only-delta rejection, cycle rejection, the source-shape mismatch, and the distinction between structural append validation and source preflight.

These are implementation-level in-memory checks. They do not establish actual routing, native launch, live-state compatibility, install/activation, observational coverage, or original scientific acceptance.

The parent subsequently authorized the minimal preflight implementation. `lanes/harness_tests/publication_frontier_preflight.py` preserves `check(root,state=None)` and R32 defaults, accepts repository-relative `--frontier`/`--manifest`, defaults the manifest beside the selected frontier, and derives the task ownership root from that frontier's parent. `python lanes/harness_tests/test_parameterized_preflight.py` exited 0: **10/10 tests passed**, importing the complete unchanged controller and actual `native_routing.py`. They cover default/custom paths, old-state preservation, default adjacent manifest, selected/input traversal, changed hash, exact already-appended identity, active writer conflicts, task ownership and symlink escape. `--help` also ran successfully with both new flags. The candidate SHA-256 is `52424029240951a213fe71feec614a8a17620307e0c6360e8affcf90e8ec969c`.

The test module can be copied under repository `tests/`: it locates the repository source root from its ancestors and imports the installed candidate script there. Its direct-script mode writes a small result JSON; pytest/unittest discovery does not write that receipt. The final integration still needs its existing DAG/mirror checks, new frontier/static preflight and one scoped independent review of the actual diff. No production state or baseline file was edited by this worker.

## Skill context used

PhysMath Research Loop 1.3.0 main, POLICY_INTEGRATION and CODING_LOOP C4/C9; supplied R6 audit scope. Repository `htt-dag-orchestrator`, `htt-harness-engineering`, AGENTS and CURRENT_CODEX_RUNTIME were read. Their existing-checkout, single-writer, source identity, no-reset, positive-transition and no-native-solver constraints were applied. No recursive delegation, live state mutation, push or external message was performed by this worker.
