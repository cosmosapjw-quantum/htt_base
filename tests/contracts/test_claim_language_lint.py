from __future__ import annotations

import subprocess
import sys
import json
from pathlib import Path

from common.semantic_guards.no_overclaim import (
    ClaimLanguageIssue,
    scan_paths,
    scan_text,
)


REPO_ROOT = Path(__file__).resolve().parents[2]


def _rules(text: str) -> list[str]:
    return [issue.rule_id for issue in scan_text(text, path=Path("example.md"))]


def test_scalar_only_family_or_geometry_claims_are_errors() -> None:
    issues = scan_text(
        "The scalar x/Q/F/G departure establishes Bianchi family identification.",
        path=Path("claim.md"),
    )

    assert issues == (
        ClaimLanguageIssue(
            path=Path("claim.md"),
            line=1,
            rule_id="scalar_family_identification",
            severity="error",
            message=(
                "Scalar or low-ell summaries cannot identify Bianchi family "
                "or geometry before native morphology atlas gates."
            ),
            text=(
                "The scalar x/Q/F/G departure establishes Bianchi family "
                "identification."
            ),
        ),
    )


def test_scalar_and_statistical_surrogates_cannot_identify_geometry() -> None:
    forbidden = [
        "Scalar x,Q,Pi,F,G identify Bianchi family VII_h.",
        "The scalar departure detects Bianchi geometry.",
        "Direction coherence proves Bianchi type VII_h.",
        "The BiPoSH norm identifies the Bianchi family.",
        "Largest Bayes factor certifies Bianchi geometry.",
    ]

    for text in forbidden:
        assert scan_text(text, path=Path("claim.md")), text


def test_direct_geometry_detection_claim_is_blocked() -> None:
    assert _rules("Bianchi geometry detected in the low-ell scalar summary.") == [
        "geometry_detected"
    ]
    assert _rules("Bianchi family identified in this artifact.") == [
        "geometry_detected"
    ]
    for text in (
        "Bianchi family is identified in this artifact.",
        "We identify a Bianchi family from the statistic.",
        "Bianchi geometry has been detected in this map.",
        "We detected the Bianchi geometry.",
    ):
        assert _rules(text) == ["geometry_detected"], text


def test_tsc_teff_full_solver_language_is_blocked() -> None:
    assert _rules("Teff closes the full polarisation hierarchy.") == [
        "tsc_teff_full_solver"
    ]
    assert _rules("TSC is a full solver for Bianchi morphology.") == [
        "tsc_teff_full_solver"
    ]
    assert _rules("Teff parameterises full E/B polarisation.") == [
        "tsc_teff_full_solver"
    ]
    assert _rules("TSC is a full Boltzmann hierarchy solver.") == [
        "tsc_teff_full_solver"
    ]
    assert _rules("TSC validates BB for this claim.") == [
        "tsc_teff_full_solver"
    ]


def test_mio_truth_and_external_native_overclaims_are_blocked() -> None:
    assert _rules("MIO certifies truth and adjudicates posterior evidence.") == [
        "mio_truth_or_posterior"
    ]
    assert _rules("AniCLASS transfer is validated as native solver evidence.") == [
        "external_transfer_as_native"
    ]
    assert _rules("AniCLASS external transfer validates native BASS output.") == [
        "external_transfer_as_native"
    ]
    assert _rules("MIO posterior odds favor the model.") == [
        "mio_truth_or_posterior"
    ]
    assert _rules("MIO p-values are added to HTT evidence.") == [
        "mio_truth_or_posterior"
    ]
    assert _rules("The combined MIO+HTT score selects the model.") == [
        "mio_truth_or_posterior"
    ]


def test_negative_guardrails_and_blocked_examples_are_allowed() -> None:
    text = """
Forbidden examples:
- Bianchi geometry detected.
- Teff closes the full polarisation hierarchy.

Do not claim scalar x/Q/F/G statistics imply family identification.
MIO certificates are not truth certificates.
"""

    assert scan_text(text, path=Path("guardrail.md")) == ()


def test_yaml_registered_guardrail_sections_are_allowed() -> None:
    text = """
preregistered_falsifiers:
  claim:
    - a scalar result is promoted to family identification
forbidden_output_language:
  - Bianchi geometry detected
  - Bianchi family identified
"""

    assert scan_text(text, path=Path("spec.yaml")) == ()


def test_yaml_guardrail_exemption_does_not_leak_to_positive_claims() -> None:
    text = """
forbidden_output_language:
  - Bianchi geometry detected
result:
  claim_text: Bianchi family identified in this artifact.
"""

    issues = scan_text(text, path=Path("result.yaml"))

    assert [issue.rule_id for issue in issues] == ["geometry_detected"]
    assert issues[0].line == 5


