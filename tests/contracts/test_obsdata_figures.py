"""PR-120 contract for the rev-r195..r198 observed-data figure deck.

The five figure triples fed by the CF4 P0 producer/consumer chain are frozen below
``legacy/cf4_p0``.  Active source/manifest paths contain only the canonical
quarantine record and no active PNG can survive. The pre-formalism DESI figure
triple is invalidated and absent. Two unrelated figures remain byte-stable.
"""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import sys


REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPT = REPO_ROOT / "scripts/make_obsdata_r195_r198_figures.py"
FIG_DIR = REPO_ROOT / "figures/obsdata_current"
LEGACY_FIG_DIR = REPO_ROOT / "legacy/cf4_p0/figures/obsdata_current"

QUARANTINED = (
    "fig_obs_cf4_mv_bulkflow",
    "fig_obs_cf4_mock_significance",
    "fig_obs_cf4_fsigma8_ml",
    "fig_obs_cf4_reconstruction_spread",
    "fig_obs_cf4_velocity_correlation",
)
UNAFFECTED = (
    "fig_obs_cf4pp_vorticity",
    "fig_obs_act_kappa",
)
INVALIDATED = ("fig_obs_desi_dipole_mock",)
_FORBIDDEN = ("family assignment", "geometry detection")


def _load():
    spec = importlib.util.spec_from_file_location("make_obsdata_r195_r198_figures", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    sys.modules["make_obsdata_r195_r198_figures"] = module
    spec.loader.exec_module(module)
    return module


def test_check_mode_is_current():
    assert _load().main(["--check"]) == 0


def test_quarantined_active_pngs_are_absent_and_sidecars_are_blocks():
    for stem in QUARANTINED:
        assert not (FIG_DIR / f"{stem}.png").exists()
        for sidecar in ("source", "manifest"):
            card = json.loads((FIG_DIR / f"{stem}.{sidecar}.json").read_text())
            assert card["schema"] == "htt.cf4_p0_quarantine_block.v1"
            assert card["status"] == "QUARANTINED_OPEN_FINDINGS"
            assert card["claim_tier"] == "blocked"
            assert card["replacement_value"] is None
            assert card["artifact"]["artifact_id"] == stem
            assert card["artifact"]["active_png_status"] == "ABSENT_BY_QUARANTINE"


def test_exact_historical_figure_triples_live_only_under_legacy_root():
    for stem in QUARANTINED:
        for suffix in ("png", "source.json", "manifest.json"):
            assert (LEGACY_FIG_DIR / f"{stem}.{suffix}").is_file()


def test_unaffected_two_figures_and_claim_firewalls_remain_present():
    assert len(UNAFFECTED) == 2
    for stem in UNAFFECTED:
        assert (FIG_DIR / f"{stem}.png").is_file()
        source_path = FIG_DIR / f"{stem}.source.json"
        manifest_path = FIG_DIR / f"{stem}.manifest.json"
        assert source_path.is_file()
        assert manifest_path.is_file()
        manifest = json.loads(manifest_path.read_text())
        assert manifest["claim_tier"] == "diagnostic_only"
        assert manifest["family_identification"] is False
        assert manifest["native_solver_result"] is False
        assert manifest["transfer_source"] == "none"
        blob = (source_path.read_text() + manifest_path.read_text()).lower()
        for token in _FORBIDDEN:
            assert token not in blob


def test_preformalism_desi_figure_triple_is_absent():
    for stem in INVALIDATED:
        for suffix in ("png", "source.json", "manifest.json"):
            assert not (FIG_DIR / f"{stem}.{suffix}").exists()


def test_quarantine_sidecars_contain_no_numerical_figure_payload():
    prohibited_keys = {
        "amp", "obs", "mock_rms", "sigma_param", "floor", "grid", "dchi2", "fs8"
    }
    for stem in QUARANTINED:
        for sidecar in ("source", "manifest"):
            card = json.loads((FIG_DIR / f"{stem}.{sidecar}.json").read_text())
            assert prohibited_keys.isdisjoint(card)
