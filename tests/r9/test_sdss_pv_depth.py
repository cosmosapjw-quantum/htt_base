from dataclasses import replace
import importlib.util
from pathlib import Path

import numpy as np
import pytest

from obsstat.sdss_pv_depth import (Catalogue, angular_basis, read_catalogue,
    mock_identity, extract_depth, representation, ensemble_summary)


MAXIMA = (.025, .05, .075, .1)


def catalogue():
    rng = np.random.default_rng(431)
    n = 2000
    return Catalogue(np.arange(n).astype(str), rng.uniform(0, 360, n),
                     np.rad2deg(np.arcsin(rng.uniform(-1, 1, n))),
                     rng.uniform(.004, .099, n), np.zeros(n), np.ones(n, dtype=bool))


def extract(cat):
    return extract_depth(cat, z_min=.0033, maxima=MAXIMA)


def test_release_reader_retains_identity_and_basic_fp_lane():
    payload = ("# objid RA Dec zcmb logdist in_mask logdist_corr\n"
               "1237663547968323716 111 38 .02 .03 1 .04\n"
               "1237663547968323717 112 37 .03 -.01 0 .02\n")
    cat = read_catalogue(payload)
    assert cat.ids.tolist() == ["1237663547968323716", "1237663547968323717"]
    assert cat.logdist.tolist() == [.03, -.01]
    assert cat.control.tolist() == [.04, .02]
    assert cat.mask.tolist() == [True, False]
    with pytest.raises(ValueError, match="duplicate row"):
        read_catalogue(payload.replace("1237663547968323717", "1237663547968323716"))
    with pytest.raises(ValueError, match="missing"):
        read_catalogue(payload.replace("logdist_corr", "wrong"))


def test_mock_columns_use_individual_redshift_and_keep_truth():
    cat = read_catalogue("ID,RA,Dec,z_obs,z_obs_cen,logdist,logdist_true\n"
                         "11911711,205,-.73,.08,.079,.04,-.0005\n", mock=True)
    assert cat.redshift[0] == .08
    assert cat.truth[0] == -.0005
    assert cat.control is None
    assert mock_identity("mocks/MOCK_HAMHOD_SDSS_v5_R19051.5_err_corr") == (51, 5)
    with pytest.raises(ValueError):
        mock_identity("mocks/MOCK_HAMHOD_SDSS_v5_R19051.8_err_corr")


def test_repeated_public_mock_ids_preserve_every_observation():
    cat = read_catalogue("ID,RA,Dec,z_obs,logdist,logdist_true\n"
                         "42,205,-.73,.08,.04,-.0005\n"
                         "42,204,-.72,.08,.06,.0001\n", mock=True)
    assert cat.source_ids.tolist() == ["42", "42"]
    assert len(set(cat.ids)) == 2
    assert cat.logdist.tolist() == [.04, .06]


def test_common_angular_field_and_zero_point_are_preserved():
    cat = catalogue()
    theta = np.array([.02, -.03, .01, .005, .002, -.003, .006, .004, -.002])
    values = angular_basis(cat.ra, cat.dec) @ theta
    result = extract(replace(cat, logdist=values, truth=values))
    np.testing.assert_allclose(result["Y"].reshape(4, 9), np.tile(theta, (4, 1)), atol=2e-15)
    rep = representation(MAXIMA)
    np.testing.assert_allclose(rep.H @ result["Y"], 0, atol=2e-15)
    np.testing.assert_allclose(rep.restore(rep.T @ result["Y"]), result["Y"], atol=2e-15)
    shifted = extract(replace(cat, logdist=values+.004))
    expected = np.tile([.004]+[0.]*8, 4)
    np.testing.assert_allclose(shifted["Y"]-result["Y"], expected, atol=2e-15)
    # The initial level retains calibration; a contrast-only likelihood loses it.
    assert np.isclose((rep.T @ expected)[0], .004)
    np.testing.assert_allclose(rep.H @ expected, 0, atol=2e-15)


