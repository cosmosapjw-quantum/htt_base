from __future__ import annotations

import importlib.util
import json
import math
from pathlib import Path
import sys

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
PROOF_RECORD = REPO_ROOT / "docs/generated/egs_lowell_theorem_proofs.json"


# ---- pure-python re-derivation of the proven identities (no Wolfram) --------

def test_nt_a1_quadrupole_filling_identity():
    kappa, x_max = 4.0 / 21.0, 9.25e-6
    sigma = 3.3e-5
    a2 = kappa * sigma
    f_shear_direct = sigma**2 / x_max
    f_shear_in_a2 = a2**2 / (kappa**2 * x_max)
    assert math.isclose(f_shear_direct, f_shear_in_a2, rel_tol=1e-12)
    # EGS limit: D2 -> 0 (a2 -> 0) => F_shear -> 0
    assert (0.0**2) / (kappa**2 * x_max) == 0.0


def test_nt_a3_cosmic_variance_floor():
    def floor(ell: int) -> float:
        return math.sqrt(2.0 / (2 * ell + 1))

    assert math.isclose(floor(2), math.sqrt(2.0 / 5.0), rel_tol=1e-12)
    assert math.isclose(floor(2), 0.6324555320336759, rel_tol=1e-12)
    # Var(F)/F^2 == 2/(2l+1): F linear in power C2, Var(C2)=2C2^2/(2l+1)
    kappa, x_max, c2, ell = 0.2, 9.25e-6, 1e-10, 2
    fc = c2 / (kappa**2 * x_max)
    var_f = (1.0 / (kappa**2 * x_max)) ** 2 * (2 * c2**2 / (2 * ell + 1))
    assert math.isclose(var_f / fc**2, 2.0 / (2 * ell + 1), rel_tol=1e-12)


def test_nt_b3_depth_transport_limit():
    fsh, c, q, zref = 1.0, 0.5, 1.0, 1.0
    gf_steady = lambda z: (fsh + 0.0) / (fsh + 0.0)  # noqa: E731
    gf_tilt = lambda z: (fsh + c * z**q) / (fsh + c * zref**q)  # noqa: E731
    assert gf_steady(0.3) == 1.0 and gf_steady(0.9) == 1.0
    assert gf_tilt(0.0) != gf_tilt(0.9)  # depth-evolving tilt imprints a gap


# ---- proof record contract --------------------------------------------------

def test_proof_record_all_qed_and_gate_clean():
    assert PROOF_RECORD.exists(), "run scripts/prove_egs_lowell_theorems.py"
    payload = json.loads(PROOF_RECORD.read_text())
    assert payload["claim_tier"] == "program_theorem"
    assert payload["transfer_source"] == "none"
    ids = {t["theorem_id"] for t in payload["theorems"]}
    assert {"NT-A1", "NT-A3", "NT-B3"} <= ids
    for thm in payload["theorems"]:
        assert thm["qed"] is True, thm["theorem_id"]
        assert thm["proof_status"] == "symbolically_verified_wolfram"
    blob = json.dumps(payload).lower()
    for forbidden in ("family identified", "geometry detected", "native solver result", "posterior odds"):
        assert forbidden not in blob


# ---- optional Wolfram re-proof (skipped if engine/client unavailable) -------

def _wolfram_available() -> bool:
    try:
        import wolframclient  # noqa: F401
    except Exception:
        return False
    from shutil import which

    return which("WolframKernel") is not None or which("wolframscript") is not None


@pytest.mark.skipif(not _wolfram_available(), reason="Wolfram engine/client unavailable")
def test_wolfram_reproves_theorems():
    spec = importlib.util.spec_from_file_location(
        "egs_proofs", REPO_ROOT / "scripts/prove_egs_lowell_theorems.py"
    )
    module = importlib.util.module_from_spec(spec)
    sys.modules["egs_proofs"] = module
    spec.loader.exec_module(module)
    payload = module.build_proofs()
    assert all(t["qed"] for t in payload["theorems"])
