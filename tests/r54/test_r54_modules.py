"""R54 module tests: Thomson history kernels, LCDM body, tensor five-view calculus.

Each test names the equation (R54-EQ-xx) or gate (MG-xx) it protects so that a
failing test maps back to LOCAL_AGENT_CONTRACT.json without interpretation.
"""
from __future__ import annotations

import math
from pathlib import Path

import numpy as np
import pytest
from scipy import stats
from scipy.linalg import expm

from htt.htt.infer import r54_distance_estimators as de
from htt.htt.infer import r54_lcdm_body as lb
from htt.htt.infer import r54_tensor_five_view as fv
from htt.htt.infer import r54_type1_thomson as th

ROOT = Path(__file__).resolve().parents[2]
FIX = ROOT / "tests/fixtures/r54"


@pytest.fixture(scope="module")
def history():
    tab = np.loadtxt(FIX / "planck18_tau_history.csv", delimiter=",", skiprows=1)
    bg = th.planck18_background()
    return bg, th.OpticalDepthHistory(tab[:, 0], tab[:, 1], bg.e2)


@pytest.fixture(scope="module")
def pk():
    tab = np.loadtxt(FIX / "planck18_linear_pk_z0.csv", delimiter=",", skiprows=1)
    return tab[:, 0], tab[:, 1]


# ------------------------------------------------------------------ Thomson
def test_eq03_propagator_closed_form_matches_matrix_exponential():
    for tau in (0.0, 0.03, 0.7, 1.72, 9.0, 40.0):
        assert np.allclose(th.thomson_propagator(tau), expm(-th.THOMSON_M * tau), rtol=0, atol=1e-13)
    assert np.allclose(np.linalg.eigvalsh(th.THOMSON_M), [0.3, 1.0], atol=1e-14)


def test_eq03_sympy_seal_of_kernels():
    sp = pytest.importorskip("sympy")
    tau = sp.symbols("tau", nonnegative=True)
    m = sp.Matrix([[sp.Rational(9, 10), sp.sqrt(6) / 10], [sp.sqrt(6) / 10, sp.Rational(2, 5)]])
    prop = sp.simplify((-m * tau).exp())
    k_t = (6 * sp.exp(-tau) + sp.exp(-sp.Rational(3, 10) * tau)) / 7
    k_e = sp.sqrt(6) / 7 * (sp.exp(-sp.Rational(3, 10) * tau) - sp.exp(-tau))
    assert sp.simplify(prop[0, 0] - k_t) == 0
    assert sp.simplify(-prop[1, 0] - k_e) == 0
    # thin limit: one scattering converts sqrt6/10 of the quadrupole into E
    assert sp.simplify(sp.diff(k_e, tau).subs(tau, 0) - sp.sqrt(6) / 10) == 0
    assert sp.simplify(sp.diff(k_t, tau).subs(tau, 0) + sp.Rational(9, 10)) == 0


def test_eq03_kernel_shape():
    tau = np.linspace(0, 60, 6001)
    k_t, k_e = th.thomson_kernels(tau)
    assert k_t[0] == 1.0 and k_e[0] == 0.0
    assert (k_e >= 0).all() and (np.diff(k_t) < 0).all()            # MG-01: E has the sign of T
    i = int(np.argmax(k_e))
    assert abs(tau[i] - math.log(10 / 3) / 0.7) < 0.011
    assert abs(k_e[i] - 0.146212577918735) < 1e-6
    assert k_t[-1] < 1e-7 and k_e[-1] < 1e-7
    with pytest.raises(ValueError):
        th.thomson_kernels(-1.0)


