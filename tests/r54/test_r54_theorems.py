"""Executable checks of THEOREMS.md (node R54-THM). No data are read: every test is algebra, a design-only
computation or a seeded Monte Carlo of a stated law. Test names carry the theorem id they protect."""
from __future__ import annotations

import math
from pathlib import Path

import numpy as np
import pytest
from scipy import stats

from htt.htt.infer import r54_identifiability as idn
from htt.htt.infer import r54_tensor_five_view as fv
from htt.htt.infer import r54_type1_thomson as th

FIX = Path(__file__).resolve().parents[1] / "fixtures" / "r54"
SEED = 20261116


def _spd(rng, n):
    a = rng.standard_normal((n, n))
    return a @ a.T + n * np.eye(n)


# ------------------------------------------------------------------ T1
def test_t1_no_compression_or_recoordinatization_gains_information():
    rng = np.random.default_rng(SEED)
    p, k = 12, 4
    j, c = rng.standard_normal((p, k)), _spd(rng, p)
    f = j.T @ np.linalg.solve(c, j)
    for q in (4, 6, 9, 12):                                           # any linear compression z = A y
        a = rng.standard_normal((q, p))
        f_a = j.T @ a.T @ np.linalg.solve(a @ c @ a.T, a @ j)
        assert np.linalg.eigvalsh(f - f_a).min() > -1e-9 * np.trace(f)
        if q < p:
            assert np.trace(f - f_a) > 1e-6 * np.trace(f)             # a generic compression loses information
    score = j.T @ np.linalg.inv(c)                                    # the score compression is lossless (sufficiency)
    assert np.allclose(j.T @ score.T @ np.linalg.solve(score @ c @ score.T, score @ j), f, rtol=1e-9)
    b = rng.standard_normal((k, k)) + 3.0 * np.eye(k)                 # re-coordinatization theta' = B theta (tensorization)
    f_b = np.linalg.inv(b).T @ f @ np.linalg.inv(b)
    theta = rng.standard_normal(k)
    assert math.isclose(float(theta @ f @ theta), float((b @ theta) @ f_b @ (b @ theta)), rel_tol=1e-10)   # same noncentrality: a tie


# ------------------------------------------------------------------ T2
def test_t2_exact_simultaneous_coverage_with_singular_precision():
    rng = np.random.default_rng(SEED + 2)
    p, d, r, level = 9, 6, 4, 0.90
    j = rng.standard_normal((p, r)) @ rng.standard_normal((r, d))     # rank r < d: d - r unidentified directions
    c = _spd(rng, p)
    ci = np.linalg.inv(c)
    f, f_pinv = j.T @ ci @ j, np.linalg.pinv(j.T @ ci @ j)
    kernel = np.linalg.svd(f)[2][r:]
    theta = rng.standard_normal(d) + 50.0 * kernel.T @ rng.standard_normal(d - r)   # large unidentified component
    n_draw = 40000
    y = theta @ j.T + rng.standard_normal((n_draw, p)) @ np.linalg.cholesky(c).T
    m = (y @ ci @ j) @ f_pinv
    stat = np.einsum("ni,ij,nj->n", theta - m, f, theta - m)
    cover = float(np.mean(stat <= stats.chi2.ppf(level, r)))
    assert abs(cover - level) < 4.0 * math.sqrt(level * (1 - level) / n_draw)       # chi2 with r (not d) degrees of freedom
    assert stats.kstest(stat, stats.chi2(r).cdf).pvalue > 1e-3
    # Scheffe identity on one draw: sup over identified v of (v.(theta - m))^2 / (v^T F^+ v) equals the quadratic form
    dev, q0 = theta - m[0], float(stat[0])
    v_star = f @ dev
    assert math.isclose(float((v_star @ dev) ** 2 / (v_star @ f_pinv @ v_star)), q0, rel_tol=1e-9)
    for _ in range(200):
        v = f @ rng.standard_normal(d)                                # a generic identified direction
        assert (v @ dev) ** 2 / (v @ f_pinv @ v) <= q0 * (1 + 1e-9)
    # the support interval of the module: finite on identified directions, the whole line on unidentified ones
    t0, c0 = f @ m[0], math.sqrt(stats.chi2.ppf(level, r))
    v = f @ rng.standard_normal(d)
    lo, hi = fv.support_interval(f, t0, v, c0)
    assert math.isclose(hi - lo, 2.0 * c0 * math.sqrt(v @ f_pinv @ v), rel_tol=1e-6) and math.isclose(0.5 * (lo + hi), float(v @ m[0]), rel_tol=1e-6, abs_tol=1e-9)
    assert fv.support_interval(f, t0, kernel[0], c0) == (-math.inf, math.inf)


