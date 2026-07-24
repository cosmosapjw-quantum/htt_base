"""Depth-resolved local-boost null banks for HTT local/global gates."""
from __future__ import annotations

import hashlib
import json
import math
import re
from collections.abc import Mapping, Sequence
from dataclasses import asdict, dataclass, field
from typing import Any

import numpy as np
from common.contracts import (
    ArtifactManifest,
    ClaimTier,
    ImplementationScope,
    Owner,
    normalize_claim_tier,
)
from common.enum_compat import StrEnum

from htt.departure.response_overlap import ResponseOverlapAudit

SCHEMA_VERSION = "htt.local_boost_depth_null.v1"
DEFAULT_CAVEATS = (
    "diagnostic_local_null_calibration_only",
    "does_not_authorize_global_tilt_claim",
    "does_not_identify_bianchi_family",
    "no_native_solver_values",
)
_SHA256_RE = re.compile(r"^sha256:[0-9a-fA-F]{64}$")
_COVARIANCE_PASSING_STATUSES = {
    "diagnostic_covariance_supplied",
    "directional_mock_covariance_available",
    "directional_mock_covariance_calibrated",
}
_CLAIM_TIER_RANK = {
    ClaimTier.BLOCKED: -1,
    ClaimTier.DIAGNOSTIC_ONLY: 0,
    ClaimTier.EXPLORATORY: 0,
    ClaimTier.CONDITIONAL: 1,
    ClaimTier.VALIDATED: 2,
}


