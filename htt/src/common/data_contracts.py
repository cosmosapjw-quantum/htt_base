"""Observational data-binding contracts.

These contracts describe whether a repo-local observational input is suitable
for diagnostic plotting, raw-catalog analysis, matched-mock calibration, or
end-to-end simulation work. They do not create inference evidence.
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any, Mapping

from common.enum_compat import StrEnum


class DataRole(StrEnum):
    """Canonical roles for repo-local observational data inputs."""

    RAW_CATALOG = "raw_catalog"
    RANDOM_CATALOG = "random_catalog"
    MASK = "mask"
    MOCK_CATALOG = "mock_catalog"
    COVARIANCE = "covariance"
    MAP = "map"
    HARMONIC_PRODUCT = "harmonic_product"


class DataReadinessLevel(StrEnum):
    """Fail-closed readiness levels for observational-data consumers."""

    BLOCKED = "blocked"
    D0_DERIVED_AUDIT_PAYLOAD = "D0"
    D1_PRIMARY_PUBLIC_DATA = "D1"
    D1_RAW_PUBLIC_CATALOG = "D1"
    D2_MATCHED_MOCKS = "D2"
    D3_END_TO_END_SIMULATION = "D3"


class DataAllowedUse(StrEnum):
    """Fail-closed allowed-use lanes for data bindings."""

    INVENTORY_ONLY = "inventory_only"
    DIAGNOSTIC_PLOT_ONLY = "diagnostic_plot_only"
    SCHEMA_CHECK_ONLY = "schema_check_only"
    BLOCKED_FOR_INFERENCE = "blocked_for_inference"
    BLOCKED_FOR_SPECTROSCOPIC_DIPOLE = "blocked_for_spectroscopic_dipole"


_BLOCKING_STATUS = {
    "",
    "missing",
    "missing_or_directory",
    "not_applicable",
    "not_available",
    "not_bound",
    "not_provided",
    "not_statistical",
    "unknown",
}
_CHECKSUM_RE = re.compile(r"^sha256:[0-9a-f]{64}$")
_CERTIFIED_SELECTION_WEIGHT_STATUSES = {
    "native_weights_present",
    "selection_weights_certified",
    "production_selection_weights_certified",
    "selection_model_bound",
}
_CERTIFIED_COVARIANCE_STATUSES = {
    "full_covariance_bound",
    "matched_covariance_calibrated",
    "mock_covariance_calibrated",
    "publication_grade_covariance_bound",
}
_CERTIFIED_NULL_MOCK_STATUSES = {
    "matched_null_mock_bank_bound",
    "matched_null_mocks_bound",
    "end_to_end_mock_bank_bound",
    "end_to_end_simulation_bound",
}
_END_TO_END_NULL_MOCK_STATUSES = {
    "end_to_end_mock_bank_bound",
    "end_to_end_simulation_bound",
}
_CERTIFIED_SUPPORT_PARITY_STATUSES = {
    "support_parity_verified",
    "same_support_verified",
    "matched_support_verified",
}
_BOUND_HTT_GATE_STATUSES = {
    "rank_gate_bound",
    "rank_gate_passed",
    "ppc_bound",
    "ppc_passed",
    "loocv_bound",
    "loocv_passed",
}


def _text(value: object, field_name: str) -> str:
    text = str(value).strip() if value is not None else ""
    if not text:
        raise ValueError(f"{field_name} must be non-empty")
    return text


def _optional_text(value: object) -> str:
    return "" if value is None else str(value).strip()


def _status_bound(value: str) -> bool:
    return value.strip().lower() not in _BLOCKING_STATUS


def _checksum(value: object) -> str:
    text = _text(value, "checksum")
    if text.lower() in _BLOCKING_STATUS or _CHECKSUM_RE.fullmatch(text):
        return text
    raise ValueError("checksum must be a sha256 hash or explicit missing status")


def _provenance_ref_bound(value: str) -> bool:
    text = value.strip().lower()
    if text in _BLOCKING_STATUS:
        return False
    return text.startswith("sha256:") or text.endswith((".json", ".yaml", ".yml"))


def _certified(value: str, allowed: set[str]) -> bool:
    return value.strip().lower() in allowed


@dataclass(frozen=True)
class SurveySupport:
    """Declared support metadata for one observational-data binding."""

    survey_name: str
    release: str
    tracer: str
    sky_region: str
    redshift_range: str
    data_path: str
    checksum: str
    random_or_mask_path: str
    selection_weight_status: str
    covariance_status: str
    null_mock_status: str
    allowed_use: DataAllowedUse | str
    data_role: DataRole | str = DataRole.RAW_CATALOG
    random_or_mask_checksum: str = ""
    covariance_provenance: str = ""
    null_mock_provenance: str = ""
    support_parity_status: str = "not_bound"
    rank_gate_status: str = "not_bound"
    ppc_status: str = "not_bound"
    loocv_status: str = "not_bound"

    def __post_init__(self) -> None:
        object.__setattr__(self, "survey_name", _text(self.survey_name, "survey_name"))
        object.__setattr__(self, "release", _text(self.release, "release"))
        object.__setattr__(self, "tracer", _text(self.tracer, "tracer"))
        object.__setattr__(self, "sky_region", _text(self.sky_region, "sky_region"))
        object.__setattr__(self, "redshift_range", _text(self.redshift_range, "redshift_range"))
        object.__setattr__(self, "data_path", _text(self.data_path, "data_path"))
        object.__setattr__(self, "checksum", _checksum(self.checksum))
        object.__setattr__(self, "random_or_mask_path", _optional_text(self.random_or_mask_path))
        object.__setattr__(
            self,
            "random_or_mask_checksum",
            _optional_text(self.random_or_mask_checksum),
        )
        object.__setattr__(
            self,
            "selection_weight_status",
            _text(self.selection_weight_status, "selection_weight_status"),
        )
        object.__setattr__(self, "covariance_status", _text(self.covariance_status, "covariance_status"))
        object.__setattr__(
            self,
            "covariance_provenance",
            _optional_text(self.covariance_provenance),
        )
        object.__setattr__(self, "null_mock_status", _text(self.null_mock_status, "null_mock_status"))
        object.__setattr__(
            self,
            "null_mock_provenance",
            _optional_text(self.null_mock_provenance),
        )
        object.__setattr__(self, "support_parity_status", _text(self.support_parity_status, "support_parity_status"))
        object.__setattr__(self, "rank_gate_status", _text(self.rank_gate_status, "rank_gate_status"))
        object.__setattr__(self, "ppc_status", _text(self.ppc_status, "ppc_status"))
        object.__setattr__(self, "loocv_status", _text(self.loocv_status, "loocv_status"))
        object.__setattr__(self, "allowed_use", DataAllowedUse(str(self.allowed_use)))
        object.__setattr__(self, "data_role", DataRole(str(self.data_role)))

    def to_metadata(self) -> dict[str, str]:
        return {
            "survey_name": self.survey_name,
            "release": self.release,
            "tracer": self.tracer,
            "sky_region": self.sky_region,
            "redshift_range": self.redshift_range,
            "data_path": self.data_path,
            "checksum": self.checksum,
            "random_or_mask_path": self.random_or_mask_path,
            "random_or_mask_checksum": self.random_or_mask_checksum,
            "selection_weight_status": self.selection_weight_status,
            "covariance_status": self.covariance_status,
            "covariance_provenance": self.covariance_provenance,
            "null_mock_status": self.null_mock_status,
            "null_mock_provenance": self.null_mock_provenance,
            "support_parity_status": self.support_parity_status,
            "rank_gate_status": self.rank_gate_status,
            "ppc_status": self.ppc_status,
            "loocv_status": self.loocv_status,
            "allowed_use": self.allowed_use.value,
            "data_role": self.data_role.value,
        }


@dataclass(frozen=True)
class DataReadinessDecision:
    """Fail-closed result for a requested readiness level."""

    requested_level: DataReadinessLevel
    allowed: bool
    claim_ceiling: str
    blockers: tuple[str, ...]
    support: SurveySupport

    def to_metadata(self) -> dict[str, Any]:
        return {
            "requested_level": self.requested_level.value,
            "allowed": self.allowed,
            "claim_ceiling": self.claim_ceiling,
            "blockers": list(self.blockers),
            "support": self.support.to_metadata(),
        }


def survey_support_from_mapping(payload: Mapping[str, object]) -> SurveySupport:
    """Build a support contract from a JSON-like mapping."""

    return SurveySupport(
        survey_name=payload.get("survey_name", ""),
        release=payload.get("release", ""),
        tracer=payload.get("tracer", ""),
        sky_region=payload.get("sky_region", ""),
        redshift_range=payload.get("redshift_range", ""),
        data_path=payload.get("data_path", ""),
        checksum=payload.get("checksum", ""),
        random_or_mask_path=payload.get("random_or_mask_path", ""),
        random_or_mask_checksum=payload.get("random_or_mask_checksum", ""),
        selection_weight_status=payload.get("selection_weight_status", ""),
        covariance_status=payload.get("covariance_status", ""),
        covariance_provenance=payload.get("covariance_provenance", ""),
        null_mock_status=payload.get("null_mock_status", ""),
        null_mock_provenance=payload.get("null_mock_provenance", ""),
        support_parity_status=payload.get("support_parity_status", "not_bound"),
        rank_gate_status=payload.get("rank_gate_status", "not_bound"),
        ppc_status=payload.get("ppc_status", "not_bound"),
        loocv_status=payload.get("loocv_status", "not_bound"),
        allowed_use=payload.get("allowed_use", ""),
        data_role=payload.get("data_role", DataRole.RAW_CATALOG.value),
    )


def validate_data_readiness(
    support: SurveySupport,
    requested_level: DataReadinessLevel | str,
    *,
    intended_use: str = "diagnostic_inventory",
) -> DataReadinessDecision:
    """Validate support metadata for a requested observational readiness level."""

    level = DataReadinessLevel(str(requested_level))
    blockers: list[str] = []
    checksum = support.checksum.lower()
    intended = intended_use.strip().lower()

    if checksum in _BLOCKING_STATUS:
        blockers.append("data_checksum_missing")
    if support.data_path.lower() in _BLOCKING_STATUS:
        blockers.append("data_path_missing")
    if level == DataReadinessLevel.BLOCKED:
        blockers.append("data_binding_blocked")

    if level in {
        DataReadinessLevel.D1_PRIMARY_PUBLIC_DATA,
        DataReadinessLevel.D2_MATCHED_MOCKS,
        DataReadinessLevel.D3_END_TO_END_SIMULATION,
    }:
        if support.data_role not in {DataRole.RAW_CATALOG, DataRole.MAP, DataRole.HARMONIC_PRODUCT}:
            blockers.append("raw_or_primary_data_role_required")

    if "spectroscopic_dipole" in intended:
        if support.data_role != DataRole.RAW_CATALOG:
            blockers.append("spectroscopic_dipole_requires_raw_catalog")
        if not support.random_or_mask_path:
            blockers.append("random_or_mask_catalog_required_for_spectroscopic_dipole")
        if not _certified(
            support.selection_weight_status,
            _CERTIFIED_SELECTION_WEIGHT_STATUSES,
        ):
            blockers.append("selection_weight_certification_required_for_spectroscopic_dipole")

    if level in {
        DataReadinessLevel.D2_MATCHED_MOCKS,
        DataReadinessLevel.D3_END_TO_END_SIMULATION,
    }:
        if not support.random_or_mask_path:
            blockers.append("matched_random_or_mask_required")
        if not _CHECKSUM_RE.fullmatch(support.random_or_mask_checksum):
            blockers.append("matched_random_or_mask_checksum_required")
        if not _certified(
            support.support_parity_status,
            _CERTIFIED_SUPPORT_PARITY_STATUSES,
        ):
            blockers.append("support_parity_verification_required")
        if not _certified(support.covariance_status, _CERTIFIED_COVARIANCE_STATUSES):
            blockers.append("covariance_required")
        if not _provenance_ref_bound(support.covariance_provenance):
            blockers.append("covariance_provenance_required")
        if not _certified(support.null_mock_status, _CERTIFIED_NULL_MOCK_STATUSES):
            blockers.append("matched_null_mocks_required")
        if not _provenance_ref_bound(support.null_mock_provenance):
            blockers.append("null_mock_provenance_required")
        if not _certified(support.rank_gate_status, _BOUND_HTT_GATE_STATUSES):
            blockers.append("rank_gate_required")
        if not _certified(support.ppc_status, _BOUND_HTT_GATE_STATUSES):
            blockers.append("ppc_gate_required")
        if not _certified(support.loocv_status, _BOUND_HTT_GATE_STATUSES):
            blockers.append("loocv_gate_required")

    if level == DataReadinessLevel.D3_END_TO_END_SIMULATION:
        if not _certified(support.null_mock_status, _END_TO_END_NULL_MOCK_STATUSES):
            blockers.append("end_to_end_simulation_required")

    unique_blockers = tuple(dict.fromkeys(blockers))
    allowed = not unique_blockers
    return DataReadinessDecision(
        requested_level=level,
        allowed=allowed,
        claim_ceiling="diagnostic_only" if allowed else "blocked",
        blockers=unique_blockers,
        support=support,
    )


def support_parity_blockers(
    primary: SurveySupport,
    companion: SurveySupport,
    *,
    required_fields: tuple[str, ...] = (
        "survey_name",
        "release",
        "tracer",
        "sky_region",
        "redshift_range",
    ),
) -> tuple[str, ...]:
    """Return support-mismatch blockers between data and random/mock/cov rows."""

    blockers: list[str] = []
    for field in required_fields:
        left = getattr(primary, field)
        right = getattr(companion, field)
        if left != right:
            blockers.append(f"support_mismatch_{field}")
    return tuple(blockers)


__all__ = [
    "DataAllowedUse",
    "DataReadinessDecision",
    "DataReadinessLevel",
    "DataRole",
    "SurveySupport",
    "support_parity_blockers",
    "survey_support_from_mapping",
    "validate_data_readiness",
]
