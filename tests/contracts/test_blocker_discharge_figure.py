"""Contract: the real-data blocker-discharge figure is deterministic + claim-gated."""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import sys

REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPT = REPO_ROOT / "scripts/make_blocker_discharge_figures.py"
FIG = REPO_ROOT / "figures/current/fig_blocker_discharges"


def _load():
    spec = importlib.util.spec_from_file_location("make_blocker_discharge_figures", SCRIPT)
    mod = importlib.util.module_from_spec(spec)
    sys.modules["make_blocker_discharge_figures"] = mod
    spec.loader.exec_module(mod)
    return mod


def test_check_mode_is_current():
    assert _load().main(["--check"]) == 0


def test_present_and_claim_gated():
    assert Path(str(FIG) + ".png").is_file()
    man = json.loads(Path(str(FIG) + ".manifest.json").read_text())
    assert man["claim_tier"] == "diagnostic_only"
    assert man["family_identification"] is False
    assert man["native_solver_result"] is False
    assert "must_state_k1_e2e_null_still_blocked" in man["caption_policy"]
    # the claim-lane policy scanner requires family/native/solver wording
    policy = " ".join(man["caption_policy"] + man["promotion_blockers"] + man["caveats"]).lower()
    assert "family" in policy and "native" in policy and "solver" in policy
