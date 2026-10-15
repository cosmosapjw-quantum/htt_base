"""Conditional l2/l3 shape benchmark and source-matched amplitude reweighting.

This deliberately distinguishes three probability laws:
  (i) mathematical Gaussian isotropic CMB with observed fixed per-ell norms:
      independent uniform S^4 and S^6 coefficient directions;
  (ii) actual released FFP10 CMB-only source cohort after the *same*
       masked harmonic pipeline and radial reweighting per ell;
  (iii) the one observed Planck sky, with nine dependent processing maps.

Only (i) has an exact conditional distribution under the idealized
FULL-SKY Gaussian covariance and known C_l.  Applying it directly to
masked/processed observed harmonic fits is NOT a qualified Planck p-value.
(ii) is also descriptive until FFP10 end-to-end, foreground, beam and
processing/source-frame adequacy are independently demonstrated.
"""
from __future__ import annotations
from collections.abc import Iterator
import numpy as np
from .legacy_teff_octupole_exact import quartic_power_shape_decomposition


class PhaseConditionalDomainError(ValueError):
    pass


def _checked_coeff(a,*,allow_vector=False):
    x=np.asarray(a)
    dim=1 if allow_vector else 2
    if (x.ndim!=dim or x.shape[-1]!=12
        or np.iscomplexobj(x) or not np.isfinite(x).all()):
        raise PhaseConditionalDomainError("finite real l2 5 and l3 7 harmonic coefficients")
    return np.asarray(x,dtype=np.float64)


def per_ell_radii(reference):
    """Norms in thermodynamic microK, with exactly five/seven source modes."""
    a=_checked_coeff(reference,allow_vector=True)
    return np.array([np.linalg.norm(a[:5]),np.linalg.norm(a[5:])],float)


def theoretical_uniform_phase_moments(reference):
    """Exact mean of normalized cubic and quartic angular moments.

    For independent a_l uniform on S^(D_l-1) with fixed radius R_l:
       v_l=R_l²/(4 pi T0²), E[s3]=0
       E[k4]=3 [D2/(D2+2)v2²+D3/(D3+2)v3²+2v2 v3]
                       / (v2+v3)², D2=5, D3=7.
    This is an *exact ideal full-sky conditional Gaussian phase law*.
    """
    r=per_ell_radii(reference)
    r2,r3=r
    if (not np.isfinite(r).all() or
        (r2==0 and r3==0)):
        raise PhaseConditionalDomainError("nontrivial declared l2/l3 power required")
    # T0 cancels in all standardized shape ratios: use radius-squared.
    u=r2*r2
    v=r3*r3
    k4=3*((5/7)*u*u+(7/9)*v*v+2*u*v)/(u+v)**2
    return {
        "theoretical_conditional_mean_s3":0.0,
        "theoretical_conditional_mean_k4":float(k4),
        "radii_ell2_ell3_microK":r.tolist(),
        "variance_fraction_l2":float(u/(u+v)),
        "variance_fraction_l3":float(v/(u+v)),
        "assumptions":[
            "ideal full-sky Gaussian statistically isotropic coefficients per ell",
            "independent uniform S4 and S6 directions given both observed mode norms",
            "not a source-matched masked-map or beam/foreground null",
        ],
    }


def phase_chunks_at_fixed_power(reference,*,n_draws:int,seed:int,
                               chunk_size=512) -> Iterator[np.ndarray]:
    """Generate each unique ideal conditional phase realization exactly once.

    RNG uses a fixed seed; caller owns source ID and publication claim status.
    No recycling of simulations or nine treated-as-independent observed skies.
    """
    radii=per_ell_radii(reference)
    if not isinstance(n_draws,int) or not 1<=n_draws<=250000:
        raise PhaseConditionalDomainError("bounded positive number of phase draws")
    if not isinstance(seed,int) or seed<0:
        raise PhaseConditionalDomainError("explicit nonnegative random seed required")
    if not isinstance(chunk_size,int) or not 1<=chunk_size<=4096:
        raise PhaseConditionalDomainError("bounded computational batch required")
    if not radii.any():
        raise PhaseConditionalDomainError("cannot randomize two zero harmonic vectors")
    rng=np.random.default_rng(seed)
    for start in range(0,n_draws,chunk_size):
        count=min(chunk_size,n_draws-start)
        out=np.zeros((count,12),float)
        for lo,hi,radius in ((0,5,radii[0]),(5,12,radii[1])):
            if radius==0:continue
            z=rng.standard_normal((count,hi-lo))
            zlen=np.linalg.norm(z,axis=1)
            if np.any(zlen==0):
                raise PhaseConditionalDomainError("random generator supplied zero normal vector")
            out[:,lo:hi]=radius*z/zlen[:,None]
        yield out


