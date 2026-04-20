"""VER2 departure and xQPiFG shared contracts.

This module hosts the skeleton dataclasses for the x/Q/Pi/F/G family under the
VER2 authority docs. It intentionally contains contracts only; no physics,
statistics, or inference computation lives here.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Literal, Optional

import numpy as np

from common.contracts import ArtifactManifest


ComparatorPolicy = Literal["flat", "matched", "closed", "custom"]
NumeratorPolicy = Literal["signed", "positive_part", "absolute"]
CeilingKind = Literal[
    "linear_MES",
    "family_NP",
    "atlas_envelope",
    "cmb_quantile",
    "channel_effective",
    "custom",
]
UncertaintyKind = Literal[
    "htt_posterior",
    "mio_measurement",
    "bootstrap",
    "mock_calibrated",
    "profile_likelihood",
]
FillingStatus = Literal[
    "certified_occupancy",
    "linear_proxy_score",
    "signed_saturation_diagnostic",
    "invalid_negative_sector",
    "invalid_vortical_sector",
    "invalid_ceiling_not_admissible",
]
GapKind = Literal["ratio", "log", "difference"]


@dataclass(frozen=True)
class DepartureBundle:
    comparator: ComparatorPolicy
    Sigma2_std: float
    W2_std: float
    Omega_tilt: float
    Omega_k_aniso: float
    covariance: np.ndarray | None
    frame_convention: str
    sector: str
    provenance: dict[str, str]

    @property
    def x_signed(self) -> float:
        return self.Sigma2_std - self.W2_std + self.Omega_tilt + self.Omega_k_aniso

    @property
    def x_positive(self) -> float:
        return max(self.x_signed, 0.0)


@dataclass(frozen=True)
class BudgetSpec:
    kind: CeilingKind
    value: float
    uncertainty: float | None
    family_id: str | None
    channel: str | None
    redshift: float | None
    confidence_level: float | None
    assumptions: tuple[str, ...]
    is_admissible_ceiling: bool

    def __post_init__(self) -> None:
        if self.value < 0.0:
            raise ValueError("BudgetSpec.value must be non-negative")


@dataclass(frozen=True)
class NormalizedScore:
    q_value: float
    x_value: float
    numerator_policy: NumeratorPolicy
    budget: BudgetSpec
    comparator: ComparatorPolicy
    status: str


@dataclass(frozen=True)
class FillingFraction:
    value: float | None
    status: FillingStatus
    score_if_invalid: float | None
    comparator: ComparatorPolicy
    budget: BudgetSpec
    sector: str
    redshift: float | None
    component_breakdown: dict[str, float]
    provenance: dict[str, str]


@dataclass(frozen=True)
class ExceedanceCurve:
    q_grid: np.ndarray
    pi_grid: np.ndarray
    uncertainty_kind: UncertaintyKind
    target: Literal["Q", "F"]
    threshold_labels: dict[str, float]
    q50: float
    q95: float
    provenance: dict[str, str]

    def __post_init__(self) -> None:
        if self.q_grid.ndim != 1 or self.pi_grid.ndim != 1:
            raise ValueError("ExceedanceCurve grids must be 1-D")
        if self.q_grid.shape != self.pi_grid.shape:
            raise ValueError("ExceedanceCurve grids must have matching shape")


@dataclass(frozen=True)
class IsotropyGap:
    value: float | None
    kind: GapKind
    z_a: float
    z_b: float
    F_a: FillingFraction
    F_b: FillingFraction
    epsilon_floor: float
    status: str
    uncertainty_kind: UncertaintyKind
    provenance: dict[str, str]

    def __post_init__(self) -> None:
        if self.epsilon_floor <= 0.0:
            raise ValueError("IsotropyGap.epsilon_floor must be positive")


@dataclass(frozen=True)
class DepartureReport:
    comparator_policy: ComparatorPolicy
    bundle_B: dict[str, float]
    x_value: float
    numerator_policy: NumeratorPolicy
    denominator_policy: str
    U_value: float
    Q_value: float
    F_value: float | None
    F_status: FillingStatus | str
    Pi_curve_ref: str | None
    G_values: dict[str, float]
    component_filling: dict[str, float]
    channel_filling: dict[str, float]
    caveats: list[str]
    manifest: ArtifactManifest
    tsc_overlay_ref: str | None = None

    def __post_init__(self) -> None:
        if self.manifest.owner not in {"HTT", "MIO", "COMMON"}:
            raise ValueError(
                "DepartureReport.manifest.owner must be 'HTT', 'MIO', or 'COMMON' "
                f"(got {self.manifest.owner!r})"
            )
