"""Typed depth, mask, feature-transport, and coherence contracts.

The path is observer-side and pre-solver.  It binds each depth step to one
exact sky support, mask, selection, covariance, feature layout, and source
artifact.  A later/deeper step may use only a subset of the preceding sky
support; incompatible supports are never silently pooled.

OBSSTAT owns feature extraction and transport.  MIO owns the diagnostic
coherence report and its depth-scramble negative control.  HTT likelihood
adapters live in :mod:`htt.infer.depth_path`; this module contains no
likelihood, posterior, evidence, geometry, or family-identification operation.
"""

from __future__ import annotations

from dataclasses import InitVar, dataclass, field
from enum import Enum
import hashlib
import json
import math
from numbers import Integral, Real
from typing import Sequence

import numpy as np

from common.contracts import SkySupport


class DepthPathError(ValueError):
    """Raised when a depth-path contract fails closed."""


class _StringEnum(str, Enum):
    def __str__(self) -> str:
        return self.value


class CoherenceCellStatus(_StringEnum):
    DEFINED = "DEFINED"
    COVARIANCE_RANK_DEFICIENT = "COVARIANCE_RANK_DEFICIENT"


class DepthCoherenceStatus(_StringEnum):
    DEFINED = "DEFINED"
    PARTIAL = "PARTIAL"
    UNAVAILABLE = "UNAVAILABLE"


class ScrambleControlStatus(_StringEnum):
    PASSED = "PASSED"
    FAILED = "FAILED"
    INCONCLUSIVE = "INCONCLUSIVE"


DEPTH_PATH_CLAIM_CEILING = "diagnostic_only"
DEPTH_PATH_NESTING_RULE = "TARGET_SUPPORT_SUBSET_OF_SOURCE"
DEPTH_PATH_ALLOWED_USE = (
    "observer-side feature transport across explicitly nested sky supports",
    "MIO depth-coherence diagnostic",
    "HTT model-conditional likelihood input through its separate adapter",
    "depth-scramble negative control",
)
DEPTH_PATH_FORBIDDEN_USE = (
    "silent pooling of incompatible sky supports",
    "global-tilt evidence from coherence alone",
    "native solver or native morphology-atlas result",
    "geometry detection or Bianchi family identification",
)

_STRATUM_TOKEN = object()
_KERNEL_TOKEN = object()
_PATH_TOKEN = object()
_STEP_TOKEN = object()
_CELL_TOKEN = object()
_REPORT_TOKEN = object()
_SCRAMBLE_TOKEN = object()


def _text(value: object, name: str) -> str:
    if not isinstance(value, str) or not value.strip() or value != value.strip():
        raise DepthPathError(f"{name} must be non-empty trimmed text")
    return value


def _texts(
    values: Sequence[object],
    name: str,
    *,
    minimum: int = 1,
) -> tuple[str, ...]:
    if isinstance(values, (str, bytes)):
        raise DepthPathError(f"{name} must be a sequence of text")
    result = tuple(_text(value, name) for value in values)
    if len(result) < minimum:
        raise DepthPathError(f"{name} must contain at least {minimum} value(s)")
    if len(result) != len(set(result)):
        raise DepthPathError(f"{name} must not contain duplicates")
    return result


def _real(value: object, name: str) -> float:
    if isinstance(value, bool) or not isinstance(value, Real):
        raise DepthPathError(f"{name} must be real")
    result = float(value)
    if not math.isfinite(result):
        raise DepthPathError(f"{name} must be finite")
    return result


def _nonnegative(value: object, name: str) -> float:
    result = _real(value, name)
    if result < 0.0:
        raise DepthPathError(f"{name} must be non-negative")
    return result


def _positive_int(value: object, name: str) -> int:
    if (
        isinstance(value, bool)
        or not isinstance(value, Integral)
        or int(value) <= 0
    ):
        raise DepthPathError(f"{name} must be a positive integer")
    return int(value)


def _sha256_payload(payload: object) -> str:
    encoded = json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
        allow_nan=False,
    ).encode("ascii")
    return f"sha256:{hashlib.sha256(encoded).hexdigest()}"


def _matrix(
    values: Sequence[Sequence[object]],
    name: str,
    *,
    rows: int,
    columns: int,
) -> tuple[tuple[float, ...], ...]:
    if isinstance(values, (str, bytes)):
        raise DepthPathError(f"{name} must be a numeric matrix")
    result = tuple(
        tuple(_real(value, f"{name}[{row_index}]") for value in row)
        for row_index, row in enumerate(values)
    )
    if len(result) != rows or any(len(row) != columns for row in result):
        raise DepthPathError(
            f"{name} must have shape ({rows}, {columns})"
        )
    return result


def _vector(
    values: Sequence[object],
    name: str,
    *,
    length: int,
) -> tuple[float, ...]:
    if isinstance(values, (str, bytes)):
        raise DepthPathError(f"{name} must be a numeric vector")
    result = tuple(_real(value, name) for value in values)
    if len(result) != length:
        raise DepthPathError(f"{name} must have length {length}")
    return result


def _assert_sealed(payload: object, seal: str, *, name: str) -> None:
    if _sha256_payload(payload) != seal:
        raise DepthPathError(f"{name} identity drifted after construction")


def _clone_sky_support(value: SkySupport) -> SkySupport:
    if type(value) is not SkySupport:
        raise TypeError("sky_support must be an exact SkySupport")
    return SkySupport(
        selection_mode=value.selection_mode,
        sky_support_hash=value.sky_support_hash,
        mask_hash=value.mask_hash,
        mock_coverage_status=value.mock_coverage_status,
        scan_volume_hash=value.scan_volume_hash,
        coordinate_frame=value.coordinate_frame,
        sky_fraction=value.sky_fraction,
        completeness_status=value.completeness_status,
        pixelization=value.pixelization,
        nside=value.nside,
    )


