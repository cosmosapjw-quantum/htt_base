#!/usr/bin/env python3
"""Frozen 32-catalogue conditional CF4 scenario recovery, no empirical coverage."""
import json,time,hashlib,traceback
from pathlib import Path
from dataclasses import asdict
import numpy as np
from scipy.special import logsumexp
from scipy.stats import truncnorm,norm,beta
import run_reboot_cf4_selected as d
R=d.ROOT;OUT=R/'docs/observational_reboot_20261014/results/cf4/injection_v1'
TRUTH=np.array([73.,100.,-200.,50.]);SEED=20261014

def selection_moments(model):
 _,zz=model.row_terms(TRUTH);ew=np.exp(model.log_eta_w+zz.sum(0)-logsumexp(model.log_eta_w+zz.sum(0)))
 s=model.scenario;dist=np.exp(model.x);m=TRUTH[0]*dist[None,:]+(model.sample.direction@TRUTH[1:])[:,None]+s.kappa*(75*dist)**2/d.module.C
 mean=25+d.module.A*model.x[None,:]+d.module.K*m
 sd=np.sqrt(model.sample.sigma_mu[:,None]**2+d.module.K**2*s.s_u_km_s**2)
 probs=[];mx=[];mx2=[]
 for i in range(len(model.sample.group_id)):
  lo=(31-mean[i,:,None]-model.eta)/sd[i,:,None];hi=(35-mean[i,:,None]-model.eta)/sd[i,:,None]
  logsel=d.module.log_cdf_interval(lo,hi);pw=np.exp(model.log_gw[:,None]+logsel-zz[i]);joint=pw*ew
  mx.append(float(np.sum(joint*model.x[:,None])));mx2.append(float(np.sum(joint*model.x[:,None]**2)))
  probs.append([float(np.sum(joint*np.exp(d.module.log_cdf_interval(lo,(cut-mean[i,:,None]-model.eta)/sd[i,:,None])-logsel)))for cut in(33,34)])
 em=float(ew@model.eta);ev=float(ew@(model.eta-em)**2)
 return np.array([em/.05,ev/.0025,*mx,*mx2,*np.ravel(probs)])

def generate(model,n=32):
 rng=np.random.default_rng(SEED);_,zz=model.row_terms(TRUTH);ew=np.exp(model.log_eta_w+zz.sum(0)-logsumexp(model.log_eta_w+zz.sum(0)))
 ei=rng.choice(len(model.eta),n,p=ew);mu=np.empty((n,24));vh=np.empty_like(mu);x=np.empty_like(mu);t=np.empty_like(mu)
 s=model.scenario;dist=np.exp(model.x)
 for j,e in enumerate(ei):
  eta=model.eta[e]
  for i in range(24):
   m=TRUTH[0]*dist+model.sample.direction[i]@TRUTH[1:]+s.kappa*(75*dist)**2/d.module.C
   mean=25+d.module.A*model.x+d.module.K*m+eta;var=model.sample.sigma_mu[i]**2+d.module.K**2*s.s_u_km_s**2;sd=np.sqrt(var)
   lo=(31-mean)/sd;hi=(35-mean)/sd;lp=model.log_gw+d.module.log_cdf_interval(lo,hi);ix=rng.choice(len(dist),p=np.exp(lp-logsumexp(lp)))
   x[j,i]=model.x[ix];mu[j,i]=truncnorm.rvs(lo[ix],hi[ix],loc=mean[ix],scale=sd,random_state=rng)
   tm=m[ix]+d.module.K*s.s_u_km_s**2/var*(mu[j,i]-mean[ix]);tv=s.s_u_km_s**2-(d.module.K*s.s_u_km_s**2)**2/var
   t[j,i]=rng.normal(tm,np.sqrt(tv));vh[j,i]=d.module.C*np.expm1((t[j,i]+rng.normal(0,s.s_spec_km_s))/d.module.C)
 return dict(mu=mu,Vh=vh,x_log_dA=x,t_km_s=t,eta=model.eta[ei],seed=np.array(SEED),truth_H_B=TRUTH)

def hessian(model,theta,step):
 q=np.array(theta)/[1,100,100,100];eye=np.eye(4)*step
 def f(v):return -model.log_likelihood(v*np.array([1,100,100,100]))
 c=f(q);h=np.zeros((4,4))
 for i in range(4):
  h[i,i]=(f(q+eye[i])-2*c+f(q-eye[i]))/step**2
  for j in range(i):h[i,j]=h[j,i]=(f(q+eye[i]+eye[j])-f(q+eye[i]-eye[j])-f(q-eye[i]+eye[j])+f(q-eye[i]-eye[j]))/(4*step**2)
 if np.linalg.eigvalsh(h).min()<=0:raise ValueError('Hessian not SPD')
 cov=np.linalg.inv(h)*np.outer([1,100,100,100],[1,100,100,100]);return cov

def numerical_status(generator_delta, rows):
    ok=(generator_delta<1e-4 and len(rows)==32 and all(r.get("status")=="RESOLVED" and r.get("fit",{}).get("best",{}).get("success") and r.get("interval_status")=="GAUSSIAN_WALD_PROXY" for r in rows))
    return "PASS_SCOPED" if ok else "HOLD_NUMERICAL_CHECKS"

