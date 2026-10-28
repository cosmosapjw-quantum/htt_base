import http.server,json,os,pathlib,signal,subprocess,sys,tempfile,threading,time,unittest,urllib.parse
sys.path.insert(0,'/mnt/extdrive/workdir/htt_open_data/r36_pr4_transfer_repair_preparation')
import fetch_commander_mc as m
ROOT=pathlib.Path(__file__).parent
PREFIX=(m.BASE/'commander_sim0300_prefix.bin').read_bytes()
CHILD_CODE=r'''
import sys,pathlib,json,urllib.request,urllib.parse,os,signal
sys.path.insert(0,sys.argv[1]); import fetch_commander_mc as m
r=pathlib.Path(sys.argv[2]); scenario=sys.argv[4]
original=m.CurlResponse
def local(req,attempt,storage):
    mapped=sys.argv[3]+'/?u='+urllib.parse.quote(req.full_url,safe='')
    return original(urllib.request.Request(mapped,headers=dict(req.header_items())),attempt,storage)
m.CurlResponse=local
if scenario=='completion':
    select=m.select
    def small(catalog,ids):
        rows=select(catalog,ids)
        for row in rows: row['bytes']=19712
        return rows
    m.select=small
    digest=m.digest
    def completion_stop(path):
        answer=digest(path)
        if str(path).endswith('.partial') and not m.STOP.is_set():
            os.kill(os.getpid(),signal.SIGTERM)
        return answer
    m.digest=completion_stop
ids=['300','301','302','303','304','305'] if scenario=='concurrent' else ['300','301']
mode='official-resolver-http10' if scenario in ('metadata','qualification') else 'canonical-http10'
sys.argv=['fixture-main','--ids',*ids,'--cache',str(r/'cache'),'--receipts',str(r/'attempts'),'--concurrency','4' if scenario=='concurrent' else '1',
'--handoff','/mnt/extdrive/workdir/htt_open_data/r36_pr4_actual/checkpoint/WORKER_HANDOFF_002.json','--handoff-sha256','013af5f0b4614169d881a74e7aa87a0ad38a8182496353d12ddaf4690f1c20ab','--mode',mode,
'--requested-executor-runtime','gpt-6-sol/high','--observed-executor-runtime','UNKNOWN']
code=m.main()
m.write_json(r/'EXECUTOR_RETURN.json',{'exit_code':code,'owned_children':len(m.OWNED_CHILDREN),'stop':m.STOP.is_set()})
sys.exit(code)
'''