def _jsonify(value: object) -> Any:
    if isinstance(value, StrEnum):
        return value.value
    if isinstance(value, np.ndarray):
        return [_jsonify(item) for item in value.tolist()]
    if isinstance(value, np.generic):
        return _jsonify(value.item())
    if isinstance(value, Mapping):
        return {str(key): _jsonify(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_jsonify(item) for item in value]
    if isinstance(value, float):
        if not math.isfinite(value):
            raise TypeError("payload floats must be finite")
        return value
    return value


def _stable_hash(payload: Mapping[str, object]) -> str:
    encoded = json.dumps(
        _jsonify(payload),
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    )
    return "sha256:" + hashlib.sha256(encoded.encode("utf-8")).hexdigest()


def _manifest_payload(manifest: ArtifactManifest) -> dict[str, Any]:
    payload = _jsonify(asdict(manifest))
    if not isinstance(payload, dict):
        raise TypeError("manifest payload must be a mapping")
    return payload


def _require_non_empty(value: object, field_name: str) -> str:
    text = str(value).strip()
    if not text:
        raise ValueError(f"{field_name} must be non-empty")
    return text


def _finite_float(value: object, field_name: str) -> float:
    out = float(value)
    if not math.isfinite(out):
        raise ValueError(f"{field_name} must be finite")
    return out


def _positive_float(value: object, field_name: str) -> float:
    out = _finite_float(value, field_name)
    if out <= 0.0:
        raise ValueError(f"{field_name} must be positive")
    return out


def _unit_interval(value: object, field_name: str) -> float:
    out = _finite_float(value, field_name)
    if not 0.0 <= out <= 1.0:
        raise ValueError(f"{field_name} must be in [0, 1]")
    return out


def _require_sha256(value: object, field_name: str) -> str:
    text = _require_non_empty(value, field_name)
    if _SHA256_RE.fullmatch(text) is None:
        raise ValueError(f"{field_name} must be sha256:<64 hex chars>")
    return text


def _require_sha256_sequence(values: Sequence[object], field_name: str) -> tuple[str, ...]:
    if isinstance(values, (str, bytes)) or not values:
        raise ValueError(f"{field_name} must be a non-empty sequence")
    return tuple(_require_sha256(value, field_name) for value in values)


def _unit_vector(values: Sequence[object], field_name: str) -> tuple[float, float, float]:
    if isinstance(values, (str, bytes)):
        raise ValueError(f"{field_name} must be a 3-vector")
    vector = np.asarray(tuple(float(value) for value in values), dtype=float)
    if vector.shape != (3,) or not np.all(np.isfinite(vector)):
        raise ValueError(f"{field_name} must be a finite 3-vector")
    norm = float(np.linalg.norm(vector))
    if norm <= 0.0:
        raise ValueError(f"{field_name} must be a non-zero vector")
    unit = vector / norm
    return tuple(float(item) for item in unit)


def _sample_unit_vector(rng: np.random.Generator) -> np.ndarray:
    for _ in range(32):
        vector = rng.normal(0.0, 1.0, size=3)
        norm = float(np.linalg.norm(vector))
        if norm > 0.0:
            return vector / norm
    raise RuntimeError("failed to sample a non-zero unit vector")


def _perturb_unit_vector(
    base_direction: np.ndarray,
    rng: np.random.Generator,
    jitter_sigma: float,
) -> np.ndarray:
    for _ in range(32):
        vector = base_direction + rng.normal(0.0, jitter_sigma, size=3)
        norm = float(np.linalg.norm(vector))
        if norm > 0.0:
            return vector / norm
    return np.asarray(base_direction, dtype=float)


def _angle_deg(left: Sequence[float], right: Sequence[float]) -> float:
    u = np.asarray(left, dtype=float)
    v = np.asarray(right, dtype=float)
    dot = float(np.clip(u @ v, -1.0, 1.0))
    return float(np.degrees(np.arccos(dot)))


def _wilson_interval(k: int, n: int, *, z: float = 1.0) -> tuple[float, float]:
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


def _percentiles(values: np.ndarray) -> dict[str, float]:
    if values.size == 0:
        raise ValueError("cannot summarize an empty distribution")
    return {
        "min": float(np.min(values)),
        "p05": float(np.percentile(values, 5.0)),
        "median": float(np.percentile(values, 50.0)),
        "p95": float(np.percentile(values, 95.0)),
        "max": float(np.max(values)),
    }


@dataclass(frozen=True)
class DepthBinSpec:
    """Explicit depth-bin metadata for HTT local null mock banks."""

    label: str
    z_min: float
    z_max: float
    distance_mpc_min: float
    distance_mpc_max: float
    response_weight: float = 1.0

    def __post_init__(self) -> None:
        label = _require_non_empty(self.label, "DepthBinSpec.label")
        z_min = _finite_float(self.z_min, "DepthBinSpec.z_min")
        z_max = _finite_float(self.z_max, "DepthBinSpec.z_max")
        distance_min = _finite_float(
            self.distance_mpc_min,
            "DepthBinSpec.distance_mpc_min",
        )
        distance_max = _finite_float(
            self.distance_mpc_max,
            "DepthBinSpec.distance_mpc_max",
        )
        response_weight = _finite_float(
            self.response_weight,
            "DepthBinSpec.response_weight",
        )
        if z_min < 0.0 or z_max <= z_min:
            raise ValueError("DepthBinSpec requires 0 <= z_min < z_max")
        if distance_min < 0.0 or distance_max <= distance_min:
            raise ValueError(
                "DepthBinSpec requires 0 <= distance_mpc_min < distance_mpc_max"
            )
        if response_weight < 0.0:
            raise ValueError("DepthBinSpec.response_weight must be non-negative")
        object.__setattr__(self, "label", label)
        object.__setattr__(self, "z_min", z_min)
        object.__setattr__(self, "z_max", z_max)
        object.__setattr__(self, "distance_mpc_min", distance_min)
        object.__setattr__(self, "distance_mpc_max", distance_max)
        object.__setattr__(self, "response_weight", response_weight)

    @property
    def z_mid(self) -> float:
        return 0.5 * (self.z_min + self.z_max)

    @property
    def distance_mpc_mid(self) -> float:
        return 0.5 * (self.distance_mpc_min + self.distance_mpc_max)

    def to_metadata(self) -> dict[str, object]:
        return {
            "label": self.label,
            "z_min": self.z_min,
            "z_max": self.z_max,
            "distance_mpc_min": self.distance_mpc_min,
            "distance_mpc_max": self.distance_mpc_max,
            "z_mid": self.z_mid,
            "distance_mpc_mid": self.distance_mpc_mid,
            "response_weight": self.response_weight,
            "depth_convention": "redshift_bin_edges_and_comoving_distance_mpc",
        }


@dataclass(frozen=True)
class LocalBoostNullConfig:
    """Configuration and provenance for local depth-null mock generation."""

    n_mocks: int
    seed: int
    depth_bins: Sequence[DepthBinSpec]
    target_direction: Sequence[object]
    sky_support_hash: str
    mask_hash: str
    scan_volume_hash: str
    config_hash: str
    input_hashes: Sequence[object]
    generating_command: str
    worktree_state: str
    git_commit: str | None = None
    gf_threshold: float = 1.25
    direction_threshold_deg: float = 25.0
    look_elsewhere_trials: int = 1
    max_false_positive_rate: float = 0.05
    amplitude_beta_mean: float = 1.0e-3
    amplitude_beta_sigma: float = 2.0e-4
    direction_jitter_sigma: float = 0.06
    gf_beta_scale: float = 1.0e-3
    covariance_status: str = "diagnostic_covariance_supplied"
    sky_support_status: str = "pr040_sky_support_attached"
    null_mock_status: str = "local_boost_null_bank_generated"
    coordinate_frame: str = "galactic_cartesian_unit_vector"

    def __post_init__(self) -> None:
        n_mocks = int(self.n_mocks)
        if n_mocks <= 0:
            raise ValueError("LocalBoostNullConfig.n_mocks must be positive")
        depth_bins = tuple(self.depth_bins)
        if not depth_bins:
            raise ValueError("LocalBoostNullConfig.depth_bins must be non-empty")
        if len({bin_spec.label for bin_spec in depth_bins}) != len(depth_bins):
            raise ValueError("Depth bins must have unique labels")
        ordered = sorted(depth_bins, key=lambda item: item.z_min)
        for left, right in zip(ordered, ordered[1:]):
            if left.z_max > right.z_min or left.distance_mpc_max > right.distance_mpc_min:
                raise ValueError("Depth bins must be ordered and non-overlapping")

        object.__setattr__(self, "n_mocks", n_mocks)
        object.__setattr__(self, "seed", int(self.seed))
        object.__setattr__(self, "depth_bins", tuple(ordered))
        object.__setattr__(
            self,
            "target_direction",
            _unit_vector(self.target_direction, "target_direction"),
        )
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
        object.__setattr__(
            self,
            "generating_command",
            _require_non_empty(self.generating_command, "generating_command"),
        )
        object.__setattr__(
            self,
            "worktree_state",
            _require_non_empty(self.worktree_state, "worktree_state"),
        )
        object.__setattr__(self, "gf_threshold", _positive_float(self.gf_threshold, "gf_threshold"))
        direction_threshold = _finite_float(
            self.direction_threshold_deg,
            "direction_threshold_deg",
        )
        if not 0.0 <= direction_threshold <= 180.0:
            raise ValueError("direction_threshold_deg must be in [0, 180]")
        object.__setattr__(self, "direction_threshold_deg", direction_threshold)
        look_elsewhere_trials = int(self.look_elsewhere_trials)
        if look_elsewhere_trials <= 0:
            raise ValueError("look_elsewhere_trials must be positive")
        object.__setattr__(self, "look_elsewhere_trials", look_elsewhere_trials)
        object.__setattr__(
            self,
            "max_false_positive_rate",
            _unit_interval(self.max_false_positive_rate, "max_false_positive_rate"),
        )
        object.__setattr__(
            self,
            "amplitude_beta_mean",
            _positive_float(self.amplitude_beta_mean, "amplitude_beta_mean"),
        )
        object.__setattr__(
            self,
            "amplitude_beta_sigma",
            _positive_float(self.amplitude_beta_sigma, "amplitude_beta_sigma"),
        )
        object.__setattr__(
            self,
            "direction_jitter_sigma",
            _positive_float(self.direction_jitter_sigma, "direction_jitter_sigma"),
        )
        object.__setattr__(
            self,
            "gf_beta_scale",
            _positive_float(self.gf_beta_scale, "gf_beta_scale"),
        )
        object.__setattr__(
            self,
            "covariance_status",
            _require_non_empty(self.covariance_status, "covariance_status"),
        )
        object.__setattr__(
            self,
            "sky_support_status",
            _require_non_empty(self.sky_support_status, "sky_support_status"),
        )
        object.__setattr__(
            self,
            "null_mock_status",
            _require_non_empty(self.null_mock_status, "null_mock_status"),
        )
        object.__setattr__(
            self,
            "coordinate_frame",
            _require_non_empty(self.coordinate_frame, "coordinate_frame"),
        )

    def to_metadata(self) -> dict[str, object]:
        return {
            "n_mocks": self.n_mocks,
            "seed": self.seed,
            "depth_bins": [bin_spec.to_metadata() for bin_spec in self.depth_bins],
            "target_direction": list(self.target_direction),
            "gf_threshold": self.gf_threshold,
            "direction_threshold_deg": self.direction_threshold_deg,
            "look_elsewhere_trials": self.look_elsewhere_trials,
            "max_false_positive_rate": self.max_false_positive_rate,
            "sky_support_hash": self.sky_support_hash,
            "mask_hash": self.mask_hash,
            "scan_volume_hash": self.scan_volume_hash,
            "config_hash": self.config_hash,
            "input_hashes": list(self.input_hashes),
            "covariance_status": self.covariance_status,
            "sky_support_status": self.sky_support_status,
            "null_mock_status": self.null_mock_status,
            "coordinate_frame": self.coordinate_frame,
            "generating_command": self.generating_command,
            "git_commit": self.git_commit,
            "worktree_state": self.worktree_state,
        }


@dataclass(frozen=True)
class DepthNullSample:
    """One mock/depth-bin local-null draw."""

    mock_index: int
    seed: int
    depth_label: str
    z_mid: float
    distance_mpc_mid: float
    beta: float
    log_g_f: float
    g_f: float
    direction_unit_vector: Sequence[object]
    angular_separation_deg: float
    triggered: bool

    def __post_init__(self) -> None:
        object.__setattr__(self, "mock_index", int(self.mock_index))
        object.__setattr__(self, "seed", int(self.seed))
        object.__setattr__(
            self,
            "depth_label",
            _require_non_empty(self.depth_label, "DepthNullSample.depth_label"),
        )
        for field_name in ("z_mid", "distance_mpc_mid", "beta", "log_g_f", "g_f"):
            object.__setattr__(
                self,
                field_name,
                _finite_float(getattr(self, field_name), field_name),
            )
        if self.beta < 0.0 or self.log_g_f < 0.0 or self.g_f < 1.0:
            raise ValueError("DepthNullSample requires beta >= 0, log_g_f >= 0, g_f >= 1")
        if isinstance(self.direction_unit_vector, (str, bytes)):
            raise ValueError("DepthNullSample.direction_unit_vector must be a unit vector")
        direction_array = np.asarray(
            tuple(float(value) for value in self.direction_unit_vector),
            dtype=float,
        )
        if direction_array.shape != (3,) or not np.all(np.isfinite(direction_array)):
            raise ValueError("DepthNullSample.direction_unit_vector must be a unit vector")
        norm = float(np.linalg.norm(direction_array))
        if not math.isclose(norm, 1.0, rel_tol=0.0, abs_tol=1.0e-12):
            raise ValueError("DepthNullSample.direction_unit_vector must be a unit vector")
        angle = _finite_float(self.angular_separation_deg, "angular_separation_deg")
        if not 0.0 <= angle <= 180.0:
            raise ValueError("angular_separation_deg must be in [0, 180]")
        object.__setattr__(
            self,
            "direction_unit_vector",
            tuple(float(item) for item in direction_array),
        )
        object.__setattr__(self, "angular_separation_deg", angle)
        object.__setattr__(self, "triggered", bool(self.triggered))

    @property
    def direction_norm(self) -> float:
        return float(np.linalg.norm(np.asarray(self.direction_unit_vector, dtype=float)))

    def to_metadata(self) -> dict[str, object]:
        return {
            "mock_index": self.mock_index,
            "seed": self.seed,
            "depth_label": self.depth_label,
            "z_mid": self.z_mid,
            "distance_mpc_mid": self.distance_mpc_mid,
            "beta": self.beta,
            "log_g_F": self.log_g_f,
            "G_F": self.g_f,
            "direction_unit_vector": list(self.direction_unit_vector),
            "direction_norm": self.direction_norm,
            "angular_separation_deg": self.angular_separation_deg,
            "triggered": self.triggered,
        }


@dataclass(frozen=True)
class DepthNullMockBank:
    """Generated HTT local-null mock bank with depth and direction payloads."""

    null_model_id: str
    config: LocalBoostNullConfig
    samples: Sequence[DepthNullSample]
    physical_scope: str = "observer_side_local_boost"
    null_model_scope: str = "local_boost_depth_null"
    caveats: tuple[str, ...] = DEFAULT_CAVEATS

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "null_model_id",
            _require_non_empty(self.null_model_id, "null_model_id"),
        )
        object.__setattr__(
            self,
            "physical_scope",
            _require_non_empty(self.physical_scope, "physical_scope"),
        )
        object.__setattr__(
            self,
            "null_model_scope",
            _require_non_empty(self.null_model_scope, "null_model_scope"),
        )
        samples = tuple(self.samples)
        if not samples:
            raise ValueError("DepthNullMockBank.samples must be non-empty")
        expected_depths = {item.label for item in self.config.depth_bins}
        sample_depths = {item.depth_label for item in samples}
        if not sample_depths <= expected_depths:
            raise ValueError("DepthNullMockBank.samples include unknown depth labels")
        expected_pairs = {
            (mock_index, bin_spec.label)
            for mock_index in range(self.config.n_mocks)
            for bin_spec in self.config.depth_bins
        }
        sample_pairs = [(item.mock_index, item.depth_label) for item in samples]
        if len(sample_pairs) != len(set(sample_pairs)):
            raise ValueError("DepthNullMockBank requires unique mock/depth coverage")
        if set(sample_pairs) != expected_pairs:
            raise ValueError(
                "DepthNullMockBank requires complete mock/depth coverage"
            )
        for sample in samples:
            if not math.isclose(sample.direction_norm, 1.0, rel_tol=0.0, abs_tol=1.0e-12):
                raise ValueError("DepthNullMockBank sample direction must be a unit vector")
        caveats = tuple(_require_non_empty(item, "caveats") for item in self.caveats)
        if not caveats:
            raise ValueError("DepthNullMockBank.caveats must be non-empty")
        object.__setattr__(self, "samples", samples)
        object.__setattr__(self, "caveats", caveats)

    @property
    def owner(self) -> str:
        return Owner.HTT.value

    @property
    def implementation_scope(self) -> str:
        return ImplementationScope.HTT.value

    @property
    def claim_tier(self) -> str:
        return ClaimTier.DIAGNOSTIC_ONLY.value

    @property
    def production_status(self) -> str:
        return "diagnostic_only"

    @property
    def transfer_source(self) -> str:
        return "none"

    @property
    def random_seeds(self) -> tuple[int, ...]:
        return tuple(dict.fromkeys(sample.seed for sample in self.samples))

    @property
    def config_payload(self) -> dict[str, object]:
        return {
            "schema_version": SCHEMA_VERSION,
            "null_model_id": self.null_model_id,
            "physical_scope": self.physical_scope,
            "null_model_scope": self.null_model_scope,
            "config": self.config.to_metadata(),
        }

    @property
    def bank_hash(self) -> str:
        return _stable_hash(
            {
                "config": self.config_payload,
                "samples": [sample.to_metadata() for sample in self.samples],
            }
        )

    @property
    def manifest(self) -> ArtifactManifest:
        return ArtifactManifest(
            artifact_id=f"htt.{self.null_model_id}.depth_null_bank",
            artifact_path=f"memory://htt/{self.null_model_id}/depth_null_bank.json",
            owner=Owner.HTT,
            implementation_scope=ImplementationScope.HTT,
            claim_tier=ClaimTier.DIAGNOSTIC_ONLY,
            production_status="diagnostic_only",
            created_by=f"htt.nulls.{self.null_model_id}",
            git_commit=self.config.git_commit,
            config_hash=self.config.config_hash,
            input_hashes=list(self.config.input_hashes),
            code_version=self.config.git_commit or self.config.worktree_state,
            schema_version=SCHEMA_VERSION,
            caveats=list(self.caveats),
            required_gates=[
                "depth_bins_non_overlapping",
                "direction_unit_vectors_normalized",
                "local_null_fpr_report_required_for_global_tilt_claim",
            ],
            passed_gates=[
                "depth_bins_non_overlapping",
                "direction_unit_vectors_normalized",
            ],
            failed_gates=[],
            statistics_definitions={
                "G_F": "diagnostic null-bank distribution value per depth bin",
                "log_G_F": "logarithmic diagnostic depth response before exponentiation",
                "triggered": "G_F and angular-distance threshold crossing for FPR counting",
            },
        )

    def _g_f_distribution(self) -> dict[str, object]:
        values = np.asarray([sample.g_f for sample in self.samples], dtype=float)
        by_depth: dict[str, object] = {}
        for bin_spec in self.config.depth_bins:
            depth_values = np.asarray(
                [sample.g_f for sample in self.samples if sample.depth_label == bin_spec.label],
                dtype=float,
            )
            by_depth[bin_spec.label] = {"count": int(depth_values.size), **_percentiles(depth_values)}
        return {"count": int(values.size), **_percentiles(values), "by_depth": by_depth}

    def _direction_distribution(self) -> dict[str, object]:
        vectors = np.asarray([sample.direction_unit_vector for sample in self.samples], dtype=float)
        mean = np.mean(vectors, axis=0)
        resultant_length = float(np.linalg.norm(mean))
        if resultant_length > 0.0:
            mean_unit = tuple(float(item) for item in mean / resultant_length)
        else:
            mean_unit = (0.0, 0.0, 0.0)
        angles = np.asarray([sample.angular_separation_deg for sample in self.samples], dtype=float)
        return {
            "count": len(self.samples),
            "coordinate_frame": self.config.coordinate_frame,
            "unit_norm_tolerance": 1.0e-12,
            "mean_direction_unit_vector": list(mean_unit),
            "mean_resultant_length": resultant_length,
            "angular_separation_to_target_deg": _percentiles(angles),
            "antipodal_convention": "signed_direction_not_antipodal",
        }

    def to_payload(self) -> dict[str, object]:
        return {
            "owner": self.owner,
            "implementation_scope": self.implementation_scope,
            "claim_tier": self.claim_tier,
            "production_status": self.production_status,
            "transfer_source": self.transfer_source,
            "schema_version": SCHEMA_VERSION,
            "null_model_id": self.null_model_id,
            "bank_hash": self.bank_hash,
            "manifest": _manifest_payload(self.manifest),
            "metadata": {
                "null_model_scope": self.null_model_scope,
                "physical_scope": self.physical_scope,
                "structured_null_caveat": "null model label only, not a Bianchi family label",
                "direction_convention": {
                    "coordinate_frame": self.config.coordinate_frame,
                    "unit_vector_norm": 1.0,
                    "angular_distance": "acos_clipped_dot_product_degrees",
                },
                "g_f_definition": {
                    "status": "diagnostic_null_distribution",
                    "formula": "G_F = exp((beta / beta_scale)^2)",
                    "beta_scale": self.config.gf_beta_scale,
                },
                "sky_support_status": self.config.sky_support_status,
                "sky_support_hash": self.config.sky_support_hash,
                "mask_hash": self.config.mask_hash,
                "scan_volume_hash": self.config.scan_volume_hash,
                "covariance_status": self.config.covariance_status,
                "null_mock_status": self.config.null_mock_status,
                "random_seeds": list(self.random_seeds),
                "caveats": list(self.caveats),
            },
            "config": self.config.to_metadata(),
            "depth_bins": [item.to_metadata() for item in self.config.depth_bins],
            "distributions": {
                "g_f": self._g_f_distribution(),
                "direction": self._direction_distribution(),
            },
            "samples": [sample.to_metadata() for sample in self.samples],
        }


