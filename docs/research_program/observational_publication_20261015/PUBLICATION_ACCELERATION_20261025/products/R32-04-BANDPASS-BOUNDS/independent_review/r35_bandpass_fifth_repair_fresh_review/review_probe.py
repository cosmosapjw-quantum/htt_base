import os
from pathlib import Path
OUT=Path(__file__).resolve().parent
os.environ.update(OPENBLAS_NUM_THREADS='1',OMP_NUM_THREADS='1',MKL_NUM_THREADS='1',MPLCONFIGDIR=str(OUT/'mpl'),PYTHONDONTWRITEBYTECODE='1')
import sys,json,hashlib,importlib.util,time,math,collections
import numpy as np
import sympy as sp
import mpmath as mp
mp.mp.dps=160
start=time.monotonic()
ROOT=Path('/home/cosmosapjw/Dropbox/bianchi/htt_base')
PA=ROOT/'docs/research_program/observational_publication_20261015/PUBLICATION_ACCELERATION_20261025'
BASE=PA/'products/R32-04-BANDPASS-BOUNDS'
C=BASE/'repair_05'
packet_path=Path('/mnt/extdrive/workdir/htt_open_data/r35_publication_acceleration_controller/NEXT_AFTER_BP_FIFTH_REPAIR.json')
packet=json.loads(packet_path.read_text())
ack=json.loads((packet_path.parent/'BP_FIFTH_REPAIR_REVIEW_ACTUAL_ACK_GO.json').read_text())
assert ack['go'] and ack['acknowledged']
for k in ['packet_id','input_identity','candidate_identity']:assert packet[k]==ack[k]
assert ack['agent_id']=='/root/rc_73939de9f7acb27d'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
assert 'sha256:'+sha(C/'ARTIFACT_MANIFEST.json')==packet['candidate_identity']
manifest=json.loads((C/'ARTIFACT_MANIFEST.json').read_text())
for f in manifest['files']:
 p=C/f['path'];assert p.stat().st_size==f['size_bytes'] and sha(p)==f['sha256'],f['path']
