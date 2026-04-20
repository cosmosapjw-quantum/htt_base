"""VER2 perturbation-seed compatibility skeletons for the BASS S2 lane."""
from __future__ import annotations

from dataclasses import dataclass, field, replace
from enum import Enum

import numpy as np

from bass.hierarchy.frame_contracts import BoostOrder

__all__ = [
    "SeedConvention",
    "SeedAssignmentFrame",
    "RegularSeedDescriptor",
    "RegularSeedState",
    "SeedProjectionStub",
    "build_flrw_regular_seed_stub",
    "promote_tilted_seed_stub",
    "build_constraint_projection_stub",
]


class SeedConvention(str, Enum):
    """Declared regular-seed convention."""

    FLRW_REGULAR_ADIABATIC = "flrw_regular_adiabatic"


class SeedAssignmentFrame(str, Enum):
    """Frame where the regular seed is assigned before later projection."""

    NORMAL = "normal_frame"
    ELECTRON_IF_TILTED = "electron_frame_if_tilted"


@dataclass(frozen=True)
class RegularSeedDescriptor:
    """Metadata for the FLRW-limit regular seed contract."""

    convention: SeedConvention = SeedConvention.FLRW_REGULAR_ADIABATIC
    assignment_frame: SeedAssignmentFrame = SeedAssignmentFrame.NORMAL
    boost_order: BoostOrder = BoostOrder.LINEAR
    flrw_limit_required: bool = True
    background_anisotropy_allowed: bool = True
    constraint_projection_required: bool = True

    def __post_init__(self) -> None:
        if not self.flrw_limit_required:
            raise ValueError("seed compatibility must keep the FLRW regular limit")
        if not self.constraint_projection_required:
            raise ValueError("constraint projection after seed insertion is mandatory")


@dataclass(frozen=True)
class RegularSeedState:
    """Symbolic regular seed amplitudes plus the governing metadata."""

    amplitude: float
    delta_gamma: float
    delta_baryon: float
    delta_cdm: float
    delta_nu: float
    theta_common: float
    descriptor: RegularSeedDescriptor = field(default_factory=RegularSeedDescriptor)
    tilt_velocity: np.ndarray = field(default_factory=lambda: np.zeros(3, dtype=np.float64))

    def __post_init__(self) -> None:
        for name, value in (
            ("amplitude", self.amplitude),
            ("delta_gamma", self.delta_gamma),
            ("delta_baryon", self.delta_baryon),
            ("delta_cdm", self.delta_cdm),
            ("delta_nu", self.delta_nu),
            ("theta_common", self.theta_common),
        ):
            if not np.isfinite(value):
                raise ValueError(f"{name} must be finite, got {value!r}")
        v = np.asarray(self.tilt_velocity, dtype=np.float64)
        if v.shape != (3,):
            raise ValueError(f"tilt_velocity must have shape (3,), got {v.shape}")
        object.__setattr__(self, "tilt_velocity", v)


@dataclass(frozen=True)
class SeedProjectionStub:
    """Carry-forward hook for post-insertion constraint projection."""

    projection_ready: bool = False
    constraint_projection_required: bool = True
    reason: str = (
        "Constraint projection after seed insertion is a later executable "
        "implementation task; SK-02S2 freezes only the frame-aware hook."
    )


def build_flrw_regular_seed_stub(
    *,
    amplitude: float,
    descriptor: RegularSeedDescriptor | None = None,
) -> RegularSeedState:
    """Return a symbolic regular adiabatic seed with common-amplitude placeholders."""
    if not np.isfinite(amplitude):
        raise ValueError(f"amplitude must be finite, got {amplitude!r}")
    amp = float(amplitude)
    return RegularSeedState(
        amplitude=amp,
        delta_gamma=amp,
        delta_baryon=amp,
        delta_cdm=amp,
        delta_nu=amp,
        theta_common=amp / 3.0,
        descriptor=descriptor or RegularSeedDescriptor(),
    )


def promote_tilted_seed_stub(
    seed: RegularSeedState,
    *,
    electron_velocity: np.ndarray,
    boost_order: BoostOrder = BoostOrder.LINEAR,
) -> RegularSeedState:
    """Return the explicit tilted-seed wrapper while preserving the FLRW limit."""
    velocity = np.asarray(electron_velocity, dtype=np.float64)
    if velocity.shape != (3,):
        raise ValueError(
            f"electron_velocity must have shape (3,), got {velocity.shape}"
        )
    descriptor = replace(
        seed.descriptor,
        assignment_frame=SeedAssignmentFrame.ELECTRON_IF_TILTED,
        boost_order=boost_order,
    )
    return RegularSeedState(
        amplitude=seed.amplitude,
        delta_gamma=seed.delta_gamma,
        delta_baryon=seed.delta_baryon,
        delta_cdm=seed.delta_cdm,
        delta_nu=seed.delta_nu,
        theta_common=seed.theta_common,
        descriptor=descriptor,
        tilt_velocity=velocity,
    )


def build_constraint_projection_stub(
    seed: RegularSeedState,
) -> SeedProjectionStub:
    """Return the explicit carry-forward projection hook."""
    _ = seed
    return SeedProjectionStub()
