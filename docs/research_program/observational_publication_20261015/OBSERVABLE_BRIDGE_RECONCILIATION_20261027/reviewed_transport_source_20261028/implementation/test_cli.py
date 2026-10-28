import json,pathlib,subprocess,sys,tempfile,unittest
ROOT=pathlib.Path(__file__).parent
EXPECTED='139804aa216430b5db1b711823087099c31300e8e9e6c1ff56f3602178aaabe6'
CODE=r'''
import sys,pathlib,json
sys.path.insert(0,sys.argv[1]);import fetch_commander_mc as m
r=pathlib.Path(sys.argv[2]);value=sys.argv[3]
def sentinel(*args,**kwargs):
 print(json.dumps({'accepted_guard':True,'helper_file':m.__file__,'source_sha256':m.digest(m.__file__)}),flush=True);raise RuntimeError('CLI_ACCEPTED_BEFORE_STORAGE')
m.Storage=sentinel
sys.argv=['fixture-main','--ids','300','--cache',str(r/'cache'),'--receipts',str(r/'receipts'),'--handoff','/mnt/extdrive/workdir/htt_open_data/r36_pr4_actual/checkpoint/WORKER_HANDOFF_002.json','--handoff-sha256','013af5f0b4614169d881a74e7aa87a0ad38a8182496353d12ddaf4690f1c20ab','--mode','canonical-http10','--requested-executor-runtime','gpt-6.1-sol/medium']
if value!='default':sys.argv+=['--concurrency',value]
try:m.main()
except RuntimeError as e:
 if str(e)!='CLI_ACCEPTED_BEFORE_STORAGE':raise
'''
class CLI(unittest.TestCase):
 def test_actual_cli_guards(self):
  root=pathlib.Path(tempfile.mkdtemp(prefix='cli-',dir=ROOT))
  for value in ('0','17','1','4','8','16','default'):
   with self.subTest(value=value):
    result=subprocess.run([sys.executable,'-B','-c',CODE,str(ROOT),str(root),value],capture_output=True,text=True,timeout=15)
    (root/(value+'.stdout')).write_text(result.stdout);(root/(value+'.stderr')).write_text(result.stderr)
    if value in ('0','17'):
     self.assertEqual(result.returncode,2);self.assertIn('concurrency must be within 1..16',result.stderr);self.assertEqual(result.stdout,'')
    else:
     self.assertEqual(result.returncode,0,result.stderr);proof=json.loads(result.stdout);self.assertTrue(proof['accepted_guard']);self.assertEqual(proof['source_sha256'],EXPECTED);self.assertEqual(proof['helper_file'],str(ROOT/'fetch_commander_mc.py'))
    self.assertFalse((root/'cache').exists());self.assertFalse((root/'receipts').exists())
if __name__=='__main__':unittest.main(verbosity=2)
