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
  corruption_checks=[]
  worker_doc=json.loads(Path(row['worker_receipt']['path']).read_text())
  host_doc=json.loads(Path(row['host_receipt']['path']).read_text())
  for label,evidence in [('worker_raw',worker_doc['raw_evidence'][0]),('host_raw',host_doc['raw_evidence'][0]),('host_process_observation',host_doc['process_observation'])]:
   path=Path(evidence['path']);old=path.read_bytes();path.write_bytes(old+b'corruption')
   before={str(x) for x in t.root.rglob('*')}
   try:m.validate_grant(b,grant,m.sha(grant),checkpoint,reservation['reservation_identity'])
   except ValueError:pass
   else:raise AssertionError(label+' corruption admitted')
   assert {str(x) for x in t.root.rglob('*')}==before
   path.write_bytes(old);corruption_checks.append(label)
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
  result=dict(status='PASS',scope='Controlled tiny fixture only; no production acquisition or review authority',source_hashes={x['path']:x['sha256'] for x in sources},actual_fixture_child_pid=child.pid,actual_fixture_child_exit=child.returncode,actual_helper_stdout_bytes=len(stdout),actual_helper_stderr_bytes=len(stderr),new_transfer_count=0,corrupted_bound_evidence_rejected=corruption_checks,progress_cycles=run_progress(),prior_attempts_preserved=True,prior_completed_exact=True,prior_partial_exact=True,all_source_refs_closed=True,prepared_handoff_complete=False,explicit_next_sequence=2,actual_controller_next_checkpoint_accepted=True)
  Path(os.environ['R25_TEST_RECEIPT']).write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result))
 finally:t.doCleanups()


