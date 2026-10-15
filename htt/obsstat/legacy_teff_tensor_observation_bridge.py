"""Exact legacy Teff direction-moment, mapped to modern Planck l=2 STF carriers.

A dipole d and a symmetric trace-free quadrupole S define
    Theta(n) = 1 + d_i n_i + n_i S_ij n_j.
This is a finite, full-sky *directional temperature ansatz* and not a
thermal-Boltzmann or observed CMB likelihood. S represents a dimensionless
TEMPERATURE quadrupole, not physical 1+3 congruence shear sigma_ab.

This module preserves the original TeffMomentMap angular field and its
F_4=<Theta^4>, using exact O(3) invariant polynomials. F_4 is NOT legacy
MIO certified filling fraction F, and is NOT a Bayesian posterior/evidence.
"""
from __future__ import annotations

import math
from functools import lru_cache
import numpy as np

from .planck_lowell_irrep_projection import real_harmonic_l2_to_stf
from .r7_cmb_product_response import real_to_stored,real_design
from .mes_eps_measurement_bridge import T0_MICROK


class TeffTensorBridgeError(ValueError):
    pass


def _array_inputs(dipole,quadrupole):
    d=np.asarray(dipole)
    s=np.asarray(quadrupole)
    if (np.iscomplexobj(d) or np.iscomplexobj(s)
        or d.shape[-1:]!=(3,) or s.shape[-2:]!=(3,3)
        or s.shape[:-2]!=d.shape[:-1]
        or not np.isfinite(d).all() or not np.isfinite(s).all()):
        raise TeffTensorBridgeError("real finite dimensionless d_i and STF S_ij, same batch")
    d=np.asarray(d,float)
    s=np.asarray(s,float)
    scale=np.maximum(np.linalg.norm(s,axis=(-1,-2)),1e-16)
    asym=np.max(abs(s-np.swapaxes(s,-1,-2)),axis=(-1,-2))
    tr=np.trace(s,axis1=-2,axis2=-1)
    if np.any(asym>2e-12*scale) or np.any(abs(tr)>2e-12*scale):
        raise TeffTensorBridgeError("quadrupole S must be symmetric trace-free")
    return d,s


def legacy_f4_exact_increment(dipole,quadrupole,*,require_positive=False):
    """Compute F4-1 without subtractive cancellation, batch/vectorized.

    Invariants D=|d|², J2=tr S², J3=tr S³,
               K1=d.S.d, K2=d.S².d.

    <t²>=D/3+2J2/15
    <t³>=2K1/5+8J3/105
    <t⁴>=D²/5+4DJ2/35+16K2/35+4J2²/105
    for t=Theta-1 and <t>=0.  F4-1=6<t²>+4<t³>+<t⁴>.
    """
    d,s=_array_inputs(dipole,quadrupole)
    if require_positive:
        lam=np.linalg.eigvalsh(s)
        safe=np.linalg.norm(d,axis=-1)+np.max(abs(lam),axis=-1)
        if np.any(safe>=1):
            raise TeffTensorBridgeError("sufficient positivity certificate |d|+||S||op<1 failed")
    d2=np.einsum("...i,...i->...",d,d)
    S2=s@s
    j2=np.einsum("...ij,...ji->...",s,s)
    j3=np.einsum("...ij,...ji->...",S2,s)
    k1=np.einsum("...i,...ij,...j->...",d,s,d)
    k2=np.einsum("...i,...ij,...j->...",d,S2,d)
    m2=d2/3 + 2*j2/15
    m3=2*k1/5 + 8*j3/105
    m4=(d2*d2)/5 + (4*d2*j2)/35 + (16*k2)/35 + 4*j2*j2/105
    inc=6*m2+4*m3+m4
    return {"delta_F4":inc,"F4":1+inc,
            "mean_t2":m2,"mean_t3":m3,"mean_t4":m4,
            "D":d2,"J2":j2,"J3":j3,"K1":k1,"K2":k2,
            "label":"EXACT_FULL_SKY_FINITE_DIRECTIONAL_TEMP_ANSATZ_NO_OBSERVATION_LIKELIHOOD"}


