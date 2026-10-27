"""Bind this reviewer's sealed independent review to its acknowledged packet."""
from pathlib import Path
import datetime
import hashlib
import json
import sys

ROOT = Path('/home/cosmosapjw/Dropbox/bianchi/htt_base')
OUT = Path(__file__).resolve().parent
PREP = OUT.parent
BASE = ROOT/'docs/research_program/observational_publication_20261015/OBSERVABLE_BRIDGE_RECONCILIATION_20261027'
PRODUCT = BASE/'products/R36-01-CF4-OPERATOR'
PACKET = Path('/mnt/extdrive/workdir/htt_open_data/r36_controller/NEXT_010.json')
ACK = Path('/mnt/extdrive/workdir/htt_open_data/r36_controller/ACK_010_GO.json')
REVIEW = PREP/'REVIEW_RESULT.json'
PACKET_ID = '6a1d06c19d5c65bc02ba6520e7c23462848dac98798bc79c8edf0bb258c21172'
AGENT = '/root/r36_cf4_operator_fresh_review'
CANDIDATE = 'sha256:164f5f63084caaf4ca18062d314ef53cf4773c528e72333a6b6d24a7e4437b14'
INPUT = 'sha256:83ebf1cd2ce7ae18a486506219c0a93ec939a74cfa06c21a1316c938678f1c43'
REVIEW_SHA = 'abd68f67ce33ff6c64e38f525106bba4c9fa146f207af7d863721b66e1c11d06'
checks = []
def sha(path):
    with Path(path).open('rb') as f:
        return hashlib.file_digest(f,'sha256').hexdigest()
def digest(value):
    # Same serialized-object identity as research_controller.py:24-25.
    return hashlib.sha256(json.dumps(value,sort_keys=True,ensure_ascii=False).encode()).hexdigest()
def check(label, ok, **detail):
    record = {'check':label,'pass':bool(ok),**detail}
    print(json.dumps(record,allow_nan=False),flush=True)
    checks.append(record)
    if not ok:
        raise AssertionError(label)
def exact_file(label,path,expected):
    actual=sha(path)
    check(label,actual==expected,path=str(path),sha256=actual)

packet=json.loads(PACKET.read_text())
ack=json.loads(ACK.read_text())
review=json.loads(REVIEW.read_text())
assignment=json.loads(packet['spawn_args']['message'].split('Assignment:\n',1)[1])
check('actual_packet_and_assignment_binding',packet['packet_id']==assignment['packet_id']==PACKET_ID
      and packet['task_id']==assignment['task_id']=='R36-01-CF4-OPERATOR'
      and packet['phase']==assignment['phase']=='review'
      and packet['candidate_identity']==assignment['candidate_identity']==CANDIDATE
      and packet['input_identity']==assignment['input_identity']==INPUT)
check('actual_followup_ACK_GO',ack['packet_id']==PACKET_ID and ack['agent_id']==AGENT
      and ack['native_tool']=='collaboration.followup_task'
      and bool(ack['actual_followup_agent_ack']) and bool(ack['go']),
      ack_path=str(ACK),ack_sha256=sha(ACK),ack_payload_field=ack.get('ack'),
      evidence_scope='Actual same-agent followup was received; root supplied actual host ACK GO. Planned spawn_args are not dispatch evidence.')
check('requested_not_observed_runtime',packet['route']['requested']=={'model':'gpt-6-astra','effort':'xhigh'}
      and ack['requested_runtime']=='gpt-6-astra/xhigh' and ack['observed_runtime']=='UNKNOWN')
frontier=json.loads((BASE/'FRONTIER.json').read_text())
current_spec=next(t for t in frontier['tasks'] if t['id']=='R36-01-CF4-OPERATOR')
check('unchanged_task_contract',current_spec==assignment['spec']
      and digest(current_spec)==packet['task_spec_identity'],task_spec_identity=digest(current_spec))
