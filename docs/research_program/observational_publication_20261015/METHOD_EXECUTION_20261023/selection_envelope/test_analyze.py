"""Focused falsifiers for the reviewed empirical selection envelope."""

import csv
import importlib.util
import json
from pathlib import Path

import numpy as np
from scipy.optimize import linprog


HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("r24_selection_envelope", HERE / "analyze.py")
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


def test_sharp_formula_against_independent_small_lp():
    for n, m, gamma in ((3, 1, 1.25), (7, 2, 2), (11, 8, 4), (274, 71, 1)):
        event = np.array([1] * m + [0] * (n - m), dtype=float)
        c = event / n
        args = dict(A_eq=np.ones((1, n)), b_eq=[n],
                    bounds=[(1 / gamma, gamma)] * n, method="highs")
        low = linprog(c, **args)
        high = linprog(-c, **args)
        assert low.success and high.success
        expected = (low.fun, -high.fun)
        assert np.allclose(module.sharp_bounds(m, n, gamma), expected, atol=1e-12)
        for maximize, endpoint in zip((False, True), expected):
            w = module.witness(event.astype(bool), gamma, maximize)
            assert abs(np.mean(w) - 1) < 1e-12
            assert abs(np.mean(w * event) - endpoint) < 1e-12


def test_strict_ties_and_frame_extension():
    signed = np.array([-.5, .5, .499, .501, 0.0])
    assert int(np.count_nonzero(np.abs(signed) > .5)) == 1
    assert int(np.count_nonzero(np.abs(signed) > .499)) == 3
    lo, hi = module.sharp_bounds(0, 274, 4)
    assert lo == hi == 0
    assert 274 / 628 * lo == 0
    assert 274 / 628 * hi + 354 / 628 == 354 / 628


def test_actual_surface_has_every_breakpoint_and_all_scenarios():
    result = json.loads((HERE / "RESULT.json").read_text())
    source = module.read_oof(json.loads((module.METHOD / "distance" / "RESULT.json").read_text()))
    by_key = {}
    with (HERE / "SURFACE.csv").open(newline="") as handle:
        for row in csv.DictReader(handle):
            by_key.setdefault((row["scenario"], row["model"]), []).append(row)
    assert set(by_key) == set(source)
    assert result["oracle_cells"] == 60
    assert result["oracle_optimizations"] == 120
    for key, signed in source.items():
        expected = set(np.abs(signed).tolist()) | set(module.DISPLAY_THRESHOLDS)
        rows = by_key[key]
        assert len(rows) == 5 * len(expected)
        assert {float(r["threshold_mag"]) for r in rows} == expected
        for row in rows:
            t = float(row["threshold_mag"])
            assert int(row["event_count"]) == int(np.count_nonzero(np.abs(signed) > t))
            assert abs(float(row["frame628_width"]) - (
                354 / 628 + 274 / 628 * float(row["cohort_width"]))) < 1e-12