class ActualMain(unittest.TestCase):
    def test_four_active_and_two_queued_sigterm_sigint(self):
        for sig in (signal.SIGTERM,signal.SIGINT):
            with self.subTest(signal=sig): self.exercise('concurrent',sig)
    def test_resolver_metadata_and_qualification_stop(self):
        for scenario in ('metadata','qualification'):
            with self.subTest(stage=scenario): self.exercise(scenario,signal.SIGTERM)
    def test_full_eof_then_stop_before_promotion(self):
        self.exercise('completion',None)
    def exercise(self,scenario,sig):
        root=pathlib.Path(tempfile.mkdtemp(prefix=scenario+'-',dir=ROOT))
        (root/'cache').mkdir();(root/'attempts').mkdir()
        ready=threading.Event();release=threading.Event();seen=[];seen_lock=threading.Lock()
        class Handler(http.server.BaseHTTPRequestHandler):
            def do_GET(self):
                original=urllib.parse.parse_qs(urllib.parse.urlsplit(self.path).query)['u'][0]
                with seen_lock:
                    seen.append({'url':original,'version':self.request_version,'headers':dict(self.headers)})
                    count=len(seen)
                try:
                    self.send_response(200);self.send_header('Content-Type','application/json' if 'urldata-action' in original else 'image/fits');self.end_headers()
                    if 'urldata-action' in original:
                        if scenario=='metadata':
                            self.wfile.write(b'["http');self.wfile.flush();ready.set();release.wait(15)
                        else:
                            u='http://pla.esac.esa.int/ftp_public/anonymous999/simulated_maps/PR4/comp_separation/'+m.name(300)
                            self.wfile.write(json.dumps([u]).encode())
                    elif scenario=='qualification':
                        self.wfile.write(PREFIX[:512]);self.wfile.flush();ready.set();release.wait(15)
                    else:
                        self.wfile.write(PREFIX+b'z'*8192);self.wfile.flush()
                        if scenario=='concurrent':
                            if count==4: ready.set()
                            release.wait(15)
                except (BrokenPipeError,ConnectionResetError): pass
            def log_message(self,*a): pass
        server=http.server.ThreadingHTTPServer(('127.0.0.1',0),Handler)
        thread=threading.Thread(target=server.serve_forever);thread.start()
        with open(root/'worker.stdout','wb') as out,open(root/'worker.stderr','wb') as err:
            worker=subprocess.Popen([sys.executable,'-B','-c',CHILD_CODE,str(pathlib.Path(m.__file__).parent),str(root),'http://127.0.0.1:'+str(server.server_port),scenario],stdout=out,stderr=err)
            try:
                if sig:
                    self.assertTrue(ready.wait(10),'server did not reach intended stop stage')
                    time.sleep(.15);worker.send_signal(sig)
                worker.wait(timeout=10)
                self.assertEqual(worker.returncode,1)
                summary=json.loads((root/'EXECUTOR_RETURN.json').read_text())
                self.assertEqual(summary['owned_children'],0)
                batches=list((root/'attempts').glob('batch-*/RETURN.json'));self.assertEqual(len(batches),1)
                batch=json.loads(batches[0].read_text());self.assertTrue(batch['all_futures_drained']);self.assertTrue(batch['interrupted'])
                statuses=[v['status'] for v in batch['results']]
                expected=['COMPLETE','INTERRUPTED'] if scenario=='completion' else ['INTERRUPTED']*(6 if scenario=='concurrent' else 2)
                self.assertEqual(statuses,expected)
                expected_requests={'concurrent':4,'metadata':1,'qualification':2,'completion':1}[scenario]
                self.assertEqual(len(seen),expected_requests)
                for req in seen:
                    self.assertEqual(req['version'],'HTTP/1.0')
                    self.assertEqual(req['headers']['Accept-Encoding'],'identity')
                starts=list((root/'attempts').glob('**/CURL_START.json'))
                self.assertEqual(len(starts),expected_requests)
                for p in starts:
                    pid=json.loads(p.read_text())['pid']
                    self.assertFalse(pathlib.Path('/proc',str(pid)).exists())
                    ret=json.loads((p.parent/'CURL_RETURN.json').read_text())
                    self.assertTrue(ret['all_child_processes_reaped']);self.assertFalse(ret['cleanup_errors'])
                for v in batch['results']:
                    self.assertEqual(v['item']['url'],m.url(v['item']['id']))
                    self.assertEqual(v['source_sha256'],'7d0c3ee5a2afe9655f86f674052323a69da0fc64d920d3eb2cb81c3eb2e6a2ee')
                    self.assertEqual(v['executor_runtime'],{'requested':'gpt-6-sol/high','observed':'UNKNOWN'})
                if scenario in ('metadata','qualification'):
                    self.assertTrue(seen[0]['url'].endswith('SIMULATED_MAP.SIMULATED_MAP_OID=93000'))
                    target=next((root/'attempts').glob('**/resolver.json')) if scenario=='metadata' else next((root/'attempts').glob('**/prefix.bin'))
                    self.assertEqual(target.read_bytes(),b'["http' if scenario=='metadata' else PREFIX[:512])
                    self.assertEqual(batch['auxiliary_decoded_bytes_lower_bound'],sum(v['auxiliary_decoded_bytes_lower_bound'] for v in batch['results']))
                finals=list((root/'cache').glob('*.verified.json'))
                self.assertEqual(len(finals),1 if scenario=='completion' else 0)
                (root/'OBSERVATION.json').write_text(json.dumps({'scenario':scenario,'signal':sig,'requests':seen,'batch':batch,'executor':summary},indent=2)+'\n')
            finally:
                if worker.poll() is None:worker.kill();worker.wait()
                release.set();server.shutdown();thread.join();server.server_close()

if __name__=='__main__': unittest.main(verbosity=2)
