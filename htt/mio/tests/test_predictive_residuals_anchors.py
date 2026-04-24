"""Regression anchors for ``mio.diagnostics.predictive_residuals``
low-level atlas builder (HJ-05).

The shared-schema variant (``build_predictive_residual_atlas_from_shared_schema``)
requires BASS-produced ``HttForwardOutput`` contracts and is exercised by
``test_predictive_residuals_shared_schema.py``. This file targets the
low-level ``build_predictive_residual_atlas(slices=…)`` entry that takes
pre-built ``ResidualChannelSlice`` objects — fully BASS-independent.

A canonical 2-model × 3-channel × 2-ell-bin fixture pins the atlas's
aggregate statistics (worst slice selection, mean RMS, reference
forwarding). Any drift in the tie-breaking order, the aggregation math,
or the frozen-dataclass shape will fire here.
"""
from __future__ import annotations

import dataclasses

import pytest

from mio.diagnostics.predictive_residuals import (
    PredictiveResidualAtlas,
    ResidualChannelSlice,
    build_predictive_residual_atlas,
)


# ─── Canonical fixture ────────────────────────────────────────────────
# 2 models (FLRW_tilt baseline vs BI_tilt candidate), 3 spectrum channels
# (TT/TE/EE), 2 ell bins (low-ell 2–30 covering Sachs-Wolfe + early ISW,
# acoustic 30–200). Residuals pattern: BI_tilt has a conspicuous excess
# at low-ell TT (max_abs = 60 μK²), which the atlas must surface as the
# "worst" slice.
_FIXTURE_SLICES = [
    ResidualChannelSlice("FLRW_tilt", "TT", 2,  30,  rms_residual=10.0, max_abs_residual=25.0, n_modes=29),
    ResidualChannelSlice("FLRW_tilt", "TT", 30, 200, rms_residual=15.0, max_abs_residual=40.0, n_modes=170),
    ResidualChannelSlice("FLRW_tilt", "EE", 2,  30,  rms_residual= 2.0, max_abs_residual= 8.0, n_modes=29),
    ResidualChannelSlice("FLRW_tilt", "EE", 30, 200, rms_residual= 4.0, max_abs_residual=12.0, n_modes=170),
    ResidualChannelSlice("FLRW_tilt", "TE", 2,  30,  rms_residual= 5.0, max_abs_residual=15.0, n_modes=29),
    ResidualChannelSlice("FLRW_tilt", "TE", 30, 200, rms_residual= 7.0, max_abs_residual=20.0, n_modes=170),
    ResidualChannelSlice("BI_tilt",   "TT", 2,  30,  rms_residual=25.0, max_abs_residual=60.0, n_modes=29),
    ResidualChannelSlice("BI_tilt",   "TT", 30, 200, rms_residual=18.0, max_abs_residual=50.0, n_modes=170),
    ResidualChannelSlice("BI_tilt",   "EE", 2,  30,  rms_residual= 6.0, max_abs_residual=18.0, n_modes=29),
    ResidualChannelSlice("BI_tilt",   "EE", 30, 200, rms_residual= 8.0, max_abs_residual=22.0, n_modes=170),
    ResidualChannelSlice("BI_tilt",   "TE", 2,  30,  rms_residual=10.0, max_abs_residual=28.0, n_modes=29),
    ResidualChannelSlice("BI_tilt",   "TE", 30, 200, rms_residual=12.0, max_abs_residual=33.0, n_modes=170),
]
_N_SLICES = 12
_WORST_MODEL = "BI_tilt"
_WORST_CHANNEL = "TT"
_WORST_MAX_ABS = 60.0
_MEAN_RMS = sum(s.rms_residual for s in _FIXTURE_SLICES) / len(_FIXTURE_SLICES)
# computed directly = 10.166666666666666


# ─── 1. Slice construction invariants ─────────────────────────────────
def test_slice_rejects_inverted_ell_range():
    """``ell_max < ell_min`` must fail at construction, not propagate."""
    with pytest.raises(ValueError, match="ell_max"):
        ResidualChannelSlice(
            "bad", "TT", ell_min=100, ell_max=10,
            rms_residual=1.0, max_abs_residual=2.0, n_modes=1,
        )


def test_slice_rejects_nonpositive_n_modes():
    with pytest.raises(ValueError, match="n_modes"):
        ResidualChannelSlice(
            "bad", "TT", 2, 30,
            rms_residual=1.0, max_abs_residual=2.0, n_modes=0,
        )


# ─── 2. Atlas aggregation pinned ──────────────────────────────────────
def test_atlas_n_slices_pinned():
    atlas = build_predictive_residual_atlas(_FIXTURE_SLICES)
    assert len(atlas.slices) == _N_SLICES


