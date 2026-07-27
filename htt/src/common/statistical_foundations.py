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
from statistics import NormalDist
from typing import Iterable, Mapping, Sequence

from common.mes_theorem_authority import (
    BRANCHES,
    MesAuthorityError,
    validate_hierarchy_strict,
)


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


class IdentificationStatus(_StringEnum):
    POINT_IDENTIFIED = "POINT_IDENTIFIED"
    WEAKLY_IDENTIFIED = "WEAKLY_IDENTIFIED"
    PARTIALLY_IDENTIFIED = "PARTIALLY_IDENTIFIED"
    NON_IDENTIFIED = "NON_IDENTIFIED"
    EMPTY = "EMPTY"


class NullKind(_StringEnum):
    NONE = "NONE"
    STRUCTURAL = "STRUCTURAL"
    LEADING_ORDER = "LEADING_ORDER"
    NUMERICAL = "NUMERICAL"


class StressStatus(_StringEnum):
    DEFINED = "DEFINED"
    RATIO_UNIDENTIFIED = "RATIO_UNIDENTIFIED"
    ANCHOR_UNAVAILABLE = "ANCHOR_UNAVAILABLE"
    CHANNEL_MISMATCH = "CHANNEL_MISMATCH"
    NUMERATOR_UNIDENTIFIED = "NUMERATOR_UNIDENTIFIED"


class BudgetRadiusStatus(_StringEnum):
    DEFINED = "DEFINED"
    NULL_RESIDUAL_PRESENT = "NULL_RESIDUAL_PRESENT"


BC1_LEGACY_PROJECTION = "BC1_LEGACY_PROJECTION"
BC2_NO_REPRESENTATION_PROMOTION = "BC2_NO_REPRESENTATION_PROMOTION"


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


