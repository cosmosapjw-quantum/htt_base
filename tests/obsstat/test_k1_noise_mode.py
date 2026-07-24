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

pytest.importorskip(
    "healpy",
    reason=(
        "optional dependency 'healpy' not installed; "
        "install it to run tests marked requires_healpy"
    ),
)
pytestmark = pytest.mark.requires_healpy

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


def _write_sims(tmp: Path, n: int, scale: float, tag: str, seed: int) -> Path:
    """n synthetic NSIDE=16 sims in the compact {I, unit} .npz layout."""
    tmp.mkdir(parents=True, exist_ok=True)
    npix = k1.rm.hp.nside2npix(k1.rm.NSIDE)
    rng = np.random.default_rng(seed)
    for i in range(n):
        m = rng.normal(scale=scale, size=npix)
        np.savez(tmp / f"{tag}_mc_{i:05d}.npz", I=m.astype(float), unit="uK")
    return tmp


def _write_noise_sims(tmp: Path, n: int) -> Path:
    """n synthetic NSIDE=16 noise-only sims (~25 uK)."""
    return _write_sims(tmp, n, 25.0, "noise", 2026)


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
    # the e2e paths target SEPARATE files (canonical result untouched)
    assert k1.OUT_JSON.name == "k1_global_maxscan.json"
    assert k1.OUT_E2E_JSON.name == "k1_global_maxscan_e2e_noise.json"
    assert k1.OUT_E2E_FULL_JSON.name == "k1_global_maxscan_e2e_full.json"
    assert len({k1.OUT_JSON, k1.OUT_E2E_JSON, k1.OUT_E2E_FULL_JSON}) == 3


def test_full_e2e_empty_dirs_raise(tmp_path):
    cmb = tmp_path / "cmb"; noise = tmp_path / "noise"
    cmb.mkdir(); noise.mkdir()
    with pytest.raises(FileNotFoundError):                 # no CMB sims
        k1._e2e_full_null(cmb, noise, 10, np.zeros((3, 3)), np.zeros(3))
    _write_sims(cmb, 2, 50.0, "cmb", 1)                    # CMB present, noise empty
    with pytest.raises(FileNotFoundError):
        k1._e2e_full_null(cmb, noise, 10, np.zeros((3, 3)), np.zeros(3))


@skip_no_map
def test_full_e2e_report_runs_and_is_exit_gate_labelled(tmp_path):
    cmb = _write_sims(tmp_path / "cmb", 4, 50.0, "cmb", 7)      # real-like CMB MC
    noise = _write_sims(tmp_path / "noise", 3, 25.0, "noise", 9)  # fewer noise (cycled)
    rep = k1.build_e2e_full_report(cmb, noise, method="smica", max_sims=4)
    # claim discipline
    assert rep["family_identification"] is False
    assert rep["native_solver_result"] is False
    assert rep["claim_tier"] == "conditional"
    # this is the EXIT-GATE null (real CMB + real noise), not measured_partial
    assert rep["blocker_closes"] == "BLOCKED_MISSING_PR4_E2E_ACCESS"
    assert rep["blocker_label_is_legacy_compatibility"] is True
    assert rep["result"]["noise_reuse_sensitivity"][
        "exact_iid_or_exchangeability_claimed"] is False
    assert rep["config"]["null_model"] == "ffp10_cmb_plus_noise_e2e"
    # valid look-elsewhere global p
    gp = rep["result"]["global_p"]
    assert 0.0 < gp <= 1.0
    assert gp >= min(rep["result"]["local_p"].values())
    # paired provenance: 4 CMB sims, noise cycled by id (id mod 3), both hashed
    assert rep["e2e_sims"]["n_cmb_used"] == 4
    assert "id mod n_noise" in rep["e2e_sims"]["pairing"]
    files = rep["e2e_sims"]["files"]
    assert len(files) == 4
    assert files[0]["noise_file"] == files[3]["noise_file"]   # id 0 and 3 -> same noise (mod 3)
    assert all(f["cmb_id"] == i for i, f in enumerate(files))  # id-parsed order
    assert all(f["cmb_hash"].startswith("sha256:") and f["noise_hash"].startswith("sha256:") for f in files)


