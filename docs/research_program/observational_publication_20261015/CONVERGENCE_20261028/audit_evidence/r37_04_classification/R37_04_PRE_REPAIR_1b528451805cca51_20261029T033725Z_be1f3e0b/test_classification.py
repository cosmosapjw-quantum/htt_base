"""Independent local falsifiers for the finite conditional classifier."""
import importlib.util
from pathlib import Path

import numpy as np
from scipy.spatial.transform import Rotation

P = Path(__file__).with_name("classification.py")
spec = importlib.util.spec_from_file_location("r37_classification", P)
c = importlib.util.module_from_spec(spec)
spec.loader.exec_module(c)


def test_exact_orbit_gap_and_rotated_response():
    ii = np.diag([.5, -.5, -.5])
    vii = np.diag([-.5, 1.5, -1.5])
    rng = np.random.default_rng(41)
    delta = np.sqrt(2)
    for a in (0., .25, .5, 1.):
        for _ in range(20):
            r = Rotation.random(random_state=rng).as_matrix()
            s = Rotation.random(random_state=rng).as_matrix()
            x = r @ (a*a*ii) @ r.T
            y = s @ (a*a*vii) @ s.T
            assert abs(c.orbit_distance(x, y)-a*a*delta) < 1e-13
            assert np.linalg.norm(x-y) + 1e-13 >= a*a*delta


def test_one_joint_law_compatibility_and_adequacy():
    ii = np.diag([.5, -.5, -.5])
    vii = np.diag([-.5, 1.5, -1.5])
    means = {"II": ii, "VII0matched": vii}
    y = c.raw_mean(ii)
    assert c.exact_compatibility(y, means, .5) == ["II"]
    assert set(c.exact_compatibility(y, means, 1.5)) == set(means)
    y[0] += 1
    assert c.exact_compatibility(y, means, .525816) == []
    # With a=0 both supplied family images coincide, even at zero radius.
    zero = {k: np.zeros((3,3)) for k in means}
    assert set(c.exact_compatibility(np.zeros(7), zero, 0)) == set(means)


def test_strong_quadratic_and_fixed_q_attainment():
    ii = np.diag([.5, -.5, -.5])
    vii = np.diag([-.5, 1.5, -1.5])
    assert abs(np.trace(ii@ii)-.75) < 1e-14
    assert abs(np.trace(vii@vii)-4.75) < 1e-14
    assert abs(np.linalg.norm(c.stf(vii))**2-np.linalg.norm(c.stf(ii))**2-4) < 1e-14
    r = c.fixed_q_radius()
    assert abs(r["radius"]-1/np.sqrt(3)) < 1e-14
    assert abs(r["boundary_chirality"]) < 1e-14
