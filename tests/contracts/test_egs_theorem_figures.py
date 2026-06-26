"""Contract: the EGS2/EGS3 theorem figure deck is deterministic and claim-gated.

The generator's --check mode must pass (sidecars byte-stable across commits,
since the manifests are content-addressed with no git state), and every figure
manifest must carry the diagnostic-only claim firewall (no detection, no
family/geometry, no native-solver result).
"""
from __future__ import annotations

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


def test_manifests_are_content_addressed_without_git_state():
    # no git_commit / worktree fields -> --check stays green across commits
    for stem in STEMS:
        man = json.loads((FIG_DIR / f"{stem}.manifest.json").read_text())
        assert "git_commit" not in man
        assert "git_commit_or_worktree_state" not in man
        assert man["config_hash"].startswith("sha256:")