def test_eq04_kernel_form_equals_ode_form_for_perfect_fluid(history):
    bg, hist = history
    n_hi = -math.log1p(1.0e4)
    pf = lambda n: float(th.perfect_fluid_shear(bg, n)[0])  # noqa: E731
    ker = th.history_functionals(pf, hist, n_hi)
    ode = th.solve_type1_history(bg, hist, th.STRESS_NONE, z_init=1.0e4, s_init=pf(n_hi))
    assert abs(ode["Sigma_T"] / ker["Sigma_T"] - 1) < 2e-6
    assert abs(ode["Sigma_E"] / ker["Sigma_E"] - 1) < 2e-6
    assert abs(ode["s_today"] - 1.0) < 1e-6
    # regression values bound to the committed tau fixture
    assert abs(ker["Sigma_T"] - 35955.97) < 5.0
    assert abs(ker["Sigma_E"] / ker["Sigma_T"] - 0.071101) < 2e-5
    assert ker["Sigma_E"] / ker["Sigma_T"] > 0                       # MG-01


def test_eq05_radiation_era_oscillator_matches_analytic_solution(history):
    """Deep radiation era, tight photons: u'' + u' + (8/5) f_nu u = 0 with u = int s dN."""
    bg, hist = history
    f_nu = bg.omega_nu / (bg.omega_gamma + bg.omega_nu)
    omega = math.sqrt(1.6 * f_nu - 0.25)
    z0, z1 = 1.0e10, 1.0e8
    dn = math.log((1 + z0) / (1 + z1))
    n_eval = np.array([-math.log1p(z1)])
    out = th.solve_type1_history(bg, hist, th.STRESS_PHOTON_NEUTRINO, z_init=z0, n_eval=n_eval, z_tight=5.0e4)
    s_num = float(out["y"][0, 0])
    s_ana = math.exp(-dn / 2) * (math.cos(omega * dn) - math.sin(omega * dn) / (2 * omega))
    assert abs(s_num - s_ana) < 2e-3 * math.exp(-dn / 2)
    # without stress the shear decays as 1/a in the radiation era
    free = th.solve_type1_history(bg, hist, th.STRESS_NONE, z_init=z0, n_eval=n_eval)
    assert abs(float(free["y"][0, 0]) / math.exp(-dn) - 1) < 2e-3


def test_eq05_stress_changes_present_shear_sign_and_scale(history):
    bg, hist = history
    photon = th.solve_type1_history(bg, hist, th.STRESS_PHOTON, z_init=1.0e5)
    ratio = photon["s_today"] / photon["Sigma_T"]
    assert -2.6e-4 < ratio < -2.3e-4                                 # regression: -2.445e-4
    a = th.solve_type1_history(bg, hist, th.STRESS_PHOTON_NEUTRINO, z_init=1.0e5, s_init=1.0, ncal_init=0.0)
    b = th.solve_type1_history(bg, hist, th.STRESS_PHOTON_NEUTRINO, z_init=1.0e5, s_init=0.0, ncal_init=1.0)
    m = np.array([[a["Sigma_T"], b["Sigma_T"]], [a["Sigma_E"], b["Sigma_E"]]])
    assert abs(np.linalg.det(m)) > 1e-6                              # T and E functionals are independent
    c = np.array([a["s_today"], b["s_today"]]) @ np.linalg.inv(m)
    assert abs(c[0] / 1.66166e-3 - 1) < 0.01 and abs(c[1] / -2.54120e-2 - 1) < 0.01
    with pytest.raises(ValueError):
        th.solve_type1_history(bg, hist, "unknown", z_init=10.0)


