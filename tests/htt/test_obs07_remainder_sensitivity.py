"""Frozen manufactured falsifiers for OBS07-SENSITIVITY-v1."""
import importlib.util
from pathlib import Path

import numpy as np

SCRIPT = Path(__file__).resolve().parents[2] / "scripts/obs07_remainder_sensitivity.py"
spec = importlib.util.spec_from_file_location("obs07", SCRIPT)
obs07 = importlib.util.module_from_spec(spec)
spec.loader.exec_module(obs07)


def test_frozen_gls_scalar_and_standard_error():
    result = obs07.sensitivity()
    np.testing.assert_allclose(result["theta_hat"], 0.2)
    np.testing.assert_allclose(result["standard_error"], 1.0 / np.sqrt(3.0))
    np.testing.assert_allclose(result["z_975"], 1.959963984540054)


def test_box_support_matches_all_eight_corners():
    for rho in obs07.RHO:
        corners = obs07.box_corners(float(rho))
        np.testing.assert_allclose(np.max(np.abs(corners @ obs07.M)), obs07.box_support(float(rho)))


def test_ellipsoid_support_matches_analytic_extremizer():
    for rho in obs07.RHO:
        u, b = obs07.ellipsoid_extremizer(float(rho))
        assert np.linalg.norm(u) <= rho + 1e-14
        np.testing.assert_allclose(obs07.M @ b, obs07.ellipsoid_support(float(rho)))


def test_frozen_supports_and_intervals():
    rows = obs07.sensitivity()["rows"]
    np.testing.assert_allclose([row["box_support"] for row in rows], [0.0, 4/30, 0.4, 4/3])
    np.testing.assert_allclose([row["ellipsoid_support"] for row in rows], [0.0, 2*np.sqrt(2)/30, 2*np.sqrt(2)/10, 2*np.sqrt(2)/3])
    assert rows[-1]["box_interval"][0] < rows[-1]["ellipsoid_interval"][0]
