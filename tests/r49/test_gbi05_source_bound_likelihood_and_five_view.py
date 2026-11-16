"""GBI-05 tests: Unified source-bound multi-probe likelihood, SO(3) triad invariance,
fail-closed guards (Acceptance Tests 9, 11, 12), and single-posterior 5-view pushforward.
"""

from __future__ import annotations

import json
import math
import os
from pathlib import Path

import healpy as hp
import numpy as np
import pytest

from bass.transport.general_bianchi_transfer import (
    TiltedTransferParameters,
    compute_general_bianchi_transfer,
    map_from_scalar_alm,
    qu_from_spin2_alm,
)
from common.relativistic_velocity_closure import kinematic_quadrupole_stf2
from common.stf_metric_bridge import G_STF5, stf_matrix_to_cartesian
from htt.htt.infer.r49_general_bianchi_likelihood import (
    CMBCarrierData,
    CMBModeBudgetSpec,
    CF4TomographicCarrierData,
    DEFAULT_PROBES,
    DESIBAOAndDirectionalCarrierData,
    DipoleCarrierData,
    DoubleCountedLowEllError,
    EpochMismatchError,
    FrameEpochAlignmentSpec,
    GALACTIC_TO_ICRS_MATRIX,
    GaiaVSHCarrierData,
    ICRS_TO_GALACTIC_MATRIX,
    LaneContaminationError,
    MissingTriadError,
    PantheonCarrierData,
    PsiCosmology,
    R49GeneralBianchiLikelihood,
    R49JointState,
    R49MultiProbeDataset,
    SPEED_OF_LIGHT_KM_S,
    ScalarSpeedError,
    SplitPosteriorFiveViewError,
    T_CMB_K,
    UnmarginalizedGaiaSpinError,
    _pack_transfer_modes,
    _rotate_stf5_cartesian,
    compute_r49_htt_five_views_from_posterior,
    compute_scalar_xc_ablation_comparison,
    standard_lowell_mode_labels,
)


RECEIPT_PATH = (
    Path(__file__).resolve().parents[2]
    / "docs"
    / "research_program"
    / "observational_publication_20261015"
    / "R49_GENERAL_TILTED_BIANCHI_20261112"
    / "GBI05_LIKELIHOOD_AND_FIVE_VIEW_RECEIPT.json"
)


def _random_so3(seed: int) -> np.ndarray:
    rng = np.random.default_rng(seed)
    A = rng.normal(size=(3, 3))
    Q, R = np.linalg.qr(A)
    Q *= np.sign(np.diag(R))[None, :]
    if np.linalg.det(Q) < 0:
        Q[:, 0] *= -1.0
    return Q


