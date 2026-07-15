from __future__ import annotations

import hashlib
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
    assert report["status"] == "RECONSTRUCTION_CONDITIONED_SYSTEMATICS_DIAGNOSTIC"
    assert report["artifact_mode"] == "paper_appendix_conditioned"
    assert report["analysis_mode"] == "reconstruction_conditioned_method_systematics"
    assert report["transfer_source"] == "external_proxy_cf4_wf_reconstruction"
    assert report["allowed_use"] == "paper_appendix"
    assert report["finding_state"]["finding_id"] == "C1-K5-MV-F1"
    assert report["finding_state"]["scientific_status"] == "OPEN"
    assert report["observational_amplitude_claim_allowed"] is False
    assert report["global_tilt_claim_allowed"] is False
    assert report["cosmological_inference_allowed"] is False
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


def test_figure_manifest_binds_exact_png_bytes():
    figure = REPO_ROOT / "figures/observed_current/fig_observed_cf4_bulkflow_apex_depth.png"
    manifest = json.loads(
        figure.with_suffix(".manifest.json").read_text(encoding="utf-8")
    )
    assert manifest["artifact_path"] == figure.relative_to(REPO_ROOT).as_posix()
    assert manifest["artifact_sha256"] == "sha256:" + hashlib.sha256(
        figure.read_bytes()
    ).hexdigest()
