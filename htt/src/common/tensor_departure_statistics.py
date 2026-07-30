"""Typed vector/tensor successors for the historical ``(x, Q, F, G_F)`` lane.

The active contracts in this module are deliberately narrower than the
historical scalar vocabulary:

* ``x`` is a sample-wise, preregistered scalarization of an exact
  :class:`~common.tensor_functionals.TensorFunctionalResult`;
* ``Q`` is the existing PR-254/PR-262 premise-anchor stress, never a new
  denominator or a distance/probability;
* ``F`` is a directional support-utilization profile for a finite identified
  set and one declared PR-254 anchor body; and
* the object named ``OccupancyMeasure`` is only an empirical level-set mass
  over eligible diagnostic samples.  It is not physical occupancy.

``Pi`` and the depth-path successor to ``G_F`` are intentionally unavailable
until PR-265 and PR-266.  The legacy view preserves their historical values
without silently granting them the semantics of those future typed objects.

All public results are diagnostic-only.  This module contains no likelihood,
posterior, evidence, native-solver, geometry-identification, or Bianchi-family
operation.
"""

from __future__ import annotations

from dataclasses import InitVar, dataclass, field
from enum import Enum
import hashlib
import json
import math
from numbers import Real
from typing import Mapping, Sequence

import numpy as np
from scipy.optimize import linprog

from common.anchor_geometry import (
    AnchorAvailability,
    AnchorBlockSpec,
    AnchorBodySpec,
    AnchorGaugeStatus,
    AnchorGeometryKind,
    AnchorVector,
    PolytopeHalfspace,
    evaluate_anchor_gauge,
)
from common.orbit_nonlinearity import stf5_to_matrix
from common.tensor_functionals import (
    FunctionalAdmissibilityStatus,
    FunctionalDomainStatus,
    FunctionalO3Type,
    FunctionalSignClass,
    FunctionalStressStatus,
    TensorFunctionalResult,
)


class TensorDepartureStatisticsError(ValueError):
    """Raised when a tensor departure-statistics contract is malformed."""


class _StringEnum(str, Enum):
    def __str__(self) -> str:
        return self.value


class ScalarizationPolicy(_StringEnum):
    """Preregistered deterministic maps from a functional codomain to ``x``."""

    SCALAR_IDENTITY = "SCALAR_IDENTITY"
    EUCLIDEAN_NORM = "EUCLIDEAN_NORM"
    STF_FROBENIUS_NORM = "STF_FROBENIUS_NORM"


class FunctionalCellStatus(_StringEnum):
    """Availability of one sample/functional ``x`` and anchor-stress cell."""

    DEFINED = "DEFINED"
    CONDITIONAL_ANCHOR = "CONDITIONAL_ANCHOR"
    MISSING_COMPONENT = "MISSING_COMPONENT"
    INADMISSIBLE = "INADMISSIBLE"
    ANCHOR_UNAVAILABLE = "ANCHOR_UNAVAILABLE"


class PushforwardSummaryStatus(_StringEnum):
    DEFINED = "DEFINED"
    PARTIAL_MISSING = "PARTIAL_MISSING"
    INSUFFICIENT_SAMPLES = "INSUFFICIENT_SAMPLES"


class SupportUtilizationStatus(_StringEnum):
    DEFINED = "DEFINED"
    PARTIAL_DENOMINATOR_COLLAPSE = "PARTIAL_DENOMINATOR_COLLAPSE"
    MISSING_IDENTIFIED_SET = "MISSING_IDENTIFIED_SET"
    ANCHOR_UNAVAILABLE = "ANCHOR_UNAVAILABLE"
    CHANNEL_MISMATCH = "CHANNEL_MISMATCH"


class DirectionalRatioStatus(_StringEnum):
    DEFINED = "DEFINED"
    DENOMINATOR_COLLAPSE = "DENOMINATOR_COLLAPSE"
    ANCHOR_UNAVAILABLE = "ANCHOR_UNAVAILABLE"
    CHANNEL_MISMATCH = "CHANNEL_MISMATCH"


class OccupancyMeasureStatus(_StringEnum):
    DEFINED = "DEFINED"
    INELIGIBLE_FUNCTIONAL = "INELIGIBLE_FUNCTIONAL"
    MISSING_OR_UNAVAILABLE_SUPPORT = "MISSING_OR_UNAVAILABLE_SUPPORT"


class LegacyCompatibilityStatus(_StringEnum):
    MATCHED = "MATCHED"
    MISMATCH = "MISMATCH"
    PRESERVED_PENDING_TYPED_SUCCESSOR = "PRESERVED_PENDING_TYPED_SUCCESSOR"
    UNAVAILABLE = "UNAVAILABLE"


TENSOR_DEPARTURE_CLAIM_CEILING = "diagnostic_only"
TENSOR_DEPARTURE_ALLOWED_USE = (
    "sample-wise functional pushforward diagnostic",
    "typed premise-anchor stress diagnostic",
    "directional support-utilization diagnostic",
    "empirical diagnostic level-set mass",
    "legacy scalar reproduction",
)
TENSOR_DEPARTURE_FORBIDDEN_USE = (
    "likelihood, posterior, Bayes factor, or evidence term owned by MIO",
    "physical occupancy or anisotropic volume fraction",
    "native solver validation or native morphology atlas",
    "geometry detection or Bianchi family identification",
)
SUPPORT_CATALOGUE_STATUS = "FINITE_REGISTERED_DIRECTIONS_NOT_COMPLETE_SPHERE"
OCCUPANCY_MEASURE_KIND = "EMPIRICAL_DIAGNOSTIC_LEVEL_SET_MASS"
LEGACY_NAMES = ("x", "Q", "Pi", "F", "G_F")
_PUSHFORWARD_TOKEN = object()
_PROFILE_TOKEN = object()
_OCCUPANCY_TOKEN = object()
_LEGACY_TOKEN = object()


def _text(value: object, name: str) -> str:
    if not isinstance(value, str) or not value.strip() or value != value.strip():
        raise TensorDepartureStatisticsError(
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
        raise TensorDepartureStatisticsError(
            f"{name} must be a sequence of text"
        )
    out = tuple(_text(value, name) for value in values)
    if not out and not empty_ok:
        raise TensorDepartureStatisticsError(f"{name} must not be empty")
    if len(out) != len(set(out)):
        raise TensorDepartureStatisticsError(
            f"{name} must not contain duplicates"
        )
    return out


def _real(value: object, name: str) -> float:
    if isinstance(value, (bool, np.bool_)):
        raise TensorDepartureStatisticsError(f"{name} must not be boolean")
    if isinstance(value, (complex, np.complexfloating)):
        raise TensorDepartureStatisticsError(f"{name} must be real")
    if isinstance(value, (str, bytes, np.str_, np.bytes_)):
        raise TensorDepartureStatisticsError(f"{name} must be numeric")
    if not isinstance(value, Real):
        raise TensorDepartureStatisticsError(f"{name} must be a real number")
    out = float(value)
    if not math.isfinite(out):
        raise TensorDepartureStatisticsError(f"{name} must be finite")
    return out


def _nonnegative(value: object, name: str) -> float:
    out = _real(value, name)
    if out < 0.0:
        raise TensorDepartureStatisticsError(f"{name} must be non-negative")
    return out


def _sha256_payload(payload: object) -> str:
    encoded = json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
    ).encode("ascii")
    return f"sha256:{hashlib.sha256(encoded).hexdigest()}"


