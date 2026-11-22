"""R98 finite-statistic regression tests with independent matrix and power oracles."""
import json

import healpy as hp
import numpy as np

from scripts.r98 import cmb_full as cmb


def test_equal_group_law_survives_duplicating_a_complete_group():
    x = np.array([[1., 2.], [-2., 1.], [3., -1.], [2., -5.], [5., 9.]])
    groups = np.array([0, 0, 1, 2, 2])
    same = np.r_[np.arange(len(x)), [0, 1]]
    first = cmb.fit_gaussian(x, cmb.group_weights(groups), .2)
    repeat = cmb.fit_gaussian(x[same], cmb.group_weights(groups[same]), .2)
    for a,b in zip(first, repeat):
        np.testing.assert_allclose(a,b, atol=1e-13)


def test_weighted_score_matches_direct_covariance_and_density():
    rng = np.random.default_rng(325)
    x = rng.normal(size=(90, 9)) * np.arange(1, 10)
    y = rng.normal(size=(7, 9))
    w = cmb.group_weights(np.arange(90) % 23)
    mu = np.average(x, axis=0, weights=w)
    cov = np.cov(x, rowvar=False, aweights=w, ddof=0)
    shrunk = .8 * cov + .2 * np.diag(np.diag(cov))
    q_ref = np.einsum("ij,ij->i", y-mu, np.linalg.solve(shrunk, (y-mu).T).T)
    actual_q, actual_nll = cmb.scores(cmb.fit_gaussian(x,w,.2), y)
    np.testing.assert_allclose(actual_q, q_ref, atol=1e-12)
    np.testing.assert_allclose(actual_nll, .5*(q_ref + np.linalg.slogdet(shrunk)[1] + 9*np.log(2*np.pi)))


def test_affine_invariance_of_the_unregularized_ridge_shear():
    rng = np.random.default_rng(39)
    train, test = rng.normal(size=(500,60)), rng.normal(size=(10,60))
    train[:,40:] += train[:,:20]
    test[:,40:] += test[:,:20]
    w = cmb.group_weights(np.arange(500) % 140)
    shear = cmb.fit_shear(train, w)
    model = cmb.fit_gaussian(train, w, 0)
    model_sheared = cmb.fit_gaussian(cmb.apply_shear(train,shear), w, 0)
    np.testing.assert_allclose(cmb.scores(model,test), cmb.scores(model_sheared,cmb.apply_shear(test,shear)),
                               atol=1e-11, rtol=1e-12)


def test_split_powers_have_known_coherent_amplitude():
    rng = np.random.default_rng(855)
    a = rng.normal(size=hp.Alm.getsize(cmb.LMAX)) + 1j*rng.normal(size=hp.Alm.getsize(cmb.LMAX))
    a[:cmb.LMAX+1] = a[:cmb.LMAX+1].real
    b = 2*a
    row, err = cmb.split_power(a,b)
    assert err < 1e-12
    for r in row.values():
        np.testing.assert_allclose(r["cross_correlation"],1)
        np.testing.assert_allclose(r["half_difference_over_coadd"],1/9)


def test_all_real_cache_oof_reaggregates_from_recorded_rows():
    data = json.loads((cmb.OUT/"CMB_GROUPED_FULL_CACHE.json").read_text())
    scores = data["oof_by_cmb_id"]
    assert {int(s) for s in scores} == set(range(1000)) - {970}
    assert data["commander_null_qualified"] is False
    cols = data["oof_columns"]
    for kind in ("raw","ridge","diagonal","max_T_E_B"):
        hits = [[] for _ in range(300)]
        for key, r in scores.items():
            g, f = r[:2]
            assert int(key) % 300 == g and f == g % 5
            qobs = data["folds"][f]["models"][kind]["smica_score"]
            hits[g].append(r[cols.index(kind+"_score")] >= qobs)
        assert sum(map(sum,hits)) == data["summary"][kind]["pair_exceed"]
        np.testing.assert_allclose(np.mean([np.mean(h) for h in hits]),
                                   data["summary"][kind]["group_balanced_tail"])
    assert sorted(map(len,hits)) == [3]*201 + [4]*99

def test_full_source_native_reference_and_818_refit():
    import os
    import time
    import pytest
    if os.environ.get("HTT_R98_CMB_CACHE_AUDIT") != "1":
        pytest.skip("set HTT_R98_CMB_CACHE_AUDIT=1 on the owner device with the R95 cache")
    ids, pair, _, _, obs, _, _ = cmb.matched_source()
    data = json.loads((cmb.OUT/"CMB_GROUPED_FULL_CACHE.json").read_text())
    noise_id = ids % 300
    native_seconds = numpy_seconds = max_abs = 0.0
    no818 = []
    for fold in range(5):
        test = noise_id % 5 == fold
        w = cmb.group_weights(noise_id[~test])
        terms, _ = cmb.train_terms(pair[~test], w)
        t0 = time.monotonic()
        native = cmb.project_features(pair, terms, "native")
        native_seconds += time.monotonic() - t0
        t0 = time.monotonic()
        reference = cmb.project_features(pair, terms, "numpy")
        numpy_seconds += time.monotonic() - t0
        max_abs = max(max_abs, float(np.abs(native-reference).max()))
        np.testing.assert_allclose(native, reference, rtol=1e-12, atol=1e-12)
        metric = cmb.fit_gaussian(reference[~test],w,.2)
        np.testing.assert_allclose(cmb.scores(metric, reference[test])[0],
                                   [data["oof_by_cmb_id"][str(i)][2] for i in ids[test]],
                                   atol=1e-10,rtol=1e-12)
        tr = ~test & (ids != 818)
        te = test & (ids != 818)
        tw = cmb.group_weights(noise_id[tr])
        terms, _ = cmb.train_terms(pair[tr],tw)
        train_x = cmb.project_features(pair[tr], terms)
        te_x = cmb.project_features(pair[te], terms)
        m = cmb.fit_gaussian(train_x,tw,.2)
        sky = cmb.scores(m, cmb.project_features(obs[:1], terms))[0][0]
        no818.extend(zip(noise_id[te], cmb.scores(m,te_x)[0]>=sky))
    g,h = np.asarray(no818).T
    print({"complete_fold_projections": 5*len(ids), "max_feature_error": max_abs,
           "native_seconds": native_seconds, "numpy_seconds": numpy_seconds,
           "no818_N":len(h), "no818_exceed":int(h.sum()),
           "no818_refit_group_tail":float(cmb.group_weights(g)@h)})
