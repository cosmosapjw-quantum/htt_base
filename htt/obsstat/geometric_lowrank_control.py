"""Fixed-geometry low-rank nuisance adjustment with training-only selection.

Source: the left singular directions of the actual masked high-to-low
operator K = P_low Y_high. Fits a small linear control from the *same-sky*
fit difference H=Y12-Y5 in this fixed output basis.

This is observation-level conditional analysis, not Bianchi physics,
the true unboosted sky or a validated Planck physical null.
"""
from __future__ import annotations

import numpy as np

from obsstat.paired_highmode_control import (
    FittedLeakageControl,fit_family,transform_rows,_fit_core,
    rank_upper_tail)


class LowrankControlError(ValueError):
    pass


def _real_array(value, shape=None, rank=None, name='array'):
    if np.iscomplexobj(value):
        raise LowrankControlError(f'{name} must use real harmonic coefficients')
    x=np.asarray(value,dtype=float)
    if not np.isfinite(x).all() or (shape is not None and x.shape !=shape) or (rank is not None and x.ndim!=rank):
        raise LowrankControlError(f'unsupported {name} shape/finite values')
    return x


def geometry_directions(k, *, rank=3):
    """Return fixed left singular output directions, and all singular values.

    Only the row/output subspace depends on sky mask and harmonic geometry.
    A high-harmonic basis rotation K->KV leaves K K^T and this left subspace
    unchanged, up to internal rotations/signs where singular values coincide.
    """
    m=_real_array(k,rank=2,name='K')
    q=int(rank)
    if m.ndim!=2 or m.shape[0]<q or m.shape[1]<q or q<1:
        raise LowrankControlError('positive feasible left singular rank required')
    u,s,_=np.linalg.svd(m,full_matrices=False)
    if s[0]<=0 or s[q-1]/s[0]<1e-12:
        raise LowrankControlError('finite geometry rank not supported')
    return u[:,:q].copy(),s.copy()


def fit_geometric_control(y,h,geometry_u,*,rank,ridge_multiplier,cov_shrink=.2):
    yy=_real_array(y,rank=2,name='y')
    hh=_real_array(h,shape=yy.shape,name='h')
    u=_real_array(geometry_u,rank=2,name='geometry_u')
    k=int(rank)
    rho=float(ridge_multiplier)
    if (yy.shape[0]<6 or u.shape[0]!=yy.shape[1] or
        k<1 or k>u.shape[1] or
        not np.allclose(u.T@u,np.eye(u.shape[1]),atol=1e-10,rtol=0) or
        not np.isfinite(rho) or rho<=0 or
        not 0<cov_shrink<=1):
        raise LowrankControlError('invalid rank, geometry, or ridge model')
    uz=u[:,:k]
    my=yy.mean(axis=0)
    mh=hh.mean(axis=0)
    z=(hh-mh)@uz
    ycen=yy-my
    zz=z.T@z
    ridge=rho*float(np.trace(zz))/k
    if not np.isfinite(ridge) or ridge<=0:
        raise LowrankControlError('zero positive training control scatter')
    b=np.linalg.solve(zz+ridge*np.eye(k),z.T@ycen)
    full=uz@b
    residual=ycen-(hh-mh)@full
    cov=_fit_core(residual,alpha=float(cov_shrink))
    return FittedLeakageControl(my,mh,full,cov,rho,ridge,float(cov_shrink))


