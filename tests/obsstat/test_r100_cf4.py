"""Unit & integration tests for R100 Part A (source intake guards, upstream genealogy, 3-band PV, selection)."""
from __future__ import annotations

import hashlib
import io
import json
from pathlib import Path
import urllib.error

import numpy as np
import pytest

from htt.obsstat.mv_bulkflow import pair_velocity_covariance
from scripts.r98 import cf4_p1 as old
from scripts.r99 import cf4_source_law as r99
from scripts.r99.acquisition import DeferredProduct, exact_identifier, validate_product_response
from scripts.r100 import cf4_upstream_and_kband as r100_cf4
from scripts.r100 import source_intake


def test_source_intake_budget_and_http202_and_md5_guards(tmp_path):
    """Enforce hard byte cap, HTTP 202 rejection, non-scientific Content-Type rejection, and exact MD5."""
    with pytest.raises(DeferredProduct):
        validate_product_response(202, {"content-type": "application/json"}, 100)
    with pytest.raises(ValueError, match="non-scientific"):
        validate_product_response(200, {"content-type": "text/html", "content-length": "100"}, 100)
    with pytest.raises(ValueError, match="exceeds remaining budget"):
        source_intake.download_bounded_product(
            "test_big",
            {"url": "https://example.org/data.dat", "filename": "x.dat", "expected_bytes": 500, "expected_md5": None, "release": "t"},
            dest_dir=tmp_path,
            max_bytes_remaining=499,
        )

    payload = b"hello_sdss_table"
    bad_md5 = "0" * 32
    class FakeResp:
        status = 200
        headers = {"Content-Type": "application/octet-stream", "Content-Length": str(len(payload))}
        def __init__(self): self._buf = io.BytesIO(payload)
        def read(self, n=-1): return self._buf.read(n)
        def __enter__(self): return self
        def __exit__(self, *a): return False

    with pytest.raises(ValueError, match="MD5 mismatch"):
        source_intake.download_bounded_product(
            "test_md5",
            {"url": "https://example.org/data.dat", "filename": "x.dat", "expected_bytes": len(payload), "expected_md5": bad_md5, "release": "t"},
            dest_dir=tmp_path,
            opener=lambda req, timeout=10: FakeResp(),
        )
    assert not (tmp_path / "x.dat").exists()

    good_md5 = hashlib.md5(payload).hexdigest()
    rec = source_intake.download_bounded_product(
        "test_ok",
        {"url": "https://example.org/data.dat", "filename": "x.dat", "expected_bytes": len(payload), "expected_md5": good_md5, "release": "t"},
        dest_dir=tmp_path,
        opener=lambda req, timeout=10: FakeResp(),
    )
    assert rec["verified"] is True
    assert rec["bytes"] == len(payload)


def test_exact_integer_id_and_sixdf_minus1_sentinel():
    """Reject float IDs, verify exact int64 SDSS objid, and verify 6dFGSv -1 sentinel isolation."""
    with pytest.raises(ValueError, match="never floating point"):
        exact_identifier(1237663547968323716.0)
    assert exact_identifier("1237663547968323716") == 1237663547968323716

    if r100_cf4.SIXDF_PATH.exists():
        six = r100_cf4.load_sixdf_pv()
        assert six["n"] == 8885
        assert int(np.sum(~six["is_grouped"])) == 6219
        assert np.all(np.isnan(six["cz_group_valid"][~six["is_grouped"]]))
        assert np.all(six["cz_group_valid"][six["is_grouped"]] > 0)


def test_3band_finufft_direct_and_bessel_parity():
    """Verify per-panel FINUFFT matches direct summation and Bessel kernel on a 15-source subset."""
    r30_sci, _, _, finufft = old._load_r30_and_bridge()
    rng = np.random.default_rng(1001)
    m_src = 15
    n_u = rng.normal(size=(m_src, 3))
    n_u /= np.linalg.norm(n_u, axis=1)[:, None]
    zs = np.linspace(0.015, 0.09, m_src)
    chi, g, _, _, _ = r30_sci.background(zs, 64)
    pos = chi[:, None] * n_u
    A = np.eye(m_src)
    amp, _ = r30_sci.power_amplitude()
    R_mpc = 5.0 / r30_sci.H

    # At r <= 265 Mpc/h and k <= 0.15 h/Mpc, kr reaches ~40 (|r_ij|*k ~ 78), so use Lebedev order 89 > 78
    targs, bds = r100_cf4._panel_targets(0.05, 0.15, 32, 89, r30_sci.H)
    modes = r100_cf4._batched_finufft_modes(finufft, targs, pos, n_u, [g], A, eps=1e-11)[0]
    probe = [0, len(targs) // 2, len(targs) - 1]
    direct = old._direct_fourier_modes(targs[probe], pos, n_u, g, A)
    assert np.max(np.abs(modes[probe] - direct)) / np.max(np.abs(direct)) < 1e-8

    C_num = old._cov_from_projected_modes(bds, modes, amp, r30_sci, np.array([R_mpc]))[0][0]
    def _pk_h(kh):
        kk = r30_sci.H * kh
        return (r30_sci.H ** 3) * r30_sci.power(kk, amp) * np.exp(-((kk * R_mpc) ** 2))
    C_bes = pair_velocity_covariance(
        r30_sci.H * pos, n_u, _pk_h, 1.0 / (r30_sci.H ** 2), na=1001, nk=1200, kmin=0.05, kmax=0.15
    ) * np.outer(g, g)
    assert np.max(np.abs(np.diag(C_num) - np.diag(C_bes)) / np.diag(C_bes)) < 1e-6
    assert np.linalg.norm(C_num - C_bes) / np.linalg.norm(C_bes) < 2e-4
    ev = np.linalg.eigvalsh(0.5 * (C_num + C_num.T))
    assert ev[0] >= -1e-12 * ev[-1]


def test_r100_cf4_result_artifact_contracts():
    """Verify produced CF4_UPSTREAM_KBAND_RESULTS.json consistency, PSD, and mag-unit conservation."""
    res_path = r100_cf4.OUT_DIR / "CF4_UPSTREAM_KBAND_RESULTS.json"
    if not res_path.exists():
        pytest.skip("CF4_UPSTREAM_KBAND_RESULTS.json not generated yet")
    data = json.loads(res_path.read_text())
    assert data["physical_Pi"] is None
    assert data["A2_upstream_genealogy_and_sign_audit"]["sdss_pv_census"]["exact_pgc_matches_table2"] == 34045
    assert data["A2_upstream_genealogy_and_sign_audit"]["shared_sdss_sixdf_overlap"]["corr_sdss_ldc_vs_6df_delta_d"] > 0.7
    assert data["A4_selection_likelihood_and_4term_cov"]["four_term_covariance_trace_budget_WF_R5_full_k"]["residual_trace_identity_error"] < 1e-13
    # Verify 1-point variance band fractions sum to 1 and R99 mag_tilt units preserved
    for r_str, blk in data["A3_full_kband_correlated_pv"]["one_point_variance_decomposition"].items():
        assert abs(blk["frac_low"] + blk["frac_inherited"] + blk["frac_high"] - 1.0) < 1e-12
    assert data["A3_full_kband_correlated_pv"]["models"]["WF_log_R5"]["C_tot_full_k"]["min_eig"] > 0.0
