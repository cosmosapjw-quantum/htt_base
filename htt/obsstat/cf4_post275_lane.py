"""Synthetic-only CF4 operator contracts for PR-291 preactivation.

This module owns observer-side feature algebra only.  It has no catalogue
reader, likelihood, posterior, evidence, native-transfer adapter, or family
classifier.  Every numerical API is explicitly synthetic and returns a C2
diagnostic boundary alongside its result.
"""

from __future__ import annotations

from dataclasses import InitVar, dataclass, field
import hashlib
import json
import math
from numbers import Real
from types import MappingProxyType
from typing import Mapping, Sequence

import numpy as np

from common.depth_path import (
    DepthPath,
    build_depth_path,
    build_mask_stratum,
    build_transport_kernel,
)
from common.sky_support import build_sky_support_from_mask
from common.source_separation import (
    SourceSeparationDecision,
    SourceSeparationDecisionStatus,
    revalidate_source_separation_decision,
)


SCHEMA_VERSION = "htt.obsstat.cf4_post275_lane.v1"
CLAIM_TIER = "diagnostic_only"
FAMILY_GATE = "BLOCKED_PRE_NATIVE_ATLAS"
RELATIVE_SINGULAR_FLOOR = 1e-12
RELATIVE_EIGENGAP_FLOOR = 1e-10
COVARIANCE_CONDITION_LIMIT = 1e12
FEATURE_NAMES = (
    "monopole",
    "bulk_x",
    "bulk_y",
    "bulk_z",
    "shear_Sxx",
    "shear_Syy",
    "shear_xy",
    "shear_xz",
    "shear_yz",
)
FEATURE_UNITS = (
    "km_per_s",
    "km_per_s",
    "km_per_s",
    "km_per_s",
    "km_per_s_per_Mpc",
    "km_per_s_per_Mpc",
    "km_per_s_per_Mpc",
    "km_per_s_per_Mpc",
    "km_per_s_per_Mpc",
)
CF4_OPERATOR_IDENTITY_FIELDS = frozenset(
    {
        "pipeline_id",
        "catalogue_product_id",
        "grouping_id",
        "row_identity_id",
        "selection_id",
        "coordinate_frame_id",
        "sign_orientation_convention_id",
        "distance_scale_id",
        "velocity_estimator_id",
        "estimand_id",
        "depth_path_id",
        "zone_of_avoidance_mask_id",
        "covariance_id",
        "nuisance_box_id",
        "response_id",
        "units_id",
        "feature_order_id",
        "null_or_matched_mock_id",
    }
)

_DESIGN_TOKEN = object()
_FIT_TOKEN = object()
_COMPARISON_TOKEN = object()
_DEPTH_TOKEN = object()
_SHEAR_TOKEN = object()
_EIGENSPACE_TOKEN = object()
_RESPONSE_TOKEN = object()


class Cf4Post275Error(ValueError):
    """Raised when a synthetic CF4 operator contract fails closed."""


def _canonical_bytes(payload: object) -> bytes:
    try:
        return json.dumps(
            payload,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=True,
            allow_nan=False,
        ).encode("ascii")
    except (TypeError, ValueError, UnicodeEncodeError) as exc:
        raise Cf4Post275Error("payload is not canonical JSON") from exc


def _content_id(payload: object) -> str:
    return "sha256:" + hashlib.sha256(_canonical_bytes(payload)).hexdigest()


def _column_normalized_svd(
    matrix: np.ndarray, *, name: str, relative_floor: float = RELATIVE_SINGULAR_FLOOR
) -> tuple[np.ndarray, np.ndarray, int]:
    """Return scale-invariant column norms, singular values, and rank."""

    maxima = np.max(np.abs(matrix), axis=0)
    if not np.all(np.isfinite(maxima)) or np.any(maxima <= 0.0):
        raise Cf4Post275Error(f"{name} has a zero or non-finite column normalizer")
    rescaled = matrix / maxima
    rescaled_norms = np.linalg.norm(rescaled, axis=0)
    scales = maxima * rescaled_norms
    if not np.all(np.isfinite(scales)) or np.any(scales <= 0.0):
        raise Cf4Post275Error(f"{name} has a zero or non-finite column normalizer")
    normalized = rescaled / rescaled_norms
    singular_values = np.linalg.svd(normalized, compute_uv=False)
    if not np.all(np.isfinite(singular_values)) or singular_values.size == 0:
        raise Cf4Post275Error(f"{name} singular values are invalid")
    maximum = float(singular_values[0])
    if maximum <= 0.0:
        raise Cf4Post275Error(f"{name} has no supported response")
    rank = int(np.count_nonzero(singular_values > relative_floor * maximum))
    return scales, singular_values, rank


def _relative_eigengap_threshold(values: np.ndarray, floor: float) -> float:
    scale = float(np.max(np.abs(values)))
    if not math.isfinite(scale):
        raise Cf4Post275Error("eigenvalue scale is non-finite")
    return floor * scale


CF4_FEATURE_ORDER_ID = _content_id(
    {
        "schema": "htt.obsstat.cf4_feature_order.v1",
        "feature_names": list(FEATURE_NAMES),
        "feature_units": list(FEATURE_UNITS),
        "stf_coordinate_rule": "Szz_equals_minus_Sxx_minus_Syy",
    }
)


def _text(value: object, name: str) -> str:
    if not isinstance(value, str) or not value.strip() or value != value.strip():
        raise Cf4Post275Error(f"{name} must be non-empty trimmed text")
    return value


def _finite_vector(value: object, name: str) -> np.ndarray:
    try:
        array = np.asarray(value, dtype=float)
    except (TypeError, ValueError) as exc:
        raise Cf4Post275Error(f"{name} must be numeric") from exc
    if array.ndim != 1 or not np.all(np.isfinite(array)):
        raise Cf4Post275Error(f"{name} must be a finite vector")
    return array


def _finite_matrix(value: object, name: str) -> np.ndarray:
    try:
        array = np.asarray(value, dtype=float)
    except (TypeError, ValueError) as exc:
        raise Cf4Post275Error(f"{name} must be numeric") from exc
    if array.ndim != 2 or not np.all(np.isfinite(array)):
        raise Cf4Post275Error(f"{name} must be a finite matrix")
    return array


def _hex_matrix(matrix: np.ndarray) -> list[list[str]]:
    return [[float(value).hex() for value in row] for row in matrix]


def validate_cf4_operator_identity(
    identity: Mapping[str, object],
) -> dict[str, str]:
    """Validate the exact catalogue/operator identity inventory."""

    if not isinstance(identity, Mapping) or frozenset(identity) != (
        CF4_OPERATOR_IDENTITY_FIELDS
    ):
        raise Cf4Post275Error("CF4 operator identity field inventory drifted")
    return {
        name: _text(identity[name], f"operator identity {name}")
        for name in sorted(CF4_OPERATOR_IDENTITY_FIELDS)
    }


