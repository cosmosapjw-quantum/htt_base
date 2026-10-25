"""One bounded independent metadata-only audit; all mutable fixtures are below HERE."""
import copy
import hashlib
import json
import sys
from pathlib import Path
HERE = Path('/mnt/extdrive/workdir/htt_open_data/r29_controller_candidate_blind_audit')
REPO = Path('/home/cosmosapjw/Dropbox/bianchi/htt_base')
sys.path.insert(0, str(REPO/'scripts/codex_harness'))
import research_controller as rc
policy = rc.load_policy()
profiles = {(v['requested']['model'],v['requested']['effort']) for v in policy['routes'].values()}
results = {}

def write(name, value):
    p=HERE/name
    p.write_text(json.dumps(value,indent=2)+'\n')
    return str(p)

def state(name):
    return rc.initialize({'campaign_id':'INDEPENDENT-METADATA-FIXTURE-'+name,'tasks':[{'id':'A','goal':'metadata fixture','acceptance':'metadata fixture only','kind':'code','input_identity':'frozen-fixture-input','owned_paths':[str(HERE/'candidate')]}]}, 'metadata fixture only; no dispatch')

def launch(s,agent):
    p=rc.next_packet(s,policy,profiles)
    rc.acknowledge(s,p['packet_id'],agent)
    return p

def outcome(s,p,agent,**kwargs):
    r={'packet_id':p['packet_id'],'task_id':'A','agent_id':agent,'input_identity':p['input_identity'],**kwargs}
    r['raw_receipt']=write('raw-'+p['packet_id']+'.json',r)
    rc.record(s,r,policy)
    return r

# Case 1: exact production topology in disposable tiny files, no production save.
target=HERE/'external-state.json'; alias=HERE/'STATE-link.json'
target.write_text('{"generation":1}\n')
alias.symlink_to(target)
rc.save(alias,{'generation':2})
results['symlink_save']={'link_preserved':alias.is_symlink(),'original_target':json.loads(target.read_text()),'supplied_path':json.loads(alias.read_text())}

# Case 2: first author reports controls failed; research author returns legitimate plan.
for plan in ({'repair':'fix the failed initial control'},'Fix the failed initial control'):
    kind=type(plan).__name__
    s=state('initial-failure-'+kind)
    p=launch(s,'fixture-author')
    outcome(s,p,'fixture-author',outcome='blocker',issue={'class':'code','question':'Why does first control fail?','exact_missing_or_defect':'initial test fixture mismatch','input_identity':p['input_identity']})
    research=launch(s,'fixture-research')
    outcome(s,research,'fixture-research',outcome='success',repair_plan=plan)
    repair=rc.next_packet(s,policy,profiles)
    data={'status':'dispatched','native_tool':'collaboration.followup_task','task_id':'A','agent_id':'fixture-author','phase':'repair','packet_id':repair['packet_id'],'input_identity':repair['input_identity'],'repair_plan_identity':rc.digest(plan),'base_packet_id':p['packet_id'],'base_candidate_identity':'NO_SUCCESSFUL_CANDIDATE_EXISTS','requested':repair['route']['requested'],'transport_selected':repair['route']['transport_selected']}
    host={'dispatch_accepted':True,**{k:data[k] for k in ('native_tool','agent_id','packet_id','task_id','input_identity')}}
    data['host_call_receipt']=write('host-'+kind+'.json',host)
    data['host_call_receipt_sha256']=rc._receipt(data['host_call_receipt'])['sha256']
    evidence=write('followup-'+kind+'.json',data)
    before=copy.deepcopy(s)
    try:
        rc.acknowledge(s,repair['packet_id'],'fixture-author',followup_evidence=evidence)
        error=None
    except rc.ControllerError as e:
        error=str(e)
    unchanged=s==before
    rc.acknowledge(s,repair['packet_id'],'fixture-fresh-repair-author')
    results['initial_failure_'+kind]={'research_plan_recorded':True,'followup_error':error,'rejected_ack_atomic':unchanged,'fresh_context_ack_works':s['tasks']['A']['state']=='running'}

# Case 3: ordinary packet receives an explicit no-retry refusal.
s=state('exhausted-transport')
p=rc.next_packet(s,policy,profiles)
refusal=write('transport-refusal.json',{'actual_fixture_refusal':'exhausted transport; retry prohibited'})
rc.launch_failed(s,p['packet_id'],refusal,'transport','exhausted monthly quota',retry_prohibited=True)
held=copy.deepcopy(s['tasks']['A']['hold'])
delta={'kind':'prelaunch_transport','before':{'transport':'refused'},'after':{'transport':'available'},'discriminator':'fixture transport metadata','scope':'same packet','packet_id':p['packet_id']}
evidence=write('transport-resume.json',delta)
try:
    rc.resume(s,'A',evidence,'frozen-fixture-input')
    resumed=True; error=None
except rc.ControllerError as e:
    resumed=False; error=str(e)
results['exhausted_transport']={'recorded_hold':held,'resumed_despite_explicit_no_retry':resumed,'error':error,'ultra_repairs':s['ultra_repairs']}

# Case 4: actual current state's append-only preservation and typed AND/OR metadata only.
pointer=json.loads((REPO/'.agent-harness/runtime/ACTIVE_CONTROLLER.json').read_text())
real=Path(pointer['state_path']); real_before=real.read_bytes(); live=json.loads(real_before)
old=copy.deepcopy(live)
rows=[]
for name,requires,meaning in [('AUDIT-PROVIDER',{'all':[]},'metadata-only scoped provider'),('AUDIT-USE',{'all':[{'any':[{'task_id':'AUDIT-PROVIDER','evidence':'qualified','product':'confidence_bundle'}]}]},'metadata-only scoped consumer')]:
    rows.append({'id':name,'goal':meaning,'acceptance':'metadata fixture only','kind':'code','input_identity':'fixture-input','owned_paths':[str(HERE/name)],'input_sources':[__file__],'requires':requires,'contract_origin':'new_conditional_research','promotes_original_acceptance':False,'semantic_delta':{'kind':'method','before':{'method':'none'},'after':{'method':meaning},'discriminator':'fixture-only guard','scope':'audit fixture'}})
rc.append_frontier(live,{'frontier_id':'INDEPENDENT-APPEND-FIXTURE','tasks':rows},'copy-only metadata fixture')
copy_preserved=all(live[k]==old[k] for k in ('campaign','campaign_identity','packets','ultra_repairs','ultra_pending','turn')) and all(live['tasks'][k]==v for k,v in old['tasks'].items())
live['tasks']['AUDIT-PROVIDER']['state']='completed'
empty_blocks='AUDIT-USE' not in rc.summary(live)['ready']
live['tasks']['AUDIT-PROVIDER']['qualified_products']=['confidence_bundle']
reviewed_unblocks='AUDIT-USE' in rc.summary(live)['ready']
results['append_and_obligation']={'historical_objects_preserved':copy_preserved,'completed_without_product_blocks':empty_blocks,'qualified_name_unblocks':reviewed_unblocks,'production_bytes_unchanged':real.read_bytes()==real_before,'task_count_before':len(old['tasks']),'production_target':str(real.resolve())}
results['candidate_hashes']={str(p.relative_to(REPO)):hashlib.sha256(p.read_bytes()).hexdigest() for p in (REPO/'scripts/codex_harness/research_controller.py',REPO/'scripts/codex_harness/test_research_controller_frontier.py')}
write('REPRO_RESULTS.json',results)
print(json.dumps(results,indent=2))
