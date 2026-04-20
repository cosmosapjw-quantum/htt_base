"""Regression tests for fig_retention_fraction_vs_posterior artifact loading."""
from __future__ import annotations

import json

from common.bulkflow_estimator import (
    retention_vs_posterior_artifact,
    diagnostic_zoa_ladder_artifact,
    BulkFlowCatalogue,
)
from common.contracts import DynestyResult, MockCalibrationReport
from common.posterior_summary import fiducial_posterior_bundle
from common.sky_geometry import lb_to_unitvec
from htt.figures.fig_retention_fraction_vs_posterior import (
    load_retention_vs_posterior_artifact,
)

import numpy as np


def _catalogue() -> BulkFlowCatalogue:
    rng = np.random.default_rng(55)
    n = 120
    l_deg = rng.uniform(0.0, 360.0, size=n)
    b_deg = np.rad2deg(np.arcsin(rng.uniform(-1.0, 1.0, size=n)))
    n_hat = lb_to_unitvec(l_deg, b_deg)
    V_true = np.array([220.0, 40.0, -25.0])
    u = n_hat @ V_true + rng.normal(0.0, 30.0, size=n)
    sigma = np.full(n, 30.0)
    return BulkFlowCatalogue(
        n_hat=n_hat,
        u=u,
        sigma=sigma,
        w_native=np.ones(n),
        w_selection=np.ones(n),
    )


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


def test_load_retention_vs_posterior_artifact_reads_latest_json(tmp_path):
    diagnostic = diagnostic_zoa_ladder_artifact(_catalogue())
    artifact = retention_vs_posterior_artifact(diagnostic, _bundle_fixture())
    (tmp_path / "retention_vs_posterior_v1.json").write_text(
        json.dumps(artifact),
        encoding="utf-8",
    )
    loaded = load_retention_vs_posterior_artifact(tmp_path)
    assert loaded["artifact_name"] == "retention_vs_posterior_v1.json"
    assert len(loaded["posterior_shift_deg"]) == len(loaded["bcut_deg"])
