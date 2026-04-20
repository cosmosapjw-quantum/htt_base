"""VER2 frame-split contracts for the BASS S2 lane."""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

__all__ = [
    "PhotonDirectionConvention",
    "PolarizationPhaseConvention",
    "BoostOrder",
    "FrameSplitMetadata",
]


class PhotonDirectionConvention(str, Enum):
    """Whether a direction variable is a propagation or observed-sky direction."""

    PROPAGATION = "propagation_direction"
    SKY = "observed_sky_direction"


class PolarizationPhaseConvention(str, Enum):
    """Recorded polarization phase/sign convention."""

    SCREEN_UV = "screen_u_plus_i_screen_v"
    EXPLICIT_UNFIXED = "explicit_but_not_iau_named"


class BoostOrder(str, Enum):
    """Declared boost approximation order for seed and collision wiring."""

    LINEAR = "linear"
    EXACT_ANGULAR = "exact_angular"


@dataclass(frozen=True)
class FrameSplitMetadata:
    """Single S2 source of truth for transport/collision/history frame ownership."""

    transport_frame: str = "n_frame"
    collision_frame: str = "electron_frame"
    visibility_frame: str = "electron_frame"
    scalar_history_scope: str = "scalar_history_first_pass"
    direction_convention: PhotonDirectionConvention = PhotonDirectionConvention.PROPAGATION
    polarization_phase_convention: PolarizationPhaseConvention = (
        PolarizationPhaseConvention.SCREEN_UV
    )
    no_flrw_only_collision_shortcut: bool = True
    low_ell_truncation_allowed: bool = True
    anisotropic_atomic_microphysics: bool = False

    def __post_init__(self) -> None:
        if self.transport_frame != "n_frame":
            raise ValueError(
                f"VER2 transport must remain in the n^a frame; got {self.transport_frame!r}"
            )
        if self.collision_frame != "electron_frame":
            raise ValueError(
                f"VER2 collision must remain in the electron frame; got {self.collision_frame!r}"
            )
        if self.visibility_frame != "electron_frame":
            raise ValueError(
                f"VER2 visibility must remain in the electron frame; got {self.visibility_frame!r}"
            )
        if self.scalar_history_scope != "scalar_history_first_pass":
            raise ValueError(
                "VER2 S2 freezes scalar-history-first-pass only in this packet; "
                f"got {self.scalar_history_scope!r}"
            )
        if not self.no_flrw_only_collision_shortcut:
            raise ValueError("VER2 S2 forbids silently falling back to an FLRW-only collision shortcut")
        if self.anisotropic_atomic_microphysics:
            raise ValueError(
                "Anisotropic atomic recombination is explicitly out of scope for SK-02S2"
            )
