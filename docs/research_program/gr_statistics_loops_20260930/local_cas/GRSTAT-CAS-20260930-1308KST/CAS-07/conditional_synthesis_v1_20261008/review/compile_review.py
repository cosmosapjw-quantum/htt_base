from pathlib import Path
import datetime,hashlib,json,os,subprocess,sys,time
repo=Path('/home/cosmosapjw/Dropbox/bianchi/htt_base')
b=repo/'docs/research_program/gr_statistics_loops_20260930/local_cas/GRSTAT-CAS-20260930-1308KST/CAS-07'
c=b/'conditional_synthesis_v1_20261008'
out=Path('/tmp/cas07-review-20261008'); build=out/'lean';build.mkdir(exist_ok=True)
oracle=Path('/home/cosmosapjw/lean_oracles/viii_oracle')
lean=Path('/home/cosmosapjw/.elan/toolchains/leanprover--lean4---v4.31.0/bin/lean')
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
old=json.loads((c/'logs/20261008T104259728756Z/execution.json').read_text())
record={'started_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'reused_interfaces':{},'sources':{},'steps':[]}
for n,digest in old['reused_interfaces'].items():
 actual=sha(oracle/n);assert actual==digest,(n,actual,digest)
 record['reused_interfaces'][n]=actual
for name in ['lean-toolchain','lake-manifest.json']:
 record[name]={'repo_sha256':sha(repo/'formal_mathlib'/name),'oracle_sha256':sha(oracle/name)}
assert (repo/'formal_mathlib/lean-toolchain').read_bytes()==(oracle/'lean-toolchain').read_bytes()
pm=lambda p:{a['name']:a['rev'] for a in json.loads(p.read_text())['packages']}
assert pm(repo/'formal_mathlib/lake-manifest.json')==pm(oracle/'lake-manifest.json')
record['package_revisions']=pm(oracle/'lake-manifest.json')
record['mathlib_checkout_head']=subprocess.check_output(['git','rev-parse','HEAD'],cwd=oracle/'.lake/packages/mathlib',text=True).strip()
assert record['mathlib_checkout_head']==record['package_revisions']['mathlib']
paths=[build,oracle]+sorted(oracle.glob('.lake/packages/*/.lake/build/lib/lean'))
env={**os.environ,'LEAN_PATH':':'.join(map(str,paths))}
record['environment']={'LEAN_PATH':env['LEAN_PATH']}
sources=[('CAS07M02Accepted',b/'taylor_remainder_input_aligned_v1_20261007/lean/Main.lean'),('CAS07M06Accepted',b/'distance_t_refinement_v1_20261007/lean/Main.lean'),('Synthesis',c/'lean/Synthesis.lean')]
for n,p in sources:
 digest=sha(p);assert digest==old['source_sha256'][str(p.relative_to(repo))]
 (build/(n+'.lean')).write_bytes(p.read_bytes());record['sources'][str(p)]={'sha256':digest,'temporary_source':str(build/(n+'.lean'))}
checks='''import Synthesis
#check @CAS07M01.eta_bounds
#check @CAS07M02.remainder_bound_physical
#check @CAS07M03.scalar_volterra_comparison
#check @Cas07M04.d_norm
#check @Cas07M04.d_minus_si
#print CAS07M05.JacobiPremises
#check @CAS07M05.opnorm_error_eq
#check @CAS07M05.determinant_distance_bridge
#check @Cas07C03.FD1
#check @Cas07C03.FD2
#check @Cas07C03.FD3
#check @CAS07M06.t_domain
#check @CAS07M06.eta_order
#check @CAS07M06.refined_fd1
#check @CAS07M06.no_worse_than_fd2
#print axioms CAS07Synthesis.conditional_analytic_synthesis
#print axioms CAS07Synthesis.closed_interval_controls
#print axioms CAS07Synthesis.min_branches
example (K : ℝ) : CAS07M01.eta K 0 = -1 := by
  simp [CAS07M01.eta]
'''
(build/'ReviewChecks.lean').write_text(checks)
record['review_checks_sha256']=sha(build/'ReviewChecks.lean')
def run(name,args):
 start=time.monotonic();r=subprocess.run(args,cwd=build,env=env,text=True,capture_output=True,timeout=180)
 (out/(name+'.stdout')).write_text(r.stdout);(out/(name+'.stderr')).write_text(r.stderr)
 record['steps'].append({'name':name,'argv':list(map(str,args)),'cwd':str(build),'exit_code':r.returncode,'elapsed_seconds':time.monotonic()-start,'stdout_sha256':sha(out/(name+'.stdout')),'stderr_sha256':sha(out/(name+'.stderr'))})
 (out/'execution.json').write_text(json.dumps(record,indent=2))
 print(name,'exit',r.returncode,flush=True)
 if r.returncode:print(r.stdout,r.stderr,flush=True);sys.exit(r.returncode)
run('version',[str(lean),'--version'])
for name in [n for n,p in sources]+['ReviewChecks']:
 run(name,[str(lean),'-R',str(build),'-o',str(build/(name+'.olean')),str(build/(name+'.lean'))])
for p in record['sources']:assert sha(Path(p))==record['sources'][p]['sha256']
record['finished_utc']=datetime.datetime.now(datetime.timezone.utc).isoformat();record['exit_code']=0
(out/'execution.json').write_text(json.dumps(record,indent=2))
