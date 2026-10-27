from pathlib import Path
import json,hashlib,datetime
P=Path('/mnt/extdrive/workdir/htt_open_data/r36_optical_repair_independent_review')
B=P/'formal_binding_01'
R=Path('/home/cosmosapjw/Dropbox/bianchi/htt_base')
packet_path=Path('/mnt/extdrive/workdir/htt_open_data/r36_controller/NEXT_025.json')
ack_path=Path('/mnt/extdrive/workdir/htt_open_data/r36_controller/ACK_025_GO.json')
review_path=P/'REVIEW_RESULT_002_NORM_BOUND.json'
raw_preimage_path=P/'RAW_RECEIPT_002_NORM_BOUND.json'
seal_path=P/'SEAL_002_NORM_BOUND.json'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def rec(p):p=Path(p);return {'path':str(p),'sha256':sha(p),'bytes':p.stat().st_size}
def save(p,v):
 with p.open('x') as f:f.write(json.dumps(v,indent=2,allow_nan=False)+'\n')
packet=json.loads(packet_path.read_text());ack=json.loads(ack_path.read_text());review=json.loads(review_path.read_text());seal=json.loads(seal_path.read_text())
assert packet['packet_id']=='e50bbc39710fc88bcbd25c3b365936cb11ceaaf7016a9c775898f370b80789cd'
assert ack['packet_id']==packet['packet_id'] and ack['agent_id']=='/root/r36_optical_repair_independent_review' and ack['acknowledged'] is True
assert sha(review_path)=='f7cbeb7aada2f52593b826fcc20cbcef7d65e373fce0f11bf390eaf6df7d6fca'
assert sha(raw_preimage_path)=='03a9eb571c4ed201d05eae76246601933994edc65cd20bf4c67a15b6ae6e1f72'
assert packet['candidate_identity']==review['candidate_identity']=='sha256:193630441180a6a38d856442c7b7fe2e9c322032842ce72b07aace9211fef8e0'
assert packet['input_identity']==review['input_identity']=='sha256:83ebf1cd2ce7ae18a486506219c0a93ec939a74cfa06c21a1316c938678f1c43'
assert packet['task_id']==review['task_id']=='R36-04-OPTICAL-JOINT'
for key in ('review_result','raw_receipt','norm_bound_contract','previous_seal','revision_script'):
 v=seal[key];assert sha(v['path'])==v['sha256'] and Path(v['path']).stat().st_size==v['bytes']
cand=Path(review['candidate_manifest']['path']);assert 'sha256:'+sha(cand)==packet['candidate_identity']
manifest=json.loads(cand.read_text());candidate_checks=[]
for key,v in manifest['candidate_files'].items():
 actual=rec(v['path']);assert actual['sha256']==v['sha256'] and actual['bytes']==v['bytes'];candidate_checks.append({'file':key,**actual,'match':True})
