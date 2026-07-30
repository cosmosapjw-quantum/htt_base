"""Abstaining anisotropy compatibility report.

This module combines replay-validated outputs from the joint-state, orbit,
anchored-response, open-set, conditional-exceedance, and depth-path layers.
It intentionally has no geometry-label or family-label output.  The strongest
terminal state is a finite response-compatibility candidate at roadmap level
C2; weak or missing inputs terminate as typed abstentions.
"""

from __future__ import annotations

from dataclasses import InitVar, dataclass, field
from enum import Enum
import hashlib
import json
import math
from numbers import Real
from typing import Mapping, Sequence

from common.anchor_geometry import NormalizerSpec
from common.anchored_response_geometry import (
    AnchoredResponseGeometryReport,
    AnchoredResponseStatus,
    PrincipalAngleStatus,
    measure_anchored_response_geometry,
)
from common.conditional_exceedance import (
    ConditionalExceedanceProfile,
    ExceedanceStatus,
)
from common.depth_path import (
    DepthCoherenceReport,
    DepthCoherenceStatus,
    DepthPath,
    revalidate_depth_path,
)
from common.joint_anisotropy_state import (
    JointAnisotropyState,
    MissingComponent,
)
from common.open_set_response_classes import (
    OpenSetClassificationReport,
    OpenSetClassificationStatus,
    ReopeningObservableSpec,
    ResponseClassManifoldSpec,
    ResponseClassSourceSemantics,
    ResponseEquivalenceClassReport,
    SourceSeparationGate,
    SourceSeparationGateStatus,
    build_reopening_observable_spec,
    build_response_class_manifold,
    build_response_equivalence_report,
    classify_open_set_response,
)
from common.orbit_catalogue_v3 import (
    CatalogueProofStatus,
    OrbitCatalogueV3Report,
    revalidate_orbit_catalogue_v3,
)


class AnisotropyTypeReportError(ValueError):
    """Raised when an anisotropy compatibility input fails closed."""


class _StringEnum(str, Enum):
    def __str__(self) -> str:
        return self.value


class GeometryInformationStatus(_StringEnum):
    COMPLETE = "COMPLETE"
    PARTIAL = "PARTIAL"
    MISSING = "MISSING"


class LocalGlobalCompatibility(_StringEnum):
    SEPARABLE_CANDIDATE = "SEPARABLE_CANDIDATE"
    NON_IDENTIFIED = "NON_IDENTIFIED"
    SUM_ONLY = "SUM_ONLY"
    MISSING_RESPONSE_PROVIDER = "MISSING_RESPONSE_PROVIDER"


class AnisotropyCompatibilityStatus(_StringEnum):
    PARTIAL_DIAGNOSTIC = "PARTIAL_DIAGNOSTIC"
    INDETERMINATE = "INDETERMINATE"
    UNKNOWN = "UNKNOWN"
    RESPONSE_COMPATIBILITY_CANDIDATE = "RESPONSE_COMPATIBILITY_CANDIDATE"


ANISOTROPY_TYPE_CLAIM_CEILING = "diagnostic_only"
ANISOTROPY_TYPE_ROADMAP_LEVEL = "C2"
ANISOTROPY_TYPE_FAMILY_GATE = "BLOCKED_PRE_NATIVE_ATLAS"
ANISOTROPY_TYPE_ALLOWED_USE = (
    "typed partial anisotropy diagnostic",
    "finite response-class compatibility candidate",
    "local/global response compatibility summary",
    "UNKNOWN or INDETERMINATE terminal diagnostic outcome",
)
ANISOTROPY_TYPE_FORBIDDEN_USE = (
    "nearest-label substitution after abstention",
    "geometry detection",
    "Bianchi family identification or ranking",
    "native solver or native morphology-atlas result",
    "probability-bearing inference, evidence, or truth claims under MIO ownership",
)

_LOCAL_GLOBAL_TOKEN = object()
_OPEN_SET_TOKEN = object()
_REPORT_TOKEN = object()
_REGISTERED_RESPONSE_CLASS_ID = {
    ResponseClassSourceSemantics.NEUTRAL: "response-class-neutral",
    ResponseClassSourceSemantics.LOCAL_BOOST: "response-class-local",
    ResponseClassSourceSemantics.GLOBAL_TILT: "response-class-global",
}
_REGISTERED_RESPONSE_CLASS_IDS = frozenset(
    _REGISTERED_RESPONSE_CLASS_ID.values()
)


def _text(value: object, name: str) -> str:
    if not isinstance(value, str) or not value.strip() or value != value.strip():
        raise AnisotropyTypeReportError(
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
        raise AnisotropyTypeReportError(f"{name} must be a sequence of text")
    result = tuple(_text(value, name) for value in values)
    if not result and not empty_ok:
        raise AnisotropyTypeReportError(f"{name} must not be empty")
    if len(result) != len(set(result)):
        raise AnisotropyTypeReportError(f"{name} must not contain duplicates")
    return result


def _real(value: object, name: str) -> float:
    if isinstance(value, bool) or not isinstance(value, Real):
        raise AnisotropyTypeReportError(f"{name} must be real")
    result = float(value)
    if not math.isfinite(result):
        raise AnisotropyTypeReportError(f"{name} must be finite")
    return result


def _nonnegative(value: object, name: str) -> float:
    result = _real(value, name)
    if result < 0.0:
        raise AnisotropyTypeReportError(f"{name} must be non-negative")
    return result


def _optional_nonnegative(value: object | None, name: str) -> float | None:
    return None if value is None else _nonnegative(value, name)


def _integer(value: object, name: str, *, minimum: int = 0) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < minimum:
        raise AnisotropyTypeReportError(
            f"{name} must be an integer >= {minimum}"
        )
    return value


def _sha256_payload(payload: object) -> str:
    encoded = json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
        allow_nan=False,
    ).encode("ascii")
    return f"sha256:{hashlib.sha256(encoded).hexdigest()}"


def _assert_sealed(payload: object, seal: str, *, name: str) -> None:
    if _sha256_payload(payload) != seal:
        raise AnisotropyTypeReportError(
            f"{name} identity drifted after construction"
        )


