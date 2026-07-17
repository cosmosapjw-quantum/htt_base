"""mio.core.ceiling_families — active ceiling-family registry.

The certification-matrix figure (F24 in
``BASS_PY_HTT_TSC_RESEARCH_PLAN.md``) and downstream MIO diagnostics both
need a stable, importable record of which model families have a certified
ceiling, an adopted-but-uncertified ceiling, or a hard obstruction.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

# PR-124: active MES consumers traverse the typed successor registry
# (common.mes_theorem_authority is the live authority; legacy values are
# labeled non-authoritative reproduction, see legacy_reproduction_coefficients).
from common.mes_successor_registry import current_mes_successor_registry

_MES_SUCCESSOR = current_mes_successor_registry().successor
_MES_SUCCESSOR_ID = _MES_SUCCESSOR.successor_id

__all__ = [
    "CeilingStatus",
    "CeilingFamily",
    "CEILING_FAMILIES",
    "get_ceiling_family",
    "certified_families",
    "blocked_families",
]


class CeilingStatus(Enum):
    """Status of a ceiling family's ``x_max`` derivation."""

    ADOPTED = "adopted"
    NUMERICALLY_CERTIFIED = "numerically_certified"
    THEOREM_GRADE = "theorem_grade"
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
        status=CeilingStatus.NUMERICALLY_CERTIFIED,
        certification_evidence=(
            "Restricted-scan MIO evidence: x >= 0 across the sector."
        ),
    ),
    "irrotational_nonneg_tilt": CeilingFamily(
        name="irrotational_nonneg_tilt",
        sign_sector="irrotational_nonneg",
        models=("FLRW_tilt", "BI_tilt", "BVII0_tilt", "BIII_tilt"),
        x_max_formula="Sig2_max_MES(eps1_kin) + Omega_tilt(beta)",
        status=CeilingStatus.NUMERICALLY_CERTIFIED,
        certification_evidence=(
            "Restricted-scan MIO evidence: x >= 0 and Omega_tilt >= 0."
        ),
    ),
    "irrotational_neg": CeilingFamily(
        name="irrotational_neg",
        sign_sector="irrotational_neg",
        models=("BIX_orth", "BIX_tilt", "BV_tilt"),
        x_max_formula="Sig2_max - |Omega_k_aniso|",
        status=CeilingStatus.ADOPTED,
        obstruction_reason=(
            "Negative Omega_k_aniso can flip x below zero (BIX counterexample)."
        ),
        certification_evidence="MES ceiling adopted operationally, not certified.",
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
        status=CeilingStatus.ADOPTED,
        obstruction_reason=(
            "W2 makes the sign sector indefinite without a vorticity bound."
        ),
        certification_evidence=(
            "Saadeh-style vorticity upper limits keep this operational but uncertified."
        ),
    ),
}


def get_ceiling_family(name: str) -> CeilingFamily:
    """Return a named ceiling family or raise a keyed error."""
    if name not in CEILING_FAMILIES:
        raise KeyError(
            f"Unknown ceiling family: {name}. "
            f"Available: {sorted(CEILING_FAMILIES)}"
        )
    return CEILING_FAMILIES[name]


def certified_families() -> dict[str, CeilingFamily]:
    """Return families that are numerically certified or theorem grade."""
    return {
        name: family
        for name, family in CEILING_FAMILIES.items()
        if family.status
        in (CeilingStatus.NUMERICALLY_CERTIFIED, CeilingStatus.THEOREM_GRADE)
    }


def blocked_families() -> dict[str, CeilingFamily]:
    """Return the hard-obstruction families."""
    return {
        name: family
        for name, family in CEILING_FAMILIES.items()
        if family.status == CeilingStatus.BLOCKED
    }