def test_safe_downclaim_language_passes() -> None:
    safe = """
This is a scalar departure diagnostic.
The result is transfer-conditional under AniCLASS_external provenance.
The output is a diagnostic-only certificate and not HTT evidence.
The morphology compatibility candidate remains blocked for family identification.
HTT-owned posterior/evidence is separate from MIO diagnostic cross-checks.
"""

    assert scan_text(safe, path=Path("safe.md")) == ()


def test_archival_design_paths_are_skipped_by_default(tmp_path: Path) -> None:
    design = tmp_path / "docs" / "design"
    design.mkdir(parents=True)
    legacy = design / "legacy.md"
    legacy.write_text("TSC closes the full polarization hierarchy.\n", encoding="utf-8")

    assert scan_paths([tmp_path / "docs"]) == ()
    assert scan_paths([tmp_path / "docs"], include_archives=True)


def test_cli_fails_for_forbidden_production_claim(tmp_path: Path) -> None:
    bad = tmp_path / "bad.md"
    bad.write_text("Bianchi geometry detected from scalar D_l.\n", encoding="utf-8")

    completed = subprocess.run(
        [sys.executable, "scripts/check_claim_language.py", str(bad), "--dry-run"],
        cwd=REPO_ROOT,
        text=True,
        capture_output=True,
        check=False,
    )

    assert completed.returncode == 1
    assert "geometry_detected" in completed.stdout


def test_cli_scans_nested_metadata_files(tmp_path: Path) -> None:
    bad = tmp_path / "bad.json"
    bad.write_text(
        '{"artifact": {"caption": "MIO p-values are added to HTT evidence"}}\n',
        encoding="utf-8",
    )

    completed = subprocess.run(
        [sys.executable, "scripts/check_claim_language.py", str(bad), "--dry-run"],
        cwd=REPO_ROOT,
        text=True,
        capture_output=True,
        check=False,
    )

    assert completed.returncode == 1
    assert "mio_truth_or_posterior" in completed.stdout


def test_cli_json_output_is_stable_and_parseable(tmp_path: Path) -> None:
    bad = tmp_path / "bad.md"
    bad.write_text("Teff parameterises full E/B polarisation.\n", encoding="utf-8")

    completed = subprocess.run(
        [
            sys.executable,
            "scripts/check_claim_language.py",
            str(bad),
            "--dry-run",
            "--format",
            "json",
        ],
        cwd=REPO_ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    payload = json.loads(completed.stdout)

    assert completed.returncode == 1
    assert list(payload) == ["issue_count", "issues", "missing_paths"]
    assert payload["issues"][0]["rule_id"] == "tsc_teff_full_solver"


def test_cli_skips_missing_paths_but_scans_existing_clean_path(tmp_path: Path) -> None:
    clean = tmp_path / "clean.md"
    clean.write_text(
        "This is a diagnostic-only transfer-conditional result.\n",
        encoding="utf-8",
    )

    completed = subprocess.run(
        [
            sys.executable,
            "scripts/check_claim_language.py",
            str(clean),
            str(tmp_path / "missing"),
            "--dry-run",
        ],
        cwd=REPO_ROOT,
        text=True,
        capture_output=True,
        check=False,
    )

    assert completed.returncode == 0
    assert "No forbidden claim language detected." in completed.stdout
    assert "skipped missing path" in completed.stderr


def test_cli_all_missing_roots_returns_usage_error(tmp_path: Path) -> None:
    completed = subprocess.run(
        [
            sys.executable,
            "scripts/check_claim_language.py",
            str(tmp_path / "missing-a"),
            str(tmp_path / "missing-b"),
            "--dry-run",
        ],
        cwd=REPO_ROOT,
        text=True,
        capture_output=True,
        check=False,
    )

    assert completed.returncode == 2
    assert "No existing paths to scan" in completed.stderr


def test_cli_dry_run_does_not_write_files(tmp_path: Path) -> None:
    clean = tmp_path / "clean.md"
    clean.write_text("A diagnostic-only transfer-conditional result.\n", encoding="utf-8")

    before = sorted(path.name for path in tmp_path.iterdir())
    completed = subprocess.run(
        [sys.executable, "scripts/check_claim_language.py", str(clean), "--dry-run"],
        cwd=REPO_ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    after = sorted(path.name for path in tmp_path.iterdir())

    assert completed.returncode == 0
    assert after == before
