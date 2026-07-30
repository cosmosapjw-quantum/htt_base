"""Typed conditional-exceedance contracts for the vector/tensor ``Pi`` lane.

The central rule is type separation:

* an empirical or matched-null sampling law is MIO-owned;
* an explicit posterior sampling law is HTT-owned;
* a profile-likelihood objective is an objective, not a probability law; and
* an optimizer point is never accepted where draws are required.

The module evaluates strict-tail probabilities only from sealed
``SamplingDraws``.  Missing laws, uncalibrated posterior inputs, unbounded
identified sets, and uncertified partial-identification envelopes return typed
refusals with no numeric probability.
"""

from __future__ import annotations

from dataclasses import InitVar, dataclass, field
from enum import Enum
import hashlib
import json
import math
from numbers import Integral
from numbers import Real
from typing import Mapping, Sequence

from common.statistical_foundations import (
    IdentificationStatus,
    IdentifiedDepartureSet,
)


class ConditionalExceedanceError(ValueError):
    """Raised when a conditional-exceedance contract is malformed."""


class _StringEnum(str, Enum):
    def __str__(self) -> str:
        return self.value


class SamplingLaw(_StringEnum):
    FIXED_INJECTION_MOCK = "FIXED_INJECTION_MOCK"
    BOOTSTRAP_RESAMPLING = "BOOTSTRAP_RESAMPLING"
    PROFILE_LIKELIHOOD = "PROFILE_LIKELIHOOD"
    POSTERIOR_PREDICTIVE = "POSTERIOR_PREDICTIVE"
    OBSERVATIONAL_POSTERIOR_PUSHFORWARD = (
        "OBSERVATIONAL_POSTERIOR_PUSHFORWARD"
    )


class ConditioningSource(_StringEnum):
    INJECTED = "INJECTED"
    EXTERNALLY_ESTIMATED = "EXTERNALLY_ESTIMATED"
    PROFILED = "PROFILED"
    POSTERIOR = "POSTERIOR"
    IDENTIFIED_SET = "IDENTIFIED_SET"


class ExceedanceLane(_StringEnum):
    MIO_NULL = "MIO_NULL"
    HTT_OBJECTIVE = "HTT_OBJECTIVE"
    HTT_POSTERIOR = "HTT_POSTERIOR"


class ExceedanceStatus(_StringEnum):
    DEFINED_POINT = "DEFINED_POINT"
    DEFINED_ENVELOPE = "DEFINED_ENVELOPE"
    MISSING_PROBABILITY_LAW = "MISSING_PROBABILITY_LAW"
    INSUFFICIENT_DRAWS = "INSUFFICIENT_DRAWS"
    POSTERIOR_CALIBRATION_REQUIRED = "POSTERIOR_CALIBRATION_REQUIRED"
    OPTIMIZER_REQUIRED = "OPTIMIZER_REQUIRED"
    EMPTY_IDENTIFIED_SET = "EMPTY_IDENTIFIED_SET"


class PosteriorCalibrationStatus(_StringEnum):
    PASSED = "PASSED"
    FAILED = "FAILED"
    NOT_EVALUATED = "NOT_EVALUATED"


class EnvelopeCertificate(_StringEnum):
    MONOTONE = "MONOTONE"
    UPPER_QUASI_CONVEX_LOWER_QUASI_CONCAVE = (
        "UPPER_QUASI_CONVEX_LOWER_QUASI_CONCAVE"
    )
    UPPER_QUASI_CONVEX_ONLY = "UPPER_QUASI_CONVEX_ONLY"
    UNVERIFIED = "UNVERIFIED"


CONDITIONAL_EXCEEDANCE_CLAIM_CEILING = "diagnostic_only"
CONDITIONAL_EXCEEDANCE_ALLOWED_USE = (
    "matched-null or empirical conditional exceedance diagnostic",
    "explicit model-conditional posterior exceedance diagnostic",
    "partial-identification exceedance envelope",
    "finite-draw uncertainty report",
)
CONDITIONAL_EXCEEDANCE_FORBIDDEN_USE = (
    "truth probability",
    "optimizer output relabelled as a sample or posterior",
    "MIO posterior, likelihood, Bayes factor, or evidence",
    "native solver validation or native morphology atlas",
    "geometry detection or Bianchi family identification",
)
_LAW_TOKEN = object()
_DRAWS_TOKEN = object()
_OBJECTIVE_TOKEN = object()
_CALIBRATION_TOKEN = object()
_COVERAGE_TOKEN = object()
_PROFILE_TOKEN = object()
_NULL_TOKEN = object()
_POSTERIOR_TOKEN = object()


def _text(value: object, name: str) -> str:
    if not isinstance(value, str) or not value.strip() or value != value.strip():
        raise ConditionalExceedanceError(
            f"{name} must be non-empty trimmed text"
        )
    return value


def _texts(
    values: Sequence[object],
    name: str,
    *,
    empty_ok: bool = False,
) -> tuple[str, ...]:
    if isinstance(values, (str, bytes)):
        raise ConditionalExceedanceError(
            f"{name} must be a sequence of text"
        )
    out = tuple(_text(value, name) for value in values)
    if not out and not empty_ok:
        raise ConditionalExceedanceError(f"{name} must not be empty")
    if len(out) != len(set(out)):
        raise ConditionalExceedanceError(
            f"{name} must not contain duplicates"
        )
    return out


def _real(value: object, name: str) -> float:
    if isinstance(value, bool) or not isinstance(value, Real):
        raise ConditionalExceedanceError(f"{name} must be real")
    out = float(value)
    if not math.isfinite(out):
        raise ConditionalExceedanceError(f"{name} must be finite")
    return out


def _probability(value: object, name: str) -> float:
    out = _real(value, name)
    if not 0.0 <= out <= 1.0:
        raise ConditionalExceedanceError(f"{name} must be in [0, 1]")
    return out


def _enum(value: object, enum_type: type[_StringEnum], name: str) -> _StringEnum:
    if isinstance(value, enum_type):
        return value
    try:
        return enum_type(str(value))
    except ValueError as exc:
        raise ConditionalExceedanceError(
            f"{name} must use the registered {enum_type.__name__} vocabulary"
        ) from exc


def _sha256_payload(payload: object) -> str:
    encoded = json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
    ).encode("ascii")
    return f"sha256:{hashlib.sha256(encoded).hexdigest()}"


def _thresholds(values: Sequence[object]) -> tuple[float, ...]:
    if isinstance(values, (str, bytes)):
        raise ConditionalExceedanceError(
            "thresholds must be a numeric sequence"
        )
    out = tuple(
        _real(value, f"thresholds[{index}]")
        for index, value in enumerate(values)
    )
    if not out or tuple(sorted(set(out))) != out:
        raise ConditionalExceedanceError(
            "thresholds must be non-empty, strictly increasing, and unique"
        )
    return out


