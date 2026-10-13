"""Local CF4 sensitivity under declared noise scenarios, with latent profiling.

No physical fit, selection likelihood, or measured covariance is supplied here.
The source-motion row is a model noise penalty, not an additional observation.
"""
from dataclasses import dataclass
import numpy as np

C = 299792.458
A_MAG = 5/np.log(10)
NAMES = ('b0','Bx','By','Bz','H','Ax','Ay','Az','STF1','STF2','STF3','STF4','STF5')
# theta = SCALES * scaled theta; immutable across every mask/noise comparison.
SCALES = np.array([1000.]*4+[100.]*9)
T_CART_TO_FROB = np.array([[1/np.sqrt(2),-1/np.sqrt(2),0,0,0],
 [np.sqrt(1.5),np.sqrt(1.5),0,0,0],[0,0,np.sqrt(2),0,0],
 [0,0,0,np.sqrt(2),0],[0,0,0,0,np.sqrt(2)]])

def stf_crosswalk(coefficients, covariance):
    q,v=np.asarray(coefficients,float),np.asarray(covariance,float)
    if q.shape!=(5,) or v.shape!=(5,5) or not np.isfinite(q).all() or not np.isfinite(v).all():
        raise ValueError('invalid Cartesian STF coefficient/covariance')
    return T_CART_TO_FROB@q,T_CART_TO_FROB@v@T_CART_TO_FROB.T

def angular_design(n):
    n=np.asarray(n,float)
    if n.ndim!=2 or n.shape[1]!=3 or not np.isfinite(n).all() or not np.allclose(np.linalg.norm(n,axis=1),1):
        raise ValueError('unit directions required')
    x,y,z=n.T
    return np.column_stack((np.ones(len(n)),n,(x*x-y*y)/np.sqrt(2),
        (x*x+y*y-2*z*z)/np.sqrt(6),np.sqrt(2)*x*y,np.sqrt(2)*x*z,np.sqrt(2)*y*z))

def local_values(log_r,z,n,theta,calibration=0.):
    r=np.exp(log_r); ang=angular_design(np.asarray(n)[None,:])[0]
    h=theta[0]+np.dot(n,theta[1:4])+r*np.dot(ang,theta[4:])
    return np.array([25+A_MAG*log_r+2*A_MAG*np.log1p(z)+calibration,C*z,C*z-h])

def latent_jacobian(r,z,f):
    r,z,f=np.broadcast_arrays(r,z,f)
    if not all(np.isfinite(x).all() for x in (r,z,f)) or np.any(r<=0) or np.any(z<=-1):
        raise ValueError('latent domain invalid')
    e=np.zeros(r.shape+(3,2)); e[...,0,0]=A_MAG; e[...,0,1]=2*A_MAG/(1+z)
    e[...,1,1]=C; e[...,2,0]=-r*f; e[...,2,1]=C
    return e

@dataclass(frozen=True)
class NoiseScenario:
    name: str
    redshift_sigma_km_s: float
    source_motion_sigma_km_s: float
    common_calibration_free: bool = False
    method_nuisance: bool = False
    def __post_init__(self):
        if not np.isfinite([self.redshift_sigma_km_s,self.source_motion_sigma_km_s]).all() or min(self.redshift_sigma_km_s,self.source_motion_sigma_km_s)<=0:
            raise ValueError('scenario variances must be positive finite')

def profiled_rows(catalog, scenario, *, fiducial_h=70.):
    """One residual per group via a 3x2 whitened null vector (Schur equivalent)."""
    if not np.isfinite(fiducial_h) or fiducial_h<=0:
        raise ValueError('positive fixed fiducial H required')
    z=catalog.vh_km_s/C
    r=np.exp((catalog.modulus-25)/A_MAG)/(1+z)**2
    ang=angular_design(catalog.direction)
    x=np.column_stack((np.ones(len(r)),catalog.direction,r[:,None]*ang))
    sigma=np.column_stack((catalog.modulus_error,np.full(len(r),scenario.redshift_sigma_km_s),np.full(len(r),scenario.source_motion_sigma_km_s)))
    e=latent_jacobian(r,z,np.full(len(r),fiducial_h))/sigma[:,:,None]
    q=np.cross(e[:,:,0],e[:,:,1]); q/=np.linalg.norm(q,axis=1)[:,None]
    signal=-q[:,2,None]*x/sigma[:,2,None]
    nuisance=[]
    if scenario.common_calibration_free:
        nuisance.append(q[:,0]/sigma[:,0])
    if scenario.method_nuisance:
        nuisance.extend((q[:,0,None]*catalog.method_presence/sigma[:,0,None]).T)
    nuisance=np.column_stack(nuisance) if nuisance else np.empty((len(r),0))
    return signal,nuisance,r,z

