"""Tests for R111 C1-C6 native high-l validation outputs and invariants."""
from __future__ import annotations

import json
import math
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
R111 = ROOT / "docs/research_program/observational_publication_20261015/R111_LOCAL_HIGHL_NATIVE_20261124"
GAP_REG = ROOT / "docs/research_program/observational_publication_20261015/R107_CLOUD_SOLVER_DATA_THEORY_20261124/GAP_REGISTER.json"


def _load(name: str) -> dict:
    p = R111 / name
    if not p.exists():
        pytest.skip(f"{name} not yet generated")
    return json.loads(p.read_text(encoding="utf-8"))


def test_c1_visibility_coverage_invariants() -> None:
    d = _load("C1_VISIBILITY_COVERAGE.json")
    assert d["schema"] == "htt.r111.c1_visibility_coverage/1"
    assert d["rec_source"]["commit"] == "4cffa8a0abdb104a40cac17cfc65593bec909fb3"
    assert d["acceptance"]["flrw_depth_1e6_passed"] is True
    assert d["acceptance"]["flrw_depth_to_z0_abs_err_32768"] <= 1e-6
    assert d["acceptance"]["long_run_sdirk2_stable_positive_screen"] is True
    assert d["bass_1600_to_1100_check"]["abs_err_vs_piecewise_eta"] <= 1e-6


def test_c2_rei_join_five_cases_single_owner() -> None:
    d = _load("C2_REI_JOIN.json")
    assert d["schema"] == "htt.r111.c2_rei_join/1"
    expected = {"ZERO", "SHEAR_PLUS", "SHEAR_MINUS", "SHEAR_HALF_PLUS", "SHEAR_HALF_MINUS"}
    assert set(d["cases"]) == expected
    assert d["acceptance"]["all_five_cases_single_owner_per_interval"] is True
    assert d["acceptance"]["all_five_cases_strictly_increasing_eta"] is True
    assert d["acceptance"]["all_five_cases_jump_at_z20_reported"] is True
    assert 0.0005 < d["nh0_anchors"]["relative_shift_mp_vs_mH"] < 0.0006
    for case in d["cases"].values():
        assert case["rei_report"]["z_below_low_is_conditional_placeholder"] is True
        assert math.isfinite(case["rei_report"]["jump_at_z_high"])


def test_c3_long_highl_atlas_convergence_and_types() -> None:
    d = _load("C3_LONG_HIGHL_ATLAS.json")
    assert d["schema"] == "htt.r111.c3_long_highl_atlas/1"
    assert d["total_runs"] == 61
    assert d["los_lmax"] == 128
    assert len(d["families"]) == 12
    assert d["acceptance"]["all_12_families_finest_pairs_le_1e3"] is True
    assert d["acceptance"]["all_61_runs_types_unchanged"] is True
    assert d["acceptance"]["all_61_runs_h_preserved"] is True


def test_c4_bjs_highl_correlation_without_tuning() -> None:
    d = _load("C4_BJS_HIGHL.json")
    assert d["schema"] == "htt.r111.c4_bjs_highl/1"
    assert len(d["summary_table"]) == 6
    assert d["acceptance"]["all_cases_ge_0p999_mcewen2006"] is True
    assert d["acceptance"]["min_corr_protocol_mcewen2006"] >= 0.999
    assert d["acceptance"]["min_corr_doppler_mcewen2006"] >= 0.999


def test_c5_commander_leakage_and_c6_performance() -> None:
    c5 = _load("C5_COMMANDER_LEAKAGE.json")
    assert c5["schema"] == "htt.r111.c5_commander_leakage/1"
    assert c5["kernel"]["covers_c3_lmax_128"] is True
    assert c5["r109_exact_archive_repro"]["output_sha256_equal"] is True
    assert c5["r109_exact_archive_repro"]["max_diff_vs_r109_json"] < 1e-12
    assert len(c5["c3_z1600_l128_vs_l4"]["per_family_leakage"]) == 12

    c6 = _load("C6_LOS256_PERFORMANCE.json")
    assert c6["schema"] == "htt.r111.c6_los256_performance/1"
    long_run = c6["long_epoch_z1600_4000step_24t"]
    assert long_run["los_lmax"] == 256
    assert long_run["n_rays"] == 257 * 514
    assert long_run["max_rss_kbytes"] > 0
    assert long_run["los_max_landing_error"] < 1e-11


def test_r111_hold_specs_and_no_dag_promotion() -> None:
    specs = R111 / "T1_T2_T3_SPECIFICATIONS.md"
    assert specs.exists()
    txt = specs.read_text(encoding="utf-8")
    assert "T1." in txt and "T2." in txt and "T3." in txt
    assert "HOLD" in txt

    reg = json.loads(GAP_REG.read_text(encoding="utf-8"))
    # No scientific promotions beyond existing R78 completed_scoped baseline
    assert reg["n_nodes"] == 60
    assert all(r["canonical_state"] != "completed_scoped" for r in reg["rows"])