def _nonincreasing(values: Sequence[float]) -> bool:
    return all(left >= right for left, right in zip(values, values[1:]))


def _assert_sealed(
    payload: object,
    seal: str,
    *,
    name: str,
) -> None:
    if _sha256_payload(payload) != seal:
        raise ConditionalExceedanceError(
            f"{name} identity drifted after construction"
        )


@dataclass(frozen=True)
class SamplingLawSpec:
    """Declared law and owner lane; profile likelihood is non-probabilistic."""

    law_id: str
    sampling_law: SamplingLaw
    conditioning_source: ConditioningSource
    lane: ExceedanceLane
    source_identity: str
    covariance_id: str | None
    transfer_source: str
    assumptions: tuple[str, ...]
    probability_eligible: bool
    _construction_token: InitVar[object] = None
    _identity_seal: str = field(init=False, repr=False, compare=False)

    def __post_init__(self, _construction_token: object) -> None:
        if _construction_token is not _LAW_TOKEN:
            raise ConditionalExceedanceError(
                "SamplingLawSpec must be factory-built"
            )
        _text(self.law_id, "law_id")
        if type(self.sampling_law) is not SamplingLaw:
            raise ConditionalExceedanceError(
                "sampling_law must use the registered vocabulary"
            )
        if type(self.conditioning_source) is not ConditioningSource:
            raise ConditionalExceedanceError(
                "conditioning_source must use the registered vocabulary"
            )
        if type(self.lane) is not ExceedanceLane:
            raise ConditionalExceedanceError(
                "lane must use the registered vocabulary"
            )
        _text(self.source_identity, "source_identity")
        if self.covariance_id is not None:
            _text(self.covariance_id, "covariance_id")
        _text(self.transfer_source, "transfer_source")
        assumptions = _texts(self.assumptions, "assumptions")
        object.__setattr__(self, "assumptions", assumptions)
        object.__setattr__(
            self,
            "_identity_seal",
            _sha256_payload(self._payload_unchecked()),
        )

    @property
    def content_id(self) -> str:
        self._assert_identity_sealed()
        return self._identity_seal

    def _payload_unchecked(self) -> dict[str, object]:
        return {
            "assumptions": list(self.assumptions),
            "conditioning_source": self.conditioning_source.value,
            "covariance_id": self.covariance_id,
            "lane": self.lane.value,
            "law_id": self.law_id,
            "probability_eligible": self.probability_eligible,
            "sampling_law": self.sampling_law.value,
            "schema": "HTT_SAMPLING_LAW_SPEC_V1",
            "source_identity": self.source_identity,
            "transfer_source": self.transfer_source,
        }

    def _assert_identity_sealed(self) -> None:
        _assert_sealed(
            self._payload_unchecked(),
            self._identity_seal,
            name="sampling law",
        )

    def as_payload(self) -> dict[str, object]:
        self._assert_identity_sealed()
        return {
            **self._payload_unchecked(),
            "content_id": self._identity_seal,
        }


def build_sampling_law_spec(
    *,
    law_id: str,
    sampling_law: SamplingLaw | str,
    conditioning_source: ConditioningSource | str,
    lane: ExceedanceLane | str,
    source_identity: str,
    covariance_id: str | None,
    transfer_source: str,
    assumptions: Sequence[str],
) -> SamplingLawSpec:
    law = _enum(sampling_law, SamplingLaw, "sampling_law")
    source = _enum(
        conditioning_source,
        ConditioningSource,
        "conditioning_source",
    )
    owner_lane = _enum(lane, ExceedanceLane, "lane")
    expected_lane = {
        SamplingLaw.FIXED_INJECTION_MOCK: ExceedanceLane.MIO_NULL,
        SamplingLaw.BOOTSTRAP_RESAMPLING: ExceedanceLane.MIO_NULL,
        SamplingLaw.PROFILE_LIKELIHOOD: ExceedanceLane.HTT_OBJECTIVE,
        SamplingLaw.POSTERIOR_PREDICTIVE: ExceedanceLane.HTT_POSTERIOR,
        SamplingLaw.OBSERVATIONAL_POSTERIOR_PUSHFORWARD: (
            ExceedanceLane.HTT_POSTERIOR
        ),
    }[law]
    if owner_lane is not expected_lane:
        raise ConditionalExceedanceError(
            f"{law.value} belongs to {expected_lane.value}, not "
            f"{owner_lane.value}"
        )
    allowed_conditioning = {
        SamplingLaw.FIXED_INJECTION_MOCK: {
            ConditioningSource.INJECTED,
            ConditioningSource.EXTERNALLY_ESTIMATED,
            ConditioningSource.IDENTIFIED_SET,
        },
        SamplingLaw.BOOTSTRAP_RESAMPLING: {
            ConditioningSource.EXTERNALLY_ESTIMATED,
            ConditioningSource.IDENTIFIED_SET,
        },
        SamplingLaw.PROFILE_LIKELIHOOD: {
            ConditioningSource.PROFILED,
            ConditioningSource.IDENTIFIED_SET,
        },
        SamplingLaw.POSTERIOR_PREDICTIVE: {
            ConditioningSource.POSTERIOR,
            ConditioningSource.IDENTIFIED_SET,
        },
        SamplingLaw.OBSERVATIONAL_POSTERIOR_PUSHFORWARD: {
            ConditioningSource.POSTERIOR,
            ConditioningSource.IDENTIFIED_SET,
        },
    }[law]
    if source not in allowed_conditioning:
        raise ConditionalExceedanceError(
            "conditioning_source is incompatible with the declared law"
        )
    return SamplingLawSpec(
        law_id=law_id,
        sampling_law=law,  # type: ignore[arg-type]
        conditioning_source=source,  # type: ignore[arg-type]
        lane=owner_lane,  # type: ignore[arg-type]
        source_identity=source_identity,
        covariance_id=covariance_id,
        transfer_source=transfer_source,
        assumptions=tuple(assumptions),
        probability_eligible=law is not SamplingLaw.PROFILE_LIKELIHOOD,
        _construction_token=_LAW_TOKEN,
    )


