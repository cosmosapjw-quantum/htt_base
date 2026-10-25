"""Extract a compact, read-only native control-consumption witness."""
from pathlib import Path
import hashlib,json
BASE=Path('/mnt/extdrive/workdir/htt_open_data')
ROOT=Path('/home/cosmosapjw/Dropbox/bianchi/htt_base')
OUT=BASE/'r26_post_gaia_publication_assembly'
def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
state_file=BASE/'r25_root_space_recovery/LIVE_STATE.json'
state_raw=state_file.read_bytes();state=json.loads(state_raw)
source=ROOT/'scripts/codex_harness/research_controller.py';test=ROOT/'scripts/codex_harness/test_research_controller_frontier.py'
expected_source='7516787e5b7fc777164d04276f1858e66070bd32ff111759d4646dc02169c819'
expected_test='b3e2f102da00e0dd1d7d97bb4a2f3ae9d7fecc713a40db0193110006ff71987a'
assert sha(source)==expected_source and sha(test)==expected_test
integration=BASE/'r25_root_space_recovery/receipts/REVIEW_SLOT_SOURCE_ACTUAL_INTEGRATION.json'
assert json.loads(integration.read_text())['status']=='EXACT_REVIEWED_SOURCE_TEST_INTEGRATED'
records={}
for key,expect in [('R25-GAIA-RELEASE-TAG-ASSOCIATION',('blocker',False,'3d2e96774c28cb5c3aa4d00757e022d61d1d696f50ff50e1b4dcdd31fc181793')),('R25-GAIA-SOURCE-QUOTIENT-CERTIFICATE',('success',True,'55e9d6bd8d9ca98d5736baf9327a51d00d8c01dac14fa8de63a26cb489022404'))]:
 task=state['tasks'][key]
 rows=[r for r in task.get('history',[]) if r.get('type')=='outcome' and r.get('phase')=='review']
 assert len(rows)==1
 row=rows[0];result=row['result']
 assert (result['outcome'],result['acceptance_met'],result['candidate_identity'].removeprefix('sha256:'))==expect
 packet=state['packets'][row['packet_id']]
 records[key]={'state_at_read':task['state'],'review_packet_id':row['packet_id'],'native_ack_agent_id':packet.get('agent_id'),'native_ack_launch_performed':packet.get('launch_performed'),'outcome':result['outcome'],'acceptance_met':result['acceptance_met'],'candidate_identity':result['candidate_identity'],'receipt_absolute':row['receipt']['path'],'receipt_sha256':row['receipt']['sha256'],'history_review_outcomes':len(rows)}
 assert packet.get('agent_id') and packet.get('launch_performed')
proof={'schema':'htt.compact_review_consumption_witness/1','status':'READ_ONLY_INSTANTANEOUS_STATE_WITNESS','observed_live_state_absolute':str(state_file),'observed_live_state_sha256':hashlib.sha256(state_raw).hexdigest(),'source_integration_receipt_absolute':str(integration),'source_integration_receipt_sha256':sha(integration),'installed_source_sha256':sha(source),'installed_test_sha256':sha(test),'records':records,'limits':['Read-only snapshot only; LIVE_STATE remains mutable','TAG blocker is consumed but later research packet may be planned','QUOTIENT scoped conditional PASS does not establish physical coverage','No scientific admission or publication follows from this witness']}
p=OUT/'CONTROL_CONSUMPTION_PROOF.json';p.write_text(json.dumps(proof,indent=2,sort_keys=True)+'\n')
print(json.dumps({'proof_sha256':sha(p),'source_sha256':proof['installed_source_sha256'],'test_sha256':proof['installed_test_sha256'],'outcomes':{k:(v['outcome'],v['acceptance_met'],v['state_at_read']) for k,v in records.items()}},sort_keys=True))
