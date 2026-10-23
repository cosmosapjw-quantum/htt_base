"""Narrow independent checks of public SALT2 model-error propagation."""
import numpy as np
from scipy.interpolate import RectBivariateSpline, RegularGridInterpolator

import model_error as m


def raw_grid(path):
    triplets = np.loadtxt(path)
    phase = np.unique(triplets[:, 0])
    wave = np.unique(triplets[:, 1])
    return phase, wave, triplets[:, 2].reshape((len(phase), len(wave)))


def independent_single_band_reference(source_dir, band, phase, x1):
    """Evaluate the published grid formula without sncosmo interpolation APIs."""
    wave = np.arange(band.minwave(), band.maxwave() + 0.25, 0.5)
    wave[-1] = min(wave[-1], band.maxwave())
    trans = np.interp(wave, band.wave, band.trans, left=0, right=0)
    integrals = []
    for component in (0, 1):
        p, w, grid = raw_grid(source_dir / f"salt2_template_{component}.dat")
        spline = RectBivariateSpline(p, w, grid, kx=3, ky=3)
        integrals.append(np.trapezoid(spline(phase, wave, grid=False) * trans * wave, wave))
    f0, f1 = integrals
    center = np.trapezoid(wave * trans, wave) / np.trapezoid(trans, wave)
    v = []
    for suffix in ("variance_0", "covariance_01", "variance_1"):
        p, w, grid = raw_grid(source_dir / f"salt2_lc_relative_{suffix}.dat")
        v.append(float(RegularGridInterpolator((p, w), grid)([phase, center])[0]))
    p, w, grid = raw_grid(source_dir / "salt2_lc_dispersion_scaling.dat")
    scale = float(RegularGridInterpolator((p, w), grid)([phase, center])[0])
    cd = np.loadtxt(source_dir / "salt2_color_dispersion.dat")
    disp = np.interp(center, cd[:, 0], cd[:, 1])
    diagonal = v[0] + 2 * x1 * v[1] + x1 * x1 * v[2]
    if diagonal < 0:
        diagonal = 0.0001
    diagonal *= (f0 / (f0 + x1 * f1)) ** 2 * scale ** 2
    return diagonal + disp ** 2, disp ** 2


def test_raw_grid_reference_and_color_block():
    times, bands, y, errors, _, retained = m.frozen_data()
    exp = m.old.Experiment()
    z = m.old.CFG["zHEL"]
    rest = m.rest_bandpasses(exp, z)
    theta = np.array(retained["theta"])
    _, rcov, modelcov, total, _ = m.covariance(exp, theta, times, bands, errors, z, rest)
    assert np.linalg.eigvalsh(total).min() > 0
    assert not np.allclose(modelcov, np.diag(np.diag(modelcov)))
    source_dir = m.old.RAW / "3_SALT2/SALT2_B21trained_withsys/SALT2.MODEL000"
    i = int(np.flatnonzero(bands == "r")[0])
    j = int(np.flatnonzero((bands == "r") & (np.arange(len(bands)) != i))[0])
    phase = (times[i] - theta[0]) / (1 + z)
    direct_diag, direct_color = independent_single_band_reference(source_dir, rest["r"], phase, theta[2])
    assert abs(rcov[i, i] / direct_diag - 1) < 0.03
    assert abs(rcov[i, j] / direct_color - 1) < 0.01
    g = int(np.flatnonzero(bands == "g")[0])
    assert rcov[i, g] == 0


def test_original_failure_is_retained_and_public_parity_is_conditional():
    result = __import__("json").loads((m.HERE / "RESULT.json").read_text())
    assert abs(result["original_baseline"]["reduced_chi2"] - 3.2323283226396393) < 1e-12
    assert result["original_baseline"]["adequacy"] == "BASELINE_ADEQUACY_HOLD"
    assert result["original_baseline"]["threshold"] == 3
    assert result["public_modelcov_fit"]["published_parity"] == "NOT_REPRODUCED"