@dataclass(frozen=True)
class SamplingDraws:
    draws_id: str
    law_spec_id: str
    sampling_law: SamplingLaw
    conditioning_source: ConditioningSource
    lane: ExceedanceLane
    values: tuple[float, ...]
    source_artifact_id: str
    sample_unit: str
    _construction_token: InitVar[object] = None
    _identity_seal: str = field(init=False, repr=False, compare=False)

    def __post_init__(self, _construction_token: object) -> None:
        if _construction_token is not _DRAWS_TOKEN:
            raise ConditionalExceedanceError(
                "SamplingDraws must be factory-built"
            )
        for name in (
            "draws_id",
            "law_spec_id",
            "source_artifact_id",
            "sample_unit",
        ):
            _text(getattr(self, name), name)
        if (
            type(self.sampling_law) is not SamplingLaw
            or type(self.conditioning_source) is not ConditioningSource
            or type(self.lane) is not ExceedanceLane
        ):
            raise ConditionalExceedanceError(
                "draw law fields must use registered vocabularies"
            )
        values = tuple(
            _real(value, f"values[{index}]")
            for index, value in enumerate(self.values)
        )
        object.__setattr__(self, "values", values)
        object.__setattr__(
            self,
            "_identity_seal",
            _sha256_payload(self._payload_unchecked()),
        )

    @property
    def content_id(self) -> str:
        self._assert_identity_sealed()
        return self._identity_seal

    def _payload_unchecked(self) -> dict[str, object]:
        return {
            "conditioning_source": self.conditioning_source.value,
            "draws_id": self.draws_id,
            "lane": self.lane.value,
            "law_spec_id": self.law_spec_id,
            "sample_unit": self.sample_unit,
            "sampling_law": self.sampling_law.value,
            "schema": "HTT_SAMPLING_DRAWS_V1",
            "source_artifact_id": self.source_artifact_id,
            "values_hex": [value.hex() for value in self.values],
        }

    def _assert_identity_sealed(self) -> None:
        _assert_sealed(
            self._payload_unchecked(),
            self._identity_seal,
            name="sampling draws",
        )

    def as_payload(self) -> dict[str, object]:
        self._assert_identity_sealed()
        return {
            **self._payload_unchecked(),
            "content_id": self._identity_seal,
        }


def build_sampling_draws(
    *,
    draws_id: str,
    law: SamplingLawSpec,
    values: Sequence[object],
    source_artifact_id: str,
    sample_unit: str,
) -> SamplingDraws:
    if type(law) is not SamplingLawSpec:
        raise TypeError("law must be an exact SamplingLawSpec")
    law.as_payload()
    if not law.probability_eligible:
        raise ConditionalExceedanceError(
            "profile-likelihood objectives are not sampling draws"
        )
    return SamplingDraws(
        draws_id=draws_id,
        law_spec_id=law.content_id,
        sampling_law=law.sampling_law,
        conditioning_source=law.conditioning_source,
        lane=law.lane,
        values=tuple(_real(value, "values") for value in values),
        source_artifact_id=source_artifact_id,
        sample_unit=sample_unit,
        _construction_token=_DRAWS_TOKEN,
    )


@dataclass(frozen=True)
class LikelihoodObjective:
    """HTT objective surface. It deliberately has no draw/probability field."""

    objective_id: str
    law_spec_id: str
    coordinate_names: tuple[str, ...]
    coordinates: tuple[tuple[float, ...], ...]
    objective_values: tuple[float, ...]
    optimizer_point: tuple[float, ...] | None
    source_artifact_id: str
    lane: ExceedanceLane = ExceedanceLane.HTT_OBJECTIVE
    _construction_token: InitVar[object] = None
    _identity_seal: str = field(init=False, repr=False, compare=False)

    def __post_init__(self, _construction_token: object) -> None:
        if _construction_token is not _OBJECTIVE_TOKEN:
            raise ConditionalExceedanceError(
                "LikelihoodObjective must be factory-built"
            )
        for name in ("objective_id", "law_spec_id", "source_artifact_id"):
            _text(getattr(self, name), name)
        names = _texts(self.coordinate_names, "coordinate_names")
        dimension = len(names)
        coordinates = tuple(
            tuple(
                _real(value, f"coordinates[{row_index}]")
                for value in row
            )
            for row_index, row in enumerate(self.coordinates)
        )
        if (
            not coordinates
            or any(len(row) != dimension for row in coordinates)
        ):
            raise ConditionalExceedanceError(
                "coordinates must be a non-empty rectangular design"
            )
        objective_values = tuple(
            _real(value, f"objective_values[{index}]")
            for index, value in enumerate(self.objective_values)
        )
        if len(objective_values) != len(coordinates):
            raise ConditionalExceedanceError(
                "objective_values must align with coordinates"
            )
        optimizer = (
            None
            if self.optimizer_point is None
            else tuple(
                _real(value, "optimizer_point")
                for value in self.optimizer_point
            )
        )
        if optimizer is not None and len(optimizer) != dimension:
            raise ConditionalExceedanceError(
                "optimizer_point must match the coordinate dimension"
            )
        if self.lane is not ExceedanceLane.HTT_OBJECTIVE:
            raise ConditionalExceedanceError(
                "LikelihoodObjective is HTT-objective owned"
            )
        object.__setattr__(self, "coordinate_names", names)
        object.__setattr__(self, "coordinates", coordinates)
        object.__setattr__(self, "objective_values", objective_values)
        object.__setattr__(self, "optimizer_point", optimizer)
        object.__setattr__(
            self,
            "_identity_seal",
            _sha256_payload(self._payload_unchecked()),
        )

    @property
    def content_id(self) -> str:
        self._assert_identity_sealed()
        return self._identity_seal

    def _payload_unchecked(self) -> dict[str, object]:
        return {
            "coordinate_names": list(self.coordinate_names),
            "coordinates_hex": [
                [value.hex() for value in row] for row in self.coordinates
            ],
            "lane": self.lane.value,
            "law_spec_id": self.law_spec_id,
            "objective_id": self.objective_id,
            "objective_values_hex": [
                value.hex() for value in self.objective_values
            ],
            "optimizer_point_hex": (
                None
                if self.optimizer_point is None
                else [value.hex() for value in self.optimizer_point]
            ),
            "schema": "HTT_LIKELIHOOD_OBJECTIVE_V1",
            "source_artifact_id": self.source_artifact_id,
        }

    def _assert_identity_sealed(self) -> None:
        _assert_sealed(
            self._payload_unchecked(),
            self._identity_seal,
            name="likelihood objective",
        )

    def as_payload(self) -> dict[str, object]:
        self._assert_identity_sealed()
        return {
            **self._payload_unchecked(),
            "content_id": self._identity_seal,
        }


