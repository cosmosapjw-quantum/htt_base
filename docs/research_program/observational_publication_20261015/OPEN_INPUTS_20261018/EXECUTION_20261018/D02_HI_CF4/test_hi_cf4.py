import csv
import hashlib
import importlib.util
import json
from pathlib import Path

import numpy as np
import pytest
from scipy.special import expit

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("d02_analysis", HERE / "hi_cf4.py")
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)


@pytest.fixture(scope="module")
def inputs():
    return m.load_inputs()[0]


@pytest.fixture(scope="module")
def result():
    return json.loads((HERE / "D02_RESULT.json").read_text())


def test_published_outcomes_and_gbt_membership(inputs):
    assert len(inputs) == len({r["pgc"] for r in inputs}) == 628
    assert {k: sum(r["outcome"] == k for r in inputs) for k in m.OUTCOMES} == {
        "accepted": 385, "other_quality": 22, "confused": 29, "nondetection": 192}
    # load_inputs independently enforces all385 PGC-set equality against table4 GBT.
    assert m.outcome(500) == "nondetection"
    assert m.outcome(100) == "confused"
    with pytest.raises(ValueError):
        m.outcome(300)


def test_no_join_loss_and_no_group_fold_leak(inputs, result):
    routes = result["counts_and_joins"]["full_route_counts"]
    assert sum(r["count"] for r in routes) == 628
    assert sum(result["counts_and_joins"]["all_targets"]["CF4_status"].values()) == 628
    for fold in range(5):
        test = {r["block"] for r in inputs if r["fold"] == fold}
        train = {r["block"] for r in inputs if r["fold"] != fold}
        assert not test & train
    groups = [r["CF4_group"] for r in inputs if r["CF4_group"] is not None]
    assert len(groups) - len(set(groups)) == 6
    assert result["counts_and_joins"]["holdout_blocks"] == 622


def test_ambiguous_covariate_retained_and_not_imputed(inputs, result):
    ambiguous = [r for r in inputs if r["model_input_status"] == "AMBIGUOUS_SOURCE_VALUE"]
    assert len(ambiguous) == 1 and ambiguous[0]["pgc"] == 1095542
    assert ambiguous[0]["Vhel"] == -1
    assert ambiguous[0]["oof_detection"] is None
    domain = result["model"]["model_domain"]
    assert (domain["all_retained_targets"], domain["scored_targets"], domain["unscored_targets"]) == (628, 627, 1)
    assert domain["undefined_prediction_mass"] == 1 / 628
    for low, high in domain["628_target_mean_prediction_bounds_missing_in_0_1"].values():
        assert high - low == pytest.approx(1 / 628)


def test_recorded_predictions_reproduce_heldout_fit(inputs):
    # Refit one fixed fold directly, retaining its group exclusion, and compare
    # saved per-target predictions; labels/velocity are loaded from sealed raw.
    with (m.EXTERNAL / "TARGET_JOIN_AND_OOF.csv").open() as stream:
        saved = {int(r["pgc"]): r for r in csv.DictReader(stream)}
    scored = [r for r in inputs if r["model_input_status"] == "UNAMBIGUOUS_INPUT_VHEL"]
    train = [r for r in scored if r["fold"] != 0]
    test = [r for r in scored if r["fold"] == 0]
    x = m.design([r["Vhel"] for r in train])
    det = np.array([r["outcome"] != "nondetection" for r in train])
    y = np.array([r["outcome"] == "accepted" for r in train])
    bd = m.fit_logistic(x, det)
    bq = m.fit_logistic(x[det], y[det])
    for row in test:
        xx = m.design([row["Vhel"]])[0]
        pd, pq = expit(xx @ bd), expit(xx @ bq)
        recorded = saved[row["pgc"]]
        assert float(recorded["oof_detection"]) == pytest.approx(pd, abs=1e-12)
        assert float(recorded["oof_suitable"]) == pytest.approx(pd * pq, abs=1e-12)
        assert 0 <= pd * pq <= pd <= 1
    assert saved[1095542]["oof_suitable"] == ""


def test_all_saved_predictions_and_aggregate_score(result):
    with (m.EXTERNAL / "TARGET_JOIN_AND_OOF.csv").open() as stream:
        rows = list(csv.DictReader(stream))
    scored = [r for r in rows if r["oof_suitable"]]
    assert len(rows) == 628 and len(scored) == 627
    y = np.array([r["outcome"] == "accepted" for r in scored])
    p = np.array([float(r["oof_suitable"]) for r in scored])
    assert np.mean((y - p) ** 2) == pytest.approx(result["model"]["heldout"]["suitable_all_targets_two_stage"]["brier"])
    assert result["external_all_target_ledger"]["sha256"] == m.sha(m.EXTERNAL / "TARGET_JOIN_AND_OOF.csv")
    assert result["generator_sha256"] == m.sha(HERE / "hi_cf4.py")


def test_missing_and_release_versions_are_not_inferred_rejections(inputs):
    # New programme non-detections can legitimately have a released TF distance.
    nondet = [r for r in inputs if r["outcome"] == "nondetection"]
    assert sum(r["CF4_registered_TF"] for r in nondet) == 2
    assert sum(r["TF2020_DMbest"] for r in nondet) == 1
    accepted = [r for r in inputs if r["outcome"] == "accepted"]
    assert sum(r["TF_version_status"] == "absent_both" for r in accepted) == 108
    assert sum(r["CF4_status"] == "not_in_CF4_galaxy" for r in accepted) == 114


def test_synthetic_logistic_and_no_response_predictors():
    x = m.design([5000, 6000, 7000, 8000, 9000, 10000, 11000, 12000])
    beta = m.fit_logistic(x, [1, 1, 1, 1, 0, 0, 0, 0])
    assert beta[1] < 0
    assert np.all(np.diff(expit(x @ beta)) < 0)
    assert x.shape[1] == 2
    np.testing.assert_array_equal(m.design([10000, 15000]), [[1, 0], [1, 1]])
    with pytest.raises(ValueError):
        m.design([np.nan])


def test_first_raw_value_sensitivity_is_preserved(result):
    raw = json.loads((HERE / "D02_RAW_VHEL_SENSITIVITY.json").read_text())
    assert raw["model"]["heldout"]["detection_inclusive_confusion"]["n"] == 628
    assert result["model"]["heldout"]["detection_inclusive_confusion"]["n"] == 627
    assert raw["source_identities"] == result["source_identities"]
    assert result["model"]["bootstrap_failures"] == []