def main():
 start=time.monotonic();OUT.mkdir(exist_ok=False);packet,sample,sources=d.intake(R,R/'docs/observational_reboot_20261014/task_packets/RB07_selected_scenario.json');scenario=d.Scenario(**packet['baseline']);g=d.SelectedLaw(sample,scenario,256,64)
 delta=float(np.max(abs(selection_moments(g)-selection_moments(d.SelectedLaw(sample,scenario,384,96)))))
 raw=generate(g);np.savez(OUT/'frozen_generated_catalogues.npz',**raw,group_id=sample.group_id,direction=sample.direction,sigma_mu=sample.sigma_mu)
 results=[]
 for j in range(32):
  row={'index':j,'seed':SEED,'status':'NOT_RUN'}
  try:
   s=d.Sample(sample.group_id,raw['mu'][j],sample.sigma_mu,raw['Vh'][j],sample.direction);model=d.SelectedLaw(s,scenario,192,40);fine=d.SelectedLaw(s,scenario,256,64);fit=model.fit(maxiter=400);theta=fit['best']['theta'];checks=[abs(model.log_likelihood(v)-fine.log_likelihood(v))for v in(TRUTH,theta)]
   row.update(fit=fit,grid_delta_truth_fit=checks,theta=theta,boundary=bool(np.any(np.isclose(np.array(theta)/[1,100,100,100],np.array(d.module.BOUNDS)[:,0]))or np.any(np.isclose(np.array(theta)/[1,100,100,100],np.array(d.module.BOUNDS)[:,1]))),status='RESOLVED' if max(checks)<1e-6 else 'QUADRATURE_UNRESOLVED')
   try:
    c1=hessian(model,theta,.02);c2=hessian(model,theta,.01);change=float(np.max(abs(np.diag(c2)/np.diag(c1)-1)));row['hessian_variance_relative_change']=change
    if change>=.01:raise ValueError('Hessian variance refinement exceeds1percent')
    row['proxy_sigma']=np.sqrt(np.diag(c2)).tolist();row['interval_status']='GAUSSIAN_WALD_PROXY'
   except Exception as exc:row.update(interval_status='UNAVAILABLE',interval_error=str(exc))
  except Exception:row.update(status='FIT_FAILURE',failure=traceback.format_exc())
  results.append(row);d.write_json(OUT/f'catalogue_{j:02d}.json',row)
 resolved=[x for x in results if x['status']=='RESOLVED'];intervals=[x for x in resolved if 'proxy_sigma'in x];summary={'resolved':len(resolved),'total_denominator':32,'missing_intervals':32-len(intervals)}
 if resolved:
  errors=np.array([x['theta']for x in resolved])-TRUTH;summary.update(bias=errors.mean(0).tolist(),RMSE=np.sqrt((errors**2).mean(0)).tolist(),bias_mcse=(errors.std(0,ddof=1)/np.sqrt(len(resolved))).tolist())
 if intervals:
  errors=abs(np.array([x['theta']for x in intervals])-TRUTH);sig=np.array([x['proxy_sigma']for x in intervals]);cover=[]
  for level in(.68,.95):
   k=(errors<=norm.ppf((1+level)/2)*sig).sum(0);n=len(intervals);lo=np.where(k==0,0,beta.ppf(.025,k,n-k+1));hi=np.where(k==n,1,beta.ppf(.975,k+1,n-k));cover.append({'level':level,'covered_counts':k.tolist(),'resolved_interval_denominator':n,'exact_binomial95_low':lo.tolist(),'exact_binomial95_high':hi.tolist()})
  summary['coverage_proxy']=cover
 result={'task':'RB07','scope':'32 conditional selected-scenario injections, not CF4 empirical coverage','source':sources,'truth':TRUTH.tolist(),'seed':SEED,'scenario':asdict(scenario),'generator_moment_max_scaled_delta':delta,'generator_threshold':1e-4,'generator_status':'RESOLVED' if delta<1e-4 else 'QUADRATURE_UNRESOLVED','summary':summary,'results':results,'numerical_status':numerical_status(delta,results),'statistic_vs_bias':'finite conditional bias/RMSE and Gaussian Hessian interval coverage; no physical H0/globaltilt admission','seconds':time.monotonic()-start,'code_sha256':d.digest(Path(__file__)),'law_sha256':d.digest(d.module_path),'requested_author':'gpt-6.1-sol/high','physics_contract':'gpt-6-astra/xhigh','observed':'UNKNOWN'}
 d.write_json(OUT/'result.json',result)
 import matplotlib;matplotlib.use('Agg');from matplotlib import pyplot as plt
 fig,axes=plt.subplots(2,2,figsize=(9,6))
 for i,ax in enumerate(axes.ravel()):
  ax.plot([x['index']for x in resolved],[x['theta'][i]-TRUTH[i]for x in resolved],'o');ax.axhline(0,color='k');ax.set(xlabel='frozen catalogue index',ylabel=['H error (km/s/Mpc)','Bx error(km/s)','By error(km/s)','Bz error(km/s)'][i])
 fig.suptitle('CF4 declared-scenario recovery; resolved fits only');fig.tight_layout()
 for ext in('png','pdf'):fig.savefig(OUT/f'recovery.{ext}',dpi=160)
 (OUT/'report.md').write_text('# CF4 conditional injection recovery\n\n'+json.dumps(summary,indent=2)+'\n\nSame24slots and published modulus error proxies;32 frozen generated catalogues. All failures are retained. Gaussian Wald intervals are an approximate procedure, not empirical CF4 coverage. Generator and fit quadrature checks are separate.\n')
 print(json.dumps({'numerical_status':result['numerical_status'],'resolved':len(resolved),'generator_delta':delta}))
if __name__=='__main__':main()