def _enum(
    value: object,
    enum_type: type[_StringEnum],
    name: str,
) -> _StringEnum:
    if isinstance(value, enum_type):
        return value
    try:
        return enum_type(str(value))
    except ValueError as exc:
        raise TensorDepartureStatisticsError(
            f"{name} must use the registered {enum_type.__name__} vocabulary"
        ) from exc


def _optional_real(value: object | None, name: str) -> float | None:
    return None if value is None else _real(value, name)


def _clone_anchor_body(body: AnchorBodySpec) -> AnchorBodySpec:
    """Replay the PR-254 constructor before using anchor geometry."""

    if type(body) is not AnchorBodySpec:
        raise TypeError("anchor must be an exact AnchorBodySpec")
    return AnchorBodySpec(
        body_id=body.body_id,
        geometry=body.geometry,
        coordinate_labels=tuple(body.coordinate_labels),
        frame=body.frame,
        normalization=body.normalization,
        perturbative_order=body.perturbative_order,
        branch=body.branch,
        premise_identity=body.premise_identity,
        blocks=tuple(
            AnchorBlockSpec(
                block_id=block.block_id,
                coordinate_indices=tuple(block.coordinate_indices),
                radius=block.radius,
                availability=block.availability,
                unavailable_reason=block.unavailable_reason,
            )
            for block in body.blocks
        ),
        quadratic_form=tuple(
            tuple(value for value in row) for row in body.quadratic_form
        ),
        halfspaces=tuple(
            PolytopeHalfspace(
                normal=tuple(halfspace.normal),
                bound=halfspace.bound,
            )
            for halfspace in body.halfspaces
        ),
        availability=body.availability,
        unavailable_reason=body.unavailable_reason,
        assumptions=tuple(body.assumptions),
        allowed_use=tuple(body.allowed_use),
        forbidden_use=tuple(body.forbidden_use),
    )


def _scalarize(
    result: TensorFunctionalResult,
    policy: ScalarizationPolicy,
) -> float | None:
    if result.value is None:
        return None
    values = np.asarray(result.value, dtype=float)
    o3_type = result.spec.o3_type
    if policy is ScalarizationPolicy.SCALAR_IDENTITY:
        if result.codomain.shape != (1,):
            raise TensorDepartureStatisticsError(
                "SCALAR_IDENTITY requires a scalar codomain"
            )
        return float(values[0])
    if policy is ScalarizationPolicy.EUCLIDEAN_NORM:
        if o3_type not in {
            FunctionalO3Type.POLAR_VECTOR,
            FunctionalO3Type.AXIAL_VECTOR,
        }:
            raise TensorDepartureStatisticsError(
                "EUCLIDEAN_NORM requires a polar or axial vector"
            )
        return float(np.linalg.norm(values))
    if (
        policy is not ScalarizationPolicy.STF_FROBENIUS_NORM
        or o3_type is not FunctionalO3Type.STF2_TENSOR
        or result.codomain.shape != (5,)
    ):
        raise TensorDepartureStatisticsError(
            "STF_FROBENIUS_NORM requires the canonical STF5 codomain"
        )
    return float(np.linalg.norm(stf5_to_matrix(tuple(values))))


def _cell_status(result: TensorFunctionalResult) -> FunctionalCellStatus:
    if result.domain.status is FunctionalDomainStatus.MISSING_COMPONENT:
        return FunctionalCellStatus.MISSING_COMPONENT
    if (
        result.domain.status is not FunctionalDomainStatus.ADMISSIBLE
        or result.admissibility.status
        is not FunctionalAdmissibilityStatus.ADMISSIBLE
    ):
        return FunctionalCellStatus.INADMISSIBLE
    if result.stress.status is FunctionalStressStatus.DEFINED:
        return FunctionalCellStatus.DEFINED
    if result.stress.status is FunctionalStressStatus.CONDITIONAL:
        return FunctionalCellStatus.CONDITIONAL_ANCHOR
    return FunctionalCellStatus.ANCHOR_UNAVAILABLE


