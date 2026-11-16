import ast,hashlib,importlib.util,json,math,subprocess
from pathlib import Path
import numpy as np
from scipy import stats
root=Path('/workspace/scratch/ca5a06f498ba/r58_patch')
file=root/'htt/htt/htt/infer/r58_mixed_tensor_likelihood.py'
s=importlib.util.spec_from_file_location('mt',file);m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
out={'module_sha256':hashlib.sha256(file.read_bytes()).hexdigest(),'checks':{}}
x=np.array([[1.,1.,1.],[0.,1.,1.]])
f=m.fit_linear([0,0],np.eye(2),x)
res=m.linear_interval(f,[1,0,0],simultaneous=False)
assert res['identified'] and math.isclose(res['sd'],math.sqrt(2))
out['checks']['identified_coordinate_roundoff_repair']={'identified':res['identified'],'sd':res['sd']}
try:m.fit_linear([0,10],np.eye(2),np.diag([1.,1e-13]))
except ValueError as exc:out['checks']['rank_disagreement_fails_closed']={'exception':str(exc)}
else:raise AssertionError('rank ambiguity accepted')
rng=np.random.default_rng(777);x=rng.normal(size=(8,2))@rng.normal(size=(2,3));y=rng.normal(size=8)
f=m.fit_linear(y,np.eye(8),x);null=f['null_basis'][:,0]
rows=[]
for a in [0,1e4,1e6,1e8,1e10]:
 th=f['estimate']+a*null
 ll=m.gaussian_log_likelihood(f,th)
 direct=-.5*(np.sum((y-x@th)**2)+8*np.log(2*np.pi))
 bound=2e-14*(1+np.linalg.norm(x)*np.linalg.norm(th))*(1+np.linalg.norm(y-x@th))
 assert abs(ll-direct)<=bound
 assert ll<=-.5*8*np.log(2*np.pi)
 rows.append({'amplitude':a,'logL':ll,'direct':direct,'difference':ll-direct,'backward_error_bound':bound})
out['checks']['far_null_loglikelihood_psd_repair']=rows
r=np.random.default_rng(901);err=[];lik=[]
for n,p in [(4,2),(8,3),(5,5)]:
 for _ in range(8):
  a=r.normal(size=(n,n));c=a@a.T+.3*np.eye(n);x=r.normal(size=(n,p));y=r.normal(size=n)
  f=m.fit_linear(y,c,x,np.exp(r.normal(size=p)))
  ci=np.linalg.inv(c);pr=x.T@ci@x;cov=np.linalg.inv(pr);oracle=cov@x.T@ci@y
  err.append(float(np.max(np.abs(oracle-f['estimate']))))
  v=r.normal(size=p);iv=m.linear_interval(f,v,simultaneous=False)
  assert iv['identified'] and np.isclose(iv['sd']**2,v@cov@v,rtol=1e-10,atol=1e-10)
  th=r.normal(size=p);direct=stats.multivariate_normal.logpdf(y,mean=x@th,cov=c)
  lik.append(abs(direct-m.gaussian_log_likelihood(f,th)))
  assert np.isclose(direct,m.gaussian_log_likelihood(f,th),rtol=1e-11,atol=1e-10)
out['checks']['independent_full_GLS_oracle']={'experiments':24,'max_estimate_abs_error':max(err),'max_logL_abs_error':max(lik)}
ns={'np':np,'math':math,'SQRT6':math.sqrt(6)}
for fi,names in [('r54_identifiability.py',['wishart_gls_factors','rho_ratio']),('r54_tensor_five_view.py',['finite_mc_sd_inflation'])]:
 mod=ast.parse((root/'htt/htt/htt/infer'/fi).read_text())
 for name in names:
  node=next(n for n in mod.body if isinstance(n,ast.FunctionDef) and n.name==name)
  exec(compile(ast.Module(body=[node],type_ignores=[]),fi,'exec'),ns)
for args in [(2,3,3),(3,3,1),(30.0,8,3),(True,1,1)]:
 try:ns['wishart_gls_factors'](*args)
 except ValueError:pass
 else:raise AssertionError(args)
for args in [(3,3,3),(4,3,1),(300.0,45,5)]:
 try:ns['finite_mc_sd_inflation'](*args)
 except ValueError:pass
 else:raise AssertionError(args)
for tau in [-1,np.nan,np.inf]:
 try:ns['rho_ratio'](tau)
 except ValueError:pass
 else:raise AssertionError(tau)
assert ns['rho_ratio'](0)==0 and ns['rho_ratio'](10000)==math.sqrt(6)
assert math.isclose(ns['rho_ratio'](1e-20),math.sqrt(6)*1e-21,rel_tol=1e-14)
out['checks']['r54_repair_domain_and_limits']='pass_scoped'
Path('/workspace/scratch/ca5a06f498ba/r58_review_checks.json').write_text(json.dumps(out,indent=2)+'\n')
print(json.dumps(out,indent=2))