# ------------------------------------------------------------------ T3
def test_t3_unidentified_direction_posterior_is_the_conditional_prior_and_bounded_sets_lose_coverage():
    rng = np.random.default_rng(SEED + 3)
    d, r = 5, 3
    jr = rng.standard_normal((7, r)) @ rng.standard_normal((r, d))
    f = jr.T @ jr                                                     # singular precision, kernel of dimension d - r
    basis = np.linalg.svd(f)[2]                                       # rows: r identified directions, then the kernel
    prior = _spd(rng, d)                                              # proper Gaussian prior N(0, prior), correlated
    post_prec = f + np.linalg.inv(prior)
    rot_prior, rot_post = basis @ np.linalg.inv(prior) @ basis.T, basis @ post_prec @ basis.T
    # conditional law of the kernel coordinates given the identified ones: precision block and regression map are unchanged
    assert np.allclose(rot_post[r:, r:], rot_prior[r:, r:], rtol=1e-9, atol=1e-11)
    assert np.allclose(rot_post[r:, :r], rot_prior[r:, :r], rtol=1e-9, atol=1e-11)
    # coverage of the 95% credible interval of v.theta, v in the kernel, as the truth moves along the kernel
    v, cov_post = basis[r], np.linalg.inv(post_prec)
    half = stats.norm.ppf(0.975) * math.sqrt(v @ cov_post @ v)
    gain = cov_post @ f                                               # posterior mean = gain @ theta_true + noise
    sd_mean = math.sqrt(v @ cov_post @ f @ cov_post @ v)
    theta0 = rng.standard_normal(d)
    cover = []
    for shift in (0.0, 2.0, 50.0):
        truth = theta0 + shift * half * v                             # same data law for every shift (F v = 0)
        assert np.allclose(f @ truth, f @ theta0, atol=1e-9 * np.abs(f).max() * (1 + shift * half))
        delta = float(v @ truth - v @ gain @ truth)
        cover.append(float(stats.norm.cdf((half - delta) / sd_mean) - stats.norm.cdf((-half - delta) / sd_mean)))
    # the interval is as wide as the conditional prior: it covers a truth near the prior centre almost surely and a truth
    # two half-widths away almost never, although the data law is the same in both cases
    assert cover[0] > 0.99 and cover[1] < 1e-12 and cover[2] <= cover[1]


# ------------------------------------------------------------------ T5
def test_t5_exact_second_moments_with_a_simulated_covariance():
    rng = np.random.default_rng(SEED + 5)
    n, p, k, n_draw = 30, 8, 3, 6000
    fac = idn.wishart_gls_factors(n, p, k)
    assert math.isclose(math.sqrt(fac["variance_ratio"]), fv.finite_mc_sd_inflation(n + 1, p, k), rel_tol=1e-12)
    assert idn.wishart_gls_factors(n, p, p) == {"cov_factor": 1.0, "plugin_factor": 1.0, "variance_ratio": 1.0}
    j, sigma = rng.standard_normal((p, k)), _spd(rng, p)
    chol = np.linalg.cholesky(sigma)
    v_true = np.linalg.inv(j.T @ np.linalg.solve(sigma, j))
    est, plug = np.empty((n_draw, k)), np.zeros((k, k))
    for i in range(n_draw):
        x = rng.standard_normal((n, p)) @ chol.T
        s = x.T @ x / n                                               # n S ~ W_p(n, Sigma)
        y = rng.standard_normal(p) @ chol.T                           # theta = 0
        sj = np.linalg.solve(s, j)
        v_hat = np.linalg.inv(j.T @ sj)
        est[i], plug = v_hat @ (sj.T @ y), plug + v_hat / n_draw
    w = np.linalg.inv(np.linalg.cholesky(v_true))                     # whiten with the true V
    emp_cov, emp_plug = w @ np.cov(est, rowvar=False) @ w.T, w @ plug @ w.T
    assert abs(np.trace(emp_cov) / k - fac["cov_factor"]) < 0.05 * fac["cov_factor"]
    assert abs(np.trace(emp_plug) / k - fac["plugin_factor"]) < 0.02 * fac["plugin_factor"]
    assert fac["cov_factor"] > 1.10 and fac["plugin_factor"] < 0.90   # both effects are resolved by the tolerances
    # algebraic step of the proof: in a basis with J = Q [R; 0], theta_hat = R^-1 (y_1 - S_12 S_22^-1 y_2)
    q_full, r_full = np.linalg.qr(j, mode="complete")
    s_rot, y_rot = q_full.T @ s @ q_full, q_full.T @ y
    direct = np.linalg.solve(r_full[:k], y_rot[:k] - s_rot[:k, k:] @ np.linalg.solve(s_rot[k:, k:], y_rot[k:]))
    assert np.allclose(direct, est[-1], rtol=1e-8, atol=1e-10)
    with pytest.raises(ValueError):
        idn.wishart_gls_factors(5, 8, 3)



