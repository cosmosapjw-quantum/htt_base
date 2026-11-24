"""Fast synthetic tests for scripts/r108/radio_p_of_c1.py (< 30 s)."""
from __future__ import annotations

import math

import numpy as np
import pytest

from scripts.r108 import radio_p_of_c1 as P


def synthetic_state(n=400, df=0.07, seed=3):
    rng = np.random.default_rng(seed)
    d0 = rng.normal(0, 1e-3, size=(n, 2))
    u = rng.normal(0, math.sqrt(3 / (4 * math.pi)), size=(n, 2))
    prec = np.repeat(np.eye(2)[None] / 1e-6, n, axis=0)
    coeffs = P.R.tself_coefficients(d0, prec, u, df)
    dob = np.array([2.5e-3, 1.5e-3])
    return dict(coeffs=coeffs, cov0=np.cov(d0.T), dob=dob, tob=float(dob @ dob / 1e-6), df=df, n=n), d0, u


def test_p_at_matches_direct_injection():
    st, d0, u = synthetic_state()
    for c1 in (0.0, 1e-4, 3e-3):
        d = d0 + st["df"] * math.sqrt(c1) * u
        t = np.sum(d * d, axis=1) / 1e-6
        k = int(np.sum(t >= st["tob"]))
        r = P.p_at(st, c1)
        assert r["k_ge_observed"] == k
        assert r["p_mc"] == pytest.approx((k + 1) / (st["n"] + 1))


def test_p_nondecreasing_in_c1_for_gaussian_form():
    st, _, _ = synthetic_state()
    g = [P.p_at(st, c)["gaussian_p"] for c in (0.0, 1e-5, 1e-4, 1e-3, 1e-2)]
    assert all(b >= a for a, b in zip(g, g[1:]))


def test_theory_points_parser():
    env = dict(primary_min=1e-6, primary_max=2e-5, primary_argmin="A|b", primary_argmax="B|c", extended_max=3e-5,
               extended_argmax="C|d", differential_pair_max=dict(C1=4e-6, pair=["A|b", "C|d"]),
               differential_triangle_bound_4max=1.2e-4,
               with_V3_low_l_systematic=dict(factor_up=1.25, extended_max=3.75e-5, differential_pair_max=5e-6,
                                             differential_triangle_bound_4max=1.5e-4))
    gd = dict(labels=["x", "y", "z"], with_shot_noise=[1e-4, 2e-4, 3e-4], shot_noise_free=[0, 4e-6, 1.2e-4])
    th = dict(envelope=dict(linear=env, hmcode2020=env),
              C1_forms_for_R106=dict(linear=dict(g_diff=gd), hmcode2020=dict(g_diff=gd)))
    pts = P.theory_points(th)
    assert pts[0][1] == 0.0
    assert sum(1 for p in pts if p[2] == "with_shot_noise") == 6
    assert max(p[1] for p in pts if p[2] == "shot_noise_free") == pytest.approx(1.2e-4)
    v3 = [p for p in pts if p[2] == "shot_noise_free_x_V3_factor_up"]
    assert len(v3) == 6 and max(p[1] for p in v3) == pytest.approx(1.5e-4)


def test_theory_points_require_the_v3_systematic():
    env = dict(primary_min=1e-6, primary_max=2e-5, primary_argmin="A|b", primary_argmax="B|c", extended_max=3e-5,
               extended_argmax="C|d", differential_pair_max=dict(C1=4e-6, pair=["A|b", "C|d"]),
               differential_triangle_bound_4max=1.2e-4)
    gd = dict(labels=["x"], with_shot_noise=[1e-4], shot_noise_free=[0])
    th = dict(envelope=dict(linear=env, hmcode2020=env), C1_forms_for_R106=dict(linear=dict(g_diff=gd), hmcode2020=dict(g_diff=gd)))
    with pytest.raises(KeyError):
        P.theory_points(th)


def test_empirical_points_are_scale_only_and_every_p_is_conditional():
    blk = dict(differential_offdiag_dipole=dict(mono_dipole=dict(C1_transverse_debiased_pearson=4e-4, C1_transverse_raw=-1e-5)))
    racs = {k: blk for k in ("racs_full_mask_alpha0p75", "racs_overlap_with_R65_NVSS_mask", "racs_full_mask_alpha0p75_cut_x1p5",
                             "nvss_full_R65_mask")}
    pts = P.empirical_points(racs)
    forms = {p[2] for p in pts}
    assert forms == {P.RACS_FORM, "empirical_circular"} and not any("independent" in f for f in forms)
    assert min(p[1] for p in pts) == 0.0
    st, _, _ = synthetic_state()
    rows = [dict(label=lab, form=form, **P.p_at(st, c1)) for lab, c1, form in pts + [("w", 1e-3, "with_shot_noise")]]
    assert all(r["claim_class"] == "CONDITIONAL" for r in rows)
    summ = P.summary_rows(rows)
    assert len(summ) == len(pts) and all(r["claim_class"] == "CONDITIONAL" and "p" not in r and "p_conditional" in r for r in summ)
    assert P.CLAIM_CLASS["label"] == "CONDITIONAL" and P.CLAIM_CLASS["calibrated_p"] is None
    assert P.CLASSIFICATION == dict(label="CONDITIONAL", calibrated_p=None,
                                    scope="p conditional on R106 EMPIRICAL_DIFF_SELECTION null families")