def test_atlas_worst_slice_selection_pinned():
    """The worst slice is the max ``abs(max_abs_residual)`` with stable tiebreak.

    Tie rule: ``(abs(max_abs_residual), model_label, channel)`` — alphabetical
    on model then channel. Hardcoded here so any refactor that reorders the
    tiebreak will fire.
    """
    atlas = build_predictive_residual_atlas(_FIXTURE_SLICES)
    assert atlas.worst_model_label == _WORST_MODEL
    assert atlas.worst_channel == _WORST_CHANNEL
    assert atlas.worst_max_abs_residual == pytest.approx(_WORST_MAX_ABS, abs=1e-12)


def test_atlas_mean_rms_pinned():
    """Mean RMS across all slices is pinned to float precision."""
    atlas = build_predictive_residual_atlas(_FIXTURE_SLICES)
    assert atlas.mean_rms_residual == pytest.approx(_MEAN_RMS, abs=1e-12)
    # Sanity: the computation is an unweighted mean over all slices
    expected = sum(s.rms_residual for s in _FIXTURE_SLICES) / _N_SLICES
    assert atlas.mean_rms_residual == pytest.approx(expected, abs=1e-12)


def test_atlas_refs_forwarded():
    atlas = build_predictive_residual_atlas(
        _FIXTURE_SLICES,
        atlas_ref="atlas.ver2.test.canonical",
        covariance_ref="cov.ver2.test.canonical",
    )
    assert atlas.atlas_ref == "atlas.ver2.test.canonical"
    assert atlas.covariance_ref == "cov.ver2.test.canonical"


def test_atlas_refs_none_by_default():
    atlas = build_predictive_residual_atlas(_FIXTURE_SLICES)
    assert atlas.atlas_ref is None
    assert atlas.covariance_ref is None


def test_atlas_rejects_empty_slices():
    with pytest.raises(ValueError, match="at least one"):
        build_predictive_residual_atlas([])


# ─── 3. Tiebreak determinism ──────────────────────────────────────────
def test_atlas_tiebreak_is_stable_for_equal_max_abs():
    """When two slices share the same max_abs, the ``max``-based key picks
    the lexicographically *later* ``(model_label, channel)`` tuple.

    Anchors the current ``builder`` behaviour (``max(..., key=(abs_max,
    model_label, channel))``). If the tie rule ever flips to "alphabetically
    first wins" (e.g. switched to ``min`` or a reversed sort), this test
    fires.
    """
    tied = [
        ResidualChannelSlice(
            "ZModel", "TT", 2, 30,
            rms_residual=10.0, max_abs_residual=100.0, n_modes=29,
        ),
        ResidualChannelSlice(
            "AModel", "TT", 2, 30,
            rms_residual=10.0, max_abs_residual=100.0, n_modes=29,
        ),
    ]
    atlas = build_predictive_residual_atlas(tied)
    assert atlas.worst_model_label == "ZModel"


def test_atlas_tiebreak_alphabetical_on_channel_after_model():
    """Same model + max_abs → channel tiebreak picks lexicographically later."""
    tied = [
        ResidualChannelSlice(
            "M", "TT", 2, 30, rms_residual=1.0, max_abs_residual=50.0, n_modes=29,
        ),
        ResidualChannelSlice(
            "M", "EE", 2, 30, rms_residual=1.0, max_abs_residual=50.0, n_modes=29,
        ),
    ]
    atlas = build_predictive_residual_atlas(tied)
    assert atlas.worst_channel == "TT"


# ─── 4. Structural / dataclass invariants ─────────────────────────────
def test_atlas_is_frozen_dataclass():
    """PredictiveResidualAtlas must be immutable — G19 spirit."""
    atlas = build_predictive_residual_atlas(_FIXTURE_SLICES)
    assert dataclasses.is_dataclass(atlas)
    with pytest.raises(dataclasses.FrozenInstanceError):
        atlas.worst_max_abs_residual = 999.0  # type: ignore[misc]


def test_atlas_slices_are_tuple_not_list():
    """Freezing the slice container prevents accidental in-place mutation."""
    atlas = build_predictive_residual_atlas(_FIXTURE_SLICES)
    assert isinstance(atlas.slices, tuple)


def test_atlas_has_no_posterior_field():
    """G19: no field on PredictiveResidualAtlas contains the posterior token."""
    for f in dataclasses.fields(PredictiveResidualAtlas):
        assert "posterior" not in f.name.lower(), (
            f"PredictiveResidualAtlas.{f.name} violates MIO naming "
            "convention (G19 §10.2bis)."
        )
