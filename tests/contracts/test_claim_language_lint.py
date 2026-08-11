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


def test_cf4_legacy_diagnostics_cannot_be_promoted_to_physics_claims() -> None:
    assert _rules(
        "The 0.0089 curl diagnostic is evidence for physical cosmic vorticity."
    ) == ["legacy_curl_physics_promotion"]
    assert _rules(
        "The 0.0089 curl diagnostic is evidence for cosmic potential flow."
    ) == ["legacy_curl_physics_promotion"]
    assert _rules(
        "Physical cosmic vorticity is supported by the 0.0089 curl diagnostic."
    ) == ["legacy_curl_physics_promotion"]
    assert _rules(
        "Cosmic potential flow is established by the WF curl-div ratio."
    ) == ["legacy_curl_physics_promotion"]
    assert _rules(
        "Physical cosmic vorticity is supported by\n"
        "the 0.0089 curl diagnostic."
    ) == ["legacy_curl_physics_promotion"]
    assert _rules(
        "Cosmic potential flow\n"
        "is established by\n"
        "the WF curl-div ratio."
    ) == ["legacy_curl_physics_promotion"]
    assert _rules(
        "- Physical cosmic vorticity is supported by\n"
        "  the 0.0089 curl diagnostic."
    ) == ["legacy_curl_physics_promotion"]
    assert _rules(
        "> Physical cosmic vorticity is supported by\n"
        "> the 0.0089 curl diagnostic."
    ) == ["legacy_curl_physics_promotion"]
    assert _rules(
        ">> Cosmic potential flow is established by\n"
        ">> the WF curl-div ratio."
    ) == ["legacy_curl_physics_promotion"]
    assert _rules(
        "> - Physical cosmic vorticity is supported by\n"
        ">   the 0.0089 curl diagnostic."
    ) == ["legacy_curl_physics_promotion"]
    assert _rules(
        "> Physical cosmic vorticity is supported by\n"
        "the 0.0089 curl diagnostic."
    ) == ["legacy_curl_physics_promotion"]
    assert _rules(
        ">> Cosmic potential flow is established by\n"
        "the WF curl-div ratio."
    ) == ["legacy_curl_physics_promotion"]
    assert _rules("PR-291 rescues the retired P0 velocity-shape headline.") == [
        "retired_p0_rescue"
    ]


def test_cf4_legacy_downclaims_remain_allowed() -> None:
    safe = """
The 0.0089 curl diagnostic is not evidence for physical cosmic vorticity.
The legacy diagnostic does not establish a cosmic potential flow.
Physical cosmic vorticity is not supported by the 0.0089 curl diagnostic.
Cosmic potential flow is not established by the WF curl-div ratio.
Physical cosmic vorticity is not supported by
the 0.0089 curl diagnostic.
Cosmic potential flow
is not established by
the WF curl-div ratio.
PR-291 does not rescue the retired P0 velocity-shape headline.
"""

    assert scan_text(safe, path=Path("cf4_downclaim.md")) == ()


def test_unrelated_negation_cannot_hide_positive_cf4_or_geometry_claims() -> None:
    cases = (
        "No posterior is computed. The 0.0089 curl diagnostic is evidence for physical cosmic vorticity.",
        "The pipeline is not public. Bianchi geometry detected in the CF4 result.",
        "Without observed execution, this is synthetic. Cosmic potential flow is established by the WF curl-div ratio.",
        "No posterior is computed.\nPhysical cosmic vorticity is supported by\nthe 0.0089 curl diagnostic.",
    )

    for text in cases:
        assert scan_text(text, path=Path("unrelated_negation.md")), text


def test_neighboring_markdown_cell_cannot_hide_allowed_cell_claim() -> None:
    text = """
| Allowed reading | Forbidden reading |
|---|---|
| The 0.0089 curl diagnostic is evidence for physical cosmic vorticity. | Do not claim potential flow. |
"""

    issues = scan_text(text, path=Path("claim_matrix.md"))

    assert [issue.rule_id for issue in issues] == ["legacy_curl_physics_promotion"]