class LocalBoostDepthNull:
    """Generate observer-side local-boost-only depth null mocks."""

    null_model_id = "local_boost_only"
    physical_scope = "observer_side_local_boost"
    null_model_scope = "local_boost_depth_null"
    amplitude_multiplier = 1.0
    jitter_multiplier = 1.0

    def __init__(self, config: LocalBoostNullConfig):
        self.config = config

    def generate(self) -> DepthNullMockBank:
        samples: list[DepthNullSample] = []
        target = np.asarray(self.config.target_direction, dtype=float)
        for mock_index in range(self.config.n_mocks):
            mock_seed = int(self.config.seed + mock_index)
            rng = np.random.default_rng(mock_seed)
            base_direction = _sample_unit_vector(rng)
            amplitude = max(
                rng.normal(
                    self.config.amplitude_beta_mean * self.amplitude_multiplier,
                    self.config.amplitude_beta_sigma * self.amplitude_multiplier,
                ),
                0.0,
            )
            for depth_index, bin_spec in enumerate(self.config.depth_bins):
                jitter = self.config.direction_jitter_sigma * self.jitter_multiplier
                jitter *= 1.0 + 0.25 * depth_index
                direction = _perturb_unit_vector(base_direction, rng, jitter)
                beta_center = amplitude * bin_spec.response_weight
                beta_noise = rng.normal(0.0, self.config.amplitude_beta_sigma * 0.08)
                beta = max(beta_center + beta_noise, 0.0)
                log_g_f = float((beta / self.config.gf_beta_scale) ** 2)
                g_f = float(math.exp(min(log_g_f, 60.0)))
                angle = _angle_deg(direction, target)
                triggered = (
                    g_f >= self.config.gf_threshold
                    and angle <= self.config.direction_threshold_deg
                )
                samples.append(
                    DepthNullSample(
                        mock_index=mock_index,
                        seed=mock_seed,
                        depth_label=bin_spec.label,
                        z_mid=bin_spec.z_mid,
                        distance_mpc_mid=bin_spec.distance_mpc_mid,
                        beta=beta,
                        log_g_f=log_g_f,
                        g_f=g_f,
                        direction_unit_vector=tuple(float(item) for item in direction),
                        angular_separation_deg=angle,
                        triggered=triggered,
                    )
                )
        return DepthNullMockBank(
            null_model_id=self.null_model_id,
            config=self.config,
            samples=tuple(samples),
            physical_scope=self.physical_scope,
            null_model_scope=self.null_model_scope,
        )


