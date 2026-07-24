"""Unit tests for the v2 precision low-ell statistics (htt/obsstat/lowell_precision.py).

Verifies the three precision levers behave correctly and deterministically:
mask downgrade + threshold, diffuse inpainting (deterministic, leaves kept pixels
fixed, converges), and that precision_map_statistics returns the six v1 keys at the
configured NSIDE/lmax under both full-sky and masked+inpainted modes.
"""
from __future__ import annotations

import numpy as np
import pytest

hp = pytest.importorskip(
    "healpy",
    reason=(
        "optional dependency 'healpy' not installed; "
        "install it to run tests marked requires_healpy"
    ),
)
pytestmark = pytest.mark.requires_healpy

from htt.obsstat.lowell_precision import (
    PrecisionConfig, downgrade_mask, diffuse_inpaint, precision_map_statistics,
)

SIX_KEYS = {"s_one_half", "parity_even_over_odd_ratio", "parity_asymmetry",
            "planarity_mean", "qo_axis_alignment_deg", "axis_to_cmb_dipole_deg"}


def _rand_map(nside, seed):
    return np.random.default_rng(seed).normal(scale=30.0, size=hp.nside2npix(nside))


def test_downgrade_mask_thresholds_to_keep_boolean():
    nside_hi = 64
    mask_hi = np.ones(hp.nside2npix(nside_hi))
    mask_hi[: hp.nside2npix(nside_hi) // 2] = 0.0          # mask half the sky
    keep = downgrade_mask(mask_hi, nside_out=16, keep_threshold=0.9)
    assert keep.dtype == bool
    assert keep.size == hp.nside2npix(16)
    assert 0 < keep.sum() < keep.size                      # partial coverage retained


def test_diffuse_inpaint_holds_kept_pixels_and_is_deterministic():
    nside = 16
    m = _rand_map(nside, 1)
    keep = np.ones(m.size, dtype=bool)
    keep[: m.size // 4] = False                            # mask a quarter
    out1 = diffuse_inpaint(m, keep, n_iter=30)
    out2 = diffuse_inpaint(m, keep, n_iter=30)
    np.testing.assert_array_equal(out1, out2)              # deterministic
    np.testing.assert_array_equal(out1[keep], m[keep])     # kept pixels untouched
    assert np.isfinite(out1).all()
    # inpainted values lie within the kept-sky range (diffusion cannot overshoot)
    assert out1[~keep].min() >= m[keep].min() - 1e-9
    assert out1[~keep].max() <= m[keep].max() + 1e-9


def test_diffuse_inpaint_noop_on_full_sky():
    m = _rand_map(16, 2)
    keep = np.ones(m.size, dtype=bool)
    np.testing.assert_array_equal(diffuse_inpaint(m, keep, 40), m)


def test_precision_statistics_full_sky_returns_six_keys():
    cfg = PrecisionConfig(proc_nside=16, lmax=12, masked=False)
    m = _rand_map(16, 3)
    apex = np.array([0.0, 0.0, 1.0])
    stats = precision_map_statistics(m, apex, cfg)
    assert set(stats) == SIX_KEYS
    assert all(np.isfinite(v) for v in stats.values())
    assert 0.0 <= stats["qo_axis_alignment_deg"] <= 90.0
    assert 0.0 <= stats["axis_to_cmb_dipole_deg"] <= 90.0


def test_precision_statistics_masked_requires_mask_and_runs():
    cfg = PrecisionConfig(proc_nside=16, lmax=12, masked=True, inpaint_iters=20)
    m = _rand_map(16, 4)
    apex = np.array([0.0, 0.0, 1.0])
    with pytest.raises(ValueError):
        precision_map_statistics(m, apex, cfg)             # masked=True needs keep_mask
    keep = np.ones(m.size, dtype=bool)
    keep[: m.size // 5] = False
    stats = precision_map_statistics(m, apex, cfg, keep_mask=keep)
    assert set(stats) == SIX_KEYS
    assert all(np.isfinite(v) for v in stats.values())


def test_precision_statistics_rejects_wrong_nside():
    cfg = PrecisionConfig(proc_nside=64, lmax=20, masked=False)
    with pytest.raises(ValueError):
        precision_map_statistics(_rand_map(16, 5), np.array([0, 0, 1.0]), cfg)


def test_config_records_reregistration_and_qo_invariance():
    cfg = PrecisionConfig()
    d = cfg.as_dict()
    assert d["statistic_set"] == "v2_precision"
    assert d["proc_nside"] == 64 and d["lmax"] == 30
    assert d["alignment_stats_ell"] == [2, 3]              # Q-O unaffected by lmax
    assert d["mask_handling"].startswith("diffuse_inpaint")


def test_lmax_changes_ell_summed_stats_but_not_qo():
    # raising lmax must move the ell-summed stats (more multipoles) a lot while leaving
    # the quadrupole-octupole alignment (intrinsically ell=2,3) statistic essentially
    # unchanged. (Q-O is not bit-identical because map2alm(iter=3) refines the ell=2,3
    # coefficients within the full band, so it shifts by ~1e-3 deg -- far below any
    # statistical relevance -- not by the large amounts the ell-summed stats move.)
    m = _rand_map(64, 6)
    apex = np.array([0.0, 0.0, 1.0])
    s8 = precision_map_statistics(m, apex, PrecisionConfig(proc_nside=64, lmax=8, masked=False))
    s30 = precision_map_statistics(m, apex, PrecisionConfig(proc_nside=64, lmax=30, masked=False))
    assert abs(s8["parity_asymmetry"] - s30["parity_asymmetry"]) > 1e-3      # ell-summed: moves
    assert abs(s8["planarity_mean"] - s30["planarity_mean"]) > 1e-3
    assert s8["qo_axis_alignment_deg"] == pytest.approx(s30["qo_axis_alignment_deg"], abs=0.5)
