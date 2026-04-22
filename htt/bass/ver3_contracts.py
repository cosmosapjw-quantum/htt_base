"""Concrete ver3 document-level contracts and time-gauge bridge helpers.

This module implements the remaining dataclass/API skeletons frozen in
``docs/ver3/02_NUMERICAL_ARCHITECTURE_AND_ALGORITHMS.md`` and
``docs/ver3/04_IMPLEMENTATION_SKELETON_AND_PORTABILITY.md`` so the design
contracts exist as importable code rather than prose-only templates.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Iterable, Mapping, Sequence

import numpy as np

from bass.background.bianchi_types import FamilySpec
from bass.background.constraints import BackgroundConstraintResiduals
from bass.background.geometry import TetradGeometry, pstf_rank2
from bass.validation import summarize_gate_status
from common.conventions import gamma_trace, pstf_gamma
from common.contracts import SolverCoreOutput

__all__ = [
    "BackgroundState",
    "GeometryDiagnostics",
    "ResidualPack",
    "OutputMetadata",
    "BackgroundInterpolator",
    "eta_from_t_grid",
    "background_interpolator",
    "sample_background_on_eta",
]


def _coerce_vector3(value: np.ndarray | Sequence[float], *, name: str) -> np.ndarray:
    array = np.asarray(value, dtype=np.float64)
    if array.shape != (3,):
        raise ValueError(f"{name} must have shape (3,), got {array.shape}")
    return array


def _coerce_matrix33(
    value: np.ndarray | Sequence[Sequence[float]],
    *,
    name: str,
    symmetric: bool = True,
) -> np.ndarray:
    array = np.asarray(value, dtype=np.float64)
    if array.shape != (3, 3):
        raise ValueError(f"{name} must have shape (3,3), got {array.shape}")
    if symmetric:
        if not np.all(np.isnan(array)) and not np.allclose(
            array,
            array.T,
            atol=1.0e-12,
            equal_nan=True,
        ):
            raise ValueError(f"{name} must be symmetric")
        array = 0.5 * (array + array.T)
    return array


def _interp_scalar(grid_x: np.ndarray, grid_y: np.ndarray, x: float) -> float:
    return float(np.interp(float(x), grid_x, grid_y))


def _interp_matrix33(grid_x: np.ndarray, matrices: np.ndarray, x: float, *, pstf: bool = False) -> np.ndarray:
    out = np.zeros((3, 3), dtype=np.float64)
    for i in range(3):
        for j in range(3):
            out[i, j] = _interp_scalar(grid_x, matrices[:, i, j], x)
    out = 0.5 * (out + out.T)
    return pstf_gamma(out) if pstf else out


def _same_mapping_keys(mappings: Sequence[Mapping[str, object]]) -> tuple[str, ...]:
    if not mappings:
        return ()
    key_set = tuple(mappings[0].keys())
    expected = set(key_set)
    for mapping in mappings[1:]:
        if set(mapping.keys()) != expected:
            raise ValueError("all interpolated mapping states must share the same keys")
    return key_set


def _interpolate_mapping_values(
    mappings: Sequence[Mapping[str, object]],
    x_grid: np.ndarray,
    x: float,
    *,
    name: str,
) -> dict[str, object]:
    if not mappings:
        return {}
    out: dict[str, object] = {}
    for key in _same_mapping_keys(mappings):
        values = [mapping[key] for mapping in mappings]
        first = values[0]
        try:
            numeric = np.asarray(first, dtype=np.float64)
            if numeric.ndim > 2:
                raise ValueError
            if not all(np.asarray(value, dtype=np.float64).shape == numeric.shape for value in values):
                raise ValueError
            stacked = np.stack([np.asarray(value, dtype=np.float64) for value in values], axis=0)
            if numeric.ndim == 0:
                out[key] = _interp_scalar(x_grid, stacked[:, 0] if stacked.ndim == 2 else stacked, x)
            else:
                value = np.zeros(numeric.shape, dtype=np.float64)
                for index in np.ndindex(numeric.shape):
                    value[index] = _interp_scalar(x_grid, stacked[(slice(None), *index)], x)
                out[key] = value
            continue
        except (TypeError, ValueError):
            if all(value == first for value in values[1:]):
                out[key] = first
                continue
            raise ValueError(
                f"{name}[{key!r}] is not a linearly interpolable numeric field and is not constant"
            ) from None
    return out


@dataclass(frozen=True)
class BackgroundState:
    """Document-level background state contract on the proper-time grid."""

    t: float
    alpha: float
    gamma_AB: np.ndarray
    theta: float
    sigma_AB: np.ndarray
    family_spec: FamilySpec
    species_hat: Mapping[str, object] = field(default_factory=dict)
    species_tilt: Mapping[str, object] = field(default_factory=dict)
    metadata: Mapping[str, object] = field(default_factory=dict)

    def __post_init__(self) -> None:
        gamma_ab = _coerce_matrix33(self.gamma_AB, name="BackgroundState.gamma_AB")
        sigma_ab = pstf_rank2(_coerce_matrix33(self.sigma_AB, name="BackgroundState.sigma_AB"))
        if not np.all(np.isfinite(gamma_ab)):
            raise ValueError("BackgroundState.gamma_AB must be finite")
        if not np.all(np.linalg.eigvalsh(gamma_ab) > 0.0):
            raise ValueError("BackgroundState.gamma_AB must be positive definite")
        if not np.isfinite(float(self.t)):
            raise ValueError("BackgroundState.t must be finite")
        if not np.isfinite(float(self.alpha)):
            raise ValueError("BackgroundState.alpha must be finite")
        if not np.isfinite(float(self.theta)):
            raise ValueError("BackgroundState.theta must be finite")
        object.__setattr__(self, "gamma_AB", gamma_ab)
        object.__setattr__(self, "sigma_AB", sigma_ab)
        object.__setattr__(self, "species_hat", dict(self.species_hat))
        object.__setattr__(self, "species_tilt", dict(self.species_tilt))
        object.__setattr__(self, "metadata", dict(self.metadata))

    @property
    def a_m(self) -> float:
        return float(np.exp(self.alpha))


@dataclass(frozen=True)
class GeometryDiagnostics:
    """Document-level geometry diagnostics bundle."""

    triad_iA: np.ndarray
    triad_Ai: np.ndarray
    C_ortho: np.ndarray
    Gamma_ortho: np.ndarray
    Ricci_routeA: np.ndarray
    Ricci_routeB_or_nan: np.ndarray
    Ricci_scalar: float
    S_AB: np.ndarray
    residuals: Mapping[str, object] = field(default_factory=dict)
    metadata: Mapping[str, object] = field(default_factory=dict)

    def __post_init__(self) -> None:
        triad_iA = _coerce_matrix33(self.triad_iA, name="GeometryDiagnostics.triad_iA", symmetric=False)
        triad_Ai = _coerce_matrix33(self.triad_Ai, name="GeometryDiagnostics.triad_Ai", symmetric=False)
        C_ortho = np.asarray(self.C_ortho, dtype=np.float64)
        Gamma_ortho = np.asarray(self.Gamma_ortho, dtype=np.float64)
        if C_ortho.shape != (3, 3, 3):
            raise ValueError(f"GeometryDiagnostics.C_ortho must have shape (3,3,3), got {C_ortho.shape}")
        if Gamma_ortho.shape != (3, 3, 3):
            raise ValueError(
                f"GeometryDiagnostics.Gamma_ortho must have shape (3,3,3), got {Gamma_ortho.shape}"
            )
        object.__setattr__(self, "triad_iA", triad_iA)
        object.__setattr__(self, "triad_Ai", triad_Ai)
        object.__setattr__(self, "C_ortho", C_ortho)
        object.__setattr__(self, "Gamma_ortho", Gamma_ortho)
        object.__setattr__(self, "Ricci_routeA", _coerce_matrix33(self.Ricci_routeA, name="GeometryDiagnostics.Ricci_routeA"))
        object.__setattr__(
            self,
            "Ricci_routeB_or_nan",
            _coerce_matrix33(self.Ricci_routeB_or_nan, name="GeometryDiagnostics.Ricci_routeB_or_nan"),
        )
        object.__setattr__(self, "S_AB", pstf_rank2(_coerce_matrix33(self.S_AB, name="GeometryDiagnostics.S_AB")))
        object.__setattr__(self, "residuals", dict(self.residuals))
        object.__setattr__(self, "metadata", dict(self.metadata))

    @classmethod
    def from_tetrad_geometry(
        cls,
        geometry: TetradGeometry,
        *,
        triad_iA: np.ndarray | None = None,
        triad_Ai: np.ndarray | None = None,
        metadata: Mapping[str, object] | None = None,
    ) -> "GeometryDiagnostics":
        route_b = (
            np.full((3, 3), np.nan, dtype=np.float64)
            if geometry.compact_ricci_tensor is None
            else np.asarray(geometry.compact_ricci_tensor, dtype=np.float64)
        )
        return cls(
            triad_iA=np.eye(3, dtype=np.float64) if triad_iA is None else triad_iA,
            triad_Ai=np.eye(3, dtype=np.float64) if triad_Ai is None else triad_Ai,
            C_ortho=geometry.algebra.C,
            Gamma_ortho=geometry.Gamma,
            Ricci_routeA=geometry.ricci_tensor,
            Ricci_routeB_or_nan=route_b,
            Ricci_scalar=float(geometry.ricci_scalar),
            S_AB=geometry.ricci_pstf,
            residuals={
                "dual_route_status": geometry.dual_route_status,
                "dual_route_curvature_residual_norm": float(geometry.dual_route_curvature_residual_norm),
                "torsion_residual_norm": float(geometry.torsion_residual_norm),
                "compact_formula_status": geometry.compact_formula_status,
            },
            metadata={
                "family": geometry.algebra.type_name,
                "class_label": geometry.algebra.class_label,
                "h_parameter": geometry.algebra.h_parameter,
                **({} if metadata is None else dict(metadata)),
            },
        )


@dataclass(frozen=True)
class ResidualPack:
    """Normalized residual carrier frozen by the ver3 numerical SSOT."""

    gauss: float
    codazzi: np.ndarray
    dual_route_curvature: float
    electric_weyl: np.ndarray
    magnetic_weyl: np.ndarray
    collision_isotropy: float | None = None
    inverse_boost: float | None = None
    notes: tuple[str, ...] = ()
    metadata: Mapping[str, object] = field(default_factory=dict)

    def __post_init__(self) -> None:
        object.__setattr__(self, "codazzi", _coerce_vector3(self.codazzi, name="ResidualPack.codazzi"))
        object.__setattr__(
            self,
            "electric_weyl",
            pstf_rank2(_coerce_matrix33(self.electric_weyl, name="ResidualPack.electric_weyl")),
        )
        object.__setattr__(
            self,
            "magnetic_weyl",
            pstf_rank2(_coerce_matrix33(self.magnetic_weyl, name="ResidualPack.magnetic_weyl")),
        )
        object.__setattr__(self, "notes", tuple(str(note) for note in self.notes))
        object.__setattr__(self, "metadata", dict(self.metadata))

    @property
    def all_finite(self) -> bool:
        pieces = (
            np.array([self.gauss, self.dual_route_curvature], dtype=np.float64),
            self.codazzi,
            self.electric_weyl,
            self.magnetic_weyl,
        )
        optional = [self.collision_isotropy, self.inverse_boost]
        return bool(
            all(np.all(np.isfinite(piece)) for piece in pieces)
            and all(value is None or np.isfinite(float(value)) for value in optional)
        )

    def norm_summary(self) -> dict[str, float | None]:
        return {
            "gauss_abs": float(abs(self.gauss)),
            "codazzi_norm": float(np.linalg.norm(self.codazzi)),
            "dual_route_curvature_abs": float(abs(self.dual_route_curvature)),
            "electric_weyl_norm": float(np.linalg.norm(self.electric_weyl)),
            "magnetic_weyl_norm": float(np.linalg.norm(self.magnetic_weyl)),
            "collision_isotropy_abs": None
            if self.collision_isotropy is None
            else float(abs(self.collision_isotropy)),
            "inverse_boost_abs": None
            if self.inverse_boost is None
            else float(abs(self.inverse_boost)),
        }

    @classmethod
    def from_covariant_objects(
        cls,
        residuals: BackgroundConstraintResiduals,
        geometry: TetradGeometry,
        *,
        electric_weyl: np.ndarray,
        magnetic_weyl: np.ndarray,
        collision_isotropy: float | None = None,
        inverse_boost: float | None = None,
        notes: Iterable[str] = (),
        metadata: Mapping[str, object] | None = None,
    ) -> "ResidualPack":
        return cls(
            gauss=float(residuals.gauss),
            codazzi=np.asarray(residuals.codazzi, dtype=np.float64),
            dual_route_curvature=float(geometry.dual_route_curvature_residual_norm),
            electric_weyl=np.asarray(electric_weyl, dtype=np.float64),
            magnetic_weyl=np.asarray(magnetic_weyl, dtype=np.float64),
            collision_isotropy=collision_isotropy,
            inverse_boost=inverse_boost,
            notes=tuple(notes),
            metadata={
                "dual_route_status": geometry.dual_route_status,
                "compact_formula_status": geometry.compact_formula_status,
                **({} if metadata is None else dict(metadata)),
            },
        )


@dataclass(frozen=True)
class OutputMetadata:
    """Concrete archive/output metadata contract for ver3 PR-10."""

    family: str | None
    branch: str
    backend: str | None
    ordering: str
    boost_applied: bool
    global_tilt_present: bool
    component_kind: str
    component_status: str
    local_boost_contract: str | None
    global_tilt_contract: str | None
    gate_status: Mapping[str, str] = field(default_factory=dict)
    residual_summary: Mapping[str, float] = field(default_factory=dict)
    manifest_claim_tier: str | None = None
    manifest_production_status: str | None = None
    metadata: Mapping[str, object] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.branch:
            raise ValueError("OutputMetadata.branch must be non-empty")
        if not self.ordering:
            raise ValueError("OutputMetadata.ordering must be non-empty")
        if not self.component_kind:
            raise ValueError("OutputMetadata.component_kind must be non-empty")
        if not self.component_status:
            raise ValueError("OutputMetadata.component_status must be non-empty")
        object.__setattr__(self, "gate_status", dict(self.gate_status))
        object.__setattr__(self, "residual_summary", dict(self.residual_summary))
        object.__setattr__(self, "metadata", dict(self.metadata))

    def as_dict(self) -> dict[str, object]:
        out: dict[str, object] = {
            "family": self.family,
            "branch": self.branch,
            "backend": self.backend,
            "ordering": self.ordering,
            "boost_applied": bool(self.boost_applied),
            "global_tilt_present": bool(self.global_tilt_present),
            "component_kind": self.component_kind,
            "component_status": self.component_status,
            "local_boost_contract": self.local_boost_contract,
            "global_tilt_contract": self.global_tilt_contract,
        }
        if self.gate_status:
            out["gate_status"] = dict(self.gate_status)
        if self.residual_summary:
            out["residual_summary"] = dict(self.residual_summary)
        if self.manifest_claim_tier is not None:
            out["manifest_claim_tier"] = self.manifest_claim_tier
        if self.manifest_production_status is not None:
            out["manifest_production_status"] = self.manifest_production_status
        out.update(self.metadata)
        return out

    @classmethod
    def from_solver_output(
        cls,
        output: SolverCoreOutput,
        *,
        ordering: str,
        component_kind: str,
        component_status: str,
        boost_applied: bool,
        gate_registry: Mapping[str, object] | None = None,
        residual_summary: Mapping[str, float] | None = None,
        metadata: Mapping[str, object] | None = None,
    ) -> "OutputMetadata":
        gate_status = {} if gate_registry is None else summarize_gate_status(gate_registry)
        return cls(
            family=output.metadata.get("bianchi_type"),
            branch=str(output.metadata.get("bianchi_branch", "orthogonal")),
            backend=output.metadata.get("source_propagator_realization"),
            ordering=ordering,
            boost_applied=boost_applied,
            global_tilt_present=bool(output.metadata.get("tilt_enabled", False)),
            component_kind=component_kind,
            component_status=component_status,
            local_boost_contract=output.metadata.get("local_boost_contract"),
            global_tilt_contract=output.metadata.get("global_tilt_contract"),
            gate_status=gate_status,
            residual_summary={} if residual_summary is None else dict(residual_summary),
            manifest_claim_tier=output.manifest.claim_tier,
            manifest_production_status=output.manifest.production_status,
            metadata={} if metadata is None else dict(metadata),
        )


@dataclass(frozen=True)
class BackgroundInterpolator:
    """Proper-time background interpolator with explicit conformal-time bridge."""

    t_grid: np.ndarray
    eta_grid: np.ndarray
    states: tuple[BackgroundState, ...]

    def __post_init__(self) -> None:
        t_grid = np.asarray(self.t_grid, dtype=np.float64)
        eta_grid = np.asarray(self.eta_grid, dtype=np.float64)
        if t_grid.ndim != 1 or eta_grid.ndim != 1:
            raise ValueError("BackgroundInterpolator grids must be 1-D")
        if t_grid.shape != eta_grid.shape:
            raise ValueError("BackgroundInterpolator grids must share shape")
        if len(self.states) != t_grid.size:
            raise ValueError("BackgroundInterpolator.states length must match the grid length")
        object.__setattr__(self, "t_grid", t_grid)
        object.__setattr__(self, "eta_grid", eta_grid)
        object.__setattr__(self, "states", tuple(self.states))

    def sample(self, eta: float) -> BackgroundState:
        if float(eta) < float(self.eta_grid[0]) or float(eta) > float(self.eta_grid[-1]):
            raise ValueError(
                f"eta={eta!r} lies outside [{self.eta_grid[0]!r}, {self.eta_grid[-1]!r}]"
            )
        gamma_stack = np.stack([state.gamma_AB for state in self.states], axis=0)
        sigma_stack = np.stack([state.sigma_AB for state in self.states], axis=0)
        species_hat = _interpolate_mapping_values(
            [state.species_hat for state in self.states],
            self.eta_grid,
            float(eta),
            name="species_hat",
        )
        species_tilt = _interpolate_mapping_values(
            [state.species_tilt for state in self.states],
            self.eta_grid,
            float(eta),
            name="species_tilt",
        )
        source_spec = self.states[0].family_spec
        return BackgroundState(
            t=_interp_scalar(self.eta_grid, self.t_grid, float(eta)),
            alpha=_interp_scalar(
                self.eta_grid,
                np.array([state.alpha for state in self.states], dtype=np.float64),
                float(eta),
            ),
            gamma_AB=_interp_matrix33(self.eta_grid, gamma_stack, float(eta)),
            theta=_interp_scalar(
                self.eta_grid,
                np.array([state.theta for state in self.states], dtype=np.float64),
                float(eta),
            ),
            sigma_AB=_interp_matrix33(self.eta_grid, sigma_stack, float(eta), pstf=True),
            family_spec=source_spec,
            species_hat=species_hat,
            species_tilt=species_tilt,
            metadata={
                "sampled_on": "eta_grid",
                "eta": float(eta),
                "eta_bounds": (float(self.eta_grid[0]), float(self.eta_grid[-1])),
                "proper_time_bounds": (float(self.t_grid[0]), float(self.t_grid[-1])),
            },
        )


def eta_from_t_grid(t_grid: Sequence[float], a_m_grid: Sequence[float]) -> np.ndarray:
    """Return the conformal-time grid implied by ``deta = dt / a_m``."""

    t = np.asarray(t_grid, dtype=np.float64)
    a = np.asarray(a_m_grid, dtype=np.float64)
    if t.ndim != 1 or a.ndim != 1:
        raise ValueError("eta_from_t_grid expects 1-D t_grid and a_m_grid")
    if t.shape != a.shape:
        raise ValueError("t_grid and a_m_grid must share shape")
    if t.size < 2:
        raise ValueError("eta_from_t_grid requires at least two samples")
    if np.any(~np.isfinite(t)) or np.any(~np.isfinite(a)):
        raise ValueError("eta_from_t_grid requires finite inputs")
    if np.any(np.diff(t) <= 0.0):
        raise ValueError("t_grid must be strictly increasing")
    if np.any(a <= 0.0):
        raise ValueError("a_m_grid must stay strictly positive")
    integrand = 1.0 / a
    eta = np.zeros_like(t)
    dt = np.diff(t)
    eta[1:] = np.cumsum(0.5 * (integrand[:-1] + integrand[1:]) * dt)
    return eta


def background_interpolator(
    t_grid: Sequence[float],
    state_grid: Sequence[BackgroundState],
) -> BackgroundInterpolator:
    """Build the mandatory proper-time background interpolator contract."""

    states = tuple(state_grid)
    if len(states) < 2:
        raise ValueError("background_interpolator requires at least two background states")
    t = np.asarray(t_grid, dtype=np.float64)
    if t.shape != (len(states),):
        raise ValueError("t_grid length must match state_grid length")
    alpha = np.array([state.alpha for state in states], dtype=np.float64)
    family = states[0].family_spec.family
    if any(state.family_spec.family != family for state in states[1:]):
        raise ValueError("background_interpolator requires one consistent family_spec")
    eta = eta_from_t_grid(t, np.exp(alpha))
    return BackgroundInterpolator(t_grid=t, eta_grid=eta, states=states)


def sample_background_on_eta(
    background_interp: BackgroundInterpolator,
    eta_grid: Sequence[float],
) -> tuple[BackgroundState, ...]:
    """Sample the proper-time background contract on an explicit eta grid."""

    eta = np.asarray(eta_grid, dtype=np.float64)
    if eta.ndim != 1:
        raise ValueError("sample_background_on_eta expects a 1-D eta grid")
    if np.any(np.diff(eta) < 0.0):
        raise ValueError("eta_grid must be monotone non-decreasing")
    return tuple(background_interp.sample(float(value)) for value in eta)