def test_t5_covariance_factor_discriminates_neighbouring_laws():
    """Review finding R54-A1-02: at q/n = 1/2 the stated factor (n-1)/(n-q-1) is separated from its neighbours by the tolerance."""
    rng = np.random.default_rng(SEED + 51)
    n, p, k, n_draw = 20, 12, 2, 40000
    q = p - k
    fac = idn.wishart_gls_factors(n, p, k)["cov_factor"]
    assert math.isclose(fac, (n - 1) / (n - q - 1), rel_tol=1e-12)
    tol = 0.025                                                                      # about 4.7 Monte Carlo standard errors
    for wrong in ((n - 1) / (n - q), n / (n - q - 1), n / (n - q), (n - 2) / (n - q - 2), (n - 1) / (n - q - 2)):
        assert abs(wrong - fac) > 2.0 * tol * fac, wrong                             # every neighbour lies outside twice the tolerance
    j = rng.standard_normal((p, k))
    sigma = _spd(rng, p)
    chol = np.linalg.cholesky(sigma)
    v_true = np.linalg.inv(j.T @ np.linalg.solve(sigma, j))
    x = rng.standard_normal((n_draw, n, p)) @ chol.T
    s = np.einsum("dni,dnj->dij", x, x) / n                                          # n S ~ W_p(n, Sigma)
    y = rng.standard_normal((n_draw, p)) @ chol.T                                    # theta = 0
    sj = np.linalg.solve(s, np.broadcast_to(j, (n_draw, p, k)))
    v_hat = np.linalg.inv(np.einsum("pk,dpl->dkl", j, sj))
    est = np.einsum("dkl,dpl,dp->dk", v_hat, sj, y)
    w = np.linalg.inv(np.linalg.cholesky(v_true))
    emp = float(np.trace(w @ np.cov(est, rowvar=False) @ w.T) / k)
    assert abs(emp - fac) < tol * fac, (emp, fac)

# ------------------------------------------------------------------ T6
EXPECTED_O3 = {("polar", "scalar"): 1, ("axial", "scalar"): 0, ("stf2", "scalar"): 1, ("pseudo_stf2", "scalar"): 0,
               ("polar", "pseudoscalar"): 0, ("axial", "pseudoscalar"): 1, ("stf2", "pseudoscalar"): 0, ("pseudo_stf2", "pseudoscalar"): 1,
               ("polar", "vector"): 1, ("axial", "vector"): 1, ("stf2", "vector"): 1, ("pseudo_stf2", "vector"): 1}


def test_t6_selection_rule_counted_without_schur():
    for (kin, obs), expected in EXPECTED_O3.items():
        assert idn.equivariant_response_rank(kin, obs) == expected, (kin, obs)
    # without parity (rotations only) every scalar-type field couples and every vector field gains its second pattern
    for kin in idn.KIN_KINDS:
        assert idn.equivariant_response_rank(kin, "scalar", parity=False) == 1
        assert idn.equivariant_response_rank(kin, "vector", parity=False) == 2
    # leading-order scalar observable: expansion (1) + polar vector (3) + shear (5) and no vorticity column: 9 numbers
    dims = {"polar": 3, "axial": 3, "stf2": 5}
    assert 1 + sum(dims[kin] * EXPECTED_O3[(kin, "scalar")] for kin in dims) == 9
    # C6.5: the count is unchanged when the solutions are compared on a polar cap only
    cap = lambda n: n[:, 2] > 0.6                                     # noqa: E731
    assert idn.equivariant_response_rank("stf2", "vector", region=cap) == 1 and idn.equivariant_response_rank("axial", "scalar", region=cap) == 0


