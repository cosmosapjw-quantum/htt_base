# 08 — P0–P3 BACKLOG

## P0 — continuation/correctness/data-loss blockers

| ID | Task | Why | Dependency | Required output/evidence | Done criterion |
|---|---|---|---|---|---|
| P0-STATE | fresh-read PR463/PR464 and confirm no newer owner-approved successor | concurrent remote work can make a handoff stale | none | exact current heads + active master/DAG identity | canonical state reconstructed without unresolved conflict |
| P0-WRITER | preserve one source writer and do not dispatch Local Codex before freeze | avoids divergent source/science branches | P0-STATE | explicit MAIN/Local ownership | no competing execution candidate |
| P0-FREEZE | keep `execution_release=false` until M1/M2/M3 close | executor must not choose missing science | M1,M2,M3 | immutable `THEORY_FREEZE` handoff | all selected scientific choices fixed |

## P1 — core scientific claims/functionality

| ID | Task | Why | Dependency | Required output/evidence | Done criterion |
|---|---|---|---|---|---|
| P1-M1 | close `M1_CMB_MODEL` | highest-priority scientific gap | T_CORE, REUSE | exact PR3 product semantics; ordered observation operator; low/high/foreground/noise joint law; primary score/controls; null/chart/tail/numerical policy | no CMB product/statistic/prior/null substitution left to executor |
| P1-M2 | close `M2_REDSHIFT_MODEL` | required for valid depth/frame inference | T_CORE, REUSE | actual distance/redshift likelihood; calibration/selection/frame/windows; shared covariance; supported and unsupported functionals | no toy profile promoted to global native tilt; partial identification explicit |
| P1-M3 | close `M3_EXPERIMENT` | turns M1/M2 into executable finite experiment | M1,M2 | estimands, exact inputs, masks/bins/grid, mock roles, training/calibration/test, multiplicity/coverage/power/abstention, numerical/error budget, missing/model-failure branches | single immutable implementation/data contract |
| P1-CAMPAIGN | execute C0–C5 after theory freeze | actual code and scientific result are still absent | THEORY_FREEZE | source patch, affected tests, synthetic validation, selected-input manifest, observed result or typed stop, readable Git return | MAIN can assess actual scientific result |

## P2 — robustness / validation / manuscript readiness

| ID | Task | Why | Dependency | Required output/evidence | Done criterion |
|---|---|---|---|---|---|
| P2-TCORE | native/focused regression of only T_CORE formulas actually consumed by new code | T1–T10 are derived, not newly native-tested | C1 | exact/numerical oracle tests with failure preservation | used formulas pass at exact candidate source |
| P2-FINITE | establish selected finite-operator numerical statement | current finite-pixel containment remains unresolved | M1/M3/C2 | rigorous enclosure or explicitly empirical convergence + claim grade | no continuum→pixel overclaim |
| P2-FIG | hostile/legibility audit of C2/C4 figures | plots can visually overstate evidence | C2/C4 | plot code+inputs+caption+review | scientific message <= evidence |
| P2-ARTICLE | focused research-article revision after results | 55p teaching report is not the final research article | MAIN_RESULT | result-specific claim/evidence/literature map | abstract/conclusion match actual result |

## P3 — extension/cleanup/future work

| ID | Task | Why | Dependency | Required output/evidence | Done criterion |
|---|---|---|---|---|---|
| P3-CANON | decide canonical migration beyond T9 v4/30 | governance/release choice | post-result owner decision | explicit promotion ledger | owner-approved canonical state |
| P3-PR4 | admit PR4/NPIPE or other expanded CMB products | optional robustness/upgrade | product availability + frozen model | matched product manifest | no substitution by directory name |
| P3-REMOTE | remote kSZ/pSZ/new survey extensions | future extra information | owned response/data | separate scientific contract | not required by current finite campaign |
| P3-BIANCHI | native Bianchi/global-tilt solver family work | separate adjacent track | actual upstream response/provider work | separate repo/DAG evidence | do not mix with current HTT campaign |
| P3-PERF | GPU/JIT/performance optimisation | useful only after same-physics target fixed | validated C1/C2 | before/after same-output benchmark | speedup without physics/tolerance drift |
| P3-RELEASE | merge/ready/public hosting/submission | dissemination/governance | owner decision | explicit approval + applicable release checks | not automatic from document or test PASS |

## Priority sanity check

P0 is intentionally small. M1/M2/M3 are P1 scientific closure, not P0, because the project can continue productively in MAIN without them; they block **execution release**, not state reconstruction. A missing optional data lane at C3 blocks only that lane and must not invalidate independent admitted theory/synthetic/CMB/depth work.
