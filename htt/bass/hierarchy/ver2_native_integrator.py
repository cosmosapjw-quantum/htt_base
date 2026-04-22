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
from bass.hierarchy.ver3_layout_protocol import build_hierarchy_layout, flatten
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
    baryon_euler_rhs,
)
from bass.perturbation.cdm_fluid import (
    CDMFluidState,
    CDMParameters,
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
    coupled_sector_history: _CoupledAuxiliarySectorHistory
    metadata: dict[str, object]

    def __post_init__(self) -> None:
        object.__setattr__(self, "eta", np.asarray(self.eta, dtype=np.float64))
        object.__setattr__(self, "source_history", np.asarray(self.source_history, dtype=np.float64))
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
    y: np.ndarray, L_max: int
) -> tuple[PSTFHierarchyState, PolarizationHierarchyState, PSTFHierarchyState]:
    arr = np.asarray(y, dtype=np.float64)
    tower_size = (L_max + 1) ** 2
    if arr.shape != (3 * tower_size,):
        raise ValueError(f"radiation state shape {arr.shape} does not match L_max={L_max}")
    photon_T = _unpack_hierarchy_view(arr[:tower_size], L_max)
    photon_E = PolarizationHierarchyState(E=_unpack_hierarchy_view(arr[tower_size : 2 * tower_size], L_max))
    neutrino_tower = _unpack_hierarchy_view(arr[2 * tower_size :], L_max)
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
        neutrino_tower: PSTFHierarchyState,
        background,
        collision_aux: _ProjectedCollisionAux | None,
    ) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
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
        rhs_nu = hierarchy_rhs_neutrino_from_state(
            neutrino_tower,
            background=background,
            closure=self.closure,
            neutrino_background=self._neutrino_background,
        )
        return rhs_T, rhs_E, rhs_nu

    def _rhs(
        self,
        eta: float,
        y: np.ndarray,
        *,
        tca_tracker: list[bool] | None = None,
    ) -> np.ndarray:
        photon_T, photon_E, neutrino_tower = _unpack_radiation_state(y, self.config.L_max)
        background = self._background_snapshot(float(eta))
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
            v_b_real_sph=self._zero_v_b_real_sph,
            b_state=self._zero_b_state,
        )
        rhs_T, rhs_E, rhs_nu = self._radiation_rhs_components(
            photon_T=photon_T,
            photon_E=photon_E,
            neutrino_tower=neutrino_tower,
            background=background,
            collision_aux=aux,
        )

        tca_active = False
        if isinstance(self.closure, TCAClosure) and gamma_t > 0.0:
            H_local = self._h_local_at(float(eta))
            if H_local > 0.0 and gamma_t / H_local > self.config.gamma_T_over_H_threshold:
                tca_active = True
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
                current_pi2 = float(photon_T.tensors[2].components[2])
                current_e2 = float(photon_E.E.tensors[2].components[2])
                relax_rate = background.a_val * float(gamma_t)
                rhs_T[slot] = -relax_rate * (current_pi2 - theta_2_alg)
                rhs_E[slot] = -relax_rate * (current_e2 - e_2_alg)

        if tca_tracker is not None:
            tca_tracker.append(bool(tca_active))

        return np.concatenate([rhs_T, rhs_E, rhs_nu])

    def _explicit_rhs(self, eta: float, y: np.ndarray) -> np.ndarray:
        photon_T, photon_E, neutrino_tower = _unpack_radiation_state(y, self.config.L_max)
        background = self._background_snapshot(float(eta))
        rhs_T, rhs_E, rhs_nu = self._radiation_rhs_components(
            photon_T=photon_T,
            photon_E=photon_E,
            neutrino_tower=neutrino_tower,
            background=background,
            collision_aux=None,
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
        coll_T_diag = self._coll_T_diag
        coll_E_diag = self._coll_E_diag

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
            out_T.tensors[ell].components = photon_T.tensors[ell].components / (1.0 + T_dt)
            out_E.tensors[ell].components = photon_E.E.tensors[ell].components / (1.0 + E_dt)

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
            eta_mid = 0.5 * (eta_left + eta_right)
            H_mid = max(self._h_local_at(eta_mid), 0.0)
            rho_b = max(float(baryon.rho_rest(eta_mid)), 1.0e-30)
            rho_gamma = max(float(photon.rho_rest(eta_mid)), 1.0e-30)
            gamma_mid = max(
                _resolved_gamma_t(
                    eta=eta_mid,
                    direction=self._direction,
                    visibility_source=self.visibility_source,
                    config=self.config,
                ),
                0.0,
            )
            theta_mid = 0.5 * (
                self._theta_1_photon_m0(photon_arr[idx])
                + self._theta_1_photon_m0(photon_arr[idx + 1])
            )
            baryon_params = BaryonParameters(
                R_b=max(3.0 * rho_b / (4.0 * rho_gamma), 1.0e-30),
                tau_dot=gamma_mid,
                H=H_mid,
            )
            cdm_params = CDMParameters(H=H_mid)
            baryon_state = BaryonFluidState(
                delta_b=float(baryon_state.delta_b - 3.0 * phi_dot_assumed * dt),
                v_b=float(
                    baryon_state.v_b
                    + dt
                    * baryon_euler_rhs(
                        baryon_state,
                        theta_mid,
                        baryon_params,
                        self.canonical_decision,
                    )
                ),
                axis=baryon_state.axis,
            )
            cdm_state = CDMFluidState(
                delta_c=float(cdm_state.delta_c - 3.0 * phi_dot_assumed * dt),
                v_c=float(
                    cdm_state.v_c
                    + dt
                    * cdm_euler_rhs(
                        cdm_state,
                        cdm_params,
                        self.canonical_decision,
                    )
                ),
                axis=cdm_state.axis,
            )
            _store(idx + 1, self._theta_1_photon_m0(photon_arr[idx + 1]))

        return _LocalMatterHistory(
            eta=eta_arr,
            baryon_history=baryon_history,
            cdm_history=cdm_history,
            baryon_labels=("delta_b", "v_b", "v_e", "drag_lock_residual"),
            cdm_labels=("delta_c", "v_c"),
            metadata={
                "owner": "runtime_postprocessed_homogeneous_local_matter",
                "phi_dot_source": "unavailable_assumed_zero_homogeneous_limit",
                "photon_dipole_source": "live_runtime_ph_I_ell1_m0",
                "gamma_t_source": "resolved_visibility_gamma_t",
                "history_sample_count": int(eta_arr.size),
            },
        )

    def build_layout_auxiliary_history_bundle(
        self,
        result: IntegrationResult,
        *,
        covered_mode_label: str | None = None,
    ) -> _LayoutAuxiliaryHistoryBundle:
        from bass.hierarchy.ver3_state_contracts import project_runtime_native_state

        neutrino_tower = result.neutrino_tower
        if neutrino_tower is None:
            raise ValueError("layout auxiliary history bundle requires result.neutrino_tower")
        layout = build_hierarchy_layout(self.backend, self.backend.truncation)
        covered = self._layout_covered_mode_label
        if covered is None:
            covered = layout.mode_labels[0] if covered_mode_label is None else str(covered_mode_label)
        reference_history = self._postprocess_local_matter_history(
            eta=np.asarray(result.eta, dtype=np.float64),
            photon_T_tower=np.asarray(result.photon_T_tower, dtype=np.float64),
        )
        eta_samples = np.asarray(result.eta, dtype=np.float64)
        photon_T_tower = np.asarray(result.photon_T_tower, dtype=np.float64)
        photon_E_tower = np.asarray(result.photon_E_tower, dtype=np.float64)
        neutrino_arr = np.asarray(neutrino_tower, dtype=np.float64)
        ell2_m0_slot = _ell2_m0_slot_offset(int(result.L_max)) if int(result.L_max) >= 2 else None
        reionization_amplitude = (
            0.0
            if self.visibility_source.contract.events is None
            else float(self.visibility_source.contract.events.tau_reion)
        )
        source_width = int(layout.sector_local_dofs["src"])
        source_rows = np.zeros((eta_samples.size, source_width), dtype=np.float64)
        size = (int(layout.ell_max) + 1) ** 2
        b_rows = np.zeros((eta_samples.size, size), dtype=np.float64)
        baryon_rows = np.zeros_like(np.asarray(reference_history.baryon_history, dtype=np.float64))
        cdm_rows = np.zeros_like(np.asarray(reference_history.cdm_history, dtype=np.float64))
        b_prev = np.zeros(size, dtype=np.float64)
        baryon_prev = np.asarray(reference_history.baryon_history[0], dtype=np.float64)
        cdm_prev = np.asarray(reference_history.cdm_history[0], dtype=np.float64)
        b_rows[0] = b_prev
        baryon_rows[0] = baryon_prev
        cdm_rows[0] = cdm_prev
        b_indices = np.array(
            [
                flatten(layout, covered, "ph_B", ell, m)
                for ell in range(layout.ell_max + 1)
                for m in range(-ell, ell + 1)
            ],
            dtype=np.int64,
        )
        baryon_indices = np.array(
            [
                flatten(layout, covered, "baryon", None, None, local_dof=i)
                for i in range(int(layout.sector_local_dofs["baryon"]))
            ],
            dtype=np.int64,
        )
        cdm_indices = np.array(
            [
                flatten(layout, covered, "cdm", None, None, local_dof=i)
                for i in range(int(layout.sector_local_dofs["cdm"]))
            ],
            dtype=np.int64,
        )

        for index, eta in enumerate(eta_samples):
            gamma_t = _resolved_gamma_t(
                visibility_source=self.visibility_source,
                eta=float(eta),
                direction=self._direction,
                config=self.config,
            )
            visibility_amplitude = abs(float(photon_T_tower[index, 0]))
            polarization_source = (
                0.0 if ell2_m0_slot is None else abs(float(photon_E_tower[index, ell2_m0_slot]))
            )
            sample_ops = self.backend.operator_factory(
                self._live_backend_state_payload(
                    eta=float(eta),
                    gamma_t_probe=float(gamma_t),
                    visibility_amplitude=visibility_amplitude,
                    polarization_source=polarization_source,
                    reionization_amplitude=reionization_amplitude,
                )
            )
            source_rows[index, :] = _extract_src_local_block(
                layout=layout,
                source_template=np.asarray(sample_ops.source_template, dtype=np.float64),
                covered_mode_label=covered,
            )
            sample_projection = project_runtime_native_state(
                layout=layout,
                layout_manifest=getattr(sample_ops, "layout_metadata", {}),
                photon_T=np.asarray(photon_T_tower[index], dtype=np.float64),
                photon_E=np.asarray(photon_E_tower[index], dtype=np.float64),
                photon_B=b_prev,
                neutrino_tower=np.asarray(neutrino_arr[index], dtype=np.float64),
                source_template=np.asarray(sample_ops.source_template, dtype=np.float64),
                baryon_block=baryon_prev,
                cdm_block=cdm_prev,
                matter_sector_status={
                    "baryon": "layout_operator_auxiliary_local_matter",
                    "cdm": "layout_operator_auxiliary_local_matter",
                },
                covered_mode_label=covered,
            )
            if index == eta_samples.size - 1:
                break
            dt = float(eta_samples[index + 1] - eta_samples[index])
            if dt <= 0.0:
                raise ValueError("eta grid must be strictly increasing for coupled auxiliary history sampling")
            vector = np.asarray(sample_projection.state_vector, dtype=np.float64)
            drive = (
                np.asarray(sample_ops.A_fs @ vector, dtype=np.float64)
                + np.asarray(sample_ops.A_mix @ vector, dtype=np.float64)
                + np.asarray(sample_ops.A_coll @ vector, dtype=np.float64)
                + np.asarray(sample_ops.source_template, dtype=np.float64)
            )
            mass_diag = np.asarray(sample_ops.mass_matrix.diagonal(), dtype=np.float64)
            b_next = b_prev.copy()
            baryon_next = baryon_prev.copy()
            cdm_next = cdm_prev.copy()
            for slot, idx in enumerate(b_indices):
                inv_mass = 1.0 / max(abs(float(mass_diag[idx])), 1.0e-30)
                b_next[slot] = float(b_prev[slot] + dt * inv_mass * float(drive[idx]))
            for slot, idx in enumerate(baryon_indices):
                inv_mass = 1.0 / max(abs(float(mass_diag[idx])), 1.0e-30)
                baryon_next[slot] = float(baryon_prev[slot] + dt * inv_mass * float(drive[idx]))
            for slot, idx in enumerate(cdm_indices):
                inv_mass = 1.0 / max(abs(float(mass_diag[idx])), 1.0e-30)
                cdm_next[slot] = float(cdm_prev[slot] + dt * inv_mass * float(drive[idx]))
            b_prev = b_next
            baryon_prev = baryon_next
            cdm_prev = cdm_next
            b_rows[index + 1] = b_prev
            baryon_rows[index + 1] = baryon_prev
            cdm_rows[index + 1] = cdm_prev

        reference_baryon = np.asarray(reference_history.baryon_history, dtype=np.float64)
        reference_cdm = np.asarray(reference_history.cdm_history, dtype=np.float64)
        baryon_delta = baryon_rows - reference_baryon
        cdm_delta = cdm_rows - reference_cdm
        max_abs = max(
            1.0,
            float(np.max(np.abs(baryon_delta))),
            float(np.max(np.abs(cdm_delta))),
        )
        scaled_delta_norm = max_abs * float(
            np.sqrt(
                np.sum(np.square(baryon_delta / max_abs), dtype=np.float64)
                + np.sum(np.square(cdm_delta / max_abs), dtype=np.float64)
            )
        )
        coupled_history = _CoupledAuxiliarySectorHistory(
            eta=eta_samples,
            photon_B_history=b_rows,
            baryon_history=baryon_rows,
            cdm_history=cdm_rows,
            baryon_labels=tuple(reference_history.baryon_labels),
            cdm_labels=tuple(reference_history.cdm_labels),
            metadata={
                "owner": "mode_ops.mass_inverse_coupled_auxiliary_sector_evolution",
                "reference_owner": str(reference_history.metadata.get("owner", "unknown")),
                "history_sample_count": int(eta_samples.size),
                "reference_sample_count": int(reference_baryon.shape[0]),
                "reference_delta_norm": float(scaled_delta_norm),
                "reference_baryon_history": reference_baryon,
                "reference_cdm_history": reference_cdm,
                "coupling_passes": 1,
                "coupled_sectors": ("ph_B", "baryon", "cdm"),
            },
        )
        return _LayoutAuxiliaryHistoryBundle(
            eta=eta_samples,
            source_history=source_rows,
            coupled_sector_history=coupled_history,
            metadata={
                "owner": "ver2_native_integrator.layout_auxiliary_history_bundle",
                "history_sample_count": int(eta_samples.size),
                "covered_mode_label": covered,
            },
        )

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
        visibility_amplitude: float,
        polarization_source: float,
        reionization_amplitude: float,
        covered_mode_label: str | None = None,
    ) -> _RuntimeLayoutProjectionBundle:
        from bass.los.family_backend_protocol import family_backend_gate_bundle
        from bass.runtime.gate_fragments import (
            ic_provenance_gate_bundle,
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
            "baryon": "layout_operator_auxiliary_local_matter",
            "cdm": "layout_operator_auxiliary_local_matter",
        }
        matter_block_metadata = {
            "owner": str(coupled.metadata["owner"]),
            "reference_owner": str(coupled.metadata["reference_owner"]),
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
        canonical_projection = project_runtime_native_state(
            layout=layout,
            layout_manifest=getattr(mode_ops, "layout_metadata", {}),
            photon_T=np.asarray(result.photon_T_tower[-1], dtype=np.float64),
            photon_E=np.asarray(result.photon_E_tower[-1], dtype=np.float64),
            photon_B=np.asarray(b_history[-1], dtype=np.float64),
            photon_B_history_eta=np.asarray(auxiliary_bundle.eta, dtype=np.float64),
            photon_B_history_samples=b_history,
            neutrino_tower=np.asarray(neutrino_tower[-1], dtype=np.float64),
            source_template=np.asarray(mode_ops.source_template, dtype=np.float64),
            baryon_block=np.asarray(coupled.baryon_history[-1], dtype=np.float64),
            cdm_block=np.asarray(coupled.cdm_history[-1], dtype=np.float64),
            matter_history_eta=np.asarray(coupled.eta, dtype=np.float64),
            baryon_history_samples=np.asarray(coupled.baryon_history, dtype=np.float64),
            cdm_history_samples=np.asarray(coupled.cdm_history, dtype=np.float64),
            matter_block_labels={
                "baryon": tuple(coupled.baryon_labels),
                "cdm": tuple(coupled.cdm_labels),
            },
            matter_sector_status=matter_sector_status,
            matter_block_metadata=matter_block_metadata,
            source_history_eta=np.asarray(auxiliary_bundle.eta, dtype=np.float64),
            source_history_samples=np.asarray(auxiliary_bundle.source_history, dtype=np.float64),
            covered_mode_label=covered,
        )
        source_block = np.asarray(
            canonical_projection.hierarchy_state.source_history_block["src"],
            dtype=np.float64,
        )
        b_mode_proxy = np.asarray(b_history[-1], dtype=np.float64)
        gate_provenance = {
            "layout_projection_owner": "ver2_native_integrator.build_runtime_layout_projection",
            "layout_auxiliary_bundle_owner": str(auxiliary_bundle.metadata["owner"]),
            "covered_mode_label": covered,
            "layout_source_block_owner": str(
                canonical_projection.hierarchy_state.metadata["sector_status"]["src"]
            ),
            "layout_local_matter_owner": str(coupled.metadata["owner"]),
            "layout_b_mode_proxy_source": "mode_ops.mass_inverse_coupled_auxiliary_sector_evolution",
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
                    "layout_source_history_sample_count": int(auxiliary_bundle.source_history.shape[0]),
                    "layout_local_matter_blocks_consumed": True,
                    "layout_local_matter_owner": str(coupled.metadata["owner"]),
                    "layout_local_matter_sample_count": int(coupled.metadata["history_sample_count"]),
                    "layout_local_matter_reference_owner": str(coupled.metadata["reference_owner"]),
                    "layout_local_matter_reference_sample_count": int(
                        coupled.metadata["reference_sample_count"]
                    ),
                    "layout_local_matter_reference_delta_norm": float(
                        coupled.metadata["reference_delta_norm"]
                    ),
                    "layout_b_mode_proxy_consumed": bool(np.any(np.abs(b_mode_proxy) > 0.0)),
                    "layout_b_mode_proxy_norm": float(np.linalg.norm(b_mode_proxy)),
                    "layout_b_mode_proxy_source": "mode_ops.mass_inverse_coupled_auxiliary_sector_evolution",
                    "layout_b_mode_history_sample_count": int(b_history.shape[0]),
                    "layout_auxiliary_coupling_passes": int(coupled.metadata["coupling_passes"]),
                    "layout_auxiliary_bundle_owner": str(auxiliary_bundle.metadata["owner"]),
                    "layout_projection_owner": "ver2_native_integrator.build_runtime_layout_projection",
                },
            },
        )

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
