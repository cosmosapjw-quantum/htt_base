"""Exact finite l=2+3 full-sky blackbody-temperature F4 from real harmonics.

The original 2026 legacy TeffMomentMap handled an l<=2 (dipole and
quadrupole) polynomial angular ansatz. This extends *that finite
ansatz* to all 5 quadrupole and 7 octupole real coefficients, preserving
their relative morphology, and calculates exact spherical moments
without subtracting F4-1 from two machine-sized numbers.

Gauss-Legendre × uniform-phi quadrature is exact (up to roundoff) for
the 4th power of a finite Cartesian polynomial of degree <=3:
integrand polynomial degree <=12, whose azimuthal Fourier harmonics
have |m|<=12. N_mu>=8 integrates degree<=15, N_phi>=25 resolves
azimuth modes. We choose N_mu=16 and N_phi=32 and independently
verify with 24×48. This does not estimate omitted l>=4 sky modes
or an intrinsic CMB dipole, and is not a full Planck likelihood.
"""
from __future__ import annotations
from functools import lru_cache
import numpy as np

from .r7_cmb_product_response import real_design
from .legacy_teff_tensor_observation_bridge import (
    T0_MICROK,legacy_f4_exact_increment,
    masked_planck_quadrupole_to_temperature_stf,
    bolometric_proxy_shift_microK,
)


class TeffOctupoleError(ValueError):
    pass


@lru_cache(maxsize=4)
def _quadrature_grid(n_mu:int,n_phi:int):
    if (not isinstance(n_mu,int) or not isinstance(n_phi,int)
        or n_mu<8 or n_phi<25):
        raise TeffOctupoleError("exact quadrupole+octupole quartic quadrature needs >=8,>=25")
    mu,w=np.polynomial.legendre.leggauss(n_mu)
    phis=np.arange(n_phi)*2*np.pi/n_phi
    x=np.sqrt(1-mu[:,None]**2)*np.cos(phis[None,:])
    y=np.sqrt(1-mu[:,None]**2)*np.sin(phis[None,:])
    z=np.broadcast_to(mu[:,None],(n_mu,n_phi))
    dirs=np.column_stack((x.ravel(),y.ravel(),z.ravel()))
    source=real_design(dirs,ell_max=3)[:,4:16]
    weights=np.repeat(w/(2*n_phi),n_phi)
    weights.setflags(write=False);source.setflags(write=False)
    return source,weights


def moment_delta_l23(real_coeff_l2_l3,*,T0_uK=T0_MICROK,n_mu=16,n_phi=32,
                     keep_components=True):
    """Batch (n,12) real [l2 five,l3 seven] in thermodynamic microK."""
    a=np.asarray(real_coeff_l2_l3)
    if (np.iscomplexobj(a) or a.ndim!=2 or a.shape[1]!=12
        or not np.isfinite(a).all() or not np.isfinite(T0_uK) or T0_uK<=0):
        raise TeffOctupoleError("finite source real l2+l3 12D with positive T0 in microK required")
    basis,w=_quadrature_grid(n_mu,n_phi)
    fields=np.asarray(a,float)@basis.T/T0_uK
    q=fields
    var=np.einsum("ni,ni,i->n",q,q,w,optimize=True)
    skew=np.einsum("ni,ni,ni,i->n",q,q,q,w,optimize=True)
    quartic=np.einsum("ni,ni,ni,ni,i->n",q,q,q,q,w,optimize=True)
    one=6*var+4*skew+quartic
    # Numerically stable F4 source increment.
    out={"deltaF4":one,"variance":var,"cubic":skew,"quartic":quartic,
         "Tbol_delta_microK":bolometric_proxy_shift_microK(one,T0_uK=T0_uK),
         "scope":"FINITE_ELL2_3_FULLSKY_ANSATZ_QUARTIC_NO_BEAM_OR_SELECTION_LIKELIHOOD"}
    if keep_components:
        q2=np.zeros_like(a);q2[:,:5]=a[:,:5]
        q3=np.zeros_like(a);q3[:,5:]=a[:,5:]
        t2=np.asarray(q2,float)@basis.T/T0_uK
        t3=np.asarray(q3,float)@basis.T/T0_uK
        def dlt(t):
            u2=np.einsum("ni,ni,i->n",t,t,w,optimize=True)
            u3=np.einsum("ni,ni,ni,i->n",t,t,t,w,optimize=True)
            u4=np.einsum("ni,ni,ni,ni,i->n",t,t,t,t,w,optimize=True)
            return 6*u2+4*u3+u4
        dl2=dlt(t2)
        dl3=dlt(t3)
        out.update({"deltaF4_quad_only":dl2,
                    "deltaF4_oct_only":dl3,
                    "deltaF4_morphology_coupling":one-dl2-dl3,
                    "octupole_variance_analytic":
                       np.sum(a[:,5:12]**2,axis=1)/(4*np.pi*T0_uK**2),
                    "quad_variance_analytic":
                       np.sum(a[:,:5]**2,axis=1)/(4*np.pi*T0_uK**2)})
    return out


