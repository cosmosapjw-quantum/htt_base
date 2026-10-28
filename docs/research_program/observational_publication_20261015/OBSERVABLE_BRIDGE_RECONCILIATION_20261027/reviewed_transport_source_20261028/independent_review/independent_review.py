#!/usr/bin/env python3
"""Independent reviewer fixtures; all mutable data stays under this directory."""
import ast, datetime, difflib, hashlib, http.server, importlib.util, json, os, pathlib, signal, subprocess, sys, threading, time, urllib.parse
ROOT=pathlib.Path(__file__).resolve().parent
EXT=ROOT.parent
CAND=EXT/'r36_pr4_concurrency_implementation/fetch_commander_mc.py'
OLD=EXT/'r36_pr4_transfer_repair_preparation/fetch_commander_mc.py'
CAND_SHA='139804aa216430b5db1b711823087099c31300e8e9e6c1ff56f3602178aaabe6'
OLD_SHA='7d0c3ee5a2afe9655f86f674052323a69da0fc64d920d3eb2cb81c3eb2e6a2ee'
HANDOFF=EXT/'r36_pr4_actual/checkpoint/WORKER_HANDOFF_002.json'
HANDOFF_SHA='013af5f0b4614169d881a74e7aa87a0ad38a8182496353d12ddaf4690f1c20ab'
PREFIX=(EXT/'r36_pr4_contract_preparation/commander_sim0300_prefix.bin').read_bytes()
assert len(PREFIX)==11520

def sha(p):return hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest()
def save(p,v):
 with pathlib.Path(p).open('x') as f:json.dump(v,f,indent=2);f.write('\n')
def getjson(p):return json.loads(pathlib.Path(p).read_text())
def stamp():return datetime.datetime.now(datetime.timezone.utc).isoformat()
def filename(i):return f'npipe6v20_commander_cmb_2048_mc_{i:04d}_005a.fits'
def payload(i):return PREFIX+bytes([i%256])*(32768-len(PREFIX))
def proc_identity(pid):
 raw=pathlib.Path(f'/proc/{pid}/stat').read_text();r=raw.rsplit(')',1)[1].split()
 return {'pid':pid,'stat':raw,'state':r[0],'ppid':int(r[1]),'start_ticks':r[19]}
def must(ok,what):
 if not ok:raise AssertionError(what)
def source_check():
 expected={
 'r36_pr4_concurrency_framing/IMPLEMENTATION_CONTRACT.json':'223fde11036657cea437313e06f26a94190f3eda27d40680bc689f0da38e1ac2',
 'r36_pr4_concurrency_framing/DECISION.json':'54597d53b77dcb62bbf6cbc4d9d070911257698a17fd0750892c300886d65119',
 'r36_pr4_concurrency_implementation/RETURN.json':'b1690ac2c31132f559ca146dc6201a016387ab7292d941cdbd04e69b326b66a3',
 'r36_pr4_concurrency_implementation/MANIFEST.json':'d5eff985d8bc11c7e649dd91c5fa3f5b7402a7dc46261edf2cf9878ba30b1edc',
 'r36_pr4_concurrency_implementation/fetch_commander_mc.py':CAND_SHA,
 'r36_pr4_transfer_repair_preparation/fetch_commander_mc.py':OLD_SHA,
 'r36_pr4_http10_source_fresh_review/closeout_01/REVIEW_RESULT.json':'0b2d56f12abe474f255035c831cffbd783db26d1c728602087c02f6dcc1cc4a0'}
 contract=getjson(EXT/'r36_pr4_concurrency_framing/IMPLEMENTATION_CONTRACT.json')
 for b in contract['source_bindings'].values():expected[str(pathlib.Path(b['path']).relative_to(EXT))]=b['sha256']
 checks=[]
 for rel,want in expected.items():
  p=EXT/rel;actual=sha(p);must(actual==want,'input binding '+rel);checks.append({'path':str(p),'sha256':actual,'bytes':p.stat().st_size})
 old=OLD.read_bytes();candidate=CAND.read_bytes();reversed_source=candidate
 for replacement in contract['production_source_allowlist']['only_two_lines']:
  new=(replacement['new']+'\n').encode();base=(replacement['old']+'\n').encode()
  must(reversed_source.count(new)==1,'unique allowlist new line');must(old.count(base)==1,'unique allowlist base line')
  reversed_source=reversed_source.replace(new,base,1)
 must(reversed_source==old,'exact reverse bytes')
 must(ast.dump(ast.parse(reversed_source),include_attributes=False)==ast.dump(ast.parse(old),include_attributes=False),'normalized AST')
 (ROOT/'SOURCE.diff').write_text(''.join(difflib.unified_diff(old.decode().splitlines(True),candidate.decode().splitlines(True),fromfile=str(OLD),tofile=str(CAND))))
 prior=getjson(EXT/'r36_pr4_http10_source_fresh_review/closeout_01/REVIEW_RESULT.json')
 retained=[]
 for row in prior['raw_evidence']:
  if pathlib.Path(row['path']).name in {'AFFECTED.stderr','ORIGINAL_FALSIFIERS.stderr','MAIN_CLOSEOUT_FINAL.stderr','AUX_REAL_FINAL.stderr','SOURCE_PRESERVATION.json','SOURCE_SEALS.json'}:
   must(sha(row['path'])==row['sha256'],'prior raw seal '+row['path']);retained.append(row)
 save(ROOT/'SOURCE_PROOF.json',{'checked_at':stamp(),'bindings':checks,'reverse_exact_bytes':True,'reverse_sha256':hashlib.sha256(reversed_source).hexdigest(),'normalized_AST_equal_after_only_allowlist_reversal':True,'reused_prior_raw_evidence':retained,'unchanged_controls_rerun':False})
 return {'reverse_exact_bytes':True,'normalized_AST_equal':True,'binding_count':len(checks),'unchanged_raw_reuse_count':len(retained)}

