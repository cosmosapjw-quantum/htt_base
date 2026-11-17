"""Independent finite checks for the R60 tensor/calibration construction.
These are manufactured experiments, not observations or universal proof certificates.
"""
from __future__ import annotations
import json, math
from pathlib import Path
import numpy as np
from scipy import optimize, stats
from numpy.polynomial import Polynomial

ROOT=Path(__file__).resolve().parent
rng=np.random.default_rng(6172026)
s2,s6=1/math.sqrt(2),1/math.sqrt(6)
E=np.array([[[s2,0,0],[0,-s2,0],[0,0,0]],[[s6,0,0],[0,s6,0],[0,0,-2*s6]],[[0,s2,0],[s2,0,0],[0,0,0]],[[0,0,s2],[0,0,0],[s2,0,0]],[[0,0,0],[0,0,s2],[0,s2,0]]])
G=np.diag([1/3]*3+[2/15]*5)
B=np.diag([3.]*3+[7.5]*5)

# Exact fourth-moment contraction, independently of angular quadrature.
# <n_i n_j n_k n_l>=(delta_ij delta_kl+delta_ik delta_jl+delta_il delta_jk)/15.
gram=np.zeros((8,8));gram[:3,:3]=np.eye(3)/3
for a in range(5):
 for b in range(5):
  gram[3+a,3+b]=(np.trace(E[a])*np.trace(E[b])+2*np.sum(E[a]*E[b]))/15

# Mixed irrep transformation and likelihood invariance under a general rotation.
r,_=np.linalg.qr(rng.normal(size=(3,3)))
if np.linalg.det(r)<0:r[:,0]*=-1
d2=np.einsum('aij,ik,bkl,jl->ab',E,r,E,r)
D=np.zeros((8,8));D[:3,:3]=r;D[3:,3:]=d2
h=rng.normal(size=8);u=rng.normal(size=8)
z=rng.normal(size=(8,8));cov=z@z.T+np.eye(8)
j=np.linalg.inv(cov);jrot=D@j@D.T
rot_errors={
 'orthogonal':float(np.max(np.abs(D.T@D-np.eye(8)))),
 'rms_metric':float(np.max(np.abs(D.T@G@D-G))),
 'likelihood':float(abs(h@j@h-(D@h)@jrot@(D@h))),
 'linear_contraction':float(abs(u@h-(D@u)@(D@h)))
}

# Profile covariance equality for an actual mixed correlated SPD 11D carrier.
z=rng.normal(size=(11,11));cov11=z@z.T+np.eye(11)
j11=np.linalg.inv(cov11)
schur=j11[3:,3:]-j11[3:,:3]@np.linalg.solve(j11[:3,:3],j11[:3,3:])
schur_error=float(np.max(np.abs(schur-np.linalg.inv(cov11[3:,3:]))))

# Constrained calibrated null: spectral trust-region solution vs SLSQP oracle.
hat=rng.normal(size=8);hat*=5/np.sqrt(hat@G@hat)
covh=cov11[3:,3:];Jh=np.linalg.inv(covh);Bl=np.linalg.cholesky(B)
a,V=np.linalg.eigh(Bl.T@Jh@Bl);nu=V.T@np.linalg.solve(Bl,hat)
rhos=[0.,0.1,0.8,2.,4.,6.]
rows=[]
for rho in rhos:
 if np.linalg.norm(nu)<=rho:
  lam=0.;b=nu.copy()
 elif rho==0:
  lam=None;b=np.zeros(8)
 else:
  f=lambda lam:np.sum((a*nu/(a+lam))**2)-rho**2
  hi=max(a)
  while f(hi)>0:hi*=2
  lam=optimize.brentq(f,0,hi,xtol=1e-13,rtol=1e-14)
  b=a*nu/(a+lam)
 xi=Bl@V@b
 d2val=float((hat-xi)@Jh@(hat-xi))
 if rho>0:
  obj=lambda x:float((hat-x)@Jh@(hat-x))
  sol=optimize.minimize(obj,np.zeros(8),jac=lambda x:-2*Jh@(hat-x),
    constraints={'type':'ineq','fun':lambda x:rho*rho-x@G@x,'jac':lambda x:-2*G@x},
    method='SLSQP',options={'ftol':1e-12,'maxiter':2000})
  err=abs(float(sol.fun)-d2val);ok=bool(sol.success)
 else:err=0.;ok=True
 rows.append({'rho':rho,'delta2':d2val,'constraint':float(xi@G@xi),'oracle_abs_error':err,'oracle_success':ok})

# Covariance scale/Wald counterexample: increasing PSD covariance can increase W.
wald=[]
for lam in [0,.1,1,10,100]:
 C=np.eye(2)+lam*np.ones((2,2)); y=np.array([0.,1.]);X=np.array([[1.],[0.]])
 ci=np.linalg.inv(C);J=X.T@ci@X;t=X.T@ci@y
 W=float(t@np.linalg.solve(J,t));exact=lam*lam/((1+lam)*(1+2*lam))
 wald.append({'lambda':lam,'wald':W,'exact_error':abs(W-exact),'omnibus':float(y@ci@y)})

# Fixed-mean covariance-amplitude likelihood counterexample using polynomial oracle.
lam=np.array([100.,1.]);p2=np.array([0.,20.]);den=[Polynomial([1.,q]) for q in lam]
P=Polynomial([0.])
for i in range(2):
 t=lam[i]*Polynomial([p2[i]-1.,-lam[i]])
 for k in range(2):
  if k!=i:t=t*den[k]**2
 P=P+t
roots=sorted(float(z.real) for z in P.roots() if abs(z.imag)<1e-10 and z.real>=0)
f=lambda a:float(.5*np.sum(p2*(a*lam)/(1+a*lam)-np.log1p(a*lam)))
amp={'score_at_zero':float(.5*np.sum(lam*(p2-1))),
     'upper_bound':float(max(0,np.max((p2-1)/lam))),
     'roots':roots,'loglik_gains_at_roots':[f(a) for a in roots],
     'loglik_gain_at_one':f(1),'global_mle':max([0,*roots],key=f)}
assert np.max(np.abs(gram-G))<1e-15
assert max(rot_errors.values())<1e-12
assert schur_error<1e-12
assert max(row['oracle_abs_error'] for row in rows)<1e-8
assert all(row['oracle_success'] for row in rows)
assert all(rows[i]['delta2']>=rows[i+1]['delta2']-1e-11 for i in range(len(rows)-1))
assert amp['score_at_zero']<0 and amp['loglik_gain_at_one']>0
assert wald[0]['wald']==0 and wald[-1]['wald']>0.4
out={'kind':'finite_independent_synthetic_checks','seed':6172026,'source_base_commit':'6fe19c5139004a1f281ec85c592e5ab4c7590d5f',
     'angular_gram_max_error':float(np.max(np.abs(gram-G))),'rotation_errors':rot_errors,
     'profile_marginal_covariance_error':schur_error,'calibration_constraint_checks':rows,
     'covariance_wald_nonmonotonicity':wald,'amplitude_counterexample':amp,
     'mag_per_log_distance':5/math.log(10),'status':'PASS_SCOPED'}
(ROOT/'tensor_theory_checks.json').write_text(json.dumps(out,indent=2)+'\n')
print(json.dumps(out,indent=2))