def build_likelihood_objective(
    *,
    objective_id: str,
    law: SamplingLawSpec,
    coordinate_names: Sequence[str],
    coordinates: Sequence[Sequence[object]],
    objective_values: Sequence[object],
    optimizer_point: Sequence[object] | None,
    source_artifact_id: str,
) -> LikelihoodObjective:
    if type(law) is not SamplingLawSpec:
        raise TypeError("law must be an exact SamplingLawSpec")
    law.as_payload()
    if (
        law.sampling_law is not SamplingLaw.PROFILE_LIKELIHOOD
        or law.lane is not ExceedanceLane.HTT_OBJECTIVE
    ):
        raise ConditionalExceedanceError(
            "LikelihoodObjective requires PROFILE_LIKELIHOOD"
        )
    return LikelihoodObjective(
        objective_id=objective_id,
        law_spec_id=law.content_id,
        coordinate_names=tuple(coordinate_names),
        coordinates=tuple(tuple(row) for row in coordinates),
        objective_values=tuple(objective_values),  # type: ignore[arg-type]
        optimizer_point=(
            None if optimizer_point is None else tuple(optimizer_point)
        ),  # type: ignore[arg-type]
        source_artifact_id=source_artifact_id,
        _construction_token=_OBJECTIVE_TOKEN,
    )


@dataclass(frozen=True)
class PosteriorCalibrationReport:
    calibration_id: str
    status: PosteriorCalibrationStatus
    method: str
    dgp_id: str
    seed_family: str
    tolerance: float
    diagnostic_values: tuple[float, ...]
    _construction_token: InitVar[object] = None
    _identity_seal: str = field(init=False, repr=False, compare=False)

    def __post_init__(self, _construction_token: object) -> None:
        if _construction_token is not _CALIBRATION_TOKEN:
            raise ConditionalExceedanceError(
                "PosteriorCalibrationReport must be factory-built"
            )
        for name in ("calibration_id", "method", "dgp_id", "seed_family"):
            _text(getattr(self, name), name)
        if type(self.status) is not PosteriorCalibrationStatus:
            raise ConditionalExceedanceError(
                "status must use PosteriorCalibrationStatus"
            )
        tolerance = _probability(self.tolerance, "tolerance")
        diagnostics = tuple(
            _real(value, f"diagnostic_values[{index}]")
            for index, value in enumerate(self.diagnostic_values)
        )
        if (
            self.status is PosteriorCalibrationStatus.PASSED
            and not diagnostics
        ):
            raise ConditionalExceedanceError(
                "passed calibration requires diagnostic values"
            )
        object.__setattr__(self, "tolerance", tolerance)
        object.__setattr__(self, "diagnostic_values", diagnostics)
        object.__setattr__(
            self,
            "_identity_seal",
            _sha256_payload(self._payload_unchecked()),
        )

    @property
    def content_id(self) -> str:
        self._assert_identity_sealed()
        return self._identity_seal

    def _payload_unchecked(self) -> dict[str, object]:
        return {
            "calibration_id": self.calibration_id,
            "dgp_id": self.dgp_id,
            "diagnostic_values_hex": [
                value.hex() for value in self.diagnostic_values
            ],
            "method": self.method,
            "schema": "HTT_POSTERIOR_CALIBRATION_REPORT_V1",
            "seed_family": self.seed_family,
            "status": self.status.value,
            "tolerance_hex": self.tolerance.hex(),
        }

    def _assert_identity_sealed(self) -> None:
        _assert_sealed(
            self._payload_unchecked(),
            self._identity_seal,
            name="posterior calibration",
        )

    def as_payload(self) -> dict[str, object]:
        self._assert_identity_sealed()
        return {
            **self._payload_unchecked(),
            "content_id": self._identity_seal,
        }


def build_posterior_calibration_report(
    *,
    calibration_id: str,
    status: PosteriorCalibrationStatus | str,
    method: str,
    dgp_id: str,
    seed_family: str,
    tolerance: object,
    diagnostic_values: Sequence[object],
) -> PosteriorCalibrationReport:
    resolved = _enum(
        status,
        PosteriorCalibrationStatus,
        "status",
    )
    return PosteriorCalibrationReport(
        calibration_id=calibration_id,
        status=resolved,  # type: ignore[arg-type]
        method=method,
        dgp_id=dgp_id,
        seed_family=seed_family,
        tolerance=_probability(tolerance, "tolerance"),
        diagnostic_values=tuple(diagnostic_values),  # type: ignore[arg-type]
        _construction_token=_CALIBRATION_TOKEN,
    )


@dataclass(frozen=True)
class FiniteNullCoverageReport:
    method: str
    alpha: float
    draw_count: int
    simultaneous_radius: float
    lower: tuple[float, ...]
    upper: tuple[float, ...]
    _construction_token: InitVar[object] = None
    _identity_seal: str = field(init=False, repr=False, compare=False)

    def __post_init__(self, _construction_token: object) -> None:
        if _construction_token is not _COVERAGE_TOKEN:
            raise ConditionalExceedanceError(
                "FiniteNullCoverageReport must be factory-built"
            )
        if self.method != "DKW_TWO_SIDED_SIMULTANEOUS":
            raise ConditionalExceedanceError("unknown coverage method")
        alpha = _probability(self.alpha, "alpha")
        if alpha in {0.0, 1.0}:
            raise ConditionalExceedanceError("alpha must be strictly in (0, 1)")
        if (
            isinstance(self.draw_count, bool)
            or not isinstance(self.draw_count, Integral)
            or self.draw_count < 2
        ):
            raise ConditionalExceedanceError(
                "draw_count must be an integer at least two"
            )
        radius = _probability(
            self.simultaneous_radius,
            "simultaneous_radius",
        )
        lower = tuple(_probability(value, "lower") for value in self.lower)
        upper = tuple(_probability(value, "upper") for value in self.upper)
        if len(lower) != len(upper) or any(
            lo > hi for lo, hi in zip(lower, upper, strict=True)
        ):
            raise ConditionalExceedanceError(
                "coverage bounds must align and be ordered"
            )
        object.__setattr__(self, "alpha", alpha)
        object.__setattr__(self, "simultaneous_radius", radius)
        object.__setattr__(self, "lower", lower)
        object.__setattr__(self, "upper", upper)
        object.__setattr__(
            self,
            "_identity_seal",
            _sha256_payload(self._payload_unchecked()),
        )

    def _payload_unchecked(self) -> dict[str, object]:
        return {
            "alpha": self.alpha,
            "draw_count": self.draw_count,
            "lower": list(self.lower),
            "method": self.method,
            "simultaneous_radius": self.simultaneous_radius,
            "upper": list(self.upper),
        }

    def _assert_identity_sealed(self) -> None:
        _assert_sealed(
            self._payload_unchecked(),
            self._identity_seal,
            name="finite-null coverage",
        )

    def as_payload(self) -> dict[str, object]:
        self._assert_identity_sealed()
        return {
            **self._payload_unchecked(),
            "content_id": self._identity_seal,
        }