source=R/'docs/research_program/observational_publication_20261015/OBSERVABLE_BRIDGE_RECONCILIATION_20261027/EVIDENCE_MANIFEST.json'
assert 'sha256:'+sha(source)==packet['input_identity']
identity={k:packet[k] for k in ('campaign','task_id','attempt','phase','packet_id','input_identity','candidate_identity','frontier_identity','task_spec_identity')}
raw={**identity,'schema':'htt.r36.formal_review_binding_raw_receipt/1','agent_id':ack['agent_id'],'reviewer_agent_id':ack['agent_id'],'author_agent_id':review['author_agent_id'],'outcome':'blocker','substantive_failure':True,'acceptance_met':False,'qualified_products':[],'requested_runtime':review['requested_runtime'],'observed_runtime':'UNKNOWN','binding_kind':'SAME_AGENT_UNCHANGED_PREPARED_NEGATIVE_REVIEW','packet':rec(packet_path),'actual_host_ack':rec(ack_path),'host_go':'Explicit parent message authorizes binding after ACK_025_GO.json; no controller state write by reviewer.','original_review':rec(review_path),'original_raw_receipt':rec(raw_preimage_path),'original_seal':rec(seal_path),'norm_bound_contract':rec(P/'NORM_BOUND_CONTRACT.json'),'candidate_manifest':rec(cand),'candidate_file_checks':candidate_checks,'source_manifest':rec(source),'new_numerical_execution':False,'new_scientific_review':False,'historical_failures_preserved':True,'read_only_repository':True,'controller_state_written':False,'git_changes':False,'binding_script':rec(B/'bind_review.py'),'timestamp_utc':datetime.datetime.now(datetime.timezone.utc).isoformat()}
save(B/'RAW_BINDING_RECEIPT.json',raw)
result={**identity,'schema':'htt.r36.formal_review_controller_return/1','agent_id':ack['agent_id'],'reviewer_agent_id':ack['agent_id'],'author_agent_id':review['author_agent_id'],'outcome':'blocker','substantive_failure':True,'substantive':True,'acceptance_met':False,'qualified_products':[],'qualification_status':'NOT_QUALIFIED_NEGATIVE_INDEPENDENT_REVIEW','scoped_verdict':'HOLD','requested_runtime':review['requested_runtime'],'observed_runtime':'UNKNOWN','raw_receipt':str(B/'RAW_BINDING_RECEIPT.json'),'bound_original_review':rec(review_path),'bound_original_raw_receipt':rec(raw_preimage_path),'bound_original_seal':rec(seal_path),'binding_kind':'SAME_AGENT_UNCHANGED_PREPARED_NEGATIVE_REVIEW','issue_class':'numeric','issue':review['issue'],'counterexample':review['counterexample'],'repair_plan':review['repair_plan'],'norm_bound_contract':rec(P/'NORM_BOUND_CONTRACT.json'),'finding_ids':[f['id'] for f in review['findings']],'validation':['Actual ACK_025_GO.json identifies this same reviewer and exact packet; explicit host GO received.','Original review/raw/seal/norm-contract bytes match the completed preparatory review.','Current candidate manifest, all 10 candidate files and frozen input manifest match the formal packet.','RF1 false rejection, RF2 false acceptance and RF3 nonfinite result remain the unchanged negative review findings; all existing focused tests and numerical evidence are reused.','Prospective repair framing did not implement or author this assessed candidate. Requested gpt-6-astra/xhigh; observed runtime UNKNOWN.','No scientific rerun, original acceptance promotion, qualification, publication, production edit or controller state write.'],'validation_evidence':[str(P/'PYTEST.stdout'),str(P/'INITIAL_COUNTEREXAMPLES.json'),str(P/'EXTREME_RATIO_INTERVAL_COUNTEREXAMPLES.json'),str(P/'FINAL_CHECKS.json'),str(P/'NORM_BOUND_CONTRACT.json'),str(ack_path)],'new_numerical_execution':False,'new_scientific_review':False}
assert result['issue']['class']=='numeric'
assert all(result['issue'].get(k) for k in ('question','exact_missing_or_defect','input_identity'))
assert isinstance(result['counterexample'],dict) and isinstance(result['repair_plan'],str)
save(B/'CONTROLLER_RETURN.json',result)
assert result['counterexample']==review['counterexample'] and result['repair_plan']==review['repair_plan'] and result['issue']==review['issue']
assert sha(review_path)=='f7cbeb7aada2f52593b826fcc20cbcef7d65e373fce0f11bf390eaf6df7d6fca'
seal_result={'schema':'htt.r36.formal_review_binding_seal/1','controller_return':rec(B/'CONTROLLER_RETURN.json'),'raw_receipt':rec(B/'RAW_BINDING_RECEIPT.json'),'original_review':rec(review_path),'candidate_manifest':rec(cand),'new_numerical_execution':False}
save(B/'SEAL.json',seal_result)
print(json.dumps(seal_result,indent=2))
