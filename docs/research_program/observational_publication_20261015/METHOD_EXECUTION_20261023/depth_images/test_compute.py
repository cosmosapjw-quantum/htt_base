from __future__ import annotations

import numpy as np

from compute import (PAIRS, RADII, compute, contrast_covariance, functional_map,
                     load_source, strict_frequency)

ATOL = RTOL = 1e-10


def close(actual, expected):
    np.testing.assert_allclose(actual, expected, atol=ATOL, rtol=RTOL)


def test_frozen_source_and_retained_joint_sample():
    source, mu, cov, samples = load_source()
    result, arrays = compute()
    assert result["source_candidate"].endswith("39f15bd86ecd76907beef05fcfa09fe57c48d5536218b3e4840311783e9bfc7a")
    assert source["x"]["sample_size"] == 4096
    assert arrays["sample24_uasyr"].shape == (4096, 24)
    assert arrays["functional_sample_uasyr"].shape == (4096, 12, 3)
    m = np.asarray(source["G_F"]["M24_to_Y18_matrix"])
    a = functional_map(m)
    close(arrays["functional_sample_uasyr"].reshape(4096, 36), samples@a.T)
    close(arrays["linear_mean_36"], a@mu)
    close(arrays["linear_cov_36x36"], a@cov@a.T)
    close(arrays["raw_intercept_sample_uasyr"], samples[:, :18])


def test_support_attainment_and_certified_outer():
    source, mu, cov, _ = load_source()
    _, arrays = compute()
    a = functional_map(source["G_F"]["M24_to_Y18_matrix"])
    chol = np.linalg.cholesky(cov)
    for ir, rho in enumerate(RADII):
        for row in range(36):
            direction = a[row]
            unit = chol.T@direction / np.linalg.norm(chol.T@direction)
            plus = mu + rho*chol@unit
            minus = mu - rho*chol@unit
            close(direction@plus, arrays["coordinate_support_5x36x2"][ir, row, 1])
            close(direction@minus, arrays["coordinate_support_5x36x2"][ir, row, 0])
        # Deterministic full24 sphere witnesses, not new empirical draws.
        for axis in range(24):
            for sign in (-1, 1):
                point = mu + sign*rho*chol[:, axis]
                norms = np.linalg.norm((a@point).reshape(12, 3), axis=1)
                bounds = arrays["norm_outer_5x12x2"][ir]
                assert np.all(norms >= bounds[:, 0]-ATOL)
                assert np.all(norms <= bounds[:, 1]+ATOL)


def test_full_contrast_covariance_and_nonzero_discriminator():
    source, _, cov, _ = load_source()
    result, arrays = compute()
    m = np.asarray(source["G_F"]["M24_to_Y18_matrix"])
    ycov = m@cov@m.T
    assert contrast_covariance(np.eye(3), np.eye(3), None) is None
    assert len(result["cross_depth_discriminator"]) == 6
    for p, (i, j) in enumerate(PAIRS):
        for mode in range(2):
            si = slice(6*i+3*mode, 6*i+3*mode+3)
            sj = slice(6*j+3*mode, 6*j+3*mode+3)
            expected = ycov[si, si]+ycov[sj, sj]-ycov[si, sj]-ycov[sj, si]
            index = 18+6*p+3*mode
            close(expected, arrays["linear_cov_36x36"][index:index+3, index:index+3])
            row = result["cross_depth_discriminator"][2*p+mode]
            close(row["full_cov_uasyr2"], expected)
            close(row["signed_full_minus_zero_cov_uasyr2"], -ycov[si, sj]-ycov[sj, si])
            assert np.linalg.norm(row["signed_full_minus_zero_cov_uasyr2"]) > 0


