"""Typed velocity-frame decomposition and local/global response geometry.

This module keeps two questions separate:

* whether three declared first-order velocities satisfy
  ``beta_RO = beta_RM + beta_MO + O(beta^2)``; and
* whether registered local-boost and global-tilt *hypothesis responses* span
  distinguishable tangent spaces on one covariance-supported quotient.

The closure relation is a kinematic consistency diagnostic, not a source
identifier.  Missing response providers are never represented by zero
columns.  The response result is diagnostic-only and pre-solver: it cannot
detect a global tilt, FLRW departure, geometry, or a Bianchi family.
"""

from __future__ import annotations

from dataclasses import InitVar, dataclass
from enum import Enum
import hashlib
import json
import math
from numbers import Real
from typing import Iterable, Sequence

import numpy as np

from common.anchor_geometry import (
    NormalizerAvailability,
    NormalizerPurpose,
    NormalizerSpec,
)
from common.anchored_response_geometry import (
    AnchoredResponseGeometryReport,
    AnchoredResponseStatus,
    anchored_numeric_content_id,
    measure_anchored_response_geometry,
)
from common.transfer_registry import TransferFunctionSpec, TransferSource


class VelocityFrameError(ValueError):
    """Raised when a velocity-frame or source-response contract is invalid."""


class _StringEnum(str, Enum):
    def __str__(self) -> str:
        return self.value


class VelocityDecompositionStatus(_StringEnum):
    CLOSURE_VERIFIED = "CLOSURE_VERIFIED"
    CLOSURE_MISMATCH = "CLOSURE_MISMATCH"
    SUM_ONLY = "SUM_ONLY"
    MISSING_COMPONENT = "MISSING_COMPONENT"


class SourceHypothesis(_StringEnum):
    LOCAL_BOOST = "LOCAL_BOOST"
    GLOBAL_TILT = "GLOBAL_TILT"


class VelocityComponent(_StringEnum):
    BETA_MO = "beta_MO"
    BETA_RM = "beta_RM"


class ResponseProviderKind(_StringEnum):
    ANALYTIC = "ANALYTIC"
    SYNTHETIC = "SYNTHETIC"
    EMPIRICAL_PROXY = "EMPIRICAL_PROXY"


class ResponseProviderAvailability(_StringEnum):
    AVAILABLE = "AVAILABLE"
    MISSING = "MISSING"


class SourceResponseGeometryStatus(_StringEnum):
    NON_IDENTIFIED = "NON_IDENTIFIED"
    SUM_ONLY = "SUM_ONLY"
    SEPARABLE_CANDIDATE = "SEPARABLE_CANDIDATE"
    MISSING_RESPONSE_PROVIDER = "MISSING_RESPONSE_PROVIDER"


_DECOMPOSITION_TOKEN = object()
_PROVIDER_TOKEN = object()
_GEOMETRY_TOKEN = object()
_RESPONSE_ROLE = "hypothesis_only"
_EXPECTED_COMPONENT = {
    SourceHypothesis.LOCAL_BOOST: VelocityComponent.BETA_MO,
    SourceHypothesis.GLOBAL_TILT: VelocityComponent.BETA_RM,
}
_DECOMPOSITION_ALLOWED_USE = (
    "first-order velocity-frame closure diagnostic",
    "explicit reporting of unresolved velocity components",
)
_DECOMPOSITION_FORBIDDEN_USE = (
    "global-tilt detection",
    "source attribution from closure",
    "reinterpretation of DepartureState.beta_a",
)
_GEOMETRY_ALLOWED_USE = (
    "pre-solver local/global tangent-space diagnostic",
    "synthetic hypothesis-response benchmark",
    "mandatory abstention and next-observable planning",
)
_GEOMETRY_FORBIDDEN_USE = (
    "observed global-tilt detection",
    "FLRW departure or geometry detection",
    "Bianchi family identification",
    "native-solver validation",
    "posterior odds, Bayes factor, e-value, or evidence",
)


def _text(value: object, name: str) -> str:
    if not isinstance(value, str) or not value.strip() or value != value.strip():
        raise VelocityFrameError(f"{name} must be non-empty trimmed text")
    return value


def _texts(
    values: Iterable[object],
    name: str,
    *,
    empty_ok: bool = False,
) -> tuple[str, ...]:
    if isinstance(values, (str, bytes)):
        raise VelocityFrameError(f"{name} must be a sequence")
    out = tuple(_text(value, name) for value in values)
    if not out and not empty_ok:
        raise VelocityFrameError(f"{name} must not be empty")
    if len(out) != len(set(out)):
        raise VelocityFrameError(f"{name} must not contain duplicates")
    return out


def _real(value: object, name: str) -> float:
    if isinstance(value, (bool, np.bool_)):
        raise VelocityFrameError(f"{name} must not be boolean")
    if isinstance(value, (complex, np.complexfloating)):
        raise VelocityFrameError(f"{name} must be real")
    if isinstance(value, (str, bytes, np.str_, np.bytes_)):
        raise VelocityFrameError(f"{name} must be numeric")
    if not isinstance(value, Real):
        raise VelocityFrameError(f"{name} must be a real number")
    out = float(value)
    if not math.isfinite(out):
        raise VelocityFrameError(f"{name} must be finite")
    return out


def _nonnegative(value: object, name: str) -> float:
    out = _real(value, name)
    if out < 0.0:
        raise VelocityFrameError(f"{name} must be non-negative")
    return out


