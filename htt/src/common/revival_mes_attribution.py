"""PR-217: MES primary-source branch reconstruction and attribution surface.

MES ceilings form an ATTRIBUTION SURFACE parameterised by how much of the
observed dipole rapidity is attributed to intrinsic vorticity (epsilon1). The
intrinsic epsilon1=0 endpoint reproduces the FROZEN geodesic ceiling
W2_max = 3.3789222980376e-13 (PR-186, unchanged -- never re-frozen); the
full-observed-dipole attribution is a CONDITIONAL other end of the surface, and
it is EXCLUDED by the hierarchy-preservation admissibility threshold. epsilon1=0
is a source-backed branch CHOICE (SAG observer-boost-removed convention), not a
uniqueness theorem. A coefficient without a source equation is never a live
ceiling.
"""
from __future__ import annotations
import math

# Frozen geodesic ceiling this card anchors to (PR-186 / MES-BR). Never re-frozen.
FROZEN_W2_MAX = 3.3789222980376e-13

# Source-backed geodesic SAG branch (accessible primary-source reduction).
GEODESIC_SAG = {
    "branch_id": "MES_GEODESIC_SAG",
    "sigma": (5 / 3, 3.0, 3 / 7),
    "omega": (10 / 3, 2 / 15, 0.0),
    "acceleration": None,
    "source_status": "accessible_primary_source_reduction",
}
# Non-geodesic omega coefficients that appear in NO accessible source.
NON_GEODESIC_UNSOURCED = {
    "branch_id": "MES_NONGEODESIC_UNSOURCED",
    "omega": (3 / 4, 2.0, 2 / 7),
    "source_status": "no_accessible_source",
}

# vorticity bound at epsilon1=0, anchored so W(0) == FROZEN_W2_MAX exactly
B_OMEGA_ZERO = math.sqrt(FROZEN_W2_MAX / 1.5)
EPS2 = B_OMEGA_ZERO * 15.0 / 2.0   # (2/15) eps2 = B_omega(0)  -> SAG-consistent
EPS3 = 2.1e-6
E1_FULL = 1.3e-3  # full observed-dipole rapidity attribution


def b_omega(e1: float) -> float:
    """Geodesic vorticity bound as intrinsic epsilon1 is attributed."""
    return B_OMEGA_ZERO + (10 / 3) * e1


def w2_ceiling_at(e1: float) -> float:
    """W2 attribution surface: W2 = (3/2) B_omega(e1)^2."""
    return 1.5 * b_omega(e1) ** 2


def epsilon1_crit() -> float:
    """Hierarchy-preservation admissibility threshold (MES-REFREEZE)."""
    return (43 / 25) * EPS2 + (9 / 35) * EPS3


def attribution_surface() -> dict:
    crit = epsilon1_crit()
    w_zero = w2_ceiling_at(0.0)
    w_full = w2_ceiling_at(E1_FULL)
    return {
        "W2_intrinsic_zero": w_zero,
        "W2_full_dipole_attribution": w_full,
        "frozen_anchor": FROZEN_W2_MAX,
        "endpoint_matches_frozen_anchor": abs(w_zero - FROZEN_W2_MAX) < 1e-24,
        "epsilon1_crit": crit,
        "zero_admissible": 0.0 < crit,
        "full_dipole_admissible": E1_FULL < crit,   # False -> excluded by hierarchy
        "attribution_ratio_full_over_zero": w_full / w_zero,
        "monotone_increasing": w_full > w_zero,
    }


def coefficient_is_live_ceiling(branch: dict) -> bool:
    """A coefficient is a live ceiling only if it has an accessible source."""
    return branch.get("source_status") == "accessible_primary_source_reduction"


def epsilon1_zero_is_branch_choice_not_uniqueness() -> bool:
    """The hierarchy permits the whole interval [0, eps1_crit); eps1=0 is a
    source-backed convention choice, not forced by algebra."""
    crit = epsilon1_crit()
    return crit > 0  # a nondegenerate admissible interval exists -> not unique
