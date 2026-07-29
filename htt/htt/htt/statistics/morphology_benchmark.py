"""Held-out comparison of preregistered low-ell morphology representations.

This HTT module consumes already extracted synthetic feature matrices.  It
does not extract OBSSTAT features, infer an observed source, or turn
separation into scientific evidence.  The classifier and abstention rules are
frozen by :class:`MorphologyBenchmarkProtocol` before held-out arrays are
scored.
"""

from __future__ import annotations

from dataclasses import InitVar, dataclass
from enum import Enum
import hashlib
import json
import math
import re
from typing import Mapping, Sequence

import numpy as np

from common.anchored_response_geometry import (
    SchurMorphologyInformationReport,
    SchurMorphologyStatus,
    revalidate_schur_morphology_information,
)
from common.anchor_geometry import NormalizerSpec


class MorphologyBenchmarkError(ValueError):
    """Raised when a held-out benchmark contract is incomplete."""


class MorphologyRepresentation(str, Enum):
    SCALAR_X_C = "scalar_x_C"
    FULL_DEPARTURE_STATE = "full_departure_state"
    FISHER_WHITENED_STATE = "fisher_whitened_state"
    ANCHOR_COORDINATE_WITH_IDENTITY = "anchor_coordinate_with_identity"
    ORBIT_CATALOGUE_V2 = "orbit_catalogue_v2"
    MULTIPOLE_POWER_TENSOR = "multipole_power_tensor"
    BIPOSH = "biposh"
    DIRECTIONAL_WAVELET = "directional_wavelet"
    TEB_CROSS_MORPHOLOGY = "TEB_cross_morphology"


class RepresentationAvailability(str, Enum):
    AVAILABLE = "AVAILABLE"
    MISSING_FEATURE_PROVIDER = "MISSING_FEATURE_PROVIDER"


class RepresentationBenchmarkStatus(str, Enum):
    MEASURED = "MEASURED"
    DEGENERATE_ABSTENTION = "DEGENERATE_ABSTENTION"
    MISSING_FEATURE_PROVIDER = "MISSING_FEATURE_PROVIDER"


class MorphologyBenchmarkStatus(str, Enum):
    MEASURED = "MEASURED"
    INCONCLUSIVE_MC_PRECISION = "INCONCLUSIVE_MC_PRECISION"


PR257_REPRESENTATIONS = tuple(MorphologyRepresentation)
PR257_MULTIPLICITY_RULE = "MAX_ABS_Z_FIXED_CATALOGUE_V1"
PR257_SCORING_RULE = "NEAREST_CENTROID_FIXED_MARGIN_OPEN_SET_V1"
PR257_MINIMUM_MC_REPLICATES = 20_000
_SHA256_RE = re.compile(r"sha256:[0-9a-f]{64}\Z")
_RESULT_TOKEN = object()
_REPORT_TOKEN = object()
_ALLOWED_USE = (
    "synthetic held-out representation comparison",
    "synthetic generator-label loss and abstention diagnostic",
    "mask, beam, and foreground sensitivity diagnostic",
)
_FORBIDDEN_USE = (
    "observed source detection",
    "posterior or evidence term",
    "FLRW departure detection",
    "Bianchi family identification",
)


def _text(value: object, name: str) -> str:
    if not isinstance(value, str) or not value or value != value.strip():
        raise MorphologyBenchmarkError(
            f"{name} must be non-empty trimmed text"
        )
    return value


def _receipt(value: object, name: str) -> str:
    text = _text(value, name)
    if not _SHA256_RE.fullmatch(text):
        raise MorphologyBenchmarkError(
            f"{name} must be a lowercase sha256 content identity"
        )
    return text


def _finite_real(value: object, name: str) -> float:
    if isinstance(value, (bool, np.bool_)) or isinstance(value, (str, bytes)):
        raise MorphologyBenchmarkError(f"{name} must be a finite real")
    try:
        out = float(value)
    except (TypeError, ValueError, OverflowError) as exc:
        raise MorphologyBenchmarkError(f"{name} must be a finite real") from exc
    if not math.isfinite(out):
        raise MorphologyBenchmarkError(f"{name} must be finite")
    return out


def _probability(value: object, name: str) -> float:
    out = _finite_real(value, name)
    if not 0.0 <= out <= 1.0:
        raise MorphologyBenchmarkError(f"{name} must be in [0, 1]")
    return out


def _positive(value: object, name: str) -> float:
    out = _finite_real(value, name)
    if out <= 0.0:
        raise MorphologyBenchmarkError(f"{name} must be positive")
    return out


def _positive_int(value: object, name: str) -> int:
    if isinstance(value, (bool, np.bool_)) or not isinstance(
        value, (int, np.integer)
    ):
        raise MorphologyBenchmarkError(f"{name} must be an integer")
    out = int(value)
    if out <= 0:
        raise MorphologyBenchmarkError(f"{name} must be positive")
    return out


def _sha256_payload(payload: object) -> str:
    encoded = json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
    ).encode("ascii")
    return f"sha256:{hashlib.sha256(encoded).hexdigest()}"