@dataclass(frozen=True)
class MaskStratum:
    stratum_id: str
    depth_coordinate: float
    depth_unit: str
    support_unit_ids: tuple[str, ...]
    support_universe_size: int
    sky_support: SkySupport
    selection_id: str
    covariance_id: str
    source_artifact_id: str
    feature_names: tuple[str, ...]
    feature_unit: str
    assumptions: tuple[str, ...]
    _construction_token: InitVar[object] = None
    _identity_seal: str = field(init=False, repr=False, compare=False)

    def __post_init__(self, _construction_token: object) -> None:
        if _construction_token is not _STRATUM_TOKEN:
            raise DepthPathError("MaskStratum must be factory-built")
        for name in (
            "stratum_id",
            "depth_unit",
            "selection_id",
            "covariance_id",
            "source_artifact_id",
            "feature_unit",
        ):
            _text(getattr(self, name), name)
        depth = _nonnegative(self.depth_coordinate, "depth_coordinate")
        support_ids = tuple(
            sorted(_texts(self.support_unit_ids, "support_unit_ids"))
        )
        universe_size = _positive_int(
            self.support_universe_size,
            "support_universe_size",
        )
        if len(support_ids) > universe_size:
            raise DepthPathError(
                "support_unit_ids cannot exceed support_universe_size"
            )
        support = _clone_sky_support(self.sky_support)
        if not support.mask_hash.startswith("sha256:"):
            raise DepthPathError("sky_support.mask_hash must be a sha256 identity")
        if not support.sky_support_hash.startswith("sha256:"):
            raise DepthPathError(
                "sky_support.sky_support_hash must be a sha256 identity"
            )
        if support.sky_fraction is None:
            raise DepthPathError("sky_support.sky_fraction is required")
        exact_fraction = len(support_ids) / universe_size
        if not math.isclose(
            support.sky_fraction,
            exact_fraction,
            rel_tol=0.0,
            abs_tol=1e-12,
        ):
            raise DepthPathError(
                "sky_support.sky_fraction must match the exact support units"
            )
        feature_names = _texts(self.feature_names, "feature_names")
        assumptions = _texts(self.assumptions, "assumptions")
        object.__setattr__(self, "depth_coordinate", depth)
        object.__setattr__(self, "support_unit_ids", support_ids)
        object.__setattr__(self, "support_universe_size", universe_size)
        object.__setattr__(self, "sky_support", support)
        object.__setattr__(self, "feature_names", feature_names)
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
            "covariance_id": self.covariance_id,
            "depth_coordinate_hex": self.depth_coordinate.hex(),
            "depth_unit": self.depth_unit,
            "feature_names": list(self.feature_names),
            "feature_unit": self.feature_unit,
            "schema": "HTT_MASK_STRATUM_V1",
            "selection_id": self.selection_id,
            "sky_support": self.sky_support.to_metadata(),
            "source_artifact_id": self.source_artifact_id,
            "stratum_id": self.stratum_id,
            "support_unit_ids": list(self.support_unit_ids),
            "support_universe_size": self.support_universe_size,
        }

    def _assert_identity_sealed(self) -> None:
        _assert_sealed(
            self._payload_unchecked(),
            self._identity_seal,
            name="mask stratum",
        )

    def as_payload(self) -> dict[str, object]:
        self._assert_identity_sealed()
        return {**self._payload_unchecked(), "content_id": self._identity_seal}


def build_mask_stratum(
    *,
    stratum_id: str,
    depth_coordinate: object,
    depth_unit: str,
    support_unit_ids: Sequence[str],
    support_universe_size: int,
    sky_support: SkySupport,
    selection_id: str,
    covariance_id: str,
    source_artifact_id: str,
    feature_names: Sequence[str],
    feature_unit: str,
    assumptions: Sequence[str],
) -> MaskStratum:
    return MaskStratum(
        stratum_id=stratum_id,
        depth_coordinate=_nonnegative(depth_coordinate, "depth_coordinate"),
        depth_unit=depth_unit,
        support_unit_ids=tuple(support_unit_ids),
        support_universe_size=support_universe_size,
        sky_support=_clone_sky_support(sky_support),
        selection_id=selection_id,
        covariance_id=covariance_id,
        source_artifact_id=source_artifact_id,
        feature_names=tuple(feature_names),
        feature_unit=feature_unit,
        assumptions=tuple(assumptions),
        _construction_token=_STRATUM_TOKEN,
    )


