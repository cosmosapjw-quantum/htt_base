"""Matched-sky, train-only linear leakage control for finite-null CMB diagnostics.

Observable statistics only. If the observed sky and heldout full joint simulation
rows are exchangeable conditional on independent training, any deterministic
fixed-trained score has a valid finite Monte Carlo rank. This *does not*
establish physical observed/FFP10 exchangeability. No Bianchi/boost inference.
"""
from __future__ import annotations

from dataclasses import dataclass
import numpy as np


class PairedHighModeError(ValueError):
    pass


def _matrix(value, *, name, rows_min=1):
    if np.iscomplexobj(value):
        raise PairedHighModeError(f'{name}: complex harmonic coordinates are not allowed')
    a=np.asarray(value,dtype=float)
    if a.ndim!=2 or a.shape[0]<rows_min or a.shape[1]<1 or not np.isfinite(a).all():
        raise PairedHighModeError(f'{name}: require finite 2D matrix')
    return a


@dataclass(frozen=True)
class FittedLeakageControl:
    mean_y: np.ndarray
    mean_h: np.ndarray
    operator: np.ndarray  # High H(row) -> low Y(row), prediction H @ operator.
    covariance: np.ndarray
    ridge_multiplier: float
    ridge_absolute: float
    cov_shrink: float
    def scaled_scores(self, residual: object) -> np.ndarray:
        r=_matrix(residual,name='residual')
        if r.shape[1]!=self.covariance.shape[0]:
            raise PairedHighModeError('residual dimension mismatch')
        ch=np.linalg.cholesky(self.covariance)
        x=np.linalg.solve(ch,r.T)
        return np.sum(x*x,axis=0)


def _fit_core(residual, *, alpha):
    # Trace-diagonal shrinkage keeps all 32 retained coordinates in a common
    # orthonormal-real microK unit; not a validated sampling law in itself.
    s=np.cov(residual,rowvar=False,ddof=1)
    s=np.atleast_2d(s)
    d=s.shape[0]
    tr=float(np.trace(s))/d
    if not np.isfinite(tr) or tr <= 0:
        raise PairedHighModeError('training scatter zero or invalid')
    c=(1.-alpha)*s+alpha*tr*np.eye(d)
    cond=np.linalg.cond(c)
    if not np.isfinite(cond) or cond>1e12:
        raise PairedHighModeError('regularised training covariance numerically unsupported')
    return c


def fit_control(y: object, h: object, *, ridge_multiplier: float, cov_shrink: float):
    """Fit on independent training SKIES only; no observed/heldout row used."""
    yy=_matrix(y,name='training y',rows_min=4)
    hh=_matrix(h,name='training high proxy',rows_min=4)
    if yy.shape!=hh.shape:
        raise PairedHighModeError('training Y/H must be paired same-sky rows')
    ridge=float(ridge_multiplier)
    alpha=float(cov_shrink)
    if not np.isfinite(ridge) or ridge <= 0 or not np.isfinite(alpha) or not 0<alpha<=1:
        raise PairedHighModeError('positive ridge multiplier and covariance shrink required')
    my=yy.mean(axis=0)
    mh=hh.mean(axis=0)
    ycen=yy-my
    hcen=hh-mh
    hhgram=hcen.T@hcen
    scale=float(np.trace(hhgram))/hh.shape[1]
    if scale<=0 or not np.isfinite(scale):
        raise PairedHighModeError('zero high-mode predictor scatter')
    lam=ridge*scale
    b=np.linalg.solve(hhgram+lam*np.eye(hh.shape[1]),hcen.T@ycen)
    if not np.isfinite(b).all():
        raise PairedHighModeError('unstable ridge control')
    residual=ycen-hcen@b
    cov=_fit_core(residual,alpha=alpha)
    return FittedLeakageControl(my,mh,b,cov,ridge,lam,alpha)


def fit_family(y: object, *, cov_shrink: float):
    """No high proxy, training-only baseline centre and covariance."""
    yy=_matrix(y,name='baseline training',rows_min=4)
    alpha=float(cov_shrink)
    if not np.isfinite(alpha) or not 0<alpha<=1:
        raise PairedHighModeError('invalid baseline covariance shrink')
    my=yy.mean(axis=0)
    cov=_fit_core(yy-my,alpha=alpha)
    return FittedLeakageControl(my,np.zeros(yy.shape[1]),np.zeros((yy.shape[1],yy.shape[1])),cov,0.,0.,alpha)


def transform_rows(y: object, h: object, fitted: FittedLeakageControl):
    yy=_matrix(y,name='scored y')
    hh=_matrix(h,name='scored h')
    if (yy.shape!=hh.shape or yy.shape[1]!=fitted.mean_y.size):
        raise PairedHighModeError('scored joint features do not match trained model')
    return (yy-fitted.mean_y)-(hh-fitted.mean_h)@fitted.operator


