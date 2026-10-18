"""CF4 directional q information loss from declared ordered nuisance families.

Computes diagnostics on an already fixed observational design, not source
acceleration, global tilt, physical geodesicity or an accepted q likelihood.
No change to the registered PR179 q-withheld gate is allowed here.
"""
from __future__ import annotations
from collections.abc import Mapping
import numpy as np
from scipy.linalg import eigh


class NuisanceAblationError(ValueError):
    pass


def compare_nuisance_stages(q,weights,stages: Mapping[str,object]):
    """Compute generalized q information ratio under several explicit nuisances.

    Let W=diag(weights), G0=Q.T W Q, G=Qperp.T W Qperp.
    eig(G,G0) is invariant under Q -> Q A, A invertible. The residual
    Qperp is computed using a weighted orthogonal nuisance projector,
    without assuming a physical covariance law.
    """
    if np.iscomplexobj(q) or np.iscomplexobj(weights):
        raise NuisanceAblationError('require real input')
    q=np.asarray(q,dtype=float)
    w=np.asarray(weights,dtype=float)
    if (q.ndim!=2 or q.shape[1]!=3 or q.shape[0]<6 or
        w.shape!=(q.shape[0],) or not np.isfinite(q).all() or
        not np.isfinite(w).all() or np.any(w<=0) or not stages):
        raise NuisanceAblationError('finite (N,3) q, strictly positive W, nonempty stages required')
    raw=q.T@(w[:,None]*q)
    if np.linalg.eigvalsh(raw)[0]<=0:
        raise NuisanceAblationError('raw q Gram not positive definite')
    sw=np.sqrt(w)
    result={}
    for name,design in stages.items():
        if design is None:
            n=np.empty((len(q),0))
        else:
            if np.iscomplexobj(design):
                raise NuisanceAblationError('complex nuisance invalid')
            n=np.asarray(design,dtype=float)
        if (n.ndim!=2 or n.shape[0]!=len(q) or not np.isfinite(n).all()):
            raise NuisanceAblationError('nuisance rows / finite values invalid')
        if n.shape[1]>0:
            nw=n*sw[:,None]
            operator=np.linalg.pinv(nw,rcond=100*np.finfo(float).eps)*sw[None,:]
            qres=q-n@(operator@q)
            s=np.linalg.svd(nw,compute_uv=False)
            nu_rank=int(np.count_nonzero(s>s[0]*1e-10))
        else:
            qres=q.copy()
            nu_rank=0
        gram=qres.T@(w[:,None]*qres)
        g=eigh((gram+gram.T)*.5,raw,eigvals_only=True)
        if g.min()<-1e-8 or g.max()>1+1e-8:
            raise NuisanceAblationError(f'{name}: residual information outside Loewner interval')
        g=np.clip(g,0,1)
        if np.linalg.norm(qres)<0 or np.linalg.norm(qres)>1e100:
            raise NuisanceAblationError('nuisance residual invalid')
        result[name]={
            'nuisance_columns':int(n.shape[1]),
            'nuisance_numerical_rank':nu_rank,
            'relative_information_eigenvalues':g.tolist(),
            'weakest_relative_information':float(g[0]),
            'mean_relative_information':float(np.mean(g)),
            'trace_relative_information':float(np.sum(g)),
            'retained_weighted_gram_trace':float(np.trace(gram)),
            'raw_weighted_gram_trace':float(np.trace(raw)),
            'raw_min_gram_eigenvalue':float(np.linalg.eigvalsh(raw)[0]),
            'retained_min_gram_eigenvalue':float(np.linalg.eigvalsh(gram)[0]),
            'registered_scalar_minimum_information_ratio':
                float(np.linalg.eigvalsh(gram)[0]/np.linalg.eigvalsh(raw)[0])
        }
    return {'stages':result,
      'q_dimensions':3,'n':int(len(q)),
      'source_claim_tier':'FINITE_DECLARED_CATALOGUE_DESIGN_ONLY'}


def exact_radial_alias_bound(z, directions, weights, *, pivot_z=None):
    """Constructive z*n alias by the H=n and cubic=z^2*n nuisance responses.

    The exact identity
        z*n = (z0/2)*n + (1/(2 z0))*(z^2*n)
              - ((z-z0)^2/(2 z0))*n
    gives a weighted RMS bound for the best H+cubic linear projection.
    In a narrow shell, the response residual is O(Delta z^2 / z0),
    relative squared information of the un-normalized q response is
    O((Delta z/z0)^4). No sky prior or measured physical deceleration.
    """
    if any(np.iscomplexobj(x) for x in (z,directions,weights)):
        raise NuisanceAblationError('real finite redshift, sky and weights required')
    zz=np.asarray(z,dtype=float)
    n=np.asarray(directions,dtype=float)
    w=np.asarray(weights,dtype=float)
    if (zz.ndim!=1 or n.shape!=(len(zz),3) or w.shape!=(len(zz),) or len(zz)<6
        or not np.isfinite(zz).all() or not np.isfinite(n).all() or not np.isfinite(w).all()
        or np.any(zz<=0) or np.any(w<=0)
        or not np.allclose(np.linalg.norm(n,axis=1),1.,rtol=0,atol=5e-13)):
        raise NuisanceAblationError('invalid positive z, unit sky, weights')
    z0=float(np.average(zz,weights=w)) if pivot_z is None else float(pivot_z)
    if not np.isfinite(z0) or z0<=0:
        raise NuisanceAblationError('strict positive radial pivot needed')
    q=zz[:,None]*n
    h=n
    cubic=zz[:,None]**2*n
    candidate=z0/2*h + 1/(2*z0)*cubic
    discrepancy=q-candidate
    predicted=-(zz-z0)[:,None]**2/(2*z0)*n
    ident=float(np.max(np.abs(discrepancy-predicted)))
    x=np.column_stack((h,cubic))
    sq=np.sqrt(w)
    operator=np.linalg.pinv(x*sq[:,None],
                           rcond=100*np.finfo(float).eps)*sq[None,:]
    residual=q-x@(operator@q)
    raw_energy=float(np.sum(w[:,None]*q*q))
    projected_energy=float(np.sum(w[:,None]*residual*residual))
    bound_energy=float(np.sum(w[:,None]*predicted*predicted))
    if projected_energy>bound_energy+1e-8*max(1,bound_energy):
        raise NuisanceAblationError('constructive projection envelope violated')
    return {
        'pivot_z':z0,
        'exact_identity_max_abs_residual':ident,
        'actual_best_H_and_cubic_weighted_squared_ratio':projected_energy/raw_energy,
        'constructive_upper_squared_ratio':bound_energy/raw_energy,
        'upper_relative_RMS_amplitude':float(np.sqrt(bound_energy/raw_energy)),
        'delta_z_squared_weighted_mean':float(np.average((zz-z0)**2,weights=w)),
        'dimensionless_mean_relative_width':float(np.sqrt(np.average((zz-z0)**2,weights=w))/z0),
        'bound_interpretation':'Unnormalized z*n response within span[n,z^2*n]; fourth-moment bound holds for any positive W diagonal, no method nuisance needed.'
    }
