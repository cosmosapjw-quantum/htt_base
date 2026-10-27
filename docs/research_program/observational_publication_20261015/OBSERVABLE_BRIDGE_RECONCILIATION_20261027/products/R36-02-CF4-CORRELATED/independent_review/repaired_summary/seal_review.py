from pathlib import Path
import hashlib,json,time
D=Path('/mnt/extdrive/workdir/htt_open_data/r36_cf4_summary_repair_independent_review')
C=Path('/home/cosmosapjw/Dropbox/bianchi/htt_base/docs/research_program/observational_publication_20261015/OBSERVABLE_BRIDGE_RECONCILIATION_20261027/products/R36-02-CF4-CORRELATED/repair_01')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def dump(n,v):(D/n).write_text(json.dumps(v,indent=2,sort_keys=True)+'\n')
checks=json.loads((D/'INDEPENDENT_CHECKS.json').read_text())
expected='a0edd2e76d0b74630d47bbccd5cd90dcb4e372ca1772ee202585a34270d68fb4'
assert sha(C/'ARTIFACT_MANIFEST.json')==expected
for row in checks['bindings']:assert sha(Path(row['path']))==row['sha256']
erratum='''# R36-02 outer source-location erratum

This erratum accompanies, and does not modify, candidate
`sha256:a0edd2e76d0b74630d47bbccd5cd90dcb4e372ca1772ee202585a34270d68fb4`.
The current source entrypoint must consume `RESULT_REFERENCE_RESOLUTION.json`
when exposing the inherited controls references in `repair_01/RESULT.json`.

| RESULT field | Frozen value | Explicit path relative to repair_01/RESULT.json |
|---|---|---|
| controls | CONTROLS.json | ../CONTROLS.json |
| sample_covariance_uncertainty | CONTROLS.json#sample_covariance_if_N64_p36 | ../CONTROLS.json#sample_covariance_if_N64_p36 |

Both controls references resolve to:
`/home/cosmosapjw/Dropbox/bianchi/htt_base/docs/research_program/observational_publication_20261015/OBSERVABLE_BRIDGE_RECONCILIATION_20261027/products/R36-02-CF4-CORRELATED/CONTROLS.json`.
The retained controls SHA-256 is
`5bc24992254da084775eff20b89f49346db9be85158a54ad12df76caefa726e9`.
Its source authority is the parent base manifest, candidate
`sha256:dd3cb2d77c97e33380ec06e04bc5465f65129dc319f8795dc30e3bc84b3e877b`.
The independent review actually read this file, matched its hash to that manifest,
and checked that the `sample_covariance_if_N64_p36` key exists.

`footprint_method_sensitivity` already resolves to the repaired sibling
`SENSITIVITY.json`; its hash is
`ebacda58de95a46e5418ecdbf400976ecd21829c013f774e74ecc7c1ff3d47c5`.

Bare document-relative resolution of the two frozen controls fields fails because
there is no `repair_01/CONTROLS.json`. This is a P3 packaging locator ambiguity.
The actual bounded cache-summary consumer does not read either field and
reproduces RESULT.json and SENSITIVITY.json byte for byte. The parent manifest
already gives an unambiguous source identity. No separate RESULT resolver
contract or failing operational controls consumer was found in the searched
scripts, tests, or R36 package. This erratum does not assert that the frozen
relative fields themselves have been corrected.

Reproduce the explicit source resolution with the existing project interpreter:
`.venv/bin/python -B /mnt/extdrive/workdir/htt_open_data/r36_cf4_summary_repair_independent_review/check_result_references.py`.
The script performs actual file reads, hashes and the fragment check; its
`RESULT_REFERENCE_RESOLUTION.json` is the machine-readable map consumed by this
review. Before publication, the publisher must carry this erratum/map into the
current README/source map entrypoint so that consumers see the correct locations.
This packaging integration does not require covariance or summary recalculation.
The frozen candidate, failed candidate, preimages and scientific ceilings remain
unchanged. No original 42-node acceptance is promoted.
'''
(D/'SOURCE_LOCATION_ERRATUM.md').write_text(erratum)
finding={
 'id':'R36-02-PACKAGING-P3-01','severity':'P3','blocking_for_scoped_summary_acceptance':False,
 'classification':'PACKAGING_METADATA_LOCATOR_AMBIGUITY','path':str(C/'RESULT.json'),'lines':[83,180],
 'fields':['controls','sample_covariance_uncertainty'],
 'issue':'The inherited controls locators retain base-directory-relative text after RESULT.json is copied into repair_01. Plain resolution relative to the new containing directory finds no CONTROLS.json.',
 'actual_consumer_effect':'The bounded cache-summary consumer succeeds and regenerates both outputs byte-identically. It does not read these locator fields. No operational RESULT controls resolver or independent schema requiring sibling-relative resolution was found in the bounded scripts/tests/R36-package search.',
 'source_identity_status':'Resolved: the exact new manifest pins an absolute base_manifest_path and base candidate identity; the retained base manifest pins parent CONTROLS.json.',
 'evidence':str(D/'INDEPENDENT_CHECKS.json')+'#result_pointers',
 'counterexample':{'resolution_rule':'RESULT.json parent directory plus frozen controls filename','missing_path':str(C/'CONTROLS.json'),'observed_exception':'FileNotFoundError','cache_consumer_failed':False},
 'minimal_fix':'Consume the outer SOURCE_LOCATION_ERRATUM.md and RESULT_REFERENCE_RESOLUTION.json at the current publication README/source map. They resolve the two fields to ../CONTROLS.json and ../CONTROLS.json#sample_covariance_if_N64_p36 and have been actually read/hash/fragment checked. Preserve the exact candidate.',
 'scope_effect':'No numerical counterexample. Does not block this cache-summary correctness closeout; publication must expose the verified source locations.'}