@dataclass(frozen=True)
class LocalBoostNullFprReport:
    """Diagnostic FPR report for local/null depth-bank gates."""

    bank: DepthNullMockBank
    response_overlap_audit: ResponseOverlapAudit
    max_false_positive_rate: float | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.response_overlap_audit, ResponseOverlapAudit):
            raise TypeError("response_overlap_audit must be a ResponseOverlapAudit")
        if self.max_false_positive_rate is None:
            object.__setattr__(
                self,
                "max_false_positive_rate",
                self.bank.config.max_false_positive_rate,
            )
        else:
            object.__setattr__(
                self,
                "max_false_positive_rate",
                _unit_interval(self.max_false_positive_rate, "max_false_positive_rate"),
            )

    @property
    def owner(self) -> str:
        return Owner.HTT.value

    @property
    def implementation_scope(self) -> str:
        return ImplementationScope.HTT.value

    @property
    def claim_tier(self) -> str:
        return ClaimTier.DIAGNOSTIC_ONLY.value

    @property
    def transfer_source(self) -> str:
        return "none"

    @property
    def false_positive_count(self) -> int:
        return sum(
            1
            for mock_index in range(self.bank.config.n_mocks)
            if any(
                sample.triggered
                for sample in self.bank.samples
                if sample.mock_index == mock_index
            )
        )

    @property
    def false_positive_rate(self) -> float:
        return self.false_positive_count / self.bank.config.n_mocks

    @property
    def false_positive_rate_interval(self) -> tuple[float, float]:
        return _wilson_interval(self.false_positive_count, self.bank.config.n_mocks)

    @property
    def false_positive_rate_adjusted(self) -> float:
        return min(1.0, self.false_positive_rate * self.bank.config.look_elsewhere_trials)

    @property
    def false_positive_rate_interval_adjusted(self) -> tuple[float, float]:
        lower, upper = self.false_positive_rate_interval
        trials = self.bank.config.look_elsewhere_trials
        return min(1.0, lower * trials), min(1.0, upper * trials)

    @property
    def blocked_reasons(self) -> tuple[str, ...]:
        blocked: list[str] = []
        interval_upper = self.false_positive_rate_interval_adjusted[1]
        if (
            self.false_positive_rate_adjusted > float(self.max_false_positive_rate)
            or interval_upper > float(self.max_false_positive_rate)
        ):
            blocked.append("local_boost_null_fpr_exceeds_threshold")
        audit = self.response_overlap_audit
        if audit.rank_status != "full_rank":
            blocked.append("response_overlap_rank_not_full")
        if audit.claim_status != "identifiable_diagnostic_candidate":
            blocked.append("response_overlap_claim_status_not_identifiable")
        if audit.projected_rank < 2:
            blocked.append("response_overlap_rank_deficient")
        if audit.null_space_dimension != 0:
            blocked.append("response_overlap_null_space_nonzero")
        if str(self.bank.config.covariance_status) not in _COVARIANCE_PASSING_STATUSES:
            blocked.append("covariance_status_not_supported")
        if self.bank.config.sky_support_status != "pr040_sky_support_attached":
            blocked.append("sky_support_status_not_attached")
        return _dedupe(blocked)

    @property
    def allowed_claim_tier(self) -> ClaimTier:
        if self.blocked_reasons:
            return ClaimTier.DIAGNOSTIC_ONLY
        return ClaimTier.CONDITIONAL

    @property
    def report_hash(self) -> str:
        return _stable_hash(self._hash_payload())

    @property
    def manifest(self) -> ArtifactManifest:
        audit_payload = self.response_overlap_audit.as_payload()
        failed_gates = list(self.blocked_reasons)
        return ArtifactManifest(
            artifact_id=f"htt.{self.bank.null_model_id}.local_null_fpr_report",
            artifact_path=f"memory://htt/{self.bank.null_model_id}/local_null_fpr_report.json",
            owner=Owner.HTT,
            implementation_scope=ImplementationScope.HTT,
            claim_tier=ClaimTier.DIAGNOSTIC_ONLY,
            production_status="diagnostic_only",
            created_by="htt.nulls.local_boost_depth_null",
            git_commit=self.bank.config.git_commit,
            config_hash=self.report_hash,
            input_hashes=[
                *self.bank.config.input_hashes,
                str(audit_payload["config_hash"]),
            ],
            code_version=self.bank.config.git_commit or self.bank.config.worktree_state,
            schema_version=SCHEMA_VERSION,
            caveats=list(DEFAULT_CAVEATS),
            required_gates=[
                "local_boost_null_bank_generated",
                "response_overlap_rank_bound",
                "local_boost_null_fpr_below_threshold",
            ],
            passed_gates=[
                "local_boost_null_bank_generated",
                "response_overlap_rank_bound",
            ]
            if not failed_gates
            else ["local_boost_null_bank_generated"],
            failed_gates=failed_gates,
            statistics_definitions={
                "false_positive_rate": "mock-level threshold-crossing rate under local null bank",
                "adjusted_interval": "Wilson one-sigma interval after look-elsewhere multiplier",
                "rank_status": "PR-060 response-overlap audit state bound to this FPR report",
            },
        )

    def _hash_payload(self) -> dict[str, object]:
        audit_payload = self.response_overlap_audit.as_payload()
        return {
            "schema_version": SCHEMA_VERSION,
            "bank_hash": self.bank.bank_hash,
            "bank_config_hash": self.bank.config.config_hash,
            "response_overlap_config_hash": audit_payload["config_hash"],
            "max_false_positive_rate": self.max_false_positive_rate,
            "gf_threshold": self.bank.config.gf_threshold,
            "direction_threshold_deg": self.bank.config.direction_threshold_deg,
            "look_elsewhere_trials": self.bank.config.look_elsewhere_trials,
            "false_positive_count": self.false_positive_count,
            "false_positive_denominator": self.bank.config.n_mocks,
        }

    def to_metadata(self) -> dict[str, object]:
        audit_payload = self.response_overlap_audit.as_payload()
        return {
            "artifact_name": "local_boost_null_fpr_report_v1",
            "owner": self.owner,
            "implementation_scope": self.implementation_scope,
            "claim_tier": self.claim_tier,
            "allowed_claim_tier": self.allowed_claim_tier.value,
            "production_status": "diagnostic_only",
            "transfer_source": self.transfer_source,
            "schema_version": SCHEMA_VERSION,
            "manifest": _manifest_payload(self.manifest),
            "report_hash": self.report_hash,
            "bank_hash": self.bank.bank_hash,
            "null_model_id": self.bank.null_model_id,
            "null_model_scope": self.bank.null_model_scope,
            "physical_scope": self.bank.physical_scope,
            "false_positive_rate": {
                "raw": self.false_positive_rate,
                "false_positive_count": self.false_positive_count,
                "false_positive_denominator": self.bank.config.n_mocks,
                "interval": list(self.false_positive_rate_interval),
                "adjusted": self.false_positive_rate_adjusted,
                "adjusted_interval": list(self.false_positive_rate_interval_adjusted),
                "max_false_positive_rate": self.max_false_positive_rate,
                "look_elsewhere_trials": self.bank.config.look_elsewhere_trials,
                "detection_rule": (
                    "mock triggers if any depth bin has G_F >= gf_threshold "
                    "and angular_separation_deg <= direction_threshold_deg"
                ),
            },
            "rank_status": {
                "rank_status": self.response_overlap_audit.rank_status,
                "claim_status": self.response_overlap_audit.claim_status,
                "projected_rank": self.response_overlap_audit.projected_rank,
                "condition_number": self.response_overlap_audit.condition_number,
                "null_space_dimension": self.response_overlap_audit.null_space_dimension,
                "response_overlap_artifact_id": self.response_overlap_audit.artifact_id,
                "response_overlap_config_hash": audit_payload["config_hash"],
                "response_overlap_input_hashes": list(audit_payload["input_hashes"]),
                "rho_LB_GT": self.response_overlap_audit.rho_LB_GT,
            },
            "sky_support_hash": self.bank.config.sky_support_hash,
            "mask_hash": self.bank.config.mask_hash,
            "scan_volume_hash": self.bank.config.scan_volume_hash,
            "sky_support_status": self.bank.config.sky_support_status,
            "covariance_status": self.bank.config.covariance_status,
            "null_mock_status": "local_boost_null_fpr_available",
            "config_hash": self.bank.config.config_hash,
            "input_hashes": list(self.bank.config.input_hashes),
            "blocked_reasons": list(self.blocked_reasons),
            "random_seeds": list(self.bank.random_seeds),
            "caveats": list(DEFAULT_CAVEATS),
            "generating_command": self.bank.config.generating_command,
            "git_commit": self.bank.config.git_commit,
            "worktree_state": self.bank.config.worktree_state,
        }


