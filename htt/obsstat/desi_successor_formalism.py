"""Observation-neutral DESI BGS successor operator for PR-311.

The module constructs a frozen NGC/SGC redshift-tomographic number-count
feature vector.  Each realization independently refits its random-catalogue
normalization and selection-template nuisance amplitude.  Exactly 1000
EZmocks own the empirical covariance; 25 Abacus realizations are evaluated as
a separate held-out tier.  The outputs are numerical identifiability
diagnostics, never component attribution or a detection claim.
"""

from __future__ import annotations

from dataclasses import dataclass
import math
from typing import Mapping, Sequence

import numpy as np


CAP_ORDER = ("NGC", "SGC")
TOMOGRAPHY = (
    ("z0.1-0.2", 0.1, 0.2),
    ("z0.2-0.3", 0.2, 0.3),
    ("z0.3-0.4", 0.3, 0.4),
)
AXES = ("x", "y", "z")
FEATURE_ORDER = tuple(
    f"{cap}:{bin_id}:{axis}"
    for cap in CAP_ORDER
    for bin_id, _lower, _upper in TOMOGRAPHY
    for axis in AXES
)
EXPECTED_EZMOCK_REALIZATIONS = tuple(range(1, 1001))
EXPECTED_ABACUS_REALIZATIONS = tuple(range(25))
RANK_RELATIVE_TOLERANCE = 1.0e-6
MAXIMUM_COVARIANCE_CONDITION = 1.0e12
SELECTION_DERIVATION_ID = (
    "desi:dr1:v1.5:bgs-bright-mr21.5-official-clustering-selection"
)
SEMANTIC_IDENTITY_FIELDS = (
    "units_contract_id",
    "coordinate_frame_id",
    "sign_orientation_convention_id",
    "directional_convention_id",
    "harmonic_convention_id",
    "mask_id",
    "sky_support_id",
    "covariance_id",
    "null_ensemble_id",
    "transfer_function_spec_id",
)


class DESISuccessorError(ValueError):
    """Raised when the current-stack DESI contract cannot be evaluated."""


def _finite_vector(value: object, *, label: str) -> np.ndarray:
    try:
        array = np.asarray(value, dtype=float)
    except (TypeError, ValueError) as exc:
        raise DESISuccessorError(f"{label} must be a finite vector") from exc
    if array.ndim != 1 or array.size == 0 or not np.all(np.isfinite(array)):
        raise DESISuccessorError(f"{label} must be a finite vector")
    return array


def _finite_matrix(value: object, *, label: str) -> np.ndarray:
    try:
        array = np.asarray(value, dtype=float)
    except (TypeError, ValueError) as exc:
        raise DESISuccessorError(f"{label} must be a finite matrix") from exc
    if array.ndim != 2 or 0 in array.shape or not np.all(np.isfinite(array)):
        raise DESISuccessorError(f"{label} must be a finite matrix")
    return array


@dataclass(frozen=True)
class DESISelection:
    release_id: str
    tracer: str
    base_apparent_r_limit: float
    absolute_magnitude_max: float
    z_min: float
    z_max: float
    caps: tuple[str, ...]
    selection_id: str
    selection_derivation_id: str
    window_ids: tuple[str, ...]
    operator_id: str
    units_contract_id: str
    coordinate_frame_id: str
    sign_orientation_convention_id: str
    directional_convention_id: str
    harmonic_convention_id: str
    mask_id: str
    sky_support_id: str
    covariance_id: str
    null_ensemble_id: str
    transfer_source: str
    transfer_function_spec_id: str