def test_t6_closed_form_patterns_and_representations():
    rng = np.random.default_rng(SEED + 6)
    n = idn._unit(rng.standard_normal((20, 3)))
    a, w = rng.standard_normal(3), rng.standard_normal(3)
    coef = rng.standard_normal(5)
    s = np.einsum("k,kij->ij", coef, fv.STF5_BASIS)
    for proper in (True, False):
        g = idn._group_element(rng, proper)
        det, gn = np.sign(np.linalg.det(g)), n @ g.T
        for kind in idn.KIN_KINDS:                                    # orthogonal representations with the right inversion sign
            rho = idn.rep_matrix(kind, g)
            assert np.allclose(rho @ rho.T, np.eye(rho.shape[0]), atol=1e-12)
        assert np.allclose(idn.rep_matrix("axial", -np.eye(3)), np.eye(3)) and np.allclose(idn.rep_matrix("polar", -np.eye(3)), -np.eye(3))
        assert np.allclose(idn.rep_matrix("stf2", -np.eye(3)), np.eye(5)) and np.allclose(idn.rep_matrix("pseudo_stf2", -np.eye(3)), -np.eye(5))
        gs = g @ s @ g.T
        assert np.allclose(np.einsum("k,kij->ij", idn.rep_matrix("stf2", g) @ coef, fv.STF5_BASIS), gs, atol=1e-12)
        # spheroidal dipole from a polar vector, toroidal dipole from an axial vector, spheroidal quadrupole from the shear
        sph1 = lambda x, v: v[None, :] - (x @ v)[:, None] * x         # noqa: E731
        tor1 = lambda x, v: np.cross(v[None, :], x)                   # noqa: E731
        sph2 = lambda x, m: x @ m.T - np.einsum("pi,ij,pj->p", x, m, x)[:, None] * x   # noqa: E731
        assert np.allclose(sph1(gn, g @ a), sph1(n, a) @ g.T, atol=1e-12)
        assert np.allclose(tor1(gn, det * g @ w), tor1(n, w) @ g.T, atol=1e-12)
        assert np.allclose(sph2(gn, gs), sph2(n, s) @ g.T, atol=1e-12)
        # a rotation pattern sourced by a POLAR vector is equivariant under rotations and fails under reflections
        ok = np.allclose(tor1(gn, g @ a), tor1(n, a) @ g.T, atol=1e-12)
        assert ok == proper


def test_t6_block_bookkeeping_and_null_channels():
    res = idn.block_identification({
        (1, "+"): np.array([[1.0, -1.0]]),            # toroidal proper-motion dipole: vorticity minus frame spin (T7b)
        (1, "-"): np.eye(2),                          # two polar vectors seen by two independent dipole slots
        (2, "+"): np.array([[1.0], [0.3]]),           # one shear amplitude seen by two quadrupole slots
        (2, "-"): np.zeros((2, 0)),                   # B_2 and the toroidal proper-motion quadrupole: slots without a source
    })
    assert res["blocks"]["1+"] == {"slots": 1, "copies": 2, "rank": 1, "nullity": 1, "unidentified_dimension": 3}
    assert res["blocks"]["2-"]["rank"] == 0 and res["blocks"]["2-"]["nullity"] == 0
    assert res["unidentified_dimension"] == 3 and res["identified"] is False
    assert idn.block_identification({(1, "+"): np.array([[1.0, -1.0], [0.0, 1.0]])})["identified"] is True   # with a dynamical frame tie


