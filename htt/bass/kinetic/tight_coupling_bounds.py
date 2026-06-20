"""Synthetic tight-coupling theorem diagnostics."""

from __future__ import annotations

from dataclasses import dataclass, field
import math
from typing import Any


DEFAULT_TIGHT_COUPLING_CAVEAT = (
    "Synthetic BASS tight-coupling diagnostic only; not an observed CMB "
    "temperature multipole bound, not native solver validation, and not "
    "geometry/family support."
)


@dataclass(frozen=True)
class AngularKLMomentBound:
    theorem_id: str
    multipole_status: str
    multipole_bound: float | None
    ell_max: int
    bridge_operator_norm: float | None
    source_norm: float
    harmonic_convention_status: str
    kl_to_temperature_bridge_status: str
    kill_switches: tuple[str, ...]
    owner: str = "BASS"
    implementation_scope: str = "bass_py"
    claim_tier: str = "diagnostic_only"
    transfer_source: str = "none"
    production_claim_allowed: bool = False
    native_solver_result: bool = False
    family_identification: bool = False
    caveats: tuple[str, ...] = field(default_factory=lambda: (DEFAULT_TIGHT_COUPLING_CAVEAT,))

    def as_payload(self) -> dict[str, Any]:
        return {
            "theorem_id": self.theorem_id,
            "multipole_status": self.multipole_status,
            "multipole_bound": self.multipole_bound,
            "ell_max": self.ell_max,
            "bridge_operator_norm": self.bridge_operator_norm,
            "source_norm": self.source_norm,
            "harmonic_convention_status": self.harmonic_convention_status,
            "kl_to_temperature_bridge_status": self.kl_to_temperature_bridge_status,
            "kill_switches": list(self.kill_switches),
            "owner": self.owner,
            "implementation_scope": self.implementation_scope,
            "claim_tier": self.claim_tier,
            "transfer_source": self.transfer_source,
            "production_claim_allowed": self.production_claim_allowed,
            "native_solver_result": self.native_solver_result,
            "family_identification": self.family_identification,
            "caveats": list(self.caveats),
        }


def angular_kl_multipole_bound(
    *,
    ell_max: int,
    bridge_operator_norm: float | None,
    source_norm: float,
    theorem_id: str,
    harmonic_convention_status: str = "declared_synthetic_density_only",
    kl_to_temperature_bridge_status: str = "not_bound",
    density_positive: bool = True,
) -> AngularKLMomentBound:
    if not isinstance(ell_max, int) or ell_max < 0:
        raise ValueError("ell_max must be a non-negative integer")
    source = float(source_norm)
    if not math.isfinite(source) or source < 0.0:
        raise ValueError("source_norm must be non-negative finite")
    if not density_positive:
        return AngularKLMomentBound(
            theorem_id=theorem_id,
            multipole_status="blocked_nonpositive_density_fixture",
            multipole_bound=None,
            ell_max=ell_max,
            bridge_operator_norm=None if bridge_operator_norm is None else float(bridge_operator_norm),
            source_norm=source,
            harmonic_convention_status=harmonic_convention_status,
            kl_to_temperature_bridge_status=kl_to_temperature_bridge_status,
            kill_switches=("nonpositive_density_blocks_angular_kl_bound",),
        )
    if harmonic_convention_status != "declared_synthetic_density_only":
        return AngularKLMomentBound(
            theorem_id=theorem_id,
            multipole_status="blocked_harmonic_convention_not_bound",
            multipole_bound=None,
            ell_max=ell_max,
            bridge_operator_norm=None if bridge_operator_norm is None else float(bridge_operator_norm),
            source_norm=source,
            harmonic_convention_status=harmonic_convention_status,
            kl_to_temperature_bridge_status=kl_to_temperature_bridge_status,
            kill_switches=("harmonic_convention_not_bound_blocks_kl_bound_use",),
        )
    if bridge_operator_norm is None:
        return AngularKLMomentBound(
            theorem_id=theorem_id,
            multipole_status="blocked_unbounded_multipole_bridge",
            multipole_bound=None,
            ell_max=ell_max,
            bridge_operator_norm=None,
            source_norm=source,
            harmonic_convention_status=harmonic_convention_status,
            kl_to_temperature_bridge_status=kl_to_temperature_bridge_status,
            kill_switches=("unbounded_multipole_bridge_blocks_s2_observational_use",),
        )
    bridge = float(bridge_operator_norm)
    if not math.isfinite(bridge) or bridge < 0.0:
        raise ValueError("bridge_operator_norm must be non-negative finite")
    return AngularKLMomentBound(
        theorem_id=theorem_id,
        multipole_status="synthetic_angular_kl_bound",
        multipole_bound=source * bridge / float(ell_max + 1),
        ell_max=ell_max,
        bridge_operator_norm=bridge,
        source_norm=source,
        harmonic_convention_status=harmonic_convention_status,
        kl_to_temperature_bridge_status=kl_to_temperature_bridge_status,
        kill_switches=("unbounded_multipole_bridge_blocks_s2_observational_use",),
    )
