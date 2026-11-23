"""Regression checks for R102 60-node overlay, R78 SHA immutability, and R102 artifact contracts."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[2]
R78_DAG = ROOT / "docs/research_program/observational_publication_20261015/R78_UNIFIED_SCIENCE_DAG_20261119/INTEGRATED_DAG.json"
R102_DIR = ROOT / "docs/research_program/observational_publication_20261015/R102_CF4_HOLDOUT_NATIVE_SOLVER_20261123"


def test_r78_ssot_sha_and_sq_cf4_exit_code() -> None:
    sha = hashlib.sha256(R78_DAG.read_bytes()).hexdigest()
    assert sha == "90aba8c1ca9c8e3a7744be0f071dcfe09b81e5353892aca13878191e20f58c11"

    proc = subprocess.run(
        [sys.executable, "-B", "-m", "scripts.r102.program", "check-node", "--node", "SQ-CF4", "--phase", "science"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    assert proc.returncode == 3
    parsed = json.loads(proc.stdout)
    assert parsed["id"] == "SQ-CF4"
    assert parsed["new_scientific_acceptance"] is False
    assert parsed["science_status"] != "UNKNOWN"
    assert isinstance(parsed["title"], str) and len(parsed["title"]) > 0


def test_r102_generated_receipts_and_claim_boundaries() -> None:
    acq = json.loads((R102_DIR / "ACQUISITION_RECEIPT.json").read_text())
    assert acq["sdss_randoms_v1_1"]["bytes"] == 284000071
    assert acq["sdss_randoms_v1_1"]["md5"] == "8627b4063e8a71572e333e0ac65d6657"
    assert acq["commander_pr3_ffp10_noise_00000"]["bytes"] == 603987840
    assert acq["commander_pr3_ffp10_noise_00000"]["commander_null_qualified"] is False

    cmd = json.loads((R102_DIR / "COMMANDER_PAIR_00000_CHECK.json").read_text())
    assert cmd["commander_null_qualified"] is False
    assert cmd["Bianchi_family_attribution"] is None
    assert cmd["physical_Pi"] is None
    assert cmd["pseudo_cl_identity_rel_err_TT_EE_BB"] < 1e-12
    assert cmd["ordering_and_unit_alignment"]["reordered_nested_to_ring_for_analysis"] is True

    cf4 = json.loads((R102_DIR / "CF4_SELECTION_HOLDOUT_RESULTS.json").read_text())
    assert cf4["source_qualification"] == "BLOCKED_INPUT"
    assert cf4["physical_Pi"] is None
    assert cf4["physical_GF"] is None
    assert cf4["calibrated_p"] is None
    assert cf4["Bianchi_family_attribution"] is None
    assert cf4["part1_sixdf_holdout_and_selection_uncertainty"]["five_fold_group_cv"]["zero_cluster_leakage_verified"] is True
    assert cf4["part2_sdss_randoms_and_holdout"]["sdss_randoms_file"]["row_count"] == 4000000
    assert cf4["part3_cf4_36d_component_tangents_and_quadrants"]["predictive_36d_component_tangents"]["euler_homogeneity_errors"]["max"] < 1e-11

    conv = json.loads((R102_DIR / "NATIVE_SOLVER_CONVERGENCE.json").read_text())
    assert conv["atlas_qualified_for_planck_family_id"] is False
    assert conv["Bianchi_family_attribution"] is None
    assert conv["physical_Pi"] is None
    assert conv["physical_GF"] is None
    assert conv["calibrated_p"] is None
    base = conv["baseline_seven_families_L8_ref2"]
    assert set(base.keys()) == {"FLRW", "I", "V", "VII_h", "VII_h_minus", "VI_h", "VI_-1/9", "IX"}
    for row in base.values():
        assert row["max_jacobi_residual"] < 1e-10
        assert row["max_hamiltonian_residual"] < 1e-6
        assert row["max_codazzi_residual"] < 1e-6
        assert row["max_four_force_orthog_error"] < 1e-12
        assert row["max_momentum_sum_error"] < 1e-12
        assert row["max_stokes_reality_err"] < 1e-12

    n60 = json.loads((R102_DIR / "NODE60_EXECUTION.json").read_text())
    assert n60["science_authority_sha256"] == "90aba8c1ca9c8e3a7744be0f071dcfe09b81e5353892aca13878191e20f58c11"
    assert n60["original_42_sha256"] == "e3264e105cabf78ddac37addc36cacc3cfa05ee942e33e54b431b22e3e87de0d"
    assert n60["counts"]["nodes"] == 60
    assert n60["counts"]["canonical_edges"] == 129
    assert n60["counts"]["new_science_acceptances"] == 0
    assert n60["next_id"] == "SQ-CF4"
    assert n60["nodes"][0]["id"] == "E0"
    assert n60["nodes"][0]["science_status"] == "completed_scoped"
    assert all(
        row["science_status"] != "UNKNOWN"
        and isinstance(row["title"], str)
        and len(row["title"]) > 0
        for row in n60["nodes"]
    )
