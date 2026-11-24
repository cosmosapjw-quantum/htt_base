"""Fast synthetic tests for scripts/r108/cf4_cf3_table3_overlap.py (route classification, nest keys, window, shares)."""
import numpy as np
import pytest

from scripts.r108 import cf4_cf3_table3_overlap as m


def test_classify_statuses():
    cands = [([3, 3, 3], False),      # all routes agree
             ([3, -1, -1], False),    # one route only
             ([3, 4, -1], False),     # routes disagree
             ([-1, -1, -1], False),   # nothing
             ([5, 5, -1], True)]      # agree but the position window held two rows
    status, chosen = m.classify(cands)
    assert status.tolist() == ["matched", "matched", "ambiguous_routes_disagree", "unmatched",
                               "ambiguous_window_multiple"]
    assert chosen.tolist() == [3, 3, -1, -1, 5]


def test_group_keys_singletons_unique():
    t3 = dict(n=5, nest=np.array([100001, 0, 100001, 0, 200002]))
    k = m.group_keys(t3)
    assert k[0] == k[2] == 100001
    assert k[1] < 0 and k[3] < 0 and k[1] != k[3]
    assert len(np.unique(k)) == 4


def test_window_flags_zero_frame():
    frames = {"CMB": (0.0, 0.0, 0.0), "LG": (0.0, 0.0, 0.0)}
    ghv = np.array([1500., 2000., 9000., 16000., 16001.])
    w = m.window_flags(ghv, np.zeros(5), np.zeros(5), frames, 2000., 16000.)
    assert w["CMB"].tolist() == [False, True, True, True, False]
    assert np.array_equal(w["CMB"], w["LG"])


def test_window_flags_frame_shift_sign():
    # apex at (lat=0, lon=0) with 300 km/s: a galaxy at the apex gains +300 km/s
    frames = {"CMB": (300.0, 0.0, 0.0), "LG": (-300.0, 0.0, 0.0)}
    w = m.window_flags(np.array([1800.]), np.array([0.]), np.array([0.]), frames, 2000., 16000.)
    assert w["CMB"].tolist() == [True] and w["LG"].tolist() == [False]


def test_information_shares_analytic():
    # nest A: galaxy0 (6dF only, e=0.5) + galaxy1 (other, e=0.5); nest B: galaxy2 (6dF+other, e_DM=0.25)
    t3 = dict(n=3, nest=np.array([100001, 100001, 0]), edm=np.array([.5, .5, .25]), edmp=np.array([.5, np.nan, .5]),
              gedm=np.array([.35, .35, .25]), gvcmb=np.array([5000., 5000., 8000.]))
    is6 = np.array([True, False, True])
    keys = m.group_keys(t3)
    win = {"CMB": np.array([True, True, True])}
    out = m.information_shares(t3, keys, is6, win)["CMB"]
    wm = np.array([1 / .35 ** 2, 1 / .25 ** 2])
    share_gal = np.array([.5, 1.])
    share_src = np.array([.5, (.25 / .5) ** 2])
    assert out["mu_share_galaxy_flag"] == pytest.approx(float((share_gal * wm).sum() / wm.sum()))
    assert out["mu_share_source_level"] == pytest.approx(float((share_src * wm).sum() / wm.sum()))
    assert out["n_nests_in_window"] == 2 and out["n_window_nests_with_6df_member"] == 2


def test_robust_handles_nan():
    r = m.robust(np.array([np.nan, 1., 2., 3.]))
    assert r["n"] == 3 and r["median"] == 2.


def test_route_candidates_name_multiplicity_flags_window():
    # review CF4-3: a name-route window with two rows makes the row ambiguous even when the position window is unique
    best = [np.array([3, 4]), np.array([3, 4]), np.array([3, -1])]
    counts = [np.array([1, 1]), np.array([2, 1])]
    cands = m.route_candidates(best, counts)
    assert cands == [([3, 3, 3], True), ([4, 4, -1], False)]
    status, chosen = m.classify(cands)
    assert status.tolist() == ["ambiguous_window_multiple", "matched"] and chosen.tolist() == [3, 4]


def test_position_pairing_record_is_data_driven():
    rows = [dict(sixdf_id="a", pgc=1, sep_arcsec=.5, sixdfv_cz_minus_cf3_vcmb_kms=-10711., name_route_no_cz_gate_pgc=1),
            dict(sixdf_id="b", pgc=2, sep_arcsec=1., sixdfv_cz_minus_cf3_vcmb_kms=661., name_route_no_cz_gate_pgc=None)]
    rec = m.position_pairing_record(rows, 2., 2.5, 500.)
    assert rec["identity_verified"] is False and rec["n_resolved"] == 2
    assert rec["n_name_route_no_cz_gate_same_row"] == 1 and rec["n_exceeding_cz_gate"] == 2
    assert "-10711" in rec["note"] and "+661" in rec["note"] and "not verified" in rec["note"]
    assert "same galaxy" not in rec["note"].replace("Same-galaxy identity is not verified", "")
    assert rows[0]["name_route_no_cz_gate_same_row"] and not rows[1]["name_route_no_cz_gate_same_row"]
    assert m.position_pairing_record([], 2., 2.5, 500.)["n_resolved"] == 0
