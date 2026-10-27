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

## PR-R36-09 reviewed source intake backup (2026-10-27)

Record the exact source-scoped input HOLD and publish inventories/code/actual receipts/independent partial review. No numeric polarized T/E/B payload qualified in the inspected pinned trees, six archives and source products; this is not universal absence. Source-backup README consumes the review's narrower restricted-morphology requirements: no blanket physical shear conversion/full separate history-array prerequisite, and canonical m support can be completed by justified symmetry/rotation. AniLoS m=0 documentation versus m=1/2 implementation discrepancy remains a future payload check. Preserve frozen RESULT/RETURN, all first failures, original42 and other lane statuses. No provider archive/raw input table, STATE dump, solver or ODE is published or executed. Canonical09 is blocked, never completed; acceptance=false and qualified_products=[].

## PR-R36-01 formal source-operator qualification (2026-10-27)

Consume the actual formally recorded independent review packet6a1d06c19d5c65bc02ba6520e7c23462848dac98798bc79c8edf0bb258c21172 for unchanged candidate164f5f63084caaf4ca18062d314ef53cf4773c528e72333a6b6d24a7e4437b14. Canonical01 now completed and h03_exact_operator qualified only under fixed d,w,n working law. Add exact formal RETURN/raw/identity/source/ACK evidence and retain prior pending-publication metadata as history. No source, artifact, consumer, numerical result or original42 acceptance is changed;02 and all other scientific task statuses remain unchanged. Reuse the76 independent checks and actual consumer/row-ID falsifier evidence; no expensive rerun or STATE write.

## PR-R36-07 conditional envelope/tail source checkpoint (2026-10-27)

Publish exact same-issue positive-envelope research and a separate fresh independent conditional-method review. Preserve first independent-fixture failures, analytical proof, numeric witnesses and source intake; omit15raw primary source files70068684B with URL/seals. Consumer README names centered delta=beta+3 moments and high-order quadrature, confines7.898526K_CMB to three synchrotron rows under idealized assumptions, and requires all native response inside the bracket or positive out-of-band domination. Refined physical certificate permits aggregate flux/response-loss bounds, supported tails/common-emitter law and native response bridging without exact beam equality or FIRAS C-squared byte equivalence. Canonical07 remains blocked/unqualified with acceptance=false; no candidate/frontier/STATE/original42 change, new task/reset or numerical rerun.

## PR-R36-03 formal conditional PM-history qualification (2026-10-27)

Consume the actual formally recorded independent review packetf7f717415da24a41132c78357939d61cdcc8ac32dd080f8a0f242087f25b5984 for unchanged candidate781939c14b1ae7a17f8321d268955cf099d04ede9a0bcfc4c006317d3c137424. Canonical03 now completed and pm_history_response qualified only as a C0 conditional endpoint/history response and fixed-design working sensitivity; spatial covariance, physical depth/history, centroid-to-matter, NNR and selection laws remain unsupplied. Add exact formal RETURN/raw/identity/source/ACK evidence and retain prior pending-publication metadata as history. No source, artifact, consumer, numerical result or original42 acceptance is changed;02 and all other scientific task statuses remain unchanged. Reuse the existing independent checks, five focused tests and in-memory reproduction evidence; no expensive rerun or STATE write.

## PR-R36-05 formal common-input radiation-response qualification (2026-10-27)

Consume the actual formally recorded independent review packetc9aea65e654c85e395aa4cb71bb0f15e1979380e1c818c6c3f83c53394702eea for unchanged candidate91a3af176f7eabf3dba8d1af94616cd3a66a4e3ee374f731f45bb58236e6593d. Canonical05 now completed and radiation_response_comparison qualified only for the six-case synthetic common-input nonlinear T4 versus linear quadrupole comparison, finite coverage/physicality diagnostics and static rank0/2/4 response. Three nonblocking limitations, two actual producer calls, resource clarification and the existing31280133-byte carrier remain unchanged; no second carrier copy. Add exact formal RETURN/raw/identity/source/ACK evidence and retain prior pending-publication metadata as history. No source, artifact, consumer, numerical result or original42 acceptance is changed;02 and all other scientific task statuses remain unchanged. Reuse the392 independent checks and exact existing scientific evidence; no expensive rerun or STATE write.

