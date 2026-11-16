#!/usr/bin/env python3
"""Project the same CF4 tensor confidence region into typed five views.

R39/R7-R9 definitions are reused. Support utilization is not occupancy.
The physical pullback below is a declared constant low-z kinematic response
with free dipole/STF calibration; it is not a general Bianchi transfer.
"""
from __future__ import annotations
import argparse, hashlib, importlib.util, json, sys
from pathlib import Path
import numpy as np
from scipy import stats

C_KM_S=299792.458
ALPHA_NAMES=['V_x_km_s','V_y_km_s','V_z_km_s','dH_x','dH_y','dH_z']+[f'kappa_{i}' for i in range(5)]
PARAMETER_NAMES=[*[f'sigma_over_H_{i}' for i in range(5)],*[f'omega_over_H_{i}' for i in range(3)],*[f'A_over_cH_{i}' for i in range(3)],*[f'beta_MR_{i}' for i in range(3)],*[f'calibration_dipole_{i}' for i in range(3)],*[f'calibration_STF_{i}' for i in range(5)]]

def physical_map():
    """alpha=(V,dH,kappa) = K theta, observer-to-source n convention.

    Constant low-z kinematic hypothesis: V=c beta, dH=-A/(cH)+dcal,
    kappa=sigma/H+qcal. omega has no first-order scalar-distance column.
    This is conditional on a common congruence and the stated truncation.
    """
    k=np.zeros((11,22));k[:3,11:14]=C_KM_S*np.eye(3)
    k[3:6,8:11]=-np.eye(3);k[3:6,14:17]=np.eye(3)
    k[6:,0:5]=np.eye(5);k[6:,17:22]=np.eye(5)
    return k

def depth_path_matrix():
    """Reorder polar12|STF20 to four 8-vectors, then keep level0+differences."""
    perm=[]
    for w in range(4): perm.extend([3*w+i for i in range(3)]+[12+5*w+i for i in range(5)])
    p=np.eye(32)[perm];t=np.eye(32)
    for w in range(1,4):t[8*w:8*(w+1),:8]=-np.eye(8)
    return t@p

def directional_contrast(direction):
    """Linear apparent log-H anisotropy dH.n + kappa:nn, excluding V.

    Uses the frozen orthonormal R54 STF5 order. This is a projection of the
    common constant-coefficient hypothesis, not an absolute H0 measurement.
    """
    n=np.asarray(direction,dtype=float)
    if n.shape != (3,) or not np.all(np.isfinite(n)) or not np.any(n):
        raise ValueError('direction must be a finite nonzero three-vector')
    n=n/np.max(np.abs(n))
    x,y,z=n/np.linalg.norm(n)
    stf=np.array([(x*x-y*y)/np.sqrt(2),(x*x+y*y-2*z*z)/np.sqrt(6),
                  np.sqrt(2)*x*y,np.sqrt(2)*x*z,np.sqrt(2)*y*z])
    return np.r_[np.zeros(3),[x,y,z],stf]

def load_module(root,override):
    if override:
        spec=importlib.util.spec_from_file_location('r58_views_fit',override);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
    for p in (root,root/'htt',root/'htt/src'):sys.path.insert(0,str(p))
    from htt.htt.infer import r58_mixed_tensor_likelihood as m
    return m

def clean(o):
    if isinstance(o,dict):return {str(k):clean(v) for k,v in o.items()}
    if isinstance(o,(tuple,list,np.ndarray)):return [clean(v) for v in o]
    if isinstance(o,(np.bool_,bool)):return bool(o)
    if isinstance(o,(np.integer,int)):return int(o)
    if isinstance(o,(np.floating,float)):
        if np.isnan(o): raise ValueError('NaN is not an infinite confidence interval')
        return float(o) if np.isfinite(o) else ('+infinity' if o>0 else '-infinity')
    return o

