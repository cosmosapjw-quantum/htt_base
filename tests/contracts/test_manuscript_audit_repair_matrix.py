import re
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
MATRIX = ROOT / "docs/generated/manuscript_audit_repair_matrix.md"
MANUSCRIPT_FILES = [
    "docs/manuscript/ch01_introduction.tex",
    "docs/manuscript/ch02_dipole_anomaly.tex",
    "docs/manuscript/ch03_framework.tex",
    "docs/manuscript/ch05_teff_corrections.tex",
    "docs/manuscript/ch07_results.tex",
    "docs/manuscript/ch08_robustness.tex",
    "docs/manuscript/ch09_discussion.tex",
]


def test_manuscript_audit_repair_matrix_exists_and_closes_findings():
    text = MATRIX.read_text(encoding="utf-8")

    for token in [
        "owner: COMMON",
        "claim_tier: diagnostic_only",
        "neutrino quadrupole wording",
        "CF4++ lnB provenance",
        "Q/F/Pi harmonization",
        "headline departure number provenance",
        "NO_FLRW_LIMIT rows",
        "sensitivity window wording",
        "observer-frame marginalization pending",
        "not native transfer",
        "no morphology-family naming or selection claim",
        "no geometry-detection claim",
    ]:
        assert token in text
    assert text.count("| closed |") >= 7


def test_manuscript_removes_audited_high_risk_phrases():
    combined = "\n".join(
        (ROOT / path).read_text(encoding="utf-8") for path in MANUSCRIPT_FILES
    )
    blocked = [
        r"the discovery that neutrinos",
        r"discovered by the\s+solver",
        r"solver\s+result\s+of\s+\$?28",
        r"98\\% accuracy",
        r"detection window",
        r"detectable against the cosmic-variance floor",
    ]

    for pattern in blocked:
        assert not re.search(pattern, combined, flags=re.IGNORECASE | re.DOTALL), pattern


def test_sensitivity_lnb_mentions_are_quarantined():
    for path in [
        "docs/manuscript/ch07_results.tex",
        "docs/manuscript/ch08_robustness.tex",
        "docs/manuscript/ch09_discussion.tex",
    ]:
        text = (ROOT / path).read_text(encoding="utf-8")
        for match in re.finditer(r"\+(?:44(?:\.0)?|105\.8|106)", text):
            line_start = text.rfind("\n", 0, match.start()) + 1
            line_end = text.find("\n", match.end())
            if line_end == -1:
                line_end = len(text)
            line = text[line_start:line_end].lower()
            window = text[max(0, match.start() - 360) : match.end() + 360].lower()
            context = line + "\n" + window
            assert any(
                token in window
                for token in [
                    "pending",
                    "untraceable",
                    "quarantined",
                    "not in canonical",
                    "independently verified before publication",
                ]
            ), f"{path}: sensitivity lnB mention is not quarantined"
            assert "quarantined" in context or "not interpreted as threshold-crossing" in context


def test_no_flrw_limit_rows_are_not_printed_as_bayes_factors():
    ch07 = (ROOT / "docs/manuscript/ch07_results.tex").read_text(encoding="utf-8")

    for row in ["II", "III", "IV", "VI$_0$", "VI$_h$", "VIII"]:
        pattern = rf"{re.escape(row)}\s*&\s*\\multicolumn\{{1\}}\{{c\}}\{{N/A \(no FLRW limit\)\}}"
        assert re.search(pattern, ch07), row


def test_q_f_pi_text_separates_htt_and_mio_semantics():
    combined = "\n".join(
        (ROOT / path).read_text(encoding="utf-8")
        for path in [
            "docs/manuscript/ch03_framework.tex",
            "docs/manuscript/ch07_results.tex",
        ]
    )

    assert "HTT posterior exceedance" in combined
    assert "MIO diagnostic exceedance" in combined
    assert "MIO diagnostic" in combined
    assert "no posterior, occupancy, or evidence semantics" in combined


def test_pdf_claim_lint_still_passes_after_repair():
    result = subprocess.run(
        ["venv/bin/python", "scripts/pdf_claim_lint.py", "--check"],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 0, result.stdout + result.stderr
