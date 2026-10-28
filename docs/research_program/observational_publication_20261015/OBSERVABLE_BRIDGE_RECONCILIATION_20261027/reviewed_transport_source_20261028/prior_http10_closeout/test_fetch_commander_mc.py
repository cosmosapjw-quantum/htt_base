import concurrent.futures,copy,http.server,json,pathlib,tempfile,threading,unittest,urllib.request
import fetch_commander_mc as m
BASE=pathlib.Path('/mnt/extdrive/workdir/htt_open_data/r36_pr4_contract_preparation')
GOOD=(BASE/'commander_sim0300_prefix.bin').read_bytes()+b'payload-fixture'*2000
BAD=(BASE/'commander_sim0200_prefix.bin').read_bytes()+b'T-only'*2000
class Handler(http.server.BaseHTTPRequestHandler):
 def do_GET(self):
  body=self.server.payload
  self.send_response(200);self.send_header('Content-Type','image/fits')
  if getattr(self.server,'disposition',None):self.send_header('Content-Disposition',self.server.disposition)
  self.end_headers();self.wfile.write(body)
 def log_message(self,*a):pass
class Cases(unittest.TestCase):
 def setUp(self):
  fixtures=pathlib.Path(__file__).parent/'test_fixtures';fixtures.mkdir(exist_ok=True)
  self.root=pathlib.Path(tempfile.mkdtemp(prefix=self._testMethodName+'-',dir=fixtures));self.cache=self.root/'cache';self.cache.mkdir();self.logs=self.root/'attempts';self.logs.mkdir()
  self.server=http.server.ThreadingHTTPServer(('127.0.0.1',0),Handler);self.server.payload=GOOD
  self.thread=threading.Thread(target=self.server.serve_forever);self.thread.start()
  self.store=m.Storage(self.cache,reserve=0,fixture=True)
 def tearDown(self):
  self.server.shutdown();self.thread.join();self.server.server_close()
 def opener(self,req,timeout):
  return urllib.request.urlopen('http://127.0.0.1:'+str(self.server.server_port)+'/?'+req.full_url.split('?')[1],timeout=timeout)
 def item(self,i=300):return {'id':i,'filename':m.name(i),'url':m.url(i),'bytes':len(GOOD),'catalog_row':{'fixture':True}}
 def runitem(self,i=None):return m.acquire(i or self.item(),self.store,self.logs,self.opener)
 def partial(self,b):
  p=self.cache/(m.name(300)+'.partial');p.write_bytes(b);return p
 def test_actual_catalog_all_fixed_ids_and_Tonly_rejected(self):
  catalog=json.loads((BASE/'PLA_PR4_ALL_SIMULATED_MAPS.json').read_text());r=m.select(catalog,list(range(300,400)));self.assertEqual(len(r),100)
  with self.assertRaises(ValueError):m.select(catalog,[200])
  altered=copy.deepcopy(catalog)
  for row in altered['data']:
   if row['SIMULATED_MAP__FILE_ID']==m.name(300):row['SIMULATED_MAP__SIZE']+=1
  with self.assertRaises(ValueError):m.select(altered,[300])
 def test_URL_ID_binding_rejected_no_request(self):
  i=self.item();i['url']=m.url(301);r=self.runitem(i);self.assertEqual(r['network_bytes'],0);self.assertEqual(r['status'],'ERROR')
 def test_wrong_Tonly_role_preserves_prefix(self):
  self.server.payload=BAD;p=self.partial(BAD[:100]);before=p.read_bytes();i=self.item();i['bytes']=len(BAD)
  self.assertEqual(self.runitem(i)['status'],'ERROR');self.assertEqual(p.read_bytes(),before)
 def test_success_full_and_exact_cache(self):
  r=self.runitem();self.assertEqual(r['status'],'COMPLETE');final=self.cache/m.name(300);self.assertEqual(final.read_bytes(),GOOD)
  r2=self.runitem();self.assertEqual(r2['status'],'CACHE_VERIFIED');self.assertEqual(r2['network_bytes'],0)
 def test_cache_mismatch_never_overwritten(self):
  self.runitem();f=self.cache/m.name(300);f.write_bytes(b'owner-bytes');before=f.stat()
  self.assertEqual(self.runitem()['status'],'ERROR');self.assertEqual(f.read_bytes(),b'owner-bytes');self.assertEqual(f.stat().st_ino,before.st_ino)
 def test_unreceipted_completed_target_preserved(self):
  f=self.cache/m.name(300);f.write_bytes(GOOD);self.assertEqual(self.runitem()['status'],'ERROR');self.assertEqual(f.read_bytes(),GOOD)
 def test_prefix_mismatch_unchanged(self):
  p=self.partial(GOOD[:12000]+b'X');before=p.read_bytes();r=self.runitem();self.assertEqual(r['status'],'ERROR');self.assertEqual(p.read_bytes(),before)
 def test_success_full_prefix_resume(self):
  p=self.partial(GOOD[:17000]);r=self.runitem();self.assertEqual(r['status'],'COMPLETE');self.assertEqual(r['redundant_prefix_bytes'],17000);self.assertEqual(p.read_bytes(),GOOD);self.assertEqual(r['sha256'],m.digest(p))
 def test_short_response_before_prefix_unchanged(self):
  p=self.partial(GOOD[:17000]);self.server.payload=GOOD[:15000];before=p.read_bytes();self.assertEqual(self.runitem()['status'],'ERROR');self.assertEqual(p.read_bytes(),before)
 def test_interrupted_suffix_retained_and_resumable(self):
  p=self.partial(GOOD[:12000]);self.server.payload=GOOD[:20000];r=self.runitem();self.assertEqual(r['status'],'ERROR');self.assertEqual(p.read_bytes(),GOOD[:20000]);self.server.payload=GOOD;self.assertEqual(self.runitem()['status'],'COMPLETE')
 def test_reserve_failure_retains_attempt_and_old_partial(self):
  p=self.partial(GOOD[:100]);self.store.reserve=10**30;r=self.runitem();self.assertEqual(r['status'],'ERROR');self.assertEqual(p.read_bytes(),GOOD[:100]);a=list(self.logs.glob('*/RETURN.json'));self.assertEqual(len(a),1);self.assertIn('reserve',a[0].read_text())
 def test_different_ID_concurrency_drains_and_retains(self):
  with concurrent.futures.ThreadPoolExecutor(max_workers=2) as ex:
   results=list(ex.map(self.runitem,[self.item(300),self.item(301)]))
  self.assertEqual([r['status'] for r in results],['COMPLETE','COMPLETE']);self.assertEqual(len(list(self.logs.glob('*/response.bin'))),2)
 def test_late_prefix_mismatch_after_first_chunk_unchanged(self):
  self.server.payload=GOOD+b'z'*(2*m.CHUNK);i=self.item();i['bytes']=len(self.server.payload)
  b=self.server.payload[:m.CHUNK+100]+b'X';p=self.partial(b);self.assertEqual(self.runitem(i)['status'],'ERROR');self.assertEqual(p.read_bytes(),b)
 def test_missing_pilot_cache_blocks_extension_validation(self):
  with self.assertRaises(ValueError):m.verify_cache(self.item(),self.cache)
 def test_wrong_units_preserves_prefix(self):
  self.server.payload=GOOD.replace(b'uK_CMB',b'mK_CMB');p=self.partial(self.server.payload[:100]);old=p.read_bytes();self.assertEqual(self.runitem()['status'],'ERROR');self.assertEqual(p.read_bytes(),old)
 def test_F1_contradictory_source_cards_preserve_full_prefix(self):
  for old,new in [(b"'Commander'",b"'SEVEM    '"),(b"'CMB     '",b"'DUST    '"),(b"'HEALPIX '",b"'OTHER   '")]:
   with self.subTest(card=old):
    self.assertIn(old,GOOD);self.server.payload=GOOD.replace(old,new);p=self.partial(GOOD[:100]);r=self.runitem()
    self.assertEqual(r['status'],'ERROR');self.assertEqual(p.read_bytes(),GOOD[:100]);self.assertFalse((self.cache/m.name(300)).exists());self.assertFalse((self.cache/(m.name(300)+'.verified.json')).exists())
 def test_F1_contradictory_cache_even_matching_hash_rejected(self):
  for old,new in [(b"'Commander'",b"'SEVEM    '"),(b"'CMB     '",b"'DUST    '"),(b"'HEALPIX '",b"'OTHER   '")]:
   with self.subTest(card=old):
    f=self.cache/m.name(300);f.write_bytes(GOOD.replace(old,new));receipt=pathlib.Path(str(f)+'.verified.json');receipt.write_text(json.dumps({'item':self.item(),'sha256':m.digest(f)}));before=f.read_bytes()
    r=self.runitem();self.assertEqual(r['status'],'ERROR');self.assertEqual(r['network_bytes'],0);self.assertEqual(f.read_bytes(),before)
 def test_F2_exact_quoted_unquoted_and_extended_filename(self):
  for i,template in enumerate(['inline; filename="{}"','attachment; filename={}',"attachment; filename*=UTF-8''{}"],300):
   header=template.format(m.name(i))
   with self.subTest(header=header):
    m.validate_disposition(header,m.name(i));self.server.disposition=header;self.assertEqual(self.runitem(self.item(i))['status'],'COMPLETE')
 def test_F2_conflicting_disposition_preserves_prefix(self):
  n=m.name(300)
  headers=['inline; filename="'+n+'.wrong-product"','inline; filename="prefix-'+n+'"','inline; filename="different.fits"; comment="'+n+'"','inline; filename="../'+n+'"',"inline; filename*=UTF-8''..%2F"+n,"inline; filename=\""+n+"\"; filename*=UTF-8''wrong.fits"]
  for header in headers:
   with self.subTest(header=header):
    self.server.disposition=header;p=self.partial(GOOD[:100]);r=self.runitem();self.assertEqual(r['status'],'ERROR');self.assertEqual(p.read_bytes(),GOOD[:100]);self.assertFalse((self.cache/n).exists());self.assertFalse((self.cache/(n+'.verified.json')).exists())
 def test_single_writer_lock_rejected(self):
  import fcntl
  with open(self.cache/(m.name(300)+'.lock'),'wb') as f:
   fcntl.flock(f,fcntl.LOCK_EX|fcntl.LOCK_NB);self.assertEqual(self.runitem()['status'],'ERROR')
if __name__=='__main__':unittest.main(verbosity=2)
