"""Independent exact-rational contrast oracle and full-sphere output audit."""
import os
os.environ.update(OPENBLAS_NUM_THREADS='1',OMP_NUM_THREADS='1',MKL_NUM_THREADS='1',PYTHONDONTWRITEBYTECODE='1')
import sys, pathlib, json, importlib.util, hashlib, time, math
import numpy as np
import sympy as sp
import mpmath as mp
OUT=pathlib.Path(__file__).resolve().parent
ROOT=OUT  # Bind this independent oracle to the actual repair_05 candidate.
spec=importlib.util.spec_from_file_location('reviewed',ROOT/'consumer.py'); mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)
assert hashlib.sha256(mod.SOURCE.read_bytes()).hexdigest()==mod.SOURCE_SHA
source=json.loads(mod.SOURCE.read_text())['branches']; mp.mp.dps=150
rat=lambda x:sp.Rational(*float(x).as_integer_ratio())
def mm(x): return mp.mpf(int(x.p))/mp.mpf(int(x.q))
H=sp.zeros(6,7)
for i in range(6): H[i,0]=-1; H[i,i+1]=1
failures=[]; records=[]; conditions=[]; exact_bp04=None
start=time.monotonic();rng=np.random.default_rng(892143)
def note(ok,kind,ctx,**values):
 if not ok: failures.append(dict(kind=kind,context=ctx,**values))
