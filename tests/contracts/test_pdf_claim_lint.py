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
