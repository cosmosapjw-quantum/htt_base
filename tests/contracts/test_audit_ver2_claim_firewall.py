from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
TASK2_FILES = [
    "docs/manuscript/ch01_introduction.tex",
    "docs/manuscript/ch02_dipole_anomaly.tex",
    "docs/manuscript/ch07_results.tex",
    "docs/manuscript/ch08_robustness.tex",
    "docs/manuscript/ch09_discussion.tex",
    "docs/manuscript/ch10_future.tex",
]


def _manuscript_text() -> str:
    return "\n".join(
        (ROOT / path).read_text(encoding="utf-8") for path in TASK2_FILES
    )


def _normalised_lower() -> str:
    return " ".join(_manuscript_text().lower().split())


def test_strict_audit_reclassified_positive_evidence_language():
    lowered = _normalised_lower()
    forbidden_fragments = [
        "odds exceeding",
        "one-sixteenth of the mes-allowed anisotropy budget",
        "property of the data, not a model failure",
        "comparator is the most conservative",
        "conditional evidence for global tilt",
    ]
    for fragment in forbidden_fragments:
        assert fragment not in lowered

    assert "premise-conditioned amplitude fit" in lowered
    assert "single-$\\beta$ likelihood or covariance model fails" in lowered
    assert "fiducial comparator" in lowered


def test_pi_and_f_are_namespace_disambiguated():
    text = _manuscript_text()
    lowered = _normalised_lower()

    assert "\\Pi_{\\rm HTT}" in text
    assert "\\Pi_{\\rm MIO}" in text
    assert "legacy budget-normalised score" in lowered
    assert "class-conditioned filling" in lowered


def test_neutrino_result_is_derived_not_discovered():
    lowered = _normalised_lower()

    assert "solver discovers" not in lowered
    assert "discovery that neutrinos" not in lowered
    assert "derived result" in lowered
    assert "transfer-conditional" in lowered


def test_scalar_occupancy_language_is_proxy_gated():
    lowered = _normalised_lower()
    assert "channel-mismatched proxy score" in lowered
    assert "channel-matched occupancy" in lowered
