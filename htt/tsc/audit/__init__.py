"""No-overclaim and quarantine helpers for TSC artifacts."""

from .no_overclaim import (
    FORBIDDEN_PHRASE_REGISTRY,
    build_no_overclaim_flags,
    lint_claim_text,
    lint_metadata,
    quarantine_reasons_from_flags,
)

__all__ = [
    "FORBIDDEN_PHRASE_REGISTRY",
    "build_no_overclaim_flags",
    "lint_claim_text",
    "lint_metadata",
    "quarantine_reasons_from_flags",
]
