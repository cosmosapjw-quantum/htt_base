"""Depth-resolved survey/selection null banks for HTT diagnostics."""
from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
import math

import numpy as np

from common.contracts import (
    ArtifactManifest,
    ClaimTier,
    ImplementationScope,
    Owner,
    normalize_claim_tier,
)
from htt.departure.response_overlap import ResponseOverlapAudit
from htt.nulls.local_boost_depth_null import (
    _COVARIANCE_PASSING_STATUSES,
    _angle_deg,
    _dedupe,
    _manifest_payload,
    _require_non_empty,
    _require_sha256,
    _stable_hash,
    _tier_exceeds,
    _unit_interval,
    _unit_vector,
    _wilson_interval,
    DepthNullMockBank,
    DepthNullSample,
    LocalBoostNullConfig,
)


SCHEMA_VERSION = "htt.survey_systematic_nulls.v1"
SURVEY_SYSTEMATIC_CAVEATS = (
    "diagnostic_survey_systematic_null_calibration_only",
    "does_not_authorize_global_tilt_claim",
    "does_not_identify_bianchi_family",
    "no_native_solver_values",
)
_SELECTION_COMPLETENESS_PASSING_STATUSES = {
    "depth_dependent_selection_metadata_attached",
    "selection_response_metadata_attached",
    "mock_calibrated_selection_response_attached",
}
_SURVEY_AXIS_COHERENCE_PASSING_STATUSES = {
    "survey_axis_coherence_calibration_attached",
    "survey_axis_metadata_attached",
    "mock_calibrated_survey_axis_attached",
}
_MAX_SURVEY_SYSTEMATIC_FPR_CEILING = 0.2
_MAX_RESPONSE_OVERLAP_CONDITION_NUMBER = 1.0e8


@dataclass(frozen=True)
class SelectionResponseMetadata:
    """Selection-function provenance carried by PR-062 survey null banks."""

    selection_function_id: str
    selection_function_hash: str
    selection_metadata_hash: str
    depth_response_hash: str
    source_catalog: str
    completeness_status: str
    completeness_axis: Sequence[object]
    depth_response_label: str

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "selection_function_id",
            _require_non_empty(
                self.selection_function_id,
                "selection_function_id",
            ),
        )
        object.__setattr__(
            self,
            "selection_function_hash",
            _require_sha256(
                self.selection_function_hash,
                "selection_function_hash",
            ),
        )
        object.__setattr__(
            self,
            "selection_metadata_hash",
            _require_sha256(
                self.selection_metadata_hash,
                "selection_metadata_hash",
            ),
        )
        object.__setattr__(
            self,
            "depth_response_hash",
            _require_sha256(self.depth_response_hash, "depth_response_hash"),
        )
        object.__setattr__(
            self,
            "source_catalog",
            _require_non_empty(self.source_catalog, "source_catalog"),
        )
        object.__setattr__(
            self,
            "completeness_status",
            _require_non_empty(self.completeness_status, "completeness_status"),
        )
        object.__setattr__(
            self,
            "completeness_axis",
            _unit_vector(self.completeness_axis, "completeness_axis"),
        )
        object.__setattr__(
            self,
            "depth_response_label",
            _require_non_empty(self.depth_response_label, "depth_response_label"),
        )

    @property
    def input_hashes(self) -> tuple[str, str, str]:
        return (
            self.selection_metadata_hash,
            self.selection_function_hash,
            self.depth_response_hash,
        )

    def to_metadata(self) -> dict[str, object]:
        return {
            "selection_function_id": self.selection_function_id,
            "selection_function_hash": self.selection_function_hash,
            "selection_metadata_hash": self.selection_metadata_hash,
            "depth_response_hash": self.depth_response_hash,
            "source_catalog": self.source_catalog,
            "completeness_status": self.completeness_status,
            "completeness_axis": list(self.completeness_axis),
            "depth_response_label": self.depth_response_label,
            "selection_metadata_role": "survey_selection_response_null_provenance",
        }


