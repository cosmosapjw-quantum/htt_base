"""GBI-06 tests: Calibrated Planck PR3+FFP10 (300 pairs), isolated NPIPE PR4
(PR4_NULL_NOT_FORMABLE), real 8-probe reconciliation, and Acceptance Test 10.
"""

from __future__ import annotations

import json
import math
from pathlib import Path

import numpy as np
import pytest

from htt.htt.infer.r49_general_bianchi_likelihood import (
    CF4TomographicCarrierData,
    CMBCarrierData,
    CMBModeBudgetSpec,
    DEFAULT_PROBES,
    DESIBAOAndDirectionalCarrierData,
    DipoleCarrierData,
    FrameEpochAlignmentSpec,
    GaiaVSHCarrierData,
    LaneContaminationError,
    PantheonCarrierData,
    PsiCosmology,
    R49GeneralBianchiLikelihood,
    R49JointState,
    R49MultiProbeDataset,
)


OUT_DIR = (
    Path(__file__).resolve().parents[2]
    / "docs"
    / "research_program"
    / "observational_publication_20261015"
    / "R49_GENERAL_TILTED_BIANCHI_20261112"
)
CHAIN_DIR = Path("/mnt/extdrive/workdir/r49_chains")


def load_real_dataset_from_npz(npz_path: Path, *, use_pr4: bool = False, use_racs_raw: bool = False) -> R49MultiProbeDataset:
    z = np.load(npz_path, allow_pickle=False)
    ells = tuple(int(v) for v in z["ells"])
    mode_labels = tuple(str(v) for v in z["mode_labels"])
    if use_pr4:
        cmb = CMBCarrierData(
            ells=ells,
            mode_labels=mode_labels,
            d_obs=np.asarray(z["cmb_pr4_d"], dtype=np.float64),
            cov=np.asarray(z["cmb_pr4_cov"], dtype=np.float64),
            lane="NPIPE_PR4_ROBUSTNESS",
            mc_source="PR4_NULL_NOT_FORMABLE",
            coordinate_frame="galactic",
            n_mc=0,
        )
    else:
        cmb = CMBCarrierData(
            ells=ells,
            mode_labels=mode_labels,
            d_obs=np.asarray(z["cmb_pr3_d"], dtype=np.float64),
            cov=np.asarray(z["cmb_pr3_cov"], dtype=np.float64),
            lane="PR3_CALIBRATED",
            mc_source="FFP10_PR3",
            coordinate_frame="galactic",
            n_mc=300,
        )
    quaia = DipoleCarrierData(
        probe_name="Quaia",
        d_obs=np.asarray(z["quaia_d_icrs"], dtype=np.float64),
        cov=np.asarray(z["quaia_cov_icrs"], dtype=np.float64),
        c_eb=4.5,
        coordinate_frame="icrs",
        z_eff=1.47,
        n_sources=int(z["quaia_n_sources"]),
    )
    nvss = DipoleCarrierData(
        probe_name="NVSS",
        d_obs=np.asarray(z["nvss_d_icrs"], dtype=np.float64),
        cov=np.asarray(z["nvss_cov_icrs"], dtype=np.float64),
        c_eb=4.0,
        coordinate_frame="icrs",
        z_eff=1.1,
        n_sources=int(z["nvss_n_sources"]),
    )
    racs_cov_key = "racs_cov_raw_icrs" if use_racs_raw else "racs_cov_sys_icrs"
    racs = DipoleCarrierData(
        probe_name="RACS",
        d_obs=np.asarray(z["racs_d_icrs"], dtype=np.float64),
        cov=np.asarray(z[racs_cov_key], dtype=np.float64),
        c_eb=4.2,
        coordinate_frame="icrs",
        z_eff=0.8,
        n_sources=int(z["racs_n_sources"]),
    )
    th11 = np.asarray(z["gaia_theta11_icrs"], dtype=np.float64)
    gaia = GaiaVSHCarrierData(
        e1_obs=th11[0:3],
        b1_obs=th11[3:6],
        e2_obs=th11[6:11],
        cov_e1b1e2=np.asarray(z["gaia_cov11_icrs"], dtype=np.float64),
        coordinate_frame="icrs",
        z_eff=1.47,
        n_sources=int(z["gaia_n_sources"]),
    )
    pantheon = PantheonCarrierData(
        z_hd=np.asarray(z["pan_z_hd"], dtype=np.float64),
        z_hel=np.asarray(z["pan_z_hel"], dtype=np.float64),
        n_hat_gal=np.asarray(z["pan_n_hat_gal"], dtype=np.float64),
        m_b_obs=np.asarray(z["pan_m_b"], dtype=np.float64),
        cov=np.asarray(z["pan_cov"], dtype=np.float64),
    )
    cf4 = CF4TomographicCarrierData(
        shell_z_bins=tuple((float(a), float(b)) for a, b in z["cf4_bins"]),
        d_obs=np.asarray(z["cf4_d_gal"], dtype=np.float64),
        cov=np.asarray(z["cf4_cov_gal"], dtype=np.float64),
        coordinate_frame="galactic",
    )
    desi = DESIBAOAndDirectionalCarrierData(
        bao_z=np.asarray(z["desi_bao_z"], dtype=np.float64),
        bao_quantities=tuple(str(q) for q in z["desi_bao_quantities"]),
        bao_mean=np.asarray(z["desi_bao_mean"], dtype=np.float64),
        bao_cov=np.asarray(z["desi_bao_cov"], dtype=np.float64),
        directional_quad_obs=np.asarray(z["desi_dq_obs_gal"], dtype=np.float64),
        directional_quad_cov=np.asarray(z["desi_dq_cov_gal"], dtype=np.float64),
        coordinate_frame="galactic",
    )
    return R49MultiProbeDataset(cmb, quaia, nvss, racs, gaia, pantheon, cf4, desi)