@skip_no_map
def test_full_e2e_max_sims_caps(tmp_path):
    cmb = _write_sims(tmp_path / "cmb", 6, 50.0, "cmb", 3)
    noise = _write_sims(tmp_path / "noise", 6, 25.0, "noise", 4)
    rep = k1.build_e2e_full_report(cmb, noise, method="smica", max_sims=2)
    assert rep["e2e_sims"]["n_cmb_used"] == 2


def test_parse_mc_id_handles_real_and_fixture_names():
    assert k1._parse_mc_id(Path("dx12_v3_smica_cmb_mc_00970_raw.fits")) == 970
    assert k1._parse_mc_id(Path("dx12_v3_smica_noise_mc_00042_raw.fits.gz")) == 42
    assert k1._parse_mc_id(Path("cmb_mc_00007.npz")) == 7
    with pytest.raises(ValueError):
        k1._parse_mc_id(Path("not_a_sim.fits"))


def test_id_based_pairing_survives_a_missing_cmb_realization(tmp_path):
    # emulate the real defect: CMB id 00003 missing. Positional pairing would shift
    # every later CMB; id-based pairing must keep noise = cmb_id mod n_noise intact.
    cmb = tmp_path / "cmb"; cmb.mkdir()
    npix = k1.rm.hp.nside2npix(NSIDE_FIX)
    rng = np.random.default_rng(7)
    present = [0, 1, 2, 4, 5]                    # 3 is missing (like 00970)
    for i in present:
        np.savez(cmb / f"cmb_mc_{i:05d}.npz", I=rng.normal(size=npix), unit="uK")
    noise = _write_sims(tmp_path / "noise", 3, 25.0, "noise", 8)
    _cmb, pairs, n_noise = k1._pair_cmb_noise_by_id(cmb, noise, max_sims=1000)
    assert n_noise == 3
    got = {cmb_id: noise_id for _cf, cmb_id, _nf, noise_id in pairs}
    assert got == {0: 0, 1: 1, 2: 2, 4: 1, 5: 2}   # noise = cmb_id mod 3, gap-robust
    assert 3 not in got                             # missing CMB simply absent, no shift


@skip_no_map
def test_full_e2e_records_missing_and_pla_status(monkeypatch, tmp_path):
    _patch_precision_inputs(monkeypatch, tmp_path, masked=False)
    cmb = tmp_path / "cmb"; cmb.mkdir()
    npix = k1.rm.hp.nside2npix(NSIDE_FIX)
    rng = np.random.default_rng(5)
    for i in [0, 1, 2, 4]:                          # id 3 missing within the range
        np.savez(cmb / f"cmb_mc_{i:05d}.npz", I=rng.normal(size=npix), unit="uK")
    noise = _write_sims(tmp_path / "noise", 3, 25.0, "noise", 6)
    rep = k1.build_e2e_full_report(cmb, noise, "smica", 1000, precision=_cfg(False), jobs=1)
    e = rep["e2e_sims"]
    assert e["n_cmb_used"] == 4
    assert e["nominal_cmb"] == 1000 and e["nominal_noise"] == 300
    assert e["known_missing_cmb_ids"] == [970]
    assert e["observed_cmb_id_gaps"] == [3]         # detected the in-range gap
    assert e["pla_confirmation"] == "officially_confirmed_by_planck_helpdesk"
    assert e["replacement_available"] is False
    assert "used CMB MC" in rep["headline"]
    assert "4 used CMB MC" in rep["headline"]       # reports the actual used count


# --------------------------------------------------------------------------- #
# v2 PRECISION path (proc-NSIDE + ell_max + mask) + parallel --jobs.
# Patch the full-res observed map + mask to small NSIDE-16 fixtures so the path
# runs without the 2 GB real FITS.
# --------------------------------------------------------------------------- #
from htt.obsstat.lowell_precision import PrecisionConfig  # noqa: E402

NSIDE_FIX = 16


