import importlib.util,unittest,tempfile,io,gzip,json
from pathlib import Path
from unittest.mock import patch
s=importlib.util.spec_from_file_location('fetch',Path(__file__).resolve().parents[2]/'scripts/htt_fetch_open_inputs.py');m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
class Response(io.BytesIO):
 status=200
 def __init__(self,data,length=True):super().__init__(data);self.headers={'Content-Length':str(len(data))} if length else {}
 def geturl(self):return 'https://example.org/data'
 def __enter__(self):return self
 def __exit__(self,*a):self.close()
class Tests(unittest.TestCase):
 def spec(self,**kw):return dict(id='x',url='https://example.org/data',path='data',format='text',max_bytes=None,**kw)
 def run_fetch(self,data,cap=None,length=True):
  with tempfile.TemporaryDirectory() as t:
   spec=self.spec();spec['max_bytes']=cap
   opener=type('Opener',(),{'open':lambda *_a,**_k:Response(data,length)})()
   return m.acquire(spec,t,['example.org'],reserve_bytes=0,opener=opener)
 def test_uncapped_known(self):self.assertEqual(self.run_fetch(b'x'*100)['bytes'],100)
 def test_uncapped_unknown(self):self.assertEqual(self.run_fetch(b'x'*100,length=False)['bytes'],100)
 def test_explicit_cap(self):
  with self.assertRaises(RuntimeError):self.run_fetch(b'x'*100,10,False)
 def test_identity(self):
  with tempfile.TemporaryDirectory() as t:
   p=Path(t)/'x';p.write_bytes(b'hello')
   with self.assertRaises(ValueError):m.validate_payload(p,self.spec(expected_bytes=4))
 def test_disk_exhaustion(self):
  disk=type('Disk',(),{'free':0})()
  with patch.object(m.shutil,'disk_usage',return_value=disk):
   with self.assertRaises(OSError):self.run_fetch(b'hello')
 def test_gzip_uncapped(self):
  with tempfile.TemporaryDirectory() as t:
   p=Path(t)/'x';p.write_bytes(gzip.compress(b'x'*10000));spec=self.spec();spec['format']='gzip'
   self.assertEqual(m.validate_payload(p,spec)['bytes'],p.stat().st_size)
if __name__=='__main__':unittest.main()