def _vector(
    value: object,
    name: str,
    *,
    length: int = 3,
) -> np.ndarray:
    if _contains_invalid_scalar(value):
        raise VelocityFrameError(
            f"{name} must contain finite real values, not bool/text/complex"
        )
    try:
        out = np.asarray(value, dtype=float)
    except (TypeError, ValueError) as exc:
        raise VelocityFrameError(f"{name} must be numeric") from exc
    if out.shape != (length,):
        raise VelocityFrameError(
            f"{name} must have shape ({length},), got {out.shape}"
        )
    if not np.isfinite(out).all():
        raise VelocityFrameError(f"{name} must be finite")
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


def _matrix(
    value: object,
    name: str,
    *,
    shape: tuple[int, int] | None = None,
) -> np.ndarray:
    if _contains_invalid_scalar(value):
        raise VelocityFrameError(
            f"{name} must contain finite real values, not bool/text/complex"
        )
    try:
        out = np.asarray(value, dtype=float)
    except (TypeError, ValueError) as exc:
        raise VelocityFrameError(f"{name} must be numeric") from exc
    if out.ndim != 2:
        raise VelocityFrameError(f"{name} must be a matrix")
    if out.size == 0 or out.shape[0] == 0 or out.shape[1] == 0:
        raise VelocityFrameError(f"{name} must not be empty")
    if shape is not None and out.shape != shape:
        raise VelocityFrameError(
            f"{name} must have shape {shape}, got {out.shape}"
        )
    if not np.isfinite(out).all():
        raise VelocityFrameError(f"{name} must be finite")
    return out


def _matrix_tuple(value: np.ndarray) -> tuple[tuple[float, ...], ...]:
    return tuple(tuple(float(item) for item in row) for row in value)


def _vector_tuple(value: np.ndarray) -> tuple[float, ...]:
    return tuple(float(item) for item in value)


def _receipt(value: object, name: str) -> str:
    out = _text(value, name)
    digest = out[7:] if out.startswith("sha256:") else ""
    if len(digest) != 64 or any(ch not in "0123456789abcdef" for ch in digest):
        raise VelocityFrameError(
            f"{name} must be a lowercase sha256 receipt identity"
        )
    return out


def _semantic_receipt(payload: object) -> str:
    encoded = json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
        allow_nan=False,
    ).encode("ascii")
    return "sha256:" + hashlib.sha256(encoded).hexdigest()


def _transfer_source(value: object) -> TransferSource:
    try:
        source = (
            value
            if isinstance(value, TransferSource)
            else TransferSource(str(value))
        )
    except ValueError as exc:
        raise VelocityFrameError(
            "transfer_source must use the registered TransferSource vocabulary"
        ) from exc
    if source not in {TransferSource.NONE, TransferSource.EMPIRICAL_PROXY}:
        raise VelocityFrameError(
            "PR-256 permits only transfer_source none or empirical_proxy"
        )
    return source


def _validate_transfer_binding(
    *,
    provider_kind: ResponseProviderKind,
    transfer_id: object,
    transfer_source: object,
    transfer_spec: TransferFunctionSpec | None,
) -> tuple[str, TransferSource, TransferFunctionSpec | None]:
    source = _transfer_source(transfer_source)
    if source is TransferSource.NONE:
        transfer = _receipt(transfer_id, "transfer_id")
        if transfer_spec is not None:
            raise VelocityFrameError(
                "transfer_source=none must not carry TransferFunctionSpec"
            )
        if provider_kind is ResponseProviderKind.EMPIRICAL_PROXY:
            raise VelocityFrameError(
                "EMPIRICAL_PROXY providers require empirical_proxy provenance"
            )
        return transfer, source, None
    if provider_kind is not ResponseProviderKind.EMPIRICAL_PROXY:
        raise VelocityFrameError(
            "empirical_proxy provenance requires EMPIRICAL_PROXY provider kind"
        )
    if type(transfer_spec) is not TransferFunctionSpec:
        raise VelocityFrameError(
            "empirical_proxy providers require an exact TransferFunctionSpec"
        )
    transfer = _text(transfer_id, "transfer_id")
    if transfer_spec.source is not source or transfer_spec.transfer_id != transfer:
        raise VelocityFrameError(
            "transfer_id and transfer_source must match TransferFunctionSpec"
        )
    return transfer, source, transfer_spec


def _normalizer_for_blocks(
    normalizer: object,
    *,
    local_labels: tuple[str, ...],
    global_labels: tuple[str, ...],
) -> NormalizerSpec:
    if type(normalizer) is not NormalizerSpec:
        raise VelocityFrameError("normalizer must be an exact NormalizerSpec")
    labels = (*local_labels, *global_labels)
    if normalizer.availability is not NormalizerAvailability.AVAILABLE:
        raise VelocityFrameError("normalizer must be available")
    if NormalizerPurpose.RESPONSE_CONDITIONING not in normalizer.purposes:
        raise VelocityFrameError(
            "normalizer must declare RESPONSE_CONDITIONING"
        )
    if normalizer.coordinate_labels != labels:
        raise VelocityFrameError(
            "normalizer labels must match local labels followed by global labels"
        )
    matrix = _matrix(
        normalizer.coordinate_map,
        "normalizer.coordinate_map",
        shape=(len(labels), len(labels)),
    )
    split = len(local_labels)
    if np.any(matrix[:split, split:] != 0.0) or np.any(
        matrix[split:, :split] != 0.0
    ):
        raise VelocityFrameError(
            "normalizer must not mix local and global parameter blocks"
        )
    if (
        np.linalg.matrix_rank(matrix[:split, :split]) != split
        or np.linalg.matrix_rank(matrix[split:, split:])
        != len(global_labels)
    ):
        raise VelocityFrameError(
            "local and global normalizer blocks must each be invertible"
        )
    return normalizer