def validate_selection(selection: DESISelection) -> None:
    """Bind the official DR1 BGS_BRIGHT-21.5 cosmology-sample identity."""

    if not isinstance(selection, DESISelection):
        raise DESISuccessorError("DESI selection contract is required")
    if (
        selection.release_id != "DESI_DR1_LSS_IRON_V1_5"
        or selection.tracer != "BGS_BRIGHT-21.5"
        or not math.isclose(selection.base_apparent_r_limit, 19.5)
        or not math.isclose(selection.absolute_magnitude_max, -21.5)
        or not math.isclose(selection.z_min, 0.1)
        or not math.isclose(selection.z_max, 0.4)
        or selection.caps != CAP_ORDER
        or selection.window_ids
        != ("desi:dr1:ngc:random0", "desi:dr1:sgc:random0")
        or selection.selection_id != "desi:dr1:bgs_bright-21.5:z0.1-0.4"
        or selection.selection_derivation_id != SELECTION_DERIVATION_ID
        or selection.operator_id != "desi-pr311-identical-data-null-operator-v1"
        or selection.transfer_source != "none"
        or any(
            not isinstance(getattr(selection, field), str)
            or not getattr(selection, field).strip()
            for field in SEMANTIC_IDENTITY_FIELDS
        )
    ):
        raise DESISuccessorError(
            "DESI selection must be exact official BGS_BRIGHT-21.5 with "
            "base r<19.5, M_r<-21.5, strict 0.1<z<0.4, and ordered NGC/SGC windows"
        )


@dataclass(frozen=True)
class DESIRealization:
    family: str
    realization: int
    tracer: str
    base_apparent_r_limit: float
    absolute_magnitude_max: float
    cap: np.ndarray
    redshift: np.ndarray
    official_sample_member: np.ndarray
    apparent_r_mag: np.ndarray
    absolute_magnitude_r: np.ndarray
    direction: np.ndarray
    weighted_counts: np.ndarray
    random_window_weight: np.ndarray
    nuisance_template: np.ndarray
    selection_id: str
    window_ids: tuple[str, ...]
    operator_id: str

    def __post_init__(self) -> None:
        if self.family not in {"OBSERVED", "EZMOCK", "ABACUS"}:
            raise DESISuccessorError("DESI realization family is unsupported")
        if type(self.realization) is not int or self.realization < 0:
            raise DESISuccessorError("DESI realization identity is invalid")
        cap = np.asarray(self.cap)
        redshift = _finite_vector(self.redshift, label="redshift")
        membership = np.asarray(self.official_sample_member)
        apparent_r = _finite_vector(self.apparent_r_mag, label="apparent r magnitude")
        absolute_r = _finite_vector(
            self.absolute_magnitude_r, label="absolute r magnitude"
        )
        direction = _finite_matrix(self.direction, label="direction")
        counts = _finite_vector(self.weighted_counts, label="weighted counts")
        randoms = _finite_vector(
            self.random_window_weight, label="random-window weights"
        )
        nuisance = _finite_vector(self.nuisance_template, label="nuisance template")
        rows = redshift.size
        if (
            cap.shape != (rows,)
            or membership.shape != (rows,)
            or membership.dtype.kind != "b"
            or not np.all(membership)
            or apparent_r.shape != (rows,)
            or absolute_r.shape != (rows,)
            or direction.shape != (rows, 3)
            or counts.shape != (rows,)
            or randoms.shape != (rows,)
            or nuisance.shape != (rows,)
            or not set(cap).issubset(CAP_ORDER)
            or set(cap) != set(CAP_ORDER)
            or np.any(counts < 0.0)
            or np.any(randoms <= 0.0)
            or np.any(redshift <= 0.1)
            or np.any(redshift >= 0.4)
            or np.any(apparent_r >= self.base_apparent_r_limit)
            or np.any(absolute_r >= self.absolute_magnitude_max)
            or not np.allclose(
                np.linalg.norm(direction, axis=1), 1.0, atol=1.0e-12, rtol=1.0e-12
            )
        ):
            raise DESISuccessorError(
                "DESI rows must be official BGS_BRIGHT-21.5 members satisfying "
                "r<19.5, M_r<-21.5, and strict 0.1<z<0.4"
            )
        object.__setattr__(self, "cap", cap.astype(str, copy=True))
        object.__setattr__(self, "redshift", redshift.copy())
        object.__setattr__(self, "official_sample_member", membership.copy())
        object.__setattr__(self, "apparent_r_mag", apparent_r.copy())
        object.__setattr__(self, "absolute_magnitude_r", absolute_r.copy())
        object.__setattr__(self, "direction", direction.copy())
        object.__setattr__(self, "weighted_counts", counts.copy())
        object.__setattr__(self, "random_window_weight", randoms.copy())
        object.__setattr__(self, "nuisance_template", nuisance.copy())


