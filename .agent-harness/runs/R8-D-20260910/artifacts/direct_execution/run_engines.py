"""Direct host engine checks with exact inputs; no independent admission."""
from concurrent.futures import ThreadPoolExecutor
import argparse,hashlib,json,os,subprocess,time
from pathlib import Path
HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[4]
PIN='c2a9299fa2a751da7b7264e7be49129e15d5d24eb643f366f8425cf82b7f0062'
PY='/mnt/sn850x2t/htt_base_e2e/venvs/htt_base-py312-20260829/bin/python'
LEAN='/home/cosmosapjw/.elan/toolchains/leanprover--lean4---v4.31.0/bin/lean'
PACKAGES=Path('/mnt/sn850x2t/htt_base_e2e/lean-shared/v4.31.0/packages')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
assert sha(HERE/'DIRECT_CHECK_CONTRACT.json')==PIN
assert (ROOT/'formal/lean-toolchain').read_text().strip()=='leanprover/lean4:v4.31.0'
assert subprocess.check_output(['git','-C',str(PACKAGES/'mathlib'),'rev-parse','HEAD'],text=True).strip()=='fabf563a7c95a166b8d7b6efca11c8b4dc9d911f'
axes={
 'wolfram_xact':['/usr/local/Wolfram/WolframEngine/15.0/Executables/WolframKernel','-noprompt','-script',str(HERE/'verify.wl'),str(HERE/'wolfram_payload.json')],
 'sympy':[PY,str(HERE/'verify_sympy.py')],
 'sage_singular':['/usr/local/bin/sage','-python',str(HERE/'verify_sage.py')],
 'lean':[LEAN,'-o',str(HERE/'Support.olean'),str(HERE/'Support.lean')],
}
def run(item):
 axis,argv=item;env=os.environ.copy();env['PYTHONDONTWRITEBYTECODE']='1'
 if axis=='lean':env['LEAN_PATH']=':'.join(str(p/'.lake/build/lib/lean') for p in sorted(PACKAGES.iterdir()) if p.is_dir())
 start=time.monotonic()
 try:
  p=subprocess.run(argv,cwd=ROOT,env=env,capture_output=True,text=True,timeout=180)
  output=p.stdout+p.stderr;code=p.returncode
 except subprocess.TimeoutExpired as ex:output=str(ex);code=124
 (HERE/f'{axis}.log').write_text(output)
 result={'argv':argv,'cwd':str(ROOT),'exit_code':code,'elapsed_seconds':time.monotonic()-start,'log_sha256':sha(HERE/f'{axis}.log')}
 if code==0:
  if axis=='lean':
   result.update(checks={k:'sorryAx' not in output for k in json.loads((HERE/'DIRECT_CHECK_CONTRACT.json').read_text())['target']['exact_test_obligations']},versions={'lean':subprocess.check_output([LEAN,'--version'],text=True).strip()},source_sha256=sha(HERE/'Support.lean'),compiled_sha256=sha(HERE/'Support.olean'))
  elif axis=='wolfram_xact':result.update(json.loads((HERE/'wolfram_payload.json').read_text()))
  else:result.update(json.loads(output.strip().splitlines()[-1]))
 result['status']='BLOCKED' if code==124 else 'PASS' if code==0 and all(result.get('checks',{}).values()) else 'FAIL'
 print(axis,result['status'],code,flush=True)
 return axis,result
parser=argparse.ArgumentParser()
parser.add_argument('--axis',action='append',choices=tuple(axes))
args=parser.parse_args()
selected=args.axis or tuple(axes)
results=json.loads((HERE/'engine_results.json').read_text())['axes'] if args.axis else {}
with ThreadPoolExecutor(max_workers=4) as pool:results.update(dict(pool.map(run,((k,axes[k]) for k in selected))))
payload={'contract_sha256':PIN,'status':'FOUR_ENGINE_SUPPORTING_CHECKS_PASS' if all(r['status']=='PASS' for r in results.values()) else 'DIRECT_CHECKS_INCOMPLETE',
 'axes':results,'independence':'HOST_AUTHORED_AND_EXECUTED_NOT_BLIND',
 'independent_four_axis_status':'NOT_PERFORMED','scientific_claim_promotion':False,
 'scope':'Limited P1 coordinate identities, P2 mock squared norms, J1 set logic and alpha, V08 supplied ray. Generic physical/probability theorems remain outside these checks.',
 'source_sha256':{p.name:sha(p) for p in HERE.iterdir() if p.suffix in ('.py','.wl','.lean')}}
(HERE/'engine_results.json').write_text(json.dumps(payload,indent=2)+'\n')
raise SystemExit(0 if all(r['status']=='PASS' for r in results.values()) else 1)
