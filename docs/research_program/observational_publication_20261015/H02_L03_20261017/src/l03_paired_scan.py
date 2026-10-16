"""One-sky-per-row Planck finite processing scan, not an E2E null admission.

Source process-bounded coefficients are six conditions sharing 300 latent sky
rows. Independent calibration subset (first 100) freezes per-method norm
scales, then 200 held-out rows yield a *descriptive, conditional* rank.
No claim real Planck observations are exchangeable with these source sims.
"""
from __future__ import annotations
import hashlib
from pathlib import Path
import numpy as np

SHA='0c104e41b2cbd979bbb92b61a43744fb0e17376d26dd8a534cc90ab79ca23b08'

def read_bank(path):
    if hashlib.sha256(Path(path).read_bytes()).hexdigest()!=SHA:
        raise ValueError('Planck source processing bank hash mismatch')
    with np.load(path,allow_pickle=False) as z:
        o=z['observed'].copy(); p=z['paired'].copy()
    if o.shape!=(6,32) or p.shape!=(6,300,32) or not np.isfinite(o).all() or not np.isfinite(p).all():
        raise ValueError('unadmitted simulation/observed source')
    return o,p

def process_scan(obs,bank,calibration_rows=100):
    obs=np.asarray(obs,float);bank=np.asarray(bank,float)
    if obs.ndim!=2 or bank.ndim!=3 or obs.shape!=(bank.shape[0],bank.shape[2]) or calibration_rows<5 or calibration_rows>=bank.shape[1]:
        raise ValueError('shape or independent split invalid')
    if not np.isfinite(obs).all() or not np.isfinite(bank).all():
        raise ValueError('nonfinite coefficients')
    e_obs=np.sum(obs**2,axis=1);e_null=np.sum(bank**2,axis=2)
    # Training simulations and heldout simulations are disjoint latent sky IDs.
    ref=np.median(e_null[:,:calibration_rows],axis=1)
    if np.any(ref<=0):raise ValueError('invalid calibration reference')
    x_obs=e_obs/ref
    x_eval=e_null[:,calibration_rows:]/ref[:,None]
    t_obs=float(np.max(x_obs)); t_eval=np.max(x_eval,axis=0)
    p_max=(1+np.sum(t_eval>=t_obs))/(1+len(t_eval))
    per=[(1+int(np.sum(row>=xo)))/(1+len(row)) for row,xo in zip(x_eval,x_obs)]
    corr=np.corrcoef(x_eval)
    return {
        'schema':'htt.L03_paired_processed_finite_scan/1',
        'simulated_source_identity':SHA,
        'source':'SIX_PLANCK_PROCESSING_CONDITIONS_SAME_300_LATENT_SKIES',
        'calibration_latent_rows':calibration_rows,'heldout_latent_rows':len(t_eval),
        'independent_unit':'ONE_LATENT_CMB_SKY_PER_NULL_ROW_NOT_SIX_CONDITIONS',
        'scan_statistic':'MAX_six(sum_{ell2..5 real harmonic coeff}^2 / frozen_method_median_null_energy)',
        'observed_scan':t_obs,'heldout_scan_median':float(np.median(t_eval)),
        'heldout_scan_q95':float(np.quantile(t_eval,.95)),
        'heldout_scan_exceed':int(np.sum(t_eval>=t_obs)),
        'descriptive_rank_p':float(p_max),
        'per_method_descriptive_rank_p':[float(x) for x in per],
        'method_energy_correlation_lower_tri':np.round(corr,6).tolist(),
        'min_crossmethod_corr':float(corr[np.triu_indices_from(corr,1)].min()),
        'max_crossmethod_corr':float(corr[np.triu_indices_from(corr,1)].max()),
        'scientific_admission':'CONDITIONAL_PROCESSING_DESCRIPTIVE_RANK_ONLY; PHYSICAL_E2E_NULL_UNKNOWN; NO_ANOMALY_PVALUE',
    }

def crossed_reuse_variance(n_sky,n_noise,sigma_sky,sigma_noise):
    """Two-way crossed reuse of same skies/noise is NOT n_sky*n_noise iid.

    For T_ij = U_i+V_j, independent centered U_i,V_j with variances S^2,N^2,
    Var[mean_{ij}T_ij]=S^2/n_sky+N^2/n_noise.
    Treating cross-products as iid yields (S^2+N^2)/(n_sky*n_noise).
    """
    if min(n_sky,n_noise)<1 or min(sigma_sky,sigma_noise)<0:
        raise ValueError('positive dimensions, nonnegative sigmas required')
    exact=(sigma_sky**2/n_sky+sigma_noise**2/n_noise)
    iid=(sigma_sky**2+sigma_noise**2)/(n_sky*n_noise)
    return {'n_sky':n_sky,'n_noise':n_noise,'var_two_way':exact,'var_naive_iid':iid,
            'sd_inflation_vs_iid':float(np.sqrt(exact/iid)) if iid>0 else None}

def diagnostics(path):
    o,p=read_bank(path)
    d=process_scan(o,p)
    d['crossed_reuse_manufactured_counterfactual']=crossed_reuse_variance(999,300,1,1)
    d['crossed_reuse_manufactured_counterfactual']['not_released_null_bank']='DO_NOT_INFER_FFP10_HAS_999x300_INDEPENDENT_UNITS'
    return d