def _vector(
    values: Sequence[object],
    name: str,
) -> tuple[float, ...]:
    if isinstance(values, (str, bytes)):
        raise AnisotropyTypeReportError(f"{name} must be a numeric vector")
    result = tuple(_real(value, name) for value in values)
    if not result:
        raise AnisotropyTypeReportError(f"{name} must not be empty")
    return result


def _matrix(
    values: Sequence[Sequence[object]],
    name: str,
    *,
    rows: int | None = None,
    columns: int | None = None,
) -> tuple[tuple[float, ...], ...]:
    if isinstance(values, (str, bytes)):
        raise AnisotropyTypeReportError(f"{name} must be a numeric matrix")
    result = tuple(
        tuple(_real(value, f"{name}[{row_index}]") for value in row)
        for row_index, row in enumerate(values)
    )
    if not result or any(not row for row in result):
        raise AnisotropyTypeReportError(f"{name} must not be empty")
    width = len(result[0])
    if any(len(row) != width for row in result):
        raise AnisotropyTypeReportError(f"{name} must be rectangular")
    if rows is not None and len(result) != rows:
        raise AnisotropyTypeReportError(f"{name} must have {rows} rows")
    if columns is not None and width != columns:
        raise AnisotropyTypeReportError(
            f"{name} must have {columns} columns"
        )
    return result


def _optional_matrix(
    value: Sequence[Sequence[object]] | None,
    name: str,
    *,
    rows: int,
) -> tuple[tuple[float, ...], ...] | None:
    if value is None:
        return None
    return _matrix(value, name, rows=rows)


@dataclass(frozen=True)
class LocalGlobalCompatibilityInput:
    """COMMON snapshot produced only after the HTT PR-256 replay."""

    source_report_id: str
    status: LocalGlobalCompatibility
    local_rank: int | None
    global_rank: int | None
    joint_rank: int | None
    principal_angles_radians: tuple[float, ...]
    minimum_principal_angle_radians: float | None
    separation_threshold_radians: float
    direct_sum: bool | None
    observable_labels: tuple[str, ...]
    covariance_id: str
    mask_id: str
    normalizer_id: str
    normalizer_source_identity: str
    local_provider_id: str
    global_provider_id: str
    local_response_id: str | None
    global_response_id: str | None
    joint_transfer_id: str | None
    assumptions: tuple[str, ...]
    claim_ceiling: str = ANISOTROPY_TYPE_CLAIM_CEILING
    _construction_token: InitVar[object] = None
    _identity_seal: str = field(init=False, repr=False, compare=False)

    def __post_init__(self, _construction_token: object) -> None:
        if _construction_token is not _LOCAL_GLOBAL_TOKEN:
            raise AnisotropyTypeReportError(
                "LocalGlobalCompatibilityInput must come from the HTT replay "
                "adapter"
            )
        for name in (
            "source_report_id",
            "covariance_id",
            "mask_id",
            "normalizer_id",
            "normalizer_source_identity",
            "local_provider_id",
            "global_provider_id",
        ):
            _text(getattr(self, name), name)
        if type(self.status) is not LocalGlobalCompatibility:
            raise AnisotropyTypeReportError(
                "status must use LocalGlobalCompatibility"
            )
        for name in ("local_rank", "global_rank", "joint_rank"):
            value = getattr(self, name)
            if value is not None:
                object.__setattr__(
                    self,
                    name,
                    _integer(value, name),
                )
        angles = tuple(
            _nonnegative(value, "principal_angles_radians")
            for value in self.principal_angles_radians
        )
        minimum = _optional_nonnegative(
            self.minimum_principal_angle_radians,
            "minimum_principal_angle_radians",
        )
        threshold = _nonnegative(
            self.separation_threshold_radians,
            "separation_threshold_radians",
        )
        if angles and minimum is None:
            raise AnisotropyTypeReportError(
                "principal angles require an explicit minimum angle"
            )
        if minimum is not None and (
            not angles
            or not math.isclose(
                minimum,
                min(angles),
                rel_tol=1e-12,
                abs_tol=1e-12,
            )
        ):
            raise AnisotropyTypeReportError(
                "minimum principal angle must match the angle tuple"
            )
        if self.direct_sum is not None and type(self.direct_sum) is not bool:
            raise AnisotropyTypeReportError("direct_sum must be Boolean or null")
        if self.status is LocalGlobalCompatibility.SEPARABLE_CANDIDATE and (
            minimum is None
            or minimum <= threshold
            or self.direct_sum is not True
            or any(
                value is None
                for value in (
                    self.local_rank,
                    self.global_rank,
                    self.joint_rank,
                )
            )
        ):
            raise AnisotropyTypeReportError(
                "separable candidate requires ranks, a direct sum, and an "
                "angle above threshold"
            )
        labels = _texts(self.observable_labels, "observable_labels")
        assumptions = _texts(self.assumptions, "assumptions")
        for name in (
            "local_response_id",
            "global_response_id",
            "joint_transfer_id",
        ):
            value = getattr(self, name)
            if value is not None:
                _text(value, name)
        if self.claim_ceiling != ANISOTROPY_TYPE_CLAIM_CEILING:
            raise AnisotropyTypeReportError("claim ceiling drifted")
        object.__setattr__(self, "principal_angles_radians", angles)
        object.__setattr__(
            self,
            "minimum_principal_angle_radians",
            minimum,
        )
        object.__setattr__(
            self,
            "separation_threshold_radians",
            threshold,
        )
        object.__setattr__(self, "observable_labels", labels)
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
            "claim_ceiling": self.claim_ceiling,
            "covariance_id": self.covariance_id,
            "direct_sum": self.direct_sum,
            "global_provider_id": self.global_provider_id,
            "global_rank": self.global_rank,
            "global_response_id": self.global_response_id,
            "joint_rank": self.joint_rank,
            "joint_transfer_id": self.joint_transfer_id,
            "local_provider_id": self.local_provider_id,
            "local_rank": self.local_rank,
            "local_response_id": self.local_response_id,
            "mask_id": self.mask_id,
            "minimum_principal_angle_radians_hex": (
                None
                if self.minimum_principal_angle_radians is None
                else self.minimum_principal_angle_radians.hex()
            ),
            "normalizer_id": self.normalizer_id,
            "normalizer_source_identity": self.normalizer_source_identity,
            "observable_labels": list(self.observable_labels),
            "principal_angles_radians_hex": [
                value.hex() for value in self.principal_angles_radians
            ],
            "schema": "HTT_LOCAL_GLOBAL_COMPATIBILITY_INPUT_V1",
            "separation_threshold_radians_hex": (
                self.separation_threshold_radians.hex()
            ),
            "source_report_id": self.source_report_id,
            "status": self.status.value,
        }

    def _assert_identity_sealed(self) -> None:
        _assert_sealed(
            self._payload_unchecked(),
            self._identity_seal,
            name="local/global compatibility input",
        )

    def as_payload(self) -> dict[str, object]:
        self._assert_identity_sealed()
        return {**self._payload_unchecked(), "content_id": self._identity_seal}