def information(signal,nuisance,mask=None):
    x,n=np.asarray(signal,float),np.asarray(nuisance,float)
    if x.ndim!=2 or x.shape[1]!=13 or n.ndim!=2 or len(x)!=len(n) or not np.isfinite(x).all() or not np.isfinite(n).all():
        raise ValueError('invalid thin designs')
    if mask is not None:
        mask=np.asarray(mask)
        if mask.dtype!=bool or mask.shape!=(len(x),): raise ValueError('invalid mask')
        x,n=x[mask],n[mask]
    if not len(x): raise ValueError('empty comparison mask')
    x=x*SCALES
    # The tolerance must retain the pre-projection signal scale. Otherwise
    # cancellation roundoff becomes its own reference and looks full rank.
    original_norm=float(np.linalg.norm(x,ord=2))
    projection_error_bound=8*np.finfo(float).eps*max(x.shape[0],x.shape[1],n.shape[1])*original_norm
    nrank=0
    if n.shape[1]:
        u,s,_=np.linalg.svd(n,full_matrices=False)
        nrank=int(np.sum(s>np.finfo(float).eps*max(n.shape)*s[0])) if len(s) and s[0]>0 else 0
        u=u[:,:nrank]; x=x-u@(u.T@x)
    _,s,vt=np.linalg.svd(x,full_matrices=False)
    # full right null basis also needed for tiny samples with fewer than 13 rows.
    if len(x)<13:
        _,s,vt=np.linalg.svd(x,full_matrices=True)
    tol=max(projection_error_bound,np.finfo(float).eps*max(x.shape)*s[0])
    # Nuisance cannot leave more than N-rank(N) independent residual rows.
    rank=min(int(np.sum(s>tol)),max(len(x)-nrank,0)); v=vt[:rank].T
    cov=(v/(s[:rank]**2))@v.T if rank else np.zeros((13,13))
    return {'singular_values':s,'rank':rank,'null_basis_scaled':vt[rank:].T,
        'covariance_scaled_on_estimable_space':cov,'nuisance_rank':nrank,'rows':len(x),
        'rank_tolerance':tol,'preprojection_scaled_design_norm':original_norm,
        'projection_roundoff_bound':projection_error_bound,'fixed_coefficient_scales':SCALES.copy()}

def contrast_uncertainty(result,contrast):
    g=np.asarray(contrast,float)
    if g.shape!=(13,) or not np.isfinite(g).all(): raise ValueError('invalid contrast')
    amplitude=float(np.max(np.abs(g)))
    if amplitude==0:
        return {'estimable':True,'standard_error':0.,'status':'ZERO_CONTRAST'}
    # Normalize before the null test so estimability is unchanged by a nonzero
    # change of contrast units, including very small contrast magnitudes.
    normalized=(g/amplitude)*SCALES
    unit=normalized/np.linalg.norm(normalized)
    null=result['null_basis_scaled']
    if np.linalg.norm(null.T@unit)>1e-8:
        return {'estimable':False,'standard_error':None,'status':'UNBOUNDED_NULL_DIRECTION'}
    variance=normalized@result['covariance_scaled_on_estimable_space']@normalized
    return {'estimable':True,'standard_error':float(amplitude*np.sqrt(max(variance,0.))),
        'status':'LOCAL_SCENARIO_SENSITIVITY_NOT_MEASURED_UNCERTAINTY'}
