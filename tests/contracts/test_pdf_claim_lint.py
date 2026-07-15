import pytest

import json
from pathlib import Path

import scripts.pdf_claim_lint as pdf_claim_lint
from scripts.pdf_claim_lint import lint_pages, verify_pdf_manifest_pair


def test_pdf_claim_lint_fails_high_strength_language_without_context():
    findings = lint_pages(["This gives decisive evidence for a signal."])

    assert [finding.severity for finding in findings] == ["fail"]
    assert findings[0].pattern == "decisive evidence"


def test_pdf_claim_lint_allows_high_strength_language_in_conditioned_context():
    findings = lint_pages(
        [
            "This legacy transfer-conditional appendix records decisive evidence "
            "from a deprecated evidence table."
        ]
    )

    assert findings == []


def test_pdf_claim_lint_warns_on_lnb_numeric_without_high_strength_claim():
    findings = lint_pages(["The technical table reports ln B = +2.0 as an input value."])

    assert [finding.severity for finding in findings] == ["warn"]
    assert findings[0].pattern == "lnB numeric or threshold"


def test_pdf_claim_lint_warns_on_jeffreys_definition():
    findings = lint_pages(
        [
            "We adopt the Jeffreys scale for qualitative interpretation: "
            "|ln B| > 5 is decisive."
        ]
    )

    assert [finding.severity for finding in findings] == ["warn"]
    assert findings[0].pattern == "lnB numeric or threshold"


def test_pdf_claim_lint_fails_lnb_numeric_detection_claim():
    findings = lint_pages(
        ["The tilt detection (ln B > 5) survives all tested perturbations."]
    )

    assert [finding.severity for finding in findings] == ["fail"]
    assert findings[0].pattern == "lnB numeric with high-strength claim language"


@pytest.mark.parametrize(
    ("text", "pattern"),
    [
        (
            "The result has odds exceeding 10^11:1 in favour of tilted models.",
            "odds exceeding",
        ),
        (
            "The combined significance now exceeds 5 sigma across multiple probes.",
            "combined significance now exceeds",
        ),
        (
            "This tension is a property of the data, not a model failure.",
            "property of the data, not a model failure",
        ),
        (
            "The flat comparator is the most conservative choice for the signal.",
            "most conservative choice",
        ),
        (
            "The result is one-sixteenth of the MES-allowed anisotropy budget.",
            "one-sixteenth of the MES-allowed anisotropy budget",
        ),
    ],
)
def test_pdf_claim_lint_fails_strict_audit_forbidden_phrases(text, pattern):
    findings = lint_pages([text])

    assert [finding.severity for finding in findings] == ["fail"]
    assert findings[0].pattern == pattern


def test_pdf_claim_lint_forbidden_phrases_are_not_context_exempt():
    findings = lint_pages(
        ["This legacy transfer-conditional appendix records odds exceeding 10^11:1."]
    )

    assert [finding.severity for finding in findings] == ["fail"]
    assert findings[0].pattern == "odds exceeding"


def test_pdf_claim_lint_fails_lnb_global_tilt_source_identification():
    findings = lint_pages(["The global tilt evidence has ln B = +26."])

    assert [finding.severity for finding in findings] == ["fail"]
    assert findings[0].pattern == "lnB numeric with high-strength claim language"


def test_pdf_claim_lint_allows_premise_conditioned_admitted_amplitude_lnb():
    findings = lint_pages(
        [
            "The premise-conditioned admitted-amplitude fit reports ln B = +26; "
            "this is not a source-identification claim."
        ]
    )

    assert [finding.severity for finding in findings] == ["warn"]
    assert findings[0].pattern == "lnB numeric or threshold"


def test_pdf_claim_lint_allows_lnb_numeric_diagnostic_preference_language():
    findings = lint_pages(
        [
            "The direction-marginalized diagnostic preference (ln B > 5) "
            "is a conditional model-comparison summary."
        ]
    )

    assert [finding.severity for finding in findings] == ["warn"]
    assert findings[0].pattern == "lnB numeric or threshold"


def test_pdf_claim_lint_fails_lnb_detection_even_with_page_context_marker():
    findings = lint_pages(
        [
            "This legacy transfer-conditional appendix records deprecated labels. "
            + ("Neutral text. " * 80)
            + "The tilt detection (ln B > 5) survives all tested perturbations."
        ]
    )

    assert [finding.severity for finding in findings] == ["fail"]
    assert findings[0].pattern == "lnB numeric with high-strength claim language"


