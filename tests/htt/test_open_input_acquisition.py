"""Transport failure tests; independent of a scientific data-likelihood claim."""
import gzip
import hashlib
import importlib.util
import io
import json
from pathlib import Path
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location('open_inputs', ROOT/'scripts/htt_fetch_open_inputs.py')
m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)

class Response(io.BytesIO):
    status = 200
    def __init__(self, data, headers=None, url='https://example.org/file'):
        super().__init__(data); self.headers = headers or {}; self.url = url
    def geturl(self): return self.url

class Opener:
    def __init__(self, data, headers=None, url='https://example.org/file'):
        self.data=data; self.headers=headers; self.url=url; self.calls=0
    def open(self, req, timeout):
        self.calls += 1
        return Response(self.data, self.headers, self.url)

class AcquisitionTest(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory(); self.addCleanup(self.tmp.cleanup)
        self.root=Path(self.tmp.name)
        self.spec={'id':'x','url':'https://example.org/file','path':'x/data.txt','format':'text','max_bytes':100,'required_prefix_tokens':['ID']}
    def acquire(self, opener, spec=None):
        return m.acquire(spec or self.spec,self.root,['example.org'],reserve_bytes=0,opener=opener)
    def test_create_and_reuse_without_network(self):
        o=Opener(b'ID VALUE\n1 4\n')
        a=self.acquire(o); b=self.acquire(o)
        self.assertEqual(a['status'],'DOWNLOADED'); self.assertEqual(b['status'],'REUSED'); self.assertEqual(o.calls,1)
    def test_tampered_reuse_rejected(self):
        self.acquire(Opener(b'ID VALUE\n1 4\n'))
        (self.root/'x/data.txt').write_text('ID VALUE\n1 8\n')
        with self.assertRaisesRegex(ValueError,'identity mismatch'): self.acquire(Opener(b''))
    def test_unknown_existing_preserved(self):
        p=self.root/'x/data.txt'; p.parent.mkdir(); p.write_text('ID VALUE\n')
        with self.assertRaises(FileExistsError): self.acquire(Opener(b''))
        self.assertEqual(p.read_text(),'ID VALUE\n')
    def test_expected_hash_adoption(self):
        p=self.root/'x/data.txt'; p.parent.mkdir(); data=b'ID VALUE\n'; p.write_bytes(data)
        s={**self.spec,'sha256':hashlib.sha256(data).hexdigest()}
        self.assertEqual(self.acquire(Opener(b''),s)['status'],'REUSED')
    def test_truncation_never_finalized(self):
        with self.assertRaisesRegex(RuntimeError,'Truncated'): self.acquire(Opener(b'ID',{'Content-Length':'20'}))
        self.assertFalse((self.root/'x/data.txt').exists())
        self.assertEqual(len(list((self.root/'x').glob('*.part'))),1)
    def test_stream_cap(self):
        with self.assertRaisesRegex(RuntimeError,'bound'): self.acquire(Opener(b'ID'+b'x'*100))
        self.assertFalse((self.root/'x/data.txt').exists())
    def test_html_login_and_wrong_header(self):
        for data in (b'<html>login</html>',b'WRONG DATA'):
            with self.subTest(data=data),self.assertRaises(RuntimeError): self.acquire(Opener(data))
    def test_hash_mismatch(self):
        with self.assertRaisesRegex(RuntimeError,'SHA256 mismatch'): self.acquire(Opener(b'ID'),{**self.spec,'sha256':'0'*64})
    def test_gzip_crc_and_decompression_bound(self):
        data=gzip.compress(b'a'*1000)
        s={**self.spec,'format':'gzip','max_bytes':100,'max_expanded_bytes':500}
        with self.assertRaisesRegex(RuntimeError,'Expanded'): self.acquire(Opener(data),s)
        s['max_expanded_bytes']=2000
        with self.assertRaises(RuntimeError): self.acquire(Opener(data[:-3]),s)
    def test_unapproved_url_and_redirect(self):
        for url in ['http://example.org/f','https://x.test/f','https://u:p@example.org/f']:
            with self.subTest(url=url),self.assertRaises(ValueError): m.check_url(url,['example.org'])
        with self.assertRaisesRegex(RuntimeError,'HTTPS'): self.acquire(Opener(b'ID',url='https://other.org/f'))
    def test_path_traversal_and_symlink(self):
        with self.assertRaises(ValueError): m.destination(self.root,'../bad')
        (self.root/'x').symlink_to('/tmp')
        with self.assertRaises(ValueError): m.destination(self.root,'x/data')
    def test_orphan_receipt(self):
        p=self.root/'x/data.txt.receipt.json';p.parent.mkdir();p.write_text('{}')
        with self.assertRaisesRegex(FileExistsError,'Orphan'):self.acquire(Opener(b'ID'))
    def test_manifest_duplicate(self):
        p=self.root/'manifest.json';p.write_text(json.dumps({'allowed_hosts':['example.org'],'resources':[self.spec,self.spec]}))
        with self.assertRaisesRegex(ValueError,'Duplicate'):m.load_manifest(p)
    def test_transport_encoding(self):
        with self.assertRaisesRegex(RuntimeError,'content encoding'):self.acquire(Opener(b'ID',{'Content-Encoding':'gzip'}))

if __name__ == '__main__': unittest.main()