def _make_synthetic_dataset(truth: R49JointState, *, seed: int = 101) -> tuple[R49MultiProbeDataset, CMBModeBudgetSpec]:
    rng = np.random.default_rng(seed)
    ells = (2, 3, 4, 5, 6)
    labels = standard_lowell_mode_labels(ells, include_eb=True)
    budget = CMBModeBudgetSpec(
        ell_min=2,
        ell_max=6,
        deterministic_ells=(2, 3, 4),
        covariance_ells=(5, 6),
        lane="PR3_CALIBRATED",
        mc_source="FFP10_PR3",
        transfer_mode="linearized_near_flrw",
        use_polarized_eb=True,
    )
    out = compute_general_bianchi_transfer(
        TiltedTransferParameters(
            family=truth.family,
            sigma_N=truth.sigma_matrix,
            v_matter=truth.v_matter,
            v_rad=truth.v_rad,
            v_obs=truth.beta_MO,
            h_bianchi=truth.h_bianchi,
            omega_k=truth.omega_k,
            handedness=truth.handedness,
            ell_max=6,
            n_gl_theta=16,
            transfer_mode="linearized_near_flrw",
        )
    )
    d_cmb = 1.0e6 * T_CMB_K * _pack_transfer_modes(out.alm_T, out.alm_E, out.alm_B, labels)
    # Zero out deterministic expectations only? No, synthetic truth carries full realization
    cov_diag = np.array([400.0 if lbl.startswith("T_") else 9.0 for lbl in labels], dtype=np.float64)
    cov_cmb = np.diag(cov_diag)
    cmb = CMBCarrierData(
        ells=ells,
        mode_labels=labels,
        d_obs=d_cmb,
        cov=cov_cmb,
        lane="PR3_CALIBRATED",
        mc_source="FFP10_PR3",
        coordinate_frame="galactic",
        n_mc=300,
    )

    def _dip(name: str, c_eb: float, frame: str, sigma_ax: float) -> DipoleCarrierData:
        vec_gal = c_eb * (truth.beta_MO + 0.1 * truth.A_A)
        d = vec_gal if frame == "galactic" else GALACTIC_TO_ICRS_MATRIX @ vec_gal
        return DipoleCarrierData(
            probe_name=name,
            d_obs=d,
            cov=(sigma_ax**2) * np.eye(3),
            c_eb=c_eb,
            coordinate_frame=frame,
            z_eff=1.2,
            n_sources=100_000,
        )

    quaia = _dip("Quaia", 4.5, "icrs", 2.0e-3)
    nvss = _dip("NVSS", 4.0, "icrs", 3.0e-3)
    racs = _dip("RACS", 4.2, "icrs", 5.0e-3)

    H0_uasyr = (truth.psi.H_0 * 1.0227e-12) * (180.0 * 3600.0e6 / math.pi)
    e1_gal = H0_uasyr * (truth.beta_MO + truth.A_A)
    b1_gal = H0_uasyr * truth.omega_A + np.array([12.0, -7.0, 5.0])  # plus unmodeled Gaia spin nuisance!
    e2_gal = H0_uasyr * (
        truth.sigma_AB_stf5 + 0.25 * stf_matrix_to_cartesian(kinematic_quadrupole_stf2(truth.beta_MO))
    )
    R_g2i = GALACTIC_TO_ICRS_MATRIX
    gaia = GaiaVSHCarrierData(
        e1_obs=R_g2i @ e1_gal,
        b1_obs=R_g2i @ b1_gal,
        e2_obs=_rotate_stf5_cartesian(e2_gal, R_g2i),
        cov_e1b1e2=np.diag(np.concatenate([np.full(6, 2.0**2), np.full(5, 1.5**2)])),
        coordinate_frame="icrs",
        z_eff=1.4,
        n_sources=1_200_000,
    )

    n_sn = 32
    raw_dirs = rng.normal(size=(n_sn, 3))
    n_hat_gal = raw_dirs / np.linalg.norm(raw_dirs, axis=1, keepdims=True)
    z_hd = np.linspace(0.02, 1.2, n_sn)
    z_hel = z_hd + 1.0e-3
    m_b = np.array(
        [
            5.0 * math.log10(max((1.0 + float(zhl)) * truth.psi.transverse_comoving_distance_Mpc(float(zh)), 1.0e-9)) + 25.0
            for zh, zhl in zip(z_hd, z_hel)
        ],
        dtype=np.float64,
    )
    m_b += 19.3  # arbitrary M_0 marginalized by Schur!
    n_dot_dip = n_hat_gal @ (truth.beta_MO - truth.v_matter + 0.5 * truth.A_A)
    n_sig_n = np.einsum("ni,ij,nj->n", n_hat_gal, truth.sigma_matrix, n_hat_gal)
    m_b -= (5.0 / math.log(10.0)) * (n_dot_dip / np.maximum(z_hd, 0.015) - 0.5 * z_hd * n_sig_n)
    pantheon = PantheonCarrierData(
        z_hd=z_hd,
        z_hel=z_hel,
        n_hat_gal=n_hat_gal,
        m_b_obs=m_b,
        cov=(0.12**2) * np.eye(n_sn),
    )

    bins = ((0.0, 0.02), (0.02, 0.04), (0.04, 0.06), (0.06, 0.08))
    base_v = SPEED_OF_LIGHT_KM_S * (truth.v_matter - truth.beta_MO)
    d_cf4 = np.concatenate([base_v + SPEED_OF_LIGHT_KM_S * (0.5 * (a + b)) * 0.1 * truth.A_A for a, b in bins])
    cf4 = CF4TomographicCarrierData(
        shell_z_bins=bins,
        d_obs=d_cf4,
        cov=(40.0**2) * np.eye(3 * len(bins)),
        coordinate_frame="galactic",
    )

    bao_z = np.array([0.51, 0.71, 1.32])
    bao_q = ("DM_over_rs", "DH_over_rs", "DV_over_rs")
    bao_m = np.array(
        [
            truth.psi.transverse_comoving_distance_Mpc(0.51) / truth.psi.r_d,
            truth.psi.hubble_distance_Mpc(0.71) / truth.psi.r_d,
            truth.psi.volume_distance_Mpc(1.32) / truth.psi.r_d,
        ],
        dtype=np.float64,
    )
    desi = DESIBAOAndDirectionalCarrierData(
        bao_z=bao_z,
        bao_quantities=bao_q,
        bao_mean=bao_m,
        bao_cov=(0.25**2) * np.eye(3),
        directional_quad_obs=truth.sigma_AB_stf5.copy(),
        directional_quad_cov=(5.0e-4) ** 2 * np.eye(5),
        coordinate_frame="galactic",
    )
    return R49MultiProbeDataset(cmb, quaia, nvss, racs, gaia, pantheon, cf4, desi), budget


