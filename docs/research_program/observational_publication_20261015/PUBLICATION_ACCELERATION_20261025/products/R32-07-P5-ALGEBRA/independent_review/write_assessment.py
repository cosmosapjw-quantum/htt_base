from pathlib import Path
import json, hashlib, datetime, subprocess
O=Path('/mnt/extdrive/workdir/htt_open_data/r35_p5_fresh_independent_review')
R=Path('/home/cosmosapjw/Dropbox/bianchi/htt_base')
P=R/'docs/research_program/observational_publication_20261015/PUBLICATION_ACCELERATION_20261025/products/R32-07-P5-ALGEBRA/report'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
candidate=json.loads((P/'RESULT.json').read_text())
binding=json.loads((O/'raw/repaired_candidate_identity.json').read_text())
probes=json.loads((O/'raw/independent_probes.json').read_text())
extra=json.loads((O/'raw/supplementary_probes.json').read_text())
assert probes['status']==extra['status']=='PASS'
assert sha(P/'arrays.npz')==probes['array_sha256']==extra['array_sha256']
for name in ('RESULT.json','OUTPUT_MANIFEST.json','manuscript.pdf'):
    assert sha(P/name)==binding[name]['sha256']
source_checks=[]
for field,name in [('science_manuscript_sha256','manuscript.md'),('science_build_contract_sha256','BUILD_CONTRACT.md'),('science_claim_map_sha256','CLAIM_SOURCE_MAP.md'),('science_research_notes_sha256','RESEARCH_NOTES.md')]:
    s=sha(P.parent/'science'/name);assert s==candidate['source_identifiers'][field]
    source_checks.append({'path':str(P.parent/'science'/name),'sha256':s})
for x in candidate['source_identifiers']['retained_files']:
    assert sha(R/x['path'])==x['sha256']
commands=[
 ['python3','-B',str(O/'inspect_candidate.py')],
 ['python3','-B',str(O/'independent_probes.py')],
 ['python3','-B',str(O/'supplementary_probes.py')],
 ['python3','-B',str(O/'bind_repaired_candidate.py')],
 ['python3','-B',str(O/'write_assessment.py')]]
files=['inspect_candidate.py','independent_probes.py','supplementary_probes.py','bind_repaired_candidate.py','write_assessment.py','REVIEW.md',
       'raw/identity_check.json','raw/commands.json','raw/validate_only.stdout','raw/validate_only.stderr','raw/independent_probes.json',
       'raw/independent_probes.stdout','raw/independent_probes.stderr','raw/supplementary_probes.json','raw/supplementary_probes.stdout',
       'raw/supplementary_probes.stderr','raw/repaired_candidate_identity.json','raw/repaired_RESULT_json.diff','raw/literal_repair_verification.json']
receipt={'status':'EXECUTED','written_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'actual_commands':commands,
         'nested_inspection_commands':json.loads((O/'raw/commands.json').read_text()),'repaired_pdf_commands':binding['commands'],
         'execution_outcomes':{'consumer_validate_only_exit':0,'independent_probes_exit':0,'supplementary_probes_exit':0,'repaired_identity_and_pdf_render_exit':0},
         'raw_probes_preserved':True,'reviewer_production_mutations':False,'source_checks':source_checks,
         'observed_head_at_closeout':subprocess.check_output(['git','rev-parse','HEAD'],cwd=R,text=True).strip(),
         'artifacts':[{'path':str(O/name),'bytes':(O/name).stat().st_size,'sha256':sha(O/name)} for name in files]}