def _finite_real(value: object, field_name: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise StatisticalFoundationError(
            f"{field_name} must be a finite real number"
        )
    out = float(value)
    if not math.isfinite(out):
        raise StatisticalFoundationError(
            f"{field_name} must be a finite real number"
        )
    return out


def _finite_positive(value: object, field_name: str) -> float:
    out = _finite_nonnegative(value, field_name)
    if out == 0.0:
        raise StatisticalFoundationError(
            f"{field_name} must be a finite positive real number"
        )
    return out


def _text_tuple(values: Iterable[object], field_name: str) -> tuple[str, ...]:
    out = tuple(_required_text(value, field_name) for value in values)
    if not out:
        raise StatisticalFoundationError(f"{field_name} must not be empty")
    if len(set(out)) != len(out):
        raise StatisticalFoundationError(f"{field_name} must not contain duplicates")
    return out


_VERIFIED_MES_CHANNELS: dict[str, dict[str, str]] = {
    "MES_G_SIGMA": {
        "target_sector": "Sigma2",
        "target_invariant": "sigma_ab_sigma_ab_over_6H2",
        "frame": "registered MES fundamental-observer frame",
        "congruence": "geodesic",
        "normalization": "Sigma2_std",
        "perturbative_order": "linear almost-EGS",
    },
    "MES_G_OMEGA": {
        "target_sector": "W2",
        "target_invariant": "omega_ab_omega_ab_over_6H2",
        "frame": "registered MES fundamental-observer frame",
        "congruence": "geodesic",
        "normalization": "W2_std",
        "perturbative_order": "linear almost-EGS",
    },
}


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
    calibration_values: tuple[tuple[str, float], ...] = ()

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
        calibration_values: list[tuple[str, float]] = []
        for item in self.calibration_values:
            if not isinstance(item, (tuple, list)) or len(item) != 2:
                raise StatisticalFoundationError(
                    "calibration_values entries must be (name, value) pairs"
                )
            name = _required_text(item[0], "calibration_values.name")
            value = _finite_nonnegative(item[1], f"calibration_values.{name}")
            calibration_values.append((name, value))
        if len({name for name, _ in calibration_values}) != len(
            calibration_values
        ):
            raise StatisticalFoundationError(
                "calibration_values must not contain duplicate names"
            )
        object.__setattr__(self, "calibration_values", tuple(calibration_values))

        if self.status is AnchorStatus.NO_MES_ANCHOR:
            if self.value is not None:
                raise StatisticalFoundationError(
                    "NO_MES_ANCHOR must carry value=None"
                )
        elif self.status is AnchorStatus.VERIFIED:
            object.__setattr__(
                self, "value", _finite_positive(self.value, "value")
            )
        else:
            object.__setattr__(
                self, "value", _finite_nonnegative(self.value, "value")
            )

        if (
            self.status is AnchorStatus.VERIFIED
            and self.authority_kind is AnchorAuthorityKind.MES
        ):
            registered = _VERIFIED_MES_CHANNELS.get(self.branch)
            if registered is None:
                raise StatisticalFoundationError(
                    "verified MES anchors require a registered geodesic branch"
                )
            mismatches = tuple(
                name
                for name, expected in registered.items()
                if getattr(self, name) != expected
            )
            if mismatches:
                raise StatisticalFoundationError(
                    "verified MES anchor metadata does not match the registered "
                    f"branch: {', '.join(mismatches)}"
                )
            calibration = dict(self.calibration_values)
            if set(calibration) != {"eps1", "eps2", "eps3"}:
                raise StatisticalFoundationError(
                    "verified MES anchors require exact eps1/eps2/eps3 "
                    "calibration values"
                )
            try:
                validate_hierarchy_strict(
                    str(calibration["eps1"]),
                    str(calibration["eps2"]),
                    str(calibration["eps3"]),
                )
            except MesAuthorityError as exc:
                raise StatisticalFoundationError(
                    "verified MES anchor calibration violates the registered "
                    "strict geodesic hierarchy"
                ) from exc
            expected_value = 1.5 * _branch_bound(
                self.branch,
                calibration["eps1"],
                calibration["eps2"],
                calibration["eps3"],
            ) ** 2
            if self.value != expected_value:
                raise StatisticalFoundationError(
                    "verified MES anchor value does not match its registered "
                    "branch and calibration values"
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
        if self.status is not AnchorStatus.VERIFIED:
            return False
        if self.value is None or self.value <= 0.0:
            return False
        if self.authority_kind is not AnchorAuthorityKind.MES:
            return True
        registered = _VERIFIED_MES_CHANNELS.get(self.branch)
        return registered is not None and all(
            getattr(self, name) == expected
            for name, expected in registered.items()
        )


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
            calibration_values=(
                ("eps1", eps1),
                ("eps2", eps2),
                ("eps3", eps3),
            ),
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
            calibration_values=(
                ("eps1", eps1),
                ("eps2", eps2),
                ("eps3", eps3),
            ),
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


def _numeric_tuple(
    values: Sequence[object], field_name: str, *, length: int | None = None
) -> tuple[float, ...]:
    if isinstance(values, (str, bytes)):
        raise StatisticalFoundationError(f"{field_name} must be a numeric sequence")
    out = tuple(
        _finite_real(value, f"{field_name}[{index}]")
        for index, value in enumerate(values)
    )
    if length is not None and len(out) != length:
        raise StatisticalFoundationError(
            f"{field_name} must have length {length}, got {len(out)}"
        )
    if not out:
        raise StatisticalFoundationError(f"{field_name} must not be empty")
    return out


@dataclass(frozen=True)
class DepartureState:
    """Immutable signed irreducible state, separate from every anchor.

    Components use an explicitly named basis and units.  This type deliberately
    has no automatic conversion to a family, morphology, probability or MES
    stress.  A caller that needs the non-negative budget summaries must provide
    their already registered normalization through :class:`SummaryDepartureState`.
    """

    sigma_ab: tuple[float, ...]
    omega_a: tuple[float, ...]
    beta_a: tuple[float, ...]
    delta_omega_k: float
    frame: str
    congruence: str
    epoch_window: str
    averaging_scale: str
    basis: str
    units: str
    parity: str
    perturbative_order: str

    def __post_init__(self) -> None:
        object.__setattr__(
            self, "sigma_ab", _numeric_tuple(self.sigma_ab, "sigma_ab", length=5)
        )
        object.__setattr__(
            self, "omega_a", _numeric_tuple(self.omega_a, "omega_a", length=3)
        )
        object.__setattr__(
            self, "beta_a", _numeric_tuple(self.beta_a, "beta_a", length=3)
        )
        object.__setattr__(
            self,
            "delta_omega_k",
            _finite_real(self.delta_omega_k, "delta_omega_k"),
        )
        for name in (
            "frame",
            "congruence",
            "epoch_window",
            "averaging_scale",
            "basis",
            "units",
            "parity",
            "perturbative_order",
        ):
            _required_text(getattr(self, name), name)

    @property
    def vector(self) -> tuple[float, ...]:
        return (*self.sigma_ab, *self.omega_a, *self.beta_a, self.delta_omega_k)


@dataclass(frozen=True)
class SummaryDepartureState:
    """Non-negative sector summaries plus the signed curvature coordinate."""

    sigma2: float
    w2: float
    omega_tilt: float
    delta_omega_k: float
    normalization: str
    source_state_id: str

    def __post_init__(self) -> None:
        for name in ("sigma2", "w2", "omega_tilt"):
            object.__setattr__(
                self, name, _finite_nonnegative(getattr(self, name), name)
            )
        object.__setattr__(
            self,
            "delta_omega_k",
            _finite_real(self.delta_omega_k, "delta_omega_k"),
        )
        _required_text(self.normalization, "normalization")
        _required_text(self.source_state_id, "source_state_id")

    @property
    def x_C(self) -> float:
        """Exact legacy signed Gauss/Friedmann coordinate in float form."""
        return self.sigma2 - self.w2 + self.omega_tilt + self.delta_omega_k


@dataclass(frozen=True)
class SectorAlias:
    alias: str
    canonical: str
    caveat: str

    def __post_init__(self) -> None:
        _required_text(self.alias, "alias")
        _required_text(self.canonical, "canonical")
        _required_text(self.caveat, "caveat")
        if self.alias == self.canonical:
            raise StatisticalFoundationError("alias must differ from canonical")


W2_V2_ALIAS = SectorAlias(
    alias="V2",
    canonical="W2",
    caveat="normalized vorticity alias only; never identify it with Nilsson W_N2",
)


@dataclass(frozen=True)
class ScalarRange:
    lower: float
    upper: float

    def __post_init__(self) -> None:
        if isinstance(self.lower, bool) or isinstance(self.upper, bool):
            raise StatisticalFoundationError(
                "ScalarRange endpoints must not be boolean"
            )
        lower = float(self.lower)
        upper = float(self.upper)
        if math.isnan(lower) or math.isnan(upper) or lower > upper:
            raise StatisticalFoundationError(
                "ScalarRange requires ordered non-NaN endpoints"
            )
        object.__setattr__(self, "lower", lower)
        object.__setattr__(self, "upper", upper)

    @property
    def is_point(self) -> bool:
        return self.lower == self.upper

    def separated_from_zero(self, *, atol: float, rtol: float) -> bool:
        atol = _finite_nonnegative(atol, "atol")
        rtol = _finite_nonnegative(rtol, "rtol")
        scale = max(abs(self.lower), abs(self.upper), 1.0)
        tolerance = atol + rtol * scale
        return self.lower > tolerance or self.upper < -tolerance


@dataclass(frozen=True)
class IdentifiedDepartureSet:
    """Finite-generator feasible set with explicit recession and null kinds."""

    coordinate_names: tuple[str, ...]
    vertices: tuple[tuple[float, ...], ...]
    recession_directions: tuple[tuple[float, ...], ...]
    null_kinds: tuple[NullKind, ...]
    assumptions: tuple[str, ...]
    status: IdentificationStatus
    representation: str = "VERTEX_RECESSION_V1"

    def __post_init__(self) -> None:
        if not isinstance(self.status, IdentificationStatus):
            raise StatisticalFoundationError(
                "status must be an IdentificationStatus"
            )
        names = _text_tuple(self.coordinate_names, "coordinate_names")
        object.__setattr__(self, "coordinate_names", names)
        dimension = len(names)
        vertices = tuple(
            _numeric_tuple(row, "vertices", length=dimension)
            for row in self.vertices
        )
        recession = tuple(
            _numeric_tuple(row, "recession_directions", length=dimension)
            for row in self.recession_directions
        )
        if any(all(value == 0.0 for value in row) for row in recession):
            raise StatisticalFoundationError(
                "recession directions must be non-zero"
            )
        if self.status is IdentificationStatus.EMPTY:
            if vertices or recession:
                raise StatisticalFoundationError(
                    "EMPTY identified sets must not carry generators"
                )
        elif not vertices:
            raise StatisticalFoundationError(
                "non-empty identified sets require at least one vertex"
            )
        if self.status is IdentificationStatus.POINT_IDENTIFIED and (
            len(set(vertices)) != 1 or recession
        ):
            raise StatisticalFoundationError(
                "POINT_IDENTIFIED requires one unique point and no recession"
            )
        if len(self.null_kinds) != dimension:
            raise StatisticalFoundationError(
                "null_kinds must match the coordinate dimension"
            )
        if any(not isinstance(kind, NullKind) for kind in self.null_kinds):
            raise StatisticalFoundationError(
                "null_kinds entries must be NullKind values"
            )
        object.__setattr__(self, "vertices", vertices)
        object.__setattr__(self, "recession_directions", recession)
        object.__setattr__(
            self, "assumptions", _text_tuple(self.assumptions, "assumptions")
        )
        _required_text(self.representation, "representation")

    @property
    def dimension(self) -> int:
        return len(self.coordinate_names)

    def support(self, direction: Sequence[object], *, tol: float = 1e-12) -> float:
        if self.status is IdentificationStatus.EMPTY:
            raise StatisticalFoundationError("EMPTY set has no support function")
        vector = _numeric_tuple(direction, "direction", length=self.dimension)
        tol = _finite_nonnegative(tol, "tol")
        if any(
            sum(a * b for a, b in zip(vector, ray)) > tol
            for ray in self.recession_directions
        ):
            return math.inf
        return max(
            sum(a * b for a, b in zip(vector, vertex))
            for vertex in self.vertices
        )

    def interval(self, direction: Sequence[object]) -> ScalarRange:
        vector = _numeric_tuple(direction, "direction", length=self.dimension)
        upper = self.support(vector)
        lower_support = self.support(tuple(-value for value in vector))
        lower = -lower_support
        return ScalarRange(lower=lower, upper=upper)


@dataclass(frozen=True)
class SectorStress:
    sector: str
    status: StressStatus
    anchor_id: str | None
    saturation: ScalarRange | None
    exceedance: ScalarRange | None
    allowed_use: tuple[str, ...]
    rationale: str

    def __post_init__(self) -> None:
        _required_text(self.sector, "sector")
        if not isinstance(self.status, StressStatus):
            raise StatisticalFoundationError("status must be a StressStatus")
        if self.status is StressStatus.DEFINED:
            if self.saturation is None or self.exceedance is None:
                raise StatisticalFoundationError(
                    "DEFINED stress requires saturation and exceedance ranges"
                )
            _required_text(self.anchor_id, "anchor_id")
        elif self.saturation is not None or self.exceedance is not None:
            raise StatisticalFoundationError(
                "undefined stress must not carry numeric ranges"
            )
        object.__setattr__(
            self, "allowed_use", _text_tuple(self.allowed_use, "allowed_use")
        )
        _required_text(self.rationale, "rationale")


@dataclass(frozen=True)
class AnchorStressReport:
    stresses: tuple[SectorStress, ...]
    conditioning: AnchorConditioning
    allowed_use: tuple[str, ...] = (
        "one-way channel-matched anchor stress",
    )
    forbidden_use: tuple[str, ...] = (
        "FLRW converse",
        "distance",
        "occupancy",
        "family identification",
    )

    def __post_init__(self) -> None:
        if not self.stresses:
            raise StatisticalFoundationError("stresses must not be empty")
        if len({stress.sector for stress in self.stresses}) != len(self.stresses):
            raise StatisticalFoundationError("stress sectors must be unique")
        if not isinstance(self.conditioning, AnchorConditioning):
            raise StatisticalFoundationError(
                "conditioning must be an AnchorConditioning"
            )
        object.__setattr__(
            self, "allowed_use", _text_tuple(self.allowed_use, "allowed_use")
        )
        object.__setattr__(
            self, "forbidden_use", _text_tuple(self.forbidden_use, "forbidden_use")
        )

    @property
    def saturation_vector(self) -> tuple[ScalarRange | None, ...]:
        return tuple(stress.saturation for stress in self.stresses)


def evaluate_sector_stress(
    *,
    sector: str,
    numerator: ScalarRange | None,
    numerator_channel_key: tuple[str, ...] | None,
    anchor: MESAnchorSpec | None,
) -> SectorStress:
    """Construct one typed stress without cross-channel scalar synthesis."""
    sector = _required_text(sector, "sector")
    if numerator is None or numerator_channel_key is None:
        return SectorStress(
            sector=sector,
            status=StressStatus.NUMERATOR_UNIDENTIFIED,
            anchor_id=None if anchor is None else anchor.anchor_id,
            saturation=None,
            exceedance=None,
            allowed_use=("partial-identification status",),
            rationale="numerator is not point/set identified in this channel",
        )
    if anchor is None or not anchor.normalization_allowed:
        return SectorStress(
            sector=sector,
            status=StressStatus.ANCHOR_UNAVAILABLE,
            anchor_id=None if anchor is None else anchor.anchor_id,
            saturation=None,
            exceedance=None,
            allowed_use=("anchor availability report",),
            rationale="no verified numeric anchor is available",
        )
    if tuple(numerator_channel_key) != anchor.channel_key:
        return SectorStress(
            sector=sector,
            status=StressStatus.CHANNEL_MISMATCH,
            anchor_id=anchor.anchor_id,
            saturation=None,
            exceedance=None,
            allowed_use=("channel mismatch report",),
            rationale="numerator and anchor frame/order/branch identities differ",
        )
    if numerator.lower < 0.0:
        return SectorStress(
            sector=sector,
            status=StressStatus.NUMERATOR_UNIDENTIFIED,
            anchor_id=anchor.anchor_id,
            saturation=None,
            exceedance=None,
            allowed_use=("partial-identification status",),
            rationale="non-negative invariant numerator has a negative feasible bound",
        )
    assert anchor.value is not None
    saturation = ScalarRange(
        numerator.lower / anchor.value,
        numerator.upper / anchor.value,
    )
    exceedance = ScalarRange(
        max(saturation.lower - 1.0, 0.0),
        max(saturation.upper - 1.0, 0.0),
    )
    return SectorStress(
        sector=sector,
        status=StressStatus.DEFINED,
        anchor_id=anchor.anchor_id,
        saturation=saturation,
        exceedance=exceedance,
        allowed_use=("one-way linear-premise stress",),
        rationale=(
            "s>1 is evidence against the registered premises; s<=1 proves no "
            "converse"
        ),
    )


@dataclass(frozen=True)
class BudgetRadiusResult:
    radius_sq: tuple[float, ...]
    rank: int
    null_residual: tuple[float, ...]
    status: BudgetRadiusStatus

    def __post_init__(self) -> None:
        object.__setattr__(
            self, "radius_sq", _numeric_tuple(self.radius_sq, "radius_sq")
        )
        object.__setattr__(
            self,
            "null_residual",
            _numeric_tuple(self.null_residual, "null_residual"),
        )
        if len(self.radius_sq) != len(self.null_residual):
            raise StatisticalFoundationError(
                "radius_sq and null_residual must have equal length"
            )
        if isinstance(self.rank, bool) or not isinstance(self.rank, int) or self.rank < 0:
            raise StatisticalFoundationError("rank must be a non-negative integer")
        if not isinstance(self.status, BudgetRadiusStatus):
            raise StatisticalFoundationError(
                "status must be a BudgetRadiusStatus"
            )


@dataclass(frozen=True)
class DiagnosticScalarReport:
    name: str
    value_range: ScalarRange | None
    status: str
    null_calibration: str
    bin_metadata: tuple[tuple[str, str], ...] = ()

    def __post_init__(self) -> None:
        _required_text(self.name, "name")
        _required_text(self.status, "status")
        _required_text(self.null_calibration, "null_calibration")
        metadata = tuple(
            (
                _required_text(key, "bin_metadata.key"),
                _required_text(value, "bin_metadata.value"),
            )
            for key, value in self.bin_metadata
        )
        if len({key for key, _ in metadata}) != len(metadata):
            raise StatisticalFoundationError("bin_metadata keys must be unique")
        object.__setattr__(self, "bin_metadata", metadata)


@dataclass(frozen=True)
class LegacyProjectionReport:
    """BC1 wrapper around unchanged historical x_C/Q/F/Pi/G_F values."""

    x_C: DiagnosticScalarReport
    Q: DiagnosticScalarReport | None = None
    F: DiagnosticScalarReport | None = None
    F_C_plus_minus: DiagnosticScalarReport | None = None
    Pi: DiagnosticScalarReport | None = None
    G_F: DiagnosticScalarReport | None = None
    classification: str = BC1_LEGACY_PROJECTION
    representation_policy: str = BC2_NO_REPRESENTATION_PROMOTION
    allowed_use: tuple[str, ...] = (
        "historical reproduction",
        "signed budget-coordinate reporting",
    )
    forbidden_use: tuple[str, ...] = (
        "departure distance",
        "identified estimand",
        "probability",
        "occupancy",
        "evidence",
        "claim-tier promotion",
    )

    def __post_init__(self) -> None:
        if self.x_C.name != "x_C":
            raise StatisticalFoundationError("x_C report must be named x_C")
        if self.classification != BC1_LEGACY_PROJECTION:
            raise StatisticalFoundationError("legacy classification is immutable")
        if self.representation_policy != BC2_NO_REPRESENTATION_PROMOTION:
            raise StatisticalFoundationError(
                "representation policy must prohibit claim promotion"
            )
        object.__setattr__(
            self, "allowed_use", _text_tuple(self.allowed_use, "allowed_use")
        )
        object.__setattr__(
            self, "forbidden_use", _text_tuple(self.forbidden_use, "forbidden_use")
        )


def im_critical_value(delta: float, se: float, alpha: float = 0.05) -> float:
    """Canonical Imbens-Manski critical value with one strict domain."""
    delta = _finite_nonnegative(delta, "delta")
    se = _finite_positive(se, "se")
    alpha = _finite_real(alpha, "alpha")
    if not 0.0 < alpha < 1.0:
        raise StatisticalFoundationError("alpha must lie in (0, 1)")
    normal = NormalDist()
    ratio = delta / se
    target = 1.0 - alpha

    def residual(value: float) -> float:
        return normal.cdf(value + ratio) - normal.cdf(-value) - target

    lower = normal.inv_cdf(1.0 - alpha)
    upper = normal.inv_cdf(1.0 - alpha / 2.0)
    for _ in range(100):
        midpoint = 0.5 * (lower + upper)
        if residual(midpoint) >= 0.0:
            upper = midpoint
        else:
            lower = midpoint
    return 0.5 * (lower + upper)


__all__ = [
    "AnchorAuthorityKind",
    "AnchorConditioning",
    "AnchorStatus",
    "AnchorStressReport",
    "BC1_LEGACY_PROJECTION",
    "BC2_NO_REPRESENTATION_PROMOTION",
    "BudgetRadiusResult",
    "BudgetRadiusStatus",
    "DepartureState",
    "DiagnosticScalarReport",
    "IdentificationStatus",
    "IdentifiedDepartureSet",
    "LegacyProjectionReport",
    "MESAnchorSpec",
    "NullKind",
    "ScalarRange",
    "SectorAlias",
    "SectorStress",
    "StressStatus",
    "SummaryDepartureState",
    "W2_V2_ALIAS",
    "StatisticalFoundationError",
    "evaluate_sector_stress",
    "im_critical_value",
    "quarantined_shear_anchors",
    "registered_geodesic_mes_anchors",
]