def test_healpy_real_alm_packing_parity() -> None:
    lmax = 5
    labels = standard_lowell_mode_labels([2, 3, 4, 5], include_eb=True)
    n_alm = hp.Alm.getsize(lmax)
    rng = np.random.default_rng(17)
    alm_T = np.zeros(n_alm, dtype=np.complex128)
    alm_E = np.zeros(n_alm, dtype=np.complex128)
    alm_B = np.zeros(n_alm, dtype=np.complex128)
    for ell in [2, 3, 4, 5]:
        for m in range(ell + 1):
            idx = hp.Alm.getidx(lmax, ell, m)
            if m == 0:
                alm_T[idx], alm_E[idx], alm_B[idx] = rng.normal(size=3)
            else:
                alm_T[idx] = rng.normal() + 1j * rng.normal()
                alm_E[idx] = rng.normal() + 1j * rng.normal()
                alm_B[idx] = rng.normal() + 1j * rng.normal()

    nside = 128
    ipix = np.arange(hp.nside2npix(nside))
    th, ph = hp.pix2ang(nside, ipix)
    dT: dict[tuple[int, int], complex] = {}
    dE: dict[tuple[int, int], complex] = {}
    dB: dict[tuple[int, int], complex] = {}
    for ell in range(lmax + 1):
        for m in range(ell + 1):
            idx = hp.Alm.getidx(lmax, ell, m)
            dT[(ell, m)] = complex(alm_T[idx])
            dE[(ell, m)] = complex(alm_E[idx])
            dB[(ell, m)] = complex(alm_B[idx])
            if m > 0:
                sgn = -1.0 if (m % 2 == 1) else 1.0
                dT[(ell, -m)] = sgn * complex(np.conj(alm_T[idx]))
                dE[(ell, -m)] = sgn * complex(np.conj(alm_E[idx]))
                dB[(ell, -m)] = sgn * complex(np.conj(alm_B[idx]))

    T_map = map_from_scalar_alm(dT, th, ph, ell_min=0, ell_max=lmax)
    Q_map, U_map = qu_from_spin2_alm(dE, dB, th, ph, ell_max=lmax)
    back = hp.map2alm([T_map, Q_map, U_map], lmax=lmax, pol=True)
    dT_b = {(ell, m): back[0][hp.Alm.getidx(lmax, ell, m)] for ell in range(lmax + 1) for m in range(ell + 1)}
    dE_b = {(ell, m): back[1][hp.Alm.getidx(lmax, ell, m)] for ell in range(lmax + 1) for m in range(ell + 1)}
    dB_b = {(ell, m): back[2][hp.Alm.getidx(lmax, ell, m)] for ell in range(lmax + 1) for m in range(ell + 1)}

    v_ref = _pack_transfer_modes(dT, dE, dB, labels)
    v_back = _pack_transfer_modes(dT_b, dE_b, dB_b, labels)
    assert float(np.max(np.abs(v_ref - v_back))) < 1.0e-13


