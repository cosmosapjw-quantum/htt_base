"""VER2 native Tier-B integrator owned by the S1/S2 BASS stack.

This module closes the main BF-01B-HCORE debt: the executable Tier-B
runtime no longer has to call the shipped Lowell integrator as the
hidden physics core. The production route here is:

1. S1 background evolution is solved first and frozen on its own grid.
2. That history is adapted into the `bg_table` / `tetrad_state`
   contract expected by the hierarchy RHS.
3. S2 photon transport, projected Thomson sourcing, and visibility
   ownership drive the radiation-sector ODE directly.

The legacy Lowell integrator remains available as a compatibility path,
but it is no longer the production owner of the VER2 Tier-B route.
"""
from __future__ import annotations

from dataclasses import dataclass
from collections.abc import Callable, Mapping
from typing import Optional

import numpy as np
from scipy.integrate import solve_ivp
from scipy.sparse import csc_matrix
from scipy.sparse.linalg import splu

from bass.background.evolution import BackgroundEvolutionResult
from bass.collision.electron_frame import (
    ExactThomsonSource,
    ElectronFrameThomsonContext,
    ProjectedThomsonSource,
    exact_thomson_source,
    project_thomson_source,
)
from bass.collision.polarization import (
    E_MODE_ELL2_SELF_COEFF,
    E_MODE_ELL2_TEMPERATURE_COEFF,
    PolarizationHierarchyState,
    zero_polarization_hierarchy,
)
from bass.collision.thomson_pstf import (
    THOMSON_ELL2_POLARIZATION_COEFF,
    THOMSON_ELL2_SELF_COEFF,
)
from bass.closure.stiff_closure import (
    QuadrupoleStartupState,
    StartupGateDecision,
    decide_startup_gate,
    quadrupole_startup_from_sources,
)
from bass.closure.quadrupole_tca import solve_tca_closure
from bass.hierarchy.collision_interface import CollisionOperator, ZeroCollisionOperator
from bass.hierarchy.closure import TCAClosure, build_default_closure
from bass.hierarchy.hierarchy_rhs import (
    hierarchy_rhs_neutrino_from_state,
    hierarchy_rhs_photon_from_state,
    sample_hierarchy_background,
)
from bass.hierarchy.integrator import (
    C_KMS,
    IntegratorConfig,
    IntegrationResult,
    _ell2_m0_slot_offset,
)
from bass.hierarchy.pstf_tensor import PSTFHierarchyState, PSTFTensor, pack_hierarchy, unpack_hierarchy, zero_hierarchy
from bass.hierarchy.ver3_layout_protocol import (
    ReducedJointAffineOperator,
    ReducedLocalAffineOperator,
    build_reduced_joint_affine_operator,
    build_reduced_local_affine_operator,
    build_hierarchy_layout,
    flatten,
)
from bass.hierarchy.seed_compatibility import (
    PackedRegularSeedInjection,
    SeedConstraintProjection,
    project_packed_regular_seed,
)
from bass.hierarchy.boost_kernel import is_axis_aligned
from bass.los.family_backend_protocol import FamilyBackend, SeedPack, SeedRequest
from bass.perturbation.baryon_fluid import (
    BaryonFluidState,
    BaryonParameters,
    SymmetryAxis,
    baryon_continuity_rhs,
    baryon_euler_rhs,
)
from bass.perturbation.cdm_fluid import (
    CDMFluidState,
    CDMParameters,
    cdm_continuity_rhs,
    cdm_euler_rhs,
)
from bass.perturbation.regular_adiabatic_ic import (
    make_camb_regular_adiabatic_seed,
    pack_regular_adiabatic_seed_from_formulae,
    regular_adiabatic_formulae,
    unpack_camb_regular_adiabatic_seed,
)
from bass.perturbation.tilted_seed_rule import apply_tilted_boost_seed_rule
from bass.runtime.canonical_decision import CanonicalDecision
from bass.species.base import SpeciesLabel
from bass.species.registry import SpeciesBackgroundRegistry
from bass.species.tilted import TiltedSpeciesBackground, rapidity_to_velocity
from bass.ver3_contracts import BackgroundState, background_interpolator

__all__ = [
    "Ver2TierBIntegrator",
    "NativeTierBRestartState",
]


_SIGMA_PLUS_BASIS = np.diag([-2.0, 1.0, 1.0]) / np.sqrt(6.0)
_SIGMA_MINUS_BASIS = np.diag([0.0, 1.0, -1.0]) / np.sqrt(2.0)
_ZERO_COLLISION = ZeroCollisionOperator()
_BARYON_LOCAL_DOF = 4
_CDM_LOCAL_DOF = 2
_LOCAL_MATTER_DOF = _BARYON_LOCAL_DOF + _CDM_LOCAL_DOF
_SOURCE_LOCAL_DOF = 3
_PRIMARY_LOCAL_DOF = _LOCAL_MATTER_DOF + _SOURCE_LOCAL_DOF
_ROS2_GAMMA = 1.0 + 1.0 / np.sqrt(2.0)
_ROS2_A21 = 1.0 / _ROS2_GAMMA
_ROS2_C21 = -2.0 / _ROS2_GAMMA
_ROS2_M1 = 3.0 / (2.0 * _ROS2_GAMMA)
_ROS2_M2 = 1.0 / (2.0 * _ROS2_GAMMA)


def _tower_size(L_max: int) -> int:
    return (int(L_max) + 1) ** 2


def _radiation_state_size(L_max: int) -> int:
    return 4 * _tower_size(L_max) + _PRIMARY_LOCAL_DOF


def _interp_scalar(eta_grid: np.ndarray, values: np.ndarray, eta: float) -> float:
    return float(np.interp(float(eta), eta_grid, np.asarray(values, dtype=np.float64)))


def _interp_matrix(eta_grid: np.ndarray, values: np.ndarray, eta: float) -> np.ndarray:
    arr = np.asarray(values, dtype=np.float64)
    return np.array(
        [
            [_interp_scalar(eta_grid, arr[:, i, j], eta) for j in range(arr.shape[2])]
            for i in range(arr.shape[1])
        ],
        dtype=np.float64,
    )


class _BackgroundTableAdapter:
    """Minimal `FLRWBackgroundTable`-like adapter backed by S1 history."""

    def __init__(self, background_interp) -> None:
        self._eta = np.asarray(background_interp.eta_grid, dtype=np.float64)
        self._a = np.array(
            [float(np.exp(state.alpha)) for state in background_interp.states],
            dtype=np.float64,
        )
        self._H = np.array(
            [float(state.theta) / 3.0 for state in background_interp.states],
            dtype=np.float64,
        )

    def interp_a(self, eta: float | np.ndarray) -> float | np.ndarray:
        eta_arr = np.asarray(eta, dtype=np.float64)
        out = np.interp(eta_arr, self._eta, self._a)
        if np.ndim(eta_arr) == 0:
            return float(out)
        return np.asarray(out, dtype=np.float64)

    def interp_Theta(self, eta: float | np.ndarray) -> float | np.ndarray:
        eta_arr = np.asarray(eta, dtype=np.float64)
        out = np.interp(eta_arr, self._eta, 3.0 * self._H)
        if np.ndim(eta_arr) == 0:
            return float(out)
        return np.asarray(out, dtype=np.float64)

    def interp_calH(self, eta: float | np.ndarray) -> float | np.ndarray:
        eta_arr = np.asarray(eta, dtype=np.float64)
        out = np.interp(eta_arr, self._eta, self._a * self._H / C_KMS)
        if np.ndim(eta_arr) == 0:
            return float(out)
        return np.asarray(out, dtype=np.float64)


class _TetradStateAdapter:
    """Minimal tetrad-state adapter backed by S1 history.

    `hierarchy_rhs_photon` expects conformal shear `Σ_ab = a σ_ab`.
    `BackgroundEvolutionResult.sigma_tensor` stores the proper-time
    shear, so we convert here once.
    """

    def __init__(self, background_interp, ricci_pstf: np.ndarray) -> None:
        eta = np.asarray(background_interp.eta_grid, dtype=np.float64)
        a = np.array(
            [float(np.exp(state.alpha)) for state in background_interp.states],
            dtype=np.float64,
        )
        sigma = np.stack(
            [np.asarray(state.sigma_AB, dtype=np.float64) for state in background_interp.states],
            axis=0,
        )
        ricci = np.asarray(ricci_pstf, dtype=np.float64)
        self.eta = eta
        self.sigma_tensor = sigma * a[:, None, None]
        self.aniso_3_curvature = (
            None
            if not np.any(ricci)
            else ricci
        )


def _proper_time_grid(background_monitor: BackgroundEvolutionResult) -> np.ndarray:
    N = np.asarray(background_monitor.N, dtype=np.float64)
    H = np.maximum(np.asarray(background_monitor.H, dtype=np.float64), 1.0e-30)
    t = np.zeros_like(N)
    if N.size > 1:
        dN = np.diff(N)
        dt_dN = 1.0 / H
        t[1:] = np.cumsum(0.5 * (dt_dN[:-1] + dt_dN[1:]) * dN)
    return t


def _build_background_interpolator(
    background_monitor: BackgroundEvolutionResult,
    *,
    backend: FamilyBackend,
):
    t_grid = _proper_time_grid(background_monitor)
    states = tuple(
        BackgroundState(
            t=float(t_grid[i]),
            alpha=float(np.log(max(background_monitor.a[i], 1.0e-30))),
            gamma_AB=np.eye(3, dtype=np.float64),
            theta=3.0 * float(background_monitor.H[i]),
            sigma_AB=np.asarray(background_monitor.sigma_tensor[i], dtype=np.float64),
            family_spec=backend.family_spec,
            species_hat={
                "rho": float(background_monitor.rho[i]),
                "p": float(background_monitor.p[i]),
                "q": np.asarray(background_monitor.q[i], dtype=np.float64),
                "pi": np.asarray(background_monitor.pi[i], dtype=np.float64),
            },
            species_tilt={
                "rapidity": float(background_monitor.tilt_rapidity[i]),
                "velocity": np.asarray(background_monitor.tilt_velocity[i], dtype=np.float64),
            },
            metadata={
                "branch": str(background_monitor.branch),
                "matter_model_tag": str(background_monitor.matter_model_tag),
                "eta": float(background_monitor.eta[i]),
            },
        )
        for i in range(len(background_monitor.eta))
    )
    return background_interpolator(t_grid, states)


def _sigma_pm_from_conformal_sigma(sigma_ab: np.ndarray) -> tuple[float, float]:
    sigma = np.asarray(sigma_ab, dtype=np.float64)
    return (
        float(np.sum(sigma * _SIGMA_PLUS_BASIS)),
        float(np.sum(sigma * _SIGMA_MINUS_BASIS)),
    )


def _resolved_gamma_t(
    *,
    eta: float,
    direction: np.ndarray,
    visibility_source,
    config: IntegratorConfig,
) -> float:
    if config.gamma_T_override is None:
        return float(visibility_source.Gamma_T(float(eta), np.asarray(direction, dtype=np.float64)))
    boost = float(visibility_source.visibility.boost_factor(float(eta), np.asarray(direction, dtype=np.float64)))
    return float(config.gamma_T_override(float(eta))) * boost


def _electron_velocity_real_sph_from_baryon_row(row: np.ndarray) -> np.ndarray:
    baryon_row = np.asarray(row, dtype=np.float64)
    if baryon_row.shape[0] < 3:
        raise ValueError("baryon local matter row must contain v_e in slot 2")
    return np.array([0.0, float(baryon_row[2]), 0.0], dtype=np.float64)


def _interp_electron_velocity_real_sph(
    *,
    eta: float,
    eta_grid: np.ndarray,
    baryon_history: np.ndarray,
) -> np.ndarray:
    history = np.asarray(baryon_history, dtype=np.float64)
    if history.ndim != 2 or history.shape[1] < 3:
        raise ValueError("baryon_history must have shape (n_samples, >=3)")
    v_e = _interp_scalar(np.asarray(eta_grid, dtype=np.float64), history[:, 2], float(eta))
    return np.array([0.0, float(v_e), 0.0], dtype=np.float64)


def _theta_1_from_temperature_state(state: PSTFHierarchyState) -> float:
    if state.L < 1:
        return 0.0
    return float(state.tensors[1].components[1])


def _tilted_electron(
    *,
    species: SpeciesBackgroundRegistry,
    config: IntegratorConfig,
) -> TiltedSpeciesBackground | None:
    if abs(float(config.tilt_rapidity)) == 0.0:
        return None
    return TiltedSpeciesBackground.from_rapidity(
        base=species[SpeciesLabel.BARYON],
        rapidity=float(config.tilt_rapidity),
        v_hat_e=tuple(float(x) for x in config.tilt_direction),
    )


@dataclass
class _ProjectedCollisionAux:
    eta: float
    temperature_state: PSTFHierarchyState
    polarization_state: PolarizationHierarchyState
    Gamma_T: float
    direction: np.ndarray
    tilted_electron: TiltedSpeciesBackground | None
    v_b_real_sph: np.ndarray
    b_state: PSTFHierarchyState
    projected_source: ProjectedThomsonSource | None = None
    exact_source: ExactThomsonSource | None = None

    def get_source(self) -> ProjectedThomsonSource:
        if self.projected_source is None:
            self.projected_source = project_thomson_source(
                ElectronFrameThomsonContext(),
                temperature_state=self.temperature_state,
                polarization_state=self.polarization_state,
                v_b_real_sph=np.asarray(self.v_b_real_sph, dtype=np.float64),
                Gamma_T=float(self.Gamma_T),
                direction=np.asarray(self.direction, dtype=np.float64),
                tilted_electron=self.tilted_electron,
                b_state=self.b_state,
            )
        return self.projected_source

    def get_exact_source(self) -> ExactThomsonSource:
        if self.exact_source is None:
            self.exact_source = exact_thomson_source(
                ElectronFrameThomsonContext(),
                temperature_state=self.temperature_state,
                polarization_state=self.polarization_state,
                v_b_real_sph=np.asarray(self.v_b_real_sph, dtype=np.float64),
                Gamma_T=float(self.Gamma_T),
                direction=np.asarray(self.direction, dtype=np.float64),
                tilted_electron=self.tilted_electron,
                b_state=self.b_state,
            )
            if self.projected_source is None:
                self.projected_source = self.exact_source.projected
        assert self.exact_source is not None
        return self.exact_source


class _TemperatureProjectedCollision(CollisionOperator):
    def evaluate(
        self,
        ell: int,
        state: PSTFHierarchyState,
        aux: Optional[object] = None,
    ) -> PSTFTensor:
        del state
        if not isinstance(aux, _ProjectedCollisionAux):
            raise TypeError("temperature collision requires _ProjectedCollisionAux")
        return aux.get_source().temperature.tensors[ell]


class _EProjectedCollision(CollisionOperator):
    def evaluate(
        self,
        ell: int,
        state: PSTFHierarchyState,
        aux: Optional[object] = None,
    ) -> PSTFTensor:
        del state
        if not isinstance(aux, _ProjectedCollisionAux):
            raise TypeError("E-mode collision requires _ProjectedCollisionAux")
        return aux.get_source().polarization_E.E.tensors[ell]


class _BProjectedCollision(CollisionOperator):
    def evaluate(
        self,
        ell: int,
        state: PSTFHierarchyState,
        aux: Optional[object] = None,
    ) -> PSTFTensor:
        del state
        if not isinstance(aux, _ProjectedCollisionAux):
            raise TypeError("B-mode collision requires _ProjectedCollisionAux")
        return aux.get_source().polarization_B.tensors[ell]


@dataclass(frozen=True)
class _SeededInitialState:
    photon_T: PSTFHierarchyState
    photon_E: PolarizationHierarchyState
    neutrino_tower: PSTFHierarchyState
    startup_gate: StartupGateDecision
    seed_projection: SeedConstraintProjection
    startup_state: QuadrupoleStartupState | None
    seed_k_comoving: float
    seed_injection_mode: str
    velocity_scale: float
    seed_pack: SeedPack
    matter_seed_observables: dict[str, float]

    def __post_init__(self) -> None:
        if self.neutrino_tower.L != self.photon_T.L:
            raise ValueError(
                f"neutrino_tower L={self.neutrino_tower.L} must match photon_T L={self.photon_T.L}"
            )


@dataclass(frozen=True)
class _LocalMatterHistory:
    eta: np.ndarray
    baryon_history: np.ndarray
    cdm_history: np.ndarray
    baryon_labels: tuple[str, ...]
    cdm_labels: tuple[str, ...]
    metadata: dict[str, object]

    def __post_init__(self) -> None:
        object.__setattr__(self, "eta", np.asarray(self.eta, dtype=np.float64))
        object.__setattr__(self, "baryon_history", np.asarray(self.baryon_history, dtype=np.float64))
        object.__setattr__(self, "cdm_history", np.asarray(self.cdm_history, dtype=np.float64))
        object.__setattr__(self, "baryon_labels", tuple(self.baryon_labels))
        object.__setattr__(self, "cdm_labels", tuple(self.cdm_labels))
        object.__setattr__(self, "metadata", dict(self.metadata))


@dataclass(frozen=True)
class _CoupledAuxiliarySectorHistory:
    eta: np.ndarray
    photon_B_history: np.ndarray
    baryon_history: np.ndarray
    cdm_history: np.ndarray
    baryon_labels: tuple[str, ...]
    cdm_labels: tuple[str, ...]
    metadata: dict[str, object]

    def __post_init__(self) -> None:
        object.__setattr__(self, "eta", np.asarray(self.eta, dtype=np.float64))
        object.__setattr__(self, "photon_B_history", np.asarray(self.photon_B_history, dtype=np.float64))
        object.__setattr__(self, "baryon_history", np.asarray(self.baryon_history, dtype=np.float64))
        object.__setattr__(self, "cdm_history", np.asarray(self.cdm_history, dtype=np.float64))
        object.__setattr__(self, "baryon_labels", tuple(self.baryon_labels))
        object.__setattr__(self, "cdm_labels", tuple(self.cdm_labels))
        object.__setattr__(self, "metadata", dict(self.metadata))


@dataclass(frozen=True)
class _LayoutAuxiliaryHistoryBundle:
    eta: np.ndarray
    source_history: np.ndarray
    source_history_by_mode_label: dict[str, np.ndarray]
    layout_state_history: np.ndarray
    coupled_sector_history: _CoupledAuxiliarySectorHistory
    metadata: dict[str, object]

    def __post_init__(self) -> None:
        object.__setattr__(self, "eta", np.asarray(self.eta, dtype=np.float64))
        object.__setattr__(self, "source_history", np.asarray(self.source_history, dtype=np.float64))
        object.__setattr__(
            self,
            "source_history_by_mode_label",
            {
                str(key): np.asarray(value, dtype=np.float64)
                for key, value in dict(self.source_history_by_mode_label).items()
            },
        )
        object.__setattr__(self, "layout_state_history", np.asarray(self.layout_state_history, dtype=np.float64))
        object.__setattr__(self, "coupled_sector_history", self.coupled_sector_history)
        object.__setattr__(self, "metadata", dict(self.metadata))


@dataclass(frozen=True)
class _RuntimeLayoutProjectionBundle:
    mode_ops: object
    layout: object
    covered_mode_label: str
    auxiliary_history_bundle: _LayoutAuxiliaryHistoryBundle
    canonical_projection: object
    metadata: dict[str, object]

    def __post_init__(self) -> None:
        object.__setattr__(self, "covered_mode_label", str(self.covered_mode_label))
        object.__setattr__(self, "metadata", dict(self.metadata))


@dataclass(frozen=True)
class _RuntimeTraceProducts:
    geodesic_probe: object
    gamma_t_probe: float
    thomson_probe: object
    layout_projection: _RuntimeLayoutProjectionBundle
    metadata: dict[str, object]

    def __post_init__(self) -> None:
        object.__setattr__(self, "gamma_t_probe", float(self.gamma_t_probe))
        object.__setattr__(self, "metadata", dict(self.metadata))


@dataclass(frozen=True)
class _RuntimeExecutionTraceBundle:
    background_monitor: object
    startup_gate: object
    startup_state: object
    seed_projection: object
    seed_pack: object
    visibility_source: object
    runtime_trace_products: _RuntimeTraceProducts
    metadata: dict[str, object]

    def __post_init__(self) -> None:
        object.__setattr__(self, "metadata", dict(self.metadata))

    @property
    def geodesic_probe(self):
        return self.runtime_trace_products.geodesic_probe

    @property
    def gamma_t_probe(self) -> float:
        return float(self.runtime_trace_products.gamma_t_probe)

    @property
    def thomson_probe(self):
        return self.runtime_trace_products.thomson_probe

    @property
    def layout_projection(self) -> _RuntimeLayoutProjectionBundle:
        return self.runtime_trace_products.layout_projection

    @property
    def canonical_projection(self):
        return self.runtime_trace_products.layout_projection.canonical_projection

    @property
    def mode_ops(self):
        return self.runtime_trace_products.layout_projection.mode_ops


@dataclass(frozen=True)
class NativeTierBRestartState:
    """Checkpoint-backed restart state for the native Tier-B integrator."""

    step_index: int
    eta_restart: float
    state_vector: np.ndarray
    eta_prefix: np.ndarray
    photon_T_prefix: np.ndarray
    photon_E_prefix: np.ndarray
    photon_B_prefix: np.ndarray
    neutrino_tower_prefix: np.ndarray
    baryon_local_prefix: np.ndarray
    cdm_local_prefix: np.ndarray
    source_local_prefix: np.ndarray
    residual_local_prefix: np.ndarray
    residual_harmonic_prefix: np.ndarray
    residual_source_prefix: np.ndarray

    def __post_init__(self) -> None:
        if self.step_index < 0:
            raise ValueError("step_index must be non-negative")
        if not np.isfinite(self.eta_restart):
            raise ValueError("eta_restart must be finite")
        state = np.asarray(self.state_vector, dtype=np.float64)
        if state.ndim != 1:
            raise ValueError("state_vector must be 1-D")
        eta_prefix = np.asarray(self.eta_prefix, dtype=np.float64)
        if eta_prefix.ndim != 1 or eta_prefix.size != self.step_index + 1:
            raise ValueError("eta_prefix length must equal step_index + 1")
        for name, value in (
            ("photon_T_prefix", self.photon_T_prefix),
            ("photon_E_prefix", self.photon_E_prefix),
            ("photon_B_prefix", self.photon_B_prefix),
            ("neutrino_tower_prefix", self.neutrino_tower_prefix),
            ("baryon_local_prefix", self.baryon_local_prefix),
            ("cdm_local_prefix", self.cdm_local_prefix),
            ("source_local_prefix", self.source_local_prefix),
            ("residual_local_prefix", self.residual_local_prefix),
            ("residual_harmonic_prefix", self.residual_harmonic_prefix),
            ("residual_source_prefix", self.residual_source_prefix),
        ):
            arr = np.asarray(value, dtype=np.float64)
            if arr.ndim != 2 or arr.shape[0] != eta_prefix.size:
                raise ValueError(f"{name} must have shape (len(eta_prefix), n_state)")


@dataclass(frozen=True)
class _SegmentResult:
    t: np.ndarray
    y: np.ndarray
    nfev: int
    njev: int
    nlu: int
    status: int
    message: str


@dataclass(frozen=True)
class _EtaRuntimeSnapshot:
    eta: float
    background: object
    gamma_t: float
    h_local: float
    tilted_electron: TiltedSpeciesBackground | None


@dataclass(frozen=True)
class _AuxiliaryOperatorSample:
    mode_ops: object
    source_template: np.ndarray
    mass_diag: np.ndarray

    def __post_init__(self) -> None:
        object.__setattr__(self, "source_template", np.asarray(self.source_template, dtype=np.float64))
        object.__setattr__(self, "mass_diag", np.asarray(self.mass_diag, dtype=np.float64))

    def drive(self, state_vector: np.ndarray) -> np.ndarray:
        vector = np.asarray(state_vector, dtype=np.float64)
        return (
            np.asarray(self.mode_ops.A_fs @ vector, dtype=np.float64)
            + np.asarray(self.mode_ops.A_mix @ vector, dtype=np.float64)
            + np.asarray(self.mode_ops.A_coll @ vector, dtype=np.float64)
            + np.asarray(self.source_template, dtype=np.float64)
        )

    def drive_subset(self, state_vector: np.ndarray, rows: np.ndarray) -> np.ndarray:
        vector = np.asarray(state_vector, dtype=np.float64)
        row_idx = np.asarray(rows, dtype=np.int64)
        return (
            np.asarray(self.mode_ops.A_fs[row_idx, :] @ vector, dtype=np.float64)
            + np.asarray(self.mode_ops.A_mix[row_idx, :] @ vector, dtype=np.float64)
            + np.asarray(self.mode_ops.A_coll[row_idx, :] @ vector, dtype=np.float64)
            + np.asarray(self.source_template[row_idx], dtype=np.float64)
        )


@dataclass(frozen=True)
class _ResidualAffineSystem:
    operator: np.ndarray
    forcing: np.ndarray

    def __post_init__(self) -> None:
        object.__setattr__(self, "operator", np.asarray(self.operator, dtype=np.float64))
        object.__setattr__(self, "forcing", np.asarray(self.forcing, dtype=np.float64))

    def rhs(self, state: np.ndarray) -> np.ndarray:
        return np.asarray(self.operator @ np.asarray(state, dtype=np.float64), dtype=np.float64) + np.asarray(
            self.forcing,
            dtype=np.float64,
        )


@dataclass(frozen=True)
class _LayoutProjectionIndexCache:
    harmonic_photon_T: np.ndarray
    harmonic_photon_E: np.ndarray
    harmonic_photon_B: np.ndarray
    harmonic_neutrino: np.ndarray
    src_all: np.ndarray
    src_by_mode_label: dict[str, np.ndarray]
    baryon_by_mode_label: dict[str, np.ndarray]
    cdm_by_mode_label: dict[str, np.ndarray]
    auxiliary_coupled_rows: np.ndarray
    auxiliary_photon_B_rows: np.ndarray
    auxiliary_baryon_rows: dict[str, np.ndarray]
    auxiliary_cdm_rows: dict[str, np.ndarray]


def _resolve_projection_mode_label(
    mode_labels: tuple[str, ...],
    fallback: str,
    *,
    m: int,
) -> str:
    preferred = {
        0: "m0",
        2: "m+2",
        -2: "m-2",
    }.get(int(m))
    if preferred is not None and preferred in mode_labels:
        return preferred
    return fallback


