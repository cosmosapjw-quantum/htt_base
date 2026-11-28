"""Signed finite-response decomposition and physical-amplitude local geometry."""
import numpy as np
from common.morphology_manifold import generators, realify
from common.morphology_orbit import rotation_factory

def signed_split(plus,zero,minus):
    p,z,m=(np.asarray(a,dtype=complex) for a in (plus,zero,minus))
    if p.shape!=z.shape or p.shape!=m.shape or not all(np.isfinite(a).all() for a in (p,z,m)):
        raise ValueError("incompatible signed skies")
    return z,(p-m)/2,(p+m)/2-z

def amplitude_shape(x,derivatives,ell_min=2,ell_max=8,rtol=1e-10,floor=0.):
    x=np.asarray(x,dtype=complex);d=np.asarray(derivatives,dtype=complex)
    gen=generators(x,ell_min,ell_max)
    if d.ndim!=3 or d.shape[1:]!=x.shape or not len(d) or not np.isfinite(d).all():
        raise ValueError("invalid derivative shape")
    if not np.isfinite(rtol) or not 0<rtol<1 or not np.isfinite(floor) or floor<0:
        raise ValueError("invalid tolerance/floor")
    y=realify(x);amp=np.linalg.norm(y)
    if not np.isfinite(amp) or amp<=floor:raise ValueError("sky at or below amplitude floor")
    a=y/amp
    j=np.column_stack([realify(v) for v in d])
    r=np.column_stack([realify(v) for v in gen])/amp
    r=r-a[:,None]*(a@r)[None,:]
    w,s,_=np.linalg.svd(r,full_matrices=False)
    rank=int(np.count_nonzero(s>rtol*max(1.,s[0])))
    q=w[:,:rank]
    # Project rotations at fixed amplitude, then remove the independent radial column.
    ro=j-q@(q.T@j)
    grad=a@j/amp
    shape=ro/amp-a[:,None]*grad[None,:]
    g_abs=ro.T@ro;g_shape=shape.T@shape
    if not np.allclose(g_abs,amp**2*(g_shape+np.outer(grad,grad)),rtol=2e-11,atol=2e-14*max(1e-300,np.linalg.norm(g_abs))):
        raise ArithmeticError("amplitude-shape identity")
    return {"amplitude":float(amp),"unit":a,"rotation_basis":q,"rotation_rank":rank,
            "rotation_singular_values":s,"grad_log_amplitude":grad,"raw":j,
            "rotation_projected":ro,"shape_projected":shape,"absolute_gram":g_abs,"shape_gram":g_shape,
            "absolute_singular_values":np.linalg.svd(ro,compute_uv=False),
            "shape_singular_values":np.linalg.svd(shape,compute_uv=False)}

def scaled_diagnostic(reference,others,scales):
    """Compare finite arrays in fixed units. Observed differences are not rigorous errors."""
    a=np.asarray(reference,dtype=float);d=np.asarray(scales,dtype=float)
    if a.ndim!=2 or d.shape!=(a.shape[1],) or np.any(d<=0) or not np.isfinite(a).all() or not np.isfinite(d).all():
        raise ValueError("invalid coordinate scales")
    b=a*d;sig=np.linalg.svd(b,compute_uv=False)
    errors={}
    for n,value in others.items():
        v=np.asarray(value,dtype=float)
        if v.shape!=a.shape or not np.isfinite(v).all():raise ValueError("invalid comparison")
        e=a-v;columns=np.linalg.norm(e,axis=0);scaled=e*d
        errors[n]={"column_norms":columns,"scaled_column_norms":columns*d,
            "unscaled_operator":float(np.linalg.norm(e,2)),"scaled_operator":float(np.linalg.norm(scaled,2)),
            "scaled_frobenius":float(np.linalg.norm(scaled))}
    observed=max((x["scaled_frobenius"] for x in errors.values()),default=0.)
    return {"scales":d,"singular_values":sig,"errors":errors,"empirical_frobenius_scale":observed,
            "count_above_observed_scale":int(np.count_nonzero(sig>observed))}

def spin2_support(sky,ell_min=2,ell_max=8):
    """Rotate original e1 symmetry axis to a polar axis and report |m|=2 support."""
    a=rotation_factory(ell_min,ell_max)(sky,(0.,-np.pi/2,0.))
    m=np.concatenate([np.arange(-l,l+1) for l in range(ell_min,ell_max+1)])
    n=np.linalg.norm(a);off=np.linalg.norm(a[abs(m)!=2]);on=np.linalg.norm(a[abs(m)==2])
    return {"norm":float(n),"on_m2":float(on),"off_m2":float(off),
            "relative_off_m2":float(off/n) if n else None}
