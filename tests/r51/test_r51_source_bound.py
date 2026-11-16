"""R51 regressions: source-bound response, laws, quarantine. No external data paths."""
import dataclasses
import importlib.util
import math
from pathlib import Path

import numpy as np
import pytest
from scipy import integrate, stats

from bass.transport.general_bianchi_transfer import (
    TiltedTransferParameters, compute_general_bianchi_transfer, gl_sphere_grid,
)
from htt.htt.infer.r49_general_bianchi_likelihood import (
    R49GeneralBianchiLikelihood, R49JointState,
)
from htt.htt.infer.r51_source_bound_response import (
    RESPONSE_TERM_REGISTRY, SOURCE_BOUND, WORKING_MODEL, DataBlockRegistry, DuplicateDataBlockError,
    WorkingModelResponseError, bianchi_i_exact_temperature_contrast, bianchi_i_shear_history_integral,
    carrier_quadratic, finite_mc_t_loglike, gaussian_loglike, heldout_pit,
    integrated_shear_isw_temperature, registry_status, signed_linear_carrier,
)

SIG = np.array([[1.0, 0.3, -0.2], [0.3, -0.4, 0.5], [-0.2, 0.5, -0.6]])


def _gbi05():
    path = Path(__file__).resolve().parents[1] / "r49/test_gbi05_source_bound_likelihood_and_five_view.py"
    spec = importlib.util.spec_from_file_location("gbi05_fixture", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_linear_isw_is_first_order_of_exact_bianchi_i_redshift():
    _, _, n, _ = gl_sphere_grid(12)
    res = []
    for eps in (1e-4, 2e-4):
        s = eps * SIG
        exact = bianchi_i_exact_temperature_contrast(n, s)
        lin = integrated_shear_isw_temperature(n, s)
        assert np.max(np.abs(exact - lin)) < 10 * eps * np.max(np.abs(lin))
        res.append(np.max(np.abs(exact - lin)))
    assert res[1] / res[0] == pytest.approx(4.0, rel=2e-3)  # remainder is O(Sigma^2)


def test_transfer_type_i_boundary_equals_source_equation_and_is_tagged():
    s = 3e-6 * SIG
    out = compute_general_bianchi_transfer(TiltedTransferParameters(family="I", sigma_N=s, ell_max=4, n_gl_theta=12))
    np.testing.assert_allclose(out.cosmo_T_map, integrated_shear_isw_temperature(out.n_hat_grid, s), rtol=1e-12, atol=1e-20)
    prov = out.channel_breakdown["response_provenance"]
    assert prov["temperature"] == "SOURCE_BOUND_TYPE_I_INTEGRATED_SHEAR"
    assert prov["polarization"] == "WORKING_MODEL_POLARIZATION_GAIN"


def test_finite_curvature_and_rescaled_gain_are_working_models():
    p = TiltedTransferParameters(family="VII_h", sigma_N=1e-6 * SIG, omega_k=0.01, ell_max=4, n_gl_theta=12)
    assert compute_general_bianchi_transfer(p).channel_breakdown["response_provenance"]["temperature"].startswith("WORKING_MODEL")
    q = TiltedTransferParameters(family="I", sigma_N=1e-6 * SIG, x_curvature=2.0, ell_max=4, n_gl_theta=12)
    assert compute_general_bianchi_transfer(q).channel_breakdown["response_provenance"]["temperature"] == "WORKING_MODEL_RESCALED_TYPE_I"


def test_registry_quarantines_every_named_unsourced_coefficient():
    for tid in ("CMB_TYPE_I_POLARIZATION_GAIN_0p18", "CMB_FINITE_CURVATURE_FOCUS_TWIST", "COUNT_DIPOLE_0p1_A",
                "CF4_0p1_Z_A", "DESI_DIRECTIONAL_QUAD_AS_SHEAR", "GAIA_E2_DIRECT_SHEAR_PLUS_0p25_Q",
                "CMB_SIGMA_AS_TODAY_SHEAR", "CMB_COVARIANCE_EXCESS_1e-8"):
        assert registry_status(tid) == WORKING_MODEL
    for row in RESPONSE_TERM_REGISTRY:
        if row["status"] == SOURCE_BOUND:
            assert row["source"] and row["equation"]


def test_history_operator_matter_only_closed_form_and_lcdm_range():
    zs = 1089.94
    a = 1.0 / (1.0 + zs)
    closed = (2.0 / 3.0) * (a**-1.5 - 1.0)
    assert bianchi_i_shear_history_integral(1.0, 0.0, 0.0, zs) == pytest.approx(closed, rel=1e-9)
    lcdm = bianchi_i_shear_history_integral(0.3153, 9.2e-5, 1 - 0.3153 - 9.2e-5, zs)
    upper = (2.0 / 3.0) * a**-1.5 / math.sqrt(0.3153)  # radiation and Lambda only reduce I
    assert 0.8 * upper < lcdm < upper


def test_finite_mc_law_normalized_and_gaussian_limit():
    S = np.array([[2.3]])
    v, _ = integrate.quad(lambda x: math.exp(finite_mc_t_loglike(np.array([x]), S, 7)), -np.inf, np.inf)
    assert v == pytest.approx(1.0, abs=1e-10)
    S2 = np.array([[1.5, 0.4], [0.4, 0.8]])
    r = np.array([0.3, -0.2])
    assert finite_mc_t_loglike(r, S2, 10**9) == pytest.approx(gaussian_loglike(r, S2), abs=1e-6)
    with pytest.raises(ValueError):
        finite_mc_t_loglike(r, S2, 2)


@pytest.mark.parametrize("bad", [np.diag([1.0, 0.0]), np.array([[1.0, 2.0], [2.0, 1.0]]), np.array([[1.0, 0.1], [0.0, 1.0]])])
def test_laws_refuse_singular_indefinite_or_asymmetric(bad):
    with pytest.raises(ValueError):
        gaussian_loglike(np.zeros(2), bad)


def test_heldout_pit_calibrated_for_finite_mc_and_overdispersed_plugin():
    rng = np.random.default_rng(5101)
    p, n = 6, 20
    A = rng.normal(size=(p, p))
    C = A @ A.T + p * np.eye(p)
    L = np.linalg.cholesky(C)
    fm, pg = [], []
    for _ in range(3000):
        draws = (L @ rng.normal(size=(p, n + 1))).T
        out = heldout_pit(draws[-1], draws[:-1])
        fm.append(out["pit_finite_mc"]); pg.append(out["pit_plugin_gaussian"])
    assert stats.kstest(fm, "uniform").pvalue > 1e-3
    assert np.mean(np.asarray(pg) > 0.95) > 0.15  # plug-in law under-covers


def test_signed_carrier_exact_for_gaussian_and_needs_q0_for_finite_mc():
    rng = np.random.default_rng(5102)
    J = rng.normal(size=(12, 3)); d = rng.normal(size=12)
    Z = rng.normal(size=(12, 12)); C = Z @ Z.T + np.eye(12)
    car = signed_linear_carrier(J, d, C)
    for th in rng.normal(size=(6, 3)):
        r = d - J @ th
        direct = gaussian_loglike(r, C) - gaussian_loglike(d, C)
        assert th @ car["t"] - 0.5 * th @ car["F"] @ th == pytest.approx(direct, abs=1e-8)
        assert carrier_quadratic(car, th) == pytest.approx(r @ np.linalg.solve(C, r), rel=1e-10)
        tl = finite_mc_t_loglike(r, C, 40) - finite_mc_t_loglike(d, C, 40)
        q = carrier_quadratic(car, th)
        assert -20.0 * (math.log1p(q / 39) - math.log1p(car["Q0"] / 39)) == pytest.approx(tl, abs=1e-8)


def test_data_block_registry_blocks_duplicate_independent_factors():
    reg = DataBlockRegistry()
    reg.register("sha:abc", "CMB")
    reg.register("sha:abc", "CMB")
    with pytest.raises(DuplicateDataBlockError):
        reg.register("sha:abc", "Gaia")


def test_source_bound_policy_quarantines_deferred_probes_and_finite_curvature():
    mod = _gbi05()
    truth = R49JointState(family="I", sigma_AB_stf5=np.zeros(5), omega_A=np.zeros(3), A_A=np.array([0.01, 0.0, 0.0]),
                          v_matter=np.zeros(3), v_rad=np.zeros(3), beta_MO=np.array([1e-3, -5e-4, 2e-4]))
    ds0, budget = mod._make_synthetic_dataset(truth)
    with pytest.raises(WorkingModelResponseError):
        R49GeneralBianchiLikelihood(ds0, mode_budget=budget, response_policy="source_bound")
    probes = ("CMB", "Quaia", "NVSS", "RACS", "DESI")
    with pytest.raises(ValueError, match="data-block identity"):
        R49GeneralBianchiLikelihood(ds0, mode_budget=budget, active_probes=probes, response_policy="source_bound")
    ds = dataclasses.replace(ds0, **{k: dataclasses.replace(getattr(ds0, k), provenance_sha256=f"sha:{k}")
                                     for k in ("cmb", "quaia", "nvss", "racs", "desi")})
    dup = dataclasses.replace(ds, nvss=dataclasses.replace(ds.nvss, provenance_sha256="sha:quaia"))
    with pytest.raises(DuplicateDataBlockError):
        R49GeneralBianchiLikelihood(dup, mode_budget=budget, active_probes=probes, response_policy="source_bound")
    like = R49GeneralBianchiLikelihood(ds, mode_budget=budget, active_probes=probes, response_policy="source_bound")
    assert like.physical_inference_admissible
    scores = like.logp_by_probe(truth)
    assert set(scores) == {"CMB", "Quaia", "NVSS", "RACS", "DESI_BAO"}
    # A_A has no source-bound count-dipole response: changing it leaves dipole scores unchanged.
    moved = R49JointState(**{**truth.__dict__, "A_A": np.array([0.5, 0.2, -0.1])})
    for k in ("Quaia", "NVSS", "RACS"):
        assert like.logp_by_probe(moved)[k] == pytest.approx(scores[k], abs=1e-12)
    curved = R49JointState(**{**truth.__dict__, "family": "VII_h"})
    with pytest.raises(WorkingModelResponseError):
        like.logp_by_probe(curved)
    # 0 < n_mc <= p has no admissible law: no silent Gaussian fallback.
    small = dataclasses.replace(ds, cmb=dataclasses.replace(ds.cmb, n_mc=10))
    with pytest.raises(ValueError, match="n_mc"):
        R49GeneralBianchiLikelihood(small, mode_budget=budget, active_probes=probes,
                                    response_policy="source_bound").logp_by_probe(truth)
    hist = like.shear_history_operator(truth)
    assert 2.0e4 < hist < 5.0e4
    assert not R49GeneralBianchiLikelihood(ds, mode_budget=budget).physical_inference_admissible