def test_pdf_claim_lint_fails_lnb_detection_even_with_safe_marker():
    findings = lint_pages(
        [
            "The direction-marginalized diagnostic preference is reported, but "
            "the tilt detection (ln B > 5) survives all tested perturbations; "
            "this is not a detection claim."
        ]
    )

    assert [finding.severity for finding in findings] == ["fail"]
    assert findings[0].pattern == "lnB numeric with high-strength claim language"


def test_pdf_claim_lint_allows_negative_family_id_statement():
    findings = lint_pages(["Bianchi family identification is not established."])

    assert findings == []


@pytest.mark.parametrize(
    ("text", "signature"),
    [
        (
            "The CF4 MV bulk-flow B200 amplitude is " + "40" + "5.22 km/s.",
            "cf4_mv_r200_headline",
        ),
        (
            "CF4 velocity-correlation f_sigma8="
            + "0.404"
            + "6 after shape correction "
            + "1.442"
            + "3.",
            "cf4_ml_corrected_headline",
        ),
        (
            "The CF4 GLS bulk-flow is "
            + "34"
            + "1 km/s and Omega_tilt is "
            + "4.07"
            + "e-7.",
            "cf4_gls_headline",
        ),
    ],
)
def test_pdf_claim_lint_rejects_cf4_p0_text(text: str, signature: str):
    findings = lint_pages([text])

    assert any(
        finding.severity == "fail" and signature in finding.pattern
        for finding in findings
    )


def test_pdf_claim_lint_rejects_mismatched_companion_manifest(tmp_path: Path):
    pdf = tmp_path / "report.pdf"
    manifest = tmp_path / "report.manifest.json"
    pdf.write_bytes(b"%PDF-1.4\nclaim surface\n")
    manifest.write_text(
        json.dumps({"artifact_sha256": "sha256:" + "0" * 64}),
        encoding="utf-8",
    )

    try:
        verify_pdf_manifest_pair(pdf, manifest)
    except ValueError as exc:
        assert "digest mismatch" in str(exc)
    else:
        raise AssertionError("mismatched PDF companion manifest must fail closed")


def test_missing_current_pdf_emits_blocked_not_passed_report(
    tmp_path: Path,
    monkeypatch,
):
    class Block:
        sha256 = "1" * 64
        findings = (
            {"finding_id": "C1-K5-MV-F1"},
            {"finding_id": "C3-K5-VCORR-ML-F1"},
            {"finding_id": "N-DATA-CF4-DOWNSTREAM"},
        )

    monkeypatch.setattr(pdf_claim_lint, "load_block_record", lambda _root: Block())
    payload = pdf_claim_lint.build_report_payload(
        repo_root=tmp_path,
        pdf_path=Path("docs/generated/manuscript_pdf/report.pdf"),
        manifest_path=Path("docs/generated/manuscript_pdf/report.manifest.json"),
        output_path=tmp_path / "docs/generated/pdf_claim_lint_report.md",
        generating_command="pytest",
    )
    report = pdf_claim_lint.render_report(payload)

    assert payload["status"] == "BLOCKED_NO_CURRENT_PDF"
    assert payload["claim_lint_passed"] is False
    assert payload["page_count"] == 0
    assert "No current PDF was linted" in report
    assert "claim_lint_passed: false" in report


def test_blocked_no_current_pdf_cli_is_nonzero_in_write_and_check_modes(
    tmp_path: Path,
    monkeypatch,
):
    payload = {
        "owner": "COMMON",
        "implementation_scope": "common",
        "claim_tier": "blocked",
        "transfer_source": "none",
        "sky_support_status": "not_applicable_no_current_pdf",
        "null_mock_status": "not_applicable_no_current_pdf",
        "artifact_path": "report.md",
        "status": "BLOCKED_NO_CURRENT_PDF",
        "claim_lint_passed": False,
        "pdf_path": "missing.pdf",
        "pdf_sha256": None,
        "pdf_manifest_path": None,
        "quarantine_block_path": "docs/generated/cf4_p0_quarantine_block.json",
        "quarantine_block_sha256": "sha256:" + "1" * 64,
        "config_hash": "sha256:" + "2" * 64,
        "input_hashes": [],
        "generating_command": "pytest",
        "git_commit_or_worktree_state": "test",
        "page_count": 0,
        "failed_findings": 0,
        "warning_findings": 0,
        "findings": [],
        "open_findings": ["C1-K5-MV-F1"],
        "caveats": ["blocked"],
    }
    output = tmp_path / "report.md"
    monkeypatch.setattr(
        pdf_claim_lint,
        "build_report_payload",
        lambda **_kwargs: dict(payload),
    )

    assert pdf_claim_lint.main(["--output", str(output)]) == 1
    assert output.is_file()
    assert pdf_claim_lint.main(["--output", str(output), "--check"]) == 1