def test_eq06_massive_neutrino_stress_weight(history):
    from scipy import integrate as sint

    def direct(mu):                                                  # same integral with adaptive quadrature
        num = sint.quad(lambda x: x**4 * (4 * x * x + 5 * mu * mu) / (x * x + mu * mu) ** 1.5 / (math.exp(x) + 1.0), 0.0, 60.0, limit=200)[0]
        return num / (4.0 * 7.0 * math.pi**4 / 120.0)                # int x^3/(e^x+1) = 7 pi^4/120

    w = th.massive_stress_weight(np.array([0.0, 0.3, 3.0, 30.0, 1000.0]))
    assert abs(w[0] - 1.0) < 1e-10 and (np.diff(w) < 0).all()
    for mu, val in zip((0.3, 3.0, 30.0), w[1:4]):
        assert abs(val / direct(mu) - 1.0) < 1e-6
    i4, i3 = 45.0 * 1.0369277551433699 / 2.0, 7.0 * math.pi**4 / 120.0   # int x^4/(e^x+1) = (45/2) zeta(5)
    assert abs(w[4] / (5.0 * i4 / (4.0 * 1000.0 * i3)) - 1.0) < 1e-3   # MG-20: non-relativistic limit, stress ~ pressure
    scale = th.neutrino_stress_scale((0.0, 0.00868, 0.0503))
    t_nu0 = (4.0 / 11.0) ** (1.0 / 3.0) * 2.72548 * th.K_B_EV_PER_K
    today = (1.0 + th.massive_stress_weight(0.00868 / t_nu0)[0] + th.massive_stress_weight(0.0503 / t_nu0)[0]) / 3.0
    assert abs(scale(-20.0) - 1.0) < 1e-6 and abs(scale(0.0) / today - 1.0) < 1e-6 and 1.0 / 3.0 < today < 0.40
    bg, hist = history
    light = th.solve_type1_history(bg, hist, th.STRESS_PHOTON_NEUTRINO, z_init=1.0e5, neutrino_stress_scale=th.neutrino_stress_scale((0.0, 0.0, 0.0)))
    ref = th.solve_type1_history(bg, hist, th.STRESS_PHOTON_NEUTRINO, z_init=1.0e5)
    assert abs(light["s_today"] / ref["s_today"] - 1.0) < 1e-6          # massless limit reproduces R54-EQ-05
    with pytest.raises(ValueError):
        th.massive_stress_weight(-1.0)


def test_optical_depth_table_guards(history):
    bg, hist = history
    assert abs(hist.tau(-math.log1p(50.0)) - 0.0545551) < 2e-6
    assert 1.04 < hist.tau(-math.log1p(1089.94)) < 1.07
    assert hist.kappa(-math.log1p(2.0e4)) > hist.kappa(-math.log1p(1.0e4)) > 0
    with pytest.raises(ValueError):
        hist.tau(0.1)
    with pytest.raises(ValueError):
        th.OpticalDepthHistory(np.arange(20.0) + 1, np.arange(20.0), bg.e2)


# ---------------------------------------------------------------- LCDM body
def test_eq11_point_window_recovers_velocity_dispersion(pk):
    k, p = pk
    sel = k < 2.0
    k, p = k[sel], p[sel]
    f, h0 = lb.growth_rate(0.3153), 67.36
    win = lb.gaussian_window(0.02, 0.002, 1.0)
    c1 = lb.harmonic_cosmic_cov(1, k, p, [win], f, h0)[0, 0]
    var_axis = lb.CARTESIAN_FACTOR[1] * c1
    assert abs(var_axis / lb.point_velocity_dispersion_1d(k, p, f, h0) - 1) < 2e-3
    assert abs(win.norm - 1.0) < 1e-12


def test_eq11_eq12_stacked_body_structure(pk):
    k, p = pk
    a = np.array([0.0105, 0.0074, 0.0047, 0.0033])
    wins = [lb.gaussian_window(1 / x, 48.0, x) for x in a]
    body = lb.stacked_window_body(k, p, wins, lb.growth_rate(0.3153), 67.36)
    assert body.shape == (36, 36) and np.allclose(body, body.T)
    assert np.linalg.eigvalsh(body)[0] > -1e-12
    assert body[1, 4] == 0.0 and body[0, 1] == 0.0                   # different ell uncorrelated on the ideal sky
    assert np.allclose(body[1, 1], body[2, 2]) and np.allclose(body[4, 4], body[8, 8])
    bulk_sd = np.sqrt(np.diag(body))[1::9] / a
    assert (np.diff(bulk_sd) < 0).all() and 60 < bulk_sd[-1] < bulk_sd[0] < 160
    corr = body[1, 10] / math.sqrt(body[1, 1] * body[10, 10])
    assert 0.5 < corr < 1.0
    assert lb.CARTESIAN_FACTOR == {0: 1 / (4 * math.pi), 1: 3 / (4 * math.pi), 2: 15 / (8 * math.pi)}
    with pytest.raises(ValueError):
        lb.window_integral(3, k, wins[0])


