"""Regression tests for fig_zoa_ladder_mode0 artifact loading."""
from __future__ import annotations

import json

import numpy as np

from common.bulkflow_estimator import (
    BulkFlowCatalogue,
    diagnostic_zoa_ladder_artifact,
)
from common.sky_geometry import lb_to_unitvec
from htt.figures.fig_zoa_ladder_mode0 import load_zoa_ladder_artifact


def _catalogue() -> BulkFlowCatalogue:
    rng = np.random.default_rng(44)
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


def test_load_zoa_ladder_artifact_reads_latest_json(tmp_path):
    artifact = diagnostic_zoa_ladder_artifact(_catalogue())
    (tmp_path / "diag_zoa_ladder_v1.json").write_text(
        json.dumps(artifact),
        encoding="utf-8",
    )
    loaded = load_zoa_ladder_artifact(tmp_path)
    assert loaded["artifact_name"] == "diag_zoa_ladder_v1.json"
    assert len(loaded["bcut_deg"]) == 7
