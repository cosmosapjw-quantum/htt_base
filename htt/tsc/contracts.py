"""TSC-side aliases and vocabulary for the VER2 active-service layer.

The canonical dataclass owners remain under ``common.contracts``. This module
must stay schema-thin: it may alias common contracts and define TSC-local
label vocabulary, but it must not redefine shared manifests or ownership
enums.
"""
from __future__ import annotations

from typing import Final

from common.contracts import (
    Channel,
    TscAdequacyOverlay,
    TscChannelAdequacyBudget,
    TscDomainReport,
    TscResidualReport,
    TscSourceBridgeReport,
    TscUpgradeRecommendation,
)

TSC_NOT_APPLICABLE: Final[str] = "tsc_not_applicable"

ALLOWED_COMBINED_LABELS: Final[tuple[str, ...]] = (
    "source_adequate__propagation_validated",
    "source_adequate__propagation_pending",
    "source_inadequate__propagation_not_evaluated",
    "source_invalid_domain__blocked",
    "trace_ok__spin2_required",
    "trace_only__bb_claim_forbidden",
    "two_field_recommended__one_field_warn",
    "full_resolved_trace_required",
)

ALLOWED_SERVICE_LABELS: Final[tuple[str, ...]] = (
    *ALLOWED_COMBINED_LABELS,
    "te_mixed_channel_requires_spin2",
    "trace_source_exact_on_manifold",
    "trace_source_bound_available",
    "source_bound_within_budget",
    "source_bound_exceeds_budget",
    "source_bridge_bound_pending",
    "source_bridge_not_applicable",
    "eta_correction_small",
    "eta_correction_not_small",
    "linear_bridge_underestimates_risk",
    "stable_no_upgrade",
)

FORBIDDEN_COMBINED_LABELS: Final[tuple[str, ...]] = (
    "tsc_validated_full_polarization",
    "tsc_validated_bianchi_family",
    "source_adequate_implies_observable_adequate",
    "mio_truth_certified_by_tsc",
    "htt_evidence_corrected_by_tsc",
)

FORBIDDEN_TSC_FIELDS: Final[frozenset[str]] = frozenset(
    {
        "allow_reduction",
        "posterior_weight",
        "truth_certified",
        "bianchi_family_detected",
        "full_polarization_validated",
    }
)

CHANNEL_DEFAULT_CLAIM_CEILINGS: Final[dict[Channel, str]] = {
    "TT": "conditional",
    "TE": "conditional",
    "EE": "conditional",
    "BB": "blocked",
    "TB": "blocked",
    "EB": "blocked",
    "BiPoSH": "exploratory",
    "template": "blocked",
    "scalar_summary": "conditional",
}


def serious_artifact_has_tsc_annotation(
    *, has_overlay: bool, metadata: dict[str, object] | None = None
) -> bool:
    """Return whether a serious artifact carries overlay or explicit N/A."""
    if has_overlay:
        return True
    meta = metadata or {}
    return bool(meta.get(TSC_NOT_APPLICABLE))


def validate_tsc_service_labels(labels: tuple[str, ...] | list[str]) -> tuple[str, ...]:
    """Validate TSC-local service labels against the frozen VER2 registry."""
    ordered = tuple(dict.fromkeys(str(label) for label in labels))
    forbidden = tuple(label for label in ordered if label in FORBIDDEN_COMBINED_LABELS)
    if forbidden:
        raise ValueError(
            "forbidden TSC service labels encountered: " + ", ".join(forbidden)
        )
    unknown = tuple(label for label in ordered if label not in ALLOWED_SERVICE_LABELS)
    if unknown:
        raise ValueError(
            "unknown TSC service labels encountered: " + ", ".join(unknown)
        )
    return ordered


__all__ = [
    "ALLOWED_COMBINED_LABELS",
    "ALLOWED_SERVICE_LABELS",
    "CHANNEL_DEFAULT_CLAIM_CEILINGS",
    "FORBIDDEN_COMBINED_LABELS",
    "FORBIDDEN_TSC_FIELDS",
    "TSC_NOT_APPLICABLE",
    "TscAdequacyOverlay",
    "TscChannelAdequacyBudget",
    "TscDomainReport",
    "TscResidualReport",
    "TscSourceBridgeReport",
    "TscUpgradeRecommendation",
    "serious_artifact_has_tsc_annotation",
    "validate_tsc_service_labels",
]