CHILD=r'''
import hashlib,importlib.util,json,pathlib,sys,urllib.parse,urllib.request
source=pathlib.Path(sys.argv[1]);r=pathlib.Path(sys.argv[2]);mode=sys.argv[3];url=sys.argv[4]
actual=hashlib.sha256(source.read_bytes()).hexdigest()
assert actual=='139804aa216430b5db1b711823087099c31300e8e9e6c1ff56f3602178aaabe6'
spec=importlib.util.spec_from_file_location('reviewed_helper_exact',source);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
def record(p,v):
 with open(p,'x') as f:json.dump(v,f,indent=2);f.write('\n')
record(r/'CHILD_SOURCE.json',{'helper_file':m.__file__,'sha256':actual,'fixture_mode':mode})
argv=['review-fixture','--ids',*map(str,range(300,318) if mode=='signals' else [300]),'--cache',str(r/'cache'),'--receipts',str(r/'attempts'),'--handoff','/mnt/extdrive/workdir/htt_open_data/r36_pr4_actual/checkpoint/WORKER_HANDOFF_002.json','--handoff-sha256','013af5f0b4614169d881a74e7aa87a0ad38a8182496353d12ddaf4690f1c20ab','--mode','canonical-http10','--requested-executor-runtime','INDEPENDENT_LOCALHOST_FIXTURE','--observed-executor-runtime','UNKNOWN']
if mode=='cli':
 value=url
 if value!='default':argv+=['--concurrency',value]
 parsed=m.argparse.ArgumentParser.parse_args
 def capture(parser,*args,**kwargs):
  a=parsed(parser,*args,**kwargs);record(r/'PARSED.json',vars(a)|{'cache':str(a.cache),'receipts':str(a.receipts),'handoff':str(a.handoff)});return a
 m.argparse.ArgumentParser.parse_args=capture
 class StopBeforeIO(Exception):pass
 def digest_guard(path):record(r/'GUARD_ACCEPTED.json',{'source_file':m.__file__,'source_sha256':actual,'before_first_frozen_source_read':str(path)});raise StopBeforeIO()
 m.digest=digest_guard
 sys.argv=argv
 try:m.main()
 except StopBeforeIO:sys.exit(0)
 raise AssertionError('unreachable')
else:
 argv+=['--concurrency','16'];sys.argv=argv
 original=m.CurlResponse
 def local(req,attempt,storage):
  # Keep canonical item and Request identity; map only the real transport endpoint.
  original_url=urllib.parse.urlsplit(req.full_url)
  assert original_url.netloc=='pla.esac.esa.int'
  item=urllib.parse.parse_qs(original_url.query)['SIMULATED_MAP.FILE_ID'][0]
  target=url+'/'+item
  assert urllib.parse.urlsplit(target).hostname=='127.0.0.1'
  return original(urllib.request.Request(target,headers=dict(req.header_items())),attempt,storage)
 m.CurlResponse=local
 pilots=[]
 def fixture_pilots(item,root):pilots.append(item['id']);return 'LOCAL_FIXTURE_PILOT_ADMISSION_ONLY'
 m.verify_cache=fixture_pilots
 code=m.main()
 record(r/'CHILD_RETURN.json',{'code':code,'owned_children_count':len(m.OWNED_CHILDREN),'stop':m.STOP.is_set(),'stop_signal':m.STOP_SIGNAL,'pilot_ids':pilots,'helper_file':m.__file__,'helper_sha256':hashlib.sha256(source.read_bytes()).hexdigest()})
 sys.exit(code)
'''

