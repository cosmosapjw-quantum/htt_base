"""VER2 frame-split contracts for the BASS S2 lane."""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

__all__ = [
    "PhotonDirectionConvention",
    "PolarizationPhaseConvention",
    "BoostOrder",
    "FrameSplitMetadata",
    "FrameIdentityScope",
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
class FrameIdentityScope:
    """Immutable contract separating the two admissible vorticity identities.

    REV-R093 closes the strict-audit finding that a Bianchi~VII$_h$ vorticity
    decomposition was advertised as a current result without declaring its
    frame. Two scopes are distinguished:

    - ``normal_frame_slicing``: the hypersurface-normal (group-orbit normal)
      Bianchi slicing. Intrinsic group-orbit Ricci substitution is allowed and
      the vorticity sector is absent by construction (``W_std = 0``); a nonzero
      vorticity term is forbidden here.
    - ``threading_candidate``: the matter/threading frame. Vorticity may be
      discussed only if the full boost, energy-flux, anisotropic-stress, and
      momentum-constraint terms are bound; otherwise the scope is ``blocked``
      and records the missing terms.
    """

    frame_kind: str
    vorticity_term_allowed: bool
    geometry_ricci_substitution_allowed: bool
    claim_tier: str
    blocked_reasons: tuple[str, ...] = ()

    @classmethod
    def normal_frame_slicing(cls) -> "FrameIdentityScope":
        return cls(
            frame_kind="hypersurface_normal_slicing",
            vorticity_term_allowed=False,
            geometry_ricci_substitution_allowed=True,
            claim_tier="conditional",
            blocked_reasons=(),
        )

    @classmethod
    def threading_candidate(
        cls,
        *,
        full_boost_terms_bound: bool,
        flux_terms_bound: bool = False,
        anisotropic_stress_terms_bound: bool = False,
        constraint_terms_bound: bool = False,
    ) -> "FrameIdentityScope":
        blocked_reasons: list[str] = []
        if not full_boost_terms_bound:
            blocked_reasons.append("full_boost_terms_missing")
        if not flux_terms_bound:
            blocked_reasons.append("flux_terms_missing")
        if not anisotropic_stress_terms_bound:
            blocked_reasons.append("anisotropic_stress_terms_missing")
        if not constraint_terms_bound:
            blocked_reasons.append("constraint_terms_missing")
        is_blocked = bool(blocked_reasons)
        return cls(
            frame_kind="matter_threading_candidate",
            vorticity_term_allowed=not is_blocked,
            geometry_ricci_substitution_allowed=False,
            claim_tier="blocked" if is_blocked else "conditional",
            blocked_reasons=tuple(blocked_reasons),
        )


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
