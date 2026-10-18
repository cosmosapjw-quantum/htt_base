"""P1 S02: source-conditioned joint finite *working* measure and physical unknown sectors.

The 4x9 Gaussian below is an assumed working noise law conditioned on the actual
CF4 35970 groups; it is NOT a posterior distribution for physical Gauss x_C.
Uses one joint draw ID for four overlapping redshift windows.
"""
import hashlib,json,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent.parent/'source/s01/htt/obsstat'))
import numpy as np
from scipy.stats import qmc, norm

SOURCE_SHA = '86dfd896d5cf8f223396694dfb945137d1d28ea2227bc984665fb43f77fa376c'
ARCHIVE = '303c78ff655237edf87db972ce882142837fac8588d269d6cd861c76346fb219'
CENTERS=(.025,.04,.06,.08)
SEED=160916
POWER=11  # 2048 complete coupled 4x9 vectors
THRESHOLDS_WORKING = (.025,.05,.075)  # fixed diagnostic thresholds for ||STF5||/H0

def read_h03(archive_path, source_path):
    from zipfile import ZipFile
    a=Path(archive_path);s=Path(source_path)
    if hashlib.sha256(a.read_bytes()).hexdigest()!=ARCHIVE:raise ValueError('H03 archive digest mismatch')
    if hashlib.sha256(s.read_bytes()).hexdigest()!=SOURCE_SHA:raise ValueError('CF4 source digest mismatch')
    with np.load(s,allow_pickle=False) as x:
        if len(x['group_id'])!=35970 or len(np.unique(x['group_id']))!=35970:raise ValueError('CF4 unique group cohort mismatch')
    with ZipFile(a) as z:
        with z.open('htt_six_paper_h03/results/source_h03_v1/H03_CONDITIONAL_MATRIX.npz') as f:
            with np.load(f,allow_pickle=False) as dat:theta=dat['theta4x9'].copy();cov=dat['joint_cov36x36'].copy()
    if theta.shape!=(4,9) or cov.shape!=(36,36) or not np.allclose(cov,cov.T,atol=1e-13):raise ValueError('H03 source contract')
    if np.linalg.eigvalsh(cov)[0]<=0:raise ValueError('no positive definite working covariance')
    return theta,cov

def joint_draw(theta,cov):
    # SciPy Sobol deterministic scrambled draw and antithetic symmetric pairing, 2^POWER rows
    n=1<<POWER
    z=qmc.Sobol(d=36,scramble=True,seed=SEED).random_base2(m=POWER-1)
    z=np.clip(z,np.finfo(float).eps,1-np.finfo(float).eps)
    a=norm.ppf(z)
    a=np.vstack([a,-a])
    L=np.linalg.cholesky(cov)
    vals=(theta.ravel()[None,:]+a@L.T).reshape(n,4,9)
    if vals.shape!=(n,4,9) or not np.isfinite(vals).all():raise ValueError('nonfinite joint finite measure')
    return vals

def working_functional(draw):
    # Source-H03 orthonormal STF basis positions 4..8; no physical sigma identification
    h=draw[:,:,0]
    if not np.all(h>0):raise ValueError('working conditional monopoles nonpositive')
    q=np.linalg.norm(draw[:,:,4:9],axis=2)/h
    return q

def paired_partial_measure(draws,source_sha=SOURCE_SHA):
    from publication_functionals import PartialMeasure,PartialDraw
    n=len(draws)
    return PartialMeasure(tuple(PartialDraw(sample_id=f'CF4_WORKING_JOINT_{i:05d}',weight=1./n,
       congruence_id='OBSERVATIONAL_WORKING_LAW_NO_COMMON_PHYSICAL_CONGRUENCE',input_sha256=source_sha,
       missing_reasons={'Q':'unmeasured_defined','F':'domain_uncertified','G_F':'domain_uncertified'}) for i in range(n)))

def run(archive_path,source_path,output):
    theta,cov=read_h03(archive_path,source_path)
    x=joint_draw(theta,cov)
    q=working_functional(x)
    n=len(x)
    # One vector-valued source, NOT n*4 independent physical skies or galaxies
    p=paired_partial_measure(x)
    pi=p.exceedance('Q',(0.,.25,.5,1.0))
    if pi['unknown_mass']<1-1e-12:raise ValueError('physical unknown mass was silently renormalized')
    pear=np.corrcoef(q,rowvar=False)
    out={
      'schema':'htt.S02_real_CF4_working_partial_joint/1','source_sha256':SOURCE_SHA,
      'source_group_count':35970,'simulation_kind':'CONDITIONAL_GAUSSIAN_SOURCE_WORKING_MEASURE_NOT_POSTERIOR',
      'joint_unit':'one four-window 36-component vector per ID','sample_count':n,
      'selection':'four historical Gaussian z windows centers '+str(list(CENTERS)),
      'source_independence':'same CF4 cohort all four windows','randomization':{'sobol_scramble_seed':SEED,'power':POWER,'antithetic_pairing':True},
      'working_q_definition':'sqrt(sum_{STF5} Q_app_a^2) / H_app; dimensionless, NOT physical Q=x_C/U_sigma',
      'working_q_quantiles':np.quantile(q,[.05,.5,.95],axis=0).tolist(),
      'working_q_exceedance_thresholds':list(THRESHOLDS_WORKING),
      'working_q_exceedance':[(q>t).mean(axis=0).tolist() for t in THRESHOLDS_WORKING],
      'working_q_crosswindow_correlation':pear.tolist(),
      'working_H0_mean':x[:,:,0].mean(axis=0).tolist(),
      'physical_functionals':{'x_C':'UNMEASURED','Q':'UNMEASURED_DEFINED_SECTOR','F':'DOMAIN_UNCERTIFIED','G_F':'DOMAIN_UNCERTIFIED',
                              'joint_partial_mu_unknown_mass':1.0,'Pi_Q_outer_lower':[0.0]*4,'Pi_Q_outer_upper':[1.0]*4,
                              'Pi_interpretation':'Unrestricted mathematical event completion only, not sharp under physical domain restrictions'},
      'no_new_cosmological_anomaly_pvalue':True,
      'claim':'CF4_WORKING_GAUSSIAN_ONLY; physical sectors all unknown, no posterior/tilt/shear claims'}
    Path(output).write_text(json.dumps(out,indent=2,sort_keys=True)+'\n')
    return out
