"""Narrow falsifiers for the full tensor scenario interface."""
import numpy as np

from adapter import (load_reviewed_state, y_map, depth_path, ellipsoid_support,
                     computational_reference, gaussian_replicates, sample_pushforward,
                     reference_exceedance, parity_transform, block_specs)
from common.typefree_functionals import (FiniteFunctionalImage, ImageAtom,
                                         strict_exceedance, ratio_value, UndefinedValue)


def state():
    source, mu, cov = load_reviewed_state()
    rep, m, y, cy, z, cz = depth_path(mu, cov, source["depth_c_reported_z_centers"])
    return source, mu, cov, rep, m, y, cy, z, cz


def test_depth_reconstruction_full_covariance_quadratic_fisher():
    source, mu, cov, rep, m, y, cy, z, cz = state()
    np.testing.assert_allclose(rep.restore(z), y, atol=1e-12, rtol=0)
    np.testing.assert_allclose(m @ mu, source["Y18_state_uasyr"], atol=1e-12, rtol=0)
    np.testing.assert_allclose(m @ cov @ m.T, source["Y18_cov_uasyr2"], atol=1e-10, rtol=1e-12)
    np.testing.assert_allclose(z, source["anchored_difference18_state_uasyr"], atol=1e-12, rtol=0)
    np.testing.assert_allclose(cz, source["anchored_difference18_cov_uasyr2"], atol=1e-10, rtol=1e-12)
    assert abs(np.linalg.det(rep.T)-1) < 1e-12
    direction = np.linspace(-1., 1., 18)
    qy = direction @ np.linalg.solve(cy, direction)
    qz = (rep.T @ direction) @ np.linalg.solve(cz, rep.T @ direction)
    assert abs(qy-qz)/max(1, abs(qy)) < 1e-10
    jac = np.vstack([direction, np.roll(direction, 3)]).T
    fy = jac.T @ np.linalg.solve(cy, jac)
    fz = (rep.T @ jac).T @ np.linalg.solve(cz, rep.T @ jac)
    np.testing.assert_allclose(fy, fz, rtol=1e-10, atol=1e-10)


def test_full24_information_loss_and_initial_block_necessity():
    source, mu, cov, rep, m, y, cy, z, cz = state()
    assert np.linalg.matrix_rank(m, tol=1e-10) == 18
    assert np.linalg.matrix_rank(m @ cov @ m.T, tol=1e-10) == 18
    for i in range(6):
        witness = np.zeros(24); witness[18+i] = 1
        for b, c in enumerate(source["depth_c_reported_z_centers"]):
            witness[6*b+i] = -c
        np.testing.assert_allclose(m @ witness, 0, atol=1e-15, rtol=0)
        assert np.linalg.norm(witness) > 0
    assert np.linalg.matrix_rank(rep.H) == 12
    common_mode = np.tile(np.array([1., -2., 0., 0., 3., 4.]), 3)
    np.testing.assert_array_equal(rep.H @ common_mode, np.zeros(12))
    np.testing.assert_array_equal(rep.restore(rep.T @ common_mode), common_mode)


def test_missing_cross_covariance_and_undefined_denominators():
    source, mu, cov, rep, m, y, cy, z, cz = state()
    blocks = {(i, j): cy[6*i:6*i+6, 6*j:6*j+6] for i in range(3) for j in range(3)}
    blocks.pop((0, 1))
    _, _, _, missing, _, missing_z = depth_path(mu, cov, source["depth_c_reported_z_centers"], covariance_blocks=blocks)
    assert missing is None and missing_z is None
    assert isinstance(ratio_value(1., 0.), UndefinedValue)
    assert isinstance(ratio_value(-1., 0., positive_denominator=True), UndefinedValue)
    assert isinstance(ratio_value(1., -1., positive_denominator=True), UndefinedValue)
    assert computational_reference(mu)[0] > 0  # reference only


def test_strict_ties_explicit_sampling_law_and_signed_support():
    image = FiniteFunctionalImage("same-law", "SAMPLING", "s", "q", "q",
                                  (ImageAtom("tie", np.asarray(2.), .5, "DEFINED"),
                                   ImageAtom("above", np.asarray(3.), .25, "DEFINED"),
                                   ImageAtom("undefined", None, .25, "UNDEFINED")),
                                  "PARTIALLY_UNDEFINED")
    pi = strict_exceedance(image, 2.)
    assert (pi.known_exceedance_mass, pi.undefined_mass, pi.lower, pi.upper) == (.25, .25, .25, .5)
    _, mu, cov, *_ = state()
    u = np.eye(24)[0]
    assert ellipsoid_support(mu, cov, u, 0) == mu[0]
    assert ellipsoid_support(mu, cov, -u, 2) > -mu[0]
    samples = gaussian_replicates(mu, cov, 12)
    x, images = sample_pushforward(samples)
    assert x.shape == (12, 8, 3) and all(im.status == "DEFINED" for im in images)
    assert reference_exceedance(samples, computational_reference(mu)[0]).rule == "value > threshold"
    assert {spec.parity for spec in block_specs()} == {"polar", "axial"}


def test_so3_and_polar_axial_parity():
    sample = np.arange(24., dtype=float).reshape(8, 3)
    r = np.array([[0., -1., 0.], [1., 0., 0.], [0., 0., 1.]])
    rotated = parity_transform(sample, r)
    np.testing.assert_allclose(np.linalg.norm(rotated, axis=1), np.linalg.norm(sample, axis=1))
    inverted = parity_transform(sample, np.eye(3), inversion=True)
    for i, spec in enumerate(block_specs()):
        np.testing.assert_array_equal(inverted[i], (-1 if spec.parity == "polar" else 1)*sample[i])
    np.testing.assert_array_equal(parity_transform(inverted, np.eye(3), inversion=True), sample)
