#!/usr/bin/env python3
"""Explicit-batch acquisition only. No scientific producer or controller writes."""
import http.client, urllib.parse, signal
import argparse, concurrent.futures, contextlib, fcntl, hashlib, json, os
from email.message import Message
from email.utils import collapse_rfc2231_value
import pathlib, shutil, subprocess, sys, threading, time, urllib.request, uuid
BASE=pathlib.Path('/mnt/extdrive/workdir/htt_open_data/r36_pr4_contract_preparation')
SEALS={'IMPLEMENTATION_CONTRACT.json':'fa08a55ccbf7a5e488cfc2866f0138d0682d3732fe01a785870f8adf9fc677d4',
       'ACQUISITION_CHECKPOINT_CLARIFICATION.json':'e8c7b97cc3146ebb992e7ece73b3549bcfe2528743d2c6a7b54fcc8c7e7d0882',
       'PLA_PR4_ALL_SIMULATED_MAPS.json':'05ae88c82a63887829a4f691b8dbfccfdbba7268c5a230ecc5546c5e7b0224f0'}
RESEARCH=pathlib.Path('/mnt/extdrive/workdir/htt_open_data/r36_pr4_transfer_source_research/RESEARCH_RETURN.json')
RESEARCH_SHA256='c3b3193f2260f3ec8e715ea345e40d85777a8dcdc41421f148ebbe12d0c0b451'
ADDENDUM=pathlib.Path('/mnt/extdrive/workdir/htt_open_data/r36_pr4_transfer_source_research/CHECKPOINT_002_ADDENDUM.json')
ADDENDUM_SHA256='f8278d1006496bf81bbd51afa970db9e0f6b1958af1a861531b27edaa07cfccf'
TASK='R36-06-PR4-MORPHOLOGY'
PACKET='902ebd6a521d6b31864e0bfce63336c62d6cec5ff2f6c3128de7ab68046fce35'
RESERVE=2*1024**3
CHUNK=1024*1024
DISK_LOCK=threading.Lock()
STOP=threading.Event()
CHILD_LOCK=threading.RLock()
OWNED_CHILDREN=set()
STOP_SIGNAL=None
def request_stop(signum=None,frame=None):
 global STOP_SIGNAL
 STOP_SIGNAL=signum;STOP.set()
 # Signal only retained Popen identities belonging to this executor. No group kill.
 with CHILD_LOCK:
  for child in tuple(OWNED_CHILDREN):
   if child.poll() is None:
    try:child.terminate()
    except ProcessLookupError:pass

def install_stop_handlers():
 if threading.current_thread() is threading.main_thread():
  signal.signal(signal.SIGTERM,request_stop);signal.signal(signal.SIGINT,request_stop)

def check_stop():
 if STOP.is_set():raise InterruptedError('controlled acquisition stop signal='+str(STOP_SIGNAL))

def digest(p):
 h=hashlib.sha256()
 with open(p,'rb') as f:
  for b in iter(lambda:f.read(CHUNK),b''): h.update(b)
 return h.hexdigest()
def write_json(p,v):
 with open(p,'x') as f: json.dump(v,f,indent=2);f.write('\n');f.flush();os.fsync(f.fileno())
def name(i):return f'npipe6v20_commander_cmb_2048_mc_{i:04d}_005a.fits'
def url(i):return 'https://pla.esac.esa.int/pla/aio/product-action?SIMULATED_MAP.FILE_ID='+name(i)
def select(catalog,ids):
 if len(ids)!=len(set(ids)) or not ids or any(i not in range(300,400) for i in ids): raise ValueError('Explicit distinct IDs must be within frozen 0300-0399')
 selected=[]
 for i in ids:
  rows=[r for r in catalog['data'] if r['SIMULATED_MAP__FILE_ID']==name(i)]
  if len(rows)!=1:raise ValueError('catalog ID missing/ambiguous')
  r=rows[0]
  for k,v in {'RELEASE__NAME':'PR4','SIMULATED_MAP__TYPE':'COMP_SEPARATION','SIMULATED_MAP__PERIOD':'full','SIMULATED_MAP__VERSION_MAP':'npipe6v20','SIMULATED_MAP__MC_NUMBER':i,'SIMULATED_MAP__SIZE':603990720,'SIMULATED_MAP__COMP_SEP_METHOD':'commander','SIMULATED_MAP__COMP_SEP_TYPE':'cmb'}.items():
   if r.get(k)!=v:raise ValueError('catalog role/binding mismatch '+k)
  selected.append({'id':i,'filename':name(i),'url':url(i),'bytes':r['SIMULATED_MAP__SIZE'],'catalog_row':r})
 return selected
