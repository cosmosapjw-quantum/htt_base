# Continue the current local HTT campaign

Owner instruction, 27 October 2026: integrate the observable-bridge reconciliation and continue the existing campaign towards reviewed scientific results. Preserve the current session, actual active assignment and original scientific acceptance. The reference before integration was `a55036ad09c53a9215dee3282e425d37cfb95443`; the integration branch is `research/htt-observable-bridge-reconciliation-20261027`. Use the exact commit supplied with the PR/owner handoff, and inspect its diff against the reference.

## Uptake in the existing checkout

1. Finish or durably checkpoint the actual active assignment under the existing host. Preserve its worker identity, packet, raw receipt, download checkpoint and outstanding review. Inspect current branch/HEAD, dirty paths and **the state path this session already uses**. Known checkout: `/home/cosmosapjw/Dropbox/bianchi/htt_base`. Do not create another checkout or worktree.
2. Fetch the integration branch. If the commit is already an ancestor, do not apply it twice. Otherwise integrate the single reviewed change at this checkpoint, preserving newer local/remote work and dirty files. Resolve ordinary conflicts semantically; do not reset, force-push, overwrite another worker's files, replace old DAG cards or reinitialize runtime. Main merge and paper submission are outside this instruction.
3. Read current `AGENTS.md`, `.agents/skills/htt-dag-orchestrator/SKILL.md`, the current native router, this folder's `REPORT.md`, `RUN_CONTRACT.json`, `FRONTIER.json` and relevant research lane. Use accepted evidence rather than reopening entire reports. The old nine R32 companions are complete. Original acceptance is 17/42; analytic V03 alternate is 18/42. New conditional products have a separate ledger.
4. Validate mirrors and the new frontier against the **existing live state** under one host writer. A preflight only reads and simulates append in memory; it cannot lock another process. If `ALREADY_APPENDED`, continue its existing tasks. If an equivalent scientific action is already running or completed, attach the new evidence to that action instead of manufacturing a retry. Do not append a renamed action to reset exhausted allowances.

```bash
# In the existing checkout. Set STATE to the actual path already owned by this session.
P=docs/research_program/observational_publication_20261015/OBSERVABLE_BRIDGE_RECONCILIATION_20261027
STATE=.agent-harness/runtime/r23-continuous/STATE.json
test -f "$STATE" || exit 1
.venv/bin/python -m unittest discover -s tests -p 'test_publication_frontier_preflight_parameterized.py'
.venv/bin/python -m unittest discover -s "$P/covariance" -p 'test_covariance_bridge.py'
.venv/bin/python scripts/codex_harness/sync_pr_dag_mirrors.py --check
.venv/bin/python scripts/codex_harness/publication_frontier_preflight.py \
  --state "$STATE" --frontier "$P/FRONTIER.json" --manifest "$P/EVIDENCE_MANIFEST.json"

# Only on APPEND_READY, after a durable before-state checkpoint and under the same host writer:
.venv/bin/python scripts/codex_harness/research_controller.py --state "$STATE" append-frontier \
  --frontier "$P/FRONTIER.json" \
  --authorization 'Owner 2026-10-27: integrate the reviewed observable bridges and complete feasible scientific products; preserve original contracts and live history.'
.venv/bin/python scripts/codex_harness/research_controller.py --state "$STATE" summary
.venv/bin/python scripts/codex_harness/research_controller.py --state "$STATE" next \
  --available-profile gpt-6.1-sol/medium \
  --available-profile gpt-6-sol/high \
  --available-profile gpt-6-astra/xhigh \
  --available-profile gpt-6-astra/ultra
```

Pass only profiles actually supported by this host. The supplied list reflects the existing campaign interface, not observed runtime on the offline desktop. Preserve old task objects, active packet, campaign identity, event prefix and cumulative ultra records after append. If the preflight reports a changed frozen frontier, changed source or active overlapping writer, resolve that concrete finding without a new state or renamed frontier.

## Scientific goal and parallel work

The goal is a coherent sequence of source-bound scientific results and manuscript sections from the existing theory and measured summaries. Produce an equation/result table/figure before expanding governance text. Existing scheduler fairness and active packets remain authoritative. The nine new root candidates are independent where their declared write paths permit it. The controller may serialize dispatch: do not fabricate simultaneous reservations. Independent research can use native subagents under separate owned paths.

- **R36-01 → R36-02:** recover the exact H03 source operator, then propagate physical correlated PV/calibration covariance through it. The streamed implementation is already supplied. Conditional model-based covariance is executable before author-only mocks; original source-population calibration remains separate. Recover the producer and cache first. Do not repeat a frozen failed fit or add the 250 km/s term twice. Physical leading source/observer columns use the same operator with opposite signs.
- **R36-03:** implement the full PM endpoint/history response, its positive nearby-source sign, finite-history bound, VSH projection and source-specific information image. A low-power forecast is not a universal no-go. Keep photocentre/matter and reference-frame laws as empirical requirements.
- **R36-04:** implement the single-budget seven-component optical consistency test with uncertain shear and direct-dipole profiling. Derive the observer chart and raw-to-target estimator response before assigning acceleration or boost to catalogue coefficients.
- **R36-05:** consume the exact boost-stress criterion and ranks 0/2/4 energy response. Compare against the linear quadrupole method on common inputs and errors. Stop reconstructing when the target response is preserved; evaluate the actual spectrum if a sufficient entropy certificate fails. Matter-shear inference still needs the transport residual.
- **R36-06/07:** qualify a separate PR4 morphology law and a dimensional complex foreground budget. Use actual release/split genealogy and total-variation remainder; one shared sky is one null unit. An arbitrary one-percent cross threshold or free radius is not physical calibration.
- **R36-08:** run the pinned public Pantheon+ released-magnitude anisotropy comparator with its full total covariance, row binding and profiled calibration. This explicit alternate estimand does not establish nominal SALT2 parity.
- **R36-09/10:** search for existing numeric polarized atlas outputs without running a solver; independently complete the finite geometry/constraint image and imported II/VII0 distinction. Code existence is not an atlas payload. A precise atlas source gap must not stop geometry or other ready tasks.
- **R36-11:** as soon as any listed scientific product is actually qualified, draft its integration into the relevant existing R32 manuscript. Own the draft/patch in the task product directory; the host applies it after review. Do not wait for all sources. More completed lanes can be added subsequently.

