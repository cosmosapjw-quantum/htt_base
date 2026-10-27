import datetime, hashlib, json, pathlib

OUT=pathlib.Path('/mnt/extdrive/workdir/htt_open_data/r36_synthesis_repair_fresh_review')
ROOT=pathlib.Path('/home/cosmosapjw/Dropbox/bianchi/htt_base')
CAND=ROOT/'docs/research_program/observational_publication_20261015/OBSERVABLE_BRIDGE_RECONCILIATION_20261027/products/R36-11-SCIENCE-SYNTHESIS/repair_01'
ORIGINAL=ROOT/'docs/research_program/observational_publication_20261015/PUBLICATION_ACCELERATION_20261025/products/R32-06-P4-DESIGN'
CP=CAND/'candidate/R32-06-P4-DESIGN'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def bind(p):return {'path':str(p),'sha256':sha(p),'bytes':p.stat().st_size}
def write(name,x):p=OUT/name;p.parent.mkdir(exist_ok=True,parents=True);assert not p.exists(),('sealed file already exists',p);p.write_text(json.dumps(x,indent=2,ensure_ascii=False)+'\n');return p
identity='sha256:'+sha(CAND/'ARTIFACT_MANIFEST.json')
assert identity=='sha256:83b167a9388071a1a82500716d338473bd8ac5c9abb3c978974a914a37066519'
packetpath=pathlib.Path('/mnt/extdrive/workdir/htt_open_data/r36_controller/NEXT_028.json')
ackpath=pathlib.Path('/mnt/extdrive/workdir/htt_open_data/r36_controller/ACK_028_GO.json')
packet=json.loads(packetpath.read_text());ack=json.loads(ackpath.read_text())
assert packet['candidate_identity']==identity and packet['packet_id']==ack['packet_id'] and ack['acknowledged']
agent='/root/r36_synthesis_repair_fresh_review';assert ack['agent_id']==agent
assignment=json.loads(packet['spawn_args']['message'].split('Assignment:\n',1)[1])
assert agent not in assignment['authors'] and agent not in assignment['contributors']
workflow=json.loads((OUT/'WORKFLOW_RESULT.json').read_text());assert workflow['status']=='PASS'
science=json.loads((OUT/'RETAINED_SCIENCE_CHECKS.json').read_text());assert science['status']=='PASS'
pdf=json.loads((OUT/'PDF_CHECKS.json').read_text());assert pdf['extracted_text_equal']
assert {str(f.relative_to(ORIGINAL)):sha(f) for f in sorted(ORIGINAL.rglob('*')) if f.is_file()}==json.loads((OUT/'PRODUCTION_BEFORE.json').read_text())
for entry in json.loads((CAND/'ARTIFACT_MANIFEST.json').read_text())['artifacts']:assert sha(CAND/entry['path'])==entry['sha256'],entry['path']
erratum={
 'schema':'htt.r36.outer_claim_locator_erratum/1','candidate_identity':identity,'candidate_manifest':bind(CAND/'ARTIFACT_MANIFEST.json'),
 'scope':'Nonblocking packaging/provenance locator corrections only; no candidate file or scientific value changed.',
 'consumer':'Publisher may include this outer map with the source/PDF package. The actual assembly/build/check consumers do not use the stale historical section labels.',
 'affected_files':[bind(CP/'science/CLAIM_SOURCE_MAP.md'),bind(CP/'report/CLAIM_SOURCE_MAP.md')],
 'manuscript':bind(CP/'science/MANUSCRIPT.md'),
 'entries':[
  {'claim_id':'P4-C09','map_line':15,'field':'Claim and manuscript location','old_section':'§7','actual_section':'§8. Physical interpretation and the next measurement','actual_manuscript_line':449,'paragraph_starts':'The complete carrier therefore retains','reason':'The proper-motion section was inserted as section 7, moving the physical discussion to section 8.'},
  {'claim_id':'P4-C10','map_line':16,'field':'Claim and manuscript location','old_section':'§7','actual_section':'§8. Physical interpretation and the next measurement','actual_manuscript_line':451,'paragraph_starts':'A physical comparator x','reason':'The full-comparator and missing-sector discussion is now in section 8.'},
  {'claim_id':'P4-C11','map_line':17,'field':'Claim and manuscript location','old_section':'§7','actual_section':'Administrative acceptance statement is outside the physics manuscript; related physical requirements remain in §8, line 453.','actual_manuscript_line':453,'paragraph_starts':'The additional physical inputs are concrete','authoritative_administrative_sources':[{'file':bind(CAND/'RESULT.json'),'json_pointer':'/original42_promotion','value':False},{'file':bind(CP/'report/r36_11/SOURCE_CONTRACT.json'),'json_pointer':'/hard_scope/original_acceptances_changed','value':False},{'file':bind(CP/'report/r36_11/SOURCE_CONTRACT.json'),'json_pointer':'/hard_scope/original_17_of_42_and_analytic18_of_42','value':'UNCHANGED'}],'reason':'The frozen editor contract explicitly moves internal V03/acceptance wording out of physics prose. Do not represent that administrative statement as present in section 8.'}
 ],
 'consumer_evidence':{'assemble_py':bind(CP/'report/r36_11/assemble.py'),'check_py':bind(CP/'report/r36_11/check.py'),'explanation':'The assembler reads frozen source hashes and prose; check.py validates hashes and four literal report/r36_11 or supplement path strings in the maps, not P4-C09/C10/C11 or section numbers. Actual fixture assembly/check/build succeeded.'}
}
write('CLAIM_LOCATOR_ERRATUM.json',erratum)
validation=[
 'Verified exact candidate manifest sha256:83b167a9388071a1a82500716d338473bd8ac5c9abb3c978974a914a37066519, all 56 manifest artifacts, and all 30 frozen source identities; source contract is JSON-equivalent to frozen EDITOR_CONTRACT.',
 'Executed unchanged apply(target) in a fresh owned external manuscript fixture, then reassembled, checked, forced latexmk rebuild, checked again, and confirmed second application changed zero files.',
 'All six sealed replaced preimages and all six corresponding applied identities were deliberately corrupted one at a time and rejected; wrong apply source was rejected before any overlay write, and wrong CLI/assembler/check target paths were rejected.',
 'Preserved equations 1-27 and old generated numerical appendix exactly, all ten old JSON artifacts and all three old figures byte for byte; complete PM supplement and two PM figures match sealed sources.',
 'Independently inspected Marcori arXiv:1805.12121v1 Eq.5.13 and response derivations: signed endpoint derivative formula, positive nearby limit, linear-response error bound, full-five sphere norm, ten-coordinate rank-five history image and non-gauge null distinction.',
 'Checked retained signed coefficient rows, eigenbasis and covariance identities, nonzero 5x6 and 5x97 signal-nuisance covariance, positive information loss, full 10x10 history blocks and five null directions, Gaussian threshold/power arithmetic and table radii.',
 'Deliberate swapped-profile, sign-loss, missing cross covariance, wrong nuisance-width, changed PM-figure and supplement mutations were rejected by the applied consumer.',
 'Actual rebuilt PDF has 24 pages and five figures, resolves Marcori citation and references, and has no TeX errors, missing files, undefined references/citations or overfull boxes; inspected pages 14-18 and confirmed text identity with sealed PDF.',
 'Figure 4 caption explicitly identifies evaluated markers, connecting segments as visual guides and exact 80-percent radii from the numerical table and Eq.35. No empirical power, matter-shear limit, posterior, family identification, native solver or original42 promotion is claimed.',
 'Preserved reviewer first absolute residual failure and diagnosed 9.940094969351776e-9 absolute versus 8.953126834247517e-11 relative full97 coefficient residual; manuscript six-decimal transcription unaffected and no frozen source/test/tolerance changed.',
 'Published separate source-bound CLAIM_LOCATOR_ERRATUM.json for historical C09-C11 section labels; the stale labels are not consumed by assembly/check/build and do not prevent the declared applied workflow.'
]
firsts=[OUT/'SCIENCE_CHECK_FIRST_FAILURE.txt',OUT/'check_retained_science_first.py',OUT/'FIRST_FAILURE_DIAGNOSIS.json']
raw=write('REVIEW_RAW_RECEIPT.json',{
 'schema':'htt.r36.independent_review_raw/1','agent_id':agent,'task_id':packet['task_id'],'input_identity':packet['input_identity'],'candidate_identity':identity,'requested_runtime':'gpt-6-astra/xhigh','observed_runtime':'UNKNOWN',
 'actual_consumer_receipt':bind(OUT/'RAW_RECEIPT.json'),'additional_executed_commands':bind(OUT/'ADDITIONAL_COMMANDS.json'),'actual_successful_workflow_commands':len(json.loads((OUT/'RAW_RECEIPT.json').read_text())['commands']),'additional_commands':len(json.loads((OUT/'ADDITIONAL_COMMANDS.json').read_text())),
 'first_failed_probe':{'command':[str(ROOT/'.venv/bin/python'),'-B',str(OUT/'check_retained_science.py')],'exit':1,'preserved':[bind(p) for p in firsts],'classification':'Reviewer diagnostic used an unscaled absolute cutoff for heterogeneous joint coefficients. Subsequent dimensionless residual is 8.95e-11. No candidate changes or threshold relaxation in production/source tests.'},
 'pdf_commands':[{'command':['pdftotext','-layout',str(CP/'report/main.pdf'),str(OUT/'sealed_candidate_pdf.txt')],'exit':0},{'command':['pdftoppm','-f','14','-l','17','-scale-to','1600','-png',str(OUT/'fixture/P4/report/main.pdf'),str(OUT/'page')],'exit':0},{'command':['pdftoppm','-f','18','-l','18','-scale-to','1600','-png',str(OUT/'fixture/P4/report/main.pdf'),str(OUT/'page')],'exit':0}],
 'retained_author_raw_receipt':bind(pathlib.Path('/mnt/extdrive/workdir/htt_open_data/r36_science_synthesis_repair_actual/RAW_RECEIPT.json')),
 'prior_author_failures_preserved':[bind(pathlib.Path('/mnt/extdrive/workdir/htt_open_data/r36_science_synthesis_repair_actual')/n) for n in ['first_assemble_failure.txt','second_assemble_failure.txt','postbuild_noop_first_failure.txt']],
 'production_tree_unchanged':True,'production_writes':0,'STATE_writes':0,'git_writes':0,'scientific_producer_runs':0,'old_P4_numerical_consumer_runs':0,'native_solver_runs':0,'ODE_runs':0,'children_spawned':0,
 'prior_synthesis_reviewer_verdict_file_read':False,'late_formal_packet_contains_historical_outcome':'Read only after independent workflow, science checks and no-blocker conclusion; no previous reviewer result file opened.',
 'actual_runtime_identity':'NOT_INDEPENDENTLY_OBSERVED','cumulative_token_usage':'UNKNOWN_NOT_EXPOSED','task_identity_reset':False
})
evidence=[OUT/'WORKFLOW_RESULT.json',OUT/'IDENTITY_CHECKS.json',OUT/'RETAINED_SCIENCE_CHECKS.json',OUT/'PDF_CHECKS.json',OUT/'CLAIM_LOCATOR_ERRATUM.json',OUT/'REVIEW_RAW_RECEIPT.json']
review={
 'schema':'htt.r36.independent_manuscript_review/1','reviewer_agent_id':agent,'task_id':packet['task_id'],'input_identity':packet['input_identity'],'candidate_identity':identity,'manifest':bind(CAND/'ARTIFACT_MANIFEST.json'),'candidate_return':bind(CAND/'RETURN.json'),'editor_contract':bind(pathlib.Path('/mnt/extdrive/workdir/htt_open_data/r36_science_synthesis_framing/EDITOR_CONTRACT.json')),
 'requested_runtime':'gpt-6-astra/xhigh','observed_runtime':'UNKNOWN','independence':{'authored_candidate':False,'contributed_to_candidate':False,'read_previous_synthesis_verdict':False,'no_children':True},
 'status':'SCOPED_PASS','outcome':'success','scoped_acceptance_met':True,'acceptance_scope':'Exact bounded P4 manuscript overlay integrating qualified pm_history_response; host production application remains a subsequent action.',
 'scientific_ceiling':'C0 CONDITIONAL. Full-five observable tensor and conditional working-design sensitivity only; no empirical matter-shear or original42 acceptance promotion.',
 'reviewed_products':['observable_bridge_manuscript_update'],'blocking_findings':[],
 'nonblocking_findings':[{'id':'R36-11-N1','severity':'LOW','classification':'packaging/provenance locator','files':['candidate/R32-06-P4-DESIGN/science/CLAIM_SOURCE_MAP.md:15','candidate/R32-06-P4-DESIGN/report/CLAIM_SOURCE_MAP.md:15'],'exact_fields':'P4-C09, P4-C10, P4-C11 Claim and manuscript location column (lines 15-17 in both maps)','finding':'Historical section-7 locators are stale after section insertion. C09/C10 are now section 8; C11 administrative no-promotion claim lives in RESULT/contract rather than manuscript physics prose.','consumer_impact':'No impact on actual assembly/check/build; section labels are not parsed. Exact new source, number, code, supplement and figure locators resolve.','disposition':'Outer erratum supplied without editing frozen candidate. Include alongside published source/PDF.', 'erratum':bind(OUT/'CLAIM_LOCATOR_ERRATUM.json')}],
 'review_views':{
  'relativistic_cosmology':'Marcori Eq.5.13 sign/c restoration matches Eq29; Eq30 follows integral remainder bound; fixed-axis/comoving/nonrotating and first-order domains explicit; no matter-frame calibration implied.',
  'statistical_inference':'Same selected realization and G/b; six common versus all97 nuisance; complete covariance/cross covariance retained; Gaussian size/power explicitly stipulated; no selected-field empirical p-value or posterior claim.',
  'numerical_methods':'Retained products and extraction arithmetic agree; five tensor coordinates and rank/null metadata checked algebraically; first unscaled reviewer diagnostic failure preserved and normalized interpretation explicit.',
  'software_reproducibility':'Unchanged actual apply function and runnable post-apply assembly/check/build succeed; wrong source/path/number/figure guards fail closed; source overlay idempotent after PDF build.',
  'claim_editor':'New results, two plots, full supplement and physical explanation integrated into the complete existing P4 manuscript; original equations/numbers preserved; unknown x,Q,Pi,F,G_F sectors not zero-filled.',
  'family_identification':'Full10 latent domain remains enlarged kinematic response and is not a dynamical family selector. Common-endpoint coordinate freedom is distinguished from unresolved history directions.'},
 'minimal_publishable_claim':'Under the declared first-order fixed-axis kinematic response and stipulated Gaussian catalogue design, a full five-component common PM tensor is estimable under both nuisance profiles while its ten-coordinate endpoint/derivative history retains five null directions; the stated radius thresholds are conditional design sensitivities.',
 'novelty':'NOT_ASSESSED beyond the retained sources; no priority claim.',
 'validation_evidence':validation,'evidence':[bind(p) for p in evidence],
 'raw_receipt':str(raw),'build_status':'PASS; 24 pages, 5 figures','latex_nonblocking_warnings':pdf['other_warnings'],
 'remaining_scientific_limits':['Physical source-dependent distance/history law absent','Optical-centroid-to-matter response absent','Empirical spatial covariance/selection and frame calibration not qualified','No independent physical history/ODE/native transfer or family identification'],
 'kill_switches':['Any exact candidate/source identity change requires changed-scope review','Do not interpret plotted polygon crossings as evaluated 80-percent thresholds','Do not promote this product to original42 or full manuscript-submission readiness'],
 'proposed_changes':'No candidate edits required for this scope; consume the outer locator erratum in packaging.',
 'production_application':'PENDING_ROOT_PUBLISHER','controller_state_writes':False,'original42_promotion':False,'journal_submission_authorized':False
}
rp=write('REVIEW_RESULT.json',review)
seal=write('REVIEW_SEAL.json',{'schema':'htt.r36.independent_review_seal/1','candidate_identity':identity,'review_result':bind(rp),'raw_receipt':bind(raw),'evidence':[bind(p) for p in evidence],'first_failures':[bind(p) for p in firsts],'reviewer':agent,'requested_runtime':'gpt-6-astra/xhigh','observed_runtime':'UNKNOWN'})
formalraw=write('formal_binding_01/RAW_BINDING_RECEIPT.json',{
 'schema':'htt.r36.actual_independent_review_binding/1','packet_id':packet['packet_id'],'task_id':packet['task_id'],'input_identity':packet['input_identity'],'candidate_identity':identity,'agent_id':agent,
 'packet':bind(packetpath),'actual_ack':bind(ackpath),'review_result':bind(rp),'review_seal':bind(seal),'actual_review_raw':bind(raw),'binding_created_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),
 'binding_operation':'Bind this same completed independent actual-consuming review to the selected and acknowledged formal packet. No rerun, candidate change or task/cost reset. Parent remains sole STATE writer.',
 'requested_runtime':'gpt-6-astra/xhigh','observed_runtime':'UNKNOWN','status':'SCOPED_PASS','acceptance_met':True,'qualified_products':['observable_bridge_manuscript_update'],'original42_promotion':False
})
ret=write('formal_binding_01/CONTROLLER_RETURN.json',{
 'packet_id':packet['packet_id'],'task_id':packet['task_id'],'input_identity':packet['input_identity'],'candidate_identity':identity,'agent_id':agent,'outcome':'success','status':'SCOPED_PASS','acceptance_met':True,
 'qualified_products':['observable_bridge_manuscript_update'],'qualification_status':'SCOPED_INDEPENDENT_REVIEW_PASS','validation_evidence':validation,'raw_receipt':str(formalraw),'review_result':bind(rp),'review_seal':bind(seal),'outer_locator_erratum':bind(OUT/'CLAIM_LOCATOR_ERRATUM.json'),
 'requested_runtime':'gpt-6-astra/xhigh','observed_runtime':'UNKNOWN','original42_promotion':False,'production_application':'PENDING_ROOT_PUBLISHER','scientific_scope':'C0 conditional observable/response/design manuscript integration only',
 'remaining_limits':review['remaining_scientific_limits'],'no_STATE_git_production_writes':True
})
write('formal_binding_01/SEAL.json',{'controller_return':bind(ret),'raw_binding_receipt':bind(formalraw),'review_result':bind(rp),'review_seal':bind(seal),'candidate_identity':identity})
print(json.dumps({'status':'SCOPED_PASS','review_result':bind(rp),'controller_return':bind(ret),'raw_binding_receipt':bind(formalraw),'outer_locator_erratum':bind(OUT/'CLAIM_LOCATOR_ERRATUM.json')},indent=2))
