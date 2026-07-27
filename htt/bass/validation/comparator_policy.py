"""
bass/background/comparator_policy.py  (Week 1 Day 3)
=====================================================

Comparator policy for the master departure identity across Bianchi types.

Background
----------
The master departure identity (ch03 Thm 3.master-defect-id) is:

    x_C = Σ²_std - W²_std + Ω_tilt + Ω_{k,aniso}

where x_C is the comparator-dependent signed budget coordinate and
Ω_{k,aniso} = Ω_k - Ω_{k,ref}. The choice of comparator determines Ω_{k,ref}:

  - FLAT comparator (Ω_{k,ref} = 0): always algebraically well-defined
  - MATCHED comparator (Ω_{k,ref} = Ω_k^FLRW of matched type): only valid when
    the Bianchi type admits an FLRW limit
  - NULL comparator: for cosmologically marginal types (no FLRW limit) where
    neither FLAT nor MATCHED carries unambiguous physical meaning — in this
    case only x_C^direct (raw signed projection) is reported

Type compatibility (from ch03 §sec:ceiling-semantics + ch04 §sec:classAB)
------------------------------------------------------------------------
                      FLAT     MATCHED  NULL
  FLRW                ✅       n/a      n/a
  I       (k=0)        ✅       ✅       n/a
  V       (k=-1)       ✅       ✅       n/a
  VII_0   (k=0)        ✅       ✅       n/a
  VII_h   (k=-1)       ✅       ✅       n/a
  IX      (k=+1)       ✅       ✅       n/a
  II      (no limit)   ✅*      ❌       ✅
  III     (no limit)   ✅*      ❌       ✅
  IV      (no limit)   ✅*      ❌       ✅
  VI_0    (no limit)   ✅*      ❌       ✅
  VI_h    (no limit)   ✅*      ❌       ✅
  VIII    (no limit)   ✅*      ❌       ✅

  ✅* = valid but carries comparator-dependent meaning (see Prop `FC-no-auto`)
  ❌ = undefined (MATCHED requires matched FLRW limit)
  ✅ default = canonical choice for the type

Ratio semantics
---------------
The active module never divides this cross-sector signed projection by a bare
``x_max``.  A valid stress requires a non-negative identified sector and an
exactly channel-matched typed anchor.  Historical ``x_C/x_max`` arithmetic
lives only in ``bass.validation.legacy_comparator_policy``.

This module provides the logic for:
  1. Determining the appropriate comparator per type (`recommend_comparator`)
  2. Computing x_C given structure constants + kinematic variables
     (`compute_x_C` — Week 5 wires up; Day 3 provides API shape)
  3. Structured-null handling for Type IV and other marginal types
  4. Typed channel-matched anchor stress

References
----------
  ch03_framework.tex §sec:master-id, §sec:sector-partition, §sec:ceiling-semantics
  ch04_bianchi_bounds.tex §sec:classAB (Bianchi IV discussion)
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Optional, Sequence
import warnings

from common.statistical_foundations import (
    MESAnchorSpec,
    ScalarRange,
    SectorStress,
    evaluate_sector_stress,
)
from common.mes_successor_registry import current_mes_successor_registry
from bass.background.bianchi_types import (
    StructureConstants,
    TYPES_WITH_FLRW_LIMIT, MARGINAL_TYPES,
)

_MES_SUCCESSOR = current_mes_successor_registry().successor
_MES_SUCCESSOR_ID = _MES_SUCCESSOR.successor_id


# ═══════════════════════════════════════════════════════════════
# §1 — Comparator policy enum
# ═══════════════════════════════════════════════════════════════

class ComparatorPolicy(Enum):
    """Comparator choice for the departure identity x_C = ... + Ω_{k,aniso}.

    FLAT: Ω_{k,ref} = 0 (Euclidean FLRW comparator). Always valid but does
          not carry distance-from-matched-FLRW meaning for
          curvature-carrying types.

    MATCHED: Ω_{k,ref} = Ω_k^FLRW of the FLRW limit of this type. Only valid
             for types with an FLRW limit (I, V, VII_0, VII_h, IX).

    NULL: No comparator applied. Only the raw signed projection x_C^direct is
          reported. Used for marginal types
          (II, III, IV, VI_0, VI_h, VIII) where MATCHED is undefined and
          FLAT carries ambiguous meaning.
    """
    FLAT = "flat"
    MATCHED = "matched"
    NULL = "null"


@dataclass(frozen=True)
class ComparatorStatus:
    """Metadata describing the comparator choice for a given type+policy."""
    policy: ComparatorPolicy
    type_label: str
    is_valid: bool
    reason: str = ""

    @property
    def x_C_defined(self) -> bool:
        """Deprecated alias: whether a comparator-defined projection exists."""
        return self.is_valid and self.policy != ComparatorPolicy.NULL

    @property
    def F_C_defined(self) -> bool:
        """Deprecated compatibility flag; never authorizes an active ratio."""
        return False

    @property
    def signed_budget_coordinate_defined(self) -> bool:
        """Whether the comparator-defined signed algebraic projection exists."""
        return self.is_valid and self.policy != ComparatorPolicy.NULL


# ═══════════════════════════════════════════════════════════════
# §2 — Policy dispatch
# ═══════════════════════════════════════════════════════════════

# Types where MATCHED is well-defined (admit FLRW limit)
MATCHED_COMPATIBLE = set(TYPES_WITH_FLRW_LIMIT)  # {I, V, VII_0, VII_h, IX}

# Types where NULL is the recommended default (no FLRW limit)
NULL_RECOMMENDED = set(MARGINAL_TYPES)  # {II, III, IV, VI_0, VI_h, VIII}


def recommend_comparator(type_label: str) -> ComparatorPolicy:
    """Recommend the canonical comparator for a given Bianchi type.

    Recommendation policy:
      - If the type admits an FLRW limit → MATCHED (algebraic comparator)
      - Otherwise → NULL (comparator-free reporting)

    The FLAT comparator is always available as a secondary option but is
    never the primary recommendation — it conflates true anisotropy with
    coordinate curvature.
    """
    if type_label == "FLRW":
        return ComparatorPolicy.MATCHED  # FLRW is its own matched comparator
    if type_label in MATCHED_COMPATIBLE:
        return ComparatorPolicy.MATCHED
    if type_label in NULL_RECOMMENDED:
        return ComparatorPolicy.NULL
    # Default: NULL for unknown types (safe)
    warnings.warn(
        f"Unknown type '{type_label}' — recommending NULL comparator"
    )
    return ComparatorPolicy.NULL


def validate_comparator(
    type_label: str,
    policy: ComparatorPolicy,
) -> ComparatorStatus:
    """Check whether a given comparator policy is valid for a type.

    Returns
    -------
    ComparatorStatus
        is_valid is True if the policy can be applied; False otherwise.
        reason gives a human-readable explanation when is_valid is False.
    """
    # FLAT is always valid (may be uninformative, but never ill-defined)
    if policy == ComparatorPolicy.FLAT:
        return ComparatorStatus(
            policy=policy, type_label=type_label, is_valid=True,
            reason="FLAT comparator is always valid (Ω_k,ref = 0)",
        )

    # MATCHED requires FLRW limit
    if policy == ComparatorPolicy.MATCHED:
        if type_label == "FLRW" or type_label in MATCHED_COMPATIBLE:
            return ComparatorStatus(
                policy=policy, type_label=type_label, is_valid=True,
                reason=f"{type_label} admits FLRW limit; MATCHED is canonical",
            )
        return ComparatorStatus(
            policy=policy, type_label=type_label, is_valid=False,
            reason=(
                f"{type_label} has no FLRW limit; MATCHED comparator "
                f"is undefined. Use NULL or FLAT instead."
            ),
        )

    # NULL is always valid (structured-null reporting)
    if policy == ComparatorPolicy.NULL:
        return ComparatorStatus(
            policy=policy, type_label=type_label, is_valid=True,
            reason="NULL comparator is always valid (x_C^direct reported)",
        )

    # Unknown policy
    return ComparatorStatus(
        policy=policy, type_label=type_label, is_valid=False,
        reason=f"Unknown comparator policy {policy}",
    )


# ═══════════════════════════════════════════════════════════════
# §3 — Departure components (API scaffolding)
# ═══════════════════════════════════════════════════════════════

@dataclass(frozen=True)
class DepartureComponents:
    """The four components of the master departure identity.

    x_C = Σ²_std - W²_std + Ω_tilt + Ω_{k,aniso}

    All fields are dimensionless (ratios to Hubble² or total density).
    Ω_{k,aniso} is policy-dependent: equals Ω_k if policy=FLAT, equals 0 if
    policy=MATCHED (for types with FLRW limit), None if policy=NULL.
    """
    Sigstd_sq: float                    # Σ²_std = σ_ab σ^ab / (6 H_θ²) ≥ 0
    Wstd_sq: float                      # W²_std = ω_ab ω^ab / (6 H_θ²) ≥ 0
    Omega_tilt: float                   # (1+w) Ω sinh²β ≥ 0
    Omega_k: float                      # Ω_k = -³R/(6 H_θ²)
    Omega_k_ref: Optional[float]        # comparator reference (None if NULL)
    policy: ComparatorPolicy

    @property
    def Omega_k_aniso(self) -> Optional[float]:
        """Ω_{k,aniso} = Ω_k - Ω_{k,ref}. Returns None if NULL comparator."""
        if self.Omega_k_ref is None:
            return None
        return self.Omega_k - self.Omega_k_ref

    @property
    def x_C(self) -> Optional[float]:
        """Signed budget projection x_C. Returns None for a NULL comparator."""
        oka = self.Omega_k_aniso
        if oka is None:
            return None
        return self.Sigstd_sq - self.Wstd_sq + self.Omega_tilt + oka

    @property
    def x_C_direct(self) -> float:
        """Raw signed projection without comparator subtraction.

        x_C^direct = Σ²_std - W²_std + Ω_tilt + Ω_k

        This is the comparator-free quantity that is ALWAYS well-defined, even
        for marginal types. For types with FLRW limit under MATCHED comparator,
        x_C_direct differs from x_C by a constant (Ω_{k,ref}).
        """
        return self.Sigstd_sq - self.Wstd_sq + self.Omega_tilt + self.Omega_k

    @property
    def sector(self) -> str:
        """Sign-domain sector classification (ch03 Proposition `x-sign`).

        Returns:
            'irrotational_positive'  if W²_std = 0 and x_C > 0
            'irrotational_negative'  if W²_std = 0 and x_C < 0
            'vortical'               if W²_std > 0
            'undefined'              if x_C is None (NULL comparator)
        """
        if self.Wstd_sq > 1e-30:
            return "vortical"
        x = self.x_C
        if x is None:
            x = self.x_C_direct
        if x >= 0:
            return "irrotational_positive"
        return "irrotational_negative"


def compute_departure_components(
    sc: StructureConstants,
    sigma_sq: float,        # σ_ab σ^ab
    omega_sq: float,        # ω_ab ω^ab
    H_theta: float,         # kinematical Hubble H_θ = Θ/3
    beta: float = 0.0,      # tilt rapidity
    w: float = 0.0,         # equation of state (default: dust)
    Omega_matter: float = 1.0,  # matter density parameter
    Omega_k: float = 0.0,       # total Ω_k from spatial curvature
    Omega_k_ref: Optional[float] = None,
    policy: Optional[ComparatorPolicy] = None,
) -> DepartureComponents:
    """Compute the four components of x_C for a given Bianchi state.

    Parameters
    ----------
    sc : StructureConstants
        Bianchi type structure constants.
    sigma_sq, omega_sq : float
        Shear and vorticity squared (same units as H_θ²).
    H_theta : float
        Kinematical Hubble rate H_θ = Θ/3.
    beta : float
        Tilt rapidity (matter frame vs geometry frame).
    w : float
        Equation of state parameter (0 = dust, 1/3 = radiation).
    Omega_matter : float
        Matter density parameter.
    Omega_k : float
        Spatial curvature density parameter Ω_k = -³R/(6 H_θ²).
    Omega_k_ref : float, optional
        Explicit comparator reference curvature. When omitted, the
        matched-comparator path uses the canonical contract already
        encoded in the manuscript: ``Ω_{k,aniso} = 0`` under the
        curvature-matched comparator, so ``Omega_k_ref`` defaults to
        ``Omega_k`` for curvature-carrying matched families and to
        ``0`` for flat matched families.
    policy : ComparatorPolicy, optional
        If None, uses recommend_comparator(sc.label).

    Returns
    -------
    DepartureComponents
        All four departure components, with comparator metadata.

    Notes
    -----
    This is the **API scaffolding** for Week 5. Day 3 provides the data
    structure and comparator routing; the actual computation from the
    background evolution is wired in during Week 5 when the forward model
    strata S1-S4 are implemented.
    """
    if policy is None:
        policy = recommend_comparator(sc.label)

    status = validate_comparator(sc.label, policy)
    if not status.is_valid:
        raise ValueError(
            f"Invalid comparator policy {policy} for type {sc.label}: "
            f"{status.reason}"
        )

    # Dimensionless kinematic components
    H_theta_sq = H_theta ** 2 if H_theta > 0 else 1e-30
    Sigstd_sq = sigma_sq / (6.0 * H_theta_sq)
    Wstd_sq = omega_sq / (6.0 * H_theta_sq)

    # Tilt component (ch03 Eq. eq:Otilt-def)
    import math
    Omega_tilt = (1.0 + w) * Omega_matter * math.sinh(beta) ** 2

    # Comparator reference
    if policy == ComparatorPolicy.FLAT:
        resolved_Omega_k_ref = 0.0 if Omega_k_ref is None else float(Omega_k_ref)
    elif policy == ComparatorPolicy.MATCHED:
        if Omega_k_ref is not None:
            resolved_Omega_k_ref = float(Omega_k_ref)
        elif sc.label in ("I", "VII_0"):
            resolved_Omega_k_ref = 0.0
        else:
            # Curvature-matched comparator sets Ω_{k,aniso} = 0 by
            # construction for the matched FLRW branch.
            resolved_Omega_k_ref = float(Omega_k)
    else:  # NULL
        resolved_Omega_k_ref = None

    return DepartureComponents(
        Sigstd_sq=Sigstd_sq,
        Wstd_sq=Wstd_sq,
        Omega_tilt=Omega_tilt,
        Omega_k=Omega_k,
        Omega_k_ref=resolved_Omega_k_ref,
        policy=policy,
    )


# ═══════════════════════════════════════════════════════════════
# §4 — Typed, channel-matched anchor stress
# ═══════════════════════════════════════════════════════════════

def evaluate_comparator_anchor_stress(
    *,
    sector: str,
    numerator: ScalarRange | None,
    anchor: MESAnchorSpec | None,
    numerator_channel_key: Sequence[str] | None,
) -> SectorStress:
    """Evaluate one non-negative sector against an exactly matched anchor.

    ``DepartureComponents.x_C`` is intentionally not accepted because it
    combines signed, heterogeneous channels. Missing and mismatched channels
    produce typed non-numeric statuses in the COMMON evaluator.
    """

    return evaluate_sector_stress(
        sector=sector,
        numerator=numerator,
        anchor=anchor,
        numerator_channel_key=numerator_channel_key,
    )


# ═══════════════════════════════════════════════════════════════
# §5 — Bianchi IV special-case reporter
# ═══════════════════════════════════════════════════════════════

def bianchi_iv_falsifiability_probe(
    comp: DepartureComponents,
    sc: StructureConstants,
) -> dict:
    """Falsifiability probe for Bianchi IV (cosmologically marginal).

    Bianchi IV has no FLRW limit. This function reports only structural
    comparator facts that a separately registered HTT likelihood may consume.

    Returns
    -------
    dict
        A structured-null report with fields:
            type_label:          'IV'
            comparator_status:   'NULL' (always for Type IV)
            x_C_direct:          the raw signed projection (always finite)
            sector:              'irrotational_positive' or 'irrotational_negative'
            no_flrw_limit_flag:  True (structural metadata)

    Notes
    -----
    This function does not calculate or predict a Bayes factor. Any exclusion
    test belongs to an HTT-owned registered likelihood and execution receipt.
    """
    if sc.label != "IV":
        raise ValueError(f"Expected Type IV, got {sc.label}")
    if not sc.no_flrw_limit:
        raise ValueError(
            "Bianchi IV must have no_flrw_limit=True (structural invariant)"
        )

    return {
        'type_label': 'IV',
        'comparator_status': 'NULL',
        'x_C_direct': comp.x_C_direct,
        'x_C': None,                    # undefined under NULL comparator
        'sector': comp.sector,
        'no_flrw_limit_flag': True,
        'inference_status': 'not_run_structural_diagnostic_only',
        'allowed_use': ('HTT validation-contract input',),
        'forbidden_use': (
            'Bayes-factor result',
            'MIO evidence',
            'family identification',
        ),
        'policy': comp.policy.value,
    }


__all__ = [
    "ComparatorPolicy",
    "ComparatorStatus",
    "DepartureComponents",
    "MATCHED_COMPATIBLE",
    "NULL_RECOMMENDED",
    "bianchi_iv_falsifiability_probe",
    "compute_departure_components",
    "evaluate_comparator_anchor_stress",
    "recommend_comparator",
    "validate_comparator",
]
