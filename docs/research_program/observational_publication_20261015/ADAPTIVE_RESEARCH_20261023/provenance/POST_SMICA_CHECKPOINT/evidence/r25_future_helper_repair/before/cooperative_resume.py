#!/usr/bin/env python3
"""Newly loaded cooperative acquisition primitives; never controls legacy workers.

Production activation requires host-verified fresh resume ACK. This module does
not infer ACK, dispatch, checkpoint acceptance or OS exit from a flag/file name.
All transfers, probes, mirror attempts and successor products must use Runner.
"""
import datetime as dt
import hashlib
import json
import os
from pathlib import Path
import selectors
import subprocess
import threading
import time

INPUT_SHA256='ae7e2f0b136ec3dddcf3b9543f9ec91446587dc50c7908b93b3f17b77e014d9f'
TARGET=Path('/mnt/extdrive/workdir/htt_open_data/planck/PR3/frequency')
BINDING_FIELDS=('campaign_identity','task_id','packet_id','input_identity','task_spec_identity','task_identity','packet_identity','agent_id','sequence')
class YieldRequested(Exception): pass
class StillRunning(Exception): pass

def now():return dt.datetime.now(dt.timezone.utc).isoformat()
def sha(path):
 h=hashlib.sha256()
 with Path(path).open('rb') as f:
  for b in iter(lambda:f.read(8*1024*1024),b''):h.update(b)
 return h.hexdigest()
def seal(path):
 p=Path(path).resolve();return {'path':str(p),'sha256':sha(p),'size_bytes':p.stat().st_size}
def write_json(path,value):
 path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
 tmp=path.with_name(path.name+'.writing')
 with tmp.open('w') as f:json.dump(value,f,indent=2);f.write('\n');f.flush();os.fsync(f.fileno())
 tmp.replace(path)
def owned_external(path):
 p=Path(path).resolve()
 if not p.is_relative_to(TARGET.resolve()):raise ValueError('Runtime/scratch output must remain in owned external directory')
 return p

def process_identity(pid):
 proc=Path(f'/proc/{pid}');s=(proc/'stat').read_text().split(') ',1)[1].split();boot=Path('/proc/sys/kernel/random/boot_id').read_text().strip()
 return {'pid':pid,'start_identity':f'boot:{boot};start_ticks:{s[19]}','parent_pid':int(s[1]),'session_id':s[3],'command':[x.decode() for x in (proc/'cmdline').read_bytes().split(b'\0') if x],'cwd':os.readlink(proc/'cwd'),'actual_proc_state':s[0]}

def drain_fd(fd,deadline,on_tick=lambda:None,sink=None):
 """Actively drain arbitrary stdout, including JSON larger than an8192B pipe.

The caller must retain exclusive read ownership. For legacy migration, pause
only the positively identified waiting parent after host authorization; never
resume that obsolete pipe consumer after this function consumes its stdout.
This function itself sends no signals and makes no process-exit assertion.
"""
 os.set_blocking(fd,False);selector=selectors.DefaultSelector();selector.register(fd,selectors.EVENT_READ);chunks=[]
 try:
  while True:
   on_tick()
   remaining=deadline-time.monotonic()
   if remaining<=0:raise TimeoutError('Bounded stdout drain expired; no quiescence/exit claim')
   for key,_ in selector.select(min(.25,remaining)):
    try:b=os.read(key.fd,65536)
    except BlockingIOError:continue
    if not b:return b''.join(chunks)
    if sink is not None:sink.write(b);sink.flush()
    chunks.append(b)
 finally:selector.close()