@dataclass(frozen=True)
class GlobalTiltLocalNullGateDecision:
    """Fail-closed gate for downstream global-tilt claim eligibility."""

    allowed: bool
    requested_claim_tier: ClaimTier
    allowed_claim_tier: ClaimTier
    blocked_reasons: tuple[str, ...]
    report: LocalBoostNullFprReport | None = None

    def to_metadata(self) -> dict[str, object]:
        return {
            "allowed": self.allowed,
            "requested_claim_tier": self.requested_claim_tier.value,
            "allowed_claim_tier": self.allowed_claim_tier.value,
            "authorization_scope": "local_null_fpr_prerequisite_only",
            "blocked_reasons": list(self.blocked_reasons),
            "report_hash": None if self.report is None else self.report.report_hash,
        }


def build_local_boost_null_fpr_report(
    bank: DepthNullMockBank,
    *,
    response_overlap_audit: ResponseOverlapAudit,
    max_false_positive_rate: float | None = None,
) -> LocalBoostNullFprReport:
    """Build a diagnostic FPR report from a generated local-null bank."""

    return LocalBoostNullFprReport(
        bank=bank,
        response_overlap_audit=response_overlap_audit,
        max_false_positive_rate=max_false_positive_rate,
    )


def evaluate_global_tilt_local_null_gate(
    report: LocalBoostNullFprReport | None,
    *,
    requested_claim_tier: ClaimTier | str = ClaimTier.CONDITIONAL,
    config_hash: str | None = None,
    input_hashes: Sequence[str] | None = None,
    report_hash: str | None = None,
    response_overlap_config_hash: str | None = None,
) -> GlobalTiltLocalNullGateDecision:
    """Require a matching local-null FPR report before stronger tilt claims."""

    requested = normalize_claim_tier(requested_claim_tier)
    if report is None:
        ceiling = ClaimTier.DIAGNOSTIC_ONLY
        blocked = ["local_boost_null_fpr_missing"]
        if _tier_exceeds(requested, ceiling):
            blocked.append("requested_claim_tier_exceeds_local_null_ceiling")
        return GlobalTiltLocalNullGateDecision(
            allowed=False,
            requested_claim_tier=requested,
            allowed_claim_tier=ceiling,
            blocked_reasons=tuple(blocked),
            report=None,
        )

    ceiling = report.allowed_claim_tier
    blocked = list(report.blocked_reasons)
    if config_hash is not None and report.bank.config.config_hash != config_hash:
        blocked.append("local_boost_null_config_hash_mismatch")
    if input_hashes is not None:
        expected = tuple(input_hashes)
        if tuple(report.bank.config.input_hashes) != expected:
            blocked.append("local_boost_null_input_hashes_mismatch")
    if report_hash is not None and report.report_hash != report_hash:
        blocked.append("local_boost_null_report_hash_mismatch")
    if (
        response_overlap_config_hash is not None
        and report.response_overlap_audit.manifest.config_hash
        != response_overlap_config_hash
    ):
        blocked.append("response_overlap_config_hash_mismatch")
    if _tier_exceeds(requested, ceiling):
        blocked.append("requested_claim_tier_exceeds_local_null_ceiling")
    blocked_reasons = _dedupe(blocked)
    return GlobalTiltLocalNullGateDecision(
        allowed=not blocked_reasons,
        requested_claim_tier=requested,
        allowed_claim_tier=ceiling,
        blocked_reasons=blocked_reasons,
        report=report,
    )


__all__ = [
    "DEFAULT_CAVEATS",
    "DepthBinSpec",
    "DepthNullMockBank",
    "DepthNullSample",
    "GlobalTiltLocalNullGateDecision",
    "LocalBoostDepthNull",
    "LocalBoostNullConfig",
    "LocalBoostNullFprReport",
    "SCHEMA_VERSION",
    "build_local_boost_null_fpr_report",
    "evaluate_global_tilt_local_null_gate",
]