@dataclass(frozen=True)
class SurveyAxisMetadata:
    """Survey-axis provenance for coherent direction/depth systematic nulls."""

    survey_axis_id: str
    survey_axis_hash: str
    survey_axis: Sequence[object]
    axis_origin: str
    coordinate_frame: str
    coherence_status: str

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "survey_axis_id",
            _require_non_empty(self.survey_axis_id, "survey_axis_id"),
        )
        object.__setattr__(
            self,
            "survey_axis_hash",
            _require_sha256(self.survey_axis_hash, "survey_axis_hash"),
        )
        object.__setattr__(
            self,
            "survey_axis",
            _unit_vector(self.survey_axis, "survey_axis"),
        )
        object.__setattr__(
            self,
            "axis_origin",
            _require_non_empty(self.axis_origin, "axis_origin"),
        )
        object.__setattr__(
            self,
            "coordinate_frame",
            _require_non_empty(self.coordinate_frame, "coordinate_frame"),
        )
        object.__setattr__(
            self,
            "coherence_status",
            _require_non_empty(self.coherence_status, "coherence_status"),
        )

    @property
    def input_hashes(self) -> tuple[str]:
        return (self.survey_axis_hash,)

    def to_metadata(self) -> dict[str, object]:
        return {
            "survey_axis_id": self.survey_axis_id,
            "survey_axis_hash": self.survey_axis_hash,
            "survey_axis": list(self.survey_axis),
            "axis_origin": self.axis_origin,
            "coordinate_frame": self.coordinate_frame,
            "coherence_status": self.coherence_status,
            "survey_axis_role": "survey_window_directional_systematic_null_provenance",
        }