# ------------------------------------------------------------------ T7
def test_t7a_zero_point_gauge_orbit_and_testable_combinations():
    rng = np.random.default_rng(SEED + 7)
    dirs = [idn._unit(rng.standard_normal((60, 3))) for _ in range(3)]
    south = idn._unit(rng.standard_normal((300, 3)))
    dirs.append(south[south[:, 2] < -0.2][:60])                        # a hemisphere-limited sample
    k = len(dirs)
    res = idn.zero_point_gauge(dirs)
    assert (res["n_parameters"], res["rank"], res["nullity"]) == (3 * (k + 1), 3 * k, 3)
    eps = rng.standard_normal(3)                                       # the orbit (delta + eps, d_p - eps) leaves every mean unchanged
    orbit = np.concatenate([eps] + [-eps] * k)
    assert np.abs(res["design"] @ orbit).max() < 1e-12
    assert np.allclose(res["null_basis"].T @ (res["null_basis"] @ orbit), orbit, atol=1e-10)   # and it is the whole null space
    for p in range(k):                                                 # delta + d_p is identified: it is orthogonal to the null space
        for axis in range(3):
            v = np.zeros(res["n_parameters"])
            v[axis], v[3 * (p + 1) + axis] = 1.0, 1.0
            assert np.abs(res["null_basis"] @ v).max() < 1e-10
    v = np.zeros(res["n_parameters"])
    v[0] = 1.0                                                         # delta alone is not
    assert np.abs(res["null_basis"] @ v).max() > 0.1
    # a velocity law is identified next to the constant terms if its response varies with depth (generic g; T7a iii gives the sufficient condition)
    g_var = [rng.uniform(0.5, 3.0, size=d.shape[0]) for d in dirs]
    g_const = [np.full(d.shape[0], 1.7) for d in dirs]
    assert idn.zero_point_gauge(dirs, g_var)["nullity"] == 3
    assert idn.zero_point_gauge(dirs, g_const)["nullity"] == 6


def test_t7a_monopoles_need_the_vectors_one_n_to_span_r4():
    """Review finding R54-A1-01: with a free monopole h_p per sample the orbit is three-dimensional only if (1, n_i) spans R^4."""
    rng = np.random.default_rng(SEED + 71)
    full = idn._unit(rng.standard_normal((80, 3)))
    phi = rng.uniform(0.0, 2.0 * np.pi, 80)
    ring = np.column_stack([math.sqrt(0.75) * np.cos(phi), math.sqrt(0.75) * np.sin(phi), np.full(80, 0.5)])   # n_z = 0.5: spans R^3
    assert np.linalg.matrix_rank(ring) == 3 and np.linalg.matrix_rank(np.column_stack([np.ones(80), ring])) == 3
    assert idn.zero_point_gauge([full, ring])["nullity"] == 3                       # without monopoles: the orbit only
    res = idn.zero_point_gauge([full, ring], monopoles=True)
    assert res["n_parameters"] == 11 and res["nullity"] == 4                         # the extra null vector h_2 = -u/2, delta + d_2 = u e_z
    extra = np.zeros(11)
    extra[3 * 2 + 2], extra[10] = 1.0, -0.5
    assert np.abs(res["design"] @ extra).max() < 1e-12
    south = idn._unit(rng.standard_normal((400, 3)))
    cap = south[south[:, 2] < -0.2][:80]                                            # a cap: (1, n_i) spans R^4
    assert np.linalg.matrix_rank(np.column_stack([np.ones(cap.shape[0]), cap])) == 4
    assert idn.zero_point_gauge([full, cap], monopoles=True)["nullity"] == 3
    g = [rng.uniform(0.5, 3.0, size=d.shape[0]) for d in (full, cap)]
    assert idn.zero_point_gauge([full, cap], g, monopoles=True)["nullity"] == 3


def test_t7c_depth_law_noncentrality_is_a_design_quantity():
    rng = np.random.default_rng(SEED + 8)
    k = 4
    g, c = rng.uniform(0.5, 3.0, size=k), _spd(rng, k)
    res = idn.depth_law_noncentrality(g, c)
    assert np.allclose(res["Lambda"], res["scalar"] * np.eye(3), rtol=1e-9, atol=1e-12) and 0.0 < res["sin2_angle"] <= 1.0
    # direct computation: drop in residual chi2 of a noise-free vector when the velocity column is added to the constant one
    v = rng.standard_normal(3)
    y = np.kron(g, v)
    full = np.kron(c, np.eye(3))
    fit_a = fv.gls_fit(y, full, np.kron(np.ones((k, 1)), np.eye(3)))
    assert math.isclose(fit_a["chi2"], float(v @ res["Lambda"] @ v), rel_tol=1e-8)
    flat = idn.depth_law_noncentrality(np.full(k, 2.0), c)             # a depth-independent response cannot be told from a constant
    assert abs(flat["scalar"]) < 1e-9 and np.abs(flat["Lambda"]).max() < 1e-9
    big = idn.depth_law_noncentrality(g, _spd(rng, 3 * k))             # general cross-depth covariance
    assert np.linalg.eigvalsh(big["Lambda"]).min() > 0.0