def _patch_precision_inputs(monkeypatch, tmp_path, masked):
    npix = k1.rm.hp.nside2npix(NSIDE_FIX)
    obs = (np.random.default_rng(99).normal(scale=40.0, size=npix)).astype(float)
    obs_path = tmp_path / "obs_fullres.npz"
    np.savez(obs_path, I=obs, unit="uK")
    monkeypatch.setitem(k1.FULLRES_OBS, "smica", obs_path)
    if masked:
        mask = np.ones(npix)
        mask[: npix // 5] = 0.0
        mask_path = tmp_path / "mask.fits"
        k1.rm.hp.write_map(mask_path, mask, overwrite=True, dtype=np.float64)
        monkeypatch.setattr(k1, "MASK_HI", mask_path)


def _cfg(masked):
    return PrecisionConfig(proc_nside=NSIDE_FIX, lmax=12, masked=masked, inpaint_iters=10)


def test_precision_full_runs_and_is_v2_labelled(monkeypatch, tmp_path):
    _patch_precision_inputs(monkeypatch, tmp_path, masked=False)
    cmb = _write_sims(tmp_path / "cmb", 5, 50.0, "cmb", 11)
    noise = _write_sims(tmp_path / "noise", 3, 25.0, "noise", 12)
    rep = k1.build_e2e_full_report(cmb, noise, "smica", 5, precision=_cfg(False), jobs=1)
    assert rep["config"]["statistic_set"] == "v2_precision"
    assert rep["config"]["lmax"] == 12 and rep["config"]["proc_nside"] == NSIDE_FIX
    assert rep["config"]["null_model"] == "ffp10_cmb_plus_noise_e2e_v2_precision"
    assert rep["blocker_closes"] == "BLOCKED_MISSING_PR4_E2E_ACCESS"
    assert 0.0 < rep["result"]["global_p"] <= 1.0
    assert rep["family_identification"] is False and rep["native_solver_result"] is False


def test_precision_full_parallel_equals_serial(monkeypatch, tmp_path):
    _patch_precision_inputs(monkeypatch, tmp_path, masked=False)
    cmb = _write_sims(tmp_path / "cmb", 6, 50.0, "cmb", 21)
    noise = _write_sims(tmp_path / "noise", 3, 25.0, "noise", 22)
    serial = k1.build_e2e_full_report(cmb, noise, "smica", 6, precision=_cfg(False), jobs=1)
    par = k1.build_e2e_full_report(cmb, noise, "smica", 6, precision=_cfg(False), jobs=2)
    # identical results regardless of worker count (deterministic, order-stable)
    assert serial["result"]["global_p"] == par["result"]["global_p"]
    assert serial["result"]["local_p"] == par["result"]["local_p"]


def test_precision_masked_full_runs_with_inpaint(monkeypatch, tmp_path):
    _patch_precision_inputs(monkeypatch, tmp_path, masked=True)
    cmb = _write_sims(tmp_path / "cmb", 4, 50.0, "cmb", 31)
    noise = _write_sims(tmp_path / "noise", 4, 25.0, "noise", 32)
    rep = k1.build_e2e_full_report(cmb, noise, "smica", 4, precision=_cfg(True), jobs=1)
    assert rep["config"]["masked"] is True
    assert rep["config"]["mask_handling"].startswith("diffuse_inpaint")
    assert 0.0 < rep["result"]["global_p"] <= 1.0


def test_precision_noise_only_stays_measured_partial(monkeypatch, tmp_path):
    _patch_precision_inputs(monkeypatch, tmp_path, masked=False)
    noise = _write_sims(tmp_path / "noise", 5, 25.0, "noise", 41)
    rep = k1.build_e2e_noise_report(noise, "smica", 5, precision=_cfg(False), jobs=2)
    assert rep["config"]["statistic_set"] == "v2_precision"
    assert rep["config"]["null_model"] == "lambdacdm_signal_plus_real_instrument_noise_v2_precision"
    assert rep["blocker_partial"] == "BLOCKED_MISSING_PR4_E2E_ACCESS"   # still partial
    assert 0.0 < rep["result"]["global_p"] <= 1.0
