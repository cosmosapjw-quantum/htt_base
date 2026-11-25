"""Tests for R114 local universal Lie sky verification outputs, invariants, and fail-closed gates."""
from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
R114 = ROOT / "docs/research_program/observational_publication_20261015/R114_LOCAL_UNIVERSAL_LIE_SKY_20261125"
GAP_REG = ROOT / "docs/research_program/observational_publication_20261015/R107_CLOUD_SOLVER_DATA_THEORY_20261124/GAP_REGISTER.json"
INTEGRATED_DAG = ROOT / "docs/research_program/observational_publication_20261015/R78_UNIFIED_SCIENCE_DAG_20261119/INTEGRATED_DAG.json"
EXPECTED_ORIGINAL_42_SHA256 = "e3264e105cabf78ddac37addc36cacc3cfa05ee942e33e54b431b22e3e87de0d"
EXPECTED_BASS_BINARY_SHA256 = "3b775cf326921797d9488f00c8e78261aa58e2b436b2128ee0ec8cefd6c38686"


def _load(name: str) -> dict:
    p = R114 / name
    assert p.exists(), f"missing R114 artifact: {p}"
    return json.loads(p.read_text(encoding="utf-8"))


def test_f0_f3_and_execution_ledger_invariants() -> None:
    f0 = _load("F0_CLOUD_DIFF_REVIEW.json")
    assert f0["schema"] == "htt.r114.f0_cloud_diff_review/1"
    assert f0["counts_by_severity"] == {"CRITICAL": 0, "HIGH": 1, "MEDIUM": 5, "LOW": 4}
    assert len(f0["findings"]) == 10

    f13 = _load("F1_F3_REPRODUCTION.json")
    assert f13["schema"] == "htt.r114.f1_f3_reproduction/1"
    assert f13["f1"]["r114_final_binary_sha256"] == EXPECTED_BASS_BINARY_SHA256
    assert f13["f1"]["r114_final_bass_cargo_test_passed"] == 221
    assert f13["f1"]["r114_final_bass_examples_passed"] == 3
    assert f13["f1"]["r114_final_v1_matched_tsvs"] == 20
    assert f13["f1"]["r114_final_v1_total_tsvs"] == 20
    assert f13["f2"]["rec_r114_cargo_test_passed"] == 129
    assert f13["f2"]["rei_cargo_test_passed"] == 271
    assert f13["f3_cloud_reproduction_pre_fix"]["RECOMBINATION_DEMO.json"]["exact_equal"] is True
    assert f13["f3_cloud_reproduction_pre_fix"]["CROSS_ROUTE_ATLAS.json"]["exact_equal"] is True
    assert f13["f3_post_f010_recheck"]["max_peak_rel_vs_r113"] < 1e-9

    ledger = _load("EXECUTED_COMMANDS.json")
    assert ledger["schema"] == "htt.r114.executed_commands/1"
    assert ledger["repositories"]["bass"]["binary_sha256"] == EXPECTED_BASS_BINARY_SHA256
    assert len(ledger["commands"]) >= 10


def test_c1_harmonic_long_atlas_invariants_and_honest_ix_floor() -> None:
    d = _load("C1_HARMONIC_LONG_ATLAS.json")
    assert d["schema"] == "htt.r114.c1_harmonic_long_atlas/1"
    assert d["binary_sha256"] == EXPECTED_BASS_BINARY_SHA256
    assert len(d["cases"]) == 13
    assert d["total_standard_runs"] == 91
    acc = d["acceptance"]
    # Strict 1e-6 C_l tolerance is NOT widened: IX l=4 hits 1.88e-6 due to sub-ULP floor.
    assert acc["strict_cl_l_pairs_le_1e6_all_12"] is False
    assert acc["strict_cl_l_pairs_le_1e6_passed_count"] == 11
    failed = acc["strict_cl_l_pairs_le_1e6_failed_cases"]
    assert len(failed) == 4
    for row in failed:
        assert row["case"] == "IX"
        assert row["channel"] in {"EE", "BB"}
        assert row["worst_ell"] == 4
        assert row["max_rel_change_cl"] <= 1.9e-6
        assert row["worst_delta_cl_over_sky_max_cl"] <= 2e-16
    assert acc["all_12_anisotropic_cl_l_pairs_le_1e6_above_f64_sub_ulp_floor"] is True
    assert acc["all_12_anisotropic_global_mode_l_pairs_le_1e6"] is True
    assert acc["all_11_non_ix_anisotropic_direct_and_los_route_gap_order2"] is True
    assert acc["all_12_anisotropic_h16_s500_s1000_s2000_order2"] is True
    assert acc["flrw_abs_route_gap_le_1e13"] is True
    assert acc["flrw_isotropic_zero_le_1e13"] is True
    assert acc["flrw_isotropic_max_abs_alm_l_ge_1"] <= 1e-13
    assert acc["all_13_cases_types_unchanged"] is True
    assert acc["all_13_cases_h_preserved"] is True
    assert acc["all_screens_positive"] is True