def _build_layout_projection_index_cache(
    layout,
    *,
    covered_mode_label: str,
) -> _LayoutProjectionIndexCache:
    size = (int(layout.ell_max) + 1) ** 2
    photon_t = np.zeros(size, dtype=np.int64)
    photon_e = np.zeros(size, dtype=np.int64)
    photon_b = np.zeros(size, dtype=np.int64)
    neutrino = np.zeros(size, dtype=np.int64)
    slot = 0
    for ell in range(layout.ell_max + 1):
        for m in range(-ell, ell + 1):
            mu = _resolve_projection_mode_label(layout.mode_labels, covered_mode_label, m=m)
            photon_t[slot] = flatten(layout, mu, "ph_I", ell, m)
            photon_e[slot] = flatten(layout, mu, "ph_E", ell, m)
            photon_b[slot] = flatten(layout, mu, "ph_B", ell, m)
            neutrino[slot] = flatten(layout, mu, "nu_I", ell, m)
            slot += 1
    src_by_mode_label = {
        str(mu): np.array(
            [
                flatten(layout, str(mu), "src", None, None, local_dof=i)
                for i in range(int(layout.sector_local_dofs["src"]))
            ],
            dtype=np.int64,
        )
        for mu in layout.mode_labels
    }
    baryon_by_mode_label = {
        str(mu): np.array(
            [
                flatten(layout, str(mu), "baryon", None, None, local_dof=i)
                for i in range(int(layout.sector_local_dofs["baryon"]))
            ],
            dtype=np.int64,
        )
        for mu in layout.mode_labels
    }
    cdm_by_mode_label = {
        str(mu): np.array(
            [
                flatten(layout, str(mu), "cdm", None, None, local_dof=i)
                for i in range(int(layout.sector_local_dofs["cdm"]))
            ],
            dtype=np.int64,
        )
        for mu in layout.mode_labels
    }
    auxiliary_rows: list[int] = [int(value) for value in photon_b]
    auxiliary_photon_B_rows = np.arange(photon_b.size, dtype=np.int64)
    auxiliary_baryon_rows: dict[str, np.ndarray] = {}
    auxiliary_cdm_rows: dict[str, np.ndarray] = {}
    offset = int(photon_b.size)
    for mu in layout.mode_labels:
        indices = baryon_by_mode_label[str(mu)]
        auxiliary_baryon_rows[str(mu)] = np.arange(offset, offset + indices.size, dtype=np.int64)
        auxiliary_rows.extend(int(value) for value in indices)
        offset += int(indices.size)
    for mu in layout.mode_labels:
        indices = cdm_by_mode_label[str(mu)]
        auxiliary_cdm_rows[str(mu)] = np.arange(offset, offset + indices.size, dtype=np.int64)
        auxiliary_rows.extend(int(value) for value in indices)
        offset += int(indices.size)
    return _LayoutProjectionIndexCache(
        harmonic_photon_T=photon_t,
        harmonic_photon_E=photon_e,
        harmonic_photon_B=photon_b,
        harmonic_neutrino=neutrino,
        src_all=np.asarray(
            np.concatenate([src_by_mode_label[str(mu)] for mu in layout.mode_labels]),
            dtype=np.int64,
        ),
        src_by_mode_label=src_by_mode_label,
        baryon_by_mode_label=baryon_by_mode_label,
        cdm_by_mode_label=cdm_by_mode_label,
        auxiliary_coupled_rows=np.asarray(auxiliary_rows, dtype=np.int64),
        auxiliary_photon_B_rows=auxiliary_photon_B_rows,
        auxiliary_baryon_rows=auxiliary_baryon_rows,
        auxiliary_cdm_rows=auxiliary_cdm_rows,
    )


def _pack_radiation_state(
    *,
    photon_T: PSTFHierarchyState,
    photon_E: PolarizationHierarchyState,
    photon_B: PSTFHierarchyState | None = None,
    neutrino_tower: PSTFHierarchyState,
    baryon_local: np.ndarray | None = None,
    cdm_local: np.ndarray | None = None,
    source_local: np.ndarray | None = None,
    residual_local: np.ndarray | None = None,
    residual_harmonic: np.ndarray | None = None,
    residual_source: np.ndarray | None = None,
) -> np.ndarray:
    b_mode = zero_hierarchy(photon_T.L) if photon_B is None else photon_B
    baryon = (
        np.zeros(_BARYON_LOCAL_DOF, dtype=np.float64)
        if baryon_local is None
        else np.asarray(baryon_local, dtype=np.float64)
    )
    cdm = (
        np.zeros(_CDM_LOCAL_DOF, dtype=np.float64)
        if cdm_local is None
        else np.asarray(cdm_local, dtype=np.float64)
    )
    source = (
        np.zeros(_SOURCE_LOCAL_DOF, dtype=np.float64)
        if source_local is None
        else np.asarray(source_local, dtype=np.float64)
    )
    residual = (
        np.zeros(0, dtype=np.float64)
        if residual_local is None
        else np.asarray(residual_local, dtype=np.float64)
    )
    residual_h = (
        np.zeros(0, dtype=np.float64)
        if residual_harmonic is None
        else np.asarray(residual_harmonic, dtype=np.float64)
    )
    residual_s = (
        np.zeros(0, dtype=np.float64)
        if residual_source is None
        else np.asarray(residual_source, dtype=np.float64)
    )
    if baryon.shape != (_BARYON_LOCAL_DOF,):
        raise ValueError(f"baryon_local must have shape ({_BARYON_LOCAL_DOF},)")
    if cdm.shape != (_CDM_LOCAL_DOF,):
        raise ValueError(f"cdm_local must have shape ({_CDM_LOCAL_DOF},)")
    if source.shape != (_SOURCE_LOCAL_DOF,):
        raise ValueError(f"source_local must have shape ({_SOURCE_LOCAL_DOF},)")
    if residual.ndim != 1:
        raise ValueError("residual_local must be a 1-D vector when provided")
    if residual_h.ndim != 1:
        raise ValueError("residual_harmonic must be a 1-D vector when provided")
    if residual_s.ndim != 1:
        raise ValueError("residual_source must be a 1-D vector when provided")
    return np.concatenate(
        [
            pack_hierarchy(photon_T),
            pack_hierarchy(photon_E.E),
            pack_hierarchy(b_mode),
            pack_hierarchy(neutrino_tower),
            baryon,
            cdm,
            source,
            residual,
            residual_h,
            residual_s,
        ]
    )


def _make_pstf_tensor_view(ell: int, components: np.ndarray) -> PSTFTensor:
    tensor = object.__new__(PSTFTensor)
    tensor.ell = int(ell)
    tensor.components = np.asarray(components)
    return tensor


def _unpack_hierarchy_view(flat: np.ndarray, L: int) -> PSTFHierarchyState:
    expected = (L + 1) ** 2
    arr = np.asarray(flat, dtype=np.float64)
    if arr.shape != (expected,):
        raise ValueError(
            f"flat shape {arr.shape} != ({expected},) for L={L}"
        )
    tensors: list[PSTFTensor] = []
    offset = 0
    for ell in range(L + 1):
        size = 2 * ell + 1
        tensors.append(_make_pstf_tensor_view(ell, arr[offset : offset + size]))
        offset += size
    state = object.__new__(PSTFHierarchyState)
    state.L = int(L)
    state.tensors = tensors
    return state


def _unpack_radiation_state(
    y: np.ndarray,
    L_max: int,
    *,
    residual_local_dof: int = 0,
    residual_harmonic_dof: int = 0,
    residual_source_dof: int = 0,
) -> tuple[
    PSTFHierarchyState,
    PolarizationHierarchyState,
    PSTFHierarchyState,
    PSTFHierarchyState,
    np.ndarray,
    np.ndarray,
    np.ndarray,
    np.ndarray,
    np.ndarray,
    np.ndarray,
]:
    arr = np.asarray(y, dtype=np.float64)
    tower_size = _tower_size(L_max)
    expected = _radiation_state_size(L_max) + int(residual_local_dof) + int(residual_harmonic_dof) + int(residual_source_dof)
    if arr.shape != (expected,):
        raise ValueError(f"radiation state shape {arr.shape} does not match L_max={L_max}")
    photon_T = _unpack_hierarchy_view(arr[:tower_size], L_max)
    photon_E = PolarizationHierarchyState(E=_unpack_hierarchy_view(arr[tower_size : 2 * tower_size], L_max))
    photon_B = _unpack_hierarchy_view(arr[2 * tower_size : 3 * tower_size], L_max)
    neutrino_tower = _unpack_hierarchy_view(arr[3 * tower_size : 4 * tower_size], L_max)
    local_offset = 4 * tower_size
    baryon_local = np.asarray(arr[local_offset : local_offset + _BARYON_LOCAL_DOF], dtype=np.float64)
    cdm_local = np.asarray(arr[local_offset + _BARYON_LOCAL_DOF : local_offset + _LOCAL_MATTER_DOF], dtype=np.float64)
    source_local = np.asarray(
        arr[local_offset + _LOCAL_MATTER_DOF : local_offset + _PRIMARY_LOCAL_DOF],
        dtype=np.float64,
    )
    residual_local = np.asarray(
        arr[local_offset + _PRIMARY_LOCAL_DOF : local_offset + _PRIMARY_LOCAL_DOF + int(residual_local_dof)],
        dtype=np.float64,
    )
    residual_harmonic = np.asarray(
        arr[
            local_offset
            + _PRIMARY_LOCAL_DOF
            + int(residual_local_dof) : local_offset
            + _PRIMARY_LOCAL_DOF
            + int(residual_local_dof)
            + int(residual_harmonic_dof)
        ],
        dtype=np.float64,
    )
    residual_source = np.asarray(
        arr[
            local_offset
            + _PRIMARY_LOCAL_DOF
            + int(residual_local_dof)
            + int(residual_harmonic_dof) : local_offset
            + _PRIMARY_LOCAL_DOF
            + int(residual_local_dof)
            + int(residual_harmonic_dof)
            + int(residual_source_dof)
        ],
        dtype=np.float64,
    )
    return (
        photon_T,
        photon_E,
        photon_B,
        neutrino_tower,
        baryon_local,
        cdm_local,
        source_local,
        residual_local,
        residual_harmonic,
        residual_source,
    )


def _seed_neutrino_tower_from_reduced(
    reduced: np.ndarray,
    *,
    L_max: int,
) -> PSTFHierarchyState:
    nu = np.asarray(reduced, dtype=np.float64)
    if nu.shape != (4,):
        raise ValueError(f"neutrino_reduced must have shape (4,), got {nu.shape}")
    tower = zero_hierarchy(L_max)
    if L_max >= 0:
        tower.tensors[0].components[0] = float(nu[0])
    if L_max >= 1:
        tower.tensors[1].components[1] = float(nu[1])
    if L_max >= 2:
        tower.tensors[2].components[2] = float(nu[2])
    if L_max >= 3:
        tower.tensors[3].components[3] = float(nu[3])
    return tower


def _reduced_summary_from_neutrino_tower(
    tower: PSTFHierarchyState,
) -> np.ndarray:
    summary = np.zeros(4, dtype=np.float64)
    if tower.L >= 0:
        summary[0] = float(tower.tensors[0].components[0])
    if tower.L >= 1:
        summary[1] = float(tower.tensors[1].components[1])
    if tower.L >= 2:
        summary[2] = float(tower.tensors[2].components[2])
    if tower.L >= 3:
        summary[3] = float(tower.tensors[3].components[3])
    return summary


def _extract_operator_diag(
    *,
    backend: FamilyBackend,
    mode_ops,
    sector: str,
    covered_mode_label: str | None = None,
) -> np.ndarray:
    layout = build_hierarchy_layout(backend, backend.truncation)
    mu = layout.mode_labels[0] if covered_mode_label is None else str(covered_mode_label)
    if mu not in layout.mode_labels:
        raise ValueError(f"covered_mode_label {mu!r} not present in layout.mode_labels")
    diagonal = np.asarray(mode_ops.A_coll.diagonal(), dtype=np.float64)
    out = np.zeros((layout.ell_max + 1) ** 2, dtype=np.float64)
    for ell in range(layout.ell_max + 1):
        for m in range(-ell, ell + 1):
            slot = sum(2 * l + 1 for l in range(ell)) + (m + ell)
            out[slot] = float(diagonal[flatten(layout, mu, sector, ell, m)])
    return out


def _extract_src_local_block(
    *,
    layout,
    source_template: np.ndarray,
    covered_mode_label: str,
) -> np.ndarray:
    width = int(layout.sector_local_dofs["src"])
    return np.array(
        [
            float(source_template[flatten(layout, covered_mode_label, "src", None, None, local_dof=i)])
            for i in range(width)
        ],
        dtype=np.float64,
    )


def _dense_submatrix(matrix, rows: np.ndarray, cols: np.ndarray) -> np.ndarray:
    row_idx = np.asarray(rows, dtype=np.int64)
    col_idx = np.asarray(cols, dtype=np.int64)
    sub = matrix[row_idx, :]
    sub = sub[:, col_idx]
    if hasattr(sub, "toarray"):
        return np.asarray(sub.toarray(), dtype=np.float64)
    return np.asarray(sub, dtype=np.float64)


def _extract_src_local_blocks_by_mode_label(
    *,
    layout,
    source_template: np.ndarray,
) -> dict[str, np.ndarray]:
    return {
        str(mu): _extract_src_local_block(
            layout=layout,
            source_template=source_template,
            covered_mode_label=str(mu),
        )
        for mu in layout.mode_labels
    }