@dataclass(frozen=True)
class Cf4MomentDesign:
    matrix: tuple[tuple[float, ...], ...]
    operator_identity: Mapping[str, str]
    feature_names: tuple[str, ...] = FEATURE_NAMES
    units: tuple[str, ...] = FEATURE_UNITS
    rank: int = 9
    _construction_token: InitVar[object] = None
    column_scales: tuple[float, ...] = field(init=False)
    column_normalizer_id: str = field(init=False)
    content_id: str = field(init=False)

    def __post_init__(self, _construction_token: object) -> None:
        if _construction_token is not _DESIGN_TOKEN:
            raise Cf4Post275Error("Cf4MomentDesign must be factory-built")
        matrix = _finite_matrix(self.matrix, "design matrix")
        if matrix.shape[1] != 9 or matrix.shape[0] < 9:
            raise Cf4Post275Error(
                "CF4 design must have at least nine rows and rank nine"
            )
        scales, _, observed_rank = _column_normalized_svd(
            matrix, name="CF4 design"
        )
        if observed_rank != 9 or self.rank != 9:
            raise Cf4Post275Error("CF4 design must have rank nine")
        identity = validate_cf4_operator_identity(self.operator_identity)
        object.__setattr__(self, "matrix", tuple(tuple(float(x) for x in row) for row in matrix))
        object.__setattr__(self, "operator_identity", MappingProxyType(identity))
        object.__setattr__(self, "column_scales", tuple(float(x) for x in scales))
        object.__setattr__(
            self,
            "column_normalizer_id",
            _content_id(
                {
                    "schema": "htt.obsstat.cf4_column_normalizer.v1",
                    "feature_order_id": CF4_FEATURE_ORDER_ID,
                    "column_scales_hex": [float(x).hex() for x in scales],
                }
            ),
        )
        payload = self._payload()
        object.__setattr__(self, "content_id", _content_id(payload))

    def _payload(self) -> dict[str, object]:
        return {
            "schema": "htt.obsstat.cf4_moment_design.v1",
            "matrix_hex": _hex_matrix(np.asarray(self.matrix, dtype=float)),
            "operator_identity": dict(self.operator_identity),
            "feature_names": list(self.feature_names),
            "units": list(self.units),
            "rank": self.rank,
            "rank_method": "column_normalized_relative_svd",
            "relative_singular_floor_hex": RELATIVE_SINGULAR_FLOOR.hex(),
            "column_scales_hex": [value.hex() for value in self.column_scales],
            "column_normalizer_id": self.column_normalizer_id,
            "observed_data_executed": False,
            "claim_tier": CLAIM_TIER,
        }

    def as_payload(self) -> dict[str, object]:
        payload = self._payload()
        if _content_id(payload) != self.content_id:
            raise Cf4Post275Error("CF4 moment-design identity drifted")
        return {**payload, "content_id": self.content_id}


def build_cf4_moment_design(
    unit_vectors: object,
    distances_mpc: object,
    operator_identity: Mapping[str, object],
) -> Cf4MomentDesign:
    directions = _finite_matrix(unit_vectors, "unit_vectors")
    distances = _finite_vector(distances_mpc, "distances_mpc")
    if directions.shape[1:] != (3,) or directions.shape[0] != distances.size:
        raise Cf4Post275Error("unit vectors and distances must have shapes (n,3) and (n,)")
    if np.any(distances <= 0.0):
        raise Cf4Post275Error("distances_mpc must be positive")
    norms = np.linalg.norm(directions, axis=1)
    if not np.allclose(norms, 1.0, rtol=0.0, atol=1e-12):
        raise Cf4Post275Error("direction rows must be unit vectors")
    x, y, z = directions.T
    design = np.column_stack(
        (
            np.ones(len(directions)),
            x,
            y,
            z,
            distances * (x * x - z * z),
            distances * (y * y - z * z),
            distances * (2.0 * x * y),
            distances * (2.0 * x * z),
            distances * (2.0 * y * z),
        )
    )
    return Cf4MomentDesign(
        matrix=tuple(tuple(float(value) for value in row) for row in design),
        operator_identity=validate_cf4_operator_identity(operator_identity),
        rank=_column_normalized_svd(design, name="CF4 design")[2],
        _construction_token=_DESIGN_TOKEN,
    )


@dataclass(frozen=True)
class Cf4SyntheticFitReport:
    design_content_id: str
    coefficients: tuple[float, ...]
    coefficient_covariance: tuple[tuple[float, ...], ...]
    effective_rank: int
    residual_chi_square: float
    units: tuple[str, ...]
    column_normalizer_id: str
    rank_method: str = "covariance_whitened_column_normalized_svd"
    observed_data_executed: bool = False
    public_use: bool = False
    family_identification_gate: str = FAMILY_GATE
    _construction_token: InitVar[object] = None

    def __post_init__(self, _construction_token: object) -> None:
        if _construction_token is not _FIT_TOKEN:
            raise Cf4Post275Error("Cf4SyntheticFitReport must be factory-built")
        if self.observed_data_executed or self.public_use:
            raise Cf4Post275Error("synthetic report cannot become observed or public")
        if self.family_identification_gate != FAMILY_GATE:
            raise Cf4Post275Error("family-identification gate drifted")
        if (
            self.effective_rank != 9
            or self.rank_method != "covariance_whitened_column_normalized_svd"
            or not all(math.isfinite(value) for value in self.coefficients)
            or not all(
                math.isfinite(value)
                for row in self.coefficient_covariance
                for value in row
            )
            or not math.isfinite(self.residual_chi_square)
            or self.residual_chi_square < 0.0
        ):
            raise Cf4Post275Error("synthetic fit numerical contract drifted")
        _text(self.column_normalizer_id, "column_normalizer_id")


def _positive_definite_covariance(
    covariance: object,
    *,
    dimension: int,
    diagonal_forbidden: bool,
) -> np.ndarray:
    matrix = _finite_matrix(covariance, "covariance")
    if matrix.shape != (dimension, dimension):
        raise Cf4Post275Error("covariance shape does not match the frozen rows")
    if not np.allclose(matrix, matrix.T, rtol=1e-12, atol=1e-15):
        raise Cf4Post275Error("covariance must be symmetric")
    if diagonal_forbidden and np.allclose(
        matrix, np.diag(np.diag(matrix)), rtol=0.0, atol=0.0
    ):
        raise Cf4Post275Error("diagonal covariance shortcut is forbidden")
    eigenvalues = np.linalg.eigvalsh(matrix)
    if float(eigenvalues[0]) <= 0.0:
        raise Cf4Post275Error("covariance must be positive definite")
    condition = float(eigenvalues[-1] / eigenvalues[0])
    if not math.isfinite(condition) or condition > COVARIANCE_CONDITION_LIMIT:
        raise Cf4Post275Error(
            "covariance is ill-conditioned and has no registered rank reduction"
        )
    try:
        np.linalg.cholesky(matrix)
    except np.linalg.LinAlgError as exc:
        raise Cf4Post275Error("covariance Cholesky replay failed") from exc
    return matrix