@dataclass(frozen=True)
class DESIFitResult:
    family: str
    realization: int
    feature_order: tuple[str, ...]
    features: np.ndarray
    alpha_hat: Mapping[str, float]
    nuisance_hat: Mapping[str, float]
    operator_id: str


def _bin_mask(redshift: np.ndarray, index: int, lower: float, upper: float) -> np.ndarray:
    lower_mask = redshift > lower if index == 0 else redshift >= lower
    return lower_mask & (redshift < upper)


def fit_realization(
    realization: DESIRealization, selection: DESISelection
) -> DESIFitResult:
    """Apply one identical estimator and refit alpha/nuisance per cap and bin."""

    validate_selection(selection)
    if not isinstance(realization, DESIRealization):
        raise DESISuccessorError("DESI realization input is required")
    if (
        realization.tracer != selection.tracer
        or not math.isclose(
            realization.base_apparent_r_limit, selection.base_apparent_r_limit
        )
        or not math.isclose(
            realization.absolute_magnitude_max, selection.absolute_magnitude_max
        )
        or realization.selection_id != selection.selection_id
        or realization.window_ids != selection.window_ids
        or realization.operator_id != selection.operator_id
    ):
        raise DESISuccessorError(
            "DESI data/null selection, cap window, or operator identity drifted"
        )
    features: list[float] = []
    alpha_hat: dict[str, float] = {}
    nuisance_hat: dict[str, float] = {}
    covered = np.zeros(realization.redshift.size, dtype=bool)
    for cap in CAP_ORDER:
        for bin_index, (bin_id, lower, upper) in enumerate(TOMOGRAPHY):
            selected = (realization.cap == cap) & _bin_mask(
                realization.redshift, bin_index, lower, upper
            )
            if np.count_nonzero(selected) < 2:
                raise DESISuccessorError("DESI tomography is empty or metadata-only")
            covered |= selected
            randoms = realization.random_window_weight[selected]
            counts = realization.weighted_counts[selected]
            alpha = float(np.sum(counts) / np.sum(randoms))
            if not math.isfinite(alpha) or alpha <= 0.0:
                raise DESISuccessorError("per-realization cap normalization is invalid")
            delta = counts / (alpha * randoms) - 1.0
            template = realization.nuisance_template[selected]
            centered = template - float(np.sum(randoms * template) / np.sum(randoms))
            denominator = float(np.sum(randoms * centered * centered))
            if not math.isfinite(denominator) or denominator <= 0.0:
                raise DESISuccessorError("per-realization nuisance refit is singular")
            beta = float(np.sum(randoms * delta * centered) / denominator)
            residual = delta - beta * centered
            vector = np.sum(
                randoms[:, None] * residual[:, None] * realization.direction[selected],
                axis=0,
            ) / np.sum(randoms)
            if not np.all(np.isfinite(vector)):
                raise DESISuccessorError("DESI tomographic feature is non-finite")
            key = f"{cap}:{bin_id}"
            alpha_hat[key] = alpha
            nuisance_hat[key] = beta
            features.extend(float(value) for value in vector)
    if not np.all(covered):
        raise DESISuccessorError("DESI rows escaped the frozen tomography")
    return DESIFitResult(
        family=realization.family,
        realization=realization.realization,
        feature_order=FEATURE_ORDER,
        features=np.asarray(features, dtype=float),
        alpha_hat=alpha_hat,
        nuisance_hat=nuisance_hat,
        operator_id=selection.operator_id,
    )