def test_unified_8probe_so3_triad_invariance_and_families() -> None:
    truth = R49JointState(
        family="VII_h",
        sigma_AB_stf5=np.array([1.2e-4, -0.5e-4, 0.8e-4, -0.3e-4, 0.4e-4]),
        omega_A=np.array([0.02, -0.01, 0.03]),
        A_A=np.array([0.01, -0.015, 0.02]),
        v_matter=np.array([1.5e-4, -2.0e-4, 0.8e-4]),
        v_rad=np.array([-1.0e-4, 1.5e-4, -0.4e-4]),
        beta_MO=np.array([-1.1e-3, -0.2e-3, 0.5e-3]),
        psi=PsiCosmology(H_0=67.8, Omega_m=0.312, r_d=147.2, DeltaOmega_k=0.005),
        h_bianchi=0.3,
        omega_k=0.02,
        handedness=1,
    )
    dataset, budget = _make_synthetic_dataset(truth)

    align_gal = FrameEpochAlignmentSpec(triad_frame="galactic", triad_rotation=np.eye(3))
    ll_gal = R49GeneralBianchiLikelihood(dataset, mode_budget=budget, alignment=align_gal, active_probes=DEFAULT_PROBES)
    scores_gal = ll_gal.logp_by_probe(truth)
    assert set(scores_gal.keys()) == set(DEFAULT_PROBES)
    assert all(math.isfinite(v) for v in scores_gal.values())

    # Active SO(3) rotation + switch triad_frame to icrs must give IDENTICAL per-probe logp!
    Q = _random_so3(2026)
    align_rot = FrameEpochAlignmentSpec(triad_frame="galactic", triad_rotation=Q)
    ll_rot = R49GeneralBianchiLikelihood(dataset, mode_budget=budget, alignment=align_rot, active_probes=DEFAULT_PROBES)
    scores_rot = ll_rot.logp_by_probe(truth.rotated_by(Q))
    for k in DEFAULT_PROBES:
        assert abs(scores_gal[k] - scores_rot[k]) < 1.0e-10, f"Triad invariance broke on {k}: {scores_gal[k]} vs {scores_rot[k]}"

    # Check Gaia spin marginalization invariance under arbitrary B1 shift!
    dataset_spin = _make_synthetic_dataset(truth)[0]
    shifted_b1 = dataset_spin.gaia.b1_obs + np.array([150.0, -230.0, 95.0])
    ds2 = R49MultiProbeDataset(
        dataset_spin.cmb,
        dataset_spin.quaia,
        dataset_spin.nvss,
        dataset_spin.racs,
        GaiaVSHCarrierData(
            e1_obs=dataset_spin.gaia.e1_obs,
            b1_obs=shifted_b1,
            e2_obs=dataset_spin.gaia.e2_obs,
            cov_e1b1e2=dataset_spin.gaia.cov_e1b1e2,
            coordinate_frame=dataset_spin.gaia.coordinate_frame,
        ),
        dataset_spin.pantheon,
        dataset_spin.cf4,
        dataset_spin.desi,
    )
    ll_spin = R49GeneralBianchiLikelihood(ds2, mode_budget=budget, alignment=align_gal)
    assert abs(ll_spin.logp_by_probe(truth)["Gaia"] - scores_gal["Gaia"]) < 1.0e-11

    # Check evaluation across Class A & non-FLRW-limit Class B families (auto-dispatching geodesic)
    for fam in ("I", "V", "VII_0", "IX", "II", "VI_h", "VIII"):
        st_f = R49JointState(
            family=fam,
            sigma_AB_stf5=truth.sigma_AB_stf5,
            omega_A=truth.omega_A,
            A_A=truth.A_A,
            v_matter=truth.v_matter,
            v_rad=truth.v_rad,
            beta_MO=truth.beta_MO,
            psi=truth.psi,
        )
        lp = ll_gal.logp(st_f)
        assert math.isfinite(lp)