def test_gbi06_pr3_npipe_and_owned_data_receipts() -> None:
    pr3 = json.loads((OUT_DIR / "GBI06_CMB_PR3_CALIBRATION_RECEIPT.json").read_text(encoding="utf-8"))
    pr4 = json.loads((OUT_DIR / "GBI06_NPIPE_ROBUSTNESS_RECEIPT.json").read_text(encoding="utf-8"))
    data = json.loads((OUT_DIR / "GBI06_OWNED_DATA_RECONCILIATION_RECEIPT.json").read_text(encoding="utf-8"))

    assert pr3["lane"] == "PR3_CALIBRATED"
    assert pr3["mc_source"] == "FFP10_PR3"
    assert pr3["n_ffp10_pairs"] == 300
    assert pr3["hmhd_dof"] == 135
    assert math.isfinite(pr3["coupling_cond_T"]) and pr3["coupling_cond_T"] < 50.0
    assert math.isfinite(pr3["coupling_cond_EB"]) and pr3["coupling_cond_EB"] < 50.0
    strat = pr3["stratified_ffp10_convergence"]
    assert strat["N60_smoke"]["n_pairs"] == 60
    assert strat["N200_pilot"]["n_pairs"] == 200
    assert strat["N300_production"]["n_pairs"] == 300
    for fam in ("I", "V", "VII_0", "VII_h", "IX"):
        rec = pr3["injection_recovery_across_families"][fam]
        assert rec["bias_z_sigma"] < 5.5
        assert rec["cos_alignment"] > 0.55

    # Acceptance Test 10: PR4 isolation and PR4_NULL_NOT_FORMABLE
    assert pr4["lane"] == "NPIPE_PR4_ROBUSTNESS"
    assert pr4["mc_source"] == "PR4_NULL_NOT_FORMABLE"
    assert pr4["null_status"] == "PR4_NULL_NOT_FORMABLE"
    assert pr4["pr3_ffp10_sims_used"] is False
    assert pr4["lane_isolation_verified"] is True
    assert pr4["frequencies_ghz"] == [100, 143, 217]
    assert set(pr4["rimo_e_mode_tf_ell2_6"].keys()) == {"100", "143", "217"}

    assert data["no_new_data_downloaded"] is True
    assert data["probes_reconciled"] == ["Quaia", "NVSS", "RACS", "Gaia+ICRF3", "Pantheon+", "CF4", "DESI"]
    assert data["quaia_g205"]["n_sources"] > 1_000_000
    assert data["nvss"]["n_sources_cut"] > 50_000
    assert data["racs"]["systematics_flagged"] is True
    assert data["gaia_icrf3"]["n_quasars_joined"] == 692_154
    assert data["pantheon_plus"]["n_sne_hubble_flow_z_gt_0p01"] == 1590
    assert len(data["cf4"]["shells"]) == 4
    assert data["desi"]["bao_points"] == 13


def test_gbi06_real_npz_loads_into_r49_likelihood_with_lane_guards() -> None:
    npz_path = CHAIN_DIR / "r49_real_multiprobe_dataset.npz"
    ffp_path = CHAIN_DIR / "ffp10_300_debiased_135.npz"
    assert npz_path.exists()
    assert ffp_path.exists()

    ffp = np.load(ffp_path)
    assert ffp["sim_tot"].shape == (300, 135)
    assert ffp["sim_noise"].shape == (300, 135)
    # Historical caches may contain null_beta; it must not be used as a velocity null.
    assert ffp["sim_tot"].shape[1] == 135

    ds_pr3 = load_real_dataset_from_npz(npz_path, use_pr4=False)
    align = FrameEpochAlignmentSpec(triad_frame="galactic", triad_rotation=np.eye(3))
    b_pr3 = CMBModeBudgetSpec(lane="PR3_CALIBRATED", mc_source="FFP10_PR3")
    ll_pr3 = R49GeneralBianchiLikelihood(ds_pr3, mode_budget=b_pr3, alignment=align, active_probes=DEFAULT_PROBES)

    st = R49JointState(
        family="I",
        sigma_AB_stf5=np.zeros(5),
        omega_A=np.zeros(3),
        A_A=np.zeros(3),
        v_matter=np.zeros(3),
        v_rad=np.zeros(3),
        beta_MO=np.array([-6.9e-4, -9.1e-4, 4.9e-4]),
        psi=PsiCosmology(),
    )
    scores = ll_pr3.logp_by_probe(st)
    assert set(scores.keys()) == set(DEFAULT_PROBES)
    assert all(math.isfinite(v) for v in scores.values())

    # Acceptance Test 10 fail-closed lane check: PR4 map with PR3/FFP10 budget must fail!
    ds_pr4 = load_real_dataset_from_npz(npz_path, use_pr4=True)
    with pytest.raises(LaneContaminationError):
        R49GeneralBianchiLikelihood(ds_pr4, mode_budget=b_pr3, alignment=align)

    b_pr4 = CMBModeBudgetSpec(lane="NPIPE_PR4_ROBUSTNESS", mc_source="PR4_NULL_NOT_FORMABLE")
    ll_pr4 = R49GeneralBianchiLikelihood(ds_pr4, mode_budget=b_pr4, alignment=align, active_probes=DEFAULT_PROBES)
    assert math.isfinite(ll_pr4.logp(st))