def _rank_and_singular(
    matrix: np.ndarray,
    *,
    rtol: float,
) -> tuple[int, tuple[float, ...], np.ndarray]:
    if matrix.shape[0] == 0:
        return 0, (), np.empty((matrix.shape[0], 0), dtype=float)
    u, singular, _ = np.linalg.svd(matrix, full_matrices=False)
    scale = float(singular[0]) if singular.size else 0.0
    rank = int(np.count_nonzero(singular > rtol * scale))
    return (
        rank,
        tuple(float(value) for value in singular),
        u[:, :rank],
    )


@dataclass(frozen=True)
class VelocityFrameDecomposition:
    """First-order frame-velocity closure report.

    ``beta_RO`` is radiation relative to observer, ``beta_RM`` is radiation
    relative to matter, and ``beta_MO`` is matter relative to observer.
    No missing component is derived by this type.
    """

    beta_RO: tuple[float, ...] | None
    beta_RM: tuple[float, ...] | None
    beta_MO: tuple[float, ...] | None
    basis: str
    epoch_window: str
    units: str
    parity: str
    perturbative_order: str
    first_order_beta_ceiling: float
    status: VelocityDecompositionStatus
    closure_residual: tuple[float, ...] | None
    closure_norm: float | None
    closure_tolerance: float | None
    atol: float
    rtol: float
    missing_components: tuple[str, ...]
    truncation_remainder_bound: float | None = None
    allowed_use: tuple[str, ...] = _DECOMPOSITION_ALLOWED_USE
    forbidden_use: tuple[str, ...] = _DECOMPOSITION_FORBIDDEN_USE
    _construction_token: InitVar[object] = None

    def __post_init__(self, _construction_token: object) -> None:
        if _construction_token is not _DECOMPOSITION_TOKEN:
            raise VelocityFrameError(
                "VelocityFrameDecomposition must be created by "
                "build_velocity_frame_decomposition"
            )
        if not isinstance(self.status, VelocityDecompositionStatus):
            raise VelocityFrameError(
                "status must be a VelocityDecompositionStatus"
            )
        if self.units != "dimensionless_beta_c_equals_1":
            raise VelocityFrameError(
                "velocity units must be dimensionless_beta_c_equals_1"
            )
        if self.parity != "polar_vector":
            raise VelocityFrameError("velocity parity must be polar_vector")
        if self.perturbative_order != "first_order_small_velocity":
            raise VelocityFrameError(
                "velocity perturbative_order must be "
                "first_order_small_velocity"
            )
        if (
            self.allowed_use != _DECOMPOSITION_ALLOWED_USE
            or self.forbidden_use != _DECOMPOSITION_FORBIDDEN_USE
        ):
            raise VelocityFrameError(
                "velocity decomposition must retain its claim boundary"
            )

    def as_payload(self) -> dict[str, object]:
        return {
            "beta_RO": None if self.beta_RO is None else list(self.beta_RO),
            "beta_RM": None if self.beta_RM is None else list(self.beta_RM),
            "beta_MO": None if self.beta_MO is None else list(self.beta_MO),
            "basis": self.basis,
            "epoch_window": self.epoch_window,
            "units": self.units,
            "parity": self.parity,
            "perturbative_order": self.perturbative_order,
            "first_order_beta_ceiling": self.first_order_beta_ceiling,
            "relation": "beta_RO = beta_RM + beta_MO + O(beta^2)",
            "status": self.status.value,
            "closure_residual": (
                None
                if self.closure_residual is None
                else list(self.closure_residual)
            ),
            "closure_norm": self.closure_norm,
            "closure_tolerance": self.closure_tolerance,
            "truncation_remainder_bound": (
                self.truncation_remainder_bound
            ),
            "atol": self.atol,
            "rtol": self.rtol,
            "missing_components": list(self.missing_components),
            "allowed_use": list(self.allowed_use),
            "forbidden_use": list(self.forbidden_use),
        }