@dataclass(frozen=True)
class ConditionalExceedanceProfile:
    profile_id: str
    functional_id: str
    thresholds: tuple[float, ...]
    lower: tuple[float, ...] | None
    upper: tuple[float, ...] | None
    point: tuple[float, ...] | None
    status: ExceedanceStatus
    sampling_law: SamplingLaw | None
    conditioning_source: ConditioningSource | None
    lane: ExceedanceLane | None
    law_spec_id: str | None
    draws_id: str | None
    conditioning_id: str
    covariance_id: str | None
    calibration_id: str | None
    identified_set_id: str | None
    refusal_reasons: tuple[str, ...]
    claim_ceiling: str = CONDITIONAL_EXCEEDANCE_CLAIM_CEILING
    allowed_use: tuple[str, ...] = CONDITIONAL_EXCEEDANCE_ALLOWED_USE
    forbidden_use: tuple[str, ...] = CONDITIONAL_EXCEEDANCE_FORBIDDEN_USE
    _construction_token: InitVar[object] = None
    _identity_seal: str = field(init=False, repr=False, compare=False)

    def __post_init__(self, _construction_token: object) -> None:
        if _construction_token is not _PROFILE_TOKEN:
            raise ConditionalExceedanceError(
                "ConditionalExceedanceProfile must be factory-built"
            )
        for name in ("profile_id", "functional_id", "conditioning_id"):
            _text(getattr(self, name), name)
        thresholds = _thresholds(self.thresholds)
        if type(self.status) is not ExceedanceStatus:
            raise ConditionalExceedanceError(
                "status must use ExceedanceStatus"
            )
        defined = self.status in {
            ExceedanceStatus.DEFINED_POINT,
            ExceedanceStatus.DEFINED_ENVELOPE,
        }
        numeric = (self.lower, self.upper, self.point)
        if defined:
            if self.lower is None or self.upper is None:
                raise ConditionalExceedanceError(
                    "defined profiles require lower and upper values"
                )
            lower = tuple(_probability(value, "lower") for value in self.lower)
            upper = tuple(_probability(value, "upper") for value in self.upper)
            point = (
                None
                if self.point is None
                else tuple(_probability(value, "point") for value in self.point)
            )
            if (
                len(lower) != len(thresholds)
                or len(upper) != len(thresholds)
                or (point is not None and len(point) != len(thresholds))
                or any(lo > hi for lo, hi in zip(lower, upper, strict=True))
                or not _nonincreasing(lower)
                or not _nonincreasing(upper)
                or (point is not None and not _nonincreasing(point))
            ):
                raise ConditionalExceedanceError(
                    "defined exceedance values must align, be ordered, and "
                    "be non-increasing over thresholds"
                )
            if point is not None and any(
                not lo <= value <= hi
                for lo, value, hi in zip(lower, point, upper, strict=True)
            ):
                raise ConditionalExceedanceError(
                    "point values must lie inside the envelope"
                )
            if self.status is ExceedanceStatus.DEFINED_POINT and (
                point is None or point != lower or point != upper
            ):
                raise ConditionalExceedanceError(
                    "DEFINED_POINT requires equal point and bounds"
                )
            if self.status is ExceedanceStatus.DEFINED_ENVELOPE and point is not None:
                raise ConditionalExceedanceError(
                    "DEFINED_ENVELOPE must not carry one selected point"
                )
            object.__setattr__(self, "lower", lower)
            object.__setattr__(self, "upper", upper)
            object.__setattr__(self, "point", point)
            if self.sampling_law is None or self.lane is None:
                raise ConditionalExceedanceError(
                    "defined profile requires one explicit probability law"
                )
        elif any(value is not None for value in numeric):
            raise ConditionalExceedanceError(
                "refusal profiles must not carry numeric probabilities"
            )
        for enum_value, enum_type, name in (
            (self.sampling_law, SamplingLaw, "sampling_law"),
            (
                self.conditioning_source,
                ConditioningSource,
                "conditioning_source",
            ),
            (self.lane, ExceedanceLane, "lane"),
        ):
            if enum_value is not None and type(enum_value) is not enum_type:
                raise ConditionalExceedanceError(
                    f"{name} must use the registered vocabulary"
                )
        for name in (
            "law_spec_id",
            "draws_id",
            "covariance_id",
            "calibration_id",
            "identified_set_id",
        ):
            value = getattr(self, name)
            if value is not None:
                _text(value, name)
        reasons = _texts(
            self.refusal_reasons,
            "refusal_reasons",
            empty_ok=defined,
        )
        if defined and reasons:
            raise ConditionalExceedanceError(
                "defined profiles must not carry refusal reasons"
            )
        if not defined and not reasons:
            raise ConditionalExceedanceError(
                "refusal profiles require a reason"
            )
        if self.claim_ceiling != CONDITIONAL_EXCEEDANCE_CLAIM_CEILING:
            raise ConditionalExceedanceError("claim ceiling drifted")
        if tuple(self.allowed_use) != CONDITIONAL_EXCEEDANCE_ALLOWED_USE:
            raise ConditionalExceedanceError("allowed-use lane drifted")
        if tuple(self.forbidden_use) != CONDITIONAL_EXCEEDANCE_FORBIDDEN_USE:
            raise ConditionalExceedanceError("forbidden-use lane drifted")
        object.__setattr__(self, "thresholds", thresholds)
        object.__setattr__(self, "refusal_reasons", reasons)
        object.__setattr__(
            self,
            "_identity_seal",
            _sha256_payload(self._payload_unchecked()),
        )

    @property
    def content_id(self) -> str:
        self._assert_identity_sealed()
        return self._identity_seal

    def _payload_unchecked(self) -> dict[str, object]:
        return {
            "allowed_use": list(self.allowed_use),
            "calibration_id": self.calibration_id,
            "claim_ceiling": self.claim_ceiling,
            "conditioning_id": self.conditioning_id,
            "conditioning_source": (
                None
                if self.conditioning_source is None
                else self.conditioning_source.value
            ),
            "covariance_id": self.covariance_id,
            "draws_id": self.draws_id,
            "forbidden_use": list(self.forbidden_use),
            "functional_id": self.functional_id,
            "identified_set_id": self.identified_set_id,
            "lane": None if self.lane is None else self.lane.value,
            "law_spec_id": self.law_spec_id,
            "lower": None if self.lower is None else list(self.lower),
            "point": None if self.point is None else list(self.point),
            "profile_id": self.profile_id,
            "refusal_reasons": list(self.refusal_reasons),
            "sampling_law": (
                None if self.sampling_law is None else self.sampling_law.value
            ),
            "schema": "HTT_CONDITIONAL_EXCEEDANCE_PROFILE_V1",
            "status": self.status.value,
            "thresholds": list(self.thresholds),
            "upper": None if self.upper is None else list(self.upper),
        }

    def _assert_identity_sealed(self) -> None:
        _assert_sealed(
            self._payload_unchecked(),
            self._identity_seal,
            name="conditional exceedance profile",
        )

    def as_payload(self) -> dict[str, object]:
        self._assert_identity_sealed()
        return {
            **self._payload_unchecked(),
            "content_id": self._identity_seal,
        }