def cli_checks():
 root=ROOT/'cli';root.mkdir();out=[]
 for value in ('0','17','1','4','8','16','default'):
  r=root/value;r.mkdir()
  # Invalid inputs execute the actual file, without instrumentation.
  if value in ('0','17'):
   cmd=[sys.executable,'-B',str(CAND),'--ids','300','--cache',str(r/'cache'),'--receipts',str(r/'attempts'),'--concurrency',value,'--handoff',str(HANDOFF),'--handoff-sha256',HANDOFF_SHA,'--mode','canonical-http10','--requested-executor-runtime','INDEPENDENT_LOCALHOST_FIXTURE']
  else:cmd=[sys.executable,'-B','-c',CHILD,str(CAND),str(r),'cli',value]
  save(r/'COMMAND.json',cmd);p=subprocess.run(cmd,capture_output=True,timeout=15)
  (r/'stdout.txt').write_bytes(p.stdout);(r/'stderr.txt').write_bytes(p.stderr)
  if value in ('0','17'):
   must(p.returncode==2,'argparse exit2 '+value);must(b'concurrency must be within 1..16' in p.stderr,'guard error '+value);must(not p.stdout,'no guard stdout')
  else:
   must(p.returncode==0,'accepted CLI '+value+': '+p.stderr.decode());parsed=getjson(r/'PARSED.json');must(parsed['concurrency']==(4 if value=='default' else int(value)),'actual parsed value '+value);must(getjson(r/'GUARD_ACCEPTED.json')['source_sha256']==CAND_SHA,'child binding')
  must(not (r/'cache').exists() and not (r/'attempts').exists(),'CLI side effect')
  out.append({'value':value,'exit_code':p.returncode,'parsed_concurrency':(4 if value=='default' else int(value)) if value not in ('0','17') else None,'cache_receipts_created':False})
 save(root/'RESULT.json',out);return out

