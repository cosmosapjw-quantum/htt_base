"""Independent physical-map and experiment-preservation checks for R58 views."""
from pathlib import Path
import hashlib
import importlib.util
import json

import numpy as np
import pytest
from scipy import stats


ROOT = Path(__file__).resolve().parents[2]
FIT_PATH = ROOT / "htt/htt/htt/infer/r58_mixed_tensor_likelihood.py"


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


views = load("r58_five_views_review", ROOT / "scripts/r58/build_r58_views.py")
mt = load("r58_five_views_fit_review", FIT_PATH)
ALPHA_NAMES = ["V_x_km_s", "V_y_km_s", "V_z_km_s", "dH_x", "dH_y", "dH_z"] + [f"kappa_{i}" for i in range(5)]


def test_physical_map_exact_kernel_and_estimable_combinations():
    k = views.physical_map()
    assert k.shape == (11, 22)
    assert len(views.PARAMETER_NAMES) == 22
    # Three vorticity, five shear/calibration and three A/calibration gauges.
    kernel = np.zeros((22, 11))
    kernel[5:8, :3] = np.eye(3)
    kernel[:5, 3:8] = np.eye(5)
    kernel[17:22, 3:8] = -np.eye(5)
    kernel[8:11, 8:11] = np.eye(3)
    kernel[14:17, 8:11] = np.eye(3)
    assert np.linalg.matrix_rank(k) == 11
    assert np.linalg.matrix_rank(kernel) == 11
    np.testing.assert_array_equal(k @ kernel, np.zeros((11, 11)))
    fit = mt.fit_linear(np.arange(11.) / 10, np.eye(11), k,
                        [.01] * 11 + [300 / views.C_KM_S] * 3 + [.01] * 8)
    assert fit["rank"] == 11
    for i in range(22):
        interval = mt.linear_interval(fit, np.eye(22)[i])
        assert interval["identified"] == (11 <= i < 14)
    # The apparent combinations, unlike individual physical/calibration terms,
    # are each identified with the original observation variance.
    for row in k:
        interval = mt.linear_interval(fit, row)
        assert interval["identified"]
        assert interval["sd"] == pytest.approx(1., rel=1e-11)
    assert mt.linear_interval(fit, np.eye(22)[11])["sd"] == pytest.approx(1 / views.C_KM_S)


def test_acceleration_sign_from_incoming_null_contraction():
    # (-,+,+,+), U=(c,0), A=∇_U U, n points observer -> source.
    # ∇_a U_b= -U_a A_b/c² + H h_ab + sigma_ab + omega_ab.
    c, energy, hubble = 3., 7., .4
    n = np.array([2., -1., 2.]) / 3
    accel = np.array([.3, -.2, .1])
    sigma = np.array([[.1, .03, -.02], [.03, -.04, .05], [-.02, .05, -.06]])
    omega = np.array([[0, .13, -.07], [-.13, 0, .11], [.07, -.11, 0]])
    grad = np.zeros((4, 4))
    grad[0, 1:] = accel / c
    grad[1:, 1:] = hubble * np.eye(3) + sigma + omega
    photon = energy / c * np.r_[1., -n]
    assert photon @ np.diag([-1., 1., 1., 1.]) @ photon == pytest.approx(0., abs=1e-14)
    contraction = c**2 / energy**2 * photon @ grad @ photon
    assert contraction == pytest.approx(hubble + n @ sigma @ n - accel @ n / c)
    assert n @ omega @ n == pytest.approx(0., abs=1e-16)
    theta = np.zeros(22)
    theta[8:11] = accel / (c * hubble)
    np.testing.assert_allclose((views.physical_map() @ theta)[3:6], -accel / (c * hubble))


def test_depth_path_preserves_level_and_full_gaussian_experiment():
    rng = np.random.default_rng(5819)
    y = rng.normal(size=32)
    blocks = np.concatenate([y[:12].reshape(4, 3), y[12:].reshape(4, 5)], axis=1)
    expected = np.vstack([blocks[0], blocks[1:] - blocks[0]]).ravel()
    t = views.depth_path_matrix()
    np.testing.assert_allclose(t @ y, expected)
    assert np.linalg.matrix_rank(t) == 32
    assert abs(np.linalg.det(t)) == pytest.approx(1.)
    assert np.linalg.matrix_rank(t[8:]) == 24
    common = np.r_[np.tile([.1, .2, .3], 4), np.tile([.4, .5, .6, .7, .8], 4)]
    np.testing.assert_allclose((t @ common)[8:], 0., atol=1e-15)
    assert np.linalg.norm((t @ common)[:8]) > 0
    np.testing.assert_allclose(np.linalg.solve(t, t @ y), y, atol=1e-15)
    a = rng.normal(size=(32, 32))
    cov = a @ a.T + 2 * np.eye(32)
    x = rng.normal(size=(32, 11))
    fit = mt.fit_linear(y, cov, x)
    transformed = mt.fit_linear(t @ y, t @ cov @ t.T, t @ x)
    np.testing.assert_allclose(transformed["estimate"], fit["estimate"], atol=2e-13)
    np.testing.assert_allclose(transformed["covariance"], fit["covariance"], atol=2e-13)
    for theta in [np.zeros(11), rng.normal(size=11), fit["estimate"]]:
        assert mt.gaussian_log_likelihood(fit, theta) == pytest.approx(
            mt.gaussian_log_likelihood(transformed, theta), abs=2e-12)