@dataclass(frozen=True)
class CertifiedFunctionalPushforward:
    """Sample-wise typed ``x`` values and inherited ``Q`` stress fields."""

    pushforward_id: str
    functional_ids: tuple[str, ...]
    functional_spec_ids: tuple[str, ...]
    anchor_ids: tuple[str | None, ...]
    scalarization_policies: tuple[ScalarizationPolicy, ...]
    sample_state_ids: tuple[str, ...]
    input_result_ids: tuple[tuple[str, ...], ...]
    raw_sample_by_functional: tuple[
        tuple[tuple[float, ...] | None, ...], ...
    ]
    sample_by_functional: tuple[tuple[float | None, ...], ...]
    q_point_by_functional: tuple[tuple[float | None, ...], ...]
    q_bounds_by_functional: tuple[
        tuple[tuple[float, float] | None, ...], ...
    ]
    cell_statuses: tuple[tuple[FunctionalCellStatus, ...], ...]
    sign_classes: tuple[FunctionalSignClass, ...]
    occupancy_eligible_by_functional: tuple[bool, ...]
    means: tuple[float, ...] | None
    covariance: tuple[tuple[float, ...], ...] | None
    quantile_levels: tuple[float, ...]
    quantiles_by_functional: tuple[tuple[float, ...], ...] | None
    summary_status: PushforwardSummaryStatus
    transfer_source: str
    claim_ceiling: str = TENSOR_DEPARTURE_CLAIM_CEILING
    allowed_use: tuple[str, ...] = TENSOR_DEPARTURE_ALLOWED_USE
    forbidden_use: tuple[str, ...] = TENSOR_DEPARTURE_FORBIDDEN_USE
    _construction_token: InitVar[object] = None
    _identity_seal: str = field(init=False, repr=False, compare=False)

    def __post_init__(self, _construction_token: object) -> None:
        if _construction_token is not _PUSHFORWARD_TOKEN:
            raise TensorDepartureStatisticsError(
                "CertifiedFunctionalPushforward must be factory-built"
            )
        _text(self.pushforward_id, "pushforward_id")
        functional_ids = _texts(self.functional_ids, "functional_ids")
        spec_ids = _texts(self.functional_spec_ids, "functional_spec_ids")
        if len(spec_ids) != len(functional_ids):
            raise TensorDepartureStatisticsError(
                "functional_spec_ids must align with functional_ids"
            )
        policies = tuple(self.scalarization_policies)
        if (
            len(policies) != len(functional_ids)
            or any(type(value) is not ScalarizationPolicy for value in policies)
        ):
            raise TensorDepartureStatisticsError(
                "scalarization_policies must align with functional_ids"
            )
        if isinstance(self.sample_state_ids, (str, bytes)):
            raise TensorDepartureStatisticsError(
                "sample_state_ids must be a sequence of text"
            )
        sample_ids = tuple(
            _text(value, "sample_state_ids")
            for value in self.sample_state_ids
        )
        if not sample_ids:
            raise TensorDepartureStatisticsError(
                "sample_state_ids must not be empty"
            )
        width = len(functional_ids)
        height = len(sample_ids)
        matrices = (
            self.input_result_ids,
            self.raw_sample_by_functional,
            self.sample_by_functional,
            self.q_point_by_functional,
            self.q_bounds_by_functional,
            self.cell_statuses,
        )
        if any(
            len(matrix) != height
            or any(len(row) != width for row in matrix)
            for matrix in matrices
        ):
            raise TensorDepartureStatisticsError(
                "all sample-by-functional matrices must have one common shape"
            )
        if self.claim_ceiling != TENSOR_DEPARTURE_CLAIM_CEILING:
            raise TensorDepartureStatisticsError("claim ceiling drifted")
        if tuple(self.allowed_use) != TENSOR_DEPARTURE_ALLOWED_USE:
            raise TensorDepartureStatisticsError("allowed-use lane drifted")
        if tuple(self.forbidden_use) != TENSOR_DEPARTURE_FORBIDDEN_USE:
            raise TensorDepartureStatisticsError("forbidden-use lane drifted")
        if type(self.summary_status) is not PushforwardSummaryStatus:
            raise TensorDepartureStatisticsError(
                "summary_status must use the registered vocabulary"
            )
        _text(self.transfer_source, "transfer_source")
        object.__setattr__(self, "functional_ids", functional_ids)
        object.__setattr__(self, "functional_spec_ids", spec_ids)
        object.__setattr__(self, "sample_state_ids", sample_ids)
        object.__setattr__(self, "scalarization_policies", policies)
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
            "anchor_ids": list(self.anchor_ids),
            "cell_statuses": [
                [value.value for value in row] for row in self.cell_statuses
            ],
            "claim_ceiling": self.claim_ceiling,
            "covariance": (
                None
                if self.covariance is None
                else [list(row) for row in self.covariance]
            ),
            "forbidden_use": list(self.forbidden_use),
            "functional_ids": list(self.functional_ids),
            "functional_spec_ids": list(self.functional_spec_ids),
            "input_result_ids": [list(row) for row in self.input_result_ids],
            "means": None if self.means is None else list(self.means),
            "occupancy_eligible_by_functional": list(
                self.occupancy_eligible_by_functional
            ),
            "pushforward_id": self.pushforward_id,
            "q_bounds_by_functional": [
                [
                    None if value is None else list(value)
                    for value in row
                ]
                for row in self.q_bounds_by_functional
            ],
            "q_point_by_functional": [
                list(row) for row in self.q_point_by_functional
            ],
            "quantile_levels": list(self.quantile_levels),
            "quantiles_by_functional": (
                None
                if self.quantiles_by_functional is None
                else [list(row) for row in self.quantiles_by_functional]
            ),
            "raw_sample_by_functional": [
                [
                    None if value is None else list(value)
                    for value in row
                ]
                for row in self.raw_sample_by_functional
            ],
            "sample_by_functional": [
                list(row) for row in self.sample_by_functional
            ],
            "sample_state_ids": list(self.sample_state_ids),
            "scalarization_policies": [
                value.value for value in self.scalarization_policies
            ],
            "schema": "HTT_CERTIFIED_FUNCTIONAL_PUSHFORWARD_V1",
            "sign_classes": [value.value for value in self.sign_classes],
            "summary_status": self.summary_status.value,
            "transfer_source": self.transfer_source,
        }

    def _assert_identity_sealed(self) -> None:
        if (
            not hasattr(self, "_identity_seal")
            or _sha256_payload(self._payload_unchecked())
            != self._identity_seal
        ):
            raise TensorDepartureStatisticsError(
                "functional pushforward identity drifted after construction"
            )

    def as_payload(self) -> dict[str, object]:
        self._assert_identity_sealed()
        payload = self._payload_unchecked()
        payload["content_id"] = self._identity_seal
        return payload


