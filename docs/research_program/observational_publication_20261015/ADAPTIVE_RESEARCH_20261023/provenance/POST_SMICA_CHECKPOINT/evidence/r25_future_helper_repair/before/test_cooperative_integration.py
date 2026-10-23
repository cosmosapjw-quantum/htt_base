"""Actual controller/short-lived helper integration; tiny external fixtures, no HTTP."""
import copy,hashlib,importlib.util,json,os,subprocess,sys,tempfile
from pathlib import Path
from types import SimpleNamespace
from test_research_controller_checkpoint import CheckpointTests,rc
from test_research_controller import POLICY,PROFILES,task
ROOT=Path(__file__).resolve().parent
sp=importlib.util.spec_from_file_location('helper',ROOT/'cooperative_resume.py');m=importlib.util.module_from_spec(sp);sp.loader.exec_module(m)
def run():
 t=CheckpointTests();t.setUp()
 try:
  t.state=rc.initialize({'campaign_id':'checkpoint-helper-integration','tasks':[task('ACQUIRE',kind='input',approved_repair_id=None,input_identity='sha256:'+m.INPUT_SHA256),task('SMICA')]},'Controlled integration fixture only')
  packet=rc.next_packet(t.state,POLICY,PROFILES);rc.acknowledge(t.state,packet['packet_id'],'actual-acquisition-agent');t.worker,t.host=t.documents()
  prior=rc.checkpoint_acquisition(t.state,'ACQUIRE',t.worker,t.host);b=prior['binding']
  sources=[m.seal(ROOT/'cooperative_resume.py'),m.seal(ROOT/'cooperative_engine.py')]
  review=t.write('fixture-review.json',dict(verdict='SCOPED_PASS',reviewer='fixture-independent-reviewer',task_id=b['task_id'],packet_id=b['packet_id'],input_identity=b['input_identity'],source_hashes={x['path']:x['sha256'] for x in sources}))
  plan=t.write('fixture-plan.json',dict(binding=b,checkpoint_identity=prior['checkpoint_identity'],sources=sources,review_receipt=m.seal(review)))
  reservation=rc.prepare_acquisition_resume(t.state,'ACQUIRE',prior['checkpoint_identity'],plan);dispatch=t.dispatch(reservation);rc.acknowledge_acquisition_resume(t.state,'ACQUIRE',reservation['reservation_identity'],dispatch)
  row=t.state['acquisition_lifecycle']['ACQUIRE'][-1];grant=t.write('grant.json',row['resume']);checkpoint=t.write('checkpoint-wrapper.json',row)
  next_binding=rc.acquisition_binding(t.state,'ACQUIRE',2)
  args=dict(binding=t.write('prior-binding.json',b),next_binding=t.write('next-binding.json',next_binding),grant=grant,grant_sha256=m.sha(grant),checkpoint=checkpoint,reservation_identity=reservation['reservation_identity'],request=t.write('sticky-request.json',dict(binding=next_binding,action='checkpoint')),engine=str(ROOT/'cooperative_engine.py'),runtime_directory=str(t.root/'runtime'),output=str(t.root/'prepared.json'))
  # Real short-lived helper process, controlled target only. It must not spawn curl.
  child_code="""import importlib.util,json,sys\nfrom pathlib import Path\nfrom types import SimpleNamespace\ns=importlib.util.spec_from_file_location('helper',sys.argv[1]);m=importlib.util.module_from_spec(s);s.loader.exec_module(m)\nm.TARGET=Path(sys.argv[2])\nm.run_reviewed_engine(SimpleNamespace(**json.loads(sys.argv[3])))\n"""
  child=subprocess.Popen([sys.executable,'-B','-c',child_code,str(ROOT/'cooperative_resume.py'),str(t.root),json.dumps(args)],stdout=subprocess.PIPE,stderr=subprocess.PIPE)
  stdout,stderr=child.communicate(timeout=30)
  if child.returncode:raise AssertionError(stderr.decode())
  prep=json.loads(Path(args['output']).read_text());assert prep['handoff_complete'] is False
  assert prep['binding']==next_binding and not prep['snapshot']['processes']
  assert prep['snapshot']['attempt_receipts']==prior['snapshot']['attempt_receipts']
  assert prep['snapshot']['completed_products']==prior['snapshot']['completed_products']
  assert prep['snapshot']['partial_products']==prior['snapshot']['partial_products']
  assert not prep['snapshot']['accounting'].get('cooperative_http_attempts')
  refs={x['path'] for x in prep['snapshot']['sources']}
  assert all(ref in refs for p in prep['snapshot']['completed_products']+prep['snapshot']['partial_products'] for ref in p['source_refs'])
  # Finalization is explicit and only after observed real fixture helper exit0.
  process=prep.pop('helper_process_pending_exit');assert process['pid']==child.pid and child.returncode==0
  process.pop('actual_proc_state',None);process.update(state='exited',exit_code=child.returncode)
  prep['snapshot']['processes'].append(process);prep['handoff_complete']=True
  worker=t.write('worker-2-actual-exit.json',prep)
  observation=t.write('host-observed-helper-exit.json',dict(binding=next_binding,observer='actual-fixture-parent',inventory_complete=True,processes=prep['snapshot']['processes'],queued_writers=[],future_launchers=[]))
  host=t.write('host-2.json',dict(binding=next_binding,worker_receipt=rc._receipt(worker),snapshot_identity=rc.digest(prep['snapshot']),inventory_complete=True,quiescence_observed=True,observer='actual-fixture-parent',process_observation=m.seal(observation),raw_evidence=[m.seal(observation)]))
  accepted=rc.checkpoint_acquisition(t.state,'ACQUIRE',worker,host)
  assert accepted['binding']['sequence']==2
  bad=dict(next_binding,packet_id='changed')
  try:m.next_checkpoint_binding(b,bad)
  except ValueError:pass
  else:raise AssertionError('Rebound next checkpoint accepted')
  result=dict(status='PASS',scope='Controlled tiny fixture only; no production acquisition or review authority',source_hashes={x['path']:x['sha256'] for x in sources},actual_fixture_child_pid=child.pid,actual_fixture_child_exit=child.returncode,actual_helper_stdout_bytes=len(stdout),actual_helper_stderr_bytes=len(stderr),new_transfer_count=0,prior_attempts_preserved=True,prior_completed_exact=True,prior_partial_exact=True,all_source_refs_closed=True,prepared_handoff_complete=False,explicit_next_sequence=2,actual_controller_next_checkpoint_accepted=True)
  (ROOT/'COOPERATIVE_INTEGRATION_RECEIPT.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result))
 finally:t.doCleanups()
if __name__=='__main__':run()
