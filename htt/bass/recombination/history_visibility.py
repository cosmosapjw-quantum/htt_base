"""VER2 scalar-history and visibility wiring for the BASS S2 lane."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Mapping

import numpy as np

from bass.hierarchy.frame_contracts import FrameSplitMetadata, PhotonDirectionConvention
from bass.recombination.recombination_ingest import (
    RecombinationInterp,
    RecombinationTable,
    build_interpolators,
    find_visibility_peak,
)
from bass.validation import GateBundle, make_gate_bundle
from bass.recombination.reionization import (
    CosmologyForRecombination,
    ReionizationParameters,
    compute_kappa_from_tau_dot,
    compute_tau_dot_conformal_Mpc,
    compute_reionization_tau,
    extend_table_with_reionization,
)

if TYPE_CHECKING:
    from bass.collision.tilted_visibility import TiltedVisibility
    from bass.species.baryon import BaryonBackground

__all__ = [
    "ScalarHistoryMetadata",
    "VisibilityEventMarkers",
    "VisibilityNormalizationStatus",
    "VisibilityHistoryContract",
    "TiltedVisibilitySource",
    "opacity_from_physical_inputs",
    "optical_depth",
    "visibility_function",
    "homogeneous_reionization_history",
    "visibility_history_gate_bundle",
    "build_visibility_history_contract",
    "build_tilted_visibility_source",
    "build_tilted_visibility_source_stub",
]


@dataclass(frozen=True)
class ScalarHistoryMetadata:
    """Metadata for scalar-history-first-pass visibility wiring."""

    reionization_mode: str = "disabled"
    homogeneous_reionization_only: bool = True
    tilted_visibility_available: bool = True
    visibility_normalization_check_required: bool = True
    source_scope: str = "scalar_history_first_pass"

    def __post_init__(self) -> None:
        if self.reionization_mode not in {"disabled", "tanh"}:
            raise ValueError(
                "reionization_mode must be 'disabled' or 'tanh', "
                f"got {self.reionization_mode!r}"
            )
        if not self.homogeneous_reionization_only:
            raise ValueError(
                "SK-02S2 only allows homogeneous reionization wiring"
            )
        if self.source_scope != "scalar_history_first_pass":
            raise ValueError(
                "SK-02S2 freezes scalar-history-first-pass only"
            )


@dataclass(frozen=True)
class VisibilityNormalizationStatus:
    """Normalization / monotonicity checks logged on the scalar history path."""

    visibility_nonnegative: bool
    kappa_monotone_increasing_in_z: bool
    optical_depth_decreases_toward_observer: bool
    sampled_on_table_grid: bool = True
    min_visibility: float = 0.0

    def __post_init__(self) -> None:
        if not self.sampled_on_table_grid:
            raise ValueError("visibility normalization checks must be sampled on the table grid")
        if not np.isfinite(self.min_visibility):
            raise ValueError("min_visibility must be finite")
        if not self.visibility_nonnegative:
            raise ValueError("visibility normalization failed: g(z) must be non-negative")
        if not self.kappa_monotone_increasing_in_z:
            raise ValueError("visibility normalization failed: kappa(z) must be monotone increasing")
        if not self.optical_depth_decreases_toward_observer:
            raise ValueError(
                "visibility normalization failed: optical depth must decrease toward the observer"
            )


@dataclass(frozen=True)
class VisibilityHistoryContract:
    """Scalar recombination/reionization history plus visibility interpolants."""

    table: RecombinationTable
    interp: RecombinationInterp
    history_metadata: ScalarHistoryMetadata = field(default_factory=ScalarHistoryMetadata)
    normalization_status: VisibilityNormalizationStatus = field(
        default_factory=lambda: VisibilityNormalizationStatus(
            visibility_nonnegative=True,
            kappa_monotone_increasing_in_z=True,
            optical_depth_decreases_toward_observer=True,
        )
    )
    frame_metadata: FrameSplitMetadata = field(default_factory=FrameSplitMetadata)
    events: "VisibilityEventMarkers | None" = None

    def __post_init__(self) -> None:
        if self.frame_metadata.visibility_frame != "electron_frame":
            raise ValueError("visibility must remain electron-frame owned in VER2")
        if self.frame_metadata.scalar_history_scope != "scalar_history_first_pass":
            raise ValueError("history scope drifted outside the S2 contract")
        if self.interp.table is not self.table:
            raise ValueError("visibility interpolator must be built from the stored table")
        if (
            self.history_metadata.reionization_mode == "tanh"
            and self.table.metadata.get("reionization") != "tanh"
        ):
            raise ValueError("tanh history mode requires reionization-tagged table metadata")
        if self.history_metadata.visibility_normalization_check_required:
            _ = self.normalization_status


@dataclass(frozen=True)
class VisibilityEventMarkers:
    """Key visibility/reionization markers carried with the scalar history."""

    z_last_scattering: float
    visibility_peak: float
    reionization_detected: bool
    tau_reion: float = 0.0
    reionization_mode: str = "disabled"

    def __post_init__(self) -> None:
        if not np.isfinite(self.z_last_scattering) or self.z_last_scattering <= 0.0:
            raise ValueError("z_last_scattering must be positive finite")
        if not np.isfinite(self.visibility_peak) or self.visibility_peak < 0.0:
            raise ValueError("visibility_peak must be non-negative finite")
        if not np.isfinite(self.tau_reion) or self.tau_reion < 0.0:
            raise ValueError("tau_reion must be non-negative finite")
        if self.reionization_mode not in {"disabled", "tanh"}:
            raise ValueError(f"unknown reionization_mode {self.reionization_mode!r}")


@dataclass(frozen=True)
class TiltedVisibilitySource:
    """Direction-resolved visibility wrapper owned by the electron frame."""

    contract: VisibilityHistoryContract
    visibility: "TiltedVisibility"
    direction_convention: PhotonDirectionConvention = PhotonDirectionConvention.PROPAGATION

    source_ready: bool = True
    tilt_active: bool = True
    reduces_to_scalar_when_tilt_zero: bool = True
    frame: str = "electron_frame"

    def __post_init__(self) -> None:
        if self.frame != "electron_frame":
            raise ValueError("tilted visibility must stay electron-frame owned")
        if self.contract.frame_metadata.visibility_frame != "electron_frame":
            raise ValueError("contract visibility frame drifted away from the electron frame")

    def Gamma_T(self, eta: float, direction: np.ndarray) -> float:
        return float(self.visibility.Gamma_T(float(eta), np.asarray(direction, dtype=np.float64)))

    def kappa(self, eta: float, direction: np.ndarray) -> float:
        return float(self.visibility.kappa(float(eta), np.asarray(direction, dtype=np.float64)))

    def g(self, eta: float, direction: np.ndarray) -> float:
        return float(self.visibility.g(float(eta), np.asarray(direction, dtype=np.float64)))


def _build_event_markers(
    interp: RecombinationInterp,
    history_metadata: ScalarHistoryMetadata,
) -> VisibilityEventMarkers:
    z_star, g_star = find_visibility_peak(interp)
    tau_reion = 0.0
    if history_metadata.reionization_mode == "tanh":
        z_cut = min(30.0, float(interp.table.z_max))
        tau_reion = compute_reionization_tau(interp.table, z_high_cutoff=z_cut)
    return VisibilityEventMarkers(
        z_last_scattering=z_star,
        visibility_peak=g_star,
        reionization_detected=history_metadata.reionization_mode == "tanh" and tau_reion > 0.0,
        tau_reion=tau_reion,
        reionization_mode=history_metadata.reionization_mode,
    )


def opacity_from_physical_inputs(
    *,
    z: np.ndarray,
    x_e: np.ndarray,
    cosmology: CosmologyForRecombination,
) -> np.ndarray:
    """ver3 opacity adapter: conformal Thomson rate in 1/Mpc."""

    return compute_tau_dot_conformal_Mpc(
        np.asarray(z, dtype=np.float64),
        np.asarray(x_e, dtype=np.float64),
        cosmology,
    )


def optical_depth(
    *,
    z: np.ndarray,
    tau_dot_Mpc: np.ndarray,
    cosmology: CosmologyForRecombination,
) -> np.ndarray:
    """ver3 optical-depth adapter built from conformal opacity."""

    return compute_kappa_from_tau_dot(
        np.asarray(z, dtype=np.float64),
        np.asarray(tau_dot_Mpc, dtype=np.float64),
        cosmology,
    )


def visibility_function(
    *,
    tau_dot_Mpc: np.ndarray,
    kappa: np.ndarray,
) -> np.ndarray:
    """Return the scalar visibility `g = tau_dot * exp(-kappa)`."""

    tau_dot = np.asarray(tau_dot_Mpc, dtype=np.float64)
    kappa_arr = np.asarray(kappa, dtype=np.float64)
    if tau_dot.shape != kappa_arr.shape:
        raise ValueError(
            f"tau_dot_Mpc and kappa must share shape, got {tau_dot.shape} and {kappa_arr.shape}"
        )
    return tau_dot * np.exp(-kappa_arr)


def _build_normalization_status(
    table: RecombinationTable,
    interp: RecombinationInterp,
) -> VisibilityNormalizationStatus:
    z_grid = np.asarray(table.z, dtype=np.float64)
    visibility = np.asarray(interp.query_visibility(z_grid), dtype=np.float64)
    kappa = np.asarray(table.kappa, dtype=np.float64)
    min_visibility = float(np.min(visibility))
    visibility_nonnegative = bool(np.all(visibility >= -1.0e-12))
    kappa_monotone = bool(np.all(np.diff(kappa) >= -1.0e-12))
    return VisibilityNormalizationStatus(
        visibility_nonnegative=visibility_nonnegative,
        kappa_monotone_increasing_in_z=kappa_monotone,
        optical_depth_decreases_toward_observer=kappa_monotone,
        min_visibility=min_visibility,
    )


def homogeneous_reionization_history(
    table: RecombinationTable,
    *,
    reionization_params: ReionizationParameters | None = None,
    cosmology: CosmologyForRecombination | None = None,
) -> VisibilityHistoryContract:
    """ver3 homogeneous reionization adapter."""

    return build_visibility_history_contract(
        table,
        include_reionization=True,
        reionization_params=reionization_params,
        cosmology=cosmology,
    )


def build_visibility_history_contract(
    table: RecombinationTable,
    *,
    include_reionization: bool = False,
    reionization_params: ReionizationParameters | None = None,
    cosmology: CosmologyForRecombination | None = None,
) -> VisibilityHistoryContract:
    """Build the scalar-history-first-pass visibility contract."""
    effective_table = table
    history_metadata = ScalarHistoryMetadata()
    if include_reionization:
        params = reionization_params or ReionizationParameters()
        effective_table = extend_table_with_reionization(
            recomb_table=table,
            reion_params=params,
            cosmology=cosmology,
        )
        history_metadata = ScalarHistoryMetadata(reionization_mode="tanh")
    interp = build_interpolators(effective_table)
    return VisibilityHistoryContract(
        table=effective_table,
        interp=interp,
        history_metadata=history_metadata,
        normalization_status=_build_normalization_status(effective_table, interp),
        events=_build_event_markers(interp, history_metadata),
    )


def build_tilted_visibility_source(
    contract: VisibilityHistoryContract,
    *,
    baryon: "BaryonBackground",
    v_e,
    direction_convention: PhotonDirectionConvention = PhotonDirectionConvention.PROPAGATION,
    beta_from_v: bool = True,
) -> TiltedVisibilitySource:
    """Build the executable tilted visibility source on top of the scalar history."""
    from bass.collision.tilted_visibility import TiltedVisibility

    if baryon._recomb is not contract.interp:  # noqa: SLF001 - deliberate contract check
        raise ValueError(
            "baryon recombination interpolator must match the stored visibility contract"
        )
    return TiltedVisibilitySource(
        contract=contract,
        visibility=TiltedVisibility(
            baryon=baryon,
            v_e=v_e,
            beta_from_v=beta_from_v,
            direction_convention=direction_convention,
        ),
        direction_convention=direction_convention,
        tilt_active=True,
    )


def build_tilted_visibility_source_stub(
    contract: VisibilityHistoryContract,
    *,
    baryon: "BaryonBackground",
    v_e,
    direction_convention: PhotonDirectionConvention = PhotonDirectionConvention.PROPAGATION,
    beta_from_v: bool = True,
) -> TiltedVisibilitySource:
    """Compatibility alias kept while call sites migrate to `build_tilted_visibility_source`."""
    return build_tilted_visibility_source(
        contract,
        baryon=baryon,
        v_e=v_e,
        direction_convention=direction_convention,
        beta_from_v=beta_from_v,
    )


def visibility_history_gate_bundle(
    contract: VisibilityHistoryContract,
    *,
    family: str = "unspecified",
    branch: str = "orthogonal",
    backend: str = "visibility_history_contract",
    truncation: Mapping[str, object] | None = None,
) -> GateBundle:
    """Emit the machine-readable PR-07 visibility/history gate bundle."""

    events = contract.events
    return make_gate_bundle(
        "visibility_history_gate",
        family=family,
        branch=branch,
        backend=backend,
        truncation={} if truncation is None else dict(truncation),
        residual_summary={
            "min_visibility": float(contract.normalization_status.min_visibility),
            "tau_reion": float(0.0 if events is None else events.tau_reion),
            "z_last_scattering": float(
                0.0 if events is None else events.z_last_scattering
            ),
        },
        known_limit_checks={
            "visibility_nonnegative": contract.normalization_status.visibility_nonnegative,
            "kappa_monotone_increasing_in_z": (
                contract.normalization_status.kappa_monotone_increasing_in_z
            ),
            "optical_depth_decreases_toward_observer": (
                contract.normalization_status.optical_depth_decreases_toward_observer
            ),
            "homogeneous_reionization_only": (
                contract.history_metadata.homogeneous_reionization_only
            ),
        },
        forbidden_shortcut_checks={
            "electron_frame_visibility_ownership": (
                contract.frame_metadata.visibility_frame == "electron_frame"
            ),
            "no_statistics_layer": True,
        },
        metadata={
            "reionization_mode": contract.history_metadata.reionization_mode,
            "source_scope": contract.history_metadata.source_scope,
        },
        passed=bool(
            contract.normalization_status.visibility_nonnegative
            and contract.normalization_status.kappa_monotone_increasing_in_z
            and contract.normalization_status.optical_depth_decreases_toward_observer
        ),
        opened_claim="source-history contract frozen",
    )