def fit_synthetic_cf4_moments(
    radial_velocities_km_s: object,
    *,
    design: Cf4MomentDesign,
    covariance: object,
) -> Cf4SyntheticFitReport:
    if type(design) is not Cf4MomentDesign:
        raise TypeError("design must be an exact Cf4MomentDesign")
    design.as_payload()
    values = _finite_vector(radial_velocities_km_s, "radial velocities")
    matrix = np.asarray(design.matrix, dtype=float)
    if values.size != matrix.shape[0]:
        raise Cf4Post275Error("radial velocities must match the design rows")
    cov = _positive_definite_covariance(
        covariance, dimension=values.size, diagonal_forbidden=True
    )
    cholesky = np.linalg.cholesky(cov)
    whitened_design = np.linalg.solve(cholesky, matrix)
    whitened_values = np.linalg.solve(cholesky, values)
    scales, _, rank = _column_normalized_svd(
        whitened_design, name="covariance-whitened CF4 design"
    )
    if rank != 9:
        raise Cf4Post275Error("weighted CF4 design must have rank nine")
    normalized = whitened_design / scales
    normalized_normal = normalized.T @ normalized
    try:
        normalized_covariance = np.linalg.solve(
            normalized_normal, np.eye(normalized_normal.shape[0])
        )
        normalized_coefficients = np.linalg.solve(
            normalized_normal, normalized.T @ whitened_values
        )
    except np.linalg.LinAlgError as exc:
        raise Cf4Post275Error("normalized GLS solve failed") from exc
    inverse_scales = 1.0 / scales
    coefficient_covariance = (
        inverse_scales[:, None]
        * normalized_covariance
        * inverse_scales[None, :]
    )
    coefficients = normalized_coefficients * inverse_scales
    residual = values - matrix @ coefficients
    whitened_residual = np.linalg.solve(cholesky, residual)
    chi_square = float(whitened_residual @ whitened_residual)
    if (
        not np.all(np.isfinite(coefficients))
        or not np.all(np.isfinite(coefficient_covariance))
        or not math.isfinite(chi_square)
        or chi_square < 0.0
    ):
        raise Cf4Post275Error("normalized GLS produced non-finite output")
    return Cf4SyntheticFitReport(
        design_content_id=design.content_id,
        coefficients=tuple(float(value) for value in coefficients),
        coefficient_covariance=tuple(
            tuple(float(value) for value in row) for row in coefficient_covariance
        ),
        effective_rank=9,
        residual_chi_square=chi_square,
        units=FEATURE_UNITS,
        column_normalizer_id=_content_id(
            {
                "schema": "htt.obsstat.cf4_whitened_normalizer.v1",
                "design_content_id": design.content_id,
                "covariance_id": design.operator_identity["covariance_id"],
                "column_scales_hex": [float(value).hex() for value in scales],
            }
        ),
        _construction_token=_FIT_TOKEN,
    )


@dataclass(frozen=True)
class CorrelatedEstimandComparison:
    feature_ids: tuple[str, ...]
    chi_square: float
    dof: int
    difference_covariance: tuple[tuple[float, ...], ...]
    same_catalogue_cross_dependence_used: bool
    _construction_token: InitVar[object] = None

    def __post_init__(self, _construction_token: object) -> None:
        if _construction_token is not _COMPARISON_TOKEN:
            raise Cf4Post275Error("CorrelatedEstimandComparison must be factory-built")


def compare_correlated_estimands(
    estimand_a: object,
    estimand_b: object,
    *,
    covariance_a: object,
    covariance_b: object,
    cross_covariance: object,
    feature_ids: Sequence[str],
) -> CorrelatedEstimandComparison:
    left = _finite_vector(estimand_a, "estimand_a")
    right = _finite_vector(estimand_b, "estimand_b")
    identifiers = tuple(_text(value, "feature_id") for value in feature_ids)
    if left.shape != right.shape or left.size != len(identifiers) or left.size == 0:
        raise Cf4Post275Error("estimands and feature identities must align")
    if len(set(identifiers)) != len(identifiers):
        raise Cf4Post275Error("feature identities must be unique")
    dimension = left.size
    ca = _finite_matrix(covariance_a, "covariance_a")
    cb = _finite_matrix(covariance_b, "covariance_b")
    cab = _finite_matrix(cross_covariance, "cross_covariance")
    if any(value.shape != (dimension, dimension) for value in (ca, cb, cab)):
        raise Cf4Post275Error("all covariance blocks must match the estimand dimension")
    if not np.any(cab != 0.0):
        raise Cf4Post275Error("same-catalogue cross-estimand covariance is required")
    ca = _positive_definite_covariance(
        ca, dimension=dimension, diagonal_forbidden=False
    )
    cb = _positive_definite_covariance(
        cb, dimension=dimension, diagonal_forbidden=False
    )
    joint_covariance = np.block([[ca, cab], [cab.T, cb]])
    _positive_definite_covariance(
        joint_covariance,
        dimension=2 * dimension,
        diagonal_forbidden=False,
    )
    difference_covariance = ca + cb - cab - cab.T
    validated = _positive_definite_covariance(
        difference_covariance,
        dimension=dimension,
        diagonal_forbidden=False,
    )
    difference = left - right
    chi_square = float(difference @ np.linalg.solve(validated, difference))
    if chi_square < 0.0 or not math.isfinite(chi_square):
        raise Cf4Post275Error("correlated quadratic form must be finite and non-negative")
    return CorrelatedEstimandComparison(
        feature_ids=identifiers,
        chi_square=chi_square,
        dof=dimension,
        difference_covariance=tuple(
            tuple(float(value) for value in row) for row in validated
        ),
        same_catalogue_cross_dependence_used=True,
        _construction_token=_COMPARISON_TOKEN,
    )


@dataclass(frozen=True)
class Cf4DepthPathReport:
    path: DepthPath
    row_identity_ids: tuple[str, ...]
    selection_ids: tuple[str, ...]
    covariance_ids: tuple[str, ...]
    catalogue_product_id: str
    grouping_id: str
    depth_definition_id: str
    zoa_mask_id: str
    transport_identity_ids: tuple[str, ...]
    observed_data_executed: bool = False
    _construction_token: InitVar[object] = None

    def __post_init__(self, _construction_token: object) -> None:
        if _construction_token is not _DEPTH_TOKEN:
            raise Cf4Post275Error("Cf4DepthPathReport must be factory-built")
        self.path.as_payload()
        if self.observed_data_executed:
            raise Cf4Post275Error("synthetic depth path cannot be observed")
        if not (
            len(self.row_identity_ids)
            == len(self.selection_ids)
            == len(self.covariance_ids)
            == len(self.path.strata)
        ):
            raise Cf4Post275Error(
                "depth native-role binding inventory drifted"
            )
        for name in (
            "catalogue_product_id",
            "grouping_id",
            "depth_definition_id",
            "zoa_mask_id",
        ):
            _text(getattr(self, name), name)