@dataclass(frozen=True)
class NullCalibratedExceedance:
    profile: ConditionalExceedanceProfile
    coverage: FiniteNullCoverageReport | None
    owner: str = "MIO"
    _construction_token: InitVar[object] = None
    _identity_seal: str = field(init=False, repr=False, compare=False)

    def __post_init__(self, _construction_token: object) -> None:
        if _construction_token is not _NULL_TOKEN:
            raise ConditionalExceedanceError(
                "NullCalibratedExceedance must be factory-built"
            )
        if type(self.profile) is not ConditionalExceedanceProfile:
            raise ConditionalExceedanceError(
                "profile must be a ConditionalExceedanceProfile"
            )
        self.profile.as_payload()
        if self.profile.lane is not ExceedanceLane.MIO_NULL:
            raise ConditionalExceedanceError(
                "null-calibrated exceedance is MIO-null owned"
            )
        if self.coverage is not None and type(
            self.coverage
        ) is not FiniteNullCoverageReport:
            raise ConditionalExceedanceError(
                "coverage must be a FiniteNullCoverageReport"
            )
        if self.owner != "MIO":
            raise ConditionalExceedanceError("owner must remain MIO")
        object.__setattr__(
            self,
            "_identity_seal",
            _sha256_payload(self._payload_unchecked()),
        )

    def _payload_unchecked(self) -> dict[str, object]:
        return {
            "coverage": (
                None if self.coverage is None else self.coverage.as_payload()
            ),
            "owner": self.owner,
            "profile": self.profile.as_payload(),
            "schema": "HTT_NULL_CALIBRATED_EXCEEDANCE_V1",
        }

    def _assert_identity_sealed(self) -> None:
        _assert_sealed(
            self._payload_unchecked(),
            self._identity_seal,
            name="null-calibrated exceedance",
        )

    def as_payload(self) -> dict[str, object]:
        self.profile.as_payload()
        if self.coverage is not None:
            self.coverage.as_payload()
        self._assert_identity_sealed()
        return {
            **self._payload_unchecked(),
            "content_id": self._identity_seal,
        }


@dataclass(frozen=True)
class PosteriorExceedance:
    profile: ConditionalExceedanceProfile
    calibration: PosteriorCalibrationReport
    owner: str = "HTT"
    _construction_token: InitVar[object] = None
    _identity_seal: str = field(init=False, repr=False, compare=False)

    def __post_init__(self, _construction_token: object) -> None:
        if _construction_token is not _POSTERIOR_TOKEN:
            raise ConditionalExceedanceError(
                "PosteriorExceedance must be factory-built"
            )
        if type(self.profile) is not ConditionalExceedanceProfile:
            raise ConditionalExceedanceError(
                "profile must be a ConditionalExceedanceProfile"
            )
        if type(self.calibration) is not PosteriorCalibrationReport:
            raise ConditionalExceedanceError(
                "calibration must be a PosteriorCalibrationReport"
            )
        self.profile.as_payload()
        self.calibration.as_payload()
        if self.profile.lane is not ExceedanceLane.HTT_POSTERIOR:
            raise ConditionalExceedanceError(
                "posterior exceedance is HTT-posterior owned"
            )
        if self.owner != "HTT":
            raise ConditionalExceedanceError("owner must remain HTT")
        object.__setattr__(
            self,
            "_identity_seal",
            _sha256_payload(self._payload_unchecked()),
        )

    def _payload_unchecked(self) -> dict[str, object]:
        return {
            "calibration": self.calibration.as_payload(),
            "owner": self.owner,
            "profile": self.profile.as_payload(),
            "schema": "HTT_POSTERIOR_EXCEEDANCE_V1",
        }

    def _assert_identity_sealed(self) -> None:
        _assert_sealed(
            self._payload_unchecked(),
            self._identity_seal,
            name="posterior exceedance",
        )

    def as_payload(self) -> dict[str, object]:
        self.profile.as_payload()
        self.calibration.as_payload()
        self._assert_identity_sealed()
        return {
            **self._payload_unchecked(),
            "content_id": self._identity_seal,
        }


def _strict_tail(values: Sequence[float], thresholds: Sequence[float]) -> tuple[float, ...]:
    count = len(values)
    return tuple(
        sum(value > threshold for value in values) / count
        for threshold in thresholds
    )


def _point_profile(
    *,
    profile_id: str,
    functional_id: str,
    thresholds: tuple[float, ...],
    values: tuple[float, ...],
    law: SamplingLawSpec,
    draws: SamplingDraws,
    conditioning_id: str,
    calibration_id: str | None = None,
) -> ConditionalExceedanceProfile:
    return ConditionalExceedanceProfile(
        profile_id=profile_id,
        functional_id=functional_id,
        thresholds=thresholds,
        lower=values,
        upper=values,
        point=values,
        status=ExceedanceStatus.DEFINED_POINT,
        sampling_law=law.sampling_law,
        conditioning_source=law.conditioning_source,
        lane=law.lane,
        law_spec_id=law.content_id,
        draws_id=draws.content_id,
        conditioning_id=conditioning_id,
        covariance_id=law.covariance_id,
        calibration_id=calibration_id,
        identified_set_id=None,
        refusal_reasons=(),
        _construction_token=_PROFILE_TOKEN,
    )


def _refusal_profile(
    *,
    profile_id: str,
    functional_id: str,
    thresholds: Sequence[object],
    status: ExceedanceStatus,
    conditioning_id: str,
    reason: str,
    law: SamplingLawSpec | None = None,
    draws: SamplingDraws | None = None,
    calibration_id: str | None = None,
    identified_set_id: str | None = None,
) -> ConditionalExceedanceProfile:
    return ConditionalExceedanceProfile(
        profile_id=profile_id,
        functional_id=functional_id,
        thresholds=_thresholds(thresholds),
        lower=None,
        upper=None,
        point=None,
        status=status,
        sampling_law=None if law is None else law.sampling_law,
        conditioning_source=(
            None if law is None else law.conditioning_source
        ),
        lane=None if law is None else law.lane,
        law_spec_id=None if law is None else law.content_id,
        draws_id=None if draws is None else draws.content_id,
        conditioning_id=conditioning_id,
        covariance_id=None if law is None else law.covariance_id,
        calibration_id=calibration_id,
        identified_set_id=identified_set_id,
        refusal_reasons=(reason,),
        _construction_token=_PROFILE_TOKEN,
    )