def carrier(tmp_path, rank_deficient=False):
    rng = np.random.default_rng(5841)
    x = rng.normal(size=(32, 11))
    x[:, :3] /= 1000
    if rank_deficient:
        x[:, 10] = 0
    a = rng.normal(size=(32, 32))
    path = tmp_path / "carrier.npz"
    np.savez(path, example__y32=rng.normal(size=32), example__cov32=a @ a.T + 2 * np.eye(32),
             example__response32x11=x, parameter_scale=np.array([1000.] * 3 + [.1] * 8),
             parameter_names=np.array(ALPHA_NAMES))
    meta = {"carrier_file": path.name, "carrier_sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
            "variants": {"example": {}}, "parameter_names": ALPHA_NAMES}
    (tmp_path / "OWNED_TENSOR_RESULT.json").write_text(json.dumps(meta))
    return meta


def test_typed_views_share_one_likelihood_and_no_occupancy(tmp_path):
    carrier(tmp_path)
    result = views.compute(ROOT, tmp_path, FIT_PATH)
    model = result["models"]["example"]
    assert set(model) == {"x", "Q", "Pi", "F", "G_F"}
    assert model["x"]["physical_pullback"]["rank"] == 11
    q = model["Q"]
    assert model["Pi"]["p"] == pytest.approx(stats.chi2.sf(q["value_at_fit"]**2 * q["reference_radius_squared"], 11))
    assert model["Pi"]["not_independent_of_Q"]
    assert q["physical_ceiling"] == "UNAVAILABLE"
    assert model["F"]["occupancy"]["status"] == "UNAVAILABLE"
    assert model["G_F"]["initial_block_retained"]
    assert model["G_F"]["likelihood_error"] < 1e-10
    assert (tmp_path / "FIVE_VIEW_RESULT.json").exists()


def test_views_fail_closed_before_fixed_full_rank_claim(tmp_path):
    carrier(tmp_path, rank_deficient=True)
    with pytest.raises(ValueError):
        views.compute(ROOT, tmp_path, FIT_PATH)
    assert not (tmp_path / "FIVE_VIEW_RESULT.json").exists()


def test_json_distinguishes_unboundedness_from_invalid_nan():
    assert views.clean([float("inf"), -float("inf")]) == ["+infinity", "-infinity"]
    with pytest.raises(ValueError):
        views.clean({"invalid": np.nan})


@pytest.mark.parametrize("changed", ["metadata", "carrier"])
def test_physical_pullback_rejects_reordered_coordinates(tmp_path, changed):
    meta = carrier(tmp_path)
    swapped = ALPHA_NAMES.copy()
    swapped[0], swapped[3] = swapped[3], swapped[0]
    if changed == "metadata":
        meta["parameter_names"] = swapped
    else:
        path = tmp_path / meta["carrier_file"]
        with np.load(path, allow_pickle=False) as loaded:
            arrays = {name: loaded[name] for name in loaded.files}
        arrays["parameter_names"] = np.array(swapped)
        np.savez(path, **arrays)
        meta["carrier_sha256"] = hashlib.sha256(path.read_bytes()).hexdigest()
    (tmp_path / "OWNED_TENSOR_RESULT.json").write_text(json.dumps(meta))
    with pytest.raises(ValueError, match="coordinate identity/order"):
        views.compute(ROOT, tmp_path, FIT_PATH)
    assert not (tmp_path / "FIVE_VIEW_RESULT.json").exists()


def test_directional_contrast_stf_normalization_parity_and_matrix_agreement():
    s2, s6 = 1 / np.sqrt(2), 1 / np.sqrt(6)
    basis = np.array([
        [[s2, 0, 0], [0, -s2, 0], [0, 0, 0]],
        [[s6, 0, 0], [0, s6, 0], [0, 0, -2*s6]],
        [[0, s2, 0], [s2, 0, 0], [0, 0, 0]],
        [[0, 0, s2], [0, 0, 0], [s2, 0, 0]],
        [[0, 0, 0], [0, 0, s2], [0, s2, 0]],
    ])
    np.testing.assert_allclose(np.einsum("aij,bij->ab", basis, basis), np.eye(5), atol=3e-16)
    rng = np.random.default_rng(58117)
    for _ in range(20):
        n = rng.normal(size=3)
        n /= np.linalg.norm(n)
        v = views.directional_contrast(n)
        minus = views.directional_contrast(-n)
        for scale in (3.2, 1e200, 1e-200):
            np.testing.assert_allclose(views.directional_contrast(scale * n), v, atol=6e-16)
        np.testing.assert_array_equal(v[:3], np.zeros(3))
        np.testing.assert_allclose(v[3:6], n, atol=4e-16)
        np.testing.assert_allclose(minus[3:6], -v[3:6])
        np.testing.assert_allclose(minus[6:], v[6:])
        assert v[6:] @ v[6:] == pytest.approx(2/3, abs=1.5e-15)
        alpha = rng.normal(size=11)
        sigma = np.einsum("a,aij->ij", alpha[6:], basis)
        assert v @ alpha == pytest.approx(alpha[3:6] @ n + n @ sigma @ n, abs=2e-15)
    for bad in (np.zeros(3), [1, 2], [1, np.nan, 0], [1, np.inf, 0]):
        with pytest.raises(ValueError):
            views.directional_contrast(bad)