# ------------------------------------------------------------------ T8
@pytest.fixture(scope="module")
def kernels():
    tab = np.loadtxt(FIX / "planck18_tau_history.csv", delimiter=",", skiprows=1)
    hist = th.OpticalDepthHistory(tab[:, 0], tab[:, 1], th.planck18_background().e2)
    z = np.concatenate([[0.0], np.geomspace(1e-3, 1400.0, 600)])
    n = -np.log1p(z)                                                   # N = ln a, decreasing along the grid
    tau = np.array([hist.tau(v) for v in n])
    kt, ke = th.thomson_kernels(tau)
    w = np.empty_like(n)                                               # trapezoid weights in N (positive)
    w[1:-1], w[0], w[-1] = 0.5 * (n[:-2] - n[2:]), 0.5 * (n[0] - n[1]), 0.5 * (n[-2] - n[-1])
    return {"tau": tau, "kt": kt, "ke": ke, "w": w, "rho": idn.rho_ratio(tau)}


def test_t8_kernel_properties(kernels):
    tau, kt, ke, rho = (kernels[k] for k in ("tau", "kt", "ke", "rho"))
    assert tau[0] == 0.0 and (np.diff(tau) > 0).all()                  # kappa > 0: strictly monotone optical depth
    assert np.allclose(ke[1:] / kt[1:], rho[1:], rtol=1e-10) and (np.diff(rho) > 0).all() and 0.0 <= rho[0] and rho[-1] < math.sqrt(6.0)
    assert (np.diff(kt) < 0).all() and kt[0] == 1.0
    assert (ke <= math.sqrt(6.0) / 10.0 * tau + 1e-15).all() and (kt >= 1.0 - 0.9 * tau - 1e-15).all()
    t = np.linspace(0.0, 30.0, 30001)                                  # the two bounds and the monotone ratio for every optical depth
    k_t, k_e = th.thomson_kernels(t)
    assert (k_e <= math.sqrt(6.0) / 10.0 * t + 1e-15).all() and (k_t >= 1.0 - 0.9 * t - 1e-15).all() and (np.diff(idn.rho_ratio(t)) > 0).all()
    t_star = math.log(10.0 / 3.0) / 0.7                                # location of the maximum of K_E
    assert th.thomson_kernels(t_star)[1] >= k_e.max() - 1e-12


def test_t8_sign_changes_of_the_shear_history(kernels):
    rng = np.random.default_rng(SEED + 9)
    kt, ke, w, rho = (kernels[k] for k in ("kt", "ke", "w", "rho"))
    size = kt.size

    def functionals(s):
        return float(np.sum(w * kt * s)), float(np.sum(w * ke * s))

    for _ in range(100):                                               # (iii-a) constant sign: ratio inside the rho range, L1 norm bounded by Sigma_T
        lo = int(rng.integers(0, size - 12))
        hi = int(rng.integers(lo + 10, size))
        s = np.zeros(size)
        s[lo:hi] = rng.uniform(0.1, 1.0, size=hi - lo)
        s_t, s_e = functionals(s)
        assert rho[lo] * s_t * (1 - 1e-12) - 1e-300 <= s_e <= rho[hi - 1] * s_t * (1 + 1e-12)
        assert np.sum(w * s) <= s_t / kt[hi - 1] * (1 + 1e-12)
    for _ in range(100):                                               # (iii-b) one sign change: exact weighted-norm identity, never annihilated
        cut = int(rng.integers(5, size - 5))
        s = rng.uniform(0.1, 1.0, size=size) * np.where(np.arange(size) < cut, 1.0, -1.0)
        s_t, s_e = functionals(s)
        rho_c = 0.5 * (rho[cut - 1] + rho[cut])
        weighted = float(np.sum(w * np.abs(rho - rho_c) * kt * np.abs(s)))
        assert math.isclose(abs(s_e - rho_c * s_t), weighted, rel_tol=1e-10) and weighted > 0.0
    # (iii-c, d) a history annihilated by both functionals exists and changes sign exactly twice
    for _ in range(50):
        edges = np.sort(rng.choice(np.arange(5, size - 5), size=6, replace=False))
        bumps = np.zeros((3, size))
        for b in range(3):
            bumps[b, edges[2 * b]:edges[2 * b + 1] + 1] = 1.0
        moments = np.array([[np.sum(w * kt * b) for b in bumps], [np.sum(w * ke * b) for b in bumps]])
        coef = np.linalg.svd(moments)[2][-1]
        s = coef @ bumps
        s_t, s_e = functionals(s)
        assert abs(s_t) < 1e-12 * np.abs(moments[0]).max() and abs(s_e) < 1e-12 * np.abs(moments[1]).max()
        assert idn.count_sign_changes(s) == 2 and coef[0] * coef[1] < 0 and coef[1] * coef[2] < 0
    # (iv) least-norm history; adding a kernel element keeps the functionals and raises the norm without bound
    target = np.array([1.0e-5, 3.0e-7])
    best = idn.minimal_norm_history(kt, ke, w, target)
    assert np.allclose(functionals(best["history"]), target, rtol=1e-9)
    for scale in (1.0, 1.0e3):
        other = best["history"] + scale * best["norm"] * s / math.sqrt(np.sum(w * s * s))
        assert np.allclose(functionals(other), target, rtol=1e-6) and math.sqrt(np.sum(w * other * other)) >= best["norm"] * math.sqrt(1 + 0.99 * scale**2)
    late = slice(0, 40)                                                # z < about 0.03: both kernels are nearly proportional, the problem is ill-conditioned
    assert np.linalg.cond(idn.history_gram(kt[late], ke[late], w[late])) > 1e6
    with pytest.raises(ValueError):
        idn.minimal_norm_history(kt[:1], ke[:1], w[:1], target)