def build_velocity_frame_decomposition(
    *,
    beta_RO: object | None,
    beta_RM: object | None,
    beta_MO: object | None,
    basis: str,
    epoch_window: str,
    first_order_beta_ceiling: float,
    units: str = "dimensionless_beta_c_equals_1",
    parity: str = "polar_vector",
    perturbative_order: str = "first_order_small_velocity",
    atol: float = 1.0e-15,
    rtol: float = 1.0e-10,
) -> VelocityFrameDecomposition:
    """Build a closure report without filling any missing component."""

    basis_value = _text(basis, "basis")
    epoch = _text(epoch_window, "epoch_window")
    units_value = _text(units, "units")
    parity_value = _text(parity, "parity")
    order = _text(perturbative_order, "perturbative_order")
    if units_value != "dimensionless_beta_c_equals_1":
        raise VelocityFrameError(
            "velocity units must be dimensionless_beta_c_equals_1"
        )
    if parity_value != "polar_vector":
        raise VelocityFrameError("velocity parity must be polar_vector")
    if order != "first_order_small_velocity":
        raise VelocityFrameError(
            "velocity perturbative_order must be first_order_small_velocity"
        )
    beta_ceiling = _nonnegative(
        first_order_beta_ceiling,
        "first_order_beta_ceiling",
    )
    if beta_ceiling == 0.0 or beta_ceiling > 0.1:
        raise VelocityFrameError(
            "first_order_beta_ceiling must be positive and at most 0.1"
        )
    absolute = _nonnegative(atol, "atol")
    relative = _nonnegative(rtol, "rtol")
    if absolute == 0.0 and relative == 0.0:
        raise VelocityFrameError("atol and rtol must not both be zero")
    vectors = {
        "beta_RO": None if beta_RO is None else _vector(beta_RO, "beta_RO"),
        "beta_RM": None if beta_RM is None else _vector(beta_RM, "beta_RM"),
        "beta_MO": None if beta_MO is None else _vector(beta_MO, "beta_MO"),
    }
    available_norms = {
        name: float(np.linalg.norm(value))
        for name, value in vectors.items()
        if value is not None
    }
    expansion_candidates: list[float] = []
    if vectors["beta_RO"] is not None:
        expansion_candidates.append(available_norms["beta_RO"])
    if vectors["beta_RM"] is not None and vectors["beta_MO"] is not None:
        expansion_candidates.append(
            available_norms["beta_RM"] + available_norms["beta_MO"]
        )
    else:
        for name in ("beta_RM", "beta_MO"):
            if vectors[name] is not None:
                expansion_candidates.append(available_norms[name])
    expansion_scale = max(expansion_candidates, default=0.0)
    if expansion_scale > beta_ceiling:
        raise VelocityFrameError(
            "velocity components exceed the registered "
            "first_order_beta_ceiling"
        )
    missing = tuple(name for name, value in vectors.items() if value is None)
    residual: np.ndarray | None = None
    residual_norm: float | None = None
    closure_tolerance: float | None = None
    truncation_remainder_bound: float | None = None
    if not missing:
        beta_ro = vectors["beta_RO"]
        beta_rm = vectors["beta_RM"]
        beta_mo = vectors["beta_MO"]
        assert beta_ro is not None and beta_rm is not None and beta_mo is not None
        residual = beta_ro - beta_rm - beta_mo
        residual_norm = float(np.linalg.norm(residual))
        scale = max(
            float(np.linalg.norm(beta_ro)),
            float(np.linalg.norm(beta_rm + beta_mo)),
        )
        component_scale = float(np.linalg.norm(beta_rm)) + float(
            np.linalg.norm(beta_mo)
        )
        truncation_remainder_bound = component_scale**2
        closure_tolerance = (
            absolute
            + relative * scale
            + truncation_remainder_bound
        )
        status = (
            VelocityDecompositionStatus.CLOSURE_VERIFIED
            if residual_norm <= closure_tolerance
            else VelocityDecompositionStatus.CLOSURE_MISMATCH
        )
    elif vectors["beta_RO"] is not None:
        status = VelocityDecompositionStatus.SUM_ONLY
    else:
        status = VelocityDecompositionStatus.MISSING_COMPONENT
    return VelocityFrameDecomposition(
        beta_RO=(
            None
            if vectors["beta_RO"] is None
            else _vector_tuple(vectors["beta_RO"])
        ),
        beta_RM=(
            None
            if vectors["beta_RM"] is None
            else _vector_tuple(vectors["beta_RM"])
        ),
        beta_MO=(
            None
            if vectors["beta_MO"] is None
            else _vector_tuple(vectors["beta_MO"])
        ),
        basis=basis_value,
        epoch_window=epoch,
        units=units_value,
        parity=parity_value,
        perturbative_order=order,
        first_order_beta_ceiling=beta_ceiling,
        status=status,
        closure_residual=(
            None if residual is None else _vector_tuple(residual)
        ),
        closure_norm=residual_norm,
        closure_tolerance=closure_tolerance,
        atol=absolute,
        rtol=relative,
        missing_components=missing,
        truncation_remainder_bound=truncation_remainder_bound,
        _construction_token=_DECOMPOSITION_TOKEN,
    )


def revalidate_velocity_frame_decomposition(
    report: VelocityFrameDecomposition,
) -> VelocityFrameDecomposition:
    if type(report) is not VelocityFrameDecomposition:
        raise VelocityFrameError(
            "report must be an exact VelocityFrameDecomposition"
        )
    rebuilt = build_velocity_frame_decomposition(
        beta_RO=report.beta_RO,
        beta_RM=report.beta_RM,
        beta_MO=report.beta_MO,
        basis=report.basis,
        epoch_window=report.epoch_window,
        first_order_beta_ceiling=report.first_order_beta_ceiling,
        units=report.units,
        parity=report.parity,
        perturbative_order=report.perturbative_order,
        atol=report.atol,
        rtol=report.rtol,
    )
    if rebuilt != report:
        raise VelocityFrameError("velocity-frame report failed replay")
    return report


