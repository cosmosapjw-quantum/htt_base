# R62 stage-10 additive DAG interface (read-only mapping)

Source checkout: /home/cosmosapjw/Dropbox/bianchi/htt_base. Baseline c118982e56ee50d68dd0446aa10f16ffe65bd02b. Read-only mapping; no remote mutation, test invocation, or scientific re-review.

## Established updater and commands

- Existing one-shot author script: scripts/r61/finalize_dag.py. DO NOT rerun: it deliberately errors when the R61 card exists. Adapt its schema for R62.
- Canonical PR authority: docs/codex_handoff/pr_backlog.yaml and pr_status.yaml.
- Existing mirror writer: `.venv/bin/python -B scripts/codex_harness/sync_pr_dag_mirrors.py --write`.
- Mirror checker: same script `--check`.
- PR DAG checker: `.venv/bin/python -B scripts/codex_harness/validate_pr_dag.py docs/codex_handoff/pr_backlog.yaml`.
- Scientific planner checker: `.venv/bin/python -B scripts/htt_publication_dag.py --validate`.
- Derived queue writer: `.venv/bin/python -B scripts/htt_publication_dag.py --export`, writes docs/research_program/observational_publication_20261015/READY_QUEUE.json.
- Existing R61 receipts: R61_KINEMATIC_MEASUREMENT_20261117/RESULTS/FINAL_SYNC_MIRRORS.log and FINAL_EXPORT_PUBLICATION.log. The historical queue reported ready_count0, external_blocker_count7.

Mirror --write copies canonical backlog YAML to machine_readable/pr_backlog.yaml; emits docs/codex_handoff/pr_backlog.json and machine_readable/pr_backlog.json from parsed YAML; copies canonical status to machine_readable/pr_status.yaml. It also synchronizes optional authorized_principals.yaml and research_remediation_state.yaml when present. --write runs its own consistency check afterward.

## Baseline counts

- Canonical backlog:285 cards. R61 receipt records284 before its insertion and285 after.
- Canonical status: completed220, blocked16, pending20, dormant_external28, background_in_progress1; in_progress=null.
- Original publication DAG:42 nodes,18 completed_scoped,1 blocked_input,23 pending; six submission-terminal gates and seven nodes with external_missing.
- Original42 node payload digest, computed exactly as R61 does with sha256(json.dumps(nodes,sort_keys=True).encode()): e3264e105cabf78ddac37addc36cacc3cfa05ee942e33e54b431b22e3e87de0d.
- PUBLICATION_DAG.canonical_backlog_baseline_entries=245 is historical creation metadata. Do not relabel that as the current285.
- An added completed R62 card would give286 total and221 completed; scientific42 counts remain unchanged.

## P5 original contract to preserve

PUBLICATION_DAG.papers entry id P5:
- priority6; slug bianchi_identification.
- Title: Bianchi observable-equivalence and family identification with CMB T/E/B.
- Question: physical type/mode response at Planck likelihood level, observational equivalence classes, family confusion/evidence.
- Estimands: verified family/mode/curvature/IC transfer, high-l temperature and polarization; no orientation-only family inference.
- Minimum publishable: qualified subset-of-types family comparison versus isotropic null with family/equivalence recovery; full11 only if atlas verified.
- Principal blocker: verified full physical polarized Bianchi atlas, including exceptional VI_-1/9, and high-l matched null unavailable.
- Submission gate: actual transfer, priors, collision/radiation physics, family equivalence, matched null, comparison with2016 constraints.
- publication_status=NOT_READY_TO_SUBMIT; allows_negative_result=true; planned_pr_id=PR-HTT-PUBLICATION-P5; planned_pr_is_open=false.
- Separate planned_pr_cards entry is id PR-HTT-PUB-P5, status PROPOSED_NOT_OPENED. Preserve both historical spellings; do not normalize identities while inserting R62.

