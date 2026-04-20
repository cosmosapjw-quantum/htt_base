"""VER2 SK-07M MIO manifest and prerequisite helpers.

This module keeps MIO-side production-status plumbing inside ``htt/mio/*``
without reopening the shared COMMON contract layer. It maps MIO-local
prerequisite declarations onto the canonical VER2 ``ArtifactManifest``.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping, Literal, Sequence

from common.contracts import ArtifactManifest, ClaimTier, ProductionStatus


SkySupportStatus = Literal["not_applicable", "partial", "complete"]


@dataclass(frozen=True)
class MioPrerequisites:
    """Declarative readiness inputs for one MIO artifact surface."""

    requires_covariance: bool = False
    has_covariance: bool = False
    requires_atlas: bool = False
    has_atlas: bool = False
    requires_null_mocks: bool = False
    has_null_mocks: bool = False
    requires_sky_support: bool = False
    sky_support_status: SkySupportStatus = "not_applicable"
    eligible_for_production: bool = False
    validated: bool = False

    def __post_init__(self) -> None:
        if self.sky_support_status not in {"not_applicable", "partial", "complete"}:
            raise ValueError(
                "sky_support_status must be one of "
                "'not_applicable', 'partial', or 'complete'"
            )
        if self.validated and not self.eligible_for_production:
            raise ValueError(
                "validated=True is only allowed when eligible_for_production=True"
            )


@dataclass(frozen=True)
class MioReadiness:
    """Resolved VER2-ready status for a single MIO artifact."""

    production_status: ProductionStatus
    claim_tier: ClaimTier
    required_gates: tuple[str, ...]
    passed_gates: tuple[str, ...]
    failed_gates: tuple[str, ...]
    caveats: tuple[str, ...]
    public_grade_label: str


def _gate_status(
    *,
    required: bool,
    ready: bool,
    gate_name: str,
    missing_caveat: str,
) -> tuple[tuple[str, ...], tuple[str, ...], tuple[str, ...], tuple[str, ...]]:
    if not required:
        return tuple(), tuple(), tuple(), tuple()
    if ready:
        return (gate_name,), (gate_name,), tuple(), tuple()
    return (gate_name,), tuple(), (gate_name,), (missing_caveat,)


def assess_mio_readiness(prerequisites: MioPrerequisites) -> MioReadiness:
    """Map local prerequisite declarations onto VER2 production metadata."""
    required: list[str] = []
    passed: list[str] = []
    failed: list[str] = []
    caveats: list[str] = []

    gate_rows = (
        _gate_status(
            required=prerequisites.requires_atlas,
            ready=prerequisites.has_atlas,
            gate_name="atlas_ready",
            missing_caveat="atlas_prerequisite_missing",
        ),
        _gate_status(
            required=prerequisites.requires_covariance,
            ready=prerequisites.has_covariance,
            gate_name="covariance_ready",
            missing_caveat="covariance_prerequisite_missing",
        ),
        _gate_status(
            required=prerequisites.requires_null_mocks,
            ready=prerequisites.has_null_mocks,
            gate_name="null_mocks_ready",
            missing_caveat="null_mock_prerequisite_missing",
        ),
    )
    for req, ok, bad, local_caveats in gate_rows:
        required.extend(req)
        passed.extend(ok)
        failed.extend(bad)
        caveats.extend(local_caveats)

    if prerequisites.requires_sky_support:
        required.append("sky_support_complete")
        if prerequisites.sky_support_status == "complete":
            passed.append("sky_support_complete")
        else:
            failed.append("sky_support_complete")
            caveats.append(
                "sky_support_partial"
                if prerequisites.sky_support_status == "partial"
                else "sky_support_missing"
            )

    if prerequisites.requires_atlas and not prerequisites.has_atlas:
        production_status: ProductionStatus = "blocked_missing_atlas"
    elif prerequisites.requires_covariance and not prerequisites.has_covariance:
        production_status = "blocked_missing_covariance"
    elif prerequisites.requires_null_mocks and not prerequisites.has_null_mocks:
        production_status = "blocked_missing_null_mocks"
    elif prerequisites.requires_sky_support and prerequisites.sky_support_status != "complete":
        production_status = "diagnostic_only"
    elif prerequisites.validated:
        production_status = "production_validated"
    elif prerequisites.eligible_for_production:
        production_status = "production_candidate"
    else:
        production_status = "diagnostic_only"

    if production_status.startswith("blocked_"):
        claim_tier: ClaimTier = "blocked"
    elif production_status == "production_validated":
        claim_tier = "validated"
    elif production_status == "production_candidate":
        claim_tier = "conditional"
    else:
        claim_tier = "exploratory"

    public_grade_label = (
        "production-grade"
        if production_status in {"production_candidate", "production_validated"}
        else "diagnostic-only"
    )
    caveats.append(f"public_grade={public_grade_label}")
    caveats.append(f"production_status={production_status}")

    return MioReadiness(
        production_status=production_status,
        claim_tier=claim_tier,
        required_gates=tuple(required),
        passed_gates=tuple(passed),
        failed_gates=tuple(failed),
        caveats=tuple(dict.fromkeys(caveats)),
        public_grade_label=public_grade_label,
    )


def merge_domain_caveats(
    base_caveats: Sequence[str] | None,
    readiness: MioReadiness | None = None,
    *,
    extra_caveats: Sequence[str] | None = None,
) -> list[str]:
    """Combine caller caveats with readiness-derived caveats."""
    merged: list[str] = list(base_caveats) if base_caveats is not None else []
    if extra_caveats is not None:
        merged.extend(str(item) for item in extra_caveats)
    if readiness is not None:
        merged.extend(readiness.caveats)
    return list(dict.fromkeys(merged))


def build_mio_manifest(
    *,
    artifact_id: str,
    artifact_path: str,
    created_by: str,
    git_commit: str | None,
    config_hash: str,
    input_hashes: Sequence[str],
    readiness: MioReadiness,
    code_version: str = "ver2-sk07m",
    schema_version: str = "ver2-v7",
    statistics_definitions: Mapping[str, object] | None = None,
) -> ArtifactManifest:
    """Construct the canonical VER2 manifest for one MIO artifact."""
    return ArtifactManifest(
        artifact_id=artifact_id,
        artifact_path=artifact_path,
        owner="MIO",
        implementation_scope="mio",
        claim_tier=readiness.claim_tier,
        production_status=readiness.production_status,
        created_by=created_by,
        git_commit=git_commit,
        config_hash=config_hash,
        input_hashes=[str(item) for item in input_hashes],
        code_version=code_version,
        schema_version=schema_version,
        caveats=list(readiness.caveats),
        required_gates=list(readiness.required_gates),
        passed_gates=list(readiness.passed_gates),
        failed_gates=list(readiness.failed_gates),
        statistics_definitions=(
            dict(statistics_definitions) if statistics_definitions is not None else {}
        ),
    )


__all__ = [
    "MioPrerequisites",
    "MioReadiness",
    "SkySupportStatus",
    "assess_mio_readiness",
    "build_mio_manifest",
    "merge_domain_caveats",
]