def _build_local_global_compatibility_input(
    *,
    source_report_id: str,
    status: LocalGlobalCompatibility | str,
    local_rank: int | None,
    global_rank: int | None,
    joint_rank: int | None,
    principal_angles_radians: Sequence[object],
    minimum_principal_angle_radians: object | None,
    separation_threshold_radians: object,
    direct_sum: bool | None,
    observable_labels: Sequence[str],
    covariance_id: str,
    mask_id: str,
    normalizer_id: str,
    normalizer_source_identity: str,
    local_provider_id: str,
    global_provider_id: str,
    local_response_id: str | None,
    global_response_id: str | None,
    joint_transfer_id: str | None,
    assumptions: Sequence[str],
) -> LocalGlobalCompatibilityInput:
    """Layer-private constructor used by the HTT replay adapter."""

    try:
        resolved_status = (
            status
            if isinstance(status, LocalGlobalCompatibility)
            else LocalGlobalCompatibility(str(status))
        )
    except ValueError as exc:
        raise AnisotropyTypeReportError(
            "unknown local/global compatibility status"
        ) from exc
    return LocalGlobalCompatibilityInput(
        source_report_id=source_report_id,
        status=resolved_status,
        local_rank=local_rank,
        global_rank=global_rank,
        joint_rank=joint_rank,
        principal_angles_radians=tuple(
            _nonnegative(value, "principal_angles_radians")
            for value in principal_angles_radians
        ),
        minimum_principal_angle_radians=(
            None
            if minimum_principal_angle_radians is None
            else _nonnegative(
                minimum_principal_angle_radians,
                "minimum_principal_angle_radians",
            )
        ),
        separation_threshold_radians=_nonnegative(
            separation_threshold_radians,
            "separation_threshold_radians",
        ),
        direct_sum=direct_sum,
        observable_labels=tuple(observable_labels),
        covariance_id=covariance_id,
        mask_id=mask_id,
        normalizer_id=normalizer_id,
        normalizer_source_identity=normalizer_source_identity,
        local_provider_id=local_provider_id,
        global_provider_id=global_provider_id,
        local_response_id=local_response_id,
        global_response_id=global_response_id,
        joint_transfer_id=joint_transfer_id,
        assumptions=tuple(assumptions),
        _construction_token=_LOCAL_GLOBAL_TOKEN,
    )


def _revalidate_response_class(
    item: ResponseClassManifoldSpec,
) -> ResponseClassManifoldSpec:
    if type(item) is not ResponseClassManifoldSpec:
        raise AnisotropyTypeReportError(
            "open-set classes must be exact ResponseClassManifoldSpec values"
        )
    rebuilt = build_response_class_manifold(
        class_id=item.class_id,
        support_kind=item.support_kind,
        provider_id=item.provider_id,
        observable_labels=item.observable_labels,
        convention_id=item.convention_id,
        nuisance_policy_id=item.nuisance_policy_id,
        support_nodes=item.support_nodes,
        transfer_source=item.transfer_source,
        source_semantics=item.source_semantics,
        source_response_id=item.source_response_id,
    )
    original = item.as_payload()
    replay = rebuilt.as_payload()
    original.pop("duplicate_node_count")
    replay.pop("duplicate_node_count")
    if original != replay:
        raise AnisotropyTypeReportError(
            f"response class {item.class_id} failed canonical replay"
        )
    return item


def _validate_registered_response_class_namespace(
    classes: tuple[ResponseClassManifoldSpec, ...],
) -> None:
    for item in classes:
        expected = _REGISTERED_RESPONSE_CLASS_ID[item.source_semantics]
        if item.class_id != expected:
            raise AnisotropyTypeReportError(
                "PR-267 accepts only the exact registered neutral/local/global "
                "response-class identifiers; "
                f"{item.source_semantics.value} requires {expected!r}"
            )


def _revalidate_reopening(
    item: ReopeningObservableSpec,
    classes: tuple[ResponseClassManifoldSpec, ...],
) -> ReopeningObservableSpec:
    if type(item) is not ReopeningObservableSpec:
        raise AnisotropyTypeReportError(
            "reopening observables must be exact ReopeningObservableSpec values"
        )
    responses: Mapping[str, Mapping[str, Sequence[object]]] | None
    if not item.provider_available:
        responses = None
    else:
        responses = {
            class_id: {node_id: values for node_id, values in rows}
            for class_id, rows in item.class_node_responses
        }
    rebuilt = build_reopening_observable_spec(
        observable_id=item.observable_id,
        classes=classes,
        added_observable_labels=item.added_observable_labels,
        responses_by_class_and_node=responses,
        joint_covariance=item.joint_covariance,
        joint_nuisance_response=item.joint_nuisance_response,
        joint_nuisance_policy_id=item.joint_nuisance_policy_id,
        convention_id=item.convention_id,
    )
    if rebuilt.as_payload() != item.as_payload():
        raise AnisotropyTypeReportError(
            f"reopening observable {item.observable_id} failed replay"
        )
    return item


