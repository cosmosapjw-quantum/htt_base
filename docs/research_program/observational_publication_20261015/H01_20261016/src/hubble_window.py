"""Paper-P3 H01: typed, fixed-window CF4 apparent Hubble response.

Linear redshift/distance proxy; NOT an observed cosmological H(z,n),
physical velocity-field reconstruction or independent-group likelihood.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import hashlib
import numpy as np
from scipy.linalg import qr, svdvals

SOURCE_SHA = '86dfd896d5cf8f223396694dfb945137d1d28ea2227bc984665fb43f77fa376c'
C_KM_S = 299792.458
KAPPA = np.log(10.0)/5.0

@dataclass(frozen=True)
class Source:
    z: np.ndarray
    mu: np.ndarray
    mu_error: np.ndarray
    n: np.ndarray
    method: np.ndarray
    ids: np.ndarray


def digest(p: Path) -> str:
    h=hashlib.sha256()
    with Path(p).open('rb') as f:
        for chunk in iter(lambda:f.read(2**20),b''):h.update(chunk)
    return h.hexdigest()


def load_cf4(path: Path, expected_sha: str = SOURCE_SHA) -> Source:
    if digest(path) != expected_sha:raise ValueError('CF4 input SHA mismatch: source identity gate')
    with np.load(path,allow_pickle=False) as f:
        required=['z_CMB','dmzp','e_dmzp','n_J2000','method_family','group_id']
        if any(k not in f.files for k in required):raise ValueError('Missing released group fields')
        z,mu,e,n,method,ids=(f[k].copy() for k in required)
    if (len(z)!=35970 or mu.shape!=z.shape or e.shape!=z.shape or
        n.shape!=(len(z),3) or len(method)!=len(z) or len(ids)!=len(z) or
        np.unique(ids).size!=len(ids) or not np.isfinite(z).all() or
        not np.isfinite(mu).all() or not np.isfinite(e).all() or
        not np.isfinite(n).all() or np.any(z<=0) or np.any(z>=0.2) or
        np.any(e<=0) or np.max(abs(np.linalg.norm(n,axis=1)-1))>2e-12):
        raise ValueError('CF4 source cohort/geometry gate')
    return Source(z,mu,e,n,method,ids)


def distance_proxy_mpc(mu):
    mu=np.asarray(mu,dtype=float)
    if not np.isfinite(mu).all() or np.any((mu<20)|(mu>60)):
        raise ValueError('distance modulus out of working model range')
    return np.power(10.0,(mu-25.0)/5.0)


def errors_proxy_km_s(d,mu_error,h_reference=70.0,sigma_pec=250.0):
    d=np.asarray(d,dtype=float);e=np.asarray(mu_error,dtype=float)
    if (np.any(~np.isfinite(d)) or np.any(~np.isfinite(e)) or
        np.any(d<=0) or np.any(e<0) or h_reference<=0 or sigma_pec<=0):
        raise ValueError('positive distance/error and working noise parameters required')
    return np.hypot(sigma_pec,KAPPA*h_reference*d*e)


def radial_weights(source:Source, center:float, bandwidth:float, ang_alpha:float=0.0,
                   ang_axis=(0.,0.,1.), h_reference=70.,sigma_pec=250.):
    if not (0<center<0.2 and 0<bandwidth<0.2 and abs(ang_alpha)<1):
        raise ValueError('window parameters invalid')
    axis=np.asarray(ang_axis,float)
    if axis.shape!=(3,) or not np.isfinite(axis).all() or not np.linalg.norm(axis)>0:
        raise ValueError('finite nonzero angular axis')
    axis=axis/np.linalg.norm(axis)
    d=distance_proxy_mpc(source.mu)
    sig=errors_proxy_km_s(d,source.mu_error,h_reference,sigma_pec)
    radial=np.exp(-.5*((source.z-center)/bandwidth)**2)
    angular=1.0+ang_alpha*(source.n@axis)
    w=radial*angular/sig**2
    if not np.isfinite(w).all() or np.any(w<0) or np.sum(w*d**2)<=0:
        raise ValueError('degenerate selected window')
    return w,d,sig


def stf_quad(n):
    n=np.asarray(n,float)
    return n[:,:,None]*n[:,None,:]-np.eye(3)[None,:,:]/3


def moments(d,n,w):
    d=np.asarray(d,float);n=np.asarray(n,float);w=np.asarray(w,float)
    if (d.ndim!=1 or n.shape!=(len(d),3) or w.shape!=d.shape or
        not np.isfinite(n).all() or np.max(abs(np.linalg.norm(n,axis=1)-1))>1e-11 or
        not np.isfinite(d).all() or np.any(d<=0) or not np.isfinite(w).all() or np.any(w<0)):
        raise ValueError('invalid fixed window inputs')
    den=float(np.sum(w*d*d))
    if not np.isfinite(den) or den<=0:raise ValueError('singular window')
    alpha=w*d/den # (km/s)^-2 * Mpc / normalizing units; exact linear y weights
    hm=w*d*d/den
    m=hm@n
    b=alpha@n
    Q=np.einsum('i,ij,ik->jk',hm,n,n)-np.eye(3)/3
    if abs(np.trace(Q))>1e-10:raise ArithmeticError('STF trace')
    return {'alpha':alpha,'angular_moment':m,'bulk_inverse_mpc':b,
            'quadrupole_moment':Q,'denominator':den,
            'effective_distance_mpc':float(1.0/(np.sum(w*d)/den)),
            'n_eff_weighted':float((hm.sum()**2)/np.dot(hm,hm))}


def window_hubble(d,n,z,w):
    m=moments(d,n,w)
    obs_v=C_KM_S*np.asarray(z,float)  # strictly cz proxy, not exact FLRW recession law
    if obs_v.shape!=np.shape(d):raise ValueError('redshift group shape mismatch')
    return float(m['alpha']@obs_v),m


def cross_window_covariance(alpha_list,velocity_sigma):
    A=np.stack([np.asarray(a,float) for a in alpha_list])
    sig=np.asarray(velocity_sigma,float)
    if (A.ndim!=2 or sig.shape!=(A.shape[1],) or not np.isfinite(A).all() or
        not np.isfinite(sig).all() or np.any(sig<0)):
        raise ValueError('conditional diagonal velocity covariance required')
    C=(A*sig[None,:]**2)@A.T
    if np.min(np.linalg.eigvalsh(C)) < -1e-10*max(1.0,np.linalg.norm(C,2)):
        raise ArithmeticError('covariance not PSD')
    scale=np.sqrt(np.diag(C))
    corr=C/scale[:,None]/scale[None,:]
    return C,corr


def dipole_bulk_principal_cosines(d,n,w,bulk_scale_mpc=100.):
    d=np.asarray(d,float);n=np.asarray(n,float);w=np.asarray(w,float)
    if bulk_scale_mpc<=0:raise ValueError('bulk scale')
    root=np.sqrt(w)
    N=(root*d)[:,None]
    q0=np.linalg.qr(N,mode='reduced')[0]
    A=(root*d)[:,None]*n
    B=(root*bulk_scale_mpc)[:,None]*n
    A-=q0@(q0.T@A);B-=q0@(q0.T@B)
    QA,RA=qr(A,mode='economic');QB,RB=qr(B,mode='economic')
    if min(np.linalg.svd(RA,compute_uv=False)[-1],np.linalg.svd(RB,compute_uv=False)[-1]) <=0:
        raise ValueError('rank-deficient direction columns')
    cos=svdvals(QA.T@QB)
    return cos


def inject_response(d,n,w,h0,dipole,bulk,quad):
    """Independent direct pixel injection vs contracted monopole moments."""
    m=moments(d,n,w)
    dip=np.asarray(dipole,float);vel=np.asarray(bulk,float);Q=np.asarray(quad,float)
    if dip.shape!=(3,) or vel.shape!=(3,) or Q.shape!=(3,3) or not np.allclose(Q,Q.T) or abs(np.trace(Q))>1e-11:
        raise ValueError('typed dipole/bulk/STF inputs')
    v=h0*d+d*(n@dip)+n@vel+d*np.einsum('ni,ij,nj->n',n,Q,n)
    direct=float(m['alpha']@v)
    predicted=float(h0+dip@m['angular_moment']+vel@m['bulk_inverse_mpc']+np.sum(Q*m['quadrupole_moment']))
    return direct,predicted
