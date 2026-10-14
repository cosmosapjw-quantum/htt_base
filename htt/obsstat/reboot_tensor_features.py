"""Temperature STF descriptors with one orthonormal real-harmonic convention.

These processed-map features do not measure matter shear or vorticity.
"""
from __future__ import annotations
import numpy as np
from .r7_cmb_product_response import real_to_stored
from .planck_lowell_irrep_projection import real_harmonic_l2_to_stf, real_harmonic_l3_to_stf

FEATURE_NAMES = ('C2','C3','C4','C5','quadrupole_shape','octupole_concentration',
                 'QO_contraction','chirality')


def tensors_from_real(row):
    if np.iscomplexobj(row):raise ValueError('real coefficients required')
    a=np.asarray(row,dtype=float)
    if a.shape!=(32,) or not np.isfinite(a).all():
        raise ValueError('finite real ell2..5 vector required')
    return (real_harmonic_l2_to_stf(real_to_stored(a[:5],2)),
            real_harmonic_l3_to_stf(real_to_stored(a[5:12],3)))


def tensor_shape_features(q,o):
    if np.iscomplexobj(q) or np.iscomplexobj(o):raise ValueError('real tensors required')
    q=np.asarray(q,dtype=float);o=np.asarray(o,dtype=float)
    if q.shape!=(3,3) or o.shape!=(3,3,3) or not np.isfinite(q).all() or not np.isfinite(o).all():
        raise ValueError('finite Q and O tensors required')
    q2=float(np.sum(q*q));o2=float(np.sum(o*o))
    if not np.isfinite([q2,o2]).all():raise ValueError('tensor norm overflow')
    if q2<=0 or o2<=0:raise ValueError('shape undefined for zero tensor')
    # All shape coordinates are scale invariant; normalize before contractions.
    q=q/np.sqrt(q2);o=o/np.sqrt(o2);q2=o2=1.
    a=np.einsum('iab,jab->ij',o,o)
    shape=float(np.trace(q@q@q)/q2**1.5)
    concentration=float(np.linalg.eigvalsh(a)[-1]/o2)
    alignment=float(np.trace((q@q)@a)/(q2*o2))
    v=np.einsum('ijk,jk->i',o,q);qv=q@v;av=a@v
    denom=np.linalg.norm(v)*np.linalg.norm(qv)*np.linalg.norm(av)
    if denom==0:raise ValueError('chirality undefined on degenerate carrier')
    chirality=float(np.dot(v,np.cross(qv,av))/denom)
    result=np.array([shape,concentration,alignment,chirality])
    if not np.isfinite(result).all():raise ValueError('nonfinite shape descriptors')
    return result


def feature_vector(row):
    if np.iscomplexobj(row):raise ValueError('real coefficients required')
    a=np.asarray(row,dtype=float);q,o=tensors_from_real(a)
    powers=[float(a[l*l-4:(l+1)*(l+1)-4]@a[l*l-4:(l+1)*(l+1)-4])/(2*l+1)
            for l in range(2,6)]
    result=np.r_[powers,tensor_shape_features(q,o)]
    if not np.isfinite(result).all():raise ValueError('power overflow')
    return result


def feature_matrix(rows):
    if np.iscomplexobj(rows):raise ValueError('real coefficients required')
    x=np.asarray(rows,dtype=float)
    if x.ndim!=2 or x.shape[1]!=32:raise ValueError('matrix of real ell2..5 vectors required')
    return np.array([feature_vector(row) for row in x])
