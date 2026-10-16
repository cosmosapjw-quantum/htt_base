"""A real-CF4-direction *conditional* calibration identifiability experiment.

The observed 35,970 unique groups' direction, method family, and reported e_DMzp
are source locked. Their published errors are NOT calibrated, independent samples
from an admitted selection/velocity likelihood. This module never fits physical
Hubble shear or returns observational p values.

For each method m: X_m = shape design demeaned over that method, W_i=1/e_i^2,
G_m=X_m^T W_m X_m. With method-angular nuisance gamma_m~N(0,tau_m^2 I),
conditional Fisher for a global common beta is
I_m=G_m-G_m(G_m+tau_m^{-2}I)^{-1}G_m
   = Q diag(lambda/(1+tau_m^2 lambda)) Q^T.
When tau_m -> infinite for all m, I -> 0: beta is not identified. This is
algebraic gauge/conditional-data identifiability, not a cosmic no-go.
"""
from __future__ import annotations
import hashlib
from pathlib import Path
import numpy as np

SHA='86dfd896d5cf8f223396694dfb945137d1d28ea2227bc984665fb43f77fa376c'
LABELS=('FP','TF','SN','OTHER')
N=35970

def read_source(path:Path):
    path=Path(path)
    if hashlib.sha256(path.read_bytes()).hexdigest()!=SHA:
        raise ValueError('CF4 35,970 selected source SHA mismatch')
    with np.load(path,allow_pickle=False) as d:
        n=d['n_J2000'].copy()
        family=d['method_family'].copy()
        sig=d['e_dmzp'].copy()
        z=d['z_CMB'].copy()
        ids=d['group_id'].copy()
    if n.shape!=(N,3) or len(family)!=N or len(sig)!=N or len(z)!=N or len(ids)!=N:
        raise ValueError('source array dimensions changed')
    if len(np.unique(ids))!=N or not np.allclose(np.sum(n*n,axis=1),1.,atol=2e-12,rtol=0):
        raise ValueError('nonunique groups or nonunit direction')
    if any(not np.isfinite(y).all() for y in [n,sig,z]) or np.any(sig<=0):
        raise ValueError('nonfinite/singular reported errors')
    if set(np.unique(family).tolist())!=set(LABELS):
        raise ValueError('wrong group-family release')
    return n,family,sig,z

def shape8(n):
    n=np.asarray(n,float)
    if n.ndim!=2 or n.shape[1]!=3 or not np.isfinite(n).all():
        raise ValueError('finite directions Nx3 required')
    x,y,z=n.T
    return np.stack((x,y,z,x*x-z*z,y*y-z*z,2*x*y,2*x*z,2*y*z),axis=1)

def method_grams(x,family,report_sigma,labels=LABELS):
    x=np.asarray(x,float);s=np.asarray(report_sigma,float);family=np.asarray(family)
    if x.ndim!=2 or x.shape[1]!=8 or len(x)!=len(s) or len(family)!=len(x) or np.any(s<=0) or not np.isfinite(s).all():
        raise ValueError('invalid source geometry/uncertainties')
    out={};means={};counts={}
    for m in labels:
        mask=family==m
        if np.sum(mask)<9:raise ValueError('method lacks sufficient sky source')
        w=1./s[mask]**2;v=x[mask];mu=(w[:,None]*v).sum(axis=0)/w.sum()
        vc=v-mu
        G=(vc.T*w)@vc
        out[m]=(G+G.T)/2
        means[m]=mu
        counts[m]=int(np.sum(mask))
    return out,means,counts

def info_marginal(grams,tau,anchored=()):
    """Integrate proper Gaussian angular calibration or fix a declared anchor.

    tau is nuisance prior standard deviation in the same angular coefficient
    (e.g. mag per raw STF basis). tau=inf is flat/improper limit and the
    returned information is precisely zero unless a method is anchored.
    """
    if not isinstance(tau,(float,int,np.floating,np.integer)) or tau<0 or np.isnan(tau):
        raise ValueError('tau must be nonnegative or infinite')
    p=next(iter(grams.values())).shape[0]
    out=np.zeros((p,p),float)
    for m,G in grams.items():
        if G.shape!=(p,p):raise ValueError('inconsistent Gram blocks')
        lam,q=np.linalg.eigh(G)
        if np.min(lam)<-1e-7*np.max(np.abs(lam)):raise ValueError('indefinite Gram')
        lam=np.maximum(0,lam)
        if m in anchored or tau==0:values=lam
        elif np.isinf(tau):values=np.zeros_like(lam)
        else:values=lam/(1+tau*tau*lam)
        out+=(q*values)@q.T
    return (out+out.T)/2

