import concurrent.futures,http.server,json,os,pathlib,signal,subprocess,sys,tempfile,threading,time,unittest
import fetch_commander_mc as m
PREFIX=(m.BASE/'commander_sim0300_prefix.bin').read_bytes()
class Signals(unittest.TestCase):
 def test_sigterm_sigint_stalled_headers_body_and_queued(self):
  for sig in (signal.SIGTERM,signal.SIGINT):
   for stage in ('headers','body'):
    with self.subTest(signal=sig,stage=stage):self.exercise(sig,stage)
 def test_completed_before_signal_preserved_no_later_http(self):
  for sig in (signal.SIGTERM,signal.SIGINT):
   with self.subTest(signal=sig):
    root=pathlib.Path(tempfile.mkdtemp(prefix=f'complete-stop-{sig}-',dir=pathlib.Path(__file__).parent));(root/'cache').mkdir();(root/'attempts').mkdir();seen=[]
    body=PREFIX+b'z'*8192
    class Handler(http.server.BaseHTTPRequestHandler):
     def do_GET(self):
      seen.append(self.path);self.send_response(200);self.send_header('Content-Type','image/fits');self.end_headers();self.wfile.write(body)
     def log_message(self,*args):pass
    server=http.server.ThreadingHTTPServer(('127.0.0.1',0),Handler);thread=threading.Thread(target=server.serve_forever);thread.start()
    code="""import sys,pathlib,json,urllib.request,os
sys.path.insert(0,sys.argv[1]);import fetch_commander_mc as m
r=pathlib.Path(sys.argv[2]);s=m.Storage(r/'cache',fixture=True)
items=m.select(json.loads((m.BASE/'PLA_PR4_ALL_SIMULATED_MAPS.json').read_text()),[300,301])
for i in items:i['bytes']=19712
# Fixture body: 11520 qualified header bytes plus8192 payload bytes.
def opener(req,timeout):
 ident=int(req.full_url.split('_mc_')[1][:4]);a=next(p for p in (r/'attempts').iterdir() if p.name.startswith(f'{ident:04d}-'))
 return m.CurlResponse(urllib.request.Request(sys.argv[3],headers=dict(req.header_items())),a,s)
first=m.acquire(items[0],s,r/'attempts',opener)
os.kill(os.getpid(),int(sys.argv[4]))
second=m.acquire(items[1],s,r/'attempts',opener)
m.write_json(r/'RESULT.json',{'first':first,'second':second,'owned_children':len(m.OWNED_CHILDREN)})
"""
    try:
     with open(root/'worker.stdout','wb') as out,open(root/'worker.stderr','wb') as err:
      result=subprocess.run([sys.executable,'-B','-c',code,str(pathlib.Path(m.__file__).parent),str(root),'http://127.0.0.1:'+str(server.server_port),str(sig)],stdout=out,stderr=err,timeout=10)
     self.assertEqual(result.returncode,0);v=json.loads((root/'RESULT.json').read_text());self.assertEqual(v['first']['status'],'COMPLETE');self.assertEqual(v['second']['status'],'INTERRUPTED');self.assertEqual(v['owned_children'],0);self.assertEqual(len(seen),1);self.assertTrue((root/'cache'/(m.name(300)+'.verified.json')).exists());self.assertFalse((root/'cache'/m.name(301)).exists())
    finally:server.shutdown();thread.join();server.server_close()
 def exercise(self,sig,stage):
  root=pathlib.Path(tempfile.mkdtemp(prefix=f'signal-{sig}-{stage}-',dir=pathlib.Path(__file__).parent));(root/'cache').mkdir();(root/'attempts').mkdir()
  ready=threading.Event();release=threading.Event();seen=[]
  class Handler(http.server.BaseHTTPRequestHandler):
   def do_GET(self):
    seen.append({'version':self.request_version,'headers':dict(self.headers)})
    if stage=='headers':ready.set();release.wait(15)
    try:
     self.send_response(200);self.send_header('Content-Type','image/fits');self.end_headers();self.wfile.write(PREFIX+b'z'*8192);self.wfile.flush()
     ready.set();release.wait(15)
    except (BrokenPipeError,ConnectionResetError):pass
   def log_message(self,*args):pass
  server=http.server.ThreadingHTTPServer(('127.0.0.1',0),Handler);thread=threading.Thread(target=server.serve_forever);thread.start()
  code='''import sys,pathlib,json,urllib.request,concurrent.futures
sys.path.insert(0,sys.argv[1]);import fetch_commander_mc as m
m.install_stop_handlers();r=pathlib.Path(sys.argv[2]);s=m.Storage(r/'cache',fixture=True)
items=m.select(json.loads((m.BASE/'PLA_PR4_ALL_SIMULATED_MAPS.json').read_text()),[300,301,302])
def opener(req,timeout):
 ident=int(req.full_url.split('_mc_')[1][:4]);a=next(p for p in (r/'attempts').iterdir() if p.name.startswith(f'{ident:04d}-'))
 return m.CurlResponse(urllib.request.Request(sys.argv[3],headers=dict(req.header_items())),a,s)
with concurrent.futures.ThreadPoolExecutor(max_workers=1) as ex:
 futures=[ex.submit(m.acquire,i,s,r/'attempts',opener) for i in items]
 results=[f.result() for f in futures]
m.write_json(r/'BATCH_RETURN.json',{'results':results,'all_futures_drained':True,'owned_children':len(m.OWNED_CHILDREN)})
'''
  out=open(root/'worker.stdout','wb');err=open(root/'worker.stderr','wb');worker=subprocess.Popen([sys.executable,'-B','-c',code,str(pathlib.Path(m.__file__).parent),str(root),'http://127.0.0.1:'+str(server.server_port)],stdout=out,stderr=err)
  try:
   self.assertTrue(ready.wait(10));time.sleep(.2);worker.send_signal(sig);worker.wait(timeout=5)
   self.assertEqual(worker.returncode,0);batch=json.loads((root/'BATCH_RETURN.json').read_text());self.assertTrue(batch['all_futures_drained']);self.assertEqual(batch['owned_children'],0)
   self.assertEqual([r['status'] for r in batch['results']],['INTERRUPTED']*3);self.assertEqual(len(seen),1)
   self.assertEqual(seen[0]['version'],'HTTP/1.0');self.assertEqual(seen[0]['headers']['Accept-Encoding'],'identity')
   children=[]
   for f in (root/'attempts').glob('*/CURL_START.json'):
    child=json.loads(f.read_text())['pid'];self.assertFalse(pathlib.Path('/proc',str(child)).exists());children.append(child)
    close=json.loads((f.parent/'CURL_RETURN.json').read_text());self.assertTrue(close['all_child_processes_reaped']);self.assertTrue(close['interrupted'])
   self.assertEqual(len(children),1);self.assertFalse(list((root/'cache').glob('*.verified.json')))
   (root/'OBSERVATION.json').write_text(json.dumps({'signal':sig,'stage':stage,'observed_requests':seen,'children_reaped':children,'batch':batch},indent=2))
  finally:
   if worker.poll() is None:worker.kill();worker.wait()
   out.close();err.close();release.set();server.shutdown();thread.join();server.server_close()
if __name__=='__main__':unittest.main(verbosity=2)