# --------------------------------------------------------------- five views
def test_stf5_basis_and_invariants():
    g = np.einsum("aij,bij->ab", fv.STF5_BASIS, fv.STF5_BASIS)
    assert np.allclose(g, np.eye(5), atol=1e-14)
    assert np.allclose(np.trace(fv.STF5_BASIS, axis1=1, axis2=2), 0)
    q = np.array([0.3, -1.2, 0.4, 0.1, 0.7])
    assert np.allclose(fv.matrix_to_stf5(fv.stf5_to_matrix(q)), q)
    n = np.array([0.3, -0.5, 0.81])
    n /= np.linalg.norm(n)
    assert abs(n @ fv.stf5_to_matrix(q) @ n - q @ fv.quadratic_direction(n)) < 1e-14
    assert abs(np.linalg.norm(fv.axisymmetric_stf5(n)) - 1) < 1e-14
    assert abs(fv.stf2_invariants(fv.axisymmetric_stf5(n))["shape"] - 1) < 1e-12
    assert abs(fv.stf2_invariants(-fv.axisymmetric_stf5(n))["shape"] + 1) < 1e-12
    axi = fv.axisymmetry_statistic(2.5 * fv.axisymmetric_stf5(n), np.eye(5))
    assert axi["statistic"] < 1e-10 and abs(abs(np.dot(axi["axis"], n)) - 1) < 1e-5


def test_eq20_gauge_range_exact_in_two_dimensions():
    rng = np.random.default_rng(54)
    ang = np.linspace(0, 2 * np.pi, 400001)
    circ = np.stack([np.cos(ang), np.sin(ang)], axis=1)
    for _ in range(12):
        a = rng.normal(size=(2, 2))
        f = a @ a.T + 0.05 * np.eye(2)
        m = rng.normal(size=2) * rng.choice([0.2, 3.0])
        b = rng.normal(size=(2, 2))
        bmat = b @ b.T + 0.1 * np.eye(2)
        c2 = float(rng.choice([0.4, 2.3, 9.0]))
        r = fv.gauge_range(f, f @ m, fv.EllipsoidBody("test body", bmat), c2)
        pts = m + math.sqrt(c2) * circ @ np.linalg.cholesky(np.linalg.inv(f)).T
        g = np.sqrt(np.einsum("ni,ij,nj->n", pts, np.linalg.inv(bmat), pts))
        inside = m @ f @ m <= c2
        assert abs(r["Q_max"] - g.max()) < 1e-8 * g.max()
        assert abs(r["Q_min"] - (0.0 if inside else g.min())) < 1e-8 * max(g.min(), 1.0)
        if not inside:                                               # R54-EQ-21 duality at the touching point
            v = np.linalg.solve(bmat, np.asarray(r["theta_at_Q_min"]))
            lo, _ = fv.support_interval(f, f @ m, v, math.sqrt(c2))
            assert abs(lo / fv.EllipsoidBody("test body", bmat).support(v) - r["Q_min"]) < 1e-7 * r["Q_min"]


def test_eq21_support_interval_in_scaled_coordinates():
    """R54-IR-08: a badly scaled but identified carrier keeps its small-eigenvalue direction (no falsely tight interval)."""
    f, t = np.diag([1.0e8, 1.0e-6]), np.array([1.0e8 * 2.0e-4, 1.0e-6 * 5.0e2])
    lo, hi = fv.support_interval(f, t, np.array([0.0, 1.0]), 2.0, scale=np.array([1.0e-4, 1.0e3]))
    assert math.isclose(0.5 * (hi - lo), 2.0e3, rel_tol=1e-9) and math.isclose(0.5 * (hi + lo), 5.0e2, rel_tol=1e-9)