repair_plan='No further numerical repair is required. Before publication, carry the reviewed outer SOURCE_LOCATION_ERRATUM.md and RESULT_REFERENCE_RESOLUTION.json into the current README/source map and consume their explicit parent CONTROLS locations. Preserve candidate a0edd2e76d0b74630d47bbccd5cd90dcb4e372ca1772ee202585a34270d68fb4, base dd3cb2d77c97e33380ec06e04bc5465f65129dc319f8795dc30e3bc84b3e877b, all retained caches, failed-candidate preimages, input identity and cumulative accounting. Do not rerun any transform, covariance producer, kernel, broad suite or original R30 600-second bank. This is a packaging source-location clarification, not a new scientific repair or relaxed criterion.'
raw={
 'schema':'htt.r36.independent_summary_review_raw_receipt/1','agent_id':'/root/r36_cf4_summary_repair_independent_review','task_id':'R36-02-CF4-CORRELATED','candidate_identity':'sha256:'+expected,'base_candidate_identity':checks['base_candidate_identity'],'input_identity':checks['input_identity'],
 'requested_runtime':'gpt-6-astra/xhigh','observed_runtime':'UNKNOWN','cwd':'/home/cosmosapjw/Dropbox/bianchi/htt_base',
 'commands':[{'command':'.venv/bin/python -B '+str(D/'independent_checks.py'),'exit_code':0,'observed_checks_report':str(D/'INDEPENDENT_CHECKS.json'),'elapsed_seconds_in_script':checks['elapsed_seconds']},{'command':checks['focused_regressions']['command'],'exit_code':checks['focused_regressions']['exit_code'],'nested_in':'independent_checks.py','stdout':str(D/'regressions.stdout.log'),'stderr':str(D/'regressions.stderr.log'),'seconds':checks['focused_regressions']['seconds']},{'operation':'Unchanged copied cache-consumer source; BASE points to retained base, HERE points to review-owned consumer_copy. No producer imports or source transforms.','exit_code':0,'source_sha256':checks['consumer_copy']['source_sha256'],'stdout':str(D/'consumer_copy_stdout.log'),'seconds':checks['consumer_copy']['seconds']},{'command':'.venv/bin/python -B '+str(D/'check_result_references.py'),'exit_code':0,'evidence':str(D/'RESULT_REFERENCE_RESOLUTION.json')}],
 'evidence_sha256':{n:sha(D/n) for n in ['independent_checks.py','INDEPENDENT_CHECKS.json','PREIMAGE_DIFFS.json','regressions.stdout.log','regressions.stderr.log','consumer_copy_stdout.log','check_result_references.py','RESULT_REFERENCE_RESOLUTION.json','SOURCE_LOCATION_ERRATUM.md']},
 'candidate_and_all_bound_files_unchanged_at_close':True,'old_R30_600s_bank_charged':False,'new_full_producer_or_physics_run':False,'repository_or_controller_state_mutated':False,'candidate_mutated':False,'timestamp_unix':time.time(),
 'execution_limit':'Three focused supplied tests; twelve independent cached summary rows; bounded cache-consumer copy; hashes/readbacks and source-location checks only.'}