def reconcile_prefix(part,body,start,total,range_status,range_header):
 """Append verified contiguous bytes exactly once, including interrupted append.

Keep body and original frozen checkpoints. Compare all existing overlap;
missing gaps or byte disagreement stop without manufacturing bytes.
"""
 part=owned_external(part);body=owned_external(body);received=body.stat().st_size
 import re
 match=re.fullmatch(r'bytes (\d+)-(\d+)/(\d+)',range_header or '')
 if range_status!=206 or not match:raise ValueError('Only exact HTTP206 range may be reconciled')
 a,b,n=map(int,match.groups())
 if a!=start or n!=total or b!=total-1 or received>b-a+1:raise ValueError('Conflicting actual range/size metadata')
 current=part.stat().st_size if part.exists() else 0
 if current<start or current>total:raise ValueError('Missing prefix gap or oversize checkpoint')
 overlap=min(max(current-start,0),received)
 if overlap:
  with part.open('rb') as old,body.open('rb') as new:
   old.seek(start);left=overlap
   while left:
    size=min(left,8*1024*1024)
    if old.read(size)!=new.read(size):raise ValueError('BYTE_IDENTITY_MISMATCH in retained overlap')
    left-=size
 if current<start+received:
  with part.open('ab') as dst,body.open('rb') as src:
   src.seek(overlap)
   while block:=src.read(8*1024*1024):dst.write(block)
   dst.flush();os.fsync(dst.fileno())
 return {'offset_before':current,'offset_after':part.stat().st_size,'received_bytes':received,'overlap_verified_bytes':overlap,'appended_bytes':max(start+received-current,0),'body_retained':True}

class Request:
 def __init__(self,binding,path):
  if any(k not in binding for k in BINDING_FIELDS):raise ValueError('Incomplete exact controller binding')
  self.binding=dict(binding);self.path=Path(path);self.requested=threading.Event();self.error=None
 def poll(self):
  if self.requested.is_set():return True
  if not self.path.exists():return False
  try:r=json.loads(self.path.read_text())
  except json.JSONDecodeError:return False  # Writer has not atomically completed request.
  if r.get('action')!='checkpoint' or r.get('binding')!=self.binding:
   self.error='Request binding/action mismatch; stop new launches without interrupting active stdout drain';self.requested.set();return True
  self.requested.set();return True
 def before_action(self):
  requested=self.poll()
  if self.error:raise ValueError(self.error)
  if requested:raise YieldRequested('Bound checkpoint requested; launch no further transfer/product')

