"""CORE-03 follow-up repairs (failing-test-first). Synthetic stubs only.

R1  certificate input hashes must be real or explicitly UNVERIFIED (no fabricated '..._sha256_verified' strings)
R2  no invented 0.53 occupancy fallback: omit the departure variable and say so in the caveats
R3  scalar-ablation shear direction must be unit in the STF5 Gram metric (GRAM-2)
R4  KinematicResponseModel.from_parameters defaults to the exact Lorentz closure (FO-1)
R5  x-bundle CMB carrier always uses exact beta_RM (+) beta_MO composition, never a stale state.beta_RO (FO-6)
R6  deceleration parameter q0 = Omega_m/2 - Omega_Lambda with Omega_Lambda = 1 - Omega_m - Omega_k
"""
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pytest

ROOT = Path(__file__).resolve().parents[2]
for p in (ROOT / "htt" / "src", ROOT / "htt", ROOT):
    sys.path.insert(0, str(p))

from htt.htt.infer import tensor_five_variable_inference as tfi  # noqa: E402
from htt.htt.infer.tensor_five_variable_inference import TensorFiveVariableEngine  # noqa: E402
from common.kinematic_response import KinematicFrameState, KinematicResponseModel  # noqa: E402
from common.relativistic_velocity_closure import compose_velocities_sr  # noqa: E402
from common.full_observable_x_bundle import build_full_observable_x_bundle  # noqa: E402

G = np.array([[2, 1, 0, 0, 0], [1, 2, 0, 0, 0], [0, 0, 2, 0, 0], [0, 0, 0, 2, 0], [0, 0, 0, 0, 2]], float)


def _find(d, key):
    if isinstance(d, dict):
        if key in d:
            return d[key]
        for v in d.values():
            r = _find(v, key)
            if r is not None:
                return r
    return None


def _cert(occupancy=np.array([0.1]), **kw):
    engine = TensorFiveVariableEngine.__new__(TensorFiveVariableEngine)
    engine.n_data = 100
    state = SimpleNamespace(
        support_profiles_F={"BETA_MO": SimpleNamespace(occupancy_ratios=occupancy)},
        exceedance_surfaces_Pi={"BETA_MO_MIO_NULL": SimpleNamespace(observed_exceedance=0.5, undefined_mass=0.0)},
        depth_path_GF=SimpleNamespace(cross_shell_covariance=np.eye(2)),
    )
    mcmc = SimpleNamespace(mean=np.zeros(17), r_hat=np.ones(17))
    loocv = {"summary_status": "LOOCV_ADEQUACY_VERIFIED", "folds": {"a": {"out_of_sample_chi2_per_dof": 1.0}}}
    comp = {"hypotheses": [{"hypothesis_id": "H_loc", "chi2": 10.0, "Delta_BIC": -1.0},
                           {"hypothesis_id": "H_0", "chi2": 12.0, "Delta_BIC": 0.0}]}
    return engine.generate_mio_certificate(state, mcmc, loocv, comp, **kw)


# ---- R1
def test_default_certificate_has_no_fabricated_verified_hashes():
    hashes = _find(_cert(), "input_data_hashes")
    assert hashes, "input_data_hashes missing"
    assert not any("sha256_verified" in h or h.endswith("_verified") for h in hashes), hashes
    assert all("UNVERIFIED" in h for h in hashes), hashes


def test_supplied_hashes_are_used_and_validated():
    good = {"planck": "a" * 64, "quaia": "b" * 64}
    hashes = _find(_cert(input_hashes=good), "input_data_hashes")
    assert f"planck:sha256:{'a' * 64}" in hashes and f"quaia:sha256:{'b' * 64}" in hashes
    with pytest.raises(ValueError):
        _cert(input_hashes={"planck": "not-a-hash"})


# ---- R2
def test_missing_occupancy_is_omitted_not_invented():
    cert = _cert(occupancy=None)
    dep = _find(cert, "departure_variables")
    assert "directional_occupancy_ratio_max" not in dep, dep
    assert "directional_occupancy_unavailable" in _find(cert, "domain_caveats")