dump('RAW_RECEIPT.json',raw)
review={
 'schema':'htt.r36.targeted_independent_summary_review/1','task_id':'R36-02-CF4-CORRELATED','agent_id':'/root/r36_cf4_summary_repair_independent_review','candidate_identity':'sha256:'+expected,'base_candidate_identity':checks['base_candidate_identity'],'input_identity':checks['input_identity'],
 'candidate_manifest':str(C/'ARTIFACT_MANIFEST.json'),'requested_runtime':'gpt-6-astra/xhigh','observed_runtime':'UNKNOWN',
 'review_binding':'PREPARATORY_ACTUAL_INDEPENDENT_REVIEW_NOT_FORMAL_CONTROLLER_ACK_OR_QUALIFICATION',
 'verdict':'SCOPED_PASS','outcome':'success','scope_acceptance_met':True,'acceptance_met':False,'science_admission':False,'original42_promotion':False,'qualified_products':[],
 'scope':'Close out R36-02-F01: radius-matched cache-only sensitivity summaries and preservation/reproducibility of the exact repaired candidate. The unchanged broader source/physics calculation is not rerun or newly admitted.',
 'closed_findings':['R36-02-F01'],
 'summary':'The eight R=10/20 rows now use their matched full-sample covariance blocks for both comparison values. All twelve independent comparisons pass; all four R=5 rows are unchanged. Three focused tests and unchanged-source cache-consumer reproduction pass. A nonblocking P3 inherited-controls locator ambiguity is explicitly resolved by the reviewed outer source-location map for publication consumers.',
 'positive_checks':[
  'Exact candidate and base manifest identities verified; all 9 base product and 13 base external entries preserved. All 5 new file bindings, all 4 named retained caches, source/operator identities, frozen repair plan and author ACK identity verified: 40 binding checks total.',
  'Independent scalar fsum recomputation, without importing repair/producer routines, verifies 12 trace ratios and 12 Frobenius relative changes against matching 36-coordinate radius blocks. Maximum absolute error 8.881784197001252e-16, within the existing 1e-14 focused-test criterion.',
  'Exactly 16 comparison values across 8 R=10/20 rows changed. All 4 R=5 rows, selected counts, traces, ranks, A-X metadata and every other summary field remain unchanged except repair provenance.',
  'exclude_FP at R=20: trace ratio 1.1710463175169397; Frobenius relative difference 0.35610037450194054. The original reversed-direction comparison is repaired.',
  'Three supplied focused regressions passed. Unchanged copied cache-consumer source generated RESULT.json and SENSITIVITY.json byte-identically in review-owned output; actual sensitivity pointer resolves the repaired sibling.',
  'Initial a571 pointer-error manifest/RETURN/raw and all three changed-file preimages are present and bound. Their diffs are limited to the sensitivity pointer, its explanatory comment and test expectation; the initial and final sensitivity summaries are byte-identical.',
  'STAGE_C, SENSITIVITY_MATRICES, RESULT_MATRICES and PV_FACTORS SHA identities remain unchanged. No source transform, kernel, model fit, full covariance producer, full previous review or broad tests were rerun.',
  'Retained TABLE.csv, FIGURE.png and INTERPRETATION.md are byte-identical. Table and figure concern retained band covariance, figure labels show R=5, and footprint prose quotes only unchanged R=5 ratios. Corrected R=20 interpretation is accurately stated in REPAIR.md.',
  'The parent CONTROLS.json source and sample_covariance_if_N64_p36 fragment were actually read and hash/fragment checked via the explicit outer map. Source identity is unambiguous despite the preserved shorthand locators.'
 ],
 'findings':[finding],'counterexample':finding['counterexample'],'repair_plan':repair_plan,
 'source_location_erratum':{'path':str(D/'SOURCE_LOCATION_ERRATUM.md'),'sha256':sha(D/'SOURCE_LOCATION_ERRATUM.md'),'map_path':str(D/'RESULT_REFERENCE_RESOLUTION.json'),'map_sha256':sha(D/'RESULT_REFERENCE_RESOLUTION.json'),'publication_condition':'Current publication README/source map must consume these correct locations before publication; the immutable numeric candidate remains unchanged.'},
 'preserved_limits':{
  'finite_conditional_covariance':'Retained 36-coordinate R5 conditional covariance and full 108-coordinate PV covariance retain cross-window/radius terms; preservation is verified by identities, not a new physics rerun.',
  'observer_common_null_and_gaussian_selection_MC':'Unchanged inherited evidence; no new coverage calculation or empirical CF4 significance claim.',
  'cross_source_empirical_covariance':'UNKNOWN','outside_PV_bands':'UNKNOWN','empirical_source_population_coverage':'UNKNOWN','full_physical_tensor_x_F_Pi_Q_G':'UNKNOWN; separate physical model and acceptance required',
  'baseline_PV_double_counting':'Inherited working covariance remains separate and is not added to or subtracted from the conditional total.',
  'original_42_acceptance_promotion':False,'native_Bianchi_family_identification':False},
 'validation_evidence':[str(D/n) for n in ['INDEPENDENT_CHECKS.json','PREIMAGE_DIFFS.json','regressions.stdout.log','consumer_copy_stdout.log','RESULT_REFERENCE_RESOLUTION.json','SOURCE_LOCATION_ERRATUM.md']],
 'raw_receipt':str(D/'RAW_RECEIPT.json'),'raw_receipt_sha256':sha(D/'RAW_RECEIPT.json'),
 'skills_applied':['independent-diff-review','htt-scientific-code-validation','htt-claim-firewall'],
 'proposed_candidate_changes':None,'tests_to_run':'No further numerical rerun needed for this summary closeout. Publication source map must actually consume the verified erratum.',
 'risks_and_kill_switches':'Any changed frozen input, cache or candidate identity invalidates this exact-candidate review. Missing outer source-location integration blocks a claim that the published RESULT package is self-resolving, not the demonstrated numerical summary result.',
 'next_transition':'Controller may bind this independent scoped review through its actual protocol, then carry the outer source-location erratum/map into the current publication entrypoint and continue the dependency-safe DAG. This review does not itself ACK, qualify or publish.'}
dump('REVIEW_RESULT.json',review)
print(json.dumps({'verdict':review['verdict'],'candidate_identity':review['candidate_identity'],'review_path':str(D/'REVIEW_RESULT.json'),'review_sha256':sha(D/'REVIEW_RESULT.json'),'raw_receipt_path':str(D/'RAW_RECEIPT.json'),'raw_sha256':sha(D/'RAW_RECEIPT.json'),'erratum_sha256':sha(D/'SOURCE_LOCATION_ERRATUM.md'),'map_sha256':sha(D/'RESULT_REFERENCE_RESOLUTION.json'),'findings':[{'severity':'P3','blocking_for_summary':False}],'formal_controller_qualification':False},indent=2))