def build_certified_functional_pushforward(
    *,
    pushforward_id: str,
    samples: Sequence[Sequence[TensorFunctionalResult]],
    scalarization_policies: Mapping[
        str, ScalarizationPolicy | str
    ],
    quantile_levels: Sequence[float] = (0.05, 0.5, 0.95),
) -> CertifiedFunctionalPushforward:
    """Build sample-wise ``x`` and inherited ``Q`` without ratio-of-means."""

    _text(pushforward_id, "pushforward_id")
    if isinstance(samples, (str, bytes)):
        raise TensorDepartureStatisticsError("samples must be a matrix")
    rows = tuple(tuple(row) for row in samples)
    if not rows or not rows[0]:
        raise TensorDepartureStatisticsError(
            "samples must contain at least one non-empty row"
        )
    width = len(rows[0])
    if any(len(row) != width for row in rows):
        raise TensorDepartureStatisticsError("samples must be rectangular")
    if any(type(result) is not TensorFunctionalResult for row in rows for result in row):
        raise TypeError(
            "samples must contain exact TensorFunctionalResult instances"
        )

    first = rows[0]
    functional_ids = tuple(result.spec.functional_id for result in first)
    if len(functional_ids) != len(set(functional_ids)):
        raise TensorDepartureStatisticsError(
            "one sample row must not repeat a functional_id"
        )
    spec_ids = tuple(result.spec.spec_id for result in first)
    if any(
        tuple(result.spec.spec_id for result in row) != spec_ids
        for row in rows[1:]
    ):
        raise TensorDepartureStatisticsError(
            "every sample must use the same ordered functional specs"
        )
    if set(scalarization_policies) != set(functional_ids):
        raise TensorDepartureStatisticsError(
            "scalarization policies must be preregistered for every functional"
        )
    policies = tuple(
        _enum(
            scalarization_policies[functional_id],
            ScalarizationPolicy,
            f"scalarization_policies[{functional_id}]",
        )
        for functional_id in functional_ids
    )

    transfer_sources = {
        result.transfer_source for row in rows for result in row
    }
    if len(transfer_sources) != 1:
        raise TensorDepartureStatisticsError(
            "transfer_source must be uniform across the pushforward"
        )
    state_ids = tuple(row[0].source_state_id for row in rows)
    if any(
        any(result.source_state_id != state_ids[index] for result in row)
        for index, row in enumerate(rows)
    ):
        raise TensorDepartureStatisticsError(
            "one sample row must come from one joint state"
        )
    anchor_ids = tuple(
        result.stress.anchor_id or result.spec.anchor_id for result in first
    )
    if any(
        tuple(
            result.stress.anchor_id or result.spec.anchor_id
            for result in row
        )
        != anchor_ids
        for row in rows[1:]
    ):
        raise TensorDepartureStatisticsError(
            "anchor identities must not drift across samples"
        )

    raw_rows: list[tuple[tuple[float, ...] | None, ...]] = []
    x_rows: list[tuple[float | None, ...]] = []
    q_rows: list[tuple[float | None, ...]] = []
    q_bound_rows: list[tuple[tuple[float, float] | None, ...]] = []
    status_rows: list[tuple[FunctionalCellStatus, ...]] = []
    result_id_rows: list[tuple[str, ...]] = []
    for row in rows:
        raw: list[tuple[float, ...] | None] = []
        x_values: list[float | None] = []
        q_values: list[float | None] = []
        q_bounds: list[tuple[float, float] | None] = []
        statuses: list[FunctionalCellStatus] = []
        result_ids: list[str] = []
        for result, policy in zip(row, policies, strict=True):
            result.spec.to_payload()
            result_ids.append(result.result_id)
            raw.append(result.value)
            x_values.append(_scalarize(result, policy))
            statuses.append(_cell_status(result))
            if result.stress.status is FunctionalStressStatus.DEFINED:
                assert result.stress.point_estimate is not None
                point = float(result.stress.point_estimate)
                q_values.append(point)
                q_bounds.append((point, point))
            elif result.stress.status is FunctionalStressStatus.CONDITIONAL:
                assert (
                    result.stress.lower is not None
                    and result.stress.upper is not None
                )
                q_values.append(None)
                q_bounds.append(
                    (
                        float(result.stress.lower),
                        float(result.stress.upper),
                    )
                )
            else:
                q_values.append(None)
                q_bounds.append(None)
        raw_rows.append(tuple(raw))
        x_rows.append(tuple(x_values))
        q_rows.append(tuple(q_values))
        q_bound_rows.append(tuple(q_bounds))
        status_rows.append(tuple(statuses))
        result_id_rows.append(tuple(result_ids))

    levels = tuple(
        _nonnegative(value, f"quantile_levels[{index}]")
        for index, value in enumerate(quantile_levels)
    )
    if (
        not levels
        or tuple(sorted(set(levels))) != levels
        or any(value > 1.0 for value in levels)
    ):
        raise TensorDepartureStatisticsError(
            "quantile_levels must be unique, sorted, and in [0, 1]"
        )
    complete = all(value is not None for row in x_rows for value in row)
    if not complete:
        means = None
        covariance = None
        quantiles = None
        summary_status = PushforwardSummaryStatus.PARTIAL_MISSING
    else:
        matrix = np.asarray(x_rows, dtype=float)
        means = tuple(float(value) for value in np.mean(matrix, axis=0))
        quantile_matrix = np.quantile(matrix, levels, axis=0)
        quantiles = tuple(
            tuple(float(value) for value in quantile_matrix[:, column])
            for column in range(width)
        )
        if matrix.shape[0] < 2:
            covariance = None
            summary_status = PushforwardSummaryStatus.INSUFFICIENT_SAMPLES
        else:
            cov = np.atleast_2d(np.cov(matrix, rowvar=False, ddof=1))
            covariance = tuple(
                tuple(float(value) for value in row) for row in cov
            )
            summary_status = PushforwardSummaryStatus.DEFINED

    return CertifiedFunctionalPushforward(
        pushforward_id=pushforward_id,
        functional_ids=functional_ids,
        functional_spec_ids=spec_ids,
        anchor_ids=anchor_ids,
        scalarization_policies=policies,  # type: ignore[arg-type]
        sample_state_ids=state_ids,
        input_result_ids=tuple(result_id_rows),
        raw_sample_by_functional=tuple(raw_rows),
        sample_by_functional=tuple(x_rows),
        q_point_by_functional=tuple(q_rows),
        q_bounds_by_functional=tuple(q_bound_rows),
        cell_statuses=tuple(status_rows),
        sign_classes=tuple(result.spec.sign_class for result in first),
        occupancy_eligible_by_functional=tuple(
            all(result.admissibility.occupancy_eligible for result in column)
            for column in zip(*rows, strict=True)
        ),
        means=means,
        covariance=covariance,
        quantile_levels=levels,
        quantiles_by_functional=quantiles,
        summary_status=summary_status,
        transfer_source=next(iter(transfer_sources)),
        _construction_token=_PUSHFORWARD_TOKEN,
    )


def _vector_channel(vector: AnchorVector) -> tuple[object, ...]:
    return (
        vector.coordinate_labels,
        vector.frame,
        vector.normalization,
        vector.perturbative_order,
        vector.branch,
    )


def _anchor_support(
    body: AnchorBodySpec,
    direction: np.ndarray,
) -> tuple[float | None, tuple[str, ...], np.ndarray | None]:
    """Return support, active geometry labels, and one maximizing point."""

    if body.availability is not AnchorAvailability.AVAILABLE:
        return None, (), None
    if body.geometry is AnchorGeometryKind.PRODUCT_BLOCK_BALL:
        if any(
            block.availability is not AnchorAvailability.AVAILABLE
            for block in body.blocks
        ):
            return None, (), None
        support = 0.0
        active: list[str] = []
        maximizer = np.zeros_like(direction)
        for block in body.blocks:
            indices = list(block.coordinate_indices)
            piece = direction[indices]
            norm = float(np.linalg.norm(piece))
            assert block.radius is not None
            support += float(block.radius) * norm
            if norm > 0.0:
                active.append(block.block_id)
                maximizer[indices] = float(block.radius) * piece / norm
        return support, tuple(active), maximizer
    if body.geometry is AnchorGeometryKind.ELLIPSOID:
        quadratic = np.asarray(body.quadratic_form, dtype=float)
        inverse = np.linalg.inv(quadratic)
        squared = max(float(direction @ inverse @ direction), 0.0)
        support = math.sqrt(squared)
        maximizer = (
            np.zeros_like(direction)
            if support == 0.0
            else inverse @ direction / support
        )
        return support, ("ellipsoid",) if support > 0.0 else (), maximizer

    normals = np.asarray(
        [halfspace.normal for halfspace in body.halfspaces],
        dtype=float,
    )
    bounds = np.asarray(
        [halfspace.bound for halfspace in body.halfspaces],
        dtype=float,
    )
    solution = linprog(
        -direction,
        A_ub=normals,
        b_ub=bounds,
        bounds=[(None, None)] * direction.size,
        method="highs",
    )
    if not solution.success or solution.x is None:
        raise TensorDepartureStatisticsError(
            "registered bounded polytope support optimization failed"
        )
    maximizer = np.asarray(solution.x, dtype=float)
    support = float(direction @ maximizer)
    slack = bounds - normals @ maximizer
    active = tuple(
        f"halfspace:{index}"
        for index, value in enumerate(slack)
        if abs(float(value)) <= 1e-9 * max(1.0, float(bounds[index]))
    )
    return support, active, maximizer