@dataclass(frozen=True)
class SourceResponseProviderSpec:
    """One exact local or global hypothesis-response provider."""

    provider_id: str
    hypothesis: SourceHypothesis
    velocity_component: VelocityComponent
    provider_kind: ResponseProviderKind
    availability: ResponseProviderAvailability
    response_role: str
    observable_labels: tuple[str, ...]
    parameter_labels: tuple[str, ...]
    response_id: str | None
    response_replay_matrix: tuple[tuple[float, ...], ...] | None
    transfer_id: str
    transfer_source: TransferSource
    transfer_spec: TransferFunctionSpec | None
    basis: str
    epoch_window: str
    perturbative_order: str
    velocity_parity: str
    assumptions: tuple[str, ...]
    caveats: tuple[str, ...]
    missing_reason: str | None
    _construction_token: InitVar[object] = None

    def __post_init__(self, _construction_token: object) -> None:
        if _construction_token is not _PROVIDER_TOKEN:
            raise VelocityFrameError(
                "SourceResponseProviderSpec must be created by "
                "register_source_response_provider"
            )
        if not isinstance(self.hypothesis, SourceHypothesis):
            raise VelocityFrameError("hypothesis must be a SourceHypothesis")
        if self.velocity_component is not _EXPECTED_COMPONENT[self.hypothesis]:
            raise VelocityFrameError(
                "hypothesis and velocity_component do not match"
            )
        if not isinstance(self.provider_kind, ResponseProviderKind):
            raise VelocityFrameError(
                "provider_kind must be a ResponseProviderKind"
            )
        if not isinstance(self.availability, ResponseProviderAvailability):
            raise VelocityFrameError(
                "availability must be a ResponseProviderAvailability"
            )
        if self.response_role != _RESPONSE_ROLE:
            raise VelocityFrameError("response_role must be hypothesis_only")
        if self.velocity_parity != "polar_vector":
            raise VelocityFrameError(
                "source velocity parity must be polar_vector"
            )
        if not isinstance(self.transfer_source, TransferSource):
            raise VelocityFrameError(
                "transfer_source must be a TransferSource"
            )

    def as_payload(self) -> dict[str, object]:
        return {
            "provider_id": self.provider_id,
            "hypothesis": self.hypothesis.value,
            "velocity_component": self.velocity_component.value,
            "provider_kind": self.provider_kind.value,
            "availability": self.availability.value,
            "response_role": self.response_role,
            "observable_labels": list(self.observable_labels),
            "parameter_labels": list(self.parameter_labels),
            "response_id": self.response_id,
            "transfer_id": self.transfer_id,
            "transfer_source": self.transfer_source.value,
            "transfer_metadata": (
                None
                if self.transfer_spec is None
                else self.transfer_spec.to_metadata()
            ),
            "basis": self.basis,
            "epoch_window": self.epoch_window,
            "perturbative_order": self.perturbative_order,
            "velocity_parity": self.velocity_parity,
            "assumptions": list(self.assumptions),
            "caveats": list(self.caveats),
            "missing_reason": self.missing_reason,
        }


def register_source_response_provider(
    *,
    provider_id: str,
    hypothesis: SourceHypothesis,
    velocity_component: VelocityComponent,
    provider_kind: ResponseProviderKind,
    availability: ResponseProviderAvailability,
    observable_labels: Sequence[object],
    parameter_labels: Sequence[object],
    response: object | None,
    transfer_id: str,
    transfer_source: TransferSource | str,
    transfer_spec: TransferFunctionSpec | None = None,
    basis: str,
    epoch_window: str,
    perturbative_order: str = "first_order_response",
    velocity_parity: str = "polar_vector",
    assumptions: Sequence[object] = (),
    caveats: Sequence[object] = (),
    missing_reason: str | None = None,
    response_role: str = _RESPONSE_ROLE,
) -> SourceResponseProviderSpec:
    """Register one provider while preserving unavailable-response semantics."""

    if not isinstance(hypothesis, SourceHypothesis):
        raise VelocityFrameError("hypothesis must be a SourceHypothesis")
    if not isinstance(velocity_component, VelocityComponent):
        raise VelocityFrameError(
            "velocity_component must be a VelocityComponent"
        )
    if velocity_component is not _EXPECTED_COMPONENT[hypothesis]:
        raise VelocityFrameError(
            "LOCAL_BOOST requires beta_MO and GLOBAL_TILT requires beta_RM"
        )
    if not isinstance(provider_kind, ResponseProviderKind):
        raise VelocityFrameError(
            "provider_kind must be a ResponseProviderKind"
        )
    if not isinstance(availability, ResponseProviderAvailability):
        raise VelocityFrameError(
            "availability must be a ResponseProviderAvailability"
        )
    provider = _receipt(provider_id, "provider_id")
    role = _text(response_role, "response_role")
    if role != _RESPONSE_ROLE:
        raise VelocityFrameError("response_role must be hypothesis_only")
    observables = _texts(observable_labels, "observable_labels")
    parameters = _texts(parameter_labels, "parameter_labels")
    transfer, source, canonical_spec = _validate_transfer_binding(
        provider_kind=provider_kind,
        transfer_id=transfer_id,
        transfer_source=transfer_source,
        transfer_spec=transfer_spec,
    )
    basis_value = _text(basis, "basis")
    epoch = _text(epoch_window, "epoch_window")
    order = _text(perturbative_order, "perturbative_order")
    parity = _text(velocity_parity, "velocity_parity")
    if parity != "polar_vector":
        raise VelocityFrameError(
            "source velocity parity must be polar_vector"
        )
    assumption_values = _texts(assumptions, "assumptions", empty_ok=True)
    caveat_values = _texts(caveats, "caveats")
    matrix_value: tuple[tuple[float, ...], ...] | None
    response_id: str | None
    reason: str | None
    if availability is ResponseProviderAvailability.MISSING:
        if response is not None:
            raise VelocityFrameError(
                "missing providers must not carry a zero or supplied response"
            )
        reason = _text(missing_reason, "missing_reason")
        matrix_value = None
        response_id = None
    else:
        if response is None:
            raise VelocityFrameError(
                "available providers require an explicit response"
            )
        if missing_reason is not None:
            raise VelocityFrameError(
                "available providers must not carry missing_reason"
            )
        matrix = _matrix(
            response,
            "response",
            shape=(len(observables), len(parameters)),
        )
        matrix_value = _matrix_tuple(matrix)
        response_id = anchored_numeric_content_id(matrix)
        reason = None
    return SourceResponseProviderSpec(
        provider_id=provider,
        hypothesis=hypothesis,
        velocity_component=velocity_component,
        provider_kind=provider_kind,
        availability=availability,
        response_role=role,
        observable_labels=observables,
        parameter_labels=parameters,
        response_id=response_id,
        response_replay_matrix=matrix_value,
        transfer_id=transfer,
        transfer_source=source,
        transfer_spec=canonical_spec,
        basis=basis_value,
        epoch_window=epoch,
        perturbative_order=order,
        velocity_parity=parity,
        assumptions=assumption_values,
        caveats=caveat_values,
        missing_reason=reason,
        _construction_token=_PROVIDER_TOKEN,
    )


