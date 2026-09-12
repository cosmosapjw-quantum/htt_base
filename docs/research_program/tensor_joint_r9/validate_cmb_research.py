#!/usr/bin/env python3
"""CMB research discriminators on synthetic algebra/metric fixtures only."""
from pathlib import Path
import json,hashlib
import numpy as np
from scipy.linalg import expm
from scipy.stats import beta

P=Path(__file__).resolve().parent; O=P/'evidence'; O.mkdir(exist_ok=True)
rng=np.random.default_rng(20260913)
result={'scope':'SYNTHETIC_ALGEBRA_AND_METRIC_FIXTURES','seed':20260913,
 'script_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
 'actual_R8_pool_continued':False,'observational_law_admitted':False}

# Exact score is the kth other-row distance. Enclosures retain inclusive ties.
cases=[]
for m in [11,31,101]:
    k=int(np.ceil(np.sqrt(m-1)));x=rng.normal(size=(m,4))
    if m==31:x[1]=x[0] # retained coincident-row tie case
    d=np.linalg.norm(x[:,None,:]-x[None,:,:],axis=2)
    exact=np.sort(d+np.diag(np.full(m,np.inf)),axis=1)[:,k-1]
    pexact=float(np.count_nonzero(exact>=exact[0])/m)
    for width in [1.,.1,0.]:
        lo=np.maximum(0,d-width);hi=d+width;np.fill_diagonal(lo,0);np.fill_diagonal(hi,0)
        sLo=np.sort(lo+np.diag(np.full(m,np.inf)),axis=1)[:,k-1]
        sHi=np.sort(hi+np.diag(np.full(m,np.inf)),axis=1)[:,k-1]
        a,b=sLo[0],sHi[0]
        below=high=0
        for i in range(1,m):
            other=np.arange(m)!=i
            below+=int(np.count_nonzero(hi[i,other]<a)>=k)
            high+=int(np.count_nonzero(lo[i,other]>=b)>=m-k)
        lower=(1+high)/m;upper=(m-below)/m
        assert lower<=pexact+1e-14<=upper+1e-14
        # Actual metric distances at two pivots provide certified triangle envelopes.
        piv=[0,1]; tl=np.zeros_like(d);tu=np.full_like(d,np.inf)
        for v in piv:
            tl=np.maximum(tl,np.abs(d[:,v,None]-d[None,v,:]))
            tu=np.minimum(tu,d[:,v,None]+d[None,v,:])
        assert np.max(tl-d)<1e-10 and np.max(d-tu)<1e-10
        cases.append({'rows':m,'k':k,'interval_half_width':width,'rank_exact':pexact,
          'rank_interval':[lower,upper],'below_witnesses':below,'high_witnesses':high})
result['threshold_witness_cases']=cases

# Ideal fixed three-dimensional subspace in seven-dimensional isotropic Gaussian O.
# This tests the probability derivation, not the actual sky or cut-sky processing.
draws=20000;o=rng.normal(size=(draws,7));f=np.sum(o[:,:3]**2,axis=1)/np.sum(o**2,axis=1)
tail=1-2.5*f**1.5+1.5*f**2.5
assert np.max(np.abs(tail-beta.sf(f,1.5,2)))<1e-12
cnt=int(np.count_nonzero(tail<=.05))
ci=[float(beta.ppf(.025,cnt,draws-cnt+1)),float(beta.ppf(.975,cnt+1,draws-cnt))]
result['ideal_projection_fraction']={'draws':draws,'observed_mean':float(np.mean(f)),
 'analytic_mean':3/7,'rejections':cnt,'empirical_size':cnt/draws,'binomial_95_percent':ci,
 'law':'Beta(3/2,2), only conditional isotropic independent O and fixed rank-three projector'}

# Full two-block joint-law finite transformation, not a plug-in conditional template.
B=rng.normal(size=(7,5))/4
G=np.block([[np.zeros((5,5)),-B.T],[B,np.zeros((7,7))]])
covrows=[]
for c3 in [1.,.4]:
    c2=1.;C=np.diag([c2]*5+[c3]*7)
    oracle=(c2-c3)*B
    errors=[]
    for h in [.002,.001,.0005]:
        Kp=expm(h*G);Km=expm(-h*G)
        finite=(Kp@C@Kp.T-Km@C@Km.T)/(2*h)
        errors.append(float(np.linalg.norm(finite[5:,:5]-oracle)))
    assert max(errors)<1e-5
    if c3!=c2: assert 3.8<errors[0]/errors[1]<4.2
    covrows.append({'C2':c2,'C3':c3,'steps':[.002,.001,.0005],
      'derivative_errors':errors,'conditional_mean_multiplier':1-c3/c2,
      'interpretation':'Unitary two-block algebra fixture; full masked sky needs its own joint law.'})
result['joint_law_response_cells']=covrows
(O/'cmb_research_checks.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps({'threshold_cases':len(cases),'beta_draws':draws,'joint_response_cells':len(covrows),'status':'PASS_SCOPED'},indent=2))
