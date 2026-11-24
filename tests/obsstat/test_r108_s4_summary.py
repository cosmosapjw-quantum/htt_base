"""R108 lane s4: invariants of SOLVER/S4_BJS_COMPARATOR.json after the review fixes (S4-1..S4-5, S4-7).

The summary must be written by the current aggregator (writer sha256), carry a real global-optimality check of
every fit, report the variant comparison without a threshold or verdict, give the measured Doppler-component
fraction, tie every map and quoted paper to a sha256, and say what the repo_solve field refers to.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[2]
SUMMARY = REPO / ("docs/research_program/observational_publication_20261015/R108_LOS_ATLAS_DATA_20261124/SOLVER/"
                  "S4_BJS_COMPARATOR.json")


@pytest.fixture(scope="module")
def s():
    if not SUMMARY.exists():
        pytest.skip("S4 summary not present")
    return json.loads(SUMMARY.read_text())


def _sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def test_written_by_the_current_aggregator(s):
    w = s["writer"]
    assert w["script"] == "scripts/r108/s4_aggregate.py"
    assert w["sha256"] == _sha(REPO / w["script"])
    assert any("s4_aggregate" in a for a in w["argv"])
    assert s["claim_class"] == "NUMERICAL"


def test_global_check_is_real_and_passes_for_every_fit(s):
    g = s["global_optimality"]
    assert g["n_fits"] == 96 and g["n_fits_checked"] == 96
    assert g["all_pass"] and g["max_corr_check_minus_corr_best"] <= g["tol"] == 1e-9
    assert g["max_reproduction_corr_abs_diff"] < 1e-12 and g["all_run_file_sha256_checked"]
    assert "global_check_refined_ge_grid" not in json.dumps(s["cases"])
    for c in s["cases"]:
        for f in c["fits"].values():
            g1 = f["global_check"]
            assert g1["n_checks"] == min(8, g1["n_check_grid_local_maxima"]) + 8  # finer-grid maxima + random restarts
            assert g1["n_checks_in_fit_basin"] >= 1
            assert f["n_starts_used"] == f["n_grid_local_maxima"] or f["n_starts_used"] == 8


def test_variant_comparison_has_no_threshold_or_verdict(s):
    v = s["variant_comparison"]
    assert v["label"] == "SECONDARY_POST_ACCEPTANCE_DIAGNOSTIC"
    assert v["pre_stated_threshold"] is None and v["verdict"] is None
    assert set(v["ranges"]) == {"protocol", "doppler_diagnostic", "protocol_richardson", "doppler_richardson"}
    for label in v["ranges"]:
        assert set(v["ranges"][label]) == {"kogut1997", "mcewen2006"}
    assert len(v["per_case"]) == 6
    for c in v["per_case"]:
        assert 0.0 < c["doppler_component_fraction"] < 1.0
        assert len(c["by_map"]) == 4


def test_doppler_fraction_matches_the_saved_maps(s):
    np = pytest.importorskip("numpy")
    for c in s["cases"]:
        p = Path(c["map_provenance"]["path"])
        if not p.exists():
            pytest.skip("map files not present")
        assert _sha(p) == c["map_provenance"]["sha256"]
        z = np.load(p)
        frac = float(np.std(z["dTT_doppler"] - z["dTT"]) / np.std(z["dTT"]))
        assert frac == c["doppler_component_fraction"]["rel_rms_doppler_minus_protocol_over_protocol"]
        cc = c["map_provenance"]["content_check_vs_run_json"]
        assert max(abs(x) for x in cc.values()) < 1e-15


def test_euler_combination_reported_near_gimbal_lock(s):
    for c in s["cases"]:
        for f in c["fits"].values():
            e = f["euler_determined"]
            if e["alpha_gamma_individually_ill_conditioned"]:
                assert e["combination"] in ("alpha - gamma", "alpha + gamma") and e["value_rad"] is not None


def test_repo_solve_note_and_literature_receipts(s):
    n = s["repo_solve_compensating_tilt_velocity_note"]
    assert n["run_time_sha_equals_git_head_blob"] and n["git_head_blob_has_difference_form"]
    assert n["current_tree_has_stable_form"]
    assert n["max_abs_recomputed_minus_recorded"] == 0.0
    assert n["max_current_tree_rel_error"] < 1e-15
    lit = s["literature_locators"]
    assert len(lit["pdf_receipts"]) == 2
    for name, r in lit["pdf_receipts"].items():
        assert len(r["sha256"]) == 64 and r["url"].startswith("https://arxiv.org/pdf/")
        assert all(lit["quoted_phrase_check"][name]["phrases_found"].values())
