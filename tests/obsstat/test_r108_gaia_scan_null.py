"""Fast synthetic tests of scripts/r108/gaia_scan_null.py helpers (no data files)."""
import healpy as hp
import numpy as np

from scripts.r108 import gaia_scan_null as sn


def test_block_ids_respect_segments_and_length():
    seg = np.array([1, 0, 0, 0, 0, 1, 0, 0], bool)
    ids = sn.block_ids(seg, 2)
    assert list(ids) == [0, 0, 1, 1, 2, 3, 3, 4]
    assert list(sn.block_ids(seg, 1)) == list(range(8))


def test_pixel_excess_is_unbiased_for_noise_and_detects_offsets():
    rng = np.random.default_rng(11)
    n = 200_000
    npix = hp.nside2npix(sn.CAL_NSIDE)
    pix = rng.integers(0, npix, n)
    e = rng.uniform(0.5, 1.5, n)
    y = rng.normal(size=(n, 2)) * e[:, None]
    m, se, _ = sn.pixel_excess(pix, y, e, e)
    assert abs(m) < 4 * se
    off = rng.normal(0, 0.05, (npix, 2))
    m2, se2, _ = sn.pixel_excess(pix, y + off[pix], e, e)
    assert abs(m2 - np.mean((off ** 2).sum(axis=1))) < 4 * se2
    split = rng.random(n) < 0.5
    m3, se3, _ = sn.pixel_excess(pix, y, e, e, split)
    assert abs(m3) < 4 * se3
    assert abs(sn.pixel_power_noise_free(pix, off[pix], e, e) - np.mean((off ** 2).sum(axis=1))) < 1e-12


def test_coupling_and_reference():
    G = np.array([18.0, 19.0, 20.0, 21.0])
    c = np.array([0.2, 0.4, 0.6, 0.8])
    ref = sn.coupling_reference(G, c)
    assert np.allclose(sn.coupling("blind", G, c, ref), 1.0)
    assert abs(np.median(sn.coupling("colour", G, c, ref))) < 1e-12
    assert np.allclose(np.diff(sn.coupling("gmag", G, c, ref)), 1.0 / ref["G_iqr"])


def test_pixel_solver_inverts_and_flags_singular():
    rng = np.random.default_rng(5)
    a = rng.normal(size=(30, 5))
    N = a.T @ a
    flat = np.stack([N[np.triu_indices(5)], np.zeros(15)])
    inv, ok = sn.pixel_solver(flat)
    assert ok.tolist() == [True, False]
    assert np.allclose(inv[0] @ N, np.eye(5), atol=1e-10) and np.all(inv[1] == 0)


def test_pixel_cross_is_insensitive_to_error_misscaling():
    rng = np.random.default_rng(12)
    n = 300_000
    npix = hp.nside2npix(sn.CAL_NSIDE)
    pix = rng.integers(0, npix, n)
    e = rng.uniform(0.5, 1.5, n)
    y = rng.normal(size=(n, 2)) * (1.1 * e)[:, None]  # catalogue errors underestimated by 10%
    half = rng.random(n) < 0.5
    m_auto, se_auto, _ = sn.pixel_excess(pix, y, e, e)
    m_x, se_x, _ = sn.pixel_cross(pix, y, e, e, half)
    assert m_auto > 5 * se_auto  # auto power is biased by the mis-scaled errors
    assert abs(m_x) < 4 * se_x
    off = rng.normal(0, 0.05, (npix, 2))
    m2, se2, _ = sn.pixel_cross(pix, y + off[pix], e, e, half)
    assert abs(m2 - np.mean((off ** 2).sum(axis=1))) < 4 * se2
    split = rng.random(n) < 0.5
    m3, se3, _ = sn.pixel_cross(pix, y, e, e, half, split)
    assert abs(m3) < 4 * se3


def test_sysfield_sparse_aggregation_equals_direct_sum():
    rng = np.random.default_rng(21)
    n, npix = 3000, hp.nside2npix(1)
    a = rng.normal(size=(n, 5)).astype(np.float32)
    pix = rng.integers(0, npix, n).astype(np.int32)
    seg = np.zeros(n, bool)
    seg[[0, 700, 1900]] = True
    N = np.zeros((npix, 15))
    for p in range(npix):
        m = pix == p
        A = a[m].astype(float)
        N[p] = (A.T @ A)[np.triu_indices(5)]
    scan = {"N": N, "streams": [{"pix": pix, "a": a, "segment_start": seg}]}
    for block in (1, 7, 60):
        f = sn.SysField(scan, block)
        v1 = f.draw(np.random.default_rng(5))
        v2 = f.draw_direct(np.random.default_rng(5), scan)
        assert np.allclose(v1, v2, rtol=1e-10, atol=1e-12)


def test_receipt_script_version_groups():
    new = {"provenance": {"main_script": {"sha256": "ab" * 32}, "module_sha256": {"scripts/r108/gaia_estimator.py": "cd"}}}
    assert sn.receipt_script_version("sys_blind_tau10", new) == {"group": "identified", "gaia_scan_null_py_sha256": "ab" * 32,
                                                                 "gaia_estimator_py_sha256": "cd"}
    old = {"provenance": {"module_sha256": {}}, "amplitude_from": None}
    assert sn.receipt_script_version("sys_gmag_tau600", old)["group"].startswith("pre_fix_A")
    assert sn.receipt_script_version("sys_gmag_tau10", dict(old, amplitude_from="x"))["group"].startswith("pre_fix_B")
    assert sn.receipt_script_version("noise_catalogue", old)["group"].startswith("pre_fix_noise_kind")


def test_replay_check_bit_identity(tmp_path):
    import json

    from scripts.r108.common import sha256_file

    stored = tmp_path / "stored.npz"
    rng = np.random.default_rng(1)
    a, q = rng.normal(size=(5, 3)), np.full(5, np.nan)
    np.savez_compressed(stored, a=a, sys_q=q)
    rd = tmp_path / "replay"
    rd.mkdir()
    rnpz = rd / "scan_null_k.npz"
    np.savez_compressed(rnpz, a=a[:2], sys_q=q[:2])
    (rd / "scan_null_k.json").write_text(json.dumps({"npz_sha256": sha256_file(rnpz), "seed": 1,
                                                     "amplitude_mas_per_yr_per_unit_e": 0.0,
                                                     "provenance": {"main_script": {"sha256": "ef"}}}))
    r = sn.replay_check(stored, rd, "k")
    assert r["status"] == "BIT_IDENTICAL" and r["draws_compared"] == 2 and r["replay_gaia_scan_null_py_sha256"] == "ef"
    np.savez_compressed(rnpz, a=a[:2] + 1e-15, sys_q=q[:2])
    (rd / "scan_null_k.json").write_text(json.dumps({"npz_sha256": sha256_file(rnpz), "seed": 1,
                                                     "amplitude_mas_per_yr_per_unit_e": 0.0, "provenance": {}}))
    r = sn.replay_check(stored, rd, "k")
    assert r["status"] == "MISMATCH" and r["mismatched_arrays"] == ["a"]
    assert sn.replay_check(stored, rd, "missing")["status"] == "NOT_RUN"
