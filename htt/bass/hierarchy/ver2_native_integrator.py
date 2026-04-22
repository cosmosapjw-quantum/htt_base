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
from collections.abc import Callable
from typing import Optional

import numpy as np
from scipy.integrate import solve_ivp

from bass.background.evolution import BackgroundEvolutionResult
from bass.collision.electron_frame import (
    ExactThomsonSource,
    ElectronFrameThomsonContext,
    ProjectedThomsonSource,
    exact_thomson_source,
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
from bass.hierarchy.hierarchy_rhs import hierarchy_rhs_neutrino, hierarchy_rhs_photon
from bass.hierarchy.integrator import (
    C_KMS,
    IntegratorConfig,
    IntegrationResult,
    _ell2_m0_slot_offset,
)
from bass.hierarchy.pstf_tensor import PSTFHierarchyState, PSTFTensor, pack_hierarchy, unpack_hierarchy, zero_hierarchy
from bass.hierarchy.seed_compatibility import (
    PackedRegularSeedInjection,
    SeedConstraintProjection,
    project_packed_regular_seed,
)
from bass.hierarchy.boost_kernel import is_axis_aligned
from bass.perturbation.regular_adiabatic_ic import (
    make_camb_regular_adiabatic_seed,
    unpack_camb_regular_adiabatic_seed,
)
from bass.perturbation.tilted_seed_rule import apply_tilted_boost_seed_rule
from bass.runtime.canonical_decision import CanonicalDecision
from bass.species.base import SpeciesLabel
from bass.species.registry import SpeciesBackgroundRegistry
from bass.species.tilted import TiltedSpeciesBackground, rapidity_to_velocity

__all__ = [
    "Ver2TierBIntegrator",
    "NativeTierBRestartState",
]


_SIGMA_PLUS_BASIS = np.diag([-2.0, 1.0, 1.0]) / np.sqrt(6.0)
_SIGMA_MINUS_BASIS = np.diag([0.0, 1.0, -1.0]) / np.sqrt(2.0)


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

    def __init__(self, background_monitor: BackgroundEvolutionResult) -> None:
        self._eta = np.asarray(background_monitor.eta, dtype=np.float64)
        self._a = np.asarray(background_monitor.a, dtype=np.float64)
        self._H = np.asarray(background_monitor.H, dtype=np.float64)

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

    def __init__(self, background_monitor: BackgroundEvolutionResult) -> None:
        eta = np.asarray(background_monitor.eta, dtype=np.float64)
        a = np.asarray(background_monitor.a, dtype=np.float64)
        sigma = np.asarray(background_monitor.sigma_tensor, dtype=np.float64)
        ricci = np.asarray(background_monitor.initial_conditions.geometry.ricci_pstf, dtype=np.float64)
        self.eta = eta
        self.sigma_tensor = sigma * a[:, None, None]
        self.aniso_3_curvature = (
            None
            if not np.any(ricci)
            else np.repeat(ricci[None, :, :], eta.size, axis=0)
        )


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
    exact_source: ExactThomsonSource | None = None

    def get_source(self) -> ProjectedThomsonSource:
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
        return self.exact_source.projected

    def get_exact_source(self) -> ExactThomsonSource:
        if self.exact_source is None:
            _ = self.get_source()
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
        return aux.get_source().temperature.tensors[ell].copy()


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
        return aux.get_source().polarization_E.E.tensors[ell].copy()


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

    def __post_init__(self) -> None:
        if self.neutrino_tower.L != self.photon_T.L:
            raise ValueError(
                f"neutrino_tower L={self.neutrino_tower.L} must match photon_T L={self.photon_T.L}"
            )


@dataclass(frozen=True)
class NativeTierBRestartState:
    """Checkpoint-backed restart state for the native Tier-B integrator."""

    step_index: int
    eta_restart: float
    state_vector: np.ndarray
    eta_prefix: np.ndarray
    photon_T_prefix: np.ndarray
    photon_E_prefix: np.ndarray
    neutrino_tower_prefix: np.ndarray

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
            ("neutrino_tower_prefix", self.neutrino_tower_prefix),
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


def _pack_radiation_state(
    *,
    photon_T: PSTFHierarchyState,
    photon_E: PolarizationHierarchyState,
    neutrino_tower: PSTFHierarchyState,
) -> np.ndarray:
    return np.concatenate(
        [
            pack_hierarchy(photon_T),
            pack_hierarchy(photon_E.E),
            pack_hierarchy(neutrino_tower),
        ]
    )


def _unpack_radiation_state(
    y: np.ndarray, L_max: int
) -> tuple[PSTFHierarchyState, PolarizationHierarchyState, PSTFHierarchyState]:
    arr = np.asarray(y, dtype=np.float64)
    tower_size = (L_max + 1) ** 2
    if arr.shape != (3 * tower_size,):
        raise ValueError(f"radiation state shape {arr.shape} does not match L_max={L_max}")
    photon_T = unpack_hierarchy(arr[:tower_size], L_max)
    photon_E = PolarizationHierarchyState(E=unpack_hierarchy(arr[tower_size : 2 * tower_size], L_max))
    neutrino_tower = unpack_hierarchy(arr[2 * tower_size :], L_max)
    return photon_T, photon_E, neutrino_tower


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


class Ver2TierBIntegrator:
    """Executable Tier-B integrator owned by S1 background + S2 hierarchy."""

    def __init__(
        self,
        config: IntegratorConfig,
        species: SpeciesBackgroundRegistry,
        *,
        background_monitor: BackgroundEvolutionResult,
        visibility_source,
        canonical_decision: CanonicalDecision,
        seed_k_comoving: float = 1.0e-4,
    ) -> None:
        self.config = config
        self.species = species
        self.background_monitor = background_monitor
        self.visibility_source = visibility_source
        self.canonical_decision = canonical_decision
        self.bg_table = _BackgroundTableAdapter(background_monitor)
        self.tetrad_state = _TetradStateAdapter(background_monitor)
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
        self._direction = np.asarray(config.tilt_direction, dtype=np.float64)
        if not np.any(self._direction):
            self._direction = np.array([1.0, 0.0, 0.0], dtype=np.float64)
        self._direction = self._direction / max(float(np.linalg.norm(self._direction)), 1.0e-30)
        self.seed_k_comoving = float(seed_k_comoving)
        self.startup_gate: StartupGateDecision | None = None
        self.seed_projection: SeedConstraintProjection | None = None
        self.startup_state: QuadrupoleStartupState | None = None
        self.seed_injection_mode: str = "uninitialized"
        self.seed_velocity_scale: float = 1.0

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
        self.seed_injection_mode = seeded.seed_injection_mode
        self.seed_velocity_scale = seeded.velocity_scale
        return _pack_radiation_state(
            photon_T=seeded.photon_T,
            photon_E=seeded.photon_E,
            neutrino_tower=seeded.neutrino_tower,
        )

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

    def _build_seeded_initial_state(self) -> _SeededInitialState:
        seed_state = make_camb_regular_adiabatic_seed(
            k_comoving=max(self.seed_k_comoving, 0.0),
            eta_initial=float(self.config.eta_initial_mpc),
            a_initial=float(self.background_monitor.a[0]),
            L_max=self.config.L_max,
        )
        injection_mode = "orthogonal_regular_adiabatic_seed"
        if abs(float(self.config.tilt_rapidity)) > 0.0:
            seed_state = apply_tilted_boost_seed_rule(
                seed_state,
                beta=float(self.config.tilt_rapidity),
                v_hat_e=tuple(float(x) for x in self._direction),
            )
            injection_mode = (
                "axisymmetric_tilted_regular_adiabatic_seed"
                if is_axis_aligned(tuple(float(x) for x in self._direction))
                else "offaxis_tilted_regular_adiabatic_seed"
            )

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
        )

    def _resolve_startup_state(
        self,
        *,
        photon_T: PSTFHierarchyState,
        photon_E: PolarizationHierarchyState,
        gamma_t: float,
    ) -> QuadrupoleStartupState:
        eta0 = float(self.background_monitor.eta[0])
        rhs_T_free = hierarchy_rhs_photon(
            eta0,
            photon_T.as_flat(),
            L_max=self.config.L_max,
            bg_table=self.bg_table,
            tetrad_state=self.tetrad_state,
            closure=self.closure,
            collision=ZeroCollisionOperator(),
            collision_aux=None,
        )
        rhs_E_free = hierarchy_rhs_photon(
            eta0,
            photon_E.E.as_flat(),
            L_max=self.config.L_max,
            bg_table=self.bg_table,
            tetrad_state=self.tetrad_state,
            closure=self.closure,
            collision=ZeroCollisionOperator(),
            collision_aux=None,
        )
        slot = _ell2_m0_slot_offset(self.config.L_max)
        a_val = self._a_at(eta0)
        S_T = float(rhs_T_free[slot]) / a_val * (-1.0)
        S_E = float(rhs_E_free[slot]) / a_val * (-1.0)
        return quadrupole_startup_from_sources(
            S_T=S_T,
            S_E=S_E,
            gamma_T=float(gamma_t),
        )

    def _h_local_at(self, eta: float) -> float:
        return _interp_scalar(self.background_monitor.eta, self.background_monitor.H, eta)

    def _a_at(self, eta: float) -> float:
        return _interp_scalar(self.background_monitor.eta, self.background_monitor.a, eta)

    def _rhs(
        self,
        eta: float,
        y: np.ndarray,
        *,
        tca_tracker: list[bool] | None = None,
    ) -> np.ndarray:
        photon_T, photon_E, neutrino_tower = _unpack_radiation_state(y, self.config.L_max)
        gamma_t = _resolved_gamma_t(
            eta=float(eta),
            direction=self._direction,
            visibility_source=self.visibility_source,
            config=self.config,
        )
        aux = _ProjectedCollisionAux(
            eta=float(eta),
            temperature_state=photon_T,
            polarization_state=photon_E,
            Gamma_T=float(gamma_t),
            direction=self._direction,
            tilted_electron=self._tilted_electron_at(float(eta)),
            v_b_real_sph=np.zeros(3, dtype=np.float64),
            b_state=zero_hierarchy(self.config.L_max),
        )
        rhs_T = hierarchy_rhs_photon(
            eta,
            photon_T.as_flat(),
            L_max=self.config.L_max,
            bg_table=self.bg_table,
            tetrad_state=self.tetrad_state,
            closure=self.closure,
            collision=self._temperature_collision,
            collision_aux=aux,
        )
        rhs_E = hierarchy_rhs_photon(
            eta,
            photon_E.E.as_flat(),
            L_max=self.config.L_max,
            bg_table=self.bg_table,
            tetrad_state=self.tetrad_state,
            closure=self.closure,
            collision=self._e_collision,
            collision_aux=aux,
        )
        rhs_nu = hierarchy_rhs_neutrino(
            eta,
            neutrino_tower.as_flat(),
            L_max=self.config.L_max,
            bg_table=self.bg_table,
            tetrad_state=self.tetrad_state,
            closure=self.closure,
            neutrino_background=self.species[SpeciesLabel.NEUTRINO],
        )

        tca_active = False
        if isinstance(self.closure, TCAClosure) and gamma_t > 0.0:
            H_local = self._h_local_at(float(eta))
            if H_local > 0.0 and gamma_t / H_local > self.config.gamma_T_over_H_threshold:
                tca_active = True
                rhs_T_free = hierarchy_rhs_photon(
                    eta,
                    photon_T.as_flat(),
                    L_max=self.config.L_max,
                    bg_table=self.bg_table,
                    tetrad_state=self.tetrad_state,
                    closure=self.closure,
                    collision=ZeroCollisionOperator(),
                    collision_aux=None,
                )
                rhs_E_free = hierarchy_rhs_photon(
                    eta,
                    photon_E.E.as_flat(),
                    L_max=self.config.L_max,
                    bg_table=self.bg_table,
                    tetrad_state=self.tetrad_state,
                    closure=self.closure,
                    collision=ZeroCollisionOperator(),
                    collision_aux=None,
                )
                slot = _ell2_m0_slot_offset(self.config.L_max)
                a_val = self._a_at(float(eta))
                S_T = float(rhs_T_free[slot]) / a_val * (-1.0)
                S_E = float(rhs_E_free[slot]) / a_val * (-1.0)
                theta_2_alg, e_2_alg = self._solve_tca_scalars(
                    S_T=S_T,
                    S_E=S_E,
                    gamma_t=float(gamma_t),
                    H_local=float(H_local),
                )
                current_pi2 = float(photon_T.tensors[2].components[2])
                current_e2 = float(photon_E.E.tensors[2].components[2])
                relax_rate = a_val * float(gamma_t)
                rhs_T[slot] = -relax_rate * (current_pi2 - theta_2_alg)
                rhs_E[slot] = -relax_rate * (current_e2 - e_2_alg)

        if tca_tracker is not None:
            tca_tracker.append(bool(tca_active))

        return np.concatenate([rhs_T, rhs_E, rhs_nu])

    def _explicit_rhs(self, eta: float, y: np.ndarray) -> np.ndarray:
        photon_T, photon_E, neutrino_tower = _unpack_radiation_state(y, self.config.L_max)
        rhs_T = hierarchy_rhs_photon(
            eta,
            photon_T.as_flat(),
            L_max=self.config.L_max,
            bg_table=self.bg_table,
            tetrad_state=self.tetrad_state,
            closure=self.closure,
            collision=ZeroCollisionOperator(),
            collision_aux=None,
        )
        rhs_E = hierarchy_rhs_photon(
            eta,
            photon_E.E.as_flat(),
            L_max=self.config.L_max,
            bg_table=self.bg_table,
            tetrad_state=self.tetrad_state,
            closure=self.closure,
            collision=ZeroCollisionOperator(),
            collision_aux=None,
        )
        rhs_nu = hierarchy_rhs_neutrino(
            eta,
            neutrino_tower.as_flat(),
            L_max=self.config.L_max,
            bg_table=self.bg_table,
            tetrad_state=self.tetrad_state,
            closure=self.closure,
            neutrino_background=self.species[SpeciesLabel.NEUTRINO],
        )
        return np.concatenate([rhs_T, rhs_E, rhs_nu])

    def _implicit_rhs(
        self,
        eta: float,
        y: np.ndarray,
        *,
        tca_tracker: list[bool] | None = None,
    ) -> np.ndarray:
        full = self._rhs(eta, y, tca_tracker=tca_tracker)
        explicit = self._explicit_rhs(eta, y)
        implicit = np.asarray(full - explicit, dtype=np.float64)
        tower_size = (self.config.L_max + 1) ** 2
        implicit[2 * tower_size :] = 0.0
        return implicit

    def _orthogonal_implicit_step(
        self,
        *,
        eta: float,
        stage: np.ndarray,
        dt: float,
        tca_tracker: list[bool],
    ) -> np.ndarray:
        photon_T, photon_E, neutrino_tower = _unpack_radiation_state(stage, self.config.L_max)
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

        if self.config.L_max >= 1:
            out_T.tensors[1].components = photon_T.tensors[1].components / (1.0 + gamma_dt)

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

            if tca_active:
                rhs_T_free = hierarchy_rhs_photon(
                    eta,
                    photon_T.as_flat(),
                    L_max=self.config.L_max,
                    bg_table=self.bg_table,
                    tetrad_state=self.tetrad_state,
                    closure=self.closure,
                    collision=ZeroCollisionOperator(),
                    collision_aux=None,
                )
                rhs_E_free = hierarchy_rhs_photon(
                    eta,
                    photon_E.E.as_flat(),
                    L_max=self.config.L_max,
                    bg_table=self.bg_table,
                    tetrad_state=self.tetrad_state,
                    closure=self.closure,
                    collision=ZeroCollisionOperator(),
                    collision_aux=None,
                )
                a_val = self._a_at(float(eta))
                slot = _ell2_m0_slot_offset(self.config.L_max)
                S_T = float(rhs_T_free[slot]) / a_val * (-1.0)
                S_E = float(rhs_E_free[slot]) / a_val * (-1.0)
                theta_2_alg, e_2_alg = self._solve_tca_scalars(
                    S_T=S_T,
                    S_E=S_E,
                    gamma_t=float(gamma_t),
                    H_local=float(H_local),
                )
                relax_rate = a_val * float(gamma_t)
                relax_dt = float(dt) * float(relax_rate)
                out_T.tensors[2].components[2] = (
                    photon_T.tensors[2].components[2] + relax_dt * theta_2_alg
                ) / (1.0 + relax_dt)
                out_E.tensors[2].components[2] = (
                    photon_E.E.tensors[2].components[2] + relax_dt * e_2_alg
                ) / (1.0 + relax_dt)
                ell2_has_tca_override = True

        for ell in range(3, self.config.L_max + 1):
            out_T.tensors[ell].components = photon_T.tensors[ell].components / (1.0 + gamma_dt)
            out_E.tensors[ell].components = photon_E.E.tensors[ell].components / (1.0 + gamma_dt)

        if self.config.L_max >= 2 and ell2_has_tca_override:
            # TCA ownership replaces only the m=0 quadrupole entry; keep the
            # non-m0 entries on the exact orthogonal Thomson solve above.
            pass

        return _pack_radiation_state(
            photon_T=out_T,
            photon_E=PolarizationHierarchyState(E=out_E),
            neutrino_tower=neutrino_tower,
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
            raise RuntimeError(f"solve_ivp failed: {sol.message} at η={sol.t[-1]}")
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

        for left, right in zip(eta_nodes[:-1], eta_nodes[1:]):
            eta_current = float(left)
            eta_target = float(right)
            while eta_current < eta_target - 1.0e-15:
                remaining = eta_target - eta_current
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
                    accepted = True
                    break
                if not accepted:
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
        neutrino_tower: np.ndarray,
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
            "startup_manifold_applied": bool(self.startup_state is not None),
            "startup_gate_selected": bool(self.startup_gate.startup_selected if self.startup_gate is not None else False),
            "neutrino_hierarchy_mode": "full_pstf_with_reduced_summary_export",
            "checkpoint_write_count": int(checkpoint_write_count),
            "restart_used": bool(restart_used),
            "collision_owner": "exact_thomson_wrapper",
        }
        return IntegrationResult(
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
            neutrino_tower=np.asarray(neutrino_tower, dtype=np.float64),
        )

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
            neutrino_segments: list[np.ndarray] = []
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
            neutrino_segments = [np.asarray(restart_state.neutrino_tower_prefix, dtype=np.float64)]

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
                    np.asarray(sol.y[2 * tower_size :].T, dtype=np.float64)[start_offset:]
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
                neutrino_chunk = np.asarray(sol.y[2 * tower_size :].T, dtype=np.float64)[start_offset:]
                eta_segments.append(eta_chunk)
                photon_T_segments.append(photon_T_chunk)
                photon_E_segments.append(photon_E_chunk)
                neutrino_segments.append(neutrino_chunk)
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
                            neutrino_tower_prefix=np.vstack(neutrino_segments),
                        )
                    )

        return self._build_result(
            eta=np.concatenate(eta_segments, axis=0),
            photon_T_tower=np.vstack(photon_T_segments),
            photon_E_tower=np.vstack(photon_E_segments),
            neutrino_tower=np.vstack(neutrino_segments),
            nfev=nfev,
            njev=njev,
            nlu=nlu,
            status=status,
            message=message,
            tca_tracker=tca_tracker,
            checkpoint_write_count=checkpoint_write_count,
            restart_used=(restart_state is not None),
        )