for name in mod.BRANCHES:
 F=np.asarray(source[name]['F2']['matrix_7xk'],float);a=np.ones(7)
 for metric,d in [('common',mod.D),('raw',np.ones(9))]:
  sol=mod.solve_metric(F,a,d)
  # Minimize ||z||^2 subject to H G z=H y. The remaining common
  # channel amplitude is y0-g0*z; no float K inversion supplies this oracle.
  G=sp.Matrix([[rat(F[i,j])/rat(d[j]) for j in range(9)] for i in range(7)])
  A=H*G;W=(A*A.T).inv(method='DM');T=A.T*W*H
  P=sp.eye(9)-A.T*W*A;beta=(G[0,:]*P*G[0,:].T)[0];ell2=1/beta
  crow=sp.zeros(1,7);crow[0,0]=1;crow-=G[0,:]*T
  Q=H.T*W*H
  exact_ell=mp.sqrt(mm(ell2));ef=mp.mpf(sol['ell'])
  conditions.append(dict(branch=name,metric=metric,condition_K=float(np.linalg.cond(sol['K'])),ell_relative_error=float(abs(ef-exact_ell)/exact_ell)))
  cases=[]
  single=np.zeros(24);single[0]=1
  mixed=np.array([(-1)**j*(j+1)/24 for j in range(24)]);mixed/=np.linalg.norm(mixed)
  for scale in (1e-6,1.,1e6):
   for perturb in (1e-4,1e-12,1e-14):
    for carrier,vec in [('single',single),('mixed',mixed)]:
     Y=np.tile(scale*vec,(7,1));Y[0,0]+=scale*perturb;Y[6,0]-=scale*perturb
     if carrier=='mixed':Y[0,13]+=scale*perturb/2;Y[6,13]-=scale*perturb/2
     cases.append((dict(scale=scale,perturbation=perturb,carrier=carrier),Y,[.5,1-1e-7,1.,1+1e-7,2.]))
   generic=np.zeros((7,24));generic[:,0]=F[:,0]+.2*F[:,3];generic[:,1]=-.4*F[:,2];generic[:,13]=.3*a+.1*F[:,8]
   cases.append((dict(scale=scale,carrier='generic'),scale*generic,[.5,1.,2.]))
  # Dense independent carrier/noise directions exercise all 24 coordinates.
  for perturb in (1e-4,1e-8,1e-12,1e-14):
   vec=rng.normal(size=24);Y=np.tile(vec,(7,1))+perturb*rng.normal(size=(7,24))
   cases.append((dict(scale=1.,perturbation=perturb,carrier='dense_random'),Y,[.5,1.,1+1e-7,2.] ))
  for context,Y,factors in cases:
   Yq=sp.Matrix([[rat(x) for x in row] for row in Y]); cq=crow*Yq
   j0=sum((Yq[:,j].T*Q*Yq[:,j])[0] for j in range(24))
   ct=[mm(cq[j]) for j in range(24)];jj=mm(j0);ee=mm(ell2)
   for factor in factors:
    rho=float(mp.sqrt(jj))*factor; b=mp.mpf(rho)**2
    out=mod.identified(Y,F,a,d,sol,rho)
    # Actual JSON-compatible serialization; this is the geometry consumed downstream.
    ser=json.loads(json.dumps({k:(v.tolist() if isinstance(v,np.ndarray) else v) for k,v in out.items()},allow_nan=False))
    ctx=dict(branch=name,metric=metric,**context,factor=factor,status=ser['status']);tol=mp.mpf('1e-9')*max(b,jj)
    rec=dict(**ctx)
    if ser['status']=='EMPTY':note(b<jj,'false_empty',ctx,budget=str(b),J0=str(jj))
    elif ser['status']=='BALL':
     c=[mp.mpf(x) for x in ser['center']];r=mp.mpf(ser['radius']);dc=mp.sqrt(sum((c[j]-ct[j])**2 for j in range(24)))
     center_cost=jj+ee*dc**2
     # Exact extrema on every direction of the returned 24-sphere.
     upper=jj+ee*(r+dc)**2;lower=jj+ee*(r-dc)**2
     deviation=max(abs(upper-b),abs(lower-b));img=mp.mpf(ser['geometry_error']['budget_image_error_bound'])
     rec.update(center_cost_over_budget=float(center_cost/b),sphere_error_over_tolerance=float(deviation/tol),sphere_error_over_reported_bound=float(deviation/img),J0_error_over_tolerance=float(abs(mp.mpf(ser['J0'])-jj)/tol))
     note(b>jj and r>0,'false_ball',ctx)
     note(center_cost<=b+tol,'infeasible_serialized_center',ctx,ratio=float(center_cost/b))
     note(deviation<=tol,'full_sphere_policy_violation',ctx,ratio=float(deviation/tol))
     note(deviation<=img,'full_sphere_bound_violation',ctx,ratio=float(deviation/img))
     note(abs(mp.mpf(ser['J0'])-jj)<=tol,'reported_J0_incoherence',ctx,ratio=float(abs(mp.mpf(ser['J0'])-jj)/tol))
     residual=ser['residual_7x24'];re=mp.sqrt(sum((mp.mpf(residual[i][j])-(mp.mpf(float(Y[i,j]))-c[j]))**2 for i in range(7) for j in range(24)))
     note(re<=mp.mpf(ser['geometry_error']['residual_relation_error'])*(1+mp.mpf('1e-14')),'residual_relation_bound',ctx)
     dirs=[single,mixed]
     if dc:
      outward=np.array([float((c[j]-ct[j])/dc) for j in range(24)]);dirs.extend([outward,-outward])
     dirs.extend(np.eye(24));dirs.extend(-np.eye(24))
     maxw=mp.mpf(0)
     for v in dirs:
      w=np.array(ser['center'])+ser['radius']*v
      wcost=jj+ee*sum((mp.mpf(float(w[j]))-ct[j])**2 for j in range(24))
      maxw=max(maxw,abs(wcost-b))
     # Arbitrary future binary64 samples are a separate diagnostic. The
     # accepted object is the abstract real sphere, tested above; actual
     # exported synthetic witnesses have their own retained control gates.
     rec['serialized_direction_error_over_tolerance']=float(maxw/tol)
     rec['serialized_direction_diagnostic_only']=True
    else:
     note(ser['status'] in ['BOUNDARY_UNCERTAIN','NUMERIC_BOUNDARY_HOLD'] and ser['radius'] is None and bool(ser['radius_uncertainty']),'invalid_hold',ctx)
    records.append(rec)
  if name=='A_BT_1e-06' and metric=='raw':
   Y=np.zeros((7,24));Y[:,0]=1.;Y[0,0]+=1e-14;Y[6,0]-=1e-14;rho=float.fromhex('0x1.ba775222664cdp-44')
   o=mod.identified(Y,F,a,d,sol,rho)
   exact_bp04={k:(v.tolist() if isinstance(v,np.ndarray) else v) for k,v in o.items()}
   note(o['status']=='NUMERIC_BOUNDARY_HOLD' and o['radius'] is None,'BP04_not_held',dict(branch=name,metric=metric))
  print('completed',name,metric,'cases',len(records),'failures',len(failures),flush=True)
summary=dict(test_kind='independent exact-rational 6x9 contrast constrained minimum and abstract 24-sphere extrema',loaded_consumer_file=str(pathlib.Path(mod.__file__).resolve()),candidate_consumer_sha256=hashlib.sha256(pathlib.Path(mod.__file__).read_bytes()).hexdigest(),case_count=len(records),counts={s:sum(r['status']==s for r in records) for s in set(r['status'] for r in records)},failures=failures,conditions=conditions,maxima={k:max((r.get(k,0) for r in records),default=0) for k in ['center_cost_over_budget','sphere_error_over_tolerance','sphere_error_over_reported_bound','J0_error_over_tolerance','serialized_direction_error_over_tolerance']},arbitrary_rounded_direction_samples='DIAGNOSTIC_ONLY_NOT_BALL_ACCEPTANCE',exact_bp04=exact_bp04,elapsed_seconds=time.monotonic()-start,records=records)
(OUT/'raw/independent_probe.json').write_text(json.dumps(summary,indent=2,allow_nan=False)+'\n')
print(json.dumps({k:v for k,v in summary.items() if k not in ['records','exact_bp04']},indent=2),flush=True)
sys.exit(1 if failures else 0)
