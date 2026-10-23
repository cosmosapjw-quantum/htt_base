"""Two conditional, shared-action reference laws for the 60 inherited CMB tensors.

Only the stored low-ell harmonic carrier is read. No map or sky is generated.
The four statistics are projections of a retained 60x12 harmonic state.
"""

from __future__ import annotations

import hashlib
import json
import math
import sys
import time
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from scipy.stats import beta

ROOT = Path(__file__).resolve().parents[5]
SOURCE = ROOT / "docs/research_program/observational_publication_20261015/METHOD_EXECUTION_20261023/cmb/RESULT.json"
INPUT = ROOT / "docs/research_program/observational_publication_20261015/ADAPTIVE_RESEARCH_20261023/R25-CMB-CONDITIONAL-GRAM_INPUT.json"
HERE = Path(__file__).resolve().parent
EXPECTED_SOURCE = "107c0ab6af308213c91cb1c38477242864fc24c6e5e0739fe6fb93b9c195bdbb"
EXPECTED_INPUT = "46803ac5255eeb92f0aa72242a3b9a339bb380c5278a7b6654f7093e80fa153b"
SEED = 20261023025
PILOT = 4096
EVAL = 16383
BATCH = 128
THRESHOLDS = (0.0, .1, .25, .5, .75, .9, 1.0)
SQRT2 = math.sqrt(2.0)


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def canonical(raw):
    """(a_l0, sqrt(2) Re a_lm, -sqrt(2) Im a_lm), for each ell."""
    out = np.asarray(raw, dtype=float).copy()
    if out.shape[-1] != 12:
        raise ValueError("expected complete ell 2 and 3 blocks")
    for start, ell in ((0, 2), (5, 3)):
        for m in range(1, ell + 1):
            out[..., start + 2*m-1] *= SQRT2
            out[..., start + 2*m] *= -SQRT2
    return out


def raw_from_canonical(orth):
    out = np.asarray(orth, dtype=float).copy()
    for start, ell in ((0, 2), (5, 3)):
        for m in range(1, ell + 1):
            out[..., start + 2*m-1] /= SQRT2
            out[..., start + 2*m] /= -SQRT2
    return out


def tensors_from_raw(raw):
    """Independent polynomial expansion of real Condon-Shortley harmonics."""
    x = np.asarray(raw, dtype=float)
    a20,a21r,a21i,a22r,a22i = np.moveaxis(x[..., :5], -1, 0)
    a30,a31r,a31i,a32r,a32i,a33r,a33i = np.moveaxis(x[..., 5:], -1, 0)
    a = math.sqrt(5/(16*math.pi)); c = math.sqrt(15/(32*math.pi)); d = math.sqrt(15/(8*math.pi))
    e = math.sqrt(7/(16*math.pi)); f = math.sqrt(21/(64*math.pi))
    g = math.sqrt(105/(32*math.pi)); h = math.sqrt(35/(64*math.pi))
    q = np.zeros(x.shape[:-1]+(3,3))
    q[...,0,0] = -a*a20+2*c*a22r
    q[...,1,1] = -a*a20-2*c*a22r
    q[...,2,2] = 2*a*a20
    q[...,0,1] = q[...,1,0] = -2*c*a22i
    q[...,0,2] = q[...,2,0] = -d*a21r
    q[...,1,2] = q[...,2,1] = d*a21i
    vals = { (0,0,0):2*f*a31r-2*h*a33r,
      (0,0,1):-2*f*a31i/3+2*h*a33i,
      (0,0,2):-e*a30+2*g*a32r/3,
      (0,1,1):2*f*a31r/3+2*h*a33r,
      (0,1,2):-2*g*a32i/3,
      (0,2,2):-(2*f*a31r-2*h*a33r)-(2*f*a31r/3+2*h*a33r),
      (1,1,1):-2*f*a31i-2*h*a33i,
      (1,1,2):-e*a30-2*g*a32r/3,
      (1,2,2):-(-2*f*a31i/3+2*h*a33i)-(-2*f*a31i-2*h*a33i),
      (2,2,2):-(-e*a30+2*g*a32r/3)-(-e*a30-2*g*a32r/3) }
    o = np.empty(x.shape[:-1]+(3,3,3))
    for i in range(3):
        for j in range(3):
            for k in range(3):
                o[...,i,j,k] = vals[tuple(sorted((i,j,k)))]
    return q,o