def _array(
    value: object,
    name: str,
    *,
    ndim: int,
    rows: int | None = None,
) -> np.ndarray:
    raw = np.asarray(value)
    if raw.dtype.kind in {"b", "O", "U", "S", "c"}:
        raise MorphologyBenchmarkError(
            f"{name} must contain real, non-boolean numeric values"
        )
    try:
        array = np.asarray(value, dtype=np.float64)
    except (TypeError, ValueError, OverflowError) as exc:
        raise MorphologyBenchmarkError(
            f"{name} must contain real numeric values"
        ) from exc
    if array.ndim != ndim:
        raise MorphologyBenchmarkError(f"{name} must have ndim={ndim}")
    if rows is not None and array.shape[0] != rows:
        raise MorphologyBenchmarkError(
            f"{name} must have {rows} rows"
        )
    if any(dimension <= 0 for dimension in array.shape):
        raise MorphologyBenchmarkError(
            f"{name} must have positive dimensions"
        )
    if not np.all(np.isfinite(array)):
        raise MorphologyBenchmarkError(f"{name} must be finite")
    canonical = np.ascontiguousarray(array, dtype=np.float64)
    out = np.frombuffer(
        canonical.tobytes(order="C"),
        dtype=np.float64,
    ).reshape(canonical.shape)
    out.setflags(write=False)
    return out


def _array_content_id(value: np.ndarray) -> str:
    array = np.ascontiguousarray(value, dtype=np.float64)
    digest = hashlib.sha256()
    digest.update(str(array.shape).encode("ascii"))
    digest.update(b"\0")
    digest.update(array.tobytes(order="C"))
    return f"sha256:{digest.hexdigest()}"


def _labels(value: object, name: str, *, rows: int) -> np.ndarray:
    raw = np.asarray(value)
    if raw.dtype.kind not in {"i", "u"} or raw.dtype.kind == "b":
        raise MorphologyBenchmarkError(f"{name} must contain integer labels")
    array = np.asarray(raw, dtype=np.int64)
    if array.ndim != 1 or array.shape[0] != rows:
        raise MorphologyBenchmarkError(
            f"{name} must be a vector with {rows} entries"
        )
    if set(array.tolist()) != {0, 1}:
        raise MorphologyBenchmarkError(
            f"{name} must contain both binary classes 0 and 1"
        )
    canonical = np.ascontiguousarray(array, dtype=np.int64)
    out = np.frombuffer(
        canonical.tobytes(order="C"),
        dtype=np.int64,
    ).reshape(canonical.shape)
    out.setflags(write=False)
    return out


@dataclass(frozen=True)
class MorphologyBenchmarkProtocol:
    """Frozen split, scoring, multiplicity, and abstention contract."""

    protocol_id: str
    preregistration_id: str
    catalogue_id: str
    master_seed: int
    train_fraction: float
    validation_fraction: float
    held_out_fraction: float
    confidence_margin_threshold: float
    unknown_distance_threshold: float
    maximum_mcse: float
    null_center_id: str
    null_scale_id: str
    available_representations: tuple[MorphologyRepresentation, ...]
    missing_representations: tuple[MorphologyRepresentation, ...]
    abstention_cost: float = 0.5
    multiplicity_rule: str = PR257_MULTIPLICITY_RULE
    scoring_rule: str = PR257_SCORING_RULE
    representations: tuple[MorphologyRepresentation, ...] = (
        PR257_REPRESENTATIONS
    )

    def __post_init__(self) -> None:
        for name in (
            "protocol_id",
            "preregistration_id",
            "catalogue_id",
            "null_center_id",
            "null_scale_id",
        ):
            _receipt(getattr(self, name), name)
        seed = _positive_int(self.master_seed, "master_seed")
        fractions = tuple(
            _probability(getattr(self, name), name)
            for name in (
                "train_fraction",
                "validation_fraction",
                "held_out_fraction",
            )
        )
        if not math.isclose(sum(fractions), 1.0, abs_tol=1.0e-12, rel_tol=0.0):
            raise MorphologyBenchmarkError(
                "train/validation/held-out fractions must sum to one"
            )
        margin = _positive(
            self.confidence_margin_threshold,
            "confidence_margin_threshold",
        )
        unknown = _positive(
            self.unknown_distance_threshold,
            "unknown_distance_threshold",
        )
        mcse = _positive(self.maximum_mcse, "maximum_mcse")
        if mcse > 0.0025:
            raise MorphologyBenchmarkError(
                "maximum_mcse must be at most 0.0025"
            )
        abstention_cost = _probability(
            self.abstention_cost,
            "abstention_cost",
        )
        available = tuple(self.available_representations)
        missing = tuple(self.missing_representations)
        if (
            any(not isinstance(item, MorphologyRepresentation) for item in available)
            or any(not isinstance(item, MorphologyRepresentation) for item in missing)
            or len(set(available)) != len(available)
            or len(set(missing)) != len(missing)
            or set(available) & set(missing)
            or set(available) | set(missing) != set(PR257_REPRESENTATIONS)
        ):
            raise MorphologyBenchmarkError(
                "available/missing representations must be a fixed partition"
            )
        required_missing = {
            MorphologyRepresentation.DIRECTIONAL_WAVELET,
            MorphologyRepresentation.TEB_CROSS_MORPHOLOGY,
        }
        if not required_missing.issubset(missing):
            raise MorphologyBenchmarkError(
                "unregistered wavelet and T/E/B providers must remain missing"
            )
        if available != PR257_REPRESENTATIONS[:-2] or missing != PR257_REPRESENTATIONS[-2:]:
            raise MorphologyBenchmarkError(
                "PR-257 availability order is frozen before held-out scoring"
            )
        if self.multiplicity_rule != PR257_MULTIPLICITY_RULE:
            raise MorphologyBenchmarkError(
                "multiplicity_rule must match the frozen PR-257 rule"
            )
        if self.scoring_rule != PR257_SCORING_RULE:
            raise MorphologyBenchmarkError(
                "scoring_rule must match the frozen held-out rule"
            )
        if tuple(self.representations) != PR257_REPRESENTATIONS:
            raise MorphologyBenchmarkError(
                "representations/order must match the frozen PR-257 list"
            )
        object.__setattr__(self, "master_seed", seed)
        object.__setattr__(self, "confidence_margin_threshold", margin)
        object.__setattr__(self, "unknown_distance_threshold", unknown)
        object.__setattr__(self, "maximum_mcse", mcse)
        object.__setattr__(self, "abstention_cost", abstention_cost)
        object.__setattr__(self, "available_representations", available)
        object.__setattr__(self, "missing_representations", missing)
        object.__setattr__(self, "representations", PR257_REPRESENTATIONS)

    @property
    def protocol_hash(self) -> str:
        return _sha256_payload(
            {
                "catalogue_id": self.catalogue_id,
                "confidence_margin_threshold_hex": (
                    self.confidence_margin_threshold.hex()
                ),
                "fractions_hex": [
                    self.train_fraction.hex(),
                    self.validation_fraction.hex(),
                    self.held_out_fraction.hex(),
                ],
                "master_seed": self.master_seed,
                "maximum_mcse_hex": self.maximum_mcse.hex(),
                "multiplicity_rule": self.multiplicity_rule,
                "null_center_id": self.null_center_id,
                "null_scale_id": self.null_scale_id,
                "available_representations": [
                    item.value for item in self.available_representations
                ],
                "missing_representations": [
                    item.value for item in self.missing_representations
                ],
                "abstention_cost_hex": self.abstention_cost.hex(),
                "preregistration_id": self.preregistration_id,
                "protocol_id": self.protocol_id,
                "representations": [
                    item.value for item in self.representations
                ],
                "schema": "PR257_MORPHOLOGY_BENCHMARK_PROTOCOL_V1",
                "scoring_rule": self.scoring_rule,
                "unknown_distance_threshold_hex": (
                    self.unknown_distance_threshold.hex()
                ),
            }
        )


