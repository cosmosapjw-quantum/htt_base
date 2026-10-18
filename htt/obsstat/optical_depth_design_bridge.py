"""Source-bound angular/depth capability of the local optical first-jet inverse.

This module does NOT fit physical source acceleration, theta, sigma, omega or
boost. It assesses the 13 *unconstrained* optical coefficients under a
specified finite source-direction-distance design, with optional method
zero-point nuisance. No CF4 likelihood/selection law is manufactured.
"""
from __future__ import annotations

import numpy as np


class OpticalDepthDesignError(ValueError):
    pass


def angular_optical_design(directions, distance, *, distance_reference):
    """X=[1,n, (r/rref)(1,n,STF2(n))], 13 columns in a frozen Cartesian chart.

    The physical velocity mass shell reduces this 13-coordinate free design
    to a 12-dimensional tangent; it is NOT imposed in this linear capability
    check. Source frame and absolute intercept are NOT available from CF4.
    """
    n=np.asarray(directions,dtype=float)
    r=np.asarray(distance,dtype=float)
    ref=float(distance_reference)
    if (n.ndim!=2 or n.shape[1]!=3 or r.shape!=(len(n),)
        or len(n)<13 or not np.isfinite(n).all() or not np.isfinite(r).all()
        or np.any(r<=0) or not np.isfinite(ref) or ref<=0
        or not np.allclose(np.linalg.norm(n,axis=1),1,atol=5e-13,rtol=0)):
        raise OpticalDepthDesignError("finite unit directions and positive depth required")
    x,y,z=n.T
    e4=np.column_stack([np.ones(len(n)),n])
    stf=np.stack([(x*x-y*y)/np.sqrt(2),
      (2*z*z-x*x-y*y)/np.sqrt(6),
      np.sqrt(2)*x*y, np.sqrt(2)*x*z, np.sqrt(2)*y*z],axis=1)
    e9=np.concatenate([e4,stf],axis=1)
    return e4,(r/ref)[:,None]*e9


def optical_depth_capability(directions, distance, *, distance_reference,
                             row_weights=None, method_groups=None):
    """Exact finite-row rank, canonical angles and method-offset stress.

    Weight vector is a declared *design weight*; it does not become a
    measurement likelihood without a matching sampling covariance.
    """
    e4,r9=angular_optical_design(directions,distance,
                                 distance_reference=distance_reference)
    n=len(e4)
    w=np.ones(n) if row_weights is None else np.asarray(row_weights,dtype=float)
    if (w.shape!=(n,) or not np.isfinite(w).all() or np.any(w<=0)):
        raise OpticalDepthDesignError('strictly positive finite row weights required')
    a=w[:,None]*e4
    b=w[:,None]*r9
    x=np.column_stack([a,b])
    def space(y):
        u,s,_=np.linalg.svd(y,full_matrices=False)
        return u[:,s>max(s)*1e-10],s
    ua,sa=space(a);ub,sb=space(b)
    cc=np.linalg.svd(ua.T@ub,compute_uv=False)
    design_s=np.linalg.svd(x,compute_uv=False)
    rank=int(np.sum(design_s>design_s[0]*1e-10))
    answer={
      'n':n,'design_rank':rank,
      'intercept_rank':int(len(sa[sa>sa[0]*1e-10])),
      'slope_rank':int(len(sb[sb>sb[0]*1e-10])),
      'principal_cosines':cc.tolist(),
      'weakest_principal_sine':float(np.sqrt(max(0,1-cc[0]**2))),
      'scaled_design_weakest_ratio':float(design_s[-1]/design_s[0]),
    }
    if method_groups is not None:
        g=np.asarray(method_groups)
        if g.shape!=(n,):
            raise OpticalDepthDesignError('method labels must bind all rows')
        labels=sorted(str(k) for k in np.unique(g))
        f=w[:,None]*np.column_stack([g==label for label in labels]).astype(float)
        uf,_=space(f)
        px=x-uf@(uf.T@x)
        ps=np.linalg.svd(px,compute_uv=False)
        dip=a[:,1:4]
        answer.update({
          'method_labels':labels,
          'method_nuisance_columns':len(labels),
          'method_projected_rank':int(np.sum(ps>ps[0]*1e-10)),
          'method_dipole_squared_design_overlap':
               float(np.linalg.norm(uf.T@dip)**2/np.linalg.norm(dip)**2),
          'method_projection_max_constant_residual':
               float(np.max(np.abs((a[:,0]-uf@(uf.T@a[:,0]))))),
        })
    return answer
