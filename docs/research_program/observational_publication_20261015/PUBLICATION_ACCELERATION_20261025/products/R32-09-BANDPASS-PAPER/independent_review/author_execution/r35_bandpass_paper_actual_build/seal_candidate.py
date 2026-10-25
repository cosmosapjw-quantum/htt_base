from pathlib import Path
import hashlib,json,sys,copy
repo=Path('/home/cosmosapjw/Dropbox/bianchi/htt_base')
p=repo/'docs/research_program/observational_publication_20261015/PUBLICATION_ACCELERATION_20261025/products/R32-09-BANDPASS-PAPER'
ext=Path('/mnt/extdrive/workdir/htt_open_data/r35_bandpass_paper_actual_build')
packet=json.loads((p/'raw/NEXT_AFTER_BP_FINAL_REVIEW.json').read_text())
ack=json.loads((p/'raw/BANDPASS_PAPER_ACTUAL_ACK_GO.json').read_text())
exclusions={'ARTIFACT_MANIFEST.json','RESULT.json','CONTROLLER_RETURN.json'}
files=[]
for f in sorted(p.rglob('*')):
    if not f.is_file() or any(x in f.parts for x in ['__pycache__','.pytest_cache']):continue
    relative=str(f.relative_to(p))
    if relative in exclusions:continue
    files.append({'path':relative,'sha256':hashlib.sha256(f.read_bytes()).hexdigest(),'size_bytes':f.stat().st_size})
manifest={'artifact_root':str(p),'packet_id':packet['packet_id'],'task_id':packet['task_id'],'input_identity':packet['input_identity'],'phase':'execute','attempt':packet['attempt'],'files':files,'file_count':len(files),'claim_ceiling':'Conditional finite signed24 seven-passband bounded-moment manuscript candidate; no physical foreground, sky/noise, native-family or original42 admission','original42_acceptance':False,'independent_scientific_review':'PENDING_FRESH_ASTRA','qualified_products_semantics':'PROPOSED_PENDING_INDEPENDENT_REVIEW','excluded_outer_wrappers':['ARTIFACT_MANIFEST.json (self)','RESULT.json (binds this manifest)','CONTROLLER_RETURN.json (binds this manifest)'],'excluded_transient_directories':['__pycache__','.pytest_cache']}
mp=p/'ARTIFACT_MANIFEST.json';mp.write_text(json.dumps(manifest,indent=2)+'\n');identity='sha256:'+hashlib.sha256(mp.read_bytes()).hexdigest()
validation=[str(p/'raw/consumer_first.receipt.json'),str(p/'raw/pytest_sealed_source.receipt.json'),str(p/'raw/publication_final.receipt.json'),str(p/'raw/latexmk_final.receipt.json'),str(p/'BUILD_AUDIT.json'),str(p/'SOURCE_BINDINGS.json')]
result={'packet_id':packet['packet_id'],'task_id':packet['task_id'],'input_identity':packet['input_identity'],'agent_id':ack['agent_id'],'outcome':'success','acceptance_met':False,'original_acceptance_met':False,'qualified_products':['bandpass_manuscript'],'qualified_products_semantics':'PROPOSED_PENDING_INDEPENDENT_REVIEW','candidate_identity':identity,'candidate_manifest':str(mp),'raw_receipt':str(ext/'CONTROLLER_RAW_BINDING.json'),'validation_evidence':validation,'requested_runtime':packet['route']['requested'],'transport_selected_runtime':packet['route']['transport_selected'],'observed_runtime':'UNKNOWN','independent_scientific_review':'PENDING_FRESH_ASTRA','owner':'obsstat','claim_tier':'C0','transfer_source':'none','manuscript':str(p/'report/main.pdf'),'source_entrypoint':str(p/'report/main.tex'),'numerical_summary':json.loads((p/'report/generated/summary.json').read_text()),'build':json.loads((p/'BUILD_AUDIT.json').read_text()),'claim_ceiling':manifest['claim_ceiling']}
(p/'RESULT.json').write_text(json.dumps(result,indent=2)+'\n')
controller={k:v for k,v in result.items() if k not in {'numerical_summary','build'}}
(p/'CONTROLLER_RETURN.json').write_text(json.dumps(controller,indent=2)+'\n')
outer=dict(controller);outer['actual_raw_receipt']={'path':str(p/'RAW_RECEIPT.json'),'sha256':hashlib.sha256((p/'RAW_RECEIPT.json').read_bytes()).hexdigest()};outer['manifest_sha256']=identity.split(':')[1]
(ext/'CONTROLLER_RAW_BINDING.json').write_text(json.dumps(outer,indent=2)+'\n')
# Requested transition check is strictly in memory; no checkpoint/save call.
sys.path.insert(0,str(repo/'scripts/codex_harness'))
import research_controller as rc
state_path=repo/'.agent-harness/runtime/r23-continuous/STATE.json'
before=hashlib.sha256(state_path.read_bytes()).hexdigest()
state=copy.deepcopy(json.loads(state_path.read_text()))
policy=json.loads((repo/'docs/harness/NATIVE_ROUTING_POLICY_V1.json').read_text())
rc.record(state,controller,policy)
after=hashlib.sha256(state_path.read_bytes()).hexdigest()
check={'status':'MEMORY_ONLY_RECORD_PRECHECK_PASS','actual_state_written':False,'state_sha256_before':before,'state_sha256_after':after,'live_state_unchanged_during_check':before==after,'in_memory_task_phase':state['tasks'][packet['task_id']]['phase'],'in_memory_task_state':state['tasks'][packet['task_id']]['state'],'candidate_identity':identity}
(ext/'RECORD_PRECHECK.json').write_text(json.dumps(check,indent=2)+'\n')
print(json.dumps(check,indent=2));print('CONTROLLER_RETURN',str(p/'CONTROLLER_RETURN.json'));print('RESULT_SHA256',hashlib.sha256((p/'RESULT.json').read_bytes()).hexdigest())
