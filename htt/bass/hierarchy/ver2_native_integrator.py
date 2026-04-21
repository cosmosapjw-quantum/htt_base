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
from typing import Optional

import numpy as np
from scipy.integrate import solve_ivp

from bass.background.evolution import BackgroundEvolutionResult
from bass.collision.electron_frame import (
    ElectronFrameThomsonContext,
    ProjectedThomsonSource,
    project_thomson_source,
)
from bass.collision.polarization import PolarizationHierarchyState, zero_polarization_hierarchy
from bass.closure.quadrupole_tca import solve_tca_closure
from bass.hierarchy.collision_interface import CollisionOperator, ZeroCollisionOperator
from bass.hierarchy.closure import TCAClosure, build_default_closure
from bass.hierarchy.hierarchy_rhs import hierarchy_rhs_photon
from bass.hierarchy.integrator import (
    C_KMS,
    IntegratorConfig,
    IntegrationResult,
    _ell2_m0_slot_offset,
)
from bass.hierarchy.neutrino_reduced import neutrino_reduced_rhs
from bass.hierarchy.pstf_tensor import PSTFHierarchyState, PSTFTensor, pack_hierarchy, unpack_hierarchy, zero_hierarchy
from bass.runtime.canonical_decision import CanonicalDecision
from bass.species.base import SpeciesLabel
from bass.species.registry import SpeciesBackgroundRegistry
from bass.species.tilted import TiltedSpeciesBackground, rapidity_to_velocity

__all__ = [
    "Ver2TierBIntegrator",
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
        self.aniso_3_curvature = np.repeat(ricci[None, :, :], eta.size, axis=0)


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
    projected_source: ProjectedThomsonSource | None = None

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


def _pack_radiation_state(
    *,
    photon_T: PSTFHierarchyState,
    photon_E: PolarizationHierarchyState,
    neutrino_reduced: np.ndarray,
) -> np.ndarray:
    nu = np.asarray(neutrino_reduced, dtype=np.float64)
    return np.concatenate(
        [
            pack_hierarchy(photon_T),
            pack_hierarchy(photon_E.E),
            nu,
        ]
    )


def _unpack_radiation_state(y: np.ndarray, L_max: int) -> tuple[PSTFHierarchyState, PolarizationHierarchyState, np.ndarray]:
    arr = np.asarray(y, dtype=np.float64)
    tower_size = (L_max + 1) ** 2
    if arr.shape != (2 * tower_size + 4,):
        raise ValueError(f"radiation state shape {arr.shape} does not match L_max={L_max}")
    photon_T = unpack_hierarchy(arr[:tower_size], L_max)
    photon_E = PolarizationHierarchyState(E=unpack_hierarchy(arr[tower_size : 2 * tower_size], L_max))
    neutrino_reduced = np.asarray(arr[2 * tower_size :], dtype=np.float64)
    return photon_T, photon_E, neutrino_reduced


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
        self._tilted_electron = _tilted_electron(species=species, config=config)
        self._direction = np.asarray(config.tilt_direction, dtype=np.float64)
        if not np.any(self._direction):
            self._direction = np.array([1.0, 0.0, 0.0], dtype=np.float64)
        self._direction = self._direction / max(float(np.linalg.norm(self._direction)), 1.0e-30)

    def initial_state(self) -> np.ndarray:
        photon_T = zero_hierarchy(self.config.L_max)
        photon_E = zero_polarization_hierarchy(self.config.L_max)
        neutrino_reduced = np.zeros(4, dtype=np.float64)
        return _pack_radiation_state(
            photon_T=photon_T,
            photon_E=photon_E,
            neutrino_reduced=neutrino_reduced,
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
        photon_T, photon_E, neutrino_reduced = _unpack_radiation_state(y, self.config.L_max)
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
            tilted_electron=self._tilted_electron,
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
        rhs_nu = neutrino_reduced_rhs(
            eta,
            neutrino_reduced,
            bg_table=self.bg_table,
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

    def run(self) -> IntegrationResult:
        y0 = self.initial_state()
        eta_out = np.linspace(
            self.config.eta_initial_mpc,
            self.config.eta_final_mpc,
            self.config.n_output,
        )
        max_step = (
            self.config.eta_final_mpc - self.config.eta_initial_mpc
        ) / 1000.0
        tca_tracker: list[bool] = []
        sol = solve_ivp(
            lambda eta, y: self._rhs(eta, y, tca_tracker=tca_tracker),
            (self.config.eta_initial_mpc, self.config.eta_final_mpc),
            y0,
            t_eval=eta_out,
            method=self.config.solver_method,
            rtol=self.config.rtol,
            atol=self.config.atol,
            max_step=max_step,
        )
        if not sol.success:
            raise RuntimeError(f"solve_ivp failed: {sol.message} at η={sol.t[-1]}")
        if np.any(~np.isfinite(sol.y)):
            raise RuntimeError("solve_ivp produced non-finite entries in VER2 native Tier-B core")

        tower_size = (self.config.L_max + 1) ** 2
        photon_T_tower = np.asarray(sol.y[:tower_size].T, dtype=np.float64)
        photon_E_tower = np.asarray(sol.y[tower_size : 2 * tower_size].T, dtype=np.float64)
        neutrino_reduced = np.asarray(sol.y[2 * tower_size :].T, dtype=np.float64)
        a_arr, sigma_plus, sigma_minus = self._background_projection(np.asarray(sol.t, dtype=np.float64))
        tca_mask = self._compute_tca_mask(np.asarray(sol.t, dtype=np.float64))

        from bass.hierarchy.event_detection import detect_critical_events

        events = detect_critical_events(self.species, self.species.bg_table)
        solver_info = {
            "nfev": int(sol.nfev),
            "njev": int(sol.njev),
            "nlu": int(sol.nlu),
            "status": int(sol.status),
            "message": str(sol.message),
            "tca_tracker_len": len(tca_tracker),
            "tca_tracker_any_active": any(tca_tracker),
            "tier_b_core_owner": "ver2_s1s2_native",
            "background_owner": "background.evolution",
        }
        return IntegrationResult(
            eta=np.asarray(sol.t, dtype=np.float64),
            a=a_arr,
            Sigma_plus=sigma_plus,
            Sigma_minus=sigma_minus,
            photon_T_tower=photon_T_tower,
            photon_E_tower=photon_E_tower,
            neutrino_reduced=neutrino_reduced,
            critical_events=events,
            config=self.config,
            solver_info=solver_info,
            tca_active_mask=tca_mask,
        )