def test_eq20_singular_precision_and_hard_case():
    f = np.diag([4.0, 1.0, 0.0])
    t = np.array([4.0, 2.0, 0.0])
    body = fv.EllipsoidBody("unit ball", np.eye(3))
    r = fv.gauge_range(f, t, body, 1.0)
    assert r["Q_max"] == math.inf and r["unidentified_dimensions"] == 1 and r["Q_center"] is None
    assert 1.0 < r["Q_min"] < math.sqrt(5.0)
    assert fv.support_interval(f, t, np.array([0, 0, 1.0]), 2.0) == (-math.inf, math.inf)   # MG-04: no silent prior
    assert np.allclose(fv.support_interval(f, t, np.array([1.0, 0, 0]), 2.0), (0.0, 2.0))
    with pytest.raises(ValueError):
        fv.gauge_range(f, np.array([4.0, 2.0, 1.0]), body, 1.0)
    f2 = np.diag([1.0, 4.0])
    r2 = fv.gauge_range(f2, f2 @ np.array([0.0, 1.0]), fv.EllipsoidBody("unit ball", np.eye(2)), 1.0)
    u = np.linspace(0, 2 * np.pi, 2000001)
    assert abs(r2["Q_max"] - np.hypot(np.cos(u), 1 + np.sin(u) / 2).max()) < 1e-9


def test_identification_and_profiling():
    j = np.array([[1.0, 1.0, 0.0], [2.0, 2.0, 0.0], [0.0, 0.0, 3.0], [1.0, 1.0, 1.0]])
    f = j.T @ j
    ident = fv.identify(f)
    assert ident.rank == 2 and ident.null_basis.shape == (3, 1)
    assert np.allclose(np.abs(ident.null_basis[:, 0]), [math.sqrt(0.5), math.sqrt(0.5), 0.0], atol=1e-10)
    assert not fv.is_identified(f, np.array([1.0, 0, 0])) and fv.is_identified(f, np.array([1.0, 1.0, 0.3]))
    rng = np.random.default_rng(7)
    a = rng.normal(size=(5, 5))
    full = a @ a.T + np.eye(5)
    keep = [0, 3]
    assert np.allclose(fv.profiled_precision(full, keep), np.linalg.inv(np.linalg.inv(full)[np.ix_(keep, keep)]))
    with pytest.raises(ValueError):
        fv.carrier_mean(np.diag([1.0, 0.0]), np.array([1.0, 1.0]))


def test_eq22_named_laws_and_calibration():
    # MG-12: exact Wishart ratio n(n-1)/((n-p+k)(n-p+k-1)), n = N-1; equal to 1 when p = k
    assert abs(fv.finite_mc_sd_inflation(300, 45, 5) - math.sqrt(299.0 * 298.0 / (259.0 * 258.0))) < 1e-14
    assert fv.finite_mc_sd_inflation(300, 10, 10) == 1.0
    rng_i = np.random.default_rng(22)
    n_s, p_d, k_p = 40, 8, 2
    j_i = rng_i.standard_normal((p_d, k_p))
    est_i, var_i = [], []
    for _ in range(3000):                                           # Monte Carlo of the GLS-with-sample-covariance estimator
        s_i = np.cov(rng_i.standard_normal((n_s, p_d)), rowvar=False, ddof=1)
        f_i = j_i.T @ np.linalg.solve(s_i, j_i)
        est_i.append(np.linalg.solve(f_i, j_i.T @ np.linalg.solve(s_i, rng_i.standard_normal(p_d)))[0])
        var_i.append(np.linalg.inv(f_i)[0, 0])
    assert abs(np.std(est_i) / math.sqrt(np.mean(var_i)) / fv.finite_mc_sd_inflation(n_s, p_d, k_p) - 1.0) < 0.04
    with pytest.raises(ValueError):
        fv.finite_mc_sd_inflation(10, 12, 2)
    rng = np.random.default_rng(11)
    p, n_sims, stat = 5, 60, []
    for _ in range(1500):
        sims = rng.normal(size=(n_sims, p))
        s = np.cov(sims, rowvar=False)
        y = rng.normal(size=p)
        stat.append(float(y @ np.linalg.solve(s, y)))
    pv = np.array([fv.hotelling_null_tail(x, p, n_sims)["p_value"] for x in stat])
    assert stats.kstest(pv, "uniform").pvalue > 1e-3
    tail = fv.empirical_upper_tail(2.0, np.arange(10.0), "toy law")
    assert tail["n_exceed"] == 8 and abs(tail["p_value"] - 9 / 11) < 1e-15
    with pytest.raises(ValueError):                                   # MG-03: no tail without a law name
        fv.chi2_null_tail(1.0, 3, " ")
    body = fv.EllipsoidBody("unit ball", np.eye(3))
    ex = fv.gauge_exceedance_gaussian(np.zeros(3), np.eye(3), body, math.sqrt(stats.chi2.ppf(0.9, 3)), n_draw=200000)
    assert abs(ex["p_value"] - 0.1) < 5 * ex["mc_se"] + 1e-4


