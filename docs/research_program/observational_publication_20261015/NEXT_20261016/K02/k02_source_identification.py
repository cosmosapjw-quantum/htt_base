"""K02: CF4 conditional working-law radial response, not geometric shear.

One immutable 35970-source group catalogue.  Four fixed retrospective
redshift windows. All source units km/s, Mpc; metric (-,+,+,+).
"""
from pathlib import Path
import hashlib
import numpy as np
from scipy.linalg import qr, solve_triangular

SOURCE_SHA = '86dfd896d5cf8f223396694dfb945137d1d28ea2227bc984665fb43f77fa376c'
C_KMS = 299792.458
CENTERS = (.025, .040, .060, .080)
METHODS = ('FP','OTHER','SN','TF')
STF = np.array([
 [[1,0,0],[0,-1,0],[0,0,0]], [[1,0,0],[0,1,0],[0,0,-2]],
 [[0,1,0],[1,0,0],[0,0,0]], [[0,0,1],[0,0,0],[1,0,0]],
 [[0,0,0],[0,0,1],[0,1,0]]],float)
STF /= np.array([np.sqrt(2),np.sqrt(6),np.sqrt(2),np.sqrt(2),np.sqrt(2)])[:,None,None]

def load(p,sha=SOURCE_SHA):
    p=Path(p)
    if hashlib.sha256(p.read_bytes()).hexdigest()!=sha: raise ValueError('exact CF4 source SHA-256 mismatch')
    with np.load(p,allow_pickle=False) as z:
        cols = {k:z[k].copy() for k in ('group_id','dmzp','e_dmzp','z_CMB','n_J2000','method_family')}
    N=len(cols['group_id'])
    if N!=35970 or len(np.unique(cols['group_id']))!=N or cols['n_J2000'].shape!=(N,3): raise ValueError('source/cohort identity mismatch')
    if not np.allclose(np.linalg.norm(cols['n_J2000'],axis=1),1,atol=1e-10):raise ValueError('non-unit sky')
    if not set(np.unique(cols['method_family']))==set(METHODS):raise ValueError('method families have changed')
    if not all(np.isfinite(a).all() for a in (cols['dmzp'],cols['e_dmzp'],cols['z_CMB'],cols['n_J2000'])):raise ValueError('nonfinite source')
    return cols

def features(cols):
    n=cols['n_J2000'];d=10.**((cols['dmzp']-25)/5)
    Xshape=np.column_stack([n,np.einsum('ni,aij,nj->na',n,STF,n,optimize=True)])
    M=d[:,None]*(cols['method_family'][:,None]==np.asarray(METHODS)[None,:])
    Xshape *= d[:,None]
    full=np.column_stack([d,Xshape,M]) # exact monopole= sum of four M columns
    if not np.allclose(full[:,0],full[:,-4:].sum(axis=1),rtol=5e-15,atol=5e-13):raise ValueError('mean design gauge not exact')
    return d,full,Xshape,M

def source_window(cols,center):
    if center not in CENTERS:raise ValueError('window cannot be selected post hoc')
    d,full,shape,M=features(cols)
    sigma=np.hypot(250.,70.*(np.log(10.)/5.)*d*cols['e_dmzp'])
    sw=np.sqrt(np.exp(-.5*((cols['z_CMB']-center)/.012)**2))/sigma
    # Use one fixed-gauge 12D design: four method-dependent intercepts + 8 anisotropic modes
    X=np.column_stack([M,shape]); WX=sw[:,None]*X
    Q,R=qr(WX,mode='economic'); diag=np.abs(np.diag(R));
    if np.min(diag)/np.max(diag)<1e-8:raise ValueError('method-conditioned design rank lost')
    yy=sw*C_KMS*cols['z_CMB']
    alpha=solve_triangular(R,Q.T@yy,lower=False)
    influence=solve_triangular(R,Q.T*sw[None,:],lower=False) # 12 x N; A@cz = alpha
    cov=(influence*sigma[None,:])@(influence*sigma[None,:]).T
    return {'center':center,'intercepts4':alpha[:4],'shape8':alpha[4:], 'cov12':cov,'influence12':influence,'sigma':sigma,'condition_R':float(np.linalg.cond(R))}

def optical_leading_direction(theta,acceleration_over_c,shear,direction):
    """Direction n points OBSERVER -> SOURCE, photon incoming; H_obs=Theta/3+sigma_nn-A.n/c.
    theta has 1/s, a/c 1/s and sigma 1/s. Valid only at observer and leading z.
    """
    n=np.asarray(direction,float);S=np.asarray(shear,float);a=np.asarray(acceleration_over_c,float)
    if not (n.shape==(3,) and S.shape==(3,3) and a.shape==(3,) and abs(n@n-1)<1e-10):raise ValueError('invalid geometry')
    if not np.allclose(S,S.T,atol=1e-12) or abs(np.trace(S))>1e-12:raise ValueError('sigma must be STF')
    return float(theta/3 + n@S@n - n@a)

def compute(p):
    cols=load(p);windows=[source_window(cols,c) for c in CENTERS];
    # keep unique galaxy-group sample IDs, cross-window analytical covariance using identical group noises
    A=np.vstack([w['influence12'][4:] for w in windows]) # only 32 anisotropic modes
    sig=windows[0]['sigma']
    C=(A*sig[None,:])@(A*sig[None,:]).T
    vals=np.linalg.eigvalsh(C)
    if vals[0]<-1e-10:raise ValueError('covariance non PSD')
    # original 9D operator with four calibrations rank 12 of 13 exactly; shape8 after profiling
    d,full,shape,M=features(cols)
    return {
       'source_sha256':SOURCE_SHA,'source_group_count':len(d),'methods':{s:int(np.sum(cols['method_family']==s)) for s in METHODS},
       'window_centers':list(CENTERS),'four_method_intercepts_kmsMpc':[list(map(float,w['intercepts4'])) for w in windows],
       'identified_working_shape8_kmsMpc':[list(map(float,w['shape8'])) for w in windows],
       'condition_R':[w['condition_R'] for w in windows],
       'joint_shape_cov32':C.tolist(),'cov32_eig_min':float(vals[0]),'cov32_eig_max':float(vals[-1]),
       'calibration_gauge':'X_monopole=sum_m X_method; 13-column mean-design rank=12, residual shape8 rank8 under fixed-weight noise',
       'optical_kinematic_bridge':'Only local leading z, same congruence, registered photon incoming convention: H(n)=Theta/3 - A_i n_i/c + sigma_ij n_i n_j; not calibrated from CF4 working coefficients',
       'observed_physical_shear_claim':False,'observed_physical_acceleration_claim':False,'observed_vorticity_claim':False,
       'claims':'SOURCE_CONDITIONED_FIXED_DISTANCE_FIXED_SELECTION_NO_PHYSICAL_LIKELIHOOD'}
