"""Preferred-axis production promotion and downstream synthesis locks.

This module does not produce preferred axes.  It consumes the canonical
``common.contracts.PreferredAxis`` plus PR-040 ``SkySupport`` metadata and
decides whether a downstream HTT harmonic operation may use the axis.
"""
from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, field
import re

from common.contracts import (
    ClaimTier,
    ImplementationScope,
    Owner,
    PreferredAxis,
    SkySupport,
    normalize_claim_tier,
    normalize_implementation_scope,
    normalize_owner,
)
from common.mock_calibration import (
    AxisMockCalibrationReport,
    evaluate_directional_claim_mock_gate,
)
from htt.direction.preferred_axis import (
    axis_coordinate_blockers,
    axis_provenance_is_stable,
)
from htt.infer.axis_gate import evaluate_axis_gate

__all__ = [
    "AxisPromotionDecision",
    "AxisPromotionRecord",
    "evaluate_axis_promotion",
    "require_axis_for_harmonic_synthesis",
    "require_axis_promotion",
]


_HARMONIC_TARGETS = {"a_lm", "a_2m", "rotate_alm", "harmonic_synthesis"}
_LEGACY_VALUES = {"legacy_unspecified", "pending", "placeholder", "unknown", "none"}
_SHA256_RE = re.compile(r"^sha256:[0-9a-fA-F]{64}$")


@dataclass(frozen=True)
class AxisPromotionRecord:
    """Self-attested gate metadata required before an axis can seed synthesis.

    PR-042 matches axis, sky-support, mask, and mock-coverage fields against the
    live inputs.  Posterior/config/input hashes are carried forward for later
    upstream bundle wiring; they are not cryptographic proof of lineage here.
    """

    axis_provenance_hash: str
    sky_support_hash: str
    mask_hash: str
    mock_coverage_status: str
    mock_calibration_hash: str
    posterior_bundle_hash: str
    config_hash: str
    input_hashes: tuple[str, ...]
    owner: Owner | str = Owner.HTT
    implementation_scope: ImplementationScope | str = ImplementationScope.HTT
    claim_tier: ClaimTier | str = ClaimTier.DIAGNOSTIC_ONLY
    null_mock_status: str = "not_statistical"
    transfer_source: str = "none"
    lineage_status: str = "self_attested_pre_solver"
    caveats: tuple[str, ...] = field(default_factory=tuple)
    generating_command: str = "htt.zoa.axis_promotion.evaluate_axis_promotion"

    def __post_init__(self) -> None:
        owner = normalize_owner(self.owner)
        scope = normalize_implementation_scope(self.implementation_scope)
        claim_tier = normalize_claim_tier(self.claim_tier)
        object.__setattr__(self, "owner", owner)
        object.__setattr__(self, "implementation_scope", scope)
        object.__setattr__(self, "claim_tier", claim_tier)
        object.__setattr__(
            self,
            "input_hashes",
            _require_sha256_sequence(self.input_hashes, "input_hashes"),
        )
        object.__setattr__(
            self,
            "caveats",
            tuple(str(item) for item in self.caveats),
        )
        if owner is not Owner.HTT:
            raise ValueError("AxisPromotionRecord.owner must be HTT")
        if scope is not ImplementationScope.HTT:
            raise ValueError("AxisPromotionRecord.implementation_scope must be htt")
        if claim_tier is not ClaimTier.DIAGNOSTIC_ONLY:
            raise ValueError(
                "AxisPromotionRecord is gate metadata; claim_tier must be "
                "diagnostic_only"
            )
        if not axis_provenance_is_stable(self.axis_provenance_hash):
            raise ValueError(
                "AxisPromotionRecord.axis_provenance_hash must be stable"
            )
        _require_sha256(self.sky_support_hash, "sky_support_hash")
        _require_sha256(self.mask_hash, "mask_hash")
        _require_sha256(self.mock_calibration_hash, "mock_calibration_hash")
        _require_sha256(self.posterior_bundle_hash, "posterior_bundle_hash")
        _require_sha256(self.config_hash, "config_hash")
        if self.mock_coverage_status != "adequate":
            raise ValueError(
                "AxisPromotionRecord.mock_coverage_status must be adequate"
            )
        if not str(self.null_mock_status).strip():
            raise ValueError(
                "AxisPromotionRecord.null_mock_status must be non-empty"
            )
        transfer_source = str(self.transfer_source).strip()
        if not transfer_source:
            raise ValueError("AxisPromotionRecord.transfer_source must be non-empty")
        if transfer_source != "none":
            raise ValueError(
                "AxisPromotionRecord.transfer_source must be 'none' until a "
                "real transfer registry gate is wired"
            )
        object.__setattr__(self, "transfer_source", transfer_source)
        if self.lineage_status != "self_attested_pre_solver":
            raise ValueError(
                "AxisPromotionRecord.lineage_status must be "
                "'self_attested_pre_solver' until upstream bundle matching lands"
            )
        if not str(self.generating_command).strip():
            raise ValueError(
                "AxisPromotionRecord.generating_command must be non-empty"
            )

    def to_metadata(self) -> dict[str, object]:
        """Return JSON-compatible gate provenance metadata."""

        return {
            "owner": self.owner.value,
            "implementation_scope": self.implementation_scope.value,
            "claim_tier": self.claim_tier.value,
            "transfer_source": self.transfer_source,
            "lineage_status": self.lineage_status,
            "axis_provenance_hash": self.axis_provenance_hash,
            "sky_support_hash": self.sky_support_hash,
            "mask_hash": self.mask_hash,
            "mock_coverage_status": self.mock_coverage_status,
            "mock_calibration_hash": self.mock_calibration_hash,
            "posterior_bundle_hash": self.posterior_bundle_hash,
            "config_hash": self.config_hash,
            "input_hashes": list(self.input_hashes),
            "null_mock_status": self.null_mock_status,
            "caveats": list(self.caveats),
            "generating_command": self.generating_command,
        }


