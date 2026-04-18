"""test_htt_to_mio_roundtrip — WS-BOOT-01 (INDEPENDENT_TRACKS_PLAN v1.2 §19.1).

Covers the minimal contract shape required by
`bass_py/htt/htt/integration/to_mio.py` `build_posterior_bundle` and the
G19 hard-separation guard on `PosteriorExportBundle`.
"""
from __future__ import annotations

import dataclasses

import pytest

from workspace.contracts.htt_to_mio import PosteriorExportBundle


def _bundle(**overrides):
    base = dict(
        x_median=0.1,
        x_hpd68=(0.05, 0.15),
        x_hpd95=(0.01, 0.20),
        Q_median=0.3,
        Q_hpd68=(0.2, 0.4),
        Pi_median=0.05,
        Pi_hpd68=(0.02, 0.10),
        ln_B_total=12.3,
        F_median=0.08,
        F_hpd68=(0.06, 0.11),
        n_live=500,
        model_evidences={"FLRW": 0.0, "FLRW_tilt": 12.3},
        model="FLRW_tilt",
    )
    base.update(overrides)
    return PosteriorExportBundle(**base)


def test_posterior_export_bundle_frozen():
    bundle = _bundle()
    with pytest.raises(dataclasses.FrozenInstanceError):
        bundle.x_median = 99.0  # type: ignore[misc]


def test_cross_check_only_enforced():
    with pytest.raises(ValueError, match="cross-check only"):
        _bundle(is_cross_check_only=False)


def test_default_is_cross_check_only():
    bundle = _bundle()
    assert bundle.is_cross_check_only is True


def test_required_field_surface_matches_to_mio_builder():
    fields = {f.name for f in dataclasses.fields(PosteriorExportBundle)}
    required_by_builder = {
        "x_median", "x_hpd68", "x_hpd95",
        "Q_median", "Q_hpd68",
        "Pi_median", "Pi_hpd68",
        "ln_B_total", "model_evidences",
        "F_median", "F_hpd68", "n_live",
    }
    missing = required_by_builder - fields
    assert not missing, f"builder fields missing from contract: {missing}"