def build_synthetic_depth_zoa_path(
    rows: Sequence[Mapping[str, object]],
    *,
    operator_identity: Mapping[str, object],
) -> Cf4DepthPathReport:
    if isinstance(rows, (str, bytes)) or len(rows) < 2:
        raise Cf4Post275Error("depth path requires at least two rows")
    identity = validate_cf4_operator_identity(operator_identity)
    resolved = tuple(rows)
    required = {"depth_mpc", "support_unit_ids"}
    if any(not isinstance(row, Mapping) or set(row) != required for row in resolved):
        raise Cf4Post275Error("depth row field inventory drifted")

    support_rows: list[tuple[str, ...]] = []
    depths: list[float] = []
    row_ids: list[str] = []
    selection_ids: list[str] = []
    covariance_ids: list[str] = []
    universe: set[str] = set()
    for index, row in enumerate(resolved):
        raw_depth = row["depth_mpc"]
        if isinstance(raw_depth, bool) or not isinstance(raw_depth, Real):
            raise Cf4Post275Error("depth_mpc must be real")
        depth = float(raw_depth)
        if not math.isfinite(depth) or depth <= 0.0:
            raise Cf4Post275Error("depth_mpc must be finite and positive")
        supports = tuple(
            _text(value, "support_unit_id") for value in row["support_unit_ids"]
        )
        if not supports or len(set(supports)) != len(supports):
            raise Cf4Post275Error(
                "support identities must be nonempty and unique"
            )
        if index and not set(supports).issubset(support_rows[index - 1]):
            raise Cf4Post275Error("depth support rows must be nested")
        support_rows.append(supports)
        universe.update(supports)
        depths.append(depth)
        row_id = _content_id(
            {
                "schema": "htt.obsstat.cf4_depth_row_binding.v1",
                "catalogue_product_id": identity["catalogue_product_id"],
                "grouping_id": identity["grouping_id"],
                "base_row_identity_id": identity["row_identity_id"],
                "depth_definition_id": identity["depth_path_id"],
                "depth_mpc_hex": depth.hex(),
                "support_unit_ids": list(supports),
            }
        )
        row_ids.append(row_id)
        selection_ids.append(
            _content_id(
                {
                    "schema": "htt.obsstat.cf4_depth_selection_binding.v1",
                    "base_selection_id": identity["selection_id"],
                    "row_identity_id": row_id,
                }
            )
        )
        covariance_ids.append(
            _content_id(
                {
                    "schema": "htt.obsstat.cf4_depth_covariance_binding.v1",
                    "base_covariance_id": identity["covariance_id"],
                    "row_identity_id": row_id,
                }
            )
        )
    if any(
        left >= right
        for left, right in zip(depths[:-1], depths[1:], strict=True)
    ):
        raise Cf4Post275Error("depth coordinates must be strictly increasing")

    ordered_universe = tuple(sorted(universe))
    strata = []
    for index, supports in enumerate(support_rows):
        support_mask = np.asarray(
            [value in supports for value in ordered_universe]
        )
        sky_support = build_sky_support_from_mask(
            support_mask,
            coordinate_frame="GALACTIC",
            completeness_status="synthetic_contract_complete",
            selection_mode=selection_ids[index],
            mock_coverage_status="synthetic_fixture",
            pixelization="PR291_SYNTHETIC_GROUP_ROWS",
        )
        strata.append(
            build_mask_stratum(
                stratum_id=_content_id(
                    {
                        "schema": "htt.obsstat.cf4_depth_stratum.v1",
                        "row_identity_id": row_ids[index],
                        "selection_id": selection_ids[index],
                        "covariance_id": covariance_ids[index],
                    }
                ),
                depth_coordinate=depths[index],
                depth_unit="Mpc",
                support_unit_ids=supports,
                support_universe_size=len(ordered_universe),
                sky_support=sky_support,
                selection_id=selection_ids[index],
                covariance_id=covariance_ids[index],
                source_artifact_id=row_ids[index],
                feature_names=FEATURE_NAMES,
                feature_unit="typed_cf4_mixed_moment_units",
                assumptions=(
                    "synthetic cumulative CF4 support only",
                    "no observed catalogue bytes",
                    "native-role identities derived from the operator binding",
                    (
                        "zone of avoidance identity "
                        + identity["zone_of_avoidance_mask_id"]
                    ),
                ),
            )
        )

    kernels = []
    transport_ids = []
    for index, (source, target) in enumerate(
        zip(strata[:-1], strata[1:], strict=True), start=1
    ):
        transport_id = _content_id(
            {
                "schema": "htt.obsstat.cf4_depth_transport_binding.v1",
                "source_row_identity_id": row_ids[index - 1],
                "target_row_identity_id": row_ids[index],
                "grouping_id": identity["grouping_id"],
                "depth_definition_id": identity["depth_path_id"],
                "zoa_definition_id": identity[
                    "zone_of_avoidance_mask_id"
                ],
            }
        )
        transport_ids.append(transport_id)
        kernels.append(
            build_transport_kernel(
                transport_id=transport_id,
                source=source,
                target=target,
                matrix=np.eye(len(FEATURE_NAMES)),
                mask_transport_id=identity["zone_of_avoidance_mask_id"],
                selection_transport_id=_content_id(
                    {
                        "source_selection_id": selection_ids[index - 1],
                        "target_selection_id": selection_ids[index],
                    }
                ),
                covariance_transport_id=_content_id(
                    {
                        "source_covariance_id": covariance_ids[index - 1],
                        "target_covariance_id": covariance_ids[index],
                    }
                ),
                method_id="PR291-SYNTHETIC-IDENTITY-TRANSPORT-V1",
                assumptions=(
                    "identity feature transport on nested supports",
                ),
            )
        )
    path = build_depth_path(
        path_id=_content_id(
            {
                "schema": "htt.obsstat.cf4_depth_path_binding.v1",
                "catalogue_product_id": identity["catalogue_product_id"],
                "grouping_id": identity["grouping_id"],
                "depth_definition_id": identity["depth_path_id"],
                "zoa_definition_id": identity[
                    "zone_of_avoidance_mask_id"
                ],
                "row_identity_ids": row_ids,
            }
        ),
        strata=strata,
        kernels=kernels,
    )
    return Cf4DepthPathReport(
        path=path,
        row_identity_ids=tuple(row_ids),
        selection_ids=tuple(selection_ids),
        covariance_ids=tuple(covariance_ids),
        catalogue_product_id=identity["catalogue_product_id"],
        grouping_id=identity["grouping_id"],
        depth_definition_id=identity["depth_path_id"],
        zoa_mask_id=identity["zone_of_avoidance_mask_id"],
        transport_identity_ids=tuple(transport_ids),
        _construction_token=_DEPTH_TOKEN,
    )


@dataclass(frozen=True)
class Cf4SyntheticShearReport:
    eigenvalues: tuple[float, float, float]
    eigengaps: tuple[float, float]
    trace: float
    determinant: float
    frobenius_norm: float
    covariance_id: str
    response_id: str
    identification_status: str
    required_action: str
    family_identification_gate: str = FAMILY_GATE
    _construction_token: InitVar[object] = None

    def __post_init__(self, _construction_token: object) -> None:
        if _construction_token is not _SHEAR_TOKEN:
            raise Cf4Post275Error("Cf4SyntheticShearReport must be factory-built")
        if self.family_identification_gate != FAMILY_GATE:
            raise Cf4Post275Error("family-identification gate drifted")


def analyze_synthetic_shear(
    shear_tensor: object,
    *,
    covariance_id: str,
    response_id: str,
) -> Cf4SyntheticShearReport:
    matrix = _finite_matrix(shear_tensor, "shear_tensor")
    if matrix.shape != (3, 3):
        raise Cf4Post275Error("shear tensor must have shape (3,3)")
    if not np.allclose(matrix, matrix.T, rtol=0.0, atol=1e-12):
        raise Cf4Post275Error("shear tensor must be symmetric")
    if not math.isclose(float(np.trace(matrix)), 0.0, rel_tol=0.0, abs_tol=1e-12):
        raise Cf4Post275Error("shear tensor must be trace-free")
    values = np.linalg.eigvalsh(matrix)
    gaps = np.diff(values)
    weak = float(np.min(gaps)) <= _relative_eigengap_threshold(
        values, RELATIVE_EIGENGAP_FLOOR
    )
    return Cf4SyntheticShearReport(
        eigenvalues=tuple(float(value) for value in values),  # type: ignore[arg-type]
        eigengaps=tuple(float(value) for value in gaps),  # type: ignore[arg-type]
        trace=float(np.trace(matrix)),
        determinant=float(np.linalg.det(matrix)),
        frobenius_norm=float(np.linalg.norm(matrix, ord="fro")),
        covariance_id=_text(covariance_id, "covariance_id"),
        response_id=_text(response_id, "response_id"),
        identification_status=(
            "WEAKLY_IDENTIFIED" if weak else "SYNTHETIC_ORBIT_COMPATIBILITY_ONLY"
        ),
        required_action=(
            "RESPONSE_EQUIVALENCE_ABSTENTION"
            if weak
            else "NO_SOURCE_OR_FAMILY_LABEL"
        ),
        _construction_token=_SHEAR_TOKEN,
    )


