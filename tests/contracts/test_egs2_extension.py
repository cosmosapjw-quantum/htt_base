"""Contract gates for the EGS2 extension programme.

Asserts the NT2-* theorem mechanics (genuine Fisher floor, two-sided exclusion,
sourced transport, joint blind sector) and the blocker-discharge mechanics, and
that the NT-A3 registry no longer overclaims a Cramer-Rao floor."""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parents[2]


def test_nt2_a1_floor_strictly_below_single_ell():
    from htt.obsstat.egs2_fisher import fisher_floor, single_ell_sampling_dispersion
    assert abs(fisher_floor(2, 1.0) - single_ell_sampling_dispersion(2, 1.0)) < 1e-12
    assert fisher_floor(5, 1.0) < 0.632          # genuine multi-l floor is lower
    assert fisher_floor(20, 1.0) < fisher_floor(5, 1.0)
    assert fisher_floor(5, 0.7) > fisher_floor(5, 1.0)   # sky cut raises it


def test_nt2_b1_excludes_zero_filling():
    from htt.obsstat.egs2_shear_bracket import filling_bracket
    br = filling_bracket(3e-5, 6e-6)
    assert br.h3_satisfied and br.F_lo > 0.0 and br.excludes_zero


def test_nt2_b2_sourced_and_b3_blind():
    from htt.obsstat.egs2_transport import sourced_depth_transport, vorticity_blind_sector
    st = sourced_depth_transport()
    assert st.steady_gap_spread < 1e-6 and st.growing_gap_spread > 1.0 and st.sourced
    bs = vorticity_blind_sector(n_configs=500, seed=33)
    assert bs.cmb_max_sensitivity == 0.0 and bs.radial_max_projection < 1e-12 and bs.joint_blind


def test_blocker_discharges():
    from htt.obsstat.constrained_realizations import curl_posterior
    from htt.obsstat.lowell_global_calibration import e2e_maxscan_from_summaries
    post = curl_posterior(seed=4242)
    assert post.wf_estimate == 0.0 and post.cr_sd > 0.3       # WF suppressed, CR posterior
    rng = np.random.default_rng(1234)
    out = e2e_maxscan_from_summaries(rng.normal(size=6), rng.normal(size=(300, 6)),
                                     ["high"] + ["two-sided"] * 5)
    assert out["global_p"] >= min(out["local_p"])
    assert out["blocker_until_real_maps"] == "BLOCKED_MISSING_PR4_E2E_ACCESS"


def test_nt_a3_registry_no_longer_overclaims_floor():
    reg = (REPO / "docs/generated/egs_lowell_theorem_proofs.md").read_text()
    # the NT-A3 title must not assert a Cramer-Rao floor; only the disclaiming
    # "NOT a Cramer-Rao bound" mention is allowed.
    assert "Cosmic-variance Cramer-Rao floor on F_shear" not in reg
    assert "Single-sky sampling dispersion" in reg
    assert "NOT a Cramer-Rao bound" in reg
