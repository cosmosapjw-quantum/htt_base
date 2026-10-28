import copy,json,pathlib,unittest,urllib.request
import fetch_commander_mc as m
from test_fetch_commander_mc import Cases,GOOD,Handler
class Transport(Cases):
 def opener(self,req,timeout):
  local=urllib.request.Request('http://127.0.0.1:'+str(self.server.server_port)+'/?'+req.full_url.split('?')[1],headers=dict(req.header_items()))
  # Explicit localhost fixture injection; CLI cannot override URLs.
  return m.CurlResponse(local,self.current_attempt(req),self.store)
 def current_attempt(self,req):
  filename=req.full_url.split('=')[-1];ident=int(filename.split('_mc_')[1][:4])
  return next(p for p in self.logs.iterdir() if p.name.startswith(f'{ident:04d}-') and not (p/'RETURN.json').exists())
 def test_curl_clean_short_eof_rejected(self):
  self.server.payload=GOOD[:20000];r=self.runitem();self.assertEqual(r['status'],'ERROR');self.assertEqual(r['network_bytes'],20000)
  a=next(self.logs.glob('*/CURL_RETURN.json'));self.assertEqual(json.loads(a.read_text())['exit_code'],0);self.assertFalse((self.cache/m.name(300)).exists())
 def test_curl_records_actual_request_headers_pid_and_runtime(self):
  r=m.acquire(self.item(),self.store,self.logs,self.opener,runtime={'requested':'gpt-6-sol/medium','observed':'UNKNOWN'})
  self.assertEqual(r['status'],'COMPLETE');self.assertEqual(r['executor_runtime']['requested'],'gpt-6-sol/medium')
  a=next(self.logs.glob('*/CURL_START.json'));v=json.loads(a.read_text());self.assertIn('--http1.0',v['command']);self.assertTrue(v['proc_stat']);self.assertTrue((a.parent/'curl.headers').exists())
 def test_unexpected206_preserves_prefix(self):
  old=Handler.do_GET
  def response(handler):
   handler.send_response(206);handler.send_header('Content-Type','image/fits');handler.end_headers();handler.wfile.write(GOOD)
  Handler.do_GET=response
  try:
   p=self.partial(GOOD[:17000]);r=self.runitem();self.assertEqual(r['status'],'ERROR');self.assertEqual(p.read_bytes(),GOOD[:17000])
  finally:Handler.do_GET=old
 def test_controlled_interruption_reaps_and_accounts(self):
  class Interrupted:
   status=200;headers={'Content-Type':'image/fits'}
   def __enter__(self):return self
   def __exit__(self,*a):pass
   def read(self,n):
    if hasattr(self,'done'):raise KeyboardInterrupt('fixture interruption')
    self.done=True;return GOOD[:20000]
  r=m.acquire(self.item(),self.store,self.logs,lambda *a,**k:Interrupted(),runtime={'requested':'gpt-6-sol/medium','observed':'UNKNOWN'})
  self.assertEqual(r['status'],'ERROR');self.assertEqual(r['network_bytes'],20000);self.assertEqual(r['response_bytes_retained'],20000);self.assertFalse((self.cache/m.name(300)).exists())
class Binding(unittest.TestCase):
 def test_real_checkpoint002_and_source_seals(self):
  m.validate_handoff(pathlib.Path('/mnt/extdrive/workdir/htt_open_data/r36_pr4_actual/checkpoint/WORKER_HANDOFF_002.json'),'013af5f0b4614169d881a74e7aa87a0ad38a8182496353d12ddaf4690f1c20ab')
  self.assertEqual(m.digest(m.RESEARCH),m.RESEARCH_SHA256)
  for n,s in m.SEALS.items():self.assertEqual(m.digest(m.BASE/n),s)
 def test_source_drift_fails_closed(self):
  with self.assertRaisesRegex(ValueError,'frozen handoff changed'):m.validate_handoff(pathlib.Path('/mnt/extdrive/workdir/htt_open_data/r36_pr4_actual/checkpoint/WORKER_HANDOFF_002.json'),'0'*64)
 def test_exact_dynamic_product_url(self):
  i={'filename':m.name(300)};u='http://pla.esac.esa.int/ftp_public/anonymous2428723/simulated_maps/PR4/comp_separation/'+m.name(300)
  self.assertEqual(m.validate_transport_url(u,i),u)
  for v in (u.replace('pla.esac.esa.int','evil.test'),u.replace('0300','0301'),u.replace('PR4','PR3'),u+'?x=1',u.replace('anonymous2428723','inferred')):
   with self.assertRaises(ValueError):m.validate_transport_url(v,i)
class Resolver(Cases):
 def test_per_id_resolver_chain_and_qualification(self):
  from unittest.mock import patch
  item=m.select(json.loads((m.BASE/'PLA_PR4_ALL_SIMULATED_MAPS.json').read_text()),[301])[0]
  endpoint='https://pla.esac.esa.int/pla-sl/urldata-action?SIMULATED_MAP.SIMULATED_MAP_OID=93001'
  returned='http://pla.esac.esa.int/ftp_public/anonymous999/simulated_maps/PR4/comp_separation/'+m.name(301)
  class Metadata:
   status=200;headers={}
   def geturl(self):return endpoint
   def read(self,n):return json.dumps([returned]).encode()
   def __enter__(self):return self
   def __exit__(self,*a):pass
  calls=[]
  class Qualified:
   status=200;headers={}
   def __init__(self,req,attempt,storage):calls.append(req.full_url);self.pos=0;self.body=json.dumps([returned]).encode() if req.full_url==endpoint else GOOD
   def read(self,n):b=self.body[self.pos:self.pos+n];self.pos+=len(b);return b
   def __enter__(self):return self
   def __exit__(self,*a):pass
  attempt=self.logs/'resolver-fixture';attempt.mkdir()
  with patch.object(m.urllib.request,'urlopen',return_value=Metadata()) as opened,patch.object(m,'CurlResponse',Qualified):
   result=m.resolve_official(item,attempt,self.store)
  self.assertFalse(opened.called)
  self.assertEqual(calls,[endpoint,returned,returned.replace('http:','https:')]);self.assertEqual(result,calls[2]);self.assertEqual(item['url'],m.url(301))
  self.assertTrue((attempt/'resolver.json').exists());self.assertTrue((attempt/'RESOLUTION.json').exists())
if __name__=='__main__':unittest.main(verbosity=2)
