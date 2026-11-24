"""Fast synthetic tests for scripts/r108/cf4_kband_contrast.py (K strata, exchangeability, zero-point diagnostics)."""
import numpy as np
import pytest

from scripts.r108 import cf4_kband_contrast as m
from scripts.r106.cf3_overlap import stratified_masks


def test_kbins_and_strata():
    K = np.array([6.1, 10.0, 11.74, 11.76, 13.4])
    kb, edges = m.kbins(K, .25)
    assert np.all(edges[kb] <= K) and np.all(K < edges[kb + 1])
    st = m.k_strata(np.array([0, 0, 1, 1, 2]), kb)
    assert len(np.unique(st)) == 5
    with pytest.raises(ValueError):
        m.kbins(np.array([5.0]), .25)


def test_exchangeability_counts():
    strata = np.array([0, 0, 1, 1, 2, 2])
    ex = np.array([True, True, True, False, False, False])
    e = m.exchangeability(strata, ex)
    assert e["n_excluded_in_strata_fully_excluded"] == 2
    assert e["n_excluded_in_mixed_strata"] == 1 and e["n_mixed_strata"] == 1


def test_stratified_masks_preserve_k_counts():
    rng = np.random.default_rng(1)
    strata = rng.integers(0, 6, 200)
    ex = rng.random(200) < .4
    n_keep = {int(s): int(np.sum(ex & (strata == s))) for s in np.unique(strata)}
    M = stratified_masks(strata, n_keep, 7, np.random.default_rng([3, 4]))
    for s, k in n_keep.items():
        assert np.all(M[strata == s].sum(0) == k)


def _synthetic(c_member, seed=7, n=6000):
    rng = np.random.default_rng(seed)
    cz = rng.uniform(1000, 16000, n)
    K = rng.uniform(8., 12.8, n)
    eps = np.full(n, .1)
    member = K < 11.6 + rng.normal(0, .1, n)      # apparent-magnitude selection with a soft edge
    dd = .02 + .05 * (K - 10.) + c_member * member + rng.normal(0, .1, n)
    return cz, dd, eps, member, K, np.ones(n, bool)


def test_zero_point_fit_recovers_member_effect():
    for c in (0., .05):
        out = m.zero_point_diagnostics(*_synthetic(c))
        fit = out["linear_fit_all_rows"]
        assert fit["b_per_mag"] == pytest.approx(.05, abs=4 * fit["b_err"])
        assert fit["c_member_dex"] == pytest.approx(c, abs=4 * fit["c_err"])


def test_raw_split_shows_selection_offset():
    # with c = 0 the raw member-minus-nonmember split is negative (members brighter -> smaller delta_d here),
    # while the matched-K cells are consistent with zero
    out = m.zero_point_diagnostics(*_synthetic(0.))
    raw = out["all_rows_by_cz"]["combined"]
    assert raw < -.05
    cells = out["matched_K_cells_all_rows"]["combined"]
    assert abs(cells["combined"]) < 4 * cells["combined_err"] + .01


# --------------------------------------------------------------------------- review CF4-1 / CF4-4

def test_exchangeability_fractions_groups_and_selected():
    strata = np.array([0, 0, 1, 1, 1, 2, 2, 3])
    ex = np.array([True, True, True, False, False, False, False, True])
    sel = np.array([True, False, True, True, True, False, False, True])
    e = m.exchangeability(strata, ex, sel)
    assert e["n_excluded"] == 4 and e["n_excluded_in_strata_fully_excluded"] == 3
    assert e["effective_n_randomised"] == 1 and e["fraction_excluded_in_strata_fully_excluded"] == pytest.approx(.75)
    assert e["n_excluded_selected"] == 3 and e["n_excluded_selected_in_mixed_strata"] == 1
    # per-group counting (test_only): stratum 1 split across two folds becomes fully excluded inside fold 0
    g = m.exchangeability(strata, ex, sel, groups=[np.array([0, 1, 2]), np.array([3, 4, 5, 6, 7])])
    assert g["n_excluded"] == 4 and g["n_excluded_in_strata_fully_excluded"] == 4 and g["effective_n_randomised"] == 0
    assert g["counted"].startswith("per fold")


