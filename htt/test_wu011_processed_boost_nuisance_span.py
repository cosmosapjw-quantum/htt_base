"""RED/GREEN contracts for the WU-011 Task-7C nuisance-span atlas."""

from __future__ import annotations

import numpy as np
import pytest


pytest.importorskip("healpy", reason="healpy is required by WU-011 Task-7C")
pytestmark = pytest.mark.requires_healpy


def _api():
    try:
        from obsstat import processed_boost_nuisance_span as api
    except ImportError as exc:
        pytest.fail(f"WU-011 Task-7C API missing: {exc}", pytrace=False)
    return api


def test_task7c_registries_and_terminals_are_frozen() -> None:
    api = _api()
    assert api.DIRECTION_IDS == (
        "X",
        "Y",
        "Z",
        "D111",
        "D1M11",
        "D11M1",
    )
    assert api.CORE_SOURCE_CUTOFFS == (9, 12, 16)
    assert api.Task7CTerminal.PASS_TASK7C_MODEL_FREE_IDENTIFIED_SUBSPACE.value
    assert api.Task7CTerminal.PASS_TASK7C_MODEL_FREE_NO_IDENTIFIED_SUBSPACE.value
    assert api.Task7CTerminal.PASS_TASK7C_SOURCE_BAND_NOT_CONVERGED.value
    assert api.Task7CTerminal.BLOCKED_BY_DIRECTIONAL_METRIC_FAILURE.value
    assert api.Task7CTerminal.BLOCKED_BY_CUTOFF_CONSTRUCTION.value
    assert api.Task7CTerminal.BLOCKED_BY_ARTIFACT_INTEGRITY.value


def test_task7c_direction_registry_is_unit_and_immutable() -> None:
    api = _api()
    registry = api.direction_registry()
    assert tuple(registry) == api.DIRECTION_IDS
    for direction_id in api.DIRECTION_IDS:
        vector = registry[direction_id]
        assert vector.shape == (3,)
        assert np.linalg.norm(vector) == pytest.approx(1.0, rel=0.0, abs=2.0e-15)
        assert vector.flags.writeable is False