def compute(root,results,override=None):
    mt=load_module(root,override); src=results/'OWNED_TENSOR_RESULT.json';meta=json.loads(src.read_text());p=results/meta['carrier_file']
    if hashlib.sha256(p.read_bytes()).hexdigest()!=meta['carrier_sha256']:raise ValueError('carrier identity mismatch')
    d=np.load(p,allow_pickle=False);t=depth_path_matrix();k=physical_map();models={};fits=[]
    if meta['parameter_names'] != ALPHA_NAMES or list(d['parameter_names']) != ALPHA_NAMES:
        raise ValueError('coefficient coordinate identity/order mismatch')
    physical_scale=np.array([.01]*11+[300/C_KM_S]*3+[.01]*8)
    for name,row in meta['variants'].items():
        y,c,x=(d[f'{name}__{key}'] for key in ('y32','cov32','response32x11'))
        fit=mt.fit_linear(y,c,x,parameter_scale=d['parameter_scale'])
        if fit['rank'] != 11: raise ValueError('apparent coefficient rank must be 11')
        fits.append(fit)
        transformed=mt.fit_linear(t@y,t@c@t.T,t@x,parameter_scale=d['parameter_scale'])
        # Same density in a determinant-one rearrangement: includes the common level.
        delta=float(abs(mt.gaussian_log_likelihood(fit,fit['estimate'])-mt.gaussian_log_likelihood(transformed,fit['estimate'])))
        if delta>1e-8:raise ValueError('depth-path likelihood not preserved')
        phy=mt.fit_linear(y,c,x@k,parameter_scale=physical_scale)
        if phy['rank'] != 11: raise ValueError('physical pullback rank must be 11')
        intervals={n:mt.linear_interval(phy,np.eye(22)[i]) for i,n in enumerate(PARAMETER_NAMES)}
        c2=float(stats.chi2.ppf(.95,fit['rank']));q=float(np.sqrt(fit['wald']/c2))
        support={}
        for i,label in enumerate(meta['parameter_names']):
            v=np.eye(11)[i];it=mt.linear_interval(fit,v);h0=np.sqrt(c2*float(v@fit['covariance']@v))
            support[label]={'lower':it['lower'],'upper':it['upper'],'null_body_support':h0,'support_utilization_lower':it['lower']/h0,'support_utilization_upper':it['upper']/h0}
        models[name]={
          'x':{'definition_id':'R39_DIRECT_VECTOR_STF_CARRIER','estimate':fit['estimate'],'covariance':fit['covariance'],'measured_rows':f'{name}__y32','full_covariance':f'{name}__cov32','physical_pullback':{'hypothesis':'constant low-z cosmography with free calibration dipole/STF; no omega response','map_11x22':k,'parameter_names':PARAMETER_NAMES,'rank':phy['rank'],'dimension':22,'null_basis':phy['null_basis'],'intervals_95_simultaneous':intervals}},
          'Q':{'definition_id':'R54_DECLARED_ELLIPSOID_GAUGE','anchor':'model-specific centered 95% Gaussian coefficient-noise ellipsoid','value_at_fit':q,'reference_radius_squared':c2,'physical_ceiling':'UNAVAILABLE'},
          'Pi':{'definition_id':'R54_NAMED_LAW_TAIL','law':'fixed C, Gaussian, common coefficient theta=0, chi2(rank=11)','p':fit['wald_p'],'not_independent_of_Q':True},
          'F':{'definition_id':'R39_DIRECTIONAL_SUPPORT_IMAGE','support':support,'occupancy':{'status':'UNAVAILABLE','reason':'no admitted physical ceiling and occupancy measure; support ratio is not a filling fraction'}},
          'G_F':{'definition_id':'R39_INITIAL_LEVEL_PLUS_FULL_COVARIANCE_DEPTH_CONTRASTS','path':t@y,'covariance':t@c@t.T,'transform':t,'likelihood_error':delta,'initial_block_retained':True,'interpretation':'invertible data representation; no new independent likelihood or global-tilt evidence'}
        }
    out={'schema':'htt.r58.five_views/1','owner':'HTT','claim_tier':'C0','source_result_sha256':hashlib.sha256(src.read_bytes()).hexdigest(),'source_carrier_sha256':meta['carrier_sha256'],'models':models,'conclusion':'All 11 apparent coefficients have full joint rank. With free physical calibration, 22 normalized kinematic+nuisance parameters have rank11; sigma, omega and A individually remain unbounded. beta intervals are conditional on this specified constant-velocity response.','definition_guard':'precision J, support utilization F_support and measure occupancy F_occupancy are distinct; Q/Pi/F/G_F share one x likelihood and are not multiplied.'}
    directions={}
    for i,axis in enumerate('xyz'):
        for sign in (-1,1):
            n=sign*np.eye(3)[i];v=directional_contrast(n)
            directions[('+' if sign>0 else '-')+axis]={'n_ICRS':n,'contrast_11':v,
                'simultaneous_95_union_interval_hull':mt.robust_interval(fits,v)}
    out['directional_observable']={'definition':'apparent log-H anisotropy dH.n + kappa:nn; excludes coherent velocity and monopole',
        'approximation':'fractional H anisotropy to first order only, common constant-coefficient fit across existing windows',
        'directions':directions,'selection':'six fixed ICRS coordinate directions, descriptive projections of the same joint confidence union'}
    (results/'FIVE_VIEW_RESULT.json').write_text(json.dumps(clean(out),indent=2,allow_nan=False)+'\n');return out

def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--root',type=Path,default=Path(__file__).resolve().parents[2]);ap.add_argument('--results',type=Path,required=True);ap.add_argument('--fit-module',type=Path);a=ap.parse_args()
    out=compute(a.root,a.results,a.fit_module);print(json.dumps({'models':len(out['models']),'ranks':{k:v['x']['physical_pullback']['rank'] for k,v in out['models'].items()},'max_path_error':max(v['G_F']['likelihood_error'] for v in out['models'].values())}))
if __name__=='__main__':main()