def _witness_directions(
    body: AnchorBodySpec,
    point: np.ndarray,
    gauge: float,
) -> tuple[tuple[tuple[float, ...], str], ...]:
    if gauge == 0.0:
        return ((tuple(0.0 for _ in point), "zero-point"),)
    if body.geometry is AnchorGeometryKind.PRODUCT_BLOCK_BALL:
        witnesses = []
        for block in body.blocks:
            assert block.radius is not None
            indices = list(block.coordinate_indices)
            piece = point[indices]
            block_gauge = float(np.linalg.norm(piece)) / float(block.radius)
            if math.isclose(block_gauge, gauge, rel_tol=1e-12, abs_tol=1e-14):
                direction = np.zeros_like(point)
                direction[indices] = piece / float(block.radius) ** 2
                witnesses.append((tuple(float(v) for v in direction), block.block_id))
        return tuple(witnesses)
    if body.geometry is AnchorGeometryKind.ELLIPSOID:
        direction = np.asarray(body.quadratic_form, dtype=float) @ point
        return ((tuple(float(value) for value in direction), "ellipsoid"),)
    values = tuple(
        float(np.dot(halfspace.normal, point)) / float(halfspace.bound)
        for halfspace in body.halfspaces
    )
    return tuple(
        (
            tuple(float(value) for value in body.halfspaces[index].normal),
            f"halfspace:{index}",
        )
        for index, value in enumerate(values)
        if math.isclose(value, gauge, rel_tol=1e-12, abs_tol=1e-14)
    )


@dataclass(frozen=True)
class SupportUtilizationProfile:
    """Directional support ratios plus an exact finite-set/anchor maximum."""

    identified_set_id: str
    anchor_id: str
    status: SupportUtilizationStatus
    point_ids: tuple[str, ...]
    direction_ids: tuple[str, ...]
    signed_support_ratios: tuple[float | None, ...]
    antipodal_support_ratios: tuple[float | None, ...]
    identified_supports: tuple[float | None, ...]
    antipodal_identified_supports: tuple[float | None, ...]
    anchor_supports: tuple[float | None, ...]
    directional_statuses: tuple[DirectionalRatioStatus, ...]
    active_blocks_by_direction: tuple[tuple[str, ...], ...]
    maximum_registered_utilization: float | None
    maximum_utilization: float | None
    witness_point_ids: tuple[str, ...]
    witness_directions: tuple[tuple[float, ...], ...]
    active_blocks: tuple[str, ...]
    direction_catalogue_status: str = SUPPORT_CATALOGUE_STATUS
    claim_ceiling: str = TENSOR_DEPARTURE_CLAIM_CEILING
    allowed_use: tuple[str, ...] = TENSOR_DEPARTURE_ALLOWED_USE
    forbidden_use: tuple[str, ...] = TENSOR_DEPARTURE_FORBIDDEN_USE
    reasons: tuple[str, ...] = ()
    _construction_token: InitVar[object] = None
    _identity_seal: str = field(init=False, repr=False, compare=False)

    def __post_init__(self, _construction_token: object) -> None:
        if _construction_token is not _PROFILE_TOKEN:
            raise TensorDepartureStatisticsError(
                "SupportUtilizationProfile must be factory-built"
            )
        _text(self.identified_set_id, "identified_set_id")
        _text(self.anchor_id, "anchor_id")
        point_ids = _texts(self.point_ids, "point_ids", empty_ok=True)
        direction_ids = _texts(
            self.direction_ids, "direction_ids", empty_ok=True
        )
        width = len(direction_ids)
        directional_fields = (
            self.signed_support_ratios,
            self.antipodal_support_ratios,
            self.identified_supports,
            self.antipodal_identified_supports,
            self.anchor_supports,
            self.directional_statuses,
            self.active_blocks_by_direction,
        )
        if any(len(values) != width for values in directional_fields):
            raise TensorDepartureStatisticsError(
                "directional profile fields must align"
            )
        if type(self.status) is not SupportUtilizationStatus:
            raise TensorDepartureStatisticsError(
                "status must use SupportUtilizationStatus"
            )
        if self.direction_catalogue_status != SUPPORT_CATALOGUE_STATUS:
            raise TensorDepartureStatisticsError(
                "finite direction catalogue must not claim completeness"
            )
        if self.claim_ceiling != TENSOR_DEPARTURE_CLAIM_CEILING:
            raise TensorDepartureStatisticsError("claim ceiling drifted")
        if tuple(self.allowed_use) != TENSOR_DEPARTURE_ALLOWED_USE:
            raise TensorDepartureStatisticsError("allowed-use lane drifted")
        if tuple(self.forbidden_use) != TENSOR_DEPARTURE_FORBIDDEN_USE:
            raise TensorDepartureStatisticsError("forbidden-use lane drifted")
        object.__setattr__(self, "point_ids", point_ids)
        object.__setattr__(self, "direction_ids", direction_ids)
        object.__setattr__(
            self,
            "reasons",
            _texts(self.reasons, "reasons", empty_ok=True),
        )
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
            "active_blocks": list(self.active_blocks),
            "active_blocks_by_direction": [
                list(values) for values in self.active_blocks_by_direction
            ],
            "allowed_use": list(self.allowed_use),
            "anchor_id": self.anchor_id,
            "anchor_supports": list(self.anchor_supports),
            "antipodal_identified_supports": list(
                self.antipodal_identified_supports
            ),
            "antipodal_support_ratios": list(
                self.antipodal_support_ratios
            ),
            "claim_ceiling": self.claim_ceiling,
            "direction_catalogue_status": self.direction_catalogue_status,
            "direction_ids": list(self.direction_ids),
            "directional_statuses": [
                value.value for value in self.directional_statuses
            ],
            "forbidden_use": list(self.forbidden_use),
            "identified_set_id": self.identified_set_id,
            "identified_supports": list(self.identified_supports),
            "maximum_registered_utilization": (
                self.maximum_registered_utilization
            ),
            "maximum_utilization": self.maximum_utilization,
            "point_ids": list(self.point_ids),
            "reasons": list(self.reasons),
            "schema": "HTT_SUPPORT_UTILIZATION_PROFILE_V1",
            "signed_support_ratios": list(self.signed_support_ratios),
            "status": self.status.value,
            "witness_directions": [
                list(values) for values in self.witness_directions
            ],
            "witness_point_ids": list(self.witness_point_ids),
        }

    def _assert_identity_sealed(self) -> None:
        if (
            not hasattr(self, "_identity_seal")
            or _sha256_payload(self._payload_unchecked())
            != self._identity_seal
        ):
            raise TensorDepartureStatisticsError(
                "support-utilization identity drifted after construction"
            )

    def as_payload(self) -> dict[str, object]:
        self._assert_identity_sealed()
        payload = self._payload_unchecked()
        payload["content_id"] = self._identity_seal
        return payload


