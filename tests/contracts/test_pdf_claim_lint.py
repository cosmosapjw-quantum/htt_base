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


def test_pdf_claim_lint_warns_on_lnb_numeric_without_failing():
    findings = lint_pages(["The technical table reports ln B = +2.0 as an input value."])

    assert [finding.severity for finding in findings] == ["warn"]
    assert findings[0].pattern == "lnB numeric or threshold"


def test_pdf_claim_lint_allows_negative_family_id_statement():
    findings = lint_pages(["Bianchi family identification is not established."])

    assert findings == []
