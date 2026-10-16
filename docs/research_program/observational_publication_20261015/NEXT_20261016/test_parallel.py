from concurrent.futures import ThreadPoolExecutor,as_completed
from pathlib import Path
import os,subprocess,sys,json,hashlib
HERE=Path(__file__).resolve().parent
TASKS={'X02':['test_x02.py'], 'K02':['test_k02.py'], 'S02':['test_s02.py'], 'L01':['test_l01.py'], 'EXTERNAL_PRECONDITIONS':['test_external_preconditions.py']}
def call(task,tests):
 env=dict(os.environ,OPENBLAS_NUM_THREADS='1',OMP_NUM_THREADS='1',MKL_NUM_THREADS='1',PYTHONDONTWRITEBYTECODE='1')
 cmd=[sys.executable,'-m','pytest','-q','-p','no:cacheprovider',*[str(HERE/p) for p in tests]]
 p=subprocess.run(cmd,env=env,cwd=str(HERE.parent),capture_output=True,text=True,timeout=35)
 return {'task':task,'cmd':' '.join(cmd),'exit_code':p.returncode,'stdout':p.stdout,'stderr':p.stderr[-1000:],'execution':'parallel subprocess, independent tests, single source files read only'}
if __name__=='__main__':
 output=[]
 with ThreadPoolExecutor(max_workers=5) as pool:
  jobs={pool.submit(call,k,v):k for k,v in TASKS.items()}
  for f in as_completed(jobs):output.append(f.result())
 output=sorted(output,key=lambda x:x['task']);
 receipt={'schema':'htt.sixpaper_parallel_scoped_test_execution/1','date_kst':'2026-10-16','runtime':sys.version,'items':output,'native_subagent':'NOT_RUN','total_passed':sum(int(x['stdout'].split(' passed')[0].split()[-1]) for x in output if ' passed' in x['stdout']),'all_exit_zero':all(x['exit_code']==0 for x in output)}
 (HERE/'PARALLEL_TEST_RECEIPT.json').write_text(json.dumps(receipt,indent=2,ensure_ascii=False,sort_keys=True)+'\n')
 for x in output:print(x['task'],x['exit_code'],x['stdout'].strip())
 if not receipt['all_exit_zero']:raise SystemExit('nonzero scoped test')
