#!/usr/bin/env python3
"""Finite observation/selection calculations; no background evolution solver.

HTT conditional diagnostics. Errors are declared scenario budgets, never
estimated physical errors. Fixed training transforms are part of the contract.
"""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
import numpy as np
from scipy.special import ndtr
from scipy.stats import beta
from numpy.polynomial.legendre import leggauss


def real(value):
    if np.iscomplexobj(value):
        raise ValueError('real finite values required')
    a = np.asarray(value, dtype=float)
    if not np.isfinite(a).all():
        raise ValueError('real finite values required')
    return a


def gaussian_bin(t, lo, hi, sigma):
    """Acceptance and true-coordinate first/second derivatives, fixed edges."""
    t, lo, hi, sigma = np.broadcast_arrays(*map(real, (t, lo, hi, sigma)))
    if np.any(lo >= hi) or np.any(sigma <= 0):
        raise ValueError('ordered finite edges and positive sigma required')
    l, u = (lo-t)/sigma, (hi-t)/sigma
    # Complementary-tail expression avoids cancellation near one.
    k = np.where(l > 0, ndtr(-l)-ndtr(-u), ndtr(u)-ndtr(l))
    pl, pu = np.exp(-l*l/2)/np.sqrt(2*np.pi), np.exp(-u*u/2)/np.sqrt(2*np.pi)
    return k, (pl-pu)/sigma, (l*pl-u*pu)/(sigma*sigma)


def selected_response(weights, h, h_prime, kernel, kernel_prime,
                      density_prime=None, mass_floor=0.):
    """Quadrature response on fixed labels; weights already include density A.

    density_prime is the derivative of these weighted masses, not a log score.
    h is latent-label statistic. Observed-y statistics need their full kernel.
    """
    w, h, hp, k, kp = map(real, (weights, h, h_prime, kernel, kernel_prime))
    if w.ndim != 1 or any(a.shape != w.shape for a in (h, hp, k, kp)):
        raise ValueError('aligned one-dimensional arrays required')
    if np.any(w < 0) or np.any((k < 0)|(k > 1)):
        raise ValueError('nonnegative masses and probability kernel required')
    wp = np.zeros_like(w) if density_prime is None else real(density_prime)
    if wp.shape != w.shape or not np.isfinite(mass_floor) or mass_floor < 0:
        raise ValueError('aligned mass derivatives and finite nonnegative floor')
    z = float(w@k)
    if z <= mass_floor:
        raise ValueError('selected mass is below the declared positive margin')
    mean = float((w*k)@h/z)
    zp = float(wp@k+w@kp)
    numerator_derivative = float((wp*k+w*kp)@h+(w*k)@hp)
    response = (numerator_derivative-mean*zp)/z
    return dict(mass=z, mean=mean, response=response,
                numerator_only=numerator_derivative/z,
                normalizer_term=-mean*zp/z)


def rank_interval(observed, null, observed_error=0., null_error=0.):
    """Sharp interval-box rank bounds for nonnegative max scores, ties >=.

    A sup-norm bound e on frozen standardized features bounds their max-abs
    score error by e. Common structured errors can make this interval loose.
    """
    obs = real(observed)
    x = real(null)
    eo, en = real(observed_error), real(null_error)
    if obs.ndim or eo.ndim or x.ndim != 1 or x.size == 0:
        raise ValueError('one observed score and nonempty null vector required')
    if np.any(obs < 0) or np.any(x < 0) or eo < 0 or np.any(en < 0):
        raise ValueError('nonnegative scores and error budgets required')
    en = np.broadcast_to(en, x.shape)
    obslo, obshi = max(0., float(obs-eo)), float(obs+eo)
    xlo, xhi = np.maximum(0., x-en), x+en
    klow, khigh = int(np.sum(xlo >= obshi)), int(np.sum(xhi >= obslo))
    b = x.size
    return dict(B=b, k_min=klow, k_max=khigh,
                p_min=(1+klow)/(b+1), p_max=(1+khigh)/(b+1))


def robust_information(response, response_error, covariance_delta=0.):
    """Scaled, nominally whitened nuisance-contrast response only.

    Rank is inf over ALL parameter directions, including a rectangular
    matrix's nullspace. This is a sufficient local criterion, not global ID.
    """
    m=real(response); e=float(real(response_error)); d=float(real(covariance_delta))
    if m.ndim != 2 or min(m.shape)==0 or e < 0 or not 0 <= d < 1:
        raise ValueError('nonempty matrix, nonnegative error, 0<=delta<1 required')
    s=np.linalg.svd(m, compute_uv=False)
    nominal=0. if m.shape[0] < m.shape[1] else float(s[-1])
    lower=max(0., nominal-e)
    return dict(sigma_min=nominal, sigma_min_lower=lower,
                information_min_lower=lower**2/(1+d), robust_full_column_rank=lower>0)


