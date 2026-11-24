"""Fast synthetic tests of scripts/r108/gaia_frame_leakage.py helpers (no data files)."""
import numpy as np

from scripts.r69.gaia_e2_b2 import templates
from scripts.r108 import gaia_frame_leakage as fl


def test_sexagesimal_conversion():
    ra, dec = fl.sexa_to_deg(["00 00 20.39997606", "12 00 00.0"], ["-32 21 01.2337415", "+45 30 00.0"])
    assert abs(ra[0] - 20.39997606 * 15 / 3600) < 1e-12 and abs(ra[1] - 180.0) < 1e-12
    assert abs(dec[0] + (32 + 21 / 60 + 1.2337415 / 3600)) < 1e-12 and abs(dec[1] - 45.5) < 1e-12


def test_vsh_fit_recovers_spin_and_glide_and_clips_outliers():
    rng = np.random.default_rng(7)
    n = 4000
    ra = rng.uniform(0, 2 * np.pi, n)
    dec = np.arcsin(rng.uniform(-1, 1, n))
    truth = np.zeros(16)
    truth[:6] = [5.0, -3.0, 2.0, 8.0, -6.0, 4.0]  # microarcsec (units x 1000)
    _, B = templates(ra, dec)
    sig = 0.05
    y = np.einsum("nkj,j->nk", B, truth) / 1000.0 + rng.normal(0, sig, (n, 2))
    y[:20] += 3.0  # gross outliers
    e = np.full(n, sig)
    fit = fl.vsh_fit(ra, dec, y, e, e, np.zeros(n), kappa=5.0)
    se = np.sqrt(np.diag(fit["cov"]))
    assert fit["n_rejected"] >= 20
    assert np.all(np.abs(fit["coef"] - truth) < 5 * se)
    s = fl.summarize_fit(fit)
    assert s["spin_chi2_vs_zero"] > 100 and set(("glide_vector", "B2_norm")) <= set(s)


def test_cell_index_matches_r106_strata_layout():
    G = np.array([18.0, 19.0, 19.6, 19.9])
    c = np.array([0.4, 0.6, 0.7, 0.9])
    idx = fl.cell_index(G, c, np.array([18.9, 19.4, 19.7]), np.array([0.5, 0.65, 0.75]))
    assert list(idx) == [0 * 8 + 0, 1 * 8 + 1, 2 * 8 + 2, 3 * 8 + 3]


def test_part_a_is_non_constraining_when_its_q_exceeds_the_observed_q():
    sc = {"clip_X_gt_5": {"all48": {"pm_equivalent_spin6_Q_in_R106_jk1_cov": 423.0}},
          "no_clip": {"all48": {"pm_equivalent_spin6_Q_in_R106_jk1_cov": 3924.0}}}
    c = fl.part_a_constraint(sc, 104.0)
    assert c["status"] == "NON_CONSTRAINING" and "only Part B" in c["statement"]
    sc["clip_X_gt_5"]["all48"]["pm_equivalent_spin6_Q_in_R106_jk1_cov"] = 50.0
    assert fl.part_a_constraint(sc, 104.0)["status"] == "SCALE_BELOW_OBSERVED"
    blocked = {"no_clip": {"all48": {"status": "BLOCKED"}}}
    assert fl.part_a_constraint(blocked, 104.0)["status"] == "BLOCKED"


def test_claim_class_is_filled():
    assert fl.CLAIM_CLASS["label"] == "CONDITIONAL" and "not_claimed" in fl.CLAIM_CLASS
