"""Low-ell likelihood branch classifier (mean-template vs covariance).

REV-R099 splits the two admissible low-ell Bianchi likelihood branches and
forbids a central scalar chi-square from standing in for either:

- the mean-template branch (Bianchi as a deterministic mean template) requires a
  harmonic-space template and either orientation marginalization or a noncentral
  statistic;
- the covariance/BiPoSH branch (Bianchi as a stochastic covariance) requires a
  full anisotropic covariance.
"""
from __future__ import annotations

from typing import Any

__all__ = [
    "classify_lowell_likelihood",
    "MEAN_TEMPLATE_ROLE",
    "STOCHASTIC_COVARIANCE_ROLE",
]

MEAN_TEMPLATE_ROLE = "deterministic_mean_template"
STOCHASTIC_COVARIANCE_ROLE = "stochastic_covariance"

_HARMONIC_TOKENS = ("harmonic", "alm", "a_lm", "bipost", "biposh")
_NONCENTRAL_TOKENS = ("noncentral", "non_central", "non-central")
_FULL_COVARIANCE_TOKENS = frozenset({"full", "full_anisotropic", "bound", "full_covariance"})


def classify_lowell_likelihood(
    *,
    statistic: str,
    bianchi_role: str,
    orientation_status: str,
    covariance_status: str,
) -> dict[str, Any]:
    """Classify whether a low-ell likelihood branch is admissible."""

    stat = str(statistic).strip().lower()
    role = str(bianchi_role).strip()
    orientation = str(orientation_status).strip().lower()
    covariance = str(covariance_status).strip().lower()

    blocked_reasons: list[str] = []

    if role == MEAN_TEMPLATE_ROLE:
        is_harmonic = any(token in stat for token in _HARMONIC_TOKENS)
        is_noncentral = any(token in stat for token in _NONCENTRAL_TOKENS)
        orientation_marginalized = orientation == "marginalized"
        if not (is_harmonic and (orientation_marginalized or is_noncentral)):
            blocked_reasons.append("noncentral_or_harmonic_orientation_required")
    elif role == STOCHASTIC_COVARIANCE_ROLE:
        if covariance not in _FULL_COVARIANCE_TOKENS:
            blocked_reasons.append("full_covariance_not_bound")
    else:
        blocked_reasons.append("unknown_bianchi_role")

    # A central scalar chi-square (e.g. a D2/D3 scalar feature) is never enough
    # for either branch: in the mean-template branch it is neither harmonic nor
    # noncentral, and in the covariance branch it is not a full anisotropic
    # covariance -- both already produce a blocked reason above.
    allowed = not blocked_reasons
    return {
        "owner": "OBSSTAT",
        "implementation_scope": "obsstat",
        "statistic": statistic,
        "bianchi_role": bianchi_role,
        "orientation_status": orientation_status,
        "covariance_status": covariance_status,
        "allowed": allowed,
        "branch": (
            "mean_template"
            if role == MEAN_TEMPLATE_ROLE
            else "covariance" if role == STOCHASTIC_COVARIANCE_ROLE else "unknown"
        ),
        "blocked_reasons": blocked_reasons,
    }