def build_support_utilization_profile(
    *,
    identified_set_id: str,
    identified_points: Sequence[AnchorVector],
    anchor: AnchorBodySpec,
    directions: Sequence[AnchorVector],
    denominator_tolerance: float = 1e-12,
    missing_reason: str | None = None,
) -> SupportUtilizationProfile:
    """Evaluate support ratios without treating a finite grid as complete."""

    _text(identified_set_id, "identified_set_id")
    tolerance = _nonnegative(
        denominator_tolerance, "denominator_tolerance"
    )
    body = _clone_anchor_body(anchor)
    if isinstance(identified_points, (str, bytes)) or isinstance(
        directions, (str, bytes)
    ):
        raise TensorDepartureStatisticsError(
            "identified_points and directions must be sequences"
        )
    points = tuple(identified_points)
    registered_directions = tuple(directions)
    if any(type(value) is not AnchorVector for value in (*points, *registered_directions)):
        raise TypeError(
            "identified_points and directions must contain exact AnchorVector values"
        )
    if len({point.vector_id for point in points}) != len(points):
        raise TensorDepartureStatisticsError(
            "identified point vector_id values must be unique"
        )
    if len({direction.vector_id for direction in registered_directions}) != len(
        registered_directions
    ):
        raise TensorDepartureStatisticsError(
            "direction vector_id values must be unique"
        )
    if missing_reason is not None:
        _text(missing_reason, "missing_reason")
        if points:
            raise TensorDepartureStatisticsError(
                "missing_reason requires an empty identified point set"
            )
    elif not points:
        raise TensorDepartureStatisticsError(
            "empty identified set requires a typed missing_reason"
        )

    channel_values = (*points, *registered_directions)
    mismatch = any(_vector_channel(value) != body.channel_key for value in channel_values)
    unavailable = (
        body.availability is not AnchorAvailability.AVAILABLE
        or (
            body.geometry is AnchorGeometryKind.PRODUCT_BLOCK_BALL
            and any(
                block.availability is not AnchorAvailability.AVAILABLE
                for block in body.blocks
            )
        )
    )
    if missing_reason is not None or mismatch or unavailable:
        if missing_reason is not None:
            status = SupportUtilizationStatus.MISSING_IDENTIFIED_SET
            reason = missing_reason
            direction_status = DirectionalRatioStatus.ANCHOR_UNAVAILABLE
        elif mismatch:
            status = SupportUtilizationStatus.CHANNEL_MISMATCH
            reason = "identified points or directions do not match anchor channel"
            direction_status = DirectionalRatioStatus.CHANNEL_MISMATCH
        else:
            status = SupportUtilizationStatus.ANCHOR_UNAVAILABLE
            reason = "anchor or one required anchor block is unavailable"
            direction_status = DirectionalRatioStatus.ANCHOR_UNAVAILABLE
        width = len(registered_directions)
        return SupportUtilizationProfile(
            identified_set_id=identified_set_id,
            anchor_id=body.body_id,
            status=status,
            point_ids=tuple(point.vector_id for point in points),
            direction_ids=tuple(
                direction.vector_id for direction in registered_directions
            ),
            signed_support_ratios=(None,) * width,
            antipodal_support_ratios=(None,) * width,
            identified_supports=(None,) * width,
            antipodal_identified_supports=(None,) * width,
            anchor_supports=(None,) * width,
            directional_statuses=(direction_status,) * width,
            active_blocks_by_direction=((),) * width,
            maximum_registered_utilization=None,
            maximum_utilization=None,
            witness_point_ids=(),
            witness_directions=(),
            active_blocks=(),
            reasons=(reason,),
            _construction_token=_PROFILE_TOKEN,
        )

    point_matrix = np.asarray([point.values for point in points], dtype=float)
    signed_ratios: list[float | None] = []
    antipodal_ratios: list[float | None] = []
    identified_supports: list[float | None] = []
    antipodal_supports: list[float | None] = []
    anchor_supports: list[float | None] = []
    directional_statuses: list[DirectionalRatioStatus] = []
    active_by_direction: list[tuple[str, ...]] = []
    for direction in registered_directions:
        u = np.asarray(direction.values, dtype=float)
        h_anchor, active, _ = _anchor_support(body, u)
        h_identified = float(np.max(point_matrix @ u))
        h_antipodal = float(np.max(point_matrix @ (-u)))
        identified_supports.append(h_identified)
        antipodal_supports.append(h_antipodal)
        anchor_supports.append(h_anchor)
        active_by_direction.append(active)
        if h_anchor is None:
            signed_ratios.append(None)
            antipodal_ratios.append(None)
            directional_statuses.append(
                DirectionalRatioStatus.ANCHOR_UNAVAILABLE
            )
        elif h_anchor <= tolerance:
            signed_ratios.append(None)
            antipodal_ratios.append(None)
            directional_statuses.append(
                DirectionalRatioStatus.DENOMINATOR_COLLAPSE
            )
        else:
            signed_ratios.append(h_identified / h_anchor)
            antipodal_ratios.append(
                max(h_identified, h_antipodal) / h_anchor
            )
            directional_statuses.append(DirectionalRatioStatus.DEFINED)

    gauges: list[float] = []
    for point in points:
        report = evaluate_anchor_gauge(body, point)
        if (
            report.status is not AnchorGaugeStatus.DEFINED
            or report.lower is None
        ):
            raise TensorDepartureStatisticsError(
                "anchor replay did not produce a defined point gauge"
            )
        gauges.append(float(report.lower))
    maximum = max(gauges)
    witness_indices = tuple(
        index
        for index, value in enumerate(gauges)
        if math.isclose(value, maximum, rel_tol=1e-12, abs_tol=1e-14)
    )
    witnesses: list[tuple[float, ...]] = []
    active_blocks: list[str] = []
    witness_point_ids: list[str] = []
    for index in witness_indices:
        for direction, active in _witness_directions(
            body, point_matrix[index], maximum
        ):
            witnesses.append(direction)
            active_blocks.append(active)
            witness_point_ids.append(points[index].vector_id)

    defined_registered = tuple(
        value
        for value in antipodal_ratios
        if value is not None
    )
    collapsed = any(
        value is DirectionalRatioStatus.DENOMINATOR_COLLAPSE
        for value in directional_statuses
    )
    return SupportUtilizationProfile(
        identified_set_id=identified_set_id,
        anchor_id=body.body_id,
        status=(
            SupportUtilizationStatus.PARTIAL_DENOMINATOR_COLLAPSE
            if collapsed
            else SupportUtilizationStatus.DEFINED
        ),
        point_ids=tuple(point.vector_id for point in points),
        direction_ids=tuple(
            direction.vector_id for direction in registered_directions
        ),
        signed_support_ratios=tuple(signed_ratios),
        antipodal_support_ratios=tuple(antipodal_ratios),
        identified_supports=tuple(identified_supports),
        antipodal_identified_supports=tuple(antipodal_supports),
        anchor_supports=tuple(anchor_supports),
        directional_statuses=tuple(directional_statuses),
        active_blocks_by_direction=tuple(active_by_direction),
        maximum_registered_utilization=(
            max(defined_registered) if defined_registered else None
        ),
        maximum_utilization=maximum,
        witness_point_ids=tuple(witness_point_ids),
        witness_directions=tuple(witnesses),
        active_blocks=tuple(active_blocks),
        reasons=(
            ("one or more registered directions had collapsed anchor support",)
            if collapsed
            else ()
        ),
        _construction_token=_PROFILE_TOKEN,
    )