@dataclass(frozen=True)
class SurveySystematicNullMockBank:
    """Generated HTT survey/systematic null bank with manifest provenance."""

    null_model_id: str
    config: LocalBoostNullConfig
    selection_metadata: SelectionResponseMetadata
    samples: Sequence[DepthNullSample]
    physical_scope: str
    null_model_scope: str
    survey_axis_metadata: SurveyAxisMetadata | None = None
    caveats: tuple[str, ...] = SURVEY_SYSTEMATIC_CAVEATS

    def __post_init__(self) -> None:
        if not isinstance(self.selection_metadata, SelectionResponseMetadata):
            raise TypeError("selection_metadata must be a SelectionResponseMetadata")
        if (
            self.survey_axis_metadata is not None
            and not isinstance(self.survey_axis_metadata, SurveyAxisMetadata)
        ):
            raise TypeError("survey_axis_metadata must be a SurveyAxisMetadata")
        base_bank = DepthNullMockBank(
            null_model_id=_require_non_empty(self.null_model_id, "null_model_id"),
            config=self.config,
            samples=tuple(self.samples),
            physical_scope=_require_non_empty(self.physical_scope, "physical_scope"),
            null_model_scope=_require_non_empty(
                self.null_model_scope,
                "null_model_scope",
            ),
            caveats=tuple(self.caveats),
        )
        object.__setattr__(self, "_base_bank", base_bank)
        object.__setattr__(self, "null_model_id", base_bank.null_model_id)
        object.__setattr__(self, "samples", base_bank.samples)
        object.__setattr__(self, "physical_scope", base_bank.physical_scope)
        object.__setattr__(self, "null_model_scope", base_bank.null_model_scope)
        object.__setattr__(self, "caveats", base_bank.caveats)

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
        return self._base_bank.random_seeds

    @property
    def input_hashes(self) -> tuple[str, ...]:
        axis_hashes = (
            ()
            if self.survey_axis_metadata is None
            else self.survey_axis_metadata.input_hashes
        )
        return (
            *self.config.input_hashes,
            *self.selection_metadata.input_hashes,
            *axis_hashes,
        )

    @property
    def config_payload(self) -> dict[str, object]:
        return {
            "schema_version": SCHEMA_VERSION,
            "null_model_id": self.null_model_id,
            "physical_scope": self.physical_scope,
            "null_model_scope": self.null_model_scope,
            "config": self.config.to_metadata(),
            "selection_response": self.selection_metadata.to_metadata(),
            "survey_axis": (
                None
                if self.survey_axis_metadata is None
                else self.survey_axis_metadata.to_metadata()
            ),
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
        required_gates = [
            "depth_bins_non_overlapping",
            "direction_unit_vectors_normalized",
            "selection_response_metadata_hashed",
        ]
        passed_gates = [
            "depth_bins_non_overlapping",
            "direction_unit_vectors_normalized",
            "selection_response_metadata_hashed",
        ]
        if self.survey_axis_metadata is not None:
            required_gates.append("survey_axis_metadata_hashed")
            passed_gates.append("survey_axis_metadata_hashed")
        return ArtifactManifest(
            artifact_id=f"htt.{self.null_model_id}.survey_systematic_null_bank",
            artifact_path=f"memory://htt/{self.null_model_id}/survey_systematic_null_bank.json",
            owner=Owner.HTT,
            implementation_scope=ImplementationScope.HTT,
            claim_tier=ClaimTier.DIAGNOSTIC_ONLY,
            production_status="diagnostic_only",
            created_by=f"htt.nulls.{self.null_model_id}",
            git_commit=self.config.git_commit,
            config_hash=self.config.config_hash,
            input_hashes=list(self.input_hashes),
            code_version=self.config.git_commit or self.config.worktree_state,
            schema_version=SCHEMA_VERSION,
            caveats=list(self.caveats),
            required_gates=required_gates,
            passed_gates=passed_gates,
            failed_gates=[],
            statistics_definitions={
                "G_F": "diagnostic survey/systematic null-bank distribution per depth bin",
                "triggered": "G_F and angular-distance threshold crossing for mock-level FPR",
                "selection_response": "hashed caller-supplied selection metadata used by the null generator",
            },
        )

    def _g_f_distribution(self) -> dict[str, object]:
        return self._base_bank._g_f_distribution()

    def _direction_distribution(self) -> dict[str, object]:
        return self._base_bank._direction_distribution()

    def to_payload(self) -> dict[str, object]:
        metadata: dict[str, object] = {
            "null_model_scope": self.null_model_scope,
            "physical_scope": self.physical_scope,
            "structured_null_caveat": "survey/systematic label only, not a Bianchi family label",
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
            "selection_response": self.selection_metadata.to_metadata(),
            "sky_support_status": self.config.sky_support_status,
            "sky_support_hash": self.config.sky_support_hash,
            "mask_hash": self.config.mask_hash,
            "scan_volume_hash": self.config.scan_volume_hash,
            "covariance_status": self.config.covariance_status,
            "null_mock_status": self.config.null_mock_status,
            "random_seeds": list(self.random_seeds),
            "caveats": list(self.caveats),
        }
        if self.survey_axis_metadata is not None:
            metadata["survey_axis"] = self.survey_axis_metadata.to_metadata()
            metadata["axis_coherence"] = {
                "axis_alignment_status": "survey_axis_directional_null",
                "coherence_reference_hash": self.survey_axis_metadata.survey_axis_hash,
            }
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
            "metadata": metadata,
            "config": self.config.to_metadata(),
            "depth_bins": [item.to_metadata() for item in self.config.depth_bins],
            "distributions": {
                "g_f": self._g_f_distribution(),
                "direction": self._direction_distribution(),
            },
            "samples": [sample.to_metadata() for sample in self.samples],
        }