@dataclass(frozen=True)
class RepresentationBenchmarkInput:
    """Exact split arrays for one representation or one typed absence."""

    representation: MorphologyRepresentation
    availability: RepresentationAvailability
    partition_ids: tuple[str, str, str, str]
    train_features: np.ndarray | None = None
    train_targets: np.ndarray | None = None
    validation_features: np.ndarray | None = None
    validation_targets: np.ndarray | None = None
    held_out_features: np.ndarray | None = None
    held_out_targets: np.ndarray | None = None
    unknown_features: np.ndarray | None = None
    mask_perturbed_features: np.ndarray | None = None
    beam_perturbed_features: np.ndarray | None = None
    foreground_features: np.ndarray | None = None
    geometry: SchurMorphologyInformationReport | None = None
    geometry_normalizer: NormalizerSpec | None = None
    missing_reason: str | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.representation, MorphologyRepresentation):
            raise MorphologyBenchmarkError(
                "representation must be a MorphologyRepresentation"
            )
        if not isinstance(self.availability, RepresentationAvailability):
            raise MorphologyBenchmarkError(
                "availability must be a RepresentationAvailability"
            )
        partitions = tuple(
            _receipt(value, f"partition_ids[{index}]")
            for index, value in enumerate(self.partition_ids)
        )
        if len(partitions) != 4 or len(set(partitions)) != 4:
            raise MorphologyBenchmarkError(
                "partition_ids must contain four distinct train, validation, "
                "held-out, and unknown receipts"
            )
        object.__setattr__(self, "partition_ids", partitions)
        array_fields = (
            "train_features",
            "train_targets",
            "validation_features",
            "validation_targets",
            "held_out_features",
            "held_out_targets",
            "unknown_features",
            "mask_perturbed_features",
            "beam_perturbed_features",
            "foreground_features",
        )
        if self.availability is RepresentationAvailability.MISSING_FEATURE_PROVIDER:
            if any(getattr(self, name) is not None for name in array_fields):
                raise MorphologyBenchmarkError(
                    "missing representation must not carry arrays, including zeros"
                )
            if self.geometry is not None or self.geometry_normalizer is not None:
                raise MorphologyBenchmarkError(
                    "missing representation must not carry response geometry"
                )
            _text(self.missing_reason, "missing_reason")
            return
        if self.missing_reason is not None:
            raise MorphologyBenchmarkError(
                "available representation must not carry missing_reason"
            )
        train = _array(self.train_features, "train_features", ndim=2)
        validation = _array(
            self.validation_features,
            "validation_features",
            ndim=2,
        )
        held_out = _array(
            self.held_out_features,
            "held_out_features",
            ndim=2,
        )
        unknown = _array(self.unknown_features, "unknown_features", ndim=2)
        feature_dimension = train.shape[1]
        for name, array in (
            ("validation_features", validation),
            ("held_out_features", held_out),
            ("unknown_features", unknown),
        ):
            if array.shape[1] != feature_dimension:
                raise MorphologyBenchmarkError(
                    f"{name} must share the train feature dimension"
                )
        train_targets = _labels(
            self.train_targets,
            "train_targets",
            rows=train.shape[0],
        )
        validation_targets = _labels(
            self.validation_targets,
            "validation_targets",
            rows=validation.shape[0],
        )
        held_out_targets = _labels(
            self.held_out_targets,
            "held_out_targets",
            rows=held_out.shape[0],
        )
        perturbations: dict[str, np.ndarray] = {}
        for name in (
            "mask_perturbed_features",
            "beam_perturbed_features",
            "foreground_features",
        ):
            array = _array(
                getattr(self, name),
                name,
                ndim=2,
                rows=held_out.shape[0],
            )
            if array.shape[1] != feature_dimension:
                raise MorphologyBenchmarkError(
                    f"{name} must share the held-out feature dimension"
                )
            perturbations[name] = array
        identities = {
            "train_features": _array_content_id(train),
            "validation_features": _array_content_id(validation),
            "held_out_features": _array_content_id(held_out),
            "train_targets": _array_content_id(train_targets),
            "validation_targets": _array_content_id(validation_targets),
            "held_out_targets": _array_content_id(held_out_targets),
        }
        feature_ids_are_distinct = len(
            {
                identities["train_features"],
                identities["validation_features"],
                identities["held_out_features"],
            }
        ) == 3
        scalar_constant_control = (
            self.representation is MorphologyRepresentation.SCALAR_X_C
            and train.shape[1] == 1
            and np.all(train == train[0, 0])
            and np.all(validation == train[0, 0])
            and np.all(held_out == train[0, 0])
        )
        if not feature_ids_are_distinct and not scalar_constant_control:
            raise MorphologyBenchmarkError(
                "train, validation, and held-out feature bytes must be distinct"
            )
        if len(
            {
                identities["train_targets"],
                identities["validation_targets"],
                identities["held_out_targets"],
            }
        ) != 3:
            raise MorphologyBenchmarkError(
                "train, validation, and held-out target bytes must be distinct"
            )
        if not isinstance(self.geometry, SchurMorphologyInformationReport):
            raise MorphologyBenchmarkError(
                "available representation requires Schur response geometry"
            )
        if not isinstance(self.geometry_normalizer, NormalizerSpec):
            raise MorphologyBenchmarkError(
                "available representation requires its exact normalizer"
            )
        revalidate_schur_morphology_information(
            self.geometry,
            normalizer=self.geometry_normalizer,
        )
        if (
            self.geometry.status
            not in {
                SchurMorphologyStatus.MEASURED,
                SchurMorphologyStatus.EXPLICIT_NULL_RESPONSE,
            }
            or self.geometry.baseline_geometry is None
            or self.geometry.conditional_morphology_geometry is None
            or self.geometry.contraction is None
        ):
            raise MorphologyBenchmarkError(
                "available representation requires measured PR-255 geometry"
            )
        for name, value in (
            ("train_features", train),
            ("train_targets", train_targets),
            ("validation_features", validation),
            ("validation_targets", validation_targets),
            ("held_out_features", held_out),
            ("held_out_targets", held_out_targets),
            ("unknown_features", unknown),
            *perturbations.items(),
        ):
            object.__setattr__(self, name, value)

    @property
    def input_ids(self) -> dict[str, str] | None:
        if self.availability is RepresentationAvailability.MISSING_FEATURE_PROVIDER:
            return None
        identities = {
            name: _array_content_id(getattr(self, name))
            for name in (
                "train_features",
                "train_targets",
                "validation_features",
                "validation_targets",
                "held_out_features",
                "held_out_targets",
                "unknown_features",
                "mask_perturbed_features",
                "beam_perturbed_features",
                "foreground_features",
            )
        }
        identities.update(
            {
                f"{role}_partition": identity
                for role, identity in zip(
                    ("train", "validation", "held_out", "unknown"),
                    self.partition_ids,
                    strict=True,
                )
            }
        )
        return identities


