"""Normalised shared-calibration and fixed-slot selection probability laws.

This mathematical module is not an empirical validated Cosmicflows-4 selection
function or calibrated H0 likelihood. It accepts observations on one declared
measurement scale and explicitly distinguishes the two different sampling laws:
preselection shared calibration vs independently slot-conditioned calibration.
No DMzp/DMsnIa double-counting or fictitious survey covariance is permitted.
"""
from __future__ import annotations

import numpy as np
from numpy.polynomial.hermite import hermgauss
from scipy.special import logsumexp, log_ndtr

LOG2PI=np.log(2*np.pi)
MAGVELOCITY=5./np.log(10.)

class Cf4SelectedLawError(ValueError):
    pass


def _inputs(y,mean,sigma):
    if any(np.iscomplexobj(v) for v in (y,mean,sigma)):
        raise Cf4SelectedLawError('real measurement law only')
    obs=np.asarray(y,float); model=np.asarray(mean,float); s=np.asarray(sigma,float)
    if (obs.ndim!=1 or not len(obs) or model.shape!=obs.shape or s.shape!=obs.shape
        or not all(np.isfinite(a).all() for a in (obs,model,s)) or np.any(s<=0)):
        raise Cf4SelectedLawError('finite equal-length observations, model and positive sigmas')
    return obs,model,s


def _tau(tau):
    v=float(tau)
    if not np.isfinite(v) or v<0:
        raise Cf4SelectedLawError('shared calibration Gaussian standard deviation >= 0')
    return v


def _selection_bounds(lower,upper,y):
    if any(np.iscomplexobj(a) for a in (lower,upper)):
        raise Cf4SelectedLawError('real selection interval required')
    lo=np.asarray(lower,float);hi=np.asarray(upper,float)
    if lo.shape!=y.shape or hi.shape!=y.shape or np.isnan(lo).any() or np.isnan(hi).any() or np.any(lo>=hi):
        raise Cf4SelectedLawError('nonempty selection interval per slot required')
    if np.any(y<lo) or np.any(y>hi):
        raise Cf4SelectedLawError('observed y outside declared selection support')
    return lo,hi


def _log_gaussian_normalizer(mu,sig,lo,hi):
    """Stable log P(lo < Gaussian(mu,sig) < hi), componentwise."""
    u=(hi-mu)/sig;l=(lo-mu)/sig
    # Upper negative uses lower-tail logarithms, lower positive uses
    # upper-tail logarithms. Remaining intervals straddle zero.
    ans=np.empty(np.broadcast_shapes(u.shape,l.shape),dtype=float)
    uu,ll=np.broadcast_arrays(u,l)
    neg=uu<=0
    pos=ll>=0
    mid=~(neg|pos)
    def log_difference(loglarge,logsmall):
        delta=np.minimum(0.,logsmall-loglarge)
        return loglarge + np.log(-np.expm1(delta))
    with np.errstate(divide='ignore',over='ignore',invalid='ignore'):
        ans[neg]=log_difference(log_ndtr(uu[neg]),log_ndtr(ll[neg]))
        ans[pos]=log_difference(log_ndtr(-ll[pos]),log_ndtr(-uu[pos]))
        # 1 - Phi(l) - (1-Phi(u)), express 1 - smaller tail sum
        ans[mid]=np.log1p(-np.exp(log_ndtr(ll[mid]))-np.exp(log_ndtr(-uu[mid])))
    if np.any(np.isnan(ans)):
        raise Cf4SelectedLawError('invalid Gaussian truncation probability')
    return ans


def _quad_nodes(nquad,sigma_eta):
    if not isinstance(nquad,int) or not 8<=nquad<=160:
        raise Cf4SelectedLawError('Hermite quadrature order 8..160 required')
    if sigma_eta==0:
        return np.array([0.]),np.array([0.])
    nodes,weights=hermgauss(nquad)
    return np.sqrt(2.)*sigma_eta*nodes, np.log(weights)-.5*np.log(np.pi)


