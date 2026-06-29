"""K1 long-run prep: the noise-augmented E2E null mode (route 4).

Self-contained: synthesises a few NSIDE=16 noise-only ``.npz`` sims and runs the
real observed map against the noise-augmented null. This exercises the
``--noise-mc-dir`` code path NOW (before the real ~300 Planck noise sims finish
downloading) so it is ready to run the moment they land. Skips if the in-repo
real observed map is absent (clean clone without workdir/).
"""
from __future__ import annotations

import importlib.util
from pathlib import Path
import sys

import numpy as np
import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "scripts"))
sys.path.insert(0, str(REPO_ROOT / "htt"))

SPEC = importlib.util.spec_from_file_location(
    "k1_global_maxscan", REPO_ROOT / "scripts/k1_global_maxscan.py")
k1 = importlib.util.module_from_spec(SPEC)
sys.modules["k1_global_maxscan"] = k1
SPEC.loader.exec_module(k1)

_REAL_MAP_PRESENT = k1.rm.SMICA_MAP.is_file()
skip_no_map = pytest.mark.skipif(
    not _REAL_MAP_PRESENT, reason="real NSIDE=16 SMICA map not present (clean clone)")


def _write_noise_sims(tmp: Path, n: int) -> Path:
    """n synthetic NSIDE=16 noise-only sims in the compact {I, unit} .npz layout."""
    npix = k1.rm.hp.nside2npix(k1.rm.NSIDE)
    rng = np.random.default_rng(2026)
    for i in range(n):
        noise = rng.normal(scale=25.0, size=npix)        # ~25 uK low-ell noise
        np.savez(tmp / f"noise_mc_{i:05d}.npz", I=noise.astype(float), unit="uK")
    return tmp


def test_list_and_load_noise_sims(tmp_path):
    _write_noise_sims(tmp_path, 3)
    files = k1._list_noise_sims(tmp_path)
    assert len(files) == 3
    assert files == sorted(files)                          # deterministic order
    m = k1._load_noise_sim_map(files[0])
    assert m.shape == (k1.rm.hp.nside2npix(k1.rm.NSIDE),)
    assert np.isfinite(m).all()


def test_empty_noise_dir_raises(tmp_path):
    with pytest.raises(FileNotFoundError):
        k1._e2e_noise_null(tmp_path, 10, np.zeros((3, 3)), np.zeros(3),
                           np.zeros(k1.rm.LMAX + 1), 0)


@skip_no_map
def test_e2e_noise_report_runs_and_is_claim_gated(tmp_path):
    _write_noise_sims(tmp_path, 4)
    rep = k1.build_e2e_noise_report(tmp_path, method="smica", max_noise_sims=4)
    # claim discipline preserved
    assert rep["family_identification"] is False
    assert rep["native_solver_result"] is False
    assert rep["claim_tier"] == "diagnostic_only"
    # partial: this is an UPGRADE of the GRF null, not a full E2E discharge
    assert rep["blocker_partial"] == "BLOCKED_MISSING_PR4_E2E_ACCESS"
    assert rep["config"]["null_model"] == "lambdacdm_signal_plus_real_instrument_noise"
    # valid look-elsewhere global p
    gp = rep["result"]["global_p"]
    assert 0.0 < gp <= 1.0
    assert gp >= min(rep["result"]["local_p"].values())
    # method-matched provenance, capped, hashed
    assert rep["method"] == "smica"
    assert rep["noise_sims"]["n_used"] == 4
    assert all(p["input_hash"].startswith("sha256:") for p in rep["noise_sims"]["files"])
    # caveat must say it is NOT the full E2E (no foregrounds/systematics)
    joined = " ".join(rep["caveats"]).lower()
    assert "not the full" in joined or "still not" in joined
    assert "measured_partial" in joined


@skip_no_map
def test_max_noise_sims_caps(tmp_path):
    _write_noise_sims(tmp_path, 6)
    rep = k1.build_e2e_noise_report(tmp_path, method="smica", max_noise_sims=2)
    assert rep["noise_sims"]["n_used"] == 2
    assert rep["noise_sims"]["max_requested"] == 2


def test_canonical_grf_report_unchanged_signature():
    # the default (no noise dir) path still targets the canonical artifact and
    # the e2e path targets a SEPARATE file (canonical result untouched)
    assert k1.OUT_JSON.name == "k1_global_maxscan.json"
    assert k1.OUT_E2E_JSON.name == "k1_global_maxscan_e2e_noise.json"
    assert k1.OUT_JSON != k1.OUT_E2E_JSON