def exercise_signal(sig):
 r=ROOT/('signal_'+sig.name);r.mkdir();(r/'cache').mkdir()
 for i in range(300,318):(r/'cache'/(filename(i)+'.partial')).write_bytes(PREFIX[:8192])
 seen=[];lock=threading.Lock();release=threading.Event();active=set();maximum=[0]
 class Handler(http.server.BaseHTTPRequestHandler):
  def do_GET(self):
   fn=urllib.parse.unquote(self.path[1:]);i=int(fn.split('_mc_')[1].split('_')[0]);must(fn==filename(i),'server file')
   with lock:
    seen.append({'id':i,'request':self.requestline,'version':self.request_version,'headers':dict(self.headers),'at':stamp()});active.add(i);maximum[0]=max(maximum[0],len(active))
   try:
    self.send_response(200);self.send_header('Content-Type','image/fits');self.send_header('Content-Length','603990720');self.send_header('Content-Disposition','attachment; filename="'+fn+'"');self.end_headers()
    self.wfile.write(payload(i));self.wfile.flush();release.wait(30)
   except (BrokenPipeError,ConnectionResetError):pass
   finally:
    with lock:active.discard(i)
  def log_message(self,*a):pass
 class Server(http.server.ThreadingHTTPServer):request_queue_size=64;daemon_threads=True
 server=Server(('127.0.0.1',0),Handler);thread=threading.Thread(target=server.serve_forever);thread.start()
 cmd=[sys.executable,'-B','-c',CHILD,str(CAND),str(r),'signals',f'http://127.0.0.1:{server.server_port}'];save(r/'COMMAND.json',cmd)
 live=[];worker=None
 try:
  with (r/'worker.stdout').open('wb') as out,(r/'worker.stderr').open('wb') as err:
   worker=subprocess.Popen(cmd,stdout=out,stderr=err)
   deadline=time.monotonic()+15
   while time.monotonic()<deadline:
    must(worker.poll() is None,'executor exited before16active; '+(r/'worker.stderr').read_text())
    starts=list((r/'attempts').glob('**/CURL_START.json'));raw=list((r/'attempts').glob('**/response.bin'))
    with lock:current=list(seen);active_now=sorted(active)
    if len(starts)==len(raw)==len(current)==16 and len(active_now)==16 and all(p.stat().st_size==32768 for p in raw) and all((r/'cache'/(filename(i)+'.partial')).stat().st_size==32768 for i in range(300,316)):break
    time.sleep(.02)
   else:raise AssertionError('16active readiness not established')
   must(sorted(x['id'] for x in current)==list(range(300,316)),'distinct first16 HTTP')
   for p in starts:
    pid=getjson(p)['pid'];observed=proc_identity(pid);must(observed['state']!='Z' and observed['ppid']==worker.pid,'actual live child owner');live.append(observed)
   must(len({p['pid'] for p in live})==16,'distinct simultaneous child PIDs')
   bstart=next((r/'attempts').glob('batch-*/START.json'));bs=getjson(bstart)
   must(bs['concurrency']==16 and len(bs['queued_jobs'])==18,'18 submitted16configured')
   must(len(list((r/'attempts').glob('batch-*/*/START.json')))==16,'2 jobs queued before signal')
   before={'worker':proc_identity(worker.pid),'children':live,'observed_HTTP':current,'simultaneously_active_server_ids':active_now,'submitted_ids':[v['id'] for v in bs['queued_jobs']],'queued_ids':[316,317],'signal':sig.name,'at':stamp()};save(r/'BEFORE_SIGNAL.json',before)
   worker.send_signal(sig);worker.wait(timeout=12)
  must(worker.returncode==1,'interrupted executor return')
  child=getjson(r/'CHILD_RETURN.json');must(child['owned_children_count']==0 and child['stop'] and child['stop_signal']==sig,'child closeout')
  must(child['helper_file']==str(CAND) and child['helper_sha256']==CAND_SHA,'candidate import')
  must(child['pilot_ids']==list(range(300,308)),'only pilot prerequisite replaced')
  batch=getjson(next((r/'attempts').glob('batch-*/RETURN.json')));results=batch['results']
  must(batch['all_futures_drained'] and batch['interrupted'] and batch['stop_signal']==sig,'batch drain')
  must(len(results)==18 and [x['item']['id'] for x in results]==list(range(300,318)),'18 exact results')
  must(all(x['status']=='INTERRUPTED' for x in results),'18 typed INTERRUPTED')
  with lock:requests=list(seen)
  must(len(requests)==16 and maximum[0]==16,'no queued or duplicate HTTP')
  for request in requests:
   must(request['version']=='HTTP/1.0','HTTP1.0');must(request['headers']['Accept-Encoding']=='identity','identity encoding');must(request['headers']['Range']=='bytes=8192-','retained prefix Range preserved')
  for result in results:
   i=result['item']['id'];running=i<316;expected=payload(i) if running else PREFIX[:8192]
   must(result['source_sha256']==CAND_SHA,'perID source');must(result['executor_runtime']=={'requested':'INDEPENDENT_LOCALHOST_FIXTURE','observed':'UNKNOWN'},'runtime separation')
   must(result['item']['bytes']==603990720,'frozen whole-file size unchanged');must(result['network_bytes']==(32768 if running else 0),'perID decoded accounting')
   must(result['response_bytes_retained']==(32768 if running else 0),'perID retained accounting');must(result['appended_bytes']==(24576 if running else 0),'perID appended accounting');must(result['redundant_prefix_bytes']==(8192 if running else 0),'perID redundant accounting')
   partial=r/'cache'/(filename(i)+'.partial');must(partial.read_bytes()==expected,'exact preserved/appended partial '+str(i));must(result['partial_after']['sha256']==sha(partial),'partial digest')
   must(result['actual_network_bytes']=='UNKNOWN' and result['received_bytes_not_retained']==0,'honest lowerbound accounting');must(result['auxiliary_decoded_bytes_lower_bound']==0,'no auxiliary transfer')
  must(batch['network_bytes']==16*32768,'batch decoded sum');must(batch['auxiliary_decoded_bytes_lower_bound']==0,'batch auxiliary sum')
  must(len(list((r/'attempts').glob('batch-*/*/RETURN.json')))==18,'all perID return files')
  must(not list((r/'cache').glob('*.fits')) and not list((r/'cache').glob('*.verified.json')),'no failed final promotion')
  post=[]
  for p in (r/'attempts').glob('**/CURL_START.json'):
   start=getjson(p);ret=getjson(p.parent/'CURL_RETURN.json');must(not pathlib.Path(f'/proc/{start["pid"]}').exists(),'no orphan '+str(start['pid']));must(ret['all_child_processes_reaped'] and not ret['cleanup_errors'],'clean perchild reap');must(ret['decoded_bytes_read_lower_bound']==32768,'curl lowerbound');must((p.parent/'response.bin').read_bytes()==payload(getjson(p.parent/'RETURN.json')['item']['id']),'exact raw bytes');post.append({'pid':start['pid'],'absent':True,'CURL_RETURN':ret})
  summary={'signal':sig.name,'result':'PASS','active_children_observed':16,'queued_without_HTTP':2,'typed_interrupted_results':18,'raw_and_partial_payloads_exact':True,'decoded_lower_bound_bytes':batch['network_bytes'],'preserved_prefix_bytes':16*8192,'appended_bytes':16*24576,'future_drain':True,'child_reaps':post,'no_failed_finals':True,'requests':requests,'at':stamp()}
  save(r/'RESULT.json',summary);return {k:v for k,v in summary.items() if k not in ('child_reaps','requests')}
 finally:
  if worker is not None and worker.poll() is None:
   worker.send_signal(signal.SIGTERM)
   try:worker.wait(timeout=10)
   except subprocess.TimeoutExpired:
    for observed in live:
     try:
      now=proc_identity(observed['pid'])
      if now['ppid']==worker.pid and now['start_ticks']==observed['start_ticks']:os.kill(observed['pid'],signal.SIGTERM)
     except FileNotFoundError:pass
    worker.kill();worker.wait()
  release.set();server.shutdown();thread.join();server.server_close()


