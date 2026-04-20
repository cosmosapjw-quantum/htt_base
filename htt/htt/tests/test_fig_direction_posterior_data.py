"""Regression tests for fig_direction_posterior data loading."""
from __future__ import annotations

import json

import numpy as np

from common.contracts import DynestyResult, MockCalibrationReport
from common.posterior_summary import fiducial_posterior_bundle
from htt.figures.fig_direction_posterior import load_direction_posterior


def _bundle_fixture() -> dict:
    rng = np.random.default_rng(123)
    center = np.array([220.0, 80.0, 40.0])
    samples = rng.normal(center, 20.0, size=(120, 3))
    result = DynestyResult(
        samples=samples,
        logwt=np.log(np.linspace(1.0, 3.0, samples.shape[0])),
        logz=9.5,
        ncall=77,
        config={"seed": 9, "sampler": "static"},
    )
    report = MockCalibrationReport(
        bias_amp=0.02,
        bias_direction_deg=1.5,
        coverage_68=0.69,
        credible_radius_deg=12.0,
        n_mock=80,
    )
    return fiducial_posterior_bundle(result, mock_report=report, nside_hpd=16)


def test_load_direction_posterior_prefers_fiducial_bundle(tmp_path):
    bundle_path = tmp_path / "fiducial_posterior_bundle_v1.json"
    bundle_path.write_text(json.dumps(_bundle_fixture()), encoding="utf-8")
    l_deg, b_deg, source = load_direction_posterior(tmp_path)
    assert source == "fiducial_bundle"
    assert l_deg.shape == b_deg.shape
    assert l_deg.size == 120


def test_load_direction_posterior_falls_back_to_legacy_npz(tmp_path):
    l = np.array([250.0, 255.0, 260.0])
    b = np.array([20.0, 25.0, 30.0])
    np.savez(tmp_path / "IS06_3D_posterior.npz", l=l, b=b)
    out_l, out_b, source = load_direction_posterior(tmp_path)
    np.testing.assert_allclose(out_l, l)
    np.testing.assert_allclose(out_b, b)
    assert source == "legacy_npz_degrees"
