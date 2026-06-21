from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import sys

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPT = REPO_ROOT / "scripts/make_cf4_bulkflow_apex_depth.py"

pytestmark = pytest.mark.skipif(
    not (REPO_ROOT / "workdir/obs_bundle/pecvel/cf4/query_batch.npz").exists(),
    reason="CF4 reconstruction grid not present in this checkout",
)


def _load():
    spec = importlib.util.spec_from_file_location("cf4_apex_driver", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    sys.modules["cf4_apex_driver"] = module
    spec.loader.exec_module(module)
    return module


def test_report_is_diagnostic_with_depth_shells():
    module = _load()
    report = module.build_report(generating_command="pytest", worktree_state="t")
    assert report["claim_tier"] == "diagnostic_only"
    assert report["transfer_source"] == "none"
    assert len(report["shells"]) >= 4
    for shell in report["shells"]:
        assert shell["n_cells"] > 0
        assert shell["bulk_magnitude_kms"] >= 0.0
        assert 0.0 <= shell["apex_drift_from_full_sample_deg"] <= 180.0
        assert 0.0 <= shell["apex_angle_to_cmb_dipole_deg"] <= 180.0
        assert 0.0 <= shell["apex_galactic_l_deg"] < 360.0
        assert -90.0 <= shell["apex_galactic_b_deg"] <= 90.0


def test_report_is_deterministic_and_clean():
    module = _load()
    a = module._public(module.build_report(generating_command="p", worktree_state="t"))
    b = module._public(module.build_report(generating_command="p", worktree_state="t"))
    assert a == b
    blob = json.dumps(a).lower()
    for forbidden in ("family identified", "geometry detected", "frame violation detected"):
        assert forbidden not in blob