class SelectionResponseDepthNull:
    """Generate depth-resolved mocks from selection-response metadata."""

    null_model_id = "selection_response_depth"
    physical_scope = "observer_side_survey_selection"
    null_model_scope = "selection_response_depth_null"
    amplitude_multiplier = 1.0
    jitter_multiplier = 1.0

    def __init__(
        self,
        config: LocalBoostNullConfig,
        *,
        selection_metadata: SelectionResponseMetadata,
    ) -> None:
        if not isinstance(selection_metadata, SelectionResponseMetadata):
            raise TypeError("selection_metadata must be a SelectionResponseMetadata")
        self.config = config
        self.selection_metadata = selection_metadata

    def _base_axis(self) -> np.ndarray:
        return np.asarray(self.selection_metadata.completeness_axis, dtype=float)

    def _sample_direction(
        self,
        rng: np.random.Generator,
        base_axis: np.ndarray,
        depth_index: int,
    ) -> np.ndarray:
        jitter = self.config.direction_jitter_sigma * self.jitter_multiplier
        jitter *= 1.0 + 0.18 * depth_index
        for _ in range(32):
            vector = base_axis + rng.normal(0.0, jitter, size=3)
            norm = float(np.linalg.norm(vector))
            if norm > 0.0:
                return vector / norm
        return base_axis

    def _beta_for_depth(
        self,
        rng: np.random.Generator,
        amplitude: float,
        response_weight: float,
        depth_index: int,
    ) -> float:
        depth_gradient = 1.0 + 0.12 * depth_index
        beta_center = amplitude * response_weight * depth_gradient
        beta_noise = rng.normal(0.0, self.config.amplitude_beta_sigma * 0.06)
        return max(beta_center + beta_noise, 0.0)

    def generate(self) -> SurveySystematicNullMockBank:
        rng = np.random.default_rng(self.config.seed)
        samples: list[DepthNullSample] = []
        target = np.asarray(self.config.target_direction, dtype=float)
        base_axis = self._base_axis()
        for mock_index in range(self.config.n_mocks):
            mock_seed = int(self.config.seed + mock_index)
            amplitude = max(
                rng.normal(
                    self.config.amplitude_beta_mean * self.amplitude_multiplier,
                    self.config.amplitude_beta_sigma * self.amplitude_multiplier,
                ),
                0.0,
            )
            for depth_index, bin_spec in enumerate(self.config.depth_bins):
                direction = self._sample_direction(rng, base_axis, depth_index)
                beta = self._beta_for_depth(
                    rng,
                    amplitude,
                    bin_spec.response_weight,
                    depth_index,
                )
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
        return SurveySystematicNullMockBank(
            null_model_id=self.null_model_id,
            config=self.config,
            selection_metadata=self.selection_metadata,
            samples=tuple(samples),
            physical_scope=self.physical_scope,
            null_model_scope=self.null_model_scope,
        )