@dataclass(frozen=True)
class AxisPromotionDecision:
    """Fail-closed decision for downstream use of a preferred axis."""

    allowed: bool
    required_conditions: tuple[str, ...]
    blocked_reasons: tuple[str, ...]
    axis: PreferredAxis
    sky_support: SkySupport | None
    target: str
    promotion_record: AxisPromotionRecord | None = None
    mock_calibration_report: AxisMockCalibrationReport | None = None
    carry_forward: tuple[str, ...] = ()

    @property
    def reasons(self) -> tuple[str, ...]:
        """Compatibility alias for decision consumers."""

        return self.blocked_reasons

    def to_metadata(self) -> dict[str, object]:
        """Return JSON-compatible gate state for reports/result cards."""

        return {
            "allowed": self.allowed,
            "target": self.target,
            "required_conditions": list(self.required_conditions),
            "blocked_reasons": list(self.blocked_reasons),
            "carry_forward": list(self.carry_forward),
            "axis": {
                "label": self.axis.label,
                "source": self.axis.source,
                "weight_mode": self.axis.weight_mode,
                "selection_mode": self.axis.selection_mode,
                "production_allowed": self.axis.production_allowed,
                "provenance_hash": self.axis.provenance_hash,
                "l_deg": self.axis.l_deg,
                "b_deg": self.axis.b_deg,
            },
            "sky_support": (
                self.sky_support.to_metadata() if self.sky_support is not None else None
            ),
            "promotion_record": (
                self.promotion_record.to_metadata()
                if self.promotion_record is not None
                else None
            ),
            "mock_calibration_report": (
                self.mock_calibration_report.to_metadata()
                if self.mock_calibration_report is not None
                else None
            ),
        }