@dataclass(frozen=True)
class MockSupport:
    ezmock_count: int
    abacus_count: int
    covariance_owner: str
    abacus_role: str
    pooled_with_ezmock: bool
    feature_order: tuple[str, ...]
    covariance: np.ndarray
    ezmock_features: np.ndarray
    abacus_features: np.ndarray
    condition_number: float


def _exact_inventory(
    rows: Sequence[DESIRealization | DESIFitResult],
    *,
    family: str,
    expected: tuple[int, ...],
) -> tuple[DESIRealization | DESIFitResult, ...]:
    if isinstance(rows, (str, bytes)):
        raise DESISuccessorError(f"{family} inventory is malformed")
    ordered = tuple(rows)
    if len(ordered) != len(expected):
        raise DESISuccessorError(
            f"{family} inventory must contain exactly {len(expected)} realizations"
        )
    if tuple(row.realization for row in ordered) != expected or any(
        row.family != family for row in ordered
    ):
        raise DESISuccessorError(f"{family} inventory order or family drifted")
    return ordered


def _as_fit(
    row: DESIRealization | DESIFitResult, selection: DESISelection
) -> DESIFitResult:
    if isinstance(row, DESIRealization):
        return fit_realization(row, selection)
    if (
        not isinstance(row, DESIFitResult)
        or row.feature_order != FEATURE_ORDER
        or row.operator_id != selection.operator_id
        or row.features.shape != (len(FEATURE_ORDER),)
        or not np.all(np.isfinite(row.features))
        or set(row.alpha_hat)
        != {
            f"{cap}:{bin_id}"
            for cap in CAP_ORDER
            for bin_id, _lower, _upper in TOMOGRAPHY
        }
        or set(row.nuisance_hat) != set(row.alpha_hat)
    ):
        raise DESISuccessorError("pre-fitted realization operator identity drifted")
    return row


def build_mock_support(
    ezmock: Sequence[DESIRealization | DESIFitResult],
    abacus: Sequence[DESIRealization | DESIFitResult],
    selection: DESISelection,
) -> MockSupport:
    """Build covariance from EZmocks and keep Abacus strictly held out."""

    validate_selection(selection)
    ez_rows = _exact_inventory(
        ezmock, family="EZMOCK", expected=EXPECTED_EZMOCK_REALIZATIONS
    )
    ab_rows = _exact_inventory(
        abacus, family="ABACUS", expected=EXPECTED_ABACUS_REALIZATIONS
    )
    ez_features = np.asarray(
        [_as_fit(row, selection).features for row in ez_rows], dtype=float
    )
    ab_features = np.asarray(
        [_as_fit(row, selection).features for row in ab_rows], dtype=float
    )
    covariance = np.cov(ez_features, rowvar=False, ddof=1)
    covariance = 0.5 * (covariance + covariance.T)
    condition = float(np.linalg.cond(covariance))
    if (
        covariance.shape != (len(FEATURE_ORDER), len(FEATURE_ORDER))
        or not np.all(np.isfinite(covariance))
        or np.linalg.matrix_rank(covariance) != len(FEATURE_ORDER)
        or not math.isfinite(condition)
        or condition > MAXIMUM_COVARIANCE_CONDITION
    ):
        raise DESISuccessorError("EZMOCK full covariance is singular or ill-conditioned")
    return MockSupport(
        ezmock_count=len(ez_rows),
        abacus_count=len(ab_rows),
        covariance_owner="EZMOCK_1000_ONLY",
        abacus_role="SEPARATE_HELD_OUT_VALIDATION",
        pooled_with_ezmock=False,
        feature_order=FEATURE_ORDER,
        covariance=covariance,
        ezmock_features=ez_features,
        abacus_features=ab_features,
        condition_number=condition,
    )