def rank_upper_tail(observed: float, null: object):
    if np.iscomplexobj(observed) or np.iscomplexobj(null):
        raise PairedHighModeError('real finite scores required')
    scores=np.asarray(null,dtype=float)
    if (scores.ndim!=1 or len(scores)<1 or
        not np.isfinite(scores).all() or not np.isfinite(observed)):
        raise PairedHighModeError('require finite observed and nonempty heldout scores')
    k=int(np.count_nonzero(scores>=float(observed)))
    return {'exceedances':k,'B':int(len(scores)),'p_rank':float((1+k)/(len(scores)+1))}


def run_fixed_family(observed: object, training: object, calibration: object,
                     *, ridge_multipliers=(.25,1.,4.), cov_shrink=.2):
    """A *fixed* 2-mask x (baseline + three ridge) joint-score family.

    Input shape observed=(2,2,d), training=(n,2,2,d), calibration=(B,2,2,d).
    channel0=retained low 32-vector Y5; channel1=joint high leakage proxy
    H=Y12-Y5 from the SAME masked sky. Both channels are correlated.
    Full observed and calibration latent rows remain paired.
    """
    if any(np.iscomplexobj(x) for x in (observed,training,calibration)):
        raise PairedHighModeError('orthonormal real harmonic coefficients required')
    obs=np.asarray(observed,dtype=float)
    train=np.asarray(training,dtype=float)
    null=np.asarray(calibration,dtype=float)
    if (obs.ndim!=3 or obs.shape[0:2]!=(2,2) or train.ndim!=4
        or null.ndim!=4 or train.shape[1:]!=obs.shape
        or null.shape[1:]!=obs.shape or len(train)<4 or len(null)<1
        or not np.isfinite(obs).all() or not np.isfinite(train).all()
        or not np.isfinite(null).all()):
        raise PairedHighModeError('require finite paired 2-mask, 2-channel joint sky rows')
    if (not ridge_multipliers or len(set(ridge_multipliers))!=len(ridge_multipliers)
        or any((not np.isfinite(x)) or x<=0 for x in ridge_multipliers)):
        raise PairedHighModeError('fixed distinct positive ridge family required')
    obs_score=[]
    cal_score=[]
    models={}
    labels=[]
    testwise=[]
    summaries=[]
    for m in range(2):
        ty,th=train[:,m,0,:],train[:,m,1,:]
        oy,oh=obs[m,0,:][None,:],obs[m,1,:][None,:]
        cy,ch=null[:,m,0,:],null[:,m,1,:]
        options=[('baseline',fit_family(ty,cov_shrink=cov_shrink))]
        options += [(f'{lam:g}',fit_control(ty,th,ridge_multiplier=lam,cov_shrink=cov_shrink)) for lam in ridge_multipliers]
        for name,model in options:
            key=f'{m}:{name}'
            rtrain=transform_rows(ty,th,model)
            robs=transform_rows(oy,oh,model)
            rcal=transform_rows(cy,ch,model)
            scores_train=model.scaled_scores(rtrain)
            scores_obs=float(model.scaled_scores(robs)[0])
            scores_null=model.scaled_scores(rcal)
            mu=float(np.mean(scores_train))
            sigma=float(np.std(scores_train,ddof=1))
            if not np.isfinite(sigma) or sigma<=0:
                raise PairedHighModeError('training score dispersion unsupported')
            obs_score.append((scores_obs-mu)/sigma)
            cal_score.append((scores_null-mu)/sigma)
            testwise.append(rank_upper_tail(scores_obs,scores_null))
            labels.append(key)
            models[key]=model
            summaries.append({'label':key,'ridge_absolute':model.ridge_absolute,
                'training_score_mean':mu,'training_score_sd':sigma,
                'observed_unscaled_score':scores_obs,
                'calibration_median_unscaled_score':float(np.median(scores_null)),
                'heldout_residual_mean_squared_norm':float(np.mean(np.sum(rcal*rcal,axis=1))),
                'train_residual_mean_squared_norm':float(np.mean(np.sum(rtrain*rtrain,axis=1)))})
    obs_vector=np.asarray(obs_score,dtype=float)
    nul=np.stack(cal_score,axis=1)
    maxnull=np.max(nul,axis=1)
    maxobs=float(np.max(obs_vector))
    results=[]
    for i,key in enumerate(labels):
        results.append({**summaries[i],'marginal_rank':testwise[i],
            'joint_max_adjusted_rank':rank_upper_tail(obs_vector[i],maxnull),
            'transformed_observed_score':float(obs_vector[i])})
    return {
        'labels':labels,'per_feature':results,
        'global_rank':rank_upper_tail(maxobs,maxnull),
        'global_observed_max_score':maxobs,
        'observed_scores':obs_vector,
        'null_maxima':maxnull,
        'training_models':models,
        'train_count':int(len(train)),'calibration_count':int(len(null)),
        'scope':'retrospective conditional joint finite rank ONLY: training independent of observed and calibration; physical sky-null exchangeability unverified'
    }