@dataclass(frozen=True)
class TransportKernel:
    transport_id: str
    source_stratum_id: str
    source_stratum_content_id: str
    target_stratum_id: str
    target_stratum_content_id: str
    source_feature_names: tuple[str, ...]
    target_feature_names: tuple[str, ...]
    matrix: tuple[tuple[float, ...], ...]
    mask_transport_id: str
    selection_transport_id: str
    covariance_transport_id: str
    method_id: str
    component_transport_ids: tuple[str, ...]
    assumptions: tuple[str, ...]
    _construction_token: InitVar[object] = None
    _identity_seal: str = field(init=False, repr=False, compare=False)

    def __post_init__(self, _construction_token: object) -> None:
        if _construction_token is not _KERNEL_TOKEN:
            raise DepthPathError("TransportKernel must be factory-built")
        for name in (
            "transport_id",
            "source_stratum_id",
            "source_stratum_content_id",
            "target_stratum_id",
            "target_stratum_content_id",
            "mask_transport_id",
            "selection_transport_id",
            "covariance_transport_id",
            "method_id",
        ):
            _text(getattr(self, name), name)
        source_names = _texts(
            self.source_feature_names,
            "source_feature_names",
        )
        target_names = _texts(
            self.target_feature_names,
            "target_feature_names",
        )
        matrix = _matrix(
            self.matrix,
            "matrix",
            rows=len(target_names),
            columns=len(source_names),
        )
        component_ids = _texts(
            self.component_transport_ids,
            "component_transport_ids",
            minimum=0,
        )
        assumptions = _texts(self.assumptions, "assumptions")
        object.__setattr__(self, "source_feature_names", source_names)
        object.__setattr__(self, "target_feature_names", target_names)
        object.__setattr__(self, "matrix", matrix)
        object.__setattr__(self, "component_transport_ids", component_ids)
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
            "component_transport_ids": list(self.component_transport_ids),
            "covariance_transport_id": self.covariance_transport_id,
            "mask_transport_id": self.mask_transport_id,
            "matrix_hex": [
                [value.hex() for value in row] for row in self.matrix
            ],
            "method_id": self.method_id,
            "schema": "HTT_TRANSPORT_KERNEL_V1",
            "selection_transport_id": self.selection_transport_id,
            "source_feature_names": list(self.source_feature_names),
            "source_stratum_content_id": self.source_stratum_content_id,
            "source_stratum_id": self.source_stratum_id,
            "target_feature_names": list(self.target_feature_names),
            "target_stratum_content_id": self.target_stratum_content_id,
            "target_stratum_id": self.target_stratum_id,
            "transport_id": self.transport_id,
        }

    def _assert_identity_sealed(self) -> None:
        _assert_sealed(
            self._payload_unchecked(),
            self._identity_seal,
            name="transport kernel",
        )

    def as_payload(self) -> dict[str, object]:
        self._assert_identity_sealed()
        return {**self._payload_unchecked(), "content_id": self._identity_seal}


def build_transport_kernel(
    *,
    transport_id: str,
    source: MaskStratum,
    target: MaskStratum,
    matrix: Sequence[Sequence[object]],
    mask_transport_id: str,
    selection_transport_id: str,
    covariance_transport_id: str,
    method_id: str,
    assumptions: Sequence[str],
) -> TransportKernel:
    if type(source) is not MaskStratum or type(target) is not MaskStratum:
        raise TypeError("source and target must be exact MaskStratum objects")
    source.as_payload()
    target.as_payload()
    return TransportKernel(
        transport_id=transport_id,
        source_stratum_id=source.stratum_id,
        source_stratum_content_id=source.content_id,
        target_stratum_id=target.stratum_id,
        target_stratum_content_id=target.content_id,
        source_feature_names=source.feature_names,
        target_feature_names=target.feature_names,
        matrix=_matrix(
            matrix,
            "matrix",
            rows=len(target.feature_names),
            columns=len(source.feature_names),
        ),
        mask_transport_id=mask_transport_id,
        selection_transport_id=selection_transport_id,
        covariance_transport_id=covariance_transport_id,
        method_id=method_id,
        component_transport_ids=(),
        assumptions=tuple(assumptions),
        _construction_token=_KERNEL_TOKEN,
    )


def apply_transport(
    kernel: TransportKernel,
    values: Sequence[object],
) -> tuple[float, ...]:
    if type(kernel) is not TransportKernel:
        raise TypeError("kernel must be an exact TransportKernel")
    kernel.as_payload()
    vector = np.asarray(
        _vector(
            values,
            "values",
            length=len(kernel.source_feature_names),
        ),
        dtype=float,
    )
    return tuple(np.asarray(kernel.matrix, dtype=float) @ vector)


def apply_covariance_transport(
    kernel: TransportKernel,
    covariance: Sequence[Sequence[object]],
) -> tuple[tuple[float, ...], ...]:
    if type(kernel) is not TransportKernel:
        raise TypeError("kernel must be an exact TransportKernel")
    kernel.as_payload()
    width = len(kernel.source_feature_names)
    source_covariance = np.asarray(
        _matrix(covariance, "covariance", rows=width, columns=width),
        dtype=float,
    )
    matrix = np.asarray(kernel.matrix, dtype=float)
    result = matrix @ source_covariance @ matrix.T
    return tuple(tuple(float(value) for value in row) for row in result)


def compose_transport_kernels(
    *,
    transport_id: str,
    first: TransportKernel,
    second: TransportKernel,
    method_id: str,
    assumptions: Sequence[str],
) -> TransportKernel:
    if type(first) is not TransportKernel or type(second) is not TransportKernel:
        raise TypeError("first and second must be exact TransportKernel objects")
    first.as_payload()
    second.as_payload()
    if (
        first.target_stratum_id != second.source_stratum_id
        or first.target_stratum_content_id
        != second.source_stratum_content_id
        or first.target_feature_names != second.source_feature_names
    ):
        raise DepthPathError(
            "transport composition requires one exact shared middle stratum"
        )
    matrix = (
        np.asarray(second.matrix, dtype=float)
        @ np.asarray(first.matrix, dtype=float)
    )
    return TransportKernel(
        transport_id=transport_id,
        source_stratum_id=first.source_stratum_id,
        source_stratum_content_id=first.source_stratum_content_id,
        target_stratum_id=second.target_stratum_id,
        target_stratum_content_id=second.target_stratum_content_id,
        source_feature_names=first.source_feature_names,
        target_feature_names=second.target_feature_names,
        matrix=tuple(tuple(float(value) for value in row) for row in matrix),
        mask_transport_id=_sha256_payload(
            [first.mask_transport_id, second.mask_transport_id]
        ),
        selection_transport_id=_sha256_payload(
            [first.selection_transport_id, second.selection_transport_id]
        ),
        covariance_transport_id=_sha256_payload(
            [first.covariance_transport_id, second.covariance_transport_id]
        ),
        method_id=method_id,
        component_transport_ids=(first.content_id, second.content_id),
        assumptions=tuple(assumptions),
        _construction_token=_KERNEL_TOKEN,
    )


