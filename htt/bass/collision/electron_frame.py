"""VER2 electron-frame Thomson contracts for the BASS S2 lane."""
from __future__ import annotations

from dataclasses import dataclass, field

from bass.hierarchy.frame_contracts import FrameSplitMetadata, PhotonDirectionConvention

__all__ = [
    "ElectronFrameRate",
    "ElectronFrameThomsonContext",
    "ThomsonProjectionStub",
    "electron_frame_rate_factor",
    "project_thomson_source_stub",
]


@dataclass(frozen=True)
class ElectronFrameRate:
    gamma_e: float
    factor: float
    direction_convention: PhotonDirectionConvention


@dataclass(frozen=True)
class ElectronFrameThomsonContext:
    """Metadata surface for projected Thomson scattering."""

    frame_metadata: FrameSplitMetadata = field(default_factory=FrameSplitMetadata)
    direction_convention: PhotonDirectionConvention = PhotonDirectionConvention.PROPAGATION
    projection_mode: str = "pstf_projected"
    operator_scope: str = "linear_classical_thomson"
    orthogonal_reference_operator: str = "ThomsonPSTFCollisionOperator"
    isotropic_null_mode_required: bool = True
    linearity_required: bool = True

    def __post_init__(self) -> None:
        if self.frame_metadata.collision_frame != "electron_frame":
            raise ValueError("Thomson collision must remain electron-frame in VER2")
        if self.projection_mode not in {"pstf_projected", "angular_grid"}:
            raise ValueError(f"unknown projection_mode {self.projection_mode!r}")
        if self.operator_scope != "linear_classical_thomson":
            raise ValueError("SK-02S2 freezes classical linear Thomson only")


@dataclass(frozen=True)
class ThomsonProjectionStub:
    """Non-executable placeholder result for S2 contract wiring."""

    source_ready: bool = False
    linearity_required: bool = True
    isotropic_null_mode_required: bool = True
    pure_quadrupole_response_required: bool = True
    reason: str = (
        "Projected Thomson source remains a skeleton in SK-02S2; executable "
        "projection belongs to the later solver packet."
    )


def electron_frame_rate_factor(
    *,
    gamma_e: float,
    v_dot_direction: float,
    convention: PhotonDirectionConvention = PhotonDirectionConvention.PROPAGATION,
) -> ElectronFrameRate:
    """Return the exact electron-frame scattering-rate factor.

    For propagation direction `e^a`, the factor is `γ_e (1 - v·e)`.
    For observed sky direction `n_sky = -e`, the factor is `γ_e (1 + v·n_sky)`.
    """
    if gamma_e < 1.0:
        raise ValueError(f"gamma_e must be >= 1, got {gamma_e!r}")
    if convention is PhotonDirectionConvention.PROPAGATION:
        factor = gamma_e * (1.0 - float(v_dot_direction))
    else:
        factor = gamma_e * (1.0 + float(v_dot_direction))
    return ElectronFrameRate(
        gamma_e=float(gamma_e),
        factor=float(factor),
        direction_convention=convention,
    )


def project_thomson_source_stub(
    context: ElectronFrameThomsonContext,
) -> ThomsonProjectionStub:
    """Return the non-executable projection contract stub."""
    _ = context
    return ThomsonProjectionStub()