def _drop_block(zraw, degenerate=False, used=64):
    ctl = dict(mean=1., sd=.5, k_control_le_observed=3, k_control_ge_observed=61, p_le_plus_one=.06,
               p_ge_plus_one=.95, replicates=used)
    return dict(per_key={"pgc": dict(sum_kept_minus_zero={"nn": 0.2}, control={"nn": ctl})},
                mark_zero_point_confound=None if zraw is None else dict(
                    z_observed_minus_control_mean_over_sd=zraw, observed=.01, control=dict(mean=.02)),
                control_replicates_used=used, degenerate=degenerate, comparable_to_controls=True)


def test_comparability_raw_rule_is_data_driven():
    for z, want in ((-7.0, False), (2.5, True), (None, None)):
        blk = _drop_block(z)
        c = m.apply_comparability(blk, "drop", None)
        assert c["comparable_to_controls"] is want and blk["comparable_to_controls"] is want
        assert ("not_comparable_reason" in blk) == (want is False)
    deg = _drop_block(-9., degenerate=True)
    assert m.apply_comparability(deg, "drop", None)["comparable_to_controls"] is None
    # a drop block with one usable control replicate has no defined z
    assert m.apply_comparability(_drop_block(-9., used=1), "drop", None)["comparable_to_controls"] is None


def test_comparability_czbin_uses_residual_not_raw_z():
    blk = _drop_block(-38.)
    c = m.apply_comparability(blk, "drop_recentered_czbin", dict(z=1.2))
    assert c["comparable_to_controls"] is True and c["raw_mark_zero_point_z"] == -38.
    c = m.apply_comparability(_drop_block(.5), "drop_recentered_czbin", dict(z=5.3))
    assert c["comparable_to_controls"] is False
    assert m.apply_comparability(_drop_block(.5), "drop_recentered_czbin", dict(z=None))["comparable_to_controls"] is None


def test_summarize_carries_labels_into_every_entry():
    strata = np.array([0, 0, 1, 1])
    ex_mask = np.array([True, True, True, False])
    exch = m.exchangeability(strata, ex_mask)
    blk = _drop_block(-7.)
    comp = m.apply_comparability(blk, "drop", None)
    out = m.summarize(blk, ["nn"], comp, exch, dict(comparable_to_controls_as_recorded_r106=False))
    e = out["pgc"]["nn"]
    assert e["comparable_to_controls"] is False and e["degenerate"] is False
    assert e["fraction_excluded_rows_fixed_in_every_control"] == pytest.approx(2 / 3) and e["effective_n_randomised"] == 1
    assert out["comparable_to_controls"] is False and out["comparability"]["statistic"] == "raw_mark_zero_point_z"
    assert out["comparable_to_controls_as_recorded_r106"] is False
    assert "2 of 3 excluded rows" in out["control_fractions_conditional_on"]
    # test_only layout: labels per fold key
    tob = {"pgc": dict(sum_kept_minus_zero={"nn": .1}, degenerate=False,
                       control={"nn": dict(mean=0., sd=1., replicates=10)},
                       mark_zero_point_confound=dict(z_observed_minus_control_mean_over_sd=1.0, observed=0.,
                                                     control=dict(mean=0.)))}
    comp = m.apply_comparability(tob, "test_only", None)
    out = m.summarize(tob, ["nn"], comp, {"pgc": exch})
    assert out["pgc"]["nn"]["comparable_to_controls"] is True and out["pgc"]["comparability"]["z"] == 1.0


def test_residual_record_detects_member_effect_at_fixed_K():
    for c, big in ((0., False), (.05, True)):
        cz, dd, eps, member, K, inc = _synthetic(c, n=20000)
        r = m.residual_record(cz, dd, eps, member, K, inc, .25)
        assert r["n_cells"] > 0
        assert (abs(r["z"]) >= m.Z_COMPARABLE) is big
    # without K matching the selection offset alone makes the split significant
    cz, dd, eps, member, K, inc = _synthetic(0., n=20000)
    assert abs(m.residual_record(cz, dd, eps, member, K, inc, None)["z"]) >= m.Z_COMPARABLE


def test_zero_point_model_labels():
    out = m.zero_point_diagnostics(*_synthetic(0.), k_label="Kc", member_label="Ktot <= K*")
    assert "b*Kc" in out["linear_fit_all_rows"]["model"] and "[Ktot <= K*]" in out["linear_fit_all_rows"]["model"]
    assert "b*Ktot" not in out["linear_fit_r105_selected_rows"]["model"]
    assert out["matched_K_cells_all_rows"]["K_variable"] == "Kc"