def test_eq23_transport_recovers_law():
    rng = np.random.default_rng(23)
    x = np.array([1.0, -2.0, 0.5])
    tau_true = np.array([1.0, 0.5, 0.25, 0.125])
    cov = 0.01 * np.eye(12)
    # MG-09: depth-major stacking, written out by hand so that the design cannot validate itself
    y_clean = np.concatenate([t * x for t in tau_true])
    assert np.allclose(fv.transport_design(tau_true, 3) @ x, y_clean, atol=1e-15)
    y = y_clean + rng.multivariate_normal(np.zeros(12), cov)
    fit = fv.gls_fit(y, cov, fv.transport_design(tau_true, 3))
    assert np.allclose(fit["theta"], x, atol=0.4) and fit["dof"] == 9 and fit["p_value"] > 1e-3
    table = fv.compare_transport_models(y, cov, {"true": fv.transport_design(tau_true, 3), "constant": fv.transport_design(np.ones(4), 3)})
    assert table["true"]["chi2"] < table["constant"]["chi2"] and table["null"]["dof"] == 12
    with pytest.raises(ValueError):
        fv.gls_fit(y, cov, np.zeros((12, 2)))


def test_five_view_record_fails_closed():
    ok = {"x": {"status": fv.AVAILABLE}, "Q": {"status": fv.AVAILABLE, "body": "declared"},
          "F": {"status": fv.UNAVAILABLE, "reason": "no body"}, "Pi": {"status": fv.AVAILABLE, "law": "named"},
          "G_F": {"status": fv.UNAVAILABLE, "reason": "single depth"}}
    assert set(fv.five_view_record(ok)) == set(fv.VIEW_NAMES)
    for view, key in (("Q", "body"), ("Pi", "law"), ("F", "reason")):
        bad = {k: dict(v) for k, v in ok.items()}
        bad[view].pop(key)
        with pytest.raises(ValueError):
            fv.five_view_record(bad)
    with pytest.raises(ValueError):
        fv.five_view_record({k: v for k, v in ok.items() if k != "G_F"})
    with pytest.raises(ValueError):
        fv.EllipsoidBody(" ", np.eye(2))


# ------------------------------------------------------------------ exact catalogue body and distance estimators
def _fine_pk(pk, n=20000):
    k, p = pk
    good = p > 0
    lk = np.linspace(np.log(k[good][0]), np.log(k[good][-1]), n)
    return np.exp(lk), np.exp(np.interp(lk, np.log(k[good]), np.log(p[good])))


def test_eq30_velocity_correlation_limits_and_identity(pk):
    k, p = pk
    f = lb.growth_rate(0.3153)
    r = np.linspace(0.0, 400.0, 801)
    perp, par = lb.velocity_correlation(k, p, f, 67.36, r, n_k=60000)
    sig2 = lb.point_velocity_dispersion_1d(k, p, f, 67.36)
    assert abs(perp[0] / sig2 - 1.0) < 1e-3 and abs(par[0] / perp[0] - 1.0) < 1e-12        # Psi(0) = sigma_v,1D^2
    ident = np.gradient(r * perp, r)                                                          # MG-15: Psi_par = d(r Psi_perp)/dr
    assert np.abs(ident[3:-3] - par[3:-3]).max() < 2e-4 * perp[0]
    assert (np.diff(perp) < 0).all() and par[-1] < 0.0 < perp[-1]
    damped = lb.velocity_correlation(k, p, f, 67.36, np.array([0.0]), n_k=60000, damping_mpc=19.3)[0][0]
    assert 0.5 * perp[0] < damped < 0.8 * perp[0]
    with pytest.raises(ValueError):                                                           # under-resolved k grid fails closed
        lb.velocity_correlation(k, p, f, 67.36, np.array([5000.0]), n_k=2000)