def revalidate_source_response_provider(
    provider: SourceResponseProviderSpec,
) -> SourceResponseProviderSpec:
    if type(provider) is not SourceResponseProviderSpec:
        raise VelocityFrameError(
            "provider must be an exact SourceResponseProviderSpec"
        )
    rebuilt = register_source_response_provider(
        provider_id=provider.provider_id,
        hypothesis=provider.hypothesis,
        velocity_component=provider.velocity_component,
        provider_kind=provider.provider_kind,
        availability=provider.availability,
        observable_labels=provider.observable_labels,
        parameter_labels=provider.parameter_labels,
        response=provider.response_replay_matrix,
        transfer_id=provider.transfer_id,
        transfer_source=provider.transfer_source,
        transfer_spec=provider.transfer_spec,
        basis=provider.basis,
        epoch_window=provider.epoch_window,
        perturbative_order=provider.perturbative_order,
        velocity_parity=provider.velocity_parity,
        assumptions=provider.assumptions,
        caveats=provider.caveats,
        missing_reason=provider.missing_reason,
        response_role=provider.response_role,
    )
    if rebuilt != provider:
        raise VelocityFrameError("source-response provider failed replay")
    return provider


@dataclass(frozen=True)
class SourceResponseGeometryReport:
    """Nuisance-projected local/global tangent-space separation report."""

    status: SourceResponseGeometryStatus
    local_provider: SourceResponseProviderSpec
    global_provider: SourceResponseProviderSpec
    local_rank: int | None
    global_rank: int | None
    joint_rank: int | None
    local_singular_values: tuple[float, ...]
    global_singular_values: tuple[float, ...]
    joint_singular_values: tuple[float, ...]
    principal_angles_radians: tuple[float, ...]
    minimum_principal_angle_radians: float | None
    separation_threshold_radians: float
    direct_sum: bool | None
    covariance_null_response_norm_sq: float | None
    common_geometry: AnchoredResponseGeometryReport | None
    normalizer_id: str
    normalizer_source_identity: str
    covariance_id: str
    mask_id: str
    joint_transfer_id: str | None
    observable_labels: tuple[str, ...]
    local_parameter_labels: tuple[str, ...]
    global_parameter_labels: tuple[str, ...]
    covariance_replay_matrix: tuple[tuple[float, ...], ...]
    nuisance_replay_matrix: tuple[tuple[float, ...], ...] | None
    relative_tolerance: float
    missing_provider_ids: tuple[str, ...]
    assumptions: tuple[str, ...]
    allowed_use: tuple[str, ...] = _GEOMETRY_ALLOWED_USE
    forbidden_use: tuple[str, ...] = _GEOMETRY_FORBIDDEN_USE
    _construction_token: InitVar[object] = None

    def __post_init__(self, _construction_token: object) -> None:
        if _construction_token is not _GEOMETRY_TOKEN:
            raise VelocityFrameError(
                "SourceResponseGeometryReport must be created by "
                "measure_source_response_geometry"
            )
        if not isinstance(self.status, SourceResponseGeometryStatus):
            raise VelocityFrameError(
                "status must be a SourceResponseGeometryStatus"
            )
        if type(self.local_provider) is not SourceResponseProviderSpec or type(
            self.global_provider
        ) is not SourceResponseProviderSpec:
            raise VelocityFrameError(
                "source-response reports require exact registered providers"
            )
        if (
            self.allowed_use != _GEOMETRY_ALLOWED_USE
            or self.forbidden_use != _GEOMETRY_FORBIDDEN_USE
        ):
            raise VelocityFrameError(
                "source-response geometry must retain its claim boundary"
            )

    @property
    def separable_candidate(self) -> bool:
        return self.status is SourceResponseGeometryStatus.SEPARABLE_CANDIDATE

    def as_payload(self) -> dict[str, object]:
        return {
            "status": self.status.value,
            "velocity_relation": "beta_RO = beta_RM + beta_MO + O(beta^2)",
            "local_provider": self.local_provider.as_payload(),
            "global_provider": self.global_provider.as_payload(),
            "local_rank": self.local_rank,
            "global_rank": self.global_rank,
            "joint_rank": self.joint_rank,
            "local_singular_values": list(self.local_singular_values),
            "global_singular_values": list(self.global_singular_values),
            "joint_singular_values": list(self.joint_singular_values),
            "principal_angles_radians": list(self.principal_angles_radians),
            "minimum_principal_angle_radians": (
                self.minimum_principal_angle_radians
            ),
            "separation_threshold_radians": self.separation_threshold_radians,
            "direct_sum": self.direct_sum,
            "covariance_null_response_norm_sq": (
                self.covariance_null_response_norm_sq
            ),
            "common_geometry_status": (
                None
                if self.common_geometry is None
                else self.common_geometry.status.value
            ),
            "normalizer_id": self.normalizer_id,
            "normalizer_source_identity": self.normalizer_source_identity,
            "covariance_id": self.covariance_id,
            "mask_id": self.mask_id,
            "joint_transfer_id": self.joint_transfer_id,
            "observable_labels": list(self.observable_labels),
            "local_parameter_labels": list(self.local_parameter_labels),
            "global_parameter_labels": list(self.global_parameter_labels),
            "relative_tolerance": self.relative_tolerance,
            "missing_provider_ids": list(self.missing_provider_ids),
            "assumptions": list(self.assumptions),
            "allowed_use": list(self.allowed_use),
            "forbidden_use": list(self.forbidden_use),
        }