def bases():
    eye=np.eye(12)
    q,o=tensors_from_raw(raw_from_canonical(eye))
    return q[:5],o[5:]


E2,E3=bases()
DUAL2=np.linalg.pinv(E2.reshape(5,9))
DUAL3=np.linalg.pinv(E3.reshape(7,27))


def load():
    if sha(SOURCE)!=EXPECTED_SOURCE or sha(INPUT)!=EXPECTED_INPUT:
        raise RuntimeError("immutable source/input identity changed")
    data=json.loads(SOURCE.read_text())
    rows=data['bundles']
    if len(rows)!=60:
        raise ValueError("expected 60 inherited views")
    raw=np.array([r['harmonic12_K_CMB'] for r in rows],dtype=float)
    if raw.shape!=(60,12) or not np.isfinite(raw).all():
        raise ValueError("invalid full carrier")
    return rows,canonical(raw)


def haar_so3(rng,n):
    z=rng.normal(size=(n,4)); z/=np.linalg.norm(z,axis=1)[:,None]
    w,x,y,t=np.moveaxis(z,-1,0)
    R=np.empty((n,3,3))
    R[:,0,0]=1-2*(y*y+t*t); R[:,0,1]=2*(x*y-w*t); R[:,0,2]=2*(x*t+w*y)
    R[:,1,0]=2*(x*y+w*t); R[:,1,1]=1-2*(x*x+t*t); R[:,1,2]=2*(y*t-w*x)
    R[:,2,0]=2*(x*t-w*y); R[:,2,1]=2*(y*t+w*x); R[:,2,2]=1-2*(x*x+y*y)
    return R


def haar_od(rng,n,d):
    z=rng.normal(size=(n,d,d))
    q,r=np.linalg.qr(z)
    return q*np.where(np.diagonal(r,axis1=-2,axis2=-1)>=0,1.,-1.)[:,None,:]


def orient_reps(R):
    e2rot=np.einsum('bip,bjq,kpq->bkij',R,R,E2,optimize=True)
    e3rot=np.einsum('bip,bjq,bkr,apqr->baijk',R,R,R,E3,optimize=True)
    d2=e2rot.reshape(len(R),5,9)@DUAL2
    d3=e3rot.reshape(len(R),7,27)@DUAL3
    return d2.transpose(0,2,1),d3.transpose(0,2,1)


def draw(rng,law,n,X):
    if law=='H_orient':
        d2,d3=orient_reps(haar_so3(rng,n))
    elif law=='H_Gram':
        d2,d3=haar_od(rng,n,5),haar_od(rng,n,7)
    else:
        raise ValueError(law)
    y2=np.einsum('bij,vj->bvi',d2,X[:,:5],optimize=True)
    y3=np.einsum('bij,vj->bvi',d3,X[:,5:],optimize=True)
    return np.concatenate((y2,y3),axis=2)


def statistics(Y):
    """Four normalized tensor statistics for every draw and every view."""
    y=np.asarray(Y,dtype=float)
    if y.shape[-1]!=12:
        raise ValueError("missing tensor coordinates")
    q=np.einsum('...a,aij->...ij',y[...,:5],E2,optimize=True)
    o=np.einsum('...a,aijk->...ijk',y[...,5:],E3,optimize=True)
    nq=np.sqrt(np.einsum('...ij,...ij->...',q,q))
    no=np.sqrt(np.einsum('...ijk,...ijk->...',o,o))
    if np.any(nq==0) or np.any(no==0):
        raise ValueError("zero tensor norm: statistic undefined")
    A=q/nq[...,None,None]; B=o/no[...,None,None,None]
    C=np.einsum('...ikl,...jkl->...ij',B,B,optimize=True)-np.eye(3)/3
    tr=np.einsum('...ij,...jk,...ki->...',A,A,A,optimize=True)
    ac=np.einsum('...ij,...ij->...',A,C,optimize=True)
    v=np.einsum('...ijk,...jk->...i',B,A,optimize=True)
    S=np.stack((6*tr*tr,1.5*np.einsum('...ij,...ij->...',C,C),1.5*ac*ac,np.einsum('...i,...i->...',v,v)),axis=-1)
    if np.any(S < -1e-11) or np.any(S > 1+1e-11):
        raise AssertionError("normalized tensor statistic outside [0,1]")
    return S