def conditional_shape_null(reference,*,n_draws:int=8192,seed:int=20261015,
                           chunk_size=512):
    """Generate phase-conditioned shape-only S3/K4 over one fixed observed power.

    All samples condition on *one* declared reference's R2,R3. Statistical
    confidence about Planck is NOT claimed: source harmonic estimates came from
    finite masked fits and were selected after seeing the sky.
    """
    theory=theoretical_uniform_phase_moments(reference)
    s3=[];k4=[]
    for batch in phase_chunks_at_fixed_power(
            reference,n_draws=n_draws,seed=seed,chunk_size=chunk_size):
        q=quartic_power_shape_decomposition(batch)
        s3.append(np.asarray(q["normalized_skewness"]))
        k4.append(np.asarray(q["normalized_kurtosis"]))
    a=np.concatenate(s3)
    b=np.concatenate(k4)
    if len(a)!=n_draws or not np.isfinite(a).all() or not np.isfinite(b).all():
        raise PhaseConditionalDomainError("finite independent source phase draw output")
    return {"s3":a,"k4":b,"theory":theory,
            "simulation_unique_phase_ids":np.arange(n_draws,dtype=np.int32),
            "seed":seed,"n_draws":n_draws,
            "scope":"IDEAL_FIXED_POWER_GAUSSIAN_PHASE_NULL_NOT_OBSERVED_PLANCK_COVARIANCE"}


def source_rescale_phase_preserving(source_coeff,reference_coeff):
    """Reweight each FFP10 sky's l2/l3 norm to one reference *exactly*.

    This is a source-conditioned phase morphology diagnostic; after masking,
    the empirical distribution of normalized coefficients need not be
    uniform on an ideal S4×S6. Outputs are paired to original source IDs.
    """
    source=_checked_coeff(source_coeff)
    radii=per_ell_radii(reference_coeff)
    if len(source)==0 or not radii.any():
        raise PhaseConditionalDomainError("nonempty actual FFP10 and reference power required")
    result=np.zeros_like(source)
    for lo,hi,R in ((0,5,radii[0]),(5,12,radii[1])):
        if R==0:
            continue
        old=np.linalg.norm(source[:,lo:hi],axis=1)
        if np.any(old<=0):
            raise PhaseConditionalDomainError("nonzero source power in every supported band")
        result[:,lo:hi]=source[:,lo:hi]*(R/old)[:,None]
    return result


def descriptive_source_rank(observed_value,samples,*,centre):
    """Descriptive finite cohort rank ONLY, explicitly not statistical p."""
    x=np.asarray(samples)
    if x.ndim!=1 or len(x)<2 or not np.isfinite(x).all():
        raise PhaseConditionalDomainError("finite scalar source cohort required")
    y=float(observed_value)
    c=float(centre)
    if not np.isfinite(y) or not np.isfinite(c):
        raise PhaseConditionalDomainError("finite observed and reference centre")
    return {
        "less_or_equal_fraction":float(np.mean(x<=y)),
        "greater_or_equal_fraction":float(np.mean(x>=y)),
        "absolute_distance_from_centre_fraction_ge":
            float(np.mean(np.abs(x-c)>=abs(y-c))),
        "n_unique_source_rows":int(len(x)),
        "finite_rank_minimum_if_exchangeable_only":float(1/(len(x)+1)),
        "physical_null_p_value":"NOT_ADMITTED_RETROSPECTIVE_AND_UNQUALIFIED_SOURCE_RESPONSE",
    }