def cards(block):
 d={}
 for off in range(0,len(block),80):
  c=block[off:off+80].decode('ascii')
  if c[:8].strip()=='END':return d
  if c[8:10]=='= ':
   v=c[10:].split('/')[0].strip();d[c[:8].strip()]=v.strip("' ")
 raise ValueError('unterminated FITS header')
def role(prefix):
 # Primary and first extension; parse FITS header blocks, not values in payload.
 headers=[];pos=0
 for _ in range(2):
  start=pos
  while True:
   block=prefix[pos:pos+2880]
   if len(block)!=2880:raise ValueError('short FITS header')
   pos+=2880
   if any(block[x:x+8].strip()==b'END' for x in range(0,2880,80)):break
  headers.append(cards(prefix[start:pos]))
 if headers[0].get('SIMPLE')!='T' or headers[0].get('NAXIS')!='0':raise ValueError('wrong primary HDU')
 h=headers[1]
 required={'METHOD':'Commander','AST-COMP':'CMB','PIXTYPE':'HEALPIX','BITPIX':'8','NAXIS':'2','NAXIS1':'12288','NAXIS2':'49152','PCOUNT':'0','GCOUNT':'1','TTYPE1':'I_STOKES','TFORM1':'1024E','TUNIT1':'uK_CMB','XTENSION':'BINTABLE','NSIDE':'2048','ORDERING':'NESTED','COORDSYS':'GALACTIC','POLCCONV':'COSMO','TFIELDS':'3','TTYPE2':'Q_STOKES','TTYPE3':'U_STOKES','TUNIT2':'uK_CMB','TUNIT3':'uK_CMB','TFORM2':'1024E','TFORM3':'1024E'}
 if any(h.get(k)!=v for k,v in required.items()):raise ValueError('wrong polarized FITS role/schema')
 return h
def validate_disposition(value,expected):
 if not value:return # Frozen absent-header policy unchanged.
 message=Message();message['Content-Disposition']=value
 filenames=[v for k,v in message.get_params(header='content-disposition',unquote=True)[1:] if k.lower()=='filename']
 if not filenames:raise ValueError('response disposition has no filename')
 for filename in filenames:
  if isinstance(filename,tuple):filename=collapse_rfc2231_value(filename,errors='strict')
  if filename!=expected:raise ValueError('response filename mismatch')
def process_identity():
 return {'pid':os.getpid(),'parent_pid':os.getppid(),'session_id':os.getsid(0),'cwd':os.getcwd(),'argv':sys.argv,'proc_stat':pathlib.Path('/proc/self/stat').read_text(),'boot_id':pathlib.Path('/proc/sys/kernel/random/boot_id').read_text().strip()}
class Storage:
 def __init__(self,root,reserve=RESERVE,fixture=False):
  self.root=pathlib.Path(root).resolve();self.reserve=reserve;self.fixture=fixture
  if not fixture:
   out=subprocess.check_output(['findmnt','-J','-T',str(self.root)],text=True)
   m=json.loads(out)['filesystems'][0]
   if m['target']!='/mnt/extdrive' or m['source']!='/dev/sda2' or m['fstype']!='fuseblk':raise ValueError('verified external mount absent/changed')
   if not self.root.is_relative_to(pathlib.Path('/mnt/extdrive')):raise ValueError('wrong target root')
  self.dev=self.root.stat().st_dev
 def check(self,n=0):
  if self.root.stat().st_dev!=self.dev or (not self.fixture and not os.path.ismount('/mnt/extdrive')):raise OSError('mount changed')
  if shutil.disk_usage(self.root).free-n<self.reserve:raise OSError('2GiB reserve would be violated')
 def write(self,f,b):
  with DISK_LOCK:
   self.check(len(b));f.write(b);f.flush()