@dataclass(frozen=True)
class DepthPath:
    path_id: str
    strata: tuple[MaskStratum, ...]
    kernels: tuple[TransportKernel, ...]
    nesting_rule: str = DEPTH_PATH_NESTING_RULE
    claim_ceiling: str = DEPTH_PATH_CLAIM_CEILING
    allowed_use: tuple[str, ...] = DEPTH_PATH_ALLOWED_USE
    forbidden_use: tuple[str, ...] = DEPTH_PATH_FORBIDDEN_USE
    _construction_token: InitVar[object] = None
    _identity_seal: str = field(init=False, repr=False, compare=False)

    def __post_init__(self, _construction_token: object) -> None:
        if _construction_token is not _PATH_TOKEN:
            raise DepthPathError("DepthPath must be factory-built")
        _text(self.path_id, "path_id")
        strata = tuple(self.strata)
        kernels = tuple(self.kernels)
        if len(strata) < 2:
            raise DepthPathError("a depth path requires at least two strata")
        if any(type(value) is not MaskStratum for value in strata):
            raise TypeError("strata must contain exact MaskStratum objects")
        for stratum in strata:
            stratum.as_payload()
        if len({value.stratum_id for value in strata}) != len(strata):
            raise DepthPathError("stratum ids must be unique")
        if any(
            left.depth_coordinate >= right.depth_coordinate
            for left, right in zip(strata[:-1], strata[1:], strict=True)
        ):
            raise DepthPathError(
                "depth coordinates must be strictly increasing"
            )
        first = strata[0]
        for stratum in strata[1:]:
            if (
                stratum.depth_unit != first.depth_unit
                or stratum.feature_unit != first.feature_unit
                or stratum.sky_support.coordinate_frame
                != first.sky_support.coordinate_frame
                or stratum.sky_support.pixelization
                != first.sky_support.pixelization
                or stratum.sky_support.nside != first.sky_support.nside
                or stratum.support_universe_size
                != first.support_universe_size
            ):
                raise DepthPathError(
                    "all path strata must share depth/feature units and one "
                    "sky coordinate/pixel universe"
                )
        for source, target in zip(strata[:-1], strata[1:], strict=True):
            if not set(target.support_unit_ids).issubset(
                source.support_unit_ids
            ):
                raise DepthPathError(
                    "non-nested sky supports cannot enter one depth path"
                )
        if (
            len(kernels) != len(strata) - 1
            or any(type(value) is not TransportKernel for value in kernels)
        ):
            raise DepthPathError(
                "one exact transport kernel is required per path edge"
            )
        for source, target, kernel in zip(
            strata[:-1],
            strata[1:],
            kernels,
            strict=True,
        ):
            kernel.as_payload()
            if (
                kernel.source_stratum_id != source.stratum_id
                or kernel.source_stratum_content_id != source.content_id
                or kernel.target_stratum_id != target.stratum_id
                or kernel.target_stratum_content_id != target.content_id
                or kernel.source_feature_names != source.feature_names
                or kernel.target_feature_names != target.feature_names
            ):
                raise DepthPathError(
                    "transport kernel is not bound to its exact adjacent strata"
                )
        if self.nesting_rule != DEPTH_PATH_NESTING_RULE:
            raise DepthPathError("nesting rule drifted")
        if self.claim_ceiling != DEPTH_PATH_CLAIM_CEILING:
            raise DepthPathError("claim ceiling drifted")
        if tuple(self.allowed_use) != DEPTH_PATH_ALLOWED_USE:
            raise DepthPathError("allowed-use lane drifted")
        if tuple(self.forbidden_use) != DEPTH_PATH_FORBIDDEN_USE:
            raise DepthPathError("forbidden-use lane drifted")
        object.__setattr__(self, "strata", strata)
        object.__setattr__(self, "kernels", kernels)
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
            "claim_ceiling": self.claim_ceiling,
            "forbidden_use": list(self.forbidden_use),
            "kernels": [value.as_payload() for value in self.kernels],
            "nesting_rule": self.nesting_rule,
            "path_id": self.path_id,
            "schema": "HTT_DEPTH_PATH_V1",
            "strata": [value.as_payload() for value in self.strata],
        }

    def _assert_identity_sealed(self) -> None:
        _assert_sealed(
            self._payload_unchecked(),
            self._identity_seal,
            name="depth path",
        )

    def as_payload(self) -> dict[str, object]:
        for stratum in self.strata:
            stratum.as_payload()
        for kernel in self.kernels:
            kernel.as_payload()
        self._assert_identity_sealed()
        return {**self._payload_unchecked(), "content_id": self._identity_seal}


def build_depth_path(
    *,
    path_id: str,
    strata: Sequence[MaskStratum],
    kernels: Sequence[TransportKernel],
) -> DepthPath:
    return DepthPath(
        path_id=path_id,
        strata=tuple(strata),
        kernels=tuple(kernels),
        _construction_token=_PATH_TOKEN,
    )


def revalidate_depth_path(path: DepthPath) -> DepthPath:
    if type(path) is not DepthPath:
        raise TypeError("path must be an exact DepthPath")
    path.as_payload()
    return build_depth_path(
        path_id=path.path_id,
        strata=path.strata,
        kernels=path.kernels,
    )