def shared_calibration_gaussian_logpdf(y,mean,sigma,sigma_eta):
    """Exact Gaussian marginal normalisation via Sherman-Morrison.

    If independent group errors D=diag(sigma^2) and eta~N(0,tau^2),
    y~N(mean,D+tau^2 * 1 1.T). No selection is assumed by this function.
    """
    y,m,s=_inputs(y,mean,sigma)
    t=_tau(sigma_eta)
    r=y-m
    inv=1/s**2
    W=np.sum(inv)
    tr=np.sum(inv*r)
    detterm=np.log1p(t*t*W)
    chisq=np.sum(inv*r*r) - (t*t*tr*tr)/(1+t*t*W)
    if chisq<0 and abs(chisq)<1e-10:chisq=0.
    return float(-.5*(chisq+np.sum(2*np.log(s))+detterm+len(y)*LOG2PI))


def gaussian_preselection_loglik(y,mean,sigma,sigma_eta,lower,upper,*,nquad=80):
    """Jointly conditioned on selected slots after ONE shared eta was drawn.

    Numerator integrates eta jointly before conditioning:
      int p(eta) prod phi_i(y_i | m_i+eta) d eta
    Denominator:
      int p(eta) prod P_i(S_i | m_i+eta) d eta
    This is a valid experiment ONLY if the supplied selection intervals
    genuinely describe the underlying generative selection mechanism.
    """
    y,m,s=_inputs(y,mean,sigma)
    t=_tau(sigma_eta); lo,hi=_selection_bounds(lower,upper,y)
    nodes,logw=_quad_nodes(nquad,t)
    u=m[None,:]+nodes[:,None]
    sz=_log_gaussian_normalizer(u,s[None,:],lo[None,:],hi[None,:])
    logden=float(logsumexp(logw+sz.sum(axis=1)))
    if not np.isfinite(logden):
        raise Cf4SelectedLawError('selection support probability numerically zero')
    return shared_calibration_gaussian_logpdf(y,m,s,t)-logden


def gaussian_slot_conditioned_loglik(y,mean,sigma,sigma_eta,lower,upper,*,nquad=80):
    """Different experiment: draw eta prior then independently truncate slots.

    The correct law for that experiment integrates products phi_i / Zi at
    prior p(eta). Do NOT interchange with preselection shared-calibration law.
    """
    y,m,s=_inputs(y,mean,sigma)
    t=_tau(sigma_eta);lo,hi=_selection_bounds(lower,upper,y)
    nodes,logw=_quad_nodes(nquad,t)
    u=m[None,:]+nodes[:,None]
    lognum=(-.5*((y[None,:]-u)/s[None,:])**2
            -np.log(s)[None,:]-.5*LOG2PI)
    logzi=_log_gaussian_normalizer(u,s[None,:],lo[None,:],hi[None,:])
    logterms=lognum-logzi
    if not np.isfinite(logterms).all():
        raise Cf4SelectedLawError('conditioned slot likelihood invalid')
    return float(logsumexp(logw+logterms.sum(axis=1)))


def uncalibrated_distance_model(vcmb_km_s,H_proxy_km_s_Mpc,angular_mag=None):
    """A declared low-z *proxy* m=25+5 log10(Vcmb/H_proxy)+angular_mag.

    Not a cosmological distance law or certified optical first-jet reconstruction.
    Actual Vcmb is a frame-derived published group velocity, not latent ztrue.
    """
    if np.iscomplexobj(vcmb_km_s):
        raise Cf4SelectedLawError('real published velocity proxy')
    v=np.asarray(vcmb_km_s,dtype=float)
    H=float(H_proxy_km_s_Mpc)
    if v.ndim!=1 or not np.isfinite(v).all() or np.any(v<=0) or not np.isfinite(H) or H<=0:
        raise Cf4SelectedLawError('positive velocity and scale proxy required')
    model=25.+5.*np.log10(v/H)
    if angular_mag is not None:
        x=np.asarray(angular_mag,float)
        if x.shape!=v.shape or not np.isfinite(x).all():
            raise Cf4SelectedLawError('angular magnitude source mismatch')
        model=model+x
    return model


def combined_distance_uncertainty(sigma_mu,vcmb_km_s,velocity_width_km_s):
    """Scenario only: independent radial Gaussian velocity -> linearised modulus error."""
    if np.iscomplexobj(sigma_mu) or np.iscomplexobj(vcmb_km_s):
        raise Cf4SelectedLawError('real uncertainties required')
    s=np.asarray(sigma_mu,dtype=float)
    v=np.asarray(vcmb_km_s,dtype=float)
    width=float(velocity_width_km_s)
    if (s.ndim!=1 or v.shape!=s.shape or not all(np.isfinite(q).all() for q in (s,v))
        or np.any(s<=0) or np.any(v<=0) or not np.isfinite(width) or width<0):
        raise Cf4SelectedLawError('positive group measurement errors and velocity scale needed')
    if width==0:
        return s.copy()
    return np.hypot(s,MAGVELOCITY*width/v)


