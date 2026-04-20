"""Helpers for manifest and metadata propagation in VER2 observational shells."""
from __future__ import annotations

from dataclasses import replace
import hashlib
import json
from typing import Any, Mapping, Sequence

from common.contracts import ArtifactManifest, SkySupport

__all__ = ["derive_manifest", "stable_payload_hash", "sky_support_metadata"]


def stable_payload_hash(payload: Any) -> str:
    encoded = json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        default=str,
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()[:16]


def sky_support_metadata(sky_support: SkySupport) -> dict[str, str]:
    return {
        "selection_mode": sky_support.selection_mode,
        "sky_support_hash": sky_support.sky_support_hash,
        "mask_hash": sky_support.mask_hash,
        "mock_coverage_status": sky_support.mock_coverage_status,
        "scan_volume_hash": sky_support.scan_volume_hash,
    }


def derive_manifest(
    parent: ArtifactManifest,
    *,
    artifact_id: str,
    artifact_path: str,
    owner: str | None = None,
    implementation_scope: str | None = None,
    claim_tier: str | None = None,
    production_status: str | None = None,
    created_by: str | None = None,
    caveats: Sequence[str] = (),
    required_gates: Sequence[str] = (),
    passed_gates: Sequence[str] = (),
    failed_gates: Sequence[str] = (),
    statistics_definitions: Mapping[str, Any] | None = None,
    extra_input_hashes: Sequence[str] = (),
) -> ArtifactManifest:
    merged_stats = dict(parent.statistics_definitions)
    if statistics_definitions is not None:
        merged_stats.update(dict(statistics_definitions))
    input_hashes = list(parent.input_hashes)
    if parent.artifact_id not in input_hashes:
        input_hashes.append(parent.artifact_id)
    for item in extra_input_hashes:
        text = str(item)
        if text and text not in input_hashes:
            input_hashes.append(text)
    return replace(
        parent,
        artifact_id=artifact_id,
        artifact_path=artifact_path,
        owner=owner or parent.owner,
        implementation_scope=implementation_scope or parent.implementation_scope,
        claim_tier=claim_tier or parent.claim_tier,
        production_status=production_status or parent.production_status,
        created_by=created_by or parent.created_by,
        input_hashes=input_hashes,
        caveats=list(caveats),
        required_gates=list(required_gates),
        passed_gates=list(passed_gates),
        failed_gates=list(failed_gates),
        statistics_definitions=merged_stats,
    )
