"""Shared semantic guard helpers for claim-language linting."""

from common.semantic_guards.no_overclaim import (
    ClaimLanguageIssue,
    scan_paths,
    scan_text,
)

__all__ = ["ClaimLanguageIssue", "scan_paths", "scan_text"]