def test_acceptance_9_fail_closed_guards() -> None:
    truth = R49JointState(
        family="I",
        sigma_AB_stf5=np.zeros(5),
        omega_A=np.zeros(3),
        A_A=np.zeros(3),
        v_matter=np.zeros(3),
        v_rad=np.zeros(3),
        beta_MO=np.array([1.0e-3, 0.0, 0.0]),
    )
    dataset, budget = _make_synthetic_dataset(truth)

    with pytest.raises(MissingTriadError):
        FrameEpochAlignmentSpec(triad_rotation=None)
    with pytest.raises(MissingTriadError):
        FrameEpochAlignmentSpec(triad_rotation=np.diag([1.0, 1.0, -1.0]))  # reflection det=-1
    with pytest.raises(EpochMismatchError):
        FrameEpochAlignmentSpec(triad_rotation=np.eye(3), allow_epoch_conflation=True)
    with pytest.raises(EpochMismatchError):
        FrameEpochAlignmentSpec(triad_rotation=np.eye(3), cmb_emission_epoch_z=1.0, observer_epoch_z=0.0)
    with pytest.raises(UnmarginalizedGaiaSpinError):
        FrameEpochAlignmentSpec(triad_rotation=np.eye(3), marginalize_gaia_spin=False)
    with pytest.raises(ScalarSpeedError):
        FrameEpochAlignmentSpec(triad_rotation=np.eye(3), require_vector_tilt=False)
    with pytest.raises(ScalarSpeedError):
        R49JointState(
            family="I",
            sigma_AB_stf5=np.zeros(5),
            omega_A=np.zeros(3),
            A_A=np.zeros(3),
            v_matter=1.0e-3,  # type: ignore[arg-type]
            v_rad=np.zeros(3),
            beta_MO=np.zeros(3),
        )
    # R51 (audit R49-A05): one Gaussian may carry mu(theta) and C(theta) on the
    # same modes; duplication is blocked by data-block identity (tests/r51).
    assert issubclass(DoubleCountedLowEllError, ValueError)
    overlap = CMBModeBudgetSpec(deterministic_ells=(2, 3, 4), covariance_ells=(4, 5, 6))
    assert set(overlap.deterministic_ells) & set(overlap.covariance_ells) == {4}
    with pytest.raises(LaneContaminationError):
        CMBModeBudgetSpec(lane="NPIPE_PR4_ROBUSTNESS", mc_source="FFP10_PR3")

    npipe_budget = CMBModeBudgetSpec(lane="NPIPE_PR4_ROBUSTNESS", mc_source="PR4_NULL_NOT_FORMABLE")
    with pytest.raises(LaneContaminationError):
        R49GeneralBianchiLikelihood(
            dataset,
            mode_budget=npipe_budget,
            alignment=FrameEpochAlignmentSpec(triad_rotation=np.eye(3)),
        )