Original P5 nodes:
- B01 completed_scoped, depends[E2]: inventory admissible I–IX and exceptional VI_-1/9 source/mode templates. Acceptance: partial synthetic/scalar templates do not count as physical verified T/E/B.
- B02 pending, depends[B01]: qualify external native polarized all-m/high-l physical atlas. Acceptance: actual Einstein/Boltzmann, recombination, constraints, IC/mode tests. external_missing explicitly names atlas.
- B03 pending, depends[B02,L03]: convolve physical atlas with actual Planck response/null. No fake source or forged full-sky score.
- B04 pending, depends[B03]: equivalence, injection/confusion recovery and evidence. Report degenerate equivalence classes and compare Saadeh2016.
- B05 pending, depends[B04,X02], submission_terminal=true: decide/draft P5 or verified subset. Actual Planck likelihood and physical mode calibration; HOLD if absent.

P5 historical companion references:
- PUBLICATION_ACCELERATION_20261025/products/R32-07-P5-ALGEBRA (canonical PR-R32-07-P5-ALGEBRA already completed).
- CONVERGENCE_20261028/products/R37-05-FINAL-REPORT/PAPER_EXTRACTS/P5_GEOMETRY_COMPATIBILITY_ATLAS.md.
- OBSERVABLE_BRIDGE_RECONCILIATION_20261027/products/R36-10-GEOMETRY-IMAGE/PUBLICATION_STATUS.json.
These are companion products, not completion of B02–B05.

## Minimal additive R62 PR card

Follow R61 card schema:
```yaml
id: PR-R62-ANISOTROPY-CLASSIFICATION  # use root's actual chosen canonical ID
wave: 0
title: Classify source-aware CF4 confidence tensors and state-dependent Bianchi tilt constraints
owner: HTT
depends: [PR-R61-KINEMATIC-MEASUREMENT]
files: [actual R62 docs/code/scripts/tests, canonical backlog/status, PUBLICATION_DAG.json]
tests: [actual scoped R62 command, existing PR DAG checker, mirror checker, publication checker]
dod:
  - Preserve source/operator/window/frame/normalization identity and full joint covariance.
  - Execute source-aware confidence-tensor structured-class compatibility with actual witnesses.
  - State state-dependent Bianchi/tilt constraints and scoped counterexamples.
  - Complete selected ten-stage result and one bounded independent review.
  - Keep all structured classes compatible, no detected family, and NOT_READY_TO_SUBMIT.
notes: actual R62 RESEARCH_DAG.json
kill: No physical family detection from retained phenotype; no original42 promotion; no automatic successor.
level: L0
scope: science
risk: R2
claim_tier_ceiling: C0
user_authorized: true
authorization: actual current owner instruction
```

Append card once; preserve parsed previous285 cards semantically. Add the ID to both policy.topological_order and policy.strict_extension_cards consistently, using R61 as the insertion predecessor if retaining the established append convention. Append status completed only once the parent has actually completed stage10 evidence.

## Minimal additive publication linkage

Archive existing current_scientific_route (R61,P6) once into previous_scientific_routes; set current_scientific_route to the R62 record with selected_paper=P5. Preserve papers/P5 original fields and add one companion pointer, e.g. current_scoped_classification={pr,report,plan,research_dag,original_acceptance_status_preserved:true}. A scoped R62 ten-stage DAG lives in its own R62 folder; do not append ten nodes to the original42.

R62 route fields should include source_base_sha=c118982e56ee50d68dd0446aa10f16ffe65bd02b, scope=source-aware confidence tensor classification plus state-dependent Bianchi/tilt constraints, status=COMPLETE_SCOPED_C0 only after actual completion, original_six_tracks_and_42_gates_preserved=true, automatic_successor=false, local_agent_prompt_created=false, submission_status=NOT_READY_TO_SUBMIT. Preserve actual review status verbatim.

After editing, assert original42 payload digest unchanged, previous285 cards unchanged and P5 original contract unchanged except additive companion pointer. Keep original B01–B05 states and dependencies. Update publication README current route while retaining R61 as prior route, then synchronize mirrors and export derived queue using the existing commands. This mapper did not execute these writes/checks.

