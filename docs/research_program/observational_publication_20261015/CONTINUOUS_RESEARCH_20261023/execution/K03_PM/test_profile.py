"""Small controls for the K03 reported-z tangent experiment; no catalogue replay."""
import importlib.util
from pathlib import Path

import mpmath as mp
import numpy as np
import pytest
from scipy.linalg import cho_factor, cho_solve

SPEC = importlib.util.spec_from_file_location("k03_profile", Path(__file__).with_name("profile.py"))
p = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(p)


def test_closed_kernels_and_clock():
    mp.mp.dps = 70
    zs = [0.08634503930807114, 0.2, 1, 2, 4.627459688728043]
    kb, kl = p.kernels(np.asarray(zs))
    for z, a, b in zip(zs, kb, kl):
        zz = mp.mpf(str(z)); r = mp.mpf("0.0001")
        q = mp.sqrt((1 + zz) * (1 + r * zz))
        I = 2 * zz / (1 + zz + q)
        np.testing.assert_allclose([a, b], [float(zz / I - 1), float(-1 / I)], rtol=1e-12, atol=1e-12)
        B, L, G = 0.007, -0.002, 0.13
        source_minus_observer = ((1 + z) * B - (B + L)) / float(I)
        direct = source_minus_observer - B + G
        np.testing.assert_allclose(direct, a * B + b * L + G, rtol=1e-12, atol=1e-12)
    assert abs(p.kernels([1e-8])[0][0] / 1e-8 - (3 + 1e-4) / 4) < 1e-7
    assert 1 / 1 - 1 == 0  # constant H: I=z, hence k_b=0
    depths = [mp.mpf(5) / 4, mp.mpf(3), mp.mpf(21) / 4]
    rows = []
    for z in depths:
        I = 2 * (1 - 1 / mp.sqrt(1 + z))
        rows.append([z / I - 1, -1 / I, 1])
    assert abs(mp.det(mp.matrix(rows)) + mp.mpf(1) / 2) < mp.mpf("1e-60")


def fixture(same_depth=False):
    rng = np.random.default_rng(314159)
    n = 36
    ra = rng.uniform(0, 360, n); dec = rng.uniform(-70, 70, n)
    z = np.full(n, 1.5) if same_depth else np.tile([0.3, 0.7, 1.3, 2.2, 3.5, 4.2], n // 6)
    model = p.old_model()
    dip = model.dipole(ra, dec)
    e = dip[:, :, :3]; b = dip[:, :, 3:]
    H = p.response(e, z)
    # Includes global B1, common E1, and independent l4 angular nuisance columns.
    l4 = model.vsh(ra, dec, [4])[:, :, :4]
    U = np.concatenate((b, e, l4), axis=2)
    sa = rng.uniform(1, 3, n); sd = rng.uniform(1, 3, n); rho = rng.uniform(-0.3, 0.3, n)
    return H, U, sa, sd, rho, rng


def test_dense_qr_streaming_moments_and_injections():
    H, U, sa, sd, rho, rng = fixture()
    theta = np.array([1.1, -2.2, 0.7, 3.3, -0.4, 1.2])
    nuisance = rng.normal(size=U.shape[2])
    y = np.einsum("nik,k->ni", H, theta) + np.einsum("nik,k->ni", U, nuisance) + rng.normal(size=H.shape[:2]) * .01
    W_H, W_y = p.old_model().whiten(H, y, sa, sd, rho)
    W_U, _ = p.old_model().whiten(U, y, sa, sd, rho)
    X = np.column_stack((W_H, W_U))
    q, r = np.linalg.qr(X, mode="reduced")
    dense = np.linalg.solve(r, q.T @ W_y)[:6]
    dense_cov = np.linalg.solve(r, np.linalg.solve(r.T, np.eye(r.shape[0])))[:6, :6]
    A = W_H.T @ W_H; J = W_H.T @ W_U; N = W_U.T @ W_U
    qh = W_H.T @ W_y; bu = W_U.T @ W_y
    ncf = cho_factor(N, lower=True)
    F = A - J @ cho_solve(ncf, J.T)
    s = qh - J @ cho_solve(ncf, bu)
    fcf = cho_factor(F, lower=True)
    stream = cho_solve(fcf, s); cov = cho_solve(fcf, np.eye(6))
    np.testing.assert_allclose(stream, dense, rtol=1e-9, atol=1e-10)
    np.testing.assert_allclose(cov, dense_cov, rtol=1e-9, atol=1e-10)
    shift = np.arange(U.shape[2]) / 3
    shifted_y = W_y + W_U @ shift
    shifted = cho_solve(fcf, W_H.T @ shifted_y - J @ cho_solve(ncf, W_U.T @ shifted_y))
    np.testing.assert_allclose(shifted, stream, rtol=1e-9, atol=1e-10)
    shifted_H = W_y + W_H @ theta
    recovered = cho_solve(fcf, W_H.T @ shifted_H - J @ cho_solve(ncf, W_U.T @ shifted_H))
    np.testing.assert_allclose(recovered, stream + theta, rtol=1e-9, atol=1e-10)
    Rmat = np.column_stack((np.eye(6), -J @ cho_solve(ncf, np.eye(len(N)))))
    Gaug = np.block([[A, J], [J.T, N]])
    assert np.linalg.norm(Rmat @ Gaug @ Rmat.T - F) / np.linalg.norm(F) < 1e-10
    assert np.linalg.norm(cov @ (Rmat @ Gaug @ Rmat.T) @ cov - cov) / np.linalg.norm(cov) < 1e-10
    assert np.linalg.norm(Rmat @ np.vstack((J, N))) / (np.linalg.norm(Rmat) * np.linalg.norm(np.vstack((J, N)))) < 1e-10


def test_same_depth_not_estimable():
    H, U, sa, sd, rho, _ = fixture(same_depth=True)
    zeros = np.zeros(H.shape[:2])
    wh, _ = p.old_model().whiten(H, zeros, sa, sd, rho)
    wu, _ = p.old_model().whiten(U, zeros, sa, sd, rho)
    q, _ = np.linalg.qr(wu, mode="reduced")
    residual = wh - q @ (q.T @ wh)
    assert np.linalg.matrix_rank(residual, tol=1e-10) < 6


def test_principal_angle_matrix_controls():
    for S, expected in [(np.zeros((3, 3)), [0, 0, 0]),
                        (np.eye(3), [1, 1, 1]),
                        (np.diag([.8, .5, 0]), [.8, .5, 0])]:
        F = np.block([[np.eye(3), S], [S.T, np.eye(3)]])
        got = p.angles(F)
        np.testing.assert_allclose(got["principal_cosines_raw"], expected, atol=1e-14)
        if expected == [.8, .5, 0]:
            assert abs(got["condition_canonical_pair"] - 9) < 1e-13
            np.testing.assert_allclose(got["information_retention_factors"], [.36, .75, 1], atol=1e-14)
        elif expected == [1, 1, 1]:
            assert got["joint_rank"] == 3
            assert got["condition_canonical_pair"] is None
        else:
            np.testing.assert_allclose(got["principal_angles_degrees"], [90, 90, 90], atol=1e-14)
