# Handoff to the already-running local Codex session

Owner directive, 25 October 2026: incorporate the new physical research into the existing DAG and prioritize concrete publication outputs. This is a continuation of your current campaign, not permission to restart it.

## Uptake at your next host checkpoint

1. Finish or durably checkpoint the actual active assignment. Preserve its packet, raw result, worker identity and any acquisition checkpoint. Do not cancel it merely to select R32. Inspect current branch, dirty paths, active controller state path and current HEAD. Default known checkout is `/home/cosmosapjw/Dropbox/bianchi/htt_base`; use the actual checkout and state already owned by this session.
2. Fetch `research/htt-publication-acceleration-20261025` from `origin`; use the exact integration commit supplied by the owner or the associated draft PR. Base reviewed here was `0d5ab96bdb55398076629099664c77517ec33bb4`. Inspect the incoming commit and diff. If already integrated, do not cherry-pick again. Integrate only this change into the current branch, preserving newer local/remote research and dirty work. Resolve ordinary conflicts semantically; preserve all prior DAG cards/status and mirror invariants. Do not reset, force-push, stash someone else's work, create a replacement checkout, merge main or submit a paper.
3. Read AGENTS.md, the current native router and the local htt-dag-orchestrator skill. Read this folder's README.md, OUTPUT_DAG.json and FRONTIER.json, then relevant evidence only. Preserve the live frozen original-science contract. Do not initialize a new state, migrate old tasks by renaming, or replace any original acceptance. The imported historical baseline is 17/42 original versus18/42 analytic-alternate, not a new counter.
4. Run the focused uptake tests and mirror validation. Run the preflight against the actual existing state. It hashes all imported evidence, checks disjoint new ownership, simulates the controller's existing append in memory and verifies preservation. If it returns ALREADY_APPENDED, do not append again. An active packet remains active. If the same logical action already exists, attach the source/result to that task and continue it; do not manufacture a new action ID to reset attempts.

```bash
# STATE must be the already-used controller state path; do not invent another.
STATE=.agent-harness/runtime/r23-continuous/STATE.json
P=docs/research_program/observational_publication_20261015/PUBLICATION_ACCELERATION_20261025
.venv/bin/python -m pytest -q tests/test_publication_frontier_uptake.py
.venv/bin/python scripts/codex_harness/sync_pr_dag_mirrors.py --check
.venv/bin/python scripts/codex_harness/publication_frontier_preflight.py --state "$STATE"

# Only when preflight reports APPEND_READY; the existing host serializes writes.
.venv/bin/python scripts/codex_harness/research_controller.py --state "$STATE" append-frontier \
  --frontier "$P/FRONTIER.json" \
  --authorization 'Owner 2026-10-25: integrate retained physical results and continue publication outputs without resetting the campaign.'
.venv/bin/python scripts/codex_harness/research_controller.py --state "$STATE" summary
.venv/bin/python scripts/codex_harness/research_controller.py --state "$STATE" next \
  --available-profile gpt-6.1-sol/medium \
  --available-profile gpt-6-sol/high \
  --available-profile gpt-6-astra/xhigh \
  --available-profile gpt-6-astra/ultra
```

Use the available-profile values actually supported by this session. Requested model/effort is not an independently observed runtime. The preflight is read-only and cannot lock a simultaneously writing process; run it and append under the same single host ownership at a stable checkpoint. Preserve a before-state checkpoint, then compare all preexisting task objects, packet objects, campaign identity, event prefix and ultra records after append. The original state is never reinitialized.

## Goal and execution loop

Your goal is a sequence of focused, reviewed scientific papers and notes from the retained results. Start with R32-01-QO-METHODS when selected by the existing scheduler, followed by P1 and the independent structured H03/bounded-bandpass experiments. Existing active packets and scheduler fairness remain authoritative. The seven root candidates are scientifically independent; a held P5 atlas input cannot stop the other products.

For every controller packet: actually invoke the returned native spawn arguments, acknowledge the returned agent ID, retain the raw worker receipt, record its outcome, then obtain one fresh independent reviewer for that exact candidate. Record the review and call `next` again immediately. Returning from one subagent or writing one report is not the campaign stop condition. A planner's `spawn_args` is not a launch receipt. The controller serializes writers; do not fabricate parallel dispatch.

The new scientific artifacts are written only to the task's declared `products/R32-*` directory. Use completed proofs, retained finite data and prior checks. Do not replay a raw sky/catalogue or the entire evidence graph just to make a paper. Generate a result table/figure and a manuscript section before expanding governance documents. Source-hash checks and direct claim tests are sufficient where the underlying accepted result has not changed.

Report each task's `qualified_product_expected` only when its acceptance has actually passed the independent review. A completed gap report is not that product. R32-08 and R32-09 require exact qualified products from R32-03 and R32-04; other root outputs can proceed. Scientific acceptance for the original42 remains a separate decision under its original contract.

The first paper centers on the attained contraction image and sharp chirality bound plus the same-frame logarithmic optical response. QO_COMPARATOR.md contains close 2026/invariant-theory prior art: make the formula-specific comparison, do not sell tensor representation alone as new. The next papers use actual selected-cohort and finite-window results with a named working law. Keep novelty assessment in research notes; write the manuscript around physics, equations, actual results and figures in the owner's direct academic style.

For an actual scientific failure, retain the finding and route bounded research/repair through the existing router. Ordinary implementation uses its selected Sol route; fresh research/review uses Astra xhigh. Ultra is available only under the existing precise-issue authorization and cumulative budget, never for a timeout or missing data alone. Do not reopen consumed R23/R9 one-use budgets. If a narrower conditional/design output satisfies its own declared contract, finish it and separately retain the stronger physical input requirement. Do not soften that contract after seeing a failed result.

Continue `next -> actual spawn -> ack -> raw record -> independent review -> next` until all feasible new products and other authorized ready work finish, or every remaining branch has an exact unresolved input/review receipt after a genuine research attempt. At each completed product update canonical backlog/status and mirrors with evidence, commit and push to the active research branch as already authorized. No automatic submission or main merge. A companion paper does not close an original physical node by relabelling it.

No native Boltzmann solver or ODE integration. Keep physical unknown mass and undefined sectors. CF4 quotient coefficients are already dimensionless; retain the repaired T1 convention. H03 tails remain conditional on the inherited covariance. R31's rank-zero conclusion is for the specified free linear moment class. Do not turn apparent tensors, rank or morphology into a physical detection without the relevant response/law.

Use open sources without additional authentication where practical. Existing receipts and cache come first. The first candidates need no large new data. For a justified later download, preserve the owner's unlimited-size policy, streaming free-space checks and 2 GiB reserve, store outside Git and validate release/schema/units/frame. Do not contact authors or bypass authentication. Missing data block the claim that needs them, not the whole campaign.