def rank_tail(pilot,values):
    """Weak upper tail, including every tie, with frozen pilot."""
    p=np.sort(np.asarray(pilot),axis=0)
    v=np.asarray(values)
    if v.shape[-(p.ndim-1):]!=p.shape[1:]:
        raise ValueError('pilot and value coordinates differ')
    pf=p.reshape(len(p),-1)
    vf=v.reshape(-1,pf.shape[1])
    counts=np.empty(vf.shape,dtype=int)
    for j in range(pf.shape[1]):
        counts[:,j]=len(p)-np.searchsorted(pf[:,j],vf[:,j],side='left')
    return ((1+counts)/(len(p)+1)).reshape(v.shape)


def family_score(pilot,values,law):
    tails=rank_tail(pilot,values)
    if law=='H_orient':
        tails[...,:2]=1
    return np.max(-np.log(tails),axis=-1)


def clopper_pearson(count,n,alpha=.01):
    return [float(beta.ppf(alpha/2,count,n-count+1)) if count else 0.,
            float(beta.ppf(1-alpha/2,count+1,n-count)) if count<n else 1.]


def generate(rng,law,X,n):
    out=np.empty((n,len(X),4),dtype=float)
    for start in range(0,n,BATCH):
        stop=min(start+BATCH,n)
        out[start:stop]=statistics(draw(rng,law,stop-start,X))
    return out


def controls(X):
    G=[X[:,:5]@X[:,:5].T,X[:,5:]@X[:,5:].T]
    q,o=tensors_from_raw(raw_from_canonical(X))
    q2=np.einsum('va,aij->vij',X[:,:5],E2)
    o2=np.einsum('va,aijk->vijk',X[:,5:],E3)
    bridge=float(max(np.max(abs(q-q2)),np.max(abs(o-o2))))
    rng=np.random.default_rng(123456)
    errors={}
    for law in ('H_orient','H_Gram'):
        Y=draw(rng,law,32,X)
        gram=max(np.max(abs(np.einsum('bvi,bwi->bvw',Y[:,:,:5],Y[:,:,:5])-G[0])),
                 np.max(abs(np.einsum('bvi,bwi->bvw',Y[:,:,5:],Y[:,:,5:])-G[1])))
        norm=max(np.max(abs(np.linalg.norm(Y[:,:,:5],axis=-1)-np.linalg.norm(X[:,:5],axis=-1))),
                 np.max(abs(np.linalg.norm(Y[:,:,5:],axis=-1)-np.linalg.norm(X[:,5:],axis=-1))))
        errors[law]={'gram_absolute_K2':float(gram),'gram_scaled':float(gram/max(np.max(abs(G[0])),np.max(abs(G[1])))),
                     'norm_scaled':float(norm/max(np.max(np.linalg.norm(X[:,:5],axis=-1)),np.max(np.linalg.norm(X[:,5:],axis=-1))))}
        if law=='H_orient':
            errors[law]['shape_first_two_max_error']=float(np.max(abs(statistics(Y)[:,:,:2]-statistics(X)[None,:,:2])))
    return {'bridge_max_absolute_K':bridge,'action':errors,
      'max_q_symmetry_K':float(np.max(abs(q-q.swapaxes(-1,-2)))),
      'max_q_trace_K':float(np.max(abs(np.trace(q,axis1=-2,axis2=-1)))),
      'max_o_trace_K':float(np.max(abs(np.einsum('viik->vk',o))))}