def profiled_common_offset_chisq(y,mean,sigma):
    """Exactly eliminate an unrestricted *common* magnitude zero point."""
    y,m,s=_inputs(y,mean,sigma)
    w=1/s**2
    r=y-m
    avg=np.sum(w*r)/np.sum(w)
    return float(np.sum(w*(r-avg)**2))


def fit_intercept_and_dipole(residual_magnitudes,directions,sigma_mu):
    """Fixed-template WLS morphology only, with intercept profiled jointly."""
    yy=np.asarray(residual_magnitudes,float)
    n=np.asarray(directions,float)
    s=np.asarray(sigma_mu,float)
    if (yy.ndim!=1 or n.shape!=(len(yy),3) or s.shape!=yy.shape or len(yy)<4
        or not np.isfinite(n).all() or not np.all(np.isfinite(yy))
        or not np.all(np.isfinite(s)) or np.any(s<=0)
        or not np.allclose(np.linalg.norm(n,axis=1),1,rtol=0,atol=5e-13)):
        raise Cf4SelectedLawError('finite sky/dipole WLS data required')
    X=np.column_stack((np.ones(len(yy)),n))
    Xw=X/s[:,None]
    yw=yy/s
    beta,_,rank,_=np.linalg.lstsq(Xw,yw,rcond=1e-12)
    if rank<4:
        raise Cf4SelectedLawError('angular design rank less than four')
    gram=Xw.T@Xw
    covariance=np.linalg.inv(gram)
    remainder=yy-X@beta
    return {
        'intercept_magnitude':float(beta[0]),
        'dipole':beta[1:].tolist(),
        'dipole_norm_mag':float(np.linalg.norm(beta[1:])),
        'dipole_covariance':covariance[1:,1:],
        'rank':int(rank),
        'weighted_residual_chisq':float(np.sum((remainder/s)**2)),
        'n':int(len(yy)),
        'scope':'Scenario fixed-cohort WLS, not cosmological dipole/acceleration'
    }


def lowrank_calibration_gaussian_logpdf(y,mean,sigma,loadings,shared_covariance):
    """Integrated multichannel shared calibration, exact PSD Gaussian submodel.

    If latent eta is Gaussian with an externally declared PSD covariance
    K_eta, and y=mean+Z eta+eps, eps_i iid independent with sd sigma_i,
    then C=diag(sigma_i^2)+Z K_eta Z.T. This includes all correlations
    among sources represented by the SAME latent calibration vector.
    A true CF4 physical law still needs actual approved Z and K_eta,
    host/event overlaps, selection normalization and velocity law.
    """
    obs,m,s=_inputs(y,mean,sigma)
    if np.iscomplexobj(loadings) or np.iscomplexobj(shared_covariance):
        raise Cf4SelectedLawError('real latent calibration loadings/covariance')
    z=np.asarray(loadings,float)
    k=np.asarray(shared_covariance,float)
    if (z.ndim!=2 or z.shape[0]!=len(obs) or z.shape[1]<1 or k.shape!=(z.shape[1],z.shape[1])
        or not np.isfinite(z).all() or not np.isfinite(k).all()
        or not np.allclose(k,k.T,rtol=1e-11,atol=1e-12)):
        raise Cf4SelectedLawError('latent zero-point block shape/symmetry mismatch')
    eig,uv=np.linalg.eigh((k+k.T)*.5)
    if eig[0]<-1e-11*max(1.,np.max(np.abs(eig))):
        raise Cf4SelectedLawError('latent calibration covariance must be PSD')
    eig=np.maximum(0.,eig)
    a=z@(uv*np.sqrt(eig))
    inv=1/s**2
    r=obs-m
    mat=np.eye(a.shape[1])+a.T@(inv[:,None]*a)
    sign,logd=np.linalg.slogdet(mat)
    if sign<=0 or not np.isfinite(logd):
        raise Cf4SelectedLawError('incoherent calibration matrix determinant')
    u=a.T@(inv*r)
    quad=float(np.sum(inv*r*r)-u@np.linalg.solve(mat,u))
    if quad<0 and quad>-1e-8:quad=0.
    return float(-.5*(quad+np.sum(2*np.log(s))+logd+len(r)*LOG2PI))
