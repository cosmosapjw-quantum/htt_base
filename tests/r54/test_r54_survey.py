"""R54-L04 survey labels and survey operators (htt/htt/htt/infer/r54_survey.py): gates MG-L05 and MG-L06.

MG-L05  survey labels are joined on identifiers: label[group_id] is invariant under a permutation of the raw rows;
MG-L06  the survey step is fitted with redshift-bin monopoles: a monopole trend with unequal hemisphere depths gives no step.
"""
from __future__ import annotations

import math

import numpy as np
import pytest

from htt.htt.infer import r54_survey as sv


def _toy():
    gal = {"pgc": np.array([101, 102, 103, 201, 202, 301, 401, 501], np.int64),
           "group": np.array([10, 10, 10, 20, 20, 30, 40, 50], np.int64),
           "has_fp": np.array([True, True, False, True, True, False, True, True]),
           "has_tf": np.zeros(8, bool), "has_sn": np.zeros(8, bool)}
    groups = np.array([10, 20, 30, 40, 50], np.int64)
    family = np.array(["FP", "FP", "TF", "FP", "FP"])
    sdss = np.array([101, 102, 201, 999], np.int64)
    return gal, groups, family, sdss


def test_mg_l05_labels_are_joined_on_identifiers_not_on_row_order():
    gal, groups, family, sdss = _toy()
    lab = sv.survey_labels(groups, family, gal, sdss)
    assert lab.tolist() == ["FP_SDSS", "FP_MIXED", "TF_ALL", "FP_NOT_SDSS", "FP_NOT_SDSS"]
    perm = np.array([7, 3, 0, 5, 1, 6, 2, 4])
    shuffled = {k: v[perm] for k, v in gal.items()}
    gperm = np.array([3, 0, 4, 2, 1])
    lab2 = sv.survey_labels(groups[gperm], family[gperm], shuffled, sdss[::-1])
    assert dict(zip(groups[gperm].tolist(), lab2.tolist())) == dict(zip(groups.tolist(), lab.tolist()))
    with pytest.raises(ValueError):
        sv.survey_labels(np.array([10, 10]), np.array(["FP", "FP"]), gal, sdss)


def test_mg_l06_survey_step_needs_the_redshift_monopoles():
    """Monopole trend across redshift bins (no step) with the north deeper than the south: the step operator returns zero."""
    rng = np.random.default_rng(20261116)
    m = 6000
    north = rng.random(m) < 0.5
    z = np.where(north, rng.uniform(0.03, 0.055, m), rng.uniform(0.01, 0.035, m))
    nz = np.where(north, rng.uniform(0.1, 1.0, m), -rng.uniform(0.1, 1.0, m))
    nvec = np.column_stack([np.sqrt(1 - nz**2), np.zeros(m), nz])
    eta = 0.005 * np.digitize(z, (0.02, 0.03, 0.04))               # piecewise-constant monopole trend across the bins
    op = sv.survey_step_operator(z, nvec, np.ones(m), np.ones(m, bool), (0.01, 0.02, 0.03, 0.04, 0.055))
    assert abs(float(op @ eta)) < 1e-12
    step_true = 0.01
    assert math.isclose(float(op @ (eta + step_true * np.sign(nz))), step_true, rel_tol=1e-9)


def test_pool_small_and_offsets():
    labels = np.array(["FP_SDSS"] * 5 + ["FP_MIXED"] * 2 + ["TF_ALL"] * 3)
    family = np.array(["FP"] * 7 + ["TF"] * 3)
    pooled = sv.pool_small(labels, family, np.ones(10, bool), 3)
    assert pooled.tolist() == ["FP_SDSS"] * 5 + ["FP_REST"] * 2 + ["TF_ALL"] * 3
    z = np.linspace(0.011, 0.054, 9)
    lab = np.array(["A", "B", "C"] * 3)
    eta = 0.1 + 0.02 * (lab == "B") - 0.03 * (lab == "C")
    op = sv.survey_offset_operator(z, np.ones(9), lab, np.ones(9, bool), "A", ["B", "C"], (0.01, 0.055))
    assert np.allclose(op @ eta, [0.02, -0.03], atol=1e-12)
    with pytest.raises(ValueError):
        sv.survey_offset_operator(z, np.ones(9), lab, np.ones(9, bool), "A", ["A", "B"], (0.01, 0.055))
    assert sv.join_coverage(np.array([1, 2, 3, 4]), np.array([1, 2, 3])) == 0.75