@dataclass(frozen=True)
class RepresentationBenchmarkResult:
    representation: MorphologyRepresentation
    status: RepresentationBenchmarkStatus
    feature_dimension: int | None
    supported_rank: int | None
    singular_values: tuple[float, ...]
    held_out_error_rate: float | None
    held_out_abstention_rate: float | None
    unknown_known_assignment_rate: float | None
    mask_decision_change_rate: float | None
    beam_decision_change_rate: float | None
    foreground_decision_change_rate: float | None
    maximum_mcse: float | None
    train_null_center_id: str | None
    train_null_scale_id: str | None
    zero_scale_coordinates: tuple[int, ...]
    held_out_max_abs_z_mean: float | None
    held_out_max_abs_z_q95: float | None
    generator_label_loss: float | None
    generator_label_loss_reduction_from_scalar: float | None
    generator_label_loss_reduction_mcse_from_scalar: float | None
    geometry_payload: Mapping[str, object] | None
    input_ids: Mapping[str, str] | None
    missing_reason: str | None
    _construction_token: InitVar[object] = None

    def __post_init__(self, _construction_token: object) -> None:
        if _construction_token is not _RESULT_TOKEN:
            raise MorphologyBenchmarkError(
                "RepresentationBenchmarkResult must be factory-derived"
            )
        if not isinstance(self.representation, MorphologyRepresentation):
            raise MorphologyBenchmarkError("invalid representation")
        if not isinstance(self.status, RepresentationBenchmarkStatus):
            raise MorphologyBenchmarkError("invalid benchmark status")
        if self.status is RepresentationBenchmarkStatus.MISSING_FEATURE_PROVIDER:
            _text(self.missing_reason, "missing_reason")
            if any(
                value is not None
                for value in (
                    self.feature_dimension,
                    self.supported_rank,
                    self.held_out_error_rate,
                    self.held_out_abstention_rate,
                    self.unknown_known_assignment_rate,
                    self.mask_decision_change_rate,
                    self.beam_decision_change_rate,
                    self.foreground_decision_change_rate,
                    self.maximum_mcse,
                    self.train_null_center_id,
                    self.train_null_scale_id,
                    self.held_out_max_abs_z_mean,
                    self.held_out_max_abs_z_q95,
                    self.generator_label_loss,
                    self.generator_label_loss_reduction_from_scalar,
                    self.generator_label_loss_reduction_mcse_from_scalar,
                    self.geometry_payload,
                    self.input_ids,
                )
            ) or self.singular_values or self.zero_scale_coordinates:
                raise MorphologyBenchmarkError(
                    "missing result must not carry measured values"
                )
            return
        if self.missing_reason is not None:
            raise MorphologyBenchmarkError(
                "measured result must not carry missing_reason"
            )
        if self.feature_dimension is None or self.feature_dimension <= 0:
            raise MorphologyBenchmarkError(
                "feature_dimension must be positive"
            )
        if self.supported_rank is None or not (
            0 <= self.supported_rank <= self.feature_dimension
        ):
            raise MorphologyBenchmarkError("supported_rank is invalid")
        for name in (
            "held_out_error_rate",
            "held_out_abstention_rate",
            "unknown_known_assignment_rate",
            "mask_decision_change_rate",
            "beam_decision_change_rate",
            "foreground_decision_change_rate",
        ):
            _probability(getattr(self, name), name)
        maximum_mcse = _finite_real(self.maximum_mcse, "maximum_mcse")
        if maximum_mcse < 0.0:
            raise MorphologyBenchmarkError(
                "maximum_mcse must be non-negative"
            )
        _receipt(self.train_null_center_id, "train_null_center_id")
        _receipt(self.train_null_scale_id, "train_null_scale_id")
        zero_scale = tuple(self.zero_scale_coordinates)
        if (
            any(
                isinstance(index, (bool, np.bool_))
                or not isinstance(index, (int, np.integer))
                for index in zero_scale
            )
            or tuple(sorted(set(int(index) for index in zero_scale)))
            != tuple(int(index) for index in zero_scale)
            or any(
                int(index) < 0 or int(index) >= self.feature_dimension
                for index in zero_scale
            )
        ):
            raise MorphologyBenchmarkError(
                "zero_scale_coordinates must be unique increasing feature indices"
            )
        if zero_scale:
            if self.status is not RepresentationBenchmarkStatus.DEGENERATE_ABSTENTION:
                raise MorphologyBenchmarkError(
                    "zero train scale must force representation abstention"
                )
            if (
                self.held_out_max_abs_z_mean is not None
                or self.held_out_max_abs_z_q95 is not None
            ):
                raise MorphologyBenchmarkError(
                    "zero-scale representation must not report standardized maxima"
                )
        else:
            for name in (
                "held_out_max_abs_z_mean",
                "held_out_max_abs_z_q95",
            ):
                value = _finite_real(getattr(self, name), name)
                if value < 0.0:
                    raise MorphologyBenchmarkError(
                        f"{name} must be non-negative"
                    )
        object.__setattr__(
            self,
            "zero_scale_coordinates",
            tuple(int(index) for index in zero_scale),
        )
        _probability(self.generator_label_loss, "generator_label_loss")
        if self.generator_label_loss_reduction_from_scalar is not None:
            value = _finite_real(
                self.generator_label_loss_reduction_from_scalar,
                "generator_label_loss_reduction_from_scalar",
            )
            if not -1.0 <= value <= 1.0:
                raise MorphologyBenchmarkError(
                    "generator-label loss reduction must be in [-1, 1]"
                )
        paired_mcse = _finite_real(
            self.generator_label_loss_reduction_mcse_from_scalar,
            "generator_label_loss_reduction_mcse_from_scalar",
        )
        if paired_mcse < 0.0:
            raise MorphologyBenchmarkError(
                "paired generator-label loss-reduction MCSE must be non-negative"
            )
        if self.geometry_payload is None or self.input_ids is None:
            raise MorphologyBenchmarkError(
                "measured result requires geometry and input identities"
            )

    def as_payload(self) -> dict[str, object]:
        return {
            "beam_decision_change_rate": self.beam_decision_change_rate,
            "feature_dimension": self.feature_dimension,
            "foreground_decision_change_rate": (
                self.foreground_decision_change_rate
            ),
            "geometry": self.geometry_payload,
            "held_out_abstention_rate": self.held_out_abstention_rate,
            "held_out_error_rate": self.held_out_error_rate,
            "generator_label_loss": self.generator_label_loss,
            "generator_label_loss_reduction_from_scalar": (
                self.generator_label_loss_reduction_from_scalar
            ),
            "generator_label_loss_reduction_mcse_from_scalar": (
                self.generator_label_loss_reduction_mcse_from_scalar
            ),
            "input_ids": self.input_ids,
            "mask_decision_change_rate": self.mask_decision_change_rate,
            "maximum_mcse": self.maximum_mcse,
            "missing_reason": self.missing_reason,
            "representation": self.representation.value,
            "singular_values": list(self.singular_values),
            "status": self.status.value,
            "supported_rank": self.supported_rank,
            "train_null_center_id": self.train_null_center_id,
            "train_null_scale_id": self.train_null_scale_id,
            "unknown_known_assignment_rate": self.unknown_known_assignment_rate,
            "zero_scale_coordinates": list(self.zero_scale_coordinates),
            "held_out_max_abs_z_mean": self.held_out_max_abs_z_mean,
            "held_out_max_abs_z_q95": self.held_out_max_abs_z_q95,
        }