def test_c2_tight_coupling_matched_invariants() -> None:
    d = _load("C2_TIGHT_COUPLING_MATCHED.json")
    assert d["schema"] == "htt.r114.c2_tight_coupling_matched/1"
    assert d["binary_sha256"] == EXPECTED_BASS_BINARY_SHA256
    assert len(d["anisotropic_histories"]) == 16
    assert d["acceptance"]["flrw_delta_xe_second_order_ratios_in_3p5_to_4p5"] is True
    assert d["acceptance"]["z1800_xe_gt_1_strictly_zero_hydrogen_response"] is True
    assert d["acceptance"]["all_runs_min_screen_positive"] is True
    for run_key in (
        "I_tilt_z1800_rays_matched",
        "I_tilt_z1800_harmonic_matched",
        "VIIh_small_z1800_rays_matched",
        "VIIh_small_z1800_harmonic_matched",
    ):
        assert d["anisotropic_histories"][run_key]["recombination"]["max_abs_delta_xe_where_xe_ge_1"] == 0.0


def test_c3_rei_matched_join_invariants() -> None:
    d = _load("C3_REI_MATCHED_JOIN.json")
    assert d["schema"] == "htt.r114.c3_rei_matched_join/1"
    expected = {"ZERO", "SHEAR_PLUS", "SHEAR_MINUS", "SHEAR_HALF_PLUS", "SHEAR_HALF_MINUS"}
    assert set(d["cases"]) == expected
    assert d["acceptance"]["all_5_cases_offset_held_exact_after_stop"] is True
    assert d["acceptance"]["all_5_cases_last_active_eta_le_stop_eta"] is True
    for name, case in d["cases"].items():
        assert case["rei_report"]["z_below_low_is_conditional_placeholder"] is True
        assert 0.05 < case["tau_quadrature"]["hyrec_mH"]["tau_reio_z_le_20"] < 0.06, name
        assert case["matched_stop_harmonic16"]["recombination"]["max_post_stop_drift"] == 0.0


def test_c4_bjs_harmonic_highl_and_c5_commander_c6_perf() -> None:
    c4 = _load("C4_BJS_HARMONIC_HIGHL.json")
    assert c4["schema"] == "htt.r114.c4_bjs_harmonic_highl/1"
    assert len(c4["cases_l32"]) == 6
    assert "check_o0p3_x0p62_l48" in c4
    assert c4["acceptance"]["all_cases_ge_0p999"] is True
    assert c4["acceptance"]["all_types_preserved"] is True
    assert c4["acceptance"]["min_protocol_corr_mcewen2006"] >= 0.999
    assert c4["acceptance"]["min_doppler_corr_mcewen2006"] >= 0.999

    c5 = _load("C5_COMMANDER_LEAKAGE.json")
    assert c5["schema"] == "htt.r114.c5_commander_leakage/1"
    assert c5["kernel"]["lmax"] == 256
    assert c5["kernel"]["covers_c1_lmax_128"] is True
    assert c5["flrw_control_max_abs_alm_l_ge_1"] <= 1e-13
    assert c5["truncated_vs_padded_max_relative_los"] <= 1e-13
    assert len(c5["per_family_leakage"]) == 12

    c6 = _load("C6_PERFORMANCE_BENCHMARKS.json")
    assert c6["schema"] == "htt.r114.c6_performance_benchmarks/1"
    long_run = c6["los256_harmonic32_long_z1600_2000step_24t"]
    assert long_run["los_lmax"] == 256
    assert long_run["n_rays"] == 257 * 514
    assert long_run["max_rss_kbytes"] > 0
    assert long_run["los_max_landing_error"] < 1e-11
    assert c6["los256_thread_speedup_1_to_24"] > 5.0


def test_hold_specs_t5_fail_closed_and_no_dag_promotion() -> None:
    from bass.hierarchy.seed_factory import STRONG_FAMILIES
    from bass.inference.envelope import EnvelopeError, enforce_inference_envelope
    from bass.transport.general_bianchi_transfer import (
        OutOfScopeError,
        TRANSFER_MODE_LINEARIZED,
        TiltedTransferParameters,
        compute_general_bianchi_transfer,
    )

    specs = (R114 / "T1_T5_HOLD_SPECIFICATIONS.md").read_text(encoding="utf-8")
    for heading in ("T1.", "T2.", "T3.", "T4.", "T5.", "HOLD"):
        assert heading in specs

    ko = (R114 / "RESULTS_KO.md").read_text(encoding="utf-8")
    for section in ("(1) 사실", "(2) 해석", "(3) 미해결·보류"):
        assert section in ko

    # T5 fail-closed boundary in htt_base remains active (envelope + linearized PSTF transport).
    assert STRONG_FAMILIES == frozenset({"FLRW", "I", "V", "VII_0", "VII_h", "IX"})
    with pytest.raises(EnvelopeError):
        enforce_inference_envelope(
            {
                "dataset": {"kind": "synthetic_surrogate", "allow_surrogate": True},
                "envelope": {"target_families": ["II"]},
            }
        )
    for fam in ("II", "III", "IV", "VI_0", "VI_h", "VIII"):
        with pytest.raises(OutOfScopeError):
            compute_general_bianchi_transfer(
                TiltedTransferParameters(family=fam, transfer_mode=TRANSFER_MODE_LINEARIZED)
            )

    reg = json.loads(GAP_REG.read_text(encoding="utf-8"))
    assert reg["n_nodes"] == 60
    assert reg["n_open"] == 42
    assert all(r["canonical_state"] != "completed_scoped" for r in reg["rows"])

    dag = json.loads(INTEGRATED_DAG.read_text(encoding="utf-8"))
    assert len(dag["nodes"]) == 60
    orig42_sha = hashlib.sha256(
        json.dumps(dag["nodes"][:42], sort_keys=True).encode("utf-8")
    ).hexdigest()
    assert orig42_sha == EXPECTED_ORIGINAL_42_SHA256