def run_progress():
 """Two actual helper/controlled Python-transport exits; no network or production data."""
 t=CheckpointTests();t.setUp()
 try:
  spec={'filename':'fixture.fits','band_GHz':143,'url':'https://fixture.invalid/map',
        'advisor_head_content_length':10,'required_release':'real-release-v1'}
  contract=t.write('controlled-contract.json',{'files':[spec]});input_sha=m.sha(contract)
  t.state=rc.initialize({'campaign_id':'progress-fixture','tasks':[
      task('ACQUIRE',kind='input',approved_repair_id=None,input_identity='sha256:'+input_sha),task('SMICA')]},'Controlled tiny local fixture only')
  packet=rc.next_packet(t.state,POLICY,PROFILES);rc.acknowledge(t.state,packet['packet_id'],'actual-acquisition-agent')
  part=t.root/'fixture.fits.part';part.write_bytes(b'abc');t.paths['partial.bin']=part
  legacy=t.write('fixture.fits.receipt.json',dict(filename='fixture.fits',status='CHECKPOINT_PARTIAL',partial_or_failure_history=[]))
  worker,host=t.documents()
  worker_doc=json.loads(Path(worker).read_text());worker_doc['snapshot']['sources'].append(m.seal(legacy))
  worker_doc['snapshot']['partial_products'][0]['source_refs'].append(legacy);worker_doc['raw_evidence'].append(m.seal(legacy))
  Path(worker).write_text(json.dumps(worker_doc))
  host_doc=json.loads(Path(host).read_text());host_doc.update(worker_receipt=rc._receipt(worker),snapshot_identity=rc.digest(worker_doc['snapshot']))
  Path(host).write_text(json.dumps(host_doc))
  prior=rc.checkpoint_acquisition(t.state,'ACQUIRE',worker,host)
  original_packet=copy.deepcopy(t.state['packets']);original_task_attempt=t.state['tasks']['ACQUIRE']['attempt']
  sources=[m.seal(ROOT/'cooperative_resume.py'),m.seal(ROOT/'cooperative_engine.py')]
  retained=list(prior['snapshot']['sources'])+[m.seal(legacy)];cycle_results=[]
  child_code=r'''
import importlib.util,json,sys,runpy,subprocess
from pathlib import Path
from types import SimpleNamespace
source,target,argument,contract_path,body_data=sys.argv[1:]
s=importlib.util.spec_from_file_location('controlled_helper',source);h=importlib.util.module_from_spec(s);s.loader.exec_module(h)
h.TARGET=Path(target);h.INPUT_SHA256=h.sha(contract_path)
args=SimpleNamespace(**json.loads(argument));next_binding=json.loads(Path(args.next_binding).read_text())
original_run=runpy.run_path
# Only fixture contract/transport are substituted; real helper and engine code execute.
def controlled_run(path,*a,**kw):
 result=original_run(path,*a,**kw)
 if Path(path).resolve()==Path(args.engine).resolve():result['acquire'].__globals__['CONTRACT']=Path(contract_path)
 return result
runpy.run_path=controlled_run
original_popen=subprocess.Popen
transport_code="""import sys,json\nfrom pathlib import Path\nc=json.loads(sys.argv[1]);body=sys.argv[2].encode();request=sys.argv[3];binding=json.loads(sys.argv[4]);offset=int(c[c.index('--range')+1].split('-')[0])\nPath(c[c.index('--output')+1]).write_bytes(body)\nPath(c[c.index('--dump-header')+1]).write_text(f'HTTP/1.1 206 Partial Content\\r\\nContent-Range: bytes {offset}-9/10\\r\\nContent-Length: {10-offset}\\r\\n\\r\\n')\nPath(request).write_text(json.dumps({'binding':binding,'action':'checkpoint'}))\nprint(json.dumps({'url_effective':'https://fixture.invalid/map','time_total':.01,'size_download':len(body),'exitcode':28}),flush=True)\n"""
def controlled_popen(command,**kwargs):
 if Path(command[0]).name!='curl':raise AssertionError('Unexpected fixture command')
 return original_popen([sys.executable,'-B','-c',transport_code,json.dumps(command),body_data,args.request,json.dumps(next_binding)],**kwargs)
h.subprocess.Popen=controlled_popen
h.run_reviewed_engine(args)
'''
  for sequence,body,expected in [(2,'de',b'abcde'),(3,'f',b'abcdef')]:
   binding=prior['binding']
   review=t.write(f'review-{sequence}.json',dict(verdict='SCOPED_PASS',reviewer='fixture-independent-reviewer',
       task_id=binding['task_id'],packet_id=binding['packet_id'],input_identity=binding['input_identity'],source_hashes={v['path']:v['sha256'] for v in sources}))
   plan=t.write(f'plan-{sequence}.json',dict(binding=binding,checkpoint_identity=prior['checkpoint_identity'],sources=sources,review_receipt=m.seal(review)))
   reservation=rc.prepare_acquisition_resume(t.state,'ACQUIRE',prior['checkpoint_identity'],plan)
   call=dict(binding=binding,checkpoint_identity=prior['checkpoint_identity'],reservation_identity=reservation['reservation_identity'],
       agent_id=reservation['agent_id'],native_tool='collaboration.followup_task',accepted=True,
       requested=reservation['route']['requested'],transport_selected=reservation['route']['transport_selected'])
   tool=t.write(f'native-call-{sequence}.json',call)
   dispatch=t.write(f'dispatch-{sequence}.json',dict(call,tool_receipt=m.seal(tool)))
   rc.acknowledge_acquisition_resume(t.state,'ACQUIRE',reservation['reservation_identity'],dispatch)
   row=t.state['acquisition_lifecycle']['ACQUIRE'][-1]
   grant=t.write(f'grant-{sequence}.json',row['resume']);checkpoint=t.write(f'wrapper-{sequence}.json',row)
   next_binding=rc.acquisition_binding(t.state,'ACQUIRE',sequence)
   args=dict(binding=t.write(f'binding-{sequence}.json',binding),next_binding=t.write(f'next-{sequence}.json',next_binding),
       grant=grant,grant_sha256=m.sha(grant),checkpoint=checkpoint,reservation_identity=reservation['reservation_identity'],
       request=str(t.root/f'request-{sequence}.json'),engine=str(ROOT/'cooperative_engine.py'),
       runtime_directory=str(t.root/f'runtime-{sequence}'),output=str(t.root/f'prepared-{sequence}.json'))
   child=subprocess.Popen([sys.executable,'-B','-c',child_code,str(ROOT/'cooperative_resume.py'),str(t.root),json.dumps(args),contract,body],stdout=subprocess.PIPE,stderr=subprocess.PIPE)
   stdout,stderr=child.communicate(timeout=30);assert child.returncode==0,stderr.decode()
   prepared=json.loads(Path(args['output']).read_text());assert not prepared['handoff_complete']
   assert part.read_bytes()==expected,(part.read_bytes(),stdout.decode())
   assert prepared['snapshot']['accounting']['cooperative_http_attempts']==sequence-1
   assert len(prepared['snapshot']['attempt_receipts'])==len(prior['snapshot']['attempt_receipts'])+1
   process=prepared.pop('helper_process_pending_exit');assert process['pid']==child.pid
   process.pop('actual_proc_state',None);process.update(state='exited',exit_code=child.returncode)
   prepared['snapshot']['processes'].append(process);prepared['handoff_complete']=True
   worker=t.write(f'actual-worker-{sequence}.json',prepared)
   observation=t.write(f'exit-{sequence}.json',dict(binding=next_binding,observer='actual-fixture-parent',inventory_complete=True,
       processes=prepared['snapshot']['processes'],queued_writers=[],future_launchers=[]))
   host=t.write(f'actual-host-{sequence}.json',dict(binding=next_binding,worker_receipt=rc._receipt(worker),snapshot_identity=rc.digest(prepared['snapshot']),
       inventory_complete=True,quiescence_observed=True,observer='actual-fixture-parent',process_observation=m.seal(observation),raw_evidence=[m.seal(observation)]))
   prior=rc.checkpoint_acquisition(t.state,'ACQUIRE',worker,host)
   # Every previously bound raw/source/attempt seal survives actual later progress.
   for evidence in retained:m.check_seal(evidence)
   retained += prepared['raw_evidence']+prepared['snapshot']['sources']+prepared['snapshot']['attempt_receipts']
   retained += [m.seal(x) for x in (worker,host,observation,review,plan,grant,checkpoint,dispatch,tool)]
   receipts=sorted((t.root/'cooperative_product_receipts'/'fixture.fits').glob('*.json'))
   latest=json.loads(receipts[-1].read_text());assert len(latest['partial_or_failure_history'])==sequence-1
   assert len(receipts)==sequence-1
   cycle_results.append(dict(sequence=sequence,actual_helper_pid=child.pid,actual_helper_exit=child.returncode,
       cumulative_controlled_transfers=sequence-1,retained_prefix=expected.decode(),versioned_receipts=len(receipts),
       controller_accepted=True,prior_seals_preserved=True))
  assert t.state['packets']==original_packet and t.state['tasks']['ACQUIRE']['attempt']==original_task_attempt
  assert len(prior['snapshot']['attempt_receipts'])==3
  return cycle_results
 finally:t.doCleanups()

if __name__=='__main__':run()
