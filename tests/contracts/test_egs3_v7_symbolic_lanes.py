"""Contract: the EGS3 v7 symbolic-seal lanes (Sage / Lean / Wolfram) are present,
current, and PASS. Each engine-backed re-run is skipped when the engine is absent
(the runner returns exit 2 = registered blocker), so this suite is green on hosts
without Sage/Lean/Wolfram while still enforcing artifact currency where they exist.
"""
from __future__ import annotations

import json
from pathlib import Path
import shutil
import subprocess
import sys

import pytest

ROOT = Path(__file__).resolve().parents[2]
GEN = ROOT / "docs/generated"


def _load(name: str) -> dict:
    path = GEN / name
    assert path.exists(), f"missing v7 seal artifact {path} (run make v7-seals)"
    return json.loads(path.read_text(encoding="utf-8"))


def test_sage_seal_artifact_pass():
    payload = _load("egs3_sage_seal.json")
    assert payload["status"] == "PASS"
    assert payload["checks"], "empty check set"
    assert all(v is True for v in payload["checks"].values())
    # F1 / T1' exact endpoints reproduced in exact rational arithmetic
    assert payload["endpoints"]["open_branch"] == ["11/100", "17/100"]
    assert payload["endpoints"]["all_branch"] == ["9/100", "17/100"]


def test_lean_seal_artifact_pass():
    payload = _load("egs3_lean_seal.json")
    assert payload["status"] == "PASS"
    assert payload["checks"]
    assert all(v is True for v in payload["checks"].values())
    for key in ("open_branch_lo_11_100", "all_branch_lo_9_100", "dl1_lower_gap_2_100",
                "promote_blocks_on_false"):
        assert payload["checks"].get(key) is True


def test_wolfram_v7_seal_artifact_pass():
    payload = _load("egs3_v7_wolfram_proofs.json")
    assert payload["status"] == "PASS"
    results = payload.get("results", [])
    assert results, "no Wolfram results recorded"
    checks = results[0]["result"]["checks"]
    assert all(v is True for v in checks.values())
    assert checks["hotelling_F_threshold_exceeds_chi2"] is True
    assert checks["uncorrected_chi2_size_exceeds_alpha"] is True


V7_SYMPY_SEALS = (
    "signed_box_interval_seal.json",
    "gf_strictness_exact_seal.json",
    "coverage_strengthened_seal.json",
    "multicomponent_tilt_seal.json",
    "linearized_realization_seal.json",
    "mes_provenance_seal.json",
    "measured_response_seal.json",
    "data_lane_forward_seal.json",
    # v8 additions (M4 rederivation + T3-full exact endpoint realization + TEFF theory)
    "mes_rederivation_seal.json",
    "nonlinear_realization_seal.json",
    "teff_representative_seal.json",
    # v8-update additions (signed-numerator T2'' successor + real-H(z) depth memory
    # + T3-int connected interior family)
    "gf_interval_v8_seal.json",
    "volterra_hz_seal.json",
    "interior_family_seal.json",
)


@pytest.mark.parametrize("name", V7_SYMPY_SEALS)
def test_v7_sympy_seal_pass(name):
    payload = _load(name)
    assert payload["status"] == "PASS", name


def test_v7_sympy_seal_lane_current():
    r = subprocess.run([sys.executable, "scripts/run_egs3_v7_seals.py", "--check"],
                       cwd=ROOT, text=True, capture_output=True, timeout=300,
                       env={**__import__("os").environ,
                            "PYTHONPATH": f"{ROOT}:{ROOT}/htt:{ROOT}/htt/htt"})
    assert r.returncode == 0, r.stdout + r.stderr


def test_t3lin_signed_box_endpoints():
    payload = _load("linearized_realization_seal.json")
    eps = payload["endpoints"]
    assert abs(eps["lower_xC_11_over_100"]["x_C"] - 0.11) < 1e-12
    assert abs(eps["upper_xC_17_over_100"]["x_C"] - 0.17) < 1e-12
    assert payload["max_momentum_residual"] < 1e-10
    assert payload["max_gauss_residual"] < 1e-10


