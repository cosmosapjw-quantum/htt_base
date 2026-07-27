"""Typed statistical foundations for the graded FLRW-departure programme.

This module separates three objects that legacy code often represented with a
single scalar:

* the exact signed Gauss/Friedmann budget projection ``x_C``;
* a channel-matched stress ratio against a typed physical anchor; and
* a data-identified (possibly set-valued) estimand.

The first change-set exposes only the anchor authority.  Later change-sets add
the state, partial-identification, orbit and reporting contracts here so all
owners consume one dependency-light authority.

No object in this module identifies a Bianchi family or geometry.  MES anchors
are conditional one-way linear-consistency bounds, never distances or evidence
for the converse.
"""
from __future__ import annotations

import math
from dataclasses import dataclass
from enum import Enum
from fractions import Fraction
from typing import Iterable

from common.mes_theorem_authority import BRANCHES


class StatisticalFoundationError(ValueError):
    """Raised when a typed foundation contract is malformed."""


class _StringEnum(str, Enum):
    def __str__(self) -> str:
        return self.value


class AnchorAuthorityKind(_StringEnum):
    MES = "MES"
    EXTERNAL_PHYSICAL = "EXTERNAL_PHYSICAL"
    EMPIRICAL = "EMPIRICAL"
    LEGACY = "LEGACY"


class AnchorStatus(_StringEnum):
    VERIFIED = "VERIFIED"
    WITHHELD = "WITHHELD"
    NO_MES_ANCHOR = "NO_MES_ANCHOR"
    LEGACY_REPRODUCTION = "LEGACY_REPRODUCTION"


class AnchorConditioning(_StringEnum):
    REALIZATION_CONDITIONAL = "REALIZATION_CONDITIONAL"
    ENSEMBLE_CALIBRATED = "ENSEMBLE_CALIBRATED"