@dataclass(frozen=True)
class Cf4EigenspaceDriftReport:
    reference_depth_id: str
    candidate_depth_id: str
    depth_path_content_id: str
    covariance_id: str
    response_id: str
    reference_eigenvalues: tuple[float, float, float]
    candidate_eigenvalues: tuple[float, float, float]
    cluster_index_groups: tuple[tuple[int, ...], ...]
    projector_frobenius_distances: tuple[float, ...]
    cluster_max_principal_angles_radians: tuple[float, ...]
    maximum_subspace_angle_radians: float
    eigengap_floor: float
    identification_status: str
    required_action: str
    family_identification_gate: str = FAMILY_GATE
    _construction_token: InitVar[object] = None
    content_id: str = field(init=False)

    def __post_init__(self, _construction_token: object) -> None:
        if _construction_token is not _EIGENSPACE_TOKEN:
            raise Cf4Post275Error(
                "Cf4EigenspaceDriftReport must be factory-built"
            )
        for name in (
            "reference_depth_id",
            "candidate_depth_id",
            "depth_path_content_id",
            "covariance_id",
            "response_id",
        ):
            _text(getattr(self, name), name)
        if self.reference_depth_id == self.candidate_depth_id:
            raise Cf4Post275Error("eigenspace drift requires two depth identities")
        if not self.cluster_index_groups or tuple(
            value for group in self.cluster_index_groups for value in group
        ) != (0, 1, 2):
            raise Cf4Post275Error("eigenspace clusters must partition three axes")
        if not (
            len(self.projector_frobenius_distances)
            == len(self.cluster_index_groups)
            == len(self.cluster_max_principal_angles_radians)
        ):
            raise Cf4Post275Error("eigenspace drift metric inventory drifted")
        if self.identification_status not in {
            "WEAKLY_IDENTIFIED",
            "SYNTHETIC_ORBIT_COMPATIBILITY_ONLY",
        }:
            raise Cf4Post275Error("eigenspace identification status is invalid")
        expected_action = (
            "EIGENSPACE_EQUIVALENCE_ABSTENTION"
            if self.identification_status == "WEAKLY_IDENTIFIED"
            else "NO_SOURCE_OR_FAMILY_LABEL"
        )
        if self.required_action != expected_action:
            raise Cf4Post275Error("eigenspace action/status pair drifted")
        if self.family_identification_gate != FAMILY_GATE:
            raise Cf4Post275Error("family-identification gate drifted")
        object.__setattr__(self, "content_id", _content_id(self._payload()))

    def _payload(self) -> dict[str, object]:
        return {
            "schema": "htt.obsstat.cf4_eigenspace_drift.v1",
            "reference_depth_id": self.reference_depth_id,
            "candidate_depth_id": self.candidate_depth_id,
            "depth_path_content_id": self.depth_path_content_id,
            "covariance_id": self.covariance_id,
            "response_id": self.response_id,
            "reference_eigenvalues_hex": [
                value.hex() for value in self.reference_eigenvalues
            ],
            "candidate_eigenvalues_hex": [
                value.hex() for value in self.candidate_eigenvalues
            ],
            "cluster_index_groups": [
                list(group) for group in self.cluster_index_groups
            ],
            "projector_frobenius_distances_hex": [
                value.hex() for value in self.projector_frobenius_distances
            ],
            "cluster_max_principal_angles_radians_hex": [
                value.hex()
                for value in self.cluster_max_principal_angles_radians
            ],
            "maximum_subspace_angle_radians_hex": (
                self.maximum_subspace_angle_radians.hex()
            ),
            "eigengap_floor_hex": self.eigengap_floor.hex(),
            "identification_status": self.identification_status,
            "required_action": self.required_action,
            "claim_tier": CLAIM_TIER,
            "family_identification_gate": self.family_identification_gate,
            "observed_data_executed": False,
        }

    def as_payload(self) -> dict[str, object]:
        payload = self._payload()
        if _content_id(payload) != self.content_id:
            raise Cf4Post275Error("eigenspace-drift identity drifted")
        return {**payload, "content_id": self.content_id}


def _validated_stf_tensor(value: object, name: str) -> np.ndarray:
    matrix = _finite_matrix(value, name)
    if matrix.shape != (3, 3):
        raise Cf4Post275Error(f"{name} must have shape (3,3)")
    if not np.allclose(matrix, matrix.T, rtol=0.0, atol=1e-12):
        raise Cf4Post275Error(f"{name} must be symmetric")
    if not math.isclose(
        float(np.trace(matrix)), 0.0, rel_tol=0.0, abs_tol=1e-12
    ):
        raise Cf4Post275Error(f"{name} must be trace-free")
    return matrix


def analyze_synthetic_eigenspace_drift(
    reference_shear_tensor: object,
    candidate_shear_tensor: object,
    *,
    reference_depth_id: str,
    candidate_depth_id: str,
    depth_path_content_id: str,
    covariance_id: str,
    response_id: str,
) -> Cf4EigenspaceDriftReport:
    """Compare path-rung STF eigenspaces using sign/basis-invariant projectors."""

    reference = _validated_stf_tensor(
        reference_shear_tensor, "reference_shear_tensor"
    )
    candidate = _validated_stf_tensor(
        candidate_shear_tensor, "candidate_shear_tensor"
    )
    floor = RELATIVE_EIGENGAP_FLOOR

    reference_values, reference_vectors = np.linalg.eigh(reference)
    candidate_values, candidate_vectors = np.linalg.eigh(candidate)
    reference_gaps = np.diff(reference_values)
    candidate_gaps = np.diff(candidate_values)
    reference_threshold = _relative_eigengap_threshold(reference_values, floor)
    candidate_threshold = _relative_eigengap_threshold(candidate_values, floor)

    groups: list[tuple[int, ...]] = []
    start = 0
    for index, (reference_gap, candidate_gap) in enumerate(
        zip(reference_gaps, candidate_gaps, strict=True)
    ):
        if (
            float(reference_gap) > reference_threshold
            and float(candidate_gap) > candidate_threshold
        ):
            groups.append(tuple(range(start, index + 1)))
            start = index + 1
    groups.append(tuple(range(start, 3)))

    projector_distances: list[float] = []
    maximum_angles: list[float] = []
    for group in groups:
        left = reference_vectors[:, group]
        right = candidate_vectors[:, group]
        overlap = np.linalg.svd(left.T @ right, compute_uv=False)
        principal_angles = np.arccos(np.clip(overlap, -1.0, 1.0))
        maximum_angles.append(
            float(np.max(principal_angles)) if principal_angles.size else 0.0
        )
        left_projector = left @ left.T
        right_projector = right @ right.T
        projector_distances.append(
            float(np.linalg.norm(left_projector - right_projector, ord="fro"))
        )

    weak = any(len(group) > 1 for group in groups)
    return Cf4EigenspaceDriftReport(
        reference_depth_id=_text(reference_depth_id, "reference_depth_id"),
        candidate_depth_id=_text(candidate_depth_id, "candidate_depth_id"),
        depth_path_content_id=_text(
            depth_path_content_id, "depth_path_content_id"
        ),
        covariance_id=_text(covariance_id, "covariance_id"),
        response_id=_text(response_id, "response_id"),
        reference_eigenvalues=tuple(float(value) for value in reference_values),
        candidate_eigenvalues=tuple(float(value) for value in candidate_values),
        cluster_index_groups=tuple(groups),
        projector_frobenius_distances=tuple(projector_distances),
        cluster_max_principal_angles_radians=tuple(maximum_angles),
        maximum_subspace_angle_radians=max(maximum_angles, default=0.0),
        eigengap_floor=floor,
        identification_status=(
            "WEAKLY_IDENTIFIED"
            if weak
            else "SYNTHETIC_ORBIT_COMPATIBILITY_ONLY"
        ),
        required_action=(
            "EIGENSPACE_EQUIVALENCE_ABSTENTION"
            if weak
            else "NO_SOURCE_OR_FAMILY_LABEL"
        ),
        _construction_token=_EIGENSPACE_TOKEN,
    )