class Runner:
 """One fresh OS controller with at most2 bulk children and a sticky request.

Host must validate ACK freshness before constructing/starting production work.
Constructor intentionally takes actual ACK seal and binding, not an ACK boolean.
The host-specific ACK validator is supplied by the reviewed controller adapter.
"""
 def __init__(self,binding,request_path,ack_seal,validate_ack,next_binding=None):
  if not callable(validate_ack):raise ValueError('Reviewed ACK adapter required')
  observed=seal(ack_seal['path'])
  if observed!=ack_seal:raise ValueError('ACK evidence identity changed')
  validate_ack(binding,Path(ack_seal['path'])) # Must reject stale/mismatched/non-ACK input.
  self.next_binding=next_checkpoint_binding(binding,next_binding) if next_binding is not None else dict(binding)
  self.request=Request(self.next_binding,request_path);self.bulk_slots=threading.BoundedSemaphore(2);self.records=[];self.lock=threading.Lock()
 def transfer(self,command,stdout_path,stderr_path,receipt_path,is_bulk=True,on_started=None):
  """One bounded attempt. Request never kills an active curl.

A request observed in flight becomes sticky; after natural completion the
caller reconciles real bytes and exits before any successor action. No queued
retry, mirror probe/fallback or next product may bypass before_action().
"""
  self.request.before_action()
  if not command or Path(command[0]).name!='curl':raise ValueError('Only declared curl transport')
  if '--max-time' not in command or not 0<float(command[command.index('--max-time')+1])<=900:raise ValueError('Per-attempt timeout must be <=900s')
  for path in (stdout_path,stderr_path,receipt_path):owned_external(path)
  for option in ('--output','--dump-header'):
   if option not in command:raise ValueError('Raw body/HTTP paths required')
   owned_external(command[command.index(option)+1])
  if is_bulk:self.bulk_slots.acquire()
  process=None;record={'start_time':now(),'command':command,'is_bulk':is_bulk,'binding':self.request.binding};failure=None
  try:
   self.request.before_action()
   with Path(stderr_path).open('wb') as error,Path(stdout_path).open('wb') as output:
    process=subprocess.Popen(command,stdout=subprocess.PIPE,stderr=error)
    record.update(actual_pid=process.pid,execution_state='ACTUALLY_STARTED')
    with self.lock:self.records.append(record)
    try:record['process_started']=process_identity(process.pid)
    except OSError as error_identity:
     record['identity_status']='UNKNOWN';failure=error_identity
    write_json(receipt_path,record)  # Preserve actual start even when later identity/drain fails.
    if on_started:on_started(record.get('process_started',{'pid':process.pid,'identity_status':'UNKNOWN'}))
    maximum=float(command[command.index('--max-time')+1])
    drain_fd(process.stdout.fileno(),time.monotonic()+maximum+30,self.request.poll,sink=output)
    exitcode=process.wait(timeout=5)
    record.update(end_time=now(),exit_code=exitcode,request_observed=self.request.poll(),child_exit_observed=True)
   if failure is not None:raise ValueError('Actual started transfer identity unavailable; retained bytes and attempt, HOLD') from failure
  except BaseException as error:
   failure=error;record['failure']=f'{type(error).__name__}: {error}'
   if process is not None and process.poll() is None:
    self.request.error=f'Child {process.pid} remains observed-active; no checkpoint eligibility';self.request.requested.set()
    # Keep the real process/pipe under ownership for diagnosis, never invent an exit.
    if not hasattr(self,'active_processes'):self.active_processes={}
    self.active_processes[process.pid]=process
    record['child_exit_observed']=False
   elif process is not None:
    record.update(exit_code=process.returncode,child_exit_observed=True,end_time=now())
  finally:
   if process is not None:
    for label,path in (('actual_stdout',stdout_path),('actual_stderr',stderr_path),('actual_http',command[command.index('--dump-header')+1]),('actual_body',command[command.index('--output')+1])):
     if Path(path).exists():record[label]=seal(path)
    write_json(receipt_path,record);record['attempt_receipt']=seal(receipt_path)
   if is_bulk and (process is None or process.poll() is not None):self.bulk_slots.release()
  if failure is not None:
   if process is not None and process.poll() is None:raise StillRunning(self.request.error) from failure
   self.request.error=record.get('failure','Actual transfer identity unavailable');self.request.requested.set()
   raise failure
  return record
 def products(self,plans,run_one):
  """Explicit serial product succession; run_one must route attempts through transfer."""
  results=[]
  for plan in plans:
   self.request.before_action()
   result=run_one(self,plan);results.append(result)
   if self.request.poll():break
  return results
 def after_reconcile(self):
  """Call after strict range reconciliation and before retry/mirror/fallback/product."""
  return self.request.poll()
 def handoff(self,snapshot,raw_evidence,output):
  """Preparation only; final host envelope is assembled after this OS helper exits."""
  if not self.request.poll() or self.request.error:raise ValueError('No valid exact bound checkpoint request')
  if snapshot.get('queued_writers') or snapshot.get('future_launchers'):raise ValueError('Unresolved queued/future writers')
  if any(p.get('state')!='exited' for p in snapshot.get('processes',[])):raise ValueError('Active OS process prevents complete handoff')
  own=process_identity(os.getpid());own.update(role='controller',source_refs=list(getattr(self,'source_refs',[])),state='running')
  value={'binding':self.next_binding,'helper_process_pending_exit':own,'handoff_complete':False,'inventory_complete':True,'snapshot':snapshot,'raw_evidence':raw_evidence,'status':'WORKER_PREPARED_PENDING_OWN_EXIT_AND_HOST_CORROBORATION','no_further_writes_after_helper_exit':True}
  write_json(owned_external(output),value)
  return value