def _required_text(value: object, field_name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise StatisticalFoundationError(
            f"{field_name} must be a non-empty string"
        )
    if value != value.strip():
        raise StatisticalFoundationError(
            f"{field_name} must not contain surrounding whitespace"
        )
    return value


def _finite_nonnegative(value: object, field_name: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise StatisticalFoundationError(
            f"{field_name} must be a finite non-negative real number"
        )
    out = float(value)
    if not math.isfinite(out) or out < 0.0:
        raise StatisticalFoundationError(
            f"{field_name} must be a finite non-negative real number"
        )
    return out


def _text_tuple(values: Iterable[object], field_name: str) -> tuple[str, ...]:
    out = tuple(_required_text(value, field_name) for value in values)
    if not out:
        raise StatisticalFoundationError(f"{field_name} must not be empty")
    if len(set(out)) != len(out):
        raise StatisticalFoundationError(f"{field_name} must not contain duplicates")
    return out


@dataclass(frozen=True)
class MESAnchorSpec:
    """One typed anchor for exactly one physical invariant and channel."""

    anchor_id: str
    value: float | None
    authority_kind: AnchorAuthorityKind
    target_sector: str
    target_invariant: str
    frame: str
    congruence: str
    normalization: str
    perturbative_order: str
    branch: str
    attribution: str
    conditioning: AnchorConditioning
    validity_domain: str
    source_equations: tuple[str, ...]
    shared_nuisance: tuple[str, ...]
    status: AnchorStatus
    allowed_use: tuple[str, ...]
    forbidden_use: tuple[str, ...]
    withheld_reason: str | None = None

    def __post_init__(self) -> None:
        for name, enum_type in (
            ("authority_kind", AnchorAuthorityKind),
            ("conditioning", AnchorConditioning),
            ("status", AnchorStatus),
        ):
            if not isinstance(getattr(self, name), enum_type):
                raise StatisticalFoundationError(
                    f"{name} must be a {enum_type.__name__}"
                )
        for name in (
            "anchor_id",
            "target_sector",
            "target_invariant",
            "frame",
            "congruence",
            "normalization",
            "perturbative_order",
            "branch",
            "attribution",
            "validity_domain",
        ):
            _required_text(getattr(self, name), name)
        object.__setattr__(
            self, "source_equations", _text_tuple(self.source_equations, "source_equations")
        )
        object.__setattr__(
            self, "shared_nuisance", tuple(
                _required_text(value, "shared_nuisance")
                for value in self.shared_nuisance
            )
        )
        object.__setattr__(
            self, "allowed_use", _text_tuple(self.allowed_use, "allowed_use")
        )
        object.__setattr__(
            self, "forbidden_use", _text_tuple(self.forbidden_use, "forbidden_use")
        )
        if len(set(self.shared_nuisance)) != len(self.shared_nuisance):
            raise StatisticalFoundationError(
                "shared_nuisance must not contain duplicates"
            )

        if self.status is AnchorStatus.NO_MES_ANCHOR:
            if self.value is not None:
                raise StatisticalFoundationError(
                    "NO_MES_ANCHOR must carry value=None"
                )
        else:
            object.__setattr__(
                self, "value", _finite_nonnegative(self.value, "value")
            )

        if self.status is AnchorStatus.WITHHELD:
            _required_text(self.withheld_reason, "withheld_reason")
        elif self.withheld_reason is not None:
            raise StatisticalFoundationError(
                "withheld_reason is only valid for WITHHELD anchors"
            )

    @property
    def channel_key(self) -> tuple[str, ...]:
        """Identity required for any valid numerator/denominator ratio."""
        return (
            self.target_sector,
            self.target_invariant,
            self.frame,
            self.congruence,
            self.normalization,
            self.perturbative_order,
            self.branch,
        )

    @property
    def normalization_allowed(self) -> bool:
        return self.status is AnchorStatus.VERIFIED


def _branch_bound(
    branch_id: str, eps1: float, eps2: float, eps3: float
) -> float:
    values = (
        _finite_nonnegative(eps1, "eps1"),
        _finite_nonnegative(eps2, "eps2"),
        _finite_nonnegative(eps3, "eps3"),
    )
    branch = BRANCHES[branch_id]
    coefficients = tuple(
        float(Fraction(value)) for value in branch["coefficients_exact"]
    )
    return float(sum(coefficient * value for coefficient, value in zip(coefficients, values)))


def registered_geodesic_mes_anchors(
    *,
    eps1: float,
    eps2: float,
    eps3: float,
    attribution: str,
    conditioning: AnchorConditioning,
) -> dict[str, MESAnchorSpec]:
    """Build the only active MES anchor set.

    The caller must choose both the dipole attribution and conditioning.  No
    observed-dipole, SAG-residual, realization or ensemble default is guessed.
    """
    attribution = _required_text(attribution, "attribution")
    sigma_bound = _branch_bound("MES_G_SIGMA", eps1, eps2, eps3)
    omega_bound = _branch_bound("MES_G_OMEGA", eps1, eps2, eps3)
    common_forbidden = (
        "FLRW converse",
        "Bianchi family identification",
        "geometry detection",
        "cross-channel scalar occupancy",
    )
    shared_nuisance = ("eps1", "eps2", "eps3")
    return {
        "sigma": MESAnchorSpec(
            anchor_id="MES_G_SIGMA_UNCORRECTED",
            value=1.5 * sigma_bound * sigma_bound,
            authority_kind=AnchorAuthorityKind.MES,
            target_sector="Sigma2",
            target_invariant="sigma_ab_sigma_ab_over_6H2",
            frame="registered MES fundamental-observer frame",
            congruence="geodesic",
            normalization="Sigma2_std",
            perturbative_order="linear almost-EGS",
            branch="MES_G_SIGMA",
            attribution=attribution,
            conditioning=conditioning,
            validity_domain="registered C1/C2 linear almost-EGS premises",
            source_equations=("MESa eq (59)", "MESa raw eq (51)"),
            shared_nuisance=shared_nuisance,
            status=AnchorStatus.VERIFIED,
            allowed_use=("channel-matched one-way linear-consistency stress",),
            forbidden_use=common_forbidden,
        ),
        "omega": MESAnchorSpec(
            anchor_id="MES_G_OMEGA",
            value=1.5 * omega_bound * omega_bound,
            authority_kind=AnchorAuthorityKind.MES,
            target_sector="W2",
            target_invariant="omega_ab_omega_ab_over_6H2",
            frame="registered MES fundamental-observer frame",
            congruence="geodesic",
            normalization="W2_std",
            perturbative_order="linear almost-EGS",
            branch="MES_G_OMEGA",
            attribution=attribution,
            conditioning=conditioning,
            validity_domain="registered C1/C2 linear almost-EGS premises",
            source_equations=("MESa eq (60)", "MESa raw eq (52)"),
            shared_nuisance=shared_nuisance,
            status=AnchorStatus.VERIFIED,
            allowed_use=("channel-matched one-way linear-consistency stress",),
            forbidden_use=common_forbidden,
        ),
        "acceleration": MESAnchorSpec(
            anchor_id="MES_G_ACCEL_ABSENCE",
            value=None,
            authority_kind=AnchorAuthorityKind.MES,
            target_sector="A2",
            target_invariant="a_dot_a_over_6H2",
            frame="registered MES fundamental-observer frame",
            congruence="geodesic",
            normalization="A2_std",
            perturbative_order="linear almost-EGS",
            branch="MES_G_ACCEL",
            attribution=attribution,
            conditioning=conditioning,
            validity_domain="geodesic premise u_dot=0",
            source_equations=("MESa p.123 geodesic premise",),
            shared_nuisance=(),
            status=AnchorStatus.NO_MES_ANCHOR,
            allowed_use=("structural absence report",),
            forbidden_use=(
                "acceleration saturation",
                "acceleration ceiling",
                *common_forbidden,
            ),
        ),
        "anisotropic_curvature": MESAnchorSpec(
            anchor_id="MES_DELTA_OMEGA_K_ABSENCE",
            value=None,
            authority_kind=AnchorAuthorityKind.MES,
            target_sector="DeltaOmegaK",
            target_invariant="anisotropic_curvature_budget_coordinate",
            frame="registered comparator frame",
            congruence="not_applicable",
            normalization="DeltaOmegaK",
            perturbative_order="not_bounded_by_MES",
            branch="NO_MES_BRANCH",
            attribution=attribution,
            conditioning=conditioning,
            validity_domain="no registered MES curvature ceiling",
            source_equations=("MES authority table: no curvature anchor",),
            shared_nuisance=(),
            status=AnchorStatus.NO_MES_ANCHOR,
            allowed_use=("partial-identification status",),
            forbidden_use=(
                "curvature saturation",
                "invented curvature ceiling",
                *common_forbidden,
            ),
        ),
    }


def quarantined_shear_anchors(
    *,
    eps1: float,
    eps2: float,
    eps3: float,
    attribution: str,
    conditioning: AnchorConditioning,
) -> dict[str, MESAnchorSpec]:
    """Historical shear anchors that must never normalize active results."""
    attribution = _required_text(attribution, "attribution")
    sigma_bound = _branch_bound("MES_G_SIGMA", eps1, eps2, eps3)
    corrected = 1.5 * ((1.0 + 2.69 * float(eps1)) * sigma_bound) ** 2
    forbidden = (
        "active saturation",
        "combined-sector denominator",
        "claim promotion",
    )
    return {
        "frame_corrected": MESAnchorSpec(
            anchor_id="LEGACY_FRAME_CORRECTED_SIGMA2",
            value=corrected,
            authority_kind=AnchorAuthorityKind.LEGACY,
            target_sector="Sigma2",
            target_invariant="sigma_ab_sigma_ab_over_6H2",
            frame="legacy VT-07-labelled frame",
            congruence="geodesic",
            normalization="Sigma2_std",
            perturbative_order="legacy linear expression",
            branch="MES_G_SIGMA_PLUS_2P69_EPS1",
            attribution=attribution,
            conditioning=conditioning,
            validity_domain="historical reproduction only",
            source_equations=("legacy VT-07 1 + 2.69 eps1 expression",),
            shared_nuisance=("eps1", "eps2", "eps3"),
            status=AnchorStatus.WITHHELD,
            allowed_use=("historical byte/value reproduction",),
            forbidden_use=forbidden,
            withheld_reason="2.69 eps1 derivation chain is numerically inconsistent",
        ),
        "s2a_catwise": MESAnchorSpec(
            anchor_id="LEGACY_S2A_CATWISE_SIGMA2",
            value=9.25e-6,
            authority_kind=AnchorAuthorityKind.LEGACY,
            target_sector="Sigma2",
            target_invariant="sigma_ab_sigma_ab_over_6H2",
            frame="legacy S2a scenario frame",
            congruence="legacy scenario",
            normalization="Sigma2_std",
            perturbative_order="legacy linear expression",
            branch="S2A_CATWISE_SHEAR_ONLY",
            attribution="CatWISE dipole scenario",
            conditioning=conditioning,
            validity_domain="historical S2a shear reproduction only",
            source_equations=("legacy S2a table",),
            shared_nuisance=("CatWISE_eps1",),
            status=AnchorStatus.LEGACY_REPRODUCTION,
            allowed_use=("historical byte/value reproduction",),
            forbidden_use=forbidden,
        ),
    }


__all__ = [
    "AnchorAuthorityKind",
    "AnchorConditioning",
    "AnchorStatus",
    "MESAnchorSpec",
    "StatisticalFoundationError",
    "quarantined_shear_anchors",
    "registered_geodesic_mes_anchors",
]