@dataclass(frozen=True)
class Cf4ResponseNullReport:
    response_id: str
    covariance_id: str
    covariance_content_id: str
    parameter_labels: tuple[str, ...]
    parameter_roles: tuple[str, ...]
    covariance_whitened_response: tuple[tuple[float, ...], ...]
    column_scales: tuple[float, ...]
    normalized_response_content_id: str
    singular_values: tuple[float, ...]
    normalizer_id: str
    response_rank: int
    response_dimension: int
    parameter_dimension: int
    nullity: int
    right_null_basis: tuple[tuple[float, ...], ...]
    relative_singular_floor: float
    null_residual_norm: float
    null_residual_bound: float
    status: str
    _construction_token: InitVar[object] = None
    content_id: str = field(init=False)

    def __post_init__(self, _construction_token: object) -> None:
        if _construction_token is not _RESPONSE_TOKEN:
            raise Cf4Post275Error("Cf4ResponseNullReport must be factory-built")
        self._validate_contract()
        object.__setattr__(self, "content_id", _content_id(self._payload()))

    def _validate_contract(self) -> None:
        _text(self.response_id, "response_id")
        _text(self.covariance_id, "covariance_id")
        _text(self.covariance_content_id, "covariance_content_id")
        if self.nullity <= 0 or self.status != "COVARIANCE_SUPPORTED_UNIDENTIFIED_DIRECTIONS":
            raise Cf4Post275Error("response report must preserve an unidentified direction")
        if (
            len(self.parameter_labels) != self.parameter_dimension
            or len(self.parameter_roles) != self.parameter_dimension
            or len(set(self.parameter_labels)) != self.parameter_dimension
            or any(role not in {"LOCAL", "GLOBAL", "NUISANCE"} for role in self.parameter_roles)
            or "LOCAL" not in self.parameter_roles
            or "GLOBAL" not in self.parameter_roles
        ):
            raise Cf4Post275Error("response parameter labels or roles drifted")
        if (
            type(self.response_rank) is not int
            or type(self.response_dimension) is not int
            or type(self.parameter_dimension) is not int
            or type(self.nullity) is not int
            or self.response_dimension < 1
            or self.parameter_dimension < 2
            or self.response_rank < 1
            or self.response_rank
            > min(self.response_dimension, self.parameter_dimension)
            or self.nullity != self.parameter_dimension - self.response_rank
        ):
            raise Cf4Post275Error("response rank/nullity contract drifted")
        if self.relative_singular_floor != RELATIVE_SINGULAR_FLOOR:
            raise Cf4Post275Error("registered response singular floor drifted")

        whitened = _finite_matrix(
            self.covariance_whitened_response,
            "covariance_whitened_response",
        )
        if whitened.shape != (self.response_dimension, self.parameter_dimension):
            raise Cf4Post275Error("whitened response dimensions drifted")
        scales = _finite_vector(self.column_scales, "column_scales")
        if scales.shape != (self.parameter_dimension,) or np.any(scales <= 0.0):
            raise Cf4Post275Error("response column scales drifted")
        normalized = whitened / scales
        expected_normalized_id = _matrix_content_id(
            "htt.obsstat.cf4_normalized_response.v1", normalized
        )
        if self.normalized_response_content_id != expected_normalized_id:
            raise Cf4Post275Error("normalized response identity drifted")

        singular = _finite_vector(self.singular_values, "singular_values")
        if singular.size == 0 or any(
            left < right for left, right in zip(singular, singular[1:])
        ):
            raise Cf4Post275Error("response singular-value inventory drifted")
        derived_singular = np.linalg.svd(normalized, compute_uv=False)
        if derived_singular.shape != singular.shape or not np.allclose(
            derived_singular,
            singular,
            rtol=64.0 * np.finfo(float).eps,
            atol=64.0 * np.finfo(float).eps,
        ):
            raise Cf4Post275Error("response singular values failed exact replay")
        derived_rank = int(
            np.count_nonzero(
                derived_singular
                > RELATIVE_SINGULAR_FLOOR * float(derived_singular[0])
            )
        )
        if derived_rank != self.response_rank:
            raise Cf4Post275Error("response rank failed registered replay")

        basis = _finite_matrix(self.right_null_basis, "right_null_basis")
        if basis.shape != (self.nullity, self.parameter_dimension):
            raise Cf4Post275Error("right-null basis dimensions drifted")
        residual = whitened @ basis.T
        residual_norm = _finite_operator_norm(residual, "right-null residual")
        residual_bound = _null_replay_bound(whitened, basis)
        if (
            residual_norm != self.null_residual_norm
            or residual_bound != self.null_residual_bound
            or residual_norm > residual_bound
        ):
            raise Cf4Post275Error("right-null basis failed numerical replay")

        expected_normalizer = _response_normalizer_id(
            response_id=self.response_id,
            covariance_id=self.covariance_id,
            covariance_content_id=self.covariance_content_id,
            parameter_labels=self.parameter_labels,
            parameter_roles=self.parameter_roles,
            column_scales=self.column_scales,
            normalized_response_content_id=self.normalized_response_content_id,
            singular_values=self.singular_values,
            response_rank=self.response_rank,
            nullity=self.nullity,
        )
        if self.normalizer_id != expected_normalizer:
            raise Cf4Post275Error("response normalizer identity drifted")

    def _payload(self) -> dict[str, object]:
        return {
            "schema": "htt.obsstat.cf4_response_null.v2",
            "response_id": self.response_id,
            "covariance_id": self.covariance_id,
            "covariance_content_id": self.covariance_content_id,
            "parameter_labels": list(self.parameter_labels),
            "parameter_roles": list(self.parameter_roles),
            "covariance_whitened_response_hex": [
                [value.hex() for value in row]
                for row in self.covariance_whitened_response
            ],
            "column_scales_hex": [value.hex() for value in self.column_scales],
            "normalized_response_content_id": self.normalized_response_content_id,
            "singular_values_hex": [value.hex() for value in self.singular_values],
            "normalizer_id": self.normalizer_id,
            "response_rank": self.response_rank,
            "response_dimension": self.response_dimension,
            "parameter_dimension": self.parameter_dimension,
            "nullity": self.nullity,
            "right_null_basis_hex": [
                [value.hex() for value in row] for row in self.right_null_basis
            ],
            "relative_singular_floor": self.relative_singular_floor,
            "relative_singular_floor_hex": self.relative_singular_floor.hex(),
            "null_residual_norm_hex": self.null_residual_norm.hex(),
            "null_residual_bound_hex": self.null_residual_bound.hex(),
            "status": self.status,
            "claim_tier": CLAIM_TIER,
            "family_identification_gate": FAMILY_GATE,
            "observed_data_executed": False,
        }

    def as_payload(self) -> dict[str, object]:
        self._validate_contract()
        payload = self._payload()
        if _content_id(payload) != self.content_id:
            raise Cf4Post275Error("response report identity drifted")
        return {**payload, "content_id": self.content_id}


def _matrix_content_id(schema: str, matrix: np.ndarray) -> str:
    return _content_id(
        {
            "schema": schema,
            "values_hex": [
                [float(value).hex() for value in row] for row in matrix
            ],
        }
    )


def _finite_operator_norm(matrix: np.ndarray, name: str) -> float:
    value = float(np.linalg.norm(matrix, ord=2))
    if not math.isfinite(value):
        raise Cf4Post275Error(f"{name} is numerically non-finite")
    return value


def _null_replay_bound(whitened: np.ndarray, basis: np.ndarray) -> float:
    bound = (
        128.0
        * np.finfo(float).eps
        * max(whitened.shape)
        * max(1.0, _finite_operator_norm(whitened, "whitened response"))
        * max(1.0, _finite_operator_norm(basis, "right-null basis"))
    )
    if not math.isfinite(bound):
        raise Cf4Post275Error("right-null replay bound is non-finite")
    return bound