def conditional_standard_errors(info):
    eig=np.linalg.eigvalsh(info)
    if eig.min()<=1e-10*np.maximum(1,eig.max()):return [None]*info.shape[0]
    diag=np.diag(np.linalg.inv(info))
    return np.sqrt(diag).tolist()

def nuisance_span_residual(x,family):
    """Exact sourcewise gauge identity X=Sum_m 1_{method=m} X."""
    recon=sum((family==m)[:,None]*x for m in LABELS)
    return float(np.max(np.abs(x-recon)))

def demeaning_invariant(y,family,w,delta):
    """Method intercept-profiled data do not change under global zero point."""
    y=np.asarray(y,float);w=np.asarray(w,float);d=np.empty_like(y)
    for m in LABELS:
        mask=family==m
        d[mask]=y[mask]-np.average(y[mask],weights=w[mask])
    p=np.empty_like(y);t=y+delta
    for m in LABELS:
        mask=family==m
        p[mask]=t[mask]-np.average(t[mask],weights=w[mask])
    return float(np.max(np.abs(p-d)))

def diagnostics(path,tau_grid=(0,0.005,0.02,0.1,0.5,2,float('inf'))):
    n,m,s,z=read_source(path)
    x=shape8(n);gs,means,counts=method_grams(x,m,s)
    eigens={k:np.linalg.eigvalsh(g) for k,g in gs.items()}
    base=info_marginal(gs,0);info0=np.linalg.eigvalsh(base)
    result={
        'schema':'htt.H02_actual_CF4_angular_nuisance_fisher/1',
        'source_sha256':SHA,'selected_groups':N,
        'source_is_selected_not_parent':True,
        'errors':'RELEASED_e_DMzp_DIAGONAL_CONDITIONAL_ONLY; TRUE_COVARIANCE_UNKNOWN',
        'source_selected_redshift_range':[float(z.min()),float(z.max())],
        'nuisance_type':'METHOD_SPECIFIC_ANGULAR_ADDITIVE_MAGNITUDE_CALIBRATION',
        'conditional_method_counts':counts,
        'method_gram_eigen_minmax':{k:[float(v.min()),float(v.max())] for k,v in eigens.items()},
        'global_method_angular_design_exact_null_max':nuisance_span_residual(x,m),
        'global_mean_zero_point_invariance_max':demeaning_invariant(s,m,1/s**2,-0.147),
        'baseline_global_fisher_minmax':[float(info0.min()),float(info0.max())],
        'grid':[],
        'nuisance_prior_status':'ASSUMED_EXPERIMENTS_NOT_EMPIRICALLY_CALIBRATED',
        'admission':'H02_PENDING; NO_PHYSICAL_SELECTION_OR_COMMON_CALIBRATION_COVARIANCE',
    }
    for tau in tau_grid:
        F=info_marginal(gs,float(tau));eig=np.linalg.eigvalsh(F)
        result['grid'].append({'tau_mag_per_angular_basis':None if np.isinf(tau) else float(tau),
          'nuisance_prior':'IMPROPER_FLAT_LIMIT' if np.isinf(tau) else 'FIXED_ANCHOR_ALL_METHODS' if tau==0 else 'ASSUMED_INDEPENDENT_PROPER_GAUSSIAN',
          'fisher_min':float(eig.min()),'fisher_max':float(eig.max()),
          'rank_numerical':int(np.sum(eig>1e-9)),
          'std_beta_mag_raw_basis':conditional_standard_errors(F)})
    anchors={}
    for k in LABELS:
        f=info_marginal(gs,float('inf'),anchored=[k]);eig=np.linalg.eigvalsh(f)
        anchors[k]={'fisher_min':float(eig.min()),'fisher_max':float(eig.max()),'rank':int(np.sum(eig>1e-9)),
          'meaning':'EXACT_KNOWN_METHOD_ANGULAR_CALIBRATION_ASSUMPTION_NOT_OBSERVED'}
    result['single_anchored_method_sensitivity']=anchors
    return result
