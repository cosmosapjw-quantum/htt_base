"""VER2 scalar-history and visibility skeletons for the BASS S2 lane."""
from __future__ import annotations

from dataclasses import dataclass, field

from bass.hierarchy.frame_contracts import FrameSplitMetadata
from bass.recombination.recombination_ingest import (
    RecombinationInterp,
    RecombinationTable,
    build_interpolators,
)
from bass.recombination.reionization import (
    CosmologyForRecombination,
    ReionizationParameters,
    extend_table_with_reionization,
)

__all__ = [
    "ScalarHistoryMetadata",
    "VisibilityHistoryContract",
    "TiltedVisibilitySourceStub",
    "build_visibility_history_contract",
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
class TiltedVisibilitySourceStub:
    """Non-executable record that visibility can later be tilt-modulated."""

    source_ready: bool = False
    tilt_active: bool = False
    reduces_to_scalar_when_tilt_zero: bool = True
    frame: str = "electron_frame"
    reason: str = (
        "Tilted visibility modulation is carried forward explicitly; "
        "SK-02S2 freezes only the scalar-history and ownership contracts."
    )

    def __post_init__(self) -> None:
        if self.frame != "electron_frame":
            raise ValueError("tilted visibility must stay electron-frame owned")


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
    )


def build_tilted_visibility_source_stub(
    contract: VisibilityHistoryContract,
    *,
    tilt_active: bool,
) -> TiltedVisibilitySourceStub:
    """Return the explicit carry-forward hook for tilted visibility."""
    _ = contract
    return TiltedVisibilitySourceStub(tilt_active=tilt_active)