## PR-R36-07 temperature-domain research and recorded input HOLD (2026-10-27)

Publish exact temperature-floor/domain proof, reproducer/witnesses/source intake, independent conditional review and actual research RETURN/ACK016/NEXT016. Omit3raw primary PDFs1738622B with URLs/seals. Consumer notes preserve comoving/bounded-velocity floor assumptions and boosted-grey counterexample; u does not control the old T/T-squared poles; pointwise Planck endpoint envelopes cannot become whole-band endpoint minima. Full24/168 response bounds do not qualify the old nine-row radius. The1532.873306K calculation is material/size/constant-temperature one-year/no-replenishment conditional, with no universal population cut. Bolometric/tail routes need explicit compatible assumptions. Actual positive upper-flux/aggregate-response-loss/native-operator/full admitted-class inputs remain missing; no exact-beam gate, zero filling, completed-status or budget/Ultra reset. Canonical07 remains blocked and points to its actual formal research input-HOLD receipt; all other statuses and original42 remain unchanged.

## PR-R36-08 formal released-magnitude comparator qualification (2026-10-27)

Consume actual formal review packet53df9b5a78c6543c23f0210f25b330efbd23cfe1b7c804ff0b550263c209fe50 for unchanged efeb05 candidate and qualify only public_sn_anisotropy_result. Preserve selected490/705 raw-C exact symmetry/PD and single-use covariance, with no duplicated PV term. Full1701 defect remains outside consumed support with UNKNOWN source cause. No SALT2 parity/absoluteH0/physical-frame/native/original42 promotion; all first failures,16deletions and bounded source-scope repair remain. Add exact formal receipts/ACK017/NEXT017 and retain prior metadata as history; other statuses unchanged. No fit/numerical rerun or STATE write.

### Required five-node R36 checkpoint

Completed 196/266 = 73.68%; Dependency-weighted completion: 79.53%; Critical path: PR-000 -> PR-003 -> PR-004 -> PR-010 -> PR-014 -> PR-050 -> PR-051 -> PR-052 -> PR-053 -> PR-054 -> PR-055 -> PR-060 -> PR-061 -> PR-062 -> PR-063 -> PR-064 -> PR-065 -> PR-066 -> PR-111 -> PR-114 -> PR-115 -> PR-116 -> PR-117 -> PR-118 -> PR-119 -> PR-121 -> PR-122 -> PR-123 -> PR-124 -> PR-125 -> PR-126 -> PR-127 -> PR-128 -> PR-131 -> PR-132 -> PR-133 -> PR-134 -> PR-135 -> PR-137 -> PR-138 -> PR-139 -> PR-140 -> PR-141 -> PR-142 -> PR-143 -> PR-153 -> PR-154 -> PR-167 -> PR-172 -> PR-184 -> PR-185 -> PR-186 -> PR-187 -> PR-188 -> PR-189 -> PR-190 -> PR-191 -> PR-193 -> PR-194 -> PR-198 -> PR-199 -> PR-202 -> PR-205 -> PR-206 -> PR-207 -> PR-208 (81.82%). These are ordinary canonical PR-card metrics, not physical scientific completion. R36completed00,01,03,05,08=5cards includes integration00; scientific qualified products=4/11. Originalexternal17/42 and analyticV03alternate18/42 remain unchanged. The existing report's generic checkpoint_due flag follows its global-card modulo; this required slice checkpoint is recorded after five R36cards.

