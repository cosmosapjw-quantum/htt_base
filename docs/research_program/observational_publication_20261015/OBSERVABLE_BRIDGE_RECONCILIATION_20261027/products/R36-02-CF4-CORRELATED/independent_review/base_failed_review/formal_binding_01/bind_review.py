"""Bind this reviewer's existing sealed negative review; no numerical execution."""
import hashlib
import json
from pathlib import Path
import sys
import time

start=time.monotonic()
here=Path(__file__).resolve().parent
repo=Path('/home/cosmosapjw/Dropbox/bianchi/htt_base')
root=repo/'docs/research_program/observational_publication_20261015/OBSERVABLE_BRIDGE_RECONCILIATION_20261027'
product=root/'products/R36-02-CF4-CORRELATED'
external=Path('/mnt/extdrive/workdir/htt_open_data/r36_cf4_correlated_actual')
controller=Path('/mnt/extdrive/workdir/htt_open_data/r36_controller')
review_path=here.parent/'REVIEW_RESULT.json'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
load=lambda p:json.loads(p.read_text())
dump=lambda p,obj:p.write_text(json.dumps(obj,indent=2)+'\n')
packet=load(controller/'NEXT_019.json')
ack=load(controller/'ACK_019_GO.json')
review=load(review_path)
agent='/root/r36_cf4_correlated_independent_review'
assert packet['packet_id']=='3a407e2341438efb5ce53700b0ff5cd941a966baef6f44e6c171aa06e8f2b1fc'
assert ack['packet_id']==packet['packet_id'] and ack['agent_id']==agent
assert ack['actual_tool_accepted'] is True and ack['ACK'] is True and ack['GO'] is True
assert ack['native_tool']=='collaboration.followup_task'
assert sha(review_path)=='c6db02c8ed7c0b73bdb56dc6a8e1bc77737e79ea7e752197f90d5c97c4d76b98'
assert packet['candidate_identity']==review['candidate_identity']=='sha256:'+sha(product/'ARTIFACT_MANIFEST.json')
assert packet['input_identity']==review['input_identity']=='sha256:'+sha(root/'EVIDENCE_MANIFEST.json')
assert packet['task_id']==review['task_id']=='R36-02-CF4-CORRELATED'
verified=[]
def verify(path,expected):
    observed=sha(path)
    assert observed==expected,(str(path),observed,expected)
    verified.append({'path':str(path),'sha256':observed,'bytes':path.stat().st_size})
manifest=load(product/'ARTIFACT_MANIFEST.json')
for key,base in [('product_files',product),('external_files',external)]:
    for name,b in manifest[key].items():
        verify(base/name,b['sha256'])
        assert (base/name).stat().st_size==b['bytes']
contract_path=Path('/mnt/extdrive/workdir/htt_open_data/r36_scientific_contract_preparation/R36-02.json')
verify(contract_path,review['frozen_contract_sha256'])
for b in load(contract_path)['source_bindings'].values():
    verify(repo/b['path'],b['sha256'])
verify(Path('/mnt/extdrive/workdir/htt_open_data/r36_cf4_exact_operator_actual/A_RAW_36x35970.npz'),manifest['source_identity']['operator_artifact_sha256'])
verify(repo/'docs/research_program/theory_obs_application_20261015/loop6_kinematics/results/cf4_rawgroup_appHubble_STF2_pooled_methods_v2/selected_source_observables.npz',manifest['source_identity']['selected_source_sha256'])
old=repo/'docs/research_program/observational_publication_20261015/EXTERNAL_AUDIT_20261025_R35/CF4_FINITE_COMPONENT/sources/r30_cf4_pv_tensor_numeric/fast_window_fixture_repair/science.py'
verify(old,load(here.parent/'INDEPENDENT_CHECKS.json')['environment']['imported_science_sha256'])
common={'packet_id':packet['packet_id'],'task_id':packet['task_id'],'input_identity':packet['input_identity'],
        'agent_id':agent,'candidate_identity':packet['candidate_identity'],
        'requested_runtime':'gpt-6-astra/xhigh','observed_runtime':'UNKNOWN'}
raw_path=here/'RAW_BINDING_RECEIPT.json'
raw={'schema':'htt.r36.unchanged_review_binding_receipt/1',**common,
     'command':[sys.executable,'-B',str(Path(__file__).resolve())],
     'cwd':str(Path.cwd()),'exit_code':0,'elapsed_seconds':time.monotonic()-start,
     'operation':'Identity checks and formal binding of this reviewer existing unchanged negative review.',
     'ack':{'path':str(controller/'ACK_019_GO.json'),'sha256':sha(controller/'ACK_019_GO.json'),'native_tool':ack['native_tool'],'actual_tool_accepted':True},
     'packet':{'path':str(controller/'NEXT_019.json'),'sha256':sha(controller/'NEXT_019.json')},
     'original_review':{'path':str(review_path),'sha256':sha(review_path),'verdict':review['verdict']},
     'verified_current_files':verified,'identity_check':'PASS',
     'numerical_commands_started':0,'full_review_rerun':False,'old_R30_bank_rerun':False,
     'repository_writes':False,'source_candidate_edits':False,'state_or_git_edits':False,
     'original_review_unchanged':True,'timestamp_unix':time.time()}
dump(raw_path,raw)
finding=review['findings'][0]
ret={'schema':'htt.r36.controller_review_return/1',**common,
     'outcome':'blocker','acceptance_met':False,'qualified_products':[],
     'status':'HOLD_TARGETED_REPAIR_REQUIRED','verdict':'HOLD',
     'review_binding':'FORMAL_PACKET_BOUND_EXISTING_OWN_INDEPENDENT_REVIEW',
     'original_review_path':str(review_path),'original_review_sha256':sha(review_path),
     'issue':{'class':'code',
              'question':'Do footprint/method sensitivity summaries compare subset and full-sample covariance at the same smoothing radius?',
              'exact_missing_or_defect':finding['mechanism'],
              'input_identity':packet['input_identity']},
     'findings':review['findings'],'counterexample':review['counterexample'],
     'repair_plan':review['repair_plan'],
     'positive_checks_preserved':review['successful_checks'],
     'statistical_limits':review['statistical_limits'],
     'original42_promotion':False,'science_admission':False,
     'validation_evidence':[str(review_path),str(raw_path),str(here.parent/'INDEPENDENT_CHECKS.json'),
          str(here.parent/'ADDITIONAL_STATISTICAL_CHECKS.json'),str(here.parent/'bridge_tests_receipt.json'),
          str(here.parent/'sensitivity_falsifier_receipt.json')],
     'raw_receipt':str(raw_path),
     'next_transition':'Controller records this negative review and dispatches the same-task bounded cache-only sensitivity-summary repair. Preserve existing matrices, numerical criteria, cumulative accounting and scientific ceilings.'}
assert isinstance(ret['issue']['exact_missing_or_defect'],str)
assert isinstance(ret['counterexample'],dict) and isinstance(ret['repair_plan'],str)
assert all(isinstance(x,str) for x in ret['validation_evidence'])
assert Path(ret['raw_receipt']).is_absolute()
dump(here/'CONTROLLER_RETURN.json',ret)
print(json.dumps({'return_path':str(here/'CONTROLLER_RETURN.json'),
                  'return_sha256':sha(here/'CONTROLLER_RETURN.json'),
                  'raw_receipt':str(raw_path),'raw_sha256':sha(raw_path),
                  'outcome':ret['outcome'],'verified_files':len(verified)}))
