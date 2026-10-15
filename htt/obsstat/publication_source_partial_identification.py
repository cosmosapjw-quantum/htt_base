"""Source-conditional signed x_C/Q partial identification without a fake posterior.

MES C1/C2 + residual eps1=0 is a COUNTERFACTUAL convention here; actual
Planck observed multipoles do not prove all-observer spacetime derivatives.
Planck map-processing alternatives are ONE physical sky, never 9 draws.
No CF4 angular STF is substituted for physical shear.
"""
from __future__ import annotations

import numpy as np
from .mes_eps_measurement_bridge import (
    eps_from_retained,geodesic_algebraic_sector_ceiling
)


class SourcePartialIdError(ValueError):
    pass


def source_case_from_planck_temperature_alm(source_ell2_to5,
                                            *,observer_epsilon1_scenario="zero"):
    """Mathematically typed conditional MES ceiling, no physical identification."""
    if observer_epsilon1_scenario!="zero":
        raise SourcePartialIdError("only explicit algebraic eps1=0 branch is implemented")
    row=eps_from_retained(source_ell2_to5)
    e2=row["2"]["SAG_eq17_covariant_rms_tensor_norm"]
    e3=row["3"]["SAG_eq17_covariant_rms_tensor_norm"]
    c=geodesic_algebraic_sector_ceiling(e2,e3,eps1=0.)
    us=c["Sigma2_anchor_only_if_conditions_met"]
    uw=c["W2_anchor_only_if_conditions_met"]
    if us <=0:
        return {
            "status":"ZERO_SHEAR_ANCHOR_Q_UNDEFINED",
            "eps2_source_projection":e2,"eps3_source_projection":e3,
            "U_sigma":us,"U_omega":uw,
            "flat_untilted_counterfactual_Q_outer_interval":None,
            "full_unknown_curvature_tilt_Q_domain":"UNDEFINED",
            "physical_posterior":"ABSENT",
        }
    return {
        "status":"SOURCE_CONDITIONAL_ALGEBRAIC_ONLY",
        "eps2_source_projection":e2,"eps3_source_projection":e3,
        "U_sigma":us,"U_omega":uw,
        "U_omega_over_U_sigma":uw/us,
        "flat_untilted_counterfactual_Q_outer_interval":[-uw/us,1.],
        "flat_untilted_case_extra_assumptions":[
            "MES small-anisotropy branch with C1/C2 all-observer derivatives",
            "Intrinsic radiation epsilon1 equals zero",
            "Omega_tilt exactly zero by model hypothesis",
            "DeltaOmega_k exactly zero by model hypothesis",
            "0 <= Sigma^2 <= U_sigma and 0 <= W^2 <= U_omega",
        ],
        "full_unknown_curvature_tilt_Q_domain":"UNBOUNDED_BOTH_SIDES",
        "full_unknown_Q_not_identified_reason":
            "Unrestricted signed curvature can shift x_C by any real value; "
            "matter/radiation tilt sector also has no observational posterior.",
        "physical_posterior":"ABSENT",
        "different_planck_processing_methods_are_new_latent_realizations":False,
    }


def strict_tail_probability_identified_set(threshold, domain):
    """Any probability measure with support on the declared Q interval.

    This is a set-of-possible-distributions bound, not a null p-value or a
    posterior inferred from actual CMB/CF4 observations. Uniform weights over
    processing products are NEVER used.
    """
    try:
        t=float(threshold)
    except (TypeError,ValueError) as err:
        raise SourcePartialIdError("finite threshold expected") from err
    if not np.isfinite(t):
        raise SourcePartialIdError("finite threshold expected")
    if domain=="UNBOUNDED_BOTH_SIDES":
        return [0.,1.]
    if domain is None or domain=="UNDEFINED":
        return [0.,1.]
    a=np.asarray(domain)
    if (a.shape!=(2,) or np.iscomplexobj(a) or
        not np.isfinite(a).all() or a[0]>a[1]):
        raise SourcePartialIdError("closed finite feasible Q interval expected")
    lo,hi=map(float,a)
    # Strict event Q>t: at t>=hi there are no exceeding completions,
    # at t<lo all feasible completions exceed; intermediate unknown.
    if t<lo:
        return [1.,1.]
    if t>=hi:
        return [0.,0.]
    return [0.,1.]
