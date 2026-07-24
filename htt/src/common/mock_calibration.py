"""common.mock_calibration — Mode 2 mock-bank Layer D machinery (COMMON-F).

Implements the isotropic-null and injected-dipole mock pipelines plus the
coverage/bias diagnostics required for the ``fiducial_posterior`` artefact
(BASS_PY_HTT_TSC_RESEARCH_PLAN §6.4 and §6.7).

The REG-01 item ``test_mock_coverage_within_bounds`` (§6.10) enforces
``coverage_68pct ∈ [0.60, 0.76]`` on a controlled WLS-covariance mock;
that is the core property checked here. Dynesty is *not* a hard dependency
— callers pass in any estimator returning ``(V_hat, cov)`` (WLS bootstrap
is the default).
"""
from __future__ import annotations

from dataclasses import dataclass, field
import hashlib
import json
import math
import platform
import re
from typing import Any, Callable, Mapping, Sequence

import numpy as np

from common.bulkflow_estimator import (
    BulkFlowCatalogue,
    BulkFlowFit,
    wls_bulk_flow,
)
from common.contracts import (
    ClaimTier,
    ImplementationScope,
    MockCalibrationReport,
    Owner,
    SkySelectionConfig,
    normalize_claim_tier,
    normalize_implementation_scope,
    normalize_owner,
)
from common.healpix_selection import (
    build_angular_completeness,
    build_zoa_mask,
    compute_selection_weights,
    lb_to_pix,
)
from common.sky_geometry import lb_to_unitvec, unitvec_to_lb

__all__ = [
    "AxisMockCalibrationGateDecision",
    "AxisMockCalibrationReport",
    "AxisMockCalibrationThresholds",
    "InjectedMockReport",
    "build_axis_mock_calibration_report",
    "evaluate_directional_claim_mock_gate",
    "generate_isotropic_mock",
    "generate_injected_dipole_mock",
    "apply_same_mask",
    "recovered_bias",
    "coverage_test",
    "run_zoa_null_mocks",
    "run_injected_dipole_mocks",
    "apply_bias_correction",
    "mock_calibration_report_artifact",
]

EstimatorFn = Callable[
    [np.ndarray, np.ndarray, np.ndarray, np.ndarray, np.ndarray],
    tuple[np.ndarray, np.ndarray],
]

_SHA256_RE = re.compile(r"^sha256:[0-9a-fA-F]{64}$")
_SAFE_CLAIM_TARGETS = {
    "diagnostic_direction",
    "production_axis_candidate",
    "harmonic_synthesis_gate",
}
_PASSING_COVARIANCE_STATUSES = {
    "directional_mock_covariance_available",
    "directional_mock_covariance_calibrated",
}
_FORBIDDEN_AXIS_REPORT_PHRASES = (
    "family identified",
    "family identification",
    "geometry detected",
    "geometry detection",
    "posterior odds",
    "bayes factor",
    "mio evidence",
    "mio posterior",
    "native solver result",
    "validated as native",
    "bass_native",
    "truth certificate",
)
_CLAIM_TIER_RANK = {
    ClaimTier.BLOCKED: -1,
    ClaimTier.DIAGNOSTIC_ONLY: 0,
    ClaimTier.EXPLORATORY: 0,
    ClaimTier.CONDITIONAL: 1,
    ClaimTier.VALIDATED: 2,
}