@dataclass(frozen=True)
class ObservableFeatureStep:
    step_id: str
    stratum_id: str
    stratum_content_id: str
    feature_names: tuple[str, ...]
    feature_unit: str
    values: tuple[float, ...]
    covariance: tuple[tuple[float, ...], ...]
    source_artifact_id: str
    extraction_method_id: str
    sample_count: int
    owner: str = "OBSSTAT"
    _construction_token: InitVar[object] = None
    _identity_seal: str = field(init=False, repr=False, compare=False)

    def __post_init__(self, _construction_token: object) -> None:
        if _construction_token is not _STEP_TOKEN:
            raise DepthPathError("ObservableFeatureStep must be factory-built")
        for name in (
            "step_id",
            "stratum_id",
            "stratum_content_id",
            "feature_unit",
            "source_artifact_id",
            "extraction_method_id",
        ):
            _text(getattr(self, name), name)
        feature_names = _texts(self.feature_names, "feature_names")
        dimension = len(feature_names)
        values = _vector(self.values, "values", length=dimension)
        covariance = _matrix(
            self.covariance,
            "covariance",
            rows=dimension,
            columns=dimension,
        )
        covariance_array = np.asarray(covariance, dtype=float)
        if not np.allclose(
            covariance_array,
            covariance_array.T,
            rtol=0.0,
            atol=1e-12,
        ):
            raise DepthPathError("covariance must be symmetric")
        if np.linalg.eigvalsh(covariance_array).min() < -1e-12:
            raise DepthPathError("covariance must be positive semidefinite")
        sample_count = _positive_int(self.sample_count, "sample_count")
        if self.owner != "OBSSTAT":
            raise DepthPathError("feature-step owner must remain OBSSTAT")
        object.__setattr__(self, "feature_names", feature_names)
        object.__setattr__(self, "values", values)
        object.__setattr__(self, "covariance", covariance)
        object.__setattr__(self, "sample_count", sample_count)
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
            "covariance_hex": [
                [value.hex() for value in row] for row in self.covariance
            ],
            "extraction_method_id": self.extraction_method_id,
            "feature_names": list(self.feature_names),
            "feature_unit": self.feature_unit,
            "owner": self.owner,
            "sample_count": self.sample_count,
            "schema": "HTT_OBSERVABLE_FEATURE_STEP_V1",
            "source_artifact_id": self.source_artifact_id,
            "step_id": self.step_id,
            "stratum_content_id": self.stratum_content_id,
            "stratum_id": self.stratum_id,
            "values_hex": [value.hex() for value in self.values],
        }

    def _assert_identity_sealed(self) -> None:
        _assert_sealed(
            self._payload_unchecked(),
            self._identity_seal,
            name="observable feature step",
        )

    def as_payload(self) -> dict[str, object]:
        self._assert_identity_sealed()
        return {**self._payload_unchecked(), "content_id": self._identity_seal}


def build_observable_feature_step(
    *,
    step_id: str,
    stratum: MaskStratum,
    values: Sequence[object],
    covariance: Sequence[Sequence[object]],
    source_artifact_id: str,
    extraction_method_id: str,
    sample_count: int,
) -> ObservableFeatureStep:
    if type(stratum) is not MaskStratum:
        raise TypeError("stratum must be an exact MaskStratum")
    stratum.as_payload()
    return ObservableFeatureStep(
        step_id=step_id,
        stratum_id=stratum.stratum_id,
        stratum_content_id=stratum.content_id,
        feature_names=stratum.feature_names,
        feature_unit=stratum.feature_unit,
        values=tuple(values),  # type: ignore[arg-type]
        covariance=tuple(tuple(row) for row in covariance),  # type: ignore[arg-type]
        source_artifact_id=source_artifact_id,
        extraction_method_id=extraction_method_id,
        sample_count=sample_count,
        _construction_token=_STEP_TOKEN,
    )


def _validate_steps(
    path: DepthPath,
    steps: Sequence[ObservableFeatureStep],
) -> tuple[ObservableFeatureStep, ...]:
    if type(path) is not DepthPath:
        raise TypeError("path must be an exact DepthPath")
    path.as_payload()
    resolved = tuple(steps)
    if (
        len(resolved) != len(path.strata)
        or any(type(value) is not ObservableFeatureStep for value in resolved)
    ):
        raise DepthPathError("one exact ObservableFeatureStep is required per stratum")
    for stratum, step in zip(path.strata, resolved, strict=True):
        step.as_payload()
        if (
            step.stratum_id != stratum.stratum_id
            or step.stratum_content_id != stratum.content_id
            or step.feature_names != stratum.feature_names
            or step.feature_unit != stratum.feature_unit
        ):
            raise DepthPathError(
                "feature step is not bound to its exact path stratum"
            )
    return resolved