@dataclass(frozen=True)
class OccupancyMeasure:
    """Empirical mass of eligible diagnostic samples above registered levels."""

    measure_id: str
    source_pushforward_id: str
    functional_id: str
    status: OccupancyMeasureStatus
    thresholds: tuple[float, ...]
    empirical_level_set_mass: tuple[float, ...] | None
    eligible_sample_count: int
    total_sample_count: int
    measure_kind: str = OCCUPANCY_MEASURE_KIND
    claim_ceiling: str = TENSOR_DEPARTURE_CLAIM_CEILING
    allowed_use: tuple[str, ...] = TENSOR_DEPARTURE_ALLOWED_USE
    forbidden_use: tuple[str, ...] = TENSOR_DEPARTURE_FORBIDDEN_USE
    reasons: tuple[str, ...] = ()
    _construction_token: InitVar[object] = None
    _identity_seal: str = field(init=False, repr=False, compare=False)

    def __post_init__(self, _construction_token: object) -> None:
        if _construction_token is not _OCCUPANCY_TOKEN:
            raise TensorDepartureStatisticsError(
                "OccupancyMeasure must be factory-built"
            )
        for name in ("measure_id", "source_pushforward_id", "functional_id"):
            _text(getattr(self, name), name)
        if type(self.status) is not OccupancyMeasureStatus:
            raise TensorDepartureStatisticsError(
                "status must use OccupancyMeasureStatus"
            )
        thresholds = tuple(
            _nonnegative(value, f"thresholds[{index}]")
            for index, value in enumerate(self.thresholds)
        )
        if not thresholds or tuple(sorted(set(thresholds))) != thresholds:
            raise TensorDepartureStatisticsError(
                "thresholds must be unique and sorted"
            )
        if self.measure_kind != OCCUPANCY_MEASURE_KIND:
            raise TensorDepartureStatisticsError("measure kind drifted")
        if self.claim_ceiling != TENSOR_DEPARTURE_CLAIM_CEILING:
            raise TensorDepartureStatisticsError("claim ceiling drifted")
        if tuple(self.allowed_use) != TENSOR_DEPARTURE_ALLOWED_USE:
            raise TensorDepartureStatisticsError("allowed-use lane drifted")
        if tuple(self.forbidden_use) != TENSOR_DEPARTURE_FORBIDDEN_USE:
            raise TensorDepartureStatisticsError("forbidden-use lane drifted")
        object.__setattr__(self, "thresholds", thresholds)
        object.__setattr__(
            self,
            "reasons",
            _texts(self.reasons, "reasons", empty_ok=True),
        )
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
            "eligible_sample_count": self.eligible_sample_count,
            "empirical_level_set_mass": (
                None
                if self.empirical_level_set_mass is None
                else list(self.empirical_level_set_mass)
            ),
            "forbidden_use": list(self.forbidden_use),
            "functional_id": self.functional_id,
            "measure_id": self.measure_id,
            "measure_kind": self.measure_kind,
            "reasons": list(self.reasons),
            "schema": "HTT_OCCUPANCY_MEASURE_V1",
            "source_pushforward_id": self.source_pushforward_id,
            "status": self.status.value,
            "thresholds": list(self.thresholds),
            "total_sample_count": self.total_sample_count,
        }

    def _assert_identity_sealed(self) -> None:
        if (
            not hasattr(self, "_identity_seal")
            or _sha256_payload(self._payload_unchecked())
            != self._identity_seal
        ):
            raise TensorDepartureStatisticsError(
                "occupancy-measure identity drifted after construction"
            )

    def as_payload(self) -> dict[str, object]:
        self._assert_identity_sealed()
        payload = self._payload_unchecked()
        payload["content_id"] = self._identity_seal
        return payload


def build_occupancy_measure(
    *,
    measure_id: str,
    pushforward: CertifiedFunctionalPushforward,
    functional_id: str,
    thresholds: Sequence[float],
) -> OccupancyMeasure:
    """Build an empirical diagnostic mass; never impute missing cells as zero."""

    if type(pushforward) is not CertifiedFunctionalPushforward:
        raise TypeError(
            "pushforward must be an exact CertifiedFunctionalPushforward"
        )
    pushforward.as_payload()
    _text(measure_id, "measure_id")
    _text(functional_id, "functional_id")
    try:
        index = pushforward.functional_ids.index(functional_id)
    except ValueError as exc:
        raise TensorDepartureStatisticsError(
            "functional_id is not present in the pushforward"
        ) from exc
    checked_thresholds = tuple(
        _nonnegative(value, f"thresholds[{offset}]")
        for offset, value in enumerate(thresholds)
    )
    total = len(pushforward.sample_state_ids)
    if (
        pushforward.sign_classes[index]
        is not FunctionalSignClass.SIGN_DEFINITE
        or not pushforward.occupancy_eligible_by_functional[index]
    ):
        return OccupancyMeasure(
            measure_id=measure_id,
            source_pushforward_id=pushforward.content_id,
            functional_id=functional_id,
            status=OccupancyMeasureStatus.INELIGIBLE_FUNCTIONAL,
            thresholds=checked_thresholds,
            empirical_level_set_mass=None,
            eligible_sample_count=0,
            total_sample_count=total,
            reasons=(
                "occupancy requires a sign-definite functional with an eligible anchor",
            ),
            _construction_token=_OCCUPANCY_TOKEN,
        )
    q_values = tuple(
        row[index] for row in pushforward.q_point_by_functional
    )
    if any(value is None for value in q_values):
        return OccupancyMeasure(
            measure_id=measure_id,
            source_pushforward_id=pushforward.content_id,
            functional_id=functional_id,
            status=OccupancyMeasureStatus.MISSING_OR_UNAVAILABLE_SUPPORT,
            thresholds=checked_thresholds,
            empirical_level_set_mass=None,
            eligible_sample_count=sum(value is not None for value in q_values),
            total_sample_count=total,
            reasons=(
                "missing or conditional anchor cells are not imputed as unoccupied",
            ),
            _construction_token=_OCCUPANCY_TOKEN,
        )
    numeric = tuple(float(value) for value in q_values if value is not None)
    masses = tuple(
        math.fsum(value >= threshold for value in numeric) / len(numeric)
        for threshold in checked_thresholds
    )
    return OccupancyMeasure(
        measure_id=measure_id,
        source_pushforward_id=pushforward.content_id,
        functional_id=functional_id,
        status=OccupancyMeasureStatus.DEFINED,
        thresholds=checked_thresholds,
        empirical_level_set_mass=masses,
        eligible_sample_count=len(numeric),
        total_sample_count=total,
        _construction_token=_OCCUPANCY_TOKEN,
    )


