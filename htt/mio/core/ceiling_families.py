"""Historical scalar ceiling-family registry.

The entries remain importable for frozen figure and payload reproduction.
They are not active MES anchors, cannot normalize Q/F, and cannot certify or
identify a Bianchi family. Active code uses typed channel anchors and
identified sets from ``common.statistical_foundations``.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
import warnings

# PR-124: active MES consumers traverse the typed successor registry
# (common.mes_theorem_authority is the live authority; legacy values are
# labeled non-authoritative reproduction, see legacy_reproduction_coefficients).
from common.mes_successor_registry import current_mes_successor_registry

_MES_SUCCESSOR = current_mes_successor_registry().successor
_MES_SUCCESSOR_ID = _MES_SUCCESSOR.successor_id
LEGACY_REPRODUCTION_ONLY = True

warnings.warn(
    "mio.core.ceiling_families is a historical scalar registry; "
    "use typed channel anchors for active analysis",
    DeprecationWarning,
    stacklevel=2,
)

__all__ = [
    "CeilingStatus",
    "CeilingFamily",
    "CEILING_FAMILIES",
    "get_ceiling_family",
    "certified_families",
    "blocked_families",
]


class CeilingStatus(Enum):
    """Compatibility status of a historical scalar formula."""

    ADOPTED = "adopted"
    NUMERICALLY_CERTIFIED = "numerically_certified"
    THEOREM_GRADE = "theorem_grade"
    LEGACY_REPRODUCTION = "legacy_reproduction"
    NO_MES_ANCHOR = "no_mes_anchor"
    BLOCKED = "blocked"


@dataclass(frozen=True)
class CeilingFamily:
    """A ceiling family: models sharing the same ceiling structure."""

    name: str
    sign_sector: str
    models: tuple[str, ...]
    x_max_formula: str
    status: CeilingStatus
    obstruction_reason: str | None = None
    certification_evidence: str | None = None
    allowed_use: tuple[str, ...] = ("historical reproduction",)
    forbidden_use: tuple[str, ...] = (
        "active normalization",
        "family certification",
        "family identification",
        "cross-channel scalar ceiling",
    )


CEILING_FAMILIES: dict[str, CeilingFamily] = {
    "irrotational_nonneg_orth": CeilingFamily(
        name="irrotational_nonneg_orth",
        sign_sector="irrotational_nonneg",
        models=(
            "FLRW",
            "BI_orth",
            "BVII0_orth",
            "BII_orth",
            "BVI0_orth",
            "BVIII_orth",
        ),
        x_max_formula="Sig2_max_MES(eps1_kin)",
        status=CeilingStatus.LEGACY_REPRODUCTION,
        certification_evidence=(
            "Historical restricted scan only; not a certification."
        ),
    ),
    "irrotational_nonneg_tilt": CeilingFamily(
        name="irrotational_nonneg_tilt",
        sign_sector="irrotational_nonneg",
        models=("FLRW_tilt", "BI_tilt", "BVII0_tilt", "BIII_tilt"),
        x_max_formula="Sig2_max_MES(eps1_kin) + Omega_tilt(beta)",
        status=CeilingStatus.NO_MES_ANCHOR,
        certification_evidence=(
            "Tilt and shear are different channels; no composite MES anchor."
        ),
    ),
    "irrotational_neg": CeilingFamily(
        name="irrotational_neg",
        sign_sector="irrotational_neg",
        models=("BIX_orth", "BIX_tilt", "BV_tilt"),
        x_max_formula="Sig2_max - |Omega_k_aniso|",
        status=CeilingStatus.NO_MES_ANCHOR,
        obstruction_reason=(
            "Negative Omega_k_aniso can flip x below zero (BIX counterexample)."
        ),
        certification_evidence="No anisotropic-curvature MES anchor.",
    ),
    "blocked_momentum": CeilingFamily(
        name="blocked_momentum",
        sign_sector="irrotational_neg",
        models=("BV_tilt",),
        x_max_formula="N/A (momentum constraint obstruction)",
        status=CeilingStatus.BLOCKED,
        obstruction_reason=(
            "Momentum-constraint sector overproduces the quadrupole by orders of magnitude."
        ),
    ),
    "vortical": CeilingFamily(
        name="vortical",
        sign_sector="vortical",
        models=("BVIIh_orth", "BVIIh_orth_grow", "BVIIh_tilt", "BVIIh_tilt_grow"),
        x_max_formula="Sig2_max - W2_max + Omega_tilt",
        status=CeilingStatus.NO_MES_ANCHOR,
        obstruction_reason=(
            "W2 makes the sign sector indefinite without a vorticity bound."
        ),
        certification_evidence=(
            "Subtracting a vorticity upper bound is not an upper bound on -W2."
        ),
    ),
}


def get_ceiling_family(name: str) -> CeilingFamily:
    """Return a historical entry or raise a keyed error."""
    warnings.warn(
        "get_ceiling_family returns legacy reproduction metadata only",
        DeprecationWarning,
        stacklevel=2,
    )
    if name not in CEILING_FAMILIES:
        raise KeyError(
            f"Unknown ceiling family: {name}. "
            f"Available: {sorted(CEILING_FAMILIES)}"
        )
    return CEILING_FAMILIES[name]


def certified_families() -> dict[str, CeilingFamily]:
    """No scalar formula in this legacy registry certifies a family."""
    return {}


def blocked_families() -> dict[str, CeilingFamily]:
    """Return every entry blocked from active scalar normalization."""
    return dict(CEILING_FAMILIES)