# ---- R3
def test_scalar_ablation_direction_is_gram_unit():
    v = np.array([3.0e-5, -1.0e-5, 2.0e-5, 0.5e-5, -4.0e-5])
    d = tfi.stf5_gram_unit_direction(v)
    assert abs(d @ G @ d - 1.0) < 1e-12
    assert np.allclose(d / np.linalg.norm(d), v / np.linalg.norm(v), rtol=1e-12)
    with pytest.raises(ValueError):
        tfi.stf5_gram_unit_direction(np.zeros(5))


# ---- R4
def test_from_parameters_defaults_to_exact_closure():
    bro, brm = [1.2e-3, 0.0, 0.0], [0.0, 1.0e-3, 0.0]
    model = KinematicResponseModel.from_parameters(beta_RO=bro, beta_RM=brm)
    assert model.state.closure_type == "EXACT_LORENTZ_BOOST"
    assert np.allclose(compose_velocities_sr(model.state.beta_RM, model.state.beta_MO), bro, rtol=0, atol=1e-15)


# ---- R5
def _joint():
    path = ROOT / "tests" / "r39" / "test_full_observable_x_bundle.py"
    spec = importlib.util.spec_from_file_location("r39_fixture", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod.make_test_joint_state()


def _model(beta_ro):
    st = KinematicFrameState(
        beta_RO=np.array(beta_ro, float), beta_RM=np.array([2.0e-4, -1.0e-4, 1.0e-4]), beta_MO=np.zeros(3),
        d_int=np.zeros(3), stf_shear_amplitudes=np.zeros(5), e1_polar_vector=np.zeros(3), b1_axial_vector=np.zeros(3))
    return KinematicResponseModel(st)


def _cmb(bundle):
    return next(c for c in bundle.predicted_carriers if c.functional_id == "PREDICTED_CMB_LOWELL_CARRIERS")


def test_cmb_carrier_ignores_stale_state_beta_ro_when_one_boost_is_zero():
    joint = _joint()
    exact = np.array([2.0e-4, -1.0e-4, 1.0e-4])                  # beta_RM (+) 0 = beta_RM exactly
    ok = _cmb(build_full_observable_x_bundle(joint, _model(exact), expansion_scalar=0.21))
    stale = _cmb(build_full_observable_x_bundle(joint, _model([5.0e-3, 0.0, 0.0]), expansion_scalar=0.21))
    assert np.allclose(np.asarray(stale.components), np.asarray(ok.components), rtol=0, atol=1e-18)


# ---- R7 (R48-T23 defect T23-D1)
def test_mock_verification_block_asserts_nothing_it_did_not_check():
    import json as _json
    import platform
    spec = importlib.util.spec_from_file_location("mock48_t23", ROOT / "scripts" / "r48" / "bianchi_fivevar_identifiability_mock.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    ver = mod.run_experiment(seed=1, n_rep=200, n_post=50, n_null=4)["verification"]
    assert ver["python"] == platform.python_version()
    assert "PASS" not in _json.dumps(ver), ver
    assert ver["local_pytest"] == "NOT_RUN_BY_SCRIPT"


# ---- R6
def test_deceleration_parameter_matches_friedmann_derivative():
    from htt.htt.infer.tensor_joint_multiprobe_likelihood import deceleration_parameter
    for om, ok_ in ((0.3, 0.0), (0.315, 0.0), (0.3, 0.05), (0.25, -0.03)):
        ol = 1.0 - om - ok_
        E = lambda z: np.sqrt(om * (1 + z) ** 3 + ok_ * (1 + z) ** 2 + ol)
        h = 1e-6
        dE = (E(h) - E(-h)) / (2 * h)
        q0_num = dE / E(0.0) - 1.0                                # q0 = (1+z) E'/E - 1 at z=0
        assert abs(deceleration_parameter(om, ok_) - q0_num) < 1e-8


# ---- review follow-up (independent review of PR #574)
def test_r39_scalar_xc_direction_is_gram_unit_and_euclid_norm_is_gone():
    path = ROOT / "scripts" / "r39" / "run_r39_identifiability_analysis.py"
    src = path.read_text()
    assert "np.linalg.norm(theta_0[:5])" not in src
    spec = importlib.util.spec_from_file_location("r39_script", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    v = np.array([3.0e-5, -1.0e-5, 2.0e-5, 0.5e-5, -4.0e-5])
    d = mod.scalar_xc_shear_direction(v)
    assert abs(d @ G @ d - 1.0) < 1e-12
    with pytest.raises(ValueError):
        mod.scalar_xc_shear_direction(np.zeros(5))


def test_fisher_gain_ablation_calls_gram_direction_helper(monkeypatch):
    calls = []
    orig = tfi.stf5_gram_unit_direction

    def spy(v):
        calls.append(np.array(v, float))
        return orig(v)

    monkeypatch.setattr(tfi, "stf5_gram_unit_direction", spy)
    rng = np.random.default_rng(0)
    A = rng.normal(size=(25, 17))
    engine = TensorFiveVariableEngine.__new__(TensorFiveVariableEngine)
    engine.n_data = 25
    engine.lik = SimpleNamespace(predict_total=lambda th: A @ th, cov_matrix=np.eye(25))
    engine.compute_fisher_information_gain()
    assert len(calls) == 1 and calls[0].shape == (5,)


# ---- CORE-05 follow-up: five-variable state must use exact ordered composition for beta_RO
class _Stop(Exception):
    pass


def test_five_variable_state_beta_ro_uses_exact_ordered_composition(monkeypatch):
    seen = {}

    def spy(**kw):
        seen.update(kw)
        raise _Stop

    monkeypatch.setattr(tfi, "build_velocity_frame_bundle", spy)
    post = np.zeros(17)
    post[11:14] = [2.0e-3, 0.0, 0.0]      # beta_RM
    post[14:17] = [0.0, 3.0e-3, 0.0]      # beta_MO
    engine = TensorFiveVariableEngine.__new__(TensorFiveVariableEngine)
    with pytest.raises(_Stop):
        engine.compute_five_variable_state(np.zeros((4, 17)), post)
    want = compose_velocities_sr(post[11:14], post[14:17])
    got = np.array(seen["beta_RO"], float)
    assert np.allclose(got, want, rtol=0, atol=1e-18)
    assert not np.allclose(got, post[11:14] + post[14:17], rtol=0, atol=1e-18)


# ---- hypothesis competition: text and best model are computed from the table, not fixed strings
def _engine_with_chi2(chi2_by_k):
    engine = TensorFiveVariableEngine.__new__(TensorFiveVariableEngine)
    engine.n_data = 100

    def chi2_breakdown(th):
        nz = int(np.count_nonzero(th))
        key = nz if nz in chi2_by_k else max(chi2_by_k)
        return -0.5 * chi2_by_k[key], {"Total": chi2_by_k[key]}, None

    engine.lik = SimpleNamespace(compute_chi2_breakdown=chi2_breakdown)
    return engine


def test_hypothesis_competition_text_and_best_model_are_computed():
    # make H_0 (zero vector -> nz=0) the best: lowest chi2 and fewest parameters
    eng = _engine_with_chi2({0: 100.0, 3: 120.0, 8: 125.0, 11: 130.0})
    out = eng.run_hypothesis_competition()
    assert out["best_model_by_bic"] == "H_0"
    txt = out["interpretation"]
    for banned in ("100%", "decisively", "detection", "-602.8"):
        assert banned not in txt
    dbic = {h["hypothesis_id"]: h["Delta_BIC"] for h in out["hypotheses"]}
    assert f"{dbic['H_loc']:.1f}" in txt
    assert out["fixed_hypothesis_points"]["status"] == "FIXED_POINTS_NOT_REFIT"