def bolometric_proxy_shift_microK(delta_F4,*,T0_uK=T0_MICROK):
    """T0 (F4^(1/4)-1) computed with log1p/expm1 for tiny CMB anisotropies."""
    a=np.asarray(delta_F4)
    if (np.iscomplexobj(a) or not np.isfinite(a).all()
        or np.any(a<=-1) or not math.isfinite(T0_uK) or T0_uK<=0):
        raise TeffTensorBridgeError("positive effective-temperature moment required")
    return T0_uK*np.expm1(.25*np.log1p(np.asarray(a,float)))


@lru_cache(maxsize=1)
def _real2stf_microK_basis():
    """Orthogonal REAL harmonics including sqrt2 Re/Im and imaginary sign."""
    vec=[]
    for k in range(5):
        e=np.eye(5)[k]
        vec.append(real_harmonic_l2_to_stf(real_to_stored(e,2)))
    return np.stack(vec)


def masked_planck_quadrupole_to_temperature_stf(real_l2_microK,
                                                 *,T0_uK=T0_MICROK):
    a=np.asarray(real_l2_microK)
    if (np.iscomplexobj(a) or a.shape[-1:]!=(5,)
        or not np.isfinite(a).all() or not math.isfinite(T0_uK) or T0_uK<=0):
        raise TeffTensorBridgeError("finite real harmonic l2 5D in thermodynamic microK")
    s=np.einsum("...j,jab->...ab",np.asarray(a,float),
                _real2stf_microK_basis(),optimize=True)/T0_uK
    return s


def real_l1_microK_to_temperature_dipole(real_l1_microK,
                                           *,T0_uK=T0_MICROK):
    """Real harmonic (a10, sqrt2*Re a11, sqrt2*Im a11).

    With scipy spherical Y11=-sqrt(3/8pi) sin(theta)e^(i phi),
    d=sqrt(3/(4pi))*(-a11_cos,-a11_sin,a10)/T0.
    """
    a=np.asarray(real_l1_microK)
    if (np.iscomplexobj(a) or a.shape[-1:]!=(3,)
        or not np.isfinite(a).all() or not math.isfinite(T0_uK) or T0_uK<=0):
        raise TeffTensorBridgeError("separately source-certified 3D real l1 coefficients")
    return math.sqrt(3/(4*math.pi))*np.stack((-a[...,1],-a[...,2],a[...,0]),axis=-1)/T0_uK


def quadrupole_morphology_stf(s):
    """Rotation-invariant normalized tr(S^3), positive for oblate/prolate sign."""
    tensor=np.asarray(s)
    if tensor.shape[-2:]!=(3,3):
        raise TeffTensorBridgeError("one/batch quadrupole tensor required")
    D=np.zeros(tensor.shape[:-2]+(3,))
    moments=legacy_f4_exact_increment(D,tensor)
    j2=np.asarray(moments["J2"])
    j3=np.asarray(moments["J3"])
    out=np.divide(np.sqrt(6)*j3,np.power(j2,1.5),
                  out=np.full_like(j2,np.nan,float),where=j2>0)
    return out


def old_axis_A_W_Q_V_to_tensors(A,W,Q,V):
    """Original 2026 legacy TeffMomentMap.theta_field exact finite ansatz."""
    nums=np.asarray([A,W,Q,V],dtype=float)
    if nums.shape!=(4,) or not np.isfinite(nums).all():
        raise TeffTensorBridgeError("finite legacy axis coefficients A,W,Q,V required")
    d=np.array([W,0.,A])
    s=np.array([[-Q/2,0.,V/2],[0.,-Q/2,0.],[V/2,0.,Q]])
    return d,s


def real_harmonic_quadrupole_source_consistency(real_coeff,source_T0=T0_MICROK,
                                                *,n_test=384):
    """Independent spherical-harmonic versus STF field trace."""
    a=np.asarray(real_coeff,float)
    if a.shape!=(5,) or n_test<30:
        raise TeffTensorBridgeError("five real source harmonic modes required")
    rng=np.random.default_rng(421)
    dirs=rng.normal(size=(n_test,3))
    dirs/=np.linalg.norm(dirs,axis=1)[:,None]
    q=masked_planck_quadrupole_to_temperature_stf(a,T0_uK=source_T0)
    left=np.einsum("ni,ij,nj->n",dirs,q,dirs)
    right=real_design(dirs,ell_max=2)[:,4:9]@a/source_T0
    return float(np.max(abs(left-right)))