@dataclass(frozen=True)
class DepthCoherenceCell:
    edge_id: str
    source_stratum_id: str
    target_stratum_id: str
    residual: tuple[float, ...]
    joint_covariance: tuple[tuple[float, ...], ...]
    mahalanobis_sq: float | None
    normalized_score: float | None
    degrees_of_freedom: int
    status: CoherenceCellStatus
    _construction_token: InitVar[object] = None
    _identity_seal: str = field(init=False, repr=False, compare=False)

    def __post_init__(self, _construction_token: object) -> None:
        if _construction_token is not _CELL_TOKEN:
            raise DepthPathError("DepthCoherenceCell must be factory-built")
        for name in ("edge_id", "source_stratum_id", "target_stratum_id"):
            _text(getattr(self, name), name)
        dof = _positive_int(self.degrees_of_freedom, "degrees_of_freedom")
        residual = _vector(self.residual, "residual", length=dof)
        covariance = _matrix(
            self.joint_covariance,
            "joint_covariance",
            rows=dof,
            columns=dof,
        )
        if type(self.status) is not CoherenceCellStatus:
            raise DepthPathError("status must use CoherenceCellStatus")
        if self.status is CoherenceCellStatus.DEFINED:
            if self.mahalanobis_sq is None or self.normalized_score is None:
                raise DepthPathError("defined cells require both scores")
            mahalanobis = _nonnegative(
                self.mahalanobis_sq,
                "mahalanobis_sq",
            )
            normalized = _nonnegative(
                self.normalized_score,
                "normalized_score",
            )
            if not math.isclose(
                normalized,
                mahalanobis / dof,
                rel_tol=1e-12,
                abs_tol=1e-12,
            ):
                raise DepthPathError("normalized score must equal chi-square / dof")
            object.__setattr__(self, "mahalanobis_sq", mahalanobis)
            object.__setattr__(self, "normalized_score", normalized)
        elif self.mahalanobis_sq is not None or self.normalized_score is not None:
            raise DepthPathError("rank-deficient cells must not carry scores")
        object.__setattr__(self, "degrees_of_freedom", dof)
        object.__setattr__(self, "residual", residual)
        object.__setattr__(self, "joint_covariance", covariance)
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
            "degrees_of_freedom": self.degrees_of_freedom,
            "edge_id": self.edge_id,
            "joint_covariance_hex": [
                [value.hex() for value in row]
                for row in self.joint_covariance
            ],
            "mahalanobis_sq_hex": (
                None
                if self.mahalanobis_sq is None
                else self.mahalanobis_sq.hex()
            ),
            "normalized_score_hex": (
                None
                if self.normalized_score is None
                else self.normalized_score.hex()
            ),
            "residual_hex": [value.hex() for value in self.residual],
            "schema": "HTT_DEPTH_COHERENCE_CELL_V1",
            "source_stratum_id": self.source_stratum_id,
            "status": self.status.value,
            "target_stratum_id": self.target_stratum_id,
        }

    def _assert_identity_sealed(self) -> None:
        _assert_sealed(
            self._payload_unchecked(),
            self._identity_seal,
            name="depth coherence cell",
        )

    def as_payload(self) -> dict[str, object]:
        self._assert_identity_sealed()
        return {**self._payload_unchecked(), "content_id": self._identity_seal}


@dataclass(frozen=True)
class DepthCoherenceReport:
    report_id: str
    path_content_id: str
    step_content_ids: tuple[str, ...]
    cells: tuple[DepthCoherenceCell, ...]
    status: DepthCoherenceStatus
    mean_normalized_score: float | None
    owner: str = "MIO"
    claim_ceiling: str = DEPTH_PATH_CLAIM_CEILING
    allowed_use: tuple[str, ...] = DEPTH_PATH_ALLOWED_USE
    forbidden_use: tuple[str, ...] = DEPTH_PATH_FORBIDDEN_USE
    _construction_token: InitVar[object] = None
    _identity_seal: str = field(init=False, repr=False, compare=False)

    def __post_init__(self, _construction_token: object) -> None:
        if _construction_token is not _REPORT_TOKEN:
            raise DepthPathError("DepthCoherenceReport must be factory-built")
        _text(self.report_id, "report_id")
        _text(self.path_content_id, "path_content_id")
        step_ids = _texts(self.step_content_ids, "step_content_ids")
        cells = tuple(self.cells)
        if not cells or any(type(value) is not DepthCoherenceCell for value in cells):
            raise DepthPathError("cells must contain exact DepthCoherenceCell objects")
        for cell in cells:
            cell.as_payload()
        if type(self.status) is not DepthCoherenceStatus:
            raise DepthPathError("status must use DepthCoherenceStatus")
        defined = tuple(
            value.normalized_score
            for value in cells
            if value.status is CoherenceCellStatus.DEFINED
        )
        expected_status = (
            DepthCoherenceStatus.UNAVAILABLE
            if not defined
            else (
                DepthCoherenceStatus.DEFINED
                if len(defined) == len(cells)
                else DepthCoherenceStatus.PARTIAL
            )
        )
        if self.status is not expected_status:
            raise DepthPathError("report status does not match cell availability")
        if defined:
            mean = _nonnegative(
                self.mean_normalized_score,
                "mean_normalized_score",
            )
            if not math.isclose(
                mean,
                sum(defined) / len(defined),
                rel_tol=1e-12,
                abs_tol=1e-12,
            ):
                raise DepthPathError("mean score does not match defined cells")
            object.__setattr__(self, "mean_normalized_score", mean)
        elif self.mean_normalized_score is not None:
            raise DepthPathError("unavailable report must not carry a mean score")
        if self.owner != "MIO":
            raise DepthPathError("coherence owner must remain MIO")
        if self.claim_ceiling != DEPTH_PATH_CLAIM_CEILING:
            raise DepthPathError("claim ceiling drifted")
        if tuple(self.allowed_use) != DEPTH_PATH_ALLOWED_USE:
            raise DepthPathError("allowed-use lane drifted")
        if tuple(self.forbidden_use) != DEPTH_PATH_FORBIDDEN_USE:
            raise DepthPathError("forbidden-use lane drifted")
        object.__setattr__(self, "step_content_ids", step_ids)
        object.__setattr__(self, "cells", cells)
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
            "cells": [value.as_payload() for value in self.cells],
            "claim_ceiling": self.claim_ceiling,
            "forbidden_use": list(self.forbidden_use),
            "mean_normalized_score_hex": (
                None
                if self.mean_normalized_score is None
                else self.mean_normalized_score.hex()
            ),
            "owner": self.owner,
            "path_content_id": self.path_content_id,
            "report_id": self.report_id,
            "schema": "HTT_DEPTH_COHERENCE_REPORT_V1",
            "status": self.status.value,
            "step_content_ids": list(self.step_content_ids),
        }

    def _assert_identity_sealed(self) -> None:
        _assert_sealed(
            self._payload_unchecked(),
            self._identity_seal,
            name="depth coherence report",
        )

    def as_payload(self) -> dict[str, object]:
        for cell in self.cells:
            cell.as_payload()
        self._assert_identity_sealed()
        return {**self._payload_unchecked(), "content_id": self._identity_seal}