def measure_source_response_geometry(
    *,
    local_provider: SourceResponseProviderSpec,
    global_provider: SourceResponseProviderSpec,
    covariance: object,
    normalizer: NormalizerSpec,
    covariance_id: str,
    mask_id: str,
    nuisance_response: object | None = None,
    separation_threshold_radians: float = 0.2,
    rtol: float = 1.0e-12,
    assumptions: Sequence[object] = (
        "first-order small-velocity response",
        "common covariance and nuisance tangent space",
    ),
) -> SourceResponseGeometryReport:
    """Compare local/global hypothesis-response tangent spaces fail closed."""

    local = revalidate_source_response_provider(local_provider)
    global_value = revalidate_source_response_provider(global_provider)
    if local.hypothesis is not SourceHypothesis.LOCAL_BOOST:
        raise VelocityFrameError("local_provider must register LOCAL_BOOST")
    if global_value.hypothesis is not SourceHypothesis.GLOBAL_TILT:
        raise VelocityFrameError("global_provider must register GLOBAL_TILT")
    if local.observable_labels != global_value.observable_labels:
        raise VelocityFrameError(
            "local and global providers must use identical observable labels"
        )
    if (
        local.basis != global_value.basis
        or local.epoch_window != global_value.epoch_window
        or local.perturbative_order != global_value.perturbative_order
        or local.velocity_parity != global_value.velocity_parity
    ):
        raise VelocityFrameError(
            "local and global providers must share basis, epoch/window, "
            "perturbative order, and velocity parity"
        )
    if set(local.parameter_labels).intersection(global_value.parameter_labels):
        raise VelocityFrameError(
            "local and global parameter labels must be disjoint"
        )
    normalizer_value = _normalizer_for_blocks(
        normalizer,
        local_labels=local.parameter_labels,
        global_labels=global_value.parameter_labels,
    )
    observables = local.observable_labels
    covariance_matrix = _matrix(
        covariance,
        "covariance",
        shape=(len(observables), len(observables)),
    )
    covariance_receipt = _receipt(covariance_id, "covariance_id")
    if covariance_receipt != anchored_numeric_content_id(covariance_matrix):
        raise VelocityFrameError(
            "covariance_id must match canonical numeric content"
        )
    mask = _receipt(mask_id, "mask_id")
    nuisance_matrix: np.ndarray | None = None
    if nuisance_response is not None:
        nuisance_matrix = _matrix(nuisance_response, "nuisance_response")
        if nuisance_matrix.shape[0] != len(observables):
            raise VelocityFrameError(
                "nuisance_response row count must match observable labels"
            )
    threshold = _nonnegative(
        separation_threshold_radians,
        "separation_threshold_radians",
    )
    if threshold > math.pi / 2.0:
        raise VelocityFrameError(
            "separation_threshold_radians must not exceed pi/2"
        )
    relative = _nonnegative(rtol, "rtol")
    if relative == 0.0 or relative > 1.0e-3:
        raise VelocityFrameError(
            "rtol must be positive and at most 1e-3"
        )
    assumption_values = _texts(assumptions, "assumptions")
    missing = tuple(
        provider.provider_id
        for provider in (local, global_value)
        if provider.availability is ResponseProviderAvailability.MISSING
    )
    if local.provider_id == global_value.provider_id:
        raise VelocityFrameError(
            "local and global providers must use distinct provider_id values"
        )
    if (
        local.transfer_source is not global_value.transfer_source
        or local.transfer_spec != global_value.transfer_spec
        or local.transfer_id != global_value.transfer_id
    ):
        raise VelocityFrameError(
            "local and global providers must share exact transfer provenance"
        )
    if missing:
        return SourceResponseGeometryReport(
            status=SourceResponseGeometryStatus.MISSING_RESPONSE_PROVIDER,
            local_provider=local,
            global_provider=global_value,
            local_rank=None,
            global_rank=None,
            joint_rank=None,
            local_singular_values=(),
            global_singular_values=(),
            joint_singular_values=(),
            principal_angles_radians=(),
            minimum_principal_angle_radians=None,
            separation_threshold_radians=threshold,
            direct_sum=None,
            covariance_null_response_norm_sq=None,
            common_geometry=None,
            normalizer_id=normalizer_value.normalizer_id,
            normalizer_source_identity=normalizer_value.source_identity,
            covariance_id=covariance_receipt,
            mask_id=mask,
            joint_transfer_id=None,
            observable_labels=observables,
            local_parameter_labels=local.parameter_labels,
            global_parameter_labels=global_value.parameter_labels,
            covariance_replay_matrix=_matrix_tuple(covariance_matrix),
            nuisance_replay_matrix=(
                None
                if nuisance_matrix is None
                else _matrix_tuple(nuisance_matrix)
            ),
            relative_tolerance=relative,
            missing_provider_ids=missing,
            assumptions=assumption_values,
            _construction_token=_GEOMETRY_TOKEN,
        )
    if local.transfer_source is TransferSource.EMPIRICAL_PROXY:
        joint_transfer_id = local.transfer_id
        joint_transfer_spec = local.transfer_spec
    else:
        joint_transfer_id = _semantic_receipt(
            {
                "schema": "PR256_JOINT_HYPOTHESIS_RESPONSE_V1",
                "shared_transfer_id": local.transfer_id,
                "local_provider_id": local.provider_id,
                "local_response_id": local.response_id,
                "global_provider_id": global_value.provider_id,
                "global_response_id": global_value.response_id,
            }
        )
        joint_transfer_spec = None
    assert local.response_replay_matrix is not None
    assert global_value.response_replay_matrix is not None
    local_matrix = np.asarray(local.response_replay_matrix, dtype=float)
    global_matrix = np.asarray(
        global_value.response_replay_matrix,
        dtype=float,
    )
    combined = np.column_stack((local_matrix, global_matrix))
    labels = (*local.parameter_labels, *global_value.parameter_labels)
    common_report = measure_anchored_response_geometry(
        response=combined,
        covariance=covariance_matrix,
        normalizer=normalizer_value,
        parameter_labels=labels,
        transfer_id=joint_transfer_id,
        transfer_source=local.transfer_source,
        transfer_spec=joint_transfer_spec,
        mask_id=mask,
        covariance_id=covariance_receipt,
        nuisance_response=nuisance_matrix,
        rtol=relative,
    )
    if common_report.anchored_response_replay_matrix is None:
        raise VelocityFrameError(
            "measured common geometry did not preserve its replay matrix"
        )
    anchored = np.asarray(
        common_report.anchored_response_replay_matrix,
        dtype=float,
    )
    split = len(local.parameter_labels)
    local_anchored = anchored[:, :split]
    global_anchored = anchored[:, split:]
    local_rank, local_singular, local_basis = _rank_and_singular(
        local_anchored,
        rtol=relative,
    )
    global_rank, global_singular, global_basis = _rank_and_singular(
        global_anchored,
        rtol=relative,
    )
    joint_rank = int(common_report.rank or 0)
    joint_singular = tuple(common_report.singular_values)
    direct_sum = joint_rank == local_rank + global_rank
    if local_rank == 0 or global_rank == 0:
        angles: tuple[float, ...] = ()
        minimum_angle = None
    else:
        cosines = np.linalg.svd(
            local_basis.T @ global_basis,
            compute_uv=False,
        )
        angles_array = np.arccos(np.clip(cosines, -1.0, 1.0))
        angles = tuple(float(value) for value in angles_array)
        minimum_angle = min(angles)
    if (
        common_report.status
        in {
            AnchoredResponseStatus.OUTSIDE_SUPPORTED_QUOTIENT,
            AnchoredResponseStatus.EXPLICIT_NULL_RESPONSE,
        }
        or local_rank == 0
        or global_rank == 0
        or local_rank < len(local.parameter_labels)
        or global_rank < len(global_value.parameter_labels)
    ):
        status = SourceResponseGeometryStatus.NON_IDENTIFIED
    elif (
        not direct_sum
        or minimum_angle is None
        or minimum_angle <= threshold
    ):
        status = SourceResponseGeometryStatus.SUM_ONLY
    else:
        status = SourceResponseGeometryStatus.SEPARABLE_CANDIDATE
    return SourceResponseGeometryReport(
        status=status,
        local_provider=local,
        global_provider=global_value,
        local_rank=local_rank,
        global_rank=global_rank,
        joint_rank=joint_rank,
        local_singular_values=local_singular,
        global_singular_values=global_singular,
        joint_singular_values=joint_singular,
        principal_angles_radians=angles,
        minimum_principal_angle_radians=minimum_angle,
        separation_threshold_radians=threshold,
        direct_sum=direct_sum,
        covariance_null_response_norm_sq=(
            common_report.covariance_null_response_norm_sq
        ),
        common_geometry=common_report,
        normalizer_id=normalizer_value.normalizer_id,
        normalizer_source_identity=normalizer_value.source_identity,
        covariance_id=covariance_receipt,
        mask_id=mask,
        joint_transfer_id=joint_transfer_id,
        observable_labels=observables,
        local_parameter_labels=local.parameter_labels,
        global_parameter_labels=global_value.parameter_labels,
        covariance_replay_matrix=_matrix_tuple(covariance_matrix),
        nuisance_replay_matrix=(
            None
            if nuisance_matrix is None
            else _matrix_tuple(nuisance_matrix)
        ),
        relative_tolerance=relative,
        missing_provider_ids=(),
        assumptions=assumption_values,
        _construction_token=_GEOMETRY_TOKEN,
    )