def evaluate_axis_promotion(
    axis: PreferredAxis,
    *,
    sky_support: SkySupport | None,
    promotion_record: AxisPromotionRecord | None = None,
    mock_calibration_report: AxisMockCalibrationReport | None = None,
    target: str = "directional_synthesis",
) -> AxisPromotionDecision:
    """Evaluate whether an axis may seed downstream HTT synthesis."""

    target_text = str(target)
    base_decision = evaluate_axis_gate(axis, sky_support=sky_support)
    required = (
        *base_decision.required_conditions,
        "PreferredAxis coordinates finite and in l=[0,360), b=[-90,90]",
        "PreferredAxis.provenance_hash is stable",
        "SkySupport.sky_support_hash and mask_hash are sha256",
        "SkySupport.scan_volume_hash is sha256",
        "SkySupport.coordinate_frame/completeness/pixelization are explicit",
        "SkySupport.sky_fraction is finite and in (0,1]",
        "AxisPromotionRecord matches axis/sky/mask/mock provenance",
        "Directional mock calibration report passes retention/bias/coverage/FPR gates",
    )
    blocked: list[str] = list(base_decision.blocked_reasons)
    blocked.extend(axis_coordinate_blockers(axis))
    if not axis_provenance_is_stable(axis.provenance_hash):
        blocked.append("axis_provenance_hash_placeholder")
    if sky_support is not None:
        blocked.extend(_sky_support_blockers(sky_support))
    if promotion_record is None:
        blocked.append("axis_promotion_record_missing")
    else:
        blocked.extend(
            _record_mismatch_blockers(
                axis,
                sky_support,
                promotion_record,
                mock_calibration_report,
            )
        )
    mock_decision = evaluate_directional_claim_mock_gate(
        mock_calibration_report,
        requested_claim_tier=ClaimTier.CONDITIONAL,
        sky_support_hash=(
            sky_support.sky_support_hash if sky_support is not None else None
        ),
        mask_hash=sky_support.mask_hash if sky_support is not None else None,
        scan_volume_hash=(
            sky_support.scan_volume_hash if sky_support is not None else None
        ),
    )
    blocked.extend(mock_decision.blocked_reasons)
    if _is_harmonic_target(target_text) and _is_diagnostic_axis(axis):
        blocked.append(f"diagnostic_axis_cannot_rotate_{_target_reason(target_text)}")

    return AxisPromotionDecision(
        allowed=not blocked,
        required_conditions=required,
        blocked_reasons=_dedupe(blocked),
        axis=axis,
        sky_support=sky_support,
        target=target_text,
        promotion_record=promotion_record,
        mock_calibration_report=mock_calibration_report,
        carry_forward=base_decision.carry_forward,
    )


def require_axis_promotion(
    axis: PreferredAxis,
    *,
    sky_support: SkySupport | None,
    promotion_record: AxisPromotionRecord | None = None,
    mock_calibration_report: AxisMockCalibrationReport | None = None,
    target: str = "directional_synthesis",
) -> PreferredAxis:
    """Return ``axis`` only when the full promotion lock passes."""

    decision = evaluate_axis_promotion(
        axis,
        sky_support=sky_support,
        promotion_record=promotion_record,
        mock_calibration_report=mock_calibration_report,
        target=target,
    )
    if not decision.allowed:
        raise RuntimeError(
            "HTT axis promotion gate failed: "
            + ", ".join(decision.blocked_reasons)
        )
    return axis


def require_axis_for_harmonic_synthesis(
    axis: PreferredAxis,
    *,
    sky_support: SkySupport | None,
    promotion_record: AxisPromotionRecord | None = None,
    mock_calibration_report: AxisMockCalibrationReport | None = None,
    target: str,
) -> PreferredAxis:
    """Fail closed before any ``a_lm``/``a_2m`` rotation or synthesis path."""

    if not _is_harmonic_target(target):
        raise ValueError(
            "target must be one of "
            f"{sorted(_HARMONIC_TARGETS)} for harmonic synthesis"
        )
    return require_axis_promotion(
        axis,
        sky_support=sky_support,
        promotion_record=promotion_record,
        mock_calibration_report=mock_calibration_report,
        target=target,
    )


