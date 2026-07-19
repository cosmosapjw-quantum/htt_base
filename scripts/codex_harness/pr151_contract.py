"""Shared terminal contract for the PR-151 DESI lane.

This module deliberately contains only immutable path/command declarations so
the writer and the read-only progress verifier cannot silently drift apart.
"""
from __future__ import annotations

from pathlib import Path

ACQUISITION_MANIFEST = "desi_dr1_mock_acquisition_manifest.json"
FINALIZATION_RECEIPT = "pr151_finalization_receipt.json"

EXPECTED_ARTIFACTS = (
    "docs/generated/desi_official_mock_card.json",
    "docs/generated/pr151_mock_manifest.json",
    "docs/generated/pr151_per_mock_refit.json",
    "docs/generated/pr151_two_tier_covariance.json",
    "docs/generated/pr151_component_confusion.json",
    "docs/generated/pr151_survey_conditional_null.json",
    "docs/generated/pr151_captions.json",
    "docs/generated/pr151_mutation_report.json",
    "docs/generated/pr151_artifact_manifest.json",
)


def finalize_commands(target: Path, repo: Path) -> list[list[str]]:
    """Return the exact, ordered production finalization command contract."""
    target = target.resolve()
    repo = repo.resolve()
    py = str(repo / "venv/bin/python")
    manifest = str(target / ACQUISITION_MANIFEST)
    return [
        [py, "-B", str(repo / "scripts/desi_official_mock_card.py"),
         "--acquisition-manifest", manifest, "--jobs", "12"],
        [py, "-B", str(repo / "scripts/codex_harness/run_pr151_desi_exact_selection.py"),
         "--write"],
        [py, "-B", str(repo / "scripts/desi_official_mock_card.py"),
         "--acquisition-manifest", manifest, "--jobs", "12", "--check"],
        [py, "-B", str(repo / "scripts/codex_harness/run_pr151_desi_exact_selection.py"),
         "--check"],
    ]


__all__ = [
    "ACQUISITION_MANIFEST", "EXPECTED_ARTIFACTS", "FINALIZATION_RECEIPT",
    "finalize_commands",
]
