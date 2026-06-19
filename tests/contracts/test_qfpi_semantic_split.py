import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


PUBLIC_SURFACES = [
    ROOT / "scripts/make_manuscript_figures.py",
    ROOT / "docs/manuscript/appendices.tex",
    ROOT / "htt/workspace/contracts/htt_to_mio.py",
    ROOT / "htt/htt/htt/core/departure_posteriors.py",
]


def test_public_qfpi_surfaces_do_not_call_q_occupancy():
    combined = "\n".join(path.read_text(encoding="utf-8") for path in PUBLIC_SURFACES)

    blocked = [
        r"occupancy\s+ratio",
        r"occupancy\s+\$Q",
        r"departure\s+occupancy",
        r"Q_median,\s+Q_hpd68\s+[-\u2014]+.*occupancy\s+posterior",
        r"Layer-?2\s+occupancy",
    ]
    for pattern in blocked:
        assert not re.search(pattern, combined, flags=re.IGNORECASE), pattern

    assert "policy-normalized diagnostic score" in combined
    assert "policy-normalized HTT posterior score" in combined


def test_public_qfpi_surfaces_namespace_htt_and_mio_pi():
    appendices = (ROOT / "docs/manuscript/appendices.tex").read_text(encoding="utf-8")
    figures = (ROOT / "scripts/make_manuscript_figures.py").read_text(encoding="utf-8")
    departure_posteriors = (
        ROOT / "htt/htt/htt/core/departure_posteriors.py"
    ).read_text(encoding="utf-8")
    htt_to_mio = (ROOT / "htt/workspace/contracts/htt_to_mio.py").read_text(
        encoding="utf-8"
    )

    assert r"\Pi_{\rm MIO}" in appendices
    assert r"\Pi_{\rm HTT}" in appendices
    assert r"\Pi_{\rm HTT}" in figures
    assert "HTT posterior exceedance cross-check" in htt_to_mio
    assert "legacy HTT posterior diagnostic export" in departure_posteriors
    assert "not MIO Pi" in departure_posteriors
