"""Read-only source review reproductions; only TemporaryDirectory under TMPDIR is changed."""
import copy,json
from pathlib import Path
from test_research_controller_checkpoint import CheckpointTests,rc,POLICY,PROFILES

def run(name, action):
    t=CheckpointTests(); t.setUp()
    try:
        result=action(t)
        print(json.dumps({'case':name,'accepted':True,**result}))
    except rc.ControllerError as e:
        print(json.dumps({'case':name,'accepted':False,'error':str(e)}))
    finally:t.doCleanups()

def replace_checkpoint(t):
    row=t.checkpoint(); original=row['checkpoint_identity']
    t.paths['partial.bin'].write_text('CHANGED')
    t.worker,t.host=t.documents()
    result=rc.next_packet(t.state,POLICY,PROFILES)
    actual=rc.digest({'worker':rc._receipt(t.worker),'host':rc._receipt(t.host)})
    return {'accepted_task':result.get('task_id'),'stored_identity':original,'current_identity':actual}

def stale_ack(t):
    t.checkpoint();p=rc.next_packet(t.state,POLICY,PROFILES)
    t.paths['partial.bin'].write_text('changed by writer after next')
    rc.acknowledge(t.state,p['packet_id'],'independent-smica-agent')
    return {'state':t.state['tasks']['SMICA']['state']}

def replace_plan(t):
    r=t.prepare();old=copy.deepcopy(r['plan']);row=t.state['acquisition_lifecycle']['ACQUIRE'][-1]
    newsource=t.root/'replacement.py';newsource.write_text('different cooperative implementation')
    review={'verdict':'SCOPED_PASS','reviewer':'independent-source-reviewer','task_id':row['binding']['task_id'],
            'packet_id':row['binding']['packet_id'],'input_identity':row['binding']['input_identity'],
            'source_hashes':{str(newsource):t.seal(newsource)['sha256']}}
    reviewpath=t.write('replacement-review.json',review)
    planpath=old['plan_receipt']['path']
    Path(planpath).write_text(json.dumps({'binding':row['binding'],'checkpoint_identity':row['checkpoint_identity'],
                          'sources':[t.seal(newsource)],'review_receipt':t.seal(reviewpath)}))
    dispatch=t.dispatch(r);rc.acknowledge_acquisition_resume(t.state,'ACQUIRE',r['reservation_identity'],dispatch)
    return {'state':t.state['tasks']['ACQUIRE']['state'],'stored_plan_still_old':row['resume']['plan']==old,
            'current_plan_identity_differs':rc._receipt(planpath)!=old['plan_receipt']}

def replace_prefix(t):
    r=t.prepare();d=t.dispatch(r);rc.acknowledge_acquisition_resume(t.state,'ACQUIRE',r['reservation_identity'],d)
    old=t.state['acquisition_lifecycle']['ACQUIRE'][0]['snapshot']['partial_products'][0]
    t.paths['partial.bin'].write_text('CHANGED');t.worker,t.host=t.documents(sequence=2)
    new=t.checkpoint()['snapshot']['partial_products'][0]
    return {'accepted_sequence':2,'old_sha':old['sha256'],'new_sha':new['sha256'],
            'same_size':old['size_bytes']==new['size_bytes']}

run('replace_checkpoint_documents_after_freeze',replace_checkpoint)
run('ordinary_ack_after_stale_checkpoint',stale_ack)
run('change_plan_after_durable_reservation',replace_plan)
run('second_checkpoint_overwrites_prior_partial_prefix',replace_prefix)

def independent_discovery(t):
    t.state['tasks']['SMICA']['state']='held'
    t.state['tasks']['SMICA']['hold']={'reason':'independent real method search remains required'}
    rc.enable_adaptive(t.state,'actual fixture authorization for independent branch research')
    t.worker,t.host=t.documents()
    fingerprint=rc.adaptive_fingerprint(t.state)
    t.checkpoint()
    result=rc.next_packet(t.state,POLICY,PROFILES)
    return {'has_discovery_packet':bool(result.get('packet_id')),
            'eligible_branches':result.get('eligible_branches'),
            'fingerprint_unchanged':fingerprint==rc.adaptive_fingerprint(t.state),
            'status':result.get('status')}

run('independent_discovery_while_acquisition_checkpointed',independent_discovery)
