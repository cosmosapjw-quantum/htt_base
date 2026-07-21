"""Gates for the v10 even-L BiPoSH rank card and figure manifest."""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parents[2]
CARD = REPO / "docs/generated/k1_evenl_biposh_rank_card.json"
FIG_MANIFEST = REPO / "docs/generated/v10_report_figure_manifest.json"


def _card() -> dict:
    return json.loads(CARD.read_text())


def test_terminal_vocabulary_and_alpha_guard() -> None:
    card = _card()
    allowed = {
        "EVENL_CONSISTENT_WITH_E2E_NULL_WITHIN_THIS_PIPELINE",
        "EVENL_FEATURE_OUTSIDE_NULL_AT_ALPHA_WITHIN_THIS_PIPELINE",
        "NUMERICALLY_UNRESOLVED_AT_CURRENT_MC_BUDGET",
        "BLOCKED_INTEGRITY_FAILURE",
    }
    assert card["terminal"] in allowed
    res = card["result"]
    p = res["pooled"]["rank_p"]
    if abs(p - res["alpha"]) <= res["finite_resolution_floor"]:
        assert card["terminal"] == "NUMERICALLY_UNRESOLVED_AT_CURRENT_MC_BUDGET"


def test_exact_rank_arithmetic() -> None:
    res = _card()["result"]
    n = res["n_sims"]
    pooled = res["pooled"]
    assert pooled["rank_p"] == (1 + pooled["rank_exceedances"]) / (n + 1)
    assert pooled["rank_p"] >= res["finite_resolution_floor"]
    for block in res["per_L_secondary"].values():
        assert block["rank_p"] == (1 + block["rank_exceedances"]) / (n + 1)


def test_odd_l_structural_zero_certified() -> None:
    res = _card()["result"]
    assert res["odd_l_structural_zero_max_ratio"] < 1e-10


def test_boost_band_cross_checks_sealed_pr180_observed_vector() -> None:
    band = _card()["result"]["boost_feature_band"]
    pr180 = json.loads(
        (REPO / "docs/generated/pr180_result_card.json").read_text()
    )["result"]
    ours = np.asarray(band["observed"])
    sealed = np.asarray(pr180["observed_feature"])
    assert np.allclose(ours, sealed, rtol=1e-10, atol=1e-12)
    assert np.all(np.asarray(band["sim_p16"]) <= np.asarray(band["sim_p84"]))


def test_no_forbidden_claim_language() -> None:
    joined = json.dumps(_card()).lower()
    for token in ("detection of", "anisotropy detected",
                  "family identification"):
        assert token not in joined


def test_figure_manifest_artifacts_on_disk() -> None:
    manifest = json.loads(FIG_MANIFEST.read_text())
    figdir = REPO / manifest["figure_dir"]
    import hashlib

    for name, digest in manifest["artifact_sha256"].items():
        p = figdir / name
        assert p.exists(), name
        assert hashlib.sha256(p.read_bytes()).hexdigest() == digest, name