@dataclass(frozen=True)
class OpenSetReplayInputs:
    """All exact inputs required to recompute one PR-258 classification."""

    classification_report: OpenSetClassificationReport
    classes: tuple[ResponseClassManifoldSpec, ...]
    equivalence_report: ResponseEquivalenceClassReport
    reopening_observables: tuple[ReopeningObservableSpec, ...]
    observation: tuple[float, ...]
    covariance: tuple[tuple[float, ...], ...]
    nuisance_tangent: tuple[tuple[float, ...], ...] | None
    source_separation_gate: SourceSeparationGate
    absolute_tolerance: float
    relative_tolerance: float
    _construction_token: InitVar[object] = None
    _identity_seal: str = field(init=False, repr=False, compare=False)

    def __post_init__(self, _construction_token: object) -> None:
        if _construction_token is not _OPEN_SET_TOKEN:
            raise AnisotropyTypeReportError(
                "OpenSetReplayInputs must be factory-built"
            )
        classes = tuple(
            _revalidate_response_class(item) for item in self.classes
        )
        if not classes:
            raise AnisotropyTypeReportError("open-set classes must not be empty")
        _validate_registered_response_class_namespace(classes)
        reopenings = tuple(
            _revalidate_reopening(item, classes)
            for item in self.reopening_observables
        )
        observation = _vector(self.observation, "observation")
        dimension = len(classes[0].observable_labels)
        if len(observation) != dimension:
            raise AnisotropyTypeReportError(
                "observation dimension must match response classes"
            )
        covariance = _matrix(
            self.covariance,
            "covariance",
            rows=dimension,
            columns=dimension,
        )
        nuisance = _optional_matrix(
            self.nuisance_tangent,
            "nuisance_tangent",
            rows=dimension,
        )
        absolute = _nonnegative(
            self.absolute_tolerance,
            "absolute_tolerance",
        )
        relative = _nonnegative(
            self.relative_tolerance,
            "relative_tolerance",
        )
        if absolute == 0.0 or relative == 0.0:
            raise AnisotropyTypeReportError(
                "open-set tolerances must be positive"
            )
        if type(self.equivalence_report) is not ResponseEquivalenceClassReport:
            raise AnisotropyTypeReportError(
                "equivalence_report must be an exact PR-258 report"
            )
        if type(self.classification_report) is not OpenSetClassificationReport:
            raise AnisotropyTypeReportError(
                "classification_report must be an exact PR-258 report"
            )
        if type(self.source_separation_gate) is not SourceSeparationGate:
            raise AnisotropyTypeReportError(
                "source_separation_gate must be factory-derived"
            )
        object.__setattr__(self, "classes", classes)
        object.__setattr__(self, "reopening_observables", reopenings)
        object.__setattr__(self, "observation", observation)
        object.__setattr__(self, "covariance", covariance)
        object.__setattr__(self, "nuisance_tangent", nuisance)
        object.__setattr__(self, "absolute_tolerance", absolute)
        object.__setattr__(self, "relative_tolerance", relative)
        self._replay_unsealed()
        object.__setattr__(
            self,
            "_identity_seal",
            _sha256_payload(self._payload_unchecked()),
        )

    def _replay_unsealed(self) -> OpenSetClassificationReport:
        rebuilt_equivalence = build_response_equivalence_report(
            classes=self.classes,
            covariance=self.covariance,
            nuisance_tangent=self.nuisance_tangent,
            equivalence_squared_distance_tolerance=(
                self.equivalence_report.equivalence_squared_distance_tolerance
            ),
            absolute_tolerance=self.absolute_tolerance,
            relative_tolerance=self.relative_tolerance,
            reopening_observables=self.reopening_observables,
        )
        if (
            rebuilt_equivalence.as_payload()
            != self.equivalence_report.as_payload()
        ):
            raise AnisotropyTypeReportError(
                "open-set equivalence report failed exact replay"
            )
        rebuilt = classify_open_set_response(
            observation=self.observation,
            classes=self.classes,
            equivalence_report=rebuilt_equivalence,
            covariance=self.covariance,
            nuisance_tangent=self.nuisance_tangent,
            unknown_squared_distance_threshold=(
                self.classification_report.unknown_squared_distance_threshold
            ),
            decision_squared_margin=(
                self.classification_report.decision_squared_margin
            ),
            covariance_null_tolerance=(
                self.classification_report.covariance_null_tolerance
            ),
            absolute_tolerance=self.absolute_tolerance,
            relative_tolerance=self.relative_tolerance,
            source_separation_gate=self.source_separation_gate,
        )
        if rebuilt.as_payload() != self.classification_report.as_payload():
            raise AnisotropyTypeReportError(
                "open-set classification report failed exact replay"
            )
        return rebuilt

    def replay(self) -> OpenSetClassificationReport:
        self._assert_identity_sealed()
        return self._replay_unsealed()

    @property
    def content_id(self) -> str:
        self._assert_identity_sealed()
        return self._identity_seal

    def _payload_unchecked(self) -> dict[str, object]:
        return {
            "absolute_tolerance_hex": self.absolute_tolerance.hex(),
            "classes": [item.as_payload() for item in self.classes],
            "classification_report": self.classification_report.as_payload(),
            "covariance_hex": [
                [value.hex() for value in row] for row in self.covariance
            ],
            "equivalence_report": self.equivalence_report.as_payload(),
            "nuisance_tangent_hex": (
                None
                if self.nuisance_tangent is None
                else [
                    [value.hex() for value in row]
                    for row in self.nuisance_tangent
                ]
            ),
            "observation_hex": [value.hex() for value in self.observation],
            "relative_tolerance_hex": self.relative_tolerance.hex(),
            "reopening_observables": [
                item.as_payload() for item in self.reopening_observables
            ],
            "schema": "HTT_OPEN_SET_REPLAY_INPUTS_V1",
            "source_separation_gate": self.source_separation_gate.as_payload(),
        }

    def _assert_identity_sealed(self) -> None:
        _assert_sealed(
            self._payload_unchecked(),
            self._identity_seal,
            name="open-set replay inputs",
        )

    def as_payload(self) -> dict[str, object]:
        self._assert_identity_sealed()
        return {**self._payload_unchecked(), "content_id": self._identity_seal}