spec=importlib.util.spec_from_file_location('actual_repair05_candidate',C/'consumer.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
assert sha(Path(m.__file__))=='61eeec1f35728f6dddd786e63485f22286c44bfe883a27757688092f782f52d1'
assert sha(m.SOURCE)==m.SOURCE_SHA=='b4c20f3595fc1148ff387df3b012ce7fd87dae4098be16a0d24dd914d183291f'
source=json.loads(m.SOURCE.read_text())['branches']
retained=json.loads((C/'RESULT.json').read_text())
rat=lambda v:sp.Rational(*float(v).as_integer_ratio())
mpq=lambda q:mp.mpf(int(q.p))/int(q.q)
records=[];failures=[];witnesses=[];metrics=[];special=[]
def check(ok,kind,ctx,**kw):
 if not ok:failures.append(dict(kind=kind,context=ctx,**kw))
def dump(o):return json.loads(json.dumps({k:v.tolist() if isinstance(v,np.ndarray) else v for k,v in o.items()},allow_nan=False))
H=sp.zeros(6,7)
for i in range(6):H[i,i]=1;H[i,6]=-1
single=np.zeros(24);single[0]=1
mixed=np.array([(-1)**j*(j+1)/32 for j in range(24)])
for branch in m.BRANCHES:
 F=np.asarray(source[branch]['F2']['matrix_7xk']);a=np.ones(7)
 for label,d in [('common_reference',m.D),('raw_identity',np.ones(9))]:
  ctx=dict(branch=branch,metric=label)
  sol=m.solve_metric(F,a,d)
  # Independent exact Schur complement with final channel as reference.
  Fq=sp.Matrix([[rat(x) for x in row] for row in F]);Mi=sp.diag(*[1/rat(x)**2 for x in d]);K=Fq*Mi*Fq.T
  W=(H*K*H.T).inv(method='DM');k=K[6,:]*H.T
  variance=K[6,6]-(k*W*k.T)[0];ee=mpq(1/variance)
  centerrow=sp.zeros(1,7);centerrow[0,6]=1;centerrow-=k*W*H
  Q=H.T*W*H
  saved=retained['branches'][branch][label];coeff=np.array(saved['minimum_coefficients_c9'])
  check(np.linalg.norm(F@coeff-a)/np.linalg.norm(a)<=1e-10,'stored_Fc_residual',ctx)
  check(abs(mp.mpf(saved['minimum_budget_ell'])/mp.sqrt(ee)-1)<=mp.mpf('1e-10'),'ell_reference',ctx)
  N=np.array(saved['coefficient_nullspace_directions_2x9']).T
  check(np.linalg.norm(F@N)/np.linalg.norm(F)<=1e-10,'original_null',ctx)
  check(np.linalg.norm(N.T@(d*d*coeff))/max(1,np.linalg.norm(d*coeff))<=1e-10,'null_minimality',ctx)
  check(np.linalg.norm(N.T@(d[:,None]**2*N)-np.eye(2))<=1e-10,'null_metric',ctx)
  metrics.append(dict(**ctx,ell_relative_error=str(abs(mp.mpf(saved['minimum_budget_ell'])/mp.sqrt(ee)-1)),min_variance=str(mpq(variance))))
  def evaluate(Y,rho,kind,structural=False):
   cq=centerrow*sp.Matrix([[rat(x) for x in row] for row in Y]);ct=[mpq(x) for x in cq]
   # Contrast is formed exactly before the quadratic form; no subtractive J0 cancellation.
   delta=H*sp.Matrix([[rat(x) for x in row] for row in Y]);jq=sum((delta[:,j].T*W*delta[:,j])[0] for j in range(24));jj=mpq(jq)
   out=dump(m.identified(Y,F,a,d,sol,rho));status=out['status'];b=mp.mpf(rho)**2;tol=mp.mpf('1e-9')*max(b,jj)
   rec=dict(**ctx,kind=kind,rho_hex=rho.hex(),status=status)
   if status=='BALL':
    c=[mp.mpf(x) for x in out['center']];r=mp.mpf(out['radius']);dist=mp.sqrt(sum((x-y)**2 for x,y in zip(c,ct)))
    # Exact continuous sphere extrema reduce to this scalar discrepancy.
    D=abs(jj+ee*(dist*dist+r*r)-b)+2*ee*r*dist
    bound=mp.mpf(out['geometry_error']['budget_image_error_bound']);relbound=mp.mpf(out['geometry_error']['budget_image_relative_error_bound'])
    check(r>0 and b>jj,'false_ball',rec)
    check(D<=tol,'abstract_sphere_policy',rec,ratio=str(D/tol))
    check(D<=bound,'abstract_sphere_bound',rec,ratio=str(D/bound))
    check(relbound<=mp.mpf('1e-9'),'metadata_relative_bound',rec,bound=str(relbound))
    check(bound>=0 and (bound>0 or D==0),'bound_lost_to_zero',rec)
    check(abs(mp.mpf(out['J0'])-jj)<=tol,'J0_coherence',rec)
    re=mp.sqrt(sum((mp.mpf(out['residual_7x24'][i][j])-(mp.mpf(float(Y[i,j]))-c[j]))**2 for i in range(7) for j in range(24)))
    check(re<=mp.mpf(out['geometry_error']['residual_relation_error']),'residual_metadata',rec)
    enc=out['geometry_error']['bound_encoding']['budget_image_error_bound']
    check((isinstance(out['geometry_error']['budget_image_error_bound'],str))==(enc=='decimal_string_upward'),'bound_encoding',rec)
    rec.update(sphere_error_policy_units=str(D/tol),sphere_error_bound_units=str(D/bound),bound_encoding=enc)
   elif status=='EMPTY':check(b<jj,'false_empty',rec)
   elif status.startswith('SINGLETON_EXACT'):
    check(rho==0 and jq==0 and out['center']==Y[0].tolist() and out['radius']==0,'false_singleton',rec)
   else:check(status in ['NUMERIC_RANGE_HOLD','NUMERIC_BOUNDARY_HOLD','BOUNDARY_UNCERTAIN'] and out['radius'] is None and bool(out['radius_uncertainty']),'untyped_hold',rec)
   if structural:
    check(out['center']==Y[0].tolist() and out['J0']==0,'structural_exactness',rec)
    if kind.endswith('normal') or kind.endswith('tiny_representable'):check(status=='BALL','lost_positive_control',rec)
   records.append(rec)
   return out
  for name,center in [('zero',np.zeros(24)),('single',1e-6*single),('mixed24',1e-6*mixed)]:
   Y=np.tile(center,(7,1))
   for rname,rho in [('zero',0.),('minsub',float.fromhex('0x0.0000000000001p-1022')),('hex40',float.fromhex('0x0.0000000000040p-1022')),('hex7e8',float.fromhex('0x0.00000000007e8p-1022')),('tiny_representable',1e-206),('normal',1e-4)]:
    o=evaluate(Y,rho,'structural_'+name+'_'+rname,True)
    if branch=='A_BT_1e-06' and label=='raw_identity' and name=='zero' and rname in ['hex40','hex7e8']:
     check(o['status']=='NUMERIC_RANGE_HOLD','BP05_not_held',rname)
     oldr=float.fromhex('0x0.0000000000001p-1022' if rname=='hex40' else '0x0.0000000000022p-1022')
     special.append(dict(**ctx,case=rname,old_sphere_cost_ratio=str(ee*mp.mpf(oldr)**2/mp.mpf(rho)**2),new_status=o['status']))
  for scale in [1e-6,1e6]:
   for cname,center,pert in [('dense',mixed,1e-4),('near_pure',single,1e-14)]:
    Y=np.tile(scale*center,(7,1));Y[0,0]+=scale*pert;Y[6,0]-=scale*pert;Y[2,19]+=scale*pert/2
    delta=H*sp.Matrix([[rat(x) for x in row] for row in Y]);jj=mpq(sum((delta[:,j].T*W*delta[:,j])[0] for j in range(24)))
    for fac in [.5,1.,2.]:evaluate(Y,float(mp.sqrt(jj))*fac,f'{cname}_scale{scale}_factor{fac}')
  tiny=np.zeros((7,24));tiny[0,0]=1e-200
  o=evaluate(tiny,1e-200,'generic_underflow')
  check(o['status']=='NUMERIC_RANGE_HOLD','generic_underflow_not_held',ctx)
  if branch=='A_BT_1e-06' and label=='raw_identity':
   Y=np.zeros((7,24));Y[:,0]=1.;Y[0,0]+=1e-14;Y[6,0]-=1e-14
   o=evaluate(Y,float.fromhex('0x1.ba775222664cdp-44'),'BP04_exact')
   check(o['status']=='NUMERIC_BOUNDARY_HOLD' and o['radius'] is None,'BP04_not_held',ctx)
   special.append(dict(**ctx,case='BP04',new_status=o['status']))
  print(branch,label,'cases',len(records),'failures',len(failures),flush=True)
 # Actual exported witnesses only, as the original contract specifies.
 z=np.load(C/f'report/generated/{branch}_full24.npz');d=m.D
 assert np.array_equal(z['F'],F) and np.array_equal(z['a'],a)
 r=retained['branches'][branch];rho=r['common_reference']['minimum_budget_ell'];mixedz=z['mixed_signed_v']
 for uk,sg in [('one_U',1),('pair_U1',1),('pair_U2',-1)]:
  U=z[uk];budget=np.linalg.norm(d[:,None]*U);res=np.linalg.norm(np.outer(a,sg*mixedz)+F@U)
  check(abs(budget-rho)<=1e-10*rho,'exported_witness_norm',dict(branch=branch,witness=uk))
  check(res<=1e-9*np.linalg.norm(a),'exported_witness_reconstruction',dict(branch=branch,witness=uk))
  witnesses.append(dict(branch=branch,witness=uk,budget_relative_error=abs(budget/rho-1),reconstruction=res))
 Y=z['synthetic_Y'];s=z['synthetic_boundary_s'];U=z['synthetic_boundary_U'];grho=r['full24_controls']['generic_rho'];res=np.linalg.norm(Y-np.outer(a,s)-F@U);bn=np.linalg.norm(d[:,None]*U)
 check(abs(bn-grho)<=1e-9*grho,'exported_generic_norm',dict(branch=branch))
 check(res<=1e-9*max(1,np.linalg.norm(Y)),'exported_generic_reconstruction',dict(branch=branch))
 witnesses.append(dict(branch=branch,witness='synthetic_boundary_s/U',budget_relative_error=abs(bn/grho-1),reconstruction=res))
 check(np.max(np.linalg.norm(z['A']-z['B']@z['C'],axis=0)/np.linalg.norm(z['A'],axis=0))<=1e-9,'full24_stored_basis',dict(branch=branch))
# Immutable published numerical products and unchanged mandatory structural tests.
parity=[]
for name in ['test_pure_target_boundary.py','test_bandpass_boundary_repair.py','report/generated/budgets.tex','report/generated/residuals.tex']+[f'report/generated/{b}_full24.npz' for b in m.BRANCHES]:
 ok=sha(BASE/'repair_04'/name)==sha(C/name);check(ok,'unchanged_artifact',name);parity.append(dict(path=name,unchanged=ok))
old=json.loads((BASE/'repair_04/RESULT.json').read_text())
for b in m.BRANCHES:
 for k in ['common_reference','raw_identity']:
  check(old['branches'][b][k]==retained['branches'][b][k],'metric_summary_parity',dict(branch=b,metric=k))
report=dict(candidate_identity=packet['candidate_identity'],input_identity=packet['input_identity'],packet_id=packet['packet_id'],loaded_consumer=str(Path(m.__file__).resolve()),loaded_consumer_sha256=sha(Path(m.__file__)),manifest_entries_verified=len(manifest['files']),source_sha256=sha(m.SOURCE),case_count=len(records),counts=dict(collections.Counter(r['status'] for r in records)),max_sphere_policy_units=max(float(r.get('sphere_error_policy_units',0)) for r in records),max_sphere_bound_units=max(float(r.get('sphere_error_bound_units',0)) for r in records),decimal_bound_count=sum(r.get('bound_encoding')=='decimal_string_upward' for r in records),failures=failures,special=special,metrics=metrics,witnesses=witnesses,parity=parity,records=records,elapsed_seconds=time.monotonic()-start)
(OUT/'probe_result.json').write_text(json.dumps(report,indent=2,allow_nan=False)+'\n')
print(json.dumps({k:v for k,v in report.items() if k not in ['records','parity','witnesses','metrics']},indent=2))
sys.exit(bool(failures))