def quartic_power_shape_decomposition(real_coeff_l2_l3, *,
                                      T0_uK=T0_MICROK,
                                      n_mu=16, n_phi=32):
    """Separate already-measured power from higher-order angular shape.

    For t=sum_(ell=2,3,m) a_lm Y_lm/T0:
       v=<t^2>=sum_{ell m}a_lm^2/(4 pi T0^2);
       F4-1=6v + 4<t^3>+<t^4>.
    Shape-only normalized moments s3=<t^3>/v^(3/2) and
    k4=<t^4>/v^2 are scale-invariant under positive rescaling of a.

    This decomposition is *not independent data*. It is a deterministic
    functional of the same source harmonic coefficients. When v=0,
    standardized shape is undefined, not zero.
    """
    y=moment_delta_l23(real_coeff_l2_l3,T0_uK=T0_uK,
                       n_mu=n_mu,n_phi=n_phi,keep_components=True)
    a=np.asarray(real_coeff_l2_l3,float)
    v=(np.sum(a*a,axis=1))/(4*np.pi*T0_uK*T0_uK)
    if np.max(abs(y["variance"]-v))>3e-12*max(float(np.max(v)),1e-25):
        raise TeffOctupoleError("real harmonic power and angular variance identity failed")
    cubic=y["cubic"]
    quartic=y["quartic"]
    residual=4*cubic+quartic
    skew=np.full_like(v,np.nan,dtype=float)
    kurt=np.full_like(v,np.nan,dtype=float)
    np.divide(cubic,v*np.sqrt(v),where=v>0,out=skew)
    np.divide(quartic,v*v,where=v>0,out=kurt)
    if np.any((v>0)&(kurt<1-1e-10)):
        raise TeffOctupoleError("normalized fourth moment violates Jensen lower bound")
    return {
      "power_only_6variance":6*v,
      "shape_excess_4cubic_plus_quartic":residual,
      "deltaF4":6*v+residual,
      "normalized_skewness":skew,
      "normalized_kurtosis":kurt,
      "source_bandpower_variance":v,
      "ell2_ell3_quadrupole_octupole_power_ratio":
        np.divide(np.sum(a[:,5:12]**2,axis=1),
                  np.sum(a[:,:5]**2,axis=1),
                  where=np.sum(a[:,:5]**2,axis=1)>0,
                  out=np.full(len(a),np.nan)),
      "source_notes":{
        "data_independence":"NONE: all diagnostics deterministic from same 12 observed coefficients",
        "physical_null_p":"WITHHELD",
        "l1_and_lge4":"ABSENT_IN_FINITE_SOURCE_ANSATZ_NOT_PHYSICALLY_ZERO"
      }
    }



def parity_exact_l2_l3_mixed_contribution(real_coeff_l2_l3, *,
                                         T0_uK=T0_MICROK,
                                         n_mu=16,n_phi=32):
    """Derive <(q+o)^4> cross terms by even/odd spatial parity.

    q(n)=l2 even, o(n)=l3 odd. On full S2:
        <(q+o)^3>=<q³>+3<q o²>  (odd powers of o cancel)
        <(q+o)^4>=<q⁴>+6<q² o²>+<o⁴>.
    Thus mixing in F4-1 is 12<q o²>+6<q² o²>.
    Exact at finite bandlimit under our 16×32 spherical quadrature.
    """
    a=np.asarray(real_coeff_l2_l3)
    if (a.ndim!=2 or a.shape[1]!=12 or np.iscomplexobj(a) or
        not np.isfinite(a).all() or not np.isfinite(T0_uK) or T0_uK<=0):
        raise TeffOctupoleError("real finite 12D l2+l3 source required")
    basis,w=_quadrature_grid(n_mu,n_phi)
    vals=np.asarray(a,float)@basis.T/T0_uK
    q=np.asarray(a[:,:5],float)@basis[:,:5].T/T0_uK
    o=np.asarray(a[:,5:],float)@basis[:,5:].T/T0_uK
    qo2=np.einsum("ni,ni,ni,i->n",q,o,o,w,optimize=True)
    q2o2=np.einsum("ni,ni,ni,ni,i->n",q,q,o,o,w,optimize=True)
    forbidden={
       "q2_o":np.einsum("ni,ni,ni,i->n",q,q,o,w,optimize=True),
       "q3_o":np.einsum("ni,ni,ni,ni,i->n",q,q,q,o,w,optimize=True),
       "q_o3":np.einsum("ni,ni,ni,ni,i->n",q,o,o,o,w,optimize=True),
       "o3":np.einsum("ni,ni,ni,i->n",o,o,o,w,optimize=True),
    }
    predicted=12*qo2+6*q2o2
    ref=moment_delta_l23(a,T0_uK=T0_uK,n_mu=n_mu,n_phi=n_phi)["deltaF4_morphology_coupling"]
    discrepancy=np.max(abs(predicted-ref))
    if discrepancy>2e-22:
        raise TeffOctupoleError(f"parity cross-coupling identity failed {discrepancy:g}")
    return {"q_o2_third_order":qo2,
            "q2_o2_fourth_order":q2o2,
            "combined_F4_cross":predicted,
            "difference_vs_direct_bandlimited":float(discrepancy),
            "forbidden_parity_odd_moments":forbidden,
            "claim":"FULL_SKY_FINITE_ELL2_3_PARITY_IDENTITY_NOT_PHYSICAL_BIANCHI_SIGNAL"}
