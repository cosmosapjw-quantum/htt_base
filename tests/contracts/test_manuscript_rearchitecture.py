from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
REPORT = ROOT / "docs/generated/manuscript_rearchitecture_report.md"


def _read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def _norm(text: str) -> str:
    return " ".join(text.split())


def test_rearchitecture_report_records_safe_narrative_order():
    text = REPORT.read_text(encoding="utf-8")

    required = [
        "owner: COMMON",
        "claim_tier: diagnostic_only",
        "formal no-go and identifiability",
        "transfer-conditional rest-frame tilt-like diagnostic",
        "rank/null/prior theorem-backed local/global rest-frame program",
        "current diagnostic figures",
        "theorem appendix",
        "future native solver bridge",
        "no native solver output",
        "no Bianchi family identification",
    ]
    for token in required:
        assert token in text

    order = [
        text.index("formal no-go and identifiability"),
        text.index("transfer-conditional rest-frame tilt-like diagnostic"),
        text.index("rank/null/prior theorem-backed local/global rest-frame program"),
        text.index("current diagnostic figures"),
        text.index("theorem appendix"),
        text.index("future native solver bridge"),
    ]
    assert order == sorted(order)


def test_manuscript_intro_and_discussion_lead_with_gated_results():
    intro = _norm(_read("docs/manuscript/ch01_introduction.tex"))
    discussion = _norm(_read("docs/manuscript/ch09_discussion.tex"))

    for token in [
        "method-level identifiability theorem",
        "finite-mock calibration rule",
        "channel-matched occupancy requirement",
        "data-binding gap report",
        "rest-frame analysis plan and rank gate",
    ]:
        assert token in intro
        assert token in discussion

    headline_region = intro.split("\\section{Outline of the thesis}")[0]
    assert "\\ln\\mathcal{B}" not in headline_region


def test_results_and_robustness_demote_legacy_bayes_factors():
    results = _norm(_read("docs/manuscript/ch07_results.tex"))
    robustness = _norm(_read("docs/manuscript/ch08_robustness.tex"))

    for text in (results, robustness):
        assert "legacy Bayes factors are sensitivity/provenance records" in text
        assert "not headline discoveries" in text
        assert "observer-frame marginalization remains pending" in text.lower()


def test_theorem_appendix_is_included_with_claim_firewall():
    appendices = _norm(_read("docs/manuscript/appendices.tex"))

    assert "\\input{generated/theorem_extension_appendix_figures}" in appendices
    assert "x/F/G/Pi theorem-extension diagnostics" in appendices
    assert "not HTT evidence" in appendices
    assert "not native-transfer outputs" in appendices
    assert "not geometry or family-identification support" in appendices


def test_references_include_crag_verified_revision_sources():
    refs = _read("docs/manuscript/references.bib")

    for key in [
        "@article{vonHauseggerDalang2025",
        "@misc{DESIDR1Release2025",
        "@article{DESIDR1QSODipole2026",
        "@article{HoffmanValadeCF42023",
        "@article{Nilsson1999AlmostIsotropic",
        "@book{WainwrightEllis1997",
    ]:
        assert key in refs

    assert "10.1103/PhysRevD.111.123547" in refs
    assert "https://data.desi.lbl.gov/doc/releases/dr1/" in refs
    assert "2606.00551" in refs
    assert "Chen, Shuangnan and Yang, Xiaofeng" in refs
    assert "Testing the cosmological principle with quasars" in refs
    assert "10.1051/0004-6361/202556955" in refs
    assert "10.1093/mnras/stad3433" in refs


def test_legacy_detection_language_is_reframed_as_conditional_diagnostic():
    discussion = _norm(_read("docs/manuscript/ch09_discussion.tex"))
    future = _norm(_read("docs/manuscript/ch10_future.tex"))

    for text in (discussion, future):
        assert "detected tilt" not in text
        assert "tilt-rapidity detection" not in text

    assert "transfer-conditional diagnostic tilt amplitude" in discussion
    assert "tilt-rapidity diagnostic persists across redshift shells" in future