def test_depth_path_information_and_crossblocks():
    source, mu, cov, samples = load_source()
    result, arrays = compute()
    m = np.asarray(result["depth"]["M24_to_Y18"])
    t = np.asarray(result["depth"]["Y18_to_Z18"])
    assert np.linalg.matrix_rank(m) == 18
    assert np.linalg.matrix_rank(t) == 18
    assert np.linalg.matrix_rank(t[6:]@m) == 12
    null = np.linalg.svd(m, full_matrices=True)[2][18:].T
    assert null.shape == (24, 6)
    close(m@null, 0)
    close(t@arrays["Y18_sample_uasyr"].T, arrays["Z18_sample_uasyr"].T)
    close(arrays["Y18_sample_uasyr"], samples@m.T)
    close(result["depth"]["Y18_cov"], m@cov@m.T)
    close(result["depth"]["Z18_cov"], t@m@cov@m.T@t.T)
    close(result["depth"]["Y18_mean"], source["G_F"]["Y18_mean_uasyr"])
    close(result["depth"]["Z18_mean"], source["G_F"]["Z18_mean_uasyr"])
    close(result["depth"]["Y18_cov"], source["G_F"]["Y18_cov_uasyr2"])
    close(result["depth"]["Z18_cov"], source["G_F"]["Z18_cov_uasyr2"])
    # Pure common bin displacement is erased by a delta-only map.
    common = np.tile(np.arange(1., 7.), 3)
    close(t[6:]@common, 0)


def test_reported_bin_map_slope_fixture_and_depth_contrasts():
    source, _, _, samples = load_source()
    result, arrays = compute()
    m = np.asarray(source["G_F"]["M24_to_Y18_matrix"])
    a = functional_map(m)
    close(a[:18], m)
    close(arrays["functional_sample_uasyr"][:, :6].reshape(4096, 18), arrays["Y18_sample_uasyr"])
    close(arrays["functional_sample_uasyr"][:, 6:10].reshape(4096, 12), arrays["Z18_sample_uasyr"][:, 6:])
    close(arrays["functional_sample_uasyr"][:, 10], arrays["Y18_sample_uasyr"][:, 12:15]-arrays["Y18_sample_uasyr"][:, :3])
    close(arrays["functional_sample_uasyr"][:, 11], arrays["Y18_sample_uasyr"][:, 15:18]-arrays["Y18_sample_uasyr"][:, 3:6])
    fixture = np.zeros(24)
    fixture[18:] = [2., 3., 5., 7., 11., 13.]
    centers = np.array([1/4, 7/12, 26/33])
    for b, center in enumerate(centers):
        close((a@fixture)[6*b:6*b+6], center*fixture[18:])
    close((a@fixture)[18:24], (centers[1]-centers[0])*fixture[18:])
    close((a@fixture)[24:30], (centers[2]-centers[1])*fixture[18:])
    close((a@fixture)[30:36], (centers[2]-centers[0])*fixture[18:])
    close(result["raw_intercepts"]["mean18_uasyr"], np.asarray(source["full24"]["mean_uasyr"])[:18])


def test_strict_empirical_pi_and_nonvacuity():
    result, arrays = compute()
    close(strict_frequency(np.array([[0., 1.], [1., 2.]]), np.array([0., 1., 2.])),
          [[0.5, 0., 0.], [1., 0.5, 0.]])
    close(arrays["empirical_norm_Pi_12x6"],
          strict_frequency(arrays["norm_sample_uasyr"], np.array([0, 1, 2, 5, 10, 20])))
    close(arrays["empirical_dot_Pi_6x3"],
          strict_frequency(arrays["E_dot_B_sample_uasyr2"], np.array([-25, 0, 25])))
    assert result["nonvacuity"]["strict_empirical_norm_Pi_nontrivial_cells"] > 0
    assert result["nonvacuity"]["strict_empirical_dot_Pi_nontrivial_cells"] > 0
    assert result["nonvacuity"]["positive_norm_lower_count_by_rho"][0] == 12
    assert result["law"]["physical_Pi_interval"] == [0, 1]


def test_polar_axial_parity_and_so3():
    _, arrays = compute()
    x = arrays["functional_sample_uasyr"][:7]
    rotation = np.array([[0., -1., 0.], [1., 0., 0.], [0., 0., 1.]])
    rotated = x@rotation.T
    close(np.linalg.norm(rotated, axis=2), np.linalg.norm(x, axis=2))
    close(np.einsum("nki,nki->nk", rotated[:, ::2], rotated[:, 1::2]),
          np.einsum("nki,nki->nk", x[:, ::2], x[:, 1::2]))
    inverted = x.copy()
    inverted[:, ::2] *= -1  # E is polar, B is axial.
    close(np.linalg.norm(inverted, axis=2), np.linalg.norm(x, axis=2))
    close(np.einsum("nki,nki->nk", inverted[:, ::2], inverted[:, 1::2]),
          -np.einsum("nki,nki->nk", x[:, ::2], x[:, 1::2]))