def test_full_window_response_matches_shell_injection_and_finite_difference():
    cat = catalogue()
    x = angular_basis(cat.ra, cat.dec)
    shell = np.searchsorted(MAXIMA, cat.redshift, side="right")
    theta = np.random.default_rng(92).normal(size=(4, 9))*.01
    values = np.sum(x*theta[shell], axis=1)
    baseline = extract(cat)
    result = extract(replace(cat, logdist=values))
    np.testing.assert_allclose(baseline["response"] @ theta.ravel(), result["Y"], atol=3e-15)
    k, q, eps = 2, 5, 1e-6
    delta = (shell == k)*x[:, q]*eps
    plus = extract(replace(cat, logdist=values+delta))["Y"]
    minus = extract(replace(cat, logdist=values-delta))["Y"]
    np.testing.assert_allclose((plus-minus)/(2*eps), result["response"][:, 9*k+q], atol=1e-10)


def test_singular_catalogue_is_not_silently_repaired():
    cat = catalogue()
    with pytest.raises(ValueError, match="unresolved angular response"):
        extract(replace(cat, ra=np.zeros(len(cat.ids)), dec=np.zeros(len(cat.ids))))


def test_runner_shared_state_retains_zero_point_rank_and_null_sign():
    path = Path(__file__).resolve().parents[2] / "scripts/observed_runs/run_sdss_pv_depth.py"
    spec = importlib.util.spec_from_file_location("sdss_runner_test", path)
    runner = importlib.util.module_from_spec(spec); spec.loader.exec_module(runner)
    config = dict(product_id="test", frame="equatorial", redshift_maxima=MAXIMA)
    response = extract(catalogue())["response"]
    embedding, joint = runner.shared_eta_state(config, response)
    null = np.zeros(37); null[::9] = -1; null[-1] = 1
    assert joint.shape == (36, 37)
    assert np.linalg.matrix_rank(joint) == 36
    np.testing.assert_allclose(joint @ null, 0, atol=2e-15)
    theta, eta = embedding.split(null)
    assert eta.tolist() == [1]
    np.testing.assert_allclose(response @ theta + joint[:, -1]*eta[0], 0, atol=2e-15)
    assert embedding.state_roles[-1] == "SHARED_NUISANCE"
    assert embedding.state_units == ("dex",)*37


def test_window_upper_boundary_and_mask_are_applied_together():
    cat = catalogue()
    z = cat.redshift.copy(); z[:5] = [.0033, .025, .05, .075, .1]
    mask = cat.mask.copy(); mask[6] = False
    cat = replace(cat, redshift=z, mask=mask)
    result = extract(cat)
    expected = [np.count_nonzero(mask & (z > .0033) & (z < cap)) for cap in MAXIMA]
    assert result["counts"].tolist() == expected


def test_whole_mock_covariance_keeps_cross_terms_and_box_split():
    rng = np.random.default_rng(55)
    common = rng.normal(size=(128, 9))
    y = np.hstack([common + .1*rng.normal(size=common.shape) for _ in MAXIMA])
    boxes = np.repeat(np.arange(16), 8)
    rep = representation(MAXIMA)
    result = ensemble_summary(y, boxes, rep)
    train = result["training_mask"]
    assert not set(boxes[train]) & set(boxes[~train])
    direct = np.cov(y[train] @ rep.H.T, rowvar=False)
    np.testing.assert_allclose(result["contrast_covariance"], direct, atol=3e-15)
    c = result["covariance"]
    no_cross = np.zeros_like(c)
    for j in range(4):
        s = slice(j*9, (j+1)*9); no_cross[s, s] = c[s, s]
    assert np.linalg.norm(rep.H @ no_cross @ rep.H.T-direct) > 1
    np.testing.assert_allclose(result["anchored_covariance"], np.cov(y[train] @ rep.T.T, rowvar=False), atol=3e-15)
    changed = y.copy(); changed[~train] += 1000
    again = ensemble_summary(changed, boxes, rep)
    np.testing.assert_array_equal(again["covariance"], c)
    np.testing.assert_array_equal(again["mean"], result["mean"])
    assert result["probability"] is None
    assert result["law_status"] == "ESTIMATED_MOMENTS_ONLY"
    assert result["physical_confidence_image"] == "UNAVAILABLE"


def test_insufficient_joint_mocks_cannot_supply_full_covariance():
    with pytest.raises(ValueError, match="insufficient"):
        ensemble_summary(np.ones((40, 36)), np.repeat(np.arange(5), 8), representation(MAXIMA))