def build_missing_probability_law_profile(
    *,
    profile_id: str,
    functional_id: str,
    thresholds: Sequence[object],
    conditioning_id: str,
    reason: str,
) -> ConditionalExceedanceProfile:
    return _refusal_profile(
        profile_id=profile_id,
        functional_id=functional_id,
        thresholds=thresholds,
        status=ExceedanceStatus.MISSING_PROBABILITY_LAW,
        conditioning_id=conditioning_id,
        reason=reason,
    )


def build_null_calibrated_exceedance(
    *,
    profile_id: str,
    functional_id: str,
    thresholds: Sequence[object],
    law: SamplingLawSpec,
    draws: SamplingDraws | LikelihoodObjective,
    conditioning_id: str,
    alpha: object = 0.05,
) -> NullCalibratedExceedance:
    if type(law) is not SamplingLawSpec:
        raise TypeError("law must be an exact SamplingLawSpec")
    law.as_payload()
    if type(draws) is not SamplingDraws:
        raise ConditionalExceedanceError(
            "null exceedance requires sampling draws, not an optimizer "
            "or likelihood objective"
        )
    draws.as_payload()
    if (
        law.lane is not ExceedanceLane.MIO_NULL
        or law.sampling_law
        not in {
            SamplingLaw.FIXED_INJECTION_MOCK,
            SamplingLaw.BOOTSTRAP_RESAMPLING,
        }
    ):
        raise ConditionalExceedanceError(
            "MIO null exceedance requires a matched-null or empirical law"
        )
    if draws.law_spec_id != law.content_id or draws.lane is not law.lane:
        raise ConditionalExceedanceError(
            "draws are not bound to the declared null law"
        )
    resolved_thresholds = _thresholds(thresholds)
    if len(draws.values) < 2:
        profile = _refusal_profile(
            profile_id=profile_id,
            functional_id=functional_id,
            thresholds=resolved_thresholds,
            status=ExceedanceStatus.INSUFFICIENT_DRAWS,
            conditioning_id=conditioning_id,
            reason="finite-null exceedance requires at least two draws",
            law=law,
            draws=draws,
        )
        return NullCalibratedExceedance(
            profile=profile,
            coverage=None,
            _construction_token=_NULL_TOKEN,
        )
    probabilities = _strict_tail(draws.values, resolved_thresholds)
    resolved_alpha = _probability(alpha, "alpha")
    if resolved_alpha in {0.0, 1.0}:
        raise ConditionalExceedanceError("alpha must be strictly in (0, 1)")
    radius = math.sqrt(
        math.log(2.0 / resolved_alpha) / (2.0 * len(draws.values))
    )
    radius = min(1.0, radius)
    coverage = FiniteNullCoverageReport(
        method="DKW_TWO_SIDED_SIMULTANEOUS",
        alpha=resolved_alpha,
        draw_count=len(draws.values),
        simultaneous_radius=radius,
        lower=tuple(max(0.0, value - radius) for value in probabilities),
        upper=tuple(min(1.0, value + radius) for value in probabilities),
        _construction_token=_COVERAGE_TOKEN,
    )
    profile = _point_profile(
        profile_id=profile_id,
        functional_id=functional_id,
        thresholds=resolved_thresholds,
        values=probabilities,
        law=law,
        draws=draws,
        conditioning_id=conditioning_id,
    )
    return NullCalibratedExceedance(
        profile=profile,
        coverage=coverage,
        _construction_token=_NULL_TOKEN,
    )


def build_posterior_exceedance(
    *,
    profile_id: str,
    functional_id: str,
    thresholds: Sequence[object],
    law: SamplingLawSpec,
    draws: SamplingDraws | LikelihoodObjective,
    conditioning_id: str,
    calibration: PosteriorCalibrationReport,
) -> PosteriorExceedance:
    if type(law) is not SamplingLawSpec:
        raise TypeError("law must be an exact SamplingLawSpec")
    if type(calibration) is not PosteriorCalibrationReport:
        raise TypeError(
            "calibration must be an exact PosteriorCalibrationReport"
        )
    law.as_payload()
    calibration.as_payload()
    if type(draws) is not SamplingDraws:
        raise ConditionalExceedanceError(
            "posterior exceedance requires posterior draws, not an optimizer "
            "or likelihood objective"
        )
    draws.as_payload()
    if (
        law.lane is not ExceedanceLane.HTT_POSTERIOR
        or law.sampling_law
        not in {
            SamplingLaw.POSTERIOR_PREDICTIVE,
            SamplingLaw.OBSERVATIONAL_POSTERIOR_PUSHFORWARD,
        }
    ):
        raise ConditionalExceedanceError(
            "posterior exceedance requires an explicit HTT posterior law"
        )
    if draws.law_spec_id != law.content_id or draws.lane is not law.lane:
        raise ConditionalExceedanceError(
            "draws are not bound to the declared posterior law"
        )
    resolved_thresholds = _thresholds(thresholds)
    if calibration.status is not PosteriorCalibrationStatus.PASSED:
        profile = _refusal_profile(
            profile_id=profile_id,
            functional_id=functional_id,
            thresholds=resolved_thresholds,
            status=ExceedanceStatus.POSTERIOR_CALIBRATION_REQUIRED,
            conditioning_id=conditioning_id,
            reason="posterior calibration has not passed the preregistered gate",
            law=law,
            draws=draws,
            calibration_id=calibration.content_id,
        )
    elif len(draws.values) < 2:
        profile = _refusal_profile(
            profile_id=profile_id,
            functional_id=functional_id,
            thresholds=resolved_thresholds,
            status=ExceedanceStatus.INSUFFICIENT_DRAWS,
            conditioning_id=conditioning_id,
            reason="posterior exceedance requires at least two draws",
            law=law,
            draws=draws,
            calibration_id=calibration.content_id,
        )
    else:
        profile = _point_profile(
            profile_id=profile_id,
            functional_id=functional_id,
            thresholds=resolved_thresholds,
            values=_strict_tail(draws.values, resolved_thresholds),
            law=law,
            draws=draws,
            conditioning_id=conditioning_id,
            calibration_id=calibration.content_id,
        )
    return PosteriorExceedance(
        profile=profile,
        calibration=calibration,
        _construction_token=_POSTERIOR_TOKEN,
    )