def test_eq31_pair_sum_equals_dense_and_harmonic_forms(pk):
    k, p = pk
    f = lb.growth_rate(0.3153)
    n = fv.fibonacci_sphere(700)
    r0 = 150.0
    grid = np.linspace(0.0, 2.0 * r0 * 1.01, 1213)
    tab = lb.velocity_correlation(k, p, f, 67.36, grid, n_k=60000)
    basis = de.multipole_basis(n)
    op = np.linalg.solve(basis.T @ basis, basis.T)                      # least-squares projector on [1, n, STF5]
    got = lb.radial_velocity_covariance_product(op, n, np.full(700, r0), grid, [tab], chunk=128)[0]
    # dense form written from 3-vectors (MG-14 protects the (n_i.rhat)(n_j.rhat) term)
    x = r0 * n
    dx = x[:, None, :] - x[None, :, :]
    rij = np.linalg.norm(dx, axis=2)
    rhat = dx / np.where(rij > 0, rij, 1.0)[:, :, None]
    perp, par = np.interp(rij, grid, tab[0]), np.interp(rij, grid, tab[1])
    cuu = perp * (n @ n.T) + (par - perp) * np.einsum("ia,ija->ij", n, rhat) * np.einsum("ja,ija->ij", n, rhat)
    assert np.allclose(got, op @ cuu @ op.T, rtol=1e-9, atol=1e-10 * np.abs(got).max())
    # ideal-sky harmonic form (R54-EQ-11/12) on a thin shell: Var(D_i) = 3/(4 pi) C_1, Var(q_a) = 15/(8 pi) C_2
    kf, pf = _fine_pk(pk)
    shell = [lb.gaussian_window(r0, 0.5, 1.0)]
    for ell, rows in ((1, slice(1, 4)), (2, slice(4, 9))):
        want = lb.CARTESIAN_FACTOR[ell] * lb.harmonic_cosmic_cov(ell, kf, pf, shell, f, 67.36)[0, 0]
        assert np.abs(np.diag(got)[rows] / want - 1.0).max() < 0.02
    with pytest.raises(ValueError):                                     # grid must cover twice the largest distance
        lb.radial_velocity_covariance_product(op, n, np.full(700, 400.0), grid, [tab])


def test_eq33_distance_factors_low_redshift_limits():
    z = np.array([1.0e-3, 0.01, 0.03])
    fac = lb.flat_lcdm_distance_factors(z, 0.3153)
    q0, c = 1.5 * 0.3153 - 1.0, 299792.458
    assert np.allclose(fac["y_km_s"] / (c * z), 1.0 + 0.5 * (1.0 - q0) * z, atol=1e-3)      # d_L = (c z/H0)[1 + (1 - q0) z/2 + ...]
    assert np.allclose(fac["g_per_km_s"] * c * z, 1.0 - 0.5 * (1.0 + q0) * z, atol=1e-3)    # MG-16: g = [1/z - (1 + q0)/2 + ...]/c
    with pytest.raises(ValueError):
        lb.flat_lcdm_distance_factors(np.array([0.0, 0.1]), 0.3)


def test_wls_operator_identity_and_fail_closed():
    rng = np.random.default_rng(5)
    x, w = rng.standard_normal((50, 3)), rng.uniform(0.5, 2.0, 50)
    assert np.allclose(de.wls_operator(x, w) @ x, np.eye(3), atol=1e-12)
    w0 = w.copy()
    w0[:10] = 0.0
    assert np.all(de.wls_operator(x, w0)[:, :10] == 0.0)
    with pytest.raises(ValueError):                                     # MG-19: collinear column is not identified
        de.wls_operator(np.column_stack((x, x[:, 0])), w)
    with pytest.raises(ValueError):
        de.multipole_basis(np.ones((4, 3)))


