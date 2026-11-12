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


# ---- probe construction is lazy: a disabled probe's data files are never loaded (NPIPE/PR4 exclusion)
def test_disabled_probe_is_never_constructed(monkeypatch):
    from htt.htt.infer import tensor_joint_multiprobe_likelihood as tm

    class Boom:
        def __init__(self, *a, **k):
            raise AssertionError("disabled probe was constructed")

    class Stub:
        def __init__(self, *a, **k):
            self.n_data = 2
            self.data_vector = np.zeros(2)
            self.cov_matrix = np.eye(2)

        def assert_zero_stub(self):
            pass

    monkeypatch.setattr(tm, "PlanckLowEllCarrierLikelihood", Boom)
    for name in ("QuaiaCountsDipoleLikelihood", "RadioCountDipoleLikelihood", "GaiaProperMotionVSHLikelihood",
                 "SupernovaIaJointLikelihood", "PeculiarVelocityLikelihood", "DESIDR2BAOLikelihood"):
        monkeypatch.setattr(tm, name, Stub)
    lik = tm.TensorJointMultiprobeLikelihood(enabled_probes=["Quasars", "Radio"])
    assert lik.enabled_probes == ["Quasars", "Radio"] and lik.n_data == 4 and "CMB" not in lik.probe_slices


# ---- SNe predict must match the data convention: the Pantheon+ 490 cache holds residuals d = m_b - mu_fid - M0 (H0=70, q0=-0.55)
def test_sne_prediction_is_residual_against_cache_fiducial():
    from htt.htt.infer import tensor_joint_multiprobe_likelihood as tm

    sn = tm.SupernovaIaJointLikelihood.__new__(tm.SupernovaIaJointLikelihood)
    z = np.linspace(0.03, 0.15, 7)
    sn.redshifts = z
    n = np.random.default_rng(1).normal(size=(7, 3)); sn.directions = n / np.linalg.norm(n, axis=1)[:, None]
    theta = tm.ThetaKinematic.from_vector(np.zeros(17))
    psi_cache = tm.PsiCosmology(H_0=70.0, Omega_m=0.3, DeltaOmega_k=0.0)   # q0 = 0.5*0.3 - 0.7 = -0.55
    assert np.allclose(sn.predict(theta, psi_cache), 0.0, atol=1e-9)
    # shifting H0 only changes a z-independent constant (absorbed by the analytic M0 marginalisation)
    shifted = sn.predict(theta, tm.PsiCosmology(H_0=67.4, Omega_m=0.3))
    assert np.allclose(shifted, shifted[0], atol=1e-9) and abs(shifted[0] - 5 * np.log10(70 / 67.4)) < 1e-9


# ---- PV data (CF4 dmzp) is a distance modulus mu(z), not a residual: the prediction must carry mu_model(z)
def test_pv_prediction_carries_distance_modulus_trend():
    from htt.htt.infer import tensor_joint_multiprobe_likelihood as tm

    pv = tm.PeculiarVelocityLikelihood.__new__(tm.PeculiarVelocityLikelihood)
    z = np.geomspace(0.01, 0.1, 40)
    pv.redshifts = z
    pv.directions = np.tile([0.0, 0.0, 1.0], (40, 1))
    theta = tm.ThetaKinematic.from_vector(np.zeros(17))
    psi = tm.PsiCosmology(H_0=70.0, Omega_m=0.3)
    pred = pv.predict(theta, psi)
    q0 = -0.55
    want = 5 * np.log10(299792.458 * z / 70.0 * (1 + 0.5 * (1 - q0) * z) * 1e5)
    assert np.allclose(pred, want, atol=1e-9)
    assert abs(np.polyfit(np.log10(z), pred, 1)[0] - 5.0) < 0.3


# ---- VSH shear coefficient amplitude: the E2 basis is not orthonormal, so the Euclidean coefficient norm is chart dependent;
#      the invariant amplitude is the sphere-averaged L2 norm sqrt(c^T G c) with G_ij = <E_i . E_j>
def test_vsh_shear_l2_amplitude_uses_basis_gram():
    from common import source_bound_gaia_vsh_operator as op

    G = op.vsh_shear_gram()
    assert G.shape == (5, 5) and np.allclose(G, G.T) and np.all(np.linalg.eigvalsh(G) > 0)
    assert np.max(np.abs(np.diag(G) - 1.0)) > 0.5          # basis is far from unit-normalised: Euclidean norm is not invariant
    for k in range(5):
        c = np.zeros(5); c[k] = 1.0
        assert abs(op.vsh_shear_l2_amplitude(c) - np.sqrt(G[k, k])) < 1e-12
    c = np.array([1.0, -0.5, 0.2, 0.3, -0.7])
    assert abs(op.vsh_shear_l2_amplitude(c) - np.sqrt(c @ G @ c)) < 1e-12


