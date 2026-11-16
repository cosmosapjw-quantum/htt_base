"""R54-L06 joint precision-form helpers (htt/htt/htt/infer/r54_joint.py): gate MG-L07 and the probe algebra."""
from __future__ import annotations

import numpy as np
import pytest

from htt.htt.infer import r54_joint as jt


def test_mg_l07_singular_block_keeps_its_null_direction():
    design = np.array([[1.0, 1.0, 0.0], [2.0, 2.0, 0.0], [0.0, 0.0, 1.0]])      # theta_0 + theta_1 identified, theta_0 - theta_1 not
    probe = jt.linear_probe(np.array([1.0, 2.0, 0.5]), np.eye(3), design, "toy")
    ident = jt.block_identification(probe["F"], None, ["a", "b", "c"])
    assert ident["rank"] == 2 and not ident["identified"] and len(ident["null_directions"]) == 1
    v = np.asarray(ident["null_directions"][0]["direction"])
    assert abs(abs(v @ np.array([1.0, -1.0, 0.0])) / np.sqrt(2.0) - 1.0) < 1e-10
    with pytest.raises(ValueError):
        jt.constrained_chi2(probe, np.eye(3), "all three free")


def test_probe_addition_and_constrained_chi2_equal_direct_gls():
    rng = np.random.default_rng(20261116)
    j1, j2 = rng.normal(size=(6, 2)), rng.normal(size=(4, 2))
    c1, c2 = np.diag(rng.uniform(0.5, 2.0, 6)), np.diag(rng.uniform(0.5, 2.0, 4))
    y1, y2 = rng.normal(size=6), rng.normal(size=4)
    blk = jt.add_probes([jt.linear_probe(y1, c1, j1, "p1"), jt.linear_probe(y2, c2, j2, "p2")])
    y, j = np.concatenate([y1, y2]), np.vstack([j1, j2])
    ci = np.linalg.inv(np.block([[c1, np.zeros((6, 4))], [np.zeros((4, 6)), c2]]))
    theta = np.linalg.solve(j.T @ ci @ j, j.T @ ci @ y)
    chi2 = float((y - j @ theta) @ ci @ (y - j @ theta))
    res = jt.constrained_chi2(blk, np.eye(2), "free")
    assert res["dof"] == 8 and np.allclose(res["phi"], theta) and abs(res["chi2"] - chi2) < 1e-10
    assert jt.constrained_chi2(blk, np.zeros((2, 0)), "null")["chi2"] == pytest.approx(float(y @ ci @ y))
    with pytest.raises(ValueError):
        jt.add_probes([blk, jt.linear_probe(y1, c1, rng.normal(size=(6, 3)), "p3")])