def next_checkpoint_binding(prior,requested):
 expected=dict(prior,sequence=prior['sequence']+1)
 if requested!=expected:raise ValueError('Next checkpoint must preserve exact original binding and increment sequence once')
 return expected

def digest(value):
 return hashlib.sha256(json.dumps(value,sort_keys=True,ensure_ascii=False).encode()).hexdigest()
def check_seal(expected):
 actual=seal(expected['path'])
 if actual['path']!=str(Path(expected['path']).resolve()) or actual['sha256']!=expected['sha256']:raise ValueError('Sealed evidence bytes changed')
 if 'size_bytes' in expected and actual['size_bytes']!=expected['size_bytes']:raise ValueError('Sealed evidence size changed')
 return actual

def validate_grant(binding,grant_path,grant_sha256,checkpoint_path,expected_reservation):
 """Verify actual host ACK, checkpoint/reservation identities and reviewed bytes.

expected_reservation and grant SHA must come from the explicit fresh host grant,
not be inferred from a cached file or model/profile selection.
"""
 if sha(grant_path)!=grant_sha256:raise ValueError('Host grant byte seal mismatch')
 grant=json.loads(Path(grant_path).read_text());checkpoint=json.loads(Path(checkpoint_path).read_text())
 if grant.get('state')!='acknowledged' or grant.get('binding')!=binding or checkpoint.get('binding')!=binding:raise ValueError('ACK/checkpoint binding or acknowledged state mismatch')
 if grant.get('agent_id')!=binding['agent_id']:raise ValueError('Resume agent changed')
 for name in ('worker_receipt','host_receipt'):check_seal(checkpoint[name])
 identity=digest({'worker':checkpoint['worker_receipt'],'host':checkpoint['host_receipt']})
 if checkpoint.get('checkpoint_identity')!=identity or grant.get('checkpoint_identity')!=identity:raise ValueError('Checkpoint identity mismatch')
 base={k:grant[k] for k in ('checkpoint_identity','binding','plan','route','agent_id')};base.update(state='pending',native_tool='collaboration.followup_task')
 if digest(base)!=expected_reservation or grant.get('reservation_identity')!=expected_reservation:raise ValueError('Fresh reservation identity mismatch')
 if not grant.get('dispatch_receipt') or not grant.get('tool_receipt'):raise ValueError('Actual accepted dispatch/ACK receipts absent')
 for name in ('dispatch_receipt','tool_receipt'):check_seal(grant[name])
 dispatch=json.loads(Path(grant['dispatch_receipt']['path']).read_text());tool=json.loads(Path(grant['tool_receipt']['path']).read_text())
 expected_call={'binding':binding,'checkpoint_identity':identity,'reservation_identity':expected_reservation,'agent_id':binding['agent_id'],'native_tool':'collaboration.followup_task','accepted':True,'requested':grant['route']['requested'],'transport_selected':grant['route']['transport_selected']}
 for document in (dispatch,tool):
  if any(document.get(k)!=v for k,v in expected_call.items()):raise ValueError('Actual accepted-call receipt binding mismatch')
 if dispatch.get('tool_receipt')!=grant['tool_receipt']:raise ValueError('Dispatch/tool evidence seal mismatch')
 worker=json.loads(Path(checkpoint['worker_receipt']['path']).read_text());host=json.loads(Path(checkpoint['host_receipt']['path']).read_text())
 if checkpoint.get('snapshot')!=worker.get('snapshot') or worker.get('binding')!=binding:raise ValueError('Wrapper snapshot differs from actual sealed worker receipt')
 if host.get('binding')!=binding or host.get('worker_receipt')!=checkpoint['worker_receipt'] or host.get('snapshot_identity')!=digest(worker['snapshot']):raise ValueError('Actual host/worker snapshot binding mismatch')
 for item in worker['snapshot'].get('sources',[])+worker['snapshot'].get('completed_products',[])+worker['snapshot'].get('partial_products',[])+worker['snapshot'].get('attempt_receipts',[]):check_seal(item)
 plan_seal=grant['plan']['plan_receipt'];check_seal(plan_seal);plan=json.loads(Path(plan_seal['path']).read_text())
 if plan.get('binding')!=binding or plan.get('checkpoint_identity')!=identity:raise ValueError('Resume plan/checkpoint binding mismatch')
 if plan.get('sources')!=grant['plan']['sources'] or plan.get('review_receipt')!=grant['plan']['review_receipt']:raise ValueError('Resume source/review plan changed')
 check_seal(plan['review_receipt']);review=json.loads(Path(plan['review_receipt']['path']).read_text())
 if review.get('verdict')!='SCOPED_PASS' or review.get('reviewer')==binding['agent_id'] or not review.get('reviewer'):raise ValueError('Independent scoped source review absent')
 if any(review.get(k)!=binding[k] for k in ('task_id','packet_id','input_identity')):raise ValueError('Source review binding mismatch')
 for source in plan['sources']:
  actual=check_seal(source)
  if review.get('source_hashes',{}).get(actual['path'])!=actual['sha256']:raise ValueError('Unreviewed source bytes in resume plan')
 return grant,checkpoint,plan