def build_open_set_replay_inputs(
    *,
    classification_report: OpenSetClassificationReport,
    classes: Sequence[ResponseClassManifoldSpec],
    equivalence_report: ResponseEquivalenceClassReport,
    reopening_observables: Sequence[ReopeningObservableSpec] = (),
    observation: Sequence[object],
    covariance: Sequence[Sequence[object]],
    nuisance_tangent: Sequence[Sequence[object]] | None,
    source_separation_gate: SourceSeparationGate,
    absolute_tolerance: object,
    relative_tolerance: object,
) -> OpenSetReplayInputs:
    return OpenSetReplayInputs(
        classification_report=classification_report,
        classes=tuple(classes),
        equivalence_report=equivalence_report,
        reopening_observables=tuple(reopening_observables),
        observation=tuple(observation),  # type: ignore[arg-type]
        covariance=tuple(tuple(row) for row in covariance),  # type: ignore[arg-type]
        nuisance_tangent=(
            None
            if nuisance_tangent is None
            else tuple(tuple(row) for row in nuisance_tangent)  # type: ignore[arg-type]
        ),
        source_separation_gate=source_separation_gate,
        absolute_tolerance=_real(absolute_tolerance, "absolute_tolerance"),
        relative_tolerance=_real(relative_tolerance, "relative_tolerance"),
        _construction_token=_OPEN_SET_TOKEN,
    )


def _geometry_status(
    state: JointAnisotropyState,
) -> tuple[GeometryInformationStatus, tuple[str, ...]]:
    geometry = state.geometry_state
    fields = (
        "spatial_curvature_stf5",
        "electric_weyl_stf5",
        "magnetic_weyl_stf5",
        "anisotropic_stress_stf5",
    )
    missing = tuple(
        name
        for name in fields
        if type(getattr(geometry, name)) is MissingComponent
    )
    if not missing:
        return GeometryInformationStatus.COMPLETE, ()
    if len(missing) == len(fields):
        return GeometryInformationStatus.MISSING, missing
    return GeometryInformationStatus.PARTIAL, missing


def _compatibility_status(
    *,
    geometry_status: GeometryInformationStatus,
    orbit_missing_components: tuple[str, ...],
    anchored_status: AnchoredResponseStatus,
    response_rank: int | None,
    parameter_dimension: int | None,
    principal_angle_status: PrincipalAngleStatus,
    local_global_status: LocalGlobalCompatibility,
    open_set_status: OpenSetClassificationStatus,
    exceedance_status: ExceedanceStatus,
    depth_status: DepthCoherenceStatus,
) -> AnisotropyCompatibilityStatus:
    if (
        geometry_status is not GeometryInformationStatus.COMPLETE
        or orbit_missing_components
        or depth_status is not DepthCoherenceStatus.DEFINED
        or exceedance_status
        not in {
            ExceedanceStatus.DEFINED_POINT,
            ExceedanceStatus.DEFINED_ENVELOPE,
        }
        or local_global_status
        is LocalGlobalCompatibility.MISSING_RESPONSE_PROVIDER
        or open_set_status
        is OpenSetClassificationStatus.MISSING_RESPONSE_PROVIDER
    ):
        return AnisotropyCompatibilityStatus.PARTIAL_DIAGNOSTIC
    if open_set_status in {
        OpenSetClassificationStatus.UNKNOWN_CLASS,
        OpenSetClassificationStatus.NEEDS_NATIVE,
    }:
        return AnisotropyCompatibilityStatus.UNKNOWN
    identified_rank = (
        anchored_status is AnchoredResponseStatus.MEASURED
        and response_rank is not None
        and parameter_dimension is not None
        and response_rank == parameter_dimension
        and principal_angle_status is PrincipalAngleStatus.DEFINED
    )
    if (
        identified_rank
        and local_global_status
        is LocalGlobalCompatibility.SEPARABLE_CANDIDATE
        and open_set_status
        is OpenSetClassificationStatus.RESPONSE_CLASS_CANDIDATE
    ):
        return (
            AnisotropyCompatibilityStatus.RESPONSE_COMPATIBILITY_CANDIDATE
        )
    return AnisotropyCompatibilityStatus.INDETERMINATE


