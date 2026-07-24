from __future__ import annotations

import importlib.util
from pathlib import Path
import sys

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
pytest.importorskip(
    "healpy",
    reason=(
        "optional dependency 'healpy' not installed; "
        "install it to run tests marked requires_healpy"
    ),
)
pytestmark = [
    pytest.mark.requires_healpy,
    pytest.mark.skipif(
        not (REPO_ROOT / "workdir/obs_bundle/cmb/maps/smica_nside16.npz").exists(),
        reason="real Planck NSIDE=16 map not present in this checkout",
    ),
]

SCRIPT = REPO_ROOT / "scripts/make_lowell_morphology_real_map.py"


def _load():
    spec = importlib.util.spec_from_file_location("lowell_morph_driver", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    sys.modules["lowell_morph_driver"] = module
    spec.loader.exec_module(module)
    return module


def test_report_is_diagnostic_and_null_calibrated():
    module = _load()
    report = module.build_report(
        n_null=120, generating_command="pytest", worktree_state="test"
    )
    assert report["claim_tier"] == "diagnostic_only"
    assert report["transfer_source"] == "none"
    assert report["null_mock_status"] == "null_calibrated_isotropic_lcdm_ensemble"
    # every tracked statistic has an observed value and a p-value in [0, 1]
    for key in module.TAILS:
        assert key in report["observed"]
        assert 0.0 <= report["p_values"][key] <= 1.0
    # feature payloads carry the fail-closed claim status
    lowell = report["lowell_feature_payload"]
    assert lowell["claim_status"]["family_status"] == "blocked_pre_native_atlas"
    assert lowell["statistic_role"] == "null_calibrated_feature"


def test_report_is_deterministic_for_fixed_seed():
    module = _load()
    a = module.build_report(n_null=120, generating_command="pytest", worktree_state="t")
    b = module.build_report(n_null=120, generating_command="pytest", worktree_state="t")
    # real-map observables are deterministic
    assert a["observed"] == b["observed"]
    # null calibration is seeded -> identical p-values
    assert a["p_values"] == b["p_values"]


def test_no_bianchi_evidence_language_in_public_report():
    module = _load()
    report = module._public_report(
        module.build_report(n_null=120, generating_command="pytest", worktree_state="t")
    )
    import json

    blob = json.dumps(report).lower()
    for forbidden in (
        "family identified",
        "geometry detected",
        "native solver result",
        "bianchi evidence",
        "posterior odds",
    ):
        assert forbidden not in blob