def stat_identity(s):return (s.st_dev,s.st_ino,s.st_size,s.st_mtime_ns,s.st_ctime_ns)
def verify_cache(item,root):
 final=root/item['filename'];receipt=pathlib.Path(str(final)+'.verified.json')
 if not final.exists() or not receipt.exists():raise ValueError('completed target missing or has no verification receipt; preserved')
 old=json.loads(receipt.read_text())
 if old['item']!=item or final.stat().st_size!=item['bytes'] or digest(final)!=old['sha256']:raise ValueError('cache mismatch; target preserved')
 with open(final,'rb') as f:role(f.read(11520))
 return old['sha256']
def validate_handoff(path,sha):
 if path.resolve()!=pathlib.Path('/mnt/extdrive/workdir/htt_open_data/r36_pr4_actual/checkpoint/WORKER_HANDOFF_002.json') or sha!='013af5f0b4614169d881a74e7aa87a0ad38a8182496353d12ddaf4690f1c20ab':raise ValueError('frozen handoff changed')
 if digest(path)!=sha:raise ValueError('frozen handoff changed')
 h=json.loads(path.read_text());b=h['binding']
 if b['sequence']!=2 or b['task_id']!=TASK or b['packet_id']!=PACKET or b['agent_id']!='/root/rc_902ebd6a521d6b31':raise ValueError('current checkpoint002 binding required')
 if not h['handoff_complete'] or not h['inventory_complete'] or h['snapshot']['queued_writers'] or h['snapshot']['future_launchers']:raise ValueError('handoff not quiescent')
 if any(p.get('state') not in ('exited','stopped') for p in h['snapshot']['processes']):raise ValueError('handoff has live processes')
 return h

def validate_transport_url(value,item):
 u=urllib.parse.urlsplit(value)
 parts=u.path.split('/')
 if u.scheme not in ('http','https') or u.netloc!='pla.esac.esa.int' or u.query or u.fragment or u.username or len(parts)!=7 or parts[1]!='ftp_public' or not parts[2].startswith('anonymous') or not parts[2][9:].isdigit() or parts[3:]!=['simulated_maps','PR4','comp_separation',item['filename']]:
  raise ValueError('unqualified official product URL')
 return value

