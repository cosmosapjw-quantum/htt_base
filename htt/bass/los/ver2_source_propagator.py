"""VER2 anisotropic source-propagator skeletons for the BASS S3 lane."""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum

from bass.runtime.ver2_execution import FeatureStatus

__all__ = [
    "PropagatorMode",
    "ObserverFrameMetadata",
    "SourcePropagatorConfig",
    "SourcePropagatorStub",
    "build_source_propagator_stub",
]


class PropagatorMode(str, Enum):
    """Declared source-to-observer propagator mode."""

    ANISOTROPIC_FORWARD = "anisotropic_forward"
    ANISOTROPIC_ADJOINT = "anisotropic_adjoint"
    FLRW_VALIDATION = "flrw_validation"


@dataclass(frozen=True)
class ObserverFrameMetadata:
    """Observer-frame and convention metadata for neutral exports."""

    observer_frame: str = "normal_tetrad"
    screen_basis_convention: str = "explicit_screen_basis"
    harmonic_basis: str = "spin_weighted_or_pstf_explicit"
    eb_sign_convention: str = "explicit_solver_state"

    def __post_init__(self) -> None:
        if not self.observer_frame:
            raise ValueError("observer_frame must be non-empty")
        if not self.screen_basis_convention:
            raise ValueError("screen_basis_convention must be non-empty")
        if not self.harmonic_basis:
            raise ValueError("harmonic_basis must be non-empty")
        if not self.eb_sign_convention:
            raise ValueError("eb_sign_convention must be non-empty")


@dataclass(frozen=True)
class SourcePropagatorConfig:
    """Anisotropic propagator policy and metadata."""

    mode: PropagatorMode
    temperature_transport: FeatureStatus
    polarization_rotation: FeatureStatus
    flrw_validation_only: bool = False
    kernel_family: str = "anisotropic_green_function"
    carries_statistics: bool = False
    observer_frame: ObserverFrameMetadata = field(default_factory=ObserverFrameMetadata)

    def __post_init__(self) -> None:
        if self.carries_statistics:
            raise ValueError("BASS propagators must remain observer-neutral")
        if self.mode is PropagatorMode.FLRW_VALIDATION:
            if not self.flrw_validation_only:
                raise ValueError(
                    "FLRW validation mode must set flrw_validation_only=True"
                )
            if self.kernel_family != "flrw_scalar_validation":
                raise ValueError(
                    "FLRW validation mode must use the explicit validation kernel family"
                )
        else:
            if self.flrw_validation_only:
                raise ValueError(
                    "FLRW scalar kernels are allowed only in explicit validation mode"
                )
            if self.kernel_family == "flrw_scalar_validation":
                raise ValueError(
                    "production propagators may not use the FLRW validation kernel family"
                )


@dataclass(frozen=True)
class SourcePropagatorStub:
    """Non-executable propagator shell for later runtime binding."""

    config: SourcePropagatorConfig
    ready: bool = False
    observer_neutral: bool = True
    mode_coupling_expected: bool = True
    reason: str = (
        "The S3 packet freezes anisotropic source-to-observer metadata only; "
        "live propagator numerics remain a later implementation task."
    )

    def __post_init__(self) -> None:
        if not self.observer_neutral:
            raise ValueError("propagator shell must remain observer-neutral")
        if self.config.mode is PropagatorMode.FLRW_VALIDATION and self.mode_coupling_expected:
            raise ValueError("FLRW validation mode should not advertise anisotropic mode coupling")


def build_source_propagator_stub(
    config: SourcePropagatorConfig,
) -> SourcePropagatorStub:
    """Return the S3 propagator contract stub."""
    return SourcePropagatorStub(
        config=config,
        mode_coupling_expected=(config.mode is not PropagatorMode.FLRW_VALIDATION),
    )