def _scaled_whitened(
    lower: np.ndarray, matrix: object, *, label: str
) -> np.ndarray:
    values = _finite_matrix(matrix, label=label)
    if values.shape[0] != len(FEATURE_ORDER):
        raise DESISuccessorError(f"{label} row count drifted")
    whitened = np.linalg.solve(lower, values)
    norms = np.linalg.norm(whitened, axis=0)
    if not np.all(np.isfinite(norms)) or np.any(norms <= np.finfo(float).tiny):
        raise DESISuccessorError(f"{label} contains a zero response column")
    return whitened / norms


def _relative_rank(matrix: np.ndarray) -> tuple[int, list[float]]:
    singular = np.linalg.svd(matrix, compute_uv=False)
    tolerance = RANK_RELATIVE_TOLERANCE * float(singular[0])
    return int(np.count_nonzero(singular > tolerance)), singular.tolist()


def evaluate_response_rank(
    covariance: object,
    *,
    nuisance_response: object,
    candidate_response: object,
    response_feature_order: Sequence[str] = FEATURE_ORDER,
) -> dict[str, object]:
    """Return a covariance-whitened, scale-invariant incremental-rank receipt."""

    if tuple(response_feature_order) != FEATURE_ORDER:
        raise DESISuccessorError("response feature order drifted")
    cov = _finite_matrix(covariance, label="EZMOCK covariance")
    if cov.shape != (len(FEATURE_ORDER), len(FEATURE_ORDER)):
        raise DESISuccessorError("response covariance shape drifted")
    try:
        lower = np.linalg.cholesky(cov)
    except np.linalg.LinAlgError as exc:
        raise DESISuccessorError("response covariance is not positive definite") from exc
    nuisance = _scaled_whitened(lower, nuisance_response, label="nuisance response")
    candidate = _scaled_whitened(lower, candidate_response, label="candidate response")
    base_rank, base_singular = _relative_rank(nuisance)
    total_rank, total_singular = _relative_rank(np.column_stack([nuisance, candidate]))
    incremental = total_rank - base_rank
    expected_base = nuisance.shape[1]
    expected = candidate.shape[1]
    full_rank = base_rank == expected_base and incremental == expected
    return {
        "status": (
            "FULL_INCREMENTAL_RANK"
            if full_rank
            else "NON_IDENTIFIED_ABSTAIN"
        ),
        "base_rank": base_rank,
        "expected_base_rank": expected_base,
        "total_rank": total_rank,
        "incremental_rank": incremental,
        "expected_incremental_rank": expected,
        "whitening": "cholesky_left",
        "column_scaling": "covariance_whitened_l2",
        "relative_tolerance": RANK_RELATIVE_TOLERANCE,
        "base_singular_values": base_singular,
        "total_singular_values": total_singular,
    }


def _confusion_diagnostic(
    covariance: np.ndarray, templates: object
) -> dict[str, object]:
    matrix = _finite_matrix(templates, label="component confusion templates")
    if matrix.shape != (len(FEATURE_ORDER), 3):
        raise DESISuccessorError("component confusion template shape drifted")
    lower = np.linalg.cholesky(covariance)
    scaled = _scaled_whitened(lower, matrix, label="component confusion templates")
    overlap = np.abs(scaled.T @ scaled)
    return {
        "component_order": ["clustering", "kinematic", "selection"],
        "normalized_overlap_matrix": overlap.tolist(),
        "causal_attribution_identified": False,
        "interpretation": "response-overlap diagnostic only",
    }


