"""VER2 electron-frame Thomson projection for the BASS S2 lane."""
from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np

from bass.hierarchy.frame_contracts import FrameSplitMetadata, PhotonDirectionConvention
from bass.hierarchy.pstf_tensor import PSTFHierarchyState, zero_hierarchy
from bass.collision.polarization import PolarizationHierarchyState
from bass.collision.thomson_pstf import (
    EModeThomsonCollisionOperator,
    ThomsonPSTFCollisionOperator,
)
from bass.collision.tilted_eb_mixing import evaluate_tilted_polarization_eb_collision
from bass.collision.tilted_thomson_layer_b import evaluate_tilted_thomson_pstf_collision
from bass.species.tilted import TiltedSpeciesBackground

__all__ = [
    "ElectronFrameRate",
    "ElectronFrameThomsonContext",
    "ProjectedThomsonSource",
    "electron_frame_rate_factor",
    "project_thomson_source",
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
class ProjectedThomsonSource:
    """Projected Thomson collision source in the solver's PSTF basis."""

    temperature: PSTFHierarchyState
    polarization_E: PolarizationHierarchyState
    polarization_B: PSTFHierarchyState
    effective_rate: ElectronFrameRate
    frame_metadata: FrameSplitMetadata = field(default_factory=FrameSplitMetadata)
    source_ready: bool = True
    linearity_required: bool = True
    isotropic_null_mode_required: bool = True
    pure_quadrupole_response_required: bool = True

    def __post_init__(self) -> None:
        if self.temperature.L != self.polarization_E.L:
            raise ValueError(
                "temperature and E-mode towers must share the same truncation depth"
            )
        if self.temperature.L != self.polarization_B.L:
            raise ValueError(
                "temperature and B-mode towers must share the same truncation depth"
            )
        if self.frame_metadata.collision_frame != "electron_frame":
            raise ValueError("projected Thomson source must remain electron-frame owned")


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


def _effective_rate(
    *,
    context: ElectronFrameThomsonContext,
    direction: np.ndarray | None,
    tilted_electron: TiltedSpeciesBackground | None,
) -> ElectronFrameRate:
    if tilted_electron is None or tilted_electron.beta == 0.0:
        return ElectronFrameRate(
            gamma_e=1.0,
            factor=1.0,
            direction_convention=context.direction_convention,
        )
    if direction is None:
        raise ValueError("nonzero tilted_electron requires an explicit photon direction")
    direction_arr = np.asarray(direction, dtype=np.float64)
    if direction_arr.shape != (3,):
        raise ValueError(f"direction must have shape (3,), got {direction_arr.shape}")
    direction_norm = float(np.linalg.norm(direction_arr))
    if direction_norm == 0.0:
        raise ValueError("direction must be non-zero when tilted_electron is supplied")
    direction_hat = direction_arr / direction_norm
    v_vec = tilted_electron.beta * np.asarray(tilted_electron.v_hat_e, dtype=np.float64)
    return electron_frame_rate_factor(
        gamma_e=tilted_electron.gamma,
        v_dot_direction=float(np.dot(v_vec, direction_hat)),
        convention=context.direction_convention,
    )


def project_thomson_source(
    context: ElectronFrameThomsonContext,
    *,
    temperature_state: PSTFHierarchyState,
    polarization_state: PolarizationHierarchyState,
    v_b_real_sph: np.ndarray,
    Gamma_T: float,
    direction: np.ndarray | None = None,
    tilted_electron: TiltedSpeciesBackground | None = None,
    b_state: PSTFHierarchyState | None = None,
) -> ProjectedThomsonSource:
    """Project the classical electron-frame Thomson source into PSTF towers.

    Orthogonal runs reuse the established LB-4 operators directly. Tilted runs
    dispatch to the shipped Layer-B boost path rather than collapsing to an
    FLRW-only scalar shortcut.
    """
    if not np.isfinite(Gamma_T) or Gamma_T < 0.0:
        raise ValueError(f"Gamma_T must be non-negative finite, got {Gamma_T!r}")
    if context.frame_metadata.no_flrw_only_collision_shortcut is not True:
        raise ValueError("VER2 collision path forbids FLRW-only shortcuts")
    if temperature_state.L != polarization_state.L:
        raise ValueError(
            f"temperature L={temperature_state.L} must match polarization L={polarization_state.L}"
        )
    b_mode_state = zero_hierarchy(temperature_state.L) if b_state is None else b_state.copy()
    if b_mode_state.L != temperature_state.L:
        raise ValueError(
            f"b_state.L={b_mode_state.L} must match temperature L={temperature_state.L}"
        )
    rate = _effective_rate(
        context=context,
        direction=direction,
        tilted_electron=tilted_electron,
    )
    effective_gamma = float(Gamma_T) * rate.factor
    if tilted_electron is None or tilted_electron.beta == 0.0:
        t_op = ThomsonPSTFCollisionOperator()
        e_op = EModeThomsonCollisionOperator()
        temperature = t_op.evaluate_tower(
            temperature_state,
            polarization_state,
            np.asarray(v_b_real_sph, dtype=np.float64),
            effective_gamma,
        )
        polarization_E = e_op.evaluate_tower(
            polarization_state,
            np.asarray(temperature_state.tensors[2].components, dtype=np.float64),
            effective_gamma,
        )
        polarization_B = zero_hierarchy(temperature_state.L)
    else:
        temperature_tensors = []
        e_tensors = []
        b_tensors = []
        for ell in range(temperature_state.L + 1):
            temperature_tensors.append(
                evaluate_tilted_thomson_pstf_collision(
                    ell,
                    temperature_state,
                    polarization_state,
                    eta=0.0,
                    v_b_real_sph=np.asarray(v_b_real_sph, dtype=np.float64),
                    Gamma_T=effective_gamma,
                    tilted_electron=tilted_electron,
                )
            )
            e_tensor, b_tensor = evaluate_tilted_polarization_eb_collision(
                ell,
                polarization_state,
                eta=0.0,
                Pi_2_packed=np.asarray(temperature_state.tensors[2].components, dtype=np.float64),
                Gamma_T=effective_gamma,
                b_state=b_mode_state,
                tilted_electron=tilted_electron,
            )
            e_tensors.append(e_tensor)
            b_tensors.append(b_tensor)
        temperature = PSTFHierarchyState(L=temperature_state.L, tensors=temperature_tensors)
        polarization_E = PolarizationHierarchyState(
            E=PSTFHierarchyState(L=temperature_state.L, tensors=e_tensors)
        )
        polarization_B = PSTFHierarchyState(L=temperature_state.L, tensors=b_tensors)
    return ProjectedThomsonSource(
        temperature=temperature,
        polarization_E=polarization_E,
        polarization_B=polarization_B,
        effective_rate=rate,
        frame_metadata=context.frame_metadata,
    )


def project_thomson_source_stub(
    context: ElectronFrameThomsonContext,
    **kwargs,
) -> ProjectedThomsonSource:
    """Compatibility alias kept while call sites migrate to `project_thomson_source`."""
    return project_thomson_source(context, **kwargs)
