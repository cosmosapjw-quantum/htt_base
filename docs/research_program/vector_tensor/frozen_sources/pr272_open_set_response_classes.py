"""Typed pre-native response classes, equivalence quotients and abstention.

This module operates on finite, preregistered analytic or synthetic response
supports.  Those supports are software-validation objects: they are not
Bianchi families, native solver manifolds, likelihoods, or observations.

All separations are computed on one covariance-supported, nuisance-projected
quotient.  Overlapping supports are collapsed before classification, unknown
inputs remain unknown, covariance-null residuals remain visible, and a future
native adapter cannot emit response values while its status is
``NEEDS_NATIVE``.
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

from common.anchor_geometry import (
    NormalizerKind,
    NormalizerPurpose,
    NormalizerSpec,
)
from common.anchored_response_geometry import (
    AnchoredResponseGeometryError,
    AnchoredResponseStatus,
    anchored_numeric_content_id,
    measure_anchored_response_geometry,
)
from common.transfer_registry import TransferSource


class OpenSetResponseError(ValueError):
    """Raised when an open-set response contract is incomplete or inconsistent."""


class _StringEnum(str, Enum):
    def __str__(self) -> str:
        return self.value


class ResponseSupportKind(_StringEnum):
    FINITE_ANALYTIC_SUPPORT = "FINITE_ANALYTIC_SUPPORT"
    FINITE_SYNTHETIC_SUPPORT = "FINITE_SYNTHETIC_SUPPORT"
    NEEDS_NATIVE = "NEEDS_NATIVE"


class ResponseEquivalenceStatus(_StringEnum):
    SEPARATED = "SEPARATED"
    EQUIVALENCE_CLASS = "EQUIVALENCE_CLASS"
    TYPE_UNIDENTIFIED = "TYPE_UNIDENTIFIED"
    MISSING_RESPONSE_PROVIDER = "MISSING_RESPONSE_PROVIDER"
    OUTSIDE_SUPPORTED_QUOTIENT = "OUTSIDE_SUPPORTED_QUOTIENT"


class ReopeningObservableStatus(_StringEnum):
    NOT_REQUIRED = "NOT_REQUIRED"
    REOPENED = "REOPENED"
    NEEDS_ADDITIONAL_OBSERVABLE = "NEEDS_ADDITIONAL_OBSERVABLE"
    MISSING_RESPONSE_PROVIDER = "MISSING_RESPONSE_PROVIDER"


class ResponseClassSourceSemantics(_StringEnum):
    NEUTRAL = "NEUTRAL"
    LOCAL_BOOST = "LOCAL_BOOST"
    GLOBAL_TILT = "GLOBAL_TILT"


class SourceSeparationGateStatus(_StringEnum):
    NOT_APPLICABLE = "NOT_APPLICABLE"
    SEPARABLE_CANDIDATE = "SEPARABLE_CANDIDATE"
    NON_IDENTIFIED = "NON_IDENTIFIED"
    SUM_ONLY = "SUM_ONLY"
    MISSING_RESPONSE_PROVIDER = "MISSING_RESPONSE_PROVIDER"


class OpenSetClassificationStatus(_StringEnum):
    RESPONSE_CLASS_CANDIDATE = "RESPONSE_CLASS_CANDIDATE"
    EQUIVALENCE_CLASS = "EQUIVALENCE_CLASS"
    TYPE_UNIDENTIFIED = "TYPE_UNIDENTIFIED"
    UNKNOWN_CLASS = "UNKNOWN_CLASS"
    NEEDS_NATIVE = "NEEDS_NATIVE"
    MISSING_RESPONSE_PROVIDER = "MISSING_RESPONSE_PROVIDER"
    OUTSIDE_SUPPORTED_QUOTIENT = "OUTSIDE_SUPPORTED_QUOTIENT"


class OpenSetBenchmarkStatus(_StringEnum):
    MEASURED_PASS = "MEASURED_PASS"
    MEASURED_FAIL = "MEASURED_FAIL"
    INCONCLUSIVE_MC_PRECISION = "INCONCLUSIVE_MC_PRECISION"


class FiniteSupportPerturbationKind(_StringEnum):
    EXACT_DUPLICATE = "EXACT_DUPLICATE"
    REFINEMENT = "REFINEMENT"
    EXPANSION = "EXPANSION"
    CONTRACTION = "CONTRACTION"
    BOUNDARY_RESTRICTION = "BOUNDARY_RESTRICTION"


_CLASS_TOKEN = object()
_EQUIVALENCE_TOKEN = object()
_CLASSIFICATION_TOKEN = object()
_BENCHMARK_TOKEN = object()
_NATIVE_TOKEN = object()
_REOPENING_TOKEN = object()
_SOURCE_GATE_TOKEN = object()
_SHA256_RE = re.compile(r"sha256:[0-9a-f]{64}\Z")
_CLASS_ID_RE = re.compile(r"response-class-[a-z0-9][a-z0-9-]*\Z")
_ALLOWED_USE = (
    "pre-native finite response-support diagnostic",
    "response-equivalence and reopening-observable audit",
    "synthetic open-set abstention benchmark",
)
_FORBIDDEN_USE = (
    "FLRW departure or geometry detection",
    "Bianchi family identification or ranking",
    "native solver or external-transfer validation",
    "posterior, Bayes factor, p-value, e-value, or evidence term",
)
_NATIVE_REQUIRED_FIELDS = (
    "native_solver_release",
    "native_solver_commit",
    "transfer_function_spec",
    "response_grid_identity",
    "parameter_domain_identity",
    "harmonic_convention",
    "sky_mask_covariance_contract",
    "validation_receipt",
)
PR258_MINIMUM_MC_REPLICATES = 20_000
PR258_MAXIMUM_MC_REPLICATES = 400_000
PR258_MAXIMUM_MCSE = 0.0025
PR258_METRIC_ID = "OBSERVABLE_COVARIANCE_SQUARED_DISTANCE_V1"
PR258_MACHINE_CLAIM_TIER = "diagnostic_only"
PR258_ROADMAP_CLAIM_LEVEL = "C2"
PR258_ARTIFACT_OWNER = "common"
PR258_ARTIFACT_SCOPE = (
    "pre_native_finite_synthetic_response_library_software_validation"
)
PR258_ARTIFACT_MODE = "internal_exploratory"
PR258_SKY_SUPPORT_STATUS = "not_applicable_synthetic_feature_space"
PR258_NULL_MOCK_STATUS = (
    "synthetic_generator_cells_only_not_observational_null_calibration"
)
PR258_COVARIANCE_STATUS = (
    "fixed_registered_synthetic_covariance_exact_bytes"
)


def _text(value: object, name: str) -> str:
    if not isinstance(value, str) or not value or value != value.strip():
        raise OpenSetResponseError(f"{name} must be non-empty trimmed text")
    return value


def _receipt(value: object, name: str) -> str:
    text = _text(value, name)
    if not _SHA256_RE.fullmatch(text):
        raise OpenSetResponseError(
            f"{name} must be a lowercase sha256 content identity"
        )
    return text


def _class_id(value: object, name: str = "class_id") -> str:
    if not isinstance(value, str) or not value or value != value.strip():
        raise OpenSetResponseError(
            f"{name} must use the response-class-* namespace"
        )
    text = value
    if not _CLASS_ID_RE.fullmatch(text):
        raise OpenSetResponseError(
            f"{name} must use the response-class-* namespace"
        )
    return text


def _texts(
    values: Sequence[object],
    name: str,
    *,
    empty_ok: bool = False,
) -> tuple[str, ...]:
    if isinstance(values, (str, bytes)):
        raise OpenSetResponseError(f"{name} must be a sequence")
    out = tuple(_text(value, f"{name}[{index}]") for index, value in enumerate(values))
    if not out and not empty_ok:
        raise OpenSetResponseError(f"{name} must not be empty")
    if len(set(out)) != len(out):
        raise OpenSetResponseError(f"{name} must be unique")
    return out


def _finite_real(value: object, name: str) -> float:
    if isinstance(value, (bool, np.bool_)) or isinstance(value, (str, bytes)):
        raise OpenSetResponseError(f"{name} must be a finite real")
    try:
        out = float(value)
    except (TypeError, ValueError, OverflowError) as exc:
        raise OpenSetResponseError(f"{name} must be a finite real") from exc
    if not math.isfinite(out):
        raise OpenSetResponseError(f"{name} must be finite")
    return out


def _nonnegative(value: object, name: str) -> float:
    out = _finite_real(value, name)
    if out < 0.0:
        raise OpenSetResponseError(f"{name} must be non-negative")
    return out


def _positive(value: object, name: str) -> float:
    out = _finite_real(value, name)
    if out <= 0.0:
        raise OpenSetResponseError(f"{name} must be positive")
    return out


def _positive_int(value: object, name: str) -> int:
    if isinstance(value, (bool, np.bool_)) or not isinstance(
        value, (int, np.integer)
    ):
        raise OpenSetResponseError(f"{name} must be an integer")
    out = int(value)
    if out <= 0:
        raise OpenSetResponseError(f"{name} must be positive")
    return out


def _array(
    value: object,
    name: str,
    *,
    ndim: int,
    columns: int | None = None,
) -> np.ndarray:
    if _contains_invalid_scalar(value):
        raise OpenSetResponseError(
            f"{name} must contain real, non-boolean numeric values"
        )
    raw = np.asarray(value)
    if raw.dtype.kind in {"b", "O", "U", "S", "c"}:
        raise OpenSetResponseError(
            f"{name} must contain real, non-boolean numeric values"
        )
    try:
        array = np.asarray(value, dtype=np.float64)
    except (TypeError, ValueError, OverflowError) as exc:
        raise OpenSetResponseError(
            f"{name} must contain real numeric values"
        ) from exc
    if array.ndim != ndim:
        raise OpenSetResponseError(f"{name} must have ndim={ndim}")
    if columns is not None and array.shape[-1] != columns:
        raise OpenSetResponseError(
            f"{name} must have {columns} columns"
        )
    if any(dimension <= 0 for dimension in array.shape):
        raise OpenSetResponseError(f"{name} must have positive dimensions")
    if not np.all(np.isfinite(array)):
        raise OpenSetResponseError(f"{name} must be finite")
    canonical = np.ascontiguousarray(array, dtype=np.float64)
    out = np.frombuffer(
        canonical.tobytes(order="C"),
        dtype=np.float64,
    ).reshape(canonical.shape)
    out.setflags(write=False)
    return out


def _contains_invalid_scalar(value: object) -> bool:
    if isinstance(value, (bool, np.bool_)):
        return True
    if isinstance(value, (complex, np.complexfloating)):
        return True
    if isinstance(value, (str, bytes, np.str_, np.bytes_)):
        return True
    if isinstance(value, np.ndarray):
        return value.dtype.kind in {"b", "c", "O", "S", "U"}
    if isinstance(value, (tuple, list)):
        return any(_contains_invalid_scalar(item) for item in value)
    return False


def _array_id(value: np.ndarray, *, role: str) -> str:
    digest = hashlib.sha256()
    digest.update(role.encode("ascii"))
    digest.update(b"\0")
    digest.update(str(value.shape).encode("ascii"))
    digest.update(b"\0")
    digest.update(np.ascontiguousarray(value).tobytes(order="C"))
    return f"sha256:{digest.hexdigest()}"


def _payload_id(payload: object) -> str:
    encoded = json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
    ).encode("ascii")
    return f"sha256:{hashlib.sha256(encoded).hexdigest()}"


def _canonical_support_nodes(value: object, *, columns: int) -> tuple[np.ndarray, int]:
    nodes = _array(value, "support_nodes", ndim=2, columns=columns)
    ordered_rows = sorted(
        (
            tuple(
                0.0 if float(item) == 0.0 else float(item)
                for item in row
            )
            for row in nodes
        ),
        key=lambda row: tuple(value.hex() for value in row),
    )
    unique_rows: list[tuple[float, ...]] = []
    seen: set[bytes] = set()
    for row in ordered_rows:
        row_bytes = np.asarray(row, dtype=np.float64).tobytes(order="C")
        if row_bytes not in seen:
            seen.add(row_bytes)
            unique_rows.append(row)
    canonical = _array(
        np.asarray(unique_rows, dtype=np.float64),
        "canonical_support_nodes",
        ndim=2,
        columns=columns,
    )
    return canonical, int(nodes.shape[0] - canonical.shape[0])


def _transfer_source(value: object) -> TransferSource:
    try:
        return value if isinstance(value, TransferSource) else TransferSource(str(value))
    except (TypeError, ValueError) as exc:
        raise OpenSetResponseError(
            "transfer_source must use the registered TransferSource vocabulary"
        ) from exc


@dataclass(frozen=True)
class ResponseClassManifoldSpec:
    """One finite pre-native response support or one unavailable native slot."""

    class_id: str
    support_kind: ResponseSupportKind
    provider_id: str
    observable_labels: tuple[str, ...]
    convention_id: str
    nuisance_policy_id: str
    transfer_source: TransferSource | None
    response_role: str
    data_source: str
    support_nodes: np.ndarray | None
    support_node_ids: tuple[str, ...]
    response_content_id: str | None
    source_response_id: str | None
    duplicate_node_count: int
    source_semantics: ResponseClassSourceSemantics
    allowed_use: tuple[str, ...] = _ALLOWED_USE
    forbidden_use: tuple[str, ...] = _FORBIDDEN_USE
    _construction_token: InitVar[object] = None

    def __post_init__(self, _construction_token: object) -> None:
        if _construction_token is not _CLASS_TOKEN:
            raise OpenSetResponseError(
                "ResponseClassManifoldSpec must be factory-derived"
            )
        _class_id(self.class_id)
        if not isinstance(self.support_kind, ResponseSupportKind):
            raise OpenSetResponseError("support_kind is invalid")
        _receipt(self.provider_id, "provider_id")
        _texts(self.observable_labels, "observable_labels")
        _receipt(self.convention_id, "convention_id")
        _receipt(self.nuisance_policy_id, "nuisance_policy_id")
        if self.response_role != "hypothesis_only":
            raise OpenSetResponseError(
                "response_role must remain hypothesis_only"
            )
        if self.allowed_use != _ALLOWED_USE or self.forbidden_use != _FORBIDDEN_USE:
            raise OpenSetResponseError("response class claim boundary drifted")
        if not isinstance(
            self.source_semantics,
            ResponseClassSourceSemantics,
        ):
            raise OpenSetResponseError("source_semantics is invalid")
        if self.source_semantics is ResponseClassSourceSemantics.NEUTRAL:
            if self.source_response_id is not None:
                raise OpenSetResponseError(
                    "neutral response class must not carry source_response_id"
                )
        elif (
            self.support_kind is not ResponseSupportKind.NEEDS_NATIVE
            and self.source_response_id is None
        ):
            raise OpenSetResponseError(
                "finite source-specific class requires source_response_id"
            )
        elif self.source_response_id is not None:
            _receipt(self.source_response_id, "source_response_id")
        if self.support_kind is ResponseSupportKind.NEEDS_NATIVE:
            if (
                self.transfer_source is not None
                or self.support_nodes is not None
                or self.support_node_ids
                or self.response_content_id is not None
                or self.duplicate_node_count != 0
                or self.data_source != "none"
            ):
                raise OpenSetResponseError(
                    "NEEDS_NATIVE class must not carry response or transfer values"
                )
            return
        if self.transfer_source is not TransferSource.NONE:
            raise OpenSetResponseError(
                "finite pre-native response supports require transfer_source=none"
            )
        expected_source = (
            "analytic_only"
            if self.support_kind is ResponseSupportKind.FINITE_ANALYTIC_SUPPORT
            else "synthetic_only"
        )
        if self.data_source != expected_source:
            raise OpenSetResponseError(
                f"{self.support_kind.value} requires data_source={expected_source}"
            )
        if self.support_nodes is None or self.response_content_id is None:
            raise OpenSetResponseError(
                "finite response class requires support nodes and content identity"
            )
        if self.support_nodes.shape[1] != len(self.observable_labels):
            raise OpenSetResponseError(
                "support-node dimension must match observable labels"
            )
        if _array_id(
            self.support_nodes,
            role="PR258_RESPONSE_SUPPORT_V1",
        ) != self.response_content_id:
            raise OpenSetResponseError("response_content_id does not match support")
        if len(self.support_node_ids) != self.support_nodes.shape[0]:
            raise OpenSetResponseError(
                "support_node_ids must align with canonical support nodes"
            )
        if len(set(self.support_node_ids)) != len(self.support_node_ids):
            raise OpenSetResponseError("support_node_ids must be unique")
        for node_id in self.support_node_ids:
            _receipt(node_id, "support_node_id")
        if self.duplicate_node_count < 0:
            raise OpenSetResponseError(
                "duplicate_node_count must be non-negative"
            )

    @property
    def support_node_count(self) -> int:
        return 0 if self.support_nodes is None else int(self.support_nodes.shape[0])

    def as_payload(self) -> dict[str, object]:
        return {
            "allowed_use": list(self.allowed_use),
            "class_id": self.class_id,
            "convention_id": self.convention_id,
            "data_source": self.data_source,
            "duplicate_node_count": self.duplicate_node_count,
            "forbidden_use": list(self.forbidden_use),
            "nuisance_policy_id": self.nuisance_policy_id,
            "observable_labels": list(self.observable_labels),
            "provider_id": self.provider_id,
            "response_content_id": self.response_content_id,
            "source_response_id": self.source_response_id,
            "response_role": self.response_role,
            "schema": "PR258_RESPONSE_CLASS_MANIFOLD_SPEC_V2",
            "support_kind": self.support_kind.value,
            "support_node_count": self.support_node_count,
            "support_node_ids": list(self.support_node_ids),
            "support_nodes": (
                None if self.support_nodes is None else self.support_nodes.tolist()
            ),
            "transfer_source": (
                None if self.transfer_source is None else self.transfer_source.value
            ),
            "source_semantics": self.source_semantics.value,
        }


def build_response_class_manifold(
    *,
    class_id: str,
    support_kind: ResponseSupportKind | str,
    provider_id: str,
    observable_labels: Sequence[str],
    convention_id: str,
    nuisance_policy_id: str,
    support_nodes: object | None,
    transfer_source: TransferSource | str | None = TransferSource.NONE,
    source_semantics: ResponseClassSourceSemantics | str = (
        ResponseClassSourceSemantics.NEUTRAL
    ),
    source_response_id: str | None = None,
) -> ResponseClassManifoldSpec:
    """Build a finite class support or an explicit future-native placeholder."""

    identifier = _class_id(class_id)
    try:
        kind = (
            support_kind
            if isinstance(support_kind, ResponseSupportKind)
            else ResponseSupportKind(str(support_kind))
        )
    except (TypeError, ValueError) as exc:
        raise OpenSetResponseError("support_kind is invalid") from exc
    labels = _texts(observable_labels, "observable_labels")
    provider = _receipt(provider_id, "provider_id")
    convention = _receipt(convention_id, "convention_id")
    nuisance = _receipt(nuisance_policy_id, "nuisance_policy_id")
    try:
        semantics = (
            source_semantics
            if isinstance(source_semantics, ResponseClassSourceSemantics)
            else ResponseClassSourceSemantics(str(source_semantics))
        )
    except (TypeError, ValueError) as exc:
        raise OpenSetResponseError("source_semantics is invalid") from exc
    if kind is ResponseSupportKind.NEEDS_NATIVE:
        if support_nodes is not None or transfer_source is not None:
            raise OpenSetResponseError(
                "NEEDS_NATIVE must receive no response bytes or transfer source"
            )
        return ResponseClassManifoldSpec(
            class_id=identifier,
            support_kind=kind,
            provider_id=provider,
            observable_labels=labels,
            convention_id=convention,
            nuisance_policy_id=nuisance,
            transfer_source=None,
            response_role="hypothesis_only",
            data_source="none",
            support_nodes=None,
            support_node_ids=(),
            response_content_id=None,
            source_response_id=source_response_id,
            duplicate_node_count=0,
            source_semantics=semantics,
            _construction_token=_CLASS_TOKEN,
        )
    if support_nodes is None:
        raise OpenSetResponseError(
            "finite response support must not be missing"
        )
    source = _transfer_source(transfer_source)
    canonical, duplicates = _canonical_support_nodes(
        support_nodes,
        columns=len(labels),
    )
    support_node_ids = tuple(
        _payload_id(
            {
                "schema": "PR258_SUPPORT_NODE_ID_V1",
                "response_class_id": identifier,
                "response": [float(value).hex() for value in row],
            }
        )
        for row in canonical
    )
    return ResponseClassManifoldSpec(
        class_id=identifier,
        support_kind=kind,
        provider_id=provider,
        observable_labels=labels,
        convention_id=convention,
        nuisance_policy_id=nuisance,
        transfer_source=source,
        response_role="hypothesis_only",
        data_source=(
            "analytic_only"
            if kind is ResponseSupportKind.FINITE_ANALYTIC_SUPPORT
            else "synthetic_only"
        ),
        support_nodes=canonical,
        support_node_ids=support_node_ids,
        response_content_id=_array_id(
            canonical,
            role="PR258_RESPONSE_SUPPORT_V1",
        ),
        source_response_id=source_response_id,
        duplicate_node_count=duplicates,
        source_semantics=semantics,
        _construction_token=_CLASS_TOKEN,
    )


@dataclass(frozen=True)
class FutureNativeResponseAdapterSpec:
    adapter_id: str
    status: ResponseSupportKind
    observable_labels: tuple[str, ...]
    convention_id: str
    required_fields: tuple[str, ...] = _NATIVE_REQUIRED_FIELDS
    transfer_source_required: TransferSource = TransferSource.BASS_NATIVE_VALIDATED
    response_values: None = None
    allowed_use: tuple[str, ...] = (
        "future native adapter schema validation",
        "missing-capability reporting",
    )
    forbidden_use: tuple[str, ...] = _FORBIDDEN_USE
    _construction_token: InitVar[object] = None

    def __post_init__(self, _construction_token: object) -> None:
        if _construction_token is not _NATIVE_TOKEN:
            raise OpenSetResponseError(
                "FutureNativeResponseAdapterSpec must be factory-derived"
            )
        _receipt(self.adapter_id, "adapter_id")
        if self.status is not ResponseSupportKind.NEEDS_NATIVE:
            raise OpenSetResponseError("future native adapter must be NEEDS_NATIVE")
        _texts(self.observable_labels, "observable_labels")
        _receipt(self.convention_id, "convention_id")
        if self.required_fields != _NATIVE_REQUIRED_FIELDS:
            raise OpenSetResponseError("future native required fields drifted")
        if self.transfer_source_required is not TransferSource.BASS_NATIVE_VALIDATED:
            raise OpenSetResponseError(
                "future adapter must require validated native transfer provenance"
            )
        if self.response_values is not None:
            raise OpenSetResponseError(
                "NEEDS_NATIVE adapter must not carry response values"
            )

    def as_payload(self) -> dict[str, object]:
        return {
            "adapter_id": self.adapter_id,
            "allowed_use": list(self.allowed_use),
            "convention_id": self.convention_id,
            "forbidden_use": list(self.forbidden_use),
            "observable_labels": list(self.observable_labels),
            "required_fields": list(self.required_fields),
            "response_values": None,
            "schema": "PR258_FUTURE_NATIVE_RESPONSE_ADAPTER_V1",
            "status": self.status.value,
            "transfer_source_required": self.transfer_source_required.value,
        }


def build_future_native_response_adapter(
    *,
    adapter_id: str,
    observable_labels: Sequence[str],
    convention_id: str,
) -> FutureNativeResponseAdapterSpec:
    """Return a schema-only adapter that cannot produce native science values."""

    return FutureNativeResponseAdapterSpec(
        adapter_id=_receipt(adapter_id, "adapter_id"),
        status=ResponseSupportKind.NEEDS_NATIVE,
        observable_labels=_texts(observable_labels, "observable_labels"),
        convention_id=_receipt(convention_id, "convention_id"),
        _construction_token=_NATIVE_TOKEN,
    )


@dataclass(frozen=True)
class SourceSeparationGate:
    """Layer-safe projection of the PR-256 local/global geometry verdict."""

    status: SourceSeparationGateStatus
    report_id: str | None
    observable_labels: tuple[str, ...]
    covariance_id: str | None
    nuisance_tangent_id: str | None
    class_contract_ids: tuple[tuple[str, str], ...]
    convention_id: str | None
    nuisance_policy_id: str | None
    source_provider_ids: tuple[tuple[str, str], ...]
    source_response_ids: tuple[tuple[str, str | None], ...]
    source_transfer_contracts: tuple[tuple[str, str, str], ...]
    source_frame_contracts: tuple[tuple[str, str, str, str], ...]
    source_mask_id: str | None
    source_normalizer_id: str | None
    source_normalizer_identity: str | None
    metric_id: str | None
    allowed_use: tuple[str, ...] = (
        "fail-closed local/global response-candidate gating",
    )
    forbidden_use: tuple[str, ...] = _FORBIDDEN_USE
    _construction_token: InitVar[object] = None

    def __post_init__(self, _construction_token: object) -> None:
        if _construction_token is not _SOURCE_GATE_TOKEN:
            raise OpenSetResponseError(
                "SourceSeparationGate must be factory-derived"
            )
        if not isinstance(self.status, SourceSeparationGateStatus):
            raise OpenSetResponseError("source gate status is invalid")
        if self.status is SourceSeparationGateStatus.NOT_APPLICABLE:
            if (
                self.report_id is not None
                or self.observable_labels
                or self.covariance_id is not None
                or self.nuisance_tangent_id is not None
                or self.class_contract_ids
                or self.convention_id is not None
                or self.nuisance_policy_id is not None
                or self.source_provider_ids
                or self.source_response_ids
                or self.source_transfer_contracts
                or self.source_frame_contracts
                or self.source_mask_id is not None
                or self.source_normalizer_id is not None
                or self.source_normalizer_identity is not None
                or self.metric_id is not None
            ):
                raise OpenSetResponseError(
                    "NOT_APPLICABLE source gate must not carry source bindings"
                )
        else:
            _receipt(self.report_id, "report_id")
            _texts(self.observable_labels, "observable_labels")
            _receipt(self.covariance_id, "covariance_id")
            _receipt(self.nuisance_tangent_id, "nuisance_tangent_id")
            _receipt(self.convention_id, "convention_id")
            _receipt(self.nuisance_policy_id, "nuisance_policy_id")
            _receipt(self.source_mask_id, "source_mask_id")
            _text(self.source_normalizer_id, "source_normalizer_id")
            _text(
                self.source_normalizer_identity,
                "source_normalizer_identity",
            )
            if self.metric_id != PR258_METRIC_ID:
                raise OpenSetResponseError(
                    "source gate metric identity drifted"
                )
            if not self.class_contract_ids:
                raise OpenSetResponseError(
                    "source gate must bind class contracts"
                )
            for class_id, contract_id in self.class_contract_ids:
                _class_id(class_id)
                _receipt(contract_id, "class_contract_id")
            expected_semantics = {
                ResponseClassSourceSemantics.LOCAL_BOOST.value,
                ResponseClassSourceSemantics.GLOBAL_TILT.value,
            }
            keyed_contracts = (
                self.source_provider_ids,
                self.source_response_ids,
                self.source_transfer_contracts,
                self.source_frame_contracts,
            )
            for values in keyed_contracts:
                if (
                    len(values) != len(expected_semantics)
                    or {row[0] for row in values} != expected_semantics
                ):
                    raise OpenSetResponseError(
                        "source gate must bind exact local/global providers"
                    )
            for semantics, provider_id in self.source_provider_ids:
                ResponseClassSourceSemantics(semantics)
                _receipt(provider_id, "source_provider_id")
            for semantics, response_id in self.source_response_ids:
                ResponseClassSourceSemantics(semantics)
                if response_id is not None:
                    _receipt(response_id, "source_response_id")
            for semantics, transfer_id, transfer_source in (
                self.source_transfer_contracts
            ):
                ResponseClassSourceSemantics(semantics)
                _receipt(transfer_id, "source_transfer_id")
                _transfer_source(transfer_source)
            for semantics, basis, epoch_window, perturbative_order in (
                self.source_frame_contracts
            ):
                ResponseClassSourceSemantics(semantics)
                _text(basis, "source_basis")
                _text(epoch_window, "source_epoch_window")
                _text(perturbative_order, "source_perturbative_order")
        if self.forbidden_use != _FORBIDDEN_USE:
            raise OpenSetResponseError("source gate claim boundary drifted")

    @property
    def gate_id(self) -> str:
        return _payload_id(self.as_payload())

    def as_payload(self) -> dict[str, object]:
        return {
            "allowed_use": list(self.allowed_use),
            "class_contract_ids": [
                {"class_id": class_id, "contract_id": contract_id}
                for class_id, contract_id in self.class_contract_ids
            ],
            "convention_id": self.convention_id,
            "covariance_id": self.covariance_id,
            "forbidden_use": list(self.forbidden_use),
            "metric_id": self.metric_id,
            "nuisance_policy_id": self.nuisance_policy_id,
            "nuisance_tangent_id": self.nuisance_tangent_id,
            "observable_labels": list(self.observable_labels),
            "report_id": self.report_id,
            "schema": "PR258_SOURCE_SEPARATION_GATE_V2",
            "source_frame_contracts": [
                {
                    "basis": basis,
                    "epoch_window": epoch_window,
                    "perturbative_order": perturbative_order,
                    "source_semantics": semantics,
                }
                for semantics, basis, epoch_window, perturbative_order in (
                    self.source_frame_contracts
                )
            ],
            "source_mask_id": self.source_mask_id,
            "source_normalizer_id": self.source_normalizer_id,
            "source_normalizer_identity": self.source_normalizer_identity,
            "source_provider_ids": [
                {"provider_id": provider_id, "source_semantics": semantics}
                for semantics, provider_id in self.source_provider_ids
            ],
            "source_response_ids": [
                {"response_id": response_id, "source_semantics": semantics}
                for semantics, response_id in self.source_response_ids
            ],
            "source_transfer_contracts": [
                {
                    "source_semantics": semantics,
                    "transfer_id": transfer_id,
                    "transfer_source": transfer_source,
                }
                for semantics, transfer_id, transfer_source in (
                    self.source_transfer_contracts
                )
            ],
            "status": self.status.value,
        }


def _build_source_separation_gate(
    *,
    status: SourceSeparationGateStatus | str,
    report_id: str | None,
    classes: Sequence[ResponseClassManifoldSpec] | None = None,
    covariance: object | None = None,
    nuisance_tangent: object | None = None,
    source_observable_labels: Sequence[str] = (),
    source_covariance: object | None = None,
    source_covariance_id: str | None = None,
    source_nuisance_tangent: object | None = None,
    source_provider_ids: Sequence[tuple[str, str]] = (),
    source_response_ids: Sequence[tuple[str, str | None]] = (),
    source_transfer_contracts: Sequence[tuple[str, str, str]] = (),
    source_frame_contracts: Sequence[tuple[str, str, str, str]] = (),
    source_mask_id: str | None = None,
    source_normalizer_id: str | None = None,
    source_normalizer_identity: str | None = None,
) -> SourceSeparationGate:
    """Internal constructor used only by typed PR-256 projections."""

    try:
        value = (
            status
            if isinstance(status, SourceSeparationGateStatus)
            else SourceSeparationGateStatus(str(status))
        )
    except (TypeError, ValueError) as exc:
        raise OpenSetResponseError("source gate status is invalid") from exc
    if value is SourceSeparationGateStatus.NOT_APPLICABLE:
        return SourceSeparationGate(
            status=value,
            report_id=None,
            observable_labels=(),
            covariance_id=None,
            nuisance_tangent_id=None,
            class_contract_ids=(),
            convention_id=None,
            nuisance_policy_id=None,
            source_provider_ids=(),
            source_response_ids=(),
            source_transfer_contracts=(),
            source_frame_contracts=(),
            source_mask_id=None,
            source_normalizer_id=None,
            source_normalizer_identity=None,
            metric_id=None,
            _construction_token=_SOURCE_GATE_TOKEN,
        )
    items = _validate_class_collection(classes or ())
    source_semantics = {item.source_semantics for item in items}
    expected_semantics = {
        ResponseClassSourceSemantics.LOCAL_BOOST,
        ResponseClassSourceSemantics.GLOBAL_TILT,
    }
    if source_semantics != expected_semantics:
        raise OpenSetResponseError(
            "PR-256 source gate requires both local and global class semantics"
        )
    labels = _texts(source_observable_labels, "source_observable_labels")
    if labels != items[0].observable_labels:
        raise OpenSetResponseError(
            "PR-256 and PR-258 observable labels are not congruent"
        )
    target_covariance = _array(covariance, "covariance", ndim=2)
    source_covariance_value = _array(
        source_covariance,
        "source_covariance",
        ndim=2,
    )
    expected_shape = (len(labels), len(labels))
    if (
        target_covariance.shape != expected_shape
        or source_covariance_value.shape != expected_shape
        or not np.array_equal(target_covariance, source_covariance_value)
    ):
        raise OpenSetResponseError(
            "PR-256 and PR-258 covariance contracts are not congruent"
        )
    covariance_identity = anchored_numeric_content_id(target_covariance)
    if (
        _receipt(source_covariance_id, "source_covariance_id")
        != covariance_identity
    ):
        raise OpenSetResponseError(
            "PR-256 covariance identity does not match replay bytes"
        )
    target_nuisance, nuisance_identity = _nuisance_contract(
        nuisance_tangent,
        dimension=len(labels),
        field="nuisance_tangent",
    )
    source_nuisance, source_nuisance_identity = _nuisance_contract(
        source_nuisance_tangent,
        dimension=len(labels),
        field="source_nuisance_tangent",
    )
    if (
        (target_nuisance is None) != (source_nuisance is None)
        or (
            target_nuisance is not None
            and source_nuisance is not None
            and not np.array_equal(target_nuisance, source_nuisance)
        )
        or nuisance_identity != source_nuisance_identity
    ):
        raise OpenSetResponseError(
            "PR-256 and PR-258 nuisance contracts are not congruent"
        )
    provider_rows = tuple(sorted(tuple(row) for row in source_provider_ids))
    response_rows = tuple(sorted(tuple(row) for row in source_response_ids))
    transfer_rows = tuple(
        sorted(tuple(row) for row in source_transfer_contracts)
    )
    frame_rows = tuple(sorted(tuple(row) for row in source_frame_contracts))
    provider_by_semantics = dict(provider_rows)
    if {
        item.source_semantics.value for item in items
    } != set(provider_by_semantics):
        raise OpenSetResponseError(
            "PR-256 provider semantics do not match PR-258 classes"
        )
    for item in items:
        if provider_by_semantics[item.source_semantics.value] != item.provider_id:
            raise OpenSetResponseError(
                "PR-256 provider identity does not match PR-258 class"
            )
    response_by_semantics = dict(response_rows)
    if set(response_by_semantics) != set(provider_by_semantics):
        raise OpenSetResponseError(
            "PR-256 response semantics do not match source providers"
        )
    for item in items:
        if (
            response_by_semantics[item.source_semantics.value]
            != item.source_response_id
        ):
            raise OpenSetResponseError(
                "PR-256 response identity does not match PR-258 class"
            )
    transfer_by_semantics = {
        semantics: (transfer_id, _transfer_source(transfer_source))
        for semantics, transfer_id, transfer_source in transfer_rows
    }
    if set(transfer_by_semantics) != set(provider_by_semantics):
        raise OpenSetResponseError(
            "PR-256 transfer semantics do not match source providers"
        )
    if any(
        source is not item.transfer_source
        for item in items
        for source in (
            transfer_by_semantics[item.source_semantics.value][1],
        )
    ):
        raise OpenSetResponseError(
            "PR-256 transfer provenance does not match PR-258 classes"
        )
    return SourceSeparationGate(
        status=value,
        report_id=report_id,
        observable_labels=labels,
        covariance_id=covariance_identity,
        nuisance_tangent_id=nuisance_identity,
        class_contract_ids=_class_contract_ids(items),
        convention_id=items[0].convention_id,
        nuisance_policy_id=items[0].nuisance_policy_id,
        source_provider_ids=provider_rows,
        source_response_ids=response_rows,
        source_transfer_contracts=transfer_rows,
        source_frame_contracts=frame_rows,
        source_mask_id=source_mask_id,
        source_normalizer_id=source_normalizer_id,
        source_normalizer_identity=source_normalizer_identity,
        metric_id=PR258_METRIC_ID,
        _construction_token=_SOURCE_GATE_TOKEN,
    )


def source_separation_not_applicable() -> SourceSeparationGate:
    return _build_source_separation_gate(
        status=SourceSeparationGateStatus.NOT_APPLICABLE,
        report_id=None,
    )


@dataclass(frozen=True)
class _SupportedQuotient:
    transform: np.ndarray
    covariance_null_transform: np.ndarray
    structural_zero_indices: tuple[int, ...]
    covariance_id: str
    nuisance_tangent_id: str
    covariance_supported_rank: int
    rank: int
    geometry_status: AnchoredResponseStatus
    metric_id: str


def _readonly_internal_matrix(value: object) -> np.ndarray:
    matrix = np.ascontiguousarray(value, dtype=np.float64)
    out = np.frombuffer(
        matrix.tobytes(order="C"),
        dtype=np.float64,
    ).reshape(matrix.shape)
    out.setflags(write=False)
    return out


def _dimensionless_covariance_null_contract(
    covariance: np.ndarray,
    *,
    relative_tolerance: float,
) -> tuple[np.ndarray, tuple[int, ...]]:
    """Separate dimensionless correlation nulls from exact structural zeros.

    A positive covariance diagonal supplies the coordinate scale needed to
    express a correlation-null residual dimensionlessly.  An exactly
    zero-variance coordinate supplies no such scale, so it is retained as an
    algebraic equality constraint instead of being divided by an arbitrary
    unit value.
    """

    diagonal = np.diag(covariance)
    structural_zero = tuple(
        int(index) for index in np.flatnonzero(diagonal == 0.0)
    )
    positive = np.flatnonzero(diagonal > 0.0)
    if positive.size == 0:
        return (
            np.empty((0, covariance.shape[0]), dtype=np.float64),
            structural_zero,
        )
    standard_deviations = np.sqrt(diagonal[positive])
    block = covariance[np.ix_(positive, positive)]
    standardized = (
        block
        / standard_deviations[:, None]
        / standard_deviations[None, :]
    )
    standardized = 0.5 * (standardized + standardized.T)
    eigenvalues, eigenvectors = np.linalg.eigh(standardized)
    eigenvalues = np.maximum(eigenvalues, 0.0)
    tolerance = relative_tolerance * max(
        float(np.max(eigenvalues, initial=0.0)),
        1.0,
    )
    null_vectors = eigenvectors[:, eigenvalues <= tolerance]
    transform = np.zeros(
        (null_vectors.shape[1], covariance.shape[0]),
        dtype=np.float64,
    )
    transform[:, positive] = (
        null_vectors.T / standard_deviations[None, :]
    )
    return transform, structural_zero


def _nuisance_contract(
    nuisance_tangent: object | None,
    *,
    dimension: int,
    field: str,
) -> tuple[np.ndarray | None, str]:
    if nuisance_tangent is None:
        return None, _payload_id(
            {
                "schema": "PR258_NO_NUISANCE_TANGENT_V1",
                "dimension": dimension,
            }
        )
    nuisance_value = _array(
        nuisance_tangent,
        field,
        ndim=2,
    )
    if nuisance_value.shape[0] != dimension:
        raise OpenSetResponseError(
            f"{field} rows must match observable dimension"
        )
    return nuisance_value, _array_id(
        nuisance_value,
        role="PR258_NUISANCE_TANGENT_V1",
    )


def _supported_quotient(
    covariance: object,
    nuisance_tangent: object | None,
    *,
    dimension: int,
    absolute_tolerance: float,
    relative_tolerance: float,
) -> _SupportedQuotient:
    cov = _array(covariance, "covariance", ndim=2)
    if cov.shape != (dimension, dimension):
        raise OpenSetResponseError(
            "covariance shape must match observable dimension"
        )
    if not np.allclose(
        cov,
        cov.T,
        atol=absolute_tolerance,
        rtol=relative_tolerance,
    ):
        raise OpenSetResponseError("covariance must be symmetric")
    nuisance_value, nuisance_tangent_id = _nuisance_contract(
        nuisance_tangent,
        dimension=dimension,
        field="nuisance_tangent",
    )
    labels = tuple(f"observable-{index}" for index in range(dimension))
    normalizer = NormalizerSpec(
        normalizer_id="PR258-OBSERVABLE-IDENTITY-NORMALIZER",
        kind=NormalizerKind.EXPANSION_NORMALIZED,
        purposes=(NormalizerPurpose.RESPONSE_CONDITIONING,),
        coordinate_labels=labels,
        coordinate_map=tuple(
            tuple(
                1.0 if row == column else 0.0
                for column in range(dimension)
            )
            for row in range(dimension)
        ),
        source_identity=PR258_METRIC_ID,
        assumptions=(
            "Identity scaling: anchor coordinates do not enter response-space distance.",
        ),
    )
    covariance_id = anchored_numeric_content_id(cov)
    try:
        geometry = measure_anchored_response_geometry(
            response=np.eye(dimension),
            covariance=cov,
            normalizer=normalizer,
            parameter_labels=labels,
            transfer_id=_payload_id(
                {
                    "schema": "PR258_SYNTHETIC_TRANSFER_NONE_V1",
                    "dimension": dimension,
                }
            ),
            transfer_source=TransferSource.NONE,
            mask_id=_payload_id(
                {
                    "schema": "PR258_SYNTHETIC_FULL_SUPPORT_V1",
                    "dimension": dimension,
                }
            ),
            covariance_id=covariance_id,
            nuisance_response=nuisance_value,
            rtol=relative_tolerance,
        )
    except AnchoredResponseGeometryError as exc:
        raise OpenSetResponseError(
            f"invalid PR-255 supported quotient contract: {exc}"
        ) from exc
    replay = geometry.anchored_response_replay_matrix
    if replay is None:
        raise OpenSetResponseError(
            "PR-255 supported quotient did not retain replay geometry"
        )
    transform = np.asarray(replay, dtype=np.float64).reshape(
        (-1, dimension)
    )
    rank = int(geometry.rank or 0)
    # The right-nullspace of ``transform`` contains both covariance-null
    # directions and supported nuisance-orbit directions. Only covariance
    # nulls may trigger OUTSIDE_SUPPORTED_QUOTIENT. Positive-diagonal
    # correlation nulls have a dimensionless standard-deviation scale.
    # Exactly zero-variance coordinates do not; they remain separate exact
    # algebraic constraints so a change of physical units cannot change the
    # decision.
    (
        covariance_null_transform,
        structural_zero_indices,
    ) = _dimensionless_covariance_null_contract(
        cov,
        relative_tolerance=relative_tolerance,
    )
    return _SupportedQuotient(
        transform=_readonly_internal_matrix(transform),
        covariance_null_transform=_readonly_internal_matrix(
            covariance_null_transform
        ),
        structural_zero_indices=structural_zero_indices,
        covariance_id=covariance_id,
        nuisance_tangent_id=nuisance_tangent_id,
        covariance_supported_rank=int(
            geometry.supported_data_dimension or 0
        ),
        rank=rank,
        geometry_status=geometry.status,
        metric_id=PR258_METRIC_ID,
    )


def _validate_class_collection(
    classes: Sequence[ResponseClassManifoldSpec],
) -> tuple[ResponseClassManifoldSpec, ...]:
    items = tuple(classes)
    if not items:
        raise OpenSetResponseError("classes must not be empty")
    if any(type(item) is not ResponseClassManifoldSpec for item in items):
        raise OpenSetResponseError(
            "classes must contain ResponseClassManifoldSpec values"
        )
    if len({item.class_id for item in items}) != len(items):
        raise OpenSetResponseError("class ids must be unique")
    items = tuple(sorted(items, key=lambda item: item.class_id))
    contracts = {
        (
            item.observable_labels,
            item.convention_id,
            item.nuisance_policy_id,
        )
        for item in items
    }
    if len(contracts) != 1:
        raise OpenSetResponseError(
            "all classes must share observable, convention, and nuisance contracts"
        )
    finite_sources = {
        item.transfer_source
        for item in items
        if item.support_kind is not ResponseSupportKind.NEEDS_NATIVE
    }
    if finite_sources not in ({TransferSource.NONE}, set()):
        raise OpenSetResponseError(
            "pre-native response classes must share transfer_source=none"
        )
    source_semantics = {item.source_semantics for item in items}
    if (
        ResponseClassSourceSemantics.NEUTRAL in source_semantics
        and len(source_semantics) > 1
    ):
        raise OpenSetResponseError(
            "neutral and local/global response semantics must not be mixed "
            "under one source-separation gate"
        )
    return items


def _class_contract_id(item: ResponseClassManifoldSpec) -> str:
    """Bind every semantic class field while ignoring raw duplicate count."""

    return _payload_id(
        {
            "schema": "PR258_RESPONSE_CLASS_CONTRACT_ID_V2",
            "class_id": item.class_id,
            "support_kind": item.support_kind.value,
            "provider_id": item.provider_id,
            "observable_labels": list(item.observable_labels),
            "convention_id": item.convention_id,
            "nuisance_policy_id": item.nuisance_policy_id,
            "transfer_source": (
                None
                if item.transfer_source is None
                else item.transfer_source.value
            ),
            "response_role": item.response_role,
            "data_source": item.data_source,
            "support_node_ids": list(item.support_node_ids),
            "response_content_id": item.response_content_id,
            "source_response_id": item.source_response_id,
            "source_semantics": item.source_semantics.value,
        }
    )


def _class_contract_ids(
    items: Sequence[ResponseClassManifoldSpec],
) -> tuple[tuple[str, str], ...]:
    return tuple((item.class_id, _class_contract_id(item)) for item in items)


def _pairwise_minimum_squared_distances(
    classes: Sequence[ResponseClassManifoldSpec],
    quotient: _SupportedQuotient,
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    count = len(classes)
    distances = np.zeros((count, count), dtype=np.float64)
    null_residuals = np.zeros((count, count), dtype=np.float64)
    structural_mismatches = np.zeros((count, count), dtype=np.bool_)
    for left_index in range(count):
        left = classes[left_index].support_nodes
        assert left is not None
        for right_index in range(left_index + 1, count):
            right = classes[right_index].support_nodes
            assert right is not None
            differences = left[:, None, :] - right[None, :, :]
            supported = differences @ quotient.transform.T
            squared = np.sum(supported * supported, axis=2)
            null_values = (
                differences @ quotient.covariance_null_transform.T
            )
            null_norms = np.linalg.norm(null_values, axis=2)
            structural = (
                np.any(
                    differences[
                        ..., quotient.structural_zero_indices
                    ] != 0.0,
                    axis=2,
                )
                if quotient.structural_zero_indices
                else np.zeros(squared.shape, dtype=np.bool_)
            )
            selected = min(
                (
                    float(squared[left_node, right_node]),
                    bool(structural[left_node, right_node]),
                    float(null_norms[left_node, right_node]),
                    classes[left_index].support_node_ids[left_node],
                    classes[right_index].support_node_ids[right_node],
                )
                for left_node in range(left.shape[0])
                for right_node in range(right.shape[0])
            )
            distances[left_index, right_index] = distances[
                right_index, left_index
            ] = selected[0]
            structural_mismatches[left_index, right_index] = (
                structural_mismatches[right_index, left_index]
            ) = selected[1]
            null_residuals[left_index, right_index] = null_residuals[
                right_index, left_index
            ] = selected[2]
    return distances, null_residuals, structural_mismatches


def _components_from_edges(
    class_ids: Sequence[str],
    edges: Sequence[tuple[int, int]],
) -> tuple[tuple[str, ...], ...]:
    parent = list(range(len(class_ids)))

    def find(index: int) -> int:
        while parent[index] != index:
            parent[index] = parent[parent[index]]
            index = parent[index]
        return index

    for left, right in edges:
        root_left = find(left)
        root_right = find(right)
        if root_left != root_right:
            parent[root_right] = root_left
    grouped: dict[int, list[str]] = {}
    for index, class_id in enumerate(class_ids):
        grouped.setdefault(find(index), []).append(class_id)
    return tuple(
        sorted(
            (tuple(sorted(values)) for values in grouped.values()),
            key=lambda values: values[0],
        )
    )


@dataclass(frozen=True)
class ReopeningObservableSpec:
    """A node-keyed added observable under one enlarged joint geometry."""

    observable_id: str
    added_observable_labels: tuple[str, ...]
    provider_available: bool
    class_node_responses: tuple[
        tuple[str, tuple[tuple[str, tuple[float, ...]], ...]], ...
    ]
    joint_covariance: tuple[tuple[float, ...], ...] | None
    joint_covariance_id: str | None
    joint_nuisance_response: tuple[tuple[float, ...], ...] | None
    joint_nuisance_policy_id: str | None
    convention_id: str
    response_content_id: str | None
    allowed_use: tuple[str, ...] = (
        "response-graph reopening under one enlarged joint quotient",
    )
    forbidden_use: tuple[str, ...] = (
        *_FORBIDDEN_USE,
        "physical kernel reopening without a separate response-rank proof",
    )
    _construction_token: InitVar[object] = None

    def __post_init__(self, _construction_token: object) -> None:
        if _construction_token is not _REOPENING_TOKEN:
            raise OpenSetResponseError(
                "ReopeningObservableSpec must be factory-derived"
            )
        _receipt(self.observable_id, "observable_id")
        _texts(self.added_observable_labels, "added_observable_labels")
        if type(self.provider_available) is not bool:
            raise OpenSetResponseError("provider_available must be boolean")
        _receipt(self.convention_id, "convention_id")
        if not self.provider_available:
            if any(
                value
                for value in (
                    self.class_node_responses,
                    self.joint_covariance,
                    self.joint_covariance_id,
                    self.joint_nuisance_response,
                    self.joint_nuisance_policy_id,
                    self.response_content_id,
                )
            ):
                raise OpenSetResponseError(
                    "missing reopening provider must not carry numeric values"
                )
            return
        if not self.class_node_responses:
            raise OpenSetResponseError(
                "available reopening provider requires node-keyed responses"
            )
        _receipt(self.joint_covariance_id, "joint_covariance_id")
        _receipt(
            self.joint_nuisance_policy_id,
            "joint_nuisance_policy_id",
        )
        _receipt(self.response_content_id, "response_content_id")
        if self.joint_covariance is None:
            raise OpenSetResponseError(
                "available reopening provider requires joint covariance"
            )

    def as_payload(self) -> dict[str, object]:
        return {
            "added_observable_labels": list(self.added_observable_labels),
            "allowed_use": list(self.allowed_use),
            "class_node_responses": [
                {
                    "response_class_id": class_id,
                    "nodes": [
                        {
                            "support_node_id": node_id,
                            "values": list(values),
                        }
                        for node_id, values in nodes
                    ],
                }
                for class_id, nodes in self.class_node_responses
            ],
            "convention_id": self.convention_id,
            "forbidden_use": list(self.forbidden_use),
            "joint_covariance": (
                None
                if self.joint_covariance is None
                else [list(row) for row in self.joint_covariance]
            ),
            "joint_covariance_id": self.joint_covariance_id,
            "joint_nuisance_policy_id": self.joint_nuisance_policy_id,
            "joint_nuisance_response": (
                None
                if self.joint_nuisance_response is None
                else [list(row) for row in self.joint_nuisance_response]
            ),
            "observable_id": self.observable_id,
            "provider_available": self.provider_available,
            "response_content_id": self.response_content_id,
            "schema": "PR258_REOPENING_OBSERVABLE_SPEC_V1",
        }


def build_reopening_observable_spec(
    *,
    observable_id: str,
    classes: Sequence[ResponseClassManifoldSpec],
    added_observable_labels: Sequence[str],
    responses_by_class_and_node: (
        Mapping[str, Mapping[str, Sequence[object]]] | None
    ),
    joint_covariance: object | None,
    joint_nuisance_response: object | None,
    joint_nuisance_policy_id: str | None,
    convention_id: str,
) -> ReopeningObservableSpec:
    items = _validate_class_collection(classes)
    identity = _receipt(observable_id, "observable_id")
    labels = _texts(
        added_observable_labels,
        "added_observable_labels",
    )
    convention = _receipt(convention_id, "convention_id")
    if convention != items[0].convention_id:
        raise OpenSetResponseError(
            "reopening convention must match the base response contract"
        )
    if responses_by_class_and_node is None:
        if any(
            value is not None
            for value in (
                joint_covariance,
                joint_nuisance_response,
                joint_nuisance_policy_id,
            )
        ):
            raise OpenSetResponseError(
                "missing provider must not carry joint geometry"
            )
        return ReopeningObservableSpec(
            observable_id=identity,
            added_observable_labels=labels,
            provider_available=False,
            class_node_responses=(),
            joint_covariance=None,
            joint_covariance_id=None,
            joint_nuisance_response=None,
            joint_nuisance_policy_id=None,
            convention_id=convention,
            response_content_id=None,
            _construction_token=_REOPENING_TOKEN,
        )
    if not isinstance(responses_by_class_and_node, Mapping):
        raise OpenSetResponseError(
            "responses_by_class_and_node must be a mapping"
        )
    class_ids = tuple(item.class_id for item in items)
    if set(responses_by_class_and_node) != set(class_ids):
        raise OpenSetResponseError(
            "reopening responses must cover every response class exactly"
        )
    canonical_responses = []
    for item in items:
        node_map = responses_by_class_and_node[item.class_id]
        if not isinstance(node_map, Mapping):
            raise OpenSetResponseError(
                "reopening class response must map support_node_id to values"
            )
        if set(node_map) != set(item.support_node_ids):
            raise OpenSetResponseError(
                "reopening node identities must match base support exactly"
            )
        node_rows = []
        for node_id in item.support_node_ids:
            raw = node_map[node_id]
            if isinstance(raw, (str, bytes)):
                raise OpenSetResponseError(
                    "reopening response must be a numeric sequence"
                )
            try:
                iterator = iter(raw)
            except TypeError as exc:
                raise OpenSetResponseError(
                    "reopening response must be a numeric sequence"
                ) from exc
            values = tuple(
                _finite_real(value, f"{identity}:{node_id}")
                for value in iterator
            )
            if len(values) != len(labels):
                raise OpenSetResponseError(
                    "reopening response dimension must match added labels"
                )
            node_rows.append((node_id, values))
        canonical_responses.append((item.class_id, tuple(node_rows)))
    joint_dimension = len(items[0].observable_labels) + len(labels)
    covariance_matrix = _array(
        joint_covariance,
        "joint_covariance",
        ndim=2,
    )
    if covariance_matrix.shape != (joint_dimension, joint_dimension):
        raise OpenSetResponseError(
            "joint_covariance must cover base and added observables"
        )
    covariance_id = anchored_numeric_content_id(covariance_matrix)
    nuisance_rows: tuple[tuple[float, ...], ...] | None
    if joint_nuisance_response is None:
        nuisance_rows = None
    else:
        nuisance_matrix = _array(
            joint_nuisance_response,
            "joint_nuisance_response",
            ndim=2,
        )
        if nuisance_matrix.shape[0] != joint_dimension:
            raise OpenSetResponseError(
                "joint nuisance rows must match joint observable dimension"
            )
        nuisance_rows = tuple(
            tuple(float(value) for value in row)
            for row in nuisance_matrix
        )
    nuisance_identity = _receipt(
        joint_nuisance_policy_id,
        "joint_nuisance_policy_id",
    )
    response_id = _payload_id(
        {
            "schema": "PR258_REOPENING_NODE_RESPONSES_V1",
            "responses": canonical_responses,
        }
    )
    return ReopeningObservableSpec(
        observable_id=identity,
        added_observable_labels=labels,
        provider_available=True,
        class_node_responses=tuple(canonical_responses),
        joint_covariance=tuple(
            tuple(float(value) for value in row)
            for row in covariance_matrix
        ),
        joint_covariance_id=covariance_id,
        joint_nuisance_response=nuisance_rows,
        joint_nuisance_policy_id=nuisance_identity,
        convention_id=convention,
        response_content_id=response_id,
        _construction_token=_REOPENING_TOKEN,
    )


def _reopening_outcome(
    *,
    classes: tuple[ResponseClassManifoldSpec, ...],
    components: tuple[tuple[str, ...], ...],
    tolerance: float,
    absolute_tolerance: float,
    relative_tolerance: float,
    observables: Sequence[ReopeningObservableSpec],
) -> tuple[
    ReopeningObservableStatus,
    tuple[str, ...],
    tuple[str, ...],
    tuple[tuple[str, str], ...],
]:
    merged = tuple(component for component in components if len(component) > 1)
    if not merged:
        return ReopeningObservableStatus.NOT_REQUIRED, (), (), ()
    items = tuple(observables)
    if any(type(item) is not ReopeningObservableSpec for item in items):
        raise OpenSetResponseError(
            "reopening_observables must contain ReopeningObservableSpec values"
        )
    if len({item.observable_id for item in items}) != len(items):
        raise OpenSetResponseError("reopening observable ids must be unique")
    items = tuple(sorted(items, key=lambda item: item.observable_id))
    missing = tuple(
        item.observable_id for item in items if not item.provider_available
    )
    successful: list[tuple[int, str]] = []
    joint_report_ids: list[tuple[str, str]] = []
    for observable in items:
        if not observable.provider_available:
            continue
        response_maps = {
            class_id: dict(nodes)
            for class_id, nodes in observable.class_node_responses
        }
        joint_classes = []
        for item in classes:
            assert item.support_nodes is not None
            added = response_maps[item.class_id]
            joint_nodes = [
                [
                    *(float(value) for value in row),
                    *added[node_id],
                ]
                for row, node_id in zip(
                    item.support_nodes,
                    item.support_node_ids,
                    strict=True,
                )
            ]
            joint_classes.append(
                build_response_class_manifold(
                    class_id=item.class_id,
                    support_kind=item.support_kind,
                    provider_id=item.provider_id,
                    observable_labels=(
                        *item.observable_labels,
                        *observable.added_observable_labels,
                    ),
                    convention_id=item.convention_id,
                    nuisance_policy_id=str(
                        observable.joint_nuisance_policy_id
                    ),
                    support_nodes=joint_nodes,
                    transfer_source=item.transfer_source,
                    source_semantics=item.source_semantics,
                )
            )
        joint_report = build_response_equivalence_report(
            classes=tuple(joint_classes),
            covariance=observable.joint_covariance,
            nuisance_tangent=observable.joint_nuisance_response,
            equivalence_squared_distance_tolerance=tolerance,
            absolute_tolerance=absolute_tolerance,
            relative_tolerance=relative_tolerance,
            reopening_observables=None,
        )
        joint_report_ids.append(
            (observable.observable_id, joint_report.report_id)
        )
        if (
            joint_report.status is ResponseEquivalenceStatus.SEPARATED
            and all(len(component) == 1 for component in joint_report.components)
        ):
            successful.append(
                (len(observable.added_observable_labels), observable.observable_id)
            )
    if successful:
        minimum_dimension = min(item[0] for item in successful)
        selected = tuple(
            sorted(
                observable_id
                for dimension, observable_id in successful
                if dimension == minimum_dimension
            )
        )
        return (
            ReopeningObservableStatus.REOPENED,
            selected,
            missing,
            tuple(joint_report_ids),
        )
    if missing:
        return (
            ReopeningObservableStatus.MISSING_RESPONSE_PROVIDER,
            (),
            missing,
            tuple(joint_report_ids),
        )
    return (
        ReopeningObservableStatus.NEEDS_ADDITIONAL_OBSERVABLE,
        (),
        (),
        tuple(joint_report_ids),
    )


@dataclass(frozen=True)
class ResponseEquivalenceClassReport:
    status: ResponseEquivalenceStatus
    class_ids: tuple[str, ...]
    components: tuple[tuple[str, ...], ...]
    equivalence_edges: tuple[tuple[str, str], ...]
    pairwise_minimum_squared_distances: tuple[
        tuple[float | None, ...], ...
    ]
    pairwise_covariance_null_residuals: tuple[
        tuple[float | None, ...], ...
    ]
    pairwise_covariance_structural_null_mismatches: tuple[
        tuple[bool | None, ...], ...
    ]
    covariance_id: str
    observable_labels: tuple[str, ...]
    convention_id: str
    nuisance_policy_id: str
    nuisance_tangent_id: str
    supported_rank: int
    metric_id: str
    equivalence_squared_distance_tolerance: float
    absolute_tolerance: float
    relative_tolerance: float
    reopening_status: ReopeningObservableStatus
    minimal_reopening_observable_ids: tuple[str, ...]
    missing_reopening_provider_ids: tuple[str, ...]
    reopening_joint_report_ids: tuple[tuple[str, str], ...]
    class_response_ids: tuple[tuple[str, str], ...]
    class_contract_ids: tuple[tuple[str, str], ...]
    claim_tier_ceiling: str = PR258_MACHINE_CLAIM_TIER
    roadmap_claim_level: str = PR258_ROADMAP_CLAIM_LEVEL
    allowed_use: tuple[str, ...] = _ALLOWED_USE
    forbidden_use: tuple[str, ...] = _FORBIDDEN_USE
    _construction_token: InitVar[object] = None

    def __post_init__(self, _construction_token: object) -> None:
        if _construction_token is not _EQUIVALENCE_TOKEN:
            raise OpenSetResponseError(
                "ResponseEquivalenceClassReport must be factory-derived"
            )
        if not isinstance(self.status, ResponseEquivalenceStatus):
            raise OpenSetResponseError("equivalence status is invalid")
        class_ids = tuple(_class_id(value) for value in self.class_ids)
        if class_ids != tuple(sorted(class_ids)) or len(set(class_ids)) != len(class_ids):
            raise OpenSetResponseError(
                "class_ids must be unique and sorted"
            )
        flattened = tuple(
            item for component in self.components for item in component
        )
        if tuple(sorted(flattened)) != class_ids or len(flattened) != len(class_ids):
            raise OpenSetResponseError(
                "components must partition class_ids"
            )
        _receipt(self.covariance_id, "covariance_id")
        _texts(self.observable_labels, "observable_labels")
        _receipt(self.convention_id, "convention_id")
        _receipt(self.nuisance_policy_id, "nuisance_policy_id")
        _receipt(self.nuisance_tangent_id, "nuisance_tangent_id")
        if self.supported_rank < 0:
            raise OpenSetResponseError("supported_rank must be non-negative")
        if self.metric_id != PR258_METRIC_ID:
            raise OpenSetResponseError("response metric identity drifted")
        _nonnegative(
            self.equivalence_squared_distance_tolerance,
            "equivalence_squared_distance_tolerance",
        )
        _positive(self.absolute_tolerance, "absolute_tolerance")
        _positive(self.relative_tolerance, "relative_tolerance")
        expected_shape = (len(class_ids), len(class_ids))
        for name in (
            "pairwise_minimum_squared_distances",
            "pairwise_covariance_null_residuals",
        ):
            matrix = getattr(self, name)
            if (
                len(matrix) != expected_shape[0]
                or any(len(row) != expected_shape[1] for row in matrix)
            ):
                raise OpenSetResponseError(
                    f"{name} must have shape {expected_shape}"
                )
            for row in matrix:
                for value in row:
                    if value is not None:
                        _nonnegative(value, name)
        structural = self.pairwise_covariance_structural_null_mismatches
        if (
            len(structural) != expected_shape[0]
            or any(len(row) != expected_shape[1] for row in structural)
        ):
            raise OpenSetResponseError(
                "pairwise_covariance_structural_null_mismatches must have "
                f"shape {expected_shape}"
            )
        for row in structural:
            for value in row:
                if value is not None and type(value) is not bool:
                    raise OpenSetResponseError(
                        "pairwise covariance structural-null flags must be "
                        "Boolean or null"
                    )
        if not isinstance(self.reopening_status, ReopeningObservableStatus):
            raise OpenSetResponseError("reopening_status is invalid")
        for observable_id, report_id in self.reopening_joint_report_ids:
            _receipt(observable_id, "reopening observable id")
            _receipt(report_id, "reopening joint report id")
        if tuple(item[0] for item in self.class_response_ids) != class_ids:
            raise OpenSetResponseError(
                "class_response_ids must align with class_ids"
            )
        if tuple(item[0] for item in self.class_contract_ids) != class_ids:
            raise OpenSetResponseError(
                "class_contract_ids must align with class_ids"
            )
        for _, response_id in self.class_response_ids:
            if response_id != "NEEDS_NATIVE":
                _receipt(response_id, "class response id")
        for _, contract_id in self.class_contract_ids:
            _receipt(contract_id, "class contract id")
        if (
            self.claim_tier_ceiling != PR258_MACHINE_CLAIM_TIER
            or self.roadmap_claim_level != PR258_ROADMAP_CLAIM_LEVEL
        ):
            raise OpenSetResponseError("claim-tier boundary drifted")
        if self.allowed_use != _ALLOWED_USE or self.forbidden_use != _FORBIDDEN_USE:
            raise OpenSetResponseError("equivalence claim boundary drifted")

    @property
    def report_id(self) -> str:
        return _payload_id(self.as_payload())

    def as_payload(self) -> dict[str, object]:
        return {
            "allowed_use": list(self.allowed_use),
            "class_ids": list(self.class_ids),
            "class_contract_ids": [
                list(item) for item in self.class_contract_ids
            ],
            "class_response_ids": [list(item) for item in self.class_response_ids],
            "components": [list(component) for component in self.components],
            "convention_id": self.convention_id,
            "covariance_id": self.covariance_id,
            "equivalence_edges": [list(edge) for edge in self.equivalence_edges],
            "equivalence_squared_distance_tolerance": (
                self.equivalence_squared_distance_tolerance
            ),
            "absolute_tolerance": self.absolute_tolerance,
            "relative_tolerance": self.relative_tolerance,
            "metric_id": self.metric_id,
            "claim_tier_ceiling": self.claim_tier_ceiling,
            "roadmap_claim_level": {
                "scheme": "roadmap_rescue_v1",
                "level": self.roadmap_claim_level,
            },
            "forbidden_use": list(self.forbidden_use),
            "minimal_reopening_observable_ids": list(
                self.minimal_reopening_observable_ids
            ),
            "missing_reopening_provider_ids": list(
                self.missing_reopening_provider_ids
            ),
            "reopening_joint_report_ids": [
                list(item) for item in self.reopening_joint_report_ids
            ],
            "nuisance_policy_id": self.nuisance_policy_id,
            "nuisance_tangent_id": self.nuisance_tangent_id,
            "observable_labels": list(self.observable_labels),
            "pairwise_covariance_null_residuals": [
                list(row) for row in self.pairwise_covariance_null_residuals
            ],
            "pairwise_covariance_structural_null_mismatches": [
                list(row)
                for row
                in self.pairwise_covariance_structural_null_mismatches
            ],
            "pairwise_minimum_squared_distances": [
                list(row) for row in self.pairwise_minimum_squared_distances
            ],
            "reopening_status": self.reopening_status.value,
            "schema": "PR258_RESPONSE_EQUIVALENCE_CLASS_REPORT_V4",
            "status": self.status.value,
            "supported_rank": self.supported_rank,
        }


def build_response_equivalence_report(
    *,
    classes: Sequence[ResponseClassManifoldSpec],
    covariance: object,
    nuisance_tangent: object | None,
    equivalence_squared_distance_tolerance: float,
    absolute_tolerance: float,
    relative_tolerance: float,
    reopening_observables: Sequence[ReopeningObservableSpec] | None = None,
) -> ResponseEquivalenceClassReport:
    """Collapse finite response supports on one declared supported quotient."""

    items = _validate_class_collection(classes)
    tolerance = _nonnegative(
        equivalence_squared_distance_tolerance,
        "equivalence_squared_distance_tolerance",
    )
    atol = _positive(absolute_tolerance, "absolute_tolerance")
    rtol = _positive(relative_tolerance, "relative_tolerance")
    class_ids = tuple(item.class_id for item in items)
    missing = tuple(
        item for item in items if item.support_kind is ResponseSupportKind.NEEDS_NATIVE
    )
    labels = items[0].observable_labels
    quotient = _supported_quotient(
        covariance,
        nuisance_tangent,
        dimension=len(labels),
        absolute_tolerance=atol,
        relative_tolerance=rtol,
    )
    if missing:
        components = tuple((class_id,) for class_id in class_ids)
        size = len(items)
        missing_rows = tuple(tuple(None for _ in range(size)) for _ in range(size))
        return ResponseEquivalenceClassReport(
            status=ResponseEquivalenceStatus.MISSING_RESPONSE_PROVIDER,
            class_ids=class_ids,
            components=components,
            equivalence_edges=(),
            pairwise_minimum_squared_distances=missing_rows,
            pairwise_covariance_null_residuals=missing_rows,
            pairwise_covariance_structural_null_mismatches=missing_rows,
            covariance_id=quotient.covariance_id,
            observable_labels=labels,
            convention_id=items[0].convention_id,
            nuisance_policy_id=items[0].nuisance_policy_id,
            nuisance_tangent_id=quotient.nuisance_tangent_id,
            supported_rank=quotient.rank,
            metric_id=quotient.metric_id,
            equivalence_squared_distance_tolerance=tolerance,
            absolute_tolerance=atol,
            relative_tolerance=rtol,
            reopening_status=ReopeningObservableStatus.MISSING_RESPONSE_PROVIDER,
            minimal_reopening_observable_ids=(),
            missing_reopening_provider_ids=tuple(
                item.provider_id for item in missing
            ),
            reopening_joint_report_ids=(),
            class_response_ids=tuple(
                (item.class_id, item.response_content_id or "NEEDS_NATIVE")
                for item in items
            ),
            class_contract_ids=_class_contract_ids(items),
            _construction_token=_EQUIVALENCE_TOKEN,
        )
    if quotient.covariance_supported_rank == 0:
        components = (class_ids,)
        (
            distances,
            null_residuals,
            structural_mismatches,
        ) = _pairwise_minimum_squared_distances(
            items,
            quotient,
        )
        return ResponseEquivalenceClassReport(
            status=ResponseEquivalenceStatus.OUTSIDE_SUPPORTED_QUOTIENT,
            class_ids=class_ids,
            components=components,
            equivalence_edges=tuple(
                (class_ids[left], class_ids[right])
                for left in range(len(class_ids))
                for right in range(left + 1, len(class_ids))
            ),
            pairwise_minimum_squared_distances=tuple(
                tuple(float(value) for value in row) for row in distances
            ),
            pairwise_covariance_null_residuals=tuple(
                tuple(float(value) for value in row) for row in null_residuals
            ),
            pairwise_covariance_structural_null_mismatches=tuple(
                tuple(bool(value) for value in row)
                for row in structural_mismatches
            ),
            covariance_id=quotient.covariance_id,
            observable_labels=labels,
            convention_id=items[0].convention_id,
            nuisance_policy_id=items[0].nuisance_policy_id,
            nuisance_tangent_id=quotient.nuisance_tangent_id,
            supported_rank=0,
            metric_id=quotient.metric_id,
            equivalence_squared_distance_tolerance=tolerance,
            absolute_tolerance=atol,
            relative_tolerance=rtol,
            reopening_status=ReopeningObservableStatus.NEEDS_ADDITIONAL_OBSERVABLE,
            minimal_reopening_observable_ids=(),
            missing_reopening_provider_ids=(),
            reopening_joint_report_ids=(),
            class_response_ids=tuple(
                (item.class_id, str(item.response_content_id)) for item in items
            ),
            class_contract_ids=_class_contract_ids(items),
            _construction_token=_EQUIVALENCE_TOKEN,
        )
    (
        distances,
        null_residuals,
        structural_mismatches,
    ) = _pairwise_minimum_squared_distances(
        items,
        quotient,
    )
    edge_indices = tuple(
        (left, right)
        for left in range(len(items))
        for right in range(left + 1, len(items))
        if distances[left, right] <= tolerance
    )
    components = _components_from_edges(class_ids, edge_indices)
    non_clique = False
    index_by_id = {class_id: index for index, class_id in enumerate(class_ids)}
    for component in components:
        for left_position, left_id in enumerate(component):
            for right_id in component[left_position + 1 :]:
                if distances[
                    index_by_id[left_id],
                    index_by_id[right_id],
                ] > tolerance:
                    non_clique = True
    if non_clique:
        status = ResponseEquivalenceStatus.TYPE_UNIDENTIFIED
    elif any(len(component) > 1 for component in components):
        status = ResponseEquivalenceStatus.EQUIVALENCE_CLASS
    else:
        status = ResponseEquivalenceStatus.SEPARATED
    reopening_status, minimal, missing_ids, joint_report_ids = _reopening_outcome(
        classes=items,
        components=components,
        tolerance=tolerance,
        absolute_tolerance=atol,
        relative_tolerance=rtol,
        observables=() if reopening_observables is None else reopening_observables,
    )
    return ResponseEquivalenceClassReport(
        status=status,
        class_ids=class_ids,
        components=components,
        equivalence_edges=tuple(
            (class_ids[left], class_ids[right]) for left, right in edge_indices
        ),
        pairwise_minimum_squared_distances=tuple(
            tuple(float(value) for value in row) for row in distances
        ),
        pairwise_covariance_null_residuals=tuple(
            tuple(float(value) for value in row) for row in null_residuals
        ),
        pairwise_covariance_structural_null_mismatches=tuple(
            tuple(bool(value) for value in row)
            for row in structural_mismatches
        ),
        covariance_id=quotient.covariance_id,
        observable_labels=labels,
        convention_id=items[0].convention_id,
        nuisance_policy_id=items[0].nuisance_policy_id,
        nuisance_tangent_id=quotient.nuisance_tangent_id,
        supported_rank=quotient.rank,
        metric_id=quotient.metric_id,
        equivalence_squared_distance_tolerance=tolerance,
        absolute_tolerance=atol,
        relative_tolerance=rtol,
        reopening_status=reopening_status,
        minimal_reopening_observable_ids=minimal,
        missing_reopening_provider_ids=missing_ids,
        reopening_joint_report_ids=joint_report_ids,
        class_response_ids=tuple(
            (item.class_id, str(item.response_content_id)) for item in items
        ),
        class_contract_ids=_class_contract_ids(items),
        _construction_token=_EQUIVALENCE_TOKEN,
    )


def _class_distances(
    observation: np.ndarray,
    classes: Sequence[ResponseClassManifoldSpec],
    quotient: _SupportedQuotient,
) -> tuple[
    tuple[tuple[str, float], ...],
    tuple[tuple[str, float], ...],
    tuple[tuple[str, bool], ...],
]:
    scores: list[tuple[str, float]] = []
    null_scores: list[tuple[str, float]] = []
    structural_scores: list[tuple[str, bool]] = []
    for item in classes:
        nodes = item.support_nodes
        assert nodes is not None
        differences = observation[None, :] - nodes
        supported = differences @ quotient.transform.T
        squared = np.sum(supported * supported, axis=1)
        null_values = differences @ quotient.covariance_null_transform.T
        null_norms = np.linalg.norm(null_values, axis=1)
        structural = (
            np.any(
                differences[:, quotient.structural_zero_indices] != 0.0,
                axis=1,
            )
            if quotient.structural_zero_indices
            else np.zeros(nodes.shape[0], dtype=np.bool_)
        )
        best_index = min(
            range(nodes.shape[0]),
            key=lambda index: (
                float(squared[index]),
                bool(structural[index]),
                float(null_norms[index]),
                item.support_node_ids[index],
            ),
        )
        scores.append((item.class_id, float(squared[best_index])))
        null_scores.append((item.class_id, float(null_norms[best_index])))
        structural_scores.append(
            (item.class_id, bool(structural[best_index]))
        )
    return tuple(scores), tuple(null_scores), tuple(structural_scores)


@dataclass(frozen=True)
class OpenSetClassificationReport:
    status: OpenSetClassificationStatus
    observation_id: str
    equivalence_report_id: str
    component_scores: tuple[tuple[tuple[str, ...], float], ...]
    candidate_class_id: str | None
    returned_equivalence_class: tuple[str, ...]
    best_squared_distance: float | None
    second_best_squared_distance: float | None
    squared_distance_margin: float | None
    unknown_squared_distance_threshold: float
    decision_squared_margin: float
    covariance_null_tolerance: float
    covariance_null_residual: float
    covariance_structural_null_mismatch: bool
    supported_rank: int
    source_separation_gate: SourceSeparationGate
    metric_id: str = PR258_METRIC_ID
    claim_tier_ceiling: str = PR258_MACHINE_CLAIM_TIER
    roadmap_claim_level: str = PR258_ROADMAP_CLAIM_LEVEL
    allowed_use: tuple[str, ...] = _ALLOWED_USE
    forbidden_use: tuple[str, ...] = _FORBIDDEN_USE
    _construction_token: InitVar[object] = None

    def __post_init__(self, _construction_token: object) -> None:
        if _construction_token is not _CLASSIFICATION_TOKEN:
            raise OpenSetResponseError(
                "OpenSetClassificationReport must be factory-derived"
            )
        if not isinstance(self.status, OpenSetClassificationStatus):
            raise OpenSetResponseError("classification status is invalid")
        _receipt(self.observation_id, "observation_id")
        _receipt(self.equivalence_report_id, "equivalence_report_id")
        _positive(
            self.unknown_squared_distance_threshold,
            "unknown_squared_distance_threshold",
        )
        _nonnegative(self.decision_squared_margin, "decision_squared_margin")
        _nonnegative(
            self.covariance_null_tolerance,
            "covariance_null_tolerance",
        )
        _nonnegative(self.covariance_null_residual, "covariance_null_residual")
        if type(self.covariance_structural_null_mismatch) is not bool:
            raise OpenSetResponseError(
                "covariance_structural_null_mismatch must be Boolean"
            )
        if self.supported_rank < 0:
            raise OpenSetResponseError("supported_rank must be non-negative")
        if type(self.source_separation_gate) is not SourceSeparationGate:
            raise OpenSetResponseError(
                "source_separation_gate must be factory-derived"
            )
        if self.metric_id != PR258_METRIC_ID:
            raise OpenSetResponseError("response metric identity drifted")
        if (
            self.claim_tier_ceiling != PR258_MACHINE_CLAIM_TIER
            or self.roadmap_claim_level != PR258_ROADMAP_CLAIM_LEVEL
        ):
            raise OpenSetResponseError("claim-tier boundary drifted")
        if self.candidate_class_id is not None:
            _class_id(self.candidate_class_id, "candidate_class_id")
        for class_id in self.returned_equivalence_class:
            _class_id(class_id, "returned_equivalence_class")
        if self.allowed_use != _ALLOWED_USE or self.forbidden_use != _FORBIDDEN_USE:
            raise OpenSetResponseError("classification claim boundary drifted")

    @property
    def report_id(self) -> str:
        return _payload_id(self.as_payload())

    def as_payload(self) -> dict[str, object]:
        return {
            "allowed_use": list(self.allowed_use),
            "best_squared_distance": self.best_squared_distance,
            "candidate_class_id": self.candidate_class_id,
            "component_scores": [
                {"component": list(component), "squared_distance": score}
                for component, score in self.component_scores
            ],
            "covariance_null_tolerance": self.covariance_null_tolerance,
            "covariance_null_residual": self.covariance_null_residual,
            "covariance_structural_null_mismatch": (
                self.covariance_structural_null_mismatch
            ),
            "decision_squared_margin": self.decision_squared_margin,
            "equivalence_report_id": self.equivalence_report_id,
            "forbidden_use": list(self.forbidden_use),
            "observation_id": self.observation_id,
            "returned_equivalence_class": list(
                self.returned_equivalence_class
            ),
            "schema": "PR258_OPEN_SET_CLASSIFICATION_REPORT_V3",
            "metric_id": self.metric_id,
            "claim_tier_ceiling": self.claim_tier_ceiling,
            "roadmap_claim_level": {
                "scheme": "roadmap_rescue_v1",
                "level": self.roadmap_claim_level,
            },
            "source_separation_gate": (
                self.source_separation_gate.as_payload()
            ),
            "second_best_squared_distance": self.second_best_squared_distance,
            "squared_distance_margin": self.squared_distance_margin,
            "status": self.status.value,
            "supported_rank": self.supported_rank,
            "unknown_squared_distance_threshold": (
                self.unknown_squared_distance_threshold
            ),
        }


def _classify_prepared(
    *,
    vector: np.ndarray,
    items: tuple[ResponseClassManifoldSpec, ...],
    equivalence_report: ResponseEquivalenceClassReport,
    quotient: _SupportedQuotient,
    threshold: float,
    margin_threshold: float,
    null_tolerance: float,
    source_separation_gate: SourceSeparationGate,
) -> OpenSetClassificationReport:
    base_kwargs = {
        "observation_id": _array_id(
            vector,
            role="PR258_OBSERVATION_V1",
        ),
        "equivalence_report_id": equivalence_report.report_id,
        "unknown_squared_distance_threshold": threshold,
        "decision_squared_margin": margin_threshold,
        "covariance_null_tolerance": null_tolerance,
        "supported_rank": quotient.rank,
        "source_separation_gate": source_separation_gate,
        "_construction_token": _CLASSIFICATION_TOKEN,
    }
    if any(
        item.support_kind is ResponseSupportKind.NEEDS_NATIVE for item in items
    ):
        return OpenSetClassificationReport(
            status=OpenSetClassificationStatus.NEEDS_NATIVE,
            component_scores=(),
            candidate_class_id=None,
            returned_equivalence_class=(),
            best_squared_distance=None,
            second_best_squared_distance=None,
            squared_distance_margin=None,
            covariance_null_residual=0.0,
            covariance_structural_null_mismatch=False,
            **base_kwargs,
        )
    if quotient.covariance_supported_rank == 0:
        (
            class_scores,
            class_null_residuals,
            class_structural_mismatches,
        ) = _class_distances(
            vector,
            items,
            quotient,
        )
        best = min(
            (
                dict(class_scores)[class_id],
                dict(class_structural_mismatches)[class_id],
                dict(class_null_residuals)[class_id],
                class_id,
            )
            for class_id in equivalence_report.class_ids
        )
        return OpenSetClassificationReport(
            status=OpenSetClassificationStatus.OUTSIDE_SUPPORTED_QUOTIENT,
            component_scores=(),
            candidate_class_id=None,
            returned_equivalence_class=equivalence_report.class_ids,
            best_squared_distance=None,
            second_best_squared_distance=None,
            squared_distance_margin=None,
            covariance_null_residual=best[2],
            covariance_structural_null_mismatch=best[1],
            **base_kwargs,
        )
    (
        class_scores,
        class_null_residuals,
        class_structural_mismatches,
    ) = _class_distances(
        vector,
        items,
        quotient,
    )
    class_score_map = dict(class_scores)
    class_null_map = dict(class_null_residuals)
    class_structural_map = dict(class_structural_mismatches)
    component_choices = tuple(
        (
            component,
            *min(
                (
                    class_score_map[class_id],
                    class_structural_map[class_id],
                    class_null_map[class_id],
                    class_id,
                )
                for class_id in component
            ),
        )
        for component in equivalence_report.components
    )
    component_choices = tuple(
        sorted(
            component_choices,
            key=lambda item: (item[1], item[2], item[3], item[0]),
        )
    )
    component_scores = tuple(
        (component, score)
        for component, score, _, _, _ in component_choices
    )
    (
        best_component,
        best,
        structural_mismatch,
        null_residual,
        _,
    ) = component_choices[0]
    second = (
        component_choices[1][1]
        if len(component_choices) > 1
        else math.inf
    )
    score_margin = second - best
    candidate: str | None = None
    returned: tuple[str, ...] = ()
    if structural_mismatch or null_residual > null_tolerance:
        status = OpenSetClassificationStatus.OUTSIDE_SUPPORTED_QUOTIENT
        returned = best_component
    elif equivalence_report.status is ResponseEquivalenceStatus.MISSING_RESPONSE_PROVIDER:
        status = OpenSetClassificationStatus.MISSING_RESPONSE_PROVIDER
    elif equivalence_report.status is ResponseEquivalenceStatus.TYPE_UNIDENTIFIED:
        status = OpenSetClassificationStatus.TYPE_UNIDENTIFIED
        returned = best_component
    elif len(best_component) > 1:
        status = OpenSetClassificationStatus.EQUIVALENCE_CLASS
        returned = best_component
    elif best >= threshold:
        status = OpenSetClassificationStatus.UNKNOWN_CLASS
    elif score_margin <= margin_threshold:
        status = OpenSetClassificationStatus.TYPE_UNIDENTIFIED
        returned = best_component
    elif source_separation_gate.status in {
        SourceSeparationGateStatus.NON_IDENTIFIED,
        SourceSeparationGateStatus.SUM_ONLY,
    }:
        status = OpenSetClassificationStatus.TYPE_UNIDENTIFIED
        returned = best_component
    elif (
        source_separation_gate.status
        is SourceSeparationGateStatus.MISSING_RESPONSE_PROVIDER
    ):
        status = OpenSetClassificationStatus.MISSING_RESPONSE_PROVIDER
        returned = best_component
    else:
        status = OpenSetClassificationStatus.RESPONSE_CLASS_CANDIDATE
        candidate = best_component[0]
    return OpenSetClassificationReport(
        status=status,
        component_scores=component_scores,
        candidate_class_id=candidate,
        returned_equivalence_class=returned,
        best_squared_distance=best,
        second_best_squared_distance=(
            None if math.isinf(second) else second
        ),
        squared_distance_margin=(
            None if math.isinf(score_margin) else score_margin
        ),
        covariance_null_residual=null_residual,
        covariance_structural_null_mismatch=structural_mismatch,
        **base_kwargs,
    )


def _validate_source_gate_binding(
    source_separation_gate: SourceSeparationGate,
    *,
    items: tuple[ResponseClassManifoldSpec, ...],
    quotient: _SupportedQuotient,
) -> None:
    if (
        source_separation_gate.status
        is SourceSeparationGateStatus.NOT_APPLICABLE
    ):
        return
    if (
        source_separation_gate.observable_labels
        != items[0].observable_labels
        or source_separation_gate.covariance_id != quotient.covariance_id
        or source_separation_gate.nuisance_tangent_id
        != quotient.nuisance_tangent_id
        or source_separation_gate.class_contract_ids
        != _class_contract_ids(items)
        or source_separation_gate.convention_id != items[0].convention_id
        or source_separation_gate.nuisance_policy_id
        != items[0].nuisance_policy_id
        or source_separation_gate.metric_id != quotient.metric_id
    ):
        raise OpenSetResponseError(
            "PR-256 source gate is not bound to this PR-258 response contract"
        )


def classify_open_set_response(
    *,
    observation: object,
    classes: Sequence[ResponseClassManifoldSpec],
    equivalence_report: ResponseEquivalenceClassReport,
    covariance: object,
    nuisance_tangent: object | None,
    unknown_squared_distance_threshold: float,
    decision_squared_margin: float,
    covariance_null_tolerance: float,
    absolute_tolerance: float,
    relative_tolerance: float,
    source_separation_gate: SourceSeparationGate,
) -> OpenSetClassificationReport:
    """Classify only when one finite response class is uniquely separated."""

    if type(equivalence_report) is not ResponseEquivalenceClassReport:
        raise OpenSetResponseError(
            "equivalence_report must be a ResponseEquivalenceClassReport"
        )
    items = _validate_class_collection(classes)
    if type(source_separation_gate) is not SourceSeparationGate:
        raise OpenSetResponseError(
            "source_separation_gate must be factory-derived"
        )
    source_semantics = {
        item.source_semantics for item in items
    }
    source_specific = bool(
        source_semantics
        - {ResponseClassSourceSemantics.NEUTRAL}
    )
    if source_specific and (
        source_separation_gate.status
        is SourceSeparationGateStatus.NOT_APPLICABLE
    ):
        raise OpenSetResponseError(
            "local/global response classes require a PR-256 source gate"
        )
    if not source_specific and (
        source_separation_gate.status
        is not SourceSeparationGateStatus.NOT_APPLICABLE
    ):
        raise OpenSetResponseError(
            "neutral response classes require NOT_APPLICABLE source gate"
        )
    threshold = _positive(
        unknown_squared_distance_threshold,
        "unknown_squared_distance_threshold",
    )
    margin_threshold = _nonnegative(
        decision_squared_margin,
        "decision_squared_margin",
    )
    null_tolerance = _nonnegative(
        covariance_null_tolerance,
        "covariance_null_tolerance",
    )
    atol = _positive(absolute_tolerance, "absolute_tolerance")
    rtol = _positive(relative_tolerance, "relative_tolerance")
    vector = _array(
        observation,
        "observation",
        ndim=1,
        columns=len(items[0].observable_labels),
    )
    if tuple(item.class_id for item in items) != equivalence_report.class_ids:
        raise OpenSetResponseError(
            "classes differ from the equivalence report"
        )
    if tuple(
        (item.class_id, item.response_content_id or "NEEDS_NATIVE")
        for item in items
    ) != equivalence_report.class_response_ids:
        raise OpenSetResponseError(
            "class response bytes differ from the equivalence report"
        )
    if _class_contract_ids(items) != equivalence_report.class_contract_ids:
        raise OpenSetResponseError(
            "class provider, convention, nuisance-policy, or response "
            "contract differs from the equivalence report"
        )
    quotient = _supported_quotient(
        covariance,
        nuisance_tangent,
        dimension=vector.shape[0],
        absolute_tolerance=atol,
        relative_tolerance=rtol,
    )
    if (
        quotient.covariance_id != equivalence_report.covariance_id
        or quotient.nuisance_tangent_id
        != equivalence_report.nuisance_tangent_id
    ):
        raise OpenSetResponseError(
            "covariance or nuisance tangent differs from the "
            "equivalence report"
        )
    if (
        quotient.metric_id != equivalence_report.metric_id
        or atol != equivalence_report.absolute_tolerance
        or rtol != equivalence_report.relative_tolerance
    ):
        raise OpenSetResponseError(
            "metric or tolerance contract differs from equivalence report"
        )
    _validate_source_gate_binding(
        source_separation_gate,
        items=items,
        quotient=quotient,
    )
    return _classify_prepared(
        vector=vector,
        items=items,
        equivalence_report=equivalence_report,
        quotient=quotient,
        threshold=threshold,
        margin_threshold=margin_threshold,
        null_tolerance=null_tolerance,
        source_separation_gate=source_separation_gate,
    )


def classify_open_set_response_batch(
    *,
    observations: object,
    classes: Sequence[ResponseClassManifoldSpec],
    equivalence_report: ResponseEquivalenceClassReport,
    covariance: object,
    nuisance_tangent: object | None,
    unknown_squared_distance_threshold: float,
    decision_squared_margin: float,
    covariance_null_tolerance: float,
    absolute_tolerance: float,
    relative_tolerance: float,
    source_separation_gate: SourceSeparationGate,
) -> tuple[OpenSetClassificationReport, ...]:
    """Classify a frozen observation batch with one quotient construction."""

    if type(equivalence_report) is not ResponseEquivalenceClassReport:
        raise OpenSetResponseError(
            "equivalence_report must be a ResponseEquivalenceClassReport"
        )
    items = _validate_class_collection(classes)
    if type(source_separation_gate) is not SourceSeparationGate:
        raise OpenSetResponseError(
            "source_separation_gate must be factory-derived"
        )
    source_specific = any(
        item.source_semantics is not ResponseClassSourceSemantics.NEUTRAL
        for item in items
    )
    if source_specific == (
        source_separation_gate.status
        is SourceSeparationGateStatus.NOT_APPLICABLE
    ):
        raise OpenSetResponseError(
            "source gate applicability does not match class semantics"
        )
    threshold = _positive(
        unknown_squared_distance_threshold,
        "unknown_squared_distance_threshold",
    )
    margin_threshold = _nonnegative(
        decision_squared_margin,
        "decision_squared_margin",
    )
    null_tolerance = _nonnegative(
        covariance_null_tolerance,
        "covariance_null_tolerance",
    )
    atol = _positive(absolute_tolerance, "absolute_tolerance")
    rtol = _positive(relative_tolerance, "relative_tolerance")
    matrix = _array(
        observations,
        "observations",
        ndim=2,
        columns=len(items[0].observable_labels),
    )
    if tuple(item.class_id for item in items) != equivalence_report.class_ids:
        raise OpenSetResponseError(
            "classes differ from the equivalence report"
        )
    if tuple(
        (item.class_id, item.response_content_id or "NEEDS_NATIVE")
        for item in items
    ) != equivalence_report.class_response_ids:
        raise OpenSetResponseError(
            "class response bytes differ from the equivalence report"
        )
    if _class_contract_ids(items) != equivalence_report.class_contract_ids:
        raise OpenSetResponseError(
            "class provider, convention, nuisance-policy, or response "
            "contract differs from the equivalence report"
        )
    quotient = _supported_quotient(
        covariance,
        nuisance_tangent,
        dimension=matrix.shape[1],
        absolute_tolerance=atol,
        relative_tolerance=rtol,
    )
    if (
        quotient.covariance_id != equivalence_report.covariance_id
        or quotient.nuisance_tangent_id
        != equivalence_report.nuisance_tangent_id
        or quotient.metric_id != equivalence_report.metric_id
        or atol != equivalence_report.absolute_tolerance
        or rtol != equivalence_report.relative_tolerance
    ):
        raise OpenSetResponseError(
            "batch metric contract differs from equivalence report"
        )
    _validate_source_gate_binding(
        source_separation_gate,
        items=items,
        quotient=quotient,
    )
    return tuple(
        _classify_prepared(
            vector=row,
            items=items,
            equivalence_report=equivalence_report,
            quotient=quotient,
            threshold=threshold,
            margin_threshold=margin_threshold,
            null_tolerance=null_tolerance,
            source_separation_gate=source_separation_gate,
        )
        for row in matrix
    )


def _mcse(rate: float, count: int) -> float:
    return math.sqrt(max(rate * (1.0 - rate), 0.0) / count)


def _classification_protocol(
    report: OpenSetClassificationReport,
) -> tuple[object, ...]:
    return (
        report.metric_id,
        report.unknown_squared_distance_threshold,
        report.decision_squared_margin,
        report.covariance_null_tolerance,
        report.supported_rank,
        report.source_separation_gate.status,
        report.source_separation_gate.report_id,
        report.source_separation_gate.gate_id,
        report.claim_tier_ceiling,
        report.roadmap_claim_level,
    )


def _perturbation_metadata(
    item: ResponseClassManifoldSpec,
) -> tuple[object, ...]:
    """Return class fields that a support-only perturbation cannot change."""

    return (
        item.class_id,
        item.support_kind,
        item.provider_id,
        item.observable_labels,
        item.convention_id,
        item.nuisance_policy_id,
        item.transfer_source,
        item.response_role,
        item.data_source,
        item.source_semantics,
        item.source_response_id,
    )


def _support_row_keys(item: ResponseClassManifoldSpec) -> set[bytes]:
    nodes = item.support_nodes
    if nodes is None:
        raise OpenSetResponseError(
            "finite-support perturbations require finite response nodes"
        )
    return {
        np.asarray(row, dtype=np.float64).tobytes(order="C")
        for row in nodes
    }


def _validate_finite_support_perturbation(
    *,
    kind: FiniteSupportPerturbationKind,
    baseline: Sequence[ResponseClassManifoldSpec],
    perturbed: Sequence[ResponseClassManifoldSpec],
) -> tuple[ResponseClassManifoldSpec, ...]:
    """Validate a declared support edit instead of trusting its map key."""

    base = _validate_class_collection(baseline)
    changed = _validate_class_collection(perturbed)
    if tuple(item.class_id for item in changed) != tuple(
        item.class_id for item in base
    ):
        raise OpenSetResponseError(
            f"{kind.value} must preserve response class ids"
        )
    if any(
        _perturbation_metadata(left) != _perturbation_metadata(right)
        for left, right in zip(base, changed, strict=True)
    ):
        raise OpenSetResponseError(
            f"{kind.value} must change support nodes only"
        )

    base_sets = tuple(_support_row_keys(item) for item in base)
    changed_sets = tuple(_support_row_keys(item) for item in changed)
    if kind is FiniteSupportPerturbationKind.EXACT_DUPLICATE:
        if base_sets != changed_sets or not any(
            right.duplicate_node_count > left.duplicate_node_count
            for left, right in zip(base, changed, strict=True)
        ):
            raise OpenSetResponseError(
                "EXACT_DUPLICATE must preserve canonical supports and "
                "increase duplicate provenance"
            )
        if any(
            right.duplicate_node_count < left.duplicate_node_count
            for left, right in zip(base, changed, strict=True)
        ):
            raise OpenSetResponseError(
                "EXACT_DUPLICATE must not remove duplicate provenance"
            )
        return changed

    if base_sets == changed_sets:
        raise OpenSetResponseError(
            f"{kind.value} cannot reuse the baseline support"
        )

    additions = tuple(
        right - left
        for left, right in zip(base_sets, changed_sets, strict=True)
    )
    removals = tuple(
        left - right
        for left, right in zip(base_sets, changed_sets, strict=True)
    )
    if kind in {
        FiniteSupportPerturbationKind.REFINEMENT,
        FiniteSupportPerturbationKind.EXPANSION,
    }:
        if any(removals) or not any(additions):
            raise OpenSetResponseError(
                f"{kind.value} must be a strict support superset"
            )
        outside = False
        for left, right in zip(base, changed, strict=True):
            base_nodes = left.support_nodes
            changed_nodes = right.support_nodes
            assert base_nodes is not None and changed_nodes is not None
            lower = np.min(base_nodes, axis=0)
            upper = np.max(base_nodes, axis=0)
            left_keys = _support_row_keys(left)
            added_rows = [
                row
                for row in changed_nodes
                if np.asarray(row, dtype=np.float64).tobytes(order="C")
                not in left_keys
            ]
            outside = outside or any(
                np.any(row < lower) or np.any(row > upper)
                for row in added_rows
            )
        expected_outside = (
            kind is FiniteSupportPerturbationKind.EXPANSION
        )
        if outside is not expected_outside:
            qualifier = "outside" if expected_outside else "inside"
            raise OpenSetResponseError(
                f"{kind.value} additions must be {qualifier} the baseline "
                "coordinate envelope"
            )
        return changed

    if any(additions) or not any(removals):
        raise OpenSetResponseError(
            f"{kind.value} must be a strict support subset"
        )
    base_absolute_bounds = tuple(
        (
            np.min(np.abs(item.support_nodes), axis=0),
            np.max(np.abs(item.support_nodes), axis=0),
        )
        for item in base
    )
    changed_absolute_bounds = tuple(
        (
            np.min(np.abs(item.support_nodes), axis=0),
            np.max(np.abs(item.support_nodes), axis=0),
        )
        for item in changed
    )
    if kind is FiniteSupportPerturbationKind.CONTRACTION:
        if not all(
            bool(np.all(right_max <= left_max))
            for (_, left_max), (_, right_max) in zip(
                base_absolute_bounds,
                changed_absolute_bounds,
                strict=True,
            )
        ) or not any(
            bool(np.any(right_max < left_max))
            for (_, left_max), (_, right_max) in zip(
                base_absolute_bounds,
                changed_absolute_bounds,
                strict=True,
            )
        ):
            raise OpenSetResponseError(
                "CONTRACTION must strictly reduce a support absolute "
                "coordinate maximum"
            )
    elif kind is FiniteSupportPerturbationKind.BOUNDARY_RESTRICTION:
        if not all(
            bool(np.all(right_min >= left_min))
            for (left_min, _), (right_min, _) in zip(
                base_absolute_bounds,
                changed_absolute_bounds,
                strict=True,
            )
        ) or not any(
            bool(np.any(right_min > left_min))
            for (left_min, _), (right_min, _) in zip(
                base_absolute_bounds,
                changed_absolute_bounds,
                strict=True,
            )
        ):
            raise OpenSetResponseError(
                "BOUNDARY_RESTRICTION must strictly increase a support "
                "absolute coordinate minimum"
            )
    return changed


@dataclass(frozen=True)
class OpenSetBenchmarkReport:
    status: OpenSetBenchmarkStatus
    false_response_class_candidate_rate: float
    equivalence_class_coverage: float
    unknown_generator_conditional_detection_rate: float
    abstention_rate: float
    finite_support_perturbation_sensitivity_rates: tuple[
        tuple[FiniteSupportPerturbationKind, float], ...
    ]
    maximum_observed_mcse: float
    maximum_mcse: float
    minimum_replicates_per_cell: int
    maximum_replicates_per_cell: int
    known_count: int
    equivalence_count: int
    unknown_count: int
    minimal_reopening_observable_ids: tuple[str, ...]
    master_seed: int
    calibration_receipt: str
    split_receipt: str
    thresholds_frozen_before_held_out: bool
    observed_data_used: bool
    pr151_data_used: bool
    old_rust_output_used: bool
    native_solver_output_used: bool
    transfer_source: TransferSource
    owner: str = PR258_ARTIFACT_OWNER
    scope: str = PR258_ARTIFACT_SCOPE
    artifact_mode: str = PR258_ARTIFACT_MODE
    sky_support_status: str = PR258_SKY_SUPPORT_STATUS
    null_mock_status: str = PR258_NULL_MOCK_STATUS
    covariance_status: str = PR258_COVARIANCE_STATUS
    claim_tier_ceiling: str = PR258_MACHINE_CLAIM_TIER
    roadmap_claim_level: str = PR258_ROADMAP_CLAIM_LEVEL
    allowed_use: tuple[str, ...] = _ALLOWED_USE
    forbidden_use: tuple[str, ...] = _FORBIDDEN_USE
    _construction_token: InitVar[object] = None

    def __post_init__(self, _construction_token: object) -> None:
        if _construction_token is not _BENCHMARK_TOKEN:
            raise OpenSetResponseError(
                "OpenSetBenchmarkReport must be factory-derived"
            )
        if not isinstance(self.status, OpenSetBenchmarkStatus):
            raise OpenSetResponseError("benchmark status is invalid")
        for name in (
            "false_response_class_candidate_rate",
            "equivalence_class_coverage",
            "unknown_generator_conditional_detection_rate",
            "abstention_rate",
        ):
            value = _finite_real(getattr(self, name), name)
            if not 0.0 <= value <= 1.0:
                raise OpenSetResponseError(f"{name} must be in [0, 1]")
        kinds = []
        for kind, rate in self.finite_support_perturbation_sensitivity_rates:
            if not isinstance(kind, FiniteSupportPerturbationKind):
                raise OpenSetResponseError(
                    "finite support perturbation kind is invalid"
                )
            if not 0.0 <= _finite_real(rate, kind.value) <= 1.0:
                raise OpenSetResponseError(
                    "finite support sensitivity rates must be in [0, 1]"
                )
            kinds.append(kind)
        if len(kinds) != len(set(kinds)):
            raise OpenSetResponseError(
                "finite support perturbation kinds must be unique"
            )
        required_kinds = set(FiniteSupportPerturbationKind)
        if set(kinds) != required_kinds:
            raise OpenSetResponseError(
                "every registered finite-support perturbation kind must be "
                "measured exactly once"
            )
        _nonnegative(self.maximum_observed_mcse, "maximum_observed_mcse")
        if (
            _positive(self.maximum_mcse, "maximum_mcse")
            != PR258_MAXIMUM_MCSE
        ):
            raise OpenSetResponseError(
                "maximum_mcse must equal the preregistered PR-258 value"
            )
        if (
            _positive_int(
                self.minimum_replicates_per_cell,
                "minimum_replicates_per_cell",
            )
            != PR258_MINIMUM_MC_REPLICATES
        ):
            raise OpenSetResponseError(
                "minimum_replicates_per_cell must equal the preregistered "
                "PR-258 value"
            )
        if (
            _positive_int(
                self.maximum_replicates_per_cell,
                "maximum_replicates_per_cell",
            )
            != PR258_MAXIMUM_MC_REPLICATES
        ):
            raise OpenSetResponseError(
                "maximum_replicates_per_cell must equal the preregistered "
                "PR-258 value"
            )
        _positive_int(self.known_count, "known_count")
        _positive_int(self.equivalence_count, "equivalence_count")
        _positive_int(self.unknown_count, "unknown_count")
        if any(
            count > self.maximum_replicates_per_cell
            for count in (
                self.known_count,
                self.equivalence_count,
                self.unknown_count,
            )
        ):
            raise OpenSetResponseError(
                "benchmark cell count exceeds maximum_replicates_per_cell"
            )
        _positive_int(self.master_seed, "master_seed")
        _receipt(self.calibration_receipt, "calibration_receipt")
        _receipt(self.split_receipt, "split_receipt")
        if self.thresholds_frozen_before_held_out is not True:
            raise OpenSetResponseError(
                "thresholds must be frozen before held-out evaluation"
            )
        if any(
            (
                self.observed_data_used,
                self.pr151_data_used,
                self.old_rust_output_used,
                self.native_solver_output_used,
            )
        ):
            raise OpenSetResponseError(
                "PR-258 benchmark must remain synthetic and pre-native"
            )
        if self.transfer_source is not TransferSource.NONE:
            raise OpenSetResponseError(
                "PR-258 synthetic benchmark transfer_source must be none"
            )
        expected_artifact_metadata = {
            "owner": PR258_ARTIFACT_OWNER,
            "scope": PR258_ARTIFACT_SCOPE,
            "artifact_mode": PR258_ARTIFACT_MODE,
            "sky_support_status": PR258_SKY_SUPPORT_STATUS,
            "null_mock_status": PR258_NULL_MOCK_STATUS,
            "covariance_status": PR258_COVARIANCE_STATUS,
        }
        if any(
            getattr(self, name) != expected
            for name, expected in expected_artifact_metadata.items()
        ):
            raise OpenSetResponseError(
                "benchmark artifact metadata drifted"
            )
        if self.allowed_use != _ALLOWED_USE or self.forbidden_use != _FORBIDDEN_USE:
            raise OpenSetResponseError("benchmark claim boundary drifted")
        if (
            self.claim_tier_ceiling != PR258_MACHINE_CLAIM_TIER
            or self.roadmap_claim_level != PR258_ROADMAP_CLAIM_LEVEL
        ):
            raise OpenSetResponseError("benchmark claim-tier boundary drifted")

    @property
    def report_id(self) -> str:
        return _payload_id(self.as_payload())

    def as_payload(self) -> dict[str, object]:
        return {
            "abstention_rate": self.abstention_rate,
            "allowed_use": list(self.allowed_use),
            "artifact_mode": self.artifact_mode,
            "covariance_status": self.covariance_status,
            "data_provenance": {
                "native_solver_output_used": self.native_solver_output_used,
                "observed_data_used": self.observed_data_used,
                "old_rust_output_used": self.old_rust_output_used,
                "pr151_data_used": self.pr151_data_used,
                "transfer_source": self.transfer_source.value,
            },
            "equivalence_class_coverage": self.equivalence_class_coverage,
            "equivalence_count": self.equivalence_count,
            "false_response_class_candidate_rate": (
                self.false_response_class_candidate_rate
            ),
            "forbidden_use": list(self.forbidden_use),
            "known_count": self.known_count,
            "master_seed": self.master_seed,
            "null_mock_status": self.null_mock_status,
            "owner": self.owner,
            "calibration_receipt": self.calibration_receipt,
            "split_receipt": self.split_receipt,
            "thresholds_frozen_before_held_out": (
                self.thresholds_frozen_before_held_out
            ),
            "claim_tier_ceiling": self.claim_tier_ceiling,
            "roadmap_claim_level": {
                "scheme": "roadmap_rescue_v1",
                "level": self.roadmap_claim_level,
            },
            "maximum_observed_mcse": self.maximum_observed_mcse,
            "maximum_mcse": self.maximum_mcse,
            "minimum_replicates_per_cell": (
                self.minimum_replicates_per_cell
            ),
            "maximum_replicates_per_cell": (
                self.maximum_replicates_per_cell
            ),
            "minimal_reopening_observable_ids": list(
                self.minimal_reopening_observable_ids
            ),
            "schema": "PR258_OPEN_SET_BENCHMARK_REPORT_V3",
            "scope": self.scope,
            "sky_support_status": self.sky_support_status,
            "status": self.status.value,
            "finite_support_perturbation_sensitivity_rates": {
                kind.value: rate
                for kind, rate
                in self.finite_support_perturbation_sensitivity_rates
            },
            "unknown_count": self.unknown_count,
            "unknown_generator_conditional_detection_rate": (
                self.unknown_generator_conditional_detection_rate
            ),
        }


def evaluate_open_set_benchmark(
    *,
    known_reports: Sequence[OpenSetClassificationReport],
    known_truth_class_ids: Sequence[str],
    equivalence_reports: Sequence[OpenSetClassificationReport],
    expected_equivalence_class: Sequence[str],
    unknown_reports: Sequence[OpenSetClassificationReport],
    support_perturbed_reports: Mapping[
        FiniteSupportPerturbationKind | str,
        Sequence[OpenSetClassificationReport],
    ],
    baseline_classes: Sequence[ResponseClassManifoldSpec],
    support_perturbed_classes: Mapping[
        FiniteSupportPerturbationKind | str,
        Sequence[ResponseClassManifoldSpec],
    ],
    baseline_equivalence_report: ResponseEquivalenceClassReport,
    equivalence_report: ResponseEquivalenceClassReport,
    support_perturbed_equivalence_reports: Mapping[
        FiniteSupportPerturbationKind | str,
        ResponseEquivalenceClassReport,
    ],
    master_seed: int,
    calibration_receipt: str,
    split_receipt: str,
    thresholds_frozen_before_held_out: bool,
    maximum_mcse: float = PR258_MAXIMUM_MCSE,
) -> OpenSetBenchmarkReport:
    """Aggregate preregistered synthetic decisions without fitting a model."""

    known = tuple(known_reports)
    equivalent = tuple(equivalence_reports)
    unknown = tuple(unknown_reports)
    declared_mcse = _positive(maximum_mcse, "maximum_mcse")
    if declared_mcse != PR258_MAXIMUM_MCSE:
        raise OpenSetResponseError(
            "maximum_mcse must equal the preregistered PR-258 value"
        )
    if any(
        count > PR258_MAXIMUM_MC_REPLICATES
        for count in (len(known), len(equivalent), len(unknown))
    ):
        raise OpenSetResponseError(
            "benchmark cell count exceeds maximum_replicates_per_cell"
        )
    truth = tuple(
        _class_id(value, "known_truth_class_id")
        for value in known_truth_class_ids
    )
    if not isinstance(support_perturbed_reports, Mapping):
        raise OpenSetResponseError(
            "support_perturbed_reports must be keyed by perturbation kind"
        )
    if not isinstance(support_perturbed_classes, Mapping):
        raise OpenSetResponseError(
            "support_perturbed_classes must be keyed by perturbation kind"
        )
    if not isinstance(support_perturbed_equivalence_reports, Mapping):
        raise OpenSetResponseError(
            "support_perturbed_equivalence_reports must be keyed by "
            "perturbation kind"
        )
    perturbed_by_kind = {}
    for raw_kind, reports in support_perturbed_reports.items():
        try:
            kind = (
                raw_kind
                if isinstance(raw_kind, FiniteSupportPerturbationKind)
                else FiniteSupportPerturbationKind(str(raw_kind))
            )
        except (TypeError, ValueError) as exc:
            raise OpenSetResponseError(
                "finite support perturbation kind is invalid"
            ) from exc
        if kind in perturbed_by_kind:
            raise OpenSetResponseError(
                "finite support perturbation kinds must be unique"
            )
        perturbed_by_kind[kind] = tuple(reports)
    if any(
        len(reports) > PR258_MAXIMUM_MC_REPLICATES
        for reports in perturbed_by_kind.values()
    ):
        raise OpenSetResponseError(
            "support-perturbed benchmark cell exceeds "
            "maximum_replicates_per_cell"
        )
    required_kinds = set(FiniteSupportPerturbationKind)
    if set(perturbed_by_kind) != required_kinds:
        raise OpenSetResponseError(
            "support-perturbed reports must cover every registered "
            "perturbation kind exactly"
        )
    baseline_items = _validate_class_collection(baseline_classes)
    perturbed_classes_by_kind = {}
    for raw_kind, classes in support_perturbed_classes.items():
        try:
            kind = (
                raw_kind
                if isinstance(raw_kind, FiniteSupportPerturbationKind)
                else FiniteSupportPerturbationKind(str(raw_kind))
            )
        except (TypeError, ValueError) as exc:
            raise OpenSetResponseError(
                "finite support perturbation class kind is invalid"
            ) from exc
        if kind in perturbed_classes_by_kind:
            raise OpenSetResponseError(
                "finite support perturbation class kinds must be unique"
            )
        perturbed_classes_by_kind[kind] = (
            _validate_finite_support_perturbation(
                kind=kind,
                baseline=baseline_items,
                perturbed=classes,
            )
        )
    if set(perturbed_classes_by_kind) != required_kinds:
        raise OpenSetResponseError(
            "support-perturbed classes must cover every registered "
            "perturbation kind exactly"
        )
    perturbed_equivalence_by_kind = {}
    for raw_kind, report in support_perturbed_equivalence_reports.items():
        try:
            kind = (
                raw_kind
                if isinstance(raw_kind, FiniteSupportPerturbationKind)
                else FiniteSupportPerturbationKind(str(raw_kind))
            )
        except (TypeError, ValueError) as exc:
            raise OpenSetResponseError(
                "finite support perturbation equivalence kind is invalid"
            ) from exc
        if kind in perturbed_equivalence_by_kind:
            raise OpenSetResponseError(
                "finite support perturbation equivalence kinds must be unique"
            )
        if type(report) is not ResponseEquivalenceClassReport:
            raise OpenSetResponseError(
                "perturbed equivalence values must be "
                "ResponseEquivalenceClassReport values"
            )
        perturbed_equivalence_by_kind[kind] = report
    if set(perturbed_equivalence_by_kind) != required_kinds:
        raise OpenSetResponseError(
            "perturbed equivalence reports must cover every registered "
            "perturbation kind exactly"
        )
    expected = tuple(sorted(_class_id(value) for value in expected_equivalence_class))
    if not known or len(known) != len(truth):
        raise OpenSetResponseError(
            "known reports and truth ids must be non-empty and aligned"
        )
    if not equivalent or not unknown:
        raise OpenSetResponseError(
            "equivalence and unknown report sets must be non-empty"
        )
    if any(len(reports) != len(known) for reports in perturbed_by_kind.values()):
        raise OpenSetResponseError(
            "support-perturbed reports must align with known reports"
        )
    all_reports = known + equivalent + unknown + tuple(
        report
        for reports in perturbed_by_kind.values()
        for report in reports
    )
    if any(type(item) is not OpenSetClassificationReport for item in all_reports):
        raise OpenSetResponseError(
            "benchmark inputs must be OpenSetClassificationReport values"
        )
    if (
        type(baseline_equivalence_report)
        is not ResponseEquivalenceClassReport
        or type(equivalence_report) is not ResponseEquivalenceClassReport
    ):
        raise OpenSetResponseError(
            "baseline and equivalence-cell reports must be "
            "ResponseEquivalenceClassReport values"
        )
    if (
        _class_contract_ids(baseline_items)
        != baseline_equivalence_report.class_contract_ids
    ):
        raise OpenSetResponseError(
            "baseline classes do not bind the supplied baseline "
            "equivalence report"
        )
    for kind, classes in perturbed_classes_by_kind.items():
        if (
            _class_contract_ids(classes)
            != perturbed_equivalence_by_kind[kind].class_contract_ids
        ):
            raise OpenSetResponseError(
                f"{kind.value} classes do not bind their supplied "
                "perturbed equivalence report"
            )
    if any(
        report.equivalence_report_id
        != baseline_equivalence_report.report_id
        for report in (*known, *unknown)
    ):
        raise OpenSetResponseError(
            "known and unknown reports must bind the supplied baseline "
            "equivalence report"
        )
    if any(
        report.equivalence_report_id != equivalence_report.report_id
        for report in equivalent
    ):
        raise OpenSetResponseError(
            "equivalence-cell classifications must bind the supplied "
            "equivalence report"
        )
    for kind, reports in perturbed_by_kind.items():
        expected_report_id = perturbed_equivalence_by_kind[kind].report_id
        if any(
            report.equivalence_report_id != expected_report_id
            for report in reports
        ):
            raise OpenSetResponseError(
                f"{kind.value} classifications do not bind their supplied "
                "perturbed equivalence report"
            )
    if (
        perturbed_equivalence_by_kind[
            FiniteSupportPerturbationKind.EXACT_DUPLICATE
        ].report_id
        != baseline_equivalence_report.report_id
    ):
        raise OpenSetResponseError(
            "exact-duplicate perturbation must preserve the complete "
            "baseline equivalence report identity"
        )
    nonduplicate_ids = tuple(
        perturbed_equivalence_by_kind[kind].report_id
        for kind in FiniteSupportPerturbationKind
        if kind is not FiniteSupportPerturbationKind.EXACT_DUPLICATE
    )
    if (
        baseline_equivalence_report.report_id in nonduplicate_ids
        or len(set(nonduplicate_ids)) != len(nonduplicate_ids)
    ):
        raise OpenSetResponseError(
            "non-duplicate perturbations require distinct, non-baseline "
            "equivalence report identities"
        )
    if any(truth_id not in baseline_equivalence_report.class_ids for truth_id in truth):
        raise OpenSetResponseError(
            "known truth ids must belong to the baseline response library"
        )
    if expected not in equivalence_report.components:
        raise OpenSetResponseError(
            "expected equivalence class must be a component of the supplied "
            "equivalence report"
        )
    protocol = _classification_protocol(known[0])
    if any(_classification_protocol(report) != protocol for report in all_reports):
        raise OpenSetResponseError(
            "benchmark classifications must share one frozen decision protocol"
        )
    false_ids = sum(
        report.status is OpenSetClassificationStatus.RESPONSE_CLASS_CANDIDATE
        and report.candidate_class_id != truth_id
        for report, truth_id in zip(known, truth, strict=True)
    )
    equivalence_hits = sum(
        report.status is OpenSetClassificationStatus.EQUIVALENCE_CLASS
        and report.returned_equivalence_class == expected
        for report in equivalent
    )
    unknown_hits = sum(
        report.status is OpenSetClassificationStatus.UNKNOWN_CLASS
        for report in unknown
    )
    decisions = known + equivalent + unknown
    abstentions = sum(
        report.status
        is not OpenSetClassificationStatus.RESPONSE_CLASS_CANDIDATE
        for report in decisions
    )

    def decision_key(report: OpenSetClassificationReport) -> tuple[object, ...]:
        return (
            report.status,
            report.candidate_class_id,
            report.returned_equivalence_class,
        )

    sensitivity_rates = tuple(
        (
            kind,
            sum(
                decision_key(base) != decision_key(changed)
                for base, changed in zip(known, reports, strict=True)
            )
            / len(known),
        )
        for kind, reports in sorted(
            perturbed_by_kind.items(),
            key=lambda item: item[0].value,
        )
    )
    duplicate_rate = dict(sensitivity_rates)[
        FiniteSupportPerturbationKind.EXACT_DUPLICATE
    ]
    if duplicate_rate != 0.0:
        raise OpenSetResponseError(
            "exact duplicate support nodes changed a decision"
        )
    false_rate = false_ids / len(known)
    equivalence_coverage = equivalence_hits / len(equivalent)
    unknown_rate = unknown_hits / len(unknown)
    abstention_rate = abstentions / len(decisions)
    rate_mcses = (
        _mcse(false_rate, len(known)),
        _mcse(equivalence_coverage, len(equivalent)),
        _mcse(unknown_rate, len(unknown)),
        _mcse(abstention_rate, len(decisions)),
        *(
            _mcse(rate, len(known))
            for _, rate in sensitivity_rates
        ),
    )
    observed_mcse = max(rate_mcses)
    seed = _positive_int(master_seed, "master_seed")
    enough_replicates = min(len(known), len(equivalent), len(unknown)) >= (
        PR258_MINIMUM_MC_REPLICATES
    )
    if not enough_replicates or observed_mcse > declared_mcse:
        status = OpenSetBenchmarkStatus.INCONCLUSIVE_MC_PRECISION
    else:
        error_limit = 0.05 + 3.0 * _mcse(false_rate, len(known))
        equivalence_limit = 0.95 - 3.0 * _mcse(
            equivalence_coverage,
            len(equivalent),
        )
        unknown_limit = 0.95 - 3.0 * _mcse(unknown_rate, len(unknown))
        status = (
            OpenSetBenchmarkStatus.MEASURED_PASS
            if (
                false_rate <= error_limit
                and equivalence_coverage >= equivalence_limit
                and unknown_rate >= unknown_limit
            )
            else OpenSetBenchmarkStatus.MEASURED_FAIL
        )
    return OpenSetBenchmarkReport(
        status=status,
        false_response_class_candidate_rate=false_rate,
        equivalence_class_coverage=equivalence_coverage,
        unknown_generator_conditional_detection_rate=unknown_rate,
        abstention_rate=abstention_rate,
        finite_support_perturbation_sensitivity_rates=sensitivity_rates,
        maximum_observed_mcse=observed_mcse,
        maximum_mcse=declared_mcse,
        minimum_replicates_per_cell=PR258_MINIMUM_MC_REPLICATES,
        maximum_replicates_per_cell=PR258_MAXIMUM_MC_REPLICATES,
        known_count=len(known),
        equivalence_count=len(equivalent),
        unknown_count=len(unknown),
        minimal_reopening_observable_ids=(
            equivalence_report.minimal_reopening_observable_ids
        ),
        master_seed=seed,
        calibration_receipt=_receipt(
            calibration_receipt,
            "calibration_receipt",
        ),
        split_receipt=_receipt(split_receipt, "split_receipt"),
        thresholds_frozen_before_held_out=(
            thresholds_frozen_before_held_out
        ),
        observed_data_used=False,
        pr151_data_used=False,
        old_rust_output_used=False,
        native_solver_output_used=False,
        transfer_source=TransferSource.NONE,
        _construction_token=_BENCHMARK_TOKEN,
    )


__all__ = [
    "FiniteSupportPerturbationKind",
    "FutureNativeResponseAdapterSpec",
    "OpenSetBenchmarkReport",
    "OpenSetBenchmarkStatus",
    "OpenSetClassificationReport",
    "OpenSetClassificationStatus",
    "OpenSetResponseError",
    "PR258_MAXIMUM_MCSE",
    "PR258_MAXIMUM_MC_REPLICATES",
    "PR258_MACHINE_CLAIM_TIER",
    "PR258_METRIC_ID",
    "PR258_MINIMUM_MC_REPLICATES",
    "PR258_ROADMAP_CLAIM_LEVEL",
    "ReopeningObservableSpec",
    "ReopeningObservableStatus",
    "ResponseClassSourceSemantics",
    "ResponseClassManifoldSpec",
    "ResponseEquivalenceClassReport",
    "ResponseEquivalenceStatus",
    "ResponseSupportKind",
    "SourceSeparationGate",
    "SourceSeparationGateStatus",
    "build_future_native_response_adapter",
    "build_reopening_observable_spec",
    "build_response_class_manifold",
    "build_response_equivalence_report",
    "classify_open_set_response",
    "classify_open_set_response_batch",
    "evaluate_open_set_benchmark",
    "source_separation_not_applicable",
]