def prefix_witness(path,prior_size,prior_sha256):
 """Actual stream-prefix witness; same-size replacement cannot pass."""
 path=Path(path)
 if path.stat().st_size<prior_size:raise ValueError('Prior prefix truncated')
 h=hashlib.sha256();left=prior_size
 with path.open('rb') as f:
  while left:
   data=f.read(min(left,8*1024*1024))
   if not data:raise ValueError('Prior prefix missing')
   h.update(data);left-=len(data)
 if h.hexdigest()!=prior_sha256:raise ValueError('BYTE_IDENTITY_MISMATCH in retained prior prefix')
 return {'path':str(path.resolve()),'prior_size_bytes':prior_size,'prior_sha256':prior_sha256,'observed_prefix_sha256':h.hexdigest(),'current_size_bytes':path.stat().st_size}

class EngineProxy:
 """Route every newly loaded reviewed-engine curl through one cooperative gate."""
 PIPE=subprocess.PIPE
 def __init__(self,runner,runtime):self.runner=runner;self.runtime=owned_external(runtime);self.runtime.mkdir(parents=True,exist_ok=True)
 def run(self,command,stdout=None,stderr=None,text=False,timeout=None,on_process_started=None,**kwargs):
  self.runner.request.before_action()
  if Path(command[0]).name!='curl':raise ValueError('Unexpected engine subprocess')
  body=Path(command[command.index('--output')+1]);base=str(body).removesuffix('.body')
  record=self.runner.transfer(command,base+'.curl.json',stderr.name,base+'.cooperative_attempt.json',True,on_started=on_process_started)
  data=Path(base+'.curl.json').read_bytes()
  return subprocess.CompletedProcess(command,record['exit_code'],data.decode() if text else data,None)

