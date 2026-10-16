"""Sharp interval event pushforward for real-CF4-conditioned, *working-only* joint draws.

The four historical overlapping redshift windows are one 36-vector per draw ID;
source conditional Gaussian noise is NOT an astrophysical posterior. Assumed
hard STF/monopole error balls generate exact mathematical conditional envelopes;
physical signed x_C,Q,F,G_F remain entirely UNMEASURED.
"""
from pathlib import Path
from zipfile import ZipFile
import hashlib,json
import numpy as np
from scipy.stats import qmc,norm

SRC = {'selected_source_observables.npz': '86dfd896d5cf8f223396694dfb945137d1d28ea2227bc984665fb43f77fa376c',
       'h03_source_original.zip':'303c78ff655237edf87db972ce882142837fac8588d269d6cd861c76346fb219',
       'H03_CONDITIONAL_MATRIX.npz':'f73fa930809731e69193ea3f0876efe73c499d1e1ca7af05221d3a004247a404'}
SEED=160916

def original_source_draws(folder):
    root=Path(folder)
    for name,digest in SRC.items():
        if hashlib.sha256((root/name).read_bytes()).hexdigest()!=digest:
            raise ValueError('S02 source digest mismatch: '+name)
    with np.load(root/'selected_source_observables.npz',allow_pickle=False) as npz:
        ids=npz['group_id']
    if len(ids)!=35970 or len(np.unique(ids))!=35970:
        raise ValueError('group ID/size drift')
    with np.load(root/'H03_CONDITIONAL_MATRIX.npz',allow_pickle=False) as npz:
        theta=npz['theta4x9'].copy();cov=npz['joint_cov36x36'].copy()
    if theta.shape!=(4,9) or cov.shape!=(36,36) or np.linalg.eigvalsh(cov)[0]<=0:
        raise ValueError('joint source H03 schema drift')
    z=qmc.Sobol(d=36,scramble=True,seed=SEED).random_base2(10)
    z=norm.ppf(np.clip(z,np.finfo(float).eps,1-np.finfo(float).eps))
    draw=(theta.ravel()[None,:]+np.vstack((z,-z))@np.linalg.cholesky(cov).T).reshape(2048,4,9)
    if (draw[:,:,0]<=0).any() or not np.isfinite(draw).all():raise ValueError('invalid working H draw')
    return draw


def ratio_intervals(draws,stf_radius,monopole_radius):
    """Sharp lower/upper ratios ||s+ds||/(H+dH), ||ds||<=b, |dH|<=a.

    b and a have source working-law units km s^-1 Mpc^-1. They must be
    externally supplied as *hard* error bounds; they are not uncertainties
    learned from CF4, physical shear, or a Bayesian posterior.
    """
    x=np.asarray(draws,dtype=float)
    if x.ndim!=3 or x.shape[1:]!=(4,9) or not np.isfinite(x).all():raise ValueError('draws shape')
    H=x[:,:,0];S=np.linalg.norm(x[:,:,4:9],axis=2)
    b=np.asarray(stf_radius,dtype=float);a=np.asarray(monopole_radius,dtype=float)
    if b.shape==() or a.shape==():raise ValueError('provide four declared window-specific radii')
    if b.shape!=(4,) or a.shape!=(4,) or (b<0).any() or (a<0).any() or not np.isfinite(a).all() or not np.isfinite(b).all():
        raise ValueError('invalid radii')
    if np.any(H<=a[None,:]):
        # A denominator touching or crossing zero destroys a finite upper bound.
        raise ValueError('monopole error ball intersects zero; no finite ratio bound')
    lower=np.maximum(0.,S-b[None,:])/(H+a[None,:])
    upper=(S+b[None,:])/(H-a[None,:])
    if np.any(lower>upper+1e-13):raise AssertionError('bad interval ordering')
    return lower,upper