@dataclass(frozen=True)
class AnisotropyTypeReport:
    report_id: str
    source_state_id: str
    orbit_report_id: str
    orbit_spec_id: str
    orbit_stratum: str
    orbit_stabilizer_status: str
    orbit_proof_statuses: tuple[str, ...]
    orbit_missing_components: tuple[str, ...]
    anchored_response_id: str
    anchored_status: AnchoredResponseStatus
    response_rank: int | None
    response_parameter_dimension: int | None
    anchored_principal_angle_status: PrincipalAngleStatus
    anchored_principal_angles_radians: tuple[float, ...]
    local_global_input_id: str
    local_global_status: LocalGlobalCompatibility
    local_global_principal_angles_radians: tuple[float, ...]
    open_set_replay_id: str
    open_set_report_id: str
    open_set_status: OpenSetClassificationStatus
    response_class_ids: tuple[str, ...]
    conditional_exceedance_id: str
    conditional_exceedance_status: ExceedanceStatus
    conditional_exceedance_lane: str | None
    depth_path_id: str
    depth_coherence_id: str
    depth_coherence_status: DepthCoherenceStatus
    depth_mean_normalized_score: float | None
    geometry_information_status: GeometryInformationStatus
    missingness: tuple[str, ...]
    compatibility_status: AnisotropyCompatibilityStatus
    owner: str = "COMMON"
    claim_ceiling: str = ANISOTROPY_TYPE_CLAIM_CEILING
    roadmap_claim_level: str = ANISOTROPY_TYPE_ROADMAP_LEVEL
    family_identification_gate: str = ANISOTROPY_TYPE_FAMILY_GATE
    allowed_use: tuple[str, ...] = ANISOTROPY_TYPE_ALLOWED_USE
    forbidden_use: tuple[str, ...] = ANISOTROPY_TYPE_FORBIDDEN_USE
    _construction_token: InitVar[object] = None
    _identity_seal: str = field(init=False, repr=False, compare=False)

    def __post_init__(self, _construction_token: object) -> None:
        if _construction_token is not _REPORT_TOKEN:
            raise AnisotropyTypeReportError(
                "AnisotropyTypeReport must be factory-built"
            )
        for name in (
            "report_id",
            "source_state_id",
            "orbit_report_id",
            "orbit_spec_id",
            "orbit_stratum",
            "orbit_stabilizer_status",
            "anchored_response_id",
            "local_global_input_id",
            "open_set_replay_id",
            "open_set_report_id",
            "conditional_exceedance_id",
            "depth_path_id",
            "depth_coherence_id",
        ):
            _text(getattr(self, name), name)
        if isinstance(self.orbit_proof_statuses, (str, bytes)):
            raise AnisotropyTypeReportError(
                "orbit_proof_statuses must be a sequence of text"
            )
        proof_statuses = tuple(
            _text(value, "orbit_proof_statuses")
            for value in self.orbit_proof_statuses
        )
        if proof_statuses != (
            CatalogueProofStatus.UNPROVEN.value,
            CatalogueProofStatus.UNPROVEN.value,
            CatalogueProofStatus.UNPROVEN.value,
        ):
            raise AnisotropyTypeReportError(
                "orbit proof statuses must remain three UNPROVEN values"
            )
        orbit_missing = _texts(
            self.orbit_missing_components,
            "orbit_missing_components",
            empty_ok=True,
        )
        for enum_value, enum_type, name in (
            (self.anchored_status, AnchoredResponseStatus, "anchored_status"),
            (
                self.anchored_principal_angle_status,
                PrincipalAngleStatus,
                "anchored_principal_angle_status",
            ),
            (
                self.local_global_status,
                LocalGlobalCompatibility,
                "local_global_status",
            ),
            (
                self.open_set_status,
                OpenSetClassificationStatus,
                "open_set_status",
            ),
            (
                self.conditional_exceedance_status,
                ExceedanceStatus,
                "conditional_exceedance_status",
            ),
            (
                self.depth_coherence_status,
                DepthCoherenceStatus,
                "depth_coherence_status",
            ),
            (
                self.geometry_information_status,
                GeometryInformationStatus,
                "geometry_information_status",
            ),
            (
                self.compatibility_status,
                AnisotropyCompatibilityStatus,
                "compatibility_status",
            ),
        ):
            if type(enum_value) is not enum_type:
                raise AnisotropyTypeReportError(
                    f"{name} must use {enum_type.__name__}"
                )
        for name in ("response_rank", "response_parameter_dimension"):
            value = getattr(self, name)
            if value is not None:
                object.__setattr__(self, name, _integer(value, name))
        anchored_angles = tuple(
            _nonnegative(value, "anchored_principal_angles_radians")
            for value in self.anchored_principal_angles_radians
        )
        local_angles = tuple(
            _nonnegative(value, "local_global_principal_angles_radians")
            for value in self.local_global_principal_angles_radians
        )
        response_ids = _texts(
            self.response_class_ids,
            "response_class_ids",
            empty_ok=True,
        )
        if any(
            value not in _REGISTERED_RESPONSE_CLASS_IDS
            for value in response_ids
        ):
            raise AnisotropyTypeReportError(
                "report response-class identifiers must use the exact "
                "registered neutral/local/global vocabulary"
            )
        if self.open_set_status in {
            OpenSetClassificationStatus.UNKNOWN_CLASS,
            OpenSetClassificationStatus.NEEDS_NATIVE,
            OpenSetClassificationStatus.MISSING_RESPONSE_PROVIDER,
            OpenSetClassificationStatus.OUTSIDE_SUPPORTED_QUOTIENT,
        } and response_ids:
            raise AnisotropyTypeReportError(
                "unknown or unavailable open-set outcomes carry no response label"
            )
        mean = _optional_nonnegative(
            self.depth_mean_normalized_score,
            "depth_mean_normalized_score",
        )
        if (
            self.depth_coherence_status is DepthCoherenceStatus.UNAVAILABLE
            and mean is not None
        ):
            raise AnisotropyTypeReportError(
                "unavailable depth coherence must not carry a score"
            )
        if self.conditional_exceedance_lane is not None:
            _text(
                self.conditional_exceedance_lane,
                "conditional_exceedance_lane",
            )
        missingness = _texts(
            self.missingness,
            "missingness",
            empty_ok=True,
        )
        expected = _compatibility_status(
            geometry_status=self.geometry_information_status,
            orbit_missing_components=orbit_missing,
            anchored_status=self.anchored_status,
            response_rank=self.response_rank,
            parameter_dimension=self.response_parameter_dimension,
            principal_angle_status=self.anchored_principal_angle_status,
            local_global_status=self.local_global_status,
            open_set_status=self.open_set_status,
            exceedance_status=self.conditional_exceedance_status,
            depth_status=self.depth_coherence_status,
        )
        if self.compatibility_status is not expected:
            raise AnisotropyTypeReportError(
                "compatibility status does not match abstention precedence"
            )
        if (
            self.compatibility_status
            is AnisotropyCompatibilityStatus.RESPONSE_COMPATIBILITY_CANDIDATE
            and len(response_ids) != 1
        ):
            raise AnisotropyTypeReportError(
                "a response compatibility candidate requires one safe class id"
            )
        if self.owner != "COMMON":
            raise AnisotropyTypeReportError("report owner must remain COMMON")
        if self.claim_ceiling != ANISOTROPY_TYPE_CLAIM_CEILING:
            raise AnisotropyTypeReportError("claim ceiling drifted")
        if self.roadmap_claim_level != ANISOTROPY_TYPE_ROADMAP_LEVEL:
            raise AnisotropyTypeReportError("roadmap claim level drifted")
        if self.family_identification_gate != ANISOTROPY_TYPE_FAMILY_GATE:
            raise AnisotropyTypeReportError(
                "family-identification gate must remain blocked"
            )
        if tuple(self.allowed_use) != ANISOTROPY_TYPE_ALLOWED_USE:
            raise AnisotropyTypeReportError("allowed-use lane drifted")
        if tuple(self.forbidden_use) != ANISOTROPY_TYPE_FORBIDDEN_USE:
            raise AnisotropyTypeReportError("forbidden-use lane drifted")
        object.__setattr__(self, "orbit_proof_statuses", proof_statuses)
        object.__setattr__(self, "orbit_missing_components", orbit_missing)
        object.__setattr__(
            self,
            "anchored_principal_angles_radians",
            anchored_angles,
        )
        object.__setattr__(
            self,
            "local_global_principal_angles_radians",
            local_angles,
        )
        object.__setattr__(self, "response_class_ids", response_ids)
        object.__setattr__(self, "depth_mean_normalized_score", mean)
        object.__setattr__(self, "missingness", missingness)
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
            "anchored_principal_angle_status": (
                self.anchored_principal_angle_status.value
            ),
            "anchored_principal_angles_radians_hex": [
                value.hex()
                for value in self.anchored_principal_angles_radians
            ],
            "anchored_response_id": self.anchored_response_id,
            "anchored_status": self.anchored_status.value,
            "claim_ceiling": self.claim_ceiling,
            "compatibility_status": self.compatibility_status.value,
            "conditional_exceedance_id": self.conditional_exceedance_id,
            "conditional_exceedance_lane": self.conditional_exceedance_lane,
            "conditional_exceedance_status": (
                self.conditional_exceedance_status.value
            ),
            "depth_coherence_id": self.depth_coherence_id,
            "depth_coherence_status": self.depth_coherence_status.value,
            "depth_mean_normalized_score_hex": (
                None
                if self.depth_mean_normalized_score is None
                else self.depth_mean_normalized_score.hex()
            ),
            "depth_path_id": self.depth_path_id,
            "family_identification_gate": self.family_identification_gate,
            "forbidden_use": list(self.forbidden_use),
            "geometry_information_status": (
                self.geometry_information_status.value
            ),
            "local_global_input_id": self.local_global_input_id,
            "local_global_principal_angles_radians_hex": [
                value.hex()
                for value in self.local_global_principal_angles_radians
            ],
            "local_global_status": self.local_global_status.value,
            "missingness": list(self.missingness),
            "open_set_replay_id": self.open_set_replay_id,
            "open_set_report_id": self.open_set_report_id,
            "open_set_status": self.open_set_status.value,
            "orbit_missing_components": list(self.orbit_missing_components),
            "orbit_proof_statuses": list(self.orbit_proof_statuses),
            "orbit_report_id": self.orbit_report_id,
            "orbit_spec_id": self.orbit_spec_id,
            "orbit_stabilizer_status": self.orbit_stabilizer_status,
            "orbit_stratum": self.orbit_stratum,
            "owner": self.owner,
            "report_id": self.report_id,
            "response_class_ids": list(self.response_class_ids),
            "response_parameter_dimension": self.response_parameter_dimension,
            "response_rank": self.response_rank,
            "roadmap_claim_level": self.roadmap_claim_level,
            "schema": "HTT_ANISOTROPY_TYPE_REPORT_V1",
            "source_state_id": self.source_state_id,
        }

    def _assert_identity_sealed(self) -> None:
        _assert_sealed(
            self._payload_unchecked(),
            self._identity_seal,
            name="anisotropy type report",
        )

    def as_payload(self) -> dict[str, object]:
        self._assert_identity_sealed()
        return {**self._payload_unchecked(), "content_id": self._identity_seal}


