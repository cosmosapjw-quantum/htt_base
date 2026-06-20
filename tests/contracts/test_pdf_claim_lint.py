import pytest

from scripts.pdf_claim_lint import lint_pages


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
