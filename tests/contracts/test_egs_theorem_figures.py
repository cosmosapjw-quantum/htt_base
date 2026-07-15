"""Contract: the EGS2/EGS3 theorem figure deck is deterministic and claim-gated.

The generator's --check mode must pass and every figure manifest must carry the
diagnostic-only claim firewall (no detection, no family/geometry, no native-
solver result). PR-120's changed U1/U2 manifests additionally bind their exact
inputs and baseline worktree state.
"""
from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path
import sys

REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPT = REPO_ROOT / "scripts/make_egs2_egs3_theorem_figures.py"
FIG_DIR = REPO_ROOT / "figures/current"

STEMS = (
    "fig_egs3_a1_graded_rank", "fig_egs3_a3_evalue_calibration",
    "fig_egs2_nt2a1_fisher_floor", "fig_egs3_b1_floor_profile",
    "fig_egs3_b2_volterra", "fig_egs3_b3_vorticity",
    "fig_egs2_nt2b1_bracket", "fig_egs3_psd_cone",
    "fig_egs3_e_im_coverage", "fig_egs3_e_refutability_power",
    "fig_egs3_f_shear_memory_bias",
    "fig_egs3_u1_beta_channel", "fig_egs3_u2_fingerprint_ceilings",
    "fig_egs3_u4_teff_im_coverage", "fig_egs3_u4v9_teff_im_coverage",
)


def _load():
    spec = importlib.util.spec_from_file_location("make_egs2_egs3_theorem_figures", SCRIPT)
    assert spec is not None and spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    sys.modules["make_egs2_egs3_theorem_figures"] = mod
    spec.loader.exec_module(mod)
    return mod


def test_check_mode_is_current():
    mod = _load()
    assert mod.main(["--check"]) == 0


def test_all_eight_figures_present_with_sidecars():
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
        assert man["null_mock_status"] == "synthetic_only"
        assert "must_not_use_for_family_identification_or_family_selection" in man["caption_policy"]
        assert man["publication_gates"]["family_identification_claim"] == "fail_blocked_pre_native_atlas"


def test_manifests_are_content_addressed_and_pr120_u_figures_bind_worktree_state():
    pr120_changed = {
        "fig_egs3_u1_beta_channel",
        "fig_egs3_u2_fingerprint_ceilings",
    }
    for stem in STEMS:
        man = json.loads((FIG_DIR / f"{stem}.manifest.json").read_text())
        assert "git_commit" not in man
        assert man["config_hash"].startswith("sha256:")
        if stem in pr120_changed:
            assert man["artifact_sha256"] == "sha256:" + hashlib.sha256(
                (FIG_DIR / f"{stem}.png").read_bytes()
            ).hexdigest()
            assert man["git_commit_or_worktree_state"].startswith(
                "baseline_commit:e6da3670043596efdcd93f9ba5e631e1462146c7;"
            )
            assert len(man["input_hashes"]) == 3
            assert all(":sha256:" in value for value in man["input_hashes"])
            assert not any(
                value.startswith("docs/generated/cf4_p0_quarantine_block.json:")
                for value in man["input_hashes"]
            )
            assert any(
                value.startswith("htt/obsstat/egs3_teff_unification.py:")
                for value in man["input_hashes"]
            )
        else:
            assert "git_commit_or_worktree_state" not in man
