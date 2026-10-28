import json,pathlib,tempfile,unittest
from unittest.mock import patch
import fetch_commander_mc as m
class Retention(unittest.TestCase):
 def test_partial_metadata_and_qualification_preserved(self):
  item=m.select(json.loads((m.BASE/'PLA_PR4_ALL_SIMULATED_MAPS.json').read_text()),[300])[0]
  returned='http://pla.esac.esa.int/ftp_public/anonymous999/simulated_maps/PR4/comp_separation/'+item['filename']
  for stage in ('metadata','qualification'):
   with self.subTest(stage=stage):
    root=pathlib.Path(tempfile.mkdtemp(prefix='aux-interruption-',dir=pathlib.Path(__file__).parent));store=m.Storage(root,fixture=True)
    class Response:
     status=200;headers={}
     def __init__(self,req,attempt,storage):self.metadata='urldata-action' in req.full_url;self.calls=0
     def read(self,n):
      self.calls+=1
      if self.metadata and stage=='qualification':return json.dumps([returned]).encode() if self.calls==1 else b''
      if self.calls==1:return b'prefix-received'
      raise InterruptedError('controlled auxiliary fixture')
     def __enter__(self):return self
     def __exit__(self,*args):pass
    with patch.object(m,'CurlResponse',Response):
     with self.assertRaisesRegex(InterruptedError,'controlled auxiliary'):m.resolve_official(item,root,store)
    target=root/'resolver.json' if stage=='metadata' else root/'qualification-0'/'prefix.bin'
    self.assertEqual(target.read_bytes(),b'prefix-received')
    if stage=='metadata':self.assertEqual(json.loads((root/'RESOLVER_HEADERS.json').read_text())['bytes_retained'],15)
if __name__=='__main__':unittest.main(verbosity=2)