class CurlResponse:
 """No redirects, retries, resume or walltime/file cap. Pipe bounds buffering.
 Decoded bytes read by parent are a lower bound on actual received bytes.
 """
 def __init__(self,request,attempt,storage):
  self.attempt=attempt;self.storage=storage;self.count=0;self.exit_code=None
  self.header_path=attempt/'curl.headers';self.err=open(attempt/'curl.stderr','xb')
  self.command=['curl','--http1.0','--silent','--show-error','--connect-timeout','60','--header','Accept-Encoding: identity','--user-agent','HTT-R36-06-acquisition/2','--dump-header',str(self.header_path),'--url',request.full_url]
  # Preserve the reviewed Range-ignored200 path; never ask curl to append/resume.
  if request.has_header('Range'):self.command.extend(['--header','Range: '+request.get_header('Range')])
  self.proc=None;self.closed=False;self.cleanup_errors=[]
  try:
   with CHILD_LOCK:
    check_stop()
    self.proc=subprocess.Popen(self.command,stdout=subprocess.PIPE,stderr=self.err)
    OWNED_CHILDREN.add(self.proc)
    check_stop()
   try:child_stat=pathlib.Path(f'/proc/{self.proc.pid}/stat').read_text()
   except FileNotFoundError:child_stat='UNAVAILABLE; child already exited'
   write_json(attempt/'CURL_START.json',{'pid':self.proc.pid,'proc_stat':child_stat,'command':self.command,'parent':process_identity()})
   deadline=time.monotonic()+65
   while True:
    check_stop()
    data=self.header_path.read_bytes() if self.header_path.exists() else b''
    blocks=data.replace(b'\r\n',b'\n').split(b'\n\n')
    complete=[b for b in blocks[:-1] if b.startswith(b'HTTP/') and not b.split(b'\n',1)[0].endswith(b'Connection established')]
    if complete:
     block=complete[-1];line,rest=block.split(b'\n',1);self.status=int(line.split()[1]);self.http_version=line.split()[0].decode();self.headers=http.client.parse_headers(__import__('io').BytesIO(rest+b'\n\n'));break
    if self.proc.poll() is not None:raise OSError('curl ended before response headers')
    if time.monotonic()>deadline:raise TimeoutError('response header timeout')
    storage.check();time.sleep(.02)
  except BaseException:self.close();raise
 def read(self,n):
  check_stop()
  b=self.proc.stdout.read1(n);self.count+=len(b)
  if not b:
   self.exit_code=self.proc.wait()
   if self.exit_code:raise OSError('curl exit '+str(self.exit_code))
  return b
 read1=read
 def close(self):
  if self.closed:return
  self.closed=True
  # Cleanup is protected immediately after Popen, including failed START writes.
  # A secondary receipt/close error must not replace the primary transfer error.
  if self.proc is not None:
   try:
    if self.proc.poll() is None:self.proc.terminate()
    try:self.proc.wait(timeout=2)
    except subprocess.TimeoutExpired:self.proc.kill();self.proc.wait()
    self.exit_code=self.proc.returncode
   except BaseException as e:self.cleanup_errors.append(repr(e))
   finally:
    try:self.proc.stdout.close()
    except BaseException as e:self.cleanup_errors.append(repr(e))
    with CHILD_LOCK:OWNED_CHILDREN.discard(self.proc)
  try:self.err.close()
  except BaseException as e:self.cleanup_errors.append(repr(e))
  value={'exit_code':self.exit_code,'decoded_bytes_read_lower_bound':self.count,'actual_network_bytes':'UNKNOWN; subprocess/kernel buffering not measured','all_child_processes_reaped':self.proc is None or self.proc.poll() is not None,'interrupted':STOP.is_set(),'stop_signal':STOP_SIGNAL,'cleanup_errors':self.cleanup_errors}
  try:write_json(self.attempt/'CURL_RETURN.json',value)
  except BaseException as e:
   self.cleanup_errors.append(repr(e))
   try:
    with open(self.attempt/'CURL_CLEANUP_ERROR.txt','x') as f:f.write(json.dumps(value)+'\n'+repr(e)+'\n')
   except BaseException:pass
 def __enter__(self):return self
 def __exit__(self,*args):self.close()