def run_reviewed_engine(args):
 """Production entrypoint, used only after explicit same-agent ACK grant.

No source/ACK inference; no legacy-process signaling. Existing completed maps
are preserved. All new engine retries/fallbacks cross the cooperative gate.
"""
 binding=json.loads(Path(args.binding).read_text())
 next_binding=next_checkpoint_binding(binding,json.loads(Path(args.next_binding).read_text()))
 grant,checkpoint,plan=validate_grant(binding,args.grant,args.grant_sha256,args.checkpoint,args.reservation_identity)
 reviewed={str(Path(x['path']).resolve()):x['sha256'] for x in plan['sources']}
 for path in (Path(__file__).resolve(),Path(args.engine).resolve()):
  if reviewed.get(str(path))!=sha(path):raise ValueError('Helper/engine source not independently reviewed at exact bytes')
 import runpy,concurrent.futures as cf
 engine=runpy.run_path(str(Path(args.engine).resolve()));g=engine['acquire'].__globals__
 if sha(g['CONTRACT'])!=INPUT_SHA256 or binding['input_identity']!='sha256:'+INPUT_SHA256:raise ValueError('Frozen input identity mismatch')
 # Recheck grant at construction; callback performs reads only, never creates ACK.
 runner=Runner(binding,args.request,seal(args.grant),lambda b,p:validate_grant(b,p,args.grant_sha256,args.checkpoint,args.reservation_identity),next_binding=next_binding)
 runtime=owned_external(args.runtime_directory);runtime.mkdir(parents=True,exist_ok=True)
 runner.source_refs=list(reviewed);g.update(TARGET=TARGET,EXECUTING_SOURCE_SHA256=sha(args.engine),subprocess=EngineProxy(runner,runtime))
 contract=json.loads(Path(g['CONTRACT']).read_text());prior=checkpoint['snapshot'];witnesses=[]
 for item in prior.get('partial_products',[]):
  check_seal(item)
  witnesses.append(prefix_witness(item['path'],item['size_bytes'],item['sha256']))
 # Completed seals are checked before reuse; no completed product is downloaded again.
 for item in prior.get('completed_products',[]):check_seal(item)
 pending=[]
 for spec in contract['files']:
  receipt=TARGET/(spec['filename']+'.receipt.json')
  if receipt.exists():
   current=json.loads(receipt.read_text())
   if current.get('status')=='VALIDATED_LOCAL_PRODUCT' and Path(current.get('path','')).is_file():continue
  pending.append(spec)
 results=[]
 def one(spec):
  runner.request.before_action();result=engine['acquire'](spec,cooperative_check=runner.request.before_action)
  if runner.request.poll() and result.get('status')!='VALIDATED_LOCAL_PRODUCT':
   result.update(status='COOPERATIVE_REQUEST_ERROR' if runner.request.error else 'CHECKPOINT_PARTIAL',checkpoint_requested=runner.request.error is None)
   write_json(TARGET/(spec['filename']+'.receipt.json'),result)
  return result
 with cf.ThreadPoolExecutor(max_workers=2) as pool:
  active={};iterator=iter(pending)
  for _ in range(2):
   if runner.request.poll():break
   spec=next(iterator,None)
   if spec is not None:active[pool.submit(one,spec)]=spec
  while active:
   done,_=cf.wait(active,return_when=cf.FIRST_COMPLETED)
   for future in done:
    active.pop(future)
    try:results.append(future.result())
    except YieldRequested:pass
    if not runner.request.poll():
     spec=next(iterator,None)
     if spec is not None:active[pool.submit(one,spec)]=spec
 # All owned Popen children are observed exited before snapshot preparation.
 completed=list(prior.get('completed_products',[]));partials=[];raw=list(json.loads(Path(checkpoint['worker_receipt']['path']).read_text()).get('raw_evidence',[]));raw.append(seal(args.request)) if Path(args.request).exists() else None
 prior_completed_paths={x['path'] for x in completed}
 for spec in contract['files']:
  receipt=TARGET/(spec['filename']+'.receipt.json')
  old_done=next((x for x in completed if Path(x['path']).name==spec['filename']),None)
  if old_done is not None:continue
  if not receipt.exists():continue
  raw.append(seal(receipt));value=json.loads(receipt.read_text())
  old=next((x for x in prior.get('partial_products',[])+prior.get('completed_products',[]) if Path(x['path']).name.removesuffix('.part')==spec['filename']),{})
  source_refs=list(old.get('source_refs',[]))
  if str(receipt) not in source_refs:source_refs.append(str(receipt))
  product_id=old.get('product_id',spec['filename'])
  if value.get('status')=='VALIDATED_LOCAL_PRODUCT':
   artifact=seal(value['path']);artifact.update(product_id=product_id,source_release=spec['required_release'],source_refs=source_refs);completed.append(artifact)
  else:
   part=TARGET/(spec['filename']+'.part')
   if part.exists():
    artifact=seal(part);artifact.update(offset=artifact['size_bytes'],product_id=product_id,source_release=spec['required_release'],source_refs=source_refs);partials.append(artifact)
 # Preserve checkpoint partials outside this concrete product list too; never lose a retained input.
 produced_ids={x['product_id'] for x in completed+partials}
 for old in prior.get('partial_products',[]):
  if old['product_id'] not in produced_ids:
   artifact=seal(old['path']);artifact.update(product_id=old['product_id'],source_release=old['source_release'],source_refs=old['source_refs'],offset=artifact['size_bytes']);partials.append(artifact)
 for record in runner.records:
  raw.extend([record['actual_stdout'],record['actual_stderr'],record['actual_http']])
  if 'actual_body' in record:raw.append(record['actual_body'])
 accounting=dict(prior.get('accounting',{}))
 for key,value in {'cooperative_http_attempts':len(runner.records),'cooperative_downloaded_bytes':sum(json.loads(Path(r['actual_stdout']['path']).read_text()).get('size_download',0) for r in runner.records),'cooperative_curl_wall_seconds':sum(json.loads(Path(r['actual_stdout']['path']).read_text()).get('time_total',0) for r in runner.records)}.items():accounting[key]=accounting.get(key,0)+value
 processes=[]
 for record in runner.records:
  p=dict(record['process_started']);p.pop('actual_proc_state',None);p.update(role='transfer',state='exited',exit_code=record['exit_code'],source_refs=list(reviewed));processes.append(p)
 all_sources=list(prior.get('sources',[]))
 for source in plan['sources']:
  if source not in all_sources:all_sources.append(source)
 for artifact in completed+partials:
  for reference in artifact['source_refs']:
   path=reference.get('path') if isinstance(reference,dict) else reference
   if path and not any(x['path']==str(Path(path).resolve()) for x in all_sources):all_sources.append(seal(path))
 for record in runner.records:
  for reference in record['process_started'].get('source_refs',[]):
   if not any(x['path']==str(Path(reference).resolve()) for x in all_sources):all_sources.append(seal(reference))
 snapshot={'sources':all_sources,'processes':processes,'queued_writers':[],'future_launchers':[],'attempt_receipts':[],'completed_products':completed,'partial_products':partials,'accounting':accounting,'prior_prefix_witnesses':witnesses}
 # Preserve full attempt receipts, not fabricated paths inferred from stdout names.
 snapshot['attempt_receipts']=list(prior.get('attempt_receipts',[]))
 prior_attempt_paths={x['path'] for x in snapshot['attempt_receipts']}
 for record in runner.records:
  actual=record['attempt_receipt']
  if actual['path'] not in prior_attempt_paths:snapshot['attempt_receipts'].append(actual);prior_attempt_paths.add(actual['path'])
 if runner.request.poll():return runner.handoff(snapshot,raw,args.output)
 value={'binding':binding,'status':'NO_CHECKPOINT_REQUEST; ACQUISITION_COMPONENTS_RETURNED','handoff_complete':False,'snapshot':snapshot,'raw_evidence':raw,'results':results};write_json(owned_external(args.output),value);return value

if __name__=='__main__':
 import argparse
 p=argparse.ArgumentParser();p.add_argument('--binding',required=True);p.add_argument('--next-binding',required=True);p.add_argument('--grant',required=True);p.add_argument('--grant-sha256',required=True);p.add_argument('--reservation-identity',required=True);p.add_argument('--checkpoint',required=True);p.add_argument('--request',required=True);p.add_argument('--engine',required=True);p.add_argument('--runtime-directory',required=True);p.add_argument('--output',required=True)
 run_reviewed_engine(p.parse_args())
