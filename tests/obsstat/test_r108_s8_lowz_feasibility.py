"""R108 lane s8: the low-z feasibility record and its page (review findings S8-1, S8-2).

- the guard-test scan of rei_bianchi 56dc609e finds the end_zbar guard of DriverConfig::validate unpinned and the
  background scale-domain guard pinned;
- the change plan starts with T0 (tests for the end_zbar guard) and T7 names it;
- the page S8_LOWZ_FEASIBILITY.md is exactly what ``render_markdown`` produces from the JSON files on disk, and it
  makes no claim the fields do not carry (DOIs, VizieR scope, guard pins, wall-time source).
"""

from __future__ import annotations

import json

import pytest

from scripts.r108 import s8_lowz_feasibility as feas

RESULTS = feas.RESULTS


def _load(name: str) -> dict:
    p = RESULTS / name
    if not p.exists():
        pytest.skip(f"{name} not present")
    return json.loads(p.read_text())


def test_sci_formatting():
    assert feas._sci(128755.03299472801) == "1.29e5"
    assert feas._sci(-2.220446049250313e-16, 2) == "-2.2e-16"
    assert feas._sci(1.25e-05) == "1.25e-5"
    assert feas._sci(0.0) == "0"


def test_guard_scan_end_zbar_unpinned_scale_domain_pinned():
    if not (feas.REI_REPO / ".git").exists():
        pytest.skip("rei_bianchi repository not present")
    scan = feas.guard_test_scan()
    assert scan["test_files_scanned"] > 10
    assert {x["value"] for x in scan["end_zbar_literals"]} == {19.8}
    assert not scan["end_zbar_guard_pinned_by_a_test"]
    assert scan["scale_domain_guard_pinned_by_a_test"]
    assert any("axbi_background.rs:118" in x["at"] for x in scan["point_at_scale_is_err_assertions"])
    # the temperature-provider test is located and is not counted as a z-domain pin
    sites = feas.find_sites(feas.NOT_Z_DOMAIN_TESTS)
    assert sites[0]["lines"] == [156]


def test_feasibility_json_records_unpinned_guard_and_t0():
    res = _load("S8_LOWZ_FEASIBILITY.json")
    assert res["acceptance_tests_if_unblocked"][0].startswith("T0 ")
    assert "T0" in res["acceptance_tests_if_unblocked"][-1]
    assert res["unpinned_guards"][0]["pinned_by_a_test"] is False
    assert res["pinned_guards_from_scan"][0]["pinned_by_a_test"] is True
    roles = " ".join(t["role"] for t in res["rust_tests_pinning_the_guards"])
    assert "geometry_map" not in roles and "temperature" not in roles
    assert res["literature_arxiv_verification"]["doi_summary"]["without_doi"] == ["Reformatted UVB tables (Taira et al.)"]
    d = res["derived_for_markdown"]
    assert d["replay_wall_time_from_command_log"]["file"].endswith("s8_COMMANDS.jsonl")
    assert 0.0 < d["max_abs_affine_prediction_minus_exact_x_e4_term"] < 1e-16


def test_markdown_is_rendered_from_the_json_files():
    res = _load("S8_LOWZ_FEASIBILITY.json")
    tau = _load("S8_LOWZ_TAU.json")
    replay = _load("S8_REPLAY_COMPARISON.json")
    md = (RESULTS / "S8_LOWZ_FEASIBILITY.md").read_text()
    assert md == feas.render_markdown(res, tau, replay, RESULTS / "S8_LOWZ_FEASIBILITY.json")
    # wording fixed by review S8-1 / S8-2
    assert "Three Rust tests pin" not in md
    assert "including the DOIs" not in md
    assert "none for Taira et al." in md
    assert "Not found on the CfA VizieR mirror" in md
    assert "No VizieR catalogue was found" not in md
    assert "s8_COMMANDS.jsonl" in md and "temperature-provider guard" in md
    assert "Unpinned guard." in md