def sharp_event_bounds(low,high,thresholds,weights=None,mode='per_window'):
    """Sharp strict exceedance for independent drawwise, windowwise rectangle ambiguity.

    Complement event uses per-window strict >, with lower true iff l>t;
    upper true iff u>t. Equality to t is nonexceedance, no inference by
    normal approximation. Joint any/all sharp if every window has independent
    allowed perturbations and the draw-support completion is product-separated.
    """
    lo=np.asarray(low,dtype=float);hi=np.asarray(high,dtype=float)
    if lo.shape!=hi.shape or lo.ndim!=2 or lo.shape[1]!=4 or (lo>hi).any():raise ValueError('bad event intervals')
    if weights is None:w=np.full(len(lo),1/len(lo))
    else:
        w=np.asarray(weights,dtype=float)
        if w.shape!=(len(lo),) or (w<0).any() or not np.isfinite(w).all() or not np.isclose(w.sum(),1.,atol=1e-13,rtol=0):
            raise ValueError('weights must be normalized once per joint draw')
    if mode not in ('per_window','at_least_one','all_windows'):raise ValueError('mode')
    out=[]
    for t in thresholds:
        if not np.isfinite(t):raise ValueError('finite threshold')
        l=lo>t;u=hi>t
        if mode=='at_least_one':l=l.any(axis=1);u=u.any(axis=1)
        elif mode=='all_windows':l=l.all(axis=1);u=u.all(axis=1)
        value=(w[:,None]*l).sum(axis=0).tolist() if l.ndim==2 else float(w@l)
        hi_val=(w[:,None]*u).sum(axis=0).tolist() if u.ndim==2 else float(w@u)
        out.append({'threshold':float(t),'lower':value,'upper':hi_val})
    return out


def run(root):
    samples=original_source_draws(root)
    scenarios={
      'exact_working':([0.]*4,[0.]*4),
      'assumed_stf0p5_H0p2':([.5]*4,[.2]*4),
      'assumed_stf1p0_H0p5':([1.]*4,[.5]*4),
    }
    res={}
    for label,(b,a) in scenarios.items():
        lo,hi=ratio_intervals(samples,b,a)
        res[label]={
           'declared_STF5_hard_radius_kms_Mpc':b,
           'declared_H0_hard_radius_kms_Mpc':a,
           'working_ratio_joint_event_bounds':{
             mode:sharp_event_bounds(lo,hi,[.025,.05,.075],mode=mode)
             for mode in ('per_window','at_least_one','all_windows')
           },
           'max_envelope_width':float(np.max(hi-lo)),
        }
    return {
      'schema':'htt.S02_conditional_sharp_coupled_interval_draws/1',
      'sample_count':2048,'joint_draw_shape':[2048,4,9],
      'source_sha256':SRC,
      'claim':'MATHEMATICALLY_SHARP_CONDITIONAL_WORKING_Q_APP_BOUNDS_NOT_PHYSICAL_GAUSS_Q',
      'scenario_bounds_are_assumed_not_measured':True,
      'physical_functionals':{'x_C':'UNMEASURED','Q':'UNMEASURED','F':'DOMAIN_UNCERTIFIED','G_F':'DOMAIN_UNCERTIFIED','physical_unknown_mass':1.0,'physical_Pi_outer':[0.,1.]},
      'scenarios':res,
      'source_unit':'same 2048 coupled samples x four overlapping source windows',
      'selection_and_likelihood':'CF4 H03 source-conditioned Gaussian working law, not physical posterior',
      'notes':'Sharp event bounds require independent arbitrary completion of each sample/window within rectangular hard balls; cross-window coherent physics may reduce identified set.'
    }

if __name__=='__main__':
 import argparse
 p=argparse.ArgumentParser();p.add_argument('--source',default='source');p.add_argument('--output',default='results/S02_CONDITIONAL_SHARP_EVENT_ENVELOPES.json');a=p.parse_args();o=run(a.source);target=Path(a.output);target.parent.mkdir(parents=True,exist_ok=True);target.write_text(json.dumps(o,indent=2,sort_keys=True)+'\n');print(target)
