"""MIO-HJ-05a-lite (W6D7) — masked_sky_caveats tests.

Plan §12.6 required tests:
  * test_f_sky_consistency
  * test_zoa_applied_then_f_sky_less_than_one
"""
from __future__ import annotations

import numpy as np
import pytest

from common.healpix_selection import build_zoa_mask, nside_to_npix
from mio.diagnostics.masked_sky_caveats import (
    BIAS_AMP_CAVEAT,
    SkyCoverageReport,
    apply_bias_amp_caveat,
    as_caveats_list,
    build_report,
)


def test_f_sky_consistency():
    """f_sky_effective == sum(mask) / n_pix_total on a handcrafted mask."""
    nside = 8
    n_pix = nside_to_npix(nside)
    mask = np.zeros(n_pix, dtype=bool)
    mask[: n_pix // 4] = True

    report = build_report(
        mask,
        nside,
        mask_provenance="handcrafted_quarter_sky",
    )
    assert report.n_pix_total == n_pix
    assert report.n_pix_kept == n_pix // 4
    assert report.f_sky_effective == pytest.approx(0.25)
    assert report.f_sky_effective == report.n_pix_kept / report.n_pix_total


def test_zoa_applied_then_f_sky_less_than_one():
    """ZoA mask with half-angle 15° must strictly reduce f_sky below 1."""
    nside = 16
    mask = build_zoa_mask(
        l_deg=None,
        b_deg=None,
        bcut_deg=15.0,
        nside=nside,
    )
    report = build_report(
        mask,
        nside,
        zoa_half_angle_deg=15.0,
        mask_provenance="galactic_zoa_15deg",
    )
    assert 0.0 < report.f_sky_effective < 1.0
    # Consistency with a naive expectation (|sin b| > sin 15° ≈ 0.2588)
    assert report.f_sky_effective < 0.80


# ---------------------------------------------------------------------------
# Coverage extras
# ---------------------------------------------------------------------------


def test_build_report_frozen():
    report = build_report(
        np.ones(nside_to_npix(4), dtype=bool),
        4,
        mask_provenance="all_sky",
    )
    import dataclasses

    with pytest.raises(dataclasses.FrozenInstanceError):
        report.nside = 8  # type: ignore[misc]


def test_as_caveats_list_round_trip():
    mask = np.ones(nside_to_npix(4), dtype=bool)
    report = build_report(
        mask,
        4,
        zoa_half_angle_deg=10.0,
        mask_provenance="all_sky",
        extra_caveats=["selection_function_uncalibrated"],
    )
    caveats = as_caveats_list(report)
    assert isinstance(caveats, list)
    assert any("f_sky_effective" in c for c in caveats)
    assert any("mask_provenance=all_sky" in c for c in caveats)
    assert "selection_function_uncalibrated" in caveats


def test_mask_shape_validation():
    with pytest.raises(ValueError, match="does not match n_pix"):
        build_report(np.ones(10, dtype=bool), 4, mask_provenance="bad")


def test_report_integrates_with_mio_certificate():
    """Caveats list is directly consumable by build_mio_certificate."""
    from mio.interface.mio_certificate import build_mio_certificate

    mask = build_zoa_mask(l_deg=None, b_deg=None, bcut_deg=10.0, nside=8)
    report = build_report(
        mask,
        8,
        zoa_half_angle_deg=10.0,
        mask_provenance="planck_2018",
    )
    caveats = as_caveats_list(report)
    cert = build_mio_certificate(
        report_type="directional_coherence",
        probe_name="CMB",
        channel="dipole",
        departure_variables={"resultant_R": 0.5},
        adequacy_indicators={"isotropy_p_lt_0p01": False},
        consistency_metrics={"isotropy_pvalue": 0.5},
        domain_caveats=caveats,
        reduction_status="diagnostic-only",
        generated_by="test",
        input_data_hashes=[],
    )
    assert any("f_sky_effective" in c for c in cert.domain_caveats)


def test_zoa_half_angle_zero_covers_full_sky():
    """bcut_deg=0 → trivially-masked (keep |b|>=0 ⇒ all kept)."""
    nside = 4
    mask = build_zoa_mask(l_deg=None, b_deg=None, bcut_deg=0.0, nside=nside)
    report = build_report(
        mask,
        nside,
        zoa_half_angle_deg=0.0,
        mask_provenance="trivial",
    )
    assert report.f_sky_effective == pytest.approx(1.0)


# ---------------------------------------------------------------------------
# W12D2 — W5 APPLY-BIAS-AMP carry-forward hardening.
# ---------------------------------------------------------------------------


def test_bias_amp_caveat_constant_mentions_w5_tag():
    """The canonical caveat must cite the W5 audit tag so grep-based
    audits can trace the carry-forward across future refactors."""
    assert isinstance(BIAS_AMP_CAVEAT, str)
    assert BIAS_AMP_CAVEAT  # non-empty
    assert "APPLY-BIAS-AMP" in BIAS_AMP_CAVEAT
    assert "amp_true" in BIAS_AMP_CAVEAT
    assert "amp_meas" in BIAS_AMP_CAVEAT


def test_apply_bias_amp_caveat_returns_constant():
    """Helper mirrors the module constant (spoiler: so users can import
    either entry point)."""
    assert apply_bias_amp_caveat() == BIAS_AMP_CAVEAT


def test_build_report_excludes_bias_amp_caveat_by_default():
    """Default behaviour preserves the pre-W12 call surface verbatim."""
    mask = np.ones(nside_to_npix(4), dtype=bool)
    report = build_report(mask, 4, mask_provenance="all_sky")
    assert BIAS_AMP_CAVEAT not in report.caveats
    # And the legacy-shape assertions still hold.
    assert any("f_sky_effective" in c for c in report.caveats)
    assert any("mask_provenance=all_sky" in c for c in report.caveats)


def test_build_report_includes_bias_amp_caveat_when_flag_set():
    """Flipping ``mock_bias_applied=True`` appends the canonical caveat."""
    mask = np.ones(nside_to_npix(4), dtype=bool)
    report = build_report(
        mask, 4, mask_provenance="all_sky", mock_bias_applied=True,
    )
    assert BIAS_AMP_CAVEAT in report.caveats
    # Ensure the caveat propagates through as_caveats_list (MIO cert path).
    caveats = as_caveats_list(report)
    assert BIAS_AMP_CAVEAT in caveats
    # And the auto-caveats are still present — the flag is additive.
    assert any("f_sky_effective" in c for c in caveats)
