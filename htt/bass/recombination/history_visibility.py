"""VER2 scalar-history and visibility wiring for the BASS S2 lane."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING

import numpy as np

from bass.hierarchy.frame_contracts import FrameSplitMetadata, PhotonDirectionConvention
from bass.recombination.recombination_ingest import (
    RecombinationInterp,
    RecombinationTable,
    build_interpolators,
    find_visibility_peak,
)
from bass.recombination.reionization import (
    CosmologyForRecombination,
    ReionizationParameters,
    compute_reionization_tau,
    extend_table_with_reionization,
)

if TYPE_CHECKING:
    from bass.collision.tilted_visibility import TiltedVisibility
    from bass.species.baryon import BaryonBackground

__all__ = [
    "ScalarHistoryMetadata",
    "VisibilityEventMarkers",
    "VisibilityHistoryContract",
    "TiltedVisibilitySource",
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
class VisibilityHistoryContract:
    """Scalar recombination/reionization history plus visibility interpolants."""

    table: RecombinationTable
    interp: RecombinationInterp
    history_metadata: ScalarHistoryMetadata = field(default_factory=ScalarHistoryMetadata)
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