def resolve_official(item,attempt,storage):
 oid=item['catalog_row']['SIMULATED_MAP__SIMULATED_MAP_OID']
 endpoint='https://pla.esac.esa.int/pla-sl/urldata-action?SIMULATED_MAP.SIMULATED_MAP_OID='+str(oid)
 request=urllib.request.Request(endpoint,headers={'Accept-Encoding':'identity'})
 write_json(attempt/'RESOLVER_START.json',{'url':endpoint,'oid':oid,'item':item,'process':process_identity()})
 resolver_attempt=attempt/'resolver-transport';resolver_attempt.mkdir()
 with CurlResponse(request,resolver_attempt,storage) as r:
  if r.status not in (200,206):raise ValueError('resolver status')
  body=b''
  with open(attempt/'resolver.json','xb') as retained:
   try:
    while len(body)<16385:
     chunk=r.read(16385-len(body))
     if not chunk:break
     storage.write(retained,chunk);body+=chunk
   finally:
    retained.flush();os.fsync(retained.fileno())
    write_json(attempt/'RESOLVER_HEADERS.json',{'status':r.status,'headers':dict(r.headers),'bytes_retained':retained.tell(),'wire_bytes':'UNKNOWN'})
 if len(body)>16384:raise ValueError('resolver metadata too large')
 values=json.loads(body)
 if not isinstance(values,list) or len(values)!=1 or not isinstance(values[0],str):raise ValueError('resolver must return one official URL')
 direct=validate_transport_url(values[0],item)
 secure=urllib.parse.urlunsplit(urllib.parse.urlsplit(direct)._replace(scheme='https'))
 # Per-ID qualification: never extrapolate an anonymous token or prior ID.
 prefixes=[]
 for idx,u in enumerate((direct,secure)):
  probe=attempt/f'qualification-{idx}';probe.mkdir()
  with CurlResponse(urllib.request.Request(u),probe,storage) as r:
   if r.status!=200:raise ValueError('qualification needs HTTP200')
   validate_disposition(r.headers.get('Content-Disposition'),item['filename'])
   b=b''
   with open(probe/'prefix.bin','xb') as retained:
    try:
     while len(b)<11520:
      chunk=r.read(11520-len(b))
      if not chunk:break
      storage.write(retained,chunk);b+=chunk
    finally:retained.flush();os.fsync(retained.fileno())
   role(b);prefixes.append(b)
 if prefixes[0]!=prefixes[1]:raise ValueError('HTTP/HTTPS prefix qualification mismatch')
 write_json(attempt/'RESOLUTION.json',{'canonical_url':item['url'],'resolver_url':endpoint,'returned_url':direct,'transport_url':secure,'same_prefix_bytes':11520,'whole_file_identity':'NOT_ESTABLISHED_BY_PREFIX'})
 return secure