@dataclass(frozen=True)
class LowEllMorphologyBenchmarkReport:
    status: MorphologyBenchmarkStatus
    protocol: MorphologyBenchmarkProtocol
    results: tuple[RepresentationBenchmarkResult, ...]
    maximum_observed_mcse: float
    held_out_count: int
    unknown_count: int
    observed_data_used: bool
    pr151_data_used: bool
    old_rust_output_used: bool
    native_solver_output_used: bool
    transfer_source: str
    allowed_use: tuple[str, ...] = _ALLOWED_USE
    forbidden_use: tuple[str, ...] = _FORBIDDEN_USE
    _construction_token: InitVar[object] = None

    def __post_init__(self, _construction_token: object) -> None:
        if _construction_token is not _REPORT_TOKEN:
            raise MorphologyBenchmarkError(
                "LowEllMorphologyBenchmarkReport must be factory-derived"
            )
        if not isinstance(self.status, MorphologyBenchmarkStatus):
            raise MorphologyBenchmarkError("invalid report status")
        if not isinstance(self.protocol, MorphologyBenchmarkProtocol):
            raise MorphologyBenchmarkError("invalid benchmark protocol")
        results = tuple(self.results)
        if tuple(item.representation for item in results) != PR257_REPRESENTATIONS:
            raise MorphologyBenchmarkError(
                "results must follow the frozen representation order"
            )
        maximum_observed_mcse = _finite_real(
            self.maximum_observed_mcse,
            "maximum_observed_mcse",
        )
        if maximum_observed_mcse < 0.0:
            raise MorphologyBenchmarkError(
                "maximum_observed_mcse must be non-negative"
            )
        _positive_int(self.held_out_count, "held_out_count")
        _positive_int(self.unknown_count, "unknown_count")
        if any(
            (
                self.observed_data_used,
                self.pr151_data_used,
                self.old_rust_output_used,
                self.native_solver_output_used,
            )
        ):
            raise MorphologyBenchmarkError(
                "PR-257 benchmark must remain synthetic and pre-solver"
            )
        if self.transfer_source != "none":
            raise MorphologyBenchmarkError(
                "PR-257 synthetic benchmark transfer_source must be none"
            )
        if self.allowed_use != _ALLOWED_USE or self.forbidden_use != _FORBIDDEN_USE:
            raise MorphologyBenchmarkError(
                "benchmark report must retain the HTT claim boundary"
            )
        object.__setattr__(self, "results", results)

    @property
    def report_id(self) -> str:
        return _sha256_payload(self.as_payload())

    def as_payload(self) -> dict[str, object]:
        return {
            "allowed_use": list(self.allowed_use),
            "data_provenance": {
                "native_solver_output_used": self.native_solver_output_used,
                "observed_data_used": self.observed_data_used,
                "old_rust_output_used": self.old_rust_output_used,
                "pr151_data_used": self.pr151_data_used,
                "transfer_source": self.transfer_source,
            },
            "forbidden_use": list(self.forbidden_use),
            "held_out_count": self.held_out_count,
            "unknown_count": self.unknown_count,
            "maximum_observed_mcse": self.maximum_observed_mcse,
            "protocol_hash": self.protocol.protocol_hash,
            "results": [item.as_payload() for item in self.results],
            "schema": "PR257_LOWELL_MORPHOLOGY_BENCHMARK_REPORT_V1",
            "status": self.status.value,
        }


