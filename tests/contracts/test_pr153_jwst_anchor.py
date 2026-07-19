"""PR-153 contract tests: JWST authenticated-row, cross-match and manifest.

The probabilistic match, authoritative decision, row manifest, replay/negative
tests, guards and captions run everywhere on small synthetic inputs; the test
that reads the built artifacts skips when the real CF4 groups are absent.
"""
from __future__ import annotations

import json
import copy
import subprocess
import sys
import warnings
from pathlib import Path

import numpy as np
import pytest

warnings.filterwarnings("ignore")

from obsstat.jwst_anchor_manifest import (
    JWSTAnchorError,
    authoritative_reproduction_decision,
    build_row_manifest,
    crossmatch_all,
    generate_caption,
    label_substitution_negative_test,
    leave_one_match_report,
    lint_caption,
    probabilistic_identity_match,
    refuse_authoritative_without_table,
    refuse_bianchi_from_jwst,
    refuse_cf4_forecast_downstream_open,
    refuse_jwst_measurement,
    refuse_radius_only_identity,
    refuse_synthetic_renamed_observed,
    row_replay,
)
from scripts.codex_harness.run_pr153_jwst_anchor import (
    _load_comparison_table,
    _verify_fetch_manifest,
    validate_artifact_metadata,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
GEN = REPO_ROOT / "docs/generated"
CF4 = REPO_ROOT / "workdir/obs_bundle/pecvel/cf4_full/cf4_groups.npz"
SEED = REPO_ROOT / "dl_pipeline/data/jwst_distances_seed.csv"
needs_data = pytest.mark.skipif(
    not (CF4.is_file() and SEED.is_file()), reason="CF4 groups / seed absent")


def _synthetic_cf4(n=200, seed=0):
    rng = np.random.default_rng(seed)
    ra = rng.uniform(0, 360, n)
    dec = rng.uniform(-80, 80, n)
    pgc = np.arange(n, dtype=float)
    return ra, dec, pgc


def _valid_source_manifest() -> dict:
    digest = "sha256:" + "a" * 64
    sources = {
        "cchp_freedman2025_source_table": ("2408.06153", "Ho2024.tex"),
        "shoes_riess2025_source_table": ("2509.01667", "main.tex"),
        "jwst_trgb_li2024_source_table": ("2408.00065", "sample631.tex"),
        "complete_hst_jwst_trgb_li2025_source_table":
            ("2504.08921", "main.tex"),
    }
    fetched = []
    for label, (arxiv, member) in sources.items():
        fetched.append({
            "label": label, "arxiv": arxiv,
            "path": f"arxiv_{arxiv}.src.tar.gz", "sha256": digest,
            "content_verified_data_table": True,
            "analysis_table_ingested": True,
            "verification": {
                "ok": True, "member": member, "missing_markers": [],
                "missing_cell_markers": [], "cell_markers_verified": True,
                "member_sha256": digest, "cell_receipt_sha256": digest,
            },
        })
    receipt_specs = {
        "cchp_trgb_jagb": ("cchp_freedman2025_source_table", 7),
        "shoes_jwst_hst": ("shoes_riess2025_source_table", 13),
        "li2024_jwst_trgb_hst_cepheid":
            ("jwst_trgb_li2024_source_table", 1),
        "li2025_complete_trgb_hst_cepheid":
            ("complete_hst_jwst_trgb_li2025_source_table", 1),
    }
    receipts = [{
        "dataset": dataset, "source_label": source,
        "registered_row_count": count, "observed_row_count": count,
        "source_archive_sha256": digest, "source_member_sha256": digest,
        "source_cell_receipt_sha256": digest,
        "transcription_csv_sha256": digest, "exact_cells_sha256": digest,
        "exact_cells": [{} for _ in range(count)], "verified": True,
    } for dataset, (source, count) in receipt_specs.items()]
    return {
        "schema": "htt.jwst_source_table_acquisition.v4",
        "fetched": fetched, "missing": [],
        "source_checked_comparison_csv": "x.csv",
        "source_checked_comparison_csv_sha256": digest,
        "source_checked_aggregate_csv": "y.csv",
        "source_checked_aggregate_csv_sha256": digest,
        "transcription_receipts": receipts,
    }


def test_probabilistic_match_discriminates_close_from_distant() -> None:
    ra, dec, pgc = _synthetic_cf4()
    # plant one group VERY close to the anchor and one 2 deg away
    ra[0], dec[0] = 150.0, 20.0                 # ~0 deg from the anchor
    m = probabilistic_identity_match(
        150.0, 20.0, ra, dec, position_sigma_deg=0.1,
        ambiguity_ratio_threshold=0.5)
    assert m["best_index"] == 0
    assert m["positionally_credible"]                  # close -> credible
    assert m["posterior_positional_match_probability"] > 0.5
    # a distant anchor (no nearby group) is NOT credible (not a bare argmin)
    m2 = probabilistic_identity_match(
        5.0, -50.0, ra, dec, position_sigma_deg=0.1,
        ambiguity_ratio_threshold=0.5)
    if m2["best_separation_deg"] > 0.5:
        assert not m2["positionally_credible"]
        assert m2["posterior_positional_match_probability"] < 0.5


def test_crossmatch_counts_credible_and_flags_duplicates() -> None:
    ra, dec, pgc = _synthetic_cf4()
    ra[0], dec[0] = 150.0, 20.0
    anchors = [
        {"object_host_name": "A", "ra_deg_j2000": 150.0, "dec_deg_j2000": 20.0},
        {"object_host_name": "B", "ra_deg_j2000": 150.001, "dec_deg_j2000": 20.0},
    ]
    cm = crossmatch_all(anchors, ra, dec, pgc, position_sigma_deg=0.1,
                        ambiguity_ratio_threshold=0.5)
    assert cm["n_positionally_credible"] >= 1
    # A and B both land on group 0 -> flagged as a duplicate, not merged
    assert any(len(v) > 1 for v in cm["duplicate_cf4_groups"].values())


def test_source_table_decision_requires_both_verified_analysis_tables() -> None:
    fm = {"fetched": [{"label": "shoes_riess"}, {"label": "trgb_blakeslee"}],
          "missing": [{"label": "cchp_freedman2025_t2"}]}
    d = authoritative_reproduction_decision(fm)
    assert not d["authoritative_table_reproduced"]
    assert d["jwst_lane_status"] == "source_table_blocked"
    assert not d["cf4_conditioned_forecast_authorized"]
    # a 200-OK page carrying the CCHP LABEL but NOT certified as a data table
    # must NOT count as reproduction (content-gate, not label-gate)
    fm_label_only = {"fetched": [{"label": "cchp_freedman2025_t2"}], "missing": []}
    assert not authoritative_reproduction_decision(
        fm_label_only)["authoritative_table_reproduced"]
    # Exact source/member/cell and transcription receipts are all required.
    fm2 = _valid_source_manifest()
    assert authoritative_reproduction_decision(fm2)["authoritative_table_reproduced"]
    for mutation in ("verification_ok", "missing_marker", "fake_hash",
                     "wrong_source", "wrong_count"):
        broken = copy.deepcopy(fm2)
        if mutation == "verification_ok":
            broken["fetched"][0]["verification"]["ok"] = False
        elif mutation == "missing_marker":
            broken["fetched"][0]["verification"]["missing_markers"] = ["x"]
        elif mutation == "fake_hash":
            broken["fetched"][0]["sha256"] = "sha256:not-a-digest"
        elif mutation == "wrong_source":
            broken["fetched"][0]["arxiv"] = "wrong"
        elif mutation == "wrong_count":
            broken["transcription_receipts"][0]["observed_row_count"] = 6
        assert not authoritative_reproduction_decision(
            broken)["authoritative_table_reproduced"]


def test_row_manifest_is_row_complete() -> None:
    seed = [{"name": "NGC1", "ra_deg": 10.0, "dec_deg": 5.0,
             "jwst_e_dm_mag": 0.04, "method": "TRGB", "source": "Freedman2025"}]
    man = build_row_manifest(seed, seed_sha256="sha256:x", fetch_manifest={})
    r = man["rows"][0]
    for key in ("object_host_name", "ra_deg_j2000", "coordinate_evidence",
                "redshift_evidence",
                "published_distance_modulus_precision_mag",
                "method_calibration_group", "cited_source_citation",
                "authoritative_doi_verified", "deterministic_transform"):
        assert key in r
    # cited-source citation present; the authoritative per-anchor DOI is NOT
    # claimed verified (the authoritative table is not reproduced)
    assert "Freedman" in r["cited_source_citation"]
    assert r["authoritative_doi_verified"] is False


def test_replay_and_negative_tests() -> None:
    ra, dec, pgc = _synthetic_cf4()
    seed = [{"name": f"N{i}", "ra_deg": float(ra[i]), "dec_deg": float(dec[i]),
             "jwst_e_dm_mag": 0.04, "method": "TRGB", "source": "Freedman2025"}
            for i in range(8)]
    rows = build_row_manifest(seed, seed_sha256="x", fetch_manifest={})["rows"]
    assert row_replay(rows, rows)["replay_identical"]
    loo = leave_one_match_report(rows, ra, dec, pgc, position_sigma_deg=0.1,
                                 ambiguity_ratio_threshold=0.5)
    assert loo["per_anchor_best_match_stable"]
    assert loo["duplicate_leave_one_status"] == "not_applicable_no_duplicates"
    assert loo["n_duplicate_grouping_changed_under_leave_one_out"] == 0
    neg = label_substitution_negative_test(
        rows, ra, dec, pgc, position_sigma_deg=0.1,
        ambiguity_ratio_threshold=0.5, seed=1)
    # a derangement of coordinates among labels breaks the credible identities
    assert neg["substitution_detected"]
    if neg["n_credible_truth"] > 0:
        assert neg["all_credible_identities_broken"]


def test_leave_one_duplicate_grouping_reports_actual_changed_subsets() -> None:
    ra, dec, pgc = _synthetic_cf4()
    ra[0], dec[0] = 150.0, 20.0
    anchors = [
        {"object_host_name": "A", "ra_deg_j2000": 150.0,
         "dec_deg_j2000": 20.0},
        {"object_host_name": "B", "ra_deg_j2000": 150.001,
         "dec_deg_j2000": 20.0},
        {"object_host_name": "C", "ra_deg_j2000": float(ra[3]),
         "dec_deg_j2000": float(dec[3])},
    ]
    report = leave_one_match_report(
        anchors, ra, dec, pgc, position_sigma_deg=0.1,
        ambiguity_ratio_threshold=0.5)
    assert report["duplicate_leave_one_status"] == "evaluated"
    assert report["n_duplicate_grouping_changed_under_leave_one_out"] == 2
    assert {row["dropped_anchor"] for row in
            report["duplicate_grouping_changed_subsets"]} == {"A", "B"}


def test_guards_and_caption_lint() -> None:
    with pytest.raises(JWSTAnchorError, match="coordinate radius alone"):
        refuse_radius_only_identity("coordinate_radius_only")
    with pytest.raises(JWSTAnchorError, match="synthetic"):
        refuse_synthetic_renamed_observed("synthetic_fixture_as_observed")
    with pytest.raises(JWSTAnchorError, match="authoritative"):
        refuse_authoritative_without_table(False, "authoritative_reproduced")
    with pytest.raises(JWSTAnchorError, match="N-DATA-CF4-DOWNSTREAM"):
        refuse_cf4_forecast_downstream_open("cf4_conditioned_forecast")
    with pytest.raises(JWSTAnchorError, match="cosmological"):
        refuse_jwst_measurement("h0_fit_from_host_offsets")
    with pytest.raises(JWSTAnchorError, match="Bianchi-family"):
        refuse_bianchi_from_jwst("bianchi_family")
    # admissible input does not raise
    refuse_authoritative_without_table(True, "authoritative_reproduced")
    refuse_jwst_measurement("published_table_host_consistency")
    with pytest.raises(JWSTAnchorError, match="forbidden caption"):
        lint_caption("this is a JWST detection of the dipole")


@needs_data
@pytest.mark.parametrize("mutation", [
    "verification_false", "missing_marker", "wrong_csv_path",
    "tampered_csv_hash", "wrong_source_member", "wrong_registered_count",
])
def test_runner_source_provenance_gate_fails_closed(mutation) -> None:
    import yaml

    spec = yaml.safe_load((REPO_ROOT /
        "docs/research_program/long_horizon_rescue/pr153_spec.yaml")
        .read_text(encoding="utf-8"))
    ds = spec["data_scope"]["raw_data_paths"]
    fetch = json.loads((REPO_ROOT / ds["fetch_manifest"])
                       .read_text(encoding="utf-8"))
    comparison = _load_comparison_table(REPO_ROOT / ds["comparison_csv"])
    aggregate = _load_comparison_table(REPO_ROOT / ds["aggregate_csv"])
    _verify_fetch_manifest(spec, fetch, comparison, aggregate)
    broken = copy.deepcopy(fetch)
    if mutation == "verification_false":
        broken["fetched"][0]["verification"]["ok"] = False
    elif mutation == "missing_marker":
        broken["fetched"][0]["verification"]["missing_cell_markers"] = ["x"]
    elif mutation == "wrong_csv_path":
        broken["source_checked_comparison_csv"] = "wrong.csv"
    elif mutation == "tampered_csv_hash":
        broken["source_checked_comparison_csv_sha256"] = "sha256:" + "0" * 64
    elif mutation == "wrong_source_member":
        broken["fetched"][0]["verification"]["member"] = "wrong.tex"
    elif mutation == "wrong_registered_count":
        broken["transcription_receipts"][0]["registered_row_count"] = 6
    with pytest.raises(SystemExit, match="invalid JWST source provenance"):
        _verify_fetch_manifest(spec, broken, comparison, aggregate)


@needs_data
def test_runner_check_and_real_artifacts() -> None:
    result = subprocess.run(
        [sys.executable,
         str(REPO_ROOT / "scripts/codex_harness/run_pr153_jwst_anchor.py"),
         "--check"], cwd=REPO_ROOT, capture_output=True, text=True, check=False)
    assert result.returncode == 0, result.stdout + result.stderr
    man = json.loads((GEN / "pr153_row_manifest.json")
                     .read_text(encoding="utf-8"))
    assert man["n_anchors"] == 17
    dec = json.loads((GEN / "pr153_authoritative_decision.json")
                     .read_text(encoding="utf-8"))
    assert dec["jwst_lane_status"] == "published_table_conditional_result"
    distance = json.loads((GEN / "pr153_distance_consistency.json")
                          .read_text(encoding="utf-8"))
    assert distance["cchp_trgb_minus_jagb_consistency"]["n_unique_hosts"] == 7
    assert distance["shoes_jwst_minus_hst_consistency"]["n_unique_hosts"] == 13
    assert distance["expanded_source_reported_aggregates"][
        "n_registered_aggregates"] == 2
    cm = json.loads((GEN / "pr153_crossmatch.json").read_text(encoding="utf-8"))
    # a genuine probabilistic result: not every anchor is a credible match
    assert 0 < cm["n_positionally_credible"] < 17
    neg = json.loads((GEN / "pr153_negative_tests.json")
                     .read_text(encoding="utf-8"))
    assert neg["label_substitution"]["substitution_detected"]
    report = json.loads((GEN / "pr153_mutation_report.json")
                        .read_text(encoding="utf-8"))
    assert report["surviving_mutation_count"] == 0
    assert len(report["mutations"]) == 6
    for name in (
        "pr153_row_manifest.json", "pr153_authoritative_decision.json",
        "pr153_distance_consistency.json", "pr153_crossmatch.json",
        "pr153_sensitivity.json", "pr153_negative_tests.json",
        "pr153_captions.json", "pr153_mutation_report.json",
    ):
        validate_artifact_metadata(json.loads((GEN / name).read_text()))