def _jsonify(obj: Any) -> Any:
    """Recursively convert numpy-heavy structures to JSON-native values."""
    if isinstance(obj, float):
        return obj if np.isfinite(obj) else None
    if isinstance(obj, np.ndarray):
        return obj.tolist()
    if isinstance(obj, np.generic):
        item = obj.item()
        return item if not isinstance(item, float) or np.isfinite(item) else None
    if isinstance(obj, Mapping):
        return {str(k): _jsonify(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [_jsonify(v) for v in obj]
    return obj


def _config_hash(payload: Mapping[str, Any]) -> str:
    """Stable SHA256 hash for artifact configuration payloads."""
    blob = json.dumps(_jsonify(payload), sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(blob.encode("utf-8")).hexdigest()


def _hash_payload(payload: Mapping[str, Any]) -> str:
    blob = json.dumps(_jsonify(payload), sort_keys=True, separators=(",", ":"))
    return "sha256:" + hashlib.sha256(blob.encode("utf-8")).hexdigest()


def _is_sha256(value: str) -> bool:
    return _SHA256_RE.fullmatch(str(value).strip()) is not None


def _require_sha256(value: str, field_name: str) -> str:
    text = str(value).strip()
    if not _is_sha256(text):
        raise ValueError(f"{field_name} must be sha256:<64 hex chars>")
    return text


def _require_sha256_sequence(
    values: Sequence[str],
    field_name: str,
) -> tuple[str, ...]:
    if not values:
        raise ValueError(f"{field_name} must be non-empty")
    return tuple(_require_sha256(value, field_name) for value in values)


def _finite_float(value: float, field_name: str) -> float:
    out = float(value)
    if not math.isfinite(out):
        raise ValueError(f"{field_name} must be finite")
    return out


def _unit_interval(value: float, field_name: str) -> float:
    out = _finite_float(value, field_name)
    if not 0.0 <= out <= 1.0:
        raise ValueError(f"{field_name} must be in [0, 1]")
    return out


def _wilson_interval(k: int, n: int, *, z: float = 1.0) -> tuple[float, float]:
    """Wilson score interval for a binomial proportion.

    ``z=1`` gives the one-sigma scale used by the mock-calibration metadata.
    """

    if n <= 0:
        raise ValueError("Wilson interval requires n > 0")
    if k < 0 or k > n:
        raise ValueError("Wilson interval requires 0 <= k <= n")
    p_hat = k / n
    z2 = z * z
    denom = 1.0 + z2 / n
    center = (p_hat + z2 / (2.0 * n)) / denom
    half_width = z / denom * math.sqrt(
        (p_hat * (1.0 - p_hat) / n) + (z2 / (4.0 * n * n))
    )
    return max(0.0, center - half_width), min(1.0, center + half_width)


def _proportion_count(value: float, n: int) -> int:
    return max(0, min(n, int(round(float(value) * n))))


def _event_count(value: int | None, rate: float, n: int, field_name: str) -> int:
    if value is None:
        raise ValueError(f"{field_name} is required")
    out = int(value)
    if out < 0 or out > n:
        raise ValueError(f"{field_name} must satisfy 0 <= {field_name} <= n")
    rate_from_count = out / n if n > 0 else 0.0
    tolerance = 0.5 / n if n > 0 else 0.0
    if abs(rate_from_count - float(rate)) > tolerance + 1.0e-12:
        raise ValueError(
            f"{field_name} is inconsistent with rate {rate!r} for n={n}"
        )
    return out


def _tier_exceeds(requested: ClaimTier, ceiling: ClaimTier) -> bool:
    return _CLAIM_TIER_RANK[requested] > _CLAIM_TIER_RANK[ceiling]


def _dedupe(values: Sequence[str]) -> tuple[str, ...]:
    seen: set[str] = set()
    out: list[str] = []
    for value in values:
        if value not in seen:
            seen.add(value)
            out.append(value)
    return tuple(out)


def _reject_axis_report_reserved_language(payload: Mapping[str, Any]) -> None:
    text = json.dumps(_jsonify(payload), sort_keys=True).lower().replace("_", " ")
    for phrase in _FORBIDDEN_AXIS_REPORT_PHRASES:
        if phrase in text:
            raise ValueError(
                "AxisMockCalibrationReport metadata contains reserved claim "
                f"language: {phrase!r}"
            )


def _validate_sky_support_metadata(
    metadata: Mapping[str, Any],
    *,
    sky_support_hash: str,
    mask_hash: str,
    scan_volume_hash: str,
) -> None:
    required = {
        "selection_mode",
        "sky_support_hash",
        "mask_hash",
        "mock_coverage_status",
        "scan_volume_hash",
        "coordinate_frame",
        "sky_fraction",
        "completeness_status",
        "pixelization",
        "nside",
    }
    missing = sorted(key for key in required if key not in metadata)
    if missing:
        raise ValueError(
            "sky_support_metadata missing required fields: " + ", ".join(missing)
        )
    if metadata["sky_support_hash"] != sky_support_hash:
        raise ValueError("sky_support_metadata.sky_support_hash mismatch")
    if metadata["mask_hash"] != mask_hash:
        raise ValueError("sky_support_metadata.mask_hash mismatch")
    if metadata["scan_volume_hash"] != scan_volume_hash:
        raise ValueError("sky_support_metadata.scan_volume_hash mismatch")
    for field_name in (
        "selection_mode",
        "mock_coverage_status",
        "coordinate_frame",
        "completeness_status",
        "pixelization",
    ):
        if not str(metadata[field_name]).strip():
            raise ValueError(f"sky_support_metadata.{field_name} must be non-empty")
    sky_fraction = _finite_float(
        float(metadata["sky_fraction"]),
        "sky_support_metadata.sky_fraction",
    )
    if not 0.0 < sky_fraction <= 1.0:
        raise ValueError("sky_support_metadata.sky_fraction must be in (0, 1]")
    if int(metadata["nside"]) <= 0:
        raise ValueError("sky_support_metadata.nside must be positive")


@dataclass(frozen=True)
class AxisMockCalibrationThresholds:
    """Threshold bundle for directional mock-calibration gates."""

    min_retention_fraction: float = 0.90
    max_bias_direction_deg: float = 5.0
    coverage_68_window: tuple[float, float] = (0.60, 0.76)
    max_false_positive_rate: float = 0.05
    min_n_mock: int = 100
    min_response_rank: int = 3
    min_effective_rank: float = 2.0
    max_condition_number: float = 1.0e8
    max_null_space_dimension: int = 0

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "min_retention_fraction",
            _unit_interval(self.min_retention_fraction, "min_retention_fraction"),
        )
        object.__setattr__(
            self,
            "max_bias_direction_deg",
            _finite_float(self.max_bias_direction_deg, "max_bias_direction_deg"),
        )
        lower, upper = self.coverage_68_window
        lower = _unit_interval(lower, "coverage_68_window[0]")
        upper = _unit_interval(upper, "coverage_68_window[1]")
        if lower > upper:
            raise ValueError("coverage_68_window must satisfy lower <= upper")
        object.__setattr__(self, "coverage_68_window", (lower, upper))
        object.__setattr__(
            self,
            "max_false_positive_rate",
            _unit_interval(self.max_false_positive_rate, "max_false_positive_rate"),
        )
        if int(self.min_n_mock) <= 0:
            raise ValueError("min_n_mock must be positive")
        object.__setattr__(self, "min_n_mock", int(self.min_n_mock))
        if int(self.min_response_rank) <= 0:
            raise ValueError("min_response_rank must be positive")
        object.__setattr__(self, "min_response_rank", int(self.min_response_rank))
        object.__setattr__(
            self,
            "min_effective_rank",
            _finite_float(self.min_effective_rank, "min_effective_rank"),
        )
        object.__setattr__(
            self,
            "max_condition_number",
            _finite_float(self.max_condition_number, "max_condition_number"),
        )
        if self.max_condition_number <= 0.0:
            raise ValueError("max_condition_number must be positive")
        if int(self.max_null_space_dimension) < 0:
            raise ValueError("max_null_space_dimension must be non-negative")
        object.__setattr__(
            self,
            "max_null_space_dimension",
            int(self.max_null_space_dimension),
        )

    def to_metadata(self) -> dict[str, object]:
        return {
            "min_retention_fraction": self.min_retention_fraction,
            "max_bias_direction_deg": self.max_bias_direction_deg,
            "coverage_68_window": list(self.coverage_68_window),
            "max_false_positive_rate": self.max_false_positive_rate,
            "min_n_mock": self.min_n_mock,
            "min_response_rank": self.min_response_rank,
            "min_effective_rank": self.min_effective_rank,
            "max_condition_number": self.max_condition_number,
            "max_null_space_dimension": self.max_null_space_dimension,
        }


@dataclass(frozen=True)
class AxisMockCalibrationReport:
    """HTT-owned directional mock-calibration report for axis claim gates."""

    claim_target: str
    n_mock_requested: int
    n_mock_succeeded: int
    bias_direction_deg: float
    coverage_68: float
    false_positive_rate: float
    null_ensemble: str
    detection_rule: str
    look_elsewhere_trials: int
    scan_trial_count: int
    scan_trial_hash: str
    response_rank: int
    effective_rank: float
    null_space_dimension: int
    condition_number: float
    sky_support_hash: str
    mask_hash: str
    scan_volume_hash: str
    config_hash: str
    input_hashes: tuple[str, ...]
    covariance_status: str
    generating_command: str
    git_commit: str | None
    worktree_state: str
    sky_support_status: str = "pr040_sky_support_attached"
    sky_support_metadata: Mapping[str, Any] | None = None
    coverage_68_count: int | None = None
    false_positive_count: int | None = None
    bias_direction_p95_deg: float | None = None
    thresholds: AxisMockCalibrationThresholds = field(
        default_factory=AxisMockCalibrationThresholds
    )
    owner: Owner | str = Owner.HTT
    implementation_scope: ImplementationScope | str = ImplementationScope.HTT
    claim_tier: ClaimTier | str = ClaimTier.DIAGNOSTIC_ONLY
    transfer_source: str = "none"
    random_seeds: tuple[int, ...] = ()
    caveats: tuple[str, ...] = (
        "pre_solver_directional_mock_calibration_only",
        "not_a_native_solver_validation",
        "does_not_identify_bianchi_family",
    )

    def __post_init__(self) -> None:
        owner = normalize_owner(self.owner)
        scope = normalize_implementation_scope(self.implementation_scope)
        claim_tier = normalize_claim_tier(self.claim_tier)
        object.__setattr__(self, "owner", owner)
        object.__setattr__(self, "implementation_scope", scope)
        object.__setattr__(self, "claim_tier", claim_tier)
        if owner is not Owner.HTT:
            raise ValueError("AxisMockCalibrationReport.owner must be HTT")
        if scope is not ImplementationScope.HTT:
            raise ValueError(
                "AxisMockCalibrationReport.implementation_scope must be htt"
            )
        if claim_tier is not ClaimTier.DIAGNOSTIC_ONLY:
            raise ValueError(
                "AxisMockCalibrationReport is gate metadata; claim_tier must be "
                "diagnostic_only"
            )
        if self.claim_target not in _SAFE_CLAIM_TARGETS:
            raise ValueError(
                "claim_target must be one of "
                f"{sorted(_SAFE_CLAIM_TARGETS)}"
            )
        if int(self.n_mock_requested) <= 0:
            raise ValueError("n_mock_requested must be positive")
        if int(self.n_mock_succeeded) < 0:
            raise ValueError("n_mock_succeeded must be non-negative")
        if int(self.n_mock_succeeded) > int(self.n_mock_requested):
            raise ValueError("n_mock_succeeded cannot exceed n_mock_requested")
        object.__setattr__(self, "n_mock_requested", int(self.n_mock_requested))
        object.__setattr__(self, "n_mock_succeeded", int(self.n_mock_succeeded))
        object.__setattr__(
            self,
            "bias_direction_deg",
            _finite_float(self.bias_direction_deg, "bias_direction_deg"),
        )
        if self.bias_direction_deg < 0.0:
            raise ValueError("bias_direction_deg must be non-negative")
        object.__setattr__(
            self,
            "coverage_68",
            _unit_interval(self.coverage_68, "coverage_68"),
        )
        object.__setattr__(
            self,
            "false_positive_rate",
            _unit_interval(self.false_positive_rate, "false_positive_rate"),
        )
        if not str(self.null_ensemble).strip():
            raise ValueError("null_ensemble must be non-empty")
        if not str(self.detection_rule).strip():
            raise ValueError("detection_rule must be non-empty")
        if int(self.look_elsewhere_trials) <= 0:
            raise ValueError("look_elsewhere_trials must be positive")
        object.__setattr__(
            self, "look_elsewhere_trials", int(self.look_elsewhere_trials)
        )
        if int(self.scan_trial_count) <= 0:
            raise ValueError("scan_trial_count must be positive")
        object.__setattr__(self, "scan_trial_count", int(self.scan_trial_count))
        object.__setattr__(
            self,
            "scan_trial_hash",
            _require_sha256(self.scan_trial_hash, "scan_trial_hash"),
        )
        if int(self.response_rank) < 0:
            raise ValueError("response_rank must be non-negative")
        object.__setattr__(self, "response_rank", int(self.response_rank))
        object.__setattr__(
            self,
            "effective_rank",
            _finite_float(self.effective_rank, "effective_rank"),
        )
        if int(self.null_space_dimension) < 0:
            raise ValueError("null_space_dimension must be non-negative")
        object.__setattr__(
            self, "null_space_dimension", int(self.null_space_dimension)
        )
        object.__setattr__(
            self,
            "condition_number",
            _finite_float(self.condition_number, "condition_number"),
        )
        if self.condition_number <= 0.0:
            raise ValueError("condition_number must be positive")
        object.__setattr__(
            self,
            "sky_support_hash",
            _require_sha256(self.sky_support_hash, "sky_support_hash"),
        )
        object.__setattr__(
            self,
            "mask_hash",
            _require_sha256(self.mask_hash, "mask_hash"),
        )
        object.__setattr__(
            self,
            "scan_volume_hash",
            _require_sha256(self.scan_volume_hash, "scan_volume_hash"),
        )
        object.__setattr__(
            self,
            "config_hash",
            _require_sha256(self.config_hash, "config_hash"),
        )
        object.__setattr__(
            self,
            "input_hashes",
            _require_sha256_sequence(self.input_hashes, "input_hashes"),
        )
        if not str(self.covariance_status).strip():
            raise ValueError("covariance_status must be non-empty")
        if not str(self.generating_command).strip():
            raise ValueError("generating_command must be non-empty")
        if not str(self.worktree_state).strip():
            raise ValueError("worktree_state must be non-empty")
        transfer_source = str(self.transfer_source).strip()
        if not transfer_source:
            raise ValueError("transfer_source must be non-empty")
        if transfer_source != "none":
            raise ValueError(
                "AxisMockCalibrationReport.transfer_source must be 'none' "
                "until a real transfer registry gate is wired"
            )
        object.__setattr__(self, "transfer_source", transfer_source)
        if not str(self.sky_support_status).strip():
            raise ValueError("sky_support_status must be non-empty")
        object.__setattr__(
            self,
            "sky_support_status",
            str(self.sky_support_status).strip(),
        )
        if self.sky_support_metadata is None:
            object.__setattr__(self, "sky_support_metadata", None)
        else:
            sky_support_metadata = dict(self.sky_support_metadata)
            _validate_sky_support_metadata(
                sky_support_metadata,
                sky_support_hash=self.sky_support_hash,
                mask_hash=self.mask_hash,
                scan_volume_hash=self.scan_volume_hash,
            )
            object.__setattr__(self, "sky_support_metadata", sky_support_metadata)
        object.__setattr__(
            self,
            "random_seeds",
            tuple(int(seed) for seed in self.random_seeds),
        )
        object.__setattr__(
            self,
            "coverage_68_count",
            _event_count(
                self.coverage_68_count,
                self.coverage_68,
                self.n_mock_succeeded,
                "coverage_68_count",
            ),
        )
        object.__setattr__(
            self,
            "false_positive_count",
            _event_count(
                self.false_positive_count,
                self.false_positive_rate,
                self.n_mock_succeeded,
                "false_positive_count",
            ),
        )
        if self.bias_direction_p95_deg is None:
            raise ValueError("bias_direction_p95_deg is required")
        object.__setattr__(
            self,
            "bias_direction_p95_deg",
            _finite_float(
                self.bias_direction_p95_deg,
                "bias_direction_p95_deg",
            ),
        )
        if self.bias_direction_p95_deg < self.bias_direction_deg:
            raise ValueError(
                "bias_direction_p95_deg must be >= bias_direction_deg"
            )
        object.__setattr__(
            self,
            "caveats",
            tuple(str(item) for item in self.caveats),
        )
        if not self.caveats:
            raise ValueError("caveats must be non-empty")
        _reject_axis_report_reserved_language(
            {
                "claim_target": self.claim_target,
                "null_ensemble": self.null_ensemble,
                "detection_rule": self.detection_rule,
                "covariance_status": self.covariance_status,
                "transfer_source": self.transfer_source,
                "sky_support_status": self.sky_support_status,
                "caveats": self.caveats,
            }
        )

    @property
    def retention_fraction(self) -> float:
        return self.n_mock_succeeded / self.n_mock_requested

    @property
    def false_positive_rate_adjusted(self) -> float:
        return min(1.0, self.false_positive_rate * self.look_elsewhere_trials)

    @property
    def false_positive_rate_interval_adjusted(self) -> tuple[float, float]:
        if self.n_mock_succeeded <= 0:
            return 0.0, 1.0
        lower, upper = _wilson_interval(
            int(self.false_positive_count or 0),
            self.n_mock_succeeded,
        )
        return (
            min(1.0, lower * self.look_elsewhere_trials),
            min(1.0, upper * self.look_elsewhere_trials),
        )

    @property
    def coverage_68_interval(self) -> tuple[float, float]:
        if self.n_mock_succeeded <= 0:
            return 0.0, 1.0
        return _wilson_interval(
            int(self.coverage_68_count or 0),
            self.n_mock_succeeded,
        )

    @property
    def blocked_reasons(self) -> tuple[str, ...]:
        thresholds = self.thresholds
        policy = AxisMockCalibrationThresholds()
        lower, upper = thresholds.coverage_68_window
        blocked: list[str] = []
        if (
            thresholds.min_retention_fraction < policy.min_retention_fraction
            or thresholds.max_bias_direction_deg > policy.max_bias_direction_deg
            or lower < policy.coverage_68_window[0]
            or upper > policy.coverage_68_window[1]
            or thresholds.max_false_positive_rate
            > policy.max_false_positive_rate
            or thresholds.min_n_mock < policy.min_n_mock
            or thresholds.min_response_rank < policy.min_response_rank
            or thresholds.min_effective_rank < policy.min_effective_rank
            or thresholds.max_condition_number > policy.max_condition_number
            or thresholds.max_null_space_dimension
            > policy.max_null_space_dimension
        ):
            blocked.append("mock_calibration_thresholds_weaker_than_policy")
        if self.n_mock_succeeded < thresholds.min_n_mock:
            blocked.append("n_mock_below_threshold")
        if self.retention_fraction < thresholds.min_retention_fraction:
            blocked.append("retention_fraction_below_threshold")
        if self.bias_direction_deg > thresholds.max_bias_direction_deg:
            blocked.append("direction_bias_exceeds_threshold")
        if (
            self.bias_direction_p95_deg is not None
            and self.bias_direction_p95_deg > thresholds.max_bias_direction_deg
        ):
            blocked.append("direction_bias_tail_exceeds_threshold")
        coverage_lower, coverage_upper = self.coverage_68_interval
        if not lower <= self.coverage_68 <= upper:
            blocked.append("coverage_68_outside_window")
        if not (lower <= coverage_lower and coverage_upper <= upper):
            blocked.append("coverage_68_interval_outside_window")
        _, fpr_upper = self.false_positive_rate_interval_adjusted
        if (
            self.false_positive_rate_adjusted > thresholds.max_false_positive_rate
            or fpr_upper > thresholds.max_false_positive_rate
        ):
            blocked.append("false_positive_rate_exceeds_threshold")
        if self.response_rank < thresholds.min_response_rank:
            blocked.append("response_rank_below_threshold")
        if self.effective_rank < thresholds.min_effective_rank:
            blocked.append("effective_rank_below_threshold")
        if self.null_space_dimension > 0:
            blocked.append("null_space_dimension_nonzero")
        if self.null_space_dimension > thresholds.max_null_space_dimension:
            blocked.append("null_space_dimension_exceeds_threshold")
        if self.condition_number > thresholds.max_condition_number:
            blocked.append("condition_number_exceeds_threshold")
        if self.look_elsewhere_trials != self.scan_trial_count:
            blocked.append("look_elsewhere_trials_scan_count_mismatch")
        if self.sky_support_status != "pr040_sky_support_attached":
            blocked.append("sky_support_status_not_attached")
        if self.sky_support_metadata is None:
            blocked.append("sky_support_metadata_missing")
        if (
            str(self.covariance_status).strip().lower()
            not in _PASSING_COVARIANCE_STATUSES
        ):
            blocked.append("covariance_status_not_calibrated")
        return _dedupe(blocked)

    @property
    def allowed_claim_tier(self) -> ClaimTier:
        if self.blocked_reasons:
            return ClaimTier.DIAGNOSTIC_ONLY
        return ClaimTier.CONDITIONAL

    @property
    def null_mock_status(self) -> str:
        if self.blocked_reasons:
            return "directional_null_mock_failed"
        return "directional_null_mock_passed"

    @property
    def calibration_hash(self) -> str:
        return _hash_payload(self._hash_payload())

    def _hash_payload(self) -> dict[str, object]:
        return {
            "schema": "axis_mock_calibration_report_v1",
            "claim_target": self.claim_target,
            "n_mock_requested": self.n_mock_requested,
            "n_mock_succeeded": self.n_mock_succeeded,
            "bias_direction_deg": self.bias_direction_deg,
            "coverage_68": self.coverage_68,
            "false_positive_rate": self.false_positive_rate,
            "null_ensemble": self.null_ensemble,
            "detection_rule": self.detection_rule,
            "look_elsewhere_trials": self.look_elsewhere_trials,
            "scan_trial_count": self.scan_trial_count,
            "scan_trial_hash": self.scan_trial_hash,
            "response_rank": self.response_rank,
            "effective_rank": self.effective_rank,
            "null_space_dimension": self.null_space_dimension,
            "condition_number": self.condition_number,
            "sky_support_hash": self.sky_support_hash,
            "mask_hash": self.mask_hash,
            "scan_volume_hash": self.scan_volume_hash,
            "config_hash": self.config_hash,
            "input_hashes": list(self.input_hashes),
            "covariance_status": self.covariance_status,
            "generating_command": self.generating_command,
            "git_commit": self.git_commit,
            "worktree_state": self.worktree_state,
            "sky_support_status": self.sky_support_status,
            "sky_support_metadata": dict(self.sky_support_metadata or {}),
            "thresholds": self.thresholds.to_metadata(),
            "owner": self.owner.value,
            "implementation_scope": self.implementation_scope.value,
            "claim_tier": self.claim_tier.value,
            "transfer_source": self.transfer_source,
            "random_seeds": list(self.random_seeds),
            "coverage_68_count": self.coverage_68_count,
            "false_positive_count": self.false_positive_count,
            "bias_direction_p95_deg": self.bias_direction_p95_deg,
            "caveats": list(self.caveats),
        }

    def to_metadata(self) -> dict[str, object]:
        coverage_ci = self.coverage_68_interval
        fpr_ci = self.false_positive_rate_interval_adjusted
        return {
            "artifact_name": "axis_mock_calibration_report_v1",
            "owner": self.owner.value,
            "implementation_scope": self.implementation_scope.value,
            "claim_tier": self.claim_tier.value,
            "allowed_claim_tier": self.allowed_claim_tier.value,
            "transfer_source": self.transfer_source,
            "claim_target": self.claim_target,
            "mock_calibration_hash": self.calibration_hash,
            "config_hash": self.config_hash,
            "input_hashes": list(self.input_hashes),
            "sky_support_hash": self.sky_support_hash,
            "sky_support_status": self.sky_support_status,
            "sky_support": dict(self.sky_support_metadata or {}),
            "mask_hash": self.mask_hash,
            "scan_volume_hash": self.scan_volume_hash,
            "retention": {
                "n_mock_requested": self.n_mock_requested,
                "n_mock_succeeded": self.n_mock_succeeded,
                "retention_fraction": self.retention_fraction,
                "min_retention_fraction": self.thresholds.min_retention_fraction,
            },
            "bias": {
                "bias_direction_deg": self.bias_direction_deg,
                "bias_direction_p95_deg": self.bias_direction_p95_deg,
                "max_bias_direction_deg": self.thresholds.max_bias_direction_deg,
            },
            "coverage": {
                "coverage_68": self.coverage_68,
                "coverage_68_count": self.coverage_68_count,
                "coverage_68_denominator": self.n_mock_succeeded,
                "coverage_68_interval": list(coverage_ci),
                "coverage_68_window": list(self.thresholds.coverage_68_window),
                "spherical_convention": "galactic_lon_lat_degrees",
            },
            "false_positive_rate": {
                "raw": self.false_positive_rate,
                "false_positive_count": self.false_positive_count,
                "false_positive_denominator": self.n_mock_succeeded,
                "adjusted": self.false_positive_rate_adjusted,
                "adjusted_interval": list(fpr_ci),
                "max_false_positive_rate": self.thresholds.max_false_positive_rate,
                "look_elsewhere_trials": self.look_elsewhere_trials,
                "scan_trial_count": self.scan_trial_count,
                "scan_trial_hash": self.scan_trial_hash,
                "null_ensemble": self.null_ensemble,
                "detection_rule": self.detection_rule,
            },
            "rank_status": {
                "response_rank": self.response_rank,
                "effective_rank": self.effective_rank,
                "null_space_dimension": self.null_space_dimension,
                "condition_number": self.condition_number,
            },
            "covariance_status": self.covariance_status,
            "null_mock_status": self.null_mock_status,
            "blocked_reasons": list(self.blocked_reasons),
            "thresholds": self.thresholds.to_metadata(),
            "random_seeds": list(self.random_seeds),
            "caveats": list(self.caveats),
            "generating_command": self.generating_command,
            "git_commit": self.git_commit,
            "worktree_state": self.worktree_state,
        }


@dataclass(frozen=True)
class AxisMockCalibrationGateDecision:
    """Claim-tier decision for an axis mock-calibration report."""

    allowed: bool
    requested_claim_tier: ClaimTier
    allowed_claim_tier: ClaimTier
    blocked_reasons: tuple[str, ...]
    report: AxisMockCalibrationReport | None = None

    def to_metadata(self) -> dict[str, object]:
        return {
            "allowed": self.allowed,
            "requested_claim_tier": self.requested_claim_tier.value,
            "allowed_claim_tier": self.allowed_claim_tier.value,
            "blocked_reasons": list(self.blocked_reasons),
            "report": self.report.to_metadata() if self.report is not None else None,
        }


def build_axis_mock_calibration_report(**kwargs: Any) -> AxisMockCalibrationReport:
    """Build a directional mock-calibration report with stable provenance hash."""

    return AxisMockCalibrationReport(**kwargs)


def evaluate_directional_claim_mock_gate(
    report: AxisMockCalibrationReport | None,
    *,
    requested_claim_tier: ClaimTier | str = ClaimTier.CONDITIONAL,
    sky_support_hash: str | None = None,
    mask_hash: str | None = None,
    scan_volume_hash: str | None = None,
    calibration_hash: str | None = None,
) -> AxisMockCalibrationGateDecision:
    """Fail closed when directional claims exceed available mock calibration."""

    requested = normalize_claim_tier(requested_claim_tier)
    if report is None:
        ceiling = ClaimTier.DIAGNOSTIC_ONLY
        blocked: list[str] = []
        if _tier_exceeds(requested, ceiling):
            blocked.extend(
                [
                    "axis_mock_calibration_report_missing",
                    "requested_claim_tier_exceeds_mock_calibration_ceiling",
                ]
            )
        return AxisMockCalibrationGateDecision(
            allowed=not blocked,
            requested_claim_tier=requested,
            allowed_claim_tier=ceiling,
            blocked_reasons=tuple(blocked),
            report=None,
        )

    ceiling = report.allowed_claim_tier
    blocked = list(report.blocked_reasons)
    if sky_support_hash is not None and report.sky_support_hash != sky_support_hash:
        blocked.append("mock_calibration_sky_support_hash_mismatch")
    if mask_hash is not None and report.mask_hash != mask_hash:
        blocked.append("mock_calibration_mask_hash_mismatch")
    if scan_volume_hash is not None and report.scan_volume_hash != scan_volume_hash:
        blocked.append("mock_calibration_scan_volume_hash_mismatch")
    if calibration_hash is not None and report.calibration_hash != calibration_hash:
        blocked.append("mock_calibration_hash_mismatch")
    if _tier_exceeds(requested, ceiling):
        blocked.append("requested_claim_tier_exceeds_mock_calibration_ceiling")
    return AxisMockCalibrationGateDecision(
        allowed=not blocked,
        requested_claim_tier=requested,
        allowed_claim_tier=ceiling,
        blocked_reasons=_dedupe(blocked),
        report=report,
    )


# ---------------------------------------------------------------------------
# Mock-report dataclass (injected family)
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class InjectedMockReport:
    """Injected-dipole mock calibration summary (§6.7)."""

    recovered_V_samples: np.ndarray    # (n_mock, 3)
    amp_bias_fraction: float
    direction_bias_deg: float
    amp_spread_fractional: float
    n_mock: int
    config: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if self.recovered_V_samples.ndim != 2 or self.recovered_V_samples.shape[1] != 3:
            raise ValueError(
                f"recovered_V_samples must be (n, 3); got "
                f"{self.recovered_V_samples.shape}"
            )
        if self.n_mock <= 0:
            raise ValueError(f"n_mock must be > 0; got {self.n_mock}")


# ---------------------------------------------------------------------------
# Mock generation
# ---------------------------------------------------------------------------

def generate_isotropic_mock(
    catalogue: BulkFlowCatalogue,
    *,
    rng: np.random.Generator | None = None,
    sigma_star_kmps: float = 0.0,
) -> BulkFlowCatalogue:
    """Draw an isotropic-null velocity realisation on the *same* geometry.

    Keeps ``n_hat``, ``sigma``, ``w_native``, ``w_selection`` fixed and
    regenerates ``u_i ~ 𝒩(0, σ_eff,i²)`` with no underlying bulk flow. This
    is the realisation used by :func:`run_zoa_null_mocks`.
    """
    if rng is None:
        rng = np.random.default_rng()
    N = catalogue.n_sources
    sigma_eff = np.sqrt(catalogue.sigma ** 2 + float(sigma_star_kmps) ** 2)
    u = rng.normal(0.0, sigma_eff, size=N)
    return BulkFlowCatalogue(
        n_hat=catalogue.n_hat.copy(),
        u=u,
        sigma=catalogue.sigma.copy(),
        w_native=catalogue.w_native.copy(),
        w_selection=catalogue.w_selection.copy(),
        label=f"{catalogue.label}.isotropic_mock",
    )


def generate_injected_dipole_mock(
    catalogue: BulkFlowCatalogue,
    V_true_kmps: np.ndarray,
    *,
    rng: np.random.Generator | None = None,
    sigma_star_kmps: float = 0.0,
) -> BulkFlowCatalogue:
    """Draw a realisation with injected bulk-flow ``V_true`` on the same geometry."""
    if rng is None:
        rng = np.random.default_rng()
    V_true = np.asarray(V_true_kmps, dtype=float)
    if V_true.shape != (3,):
        raise ValueError(f"V_true_kmps must be (3,); got {V_true.shape}")
    N = catalogue.n_sources
    sigma_eff = np.sqrt(catalogue.sigma ** 2 + float(sigma_star_kmps) ** 2)
    u_clean = catalogue.n_hat @ V_true
    u = u_clean + rng.normal(0.0, sigma_eff, size=N)
    return BulkFlowCatalogue(
        n_hat=catalogue.n_hat.copy(),
        u=u,
        sigma=catalogue.sigma.copy(),
        w_native=catalogue.w_native.copy(),
        w_selection=catalogue.w_selection.copy(),
        label=f"{catalogue.label}.injected_dipole",
    )


# ---------------------------------------------------------------------------
# Mask / weight application
# ---------------------------------------------------------------------------

def apply_same_mask(
    catalogue: BulkFlowCatalogue,
    sky_config: SkySelectionConfig,
    *,
    C_pix: np.ndarray | None = None,
) -> BulkFlowCatalogue:
    """Apply the same ZoA + selection weights as the observed data.

    Returns a new catalogue with ``w_selection`` replaced by
    ``compute_selection_weights`` output. Sources whose pixel is outside the
    ZoA mask receive ``w_selection = 0`` (they survive the catalogue so the
    fit can still see their geometry, but the log-likelihood drops them —
    see :class:`common.bulkflow_likelihood.BulkFlowLikelihood`).
    """
    nside = int(sky_config.nside)
    l_deg, b_deg = unitvec_to_lb(catalogue.n_hat)
    mask_pix = build_zoa_mask(
        l_deg, b_deg, bcut_deg=sky_config.zoa_half_angle_deg, nside=nside,
    )
    if C_pix is None:
        C_pix = build_angular_completeness(
            l_deg, b_deg, nside=nside,
            smooth_sigma_pix=sky_config.smooth_sigma_pix,
        )
    w_sel = compute_selection_weights(l_deg, b_deg, mask_pix, C_pix)
    return BulkFlowCatalogue(
        n_hat=catalogue.n_hat.copy(),
        u=catalogue.u.copy(),
        sigma=catalogue.sigma.copy(),
        w_native=catalogue.w_native.copy(),
        w_selection=w_sel,
        label=f"{catalogue.label}.masked",
    )


# ---------------------------------------------------------------------------
# Bias / coverage diagnostics
# ---------------------------------------------------------------------------

def recovered_bias(
    V_true: np.ndarray,
    estimated_V_list: np.ndarray,
) -> dict[str, float]:
    """Amplitude and direction bias between truth and recovered samples.

    ``estimated_V_list`` is ``(n_mock, 3)``. Amplitude bias is the mean
    signed fractional residual ``<|V_hat|>/|V_true| − 1``; direction bias
    is the angular separation between the mean recovered direction and the
    true direction. A zero-amplitude truth is allowed (null tests); the
    amplitude-bias field is then ``None``-like via ``np.nan``.
    """
    V_true = np.asarray(V_true, dtype=float)
    V_hat = np.asarray(estimated_V_list, dtype=float)
    if V_true.shape != (3,):
        raise ValueError(f"V_true must be (3,); got {V_true.shape}")
    if V_hat.ndim != 2 or V_hat.shape[1] != 3:
        raise ValueError(f"estimated_V_list must be (n, 3); got {V_hat.shape}")
    amp_true = float(np.linalg.norm(V_true))
    amp_hat = np.linalg.norm(V_hat, axis=1)
    if amp_true <= 0.0:
        amp_bias = float("nan")
        direction_bias = float("nan")
    else:
        amp_bias = float((amp_hat / amp_true).mean() - 1.0)
        mean_vec = V_hat.mean(axis=0)
        mean_norm = float(np.linalg.norm(mean_vec))
        if mean_norm <= 0.0:
            direction_bias = float("nan")
        else:
            cos_sep = float(np.clip(
                (mean_vec / mean_norm) @ (V_true / amp_true), -1.0, 1.0
            ))
            direction_bias = float(np.rad2deg(np.arccos(cos_sep)))
    return {
        "amp_bias_fraction": amp_bias,
        "direction_bias_deg": direction_bias,
        "amp_spread_fractional": float(
            amp_hat.std() / amp_true if amp_true > 0 else amp_hat.std()
        ),
    }


def coverage_test(
    estimates: np.ndarray,
    covariances: np.ndarray,
    truth: np.ndarray,
    level: float = 0.68,
) -> float:
    """Fraction of mocks whose ``χ²_3`` distance to ``truth`` lies within level.

    For a 3-D Gaussian posterior with mean ``V_hat`` and covariance ``cov``
    the contour at credibility ``level`` is the Mahalanobis sphere with
    radius-squared ``χ²_3(level)``. This is the working-definition coverage
    used in §6.7 (coverage_68pct, coverage_95pct).
    """
    from scipy.stats import chi2

    estimates = np.asarray(estimates, dtype=float)
    covariances = np.asarray(covariances, dtype=float)
    truth = np.asarray(truth, dtype=float)
    if estimates.ndim != 2 or estimates.shape[1] != 3:
        raise ValueError(f"estimates must be (n, 3); got {estimates.shape}")
    n = estimates.shape[0]
    if covariances.shape != (n, 3, 3):
        raise ValueError(
            f"covariances must be (n, 3, 3); got {covariances.shape}"
        )
    if truth.shape != (3,):
        raise ValueError(f"truth must be (3,); got {truth.shape}")
    if not (0.0 < level < 1.0):
        raise ValueError(f"level must be in (0, 1); got {level}")
    threshold = float(chi2.ppf(level, df=3))
    inside = 0
    for k in range(n):
        diff = estimates[k] - truth
        try:
            mahal = float(diff @ np.linalg.solve(covariances[k], diff))
        except np.linalg.LinAlgError:
            continue
        if mahal <= threshold:
            inside += 1
    return inside / n


# ---------------------------------------------------------------------------
# Production runners
# ---------------------------------------------------------------------------

def _default_estimator(
    n_hat: np.ndarray,
    u: np.ndarray,
    sigma: np.ndarray,
    w_native: np.ndarray,
    w_selection: np.ndarray,
) -> tuple[np.ndarray, np.ndarray]:
    fit = wls_bulk_flow(
        n_hat, u,
        sigma=sigma, w_native=w_native, w_selection=w_selection,
    )
    return fit.V_hat, fit.cov


def _run_mock_bank(
    catalogue: BulkFlowCatalogue,
    sky_config: SkySelectionConfig,
    V_true: np.ndarray,
    *,
    n_mock: int,
    rng: np.random.Generator | None,
    estimator: EstimatorFn | None,
    C_pix: np.ndarray | None,
) -> tuple[np.ndarray, np.ndarray]:
    """Common driver for null and injected mock banks.

    Returns ``(estimates, covariances)`` for the ``n_mock`` mocks. Mocks
    whose WLS fit is singular are dropped and do not count toward the
    returned shape (so ``estimates.shape[0] ≤ n_mock``).
    """
    if rng is None:
        rng = np.random.default_rng()
    if estimator is None:
        estimator = _default_estimator
    estimates = np.empty((n_mock, 3), dtype=float)
    covariances = np.empty((n_mock, 3, 3), dtype=float)
    succeeded = 0
    for _ in range(n_mock):
        if np.allclose(V_true, 0.0):
            mock = generate_isotropic_mock(catalogue, rng=rng)
        else:
            mock = generate_injected_dipole_mock(catalogue, V_true, rng=rng)
        masked = apply_same_mask(mock, sky_config, C_pix=C_pix)
        try:
            V_hat, cov = estimator(
                masked.n_hat, masked.u, masked.sigma,
                masked.w_native, masked.w_selection,
            )
        except (ValueError, np.linalg.LinAlgError):
            continue
        estimates[succeeded] = V_hat
        covariances[succeeded] = cov
        succeeded += 1
    return estimates[:succeeded], covariances[:succeeded]


def run_zoa_null_mocks(
    catalogue: BulkFlowCatalogue,
    sky_config: SkySelectionConfig,
    *,
    n_mock: int = 1000,
    rng: np.random.Generator | None = None,
    estimator: EstimatorFn | None = None,
    C_pix: np.ndarray | None = None,
) -> MockCalibrationReport:
    """Null-hypothesis mock bank with ZoA + selection applied (§6.7).

    Returns the ``MockCalibrationReport`` populated with bias/coverage/
    credible_radius summaries. Null-hypothesis bias is the zero-sample
    amplitude of the recovered dipole mean — not a fractional bias.
    """
    estimates, covariances = _run_mock_bank(
        catalogue, sky_config, np.zeros(3),
        n_mock=n_mock, rng=rng, estimator=estimator, C_pix=C_pix,
    )
    if estimates.shape[0] < max(20, n_mock // 10):
        raise RuntimeError(
            f"run_zoa_null_mocks: only {estimates.shape[0]} of {n_mock} mocks "
            "produced a non-singular WLS fit — catalogue geometry is too sparse"
        )

    amp = np.linalg.norm(estimates, axis=1)
    mean_vec = estimates.mean(axis=0)
    mean_norm = float(np.linalg.norm(mean_vec))
    l_mean, b_mean = unitvec_to_lb(mean_vec / max(mean_norm, 1e-12))
    # Under the null, there is no true direction; we report the *recovered*
    # mean direction as the "bias direction" and the mean amplitude as
    # the bias amplitude (both zero in expectation).
    bias_amp = float(amp.mean())
    bias_direction = float(l_mean)    # recovered-mean longitude in degrees

    coverage_68 = coverage_test(estimates, covariances, np.zeros(3), level=0.68)
    coverage_95 = coverage_test(estimates, covariances, np.zeros(3), level=0.95)
    # Credible radius: median of the 1-σ (68%) Gaussian cone over the mocks.
    # For a 3-D Gaussian the 68% Mahalanobis radius is sqrt(chi2.ppf(0.68, 3))
    # in standard-deviation units; we convert to an angular cone using the
    # covariance's trace as a scalar σ_V.
    sigma_V = np.sqrt(covariances.trace(axis1=1, axis2=2) / 3.0)
    # Angular spread ≈ σ_V / |V_hat| rad when |V_hat| ≫ σ_V; at the null it
    # is better-characterised by the distribution of recovered directions.
    with np.errstate(divide="ignore", invalid="ignore"):
        cone_rad = np.where(amp > 0.0, sigma_V / amp, np.nan)
    credible_radius_deg = float(np.nanmedian(np.rad2deg(cone_rad)))

    return MockCalibrationReport(
        bias_amp=bias_amp,
        bias_direction_deg=bias_direction,
        coverage_68=coverage_68,
        credible_radius_deg=credible_radius_deg,
        n_mock=estimates.shape[0],
        config={
            "mode": "zoa_null",
            "zoa_half_angle_deg": sky_config.zoa_half_angle_deg,
            "n_mock_requested": n_mock,
            "coverage_95": coverage_95,
            "null_amplitude_mean": float(amp.mean()),
            "null_amplitude_std": float(amp.std()),
        },
    )


def run_injected_dipole_mocks(
    catalogue: BulkFlowCatalogue,
    V_true_kmps: np.ndarray,
    sky_config: SkySelectionConfig,
    *,
    n_mock: int = 1000,
    rng: np.random.Generator | None = None,
    estimator: EstimatorFn | None = None,
    C_pix: np.ndarray | None = None,
) -> InjectedMockReport:
    """Injected-dipole mock bank. Returns amplitude + direction bias (§6.7)."""
    V_true = np.asarray(V_true_kmps, dtype=float)
    if V_true.shape != (3,):
        raise ValueError(f"V_true_kmps must be (3,); got {V_true.shape}")
    if float(np.linalg.norm(V_true)) <= 0.0:
        raise ValueError(
            "run_injected_dipole_mocks requires a non-zero V_true; "
            "use run_zoa_null_mocks for the null case"
        )
    estimates, _ = _run_mock_bank(
        catalogue, sky_config, V_true,
        n_mock=n_mock, rng=rng, estimator=estimator, C_pix=C_pix,
    )
    if estimates.shape[0] < max(20, n_mock // 10):
        raise RuntimeError(
            f"run_injected_dipole_mocks: only {estimates.shape[0]} of "
            f"{n_mock} mocks converged"
        )
    bias = recovered_bias(V_true, estimates)
    return InjectedMockReport(
        recovered_V_samples=estimates,
        amp_bias_fraction=float(bias["amp_bias_fraction"]),
        direction_bias_deg=float(bias["direction_bias_deg"]),
        amp_spread_fractional=float(bias["amp_spread_fractional"]),
        n_mock=estimates.shape[0],
        config={
            "mode": "injected_dipole",
            "V_true": tuple(float(x) for x in V_true),
            "n_mock_requested": n_mock,
            "zoa_half_angle_deg": sky_config.zoa_half_angle_deg,
        },
    )


# ---------------------------------------------------------------------------
# Bias correction for the 4-summary AH consumer
# ---------------------------------------------------------------------------

def apply_bias_correction(
    V_hat: np.ndarray,
    injected_report: InjectedMockReport,
) -> np.ndarray:
    """De-bias a selection-aware estimate using the injected-mock report.

    Subtracts the mean mock residual ``E[V_hat - V_true]`` from the raw
    estimate. This mirrors the ``mock_calibrated_summary`` slot of the
    PR13AH four-summary structure (§6.3): the selection-aware estimate is
    passed through this correction before being elevated to Mode 2 fiducial.
    """
    V_hat = np.asarray(V_hat, dtype=float)
    if V_hat.shape != (3,):
        raise ValueError(f"V_hat must be (3,); got {V_hat.shape}")
    V_true_tuple = injected_report.config.get("V_true")
    if V_true_tuple is None:
        raise ValueError(
            "injected_report.config is missing 'V_true' — can't compute residual"
        )
    V_true = np.asarray(V_true_tuple, dtype=float)
    residual = injected_report.recovered_V_samples.mean(axis=0) - V_true
    return V_hat - residual


def mock_calibration_report_artifact(
    report: MockCalibrationReport,
    *,
    injected_report: InjectedMockReport | None = None,
    coverage_window_68: tuple[float, float] = (0.60, 0.76),
    bias_fraction_threshold: float = 0.05,
    metadata: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Build the Mode 2 precondition ``mock_calibration_report_vX.json``.

    When an ``InjectedMockReport`` is available, the artifact also evaluates
    the amplitude-bias leg of the Mode 1 → Mode 2 gate from the research
    plan. Without it, only the coverage gate is assessed.
    """
    if not isinstance(report, MockCalibrationReport):
        raise TypeError(
            "mock_calibration_report_artifact requires a MockCalibrationReport"
        )
    lower, upper = coverage_window_68
    if not (0.0 <= lower <= upper <= 1.0):
        raise ValueError(
            "coverage_window_68 must satisfy 0 <= lower <= upper <= 1"
        )
    if bias_fraction_threshold < 0.0:
        raise ValueError("bias_fraction_threshold must be >= 0")
    coverage_pass = bool(lower <= report.coverage_68 <= upper)
    injected_block: dict[str, Any] | None
    if injected_report is None:
        bias_fraction = None
        bias_pass = None
        injected_block = None
    else:
        bias_fraction = float(abs(injected_report.amp_bias_fraction))
        bias_pass = bool(bias_fraction <= bias_fraction_threshold)
        injected_block = {
            "amp_bias_fraction": float(injected_report.amp_bias_fraction),
            "direction_bias_deg": float(injected_report.direction_bias_deg),
            "amp_spread_fractional": float(injected_report.amp_spread_fractional),
            "n_mock": int(injected_report.n_mock),
            "config": _jsonify(injected_report.config),
        }
    gate_passed = coverage_pass if bias_pass is None else bool(
        coverage_pass and bias_pass
    )
    extra = dict(metadata or {})
    config_payload = {
        "coverage_window_68": coverage_window_68,
        "bias_fraction_threshold": bias_fraction_threshold,
        "metadata": extra,
    }
    return _jsonify({
        "artifact_name": "mock_calibration_report_v1.json",
        "generated_by": extra.get(
            "generated_by",
            "common.mock_calibration.mock_calibration_report_artifact",
        ),
        "git_commit": extra.get("git_commit", ""),
        "config_hash": _config_hash(config_payload),
        "input_data_hashes": list(extra.get("input_data_hashes", [])),
        "random_seed": extra.get("random_seed"),
        "wall_time_sec": extra.get("wall_time_sec"),
        "python_version": extra.get("python_version", platform.python_version()),
        "numpy_version": extra.get("numpy_version", np.__version__),
        "claim_tier": extra.get("claim_tier", "CONDITIONAL"),
        "scope_label": extra.get("scope_label", "fiducial"),
        "production_allowed": False,
        "coverage_window_68": list(coverage_window_68),
        "coverage_pass": coverage_pass,
        "bias_fraction_threshold": float(bias_fraction_threshold),
        "bias_pass": bias_pass,
        "mode1_to_mode2_gate_passed": gate_passed,
        "bias_amp": float(report.bias_amp),
        "bias_direction_deg": float(report.bias_direction_deg),
        "coverage_68": float(report.coverage_68),
        "credible_radius_deg": float(report.credible_radius_deg),
        "n_mock": int(report.n_mock),
        "null_distribution_summary": {
            "coverage_95": report.config.get("coverage_95"),
            "null_amplitude_mean": report.config.get("null_amplitude_mean"),
            "null_amplitude_std": report.config.get("null_amplitude_std"),
        },
        "report_config": _jsonify(report.config),
        "injected_dipole_summary": injected_block,
    })