def run(class_result, out):
    import matplotlib
    matplotlib.use('Agg')
    from matplotlib import pyplot as plt
    out.mkdir(parents=True, exist_ok=False)
    src=class_result.read_bytes(); c=json.loads(src)['calibration']
    obs=c['observed_max_abs_z']; null=np.asarray(c['calibration_max_abs_z'])
    baseline=rank_interval(obs,null)
    if len(null)!=c['calibration_rows'] or baseline['p_min']!=c['rank_p']:
        raise ValueError('saved rank identity mismatch')
    budgets=np.linspace(0,2,81)
    intervals=[rank_interval(obs,null,e,e) for e in budgets]
    # First budget where worst-case rank ceases to reject at alpha=.05.
    alpha=.05
    k_break=int(np.floor(alpha*(len(null)+1)))
    kth=np.sort(null)[::-1][k_break-1]
    threshold=max(0., (obs-kth)/2)
    k=int(c['exceedances']); b=len(null)
    cp=[0. if k==0 else float(beta.ppf(.025,k,b-k+1)),
        1. if k==b else float(beta.ppf(.975,k+1,b-k))]
    selection=[]
    for order in (128,256):
        x,w=leggauss(order); w=w/2
        def summary(theta):
            kernel,kp,_=gaussian_bin(x*x+theta,-.1,.4,.1)
            return selected_response(w,x*x,np.zeros_like(x),kernel,kp)
        s=summary(.05); step=1e-5
        fd=(summary(.05+step)['mean']-summary(.05-step)['mean'])/(2*step)
        s.update(order=order, central_difference=fd, derivative_error=abs(fd-s['response']))
        selection.append(s)
    if selection[-1]['derivative_error']>1e-7 or abs(selection[-1]['mean']-selection[-2]['mean'])>1e-10:
        raise AssertionError('selected fold calculation did not converge')
    # Real-coordinate fold t=x²+theta at x=0 is handled in label space.
    result=dict(schema='htt.solver-free-observation-bounds/1',owner='htt',
        claim_tier='CONDITIONAL_DIAGNOSTIC',artifact_mode='solver-free finite calculation',
        transfer_source='none',null_status='CLASS_SPLIT_NOISE_APPROXIMATION_ONLY',
        covariance_status='upstream fixed feature scales; no physical covariance admission',
        source={'path':str(class_result),'sha256':hashlib.sha256(src).hexdigest()},
        class_rank=dict(observed_score=obs,baseline=baseline,budgets=budgets.tolist(),intervals=intervals,
            first_nonreject_equal_score_budget=threshold,alpha=alpha,
            iid_tail_probability_95pct_interval=cp,
            total_variation_budget_until_upper_tail_exceeds_alpha=max(0.,alpha-cp[1])),
        selection_fold=dict(law='X uniform[-1,1], true t=X²+theta, measured Y=t+N(0,.1²), -.1<=Y<=.4',
            theta=.05, statistic='latent X²', rows=selection),
        rank_geometry=[dict(name='underdetermined',**robust_information([[1,0,0],[0,1,0]],0)),
                       dict(name='separated',**robust_information(np.diag([2,1,.5]),.1,.2)),
                       dict(name='uncertainty_unresolved',**robust_information(np.diag([2,1,.5]),.5,.2))],
        allowed_use='conditional rank sensitivity and finite selected-response verification',
        forbidden_uses=['physical CLASS p','empirical selection completeness','global tilt estimate','Bianchi family identification'],
        caveats=['Score budgets are assumed, not measured; frozen training transform required.',
                 'Interval ranks do not repair exchangeability or unmodeled split systematics.',
                 'Clopper-Pearson and TV statements require iid null scores conditional on training and observation.',
                 'Fold calculation is synthetic and dimensionless; no CF4 data fit or ODE.',
                 'No physical error budget, response column, Jacobi remainder or MES bound supplied.'])
    (out/'result.json').write_text(json.dumps(result,indent=2)+'\n')
    fig,ax=plt.subplots(figsize=(7.3,4.4))
    ax.fill_between(budgets,[r['p_min'] for r in intervals],[r['p_max'] for r in intervals],alpha=.25,label='Feasible rank interval')
    ax.plot(budgets,[r['p_max'] for r in intervals],label='Worst-case rank')
    ax.axhline(.05,color='black',ls='--',label='0.05 reference')
    ax.set(xlabel='Assumed error per max score (frozen standardized units)',ylabel='Finite rank',
           title='CLASS: sensitivity within the delivered split-noise approximation')
    ax.legend();ax.grid(alpha=.2);fig.tight_layout()
    fig.savefig(out/'class_rank_budget.svg');fig.savefig(out/'class_rank_budget.png',dpi=160);plt.close(fig)
    x,w=leggauss(256);w=w/2;thetas=np.linspace(-.15,.25,81);rows=[]
    for theta in thetas:
        kk,kp,_=gaussian_bin(x*x+theta,-.1,.4,.1)
        rows.append(selected_response(w,x*x,np.zeros_like(x),kk,kp))
    fig,ax=plt.subplots(figsize=(7.3,4.4))
    for key,label in [('response','Full selected derivative'),('numerator_only','Omit normalization derivative'),('normalizer_term','Normalization contribution')]:
        ax.plot(thetas,[r[key] for r in rows],label=label)
    ax.set(xlabel='Synthetic coordinate shift theta',ylabel='d E[X² | selected] / d theta',title='Finite selection response through a fold: no inverse slope')
    ax.legend();ax.grid(alpha=.2);fig.tight_layout()
    fig.savefig(out/'selection_fold.svg');fig.savefig(out/'selection_fold.png',dpi=160);plt.close(fig)
    print(json.dumps({'class_rank':baseline,'nonreject_budget':threshold,'fold':selection[-1]},indent=2))


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--class-result',type=Path,required=True);p.add_argument('--output-dir',type=Path,required=True)
    a=p.parse_args();run(a.class_result,a.output_dir)