Full test collection exit2:10932/10990collected,58deselected and3importerrors in htt/src/common/test_structured_inference.py, tests/common/test_mes_directional_state.py and tests/pr_cards/test_pr_254_normalizer_anchor_geometry.py. All three fail importing standard-library NormalDist because statistics resolves to htt/bass/statistics.py. No skipped-count summary was reported; deselection is not a skip. Full stdout/stderr and command/PID/elapsed receipts are retained externally in r36_public_sn_formal_publication; no unrelated source fix or test execution was attempted.

No claim-tier drift found in the selected qualification metadata: conditional products remain separate from original42/physical-frame/SALT2/absoluteH0/native claims. Next slice:02/04/10/11targetedwork/repairs plus06actualMC;07/09typedinputholds. Other canonical statuses remain unchanged and controller owns all actual dispatch.

### Post-checkpoint collection correction: reviewed ordinary maintenance (2026-10-27)

The prior five-node checkpoint accurately retained3NormalDist import errors and remains historical evidence. A fresh independently reviewed two-line legacy-test path repair now removes only package-interior /bass from two test sys.path lists. Standard-library statistics is restored without preloading/shims and public bass.statistics remains unchanged. [Exact source/evidence backup](validation/LOCAL_UPTAKE_20261027/source_backup/collection_shadow_maintenance/README.md) retains both preimages/diff, author/raw/independent review, full prior/current collection stdout, restored-nodeid comparison and origin proof.

One reviewer final full collection passed exit0 atPID2816422 in19.155965815s:10996selected/11054total,58deselected,0errors;64nodeids restored and0removed. No publisher collection rerun occurred. Actual focused execution remains84passed/8failed and consumer-only baseline56passed with the SAME8PR254 missing artifact/status/AnchorBodySpec failures; this is not all-green execution. Canonicalstatus/mirrors, scientific4/11, original17/42 and analytic18/42 are unchanged; no sciencecard, controller/STATE or production numerical change follows.

## PR-R36-02 and PR-R36-10 formal reviewed source publication (2026-10-27)

Record only02 cf4_correlated_response_result and10 geometry_compatibility_result as completed from their actual formally recorded reviews, preserving candidate a0edd2e76d0b74630d47bbccd5cd90dcb4e372ca1772ee202585a34270d68fb4 and ca55901e8b35f163d0c7b011363e364497ba27bea752e142403c9f6d3d37ffa6. Archive failed base candidates/preimages, actual raw failures, matched-radius repair/controls, full6/10geometry J/H/probes/LRS280/figures/source contracts and independent/formal receipts.02 outer README/sourceMap consumes the reviewed parent-controls locator erratum with actual path/hash/fragment reads, leaving frozen RESULT fields unchanged. Include small sufficient scientific matrices/quadrature inventory; omit53MBregenerablePVfactors/rawobservations/dependencybinaries with seals.

02 is conditional model covariance with empirical coverage/physical fulltensor/native claims unavailable;10 is deterministic finite instantaneous diagnostic compatibility, not probability, topology or family identification. No original17/42 or analytic18/42 promotion, source/fit/kernel/noise/geometry rerun, oldbank/reset or STATE write. All other statuses,11/P4productions and protected dirty scopes remain unchanged. Scoped source bindings, mirror and canonical DAG checks passed; no full collection repeat is needed for exact source/evidence copying.

## PR-R36-11 reviewed production manuscript update (2026-10-27)

Record only observable_bridge_manuscript_update as completed from actual formal SCOPED_PASS candidate83b167a9388071a1a82500716d338473bd8ac5c9abb3c978974a914a37066519. Apply the reviewed overlay into the existing P4 paper; actual new applied consumer/check/build/check succeeded, PDF24pages/fivefigures and text equal sealed candidate, reapply zero changes. Preserve failed base/repaired manifests, baseline preimages, first failures and exact independent/formal/source/production receipts. Outer current README/map consumes CLAIM_LOCATOR_ERRATUM C09/C10 section8 and C11 administrative locus outside physics manuscript, without frozen map edits. Original numerical outputs retained, no old producer or STATE write; conditional C0 scope only, original17/42 and analytic18/42 unchanged. All other statuses/protected edits unchanged.