def test_eq34_log_estimator_is_unbiased_and_eq35_linear_estimator_is_not():
    rng = np.random.default_rng(34)
    n_obj, h_true, e_big = 6000, 70.0, 0.5
    n = fv.fibonacci_sphere(n_obj)
    z = rng.uniform(0.02, 0.06, n_obj)
    fac = lb.flat_lcdm_distance_factors(z, 0.3153)
    mu_true = 5.0 * np.log10(fac["y_km_s"] / h_true) + 25.0
    y_lin = h_true * de.distance_mpc(mu_true)                           # exact linear Hubble law in the true distances
    e_mu = np.where(n[:, 2] >= 0.0, e_big, 0.2)                         # noisier distance moduli in the north
    a_log = de.log_window_operator(de.log_noise_variance(e_mu, fac["g_per_km_s"], 1e-9), z, n, (0.04,), width=0.05)
    h, dz, hl, dzl, hh = [], [], [], [], []
    e_hom = np.full(n_obj, e_big)
    for _ in range(120):
        mu = mu_true + e_mu * rng.standard_normal(n_obj)
        th = a_log @ de.log_distance_ratio(mu, z, 0.3153)["eta"]
        tl = de.r36_linear_window_operator(mu, e_mu, z, n, (0.04,), width=0.05, sigma_star=1e-9) @ y_lin
        mu_h = mu_true + e_hom * rng.standard_normal(n_obj)
        hh.append((de.r36_linear_window_operator(mu_h, e_hom, z, n, (0.04,), width=0.05, sigma_star=1e-9) @ y_lin)[0])
        h.append(th[0]), dz.append(th[3]), hl.append(tl[0]), dzl.append(tl[3])

    def se(v):
        return float(np.std(v, ddof=1) / np.sqrt(len(v)))

    assert abs(np.mean(h) - np.log(h_true)) < 4 * se(h) and abs(np.mean(dz)) < 4 * se(dz)           # MG-17: unbiased
    assert np.mean(hl) - h_true > 8 * se(hl) and abs(np.mean(dzl)) > 8 * se(dzl)                     # errors in variables
    s = de.LN10_OVER_5 * e_big                                          # homogeneous errors, weights ~ 1/d^2: bias exp(+s^2/2)
    assert abs(np.mean(hh) / h_true - np.exp(0.5 * s * s)) < 4 * se(hh) / h_true + 1e-4
    assert abs(de.magnitude_equivalent(-0.03) - 0.03 * 5.0 / np.log(10.0)) < 1e-15


def test_eq35_r36_operator_is_reproduced_from_the_committed_source():
    pub = ROOT / "docs/research_program"
    src = pub / "cf4_schur_loop8_20261015/inputs/selected_source_observables.npz"
    opf = pub / ("observational_publication_20261015/OBSERVABLE_BRIDGE_RECONCILIATION_20261027/products/"
                 "R36-01-CF4-OPERATOR/audit_backup/derived/A_RAW_36x35970.npz")
    with np.load(src, allow_pickle=False) as z, np.load(opf, allow_pickle=False) as o:
        a = de.r36_linear_window_operator(z["dmzp"], z["e_dmzp"], z["z_CMB"], z["n_J2000"], (0.025, 0.04, 0.06, 0.08))
        assert np.abs(a - o["A_raw"]).max() < 1e-12 * np.abs(o["A_raw"]).max()                      # MG-18
        assert np.abs(a @ (de.C_KM_S * z["z_CMB"]) - o["theta36"]).max() < 1e-8
        design = de.distance_mpc(z["dmzp"])[:, None] * de.multipole_basis(z["n_J2000"])
        assert np.abs(a[:9] @ design - np.eye(9)).max() < 1e-9