def _response_normalizer_id(
    *,
    response_id: str,
    covariance_id: str,
    covariance_content_id: str,
    parameter_labels: tuple[str, ...],
    parameter_roles: tuple[str, ...],
    column_scales: tuple[float, ...],
    normalized_response_content_id: str,
    singular_values: tuple[float, ...],
    response_rank: int,
    nullity: int,
) -> str:
    return _content_id(
        {
            "schema": "htt.obsstat.cf4_response_normalizer.v2",
            "response_id": response_id,
            "covariance_id": covariance_id,
            "covariance_content_id": covariance_content_id,
            "parameter_labels": list(parameter_labels),
            "parameter_roles": list(parameter_roles),
            "column_scales_hex": [value.hex() for value in column_scales],
            "normalized_response_content_id": normalized_response_content_id,
            "relative_singular_floor_hex": RELATIVE_SINGULAR_FLOOR.hex(),
            "singular_values_hex": [value.hex() for value in singular_values],
            "response_rank": response_rank,
            "nullity": nullity,
        }
    )


def analyze_synthetic_response_nullspace(
    response_matrix: object,
    covariance: object,
    *,
    covariance_id: str,
    response_id: str,
    parameter_labels: Sequence[str],
    parameter_roles: Sequence[str],
) -> Cf4ResponseNullReport:
    response = _finite_matrix(response_matrix, "response_matrix")
    if response.shape[0] < 1 or response.shape[1] < 2:
        raise Cf4Post275Error("response matrix must have at least one row and two parameters")
    cov = _positive_definite_covariance(
        covariance,
        dimension=response.shape[0],
        diagonal_forbidden=response.shape[0] > 1,
    )
    labels = tuple(_text(value, "parameter_label") for value in parameter_labels)
    roles = tuple(_text(value, "parameter_role").upper() for value in parameter_roles)
    if len(labels) != response.shape[1] or len(roles) != response.shape[1]:
        raise Cf4Post275Error("response labels and roles must match parameter columns")
    whitened = np.linalg.solve(np.linalg.cholesky(cov), response)
    scales, singular_values, rank = _column_normalized_svd(
        whitened,
        name="covariance-whitened response",
        relative_floor=RELATIVE_SINGULAR_FLOOR,
    )
    normalized = whitened / scales
    _, _, right = np.linalg.svd(normalized, full_matrices=True)
    nullity = response.shape[1] - rank
    if nullity <= 0:
        raise Cf4Post275Error("synthetic response must retain an unidentified direction")
    basis = right[rank:, :] / scales[None, :]
    basis_maxima = np.max(np.abs(basis), axis=1)
    if np.any(basis_maxima <= 0.0) or not np.all(np.isfinite(basis_maxima)):
        raise Cf4Post275Error("right-null basis normalization failed")
    rescaled_basis = basis / basis_maxima[:, None]
    basis_norms = np.linalg.norm(rescaled_basis, axis=1)
    if np.any(basis_norms <= 0.0) or not np.all(np.isfinite(basis_norms)):
        raise Cf4Post275Error("right-null basis normalization failed")
    basis = rescaled_basis / basis_norms[:, None]
    residual = whitened @ basis.T
    residual_norm = _finite_operator_norm(residual, "right-null residual")
    residual_bound = _null_replay_bound(whitened, basis)
    if residual_norm > residual_bound:
        raise Cf4Post275Error("right-null basis failed numerical replay")
    covariance_content_id = _matrix_content_id(
        "htt.obsstat.cf4_covariance.v1", cov
    )
    normalized_response_content_id = _matrix_content_id(
        "htt.obsstat.cf4_normalized_response.v1", normalized
    )
    column_scales = tuple(float(value) for value in scales)
    singular = tuple(float(value) for value in singular_values)
    response_identity = _text(response_id, "response_id")
    covariance_identity = _text(covariance_id, "covariance_id")
    normalizer_id = _response_normalizer_id(
        response_id=response_identity,
        covariance_id=covariance_identity,
        covariance_content_id=covariance_content_id,
        parameter_labels=labels,
        parameter_roles=roles,
        column_scales=column_scales,
        normalized_response_content_id=normalized_response_content_id,
        singular_values=singular,
        response_rank=rank,
        nullity=nullity,
    )
    return Cf4ResponseNullReport(
        response_id=response_identity,
        covariance_id=covariance_identity,
        covariance_content_id=covariance_content_id,
        parameter_labels=labels,
        parameter_roles=roles,
        covariance_whitened_response=tuple(
            tuple(float(value) for value in row) for row in whitened
        ),
        column_scales=column_scales,
        normalized_response_content_id=normalized_response_content_id,
        singular_values=singular,
        normalizer_id=normalizer_id,
        response_rank=rank,
        response_dimension=response.shape[0],
        parameter_dimension=response.shape[1],
        nullity=nullity,
        right_null_basis=tuple(tuple(float(value) for value in row) for row in basis),
        relative_singular_floor=RELATIVE_SINGULAR_FLOOR,
        null_residual_norm=residual_norm,
        null_residual_bound=residual_bound,
        status="COVARIANCE_SUPPORTED_UNIDENTIFIED_DIRECTIONS",
        _construction_token=_RESPONSE_TOKEN,
    )


def build_structural_identified_set(
    *,
    lower: object,
    upper: object,
    nuisance_box_id: str,
    response: Cf4ResponseNullReport,
    source_separation: SourceSeparationDecision,
) -> dict[str, object]:
    if isinstance(lower, bool) or isinstance(upper, bool) or not isinstance(
        lower, Real
    ) or not isinstance(upper, Real):
        raise Cf4Post275Error("identified-set bounds must be real")
    lo = float(lower)
    hi = float(upper)
    if not math.isfinite(lo) or not math.isfinite(hi) or lo >= hi:
        raise Cf4Post275Error(
            "identified-set bounds must be finite and strictly ordered"
        )
    decision = _replay_response_source_binding(response, source_separation)
    if decision.status is not SourceSeparationDecisionStatus.WEAKLY_IDENTIFIED:
        raise Cf4Post275Error("structural identified set requires weak identification")
    return {
        "schema": "htt.obsstat.cf4_structural_identified_set.v1",
        "status": "BOUNDED_BUT_NOT_POINT_IDENTIFIED",
        "bounds": [lo, hi],
        "reported_point": None,
        "confidence_level": None,
        "nuisance_box_id": _text(nuisance_box_id, "nuisance_box_id"),
        "response_id": response.response_id,
        "response_content_id": response.content_id,
        "covariance_id": response.covariance_id,
        "covariance_content_id": response.covariance_content_id,
        "response_normalizer_id": response.normalizer_id,
        "response_rank": response.response_rank,
        "response_nullity": response.nullity,
        "relative_singular_floor": response.relative_singular_floor,
        "source_separation_decision_id": decision.decision_id,
        "source_geometry_report_id": decision.source_geometry_report_id,
        "threshold_contract_id": decision.threshold_contract.contract_id,
        "required_action": "RESPONSE_EQUIVALENCE_ABSTENTION",
        "favourable_endpoint_reporting": "FORBIDDEN",
        "pipeline_spread_as_confidence": "FORBIDDEN",
        "claim_tier": CLAIM_TIER,
        "family_identification_gate": FAMILY_GATE,
    }


