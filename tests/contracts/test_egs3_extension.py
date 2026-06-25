"""Contract gates for the EGS3 programme: theorem results + claim discipline."""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parents[2]


def test_a1_graded_rank_two_with_named_null():
    from htt.obsstat.egs3_graded_comparator import identifiable_rank
    r = identifiable_rank()
    assert r.rank == 2
    assert set(r.reachable_sectors) == {"Sigma2", "Omega_tilt"}
    assert set(r.null_sectors) == {"W2", "Omega_k"}


def test_a3_pi_evalue_markov_bound():
    from htt.obsstat.egs3_calibration import evalue_markov_calibration
    cal = evalue_markov_calibration(n_sims=20000, threshold=1.5, seed=71)
    assert abs(cal.null_mean_evalue - 1.0) < 1e-6 and cal.markov_holds


def test_b1_floor_is_k_profile():
    from htt.bass.transfer.shear_quadrupole_seminative import floor_profile_vs_k
    prof = floor_profile_vs_k([1e-5, 2e-3], lmax=40)
    floors = sorted((v["k_chi_star"], v["floor"]) for v in prof.values())
    assert abs(floors[0][1] - (2 / 5) ** 0.5) < 1e-2     # super-horizon -> 0.632
    assert floors[-1][1] < 0.6324555                     # finite k -> below


def test_b3_transverse_reopens_radial_blind():
    from htt.obsstat.egs3_vorticity_channels import vorticity_reopening
    r = vorticity_reopening(n_configs=400, seed=91)
    assert r.radial_max_abs < 1e-12 and r.transverse_design_rank == 3 and r.reopens


def test_experiments_json_claim_boundary():
    p = REPO / "docs/generated/egs3_experiments.json"
    if not p.exists():
        import pytest
        pytest.skip("run make egs3-experiments first")
    d = json.loads(p.read_text())
    assert d["family_identification"] is False
    assert d["native_solver_result"] is False
    assert "no detection" in d["claim_boundary"]
    assert set(d["blockers_kept_open"]) >= {
        "BLOCKED_MISSING_PR4_E2E_ACCESS", "AWAITING_NATIVE_LOWELL_SOLVER"}
