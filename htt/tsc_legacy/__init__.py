"""Legacy boundary metadata for the TSC package.

TSC remains import-compatible for old overlays and reproducibility checks, but
new framework artifacts must treat it as ``TSC_LEGACY`` and legacy
reproduction only.
"""

from __future__ import annotations

from common.contracts import (
    ArtifactManifest,
    BundleKind,
    ClaimTier,
    ImplementationScope,
    Owner,
    assert_owner_can_emit_bundle,
)

TSC_LEGACY_IMPORT_COMPATIBLE = True
TSC_ACTIVE_SCIENCE_OWNER = False
TSC_OWNER = Owner.TSC_LEGACY
TSC_IMPLEMENTATION_SCOPE = ImplementationScope.TSC_LEGACY
TSC_ALLOWED_BUNDLE_KIND = BundleKind.LEGACY_REPRODUCTION
TSC_DEPRECATION_STATUS = "legacy_reproduction_only"
TSC_DEPRECATION_CAVEAT = (
    "TSC is retained for legacy reproduction and advisory chart diagnostics; "
    "it is not posterior-producing, not HTT evidence, not a MIO certificate, "
    "not a native solver, and not family identification."
)

_ALLOWED_LEGACY_CLAIM_TIERS = {
    ClaimTier.CONDITIONAL,
    ClaimTier.DIAGNOSTIC_ONLY,
}


def assert_legacy_reproduction_manifest(
    manifest: ArtifactManifest,
) -> ArtifactManifest:
    """Return ``manifest`` only when it is a bounded TSC legacy artifact."""

    if not isinstance(manifest, ArtifactManifest):
        raise TypeError("TSC legacy artifacts require ArtifactManifest metadata")
    if manifest.owner is not TSC_OWNER:
        raise ValueError("TSC legacy artifacts must use owner TSC_LEGACY")
    if manifest.implementation_scope is not TSC_IMPLEMENTATION_SCOPE:
        raise ValueError(
            "TSC legacy artifacts must use implementation_scope tsc_legacy"
        )
    if manifest.claim_tier not in _ALLOWED_LEGACY_CLAIM_TIERS:
        raise ValueError(
            "TSC legacy artifacts must stay conditional or diagnostic_only"
        )
    assert_owner_can_emit_bundle(TSC_OWNER, TSC_ALLOWED_BUNDLE_KIND)
    return manifest


__all__ = [
    "TSC_ACTIVE_SCIENCE_OWNER",
    "TSC_ALLOWED_BUNDLE_KIND",
    "TSC_DEPRECATION_CAVEAT",
    "TSC_DEPRECATION_STATUS",
    "TSC_IMPLEMENTATION_SCOPE",
    "TSC_LEGACY_IMPORT_COMPATIBLE",
    "TSC_OWNER",
    "assert_legacy_reproduction_manifest",
]
