"""Controlled falsifiers; fixtures/scratch stay external, no production replay."""
import fcntl,importlib.util,json,os,subprocess,sys,tempfile,time
from pathlib import Path
p=Path(__file__).with_name('cooperative_resume.py');s=importlib.util.spec_from_file_location('cooperative',p);m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
def run():
 m.TARGET=Path(os.environ['R25_TEST_SCRATCH']);m.TARGET.mkdir(parents=True,exist_ok=True)
 results=[]
 # Reproduce actual8192B-capacity counterexample with JSON much larger than64KiB.
 child=subprocess.Popen([sys.executable,'-B','-c','import json,sys; sys.stdout.write(json.dumps({"payload":"x"*262144}));sys.stdout.flush()'],stdout=subprocess.PIPE)
 fcntl.fcntl(child.stdout.fileno(),fcntl.F_SETPIPE_SZ,8192)
 capacity=fcntl.fcntl(child.stdout.fileno(),fcntl.F_GETPIPE_SZ)
 raw=m.drain_fd(child.stdout.fileno(),time.monotonic()+10);assert child.wait(timeout=3)==0
 assert len(json.loads(raw)['payload'])==262144 and capacity==8192
 results.append({'test':'active_drain_8192B_pipe_262144B_JSON','status':'PASS','actual_pipe_bytes':capacity,'actual_stdout_bytes':len(raw)})
 with tempfile.TemporaryDirectory(dir=m.TARGET,prefix='cooperative_fixture_') as d:
  root=Path(d);part=root/'prefix.part';body=root/'body';part.write_bytes(b'abc');body.write_bytes(b'defg')
  r=m.reconcile_prefix(part,body,3,7,206,'bytes 3-6/7');assert part.read_bytes()==b'abcdefg' and r['appended_bytes']==4
  r=m.reconcile_prefix(part,body,3,7,206,'bytes 3-6/7');assert part.read_bytes()==b'abcdefg' and r['appended_bytes']==0
  part.write_bytes(b'abcde');r=m.reconcile_prefix(part,body,3,7,206,'bytes 3-6/7');assert part.read_bytes()==b'abcdefg' and r['appended_bytes']==2
  results.append({'test':'exact_once_and_interrupted_append_reconciliation','status':'PASS'})
  part.write_bytes(b'abcXX')
  try:m.reconcile_prefix(part,body,3,7,206,'bytes 3-6/7')
  except ValueError:pass
  else:raise AssertionError('Conflicting overlap accepted')
  assert part.read_bytes()==b'abcXX'
  results.append({'test':'conflicting_overlap_preserved_and_rejected','status':'PASS'})
  binding={k:'fixture' for k in m.BINDING_FIELDS};binding['sequence']=1;request=root/'request.json';r=m.Request(binding,request);calls=[]
  r.before_action();calls.append('first_attempt');m.write_json(request,{'binding':binding,'action':'checkpoint'});assert r.poll()
  try:r.before_action();calls.append('forbidden_successor')
  except m.YieldRequested:pass
  assert calls==['first_attempt']
  results.append({'test':'sticky_request_blocks_retry_mirror_and_successor_launch','status':'PASS'})
  other=dict(binding,packet_id='wrong');m.write_json(request,{'binding':other,'action':'checkpoint'})
  wrong=m.Request(binding,request);assert wrong.poll() and wrong.error
  try:wrong.before_action()
  except ValueError:pass
  else:raise AssertionError('Mismatched packet allowed launch')
  results.append({'test':'request_exact_binding_required','status':'PASS'})
  part.write_bytes(b'original-prefix-added');oldhash=m.hashlib.sha256(b'original-prefix').hexdigest();m.prefix_witness(part,len(b'original-prefix'),oldhash)
  part.write_bytes(b'changed!-prefix-added')
  try:m.prefix_witness(part,len(b'original-prefix'),oldhash)
  except ValueError:pass
  else:raise AssertionError('Same-size prefix replacement accepted')
  results.append({'test':'streaming_prior_prefix_rejects_same_size_overwrite','status':'PASS'})
 # Actual-start metadata boundary: one controlled transfer, in-flight yield,
 # then no phantom second attempt or successor transport.
 import runpy
 with tempfile.TemporaryDirectory(dir=m.TARGET,prefix='cooperative_attempt_fixture_') as d:
  root=Path(d);binding={k:'fixture' for k in m.BINDING_FIELDS};binding['sequence']=1
  request=m.Request(binding,root/'request.json');calls=[]
  class FakeRunner:
   def __init__(self):self.request=request
   def transfer(self,command,stdout_path,stderr_path,receipt_path,is_bulk=True,on_started=None):
    self.request.before_action();calls.append(command)
    if on_started:on_started({'pid':1,'scope':'controlled fixture process identity'})
    Path(command[command.index('--output')+1]).write_bytes(b'de')
    Path(command[command.index('--dump-header')+1]).write_text('HTTP/1.1 206 Partial Content\r\nContent-Range: bytes 3-9/10\r\nContent-Length: 7\r\n\r\n')
    Path(stdout_path).write_text(json.dumps({'url_effective':'https://fixture.invalid/map','time_total':.01,'size_download':2,'exitcode':28}))
    m.write_json(root/'request.json',{'binding':binding,'action':'checkpoint'});self.request.poll()
    return {'exit_code':28}
  engine=runpy.run_path(str(p.with_name('cooperative_engine.py')));g=engine['acquire'].__globals__;runner=FakeRunner();g.update(TARGET=root,EXECUTING_SOURCE_SHA256=m.sha(p.with_name('cooperative_engine.py')),subprocess=m.EngineProxy(runner,root/'runtime'))
  (root/'fixture.fits.part').write_bytes(b'abc')
  result=engine['acquire']({'filename':'fixture.fits','band_GHz':143,'url':'https://fixture.invalid/map','advisor_head_content_length':10},cooperative_check=request.before_action)
  assert len(calls)==1 and len(result['partial_or_failure_history'])==1 and (root/'fixture.fits.part').read_bytes()==b'abcde'
  assert result['partial_or_failure_history'][0]['execution_state']=='ACTUALLY_STARTED'
  results.append({'test':'actual_start_boundary_no_phantom_attempt_after_inflight_request','status':'PASS','controlled_transfer_calls':len(calls),'stored_actual_attempts':len(result['partial_or_failure_history'])})
 # Actual started child failure paths retain bytes and actual attempt metadata.
 from unittest.mock import patch
 for failure_kind in ('identity','drain_after_bytes'):
  with tempfile.TemporaryDirectory(dir=m.TARGET,prefix='cooperative_failure_fixture_') as d:
   root=Path(d);ack=root/'ack.json';ack.write_text('{}')
   binding={k:'fixture' for k in m.BINDING_FIELDS};binding['sequence']=1
   runner=m.Runner(binding,root/'request.json',m.seal(ack),lambda b,p:None)
   command=['curl','--max-time','1','--output',str(root/'body'),'--dump-header',str(root/'http')]
   actual_popen=subprocess.Popen
   def fixture_popen(command,**kwargs):
    (root/'body').write_bytes(b'actual-fixture-body');(root/'http').write_text('actual-fixture-HTTP')
    return actual_popen([sys.executable,'-B','-c','import sys;sys.stdout.write("actual-fixture-stdout");sys.stdout.flush()'],**kwargs)
   original_drain=m.drain_fd
   def drain_then_fail(*args,**kwargs):
    original_drain(*args,**kwargs);raise ValueError('controlled post-drain failure')
   started=[]
   with patch.object(m.subprocess,'Popen',fixture_popen):
    with patch.object(m,'process_identity',side_effect=OSError('controlled identity disappearance')) if failure_kind=='identity' else patch.object(m,'drain_fd',drain_then_fail):
     try:runner.transfer(command,root/'stdout',root/'stderr',root/'attempt.json',on_started=started.append)
     except (ValueError,OSError):pass
     else:raise AssertionError('Started failure not held')
   assert len(started)==1 and len(runner.records)==1
   record=runner.records[0];assert record['execution_state']=='ACTUALLY_STARTED' and record['child_exit_observed'] and record['exit_code']==0
   assert (root/'stdout').read_bytes()==b'actual-fixture-stdout' and (root/'body').read_bytes()==b'actual-fixture-body'
   assert record['actual_stdout']==m.seal(root/'stdout') and record['attempt_receipt']==m.seal(root/'attempt.json')
   assert runner.request.error and runner.request.poll()
   results.append({'test':'started_'+failure_kind+'_failure_retains_actual_attempt_and_bytes','status':'PASS'})
 receipt={'status':'PASS','source':m.seal(p),'tests':results,'scope':'Controlled external fixtures only; no production process control or transport replay','production_activation':'NOT_PERFORMED'}
 Path(os.environ['R25_TEST_RECEIPT']).write_text(json.dumps(receipt,indent=2)+'\n');print(json.dumps(receipt))
if __name__=='__main__':run()
