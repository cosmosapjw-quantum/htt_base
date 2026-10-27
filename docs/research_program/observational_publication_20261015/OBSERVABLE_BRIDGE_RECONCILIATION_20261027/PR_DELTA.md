# Canonical PR and execution-contract delta

The canonical `docs/codex_handoff/pr_backlog.yaml` gains PR-R36-00-INTEGRATION and the 11 cards below. Existing cards and topological-order prefix are retained. `pr_status.yaml` records integration separately from the pending scientific products. JSON/YAML mirrors are regenerated, not independently edited.

`PUBLICATION_DAG.json` changes metadata only: its original paper/node objects are untouched. `OUTPUT_DAG.json` gains a dated current 9/9 projection while preserving its old snapshot. The existing acquisition manifest gains two explicit-ID Pantheon resources with no byte cap. The preflight accepts `--frontier`/`--manifest`; its old default and controller remain unchanged.

| PR card | Required product before execution | Exact qualified output |
|:--|:--|:--|
| PR-R36-01-CF4-OPERATOR | none | `h03_exact_operator` |
| PR-R36-02-CF4-CORRELATED | h03_exact_operator | `cf4_correlated_response_result` |
| PR-R36-03-PM-HISTORY | none | `pm_history_response` |
| PR-R36-04-OPTICAL-JOINT | none | `optical_joint_response` |
| PR-R36-05-RADIATION-RESPONSE | none | `radiation_response_comparison` |
| PR-R36-06-PR4-MORPHOLOGY | none | `pr4_morphology_result` |
| PR-R36-07-FOREGROUND-BUDGET | none | `foreground_budget_result` |
| PR-R36-08-PUBLIC-SN | none | `public_sn_anisotropy_result` |
| PR-R36-09-ATLAS-INTAKE | none | `external_atlas_intake` |
| PR-R36-10-GEOMETRY-IMAGE | none | `geometry_compatibility_result` |
| PR-R36-11-SCIENCE-SYNTHESIS | any one qualifying response/data result | `observable_bridge_manuscript_update` |

Every frontier task owns only its declared `products/<task-id>` subtree. R36-11 drafts a manuscript patch in its own product directory; the single host integrates that patch into the existing manuscript after review. A worker does not write another task’s product or the canonical ledgers.

The outer PR backlog has ordinary scheduling dependencies; each card also carries `product_requires`. The native controller frontier is authoritative for all/any qualification, especially R36-11. A generic PR selector must not dispatch a product-gated task using `depends` alone. Scientific gap reports can be completed records but never satisfy these named scientific products.

Preflight verifies frozen inputs, not physical sufficiency. Physical acceptance is the task’s detailed `acceptance` plus one scoped independent review and an exact result/source receipt. `initial_state: ready` imports candidates; dependency readiness is computed by the controller. No new task enters as completed.

## Reviewed source checkpoint: R36-07 and R36-08 (2026-10-27)

Publish exact07 partial geometry/noise/results, original793f preimage and actual independent review while recording typed input HOLD: finite physical radius remains unqualified; C-vector/diagonal relation unresolved; correct native stream count146022144. Publish08 conditional source candidate and all16 survey deletions, covariance first failure and bounded scope-repair decision; full1701 remains FAILED_OUTSIDE_CONSUMED_SUPPORT while selected490/705 remain unchanged. Formal08 controller review is pending; acceptance=false and qualified_products=[] in publication metadata. Frozen note line49 command erratum is consumed in08/source_backup/README.md without editing the candidate. No numerical reruns, tolerance changes, raw observational inputs or STATE writes.

PR-R36-00-INTEGRATION now completed from published integration receipts (8covariance/10preflight/14integration checks), all156 exact evidence entries, independent local six-file closeout and actual98->109 append preservation. This is integration completion, not original42 scientific admission or full-repository CI. Other scientific consumer statuses remain pending. Existing mirrors/DAG are checked for this packaging-only checkpoint.