def _replay_anchored_response(
    report: AnchoredResponseGeometryReport,
    *,
    normalizer: NormalizerSpec,
    comparison_response: object | None,
) -> AnchoredResponseGeometryReport:
    if type(report) is not AnchoredResponseGeometryReport:
        raise AnisotropyTypeReportError(
            "anchored_response must be an exact PR-255 report"
        )
    if report.relative_tolerance is None:
        raise AnisotropyTypeReportError(
            "PR-255 MISSING_INPUT reports cannot be exactly replayed because "
            "their discarded input values are not available"
        )
    rebuilt = measure_anchored_response_geometry(
        response=report.response_replay_matrix,
        covariance=report.covariance_replay_matrix,
        normalizer=normalizer,
        parameter_labels=report.parameter_labels,
        transfer_id=report.transfer_id,
        transfer_source=report.transfer_source,
        transfer_spec=report.transfer_spec,
        mask_id=report.mask_id,
        covariance_id=report.covariance_id,
        nuisance_response=report.nuisance_replay_matrix,
        comparison_response=comparison_response,
        rtol=report.relative_tolerance,
    )
    if rebuilt != report or rebuilt.as_payload() != report.as_payload():
        raise AnisotropyTypeReportError(
            "anchored response failed exact replay"
        )
    return rebuilt


def _response_class_ids(
    report: OpenSetClassificationReport,
) -> tuple[str, ...]:
    if (
        report.status
        is OpenSetClassificationStatus.RESPONSE_CLASS_CANDIDATE
    ):
        if report.candidate_class_id is None:
            raise AnisotropyTypeReportError(
                "response candidate is missing its class id"
            )
        return (report.candidate_class_id,)
    if report.status in {
        OpenSetClassificationStatus.EQUIVALENCE_CLASS,
        OpenSetClassificationStatus.TYPE_UNIDENTIFIED,
    }:
        return tuple(report.returned_equivalence_class)
    return ()