def mc_moments(X,law,seed=91025,n=2048):
    """Separate check stream and fixed Hoeffding budget; never uses inference draws."""
    rng=np.random.default_rng(seed)
    acc2=np.zeros((12,12)); mean=np.zeros(12)
    for start in range(0,n,BATCH):
        y=draw(rng,law,min(BATCH,n-start),X)
        # Bounded coordinates after scaling by per-ell maximum view norm.
        z=y[:,[0,5,14,29,59],:]
        mean+=np.sum(z,axis=(0,1))/5
        acc2+=np.einsum('bvi,bvj->ij',z,z)/5
    mean/=n; acc2/=n
    g2=X[:,:5].T@X[:,:5]/60
    g3=X[:,5:].T@X[:,5:]/60
    # The actual theorem concerns harmonic-row isotropy and cross-view Gram.
    # A separate selected-view check is reported using a fixed universal bound.
    views=[0,5,14,29,59]
    target=np.zeros((12,12))
    for ell,sl in ((2,slice(0,5)),(3,slice(5,12))):
        power=np.mean(np.sum(X[views,sl]**2,axis=1))/(2*ell+1)
        target[sl,sl]=np.eye(2*ell+1)*power
    bound=max(np.linalg.norm(X[views,:5],axis=1).max(),np.linalg.norm(X[views,5:],axis=1).max())
    # Each mean term in [-B,B], product in [-B²,B²]. 156 checks, delta=0.01.
    eps_mean=bound*math.sqrt(2*math.log(2*156/.01)/n)
    eps_cov=bound**2*math.sqrt(2*math.log(2*156/.01)/n)
    return {'n':n,'selected_views':views,'delta':.01,'checks':156,
            'bound_mean_absolute_K':eps_mean,'bound_second_absolute_K2':eps_cov,
            'max_mean_absolute_K':float(np.max(abs(mean))),
            'max_second_residual_K2':float(np.max(abs(acc2-target))),
            'passed':bool(np.max(abs(mean))<=eps_mean and np.max(abs(acc2-target))<=eps_cov)}


