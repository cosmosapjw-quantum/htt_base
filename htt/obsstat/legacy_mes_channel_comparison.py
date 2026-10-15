"""R2 legacy MES channel algebra and registered modern MES source comparison.

The original legacy code and current theorem registry may use *different*
source/frame/derivative conventions for omega and A sectors. Comparing
their numerical coefficients does NOT prove that either is the correct
physical bound for Planck; it provides a reproducible incompatibility
witness to prevent silent aliasing in posterior pushforwards.

Do not merge independent Planck processing products into posterior samples.
"""
from __future__ import annotations
import math
import numpy as np
from .mes_eps_measurement_bridge import geodesic_algebraic_sector_ceiling


class LegacyMesChannelError(ValueError):
    pass


def compare_branch(eps1,eps2,eps3,legacy_bound_adapter):
    e=np.asarray((eps1,eps2,eps3),dtype=float)
    if e.shape!=(3,) or not np.isfinite(e).all() or np.any(e<0):
        raise LegacyMesChannelError("finite nonnegative registered eps1/2/3 needed")
    old=legacy_bound_adapter.bounds_from_epsilon(
        eps1,eps2,eps3,frame_correction=False)
    new=geodesic_algebraic_sector_ceiling(eps2,eps3,eps1=eps1)
    u_old=1.5*float(old["B_omega"])**2
    u_new=float(new["W2_anchor_only_if_conditions_met"])
    if u_new<=0:
        omega_ratio=None
        omega_normratio=None
    else:
        omega_ratio=u_old/u_new
        omega_normratio=float(old["B_omega"])/float(new["B_omega_over_Theta"])
    return {
        "eps1_2_3":[float(z) for z in e],
        "historical_R2_legacy_Bsigma":float(old["B_sigma"]),
        "current_geodesic_Bsigma":float(new["B_sigma_over_Theta"]),
        "historical_R2_legacy_Bomega":float(old["B_omega"]),
        "current_geodesic_Bomega":float(new["B_omega_over_Theta"]),
        "historical_R2_legacy_Baccel":float(old["B_accel"]),
        "current_geodesic_A":"ZERO_STRUCTURAL_IN_REGISTERED_GEODESIC_LANE",
        "historical_R2_legacy_W2_normalizer":u_old,
        "current_geodesic_W2_normalizer":u_new,
        "historical_over_current_W2_ratio":omega_ratio,
        "historical_over_current_Bomega_ratio":omega_normratio,
        "exact_numerical_Bsigma_agreement":
            math.isclose(float(old["B_sigma"]),float(new["B_sigma_over_Theta"]),
                         rel_tol=2e-14,abs_tol=2e-16),
        "source_physical_equivalence":"NOT_ADMITTED_CONVENTION_AND_AUTHORITY_UNRESOLVED",
        "physical_bound_status":"WITHHELD",
    }
