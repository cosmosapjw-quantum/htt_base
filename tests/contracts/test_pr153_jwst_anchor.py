"""PR-153 contract tests: JWST authenticated-row, cross-match and manifest.

The probabilistic match, authoritative decision, row manifest, replay/negative
tests, guards and captions run everywhere on small synthetic inputs; the test
that reads the built artifacts skips when the real CF4 groups are absent.
"""
from __future__ import annotations

import json
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


def test_authoritative_decision_cited_seed_when_table_missing() -> None:
    fm = {"fetched": [{"label": "shoes_riess"}, {"label": "trgb_blakeslee"}],
          "missing": [{"label": "cchp_freedman2025_t2"}]}
    d = authoritative_reproduction_decision(fm)
    assert not d["authoritative_table_reproduced"]
    assert d["jwst_lane_status"] == "cited_seed_catalogue_linkage_scenario"
    assert not d["cf4_conditioned_forecast_authorized"]
    # a 200-OK page carrying the CCHP LABEL but NOT certified as a data table
    # must NOT count as reproduction (content-gate, not label-gate)
    fm_label_only = {"fetched": [{"label": "cchp_freedman2025_t2"}], "missing": []}
    assert not authoritative_reproduction_decision(
        fm_label_only)["authoritative_table_reproduced"]
    # only a CONTENT-verified data table flips it
    fm2 = {"fetched": [{"label": "cchp_freedman2025_t2",
                        "content_verified_data_table": True}], "missing": []}
    assert authoritative_reproduction_decision(fm2)["authoritative_table_reproduced"]


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
    neg = label_substitution_negative_test(
        rows, ra, dec, pgc, position_sigma_deg=0.1,
        ambiguity_ratio_threshold=0.5, seed=1)
    # a derangement of coordinates among labels breaks the credible identities
    assert neg["substitution_detected"]
    if neg["n_credible_truth"] > 0:
        assert neg["all_credible_identities_broken"]


def test_guards_and_caption_lint() -> None:
    with pytest.raises(JWSTAnchorError, match="coordinate radius alone"):
        refuse_radius_only_identity("coordinate_radius_only")
    with pytest.raises(JWSTAnchorError, match="synthetic"):
        refuse_synthetic_renamed_observed("synthetic_fixture_as_observed")
    with pytest.raises(JWSTAnchorError, match="authoritative"):
        refuse_authoritative_without_table(False, "authoritative_reproduced")
    with pytest.raises(JWSTAnchorError, match="N-DATA-CF4-DOWNSTREAM"):
        refuse_cf4_forecast_downstream_open("cf4_conditioned_forecast")
    with pytest.raises(JWSTAnchorError, match="measurement"):
        refuse_jwst_measurement("jwst_measurement")
    with pytest.raises(JWSTAnchorError, match="Bianchi-family"):
        refuse_bianchi_from_jwst("bianchi_family")
    # admissible input does not raise
    refuse_authoritative_without_table(True, "authoritative_reproduced")
    with pytest.raises(JWSTAnchorError, match="forbidden caption"):
        lint_caption("this is a JWST measurement of the dipole")


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
    assert dec["jwst_lane_status"] == "cited_seed_catalogue_linkage_scenario"
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
