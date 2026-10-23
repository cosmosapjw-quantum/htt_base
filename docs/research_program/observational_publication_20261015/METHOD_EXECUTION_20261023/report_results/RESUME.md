# R24 report handoff

Repo: `/home/cosmosapjw/Dropbox/bianchi/htt_base`
Branch: `research/htt-open-input-theory-20261018`
Source base: `dfaf171c37f2636c942a99bf2b9803b57295ac14`
Current publication base: `2c869f634e6673703f9434785fab3c4cfab76218` plus uncommitted reviewed candidates. Final commit is pending host review/push receipt; no predicted SHA.

Input: `../R24-REPORT-RESULTS_INPUT.json`, SHA-256 `1811cba7fce4808adebadebe39334545d9f3a9cd71c58bbbb874d198d8385f3f`. Actual packet `f1f6290ebd277ddefb729a5faba53d6ee06eab0b0aaeefd030ca466f40ff7b2e`; actual author `/root/report_results`. Requested and transport-selected `gpt-6.1-sol/medium` via existing general-code router; normal-code `gpt-5.6-terra/medium` unavailable, `TRANSPORT_MODEL_UNAVAILABLE`. Observed runtime UNKNOWN. No children, commit, push or scientific rerun in this report task.

Durable live state: `.agent-harness/runtime/r23-continuous/STATE.json`; preserve it, existing packet/history/task/cost identities and exhausted ultra allocations. 13 actual conditional research nodes independently reviewed completed; external original 17/42 and alternate 18/42 unchanged. Historical 48 task objects and R9 UNKNOWN preserved. The report task's own independent review is pending host action.

First inspect the live summary/state before any continuation:

```sh
cd /home/cosmosapjw/Dropbox/bianchi/htt_base
.venv/bin/python scripts/codex_harness/research_controller.py --state .agent-harness/runtime/r23-continuous/STATE.json summary
```

The original execute return has already been normalized and recorded by the host at `.agent-harness/runtime/r23-continuous/r24/REPORT_EXECUTION_RETURN.json`. Original `AUTHOR_RETURN.json` is archival and has a raw_receipt object plus validation field incompatible with the controller record envelope. Never record or replay it. This bounded repair returns `REPAIR_RETURN.json`, with an absolute string raw_receipt and meaningful validation_evidence. Host binds the actual repair packet, receipt hash and new candidate, acknowledges/records according to the current live phase, then obtains the fresh independent final review. If the task is already completed, proceed to source-specific new-payload intake; do not relaunch the report.

After the actual pending return/review is recorded and if live state requires the next packet:

```sh
.venv/bin/python scripts/codex_harness/research_controller.py --state .agent-harness/runtime/r23-continuous/STATE.json next --available-profile gpt-6-sol/high --available-profile gpt-6.1-sol/medium --available-profile gpt-6-astra/xhigh --available-profile gpt-6-astra/ultra
```

Host actually dispatches and acknowledges any pending selected packet, records its actual raw return, and requests next. Selection alone is not dispatch. The controller is no daemon. Preserve task, packet, accounting and exhausted allocation identities. Independent final report review precedes host source push.

Input triggers for a new science intake (not authority to execute them here):

- `P1_statistical_functionals`: Source-qualified selection/physical law, source-congruence map, physical MES anchor or calibrated identified interval; finite scenario images available
- `P2_CMB`: Matched joint FULL/HM/OE processed total-field/noise/foreground/weight-estimation/selection law, justified common-contaminant constraint and crossoperator response
- `P3_distances`: Parent targeting/detection/rejected-source probabilities, source-qualified shared calibration/group/PV covariance, finite-z response/remainder and named source-congruence map
- `P4_local_global`: Actual externally supplied history and selection/calibration/jointcovariance qualified response and independent injection law; analytic alternate does not pass originalexternalhistory
- `P5_family`: External native polarized allm/highell family/mode/history atlas with admissibleIC/epoch, conventions/normalization, mask/operator/null/equivalence validation; cannot manufacture solver/ODE
- `P6_kinematic`: Centroid/matter/sourceclass response, selectedreported-to-truedepth/PM likelihood, residualGaia calibration/crosssource/spatialcovariance, physicalhistory and congruence

SN separately needs the pinned nominal trained model/PS1 config/observed FITRES parity product. New source payload identity or a distinct bounded method delta must pass the existing intake/resume semantics; do not relabel an exhausted attempt. Physical Pi remains [0,1], unknown mass1, no physical MES anchor, posterior, calibrated observed p-value, native family, or cosmological chirality. No claim that all future methods are exhausted.

Validation performed by author: source hashes/sizes, Markdown local link existence and factual number/source consistency only; no science/test execution. Reuse pinned final review receipts for historical test outcomes. Final report-independent decision and publication remain host responsibilities. Remote Desktop Commander transport is exhausted and is not retried.

Archival planning warning: `../FRONTIER_CONSUMERS.json` was an unused early draft and is not an appended live frontier. Its old input hashes do not authorize replay. `../R24-DEPTH-IMAGES_INPUT.json` is likewise an unused early advised input; actual execution used `../R24-DEPTH-IMAGES_EXECUTION_INPUT.json`. Preserve their bytes. Only existing `state.frontiers` defines appended frontiers; do not append all `FRONTIER*.json`. The 11 active frontier files are FRONTIER_FIRST, FRONTIER_K03, FRONTIER_SN, FRONTIER_DISTANCE_CONSUMERS, FRONTIER_K03_DEPTH, FRONTIER_CMB_ENVELOPE, FRONTIER_TENSOR, FRONTIER_NONLINEAR_OPTICAL, FRONTIER_DEPTH_IMAGES, FRONTIER_CMB_CHIRALITY and FRONTIER_REPORT_RESULTS (each `.json`). Exact completed science bindings are in SCIENCE_EXECUTION_CHECKPOINT.json.

Repair packet: `29918bb01e3d1270f702f96f4959ec0f2aaf064cd5889f16f764585504758ba0`; base packet `f1f6290ebd277ddefb729a5faba53d6ee06eab0b0aaeefd030ca466f40ff7b2e`; base candidate `sha256:84c6b79d248648c4a323c6a917d7b33eea55f87ec5e0e525648e29a799d5cb50`. First-candidate README and all report files are archived under `first_candidate_84c6b79d/`. Original MANIFEST.json, RAW_RECEIPT.json and AUTHOR_RETURN.json remain unchanged at their original paths. REPAIR_MANIFEST.json defines the new sealed candidate; REPAIR_RAW_RECEIPT.json and REPAIR_RETURN.json bind it without a self-hash cycle.