def _clone_identified_set(
    value: IdentifiedDepartureSet,
) -> IdentifiedDepartureSet:
    if type(value) is not IdentifiedDepartureSet:
        raise TypeError(
            "identified_set must be an exact IdentifiedDepartureSet"
        )
    return IdentifiedDepartureSet(
        coordinate_names=tuple(value.coordinate_names),
        vertices=tuple(tuple(row) for row in value.vertices),
        recession_directions=tuple(
            tuple(row) for row in value.recession_directions
        ),
        null_kinds=tuple(value.null_kinds),
        assumptions=tuple(value.assumptions),
        status=value.status,
        representation=value.representation,
    )


def _identified_set_id(value: IdentifiedDepartureSet) -> str:
    return _sha256_payload(
        {
            "assumptions": list(value.assumptions),
            "coordinate_names": list(value.coordinate_names),
            "null_kinds": [item.value for item in value.null_kinds],
            "recession_directions": [
                [number.hex() for number in row]
                for row in value.recession_directions
            ],
            "representation": value.representation,
            "status": value.status.value,
            "vertices": [
                [number.hex() for number in row] for row in value.vertices
            ],
        }
    )


def identified_vertex_id(
    coordinate_names: Sequence[str],
    vertex: Sequence[object],
) -> str:
    names = _texts(coordinate_names, "coordinate_names")
    values = tuple(_real(value, "vertex") for value in vertex)
    if len(values) != len(names):
        raise ConditionalExceedanceError(
            "vertex must match the coordinate dimension"
        )
    return _sha256_payload(
        {
            "coordinate_names": list(names),
            "vertex_hex": [value.hex() for value in values],
        }
    )


def build_conditional_exceedance_envelope(
    *,
    profile_id: str,
    functional_id: str,
    thresholds: Sequence[object],
    identified_set: IdentifiedDepartureSet,
    profiles_by_vertex: Mapping[str, ConditionalExceedanceProfile],
    certificate: EnvelopeCertificate | str,
    conditioning_id: str,
) -> ConditionalExceedanceProfile:
    """Build a vertex envelope only under the exact registered conditions."""

    identified = _clone_identified_set(identified_set)
    set_id = _identified_set_id(identified)
    resolved_thresholds = _thresholds(thresholds)
    resolved_certificate = _enum(
        certificate,
        EnvelopeCertificate,
        "certificate",
    )
    if identified.status is IdentificationStatus.EMPTY:
        return _refusal_profile(
            profile_id=profile_id,
            functional_id=functional_id,
            thresholds=resolved_thresholds,
            status=ExceedanceStatus.EMPTY_IDENTIFIED_SET,
            conditioning_id=conditioning_id,
            reason="empty identified set has no conditional exceedance",
            identified_set_id=set_id,
        )
    if (
        identified.recession_directions
        or resolved_certificate
        not in {
            EnvelopeCertificate.MONOTONE,
            EnvelopeCertificate.UPPER_QUASI_CONVEX_LOWER_QUASI_CONCAVE,
        }
    ):
        reason = (
            "identified set is unbounded; an explicit optimizer contract is "
            "required"
            if identified.recession_directions
            else "vertex enumeration lacks both an upper and lower endpoint "
            "certificate"
        )
        return _refusal_profile(
            profile_id=profile_id,
            functional_id=functional_id,
            thresholds=resolved_thresholds,
            status=ExceedanceStatus.OPTIMIZER_REQUIRED,
            conditioning_id=conditioning_id,
            reason=reason,
            identified_set_id=set_id,
        )
    expected_ids = {
        identified_vertex_id(identified.coordinate_names, vertex)
        for vertex in identified.vertices
    }
    if set(profiles_by_vertex) != expected_ids:
        raise ConditionalExceedanceError(
            "profiles_by_vertex must cover every exact identified-set vertex"
        )
    profiles = tuple(profiles_by_vertex[key] for key in sorted(expected_ids))
    if any(type(profile) is not ConditionalExceedanceProfile for profile in profiles):
        raise TypeError(
            "profiles_by_vertex values must be exact "
            "ConditionalExceedanceProfile instances"
        )
    for profile in profiles:
        profile.as_payload()
    first = profiles[0]
    if any(
        profile.status is not ExceedanceStatus.DEFINED_POINT
        or profile.thresholds != resolved_thresholds
        or profile.functional_id != functional_id
        or profile.sampling_law is not first.sampling_law
        or profile.conditioning_source is not first.conditioning_source
        or profile.lane is not first.lane
        or profile.law_spec_id != first.law_spec_id
        or profile.covariance_id != first.covariance_id
        or profile.calibration_id != first.calibration_id
        for profile in profiles
    ):
        raise ConditionalExceedanceError(
            "vertex profiles must share one defined law, functional, "
            "threshold, and covariance contract"
        )
    assert all(profile.point is not None for profile in profiles)
    columns = tuple(zip(*(profile.point for profile in profiles), strict=True))
    lower = tuple(min(column) for column in columns)
    upper = tuple(max(column) for column in columns)
    if len(profiles) == 1:
        point = first.point
        status = ExceedanceStatus.DEFINED_POINT
    else:
        point = None
        status = ExceedanceStatus.DEFINED_ENVELOPE
    return ConditionalExceedanceProfile(
        profile_id=profile_id,
        functional_id=functional_id,
        thresholds=resolved_thresholds,
        lower=lower,
        upper=upper,
        point=point,
        status=status,
        sampling_law=first.sampling_law,
        conditioning_source=ConditioningSource.IDENTIFIED_SET,
        lane=first.lane,
        law_spec_id=first.law_spec_id,
        draws_id=None,
        conditioning_id=conditioning_id,
        covariance_id=first.covariance_id,
        calibration_id=first.calibration_id,
        identified_set_id=set_id,
        refusal_reasons=(),
        _construction_token=_PROFILE_TOKEN,
    )


__all__ = [
    "CONDITIONAL_EXCEEDANCE_ALLOWED_USE",
    "CONDITIONAL_EXCEEDANCE_CLAIM_CEILING",
    "CONDITIONAL_EXCEEDANCE_FORBIDDEN_USE",
    "ConditionalExceedanceError",
    "ConditionalExceedanceProfile",
    "ConditioningSource",
    "EnvelopeCertificate",
    "ExceedanceLane",
    "ExceedanceStatus",
    "FiniteNullCoverageReport",
    "LikelihoodObjective",
    "NullCalibratedExceedance",
    "PosteriorCalibrationReport",
    "PosteriorCalibrationStatus",
    "PosteriorExceedance",
    "SamplingDraws",
    "SamplingLaw",
    "SamplingLawSpec",
    "build_conditional_exceedance_envelope",
    "build_likelihood_objective",
    "build_missing_probability_law_profile",
    "build_null_calibrated_exceedance",
    "build_posterior_calibration_report",
    "build_posterior_exceedance",
    "build_sampling_draws",
    "build_sampling_law_spec",
    "identified_vertex_id",
]