check('frontier_identity',digest(frontier)==packet['frontier_identity'],frontier_identity=digest(frontier))
check('independent_same_reviewer',AGENT==review['reviewer_agent_id']
      and AGENT not in assignment['authors'] and AGENT not in assignment['contributors']
      and review['independence']['reviewer_authored_product_or_contract'] is False,
      authors=assignment['authors'],contributors=assignment['contributors'])
exact_file('sealed_review_unchanged',REVIEW,REVIEW_SHA)
check('sealed_PASS_same_scope',review['verdict']=='PASS'
      and review['candidate_identity']==CANDIDATE and review['input_identity']==INPUT
      and review['findings']==[] and assignment['spec']['qualified_product_expected']=='h03_exact_operator'
      and assignment['spec']['promotes_original_acceptance'] is False)
exact_file('candidate_manifest_unchanged',PRODUCT/'ARTIFACT_MANIFEST.json',CANDIDATE.split(':')[1])
exact_file('input_manifest_unchanged',BASE/'EVIDENCE_MANIFEST.json',INPUT.split(':')[1])
manifest=json.loads((PRODUCT/'ARTIFACT_MANIFEST.json').read_text())
for entry in manifest['files']+manifest['evidence_logs']:
    exact_file('candidate_content:'+Path(entry['path']).name,entry['path'],entry['sha256'])
    check('candidate_size:'+Path(entry['path']).name,Path(entry['path']).stat().st_size==entry['bytes'])
contract_path=Path(review['contract_path'])
exact_file('execution_contract_unchanged',contract_path,review['contract_sha256'])
contract=json.loads(contract_path.read_text())
for name,entry in contract['source_bindings'].items():
    exact_file('frozen_source:'+name,ROOT/entry['path'],entry['sha256'])
for entry in review['evidence']:
    exact_file('retained_review_evidence:'+Path(entry['path']).name,entry['path'],entry['sha256'])
for entry in assignment['history_refs']:
    exact_file('implementation_raw_receipt',entry['receipt']['path'],entry['receipt']['sha256'])
    check('implementation_history_same_candidate',entry['candidate_identity']==CANDIDATE
          and entry['packet_id']==review['implementation_packet_id'])
raw_checks=json.loads((PREP/'NUMERICAL_CHECKS.json').read_text())
raw_commands=json.loads((PREP/'RAW_REVIEW_RECEIPT.json').read_text())
check('retained_actual_76checks_PASS',raw_checks['summary']=={'checks_passed':76,'checks_failed':0}
      and len(raw_checks['checks'])==76 and all(c['pass'] for c in raw_checks['checks']))
check('retained_actual_consumer_and_falsifier',[(c['name'],c['exit_status'],c['expected_outcome_matched'])
      for c in raw_commands['commands']]==[('independent_numerics',0,True),('actual_consumer',0,True),('permuted_id_consumer',1,True)])

binding={'schema':'htt.r36.formal_review_identity_binding/1','packet_id':PACKET_ID,
         'task_id':'R36-01-CF4-OPERATOR','input_identity':INPUT,'candidate_identity':CANDIDATE,
         'agent_id':AGENT,'verdict':'PASS','checks':checks,
         'prior_independent_review':{'path':str(REVIEW),'sha256':REVIEW_SHA},
         'packet':{'path':str(PACKET),'sha256':sha(PACKET)},
         'host_ACK_GO':{'path':str(ACK),'sha256':sha(ACK)},
         'adoption':'Same actual reviewer adopts its unchanged sealed independent review; all reviewed candidate/source/raw evidence bytes rechecked. No new numerical run or broader scientific claim.',
         'requested_runtime':'gpt-6-astra/xhigh','observed_runtime':'UNKNOWN',
         'scientific_scope':'h03_exact_operator under fixed d,w,n working law; no physical42/native/matter proof or original42 promotion.'}
(OUT/'IDENTITY_BINDING.json').write_text(json.dumps(binding,indent=2,allow_nan=False)+'\n')
print(json.dumps({'binding_checks_passed':len(checks),'binding_checks_failed':0,'verdict':'PASS'}),flush=True)