def test_gaia_script_shear_l2_helper_matches_operator():
    from common import source_bound_gaia_vsh_operator as op
    spec = importlib.util.spec_from_file_location("gaia_vsh_script", ROOT / "scripts" / "r38" / "run_gaia_vsh.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    assert np.allclose(mod.shear_e2_gram(), op.vsh_shear_gram(), rtol=1e-9, atol=1e-9)


# ---- count-dipole responses are derived: R = 2 + x(1+alpha) with measured count slopes x (no untraced 3.5/3.3 constants)
def test_count_dipole_responses_are_derived_from_slope_and_alpha():
    from htt.htt.infer import tensor_joint_multiprobe_likelihood as tm

    assert abs(tm.count_dipole_response(1.043, 0.75) - (2 + 1.043 * 1.75)) < 1e-12
    th = tm.ThetaKinematic.from_vector(np.r_[np.zeros(14), 1.0, 0.0, 0.0])
    psi = tm.PsiCosmology()
    for alpha in (0.5, 1.0):
        q = tm.QuaiaCountsDipoleLikelihood.__new__(tm.QuaiaCountsDipoleLikelihood); q.alpha = alpha
        r = tm.RadioCountDipoleLikelihood.__new__(tm.RadioCountDipoleLikelihood); r.alpha = alpha
        pq, pr = q.predict(th, psi), r.predict(th, psi)
        assert abs(pq[0] - (2 + tm.COUNT_SLOPE_DECLARED["Quaia_G20"] * (1 + alpha))) < 1e-12
        assert abs(pq[3] - (2 + tm.COUNT_SLOPE_DECLARED["Quaia_G20p5"] * (1 + alpha))) < 1e-12
        assert abs(pr[0] - (2 + tm.COUNT_SLOPE_DECLARED["NVSS"] * (1 + alpha))) < 1e-12
        assert abs(pr[3] - (2 + tm.COUNT_SLOPE_DECLARED["RACS"] * (1 + alpha))) < 1e-12


# ---- count-dipole data: frame fix (galactic -> ICRS) and sourced-data path with per-block use flags
def test_galactic_direction_is_converted_to_icrs_cartesian():
    from htt.htt.infer import tensor_joint_multiprobe_likelihood as tm

    v = tm.galactic_direction_to_icrs_unit(0.0, 0.0)           # Galactic centre: RA 266.405, Dec -28.936
    ra, dec = np.deg2rad(266.405), np.deg2rad(-28.936)
    want = np.array([np.cos(dec) * np.cos(ra), np.cos(dec) * np.sin(ra), np.sin(dec)])
    assert np.allclose(v, want, atol=2e-4) and abs(np.linalg.norm(v) - 1.0) < 1e-12


def _write_real_dipoles(tmp_path, use_racs):
    import json as _json
    blk = lambda D, s: {"D_icrs": D, "cov_icrs": (np.eye(3) * s ** 2).tolist(), "cov_icrs_stat_only": (np.eye(3) * (0.5 * s) ** 2).tolist()}
    d = {"blocks": {"Quaia_G20": blk([0.01, 0.0, 0.0], 0.004), "Quaia_G20p5": blk([0.012, 0.0, 0.0], 0.003), "NVSS": blk([0.0, 0.01, 0.0], 0.005), "RACS": blk([0.0, 0.0, 0.05], 0.004)},
         "likelihood_inputs": {"Quasars": ["Quaia_G20", "Quaia_G20p5"], "Radio": ["NVSS"] + (["RACS"] if use_racs else [])}}
    p = tmp_path / "real.json"; p.write_text(_json.dumps(d)); return p


def test_sourced_count_data_path_respects_use_flags(tmp_path):
    from htt.htt.infer import tensor_joint_multiprobe_likelihood as tm

    for use_racs, n_radio in ((False, 3), (True, 6)):
        p = _write_real_dipoles(tmp_path, use_racs)
        q = tm.QuaiaCountsDipoleLikelihood(repo_root=tmp_path, alpha=0.75, dipole_data_path=p)
        r = tm.RadioCountDipoleLikelihood(repo_root=tmp_path, alpha=0.75, dipole_data_path=p)
        assert q.n_data == 6 and r.n_data == n_radio
        assert np.allclose(q.data_vector[:3], [0.01, 0, 0]) and np.allclose(r.data_vector[:3], [0, 0.01, 0])
        th = tm.ThetaKinematic.from_vector(np.r_[np.zeros(14), 1.0, 0.0, 0.0])
        assert r.predict(th, tm.PsiCosmology()).shape == (n_radio,)
        assert q.data_provenance.startswith("REAL_DIPOLES_JSON") and r.data_provenance.startswith("REAL_DIPOLES_JSON")
        nested = q.cov_matrix[0:3, 3:6]                       # nested samples: shot-noise cross-covariance = stat cov of the larger sample
        assert np.allclose(nested, np.eye(3) * (0.5 * 0.003) ** 2)
