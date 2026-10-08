"""Build only missing M02/M06 imports and the new synthesis with pinned Lean.
Existing accepted modules are reused after checking their published digests.
No historical campaign validator or adjudication is invoked.
"""
from pathlib import Path
import hashlib, json, os, subprocess, tempfile, datetime
T = Path(__file__).resolve().parent
B = T.parent
ROOT = B.parents[5]
ORACLE = Path('/home/cosmosapjw/lean_oracles/viii_oracle')
EXPECTED = {
 'CAS07M01Accepted.olean':'83acab45987909a490f90af775cc0f3ce538de3a5e04ed5a04abc311d9c15ca2',
 'CAS07C02Accepted.olean':'67344c6d91e2abfcdc8bae9329f55a3d659438bd61a34cb91d3670e3123bb2c0',
 'CAS07C03Accepted.olean':'7d4ec056d0b4f1f8dc43e941d00e842ea39901b496108ad2c4cdfd9c334a74a8',
 'CAS07M03Accepted.olean':'2728fb438129c39a9e9aae40e8ab8c70438014a7c713962baa13adbdabccca9e',
 'CAS07M04Accepted.olean':'81e374aa492d6528188225df432f1036dd460f168f31aa15e544289b46c8182a',
 'CAS07M05Accepted.olean':'694b6683d9027ca7602277e4fdd9a65444a4ee0add69f7bdba42ccd0b7fbfab0',
}
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
stamp = datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
log = T/'logs'/stamp
log.mkdir(parents=True)
for name, digest in EXPECTED.items():
 assert sha(ORACLE/name) == digest, ('ACCEPTED_INTERFACE_MISMATCH', name)
assert (ROOT/'formal_mathlib/lean-toolchain').read_bytes() == (ORACLE/'lean-toolchain').read_bytes()
a = json.loads((ROOT/'formal_mathlib/lake-manifest.json').read_text())
b = json.loads((ORACLE/'lake-manifest.json').read_text())
assert {p['name']:p['rev'] for p in a['packages']} == {p['name']:p['rev'] for p in b['packages']}
steps=[]
with tempfile.TemporaryDirectory(prefix='htt-cas07-synthesis-build-') as tmp:
 tmp=Path(tmp)
 env={**os.environ,'LEAN_PATH':str(tmp)+':'+str(ORACLE)}
 def run(name,argv):
  p=subprocess.run(argv,cwd=ORACLE,env=env,text=True,capture_output=True)
  (log/(name+'.stdout')).write_text(p.stdout);(log/(name+'.stderr')).write_text(p.stderr)
  steps.append({'name':name,'argv':argv,'cwd':str(ORACLE),'LEAN_PATH':env['LEAN_PATH'],'exit':p.returncode})
  print(name,'exit',p.returncode,flush=True)
  if p.returncode: print(p.stdout,p.stderr,flush=True)
  return p.returncode
 assert run('version',['lake','env','lean','--version'])==0
 sources=[('CAS07M02Accepted',B/'taylor_remainder_input_aligned_v1_20261007/lean/Main.lean'),
          ('CAS07M06Accepted',B/'distance_t_refinement_v1_20261007/lean/Main.lean'),
          ('Synthesis',T/'lean/Synthesis.lean')]
 code=0
 for name,src in sources:
  target=tmp/(name+'.lean');target.write_bytes(src.read_bytes())
  code=run(name,['lake','env','lean','-R',str(tmp),'-o',str(tmp/(name+'.olean')),str(target)])
  if code: break
 (log/'execution.json').write_text(json.dumps({'steps':steps,'reused_interfaces':EXPECTED,
   'source_sha256':{str(p.relative_to(ROOT)):sha(p) for _,p in sources},
   'toolchain':(ORACLE/'lean-toolchain').read_text().strip(),
   'mathlib_rev':{p['name']:p['rev'] for p in b['packages']}['mathlib'],
   'manifest_difference_class':'packaging metadata: project name, mathlib URL suffix/scope; package revisions equal',
   'scientific_admission':'HOLD','independent_review':'PENDING','exit':code},indent=2)+'\n')
 print('logs:',log,flush=True)
 raise SystemExit(code)