@dataclass(frozen=True)
class LegacyXQPiFGView:
    """Compatibility report; it changes no historical value or meaning."""

    view_id: str
    names: tuple[str, ...]
    legacy_values: tuple[float | None, ...]
    successor_values: tuple[float | None, ...]
    statuses: tuple[LegacyCompatibilityStatus, ...]
    absolute_deltas: tuple[float | None, ...]
    tolerance: float
    source_identity: str
    claim_ceiling: str = TENSOR_DEPARTURE_CLAIM_CEILING
    allowed_use: tuple[str, ...] = TENSOR_DEPARTURE_ALLOWED_USE
    forbidden_use: tuple[str, ...] = TENSOR_DEPARTURE_FORBIDDEN_USE
    _construction_token: InitVar[object] = None
    _identity_seal: str = field(init=False, repr=False, compare=False)

    def __post_init__(self, _construction_token: object) -> None:
        if _construction_token is not _LEGACY_TOKEN:
            raise TensorDepartureStatisticsError(
                "LegacyXQPiFGView must be factory-built"
            )
        _text(self.view_id, "view_id")
        _text(self.source_identity, "source_identity")
        if tuple(self.names) != LEGACY_NAMES:
            raise TensorDepartureStatisticsError(
                "legacy names must preserve x, Q, Pi, F, G_F order"
            )
        width = len(LEGACY_NAMES)
        if any(
            len(values) != width
            for values in (
                self.legacy_values,
                self.successor_values,
                self.statuses,
                self.absolute_deltas,
            )
        ):
            raise TensorDepartureStatisticsError(
                "legacy compatibility fields must align"
            )
        object.__setattr__(
            self, "tolerance", _nonnegative(self.tolerance, "tolerance")
        )
        if self.claim_ceiling != TENSOR_DEPARTURE_CLAIM_CEILING:
            raise TensorDepartureStatisticsError("claim ceiling drifted")
        if tuple(self.allowed_use) != TENSOR_DEPARTURE_ALLOWED_USE:
            raise TensorDepartureStatisticsError("allowed-use lane drifted")
        if tuple(self.forbidden_use) != TENSOR_DEPARTURE_FORBIDDEN_USE:
            raise TensorDepartureStatisticsError("forbidden-use lane drifted")
        object.__setattr__(
            self,
            "_identity_seal",
            _sha256_payload(self._payload_unchecked()),
        )

    @property
    def all_available_successors_match(self) -> bool:
        self._assert_identity_sealed()
        return all(
            status
            in {
                LegacyCompatibilityStatus.MATCHED,
                LegacyCompatibilityStatus.PRESERVED_PENDING_TYPED_SUCCESSOR,
                LegacyCompatibilityStatus.UNAVAILABLE,
            }
            for status in self.statuses
        )

    @property
    def content_id(self) -> str:
        self._assert_identity_sealed()
        return self._identity_seal

    def _payload_unchecked(self) -> dict[str, object]:
        return {
            "absolute_deltas": list(self.absolute_deltas),
            "allowed_use": list(self.allowed_use),
            "claim_ceiling": self.claim_ceiling,
            "forbidden_use": list(self.forbidden_use),
            "legacy_values": list(self.legacy_values),
            "names": list(self.names),
            "schema": "HTT_LEGACY_XQPI_FG_VIEW_V1",
            "source_identity": self.source_identity,
            "statuses": [value.value for value in self.statuses],
            "successor_values": list(self.successor_values),
            "tolerance": self.tolerance,
            "view_id": self.view_id,
        }

    def _assert_identity_sealed(self) -> None:
        if (
            not hasattr(self, "_identity_seal")
            or _sha256_payload(self._payload_unchecked())
            != self._identity_seal
        ):
            raise TensorDepartureStatisticsError(
                "legacy compatibility view drifted after construction"
            )

    def as_payload(self) -> dict[str, object]:
        self._assert_identity_sealed()
        payload = self._payload_unchecked()
        payload["content_id"] = self._identity_seal
        return payload


def build_legacy_xqpi_fg_view(
    *,
    view_id: str,
    legacy_values: Mapping[str, float | None],
    successor_values: Mapping[str, float | None],
    tolerance: float,
    source_identity: str,
) -> LegacyXQPiFGView:
    """Compare available scalar successors and preserve pending lanes."""

    if set(legacy_values) != set(LEGACY_NAMES):
        raise TensorDepartureStatisticsError(
            "legacy_values must contain exactly x, Q, Pi, F, and G_F"
        )
    if set(successor_values) != set(LEGACY_NAMES):
        raise TensorDepartureStatisticsError(
            "successor_values must contain exactly x, Q, Pi, F, and G_F"
        )
    if successor_values["Pi"] is not None or successor_values["G_F"] is not None:
        raise TensorDepartureStatisticsError(
            "Pi and G_F typed successors remain unavailable until PR-265 "
            "and PR-266"
        )
    checked_tolerance = _nonnegative(tolerance, "tolerance")
    legacy = tuple(
        _optional_real(legacy_values[name], f"legacy_values[{name}]")
        for name in LEGACY_NAMES
    )
    successor = tuple(
        _optional_real(successor_values[name], f"successor_values[{name}]")
        for name in LEGACY_NAMES
    )
    statuses: list[LegacyCompatibilityStatus] = []
    deltas: list[float | None] = []
    for name, old, new in zip(LEGACY_NAMES, legacy, successor, strict=True):
        if old is None:
            statuses.append(LegacyCompatibilityStatus.UNAVAILABLE)
            deltas.append(None)
        elif new is None:
            statuses.append(
                LegacyCompatibilityStatus.PRESERVED_PENDING_TYPED_SUCCESSOR
            )
            deltas.append(None)
        else:
            delta = abs(old - new)
            deltas.append(delta)
            statuses.append(
                LegacyCompatibilityStatus.MATCHED
                if delta <= checked_tolerance
                else LegacyCompatibilityStatus.MISMATCH
            )
    return LegacyXQPiFGView(
        view_id=view_id,
        names=LEGACY_NAMES,
        legacy_values=legacy,
        successor_values=successor,
        statuses=tuple(statuses),
        absolute_deltas=tuple(deltas),
        tolerance=checked_tolerance,
        source_identity=source_identity,
        _construction_token=_LEGACY_TOKEN,
    )


__all__ = [
    "CertifiedFunctionalPushforward",
    "DirectionalRatioStatus",
    "FunctionalCellStatus",
    "LegacyCompatibilityStatus",
    "LegacyXQPiFGView",
    "OCCUPANCY_MEASURE_KIND",
    "OccupancyMeasure",
    "OccupancyMeasureStatus",
    "PushforwardSummaryStatus",
    "SUPPORT_CATALOGUE_STATUS",
    "ScalarizationPolicy",
    "SupportUtilizationProfile",
    "SupportUtilizationStatus",
    "TENSOR_DEPARTURE_ALLOWED_USE",
    "TENSOR_DEPARTURE_CLAIM_CEILING",
    "TENSOR_DEPARTURE_FORBIDDEN_USE",
    "TensorDepartureStatisticsError",
    "build_certified_functional_pushforward",
    "build_legacy_xqpi_fg_view",
    "build_occupancy_measure",
    "build_support_utilization_profile",
]