def analyze_successor_formalism(
    ezmock: Sequence[DESIRealization | DESIFitResult],
    abacus: Sequence[DESIRealization | DESIFitResult],
    *,
    selection: DESISelection,
    nuisance_response: object,
    candidate_response: object,
    confusion_templates: object,
    response_feature_order: Sequence[str] = FEATURE_ORDER,
    observed: bool,
    observed_realization: DESIRealization | None = None,
) -> dict[str, object]:
    """Evaluate synthetic/mock closure or an explicitly attended observed row."""

    if type(observed) is not bool or (observed != (observed_realization is not None)):
        raise DESISuccessorError("observed mode requires one explicit observed realization")
    if tuple(response_feature_order) != FEATURE_ORDER:
        raise DESISuccessorError("response feature order drifted")
    support = build_mock_support(ezmock, abacus, selection)
    rank = evaluate_response_rank(
        support.covariance,
        nuisance_response=nuisance_response,
        candidate_response=candidate_response,
        response_feature_order=response_feature_order,
    )
    confusion = _confusion_diagnostic(support.covariance, confusion_templates)
    difference = np.mean(support.abacus_features, axis=0) - np.mean(
        support.ezmock_features, axis=0
    )
    whitened_difference = np.linalg.solve(
        np.linalg.cholesky(support.covariance), difference
    )
    result: dict[str, object] = {
        "terminal_disposition": (
            "SYNTHETIC_OPERATOR_CLOSURE_PASS"
            if rank["status"] == "FULL_INCREMENTAL_RANK" and not observed
            else "OBSERVED_OPERATOR_DIAGNOSTIC_COMPLETE"
            if rank["status"] == "FULL_INCREMENTAL_RANK"
            else "NON_IDENTIFIED_ABSTAIN"
        ),
        "selection": {
            "release_id": selection.release_id,
            "tracer": selection.tracer,
            "base_apparent_r_limit": selection.base_apparent_r_limit,
            "absolute_magnitude_max": selection.absolute_magnitude_max,
            "redshift_interval": "0.1<z<0.4",
            "caps": list(selection.caps),
            "selection_id": selection.selection_id,
            "selection_derivation_id": selection.selection_derivation_id,
            "window_ids": list(selection.window_ids),
            "operator_id": selection.operator_id,
            "semantic_identities": {
                field: getattr(selection, field)
                for field in SEMANTIC_IDENTITY_FIELDS
            },
            "transfer_source": selection.transfer_source,
        },
        "mock_support": {
            "ezmock_count": support.ezmock_count,
            "abacus_count": support.abacus_count,
            "covariance_owner": support.covariance_owner,
            "abacus_role": support.abacus_role,
            "pooled_with_ezmock": support.pooled_with_ezmock,
            "feature_order": list(support.feature_order),
            "covariance_condition_number": support.condition_number,
        },
        "covariance": support.covariance.tolist(),
        "abacus_validation": {
            "count": support.abacus_count,
            "pooled_with_ezmock": False,
            "whitened_mean_shift_norm": float(np.linalg.norm(whitened_difference)),
            "role": support.abacus_role,
        },
        "response_rank": rank,
        "component_confusion": confusion,
        "p_value": None,
        "forced_source_label": None,
        "observed_statistic_seen": observed,
        "observed_science_executed": observed,
        "artifact_metadata": {
            "owner": "OBSSTAT",
            "artifact_mode": (
                "attended_observed_operator_diagnostic"
                if observed
                else "synthetic_operator_diagnostic"
            ),
            "claim_tier": "diagnostic_only",
            "covariance_status": "FULL_EZMOCK_1000_COVARIANCE",
            "null_mock_status": "EZMOCK_1000_WITH_ABACUS_25_HELD_OUT",
            "public_use": False,
            "allowed_use": "internal_operator_validation",
            "forbidden_uses": [
                "causal_component_attribution",
                "anisotropy_detection",
                "geometry_or_native_solver_claim",
            ],
        },
    }
    if observed_realization is not None:
        observed_fit = fit_realization(observed_realization, selection)
        result["observed_features"] = observed_fit.features.tolist()
        result["observed_refit"] = {
            "alpha_hat": dict(observed_fit.alpha_hat),
            "nuisance_hat": dict(observed_fit.nuisance_hat),
        }
    return result