@dataclass(frozen=True)
class SurveySystematicNullFprReport:
    """Diagnostic FPR report for PR-062 survey/systematic null banks."""

    bank: SurveySystematicNullMockBank
    response_overlap_audit: ResponseOverlapAudit
    max_false_positive_rate: float | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.bank, SurveySystematicNullMockBank):
            raise TypeError("bank must be a SurveySystematicNullMockBank")
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
        if float(self.max_false_positive_rate) > _MAX_SURVEY_SYSTEMATIC_FPR_CEILING:
            blocked.append("survey_systematic_null_fpr_ceiling_not_strict")
        if (
            self.false_positive_rate_adjusted > float(self.max_false_positive_rate)
            or interval_upper > float(self.max_false_positive_rate)
        ):
            blocked.append("survey_systematic_null_fpr_exceeds_threshold")
        audit = self.response_overlap_audit
        if audit.rank_status != "full_rank":
            blocked.append("response_overlap_rank_not_full")
        if audit.claim_status != "identifiable_diagnostic_candidate":
            blocked.append("response_overlap_claim_status_not_identifiable")
        if audit.projected_rank < 2:
            blocked.append("response_overlap_rank_deficient")
        if audit.null_space_dimension != 0:
            blocked.append("response_overlap_null_space_nonzero")
        condition_number = float(audit.condition_number)
        if (
            not math.isfinite(condition_number)
            or condition_number > _MAX_RESPONSE_OVERLAP_CONDITION_NUMBER
        ):
            blocked.append("response_overlap_condition_number_too_high")
        if str(self.bank.config.covariance_status) not in _COVARIANCE_PASSING_STATUSES:
            blocked.append("covariance_status_not_supported")
        if self.bank.config.sky_support_status != "pr040_sky_support_attached":
            blocked.append("sky_support_status_not_attached")
        if (
            self.bank.selection_metadata.completeness_status
            not in _SELECTION_COMPLETENESS_PASSING_STATUSES
        ):
            blocked.append("selection_completeness_status_not_attached")
        if (
            self.bank.survey_axis_metadata is not None
            and self.bank.survey_axis_metadata.coherence_status
            not in _SURVEY_AXIS_COHERENCE_PASSING_STATUSES
        ):
            blocked.append("survey_axis_coherence_status_not_attached")
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
            artifact_id=f"htt.{self.bank.null_model_id}.survey_systematic_null_fpr_report",
            artifact_path=f"memory://htt/{self.bank.null_model_id}/survey_systematic_null_fpr_report.json",
            owner=Owner.HTT,
            implementation_scope=ImplementationScope.HTT,
            claim_tier=ClaimTier.DIAGNOSTIC_ONLY,
            production_status="diagnostic_only",
            created_by="htt.nulls.selection_response_depth",
            git_commit=self.bank.config.git_commit,
            config_hash=self.report_hash,
            input_hashes=[
                *self.bank.input_hashes,
                str(audit_payload["config_hash"]),
            ],
            code_version=self.bank.config.git_commit or self.bank.config.worktree_state,
            schema_version=SCHEMA_VERSION,
            caveats=list(SURVEY_SYSTEMATIC_CAVEATS),
            required_gates=[
                "survey_systematic_null_bank_generated",
                "response_overlap_rank_bound",
                "survey_systematic_null_fpr_below_threshold",
            ],
            passed_gates=[
                "survey_systematic_null_bank_generated",
                "response_overlap_rank_bound",
                "survey_systematic_null_fpr_below_threshold",
            ]
            if not failed_gates
            else ["survey_systematic_null_bank_generated"],
            failed_gates=failed_gates,
            statistics_definitions={
                "false_positive_rate": "mock-level threshold-crossing rate under survey/systematic null bank",
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
            "selection_metadata_hash": self.bank.selection_metadata.selection_metadata_hash,
            "survey_axis_hash": (
                None
                if self.bank.survey_axis_metadata is None
                else self.bank.survey_axis_metadata.survey_axis_hash
            ),
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
            "artifact_name": "survey_systematic_null_fpr_report_v1",
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
            "selection_response": self.bank.selection_metadata.to_metadata(),
            "survey_axis": (
                None
                if self.bank.survey_axis_metadata is None
                else self.bank.survey_axis_metadata.to_metadata()
            ),
            "sky_support_hash": self.bank.config.sky_support_hash,
            "mask_hash": self.bank.config.mask_hash,
            "scan_volume_hash": self.bank.config.scan_volume_hash,
            "sky_support_status": self.bank.config.sky_support_status,
            "covariance_status": self.bank.config.covariance_status,
            "null_mock_status": "survey_systematic_null_fpr_available",
            "config_hash": self.bank.config.config_hash,
            "input_hashes": list(self.manifest.input_hashes),
            "blocked_reasons": list(self.blocked_reasons),
            "random_seeds": list(self.bank.random_seeds),
            "caveats": list(SURVEY_SYSTEMATIC_CAVEATS),
            "generating_command": self.bank.config.generating_command,
            "git_commit": self.bank.config.git_commit,
            "worktree_state": self.bank.config.worktree_state,
        }


@dataclass(frozen=True)
class SurveySystematicNullGateDecision:
    """Fail-closed gate for downstream survey/systematic null prerequisites."""

    allowed: bool
    requested_claim_tier: ClaimTier
    allowed_claim_tier: ClaimTier
    blocked_reasons: tuple[str, ...]
    report: SurveySystematicNullFprReport | None = None

    def to_metadata(self) -> dict[str, object]:
        return {
            "allowed": self.allowed,
            "requested_claim_tier": self.requested_claim_tier.value,
            "allowed_claim_tier": self.allowed_claim_tier.value,
            "authorization_scope": "survey_systematic_null_fpr_prerequisite_only",
            "blocked_reasons": list(self.blocked_reasons),
            "report_hash": None if self.report is None else self.report.report_hash,
        }


def build_survey_systematic_null_fpr_report(
    bank: SurveySystematicNullMockBank,
    *,
    response_overlap_audit: ResponseOverlapAudit,
    max_false_positive_rate: float | None = None,
) -> SurveySystematicNullFprReport:
    """Build a diagnostic FPR report from a PR-062 survey/systematic bank."""

    return SurveySystematicNullFprReport(
        bank=bank,
        response_overlap_audit=response_overlap_audit,
        max_false_positive_rate=max_false_positive_rate,
    )


