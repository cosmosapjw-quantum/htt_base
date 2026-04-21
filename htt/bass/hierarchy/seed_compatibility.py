"""VER2 perturbation-seed compatibility helpers for the BASS S2 lane."""
from __future__ import annotations

from dataclasses import dataclass, field, replace
from enum import Enum

import numpy as np

from bass.background.constraints import MatterNormalFrameState, codazzi_constraint_residual
from bass.background.geometry import TetradGeometry
from bass.background.initial_conditions import project_shear_to_codazzi
from bass.hierarchy.frame_contracts import BoostOrder

__all__ = [
    "SeedConvention",
    "SeedAssignmentFrame",
    "RegularSeedDescriptor",
    "RegularSeedState",
    "SeedConstraintProjection",
    "build_flrw_regular_seed",
    "build_flrw_regular_seed_stub",
    "promote_tilted_seed",
    "promote_tilted_seed_stub",
    "build_constraint_projection",
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
class SeedConstraintProjection:
    """Post-insertion seed projection and its residual bookkeeping."""

    projected_seed: RegularSeedState
    momentum_residual_before: np.ndarray
    momentum_residual_after: np.ndarray
    projection_mode: str
    constraint_projection_required: bool = True
    projection_ready: bool = True
    projected_sigma_ab: np.ndarray | None = None

    def __post_init__(self) -> None:
        before = np.asarray(self.momentum_residual_before, dtype=np.float64)
        after = np.asarray(self.momentum_residual_after, dtype=np.float64)
        if before.shape != (3,):
            raise ValueError(
                f"momentum_residual_before must have shape (3,), got {before.shape}"
            )
        if after.shape != (3,):
            raise ValueError(
                f"momentum_residual_after must have shape (3,), got {after.shape}"
            )
        object.__setattr__(self, "momentum_residual_before", before)
        object.__setattr__(self, "momentum_residual_after", after)
        if self.projected_sigma_ab is not None:
            sigma = np.asarray(self.projected_sigma_ab, dtype=np.float64)
            if sigma.shape != (3, 3):
                raise ValueError(
                    f"projected_sigma_ab must have shape (3,3), got {sigma.shape}"
                )
            object.__setattr__(self, "projected_sigma_ab", sigma)


def build_flrw_regular_seed(
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


def build_flrw_regular_seed_stub(
    *,
    amplitude: float,
    descriptor: RegularSeedDescriptor | None = None,
) -> RegularSeedState:
    """Compatibility alias kept while call sites migrate to `build_flrw_regular_seed`."""
    return build_flrw_regular_seed(amplitude=amplitude, descriptor=descriptor)


def promote_tilted_seed(
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


def promote_tilted_seed_stub(
    seed: RegularSeedState,
    *,
    electron_velocity: np.ndarray,
    boost_order: BoostOrder = BoostOrder.LINEAR,
) -> RegularSeedState:
    """Compatibility alias kept while call sites migrate to `promote_tilted_seed`."""
    return promote_tilted_seed(
        seed,
        electron_velocity=electron_velocity,
        boost_order=boost_order,
    )


def build_constraint_projection(
    seed: RegularSeedState,
    *,
    geometry: TetradGeometry | None = None,
    sigma_ab: np.ndarray | None = None,
    kappa: float = 1.0,
    atol: float = 1.0e-10,
) -> SeedConstraintProjection:
    """Project a seeded state onto the currently available normal-frame constraint surface.

    When geometry and a shear guess are available, this dispatches to the real
    S1 Codazzi projector. Otherwise it applies a first-pass boost-consistency
    reduction on the symbolic seed state so the reduced contract remains finite
    and recovers the orthogonal seed as `v_e -> 0`.
    """
    tilt = np.asarray(seed.tilt_velocity, dtype=np.float64)
    beta_sq = float(np.dot(tilt, tilt))
    if beta_sq >= 1.0:
        raise ValueError(f"tilt velocity must satisfy |v| < 1, got |v|^2={beta_sq!r}")
    gamma = 1.0 / np.sqrt(max(1.0 - beta_sq, 1.0e-30))
    residual_before = float(seed.theta_common) * tilt
    theta_projected = float(seed.theta_common) / gamma
    projected_seed = RegularSeedState(
        amplitude=seed.amplitude,
        delta_gamma=seed.delta_gamma,
        delta_baryon=seed.delta_baryon,
        delta_cdm=seed.delta_cdm,
        delta_nu=seed.delta_nu,
        theta_common=theta_projected,
        descriptor=seed.descriptor,
        tilt_velocity=tilt,
    )
    residual_after = float(projected_seed.theta_common) * tilt
    if geometry is None or sigma_ab is None:
        return SeedConstraintProjection(
            projected_seed=projected_seed,
            momentum_residual_before=residual_before,
            momentum_residual_after=residual_after,
            projection_mode="boost_consistency_first_pass",
        )

    sigma_guess = np.asarray(sigma_ab, dtype=np.float64)
    matter = MatterNormalFrameState(
        rho=0.0,
        p=0.0,
        q=residual_after,
    )
    projected_sigma, _meta = project_shear_to_codazzi(
        sigma_ab=sigma_guess,
        geometry=geometry,
        target_q=matter.q,
        kappa=kappa,
        atol=atol,
    )
    codazzi_before = codazzi_constraint_residual(
        sigma_guess,
        MatterNormalFrameState(rho=0.0, p=0.0, q=residual_before),
        geometry,
        kappa=kappa,
    )
    codazzi_after = codazzi_constraint_residual(
        projected_sigma,
        matter,
        geometry,
        kappa=kappa,
    )
    return SeedConstraintProjection(
        projected_seed=projected_seed,
        momentum_residual_before=codazzi_before,
        momentum_residual_after=codazzi_after,
        projection_mode="background_codazzi_project",
        projected_sigma_ab=projected_sigma,
    )


def build_constraint_projection_stub(
    seed: RegularSeedState,
    *,
    geometry: TetradGeometry | None = None,
    sigma_ab: np.ndarray | None = None,
    kappa: float = 1.0,
    atol: float = 1.0e-10,
) -> SeedConstraintProjection:
    """Compatibility alias kept while call sites migrate to `build_constraint_projection`."""
    return build_constraint_projection(
        seed,
        geometry=geometry,
        sigma_ab=sigma_ab,
        kappa=kappa,
        atol=atol,
    )
