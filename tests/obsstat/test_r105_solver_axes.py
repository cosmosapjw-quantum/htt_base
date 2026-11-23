import json
import time
from dataclasses import asdict
from unittest.mock import patch

import pytest

from scripts.r105 import solver_axes as axes


def test_local_grid_changes_one_axis_at_a_time():
    grid = {"cells": [96, 192, 384], "ell": [4, 6, 8], "picard": [4, 6],
            "depth": [None, 1.0, 0.5]}
    cases = axes.make_cases(["FLRW", "VII_h", "IX", "VI_-1/9"], grid)
    assert len(cases) == 32
    for case, labels in cases.items():
        reference = axes.Case(case.family, epsilon=0.0 if case.family == "FLRW" else 2e-4)
        changed = [key for key, value in asdict(case).items() if getattr(reference, key) != value]
        assert labels == (changed or ["baseline"])
        assert case.rings == 16


def test_worker_timeout_returns_receipt():
    with patch.object(axes.native_optical_refinement, "solve_case", side_effect=lambda *a, **kw: time.sleep(2)):
        result = axes.execute(axes.Case("FLRW", epsilon=0), timeout=0.02)
    assert result["status"] == "timeout"
    assert result["wall_s"] < 2


def test_previous_checkpoint_survives_invalid_result(tmp_path):
    path = tmp_path / "checkpoint.json"
    axes.save(path, {"value": 1})
    with pytest.raises(ValueError):
        axes.save(path, {"value": float("nan")})
    assert json.loads(path.read_text()) == {"value": 1}
    assert len(list(tmp_path.iterdir())) == 1