def revalidate_source_response_geometry(
    report: SourceResponseGeometryReport,
    *,
    normalizer: NormalizerSpec,
) -> SourceResponseGeometryReport:
    if type(report) is not SourceResponseGeometryReport:
        raise VelocityFrameError(
            "report must be an exact SourceResponseGeometryReport"
        )
    rebuilt = measure_source_response_geometry(
        local_provider=report.local_provider,
        global_provider=report.global_provider,
        covariance=report.covariance_replay_matrix,
        normalizer=normalizer,
        covariance_id=report.covariance_id,
        mask_id=report.mask_id,
        nuisance_response=report.nuisance_replay_matrix,
        separation_threshold_radians=report.separation_threshold_radians,
        rtol=report.relative_tolerance,
        assumptions=report.assumptions,
    )
    if rebuilt != report:
        raise VelocityFrameError("source-response geometry failed replay")
    return report


__all__ = [
    "ResponseProviderAvailability",
    "ResponseProviderKind",
    "SourceHypothesis",
    "SourceResponseGeometryReport",
    "SourceResponseGeometryStatus",
    "SourceResponseProviderSpec",
    "VelocityComponent",
    "VelocityDecompositionStatus",
    "VelocityFrameDecomposition",
    "VelocityFrameError",
    "build_velocity_frame_decomposition",
    "measure_source_response_geometry",
    "register_source_response_provider",
    "revalidate_source_response_geometry",
    "revalidate_source_response_provider",
    "revalidate_velocity_frame_decomposition",
]
