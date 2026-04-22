"""VER2 electron-frame Thomson projection for the BASS S2 lane."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Mapping

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
from bass.validation import GateBundle, make_gate_bundle

__all__ = [
    "ElectronFrameRate",
    "ElectronFrameThomsonContext",
    "ProjectedThomsonSource",
    "ExactThomsonSource",
    "SourceTerms",
    "electron_frame_rate_factor",
    "exact_thomson_source",
    "exact_thomson_gate_bundle",
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


@dataclass(frozen=True)
class ExactThomsonSource:
    """ver3 wrapper exposing scalar/directional Thomson source ownership."""

    projected: ProjectedThomsonSource
    scalar_monopole_input: float
    directional_temperature_norm: float
    polarization_quadrupole_norm: float
    effective_opacity: float
    source_split: str = "scalar_monopole_vs_directional_tensor"
    opacity_contract: str = "electron_frame_tilt_modulated"

    def __post_init__(self) -> None:
        if self.effective_opacity < 0.0 or not np.isfinite(self.effective_opacity):
            raise ValueError("effective_opacity must be non-negative finite")
        if self.source_split != "scalar_monopole_vs_directional_tensor":
            raise ValueError("exact Thomson split contract changed unexpectedly")
        if self.opacity_contract != "electron_frame_tilt_modulated":
            raise ValueError("exact Thomson opacity contract changed unexpectedly")


@dataclass(frozen=True)
class SourceTerms:
    """Document-level directional Thomson source terms."""

    dI_dir: np.ndarray
    dP_dir: np.ndarray
    effective_opacity: float
    direction_convention: PhotonDirectionConvention
    metadata: Mapping[str, object] = field(default_factory=dict)

    def __post_init__(self) -> None:
        dI = np.asarray(self.dI_dir, dtype=np.float64)
        dP = np.asarray(self.dP_dir, dtype=np.float64)
        if dI.shape != dP.shape:
            raise ValueError(
                f"dI_dir and dP_dir must share shape, got {dI.shape} and {dP.shape}"
            )
        if not np.isfinite(self.effective_opacity) or self.effective_opacity < 0.0:
            raise ValueError("effective_opacity must be non-negative finite")
        object.__setattr__(self, "dI_dir", dI)
        object.__setattr__(self, "dP_dir", dP)
        object.__setattr__(self, "metadata", dict(self.metadata))


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


def _directional_exact_thomson_source(
    e_dir: np.ndarray,
    I_dir: np.ndarray,
    I0: float | np.ndarray,
    P_dir: np.ndarray,
    I2: float | np.ndarray,
    E2_pol: float | np.ndarray,
    opacity_data: Mapping[str, object],
) -> SourceTerms:
    if not isinstance(opacity_data, Mapping):
        raise ValueError("opacity_data must be a mapping")
    direction = np.asarray(e_dir, dtype=np.float64)
    if direction.shape != (3,):
        raise ValueError(f"e_dir must have shape (3,), got {direction.shape}")
    direction_norm = float(np.linalg.norm(direction))
    if direction_norm == 0.0:
        raise ValueError("e_dir must be non-zero")
    direction_hat = direction / direction_norm
    I_arr = np.asarray(I_dir, dtype=np.float64)
    P_arr = np.asarray(P_dir, dtype=np.float64)
    I0_arr, I2_arr, E2_arr = np.broadcast_arrays(
        np.asarray(I0, dtype=np.float64),
        np.asarray(I2, dtype=np.float64),
        np.asarray(E2_pol, dtype=np.float64),
    )
    if I_arr.shape != P_arr.shape:
        raise ValueError(f"I_dir and P_dir must share shape, got {I_arr.shape} and {P_arr.shape}")
    if I_arr.shape != I0_arr.shape:
        I0_arr = np.broadcast_to(I0_arr, I_arr.shape)
        I2_arr = np.broadcast_to(I2_arr, I_arr.shape)
        E2_arr = np.broadcast_to(E2_arr, I_arr.shape)
    convention = PhotonDirectionConvention(
        opacity_data.get("direction_convention", PhotonDirectionConvention.PROPAGATION)
    )
    gamma_e = float(opacity_data.get("gamma_e", 1.0))
    v_dot_direction = float(opacity_data.get("v_dot_direction", 0.0))
    rate = electron_frame_rate_factor(
        gamma_e=gamma_e,
        v_dot_direction=v_dot_direction,
        convention=convention,
    )
    base_opacity = float(opacity_data.get("Gamma_T", 0.0))
    if not np.isfinite(base_opacity) or base_opacity < 0.0:
        raise ValueError("opacity_data['Gamma_T'] must be non-negative finite")
    effective_opacity = base_opacity * rate.factor
    dI_dir = effective_opacity * ((I0_arr + I2_arr) - I_arr)
    dP_dir = effective_opacity * (E2_arr - P_arr)
    return SourceTerms(
        dI_dir=dI_dir,
        dP_dir=dP_dir,
        effective_opacity=effective_opacity,
        direction_convention=convention,
        metadata={
            "direction_norm": direction_norm,
            "direction_hat": direction_hat.tolist(),
            "scalar_monopole_input": float(np.mean(I0_arr)),
            "quadrupole_input_norm": float(np.linalg.norm(I2_arr)),
            "polarization_source_norm": float(np.linalg.norm(E2_arr)),
            "source_split": "scalar_monopole_vs_directional_tensor",
        },
    )


def exact_thomson_source(
    context: ElectronFrameThomsonContext | np.ndarray,
    *args,
    **kwargs,
) -> ExactThomsonSource | SourceTerms:
    """ver3 exact Thomson wrapper with explicit scalar/directional separation."""

    if isinstance(context, ElectronFrameThomsonContext):
        temperature_state = kwargs["temperature_state"]
        polarization_state = kwargs["polarization_state"]
        v_b_real_sph = kwargs["v_b_real_sph"]
        Gamma_T = kwargs["Gamma_T"]
        direction = kwargs.get("direction")
        tilted_electron = kwargs.get("tilted_electron")
        b_state = kwargs.get("b_state")
        projected = project_thomson_source(
            context,
            temperature_state=temperature_state,
            polarization_state=polarization_state,
            v_b_real_sph=v_b_real_sph,
            Gamma_T=Gamma_T,
            direction=direction,
            tilted_electron=tilted_electron,
            b_state=b_state,
        )
        scalar_monopole_input = float(temperature_state.tensors[0].components[0])
        directional_norm = 0.0
        for ell in range(1, temperature_state.L + 1):
            directional_norm += float(
                np.dot(
                    temperature_state.tensors[ell].components,
                    temperature_state.tensors[ell].components,
                )
            )
        polarization_quadrupole_norm = float(
            np.linalg.norm(polarization_state.E.tensors[2].components)
        )
        return ExactThomsonSource(
            projected=projected,
            scalar_monopole_input=scalar_monopole_input,
            directional_temperature_norm=float(np.sqrt(directional_norm)),
            polarization_quadrupole_norm=polarization_quadrupole_norm,
            effective_opacity=float(Gamma_T) * projected.effective_rate.factor,
        )

    if len(args) != 6:
        raise TypeError(
            "directional exact_thomson_source expects "
            "(e_dir, I_dir, I0, P_dir, I2, E2_pol, opacity_data)"
        )
    return _directional_exact_thomson_source(
        np.asarray(context, dtype=np.float64),
        args[0],
        args[1],
        args[2],
        args[3],
        args[4],
        args[5],
    )


def exact_thomson_gate_bundle(
    source: ExactThomsonSource,
    *,
    family: str = "unspecified",
    branch: str = "orthogonal",
    backend: str = "electron_frame_tilt_modulated",
    truncation: Mapping[str, object] | None = None,
) -> GateBundle:
    """Emit the machine-readable PR-06 exact-Thomson gate bundle."""

    return make_gate_bundle(
        "exact_thomson_gate",
        family=family,
        branch=branch,
        backend=backend,
        truncation={} if truncation is None else dict(truncation),
        residual_summary={
            "scalar_monopole_input": float(source.scalar_monopole_input),
            "directional_temperature_norm": float(source.directional_temperature_norm),
            "polarization_quadrupole_norm": float(source.polarization_quadrupole_norm),
            "effective_opacity": float(source.effective_opacity),
        },
        known_limit_checks={
            "isotropic_null_mode_required": source.projected.isotropic_null_mode_required,
            "pure_quadrupole_response_required": source.projected.pure_quadrupole_response_required,
            "linearity_required": source.projected.linearity_required,
        },
        forbidden_shortcut_checks={
            "no_flrw_only_collision_shortcut": (
                source.projected.frame_metadata.no_flrw_only_collision_shortcut
            ),
            "electron_frame_owned": (
                source.projected.frame_metadata.collision_frame == "electron_frame"
            ),
        },
        metadata={
            "source_split": source.source_split,
            "opacity_contract": source.opacity_contract,
        },
        passed=bool(np.isfinite(source.effective_opacity) and source.effective_opacity >= 0.0),
        opened_claim="exact collision contract frozen",
    )


def project_thomson_source_stub(
    context: ElectronFrameThomsonContext,
    **kwargs,
) -> ProjectedThomsonSource:
    """Compatibility alias kept while call sites migrate to `project_thomson_source`."""
    return project_thomson_source(context, **kwargs)