def build_depth_coherence_report(
    *,
    report_id: str,
    path: DepthPath,
    steps: Sequence[ObservableFeatureStep],
    rank_tolerance: object = 1e-12,
) -> DepthCoherenceReport:
    resolved_steps = _validate_steps(path, steps)
    tolerance = _nonnegative(rank_tolerance, "rank_tolerance")
    cells: list[DepthCoherenceCell] = []
    for source, target, kernel in zip(
        resolved_steps[:-1],
        resolved_steps[1:],
        path.kernels,
        strict=True,
    ):
        expected = np.asarray(
            apply_transport(kernel, source.values),
            dtype=float,
        )
        residual = np.asarray(target.values, dtype=float) - expected
        transported_covariance = np.asarray(
            apply_covariance_transport(kernel, source.covariance),
            dtype=float,
        )
        joint_covariance = (
            np.asarray(target.covariance, dtype=float)
            + transported_covariance
        )
        eigenvalues = np.linalg.eigvalsh(joint_covariance)
        scale = max(
            float(np.max(np.abs(eigenvalues))),
            float(np.finfo(float).tiny),
        )
        rank = int(np.sum(eigenvalues > tolerance * scale))
        if rank < residual.size:
            status = CoherenceCellStatus.COVARIANCE_RANK_DEFICIENT
            mahalanobis = None
            normalized = None
        else:
            status = CoherenceCellStatus.DEFINED
            mahalanobis = max(
                0.0,
                float(
                    residual
                    @ np.linalg.solve(joint_covariance, residual)
                ),
            )
            normalized = mahalanobis / residual.size
        cells.append(
            DepthCoherenceCell(
                edge_id=kernel.content_id,
                source_stratum_id=source.stratum_id,
                target_stratum_id=target.stratum_id,
                residual=tuple(float(value) for value in residual),
                joint_covariance=tuple(
                    tuple(float(value) for value in row)
                    for row in joint_covariance
                ),
                mahalanobis_sq=mahalanobis,
                normalized_score=normalized,
                degrees_of_freedom=residual.size,
                status=status,
                _construction_token=_CELL_TOKEN,
            )
        )
    defined = tuple(
        value.normalized_score
        for value in cells
        if value.status is CoherenceCellStatus.DEFINED
    )
    status = (
        DepthCoherenceStatus.UNAVAILABLE
        if not defined
        else (
            DepthCoherenceStatus.DEFINED
            if len(defined) == len(cells)
            else DepthCoherenceStatus.PARTIAL
        )
    )
    return DepthCoherenceReport(
        report_id=report_id,
        path_content_id=path.content_id,
        step_content_ids=tuple(value.content_id for value in resolved_steps),
        cells=tuple(cells),
        status=status,
        mean_normalized_score=(
            None if not defined else sum(defined) / len(defined)
        ),
        _construction_token=_REPORT_TOKEN,
    )


@dataclass(frozen=True)
class DepthScrambleControl:
    control_id: str
    path_content_id: str
    baseline_report_id: str
    scrambled_report_id: str
    permutation: tuple[int, ...]
    baseline_score: float | None
    scrambled_score: float | None
    score_degradation: float | None
    minimum_degradation: float
    status: ScrambleControlStatus
    owner: str = "MIO"
    _construction_token: InitVar[object] = None
    _identity_seal: str = field(init=False, repr=False, compare=False)

    def __post_init__(self, _construction_token: object) -> None:
        if _construction_token is not _SCRAMBLE_TOKEN:
            raise DepthPathError("DepthScrambleControl must be factory-built")
        for name in (
            "control_id",
            "path_content_id",
            "baseline_report_id",
            "scrambled_report_id",
        ):
            _text(getattr(self, name), name)
        permutation = tuple(self.permutation)
        if (
            any(
                isinstance(value, bool) or not isinstance(value, Integral)
                for value in permutation
            )
            or sorted(int(value) for value in permutation)
            != list(range(len(permutation)))
            or all(int(value) == index for index, value in enumerate(permutation))
        ):
            raise DepthPathError("permutation must be a non-identity permutation")
        minimum = _nonnegative(
            self.minimum_degradation,
            "minimum_degradation",
        )
        if type(self.status) is not ScrambleControlStatus:
            raise DepthPathError("status must use ScrambleControlStatus")
        scores = (
            self.baseline_score,
            self.scrambled_score,
            self.score_degradation,
        )
        if self.status is ScrambleControlStatus.INCONCLUSIVE:
            if any(value is not None for value in scores):
                raise DepthPathError("inconclusive control must not carry scores")
        else:
            if any(value is None for value in scores):
                raise DepthPathError("evaluated control requires all scores")
            baseline = _nonnegative(self.baseline_score, "baseline_score")
            scrambled = _nonnegative(self.scrambled_score, "scrambled_score")
            degradation = _real(
                self.score_degradation,
                "score_degradation",
            )
            if not math.isclose(
                degradation,
                scrambled - baseline,
                rel_tol=1e-12,
                abs_tol=1e-12,
            ):
                raise DepthPathError("score_degradation must be scrambled - baseline")
            expected = (
                ScrambleControlStatus.PASSED
                if degradation >= minimum
                else ScrambleControlStatus.FAILED
            )
            if self.status is not expected:
                raise DepthPathError("scramble status does not match degradation")
            object.__setattr__(self, "baseline_score", baseline)
            object.__setattr__(self, "scrambled_score", scrambled)
            object.__setattr__(self, "score_degradation", degradation)
        if self.owner != "MIO":
            raise DepthPathError("scramble-control owner must remain MIO")
        object.__setattr__(
            self,
            "permutation",
            tuple(int(value) for value in permutation),
        )
        object.__setattr__(self, "minimum_degradation", minimum)
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
            "baseline_report_id": self.baseline_report_id,
            "baseline_score_hex": (
                None if self.baseline_score is None else self.baseline_score.hex()
            ),
            "control_id": self.control_id,
            "minimum_degradation_hex": self.minimum_degradation.hex(),
            "owner": self.owner,
            "path_content_id": self.path_content_id,
            "permutation": list(self.permutation),
            "schema": "HTT_DEPTH_SCRAMBLE_CONTROL_V1",
            "score_degradation_hex": (
                None
                if self.score_degradation is None
                else self.score_degradation.hex()
            ),
            "scrambled_report_id": self.scrambled_report_id,
            "scrambled_score_hex": (
                None
                if self.scrambled_score is None
                else self.scrambled_score.hex()
            ),
            "status": self.status.value,
        }

    def _assert_identity_sealed(self) -> None:
        _assert_sealed(
            self._payload_unchecked(),
            self._identity_seal,
            name="depth scramble control",
        )

    def as_payload(self) -> dict[str, object]:
        self._assert_identity_sealed()
        return {**self._payload_unchecked(), "content_id": self._identity_seal}


