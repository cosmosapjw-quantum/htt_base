"""Contract: the rev-r195..r198 observed-data figure deck is deterministic and
claim-gated.

The generator's --check mode must pass (source.json + manifest sidecars
byte-stable across commits; content-addressed, no git state), every manifest
carries the diagnostic-only claim firewall (no detection / family / geometry /
native-solver), and no figure encodes a forbidden claim token. Physics/statistics
results only (no dev-history / claim-gate / limitation-narrative content).
"""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import sys

REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPT = REPO_ROOT / "scripts/make_obsdata_r195_r198_figures.py"
FIG_DIR = REPO_ROOT / "figures/obsdata_current"

STEMS = (
    "fig_obs_cf4_mv_bulkflow", "fig_obs_cf4_reconstruction_spread",
    "fig_obs_cf4_mock_significance", "fig_obs_cf4_fsigma8_ml",
    "fig_obs_cf4_velocity_correlation", "fig_obs_desi_dipole_mock",
    "fig_obs_cf4pp_vorticity", "fig_obs_act_kappa",
)
_FORBIDDEN = ("family assignment", "native solver", "geometry detection")


def _load():
    spec = importlib.util.spec_from_file_location("make_obsdata_r195_r198_figures", SCRIPT)
    mod = importlib.util.module_from_spec(spec)
    sys.modules["make_obsdata_r195_r198_figures"] = mod
    spec.loader.exec_module(mod)
    return mod


def test_check_mode_is_current():
    assert _load().main(["--check"]) == 0


def test_all_eight_figures_present_with_sidecars():
    assert len(STEMS) == 8
    for stem in STEMS:
        assert (FIG_DIR / f"{stem}.png").is_file()
        assert (FIG_DIR / f"{stem}.source.json").is_file()
        assert (FIG_DIR / f"{stem}.manifest.json").is_file()


def test_every_manifest_carries_the_claim_firewall():
    for stem in STEMS:
        man = json.loads((FIG_DIR / f"{stem}.manifest.json").read_text())
        assert man["claim_tier"] == "diagnostic_only"
        assert man["family_identification"] is False
        assert man["native_solver_result"] is False
        assert man["transfer_source"] == "none"
        assert "must_state_observed_data_diagnostic" in man["caption_policy"]
        assert "must_not_state_detection" in man["caption_policy"]


def test_manifests_are_content_addressed_without_git_state():
    for stem in STEMS:
        man = json.loads((FIG_DIR / f"{stem}.manifest.json").read_text())
        assert "git_commit" not in man
        assert man["config_hash"].startswith("sha256:")


def test_no_forbidden_claim_token_in_sidecars():
    for stem in STEMS:
        blob = ((FIG_DIR / f"{stem}.manifest.json").read_text()
                + (FIG_DIR / f"{stem}.source.json").read_text()).lower()
        for tok in _FORBIDDEN:
            assert tok not in blob, f"{stem}: forbidden token {tok!r}"
