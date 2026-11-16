"""R52 regressions: response limits, frame rotation, profiling, rank, Cobaya tie."""
import math

import numpy as np
import pytest

from htt.htt.infer.r52_joint_identification import (
    SL, STF_BASIS, LinearProbe, block_ranks, endpoint_history_factor, gaussian_posterior,
    identification, joint, profiled_carrier, stf5_rotation,
)


def test_endpoint_history_factor_limits():
    assert endpoint_history_factor(1e-4, 0.3, 9e-5, 0.7 - 9e-5) == pytest.approx(1.0, abs=2e-3)
    a = 1 / 3.0  # z = 2, matter only closed form
    J, chi = (2 / 3) * (a**-1.5 - 1), 2 * (1 - a**0.5)
    assert endpoint_history_factor(2.0, 1.0, 0.0, 0.0) == pytest.approx(2 * J / chi - 1, rel=1e-9)
    ks = [endpoint_history_factor(z, 0.315, 9e-5, 0.685 - 9e-5) for z in (0.5, 1.0, 2.0)]
    assert ks[0] < ks[1] < ks[2]


def test_stf5_rotation_is_orthogonal_and_matches_tensor_rotation():
    rng = np.random.default_rng(5201)
    Q, _ = np.linalg.qr(rng.normal(size=(3, 3)))
    R = Q * np.sign(np.linalg.det(Q))
    M = stf5_rotation(R)
    np.testing.assert_allclose(M @ M.T, np.eye(5), atol=1e-13)
    s = rng.normal(size=5)
    T = np.einsum("a,aij->ij", s, STF_BASIS)
    np.testing.assert_allclose(np.einsum("aij,ij->a", STF_BASIS, R @ T @ R.T), M @ s, atol=1e-13)


def test_profiled_carrier_equals_explicit_nuisance_gls():
    rng = np.random.default_rng(5202)
    n = 20
    J = np.zeros((n, 17)); J[:, :4] = rng.normal(size=(n, 4))
    N = rng.normal(size=(n, 2)); y = rng.normal(size=n)
    Z = rng.normal(size=(n, n)); C = Z @ Z.T + n * np.eye(n)
    c = profiled_carrier(LinearProbe("x", y, C, J, N, block_id="a"))
    Ci = np.linalg.inv(C)

    def prof(th):
        r = y - J @ th
        eta = np.linalg.solve(N.T @ Ci @ N, N.T @ Ci @ r)
        e = r - N @ eta
        return e @ Ci @ e
    for th in rng.normal(size=(5, 17)):
        assert c["Q0"] - 2 * th @ c["t"] + th @ c["F"] @ th == pytest.approx(prof(th), rel=1e-9)


def test_identification_null_parameters_and_scale_invariance():
    F = np.zeros((17, 17)); F[SL["bMO"], SL["bMO"]] = np.diag([1e6, 2e6, 3e6]); F[0, 0] = 1e20
    idn = identification(F)
    assert idn["rank"] == 4
    assert block_ranks(F)["omega"] == 0 and block_ranks(F)["sigma"] == 1
    D = np.diag(np.logspace(-5, 5, 17))
    assert identification(D @ F @ D)["rank"] == 4


def test_joint_requires_unique_block_ids_and_posterior_inverse():
    p = LinearProbe("a", np.ones(3), np.eye(3), np.hstack([np.zeros((3, 14)), np.eye(3)]), block_id="b")
    q = LinearProbe("c", np.ones(3), np.eye(3), np.hstack([np.zeros((3, 14)), np.eye(3)]), block_id="b")
    with pytest.raises(ValueError):
        joint([p, q])
    jt = joint([p])
    sd = np.full(17, 0.5)
    m, c = gaussian_posterior(jt["F"], jt["t"], sd)
    P = jt["F"] + np.diag(1 / sd**2)
    np.testing.assert_allclose(c, np.linalg.inv(P), atol=1e-12)
    np.testing.assert_allclose(m, np.linalg.solve(P, jt["t"]), atol=1e-12)


def test_cobaya_provider_logp_equals_carrier_plus_prior():
    pytest.importorskip("cobaya")
    from cobaya.model import get_model
    from htt.htt.infer.r52_cobaya_provider import cobaya_info
    rng = np.random.default_rng(5203)
    A = rng.normal(size=(17, 17)); F = A @ A.T + np.eye(17); t = rng.normal(size=17)
    psd = np.logspace(-3, 0, 17); m0 = rng.normal(size=17); Lc = np.tril(rng.normal(size=(17, 17))) + 3 * np.eye(17)
    info = cobaya_info(F, t, m0, Lc, psd, "unused")
    model = get_model({"likelihood": info["likelihood"], "params": info["params"]})
    v = rng.normal(size=17)
    pt = dict(zip(model.parameterization.sampled_params(), v))
    th = m0 + Lc @ v
    expect = th @ t - 0.5 * th @ F @ th - 0.5 * np.sum((th / psd) ** 2)
    assert model.loglike(pt, return_derived=False) == pytest.approx(expect, rel=1e-10)


def test_block_rank_excludes_information_removed_by_nuisance():
    J = np.zeros((6, 17)); J[:3, SL["A"]] = np.eye(3); J[3:, SL["bMO"]] = np.eye(3)
    N = np.zeros((6, 3)); N[:3] = np.eye(3)
    jt = joint([LinearProbe("x", np.zeros(6), np.eye(6), J, N, block_id="x")])
    br = block_ranks(jt["F"], jt["F_unprofiled"])
    assert br["A"] == 0 and br["bMO"] == 3


def test_frame_composition_signs_cmb_counts_cf4():
    """v_M, v_R, v_O in a common frame: CMB = v_O - v_R, counts = c_EB (v_O - v_M), CF4 bulk = v_M - v_R."""
    from htt.htt.infer.r52_joint_identification import (
        C_KM_S, cf4_h03_design, cmb_dipole_design, count_dipole_design,
    )
    rng = np.random.default_rng(5204)
    vM, vR, vO = (1e-3 * rng.normal(size=3) for _ in range(3))
    th = np.zeros(17); th[SL["bRM"]] = vR - vM; th[SL["bMO"]] = vO - vM
    np.testing.assert_allclose(cmb_dipole_design() @ th, vO - vR, atol=1e-15)
    R = np.linalg.qr(rng.normal(size=(3, 3)))[0]; R *= np.sign(np.linalg.det(R))
    np.testing.assert_allclose(count_dipole_design(3.7, R) @ th, 3.7 * R @ (vO - vM), atol=1e-15)
    AN = rng.normal(size=(36, 3))
    np.testing.assert_allclose(cf4_h03_design(AN, 67.0, R) @ th, AN @ (C_KM_S * R @ (vM - vR)), rtol=1e-12)


def test_cf4_design_anisotropic_hubble_rows_use_reference_h0():
    from htt.htt.infer.r52_joint_identification import cf4_h03_design
    th = np.zeros(17); th[SL["A"]] = [0.01, -0.02, 0.03]; th[0] = 2e-3
    J = cf4_h03_design(np.zeros((36, 3)), 67.36, np.eye(3))
    y = J @ th
    for w in range(4):
        np.testing.assert_allclose(y[9 * w + 1:9 * w + 4], -67.36 * th[SL["A"]], rtol=1e-14)
        np.testing.assert_allclose(y[9 * w + 4:9 * w + 9], 67.36 * th[:5], rtol=1e-14)
        assert y[9 * w] == 0.0