def build_depth_scramble_control(
    *,
    control_id: str,
    path: DepthPath,
    steps: Sequence[ObservableFeatureStep],
    permutation: Sequence[int],
    minimum_degradation: object,
    rank_tolerance: object = 1e-12,
) -> DepthScrambleControl:
    resolved_steps = _validate_steps(path, steps)
    raw_permutation = tuple(permutation)
    if (
        any(
            isinstance(value, bool) or not isinstance(value, Integral)
            for value in raw_permutation
        )
        or len(raw_permutation) != len(resolved_steps)
    ):
        raise DepthPathError("permutation must be a non-identity permutation")
    resolved_permutation = tuple(int(value) for value in raw_permutation)
    if (
        sorted(resolved_permutation) != list(range(len(resolved_steps)))
        or all(
            value == index
            for index, value in enumerate(resolved_permutation)
        )
    ):
        raise DepthPathError("permutation must be a non-identity permutation")
    first = resolved_steps[0]
    if any(
        step.feature_names != first.feature_names
        or step.feature_unit != first.feature_unit
        for step in resolved_steps
    ):
        raise DepthPathError(
            "depth scramble requires one common feature layout and unit"
        )
    baseline = build_depth_coherence_report(
        report_id=f"{control_id}:baseline",
        path=path,
        steps=resolved_steps,
        rank_tolerance=rank_tolerance,
    )
    scrambled_steps = tuple(
        build_observable_feature_step(
            step_id=f"{control_id}:scrambled:{target.stratum_id}",
            stratum=target,
            values=resolved_steps[source_index].values,
            covariance=resolved_steps[source_index].covariance,
            source_artifact_id=(
                f"negative-control:{resolved_steps[source_index].content_id}"
            ),
            extraction_method_id="DEPTH_SCRAMBLE_NEGATIVE_CONTROL_V1",
            sample_count=resolved_steps[source_index].sample_count,
        )
        for target, source_index in zip(
            path.strata,
            resolved_permutation,
            strict=True,
        )
    )
    scrambled = build_depth_coherence_report(
        report_id=f"{control_id}:scrambled",
        path=path,
        steps=scrambled_steps,
        rank_tolerance=rank_tolerance,
    )
    minimum = _nonnegative(minimum_degradation, "minimum_degradation")
    if (
        baseline.mean_normalized_score is None
        or scrambled.mean_normalized_score is None
    ):
        degradation = None
        status = ScrambleControlStatus.INCONCLUSIVE
        baseline_score = None
        scrambled_score = None
    else:
        baseline_score = baseline.mean_normalized_score
        scrambled_score = scrambled.mean_normalized_score
        degradation = scrambled_score - baseline_score
        status = (
            ScrambleControlStatus.PASSED
            if degradation >= minimum
            else ScrambleControlStatus.FAILED
        )
    return DepthScrambleControl(
        control_id=control_id,
        path_content_id=path.content_id,
        baseline_report_id=baseline.content_id,
        scrambled_report_id=scrambled.content_id,
        permutation=resolved_permutation,
        baseline_score=baseline_score,
        scrambled_score=scrambled_score,
        score_degradation=degradation,
        minimum_degradation=minimum,
        status=status,
        _construction_token=_SCRAMBLE_TOKEN,
    )


__all__ = [
    "CoherenceCellStatus",
    "DEPTH_PATH_ALLOWED_USE",
    "DEPTH_PATH_CLAIM_CEILING",
    "DEPTH_PATH_FORBIDDEN_USE",
    "DEPTH_PATH_NESTING_RULE",
    "DepthCoherenceReport",
    "DepthCoherenceStatus",
    "DepthPath",
    "DepthPathError",
    "DepthScrambleControl",
    "MaskStratum",
    "ObservableFeatureStep",
    "ScrambleControlStatus",
    "TransportKernel",
    "apply_covariance_transport",
    "apply_transport",
    "build_depth_coherence_report",
    "build_depth_path",
    "build_depth_scramble_control",
    "build_mask_stratum",
    "build_observable_feature_step",
    "build_transport_kernel",
    "compose_transport_kernels",
    "revalidate_depth_path",
]