def _replay_response_source_binding(
    response: Cf4ResponseNullReport,
    source_separation: SourceSeparationDecision,
) -> SourceSeparationDecision:
    if (
        type(response) is not Cf4ResponseNullReport
        or type(source_separation) is not SourceSeparationDecision
    ):
        raise TypeError("response/source decision must be exact factory objects")
    response.as_payload()
    decision = revalidate_source_separation_decision(source_separation)
    if (
        decision.covariance_id != response.covariance_id
        or decision.normalizer_id != response.normalizer_id
        or decision.local_parameter_count
        != response.parameter_roles.count("LOCAL")
        or decision.global_parameter_count
        != response.parameter_roles.count("GLOBAL")
    ):
        raise Cf4Post275Error("source-response identity drifted")
    if (
        decision.local_rank != decision.local_parameter_count
        or decision.global_rank != decision.global_parameter_count
        or decision.joint_rank != response.response_rank
        or response.nullity
        != response.parameter_dimension - decision.joint_rank
    ):
        raise Cf4Post275Error("source-response rank/nullity drifted")
    return decision


def build_cf4_gate_snapshot(
    *,
    design: Cf4MomentDesign,
    depth: Cf4DepthPathReport,
    shear: Cf4SyntheticShearReport,
    eigenspace_drift: Cf4EigenspaceDriftReport,
    response: Cf4ResponseNullReport,
    source_separation: SourceSeparationDecision,
) -> dict[str, dict[str, object]]:
    if (
        type(design) is not Cf4MomentDesign
        or type(depth) is not Cf4DepthPathReport
        or type(shear) is not Cf4SyntheticShearReport
        or type(eigenspace_drift) is not Cf4EigenspaceDriftReport
        or type(response) is not Cf4ResponseNullReport
        or type(source_separation) is not SourceSeparationDecision
    ):
        raise TypeError("gate inputs must be exact PR-291 factory objects")
    design.as_payload()
    depth.path.as_payload()
    eigenspace_drift.as_payload()
    decision = _replay_response_source_binding(response, source_separation)
    identity = design.operator_identity
    if identity["feature_order_id"] != CF4_FEATURE_ORDER_ID:
        raise Cf4Post275Error("G7 feature-order identity drifted")
    if (
        identity["catalogue_product_id"] != depth.catalogue_product_id
        or identity["grouping_id"] != depth.grouping_id
        or identity["depth_path_id"] != depth.depth_definition_id
        or identity["zone_of_avoidance_mask_id"] != depth.zoa_mask_id
    ):
        raise Cf4Post275Error("G5 operator/depth identity drifted")
    depth_ids = tuple(value.stratum_id for value in depth.path.strata)
    try:
        reference_index = depth_ids.index(eigenspace_drift.reference_depth_id)
        candidate_index = depth_ids.index(eigenspace_drift.candidate_depth_id)
    except ValueError as exc:
        raise Cf4Post275Error("eigenspace drift is outside the depth path") from exc
    if candidate_index != reference_index + 1:
        raise Cf4Post275Error("eigenspace drift must bind adjacent depth rungs")
    if eigenspace_drift.depth_path_content_id != depth.path.content_id:
        raise Cf4Post275Error("eigenspace drift path identity drifted")
    if (
        shear.response_id != response.response_id
        or shear.covariance_id != response.covariance_id
        or eigenspace_drift.response_id != response.response_id
        or eigenspace_drift.covariance_id != response.covariance_id
        or identity["response_id"] != response.response_id
        or identity["covariance_id"] != response.covariance_id
    ):
        raise Cf4Post275Error("G7 response/covariance identities drifted")
    if (
        decision.source_geometry_report_id != identity["estimand_id"]
        or decision.covariance_id != identity["covariance_id"]
        or decision.normalizer_id != response.normalizer_id
        or decision.local_parameter_count
        != response.parameter_roles.count("LOCAL")
        or decision.global_parameter_count
        != response.parameter_roles.count("GLOBAL")
    ):
        raise Cf4Post275Error("G4 source-separation identity drifted")
    if decision.status is not SourceSeparationDecisionStatus.WEAKLY_IDENTIFIED:
        raise Cf4Post275Error("G4 requires a weak source-separation decision")
    return {
        "G4": {
            "status": "PASS_SYNTHETIC_WEAK_IDENTIFICATION_ABSTENTION",
            "response_action": "RESPONSE_EQUIVALENCE_ABSTENTION",
            "source_separation_status": decision.status.value,
            "source_separation_decision_id": decision.decision_id,
        },
        "G5": {
            "status": "PASS_SYNTHETIC_DEPTH_PATH_IDENTITY_BOUND",
            "path_content_id": depth.path.content_id,
            "catalogue_product_id": depth.catalogue_product_id,
            "grouping_id": depth.grouping_id,
            "depth_definition_id": depth.depth_definition_id,
            "row_identity_ids": list(depth.row_identity_ids),
            "selection_ids": list(depth.selection_ids),
            "covariance_ids": list(depth.covariance_ids),
            "zoa_mask_id": depth.zoa_mask_id,
            "transport_identity_ids": list(depth.transport_identity_ids),
            "required_nesting_rule": depth.path.nesting_rule,
            "eigenspace_drift_content_id": eigenspace_drift.content_id,
            "eigenspace_identification_status": (
                eigenspace_drift.identification_status
            ),
            "maximum_subspace_angle_radians": (
                eigenspace_drift.maximum_subspace_angle_radians
            ),
        },
        "G6": {
            "status": "BLOCKED_MATCHED_MOCK_OR_PROOF_NOT_REGISTERED",
            "observed_calibration": False,
        },
        "G7": {
            "status": "PASS_SYNTHETIC_UNIDENTIFIED_DIRECTIONS_PRESERVED",
            "design_content_id": design.content_id,
            "covariance_id": shear.covariance_id,
            "response_id": shear.response_id,
            "response_rank": response.response_rank,
            "response_normalizer_id": response.normalizer_id,
            "parameter_labels": list(response.parameter_labels),
            "parameter_roles": list(response.parameter_roles),
            "parameter_dimension": response.parameter_dimension,
            "unidentified_direction_count": response.nullity,
            "right_null_basis": [list(row) for row in response.right_null_basis],
            "source_separation_decision_id": decision.decision_id,
            "claim_tier": CLAIM_TIER,
            "family_identification_gate": FAMILY_GATE,
        },
    }


def legacy_wf_curl_selfcheck() -> dict[str, object]:
    return {
        "schema": "htt.obsstat.cf4_legacy_wf_curl_selfcheck.v1",
        "curl_div_ratio": 0.0089,
        "ratio_unit": "dimensionless",
        "field_derivative_unit": "km_per_s_per_Mpc",
        "status": "STABLE_LEGACY_STENCIL_LIMITED_SELF_CONSISTENCY",
        "physical_vorticity_claim": "FORBIDDEN",
        "potential_flow_claim": "FORBIDDEN",
        "observed_data_executed_by_pr291": False,
        "claim_tier": CLAIM_TIER,
        "family_identification_gate": FAMILY_GATE,
    }


__all__ = [
    "CF4_FEATURE_ORDER_ID",
    "CF4_OPERATOR_IDENTITY_FIELDS",
    "FEATURE_NAMES",
    "FEATURE_UNITS",
    "SCHEMA_VERSION",
    "Cf4DepthPathReport",
    "Cf4EigenspaceDriftReport",
    "Cf4MomentDesign",
    "Cf4Post275Error",
    "Cf4ResponseNullReport",
    "Cf4SyntheticFitReport",
    "Cf4SyntheticShearReport",
    "CorrelatedEstimandComparison",
    "analyze_synthetic_eigenspace_drift",
    "analyze_synthetic_shear",
    "analyze_synthetic_response_nullspace",
    "build_cf4_gate_snapshot",
    "build_cf4_moment_design",
    "build_structural_identified_set",
    "build_synthetic_depth_zoa_path",
    "compare_correlated_estimands",
    "fit_synthetic_cf4_moments",
    "legacy_wf_curl_selfcheck",
    "validate_cf4_operator_identity",
]