def acquire(item,storage,attempt_root,opener=None, mode="canonical-http10", runtime=None):
 """opener injection exists for localhost fixtures; production CLI has no URL override."""
 install_stop_handlers()
 attempt=pathlib.Path(attempt_root)/f'{item["id"]:04d}-{uuid.uuid4().hex}';attempt.mkdir()
 start=time.monotonic();rec={'item':item,'process':process_identity(),'utc_start':time.time(),'network_bytes':0,'redundant_prefix_bytes':0,'appended_bytes':0,'provider_checksum':'UNKNOWN','source_sha256':digest(__file__),'transport_mode':mode,'executor_runtime':runtime or {'requested':'UNKNOWN','observed':'UNKNOWN'},'network_bytes_semantics':'decoded bytes read; lower bound on network reception','actual_network_bytes':'UNKNOWN'}
 write_json(attempt/'START.json',rec)
 final=storage.root/item['filename'];partial=storage.root/(item['filename']+'.partial')
 lock=storage.root/(item['filename']+'.lock')
 try:
  check_stop()
  if item['filename']!=name(item['id']) or item['url']!=url(item['id']):raise ValueError('URL/ID binding changed')
  with open(lock,'a+b') as lf:
   fcntl.flock(lf,fcntl.LOCK_EX|fcntl.LOCK_NB)
   if final.exists():
    rec.update(status='CACHE_VERIFIED',sha256=verify_cache(item,storage.root));return rec
   if pathlib.Path(str(final)+'.verified.json').exists():raise ValueError('orphan receipt preserved; no overwrite')
   before=partial.stat() if partial.exists() else None
   prefix_size=before.st_size if before else 0
   rec['retained_prefix']={'bytes':prefix_size,'sha256':digest(partial) if before else None,'stat':list(before) if before else None}
   if prefix_size>item['bytes']:raise ValueError('partial exceeds catalog size')
   transport_url=resolve_official(item,attempt,storage) if mode=='official-resolver-http10' else item['url']
   if mode not in ('canonical-http10','official-resolver-http10'):raise ValueError('unknown transport mode')
   rec['transport_url']=transport_url
   request=urllib.request.Request(transport_url,headers={'User-Agent':'HTT-R36-06-acquisition/1','Accept-Encoding':'identity'})
   if prefix_size:request.add_header('Range',f'bytes={prefix_size}-')
   with (opener(request,timeout=60) if opener else CurlResponse(request,attempt,storage)) as response, open(attempt/'response.bin','xb') as raw:
    rec['http_status']=response.status;rec['response_headers']=dict(response.headers)
    length=response.headers.get('Content-Length')
    if length is not None and int(length)!=item['bytes']:raise ValueError('HTTP content length contradicts catalog')
    # Full GET is required for exact full-prefix comparison. If server honors Range,
    # stop without append; do not fabricate whole-response identity from a suffix.
    if response.status!=200:raise ValueError('full HTTP200 required; retained prefix unchanged')
    if 'fits' not in response.headers.get('Content-Type','').lower() and 'octet-stream' not in response.headers.get('Content-Type','').lower():raise ValueError('unexpected content type')
    disposition=response.headers.get('Content-Disposition','')
    validate_disposition(disposition,item['filename'])
    h=hashlib.sha256();head=b'';compared=0;out=None
    try:
     with contextlib.ExitStack() as stack:
      prior=stack.enter_context(open(partial,'rb')) if before else None
      reader=getattr(response,'read1',response.read)
      for b in iter(lambda:(check_stop(),reader(CHUNK))[1],b''):
       rec['network_bytes']+=len(b);h.update(b);storage.write(raw,b)
       if rec['network_bytes']>item['bytes']:raise ValueError('response exceeds catalog size')
       head=(head+b)[:11520]
       # Keep all incoming bytes on disk until enough header data and prefix checked.
       if compared<prefix_size:
        count=min(len(b),prefix_size-compared)
        if prior.read(count)!=b[:count]:raise ValueError('retained prefix mismatch; unchanged')
        compared+=count;rec['redundant_prefix_bytes']=compared
       if len(head)>=11520 and out is None and compared==prefix_size:
        role(head)
        if before and stat_identity(partial.stat())!=stat_identity(before):raise ValueError('concurrent partial change')
        out=stack.enter_context(open(partial,'ab' if before else 'xb'))
        # Replay verified suffix from retained response, then stream later chunks.
        raw.flush()
        with open(attempt/'response.bin','rb') as replay:
         replay.seek(prefix_size)
         for suffix in iter(lambda:replay.read(CHUNK),b''):
          storage.write(out,suffix);rec['appended_bytes']+=len(suffix)
       elif out is not None:
        storage.write(out,b);rec['appended_bytes']+=len(b)
      if out:out.flush();os.fsync(out.fileno())
    finally:raw.flush();os.fsync(raw.fileno())
    if rec['network_bytes']!=item['bytes']:raise ValueError('short response; incomplete preserved')
    if out is None:raise ValueError('short header/prefix; original unchanged')
    length=response.headers.get('Content-Length')
    if length and int(length)!=rec['network_bytes']:raise ValueError('HTTP content length disagreement')
    whole=digest(partial)
    if partial.stat().st_size!=item['bytes'] or whole!=h.hexdigest():raise ValueError('whole response/file mismatch')
    with open(partial,'rb') as f:role(f.read(11520))
    rec.update(status='COMPLETE',sha256=whole,clean_eof=True)
    # No replace: link fails if another target exists. Keep partial as evidence.
    os.link(partial,final)
    write_json(pathlib.Path(str(final)+'.verified.json'),{'item':item,'sha256':whole,'attempt':str(attempt)})
    return rec
 except BaseException as e:
  rec.update(status='INTERRUPTED' if STOP.is_set() else 'ERROR',error=repr(e),stop_signal=STOP_SIGNAL);return rec
 finally:
  rec['interrupted']=STOP.is_set();rec['stop_signal']=STOP_SIGNAL
  rec['elapsed_seconds']=time.monotonic()-start
  raw_path=attempt/'response.bin'
  rec['response_bytes_retained']=raw_path.stat().st_size if raw_path.exists() else 0
  aux=[]
  for receipt in list(attempt.glob('qualification-*/CURL_RETURN.json'))+list(attempt.glob('resolver-transport/CURL_RETURN.json')):
   aux.append({'path':str(receipt),**json.loads(receipt.read_text())})
  rec['qualification_attempts']=aux
  rec['auxiliary_decoded_bytes_lower_bound']=sum(v['decoded_bytes_read_lower_bound'] for v in aux)
  metadata=attempt/'RESOLVER_HEADERS.json'
  rec['resolver_metadata_bytes_retained']=json.loads(metadata.read_text())['bytes_retained'] if metadata.exists() else 0
  rec['received_bytes_not_retained']=rec['network_bytes']-rec['response_bytes_retained']
  if partial.exists():rec['partial_after']={'bytes':partial.stat().st_size,'sha256':digest(partial)}
  write_json(attempt/'RETURN.json',rec)
  (attempt/'stderr.txt').write_text(rec.get('error','')+'\n')
  (attempt/'stdout.txt').write_text(json.dumps({'id':item['id'],'status':rec.get('status'),'error':rec.get('error')})+'\n')
