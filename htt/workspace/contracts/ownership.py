"""Canonical ownership and bundle-role firewall.

This workspace-facing module re-exports the COMMON contract vocabulary so
cross-package contracts can import one stable surface without redefining owner
or claim-tier semantics.
"""

from common.contracts import (
    BundleKind,
    ClaimTier,
    ImplementationScope,
    Owner,
    assert_owner_can_emit_bundle,
    normalize_bundle_kind,
    normalize_claim_tier,
    normalize_implementation_scope,
    normalize_owner,
    owner_can_emit_bundle,
)

__all__ = [
    "BundleKind",
    "ClaimTier",
    "ImplementationScope",
    "Owner",
    "assert_owner_can_emit_bundle",
    "normalize_bundle_kind",
    "normalize_claim_tier",
    "normalize_implementation_scope",
    "normalize_owner",
    "owner_can_emit_bundle",
]