def _mcse(rate: float, count: int) -> float:
    return math.sqrt(max(rate * (1.0 - rate), 0.0) / count)


def _fit_rule(
    train: np.ndarray,
    targets: np.ndarray,
) -> tuple[
    np.ndarray,
    np.ndarray,
    np.ndarray,
    np.ndarray,
    np.ndarray,
    tuple[int, ...],
]:
    location = np.mean(train, axis=0)
    raw_scale = np.std(train, axis=0, ddof=1)
    scale = np.where(raw_scale > 0.0, raw_scale, 1.0)
    null_train = train[targets == 0]
    null_location = np.mean(null_train, axis=0)
    raw_null_scale = np.std(null_train, axis=0, ddof=1)
    zero_scale = tuple(
        int(index) for index in np.flatnonzero(raw_null_scale <= 0.0)
    )
    null_scale = np.where(raw_null_scale > 0.0, raw_null_scale, 1.0)
    standardized = (train - location) / scale
    centroids = np.vstack(
        [np.mean(standardized[targets == label], axis=0) for label in (0, 1)]
    )
    return (
        location,
        scale,
        centroids,
        null_location,
        null_scale,
        zero_scale,
    )


def _vector_receipt(values: np.ndarray, *, role: str) -> str:
    return _sha256_payload(
        {
            "role": role,
            "values_hex": [
                float(value).hex()
                for value in np.asarray(values, dtype=np.float64).ravel()
            ],
        }
    )


def _decide(
    features: np.ndarray,
    *,
    location: np.ndarray,
    scale: np.ndarray,
    centroids: np.ndarray,
    margin_threshold: float,
    unknown_distance_threshold: float,
) -> np.ndarray:
    standardized = (features - location) / scale
    distances = np.linalg.norm(
        standardized[:, None, :] - centroids[None, :, :],
        axis=2,
    )
    nearest = np.argmin(distances, axis=1)
    ordered = np.sort(distances, axis=1)
    margin = ordered[:, 1] - ordered[:, 0]
    decision = nearest.astype(np.int64)
    decision[
        (margin <= margin_threshold)
        | (ordered[:, 0] >= unknown_distance_threshold)
    ] = -1
    return decision


