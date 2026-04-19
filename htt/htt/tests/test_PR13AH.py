"""HTT-P0-AH regression (INDEPENDENT_TRACKS_PLAN.md §2.4)."""
from __future__ import annotations

import numpy as np
import pytest

from htt.PR13AH_observables_reintegration import (
    ChannelSummary,
    reintegrate_observables,
)


def _catalog(n=200, seed=0) -> dict:
    rng = np.random.default_rng(seed)
    l = rng.uniform(0, 360, n)
    b = rng.uniform(-90, 90, n)
    w = rng.uniform(0.5, 1.5, n)
    return {"l": l, "b": b, "w": w}


def test_four_summary_consistency():
    """All four channels must be produced and be ChannelSummary instances."""
    out = reintegrate_observables(_catalog(), {"zoa_half_angle_deg": 20.0})
    expected_keys = {
        "raw_summary",
        "zoa_masked_summary",
        "selection_aware_summary",
        "mock_calibrated_summary",
    }
    assert set(out) == expected_keys
    for k in expected_keys:
        assert isinstance(out[k], ChannelSummary)


def test_raw_and_zoa_are_diagnostic_only():
    out = reintegrate_observables(_catalog(), {"zoa_half_angle_deg": 20.0})
    assert out["raw_summary"].diagnostic_only is True
    assert out["zoa_masked_summary"].diagnostic_only is True


def test_selection_and_mock_are_production_tracks():
    out = reintegrate_observables(_catalog(), {"zoa_half_angle_deg": 20.0})
    assert out["selection_aware_summary"].diagnostic_only is False
    assert out["mock_calibrated_summary"].diagnostic_only is False


def test_mock_calibration_flagged_pending_until_common_f():
    out = reintegrate_observables(_catalog(), {"zoa_half_angle_deg": 20.0})
    assert out["mock_calibrated_summary"].calibration_pending is True
    assert out["selection_aware_summary"].calibration_pending is False


def test_resultant_R_is_in_unit_interval():
    out = reintegrate_observables(_catalog(), {"zoa_half_angle_deg": 20.0})
    for k, s in out.items():
        assert 0.0 <= s.resultant_R <= 1.0 + 1e-12, f"{k}: R={s.resultant_R}"


def test_empty_zoa_mask_marked_empty():
    """Catalogue entirely inside the ZoA — masked channels must report empty."""
    cat = {
        "l": np.array([10.0, 20.0, 30.0]),
        "b": np.array([5.0, -3.0, 1.0]),  # all |b| < 20
        "w": np.array([1.0, 1.0, 1.0]),
    }
    out = reintegrate_observables(cat, {"zoa_half_angle_deg": 20.0})
    assert out["zoa_masked_summary"].meta.get("empty") is True
    assert out["selection_aware_summary"].meta.get("empty") is True


def test_selection_modes_are_disjoint_labels():
    """The four channels advertise distinct selection_mode strings."""
    out = reintegrate_observables(_catalog(), {"zoa_half_angle_deg": 20.0})
    modes = {s.selection_mode for s in out.values()}
    assert modes == {"none", "zoa_hard_cut", "angular_completeness", "mock_calibrated"}


def test_raw_summary_uses_sphere_correct_mean():
    """R1 regression (AUDIT_PHASE_IND_TRACKS_W1W2): PR13AH must use the
    unit-vector spherical mean from COMMON-A, not a naive longitude average.

    Extreme longitudes (0°, 1°, 358°, 359° at b=0) have naive mean ≈ 179.5°
    but sphere-correct mean near 359.5°/0.0°.
    """
    cat = {
        "l": np.array([0.0, 1.0, 358.0, 359.0]),
        "b": np.array([0.0, 0.0, 0.0, 0.0]),
        "w": np.array([1.0, 1.0, 1.0, 1.0]),
    }
    out = reintegrate_observables(cat, {"zoa_half_angle_deg": 0.0})
    raw = out["raw_summary"]
    assert raw.resultant_R > 0.99, raw.resultant_R
    # Sphere-correct mean sits near 0°/360°, not near 180°.
    dist_to_zero = min(raw.l_deg, 360.0 - raw.l_deg)
    assert dist_to_zero < 1.0, f"expected near 0°, got {raw.l_deg}"


# ---------------------------------------------------------------------------
# PR13AH-v2-WIRE — mock bias correction injection (v1.1 PATCH-02 resolved).
# ---------------------------------------------------------------------------

def _injected_mock_report(V_true, V_residual_vec, n_mock=40):
    """Build a tiny InjectedMockReport whose mean recovered vector is
    ``V_true + V_residual_vec`` (so the residual ``E[V_hat] − V_true``
    equals ``V_residual_vec`` exactly).
    """
    from common.mock_calibration import InjectedMockReport

    V_true_arr = np.asarray(V_true, dtype=float)
    V_residual = np.asarray(V_residual_vec, dtype=float)
    recovered = np.tile(V_true_arr + V_residual, (n_mock, 1))
    return InjectedMockReport(
        recovered_V_samples=recovered,
        amp_bias_fraction=0.02,
        direction_bias_deg=3.5,
        amp_spread_fractional=0.1,
        n_mock=n_mock,
        config={"V_true": tuple(V_true_arr.tolist())},
    )


def test_mock_calibration_wired_when_bias_provided():
    """When mock_bias_correction is supplied, calibration_pending flips False."""
    cat = _catalog()
    report = _injected_mock_report(
        V_true=(1.0, 0.0, 0.0),
        V_residual_vec=(0.0, 0.1, 0.0),  # small directional bias
    )
    out = reintegrate_observables(
        cat,
        {"zoa_half_angle_deg": 20.0},
        mock_bias_correction=report,
    )
    mock = out["mock_calibrated_summary"]
    assert mock.calibration_pending is False
    assert mock.meta["bias_amp_corrected_fraction"] == pytest.approx(0.02)
    assert mock.meta["bias_direction_corrected_deg"] == pytest.approx(3.5)
    assert mock.meta["n_mock"] == 40


def test_mock_calibration_direction_shift_matches_bias():
    """The mock-calibrated direction must differ from the selection-aware
    direction when a non-zero bias residual is supplied, and the shift
    must be in the opposite direction from the mock residual.
    """
    from common.sky_geometry import lb_to_unitvec

    cat = _catalog()
    # Residual nudges the mean recovered direction *towards* +y. The
    # correction should push the de-biased direction *away* from +y.
    report = _injected_mock_report(
        V_true=(1.0, 0.0, 0.0),
        V_residual_vec=(0.0, 0.2, 0.0),
    )
    out = reintegrate_observables(
        cat,
        {"zoa_half_angle_deg": 20.0},
        mock_bias_correction=report,
    )
    sel = out["selection_aware_summary"]
    mock = out["mock_calibrated_summary"]
    assert (sel.l_deg, sel.b_deg) != (mock.l_deg, mock.b_deg)
    # Projection onto +y should decrease (or at worst not increase) under
    # the residual correction, since the residual vector points +y.
    u_sel = lb_to_unitvec(sel.l_deg, sel.b_deg)
    u_mock = lb_to_unitvec(mock.l_deg, mock.b_deg)
    assert float(u_mock[1]) <= float(u_sel[1]) + 1e-9


def test_mock_calibration_placeholder_preserved_without_bias():
    """Backwards compatibility: omitting mock_bias_correction keeps the
    pending placeholder path (W4 behaviour unchanged).
    """
    out = reintegrate_observables(_catalog(), {"zoa_half_angle_deg": 20.0})
    assert out["mock_calibrated_summary"].calibration_pending is True