def test_claim_ledger_forbidden_status_is_exact_structured_context() -> None:
    forbidden = """
| Claim | Owner | Status |
|---|---|---|
| PR-291 rescues the retired P0 velocity-shape headline. | HTT | FORBIDDEN / NOT_GRANTED |
"""
    positive = forbidden.replace("FORBIDDEN / NOT_GRANTED", "SUPPORTED")

    assert scan_text(forbidden, path=Path("claim_ledger.md")) == ()
    assert [issue.rule_id for issue in scan_text(positive, path=Path("claim_ledger.md"))] == [
        "retired_p0_rescue"
    ]


def test_unrelated_negation_cannot_hide_source_observable_conflation() -> None:
    text = (
        "No posterior is computed.\n"
        "Source adequacy therefore means\n"
        "the observable is adequate."
    )

    assert [issue.rule_id for issue in scan_text(text, path=Path("source.md"))] == [
        "source_observable_conflation"
    ]


def test_cf4_multiline_scan_respects_fences_and_list_item_boundaries() -> None:
    explanatory = """
```
Physical cosmic vorticity is supported by
the 0.0089 curl diagnostic.
```
- Physical cosmic vorticity is supported by
- the 0.0089 curl diagnostic.
> ```
> Physical cosmic vorticity is supported by
> the 0.0089 curl diagnostic.
> ```
> Physical cosmic vorticity is not supported by
> the 0.0089 curl diagnostic.
> - Physical cosmic vorticity is supported by
> - the 0.0089 curl diagnostic.
> Cosmic potential flow is established by
>> the WF curl-div ratio.
"""

    assert scan_text(explanatory, path=Path("cf4_examples.md")) == ()


def test_cf4_quoted_fence_state_cannot_mask_outside_promotion() -> None:
    escaped = """
> ```
Physical cosmic vorticity is supported by
the 0.0089 curl diagnostic.
> ```
"""
    closed_before_promotion = """
> ```
> quoted example
> ```
Physical cosmic vorticity is supported by
the 0.0089 curl diagnostic.
"""
    single_line_outside = """
> ```text
Physical cosmic vorticity is supported by the 0.0089 curl diagnostic.
> ```
"""
    quoted_after_unclosed_unquoted_fence = """
```
> Physical cosmic vorticity is supported by the 0.0089 curl diagnostic.
```
"""

    assert [
        issue.rule_id
        for issue in scan_text(escaped, path=Path("cf4_escaped_quote_fence.md"))
    ] == ["legacy_curl_physics_promotion"]
    assert [
        issue.rule_id
        for issue in scan_text(
            closed_before_promotion,
            path=Path("cf4_closed_quote_fence.md"),
        )
    ] == ["legacy_curl_physics_promotion"]
    assert [
        issue.rule_id
        for issue in scan_text(
            single_line_outside,
            path=Path("cf4_single_line_outside_quote_fence.md"),
        )
    ] == ["legacy_curl_physics_promotion"]
    assert [
        issue.rule_id
        for issue in scan_text(
            quoted_after_unclosed_unquoted_fence,
            path=Path("cf4_quoted_after_unclosed_fence.md"),
        )
    ] == ["legacy_curl_physics_promotion"]


def test_cf4_quoted_fence_and_lazy_downclaim_controls_remain_allowed() -> None:
    controls = """
> ```text
> Physical cosmic vorticity is supported by the 0.0089 curl diagnostic.
> ```

> Physical cosmic vorticity is not supported by
the 0.0089 curl diagnostic.
"""

    assert scan_text(controls, path=Path("cf4_quote_controls.md")) == ()


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
mutation_registry:
  - {mutation_id: BAD-P0, intended_defect: PR-291 revives the retired P0 headline}
forbidden_uses:
  - PR-291 rescues the retired P0 headline
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


def test_cli_strict_missing_path_fails_before_a_partial_scan(tmp_path: Path) -> None:
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
            "--strict-missing",
            "--dry-run",
        ],
        cwd=REPO_ROOT,
        text=True,
        capture_output=True,
        check=False,
    )

    assert completed.returncode == 2
    assert "strict missing-path check failed" in completed.stderr
    assert completed.stdout == ""


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