def cv_select_control(train_y,train_h,geometry_u,
                     *,rank_choices=(1,2,3),ridge_choices=(.25,1,4),
                     cov_shrink=.2,folds=5,minimum_gain_fraction=.005):
    """Train-only fixed 5-fold selection; heldout 240 and observed sky invisible."""
    yy=_real_array(train_y,rank=2,name='train Y')
    hh=_real_array(train_h,shape=yy.shape,name='train H')
    u=_real_array(geometry_u,rank=2,name='U')
    if (len(yy)<2*folds or folds<2 or
        len(rank_choices)==0 or len(ridge_choices)==0 or
        len(set(rank_choices))!=len(rank_choices) or
        len(set(ridge_choices))!=len(ridge_choices) or
        any(q<1 or q>u.shape[1] for q in rank_choices) or
        any(not np.isfinite(r) or r<=0 for r in ridge_choices) or
        not 0<=minimum_gain_fraction<1):
        raise LowrankControlError('invalid registered CV candidates')
    idx=np.arange(len(yy))
    candidates=[]
    baseline=0.
    for fold in range(folds):
        test=(idx%folds)==fold
        base=fit_family(yy[~test],cov_shrink=cov_shrink)
        base_res=transform_rows(yy[test],hh[test],base)
        baseline+=float(np.sum(base_res**2))
    if baseline<=0:
        raise LowrankControlError('baseline training CV variance absent')
    for k in rank_choices:
        for rho in ridge_choices:
            err=0.
            for fold in range(folds):
                test=(idx%folds)==fold
                model=fit_geometric_control(yy[~test],hh[~test],u,
                        rank=int(k),ridge_multiplier=float(rho),cov_shrink=cov_shrink)
                residual=transform_rows(yy[test],hh[test],model)
                err+=float(np.sum(residual**2))
            candidates.append({'rank':int(k),'ridge_multiplier':float(rho),
                               'cv_rss':err,'cv_mse_ratio':err/baseline,
                               'cv_relative_mse':err/baseline-1.})
    best=min(candidates,key=lambda x:(x['cv_rss'],x['rank'],x['ridge_multiplier']))
    chosen=best if best['cv_mse_ratio']<(1-minimum_gain_fraction) else None
    if chosen is None:
        model=fit_family(yy,cov_shrink=cov_shrink)
        selection='baseline'
        cv_ratio=1.
    else:
        model=fit_geometric_control(yy,hh,u,rank=chosen['rank'],
                  ridge_multiplier=chosen['ridge_multiplier'],cov_shrink=cov_shrink)
        selection=f"rank{chosen['rank']}_rho{chosen['ridge_multiplier']:g}"
        cv_ratio=chosen['cv_mse_ratio']
    train_res=transform_rows(yy,hh,model)
    train_score=model.scaled_scores(train_res)
    score_mean=float(np.mean(train_score))
    score_sd=float(np.std(train_score,ddof=1))
    if not np.isfinite(score_sd) or score_sd<=1e-12:
        raise LowrankControlError('training calibration score scale invalid')
    return {
      'model':model,'selected':selection,'cv_ratio':float(cv_ratio),
      'cv_baseline_rss':baseline,'candidates':candidates,
      'selection_source':f'training_only_{len(yy)}',
      'cv_folds':folds,'train_count':len(yy),
      'train_score_center':score_mean,'train_score_scale':score_sd,
      'fixed_candidate_policy':f'rank{tuple(rank_choices)},rho{tuple(ridge_choices)},CV gain>{minimum_gain_fraction*100}%'
    }


def score_selected_mask(selection,observed_y,observed_h,null_y,null_h):
    model=selection['model']
    d=len(model.mean_y)
    oy=_real_array(observed_y,shape=(d,),name='observed Y')
    oh=_real_array(observed_h,shape=(d,),name='observed H')
    ny=_real_array(null_y,rank=2,name='calibration Y')
    nh=_real_array(null_h,shape=ny.shape,name='calibration H')
    if ny.shape[1]!=d:raise LowrankControlError('null dimension mismatch')
    center=selection['train_score_center']
    scale=selection['train_score_scale']
    so=(model.scaled_scores(transform_rows(oy[None],oh[None],model))[0]-center)/scale
    sn=(model.scaled_scores(transform_rows(ny,nh,model))-center)/scale
    return {'observed':np.asarray(so),'null':np.asarray(sn),
            'observed_raw_score':float(model.scaled_scores(transform_rows(oy[None],oh[None],model))[0]),
            'null_raw_scores':model.scaled_scores(transform_rows(ny,nh,model)),
            'null_residuals':transform_rows(ny,nh,model)}


def rank_two_mask_joint(mask_scores):
    """One null row = the entire sky and all corresponding mask variants."""
    if not 1<=len(mask_scores)<=2:
        raise LowrankControlError('registered 1-2 complete mask rows only')
    b=len(mask_scores[0]['null'])
    if any(len(q['null'])!=b or b<1 for q in mask_scores):
        raise LowrankControlError('same aligned paired null-row count required')
    observed=max(float(q['observed']) for q in mask_scores)
    null=np.max(np.column_stack([q['null'] for q in mask_scores]),axis=1)
    result=rank_upper_tail(observed,null)
    return {**result,'observed_joint_max_score':observed,
            'null_joint_max_scores':null}