def test_acceptance_11_and_12_five_view_single_posterior_and_xc_ablation() -> None:
    rng = np.random.default_rng(49)
    n_draws = 128
    draws = np.zeros((n_draws, 24), dtype=np.float64)
    # Full 14D anisotropic spread (sigma_5, omega_3, v_matter_3, beta_MO_3) + v_rad, A_A, psi
    draws[:, 0:5] = rng.normal(loc=[1e-4, -0.5e-4, 0.5e-4, 0.2e-4, -0.2e-4], scale=3.0e-5, size=(n_draws, 5))
    draws[:, 5:8] = rng.normal(loc=0.0, scale=0.01, size=(n_draws, 3))
    draws[:, 8:11] = rng.normal(loc=0.0, scale=0.01, size=(n_draws, 3))
    draws[:, 11:14] = rng.normal(loc=[1e-4, -1e-4, 0.5e-4], scale=5.0e-5, size=(n_draws, 3))
    draws[:, 14:17] = rng.normal(loc=[-1e-4, 1e-4, 0.0], scale=5.0e-5, size=(n_draws, 3))
    draws[:, 17:20] = rng.normal(loc=[-1.2e-3, -0.2e-3, 0.5e-3], scale=8.0e-5, size=(n_draws, 3))
    draws[:, 20:24] = np.tile([67.4, 0.315, 147.09, 0.0], (n_draws, 1))

    null_samples = rng.normal(loc=0.0, scale=4.0e-4, size=(200, 3))
    shell_bins = [(0.0, 0.02), (0.02, 0.04), (0.04, 0.06)]
    shell_vecs = [rng.normal(loc=[-320.0, -50.0, 130.0], scale=20.0, size=3) for _ in shell_bins]
    shell_cov = np.diag(np.full(9, 45.0**2))

    # Acceptance Test 12: split draws forbidden!
    with pytest.raises(SplitPosteriorFiveViewError):
        compute_r49_htt_five_views_from_posterior(draws, split_draws_for_q=draws.copy())
    with pytest.raises(SplitPosteriorFiveViewError):
        compute_r49_htt_five_views_from_posterior(draws, split_draws_for_pi=draws.copy())
    with pytest.raises(SplitPosteriorFiveViewError):
        compute_r49_htt_five_views_from_posterior(draws, split_draws_for_f=draws.copy())
    with pytest.raises(SplitPosteriorFiveViewError):
        compute_r49_htt_five_views_from_posterior(draws, split_draws_for_gf=draws.copy())

    views = compute_r49_htt_five_views_from_posterior(
        draws,
        matched_null_samples_beta=None,
        null_law_name="MATCHED_NULL_FFP10_PR3",
        shell_redshift_bins=shell_bins,
        shell_data_vectors=shell_vecs,
        cross_shell_data_cov=shell_cov,
    )
    assert views["single_posterior_verified"] is True
    assert views["source_posterior_shape"] == [n_draws, 24]
    assert set(views["x_summary"].keys()) >= {"sigma_gram_norm_mean", "beta_MO_norm_mean", "stf5_gram_metric_diag"}
    assert len(views["Q_anchors"]) > 0
    assert len(views["Pi_exceedance"]) > 0
    assert views["F_directional"]["n_directions"] == 100
    assert views["G_F_depth"]["cov_min_eig"] > 0.0

    # Acceptance Test 11: scalar x_C ablation collapses rank to 1 while full tensor keeps rank 14
    ablation = compute_scalar_xc_ablation_comparison(draws)
    assert ablation["ablation_role"] == "ABLATION_ONLY_FORBIDDEN_IN_PRODUCTION"
    assert ablation["scalar_xc_dof"] == 1
    assert ablation["full_tensor_dof"] == 14
    assert ablation["full_covariance_rank"] == 14
    assert ablation["information_loss_ratio_dof"] is None
    assert ablation["coordinate_reduction_fraction"] == pytest.approx(13.0 / 14.0)

    receipt = {
        "schema_version": "r49_gbi05_likelihood_and_five_view_v1",
        "status": "PASS",
        "active_probes": list(DEFAULT_PROBES),
        "g_stf5_diag": np.diag(G_STF5).tolist(),
        "acceptance_tests_verified": ["Test_9_fail_closed_guards", "Test_11_scalar_xc_ablation", "Test_12_single_posterior_five_views"],
        "so3_triad_invariance_verified": True,
        "healpy_real_alm_parity_verified": True,
        "five_view_summary": {k: v for k, v in views.items() if k != "five_variable_state"},
        "scalar_xc_ablation": ablation,
    }
    # R51: historical receipt bytes are preserved; regenerate only on explicit request.
    if os.environ.get("HTT_WRITE_R49_RECEIPTS") == "1":
        RECEIPT_PATH.write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8")