def build_anisotropy_type_report(
    *,
    report_id: str,
    joint_state: JointAnisotropyState,
    orbit_report: OrbitCatalogueV3Report,
    anchored_response: AnchoredResponseGeometryReport,
    anchored_normalizer: NormalizerSpec,
    anchored_comparison_response: object | None,
    local_global: LocalGlobalCompatibilityInput,
    open_set: OpenSetReplayInputs,
    conditional_exceedance: ConditionalExceedanceProfile,
    depth_path: DepthPath,
    depth_coherence: DepthCoherenceReport,
) -> AnisotropyTypeReport:
    """Build one replay-bound report with deterministic abstention precedence."""

    if type(joint_state) is not JointAnisotropyState:
        raise TypeError("joint_state must be an exact JointAnisotropyState")
    state_payload = joint_state.to_payload()
    state = JointAnisotropyState.from_payload(state_payload)
    if state.to_payload() != state_payload:
        raise AnisotropyTypeReportError("joint state failed exact replay")
    orbit = revalidate_orbit_catalogue_v3(orbit_report, state)
    anchored = _replay_anchored_response(
        anchored_response,
        normalizer=anchored_normalizer,
        comparison_response=anchored_comparison_response,
    )
    if type(local_global) is not LocalGlobalCompatibilityInput:
        raise TypeError(
            "local_global must be a LocalGlobalCompatibilityInput"
        )
    local_global.as_payload()
    if type(open_set) is not OpenSetReplayInputs:
        raise TypeError("open_set must be an OpenSetReplayInputs")
    classification = open_set.replay()
    source_gate = open_set.source_separation_gate
    if source_gate.status is not SourceSeparationGateStatus.NOT_APPLICABLE:
        if (
            source_gate.report_id != local_global.source_report_id
            or source_gate.status.value != local_global.status.value
        ):
            raise AnisotropyTypeReportError(
                "PR-256 local/global replay does not match the PR-258 source gate"
            )
    if type(conditional_exceedance) is not ConditionalExceedanceProfile:
        raise TypeError(
            "conditional_exceedance must be a ConditionalExceedanceProfile"
        )
    conditional_exceedance.as_payload()
    path = revalidate_depth_path(depth_path)
    if type(depth_coherence) is not DepthCoherenceReport:
        raise TypeError(
            "depth_coherence must be an exact DepthCoherenceReport"
        )
    depth_coherence.as_payload()
    if depth_coherence.path_content_id != path.content_id:
        raise AnisotropyTypeReportError(
            "depth coherence is not bound to the exact depth path"
        )
    geometry_status, missing_geometry = _geometry_status(state)
    orbit_missing = tuple(orbit.missing_components)
    status = _compatibility_status(
        geometry_status=geometry_status,
        orbit_missing_components=orbit_missing,
        anchored_status=anchored.status,
        response_rank=anchored.rank,
        parameter_dimension=anchored.parameter_dimension,
        principal_angle_status=anchored.principal_angles.status,
        local_global_status=local_global.status,
        open_set_status=classification.status,
        exceedance_status=conditional_exceedance.status,
        depth_status=depth_coherence.status,
    )
    missingness = tuple(
        dict.fromkeys(
            (
                *(f"geometry:{name}" for name in missing_geometry),
                *(
                    f"orbit:{name}"
                    for name in orbit_missing
                ),
                *(
                    ()
                    if depth_coherence.status is DepthCoherenceStatus.DEFINED
                    else (f"depth:{depth_coherence.status.value}",)
                ),
                *(
                    ()
                    if conditional_exceedance.status
                    in {
                        ExceedanceStatus.DEFINED_POINT,
                        ExceedanceStatus.DEFINED_ENVELOPE,
                    }
                    else (
                        "conditional_exceedance:"
                        f"{conditional_exceedance.status.value}",
                    )
                ),
                *(
                    ()
                    if local_global.status
                    is not LocalGlobalCompatibility.MISSING_RESPONSE_PROVIDER
                    else ("local_global:MISSING_RESPONSE_PROVIDER",)
                ),
                *(
                    ()
                    if classification.status
                    is not OpenSetClassificationStatus.MISSING_RESPONSE_PROVIDER
                    else ("open_set:MISSING_RESPONSE_PROVIDER",)
                ),
            )
        )
    )
    orbit_payload = orbit.as_payload()
    anchored_payload = anchored.as_payload()
    proof_statuses = (
        orbit.spec.generic_orbit_separation_status.value,
        orbit.spec.degree_completeness_status.value,
        orbit.spec.global_chart_completeness_status.value,
    )
    return AnisotropyTypeReport(
        report_id=report_id,
        source_state_id=state.content_id,
        orbit_report_id=_sha256_payload(orbit_payload),
        orbit_spec_id=orbit.spec.spec_id,
        orbit_stratum=orbit.stratum.status.value,
        orbit_stabilizer_status=orbit.stabilizer.joint_status.value,
        orbit_proof_statuses=proof_statuses,
        orbit_missing_components=orbit_missing,
        anchored_response_id=_sha256_payload(anchored_payload),
        anchored_status=anchored.status,
        response_rank=anchored.rank,
        response_parameter_dimension=anchored.parameter_dimension,
        anchored_principal_angle_status=anchored.principal_angles.status,
        anchored_principal_angles_radians=(
            anchored.principal_angles.angles_radians
        ),
        local_global_input_id=local_global.content_id,
        local_global_status=local_global.status,
        local_global_principal_angles_radians=(
            local_global.principal_angles_radians
        ),
        open_set_replay_id=open_set.content_id,
        open_set_report_id=classification.report_id,
        open_set_status=classification.status,
        response_class_ids=_response_class_ids(classification),
        conditional_exceedance_id=conditional_exceedance.content_id,
        conditional_exceedance_status=conditional_exceedance.status,
        conditional_exceedance_lane=(
            None
            if conditional_exceedance.lane is None
            else conditional_exceedance.lane.value
        ),
        depth_path_id=path.content_id,
        depth_coherence_id=depth_coherence.content_id,
        depth_coherence_status=depth_coherence.status,
        depth_mean_normalized_score=(
            depth_coherence.mean_normalized_score
        ),
        geometry_information_status=geometry_status,
        missingness=missingness,
        compatibility_status=status,
        _construction_token=_REPORT_TOKEN,
    )


__all__ = [
    "ANISOTROPY_TYPE_ALLOWED_USE",
    "ANISOTROPY_TYPE_CLAIM_CEILING",
    "ANISOTROPY_TYPE_FAMILY_GATE",
    "ANISOTROPY_TYPE_FORBIDDEN_USE",
    "ANISOTROPY_TYPE_ROADMAP_LEVEL",
    "AnisotropyCompatibilityStatus",
    "AnisotropyTypeReport",
    "AnisotropyTypeReportError",
    "GeometryInformationStatus",
    "LocalGlobalCompatibility",
    "LocalGlobalCompatibilityInput",
    "OpenSetReplayInputs",
    "build_anisotropy_type_report",
    "build_open_set_replay_inputs",
]
