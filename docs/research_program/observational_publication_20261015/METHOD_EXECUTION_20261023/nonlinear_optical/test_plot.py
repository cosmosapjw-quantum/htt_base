"""Falsify an interpolated positive-power curve beyond mean-set overlap."""
import json
from pathlib import Path

import numpy as np

from plot import remainder_plot_data

HERE = Path(__file__).resolve().parent


def test_exact_overlap_and_frozen_markers_for_all_fixed_cases():
    result = json.loads((HERE/"RESULT.json").read_text())
    for scenario in result["scenarios"]:
        for row in scenario["rows"]:
            for case in row["noise"]:
                radius, power, marker_rho, marker_power = remainder_plot_data(row, case)
                star = row["d0"]/2
                assert np.any(radius == star)
                assert np.all(power[radius >= star] == .05)
                assert np.all(power[radius < star] >= .05)
                assert np.array_equal(marker_rho,
                    np.array([p["rho"] for p in case["remainder_power"]]))
                assert np.array_equal(marker_power,
                    np.array([p["maximin_power"] for p in case["remainder_power"]]))


def test_review_falsifier_crosses_threshold_without_linear_bridge():
    result = json.loads((HERE/"RESULT.json").read_text())
    scenario = result["scenarios"][0]
    row = next(r for r in scenario["rows"] if r["direction"] == "+ex" and r["amplitude"] == .3)
    case = next(c for c in row["noise"] if c["tau"] == .5)
    radius, power, marker_rho, marker_power = remainder_plot_data(row, case)
    star = row["overlap_rho_star"]
    assert abs(star-.03864389736440061) < 1e-12
    assert abs(power[radius == star][0]-.05) < 1e-15
    assert np.all(power[radius > star] == .05)
    # rho=.05 lies between frozen .01 and .1 markers: the analytic display
    # grid must show the exact overlap plateau there.
    assert .05 in radius
    assert power[np.where(radius == .05)[0][0]] == .05
    assert .1 in marker_rho
    assert abs(marker_power[np.where(marker_rho == .1)[0][0]]-.05) < 1e-14