def run():
    start=time.monotonic()
    rows,X=load()
    check=controls(X)
    if (check['bridge_max_absolute_K']>1e-11 or
        any(max(x['gram_scaled'],x['norm_scaled'])>1e-11 for x in check['action'].values()) or
        check['action']['H_orient']['shape_first_two_max_error']>1e-11):
        raise AssertionError('tensor bridge or Gram preservation')
    seeds=np.random.SeedSequence(SEED).spawn(4)
    streams={'H_orient':(np.random.Generator(np.random.PCG64(seeds[0])),np.random.Generator(np.random.PCG64(seeds[1]))),
             'H_Gram':(np.random.Generator(np.random.PCG64(seeds[2])),np.random.Generator(np.random.PCG64(seeds[3])))}
    observed=statistics(X)
    laws={}
    fig,axes=plt.subplots(2,2,figsize=(10,7),layout='constrained')
    for ax,(law,(rp,re)) in zip(axes.flat,streams.items()):
        pilot=generate(rp,law,X,PILOT)
        evaluation=generate(re,law,X,EVAL)
        tp=family_score(pilot,observed,law)
        te=family_score(pilot,evaluation,law)
        counts=np.sum(te>=tp[None,:],axis=0)
        p=(1+counts)/(EVAL+1)
        coord_tails=rank_tail(pilot,observed)
        if law=='H_orient': coord_tails[:,:2]=1
        pi={}
        for threshold in THRESHOLDS:
            strict=np.sum(evaluation>threshold,axis=0)
            pi[str(threshold)]={'count_strict':strict.tolist(),
                'p_addone':((1+strict)/(EVAL+1)).tolist(),
                'underlying_tail_99pct_CP':np.array([clopper_pearson(int(k),EVAL) for k in strict.flat]).reshape(60,4,2).tolist()}
        moments=mc_moments(X,law)
        if not moments['passed']: raise AssertionError('analytic moment control')
        laws[law]={'pilot_n':PILOT,'evaluation_n':EVAL,'observed_statistic':observed.tolist(),
            'pilot_shape':list(pilot.shape),'evaluation_shape':list(evaluation.shape),
            'observed_coordinate_weak_tails':coord_tails.tolist(),
            'observed_family_score':tp.tolist(),'evaluation_ge_counts':counts.tolist(),
            'p_ref_addone':p.tolist(),'p_ref_99pct_CP': [clopper_pearson(int(c),EVAL) for c in counts],
            'strict_Pi':pi,'analytic_moment_control':moments,
            'pilot_statistic_range':[float(pilot.min()),float(pilot.max())],
            'evaluation_statistic_range':[float(evaluation.min()),float(evaluation.max())]}
        ax.hist(p,bins=np.linspace(0,1,21),color='#466b92')
        ax.set(xlabel='conditional reference weak-tail rank',ylabel='60 processing views',title=law)
        ax2=axes.flat[2 if law=='H_orient' else 3]
        ax2.plot(np.arange(60),observed[:,2],label='observed S3')
        ax2.plot(np.arange(60),np.mean(evaluation[:,:,2],axis=0),label='law mean S3')
        ax2.set(xlabel='inherited view order',ylabel='tensor projection S3',title=law)
        ax2.legend(fontsize=8)
        print(law,'elapsed_s',round(time.monotonic()-start,2),flush=True)
    fig.savefig(HERE/'figure.png',dpi=140)
    plt.close(fig)
    result={'task_id':'R25-CMB-CONDITIONAL-GRAM','packet_id':'0d4c0bbfa25cdbd87fa5a78dcb9540a60e22f10396176c266442b98ed58c0b3f',
      'input_identity':'sha256:'+EXPECTED_INPUT,'source_identity':'sha256:'+EXPECTED_SOURCE,
      'owner':'obsstat','status':'DIAGNOSTIC_ONLY','claim_tier':'C0_PROCESSED_MAP_DIAGNOSTIC',
      'transfer_source':'none','views':[{k:r[k] for k in ('source','product','lmax','secondary_window_degrees')} for r in rows],
      'harmonic_basis':'Condon-Shortley canonical real orthonormal (a_l0,sqrt2 Re a_lm,-sqrt2 Im a_lm)',
      'q0_K':1e-5,'o0_K':1e-5,'full_observed_canonical_harmonic_60x12_K':X.tolist(),
      'gram2_K2':(X[:,:5]@X[:,:5].T).tolist(),'gram3_K2':(X[:,5:]@X[:,5:].T).tolist(),
      'laws':laws,'controls':check,'sampler':{'bit_generator':'PCG64','seed':SEED,
       'child_stream_order':['orient_pilot','orient_evaluation','gram_pilot','gram_evaluation'],
       'batch_max':BATCH,'shared_action':True},
      'full_carrier_law':'Y_ell=U_ell X_ell, one independent group action per ell shared by all 60 views; source and algorithm regenerate full tensor draws',
      'Q':'computational gauges q0=o0=1e-5 K; physical MES unavailable',
      'F':'H_Gram convex-hull support h(U)=sum_ell ||X_ell U_ell^T||_*; this does not identify every orbit point',
      'Pi':'strict threshold exceedance under named conditional law only; physical Pi unknown',
      'G_F':'shared draw across processing windows with full cross-view dependence; not physical depth',
      'caveats':['One observed PR3 sky and 60 dependent processing views, not 60 independent skies.',
        'Source invariance under either law is an unverified working assumption for masked processed carriers.',
        'Retrospective current-data exploration; p_ref is not Planck-calibrated or confirmatory.',
        'No native low-ell solver, physical p value, family identification, or original L03 acceptance promotion.']}
    (HERE/'RESULT.json').write_text(json.dumps(result,indent=2)+'\n')
    print('elapsed_s',round(time.monotonic()-start,2),flush=True)


if __name__=='__main__':
    run()
