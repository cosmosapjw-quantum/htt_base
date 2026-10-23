import importlib.util,unittest,tempfile,io,gzip,json,hashlib,struct,zipfile
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

 def zip_bytes(self, compression=zipfile.ZIP_DEFLATED):
  data=io.BytesIO()
  with zipfile.ZipFile(data,'w',compression=compression) as archive:
   archive.writestr('../not_extracted.txt',b'x'*10000)
   archive.writestr('second.txt',b'y'*10000)
  return data.getvalue()

 def test_zip_uncapped_streams_without_extraction(self):
  with tempfile.TemporaryDirectory() as t:
   p=Path(t)/'data.zip';p.write_bytes(self.zip_bytes())
   spec=self.spec();spec['format']='zip';spec['max_bytes']=p.stat().st_size
   # A compressed-byte cap must not impose an implicit ZIP expansion cap.
   with patch.object(zipfile.ZipFile,'extract',side_effect=AssertionError('extraction forbidden')),patch.object(zipfile.ZipFile,'extractall',side_effect=AssertionError('extraction forbidden')):
    identity=m.validate_payload(p,spec)
   self.assertEqual(identity,{'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()})
   self.assertEqual([x.name for x in Path(t).iterdir()],['data.zip'])

 def test_zip_expansion_cap_counts_all_members(self):
  with tempfile.TemporaryDirectory() as t:
   p=Path(t)/'data.zip';p.write_bytes(self.zip_bytes())
   spec=self.spec(max_expanded_bytes=15000);spec['format']='zip'
   with self.assertRaisesRegex(ValueError,'Expanded payload exceeds bound'):
    m.validate_payload(p,spec)
   spec['max_expanded_bytes']=20000
   self.assertEqual(m.validate_payload(p,spec)['bytes'],p.stat().st_size)
   spec['max_expanded_bytes']=None
   self.assertEqual(m.validate_payload(p,spec)['bytes'],p.stat().st_size)

 def test_zip_crc_corruption_rejected(self):
  data=bytearray(self.zip_bytes(zipfile.ZIP_STORED))
  # Alter member content without changing the local header or central-directory CRC.
  name_length,extra_length=struct.unpack_from('<HH',data,26)
  data[30+name_length+extra_length]^=1
  with tempfile.TemporaryDirectory() as t:
   p=Path(t)/'data.zip';p.write_bytes(data)
   spec=self.spec();spec['format']='zip'
   with self.assertRaises(zipfile.BadZipFile):m.validate_payload(p,spec)

 def test_md5_mismatch_rejected(self):
  with tempfile.TemporaryDirectory() as t:
   p=Path(t)/'data';p.write_bytes(b'hello')
   with self.assertRaisesRegex(ValueError,'Upstream expected MD5 mismatch'):
    m.validate_payload(p,self.spec(md5='0'*32))

 def test_md5_receipt_keeps_sha256_identity(self):
  data=self.zip_bytes();expected=hashlib.md5(data,usedforsecurity=False).hexdigest()
  with tempfile.TemporaryDirectory() as t:
   spec=self.spec(md5=expected);spec['format']='zip'
   opener=type('Opener',(),{'open':lambda *_a,**_k:Response(data)})()
   result=m.acquire(spec,t,['example.org'],reserve_bytes=0,opener=opener)
   receipt=json.loads((Path(t)/'data.receipt.json').read_text())
   self.assertEqual(result['md5'],expected)
   self.assertEqual(receipt['md5'],expected)
   self.assertEqual(receipt['sha256'],hashlib.sha256(data).hexdigest())
   self.assertEqual(m.acquire(spec,t,['example.org'],reserve_bytes=0)['status'],'REUSED')

 def test_md5_only_does_not_adopt_unreceipted_payload(self):
  data=b'hello';expected=hashlib.md5(data,usedforsecurity=False).hexdigest()
  with tempfile.TemporaryDirectory() as t:
   (Path(t)/'data').write_bytes(data)
   with self.assertRaisesRegex(FileExistsError,'Existing unreceipted product'):
    m.acquire(self.spec(md5=expected),t,['example.org'],reserve_bytes=0)
   self.assertFalse((Path(t)/'data.receipt.json').exists())
if __name__=='__main__':unittest.main()