def nooverwrite_checks():
 spec=importlib.util.spec_from_file_location('source_nooverwrite',CAND);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
 must(m.digest(m.__file__)==CAND_SHA,'nooverwrite import binding')
 catalog=getjson(m.BASE/'PLA_PR4_ALL_SIMULATED_MAPS.json');item=m.select(catalog,[300])[0];out=[]
 for case in ('unreceipted_final','corrupt_receipted_final','orphan_receipt'):
  r=ROOT/case;r.mkdir();(r/'cache').mkdir();(r/'attempts').mkdir();final=r/'cache'/item['filename'];receipt=pathlib.Path(str(final)+'.verified.json');partial=pathlib.Path(str(final)+'.partial');partial.write_bytes(b'PREEXISTING_PARTIAL_MUST_SURVIVE')
  if case!='orphan_receipt':final.write_bytes(b'PREEXISTING_FINAL_MUST_SURVIVE')
  if case!='unreceipted_final':save(receipt,{'item':item,'sha256':'0'*64})
  before={str(p):{'sha256':sha(p),'bytes':p.stat().st_size,'inode':p.stat().st_ino} for p in (partial,final,receipt) if p.exists()}
  calls=[]
  def forbidden(*args,**kwargs):calls.append(True);raise AssertionError('unexpected network')
  m.STOP.clear();result=m.acquire(item,m.Storage(r/'cache',fixture=True),r/'attempts',opener=forbidden)
  must(result['status']=='ERROR' and not calls,'nooverwrite rejects beforenetwork')
  must(before=={str(p):{'sha256':sha(p),'bytes':p.stat().st_size,'inode':p.stat().st_ino} for p in (partial,final,receipt) if p.exists()},'nooverwrite bytes/inodes')
  save(r/'RESULT.json',{'case':case,'status':'PASS','source_file':m.__file__,'source_sha256':CAND_SHA,'preserved':before,'acquire':result,'network_calls':0});out.append({'case':case,'result':'PASS'})
 return out

if __name__=='__main__':
 save(ROOT/'ENVIRONMENT.json',{'started':stamp(),'python':sys.version,'executable':sys.executable,'cwd':os.getcwd(),'requested_reviewer_runtime':{'model':'gpt-6-astra','reasoning_effort':'xhigh'},'observed_reviewer_runtime':'UNKNOWN','production_network_requests':0})
 result={'source':source_check()};print('SOURCE PASS',flush=True)
 result['CLI']=cli_checks();print('CLI 7 cases PASS',flush=True)
 result['signals']=[]
 for sig in (signal.SIGTERM,signal.SIGINT):result['signals'].append(exercise_signal(sig));print(sig.name+' 16 active + 2 queued PASS',flush=True)
 result['nooverwrite']=nooverwrite_checks();print('NOOVERWRITE 3 cases PASS',flush=True)
 must(sha(CAND)==CAND_SHA and sha(OLD)==OLD_SHA,'final source recheck')
 result['finished']=stamp();save(ROOT/'CHECKS.json',result);print('INDEPENDENT CHECKS PASS',flush=True)