# ------------------------------------------------------------------ T9
def test_t9_frame_closure_identity_and_degrees_of_freedom():
    rng = np.random.default_rng(SEED + 10)
    c = 299792.458
    v_obs, v_rad = rng.standard_normal(3) * 300.0, rng.standard_normal(3) * 300.0
    shells = rng.standard_normal((4, 3)) * 300.0                      # matter-frame velocity of each depth shell
    d_cmb = (v_obs - v_rad) / c
    for k_eb, v_m in zip((2.9, 3.4, 4.1, 5.0), shells):                # counts of a population in that shell; bulk flow of the shell
        d_counts = k_eb * (v_obs - v_m) / c
        assert np.abs(d_counts / k_eb - d_cmb + (v_m - v_rad) / c).max() < 1e-15
    # global tilt: one V for all shells; n_c count populations and n_d distance shells leave 3 (n_c + n_d - 1) residual degrees of freedom
    n_c, n_d = 2, 4
    design = np.vstack([np.kron(np.ones((n_c, 1)), -np.eye(3) / c), np.kron(np.ones((n_d, 1)), np.eye(3))])
    assert design.shape[0] - np.linalg.matrix_rank(design) == 3 * (n_c + n_d - 1)


# ------------------------------------------------------------------ L1
def test_l1_errors_in_variables_bias_identity():
    rng = np.random.default_rng(SEED + 11)
    h, n_obj = 70.0, 400
    dist = rng.uniform(50.0, 400.0, size=n_obj)
    s = np.where(rng.random(n_obj) < 0.5, 0.21, 0.07)                  # two indicator classes with different distance errors
    eps = rng.standard_normal(n_obj)
    d_obs = dist * np.exp(s * eps)
    wgt = 1.0 / (s * d_obs) ** 2                                       # distance-noise dominated weights of the linear estimator
    slope = np.sum(wgt * d_obs * h * dist) / np.sum(wgt * d_obs**2)    # weighted regression of c z = H D on the noisy d
    assert math.isclose(slope, h * np.sum(np.exp(-s * eps) / s**2) / np.sum(1.0 / s**2), rel_tol=1e-12)
    x, wq = np.polynomial.hermite_e.hermegauss(60)                     # E exp(-s eps) = exp(s^2/2)
    for sv in (0.07, 0.21, 0.4):
        assert math.isclose(float(np.sum(wq * np.exp(-sv * x)) / math.sqrt(2.0 * math.pi)), math.exp(0.5 * sv * sv), rel_tol=1e-12)
    assert math.isclose(float(np.sum(wq * (-0.21 * x)) / math.sqrt(2.0 * math.pi)), 0.0, abs_tol=1e-14)   # ln d is unbiased