def evaluate_survey_systematic_null_gate(
    report: SurveySystematicNullFprReport | None,
    *,
    requested_claim_tier: ClaimTier | str = ClaimTier.CONDITIONAL,
    config_hash: str | None = None,
    input_hashes: Sequence[str] | None = None,
    report_hash: str | None = None,
    response_overlap_config_hash: str | None = None,
    selection_metadata_hash: str | None = None,
    survey_axis_hash: str | None = None,
    require_external_bindings: bool = False,
) -> SurveySystematicNullGateDecision:
    """Require a matching survey/systematic null FPR report before promotion."""

    requested = normalize_claim_tier(requested_claim_tier)
    if report is None:
        ceiling = ClaimTier.DIAGNOSTIC_ONLY
        blocked = ["survey_systematic_null_fpr_missing"]
        if _tier_exceeds(requested, ceiling):
            blocked.append(
                "requested_claim_tier_exceeds_survey_systematic_null_ceiling"
            )
        return SurveySystematicNullGateDecision(
            allowed=False,
            requested_claim_tier=requested,
            allowed_claim_tier=ceiling,
            blocked_reasons=tuple(blocked),
            report=None,
        )

    ceiling = report.allowed_claim_tier
    blocked = list(report.blocked_reasons)
    if require_external_bindings:
        if config_hash is None:
            blocked.append("survey_systematic_null_config_hash_required")
        if input_hashes is None:
            blocked.append("survey_systematic_null_input_hashes_required")
        if report_hash is None:
            blocked.append("survey_systematic_null_report_hash_required")
        if response_overlap_config_hash is None:
            blocked.append("response_overlap_config_hash_required")
        if selection_metadata_hash is None:
            blocked.append("selection_metadata_hash_required")
        if report.bank.survey_axis_metadata is not None and survey_axis_hash is None:
            blocked.append("survey_axis_hash_required")
    if config_hash is not None and report.bank.config.config_hash != config_hash:
        blocked.append("survey_systematic_null_config_hash_mismatch")
    if input_hashes is not None:
        expected = tuple(input_hashes)
        if tuple(report.bank.input_hashes) != expected:
            blocked.append("survey_systematic_null_input_hashes_mismatch")
    if report_hash is not None and report.report_hash != report_hash:
        blocked.append("survey_systematic_null_report_hash_mismatch")
    if (
        response_overlap_config_hash is not None
        and report.response_overlap_audit.manifest.config_hash
        != response_overlap_config_hash
    ):
        blocked.append("response_overlap_config_hash_mismatch")
    if (
        selection_metadata_hash is not None
        and report.bank.selection_metadata.selection_metadata_hash
        != selection_metadata_hash
    ):
        blocked.append("selection_metadata_hash_mismatch")
    if survey_axis_hash is not None:
        if report.bank.survey_axis_metadata is None:
            blocked.append("survey_axis_hash_missing")
        elif report.bank.survey_axis_metadata.survey_axis_hash != survey_axis_hash:
            blocked.append("survey_axis_hash_mismatch")
    if _tier_exceeds(requested, ceiling):
        blocked.append("requested_claim_tier_exceeds_survey_systematic_null_ceiling")
    blocked_reasons = _dedupe(blocked)
    return SurveySystematicNullGateDecision(
        allowed=not blocked_reasons,
        requested_claim_tier=requested,
        allowed_claim_tier=ceiling,
        blocked_reasons=blocked_reasons,
        report=report,
    )


__all__ = [
    "SCHEMA_VERSION",
    "SURVEY_SYSTEMATIC_CAVEATS",
    "SelectionResponseDepthNull",
    "SelectionResponseMetadata",
    "SurveyAxisMetadata",
    "SurveySystematicNullFprReport",
    "SurveySystematicNullGateDecision",
    "SurveySystematicNullMockBank",
    "build_survey_systematic_null_fpr_report",
    "evaluate_survey_systematic_null_gate",
]