Each task's exact acceptance and named `qualified_product_expected` are in `FRONTIER.json`; the same requirements appear on the canonical PR card. A generic backlog scheduler must honor `product_requires`, not just ordinary `depends`. A completed acquisition/gap report never satisfies R36-11. Each result identifies the observed quantity, invariant, inferred physical target, frame, response, nuisance class, error budget and comparator. Write novelty assessments in a research memo; write manuscript prose around physics, equations and actual results.

## Continuous host loop and escalation

For each selected packet: **actual native spawn → acknowledge returned identity → retain raw worker receipt → record outcome → one fresh scoped independent review → record review → call next immediately**. Follow-up or repair is allowed for a concrete review finding. A worker return or one completed node is not a campaign stop condition. Requested model/effort is not proof of observed execution; use actual returned evidence.

Use the current router's implementation profile for routine code, its research/review profile for a real scientific issue, and its existing escalation procedure for a concrete failed hypothesis or unresolved review finding. Preserve consumed one-use and cumulative ultra budgets. Do not invent a fresh ultra allowance, launch unmanaged local model servers, or call a timeout/missing file scientific failure. If the stronger profile is unavailable, record that fact and continue independent ready work.

At a blocker, identify the exact missing physical input or failed mathematical assertion. First reuse cached evidence and check the declared weaker/conditional product. Then attempt the task's bounded derivation, source search or legitimate new validation. Return the concrete receipt, hold only its consumers, and dispatch the next ready branch. Preserve original failed counts, missing timing records and prior no-go equations. Future runs cannot rewrite past execution history.

Continue until all authorized executable products are completed and reviewed, or every remaining path has an exact unresolved source/review receipt after a genuine research attempt. Keep this as an incomplete scientific checkpoint when necessary, with the next input/action named. Do not relabel completion counts to meet the goal. Commit and push completed reviewed increments to the current research branch under existing authorization.

## Autonomous data intake

Public no-auth acquisition is authorized with **no per-file or cumulative byte cap**. Reuse exact cache/receipts first. Store large data outside Git on the verified external drive, retain the existing streaming free-space checks and 2 GiB reserve, and validate release, schema, units, frame, SHA256 and product roles. Recheck the mount before writing; its current condition was not observed in the cloud.

The two new explicit products total 33,864,243 bytes before any cache reuse:

```bash
M=docs/research_program/observational_publication_20261015/FRONTIER_20261020/ACQUISITION_MANIFEST.json
.venv/bin/python scripts/htt_fetch_open_inputs.py --manifest "$M"
# After exact-cache and semantic intake checks; omit --budget-gib.
.venv/bin/python scripts/htt_fetch_open_inputs.py --manifest "$M" \
  --ids R36_PUBLIC_SN_DATA R36_PUBLIC_SN_STAT_SYS_COV --fetch
```

The pinned fetcher accepts these space-separated IDs (`nargs='+'`). Use the exact source-contract identities in `research/DATA_ATLAS.json`. Verify the Git blob identities as well as local SHA256 after download. The receipt alone is not a scientific qualification. Do not contact authors, bypass authentication or substitute code/plots for a numeric atlas. No native Boltzmann solver or ODE integration is authorized.

## Local uptake binding repair, 27 October 2026

The incoming pack failed the local exact-byte preflight: 154 of 156 evidence rows matched. The imported `imports/v15/cas/response_frontier.csv` has been restored to its declared CRLF bytes (SHA256 `ebd371c45b643658693c356a84efed868133bd6c47f8b796d1b2bd6af71ef751`, 25342 bytes), with an exact-path Git `-text` attribute. The new R36 evidence entry now binds the unchanged older H03 source (SHA256 `5d31e2ab4fea682c538c31c15181ae7b07e11efba98b36c66aff6feca88f8326`, 111342 bytes). The earlier R36 H03 source representation adds exactly one terminal LF and parses to identical values. CSV fields and all H03 scientific values are unchanged.

The corrected evidence manifest SHA256 is `83ebf1cd2ce7ae18a486506219c0a93ec939a74cfa06c21a1316c938678f1c43`; the corrected frontier file SHA256 is `8de844ee16d15eadb3085e6d3a16b172ce2ce6dd62a8bf276d265b9a8b335f24`. Existing validation receipts and `covariance/H03_REPLAY.json` retain their historical candidate/source identities; they do not certify this corrected local pack. Preserve the incoming preimages and first failed preflight. Require fresh exact verification of all 156 evidence rows, the import and delivery manifests, and the read-only current-state preflight before append. The repair leaves the older H03/R32 sources, contracts, results and live campaign history unchanged. It qualifies no scientific product and changes no original acceptance, numerical tolerance, solver boundary or budget.