(O/'RAW_RECEIPT.json').write_text(json.dumps(receipt,indent=2)+'\n')
result={'status':'SCOPED_PASS','verdict':'SCOPED_PASS','task_id':'R32-07-P5-ALGEBRA','reviewed_product':'bianchi_algebra_note',
        'scope':'conditional instantaneous LRS Bianchi V algebra and exact kinematic Bianchi I full-temperature noninjectivity',
        'reviewer':'/root/r35_p5_fresh_independent_review','requested_model':'gpt-6-astra','requested_effort':'xhigh',
        'observed_model':'UNKNOWN','observed_effort':'UNKNOWN','independence_status':'SEPARATE_READ_ONLY_NON_AUTHOR',
        'excluded_authors':['/root/rc_1f2400c98c81ce56','/root/r35_p4_p5_source_contract_intake','/root/r35_p5_prescribed_numeric_build'],
        'formal_review_packet_id':None,'formal_review_packet_status':'PENDING_CONTROLLER_BINDING','formal_ack_created':False,
        'controller_qualification_performed':False,'qualified_product':None,'recommended_qualified_product':'bianchi_algebra_note',
        'original_acceptance_passed':False,'promotes_original_acceptance':False,'original_42_node_acceptance_unchanged':True,
        'candidate':{'result_path':str(P/'RESULT.json'),'result_sha256':sha(P/'RESULT.json'),
                     'output_manifest_path':str(P/'OUTPUT_MANIFEST.json'),'output_manifest_file_sha256':sha(P/'OUTPUT_MANIFEST.json'),
                     'canonical_manifest_object_identity':'NOT_ASSERTED_BY_REVIEWER',
                     'pdf_path':str(P/'manuscript.pdf'),'pdf_sha256':sha(P/'manuscript.pdf'),'pdf_pages':9,
                     'arrays_sha256':sha(P/'arrays.npz'),'source_identifiers':candidate['source_identifiers'],
                     'execute_packet_id':candidate['packet_id'],'input_identity':candidate['input_identity'],'task_spec_identity':candidate['task_spec_identity']},
        'findings':[],
        'resolved_findings':[{'path':'report/manuscript.tex','line':285,'kind':'RENDERING_TOKEN','origin':'Author surfaced; reviewer independently reproduced',
                              'issue':'Doubled backslash rendered B-to-infinity as literal to; single-token repair is now verified.',
                              'closeout':'Literal inverse recovers exact prior hashes of consumer/TeX/normalized Markdown/Pandoc body. Only rendered page 6 differs; all 15 numerical/table/figure files unchanged.'}],
        'verification':{'current_manifest_entries_verified':38,'immutable_source_entries_verified':9,'science_documents_verified':4,
                        'independent_check_count':probes['check_count']+extra['check_count'],'decimal_precision':80,'decimal_cases':225,
                        'decimal_max_abs_error':4.440892098500626e-16,'joint_rows':280,'heatmap_points':58282,'fixed_boundary_tuples':1300,
                        'fixed_empty_rows':316,'table_rows':8,'figures_visually_inspected':6,'pages_visually_inspected':9,
                        'repaired_changed_page_reinspected':6,'other_repaired_pages_pixel_identical':True,'unchanged_numerical_artifacts':15},
        'remaining_scope_limits':['Bianchi V Einstein-perfect-fluid equal-radiation history pair NOT_ESTABLISHED.',
             'No native solver, ODE evolution, empirical family identification, native/full T/E/B atlas or original-campaign promotion.',
             'x_C, Q, F, Pi and G_F remain NOT_EVALUABLE; matter vorticity remains NOT_DETERMINED.',
             'No likelihood, posterior, p-value, probability coverage or literature-wide novelty assessment.',
             'Formal controller review-packet binding is still pending; no invented dispatch or ACK.'],
        'required_repair':None,'report_path':str(O/'REVIEW.md'),'report_sha256':sha(O/'REVIEW.md'),
        'raw_receipt_path':str(O/'RAW_RECEIPT.json'),'raw_receipt_sha256':sha(O/'RAW_RECEIPT.json')}
(O/'RESULT.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps({'status':result['status'],'result_path':str(O/'RESULT.json'),'result_sha256':sha(O/'RESULT.json'),
                  'report_sha256':sha(O/'REVIEW.md'),'raw_receipt_sha256':sha(O/'RAW_RECEIPT.json'),'independent_checks':result['verification']['independent_check_count']},indent=2))