def evaluate_morphology_benchmark(
    *,
    protocol: MorphologyBenchmarkProtocol,
    inputs: Sequence[RepresentationBenchmarkInput],
) -> LowEllMorphologyBenchmarkReport:
    """Run the fixed nearest-centroid/open-set rule on held-out arrays."""

    if not isinstance(protocol, MorphologyBenchmarkProtocol):
        raise TypeError("protocol must be a MorphologyBenchmarkProtocol")
    items = tuple(inputs)
    if tuple(item.representation for item in items) != PR257_REPRESENTATIONS:
        raise MorphologyBenchmarkError(
            "inputs must follow the frozen representation order"
        )
    for item in items:
        expected = (
            RepresentationAvailability.AVAILABLE
            if item.representation in protocol.available_representations
            else RepresentationAvailability.MISSING_FEATURE_PROVIDER
        )
        if item.availability is not expected:
            raise MorphologyBenchmarkError(
                "input availability differs from the frozen protocol mask"
            )
    available_items = tuple(
        item
        for item in items
        if item.availability is RepresentationAvailability.AVAILABLE
    )
    partition_contracts = {item.partition_ids for item in items}
    if len(partition_contracts) != 1:
        raise MorphologyBenchmarkError(
            "all representations must share train, validation, held-out, "
            "and unknown partition identities"
        )
    target_contracts = {
        tuple(
            _array_content_id(values)
            for values in (
                item.train_targets,
                item.validation_targets,
                item.held_out_targets,
            )
        )
        for item in available_items
    }
    if len(target_contracts) != 1:
        raise MorphologyBenchmarkError(
            "all available representations must share target bytes for the "
            "paired train, validation, and held-out units"
        )
    geometry_contracts = {
        (
            item.geometry.parameter_labels,
            item.geometry.normalizer_id,
            item.geometry.baseline_observable_id,
            item.geometry.baseline_geometry.transfer_id,
            item.geometry.baseline_geometry.mask_id,
            item.geometry.relative_tolerance,
            tuple(tuple(row) for row in item.geometry.baseline_information),
            item.geometry_normalizer.kind.value,
            tuple(
                purpose.value
                for purpose in item.geometry_normalizer.purposes
            ),
            item.geometry_normalizer.coordinate_labels,
            item.geometry_normalizer.coordinate_map,
            item.geometry_normalizer.source_identity,
        )
        for item in available_items
    }
    if len(geometry_contracts) != 1:
        raise MorphologyBenchmarkError(
            "available representations must share one parameter, normalizer, "
            "baseline, transfer, mask, support-tolerance, and information contract"
        )
    measured: list[RepresentationBenchmarkResult] = []
    held_out_count: int | None = None
    unknown_count: int | None = None
    baseline_loss: float | None = None
    baseline_losses: np.ndarray | None = None
    for item in items:
        if item.availability is RepresentationAvailability.MISSING_FEATURE_PROVIDER:
            measured.append(
                RepresentationBenchmarkResult(
                    representation=item.representation,
                    status=RepresentationBenchmarkStatus.MISSING_FEATURE_PROVIDER,
                    feature_dimension=None,
                    supported_rank=None,
                    singular_values=(),
                    held_out_error_rate=None,
                    held_out_abstention_rate=None,
                    unknown_known_assignment_rate=None,
                    mask_decision_change_rate=None,
                    beam_decision_change_rate=None,
                    foreground_decision_change_rate=None,
                    maximum_mcse=None,
                    train_null_center_id=None,
                    train_null_scale_id=None,
                    zero_scale_coordinates=(),
                    held_out_max_abs_z_mean=None,
                    held_out_max_abs_z_q95=None,
                    generator_label_loss=None,
                    generator_label_loss_reduction_from_scalar=None,
                    generator_label_loss_reduction_mcse_from_scalar=None,
                    geometry_payload=None,
                    input_ids=None,
                    missing_reason=item.missing_reason,
                    _construction_token=_RESULT_TOKEN,
                )
            )
            continue

        train = item.train_features
        targets = item.train_targets
        held_out = item.held_out_features
        held_out_targets = item.held_out_targets
        if held_out_count is None:
            held_out_count = int(held_out.shape[0])
        elif held_out.shape[0] != held_out_count:
            raise MorphologyBenchmarkError(
                "all available representations must share held-out count"
            )
        if unknown_count is None:
            unknown_count = int(item.unknown_features.shape[0])
        elif item.unknown_features.shape[0] != unknown_count:
            raise MorphologyBenchmarkError(
                "all available representations must share unknown count"
            )
        (
            location,
            scale,
            centroids,
            null_location,
            null_scale,
            zero_scale,
        ) = _fit_rule(train, targets)
        conditional_geometry = item.geometry.conditional_morphology_geometry
        rank = int(conditional_geometry.rank or 0)
        singular = tuple(
            float(value) for value in conditional_geometry.singular_values
        )
        centroid_distance = float(np.linalg.norm(centroids[0] - centroids[1]))
        degenerate = (
            rank == 0
            or bool(zero_scale)
            or centroid_distance <= protocol.confidence_margin_threshold
        )

        if degenerate:
            decision = np.full(held_out.shape[0], -1, dtype=np.int64)
            unknown_decision = np.full(
                item.unknown_features.shape[0], -1, dtype=np.int64
            )
            mask_decision = decision.copy()
            beam_decision = decision.copy()
            foreground_decision = decision.copy()
            result_status = RepresentationBenchmarkStatus.DEGENERATE_ABSTENTION
        else:
            kwargs = {
                "location": location,
                "scale": scale,
                "centroids": centroids,
                "margin_threshold": protocol.confidence_margin_threshold,
                "unknown_distance_threshold": protocol.unknown_distance_threshold,
            }
            decision = _decide(held_out, **kwargs)
            unknown_decision = _decide(item.unknown_features, **kwargs)
            mask_decision = _decide(item.mask_perturbed_features, **kwargs)
            beam_decision = _decide(item.beam_perturbed_features, **kwargs)
            foreground_decision = _decide(item.foreground_features, **kwargs)
            result_status = RepresentationBenchmarkStatus.MEASURED

        assigned = decision >= 0
        error_rate = float(
            np.mean(assigned & (decision != held_out_targets))
        )
        abstention_rate = float(np.mean(~assigned))
        unknown_known = float(np.mean(unknown_decision >= 0))
        mask_change = float(np.mean(mask_decision != decision))
        beam_change = float(np.mean(beam_decision != decision))
        foreground_change = float(np.mean(foreground_decision != decision))
        losses = np.where(
            decision < 0,
            protocol.abstention_cost,
            (decision != held_out_targets).astype(float),
        )
        generator_label_loss = float(np.mean(losses))
        loss_mcse = float(
            np.std(losses, ddof=1) / math.sqrt(held_out.shape[0])
        )
        rate_mcses = tuple(
            _mcse(rate, held_out.shape[0])
            for rate in (
                error_rate,
                abstention_rate,
                mask_change,
                beam_change,
                foreground_change,
            )
        ) + (
            _mcse(unknown_known, item.unknown_features.shape[0]),
            loss_mcse,
        )
        maximum_mcse = max(rate_mcses)
        train_null_center_id = _vector_receipt(
            null_location,
            role=f"{item.representation.value}:train_null_center",
        )
        train_null_scale_id = _vector_receipt(
            null_scale,
            role=f"{item.representation.value}:train_null_scale",
        )
        if zero_scale:
            held_out_max_abs_z_mean = None
            held_out_max_abs_z_q95 = None
        else:
            held_out_max_abs_z = np.max(
                np.abs((held_out - null_location) / null_scale),
                axis=1,
            )
            held_out_max_abs_z_mean = float(
                np.mean(held_out_max_abs_z)
            )
            quantile_index = max(
                0,
                math.ceil(0.95 * held_out_max_abs_z.shape[0]) - 1,
            )
            held_out_max_abs_z_q95 = float(
                np.partition(
                    held_out_max_abs_z,
                    quantile_index,
                )[quantile_index]
            )
        if item.representation is MorphologyRepresentation.SCALAR_X_C:
            baseline_loss = generator_label_loss
            baseline_losses = losses
        if baseline_loss is None or baseline_losses is None:
            raise MorphologyBenchmarkError(
                "scalar x_C must precede every paired representation"
            )
        paired_loss_differences = baseline_losses - losses
        reduction = (
            baseline_loss - generator_label_loss
        )
        reduction_mcse = float(
            np.std(paired_loss_differences, ddof=1)
            / math.sqrt(held_out.shape[0])
        )
        maximum_mcse = max(maximum_mcse, reduction_mcse)
        measured.append(
            RepresentationBenchmarkResult(
                representation=item.representation,
                status=result_status,
                feature_dimension=int(train.shape[1]),
                supported_rank=rank,
                singular_values=singular,
                held_out_error_rate=error_rate,
                held_out_abstention_rate=abstention_rate,
                unknown_known_assignment_rate=unknown_known,
                mask_decision_change_rate=mask_change,
                beam_decision_change_rate=beam_change,
                foreground_decision_change_rate=foreground_change,
                maximum_mcse=maximum_mcse,
                train_null_center_id=train_null_center_id,
                train_null_scale_id=train_null_scale_id,
                zero_scale_coordinates=zero_scale,
                held_out_max_abs_z_mean=held_out_max_abs_z_mean,
                held_out_max_abs_z_q95=held_out_max_abs_z_q95,
                generator_label_loss=generator_label_loss,
                generator_label_loss_reduction_from_scalar=reduction,
                generator_label_loss_reduction_mcse_from_scalar=(
                    reduction_mcse
                ),
                geometry_payload=item.geometry.as_payload(),
                input_ids=item.input_ids,
                missing_reason=None,
                _construction_token=_RESULT_TOKEN,
            )
        )

    if held_out_count is None or unknown_count is None:
        raise MorphologyBenchmarkError(
            "at least one representation must be available"
        )
    maximum_observed_mcse = max(
        item.maximum_mcse
        for item in measured
        if item.maximum_mcse is not None
    )
    status = (
        MorphologyBenchmarkStatus.MEASURED
        if (
            held_out_count >= PR257_MINIMUM_MC_REPLICATES
            and unknown_count >= PR257_MINIMUM_MC_REPLICATES
            and maximum_observed_mcse <= protocol.maximum_mcse
        )
        else MorphologyBenchmarkStatus.INCONCLUSIVE_MC_PRECISION
    )
    return LowEllMorphologyBenchmarkReport(
        status=status,
        protocol=protocol,
        results=tuple(measured),
        maximum_observed_mcse=maximum_observed_mcse,
        held_out_count=held_out_count,
        unknown_count=unknown_count,
        observed_data_used=False,
        pr151_data_used=False,
        old_rust_output_used=False,
        native_solver_output_used=False,
        transfer_source="none",
        _construction_token=_REPORT_TOKEN,
    )


__all__ = [
    "LowEllMorphologyBenchmarkReport",
    "MorphologyBenchmarkError",
    "MorphologyBenchmarkProtocol",
    "MorphologyBenchmarkStatus",
    "MorphologyRepresentation",
    "PR257_MULTIPLICITY_RULE",
    "PR257_MINIMUM_MC_REPLICATES",
    "PR257_REPRESENTATIONS",
    "PR257_SCORING_RULE",
    "RepresentationAvailability",
    "RepresentationBenchmarkInput",
    "RepresentationBenchmarkResult",
    "RepresentationBenchmarkStatus",
    "evaluate_morphology_benchmark",
]
