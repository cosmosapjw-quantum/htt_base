"""HTT-P0-AM regression gate (INDEPENDENT_TRACKS_PLAN.md §2.2).

Also covers PR13AM-MIO-TAG (INDEPENDENT_TRACKS_PLAN v1.2 §19.5) — the
``__mio_owned__`` semantic flag and ``_mio_artifact_name`` prefix helper
that resolve v1.1 PATCH-01 / INSPECT-19 SEMANTIC-01.
"""
from __future__ import annotations

import numpy as np
import pytest

from htt.PR13AM_te_sign_d1d3_bridge import (
    _direction_weight_status,
    _mio_artifact_name,
)
from htt import PR13AM_te_sign_d1d3_bridge as pr13am


def _npz(prefix: str, w: np.ndarray) -> dict:
    return {f"{prefix}_dir_w": w}


def test_production_mode_rejects_uniform_fallback():
    """All-zero weights + production_mode=True → RuntimeError."""
    data = _npz("d1", np.zeros(8))
    with pytest.raises(RuntimeError, match="production inference forbidden"):
        _direction_weight_status(data, "d1", production_mode=True)


def test_diagnostic_mode_allows_uniform_fallback():
    """All-zero weights + production_mode=False → uniform diagnostic fallback."""
    data = _npz("d3", np.zeros(5))
    res = _direction_weight_status(data, "d3", production_mode=False)
    assert res["fallback_status"] == "uniform_fallback_diagnostic_only"
    assert res["production_allowed"] is False
    np.testing.assert_allclose(res["weights"].sum(), 1.0)
    np.testing.assert_allclose(res["weights"], np.full(5, 1 / 5))


def test_native_weights_pass_through_with_production_allowed():
    """Non-trivial weights → native status, production_allowed=True."""
    data = _npz("d1", np.array([1.0, 2.0, 1.0]))
    res = _direction_weight_status(data, "d1", production_mode=True)
    assert res["fallback_status"] == "native_weights"
    assert res["production_allowed"] is True
    np.testing.assert_allclose(res["weights"].sum(), 1.0)
    np.testing.assert_allclose(res["weights"], [0.25, 0.5, 0.25])


def test_default_production_mode_is_false():
    """Backward compatibility: omitting production_mode keeps diagnostic behaviour."""
    data = _npz("d1", np.zeros(4))
    res = _direction_weight_status(data, "d1")  # default
    assert res["fallback_status"] == "uniform_fallback_diagnostic_only"


def test_pr13am_mio_owned_flag():
    """PR13AM-MIO-TAG (§19.5): module-level __mio_owned__ must be True."""
    assert getattr(pr13am, "__mio_owned__", False) is True
    rationale = getattr(pr13am, "__mio_rationale__", "")
    assert "model-independent" in rationale.lower()


def test_mio_artifact_name_enforces_prefix():
    """PR13AM-MIO-TAG (§19.5): artifact stems without mio_ get prefixed."""
    assert _mio_artifact_name("te_sign") == "mio_pr13am_te_sign_v1.json"
    assert _mio_artifact_name("te_sign", version=3) == "mio_pr13am_te_sign_v3.json"
    # A stem that already carries the mio_ prefix is respected verbatim.
    assert _mio_artifact_name("mio_custom") == "mio_custom_v1.json"