def _sky_support_blockers(sky_support: SkySupport) -> tuple[str, ...]:
    blocked: list[str] = []
    if not _is_sha256(sky_support.sky_support_hash):
        blocked.append("sky_support_hash_not_sha256")
    if not _is_sha256(sky_support.mask_hash):
        blocked.append("mask_hash_not_sha256")
    if not _is_sha256(sky_support.scan_volume_hash):
        blocked.append("scan_volume_hash_not_sha256")
    if _is_legacy(sky_support.coordinate_frame):
        blocked.append("coordinate_frame_legacy_unspecified")
    if sky_support.sky_fraction is None:
        blocked.append("sky_fraction_missing")
    elif not (0.0 < float(sky_support.sky_fraction) <= 1.0):
        blocked.append("sky_fraction_not_in_open_unit_interval")
    if _is_legacy(sky_support.completeness_status):
        blocked.append("completeness_status_legacy_unspecified")
    if _is_legacy(sky_support.pixelization):
        blocked.append("pixelization_legacy_unspecified")
    if sky_support.nside is None or int(sky_support.nside) <= 0:
        blocked.append("nside_missing")
    elif (
        str(sky_support.pixelization).strip().lower()
        in {"healpix", "equal_area_iso_latitude_ring"}
        and int(sky_support.nside) & (int(sky_support.nside) - 1)
    ):
        blocked.append("nside_not_power_of_two")
    return tuple(blocked)


def _record_mismatch_blockers(
    axis: PreferredAxis,
    sky_support: SkySupport | None,
    record: AxisPromotionRecord,
    mock_calibration_report: AxisMockCalibrationReport | None,
) -> tuple[str, ...]:
    blocked: list[str] = []
    if record.axis_provenance_hash != axis.provenance_hash:
        blocked.append("promotion_record_axis_hash_mismatch")
    if mock_calibration_report is not None:
        if record.mock_calibration_hash != mock_calibration_report.calibration_hash:
            blocked.append("promotion_record_mock_calibration_hash_mismatch")
        if record.null_mock_status != mock_calibration_report.null_mock_status:
            blocked.append("promotion_record_null_mock_status_mismatch")
    if sky_support is None:
        return tuple(blocked)
    if record.sky_support_hash != sky_support.sky_support_hash:
        blocked.append("promotion_record_sky_support_hash_mismatch")
    if record.mask_hash != sky_support.mask_hash:
        blocked.append("promotion_record_mask_hash_mismatch")
    if record.mock_coverage_status != sky_support.mock_coverage_status:
        blocked.append("promotion_record_mock_coverage_mismatch")
    return tuple(blocked)


def _dedupe(values: Sequence[str]) -> tuple[str, ...]:
    seen: set[str] = set()
    out: list[str] = []
    for value in values:
        if value not in seen:
            seen.add(value)
            out.append(value)
    return tuple(out)


def _is_diagnostic_axis(axis: PreferredAxis) -> bool:
    return (
        not axis.production_allowed
        or axis.source != "fiducial_posterior"
        or axis.selection_mode != "mock_calibrated"
    )


def _is_harmonic_target(target: str) -> bool:
    return str(target) in _HARMONIC_TARGETS


def _target_reason(target: str) -> str:
    return "a_lm" if target == "rotate_alm" else str(target)


def _is_legacy(value: str) -> bool:
    return str(value).strip().lower() in _LEGACY_VALUES


def _is_sha256(value: str) -> bool:
    return _SHA256_RE.fullmatch(str(value).strip()) is not None


def _require_sha256(value: str, field_name: str) -> None:
    if not _is_sha256(value):
        raise ValueError(
            f"AxisPromotionRecord.{field_name} must be sha256:<64 hex chars>"
        )


def _require_sha256_sequence(values: Sequence[str], field_name: str) -> tuple[str, ...]:
    if not values:
        raise ValueError(f"AxisPromotionRecord.{field_name} must be non-empty")
    out = tuple(str(value) for value in values)
    for value in out:
        _require_sha256(value, field_name)
    return out