def test_v8_mes_rederivation_sigma_rederived():
    payload = _load("mes_rederivation_seal.json")
    assert payload["status"] == "PASS"
    sig = payload["sigma_rederivation"]
    assert sig["reduced_coeffs"] == ["5/3", "3", "3/7"]
    assert sig["rederived"] is True and sig["symbolic_identity_holds"] is True
    # omega/accel honestly stay primary-sourced (MESb print-only), not rederived
    assert payload["omega_accel_provenance"]["status"] == "primary_sourced_not_rederivable"


def test_v8_nonlinear_realization_endpoints_exact():
    payload = _load("nonlinear_realization_seal.json")
    assert payload["status"] == "PASS"
    for name, ep in payload["endpoints"].items():
        assert ep["gauss_residual_exact_zero"] is True, name
        assert ep["momentum_exact_zero"] is True, name
        assert ep["realized"] is True, name
    lo = payload["endpoints"]["lower_xC_11_over_100"]
    hi = payload["endpoints"]["upper_xC_17_over_100"]
    assert lo["bianchi_class"] == "I" and hi["bianchi_class"] == "V"


def test_v8_teff_representative_theorems():
    payload = _load("teff_representative_seal.json")
    assert payload["status"] == "PASS"
    assert payload["owner"] == "TEFF" and payload["claim_tier"] == "diagnostic_only"
    r = payload["radial_constants"]
    assert r["a_BE_over_zeta4"] == "2" and r["a_FD_over_zeta4"] == "7/4"
    f = payload["insertion_fingerprints"]
    assert f["c_4_is_zero"] is True and f["c_3"] == "-1/16" and f["c_5"] == "1/64"
    tt = payload["two_temperature_ratios"]
    assert tt["R4_invariant_pointwise"] and tt["opposite_signs"]
    assert payload["gram_ledger"]["psd"] is True
    assert payload["equal_information_nonidentifiability"]["p3_p5_move_opposite"] is True


def test_v8_teff_wolfram_crosscheck():
    path = GEN / "egs3_v8_teff_representative_proof.json"
    if not path.exists():
        pytest.skip("v8 TEFF Wolfram proof not generated on this host")
    payload = json.loads(path.read_text(encoding="utf-8"))
    assert payload["status"] == "PASS"
    checks = payload["results"][0]["result"]["checks"]
    assert all(v is True for v in checks.values())


def test_v8_wolfram_king_ellis_pass():
    path = GEN / "egs3_v8_t3_king_ellis_proof.json"
    if not path.exists():
        pytest.skip("v8 Wolfram proof not generated on this host")
    payload = json.loads(path.read_text(encoding="utf-8"))
    assert payload["status"] == "PASS"
    checks = payload["results"][0]["result"]["checks"]
    assert checks["antipodal_flux_cancels_exact"] is True
    assert checks["bianchi_v_transverse_momentum_zero"] is True


def test_v8_mathlib_seal_pass_if_present():
    # the mathlib build is ~7 GB / ~12 min cold; the contract only checks the
    # recorded artifact (never rebuilds mathlib in CI). make v8-mathlib regenerates it.
    path = GEN / "egs3_v8_mathlib_seal.json"
    if not path.exists():
        pytest.skip("mathlib lane seal not generated on this host")
    payload = json.loads(path.read_text(encoding="utf-8"))
    assert payload["status"] == "PASS"
    assert "dl1_lower_gap" in payload["theorems"]


@pytest.mark.skipif(shutil.which("sage") is None, reason="SageMath not installed")
def test_sage_lane_check_mode_current():
    r = subprocess.run([sys.executable, "scripts/run_egs3_sage_seals.py", "--check"],
                       cwd=ROOT, text=True, capture_output=True, timeout=1200)
    assert r.returncode == 0, r.stdout + r.stderr


@pytest.mark.skipif(shutil.which("lake") is None, reason="Lean/lake not installed")
def test_lean_lane_check_mode_current():
    r = subprocess.run([sys.executable, "scripts/run_egs3_lean_seals.py", "--check"],
                       cwd=ROOT, text=True, capture_output=True, timeout=900)
    assert r.returncode == 0, r.stdout + r.stderr