def main():
 install_stop_handlers()
 ap=argparse.ArgumentParser(description=__doc__)
 ap.add_argument('--ids',nargs='+',type=int,required=True,help='Explicit batch; start with 300..307. Extension requires another explicit batch.')
 ap.add_argument('--cache',type=pathlib.Path,required=True);ap.add_argument('--receipts',type=pathlib.Path,required=True);ap.add_argument('--concurrency',type=int,default=4)
 ap.add_argument('--handoff',type=pathlib.Path,required=True);ap.add_argument('--handoff-sha256',required=True)
 ap.add_argument('--mode',choices=['canonical-http10','official-resolver-http10'],required=True)
 ap.add_argument('--requested-executor-runtime',required=True);ap.add_argument('--observed-executor-runtime',default='UNKNOWN')
 a=ap.parse_args()
 if not 1<=a.concurrency<=4:ap.error('concurrency must be within 1..4')
 for n,s in SEALS.items():
  if digest(BASE/n)!=s:raise ValueError('frozen source seal changed: '+n)
 if digest(RESEARCH)!=RESEARCH_SHA256 or digest(ADDENDUM)!=ADDENDUM_SHA256:raise ValueError('frozen repair source changed')
 validate_handoff(a.handoff,a.handoff_sha256)
 catalog=json.loads((BASE/'PLA_PR4_ALL_SIMULATED_MAPS.json').read_text())
 items=select(catalog,a.ids)
 storage=Storage(a.cache);storage.check();a.receipts.mkdir(parents=True,exist_ok=True)
 if any(i>307 for i in a.ids):
  for pilot in select(catalog,list(range(300,308))):verify_cache(pilot,storage.root)
 batch=a.receipts/('batch-'+uuid.uuid4().hex);batch.mkdir()
 write_json(batch/'START.json',{'process':process_identity(),'queued_jobs':items,'concurrency':a.concurrency,'utc':time.time(),'source_bindings':{**{str(BASE/n):digest(BASE/n) for n in SEALS},str(a.handoff):a.handoff_sha256,str(RESEARCH):RESEARCH_SHA256,str(ADDENDUM):ADDENDUM_SHA256},'requested_runtime':a.requested_executor_runtime,'observed_runtime':a.observed_executor_runtime,'transport_mode':a.mode,'historical_accounting':'WORKER_HANDOFF_002 and all historical attempts retained; no reset; additive transport only'})
 start=time.monotonic()
 with concurrent.futures.ThreadPoolExecutor(max_workers=a.concurrency) as ex:
  futures=[ex.submit(acquire,i,storage,batch,mode=a.mode,runtime={'requested':a.requested_executor_runtime,'observed':a.observed_executor_runtime}) for i in items]
  results=[f.result() for f in futures] # context drains every future; no daemon/resume
 write_json(batch/'RETURN.json',{'results':results,'elapsed_seconds':time.monotonic()-start,'all_futures_drained':True,'interrupted':STOP.is_set(),'stop_signal':STOP_SIGNAL,'network_bytes':sum(r['network_bytes'] for r in results),'auxiliary_decoded_bytes_lower_bound':sum(r['auxiliary_decoded_bytes_lower_bound'] for r in results),'actual_network_bytes':'UNKNOWN; byte counts are decoded lower bounds'})
 return 0 if all(r['status'] in ['COMPLETE','CACHE_VERIFIED'] for r in results) else 1
if __name__=='__main__':sys.exit(main())