class Ver2TierBIntegrator:
    """Executable Tier-B integrator owned by S1 background + S2 hierarchy."""

    def __init__(
        self,
        config: IntegratorConfig,
        species: SpeciesBackgroundRegistry,
        *,
        backend: FamilyBackend,
        background_monitor: BackgroundEvolutionResult,
        visibility_source,
        canonical_decision: CanonicalDecision,
        seed_k_comoving: float = 1.0e-4,
    ) -> None:
        self.config = config
        self.species = species
        self.backend = backend
        self.background_monitor = background_monitor
        self.visibility_source = visibility_source
        self.canonical_decision = canonical_decision
        self.background_interp = _build_background_interpolator(
            background_monitor,
            backend=backend,
        )
        self.bg_table = _BackgroundTableAdapter(self.background_interp)
        self.tetrad_state = _TetradStateAdapter(
            self.background_interp,
            np.asarray(background_monitor.initial_conditions.geometry.ricci_pstf, dtype=np.float64),
        )
        self.closure = (
            config.closure_strategy
            if config.closure_strategy is not None
            else build_default_closure(
                L_max=config.L_max,
                strategy_name="tca",
                gamma_threshold_over_H=config.gamma_T_over_H_threshold,
            )
        )
        self._temperature_collision = _TemperatureProjectedCollision()
        self._e_collision = _EProjectedCollision()
        self._b_collision = _BProjectedCollision()
        self._zero_b_state = zero_hierarchy(config.L_max)
        self._zero_v_b_real_sph = np.zeros(3, dtype=np.float64)
        self._neutrino_background = self.species[SpeciesLabel.NEUTRINO]
        self._direction = np.asarray(config.tilt_direction, dtype=np.float64)
        if not np.any(self._direction):
            self._direction = np.array([1.0, 0.0, 0.0], dtype=np.float64)
        self._direction = self._direction / max(float(np.linalg.norm(self._direction)), 1.0e-30)
        self.seed_k_comoving = float(seed_k_comoving)
        self.startup_gate: StartupGateDecision | None = None
        self.seed_projection: SeedConstraintProjection | None = None
        self.startup_state: QuadrupoleStartupState | None = None
        self.seed_pack: SeedPack | None = None
        self.seed_injection_mode: str = "uninitialized"
        self.seed_velocity_scale: float = 1.0
        self._matter_seed_observables: dict[str, float] | None = None
        gamma_t_initial = _resolved_gamma_t(
            visibility_source=self.visibility_source,
            eta=float(self.background_monitor.eta[0]),
            direction=self._direction,
            config=self.config,
        )
        reionization_amplitude = (
            0.0
            if self.visibility_source.contract.events is None
            else float(self.visibility_source.contract.events.tau_reion)
        )
        self.mode_ops = self.backend.operator_factory(
            self._live_backend_state_payload(
                eta=float(self.background_monitor.eta[0]),
                gamma_t_probe=float(gamma_t_initial),
                visibility_amplitude=0.0,
                polarization_source=0.0,
                reionization_amplitude=reionization_amplitude,
            )
        )
        self._layout_covered_mode_label = (
            str(getattr(self.mode_ops, "layout_metadata", {}).get("mode_labels", [None])[0])
        )
        self._layout = build_hierarchy_layout(self.backend, self.backend.truncation)
        if self._layout_covered_mode_label == "None" or self._layout_covered_mode_label not in self._layout.mode_labels:
            self._layout_covered_mode_label = str(self._layout.mode_labels[0])
        self._projection_index_cache = _build_layout_projection_index_cache(
            self._layout,
            covered_mode_label=self._layout_covered_mode_label,
        )
        self._residual_mode_labels = tuple(
            str(mu) for mu in self._layout.mode_labels if str(mu) != self._layout_covered_mode_label
        )
        self._residual_local_dof = len(self._residual_mode_labels) * (_BARYON_LOCAL_DOF + _CDM_LOCAL_DOF)
        self._residual_harmonic_dof = len(self._residual_mode_labels) * 4 * _tower_size(self.config.L_max)
        self._residual_source_dof = len(self._residual_mode_labels) * int(self._layout.sector_local_dofs["src"])
        residual_rows: list[int] = []
        for mu in self._residual_mode_labels:
            residual_rows.extend(int(value) for value in self._projection_index_cache.baryon_by_mode_label[mu])
            residual_rows.extend(int(value) for value in self._projection_index_cache.cdm_by_mode_label[mu])
        self._residual_local_layout_rows = np.asarray(residual_rows, dtype=np.int64)
        covered_mu = str(self._layout_covered_mode_label)
        self._covered_harmonic_layout_rows = {
            "ph_I": np.array(
                [
                    flatten(self._layout, covered_mu, "ph_I", ell, m)
                    for ell in range(self.config.L_max + 1)
                    for m in range(-ell, ell + 1)
                ],
                dtype=np.int64,
            ),
            "ph_E": np.array(
                [
                    flatten(self._layout, covered_mu, "ph_E", ell, m)
                    for ell in range(self.config.L_max + 1)
                    for m in range(-ell, ell + 1)
                ],
                dtype=np.int64,
            ),
            "ph_B": np.array(
                [
                    flatten(self._layout, covered_mu, "ph_B", ell, m)
                    for ell in range(self.config.L_max + 1)
                    for m in range(-ell, ell + 1)
                ],
                dtype=np.int64,
            ),
            "nu_I": np.array(
                [
                    flatten(self._layout, covered_mu, "nu_I", ell, m)
                    for ell in range(self.config.L_max + 1)
                    for m in range(-ell, ell + 1)
                ],
                dtype=np.int64,
            ),
        }
        residual_harmonic_rows: list[int] = []
        for mu in self._residual_mode_labels:
            for sector in ("ph_I", "ph_E", "ph_B", "nu_I"):
                residual_harmonic_rows.extend(
                    int(flatten(self._layout, str(mu), sector, ell, m))
                    for ell in range(self.config.L_max + 1)
                    for m in range(-ell, ell + 1)
                )
        self._residual_harmonic_layout_rows = np.asarray(residual_harmonic_rows, dtype=np.int64)
        self._covered_baryon_layout_rows = np.asarray(
            self._projection_index_cache.baryon_by_mode_label[covered_mu],
            dtype=np.int64,
        )
        self._covered_cdm_layout_rows = np.asarray(
            self._projection_index_cache.cdm_by_mode_label[covered_mu],
            dtype=np.int64,
        )
        self._residual_harmonic_identity = np.eye(self._residual_harmonic_dof, dtype=np.float64)
        self._residual_harmonic_sparse_identity = csc_matrix(self._residual_harmonic_identity)
        self._residual_local_identity = np.eye(self._residual_local_dof, dtype=np.float64)
        self._residual_local_sparse_identity = csc_matrix(self._residual_local_identity)
        self._residual_joint_identity = np.eye(
            self._residual_local_dof + self._residual_harmonic_dof + self._residual_source_dof,
            dtype=np.float64,
        )
        self._residual_joint_sparse_identity = csc_matrix(self._residual_joint_identity)
        self._coll_T_diag = _extract_operator_diag(
            backend=backend,
            mode_ops=self.mode_ops,
            sector="ph_I",
            covered_mode_label=self._layout_covered_mode_label,
        )
        self._coll_E_diag = _extract_operator_diag(
            backend=backend,
            mode_ops=self.mode_ops,
            sector="ph_E",
            covered_mode_label=self._layout_covered_mode_label,
        )
        self._coll_B_diag = _extract_operator_diag(
            backend=backend,
            mode_ops=self.mode_ops,
            sector="ph_B",
            covered_mode_label=self._layout_covered_mode_label,
        )
        _ = sample_hierarchy_background(
            float(self.background_monitor.eta[0]),
            bg_table=self.bg_table,
            tetrad_state=self.tetrad_state,
        )

    def _tilted_electron_at(self, eta: float) -> TiltedSpeciesBackground | None:
        if abs(float(self.config.tilt_rapidity)) == 0.0:
            return None
        velocity = np.asarray(
            [
                np.interp(
                    float(eta),
                    np.asarray(self.background_monitor.eta, dtype=np.float64),
                    np.asarray(self.background_monitor.tilt_velocity, dtype=np.float64)[:, axis],
                )
                for axis in range(3)
            ],
            dtype=np.float64,
        )
        speed = float(np.linalg.norm(velocity))
        if speed <= 0.0:
            return None
        direction = tuple((velocity / speed).tolist())
        return TiltedSpeciesBackground.from_rapidity(
            base=self.species[SpeciesLabel.BARYON],
            rapidity=float(np.arctanh(min(speed, 1.0 - 1.0e-15))),
            v_hat_e=direction,
        )

    def initial_state(self) -> np.ndarray:
        seeded = self._build_seeded_initial_state()
        self.startup_gate = seeded.startup_gate
        self.seed_projection = seeded.seed_projection
        self.startup_state = seeded.startup_state
        self.seed_pack = seeded.seed_pack
        self.seed_injection_mode = seeded.seed_injection_mode
        self.seed_velocity_scale = seeded.velocity_scale
        self._matter_seed_observables = dict(seeded.matter_seed_observables)
        theta_1 = _theta_1_from_temperature_state(seeded.photon_T)
        baryon_v = float(seeded.matter_seed_observables["theta_b"])
        baryon_local = np.array(
            [
                float(seeded.matter_seed_observables["delta_b"]),
                baryon_v,
                baryon_v,
                float(3.0 * theta_1 - baryon_v),
            ],
            dtype=np.float64,
        )
        cdm_local = np.array(
            [
                float(seeded.matter_seed_observables["delta_c"]),
                float(seeded.matter_seed_observables["theta_c"]),
            ],
            dtype=np.float64,
        )
        eta_initial = float(self.config.eta_initial_mpc)
        gamma_t_initial = _resolved_gamma_t(
            eta=eta_initial,
            direction=self._direction,
            visibility_source=self.visibility_source,
            config=self.config,
        )
        polarization_slot = _ell2_m0_slot_offset(int(self.config.L_max)) if int(self.config.L_max) >= 2 else None
        source_seed_blocks = self.backend.evaluate_reduced_source_blocks(
            self._live_backend_state_payload(
                eta=eta_initial,
                gamma_t_probe=float(gamma_t_initial),
                visibility_amplitude=abs(float(pack_hierarchy(seeded.photon_T)[0])),
                polarization_source=(
                    0.0
                    if polarization_slot is None
                    else abs(float(pack_hierarchy(seeded.photon_E.E)[polarization_slot]))
                ),
                reionization_amplitude=float(self._reionization_amplitude()),
            )
        )
        if str(self.config.solver_method).upper() == "IMEX_MIDPOINT_BDF":
            source_local = np.asarray(source_seed_blocks[str(self._layout_covered_mode_label)], dtype=np.float64)
        else:
            source_local = np.zeros(_SOURCE_LOCAL_DOF, dtype=np.float64)
        startup_snapshot = self._eta_runtime_snapshot(eta_initial)
        residual_local, residual_harmonic, residual_source = self._solve_startup_residual_joint_state(
            snapshot=startup_snapshot,
            photon_T=seeded.photon_T,
            photon_E=seeded.photon_E,
            photon_B=zero_hierarchy(self.config.L_max),
            neutrino_tower=seeded.neutrino_tower,
            baryon_local=baryon_local,
            source_local=source_local,
        )
        return _pack_radiation_state(
            photon_T=seeded.photon_T,
            photon_E=seeded.photon_E,
            photon_B=zero_hierarchy(self.config.L_max),
            neutrino_tower=seeded.neutrino_tower,
            baryon_local=baryon_local,
            cdm_local=cdm_local,
            source_local=source_local,
            residual_local=residual_local,
            residual_harmonic=residual_harmonic,
            residual_source=residual_source,
        )

    def _reionization_amplitude(self) -> float:
        return (
            0.0
            if self.visibility_source.contract.events is None
            else float(self.visibility_source.contract.events.tau_reion)
        )

    def _split_residual_local_state(
        self,
        residual_local: np.ndarray,
    ) -> tuple[dict[str, np.ndarray], dict[str, np.ndarray]]:
        residual = np.asarray(residual_local, dtype=np.float64)
        if residual.shape != (self._residual_local_dof,):
            raise ValueError(
                f"residual_local must have shape ({self._residual_local_dof},), got {residual.shape}"
            )
        baryon_by_mode_label: dict[str, np.ndarray] = {}
        cdm_by_mode_label: dict[str, np.ndarray] = {}
        offset = 0
        for mu in self._residual_mode_labels:
            baryon_by_mode_label[str(mu)] = np.asarray(
                residual[offset : offset + _BARYON_LOCAL_DOF],
                dtype=np.float64,
            )
            offset += _BARYON_LOCAL_DOF
            cdm_by_mode_label[str(mu)] = np.asarray(
                residual[offset : offset + _CDM_LOCAL_DOF],
                dtype=np.float64,
            )
            offset += _CDM_LOCAL_DOF
        return baryon_by_mode_label, cdm_by_mode_label

    def _pack_residual_local_state(
        self,
        *,
        baryon_by_mode_label: Mapping[str, np.ndarray],
        cdm_by_mode_label: Mapping[str, np.ndarray],
    ) -> np.ndarray:
        if self._residual_local_dof == 0:
            return np.zeros(0, dtype=np.float64)
        pieces: list[np.ndarray] = []
        for mu in self._residual_mode_labels:
            pieces.append(np.asarray(baryon_by_mode_label[str(mu)], dtype=np.float64))
            pieces.append(np.asarray(cdm_by_mode_label[str(mu)], dtype=np.float64))
        return np.concatenate(pieces, dtype=np.float64)

    def _split_residual_harmonic_state(
        self,
        residual_harmonic: np.ndarray,
    ) -> tuple[dict[str, np.ndarray], dict[str, np.ndarray], dict[str, np.ndarray], dict[str, np.ndarray]]:
        residual = np.asarray(residual_harmonic, dtype=np.float64)
        if residual.shape != (self._residual_harmonic_dof,):
            raise ValueError(
                f"residual_harmonic must have shape ({self._residual_harmonic_dof},), got {residual.shape}"
            )
        width = _tower_size(self.config.L_max)
        photon_t_by_mode_label: dict[str, np.ndarray] = {}
        photon_e_by_mode_label: dict[str, np.ndarray] = {}
        photon_b_by_mode_label: dict[str, np.ndarray] = {}
        neutrino_by_mode_label: dict[str, np.ndarray] = {}
        offset = 0
        for mu in self._residual_mode_labels:
            photon_t_by_mode_label[str(mu)] = np.asarray(residual[offset : offset + width], dtype=np.float64)
            offset += width
            photon_e_by_mode_label[str(mu)] = np.asarray(residual[offset : offset + width], dtype=np.float64)
            offset += width
            photon_b_by_mode_label[str(mu)] = np.asarray(residual[offset : offset + width], dtype=np.float64)
            offset += width
            neutrino_by_mode_label[str(mu)] = np.asarray(residual[offset : offset + width], dtype=np.float64)
            offset += width
        return (
            photon_t_by_mode_label,
            photon_e_by_mode_label,
            photon_b_by_mode_label,
            neutrino_by_mode_label,
        )

    def _pack_residual_harmonic_state(
        self,
        *,
        photon_T_by_mode_label: Mapping[str, np.ndarray],
        photon_E_by_mode_label: Mapping[str, np.ndarray],
        photon_B_by_mode_label: Mapping[str, np.ndarray],
        neutrino_by_mode_label: Mapping[str, np.ndarray],
    ) -> np.ndarray:
        if self._residual_harmonic_dof == 0:
            return np.zeros(0, dtype=np.float64)
        pieces: list[np.ndarray] = []
        for mu in self._residual_mode_labels:
            pieces.append(np.asarray(photon_T_by_mode_label[str(mu)], dtype=np.float64))
            pieces.append(np.asarray(photon_E_by_mode_label[str(mu)], dtype=np.float64))
            pieces.append(np.asarray(photon_B_by_mode_label[str(mu)], dtype=np.float64))
            pieces.append(np.asarray(neutrino_by_mode_label[str(mu)], dtype=np.float64))
        return np.concatenate(pieces, dtype=np.float64)

    def _fill_layout_state_vector_from_components(
        self,
        *,
        out: np.ndarray,
        sample: _AuxiliaryOperatorSample,
        photon_T_row: np.ndarray,
        photon_E_row: np.ndarray,
        photon_B_row: np.ndarray,
        neutrino_row: np.ndarray,
        baryon_by_mode_label: Mapping[str, np.ndarray],
        cdm_by_mode_label: Mapping[str, np.ndarray],
    ) -> None:
        out.fill(0.0)
        out[self._projection_index_cache.src_all] = sample.source_template[self._projection_index_cache.src_all]
        out[self._projection_index_cache.harmonic_photon_T] = np.asarray(photon_T_row, dtype=np.float64)
        out[self._projection_index_cache.harmonic_photon_E] = np.asarray(photon_E_row, dtype=np.float64)
        out[self._projection_index_cache.harmonic_photon_B] = np.asarray(photon_B_row, dtype=np.float64)
        out[self._projection_index_cache.harmonic_neutrino] = np.asarray(neutrino_row, dtype=np.float64)
        for mu, indices in self._projection_index_cache.baryon_by_mode_label.items():
            out[indices] = np.asarray(baryon_by_mode_label[str(mu)], dtype=np.float64)
        for mu, indices in self._projection_index_cache.cdm_by_mode_label.items():
            out[indices] = np.asarray(cdm_by_mode_label[str(mu)], dtype=np.float64)

    def _build_layout_state_vector_for_residual_harmonics(
        self,
        *,
        sample: _AuxiliaryOperatorSample,
        photon_T: PSTFHierarchyState,
        photon_E: PolarizationHierarchyState,
        photon_B: PSTFHierarchyState,
        neutrino_tower: PSTFHierarchyState,
        baryon_local: np.ndarray,
        cdm_local: np.ndarray,
        residual_local: np.ndarray,
        residual_harmonic: np.ndarray,
    ) -> np.ndarray:
        state = np.zeros(self._layout.size, dtype=np.float64)
        state[self._projection_index_cache.src_all] = np.asarray(
            sample.source_template[self._projection_index_cache.src_all],
            dtype=np.float64,
        )
        state[self._covered_harmonic_layout_rows["ph_I"]] = np.asarray(pack_hierarchy(photon_T), dtype=np.float64)
        state[self._covered_harmonic_layout_rows["ph_E"]] = np.asarray(pack_hierarchy(photon_E.E), dtype=np.float64)
        state[self._covered_harmonic_layout_rows["ph_B"]] = np.asarray(pack_hierarchy(photon_B), dtype=np.float64)
        state[self._covered_harmonic_layout_rows["nu_I"]] = np.asarray(
            pack_hierarchy(neutrino_tower),
            dtype=np.float64,
        )
        state[self._covered_baryon_layout_rows] = np.asarray(baryon_local, dtype=np.float64)
        state[self._covered_cdm_layout_rows] = np.asarray(cdm_local, dtype=np.float64)
        if self._residual_local_dof > 0:
            state[self._residual_local_layout_rows] = np.asarray(residual_local, dtype=np.float64)
        if self._residual_harmonic_dof > 0:
            state[self._residual_harmonic_layout_rows] = np.asarray(residual_harmonic, dtype=np.float64)
        return state

    def _startup_gate_at_initial_time(self) -> StartupGateDecision:
        gamma_t = _resolved_gamma_t(
            eta=float(self.background_monitor.eta[0]),
            direction=self._direction,
            visibility_source=self.visibility_source,
            config=self.config,
        )
        return decide_startup_gate(
            gamma_T=float(gamma_t),
            H=float(self.background_monitor.H[0]),
            threshold=float(self.config.gamma_T_over_H_threshold),
        )

    def _build_intrinsic_family_seeded_initial_state(
        self,
        *,
        branch: str,
        seed_pack: SeedPack,
    ) -> _SeededInitialState:
        formulas = regular_adiabatic_formulae(
            k_comoving=max(self.seed_k_comoving, 0.0),
            eta_initial=float(self.config.eta_initial_mpc),
            a_initial=float(self.background_monitor.a[0]),
        )
        seed_state = pack_regular_adiabatic_seed_from_formulae(
            a_initial=float(self.background_monitor.a[0]),
            L_max=self.config.L_max,
            formulas=formulas,
        )
        if branch == "tilted":
            seed_state = apply_tilted_boost_seed_rule(
                seed_state,
                beta=float(self.config.tilt_rapidity),
                v_hat_e=tuple(float(x) for x in self._direction),
            )
        projected_seed: PackedRegularSeedInjection = project_packed_regular_seed(
            seed_state,
            electron_velocity=rapidity_to_velocity(float(self.config.tilt_rapidity))
            * self._direction,
            geometry=self.background_monitor.initial_conditions.geometry,
            sigma_ab=self.background_monitor.initial_conditions.sigma_ab,
            target_q=np.asarray(
                self.background_monitor.initial_conditions.matter.q,
                dtype=np.float64,
            ),
        )
        unpacked = unpack_camb_regular_adiabatic_seed(
            projected_seed.seed_state,
            L_max=self.config.L_max,
        )
        combined = unpacked["combined"]
        photon_T = combined.photon_T.copy()
        photon_E = combined.photon_E.copy()
        neutrino_tower = _seed_neutrino_tower_from_reduced(
            np.asarray(combined.neutrino_reduced, dtype=np.float64).copy(),
            L_max=self.config.L_max,
        )

        startup_gate = self._startup_gate_at_initial_time()
        startup_state = None
        injection_mode = f"{seed_pack.seed_mode}+family_adapted_intrinsic_seed"
        if branch == "tilted":
            injection_mode = f"{injection_mode}+intrinsic_tilted_boost"
        if startup_gate.startup_selected:
            startup_state = self._resolve_startup_state(
                photon_T=photon_T,
                photon_E=photon_E,
                gamma_t=float(startup_gate.gamma_T_over_H * self.background_monitor.H[0]),
            )
            photon_T.tensors[2].components[2] = float(startup_state.theta_2)
            photon_E.E.tensors[2].components[2] = float(startup_state.E_2)
            injection_mode = f"{injection_mode}+quadrupole_tca_startup"

        return _SeededInitialState(
            photon_T=photon_T,
            photon_E=photon_E,
            neutrino_tower=neutrino_tower,
            startup_gate=startup_gate,
            seed_projection=projected_seed.projection,
            startup_state=startup_state,
            seed_k_comoving=max(self.seed_k_comoving, 0.0),
            seed_injection_mode=f"{injection_mode}+{projected_seed.injection_mode}",
            velocity_scale=float(projected_seed.velocity_scale),
            seed_pack=seed_pack,
            matter_seed_observables={
                "delta_b": float(unpacked["delta_b"]),
                "theta_b": float(unpacked["theta_b"]),
                "delta_c": float(unpacked["delta_c"]),
                "theta_c": float(unpacked["theta_c"]),
                "eta_cov": float(unpacked["eta_cov"]),
                "Z": float(unpacked["Z"]),
            },
        )

    def _build_seeded_initial_state(self) -> _SeededInitialState:
        branch = "tilted" if abs(float(self.config.tilt_rapidity)) > 0.0 else "orthogonal"
        intrinsic_family = self.backend.family_spec.family in {"II", "III", "IV", "VI_0", "VI_h", "VIII"}
        seed_mode = (
            "collocation_projected"
            if intrinsic_family
            else ("boosted_electron_frame" if branch == "tilted" else "flrw_like_regular")
        )
        seed_pack = self.backend.seed_factory(
            SeedRequest(
                branch=branch,
                seed_mode=seed_mode,
                amplitude_reference=max(self.seed_k_comoving, 1.0e-30),
                native_label=str(self.backend.required_metadata()["native_mode_labels"]),
                metadata={
                    "runtime_owner": "ver2_tier_b_native",
                    "seed_numeric_bridge": (
                        "family_adapted_lowell_startup_owner"
                        if intrinsic_family
                        else "backend_anchor_regular_seed"
                    ),
                    "tilt_enabled": bool(branch == "tilted"),
                },
            )
        )
        if intrinsic_family:
            return self._build_intrinsic_family_seeded_initial_state(
                branch=branch,
                seed_pack=seed_pack,
            )
        seed_state = make_camb_regular_adiabatic_seed(
            k_comoving=max(self.seed_k_comoving, 0.0),
            eta_initial=float(self.config.eta_initial_mpc),
            a_initial=float(self.background_monitor.a[0]),
            L_max=self.config.L_max,
            b_k_sq=float(getattr(self.config, "primordial_b_k_sq", 1.0)),
        )
        injection_mode = str(seed_pack.seed_mode)
        if branch == "tilted":
            seed_state = apply_tilted_boost_seed_rule(
                seed_state,
                beta=float(self.config.tilt_rapidity),
                v_hat_e=tuple(float(x) for x in self._direction),
            )
            boost_mode = (
                "axisymmetric_tilted_regular_adiabatic_seed"
                if is_axis_aligned(tuple(float(x) for x in self._direction))
                else "offaxis_tilted_regular_adiabatic_seed"
            )
            injection_mode = f"{injection_mode}+{boost_mode}"

        tilt_speed = rapidity_to_velocity(float(self.config.tilt_rapidity))
        projected_seed: PackedRegularSeedInjection = project_packed_regular_seed(
            seed_state,
            electron_velocity=tilt_speed * self._direction,
            geometry=self.background_monitor.initial_conditions.geometry,
            sigma_ab=self.background_monitor.initial_conditions.sigma_ab,
            target_q=np.asarray(self.background_monitor.initial_conditions.matter.q, dtype=np.float64),
        )
        unpacked = unpack_camb_regular_adiabatic_seed(
            projected_seed.seed_state,
            L_max=self.config.L_max,
        )
        combined = unpacked["combined"]
        photon_T = combined.photon_T.copy()
        photon_E = combined.photon_E.copy()
        neutrino_tower = _seed_neutrino_tower_from_reduced(
            np.asarray(combined.neutrino_reduced, dtype=np.float64).copy(),
            L_max=self.config.L_max,
        )
        startup_gate = self._startup_gate_at_initial_time()
        startup_state = None
        if startup_gate.startup_selected:
            startup_state = self._resolve_startup_state(
                photon_T=photon_T,
                photon_E=photon_E,
                gamma_t=float(startup_gate.gamma_T_over_H * self.background_monitor.H[0]),
            )
            photon_T.tensors[2].components[2] = float(startup_state.theta_2)
            photon_E.E.tensors[2].components[2] = float(startup_state.E_2)
            injection_mode = f"{injection_mode}+quadrupole_tca_startup"
        return _SeededInitialState(
            photon_T=photon_T,
            photon_E=photon_E,
            neutrino_tower=neutrino_tower,
            startup_gate=startup_gate,
            seed_projection=projected_seed.projection,
            startup_state=startup_state,
            seed_k_comoving=max(self.seed_k_comoving, 0.0),
            seed_injection_mode=f"{injection_mode}+{projected_seed.injection_mode}",
            velocity_scale=float(projected_seed.velocity_scale),
            seed_pack=seed_pack,
            matter_seed_observables={
                "delta_b": float(unpacked["delta_b"]),
                "theta_b": float(unpacked["theta_b"]),
                "delta_c": float(unpacked["delta_c"]),
                "theta_c": float(unpacked["theta_c"]),
                "eta_cov": float(unpacked["eta_cov"]),
                "Z": float(unpacked["Z"]),
            },
        )

    def _resolve_startup_state(
        self,
        *,
        photon_T: PSTFHierarchyState,
        photon_E: PolarizationHierarchyState,
        gamma_t: float,
    ) -> QuadrupoleStartupState:
        eta0 = float(self.background_monitor.eta[0])
        background = self._background_snapshot(eta0)
        rhs_T_free, rhs_E_free = self._collisionless_photon_rhs(
            photon_T=photon_T,
            photon_E=photon_E,
            background=background,
        )
        slot = _ell2_m0_slot_offset(self.config.L_max)
        S_T = float(rhs_T_free[slot]) / background.a_val * (-1.0)
        S_E = float(rhs_E_free[slot]) / background.a_val * (-1.0)
        return quadrupole_startup_from_sources(
            S_T=S_T,
            S_E=S_E,
            gamma_T=float(gamma_t),
        )

    def _h_local_at(self, eta: float) -> float:
        return _interp_scalar(self.background_monitor.eta, self.background_monitor.H, eta)

    def _background_snapshot(self, eta: float):
        return sample_hierarchy_background(
            float(eta),
            bg_table=self.bg_table,
            tetrad_state=self.tetrad_state,
        )

    def _eta_runtime_snapshot(self, eta: float) -> _EtaRuntimeSnapshot:
        eta_val = float(eta)
        return _EtaRuntimeSnapshot(
            eta=eta_val,
            background=self._background_snapshot(eta_val),
            gamma_t=_resolved_gamma_t(
                eta=eta_val,
                direction=self._direction,
                visibility_source=self.visibility_source,
                config=self.config,
            ),
            h_local=self._h_local_at(eta_val),
            tilted_electron=self._tilted_electron_at(eta_val),
        )

    def _collision_aux_from_snapshot(
        self,
        *,
        snapshot: _EtaRuntimeSnapshot,
        photon_T: PSTFHierarchyState,
        photon_E: PolarizationHierarchyState,
        baryon_local: np.ndarray | None = None,
        v_b_real_sph: np.ndarray | None = None,
        b_state: PSTFHierarchyState | None = None,
    ) -> _ProjectedCollisionAux:
        resolved_v_b = v_b_real_sph
        if resolved_v_b is None and baryon_local is not None:
            resolved_v_b = _electron_velocity_real_sph_from_baryon_row(baryon_local)
        return _ProjectedCollisionAux(
            eta=float(snapshot.eta),
            temperature_state=photon_T,
            polarization_state=photon_E,
            Gamma_T=float(snapshot.gamma_t),
            direction=self._direction,
            tilted_electron=snapshot.tilted_electron,
            v_b_real_sph=(
                self._zero_v_b_real_sph
                if resolved_v_b is None
                else np.asarray(resolved_v_b, dtype=np.float64)
            ),
            b_state=self._zero_b_state if b_state is None else b_state,
        )

    def _rhs_components_from_snapshot(
        self,
        *,
        photon_T: PSTFHierarchyState,
        photon_E: PolarizationHierarchyState,
        photon_B: PSTFHierarchyState,
        neutrino_tower: PSTFHierarchyState,
        baryon_local: np.ndarray | None,
        snapshot: _EtaRuntimeSnapshot,
        need_explicit: bool,
        need_full: bool,
        tca_tracker: list[bool] | None = None,
    ) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
        tca_active = bool(
            isinstance(self.closure, TCAClosure)
            and snapshot.gamma_t > 0.0
            and snapshot.h_local > 0.0
            and snapshot.gamma_t / snapshot.h_local > self.config.gamma_T_over_H_threshold
        )
        explicit_required = bool(need_explicit or tca_active or snapshot.gamma_t <= 0.0)
        full_required = bool(need_full or tca_active)
        rhs_T_explicit = rhs_E_explicit = rhs_B_explicit = None
        if explicit_required:
            rhs_T_explicit, rhs_E_explicit, rhs_B_explicit, rhs_nu = self._radiation_rhs_components(
                photon_T=photon_T,
                photon_E=photon_E,
                photon_B=photon_B,
                neutrino_tower=neutrino_tower,
                background=snapshot.background,
                collision_aux=None,
            )
        else:
            rhs_nu = hierarchy_rhs_neutrino_from_state(
                neutrino_tower,
                background=snapshot.background,
                closure=self.closure,
                neutrino_background=self._neutrino_background,
            )

        if full_required and snapshot.gamma_t > 0.0:
            rhs_T_full, rhs_E_full, rhs_B_full, _ = self._radiation_rhs_components(
                photon_T=photon_T,
                photon_E=photon_E,
                photon_B=photon_B,
                neutrino_tower=neutrino_tower,
                background=snapshot.background,
                collision_aux=self._collision_aux_from_snapshot(
                    snapshot=snapshot,
                photon_T=photon_T,
                photon_E=photon_E,
                baryon_local=baryon_local,
            ),
        )
        else:
            if rhs_T_explicit is None or rhs_E_explicit is None or rhs_B_explicit is None:
                rhs_T_explicit, rhs_E_explicit, rhs_B_explicit, _ = self._radiation_rhs_components(
                    photon_T=photon_T,
                    photon_E=photon_E,
                    photon_B=photon_B,
                    neutrino_tower=neutrino_tower,
                    background=snapshot.background,
                    collision_aux=None,
                )
            rhs_T_full = np.asarray(rhs_T_explicit, dtype=np.float64)
            rhs_E_full = np.asarray(rhs_E_explicit, dtype=np.float64)
            rhs_B_full = np.asarray(rhs_B_explicit, dtype=np.float64)

        if tca_active:
            assert rhs_T_explicit is not None and rhs_E_explicit is not None
            slot = _ell2_m0_slot_offset(self.config.L_max)
            S_T = float(rhs_T_explicit[slot]) / snapshot.background.a_val * (-1.0)
            S_E = float(rhs_E_explicit[slot]) / snapshot.background.a_val * (-1.0)
            theta_2_alg, e_2_alg = self._solve_tca_scalars(
                S_T=S_T,
                S_E=S_E,
                gamma_t=float(snapshot.gamma_t),
                H_local=float(snapshot.h_local),
            )
            current_pi2 = float(photon_T.tensors[2].components[2])
            current_e2 = float(photon_E.E.tensors[2].components[2])
            relax_rate = snapshot.background.a_val * float(snapshot.gamma_t)
            rhs_T_full = np.asarray(rhs_T_full, dtype=np.float64).copy()
            rhs_E_full = np.asarray(rhs_E_full, dtype=np.float64).copy()
            rhs_T_full[slot] = -relax_rate * (current_pi2 - theta_2_alg)
            rhs_E_full[slot] = -relax_rate * (current_e2 - e_2_alg)

        if tca_tracker is not None:
            tca_tracker.append(bool(tca_active))

        return (
            (
                np.asarray(rhs_T_explicit, dtype=np.float64)
                if rhs_T_explicit is not None
                else np.asarray(rhs_T_full, dtype=np.float64)
            ),
            (
                np.asarray(rhs_E_explicit, dtype=np.float64)
                if rhs_E_explicit is not None
                else np.asarray(rhs_E_full, dtype=np.float64)
            ),
            (
                np.asarray(rhs_B_explicit, dtype=np.float64)
                if rhs_B_explicit is not None
                else np.asarray(rhs_B_full, dtype=np.float64)
            ),
            np.asarray(rhs_T_full, dtype=np.float64),
            np.asarray(rhs_E_full, dtype=np.float64),
            np.asarray(rhs_B_full, dtype=np.float64),
            np.asarray(rhs_nu, dtype=np.float64),
        )

    def _collisionless_photon_rhs(
        self,
        *,
        photon_T: PSTFHierarchyState,
        photon_E: PolarizationHierarchyState,
        background,
    ) -> tuple[np.ndarray, np.ndarray]:
        rhs_T = hierarchy_rhs_photon_from_state(
            photon_T,
            background=background,
            closure=self.closure,
            collision=_ZERO_COLLISION,
            collision_aux=None,
        )
        rhs_E = hierarchy_rhs_photon_from_state(
            photon_E.E,
            background=background,
            closure=self.closure,
            collision=_ZERO_COLLISION,
            collision_aux=None,
        )
        return rhs_T, rhs_E

    def _radiation_rhs_components(
        self,
        *,
        photon_T: PSTFHierarchyState,
        photon_E: PolarizationHierarchyState,
        photon_B: PSTFHierarchyState,
        neutrino_tower: PSTFHierarchyState,
        background,
        collision_aux: _ProjectedCollisionAux | None,
    ) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
        rhs_T = hierarchy_rhs_photon_from_state(
            photon_T,
            background=background,
            closure=self.closure,
            collision=self._temperature_collision if collision_aux is not None else _ZERO_COLLISION,
            collision_aux=collision_aux,
        )
        rhs_E = hierarchy_rhs_photon_from_state(
            photon_E.E,
            background=background,
            closure=self.closure,
            collision=self._e_collision if collision_aux is not None else _ZERO_COLLISION,
            collision_aux=collision_aux,
        )
        rhs_B = hierarchy_rhs_photon_from_state(
            photon_B,
            background=background,
            closure=self.closure,
            collision=self._b_collision if collision_aux is not None else _ZERO_COLLISION,
            collision_aux=collision_aux,
        )
        rhs_nu = hierarchy_rhs_neutrino_from_state(
            neutrino_tower,
            background=background,
            closure=self.closure,
            neutrino_background=self._neutrino_background,
        )
        return rhs_T, rhs_E, rhs_B, rhs_nu

    def _local_matter_rhs(
        self,
        *,
        snapshot: _EtaRuntimeSnapshot,
        baryon_local: np.ndarray,
        cdm_local: np.ndarray,
        theta_1: float,
        theta_1_dot: float,
    ) -> tuple[np.ndarray, np.ndarray]:
        baryon_row = np.asarray(baryon_local, dtype=np.float64)
        cdm_row = np.asarray(cdm_local, dtype=np.float64)
        if baryon_row.shape != (_BARYON_LOCAL_DOF,):
            raise ValueError("baryon_local must have shape (4,)")
        if cdm_row.shape != (_CDM_LOCAL_DOF,):
            raise ValueError("cdm_local must have shape (2,)")

        baryon_state = BaryonFluidState(
            delta_b=float(baryon_row[0]),
            v_b=float(baryon_row[1]),
            axis=SymmetryAxis.X,
        )
        cdm_state = CDMFluidState(
            delta_c=float(cdm_row[0]),
            v_c=float(cdm_row[1]),
            axis=SymmetryAxis.X,
        )
        photon = self.species[SpeciesLabel.PHOTON]
        baryon = self.species[SpeciesLabel.BARYON]
        rho_b = max(float(baryon.rho_rest(float(snapshot.eta))), 1.0e-30)
        rho_gamma = max(float(photon.rho_rest(float(snapshot.eta))), 1.0e-30)
        baryon_params = BaryonParameters(
            R_b=max(3.0 * rho_b / (4.0 * rho_gamma), 1.0e-30),
            tau_dot=max(float(snapshot.gamma_t), 0.0),
            H=max(float(snapshot.h_local), 0.0),
        )
        cdm_params = CDMParameters(H=max(float(snapshot.h_local), 0.0))
        delta_b_dot = baryon_continuity_rhs(
            baryon_state,
            0.0,
            self.canonical_decision,
        )
        v_b_dot = baryon_euler_rhs(
            baryon_state,
            float(theta_1),
            baryon_params,
            self.canonical_decision,
        )
        delta_c_dot = cdm_continuity_rhs(
            cdm_state,
            0.0,
            self.canonical_decision,
        )
        v_c_dot = cdm_euler_rhs(
            cdm_state,
            cdm_params,
            self.canonical_decision,
        )
        baryon_rhs = np.array(
            [
                float(delta_b_dot),
                float(v_b_dot),
                float(v_b_dot),
                float(3.0 * theta_1_dot - v_b_dot),
            ],
            dtype=np.float64,
        )
        cdm_rhs = np.array(
            [float(delta_c_dot), float(v_c_dot)],
            dtype=np.float64,
        )
        return baryon_rhs, cdm_rhs

    def _residual_mode_label_local_rhs(
        self,
        *,
        snapshot: _EtaRuntimeSnapshot,
        photon_T: PSTFHierarchyState,
        photon_E: PolarizationHierarchyState,
        photon_B: PSTFHierarchyState,
        neutrino_tower: PSTFHierarchyState,
        baryon_local: np.ndarray,
        cdm_local: np.ndarray,
        residual_local: np.ndarray,
        residual_harmonic: np.ndarray,
    ) -> np.ndarray:
        if self._residual_local_dof == 0:
            return np.zeros(0, dtype=np.float64)
        affine = self._build_residual_local_affine_operator(
            snapshot=snapshot,
            photon_T=photon_T,
            residual_harmonic=residual_harmonic,
        )
        return np.asarray(
            affine.matrix @ np.asarray(residual_local, dtype=np.float64) + affine.bias,
            dtype=np.float64,
        )

    def _residual_local_theta_1_by_mode_label(
        self,
        *,
        photon_T: PSTFHierarchyState,
        residual_harmonic: np.ndarray,
    ) -> dict[str, float]:
        photon_t_residual, _photon_e_residual, _photon_b_residual, _neutrino_residual = (
            self._split_residual_harmonic_state(residual_harmonic)
        )
        theta_1_by_mode_label = {
            self._layout_covered_mode_label: float(_theta_1_from_temperature_state(photon_T))
        }
        for mu in self._residual_mode_labels:
            mu_key = str(mu)
            theta_1_by_mode_label[mu_key] = float(
                self._theta_1_photon_m0(np.asarray(photon_t_residual[mu_key], dtype=np.float64))
            )
        return theta_1_by_mode_label

    def _build_residual_local_affine_operator(
        self,
        *,
        snapshot: _EtaRuntimeSnapshot,
        photon_T: PSTFHierarchyState,
        residual_harmonic: np.ndarray,
    ) -> ReducedLocalAffineOperator:
        background_state = {
            "branch": str(self.background_monitor.branch),
            "geometry": self.background_monitor.initial_conditions.geometry,
            "sigma_tensor": self._sigma_tensor_at_eta(float(snapshot.eta)),
            "opacity_data": {"Gamma_T": float(snapshot.gamma_t)},
        }
        return build_reduced_local_affine_operator(
            self._layout,
            background_state,
            self.backend,
            residual_mode_labels=self._residual_mode_labels,
            theta_1_by_mode_label=self._residual_local_theta_1_by_mode_label(
                photon_T=photon_T,
                residual_harmonic=residual_harmonic,
            ),
        )

    def _residual_harmonic_background_state(
        self,
        *,
        snapshot: _EtaRuntimeSnapshot,
    ) -> dict[str, object]:
        return {
            "branch": str(self.background_monitor.branch),
            "geometry": self.background_monitor.initial_conditions.geometry,
            "sigma_tensor": self._sigma_tensor_at_eta(float(snapshot.eta)),
            "opacity_data": {"Gamma_T": float(snapshot.gamma_t)},
            "source_tables": {
                "reionization_amplitude": float(self._reionization_amplitude()),
            },
        }

    def _build_residual_joint_affine_operator(
        self,
        *,
        snapshot: _EtaRuntimeSnapshot,
        photon_T: PSTFHierarchyState,
        photon_E: PolarizationHierarchyState,
        photon_B: PSTFHierarchyState,
        neutrino_tower: PSTFHierarchyState,
        baryon_local: np.ndarray,
        source_local: np.ndarray | None,
    ) -> ReducedJointAffineOperator:
        covered = str(self._layout_covered_mode_label)
        kwargs = {}
        if source_local is not None:
            kwargs["source_by_mode_label"] = {covered: np.asarray(source_local, dtype=np.float64)}
        return self.backend.build_reduced_joint_affine_operator(
            self._residual_harmonic_background_state(snapshot=snapshot),
            residual_mode_labels=self._residual_mode_labels,
            photon_T_by_mode_label={covered: np.asarray(pack_hierarchy(photon_T), dtype=np.float64)},
            photon_E_by_mode_label={covered: np.asarray(pack_hierarchy(photon_E.E), dtype=np.float64)},
            photon_B_by_mode_label={covered: np.asarray(pack_hierarchy(photon_B), dtype=np.float64)},
            neutrino_by_mode_label={covered: np.asarray(pack_hierarchy(neutrino_tower), dtype=np.float64)},
            baryon_by_mode_label={covered: np.asarray(baryon_local, dtype=np.float64)},
            **kwargs,
        )

    def _build_covered_source_affine_operator(
        self,
        *,
        snapshot: _EtaRuntimeSnapshot,
        photon_T: PSTFHierarchyState,
        photon_E: PolarizationHierarchyState,
        photon_B: PSTFHierarchyState,
    ):
        covered = str(self._layout_covered_mode_label)
        return self.backend.build_reduced_source_affine_operator(
            self._residual_harmonic_background_state(snapshot=snapshot),
            mode_labels=(covered,),
            photon_T_by_mode_label={covered: np.asarray(pack_hierarchy(photon_T), dtype=np.float64)},
            photon_E_by_mode_label={covered: np.asarray(pack_hierarchy(photon_E.E), dtype=np.float64)},
            photon_B_by_mode_label={covered: np.asarray(pack_hierarchy(photon_B), dtype=np.float64)},
        )

    def _exact_covered_source_rhs(
        self,
        *,
        snapshot: _EtaRuntimeSnapshot,
        photon_T: PSTFHierarchyState,
        photon_E: PolarizationHierarchyState,
        photon_B: PSTFHierarchyState,
        source_local: np.ndarray,
    ) -> np.ndarray:
        affine = self._build_covered_source_affine_operator(
            snapshot=snapshot,
            photon_T=photon_T,
            photon_E=photon_E,
            photon_B=photon_B,
        )
        return np.asarray(
            affine.matrix @ np.asarray(source_local, dtype=np.float64) + affine.bias,
            dtype=np.float64,
        )

    def _exact_residual_joint_rhs(
        self,
        *,
        snapshot: _EtaRuntimeSnapshot,
        photon_T: PSTFHierarchyState,
        photon_E: PolarizationHierarchyState,
        photon_B: PSTFHierarchyState,
        neutrino_tower: PSTFHierarchyState,
        baryon_local: np.ndarray,
        source_local: np.ndarray,
        residual_local: np.ndarray,
        residual_harmonic: np.ndarray,
        residual_source: np.ndarray,
    ) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
        affine = self._build_residual_joint_affine_operator(
            snapshot=snapshot,
            photon_T=photon_T,
            photon_E=photon_E,
            photon_B=photon_B,
            neutrino_tower=neutrino_tower,
            baryon_local=baryon_local,
            source_local=source_local,
        )
        rhs = np.asarray(
            affine.matrix
            @ np.concatenate(
                [
                    np.asarray(residual_local, dtype=np.float64),
                    np.asarray(residual_harmonic, dtype=np.float64),
                    np.asarray(residual_source, dtype=np.float64),
                ],
                dtype=np.float64,
            )
            + affine.bias,
            dtype=np.float64,
        )
        return (
            np.asarray(rhs[: self._residual_local_dof], dtype=np.float64),
            np.asarray(
                rhs[
                    self._residual_local_dof : self._residual_local_dof + self._residual_harmonic_dof
                ],
                dtype=np.float64,
            ),
            np.asarray(rhs[self._residual_local_dof + self._residual_harmonic_dof :], dtype=np.float64),
        )

    def _solve_startup_residual_joint_state(
        self,
        *,
        snapshot: _EtaRuntimeSnapshot,
        photon_T: PSTFHierarchyState,
        photon_E: PolarizationHierarchyState,
        photon_B: PSTFHierarchyState,
        neutrino_tower: PSTFHierarchyState,
        baryon_local: np.ndarray,
        source_local: np.ndarray,
    ) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
        joint_dof = self._residual_local_dof + self._residual_harmonic_dof + self._residual_source_dof
        if joint_dof == 0 or str(self.config.solver_method).upper() != "IMEX_MIDPOINT_BDF":
            return (
                np.zeros(self._residual_local_dof, dtype=np.float64),
                np.zeros(self._residual_harmonic_dof, dtype=np.float64),
                np.zeros(self._residual_source_dof, dtype=np.float64),
            )
        affine = self._build_residual_joint_affine_operator(
            snapshot=snapshot,
            photon_T=photon_T,
            photon_E=photon_E,
            photon_B=photon_B,
            neutrino_tower=neutrino_tower,
            baryon_local=baryon_local,
            source_local=source_local,
        )
        total_span = max(float(self.config.eta_final_mpc - self.config.eta_initial_mpc), 1.0e-12)
        startup_dt = max(
            total_span / (100000.0 if abs(float(self.config.tilt_rapidity)) > 0.0 else 5000.0),
            1.0e-8,
        )
        system = self._residual_joint_sparse_identity - startup_dt * affine.matrix
        lu = splu(system)
        startup_state = np.asarray(
            lu.solve(startup_dt * np.asarray(affine.bias, dtype=np.float64)),
            dtype=np.float64,
        )
        return (
            np.asarray(startup_state[: self._residual_local_dof], dtype=np.float64),
            np.asarray(
                startup_state[
                    self._residual_local_dof : self._residual_local_dof + self._residual_harmonic_dof
                ],
                dtype=np.float64,
            ),
            np.asarray(startup_state[self._residual_local_dof + self._residual_harmonic_dof :], dtype=np.float64),
        )

    def _orthogonal_residual_joint_ros2_step(
        self,
        *,
        eta_left: float,
        y_left: np.ndarray,
        eta_right: float,
        y_right: np.ndarray,
        affine_left: ReducedJointAffineOperator | None = None,
    ) -> tuple[np.ndarray, ReducedJointAffineOperator | None]:
        joint_dof = self._residual_local_dof + self._residual_harmonic_dof + self._residual_source_dof
        if joint_dof == 0:
            return np.asarray(y_right, dtype=np.float64), None
        dt = float(eta_right - eta_left)
        if dt == 0.0:
            return np.asarray(y_right, dtype=np.float64), affine_left
        (
            photon_T_left,
            photon_E_left,
            photon_B_left,
            neutrino_left,
            baryon_left,
            cdm_left,
            source_left,
            residual_local_left,
            residual_harmonic_left,
            residual_source_left,
        ) = _unpack_radiation_state(
            y_left,
            self.config.L_max,
            residual_local_dof=self._residual_local_dof,
            residual_harmonic_dof=self._residual_harmonic_dof,
            residual_source_dof=self._residual_source_dof,
        )
        (
            photon_T_right,
            photon_E_right,
            photon_B_right,
            neutrino_right,
            baryon_right,
            cdm_right,
            source_right,
            _residual_local_right,
            _residual_harmonic_right,
            _residual_source_right,
        ) = _unpack_radiation_state(
            y_right,
            self.config.L_max,
            residual_local_dof=self._residual_local_dof,
            residual_harmonic_dof=self._residual_harmonic_dof,
            residual_source_dof=self._residual_source_dof,
        )
        snapshot_left = self._eta_runtime_snapshot(float(eta_left))
        snapshot_right = self._eta_runtime_snapshot(float(eta_right))
        if affine_left is None:
            affine_left = self._build_residual_joint_affine_operator(
                snapshot=snapshot_left,
                photon_T=photon_T_left,
                photon_E=photon_E_left,
                photon_B=photon_B_left,
                neutrino_tower=neutrino_left,
                baryon_local=baryon_left,
                source_local=source_left,
            )
        state_left = np.concatenate(
            [
                np.asarray(residual_local_left, dtype=np.float64),
                np.asarray(residual_harmonic_left, dtype=np.float64),
                np.asarray(residual_source_left, dtype=np.float64),
            ],
            dtype=np.float64,
        )
        system_left = self._residual_joint_sparse_identity - (dt * _ROS2_GAMMA) * affine_left.matrix
        lu_left = splu(system_left)
        rhs_left = np.asarray(affine_left.matrix @ state_left + affine_left.bias, dtype=np.float64)
        k1 = np.asarray(lu_left.solve(dt * _ROS2_GAMMA * rhs_left), dtype=np.float64)
        stage_state = state_left + _ROS2_A21 * k1
        affine_right = self._build_residual_joint_affine_operator(
            snapshot=snapshot_right,
            photon_T=photon_T_right,
            photon_E=photon_E_right,
            photon_B=photon_B_right,
            neutrino_tower=neutrino_right,
            baryon_local=baryon_right,
            source_local=source_right,
        )
        rhs_stage = np.asarray(affine_right.matrix @ stage_state + affine_right.bias, dtype=np.float64)
        system_right = self._residual_joint_sparse_identity - (dt * _ROS2_GAMMA) * affine_right.matrix
        lu_right = splu(system_right)
        k2 = np.asarray(
            lu_right.solve(dt * _ROS2_GAMMA * rhs_stage + (_ROS2_GAMMA * _ROS2_C21) * k1),
            dtype=np.float64,
        )
        next_state = state_left + _ROS2_M1 * k1 + _ROS2_M2 * k2
        next_local = np.asarray(next_state[: self._residual_local_dof], dtype=np.float64)
        next_harmonic = np.asarray(
            next_state[
                self._residual_local_dof : self._residual_local_dof + self._residual_harmonic_dof
            ],
            dtype=np.float64,
        )
        next_source = np.asarray(
            next_state[self._residual_local_dof + self._residual_harmonic_dof :],
            dtype=np.float64,
        )
        return (
            _pack_radiation_state(
                photon_T=photon_T_right,
                photon_E=photon_E_right,
                photon_B=photon_B_right,
                neutrino_tower=neutrino_right,
                baryon_local=baryon_right,
                cdm_local=cdm_right,
                source_local=source_right,
                residual_local=next_local,
                residual_harmonic=next_harmonic,
                residual_source=next_source,
            ),
            affine_right,
        )

    def _orthogonal_covered_source_ros2_step(
        self,
        *,
        eta_left: float,
        y_left: np.ndarray,
        eta_right: float,
        y_right: np.ndarray,
        affine_left=None,
    ) -> tuple[np.ndarray, object | None]:
        if _SOURCE_LOCAL_DOF == 0:
            return np.asarray(y_right, dtype=np.float64), affine_left
        dt = float(eta_right - eta_left)
        if dt == 0.0:
            return np.asarray(y_right, dtype=np.float64), affine_left
        (
            photon_T_left,
            photon_E_left,
            photon_B_left,
            neutrino_left,
            baryon_left,
            cdm_left,
            source_left,
            residual_local_left,
            residual_harmonic_left,
            residual_source_left,
        ) = _unpack_radiation_state(
            y_left,
            self.config.L_max,
            residual_local_dof=self._residual_local_dof,
            residual_harmonic_dof=self._residual_harmonic_dof,
            residual_source_dof=self._residual_source_dof,
        )
        (
            photon_T_right,
            photon_E_right,
            photon_B_right,
            neutrino_right,
            baryon_right,
            cdm_right,
            _source_right,
            residual_local_right,
            residual_harmonic_right,
            residual_source_right,
        ) = _unpack_radiation_state(
            y_right,
            self.config.L_max,
            residual_local_dof=self._residual_local_dof,
            residual_harmonic_dof=self._residual_harmonic_dof,
            residual_source_dof=self._residual_source_dof,
        )
        snapshot_left = self._eta_runtime_snapshot(float(eta_left))
        snapshot_right = self._eta_runtime_snapshot(float(eta_right))
        if affine_left is None:
            affine_left = self._build_covered_source_affine_operator(
                snapshot=snapshot_left,
                photon_T=photon_T_left,
                photon_E=photon_E_left,
                photon_B=photon_B_left,
            )
        system_left = csc_matrix(np.eye(_SOURCE_LOCAL_DOF, dtype=np.float64)) - (dt * _ROS2_GAMMA) * affine_left.matrix
        lu_left = splu(system_left)
        rhs_left = np.asarray(
            affine_left.matrix @ np.asarray(source_left, dtype=np.float64) + affine_left.bias,
            dtype=np.float64,
        )
        k1 = np.asarray(lu_left.solve(dt * _ROS2_GAMMA * rhs_left), dtype=np.float64)
        stage_state = np.asarray(source_left, dtype=np.float64) + _ROS2_A21 * k1
        affine_right = self._build_covered_source_affine_operator(
            snapshot=snapshot_right,
            photon_T=photon_T_right,
            photon_E=photon_E_right,
            photon_B=photon_B_right,
        )
        rhs_stage = np.asarray(affine_right.matrix @ stage_state + affine_right.bias, dtype=np.float64)
        system_right = csc_matrix(np.eye(_SOURCE_LOCAL_DOF, dtype=np.float64)) - (dt * _ROS2_GAMMA) * affine_right.matrix
        lu_right = splu(system_right)
        k2 = np.asarray(
            lu_right.solve(dt * _ROS2_GAMMA * rhs_stage + (_ROS2_GAMMA * _ROS2_C21) * k1),
            dtype=np.float64,
        )
        next_source = np.asarray(source_left, dtype=np.float64) + _ROS2_M1 * k1 + _ROS2_M2 * k2
        return (
            _pack_radiation_state(
                photon_T=photon_T_right,
                photon_E=photon_E_right,
                photon_B=photon_B_right,
                neutrino_tower=neutrino_right,
                baryon_local=baryon_right,
                cdm_local=cdm_right,
                source_local=next_source,
                residual_local=residual_local_right,
                residual_harmonic=residual_harmonic_right,
                residual_source=residual_source_right,
            ),
            affine_right,
        )

    def _rhs(
        self,
        eta: float,
        y: np.ndarray,
        *,
        tca_tracker: list[bool] | None = None,
    ) -> np.ndarray:
        (
            photon_T,
            photon_E,
            photon_B,
            neutrino_tower,
            baryon_local,
            cdm_local,
            source_local,
            residual_local,
            residual_harmonic,
            residual_source,
        ) = _unpack_radiation_state(
            y,
            self.config.L_max,
            residual_local_dof=self._residual_local_dof,
            residual_harmonic_dof=self._residual_harmonic_dof,
            residual_source_dof=self._residual_source_dof,
        )
        snapshot = self._eta_runtime_snapshot(float(eta))
        _, _, _, rhs_T, rhs_E, rhs_B, rhs_nu = self._rhs_components_from_snapshot(
            photon_T=photon_T,
            photon_E=photon_E,
            photon_B=photon_B,
            neutrino_tower=neutrino_tower,
            baryon_local=baryon_local,
            snapshot=snapshot,
            need_explicit=False,
            need_full=True,
            tca_tracker=tca_tracker,
        )
        baryon_rhs, cdm_rhs = self._local_matter_rhs(
            snapshot=snapshot,
            baryon_local=baryon_local,
            cdm_local=cdm_local,
            theta_1=_theta_1_from_temperature_state(photon_T),
            theta_1_dot=float(rhs_T[sum(2 * ell + 1 for ell in range(1)) + 1]) if self.config.L_max >= 1 else 0.0,
        )
        if str(self.config.solver_method).upper() != "IMEX_MIDPOINT_BDF":
            source_rhs = self._exact_covered_source_rhs(
                snapshot=snapshot,
                photon_T=photon_T,
                photon_E=photon_E,
                photon_B=photon_B,
                source_local=source_local,
            )
        else:
            source_rhs = np.zeros(_SOURCE_LOCAL_DOF, dtype=np.float64)
        if str(self.config.solver_method).upper() != "IMEX_MIDPOINT_BDF":
            residual_rhs, residual_harmonic_rhs, residual_source_rhs = self._exact_residual_joint_rhs(
                snapshot=snapshot,
                photon_T=photon_T,
                photon_E=photon_E,
                photon_B=photon_B,
                neutrino_tower=neutrino_tower,
                baryon_local=baryon_local,
                source_local=source_local,
                residual_local=residual_local,
                residual_harmonic=residual_harmonic,
                residual_source=residual_source,
            )
        else:
            residual_rhs = self._residual_mode_label_local_rhs(
                snapshot=snapshot,
                photon_T=photon_T,
                photon_E=photon_E,
                photon_B=photon_B,
                neutrino_tower=neutrino_tower,
                baryon_local=baryon_local,
                cdm_local=cdm_local,
                residual_local=residual_local,
                residual_harmonic=residual_harmonic,
            )
            residual_harmonic_rhs = np.zeros(self._residual_harmonic_dof, dtype=np.float64)
            residual_source_rhs = np.zeros(self._residual_source_dof, dtype=np.float64)
        return np.concatenate(
            [
                rhs_T,
                rhs_E,
                rhs_B,
                rhs_nu,
                baryon_rhs,
                cdm_rhs,
                source_rhs,
                residual_rhs,
                residual_harmonic_rhs,
                residual_source_rhs,
            ]
        )

    def _explicit_rhs(self, eta: float, y: np.ndarray) -> np.ndarray:
        (
            photon_T,
            photon_E,
            photon_B,
            neutrino_tower,
            baryon_local,
            cdm_local,
            source_local,
            residual_local,
            residual_harmonic,
            residual_source,
        ) = _unpack_radiation_state(
            y,
            self.config.L_max,
            residual_local_dof=self._residual_local_dof,
            residual_harmonic_dof=self._residual_harmonic_dof,
            residual_source_dof=self._residual_source_dof,
        )
        snapshot = self._eta_runtime_snapshot(float(eta))
        rhs_T, rhs_E, rhs_B, _, _, _, rhs_nu = self._rhs_components_from_snapshot(
            photon_T=photon_T,
            photon_E=photon_E,
            photon_B=photon_B,
            neutrino_tower=neutrino_tower,
            baryon_local=baryon_local,
            snapshot=snapshot,
            need_explicit=True,
            need_full=False,
        )
        return np.concatenate(
            [
                rhs_T,
                rhs_E,
                rhs_B,
                rhs_nu,
                np.zeros(_PRIMARY_LOCAL_DOF, dtype=np.float64),
                np.zeros(self._residual_local_dof, dtype=np.float64),
                np.zeros(self._residual_harmonic_dof, dtype=np.float64),
                np.zeros(self._residual_source_dof, dtype=np.float64),
            ]
        )

    def _implicit_rhs(
        self,
        eta: float,
        y: np.ndarray,
        *,
        tca_tracker: list[bool] | None = None,
    ) -> np.ndarray:
        (
            photon_T,
            photon_E,
            photon_B,
            neutrino_tower,
            baryon_local,
            cdm_local,
            source_local,
            residual_local,
            residual_harmonic,
            residual_source,
        ) = _unpack_radiation_state(
            y,
            self.config.L_max,
            residual_local_dof=self._residual_local_dof,
            residual_harmonic_dof=self._residual_harmonic_dof,
            residual_source_dof=self._residual_source_dof,
        )
        snapshot = self._eta_runtime_snapshot(float(eta))
        rhs_T_explicit, rhs_E_explicit, rhs_B_explicit, rhs_T_full, rhs_E_full, rhs_B_full, rhs_nu = (
            self._rhs_components_from_snapshot(
            photon_T=photon_T,
            photon_E=photon_E,
            photon_B=photon_B,
            neutrino_tower=neutrino_tower,
            baryon_local=baryon_local,
            snapshot=snapshot,
            need_explicit=True,
            need_full=True,
            tca_tracker=tca_tracker,
        ))
        implicit = np.concatenate(
            [
                np.asarray(rhs_T_full - rhs_T_explicit, dtype=np.float64),
                np.asarray(rhs_E_full - rhs_E_explicit, dtype=np.float64),
                np.asarray(rhs_B_full - rhs_B_explicit, dtype=np.float64),
                np.zeros_like(rhs_nu),
                np.zeros(_PRIMARY_LOCAL_DOF, dtype=np.float64),
                np.zeros(self._residual_local_dof, dtype=np.float64),
                np.zeros(self._residual_harmonic_dof, dtype=np.float64),
                np.zeros(self._residual_source_dof, dtype=np.float64),
            ]
        )
        tower_size = _tower_size(self.config.L_max)
        implicit[3 * tower_size :] = 0.0
        baryon_rhs, cdm_rhs = self._local_matter_rhs(
            snapshot=snapshot,
            baryon_local=baryon_local,
            cdm_local=cdm_local,
            theta_1=_theta_1_from_temperature_state(photon_T),
            theta_1_dot=float(rhs_T_full[sum(2 * ell + 1 for ell in range(1)) + 1]) if self.config.L_max >= 1 else 0.0,
        )
        implicit[4 * tower_size : 4 * tower_size + _BARYON_LOCAL_DOF] = baryon_rhs
        implicit[4 * tower_size + _BARYON_LOCAL_DOF : 4 * tower_size + _LOCAL_MATTER_DOF] = cdm_rhs
        return implicit

    def _orthogonal_implicit_step(
        self,
        *,
        eta: float,
        stage: np.ndarray,
        dt: float,
        tca_tracker: list[bool],
    ) -> np.ndarray:
        (
            photon_T,
            photon_E,
            photon_B,
            neutrino_tower,
            baryon_local,
            cdm_local,
            source_local,
            residual_local,
            residual_harmonic,
            residual_source,
        ) = _unpack_radiation_state(
            stage,
            self.config.L_max,
            residual_local_dof=self._residual_local_dof,
            residual_harmonic_dof=self._residual_harmonic_dof,
            residual_source_dof=self._residual_source_dof,
        )
        background = self._background_snapshot(float(eta))
        gamma_t = _resolved_gamma_t(
            eta=float(eta),
            direction=self._direction,
            visibility_source=self.visibility_source,
            config=self.config,
        )
        H_local = self._h_local_at(float(eta))
        tca_active = bool(
            isinstance(self.closure, TCAClosure)
            and gamma_t > 0.0
            and H_local > 0.0
            and gamma_t / H_local > self.config.gamma_T_over_H_threshold
        )
        tca_tracker.append(tca_active)
        if gamma_t <= 0.0:
            return stage.copy()

        gamma_dt = float(dt) * float(gamma_t)
        out_T = photon_T.copy()
        out_E = photon_E.E.copy()
        out_B = photon_B.copy()
        coll_T_diag = self._coll_T_diag
        coll_E_diag = self._coll_E_diag
        coll_B_diag = self._coll_B_diag

        if self.config.L_max >= 1:
            if coll_T_diag is None:
                dipole_dt = np.full_like(photon_T.tensors[1].components, gamma_dt, dtype=np.float64)
            else:
                base = sum(2 * l + 1 for l in range(1))
                dipole_dt = float(dt) * np.asarray(coll_T_diag[base : base + 3], dtype=np.float64)
            out_T.tensors[1].components = photon_T.tensors[1].components / (1.0 + dipole_dt)

        ell2_has_tca_override = False
        if self.config.L_max >= 2:
            A11 = 1.0 - gamma_dt * THOMSON_ELL2_SELF_COEFF
            A12 = -gamma_dt * THOMSON_ELL2_POLARIZATION_COEFF
            A21 = -gamma_dt * E_MODE_ELL2_TEMPERATURE_COEFF
            A22 = 1.0 - gamma_dt * E_MODE_ELL2_SELF_COEFF
            det = A11 * A22 - A12 * A21
            if abs(det) <= 1.0e-30:
                raise RuntimeError("orthogonal implicit ell=2 solve became singular")
            T2_rhs = np.asarray(photon_T.tensors[2].components, dtype=np.float64)
            E2_rhs = np.asarray(photon_E.E.tensors[2].components, dtype=np.float64)
            out_T.tensors[2].components = (A22 * T2_rhs - A12 * E2_rhs) / det
            out_E.tensors[2].components = (-A21 * T2_rhs + A11 * E2_rhs) / det
            if coll_B_diag is None:
                B2_dt = np.full_like(photon_B.tensors[2].components, gamma_dt, dtype=np.float64)
            else:
                base = sum(2 * l + 1 for l in range(2))
                B2_dt = float(dt) * np.asarray(coll_B_diag[base : base + 5], dtype=np.float64)
            out_B.tensors[2].components = photon_B.tensors[2].components / (1.0 + B2_dt)

            if tca_active:
                rhs_T_free, rhs_E_free = self._collisionless_photon_rhs(
                    photon_T=photon_T,
                    photon_E=photon_E,
                    background=background,
                )
                slot = _ell2_m0_slot_offset(self.config.L_max)
                S_T = float(rhs_T_free[slot]) / background.a_val * (-1.0)
                S_E = float(rhs_E_free[slot]) / background.a_val * (-1.0)
                theta_2_alg, e_2_alg = self._solve_tca_scalars(
                    S_T=S_T,
                    S_E=S_E,
                    gamma_t=float(gamma_t),
                    H_local=float(H_local),
                )
                relax_rate = background.a_val * float(gamma_t)
                relax_dt = float(dt) * float(relax_rate)
                out_T.tensors[2].components[2] = (
                    photon_T.tensors[2].components[2] + relax_dt * theta_2_alg
                ) / (1.0 + relax_dt)
                out_E.tensors[2].components[2] = (
                    photon_E.E.tensors[2].components[2] + relax_dt * e_2_alg
                ) / (1.0 + relax_dt)
                ell2_has_tca_override = True

        for ell in range(3, self.config.L_max + 1):
            base = sum(2 * l + 1 for l in range(ell))
            width = 2 * ell + 1
            if coll_T_diag is None:
                T_dt = np.full(width, gamma_dt, dtype=np.float64)
            else:
                T_dt = float(dt) * np.asarray(coll_T_diag[base : base + width], dtype=np.float64)
            if coll_E_diag is None:
                E_dt = np.full(width, gamma_dt, dtype=np.float64)
            else:
                E_dt = float(dt) * np.asarray(coll_E_diag[base : base + width], dtype=np.float64)
            if coll_B_diag is None:
                B_dt = np.full(width, gamma_dt, dtype=np.float64)
            else:
                B_dt = float(dt) * np.asarray(coll_B_diag[base : base + width], dtype=np.float64)
            out_T.tensors[ell].components = photon_T.tensors[ell].components / (1.0 + T_dt)
            out_E.tensors[ell].components = photon_E.E.tensors[ell].components / (1.0 + E_dt)
            out_B.tensors[ell].components = photon_B.tensors[ell].components / (1.0 + B_dt)

        if self.config.L_max >= 2 and ell2_has_tca_override:
            # TCA ownership replaces only the m=0 quadrupole entry; keep the
            # non-m0 entries on the exact orthogonal Thomson solve above.
            pass

        baryon_next = np.asarray(baryon_local, dtype=np.float64).copy()
        cdm_next = np.asarray(cdm_local, dtype=np.float64).copy()
        theta_left = float(baryon_local[2] + baryon_local[3]) / 3.0
        theta_right = _theta_1_from_temperature_state(out_T)
        photon = self.species[SpeciesLabel.PHOTON]
        baryon = self.species[SpeciesLabel.BARYON]
        rho_b = max(float(baryon.rho_rest(float(eta))), 1.0e-30)
        rho_gamma = max(float(photon.rho_rest(float(eta))), 1.0e-30)
        drag = max(float(gamma_t), 0.0) / max(3.0 * rho_b / (4.0 * rho_gamma), 1.0e-30)
        lambda_b = max(float(H_local), 0.0) + drag
        forcing_left = 3.0 * drag * theta_left
        forcing_right = 3.0 * drag * theta_right
        baryon_v_next = (
            float(baryon_local[1]) + 0.5 * float(dt) * (forcing_left - lambda_b * float(baryon_local[1]) + forcing_right)
        ) / max(1.0 + 0.5 * float(dt) * lambda_b, 1.0e-30)
        baryon_next[1] = float(baryon_v_next)
        baryon_next[2] = float(baryon_v_next)
        baryon_next[3] = float(3.0 * theta_right - baryon_v_next)
        cdm_lambda = max(float(H_local), 0.0)
        cdm_v_next = float(cdm_local[1]) * max(1.0 - 0.5 * float(dt) * cdm_lambda, 0.0) / max(
            1.0 + 0.5 * float(dt) * cdm_lambda,
            1.0e-30,
        )
        cdm_next[1] = float(cdm_v_next)

        return _pack_radiation_state(
            photon_T=out_T,
            photon_E=PolarizationHierarchyState(E=out_E),
            photon_B=out_B,
            neutrino_tower=neutrino_tower,
            baryon_local=baryon_next,
            cdm_local=cdm_next,
            source_local=source_local,
            residual_local=residual_local,
            residual_harmonic=residual_harmonic,
            residual_source=residual_source,
        )

    def _solve_tca_scalars(
        self,
        *,
        S_T: float,
        S_E: float,
        gamma_t: float,
        H_local: float,
    ) -> tuple[float, float]:
        if not isinstance(self.closure, TCAClosure):
            raise RuntimeError("TCA scalar solve requires TCAClosure")
        if H_local <= 0.0 or not np.isfinite(H_local):
            raise ValueError(f"H_local must be positive finite, got {H_local}")
        if not np.isfinite(gamma_t) or gamma_t <= 0.0:
            raise ValueError(f"gamma_t must be positive finite, got {gamma_t}")
        if gamma_t / H_local < self.closure.gamma_threshold_over_H:
            raise RuntimeError(
                f"TCA inactive: Γ_T/H = {gamma_t / H_local:.3e} < threshold "
                f"{self.closure.gamma_threshold_over_H:.3e}"
            )
        return solve_tca_closure(
            S_T=float(S_T),
            S_E=float(S_E),
            gamma_T=float(gamma_t),
            decision=self.canonical_decision,
        )

    def _background_projection(self, eta_out: np.ndarray) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
        a = np.asarray(self.bg_table.interp_a(eta_out), dtype=np.float64)
        sigma_plus = np.zeros_like(a)
        sigma_minus = np.zeros_like(a)
        for i, (eta, a_i) in enumerate(zip(eta_out, a)):
            sigma_proper = _interp_matrix(self.background_monitor.eta, self.background_monitor.sigma_tensor, float(eta))
            sigma_conformal = float(a_i) * sigma_proper
            sigma_plus[i], sigma_minus[i] = _sigma_pm_from_conformal_sigma(sigma_conformal)
        return a, sigma_plus, sigma_minus

    def _sigma_tensor_at_eta(self, eta: float) -> np.ndarray:
        return _interp_matrix(
            np.asarray(self.background_monitor.eta, dtype=np.float64),
            np.asarray(self.background_monitor.sigma_tensor, dtype=np.float64),
            float(eta),
        )

    def _live_backend_state_payload(
        self,
        *,
        eta: float,
        gamma_t_probe: float,
        visibility_amplitude: float,
        polarization_source: float,
        reionization_amplitude: float,
    ) -> dict[str, object]:
        return {
            "branch": str(self.background_monitor.branch),
            "geometry": self.background_monitor.initial_conditions.geometry,
            "sigma_tensor": self._sigma_tensor_at_eta(float(eta)),
            "opacity_data": {"Gamma_T": float(gamma_t_probe)},
            "source_tables": {
                "visibility_amplitude": float(visibility_amplitude),
                "polarization_source": float(polarization_source),
                "reionization_amplitude": float(reionization_amplitude),
            },
            "state_tag": "ver2_native_integrator_auxiliary_sector_history",
        }

    def _build_auxiliary_operator_sample(
        self,
        *,
        eta: float,
        photon_T_row: np.ndarray,
        photon_E_row: np.ndarray,
        reionization_amplitude: float,
    ) -> _AuxiliaryOperatorSample:
        gamma_t = _resolved_gamma_t(
            visibility_source=self.visibility_source,
            eta=float(eta),
            direction=self._direction,
            config=self.config,
        )
        visibility_amplitude = abs(float(np.asarray(photon_T_row, dtype=np.float64)[0]))
        ell2_m0_slot = _ell2_m0_slot_offset(int(self.config.L_max)) if int(self.config.L_max) >= 2 else None
        polarization_source = (
            0.0
            if ell2_m0_slot is None
            else abs(float(np.asarray(photon_E_row, dtype=np.float64)[ell2_m0_slot]))
        )
        mode_ops = self.backend.operator_factory(
            self._live_backend_state_payload(
                eta=float(eta),
                gamma_t_probe=float(gamma_t),
                visibility_amplitude=visibility_amplitude,
                polarization_source=polarization_source,
                reionization_amplitude=reionization_amplitude,
            )
        )
        return _AuxiliaryOperatorSample(
            mode_ops=mode_ops,
            source_template=np.asarray(mode_ops.source_template, dtype=np.float64),
            mass_diag=np.asarray(mode_ops.mass_matrix.diagonal(), dtype=np.float64),
        )

    def _theta_1_photon_m0(self, photon_T_row: np.ndarray) -> float:
        arr = np.asarray(photon_T_row, dtype=np.float64)
        if self.config.L_max < 1:
            return 0.0
        slot = sum(2 * ell + 1 for ell in range(1)) + 1
        if slot >= arr.size:
            return 0.0
        return float(arr[slot])

    def _postprocess_local_matter_history(
        self,
        *,
        eta: np.ndarray,
        photon_T_tower: np.ndarray,
    ) -> _LocalMatterHistory:
        if self._matter_seed_observables is None:
            raise RuntimeError("local matter post-processing requires seeded initial observables")

        eta_arr = np.asarray(eta, dtype=np.float64)
        photon_arr = np.asarray(photon_T_tower, dtype=np.float64)
        if eta_arr.ndim != 1 or eta_arr.size == 0:
            raise ValueError("eta must be a non-empty 1-D array")
        if photon_arr.ndim != 2 or photon_arr.shape[0] != eta_arr.size:
            raise ValueError("photon_T_tower must have shape (len(eta), n_state)")

        baryon_history = np.zeros((eta_arr.size, 4), dtype=np.float64)
        cdm_history = np.zeros((eta_arr.size, 2), dtype=np.float64)
        baryon_state = BaryonFluidState(
            delta_b=float(self._matter_seed_observables["delta_b"]),
            v_b=float(self._matter_seed_observables["theta_b"]),
            axis=SymmetryAxis.X,
        )
        cdm_state = CDMFluidState(
            delta_c=float(self._matter_seed_observables["delta_c"]),
            v_c=float(self._matter_seed_observables["theta_c"]),
            axis=SymmetryAxis.X,
        )
        photon = self.species[SpeciesLabel.PHOTON]
        baryon = self.species[SpeciesLabel.BARYON]
        phi_dot_assumed = 0.0

        def _store(slot: int, theta_1: float) -> None:
            baryon_history[slot, :] = (
                float(baryon_state.delta_b),
                float(baryon_state.v_b),
                float(baryon_state.v_b),
                float(3.0 * theta_1 - baryon_state.v_b),
            )
            cdm_history[slot, :] = (
                float(cdm_state.delta_c),
                float(cdm_state.v_c),
            )

        _store(0, self._theta_1_photon_m0(photon_arr[0]))
        for idx in range(eta_arr.size - 1):
            eta_left = float(eta_arr[idx])
            eta_right = float(eta_arr[idx + 1])
            dt = eta_right - eta_left
            if dt <= 0.0:
                raise ValueError("eta grid must be strictly increasing")

            H_left = max(self._h_local_at(eta_left), 0.0)
            H_right = max(self._h_local_at(eta_right), 0.0)
            rho_b_left = max(float(baryon.rho_rest(eta_left)), 1.0e-30)
            rho_b_right = max(float(baryon.rho_rest(eta_right)), 1.0e-30)
            rho_gamma_left = max(float(photon.rho_rest(eta_left)), 1.0e-30)
            rho_gamma_right = max(float(photon.rho_rest(eta_right)), 1.0e-30)
            gamma_left = max(
                _resolved_gamma_t(
                    eta=eta_left,
                    direction=self._direction,
                    visibility_source=self.visibility_source,
                    config=self.config,
                ),
                0.0,
            )
            gamma_right = max(
                _resolved_gamma_t(
                    eta=eta_right,
                    direction=self._direction,
                    visibility_source=self.visibility_source,
                    config=self.config,
                ),
                0.0,
            )
            theta_left = self._theta_1_photon_m0(photon_arr[idx])
            theta_right = self._theta_1_photon_m0(photon_arr[idx + 1])
            baryon_params_left = BaryonParameters(
                R_b=max(3.0 * rho_b_left / (4.0 * rho_gamma_left), 1.0e-30),
                tau_dot=gamma_left,
                H=H_left,
            )
            baryon_params_right = BaryonParameters(
                R_b=max(3.0 * rho_b_right / (4.0 * rho_gamma_right), 1.0e-30),
                tau_dot=gamma_right,
                H=H_right,
            )
            cdm_params_left = CDMParameters(H=H_left)
            cdm_params_right = CDMParameters(H=H_right)

            baryon_delta_left = baryon_continuity_rhs(
                baryon_state,
                phi_dot_assumed,
                self.canonical_decision,
            )
            baryon_delta_right = baryon_continuity_rhs(
                baryon_state,
                phi_dot_assumed,
                self.canonical_decision,
            )
            drag_left = float(baryon_params_left.tau_dot / max(baryon_params_left.R_b, 1.0e-30))
            drag_right = float(baryon_params_right.tau_dot / max(baryon_params_right.R_b, 1.0e-30))
            lambda_left = float(baryon_params_left.H + drag_left)
            lambda_right = float(baryon_params_right.H + drag_right)
            forcing_left = float(3.0 * drag_left * theta_left)
            forcing_right = float(3.0 * drag_right * theta_right)
            baryon_v_next = (
                float(baryon_state.v_b)
                + 0.5 * dt * (forcing_left - lambda_left * float(baryon_state.v_b) + forcing_right)
            ) / max(1.0 + 0.5 * dt * lambda_right, 1.0e-30)
            baryon_state = BaryonFluidState(
                delta_b=float(
                    baryon_state.delta_b + 0.5 * dt * (baryon_delta_left + baryon_delta_right)
                ),
                v_b=float(baryon_v_next),
                axis=baryon_state.axis,
            )

            cdm_delta_left = cdm_continuity_rhs(
                cdm_state,
                phi_dot_assumed,
                self.canonical_decision,
            )
            cdm_delta_right = cdm_continuity_rhs(
                cdm_state,
                phi_dot_assumed,
                self.canonical_decision,
            )
            cdm_v_next = float(cdm_state.v_c) * max(
                1.0 - 0.5 * dt * float(cdm_params_left.H),
                0.0,
            ) / max(1.0 + 0.5 * dt * float(cdm_params_right.H), 1.0e-30)
            cdm_state = CDMFluidState(
                delta_c=float(cdm_state.delta_c + 0.5 * dt * (cdm_delta_left + cdm_delta_right)),
                v_c=float(cdm_v_next),
                axis=cdm_state.axis,
            )
            _store(idx + 1, theta_right)

        return _LocalMatterHistory(
            eta=eta_arr,
            baryon_history=baryon_history,
            cdm_history=cdm_history,
            baryon_labels=("delta_b", "v_b", "v_e", "drag_lock_residual"),
            cdm_labels=("delta_c", "v_c"),
            metadata={
                "owner": "ver2_native_integrator.predictor_corrector_local_matter_helper",
                "phi_dot_source": "unavailable_assumed_zero_homogeneous_limit",
                "photon_dipole_source": "live_runtime_ph_I_ell1_m0",
                "gamma_t_source": "resolved_visibility_gamma_t",
                "integration_scheme": "predictor_corrector_trapezoidal",
                "history_sample_count": int(eta_arr.size),
            },
        )

    def _integrate_live_b_mode_history(
        self,
        *,
        eta: np.ndarray,
        photon_T_tower: np.ndarray,
        photon_E_tower: np.ndarray,
        local_matter_history: _LocalMatterHistory,
    ) -> tuple[np.ndarray, dict[str, object]]:
        eta_arr = np.asarray(eta, dtype=np.float64)
        photon_T_arr = np.asarray(photon_T_tower, dtype=np.float64)
        photon_E_arr = np.asarray(photon_E_tower, dtype=np.float64)
        if eta_arr.ndim != 1 or eta_arr.size == 0:
            raise ValueError("eta must be a non-empty 1-D array")
        if photon_T_arr.shape != photon_E_arr.shape:
            raise ValueError("photon_T_tower and photon_E_tower must share shape")
        if photon_T_arr.ndim != 2 or photon_T_arr.shape[0] != eta_arr.size:
            raise ValueError("photon tower arrays must have shape (len(eta), n_state)")

        size = (self.config.L_max + 1) ** 2
        b_rows = np.zeros((eta_arr.size, size), dtype=np.float64)
        b_current = np.zeros(size, dtype=np.float64)

        def _rhs_b(
            *,
            eta_value: float,
            photon_T_row: np.ndarray,
            photon_E_row: np.ndarray,
            b_row: np.ndarray,
        ) -> np.ndarray:
            snapshot = self._eta_runtime_snapshot(float(eta_value))
            photon_T_state = _unpack_hierarchy_view(np.asarray(photon_T_row, dtype=np.float64), self.config.L_max)
            photon_E_state = PolarizationHierarchyState(
                E=_unpack_hierarchy_view(np.asarray(photon_E_row, dtype=np.float64), self.config.L_max)
            )
            b_state = _unpack_hierarchy_view(np.asarray(b_row, dtype=np.float64), self.config.L_max)
            v_b_real_sph = _interp_electron_velocity_real_sph(
                eta=float(eta_value),
                eta_grid=np.asarray(local_matter_history.eta, dtype=np.float64),
                baryon_history=np.asarray(local_matter_history.baryon_history, dtype=np.float64),
            )
            if snapshot.gamma_t <= 0.0:
                collision = _ZERO_COLLISION
                collision_aux = None
            else:
                collision = self._b_collision
                collision_aux = self._collision_aux_from_snapshot(
                    snapshot=snapshot,
                    photon_T=photon_T_state,
                    photon_E=photon_E_state,
                    v_b_real_sph=v_b_real_sph,
                    b_state=b_state,
                )
            return hierarchy_rhs_photon_from_state(
                b_state,
                background=snapshot.background,
                closure=self.closure,
                collision=collision,
                collision_aux=collision_aux,
            )

        for index in range(eta_arr.size):
            b_rows[index, :] = b_current
            if index == eta_arr.size - 1:
                break
            dt = float(eta_arr[index + 1] - eta_arr[index])
            if dt <= 0.0:
                raise ValueError("eta grid must be strictly increasing for B-mode history sampling")
            rhs_now = _rhs_b(
                eta_value=float(eta_arr[index]),
                photon_T_row=photon_T_arr[index],
                photon_E_row=photon_E_arr[index],
                b_row=b_current,
            )
            b_predict = np.asarray(b_current, dtype=np.float64) + dt * np.asarray(rhs_now, dtype=np.float64)
            rhs_next = _rhs_b(
                eta_value=float(eta_arr[index + 1]),
                photon_T_row=photon_T_arr[index + 1],
                photon_E_row=photon_E_arr[index + 1],
                b_row=b_predict,
            )
            b_current = np.asarray(b_current, dtype=np.float64) + 0.5 * dt * (
                np.asarray(rhs_now, dtype=np.float64) + np.asarray(rhs_next, dtype=np.float64)
            )

        return b_rows, {
            "owner": "hierarchy_rhs.exact_thomson_b_mode_history",
            "history_sample_count": int(eta_arr.size),
            "integration_scheme": "predictor_corrector_trapezoidal",
            "radiation_rhs_owner": "hierarchy_rhs_photon_from_state",
            "collision_owner": "projected_thomson_source.polarization_B",
        }

    def _ensure_live_b_mode_history(
        self,
        result: IntegrationResult,
    ) -> tuple[np.ndarray, dict[str, object]]:
        cached = getattr(result, "photon_B_tower", None)
        metadata = result.solver_info.get("live_b_mode_history_metadata")
        if cached is not None and isinstance(metadata, Mapping):
            return np.asarray(cached, dtype=np.float64), dict(metadata)
        local_matter_history = self._ensure_live_local_matter_history(result)
        b_rows, b_metadata = self._integrate_live_b_mode_history(
            eta=np.asarray(result.eta, dtype=np.float64),
            photon_T_tower=np.asarray(result.photon_T_tower, dtype=np.float64),
            photon_E_tower=np.asarray(result.photon_E_tower, dtype=np.float64),
            local_matter_history=local_matter_history,
        )
        result.photon_B_tower = np.asarray(b_rows, dtype=np.float64)
        result.solver_info["live_b_mode_history_metadata"] = dict(b_metadata)
        return np.asarray(b_rows, dtype=np.float64), dict(b_metadata)

    def _ensure_live_mode_label_harmonic_histories(
        self,
        result: IntegrationResult,
    ) -> tuple[
        dict[str, np.ndarray],
        dict[str, np.ndarray],
        dict[str, np.ndarray],
        dict[str, np.ndarray],
        dict[str, object],
    ]:
        cached_t = getattr(result, "photon_T_history_by_mode_label", None)
        cached_e = getattr(result, "photon_E_history_by_mode_label", None)
        cached_b = getattr(result, "photon_B_history_by_mode_label", None)
        cached_nu = getattr(result, "neutrino_history_by_mode_label", None)
        metadata = result.solver_info.get("live_mode_label_harmonic_history_metadata")
        if (
            isinstance(cached_t, Mapping)
            and isinstance(cached_e, Mapping)
            and isinstance(cached_b, Mapping)
            and isinstance(cached_nu, Mapping)
            and isinstance(metadata, Mapping)
            and str(metadata.get("owner", "")) in {
                "ver2_native_integrator.reduced_mode_label_harmonics",
                "ver2_native_integrator.main_state_mode_label_harmonics",
            }
        ):
            return (
                {str(mu): np.asarray(values, dtype=np.float64) for mu, values in cached_t.items()},
                {str(mu): np.asarray(values, dtype=np.float64) for mu, values in cached_e.items()},
                {str(mu): np.asarray(values, dtype=np.float64) for mu, values in cached_b.items()},
                {str(mu): np.asarray(values, dtype=np.float64) for mu, values in cached_nu.items()},
                dict(metadata),
            )

        eta_samples = np.asarray(result.eta, dtype=np.float64)
        mode_labels = tuple(str(mu) for mu in self._layout.mode_labels)
        covered = str(self._layout_covered_mode_label)
        residual_mode_labels = tuple(str(mu) for mu in mode_labels if str(mu) != covered)
        harmonic_width = (int(self.config.L_max) + 1) ** 2
        reionization_amplitude = self._reionization_amplitude()

        residual_harmonic_history = getattr(result, "residual_harmonic_history", None)
        if residual_harmonic_history is not None:
            residual_arr = np.asarray(residual_harmonic_history, dtype=np.float64)
            if residual_arr.ndim == 2 and residual_arr.shape[0] == eta_samples.size:
                b_history, b_history_metadata = self._ensure_live_b_mode_history(result)
                photon_t_histories = {covered: np.asarray(result.photon_T_tower, dtype=np.float64)}
                photon_e_histories = {covered: np.asarray(result.photon_E_tower, dtype=np.float64)}
                photon_b_histories = {covered: np.asarray(b_history, dtype=np.float64)}
                neutrino_histories = {covered: np.asarray(result.neutrino_tower, dtype=np.float64)}
                offset = 0
                for mu in residual_mode_labels:
                    photon_t_histories[str(mu)] = np.asarray(
                        residual_arr[:, offset : offset + harmonic_width],
                        dtype=np.float64,
                    )
                    offset += harmonic_width
                    photon_e_histories[str(mu)] = np.asarray(
                        residual_arr[:, offset : offset + harmonic_width],
                        dtype=np.float64,
                    )
                    offset += harmonic_width
                    photon_b_histories[str(mu)] = np.asarray(
                        residual_arr[:, offset : offset + harmonic_width],
                        dtype=np.float64,
                    )
                    offset += harmonic_width
                    neutrino_histories[str(mu)] = np.asarray(
                        residual_arr[:, offset : offset + harmonic_width],
                        dtype=np.float64,
                    )
                    offset += harmonic_width
                metadata_out = {
                    "owner": "ver2_native_integrator.main_state_mode_label_harmonics",
                    "history_sample_count": int(eta_samples.size),
                    "mode_labels": list(mode_labels),
                    "covered_mode_label": covered,
                    "residual_mode_labels": list(residual_mode_labels),
                    "sectors": ("ph_I", "ph_E", "ph_B", "nu_I"),
                    "covered_owner": "ver2_native_integrator.main_state_harmonics",
                    "residual_owner": "ver2_native_integrator.main_state_mode_label_harmonics",
                    "integration_scheme": "main_state_coevolved",
                }
                result.photon_T_history_by_mode_label = photon_t_histories
                result.photon_E_history_by_mode_label = photon_e_histories
                result.photon_B_history_by_mode_label = photon_b_histories
                result.neutrino_history_by_mode_label = neutrino_histories
                result.solver_info["live_mode_label_harmonic_history_metadata"] = dict(metadata_out)
                result.solver_info["live_b_mode_history_by_mode_label_metadata"] = {
                    "owner": "ver2_native_integrator.main_state_mode_label_harmonics",
                    "sector": "ph_B",
                    "history_sample_count": int(eta_samples.size),
                    "mode_labels": list(mode_labels),
                    "covered_mode_label": covered,
                    "residual_mode_labels": list(residual_mode_labels),
                    "covered_owner": str(
                        b_history_metadata.get("owner", "ver2_native_integrator.main_state_photon_B")
                    ),
                    "integration_scheme": "main_state_coevolved",
                }
                return (
                    {mu: np.asarray(values, dtype=np.float64) for mu, values in photon_t_histories.items()},
                    {mu: np.asarray(values, dtype=np.float64) for mu, values in photon_e_histories.items()},
                    {mu: np.asarray(values, dtype=np.float64) for mu, values in photon_b_histories.items()},
                    {mu: np.asarray(values, dtype=np.float64) for mu, values in neutrino_histories.items()},
                    metadata_out,
                )

        baryon_by_mode_label, _, _ = self._ensure_live_mode_label_local_matter_history(result)
        _, source_by_mode_label, source_history_metadata = self._ensure_live_source_history(result)
        b_history, b_history_metadata = self._ensure_live_b_mode_history(result)

        projected_t = self._resolve_mode_label_harmonic_history(np.asarray(result.photon_T_tower, dtype=np.float64))
        projected_e = self._resolve_mode_label_harmonic_history(np.asarray(result.photon_E_tower, dtype=np.float64))
        projected_b = self._resolve_mode_label_harmonic_history(np.asarray(b_history, dtype=np.float64))
        projected_nu = self._resolve_mode_label_harmonic_history(np.asarray(result.neutrino_tower, dtype=np.float64))

        photon_t_histories = {
            mu: np.zeros((eta_samples.size, harmonic_width), dtype=np.float64)
            for mu in mode_labels
        }
        photon_e_histories = {
            mu: np.zeros((eta_samples.size, harmonic_width), dtype=np.float64)
            for mu in mode_labels
        }
        photon_b_histories = {
            mu: np.zeros((eta_samples.size, harmonic_width), dtype=np.float64)
            for mu in mode_labels
        }
        neutrino_histories = {
            mu: np.zeros((eta_samples.size, harmonic_width), dtype=np.float64)
            for mu in mode_labels
        }

        photon_t_histories[covered][:, :] = np.asarray(result.photon_T_tower, dtype=np.float64)
        photon_e_histories[covered][:, :] = np.asarray(result.photon_E_tower, dtype=np.float64)
        photon_b_histories[covered][:, :] = np.asarray(b_history, dtype=np.float64)
        neutrino_histories[covered][:, :] = np.asarray(result.neutrino_tower, dtype=np.float64)

        if eta_samples.size > 0:
            for mu in residual_mode_labels:
                photon_t_histories[mu][0, :] = np.asarray(projected_t[mu][0], dtype=np.float64)
                photon_e_histories[mu][0, :] = np.asarray(projected_e[mu][0], dtype=np.float64)
                photon_b_histories[mu][0, :] = np.asarray(projected_b[mu][0], dtype=np.float64)
                neutrino_histories[mu][0, :] = np.asarray(projected_nu[mu][0], dtype=np.float64)

        for index in range(max(eta_samples.size - 1, 0)):
            eta_left = float(eta_samples[index])
            eta_right = float(eta_samples[index + 1])
            dt = float(eta_right - eta_left)
            if dt == 0.0:
                for mu in residual_mode_labels:
                    photon_t_histories[mu][index + 1, :] = photon_t_histories[mu][index, :]
                    photon_e_histories[mu][index + 1, :] = photon_e_histories[mu][index, :]
                    photon_b_histories[mu][index + 1, :] = photon_b_histories[mu][index, :]
                    neutrino_histories[mu][index + 1, :] = neutrino_histories[mu][index, :]
                continue

            left_t = {
                mu: np.asarray(photon_t_histories[mu][index], dtype=np.float64)
                for mu in mode_labels
            }
            left_e = {
                mu: np.asarray(photon_e_histories[mu][index], dtype=np.float64)
                for mu in mode_labels
            }
            left_b = {
                mu: np.asarray(photon_b_histories[mu][index], dtype=np.float64)
                for mu in mode_labels
            }
            left_nu = {
                mu: np.asarray(neutrino_histories[mu][index], dtype=np.float64)
                for mu in mode_labels
            }
            visibility_left = abs(float(np.asarray(result.photon_T_tower[index], dtype=np.float64)[0]))
            ell2_m0_slot = _ell2_m0_slot_offset(int(self.config.L_max)) if int(self.config.L_max) >= 2 else None
            polarization_left = (
                0.0
                if ell2_m0_slot is None
                else abs(float(np.asarray(result.photon_E_tower[index], dtype=np.float64)[ell2_m0_slot]))
            )
            bg_left = self._live_backend_state_payload(
                eta=eta_left,
                gamma_t_probe=_resolved_gamma_t(
                    visibility_source=self.visibility_source,
                    eta=eta_left,
                    direction=self._direction,
                    config=self.config,
                ),
                visibility_amplitude=visibility_left,
                polarization_source=polarization_left,
                reionization_amplitude=reionization_amplitude,
            )
            source_left = {
                mu: np.asarray(source_by_mode_label[mu][index], dtype=np.float64)
                for mu in mode_labels
            }
            rhs_t_left, rhs_e_left, rhs_b_left, rhs_nu_left = self.backend.evaluate_reduced_harmonic_rhs(
                bg_left,
                photon_T_by_mode_label=left_t,
                photon_E_by_mode_label=left_e,
                photon_B_by_mode_label=left_b,
                neutrino_by_mode_label=left_nu,
                baryon_by_mode_label={
                    mu: np.asarray(baryon_by_mode_label[mu][index], dtype=np.float64)
                    for mu in mode_labels
                },
                source_by_mode_label=source_left,
            )

            right_t = {
                covered: np.asarray(result.photon_T_tower[index + 1], dtype=np.float64),
                **{
                    mu: np.asarray(photon_t_histories[mu][index], dtype=np.float64)
                    + dt * np.asarray(rhs_t_left[mu], dtype=np.float64)
                    for mu in residual_mode_labels
                },
            }
            right_e = {
                covered: np.asarray(result.photon_E_tower[index + 1], dtype=np.float64),
                **{
                    mu: np.asarray(photon_e_histories[mu][index], dtype=np.float64)
                    + dt * np.asarray(rhs_e_left[mu], dtype=np.float64)
                    for mu in residual_mode_labels
                },
            }
            right_b = {
                covered: np.asarray(b_history[index + 1], dtype=np.float64),
                **{
                    mu: np.asarray(photon_b_histories[mu][index], dtype=np.float64)
                    + dt * np.asarray(rhs_b_left[mu], dtype=np.float64)
                    for mu in residual_mode_labels
                },
            }
            right_nu = {
                covered: np.asarray(result.neutrino_tower[index + 1], dtype=np.float64),
                **{
                    mu: np.asarray(neutrino_histories[mu][index], dtype=np.float64)
                    + dt * np.asarray(rhs_nu_left[mu], dtype=np.float64)
                    for mu in residual_mode_labels
                },
            }
            visibility_right = abs(float(np.asarray(result.photon_T_tower[index + 1], dtype=np.float64)[0]))
            polarization_right = (
                0.0
                if ell2_m0_slot is None
                else abs(float(np.asarray(result.photon_E_tower[index + 1], dtype=np.float64)[ell2_m0_slot]))
            )
            bg_right = self._live_backend_state_payload(
                eta=eta_right,
                gamma_t_probe=_resolved_gamma_t(
                    visibility_source=self.visibility_source,
                    eta=eta_right,
                    direction=self._direction,
                    config=self.config,
                ),
                visibility_amplitude=visibility_right,
                polarization_source=polarization_right,
                reionization_amplitude=reionization_amplitude,
            )
            source_right = {
                mu: np.asarray(source_by_mode_label[mu][index + 1], dtype=np.float64)
                for mu in mode_labels
            }
            rhs_t_right, rhs_e_right, rhs_b_right, rhs_nu_right = self.backend.evaluate_reduced_harmonic_rhs(
                bg_right,
                photon_T_by_mode_label=right_t,
                photon_E_by_mode_label=right_e,
                photon_B_by_mode_label=right_b,
                neutrino_by_mode_label=right_nu,
                baryon_by_mode_label={
                    mu: np.asarray(baryon_by_mode_label[mu][index + 1], dtype=np.float64)
                    for mu in mode_labels
                },
                source_by_mode_label=source_right,
            )

            for mu in residual_mode_labels:
                photon_t_histories[mu][index + 1, :] = (
                    np.asarray(photon_t_histories[mu][index], dtype=np.float64)
                    + 0.5 * dt * (np.asarray(rhs_t_left[mu], dtype=np.float64) + np.asarray(rhs_t_right[mu], dtype=np.float64))
                )
                photon_e_histories[mu][index + 1, :] = (
                    np.asarray(photon_e_histories[mu][index], dtype=np.float64)
                    + 0.5 * dt * (np.asarray(rhs_e_left[mu], dtype=np.float64) + np.asarray(rhs_e_right[mu], dtype=np.float64))
                )
                photon_b_histories[mu][index + 1, :] = (
                    np.asarray(photon_b_histories[mu][index], dtype=np.float64)
                    + 0.5 * dt * (np.asarray(rhs_b_left[mu], dtype=np.float64) + np.asarray(rhs_b_right[mu], dtype=np.float64))
                )
                neutrino_histories[mu][index + 1, :] = (
                    np.asarray(neutrino_histories[mu][index], dtype=np.float64)
                    + 0.5 * dt * (np.asarray(rhs_nu_left[mu], dtype=np.float64) + np.asarray(rhs_nu_right[mu], dtype=np.float64))
                )

        metadata_out = {
            "owner": "ver2_native_integrator.reduced_mode_label_harmonics",
            "history_sample_count": int(eta_samples.size),
            "mode_labels": list(mode_labels),
            "covered_mode_label": covered,
            "residual_mode_labels": list(residual_mode_labels),
            "sectors": ("ph_I", "ph_E", "ph_B", "nu_I"),
            "covered_owner": "ver2_native_integrator.main_state_harmonics",
            "residual_owner": "ver2_native_integrator.reduced_mode_label_harmonics",
            "source_owner": str(source_history_metadata.get("owner", "unavailable")),
            "integration_scheme": "predictor_corrector_trapezoidal",
        }
        result.photon_T_history_by_mode_label = {
            mu: np.asarray(values, dtype=np.float64)
            for mu, values in photon_t_histories.items()
        }
        result.photon_E_history_by_mode_label = {
            mu: np.asarray(values, dtype=np.float64)
            for mu, values in photon_e_histories.items()
        }
        result.photon_B_history_by_mode_label = {
            mu: np.asarray(values, dtype=np.float64)
            for mu, values in photon_b_histories.items()
        }
        result.neutrino_history_by_mode_label = {
            mu: np.asarray(values, dtype=np.float64)
            for mu, values in neutrino_histories.items()
        }
        result.solver_info["live_mode_label_harmonic_history_metadata"] = dict(metadata_out)
        result.solver_info["live_b_mode_history_by_mode_label_metadata"] = {
            "owner": "ver2_native_integrator.reduced_mode_label_harmonics",
            "sector": "ph_B",
            "history_sample_count": int(eta_samples.size),
            "mode_labels": list(mode_labels),
            "covered_mode_label": covered,
            "residual_mode_labels": list(residual_mode_labels),
            "covered_owner": str(b_history_metadata.get("owner", "ver2_native_integrator.main_state_photon_B")),
            "integration_scheme": "predictor_corrector_trapezoidal",
        }
        return (
            {mu: np.asarray(values, dtype=np.float64) for mu, values in result.photon_T_history_by_mode_label.items()},
            {mu: np.asarray(values, dtype=np.float64) for mu, values in result.photon_E_history_by_mode_label.items()},
            {mu: np.asarray(values, dtype=np.float64) for mu, values in result.photon_B_history_by_mode_label.items()},
            {mu: np.asarray(values, dtype=np.float64) for mu, values in result.neutrino_history_by_mode_label.items()},
            metadata_out,
        )

    def _ensure_live_b_mode_history_by_mode_label(
        self,
        result: IntegrationResult,
    ) -> tuple[dict[str, np.ndarray], dict[str, object]]:
        _, _, resolved_b, _, _ = self._ensure_live_mode_label_harmonic_histories(result)
        metadata = dict(result.solver_info.get("live_b_mode_history_by_mode_label_metadata", {}))
        return resolved_b, metadata

    def _resolve_mode_label_harmonic_history(
        self,
        samples: np.ndarray,
    ) -> dict[str, np.ndarray]:
        history = np.asarray(samples, dtype=np.float64)
        resolved: dict[str, np.ndarray] = {
            str(mu): np.zeros_like(history)
            for mu in self._layout.mode_labels
        }
        for ell in range(self.config.L_max + 1):
            offset = sum(2 * level + 1 for level in range(ell))
            for m in range(-ell, ell + 1):
                slot = offset + (m + ell)
                mode_label = _resolve_projection_mode_label(
                    self._layout.mode_labels,
                    self._layout_covered_mode_label,
                    m=m,
                )
                resolved[str(mode_label)][:, slot] = np.asarray(history[:, slot], dtype=np.float64)
        return resolved

    def _compute_live_source_history_payload(
        self,
        *,
        eta_samples: np.ndarray,
        photon_T_tower: np.ndarray,
        photon_E_tower: np.ndarray,
        covered_mode_label: str | None = None,
    ) -> tuple[np.ndarray, dict[str, np.ndarray], dict[str, object]]:
        layout = self._layout
        covered = self._layout_covered_mode_label
        if covered is None:
            covered = layout.mode_labels[0] if covered_mode_label is None else str(covered_mode_label)
        elif covered_mode_label is not None:
            covered = str(covered_mode_label)
        index_cache = (
            self._projection_index_cache
            if covered == self._layout_covered_mode_label
            else _build_layout_projection_index_cache(layout, covered_mode_label=str(covered))
        )
        eta_arr = np.asarray(eta_samples, dtype=np.float64)
        photon_t_arr = np.asarray(photon_T_tower, dtype=np.float64)
        photon_e_arr = np.asarray(photon_E_tower, dtype=np.float64)
        reionization_amplitude = self._reionization_amplitude()
        source_width = int(layout.sector_local_dofs["src"])
        source_rows = np.zeros((eta_arr.size, source_width), dtype=np.float64)
        source_rows_by_mode_label = {
            str(mu): np.zeros((eta_arr.size, source_width), dtype=np.float64)
            for mu in layout.mode_labels
        }
        for index, eta in enumerate(eta_arr):
            background_state = self._live_backend_state_payload(
                eta=float(eta),
                gamma_t_probe=_resolved_gamma_t(
                    visibility_source=self.visibility_source,
                    eta=float(eta),
                    direction=self._direction,
                    config=self.config,
                ),
                visibility_amplitude=abs(float(np.asarray(photon_t_arr[index], dtype=np.float64)[0])),
                polarization_source=(
                    0.0
                    if int(self.config.L_max) < 2
                    else abs(
                        float(
                            np.asarray(photon_e_arr[index], dtype=np.float64)[
                                _ell2_m0_slot_offset(int(self.config.L_max))
                            ]
                        )
                    )
                ),
                reionization_amplitude=reionization_amplitude,
            )
            reduced_source = self.backend.evaluate_reduced_source_blocks(background_state)
            source_rows[index, :] = np.asarray(reduced_source[str(covered)], dtype=np.float64)
            for mu in layout.mode_labels:
                source_rows_by_mode_label[str(mu)][index, :] = np.asarray(
                    reduced_source[str(mu)],
                    dtype=np.float64,
                )
        return (
            source_rows,
            source_rows_by_mode_label,
            {
                "owner": "ver2_native_integrator.mode_ops_source_history",
                "history_sample_count": int(eta_arr.size),
                "covered_mode_label": str(covered),
                "mode_labels": list(layout.mode_labels),
            },
        )

    def _ensure_live_local_matter_history(
        self,
        result: IntegrationResult,
    ) -> _LocalMatterHistory:
        baryon_cached = getattr(result, "baryon_local_history", None)
        cdm_cached = getattr(result, "cdm_local_history", None)
        metadata = result.solver_info.get("live_local_matter_history_metadata")
        if (
            baryon_cached is not None
            and cdm_cached is not None
            and isinstance(metadata, Mapping)
        ):
            labels = metadata.get(
                "labels",
                {
                    "baryon": ("delta_b", "v_b", "v_e", "drag_lock_residual"),
                    "cdm": ("delta_c", "v_c"),
                },
            )
            return _LocalMatterHistory(
                eta=np.asarray(result.eta, dtype=np.float64),
                baryon_history=np.asarray(baryon_cached, dtype=np.float64),
                cdm_history=np.asarray(cdm_cached, dtype=np.float64),
                baryon_labels=tuple(labels.get("baryon", ("delta_b", "v_b", "v_e", "drag_lock_residual"))),
                cdm_labels=tuple(labels.get("cdm", ("delta_c", "v_c"))),
                metadata=dict(metadata),
            )
        history = self._postprocess_local_matter_history(
            eta=np.asarray(result.eta, dtype=np.float64),
            photon_T_tower=np.asarray(result.photon_T_tower, dtype=np.float64),
        )
        result.baryon_local_history = np.asarray(history.baryon_history, dtype=np.float64)
        result.cdm_local_history = np.asarray(history.cdm_history, dtype=np.float64)
        result.solver_info["live_local_matter_history_metadata"] = {
            **dict(history.metadata),
            "labels": {
                "baryon": tuple(history.baryon_labels),
                "cdm": tuple(history.cdm_labels),
            },
        }
        return history

    def _ensure_live_mode_label_local_matter_history(
        self,
        result: IntegrationResult,
    ) -> tuple[dict[str, np.ndarray], dict[str, np.ndarray], dict[str, object]]:
        baryon_cached = getattr(result, "baryon_local_history_by_mode_label", None)
        cdm_cached = getattr(result, "cdm_local_history_by_mode_label", None)
        metadata = result.solver_info.get("live_mode_label_local_matter_history_metadata")
        if (
            isinstance(baryon_cached, Mapping)
            and isinstance(cdm_cached, Mapping)
            and isinstance(metadata, Mapping)
        ):
            return (
                {str(mu): np.asarray(values, dtype=np.float64) for mu, values in baryon_cached.items()},
                {str(mu): np.asarray(values, dtype=np.float64) for mu, values in cdm_cached.items()},
                dict(metadata),
            )
        direct_history = self._ensure_live_local_matter_history(result)
        baryon_by_mode_label = {
            self._layout_covered_mode_label: np.asarray(direct_history.baryon_history, dtype=np.float64)
        }
        cdm_by_mode_label = {
            self._layout_covered_mode_label: np.asarray(direct_history.cdm_history, dtype=np.float64)
        }
        residual_history = getattr(result, "residual_local_history", None)
        residual_arr = (
            np.zeros((len(result.eta), self._residual_local_dof), dtype=np.float64)
            if residual_history is None
            else np.asarray(residual_history, dtype=np.float64)
        )
        offset = 0
        for mu in self._residual_mode_labels:
            baryon_by_mode_label[str(mu)] = np.asarray(
                residual_arr[:, offset : offset + _BARYON_LOCAL_DOF],
                dtype=np.float64,
            )
            offset += _BARYON_LOCAL_DOF
            cdm_by_mode_label[str(mu)] = np.asarray(
                residual_arr[:, offset : offset + _CDM_LOCAL_DOF],
                dtype=np.float64,
            )
            offset += _CDM_LOCAL_DOF
        metadata_out = {
            "owner": "ver2_native_integrator.main_state_mode_label_local_matter",
            "history_sample_count": int(len(result.eta)),
            "mode_labels": list(self._layout.mode_labels),
            "covered_mode_label": self._layout_covered_mode_label,
        }
        result.baryon_local_history_by_mode_label = baryon_by_mode_label
        result.cdm_local_history_by_mode_label = cdm_by_mode_label
        result.solver_info["live_mode_label_local_matter_history_metadata"] = dict(metadata_out)
        return baryon_by_mode_label, cdm_by_mode_label, metadata_out

    def _ensure_live_source_history(
        self,
        result: IntegrationResult,
        *,
        covered_mode_label: str | None = None,
    ) -> tuple[np.ndarray, dict[str, np.ndarray], dict[str, object]]:
        cached_rows = getattr(result, "source_history", None)
        cached_by_mode = getattr(result, "source_history_by_mode_label", None)
        metadata = result.solver_info.get("live_source_history_metadata")
        if (
            cached_rows is not None
            and isinstance(cached_by_mode, Mapping)
            and isinstance(metadata, Mapping)
        ):
            return (
                np.asarray(cached_rows, dtype=np.float64),
                {
                    str(mu): np.asarray(values, dtype=np.float64)
                    for mu, values in cached_by_mode.items()
                },
                dict(metadata),
            )
        cached_rows_only = getattr(result, "source_history", None)
        residual_source_history = getattr(result, "residual_source_history", None)
        if cached_rows_only is not None and residual_source_history is not None:
            covered = (
                self._layout_covered_mode_label
                if covered_mode_label is None
                else str(covered_mode_label)
            )
            row_arr = np.asarray(cached_rows_only, dtype=np.float64)
            residual_arr = np.asarray(residual_source_history, dtype=np.float64)
            eta_arr = np.asarray(result.eta, dtype=np.float64)
            source_width = int(self._layout.sector_local_dofs["src"])
            if (
                row_arr.ndim == 2
                and row_arr.shape[0] == eta_arr.size
                and row_arr.shape[1] == source_width
                and residual_arr.ndim == 2
                and residual_arr.shape[0] == eta_arr.size
            ):
                source_rows_by_mode_label = {str(covered): np.asarray(row_arr, dtype=np.float64)}
                offset = 0
                for mu in self._residual_mode_labels:
                    source_rows_by_mode_label[str(mu)] = np.asarray(
                        residual_arr[:, offset : offset + source_width],
                        dtype=np.float64,
                    )
                    offset += source_width
                metadata_out = {
                    "owner": "ver2_native_integrator.main_state_source_history",
                    "covered_owner": "ver2_native_integrator.main_state_covered_source",
                    "residual_owner": "ver2_native_integrator.main_state_mode_label_source",
                    "history_sample_count": int(eta_arr.size),
                    "covered_mode_label": str(covered),
                    "mode_labels": list(self._layout.mode_labels),
                    "integration_scheme": "main_state_coevolved",
                }
                result.source_history_by_mode_label = {
                    str(mu): np.asarray(values, dtype=np.float64)
                    for mu, values in source_rows_by_mode_label.items()
                }
                result.solver_info["live_source_history_metadata"] = dict(metadata_out)
                return (
                    np.asarray(row_arr, dtype=np.float64),
                    {
                        str(mu): np.asarray(values, dtype=np.float64)
                        for mu, values in result.source_history_by_mode_label.items()
                    },
                    metadata_out,
                )
        source_rows, source_rows_by_mode_label, metadata_out = self._compute_live_source_history_payload(
            eta_samples=np.asarray(result.eta, dtype=np.float64),
            photon_T_tower=np.asarray(result.photon_T_tower, dtype=np.float64),
            photon_E_tower=np.asarray(result.photon_E_tower, dtype=np.float64),
            covered_mode_label=covered_mode_label,
        )
        result.source_history = np.asarray(source_rows, dtype=np.float64)
        result.source_history_by_mode_label = {
            str(mu): np.asarray(values, dtype=np.float64)
            for mu, values in source_rows_by_mode_label.items()
        }
        result.solver_info["live_source_history_metadata"] = dict(metadata_out)
        return (
            np.asarray(result.source_history, dtype=np.float64),
            {
                str(mu): np.asarray(values, dtype=np.float64)
                for mu, values in result.source_history_by_mode_label.items()
            },
            metadata_out,
        )

    def build_layout_auxiliary_history_bundle(
        self,
        result: IntegrationResult,
        *,
        covered_mode_label: str | None = None,
    ) -> _LayoutAuxiliaryHistoryBundle:
        cached_bundle = getattr(result, "layout_auxiliary_bundle", None)
        if isinstance(cached_bundle, _LayoutAuxiliaryHistoryBundle):
            cached_covered = str(
                cached_bundle.metadata.get(
                    "covered_mode_label",
                    self._layout_covered_mode_label if self._layout_covered_mode_label is not None else "",
                )
            )
            requested_covered = (
                self._layout_covered_mode_label
                if covered_mode_label is None
                else str(covered_mode_label)
            )
            if requested_covered is None or cached_covered == str(requested_covered):
                return cached_bundle
        neutrino_tower = result.neutrino_tower
        if neutrino_tower is None:
            raise ValueError("layout auxiliary history bundle requires result.neutrino_tower")
        layout = self._layout
        covered = self._layout_covered_mode_label
        if covered_mode_label is not None:
            covered = str(covered_mode_label)
        projection_index_cache = (
            self._projection_index_cache
            if covered == self._layout_covered_mode_label
            else _build_layout_projection_index_cache(layout, covered_mode_label=covered)
        )
        direct_history = self._ensure_live_local_matter_history(result)
        baryon_rows_by_mode_label, cdm_rows_by_mode_label, mode_label_metadata = (
            self._ensure_live_mode_label_local_matter_history(result)
        )
        eta_samples = np.asarray(result.eta, dtype=np.float64)
        photon_T_tower = np.asarray(result.photon_T_tower, dtype=np.float64)
        photon_E_tower = np.asarray(result.photon_E_tower, dtype=np.float64)
        neutrino_arr = np.asarray(neutrino_tower, dtype=np.float64)
        b_rows, b_metadata = self._ensure_live_b_mode_history(result)
        source_rows_live, source_rows_by_mode_label_live, _ = self._ensure_live_source_history(
            result,
            covered_mode_label=covered,
        )
        source_rows = np.asarray(source_rows_live, dtype=np.float64)
        source_rows_by_mode_label = {
            str(mu): np.asarray(values, dtype=np.float64)
            for mu, values in source_rows_by_mode_label_live.items()
        }
        layout_state_rows = np.zeros((eta_samples.size, layout.size), dtype=np.float64)
        baryon_rows = np.asarray(direct_history.baryon_history, dtype=np.float64).copy()
        cdm_rows = np.asarray(direct_history.cdm_history, dtype=np.float64).copy()
        state_vector = np.zeros(layout.size, dtype=np.float64)
        for index, eta in enumerate(eta_samples):
            state_vector.fill(0.0)
            for mu, indices in projection_index_cache.src_by_mode_label.items():
                state_vector[indices] = np.asarray(source_rows_by_mode_label[str(mu)][index], dtype=np.float64)
            state_vector[projection_index_cache.harmonic_photon_T] = np.asarray(photon_T_tower[index], dtype=np.float64)
            state_vector[projection_index_cache.harmonic_photon_E] = np.asarray(photon_E_tower[index], dtype=np.float64)
            state_vector[projection_index_cache.harmonic_photon_B] = np.asarray(b_rows[index], dtype=np.float64)
            state_vector[projection_index_cache.harmonic_neutrino] = np.asarray(neutrino_arr[index], dtype=np.float64)
            for mu, indices in projection_index_cache.baryon_by_mode_label.items():
                state_vector[indices] = np.asarray(baryon_rows_by_mode_label[str(mu)][index], dtype=np.float64)
            for mu, indices in projection_index_cache.cdm_by_mode_label.items():
                state_vector[indices] = np.asarray(cdm_rows_by_mode_label[str(mu)][index], dtype=np.float64)
            layout_state_rows[index, :] = state_vector
        reference_baryon = np.asarray(baryon_rows_by_mode_label[str(covered)], dtype=np.float64)
        reference_cdm = np.asarray(cdm_rows_by_mode_label[str(covered)], dtype=np.float64)
        delta_terms: list[float] = []
        for mu in layout.mode_labels:
            if str(mu) == str(covered):
                continue
            delta_terms.append(
                float(
                    np.linalg.norm(
                        np.asarray(baryon_rows_by_mode_label[str(mu)], dtype=np.float64) - reference_baryon
                    )
                )
            )
            delta_terms.append(
                float(
                    np.linalg.norm(
                        np.asarray(cdm_rows_by_mode_label[str(mu)], dtype=np.float64) - reference_cdm
                    )
                )
            )
        scaled_delta_norm = float(np.sqrt(np.sum(np.square(delta_terms), dtype=np.float64))) if delta_terms else 0.0
        coupled_history = _CoupledAuxiliarySectorHistory(
            eta=eta_samples,
            photon_B_history=b_rows,
            baryon_history=baryon_rows,
            cdm_history=cdm_rows,
            baryon_labels=tuple(direct_history.baryon_labels),
            cdm_labels=tuple(direct_history.cdm_labels),
            metadata={
                "owner": str(direct_history.metadata["owner"]),
                "b_mode_owner": str(b_metadata["owner"]),
                "reference_owner": str(mode_label_metadata["owner"]),
                "mode_label_extension_owner": str(mode_label_metadata["owner"]),
                "history_sample_count": int(eta_samples.size),
                "reference_sample_count": int(reference_baryon.shape[0]),
                "reference_delta_norm": float(scaled_delta_norm),
                "reference_baryon_history": reference_baryon,
                "reference_cdm_history": reference_cdm,
                "coupling_passes": 0,
                "integration_scheme": str(direct_history.metadata.get("integration_scheme", "")),
                "extension_integration_scheme": "main_state_coevolved",
                "reduced_block_size": 0,
                "b_mode_integration_scheme": str(b_metadata["integration_scheme"]),
                "coupled_sectors": ("ph_B", "baryon", "cdm"),
            },
        )
        bundle = _LayoutAuxiliaryHistoryBundle(
            eta=eta_samples,
            source_history=source_rows,
            source_history_by_mode_label=source_rows_by_mode_label,
            layout_state_history=layout_state_rows,
            coupled_sector_history=coupled_history,
            metadata={
                "owner": "ver2_native_integrator.layout_auxiliary_history_bundle",
                "history_sample_count": int(eta_samples.size),
                "layout_state_history_size": int(layout.size),
                "covered_mode_label": covered,
                "source_history_mode_labels": list(layout.mode_labels),
                "local_matter_mode_labels": list(layout.mode_labels),
                "baryon_history_by_mode_label": baryon_rows_by_mode_label,
                "cdm_history_by_mode_label": cdm_rows_by_mode_label,
            },
        )
        result.layout_auxiliary_bundle = bundle
        return bundle

    def build_coupled_auxiliary_sector_history(
        self,
        result: IntegrationResult,
        *,
        covered_mode_label: str | None = None,
    ) -> _CoupledAuxiliarySectorHistory:
        return self.build_layout_auxiliary_history_bundle(
            result,
            covered_mode_label=covered_mode_label,
        ).coupled_sector_history

    def build_sampled_source_history(
        self,
        result: IntegrationResult,
        *,
        covered_mode_label: str | None = None,
    ) -> tuple[np.ndarray, np.ndarray]:
        bundle = self.build_layout_auxiliary_history_bundle(
            result,
            covered_mode_label=covered_mode_label,
        )
        return np.asarray(bundle.eta, dtype=np.float64), np.asarray(bundle.source_history, dtype=np.float64)

    def build_runtime_layout_projection(
        self,
        result: IntegrationResult,
        *,
        thomson_probe,
        visibility_amplitude: float,
        polarization_source: float,
        reionization_amplitude: float,
        covered_mode_label: str | None = None,
    ) -> _RuntimeLayoutProjectionBundle:
        from bass.los.family_backend_protocol import family_backend_gate_bundle
        from bass.runtime.gate_fragments import (
            ic_provenance_gate_bundle,
            physics_gate_fragment,
            tilt_boost_separation_gate_bundle,
        )
        from bass.hierarchy.ver3_layout_protocol import hierarchy_layout_gate_bundle
        from bass.hierarchy.ver3_state_contracts import project_runtime_native_state

        neutrino_tower = result.neutrino_tower
        if neutrino_tower is None:
            raise ValueError("runtime layout projection requires result.neutrino_tower")
        if self.seed_pack is None or self.seed_projection is None:
            raise ValueError("runtime layout projection requires initialized seed provenance")
        gamma_t_probe = _resolved_gamma_t(
            visibility_source=self.visibility_source,
            eta=float(result.eta[-1]),
            direction=self._direction,
            config=self.config,
        )
        mode_ops = self.backend.operator_factory(
            self._live_backend_state_payload(
                eta=float(result.eta[-1]),
                gamma_t_probe=float(gamma_t_probe),
                visibility_amplitude=float(visibility_amplitude),
                polarization_source=float(polarization_source),
                reionization_amplitude=float(reionization_amplitude),
            )
        )
        layout = build_hierarchy_layout(self.backend, self.backend.truncation)
        covered = str(
            getattr(mode_ops, "layout_metadata", {}).get(
                "mode_labels",
                [layout.mode_labels[0] if covered_mode_label is None else str(covered_mode_label)],
            )[0]
        )
        auxiliary_bundle = self.build_layout_auxiliary_history_bundle(
            result,
            covered_mode_label=covered,
        )
        coupled = auxiliary_bundle.coupled_sector_history
        matter_sector_status = {
            "baryon": "direct_fluid_rhs_live_history",
            "cdm": "direct_fluid_rhs_live_history",
        }
        matter_block_metadata = {
            "owner": str(coupled.metadata["owner"]),
            "reference_owner": str(coupled.metadata["reference_owner"]),
            "mode_label_extension_owner": str(coupled.metadata["mode_label_extension_owner"]),
            "reference_baryon_history": np.asarray(
                coupled.metadata["reference_baryon_history"],
                dtype=np.float64,
            ),
            "reference_cdm_history": np.asarray(
                coupled.metadata["reference_cdm_history"],
                dtype=np.float64,
            ),
        }
        b_history = np.asarray(coupled.photon_B_history, dtype=np.float64)
        b_history_by_mode_label, _ = self._ensure_live_b_mode_history_by_mode_label(result)
        t_history_by_mode_label = {
            str(mu): np.asarray(values, dtype=np.float64)
            for mu, values in getattr(result, "photon_T_history_by_mode_label", {}).items()
        }
        e_history_by_mode_label = {
            str(mu): np.asarray(values, dtype=np.float64)
            for mu, values in getattr(result, "photon_E_history_by_mode_label", {}).items()
        }
        nu_history_by_mode_label = {
            str(mu): np.asarray(values, dtype=np.float64)
            for mu, values in getattr(result, "neutrino_history_by_mode_label", {}).items()
        }
        result.photon_B_tower = np.asarray(b_history, dtype=np.float64)
        b_metadata = dict(result.solver_info.get("live_b_mode_history_metadata", {}))
        b_mode_owner = str(coupled.metadata.get("b_mode_owner", coupled.metadata["owner"]))
        b_mode_integration_scheme = str(
            b_metadata.get(
                "integration_scheme",
                coupled.metadata.get("b_mode_integration_scheme", coupled.metadata.get("integration_scheme", "")),
            )
        )
        b_mode_sector_status_resolved = (
            "main_state_coevolved_b_mode_history"
            if b_mode_owner == "ver2_native_integrator.main_state_photon_B"
            else "hierarchy_rhs_direct_b_mode_history"
        )
        source_history_owner = str(
            result.solver_info.get("live_source_history_metadata", {}).get("owner", "unavailable")
        )
        source_sector_status_resolved = (
            "main_state_coevolved_source_history"
            if source_history_owner == "ver2_native_integrator.main_state_source_history"
            else "mode_ops_source_template"
        )
        canonical_projection = project_runtime_native_state(
            layout=layout,
            layout_manifest=getattr(mode_ops, "layout_metadata", {}),
            photon_T=np.asarray(result.photon_T_tower[-1], dtype=np.float64),
            photon_T_blocks_by_mode_label={
                str(mu): np.asarray(values[-1], dtype=np.float64)
                for mu, values in t_history_by_mode_label.items()
            },
            photon_E=np.asarray(result.photon_E_tower[-1], dtype=np.float64),
            photon_E_blocks_by_mode_label={
                str(mu): np.asarray(values[-1], dtype=np.float64)
                for mu, values in e_history_by_mode_label.items()
            },
            photon_B=np.asarray(b_history[-1], dtype=np.float64),
            photon_B_blocks_by_mode_label={
                str(mu): np.asarray(values[-1], dtype=np.float64)
                for mu, values in b_history_by_mode_label.items()
            },
            photon_B_history_eta=np.asarray(auxiliary_bundle.eta, dtype=np.float64),
            photon_B_history_samples=b_history,
            photon_B_history_by_mode_label={
                str(mu): np.asarray(values, dtype=np.float64)
                for mu, values in b_history_by_mode_label.items()
            },
            b_sector_status=b_mode_sector_status_resolved,
            neutrino_tower=np.asarray(neutrino_tower[-1], dtype=np.float64),
            neutrino_blocks_by_mode_label={
                str(mu): np.asarray(values[-1], dtype=np.float64)
                for mu, values in nu_history_by_mode_label.items()
            },
            source_template=np.asarray(mode_ops.source_template, dtype=np.float64),
            baryon_block=np.asarray(coupled.baryon_history[-1], dtype=np.float64),
            cdm_block=np.asarray(coupled.cdm_history[-1], dtype=np.float64),
            baryon_blocks_by_mode_label={
                str(mu): np.asarray(values[-1], dtype=np.float64)
                for mu, values in auxiliary_bundle.metadata["baryon_history_by_mode_label"].items()
            },
            cdm_blocks_by_mode_label={
                str(mu): np.asarray(values[-1], dtype=np.float64)
                for mu, values in auxiliary_bundle.metadata["cdm_history_by_mode_label"].items()
            },
            matter_history_eta=np.asarray(coupled.eta, dtype=np.float64),
            baryon_history_samples=np.asarray(coupled.baryon_history, dtype=np.float64),
            cdm_history_samples=np.asarray(coupled.cdm_history, dtype=np.float64),
            baryon_history_by_mode_label={
                str(mu): np.asarray(values, dtype=np.float64)
                for mu, values in auxiliary_bundle.metadata["baryon_history_by_mode_label"].items()
            },
            cdm_history_by_mode_label={
                str(mu): np.asarray(values, dtype=np.float64)
                for mu, values in auxiliary_bundle.metadata["cdm_history_by_mode_label"].items()
            },
            matter_block_labels={
                "baryon": tuple(coupled.baryon_labels),
                "cdm": tuple(coupled.cdm_labels),
            },
            matter_sector_status=matter_sector_status,
            matter_block_metadata=matter_block_metadata,
            source_history_eta=np.asarray(auxiliary_bundle.eta, dtype=np.float64),
            source_history_samples=np.asarray(auxiliary_bundle.source_history, dtype=np.float64),
            source_history_by_mode_label={
                str(mu): np.asarray(values, dtype=np.float64)
                for mu, values in auxiliary_bundle.source_history_by_mode_label.items()
            },
            source_sector_status=source_sector_status_resolved,
            covered_mode_label=covered,
        )
        source_block = np.asarray(
            canonical_projection.hierarchy_state.source_history_block["src"],
            dtype=np.float64,
        )
        b_mode_proxy = np.asarray(b_history[-1], dtype=np.float64)
        b_mode_sector_status = str(canonical_projection.sector_status.get("ph_B", "zero_filled_not_evolved"))
        b_mode_payload_available = b_mode_sector_status != "zero_filled_not_evolved"
        gate_provenance = {
            "layout_projection_owner": "ver2_native_integrator.build_runtime_layout_projection",
                "layout_auxiliary_bundle_owner": str(auxiliary_bundle.metadata["owner"]),
                "layout_state_history_sample_count": int(auxiliary_bundle.layout_state_history.shape[0]),
                "layout_state_history_size": int(auxiliary_bundle.layout_state_history.shape[1]),
                "covered_mode_label": covered,
                "covered_mode_labels": list(canonical_projection.covered_mode_labels),
            "zero_filled_mode_labels": list(canonical_projection.zero_filled_mode_labels),
            "projection_mode": str(canonical_projection.metadata.get("projection_mode", "")),
            "resolved_sector_order": list(canonical_projection.metadata.get("resolved_sector_order", ())),
            "layout_source_block_owner": str(
                canonical_projection.hierarchy_state.metadata["sector_status"]["src"]
            ),
            "layout_source_history_owner": str(
                source_history_owner
            ),
            "layout_source_mode_labels": list(
                canonical_projection.hierarchy_state.source_history_block.get(
                    "mode_label_blocks",
                    {},
                ).keys()
            ),
            "layout_local_matter_owner": str(coupled.metadata["owner"]),
            "layout_local_matter_extension_owner": str(coupled.metadata["mode_label_extension_owner"]),
            "layout_local_matter_mode_labels": list(
                canonical_projection.hierarchy_state.matter_block.get(
                    "mode_label_blocks",
                    {},
                ).keys()
            ),
            "layout_b_mode_payload_available": bool(b_mode_payload_available),
            "layout_b_mode_payload_status": b_mode_sector_status,
            "layout_b_mode_proxy_source": b_mode_owner,
            "layout_b_mode_integration_scheme": b_mode_integration_scheme,
            "layout_b_mode_mode_labels": list(
                canonical_projection.hierarchy_state.photon_polarization_block.get(
                    "mode_label_blocks",
                    {},
                ).keys()
            ),
            "layout_b_mode_history_mode_labels": list(
                canonical_projection.hierarchy_state.photon_polarization_block.get(
                    "mode_label_history",
                    {},
                ).keys()
            ),
            "layout_auxiliary_integration_scheme": str(
                coupled.metadata.get(
                    "extension_integration_scheme",
                    coupled.metadata.get("integration_scheme", ""),
                )
            ),
            "layout_auxiliary_reduced_block_size": int(coupled.metadata.get("reduced_block_size", 0)),
        }
        return _RuntimeLayoutProjectionBundle(
            mode_ops=mode_ops,
            layout=layout,
            covered_mode_label=covered,
            auxiliary_history_bundle=auxiliary_bundle,
            canonical_projection=canonical_projection,
            metadata={
                "owner": "ver2_native_integrator.build_runtime_layout_projection",
                "gamma_t_probe": float(gamma_t_probe),
                "layout_gate_provenance": gate_provenance,
                "gate_registry_fragment": {
                    **physics_gate_fragment(
                        bianchi_type=self.backend.family_spec.family,
                        background_monitor=self.background_monitor,
                        species=self.species,
                        visibility_source=self.visibility_source,
                        thomson_probe=thomson_probe,
                    ),
                    "tilt_boost_separation_gate": tilt_boost_separation_gate_bundle(
                        bianchi_type=self.backend.family_spec.family,
                        branch=str(self.background_monitor.branch),
                        background_monitor=self.background_monitor,
                    ),
                    "ic_provenance_gate": ic_provenance_gate_bundle(
                        bianchi_type=self.backend.family_spec.family,
                        branch=str(self.background_monitor.branch),
                        backend=self.backend,
                        seed_pack=self.seed_pack,
                        seed_projection=self.seed_projection,
                    ),
                    "family_backend_gate": family_backend_gate_bundle(self.backend, mode_ops),
                    "hierarchy_layout_gate": hierarchy_layout_gate_bundle(
                        self.backend,
                        mode_ops,
                        provenance_metadata=gate_provenance,
                    ),
                },
                "solver_info_fragment": {
                    "layout_contract_consumed": True,
                    "layout_mode_labels": list(getattr(mode_ops, "layout_metadata", {}).get("mode_labels", [])),
                    "layout_sector_order": list(getattr(mode_ops, "layout_metadata", {}).get("sector_order", [])),
                    "layout_operator_kernel_family": str(getattr(mode_ops, "operator_kernel_family", "")),
                    "seed_provenance_mode": str(getattr(mode_ops, "seed_provenance_mode", "")),
                    "layout_source_template_consumed": bool(
                        np.any(np.abs(source_block) > 0.0)
                    ),
                    "layout_source_template_channel": "canonical_projection.src_block",
                    "layout_source_block_norm": float(np.linalg.norm(source_block)),
                    "layout_source_block_owner": str(
                        canonical_projection.hierarchy_state.metadata["sector_status"]["src"]
                    ),
                    "layout_source_history_owner": str(
                        result.solver_info.get("live_source_history_metadata", {}).get(
                            "owner",
                            "unavailable",
                        )
                    ),
                    "layout_source_history_sample_count": int(auxiliary_bundle.source_history.shape[0]),
                    "layout_source_mode_labels": list(
                        canonical_projection.hierarchy_state.source_history_block.get(
                            "mode_label_blocks",
                            {},
                        ).keys()
                    ),
                    "layout_local_matter_blocks_consumed": True,
                    "layout_local_matter_owner": str(coupled.metadata["owner"]),
                    "layout_local_matter_extension_owner": str(
                        coupled.metadata["mode_label_extension_owner"]
                    ),
                    "layout_local_matter_mode_labels": list(
                        canonical_projection.hierarchy_state.matter_block.get(
                            "mode_label_blocks",
                            {},
                        ).keys()
                    ),
                    "layout_local_matter_sample_count": int(coupled.metadata["history_sample_count"]),
                    "layout_local_matter_reference_owner": str(coupled.metadata["reference_owner"]),
                    "layout_local_matter_reference_sample_count": int(
                        coupled.metadata["reference_sample_count"]
                    ),
                    "layout_local_matter_reference_delta_norm": float(
                        coupled.metadata["reference_delta_norm"]
                    ),
                    "layout_b_mode_payload_available": bool(b_mode_payload_available),
                    "layout_b_mode_payload_status": b_mode_sector_status,
                    "layout_b_mode_proxy_consumed": bool(np.any(np.abs(b_mode_proxy) > 0.0)),
                    "layout_b_mode_proxy_norm": float(np.linalg.norm(b_mode_proxy)),
                    "layout_b_mode_proxy_source": b_mode_owner,
                    "layout_b_mode_integration_scheme": b_mode_integration_scheme,
                    "layout_b_mode_history_sample_count": int(b_history.shape[0]),
                    "layout_b_mode_mode_labels": list(
                        canonical_projection.hierarchy_state.photon_polarization_block.get(
                            "mode_label_blocks",
                            {},
                        ).keys()
                    ),
                    "layout_b_mode_history_mode_labels": list(
                        canonical_projection.hierarchy_state.photon_polarization_block.get(
                            "mode_label_history",
                            {},
                        ).keys()
                    ),
                    "layout_auxiliary_coupling_passes": int(coupled.metadata["coupling_passes"]),
                    "layout_auxiliary_integration_scheme": str(
                        coupled.metadata.get(
                            "extension_integration_scheme",
                            coupled.metadata.get("integration_scheme", ""),
                        )
                    ),
                    "layout_auxiliary_reduced_block_size": int(
                        coupled.metadata.get("reduced_block_size", 0)
                    ),
                    "layout_auxiliary_bundle_owner": str(auxiliary_bundle.metadata["owner"]),
                    "layout_state_history_sample_count": int(auxiliary_bundle.layout_state_history.shape[0]),
                    "layout_state_history_size": int(auxiliary_bundle.layout_state_history.shape[1]),
                    "layout_projection_owner": "ver2_native_integrator.build_runtime_layout_projection",
                },
            },
        )

    def build_runtime_thomson_probe(
        self,
        result: IntegrationResult,
        *,
        gamma_t: float,
    ) -> ExactThomsonSource:
        b_history, _ = self._ensure_live_b_mode_history(result)
        local_matter_history = self._ensure_live_local_matter_history(result)
        temperature_state = unpack_hierarchy(result.photon_T_tower[-1], result.L_max)
        polarization_state = PolarizationHierarchyState(
            E=unpack_hierarchy(result.photon_E_tower[-1], result.L_max)
        )
        return exact_thomson_source(
            ElectronFrameThomsonContext(),
            temperature_state=temperature_state,
            polarization_state=polarization_state,
            v_b_real_sph=_electron_velocity_real_sph_from_baryon_row(
                np.asarray(local_matter_history.baryon_history[-1], dtype=np.float64)
            ),
            Gamma_T=float(gamma_t),
            direction=np.asarray(self.config.tilt_direction, dtype=np.float64),
            tilted_electron=self._tilted_electron_at(float(result.eta[-1])),
            b_state=unpack_hierarchy(np.asarray(b_history[-1], dtype=np.float64), result.L_max),
        )

    def build_runtime_geodesic_probe(self):
        from bass.transport.geodesics import (
            PhotonGeodesicState,
            ScreenBasisState,
            photon_geodesic_rhs,
        )

        direction = np.array([1.0, 0.0, 0.0], dtype=np.float64)
        screen_basis = ScreenBasisState(
            u=np.array([0.0, 1.0, 0.0], dtype=np.float64),
            v=np.array([0.0, 0.0, 1.0], dtype=np.float64),
        )
        state = PhotonGeodesicState(
            energy=1.0,
            direction=direction,
            screen_basis=screen_basis,
        )
        return photon_geodesic_rhs(
            state=state,
            H=float(self.background_monitor.H[-1]),
            sigma_ab=self.background_monitor.sigma_tensor[-1],
            geometry=self.background_monitor.initial_conditions.geometry,
        )

    def build_runtime_trace_products(
        self,
        result: IntegrationResult,
        *,
        reionization_amplitude: float,
    ) -> _RuntimeTraceProducts:
        geodesic_probe = self.build_runtime_geodesic_probe()
        gamma_t_probe = _resolved_gamma_t(
            visibility_source=self.visibility_source,
            eta=float(result.eta[-1]),
            direction=np.asarray(self.config.tilt_direction, dtype=np.float64),
            config=self.config,
        )
        thomson_probe = self.build_runtime_thomson_probe(
            result=result,
            gamma_t=float(gamma_t_probe),
        )
        layout_projection = self.build_runtime_layout_projection(
            result,
            thomson_probe=thomson_probe,
            visibility_amplitude=float(thomson_probe.scalar_monopole_input),
            polarization_source=float(thomson_probe.polarization_quadrupole_norm),
            reionization_amplitude=float(reionization_amplitude),
        )
        return _RuntimeTraceProducts(
            geodesic_probe=geodesic_probe,
            gamma_t_probe=float(gamma_t_probe),
            thomson_probe=thomson_probe,
            layout_projection=layout_projection,
            metadata={
                "owner": "ver2_native_integrator.build_runtime_trace_products",
                "layout_projection_owner": str(layout_projection.metadata.get("owner", "")),
            },
        )

    def build_runtime_execution_trace(
        self,
        result: IntegrationResult,
        *,
        reionization_amplitude: float,
    ) -> _RuntimeExecutionTraceBundle:
        cached_trace = getattr(result, "runtime_execution_trace", None)
        if isinstance(cached_trace, _RuntimeExecutionTraceBundle):
            cached_amp = float(cached_trace.metadata.get("reionization_amplitude", reionization_amplitude))
            if np.isclose(cached_amp, float(reionization_amplitude), atol=0.0, rtol=0.0):
                return cached_trace
        if self.startup_gate is None or self.seed_projection is None or self.seed_pack is None:
            raise ValueError("runtime execution trace requires initialized startup and seed provenance")
        runtime_trace_products = self.build_runtime_trace_products(
            result,
            reionization_amplitude=float(reionization_amplitude),
        )
        trace = _RuntimeExecutionTraceBundle(
            background_monitor=self.background_monitor,
            startup_gate=self.startup_gate,
            startup_state=self.startup_state,
            seed_projection=self.seed_projection,
            seed_pack=self.seed_pack,
            visibility_source=self.visibility_source,
            runtime_trace_products=runtime_trace_products,
            metadata={
                "owner": "ver2_native_integrator.build_runtime_execution_trace",
                "runtime_trace_products_owner": str(runtime_trace_products.metadata.get("owner", "")),
                "reionization_amplitude": float(reionization_amplitude),
            },
        )
        result.runtime_execution_trace = trace
        return trace

    def _compute_tca_mask(self, etas: np.ndarray) -> np.ndarray:
        mask = np.zeros(len(etas), dtype=bool)
        if not isinstance(self.closure, TCAClosure):
            return mask
        for i, eta in enumerate(etas):
            gamma = _resolved_gamma_t(
                eta=float(eta),
                direction=self._direction,
                visibility_source=self.visibility_source,
                config=self.config,
            )
            H = self._h_local_at(float(eta))
            if H > 0.0 and gamma > 0.0:
                mask[i] = gamma / H > self.config.gamma_T_over_H_threshold
        return mask

    def _solve_segment(
        self,
        *,
        eta_start: float,
        eta_stop: float,
        y0: np.ndarray,
        eta_eval: np.ndarray,
        tca_tracker: list[bool],
    ):
        if str(self.config.solver_method).upper() == "IMEX_MIDPOINT_BDF":
            return self._solve_segment_imex(
                eta_start=eta_start,
                eta_stop=eta_stop,
                y0=y0,
                eta_eval=eta_eval,
                tca_tracker=tca_tracker,
            )
        max_step = (
            self.config.eta_final_mpc - self.config.eta_initial_mpc
        ) / 1000.0
        sol = solve_ivp(
            lambda eta, y: self._rhs(eta, y, tca_tracker=tca_tracker),
            (float(eta_start), float(eta_stop)),
            np.asarray(y0, dtype=np.float64),
            t_eval=np.asarray(eta_eval, dtype=np.float64),
            method=self.config.solver_method,
            rtol=self.config.rtol,
            atol=self.config.atol,
            max_step=max_step,
        )
        if not sol.success:
            eta_fail = float(sol.t[-1]) if len(sol.t) > 0 else float(eta_start)
            raise RuntimeError(f"solve_ivp failed: {sol.message} at η={eta_fail}")
        if np.any(~np.isfinite(sol.y)):
            raise RuntimeError("solve_ivp produced non-finite entries in VER2 native Tier-B core")
        return sol

    def _solve_segment_imex(
        self,
        *,
        eta_start: float,
        eta_stop: float,
        y0: np.ndarray,
        eta_eval: np.ndarray,
        tca_tracker: list[bool],
    ) -> _SegmentResult:
        eta_nodes = np.asarray(eta_eval, dtype=np.float64)
        if eta_nodes.ndim != 1 or eta_nodes.size == 0:
            raise ValueError("eta_eval must be a non-empty 1-D array")
        if not np.isclose(float(eta_nodes[0]), float(eta_start)):
            raise ValueError("eta_eval[0] must match eta_start for IMEX segment solves")
        if not np.isclose(float(eta_nodes[-1]), float(eta_stop)):
            raise ValueError("eta_eval[-1] must match eta_stop for IMEX segment solves")

        total_span = max(float(self.config.eta_final_mpc - self.config.eta_initial_mpc), 1.0e-12)
        nominal_interval = max(float(np.max(np.diff(eta_nodes))), 1.0e-12)
        split_step = min(0.05, nominal_interval)
        split_step = max(split_step, total_span / 2000.0)
        min_step = max(total_span / 50000.0, 1.0e-8)
        fixed_point_iters = 6

        states = [np.asarray(y0, dtype=np.float64)]
        nfev = 0
        njev = 0
        nlu = 0
        message = "The IMEX split executor successfully reached the end of the integration interval."
        y_current = np.asarray(y0, dtype=np.float64)
        cached_residual_joint_affine: ReducedJointAffineOperator | None = None
        cached_covered_source_affine = None

        for left, right in zip(eta_nodes[:-1], eta_nodes[1:]):
            eta_current = float(left)
            eta_target = float(right)
            while eta_current < eta_target - 1.0e-15:
                remaining = eta_target - eta_current
                eta_left = float(eta_current)
                y_left = np.asarray(y_current, dtype=np.float64)
                state_scale = max(float(np.linalg.norm(y_current, ord=np.inf)), 1.0)
                explicit_0 = self._explicit_rhs(eta_current, y_current)
                nfev += 1
                explicit_scale = float(np.linalg.norm(explicit_0, ord=np.inf)) / state_scale
                trial_h = min(remaining, split_step, 0.05 / max(explicit_scale, 1.0e-12))
                trial_h = remaining if remaining <= min_step else max(min(trial_h, remaining), min_step)
                accepted = False
                for _ in range(20):
                    midpoint = eta_current + 0.5 * trial_h
                    predictor = np.asarray(y_current + 0.5 * trial_h * explicit_0, dtype=np.float64)
                    if np.any(~np.isfinite(predictor)):
                        trial_h *= 0.5
                        if trial_h < min_step:
                            break
                        continue
                    explicit_mid = self._explicit_rhs(midpoint, predictor)
                    nfev += 1
                    stage = np.asarray(y_current + trial_h * explicit_mid, dtype=np.float64)
                    if np.any(~np.isfinite(stage)):
                        trial_h *= 0.5
                        if trial_h < min_step:
                            break
                        continue
                    eta_next = eta_current + trial_h
                    if abs(float(self.config.tilt_rapidity)) == 0.0:
                        candidate = self._orthogonal_implicit_step(
                            eta=float(eta_next),
                            stage=stage,
                            dt=float(trial_h),
                            tca_tracker=tca_tracker,
                        )
                        if np.any(~np.isfinite(candidate)):
                            trial_h *= 0.5
                            if trial_h < min_step:
                                break
                            continue
                        candidate_scale = float(np.linalg.norm(candidate, ord=np.inf))
                        if (
                            candidate_scale > max(8.0 * state_scale, 1.0e6)
                            and trial_h > min_step
                        ):
                            trial_h *= 0.5
                            continue
                        with np.errstate(over="ignore", invalid="ignore"):
                            candidate, cached_covered_source_affine = self._orthogonal_covered_source_ros2_step(
                                eta_left=float(eta_left),
                                y_left=y_left,
                                eta_right=float(eta_next),
                                y_right=candidate,
                                affine_left=cached_covered_source_affine,
                            )
                        if np.any(~np.isfinite(candidate)):
                            cached_covered_source_affine = None
                            trial_h *= 0.5
                            if trial_h < min_step:
                                break
                            continue
                        candidate_scale = float(np.linalg.norm(candidate, ord=np.inf))
                        if (
                            candidate_scale > max(8.0 * state_scale, 1.0e6)
                            and trial_h > min_step
                        ):
                            cached_covered_source_affine = None
                            trial_h *= 0.5
                            continue
                        with np.errstate(over="ignore", invalid="ignore"):
                            candidate, cached_residual_joint_affine = self._orthogonal_residual_joint_ros2_step(
                                eta_left=float(eta_left),
                                y_left=y_left,
                                eta_right=float(eta_next),
                                y_right=candidate,
                                affine_left=cached_residual_joint_affine,
                            )
                        if np.any(~np.isfinite(candidate)):
                            cached_residual_joint_affine = None
                            trial_h *= 0.5
                            if trial_h < min_step:
                                break
                            continue
                        candidate_scale = float(np.linalg.norm(candidate, ord=np.inf))
                        if (
                            candidate_scale > max(8.0 * state_scale, 1.0e6)
                            and trial_h > min_step
                        ):
                            cached_residual_joint_affine = None
                            trial_h *= 0.5
                            continue
                        y_current = candidate
                        eta_current = float(eta_next)
                        accepted = True
                        break
                    candidate = stage.copy()
                    converged = False
                    fp_tol = float(self.config.atol) + float(self.config.rtol) * max(
                        1.0,
                        float(np.linalg.norm(stage, ord=np.inf)),
                    )
                    for _ in range(fixed_point_iters):
                        implicit_val = self._implicit_rhs(eta_next, candidate, tca_tracker=None)
                        nfev += 1
                        next_candidate = np.asarray(stage + trial_h * implicit_val, dtype=np.float64)
                        if np.any(~np.isfinite(next_candidate)):
                            break
                        delta = float(np.linalg.norm(next_candidate - candidate, ord=np.inf))
                        candidate = next_candidate
                        njev += 1
                        if delta <= fp_tol:
                            converged = True
                            break
                    if not converged:
                        implicit_sol = solve_ivp(
                            lambda eta, y: self._implicit_rhs(eta, y, tca_tracker=None),
                            (eta_current, eta_next),
                            stage,
                            t_eval=np.array([eta_next], dtype=np.float64),
                            method="BDF",
                            rtol=self.config.rtol,
                            atol=self.config.atol,
                            max_step=max(abs(trial_h), 1.0e-12),
                        )
                        nfev += int(implicit_sol.nfev)
                        njev += int(implicit_sol.njev)
                        nlu += int(implicit_sol.nlu)
                        if not implicit_sol.success or np.any(~np.isfinite(implicit_sol.y)):
                            trial_h *= 0.5
                            if trial_h < min_step:
                                break
                            continue
                        candidate = np.asarray(implicit_sol.y[:, -1], dtype=np.float64)
                    candidate_scale = float(np.linalg.norm(candidate, ord=np.inf))
                    if (
                        candidate_scale > max(8.0 * state_scale, 1.0e6)
                        and trial_h > min_step
                    ):
                        trial_h *= 0.5
                        continue
                    gamma_t = _resolved_gamma_t(
                        eta=float(eta_next),
                        direction=self._direction,
                        visibility_source=self.visibility_source,
                        config=self.config,
                    )
                    H_local = self._h_local_at(float(eta_next))
                    if H_local > 0.0 and gamma_t > 0.0:
                        tca_tracker.append(gamma_t / H_local > self.config.gamma_T_over_H_threshold)
                    else:
                        tca_tracker.append(False)
                    y_current = candidate
                    eta_current = float(eta_next)
                    cached_residual_joint_affine = None
                    accepted = True
                    break
                if not accepted:
                    cached_residual_joint_affine = None
                    cached_covered_source_affine = None
                    if abs(float(self.config.tilt_rapidity)) > 0.0:
                        fallback_sol = solve_ivp(
                            lambda eta, y: self._rhs(eta, y, tca_tracker=None),
                            (eta_current, eta_target),
                            y_current,
                            t_eval=np.array([eta_target], dtype=np.float64),
                            method="BDF",
                            rtol=self.config.rtol,
                            atol=self.config.atol,
                            max_step=max(abs(eta_target - eta_current), 1.0e-12),
                        )
                        nfev += int(fallback_sol.nfev)
                        njev += int(fallback_sol.njev)
                        nlu += int(fallback_sol.nlu)
                        if fallback_sol.success and np.all(np.isfinite(fallback_sol.y)):
                            gamma_t = _resolved_gamma_t(
                                eta=float(eta_target),
                                direction=self._direction,
                                visibility_source=self.visibility_source,
                                config=self.config,
                            )
                            H_local = self._h_local_at(float(eta_target))
                            if H_local > 0.0 and gamma_t > 0.0:
                                tca_tracker.append(
                                    gamma_t / H_local > self.config.gamma_T_over_H_threshold
                                )
                            else:
                                tca_tracker.append(False)
                            y_current = np.asarray(fallback_sol.y[:, -1], dtype=np.float64)
                            eta_current = float(eta_target)
                            cached_residual_joint_affine = None
                            cached_covered_source_affine = None
                            accepted = True
                            continue
                    raise RuntimeError(
                        "IMEX split executor failed to find a finite accepted substep "
                        f"before η={eta_target}"
                    )
            states.append(y_current.copy())
        return _SegmentResult(
            t=eta_nodes,
            y=np.column_stack(states),
            nfev=nfev,
            njev=njev,
            nlu=nlu,
            status=0,
            message=message,
        )

    def _build_result(
        self,
        *,
        eta: np.ndarray,
        photon_T_tower: np.ndarray,
        photon_E_tower: np.ndarray,
        photon_B_tower: np.ndarray,
        neutrino_tower: np.ndarray,
        baryon_local_history: np.ndarray,
        cdm_local_history: np.ndarray,
        source_local_history: np.ndarray,
        residual_local_history: np.ndarray,
        residual_harmonic_history: np.ndarray,
        residual_source_history: np.ndarray,
        nfev: int,
        njev: int,
        nlu: int,
        status: int,
        message: str,
        tca_tracker: list[bool],
        checkpoint_write_count: int = 0,
        restart_used: bool = False,
    ) -> IntegrationResult:
        neutrino_reduced = np.asarray(
            [
                _reduced_summary_from_neutrino_tower(
                    unpack_hierarchy(state, self.config.L_max)
                )
                for state in neutrino_tower
            ],
            dtype=np.float64,
        )
        eta_arr = np.asarray(eta, dtype=np.float64)
        a_arr, sigma_plus, sigma_minus = self._background_projection(eta_arr)
        tca_mask = self._compute_tca_mask(eta_arr)

        from bass.hierarchy.event_detection import detect_critical_events

        events = detect_critical_events(self.species, self.species.bg_table)
        solver_info = {
            "nfev": int(nfev),
            "njev": int(njev),
            "nlu": int(nlu),
            "status": int(status),
            "message": str(message),
            "solver_method": str(self.config.solver_method),
            "tca_tracker_len": len(tca_tracker),
            "tca_tracker_any_active": any(tca_tracker),
            "tier_b_core_owner": "ver2_s1s2_native",
            "background_owner": "background.evolution",
            "seed_k_comoving": float(self.seed_k_comoving),
            "seed_injection_mode": str(self.seed_injection_mode),
            "seed_velocity_scale": float(self.seed_velocity_scale),
            "seed_factory_owner": "family_backend.seed_factory",
            "seed_factory_mode": None if self.seed_pack is None else str(self.seed_pack.seed_mode),
            "seed_chart": None if self.seed_pack is None else str(self.seed_pack.chart),
            "seed_family": None if self.seed_pack is None else str(self.seed_pack.family),
            "seed_branch": None if self.seed_pack is None else str(self.seed_pack.branch),
            "seed_pack_metadata": {} if self.seed_pack is None else dict(self.seed_pack.metadata),
            "seed_pack_normalization": {} if self.seed_pack is None else dict(self.seed_pack.normalization),
            "startup_manifold_applied": bool(self.startup_state is not None),
            "startup_gate_selected": bool(self.startup_gate.startup_selected if self.startup_gate is not None else False),
            "neutrino_hierarchy_mode": "full_pstf_with_reduced_summary_export",
            "layout_operator_consumed": bool(self.mode_ops is not None),
            "layout_collision_operator_source": (
                "mode_ops.A_coll_diagonal"
                if self.mode_ops is not None
                else "gamma_t_scalar_fallback"
            ),
            "layout_initial_mode_ops_owner": (
                "ver2_native_integrator.__init__"
                if self.mode_ops is not None
                else "disabled"
            ),
            "checkpoint_write_count": int(checkpoint_write_count),
            "restart_used": bool(restart_used),
            "collision_owner": "exact_thomson_wrapper",
            "residual_harmonic_orthogonal_bridge": (
                "ros2w_sparse_reduced_joint_block"
                if self._residual_harmonic_dof > 0 and str(self.config.solver_method).upper() == "IMEX_MIDPOINT_BDF"
                else "disabled"
            ),
        }
        local_matter_history = _LocalMatterHistory(
            eta=eta_arr,
            baryon_history=np.asarray(baryon_local_history, dtype=np.float64),
            cdm_history=np.asarray(cdm_local_history, dtype=np.float64),
            baryon_labels=("delta_b", "v_b", "v_e", "drag_lock_residual"),
            cdm_labels=("delta_c", "v_c"),
            metadata={
                "owner": "ver2_native_integrator.main_state_local_matter",
                "phi_dot_source": "unavailable_assumed_zero_homogeneous_limit",
                "photon_dipole_source": "live_runtime_ph_I_ell1_m0",
                "gamma_t_source": "resolved_visibility_gamma_t",
                "integration_scheme": "main_state_coevolved",
                "history_sample_count": int(eta_arr.size),
            },
        )
        solver_info["live_local_matter_history_metadata"] = {
            **dict(local_matter_history.metadata),
            "labels": {
                "baryon": tuple(local_matter_history.baryon_labels),
                "cdm": tuple(local_matter_history.cdm_labels),
            },
        }
        baryon_by_mode_label = {
            self._layout_covered_mode_label: np.asarray(local_matter_history.baryon_history, dtype=np.float64)
        }
        cdm_by_mode_label = {
            self._layout_covered_mode_label: np.asarray(local_matter_history.cdm_history, dtype=np.float64)
        }
        residual_history_arr = np.asarray(residual_local_history, dtype=np.float64)
        if residual_history_arr.ndim != 2 or residual_history_arr.shape[0] != eta_arr.size:
            raise ValueError("residual_local_history must have shape (len(eta), n_residual)")
        offset = 0
        for mu in self._residual_mode_labels:
            baryon_by_mode_label[str(mu)] = np.asarray(
                residual_history_arr[:, offset : offset + _BARYON_LOCAL_DOF],
                dtype=np.float64,
            )
            offset += _BARYON_LOCAL_DOF
            cdm_by_mode_label[str(mu)] = np.asarray(
                residual_history_arr[:, offset : offset + _CDM_LOCAL_DOF],
                dtype=np.float64,
            )
            offset += _CDM_LOCAL_DOF
        solver_info["live_mode_label_local_matter_history_metadata"] = {
            "owner": "ver2_native_integrator.main_state_mode_label_local_matter",
            "history_sample_count": int(eta_arr.size),
            "mode_labels": list(self._layout.mode_labels),
            "covered_mode_label": self._layout_covered_mode_label,
        }
        residual_harmonic_history_arr = np.asarray(residual_harmonic_history, dtype=np.float64)
        if residual_harmonic_history_arr.ndim != 2 or residual_harmonic_history_arr.shape[0] != eta_arr.size:
            raise ValueError("residual_harmonic_history must have shape (len(eta), n_residual)")
        photon_t_history_by_mode_label = {
            self._layout_covered_mode_label: np.asarray(photon_T_tower, dtype=np.float64)
        }
        photon_e_history_by_mode_label = {
            self._layout_covered_mode_label: np.asarray(photon_E_tower, dtype=np.float64)
        }
        photon_b_history_by_mode_label = {
            self._layout_covered_mode_label: np.asarray(photon_B_tower, dtype=np.float64)
        }
        neutrino_history_by_mode_label = {
            self._layout_covered_mode_label: np.asarray(neutrino_tower, dtype=np.float64)
        }
        harmonic_width = _tower_size(self.config.L_max)
        offset = 0
        for mu in self._residual_mode_labels:
            photon_t_history_by_mode_label[str(mu)] = np.asarray(
                residual_harmonic_history_arr[:, offset : offset + harmonic_width],
                dtype=np.float64,
            )
            offset += harmonic_width
            photon_e_history_by_mode_label[str(mu)] = np.asarray(
                residual_harmonic_history_arr[:, offset : offset + harmonic_width],
                dtype=np.float64,
            )
            offset += harmonic_width
            photon_b_history_by_mode_label[str(mu)] = np.asarray(
                residual_harmonic_history_arr[:, offset : offset + harmonic_width],
                dtype=np.float64,
            )
            offset += harmonic_width
            neutrino_history_by_mode_label[str(mu)] = np.asarray(
                residual_harmonic_history_arr[:, offset : offset + harmonic_width],
                dtype=np.float64,
            )
            offset += harmonic_width
        solver_info["live_mode_label_harmonic_history_metadata"] = {
            "owner": "ver2_native_integrator.main_state_mode_label_harmonics",
            "history_sample_count": int(eta_arr.size),
            "mode_labels": list(self._layout.mode_labels),
            "covered_mode_label": self._layout_covered_mode_label,
            "residual_mode_labels": list(self._residual_mode_labels),
            "sectors": ("ph_I", "ph_E", "ph_B", "nu_I"),
            "covered_owner": "ver2_native_integrator.main_state_harmonics",
            "residual_owner": "ver2_native_integrator.main_state_mode_label_harmonics",
            "integration_scheme": "main_state_coevolved",
        }
        solver_info["live_b_mode_history_metadata"] = {
            "owner": "ver2_native_integrator.main_state_photon_B",
            "history_sample_count": int(eta_arr.size),
            "integration_scheme": "main_state_coevolved",
            "radiation_rhs_owner": "hierarchy_rhs_photon_from_state",
            "collision_owner": "projected_thomson_source.polarization_B",
        }
        solver_info["live_b_mode_history_by_mode_label_metadata"] = {
            "owner": "ver2_native_integrator.main_state_mode_label_harmonics",
            "sector": "ph_B",
            "history_sample_count": int(eta_arr.size),
            "mode_labels": list(self._layout.mode_labels),
            "covered_mode_label": self._layout_covered_mode_label,
            "residual_mode_labels": list(self._residual_mode_labels),
            "covered_owner": "ver2_native_integrator.main_state_photon_B",
            "integration_scheme": "main_state_coevolved",
        }
        covered_source_history = np.asarray(source_local_history, dtype=np.float64)
        if covered_source_history.ndim != 2 or covered_source_history.shape[0] != eta_arr.size:
            raise ValueError("source_local_history must have shape (len(eta), n_source)")
        residual_source_history_arr = np.asarray(residual_source_history, dtype=np.float64)
        if residual_source_history_arr.ndim != 2 or residual_source_history_arr.shape[0] != eta_arr.size:
            raise ValueError("residual_source_history must have shape (len(eta), n_residual)")
        source_width = int(self._layout.sector_local_dofs["src"])
        source_history_by_mode_label = {
            self._layout_covered_mode_label: np.asarray(covered_source_history, dtype=np.float64)
        }
        offset = 0
        for mu in self._residual_mode_labels:
            source_history_by_mode_label[str(mu)] = np.asarray(
                residual_source_history_arr[:, offset : offset + source_width],
                dtype=np.float64,
            )
            offset += source_width
        solver_info["live_source_history_metadata"] = {
            "owner": "ver2_native_integrator.main_state_source_history",
            "covered_owner": "ver2_native_integrator.main_state_covered_source",
            "residual_owner": "ver2_native_integrator.main_state_mode_label_source",
            "history_sample_count": int(eta_arr.size),
            "mode_labels": list(self._layout.mode_labels),
            "covered_mode_label": self._layout_covered_mode_label,
            "integration_scheme": "main_state_coevolved",
        }
        result = IntegrationResult(
            eta=eta_arr,
            a=a_arr,
            Sigma_plus=sigma_plus,
            Sigma_minus=sigma_minus,
            photon_T_tower=np.asarray(photon_T_tower, dtype=np.float64),
            photon_E_tower=np.asarray(photon_E_tower, dtype=np.float64),
            neutrino_reduced=neutrino_reduced,
            critical_events=events,
            config=self.config,
            solver_info=solver_info,
            tca_active_mask=tca_mask,
            photon_T_history_by_mode_label=photon_t_history_by_mode_label,
            photon_E_history_by_mode_label=photon_e_history_by_mode_label,
            neutrino_tower=np.asarray(neutrino_tower, dtype=np.float64),
            neutrino_history_by_mode_label=neutrino_history_by_mode_label,
            photon_B_tower=np.asarray(photon_B_tower, dtype=np.float64),
            photon_B_history_by_mode_label=photon_b_history_by_mode_label,
            baryon_local_history=np.asarray(local_matter_history.baryon_history, dtype=np.float64),
            cdm_local_history=np.asarray(local_matter_history.cdm_history, dtype=np.float64),
            residual_local_history=residual_history_arr,
            residual_harmonic_history=residual_harmonic_history_arr,
            residual_source_history=residual_source_history_arr,
            baryon_local_history_by_mode_label=baryon_by_mode_label,
            cdm_local_history_by_mode_label=cdm_by_mode_label,
            source_history=np.asarray(covered_source_history, dtype=np.float64),
            source_history_by_mode_label={
                str(mu): np.asarray(values, dtype=np.float64)
                for mu, values in source_history_by_mode_label.items()
            },
        )
        return result

    def run(
        self,
        *,
        checkpoint_every_n_steps: int | None = None,
        checkpoint_callback: Callable[[NativeTierBRestartState], None] | None = None,
        restart_state: NativeTierBRestartState | None = None,
    ) -> IntegrationResult:
        eta_out = np.linspace(
            self.config.eta_initial_mpc,
            self.config.eta_final_mpc,
            self.config.n_output,
        )
        tower_size = (self.config.L_max + 1) ** 2
        tca_tracker: list[bool] = []

        if restart_state is None:
            y_current = self.initial_state()
            current_index = 0
            eta_segments: list[np.ndarray] = []
            photon_T_segments: list[np.ndarray] = []
            photon_E_segments: list[np.ndarray] = []
            photon_B_segments: list[np.ndarray] = []
            neutrino_segments: list[np.ndarray] = []
            baryon_segments: list[np.ndarray] = []
            cdm_segments: list[np.ndarray] = []
            source_segments: list[np.ndarray] = []
            residual_segments: list[np.ndarray] = []
            residual_harmonic_segments: list[np.ndarray] = []
            residual_source_segments: list[np.ndarray] = []
        else:
            if self.startup_gate is None or self.seed_projection is None:
                _ = self.initial_state()
            y_current = np.asarray(restart_state.state_vector, dtype=np.float64)
            current_index = int(restart_state.step_index)
            if current_index >= eta_out.size:
                raise ValueError("restart_state.step_index exceeds eta grid")
            if not np.isclose(float(eta_out[current_index]), float(restart_state.eta_restart)):
                raise ValueError("restart_state eta does not match the runtime eta grid")
            eta_segments = [np.asarray(restart_state.eta_prefix, dtype=np.float64)]
            photon_T_segments = [np.asarray(restart_state.photon_T_prefix, dtype=np.float64)]
            photon_E_segments = [np.asarray(restart_state.photon_E_prefix, dtype=np.float64)]
            photon_B_segments = [np.asarray(restart_state.photon_B_prefix, dtype=np.float64)]
            neutrino_segments = [np.asarray(restart_state.neutrino_tower_prefix, dtype=np.float64)]
            baryon_segments = [np.asarray(restart_state.baryon_local_prefix, dtype=np.float64)]
            cdm_segments = [np.asarray(restart_state.cdm_local_prefix, dtype=np.float64)]
            source_segments = [np.asarray(restart_state.source_local_prefix, dtype=np.float64)]
            residual_segments = [np.asarray(restart_state.residual_local_prefix, dtype=np.float64)]
            residual_harmonic_segments = [
                np.asarray(restart_state.residual_harmonic_prefix, dtype=np.float64)
            ]
            residual_source_segments = [
                np.asarray(restart_state.residual_source_prefix, dtype=np.float64)
            ]

        nfev = 0
        njev = 0
        nlu = 0
        status = 0
        message = "The solver successfully reached the end of the integration interval."
        checkpoint_write_count = 0

        if checkpoint_every_n_steps is None or checkpoint_every_n_steps <= 0:
            if current_index < eta_out.size - 1:
                sol = self._solve_segment(
                    eta_start=float(eta_out[current_index]),
                    eta_stop=float(eta_out[-1]),
                    y0=y_current,
                    eta_eval=eta_out[current_index:],
                    tca_tracker=tca_tracker,
                )
                nfev += int(sol.nfev)
                njev += int(sol.njev)
                nlu += int(sol.nlu)
                status = int(sol.status)
                message = str(sol.message)
                start_offset = 0 if len(eta_segments) == 0 else 1
                eta_segments.append(np.asarray(sol.t, dtype=np.float64)[start_offset:])
                photon_T_segments.append(np.asarray(sol.y[:tower_size].T, dtype=np.float64)[start_offset:])
                photon_E_segments.append(
                    np.asarray(sol.y[tower_size : 2 * tower_size].T, dtype=np.float64)[start_offset:]
                )
                neutrino_segments.append(
                    np.asarray(sol.y[3 * tower_size : 4 * tower_size].T, dtype=np.float64)[start_offset:]
                )
                photon_B_segments.append(
                    np.asarray(sol.y[2 * tower_size : 3 * tower_size].T, dtype=np.float64)[start_offset:]
                )
                baryon_segments.append(
                    np.asarray(
                        sol.y[4 * tower_size : 4 * tower_size + _BARYON_LOCAL_DOF].T,
                        dtype=np.float64,
                    )[start_offset:]
                )
                cdm_segments.append(
                    np.asarray(
                        sol.y[
                            4 * tower_size + _BARYON_LOCAL_DOF : 4 * tower_size + _LOCAL_MATTER_DOF
                        ].T,
                        dtype=np.float64,
                    )[start_offset:]
                )
                source_segments.append(
                    np.asarray(
                        sol.y[
                            4 * tower_size + _LOCAL_MATTER_DOF : 4 * tower_size + _PRIMARY_LOCAL_DOF
                        ].T,
                        dtype=np.float64,
                    )[start_offset:]
                )
                residual_segments.append(
                    np.asarray(
                        sol.y[
                            4 * tower_size
                            + _PRIMARY_LOCAL_DOF : 4 * tower_size
                            + _PRIMARY_LOCAL_DOF
                            + self._residual_local_dof
                        ].T,
                        dtype=np.float64,
                    )[start_offset:]
                )
                residual_harmonic_segments.append(
                    np.asarray(
                        sol.y[
                            4 * tower_size
                            + _PRIMARY_LOCAL_DOF
                            + self._residual_local_dof : 4 * tower_size
                            + _PRIMARY_LOCAL_DOF
                            + self._residual_local_dof
                            + self._residual_harmonic_dof
                        ].T,
                        dtype=np.float64,
                    )[start_offset:]
                )
                residual_source_segments.append(
                    np.asarray(
                        sol.y[
                            4 * tower_size
                            + _PRIMARY_LOCAL_DOF
                            + self._residual_local_dof
                            + self._residual_harmonic_dof :
                        ].T,
                        dtype=np.float64,
                    )[start_offset:]
                )
        else:
            while current_index < eta_out.size - 1:
                next_index = min(current_index + int(checkpoint_every_n_steps), eta_out.size - 1)
                sol = self._solve_segment(
                    eta_start=float(eta_out[current_index]),
                    eta_stop=float(eta_out[next_index]),
                    y0=y_current,
                    eta_eval=eta_out[current_index : next_index + 1],
                    tca_tracker=tca_tracker,
                )
                nfev += int(sol.nfev)
                njev += int(sol.njev)
                nlu += int(sol.nlu)
                status = int(sol.status)
                message = str(sol.message)
                start_offset = 0 if len(eta_segments) == 0 else 1
                eta_chunk = np.asarray(sol.t, dtype=np.float64)[start_offset:]
                photon_T_chunk = np.asarray(sol.y[:tower_size].T, dtype=np.float64)[start_offset:]
                photon_E_chunk = np.asarray(sol.y[tower_size : 2 * tower_size].T, dtype=np.float64)[start_offset:]
                photon_B_chunk = np.asarray(sol.y[2 * tower_size : 3 * tower_size].T, dtype=np.float64)[start_offset:]
                neutrino_chunk = np.asarray(sol.y[3 * tower_size : 4 * tower_size].T, dtype=np.float64)[start_offset:]
                baryon_chunk = np.asarray(
                    sol.y[4 * tower_size : 4 * tower_size + _BARYON_LOCAL_DOF].T,
                    dtype=np.float64,
                )[start_offset:]
                cdm_chunk = np.asarray(
                    sol.y[4 * tower_size + _BARYON_LOCAL_DOF : 4 * tower_size + _LOCAL_MATTER_DOF].T,
                    dtype=np.float64,
                )[start_offset:]
                source_chunk = np.asarray(
                    sol.y[4 * tower_size + _LOCAL_MATTER_DOF : 4 * tower_size + _PRIMARY_LOCAL_DOF].T,
                    dtype=np.float64,
                )[start_offset:]
                residual_chunk = np.asarray(
                    sol.y[
                        4 * tower_size
                        + _PRIMARY_LOCAL_DOF : 4 * tower_size
                        + _PRIMARY_LOCAL_DOF
                        + self._residual_local_dof
                    ].T,
                    dtype=np.float64,
                )[start_offset:]
                residual_harmonic_chunk = np.asarray(
                    sol.y[
                        4 * tower_size
                        + _PRIMARY_LOCAL_DOF
                        + self._residual_local_dof : 4 * tower_size
                        + _PRIMARY_LOCAL_DOF
                        + self._residual_local_dof
                        + self._residual_harmonic_dof
                    ].T,
                    dtype=np.float64,
                )[start_offset:]
                residual_source_chunk = np.asarray(
                    sol.y[
                        4 * tower_size
                        + _PRIMARY_LOCAL_DOF
                        + self._residual_local_dof
                        + self._residual_harmonic_dof :
                    ].T,
                    dtype=np.float64,
                )[start_offset:]
                eta_segments.append(eta_chunk)
                photon_T_segments.append(photon_T_chunk)
                photon_E_segments.append(photon_E_chunk)
                photon_B_segments.append(photon_B_chunk)
                neutrino_segments.append(neutrino_chunk)
                baryon_segments.append(baryon_chunk)
                cdm_segments.append(cdm_chunk)
                source_segments.append(source_chunk)
                residual_segments.append(residual_chunk)
                residual_harmonic_segments.append(residual_harmonic_chunk)
                residual_source_segments.append(residual_source_chunk)
                y_current = np.asarray(sol.y[:, -1], dtype=np.float64)
                current_index = next_index
                if checkpoint_callback is not None and current_index < eta_out.size - 1:
                    checkpoint_write_count += 1
                    checkpoint_callback(
                        NativeTierBRestartState(
                            step_index=current_index,
                            eta_restart=float(eta_out[current_index]),
                            state_vector=y_current.copy(),
                            eta_prefix=np.concatenate(eta_segments, axis=0),
                            photon_T_prefix=np.vstack(photon_T_segments),
                            photon_E_prefix=np.vstack(photon_E_segments),
                            photon_B_prefix=np.vstack(photon_B_segments),
                            neutrino_tower_prefix=np.vstack(neutrino_segments),
                            baryon_local_prefix=np.vstack(baryon_segments),
                            cdm_local_prefix=np.vstack(cdm_segments),
                            source_local_prefix=np.vstack(source_segments),
                            residual_local_prefix=np.vstack(residual_segments),
                            residual_harmonic_prefix=np.vstack(residual_harmonic_segments),
                            residual_source_prefix=np.vstack(residual_source_segments),
                        )
                    )

        result = self._build_result(
            eta=np.concatenate(eta_segments, axis=0),
            photon_T_tower=np.vstack(photon_T_segments),
            photon_E_tower=np.vstack(photon_E_segments),
            photon_B_tower=np.vstack(photon_B_segments),
            neutrino_tower=np.vstack(neutrino_segments),
            baryon_local_history=np.vstack(baryon_segments),
            cdm_local_history=np.vstack(cdm_segments),
            source_local_history=np.vstack(source_segments),
            residual_local_history=np.vstack(residual_segments) if residual_segments else np.zeros((len(np.concatenate(eta_segments, axis=0)), 0), dtype=np.float64),
            residual_harmonic_history=np.vstack(residual_harmonic_segments) if residual_harmonic_segments else np.zeros((len(np.concatenate(eta_segments, axis=0)), 0), dtype=np.float64),
            residual_source_history=np.vstack(residual_source_segments) if residual_source_segments else np.zeros((len(np.concatenate(eta_segments, axis=0)), 0), dtype=np.float64),
            nfev=nfev,
            njev=njev,
            nlu=nlu,
            status=status,
            message=message,
            tca_tracker=tca_tracker,
            checkpoint_write_count=checkpoint_write_count,
            restart_used=(restart_state is not None),
        )
        result.layout_auxiliary_bundle = self.build_layout_auxiliary_history_bundle(result)
        result.solver_info["layout_auxiliary_bundle_cached"] = True
        reionization_amplitude = (
            0.0
            if self.visibility_source.contract.events is None
            else float(self.visibility_source.contract.events.tau_reion)
        )
        result.runtime_execution_trace = self.build_runtime_execution_trace(
            result,
            reionization_amplitude=reionization_amplitude,
        )
        result.solver_info["runtime_execution_trace_cached"] = True
        return result
