"""VER2 anisotropic source-propagator surfaces for the BASS S3 lane."""
from __future__ import annotations

from collections.abc import Callable, Mapping
from dataclasses import dataclass, field
from enum import Enum

import numpy as np

from bass.background.bianchi_types import StructureConstants
from bass.runtime.ver2_execution import FeatureStatus
from bass.spectrum.lowell_los import build_lowell_line_of_sight_propagator
from bass.spectrum.off_diagonal_covariance import assemble_bianchi_spectrum_covariance

__all__ = [
    "PropagatorMode",
    "ObserverFrameMetadata",
    "SourcePropagatorConfig",
    "SourcePropagator",
    "build_source_propagator",
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
class SourcePropagator:
    """Executable observer-neutral source-to-observer propagator bundle."""

    config: SourcePropagatorConfig
    transfer_bundle: Mapping[str, object]
    covariance_bundle: Mapping[str, object]
    ready: bool = True
    observer_neutral: bool = True
    mode_coupling_expected: bool = True

    def __post_init__(self) -> None:
        if not self.ready:
            raise ValueError("SourcePropagator must be ready=True")
        if not self.observer_neutral:
            raise ValueError("BASS propagators must remain observer-neutral")
        if self.config.mode is PropagatorMode.FLRW_VALIDATION and self.mode_coupling_expected:
            raise ValueError("FLRW validation mode should not advertise anisotropic mode coupling")
        transfer_T = np.asarray(self.transfer_bundle["transfer_T"], dtype=np.float64)
        transfer_E = np.asarray(self.transfer_bundle["transfer_E"], dtype=np.float64)
        transfer_B = np.asarray(self.transfer_bundle["transfer_B"], dtype=np.float64)
        if transfer_T.ndim != 3 or transfer_E.shape != transfer_T.shape or transfer_B.shape != transfer_T.shape:
            raise ValueError("transfer bundles must expose matching 3-D T/E/B arrays")
        ell = np.asarray(self.covariance_bundle["ell"], dtype=np.int64)
        if transfer_T.shape[1] != ell.size:
            raise ValueError("transfer/covariance ell dimensions must agree")


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


def build_source_propagator(
    config: SourcePropagatorConfig,
    *,
    structure: StructureConstants,
    eta_grid_mpc: np.ndarray,
    k_grid_mpc: np.ndarray,
    ell_max: int,
    visibility_fn: Callable[[float], float],
    source_builder: Callable[[float, float], Mapping[str, object]],
    limber_eta_sp_sign: str = "integrator",
    off_diagonal_strategy: str = "m_decoupled_blocks",
) -> SourcePropagator:
    """Build the executable VER2 propagator from LOS and covariance operators.

    This is a bounded research-grade path: it remains observer-neutral and
    carries no posterior/statistical semantics, but it is now fully executable
    and no longer a shell-only placeholder.
    """
    transfer_bundle = build_lowell_line_of_sight_propagator(
        structure,
        eta_grid_mpc=np.asarray(eta_grid_mpc, dtype=np.float64),
        k_grid_mpc=np.asarray(k_grid_mpc, dtype=np.float64),
        ell_max=int(ell_max),
        visibility_fn=visibility_fn,
        source_builder=source_builder,
        limber_eta_sp_sign=limber_eta_sp_sign,  # type: ignore[arg-type]
    )
    covariance_bundle = assemble_bianchi_spectrum_covariance(
        transfer_bundle=transfer_bundle,
        k_grid_mpc=np.asarray(k_grid_mpc, dtype=np.float64),
        ell_max=int(ell_max),
        off_diagonal_strategy=off_diagonal_strategy,  # type: ignore[arg-type]
    )
    return SourcePropagator(
        config=config,
        transfer_bundle=transfer_bundle,
        covariance_bundle=covariance_bundle,
        mode_coupling_expected=(config.mode is not PropagatorMode.FLRW_VALIDATION),
    )


def build_source_propagator_stub(
    config: SourcePropagatorConfig,
) -> SourcePropagatorStub:
    """Return the S3 propagator contract stub."""
    return SourcePropagatorStub(
        config=config,
        mode_coupling_expected=(config.mode is not PropagatorMode.FLRW_VALIDATION),
    )
