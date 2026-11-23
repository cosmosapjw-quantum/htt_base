"""Physical and numerical validation for tilted HYREC-2 recombination (N3)."""
from __future__ import annotations

import csv
from pathlib import Path

import numpy as np
from numpy.testing import assert_allclose

from bass.background.geometry import pstf_rank2
from bass.recombination.reionization import ReionizationParameters
from bass.recombination.tilted_hyrec import (
    TiltedRecombinationChannels,
    channel_expansion_from_tilted_kinematics,
    compare_against_forbidden_global_gamma_H,
    hyrec_emla_rhs_and_jacobian,
    integrate_tilted_recombination,
    load_hyrec_atomic_tables,
    to_clocked_chemistry_inputs,
)

REF_CSV = Path(__file__).resolve().parent / "fixtures/recombination_ref_planck2018.csv"


def test_sha_verified_tables_and_flrw_planck2018_match() -> None:
    tables = load_hyrec_atomic_tables(verify_sha256=True)
    assert set(tables.sha256_manifest) == {
        "Alpha_inf.dat",
        "R_inf.dat",
        "fit_swift.dat",
        "two_photon_tables.dat",
    }

    z_check = np.array([1500.0, 1400.0, 1300.0, 1200.0, 1100.0, 1000.0, 900.0, 800.0, 500.0, 100.0])
    hist = integrate_tilted_recombination(
        z_check,
        h=0.6735837,
        t_cmb0=2.72548,
        omega_b=0.0494142797907188,
        omega_m=0.313841,
        omega_r=9.220339e-5,
        omega_lambda=0.686067,
        y_he=0.245,
        n_h0_m3=0.1899866,
        tables=tables,
    )

    ref = {}
    with REF_CSV.open() as f:
        for row in csv.DictReader(line for line in f if not line.startswith("#")):
            zv = float(row["z"])
            if zv in set(z_check):
                ref[zv] = (float(row["x_e"]), float(row["T_m"]))

    rel_xe = [abs(float(hist.x_e[i]) - ref[float(zv)][0]) / ref[float(zv)][0] for i, zv in enumerate(z_check)]
    rel_tm = [abs(float(hist.T_m_K[i]) - ref[float(zv)][1]) / ref[float(zv)][1] for i, zv in enumerate(z_check)]
    assert max(rel_xe) < 0.005  # < 0.5% across z=100..1500
    assert max(rel_xe[1:]) < 0.002  # < 0.2% across z=100..1400
    assert max(rel_tm) < 0.001  # < 0.1% in T_m
    assert np.all(hist.x_HII >= 0.0) and np.all(hist.x_HII <= 1.0)
    assert np.all(hist.T_m_K > 0.0)


def test_rhs_jacobian_and_four_channel_tangents_match_fd() -> None:
    tables = load_hyrec_atomic_tables()
    ch = TiltedRecombinationChannels(
        reaction_clock_rate_s=3.4e-13,
        proper_hydrogen_density_cm3=260.0,
        lya_escape_expansion_s=3.2e-13,
        matter_expansion_rate_s=3.1e-13,
        gamma_baryon=1.08,
        tr_baryon_k=3000.0,
    )
    xh = 0.22
    tm = 2990.0
    rhs0, jac, tans = hyrec_emla_rhs_and_jacobian(xh, tm, ch, tables, f_he=0.0811)

    def eval_xy(xx: float, tt: float) -> np.ndarray:
        r, _, _ = hyrec_emla_rhs_and_jacobian(xx, tt, ch, tables, f_he=0.0811)
        return r

    eps_x = 1e-7
    eps_t = 1e-4
    fd_x = (eval_xy(xh + eps_x, tm) - eval_xy(xh - eps_x, tm)) / (2.0 * eps_x)
    fd_t = (eval_xy(xh, tm + eps_t) - eval_xy(xh, tm - eps_t)) / (2.0 * eps_t)
    assert_allclose(jac[:, 0], fd_x, rtol=1e-6, atol=1e-8)
    assert_allclose(jac[:, 1], fd_t, rtol=1e-6, atol=1e-8)

    for key, base_val in (
        ("reaction_clock_rate_s", ch.reaction_clock_rate_s),
        ("proper_hydrogen_density_cm3", ch.proper_hydrogen_density_cm3),
        ("lya_escape_expansion_s", ch.lya_escape_expansion_s),
        ("matter_expansion_rate_s", ch.matter_expansion_rate_s),
    ):
        h_s = 1e-5 * base_val
        ch_p = TiltedRecombinationChannels(**{**ch.__dict__, key: base_val + h_s})
        ch_m = TiltedRecombinationChannels(**{**ch.__dict__, key: base_val - h_s})
        rp, _, _ = hyrec_emla_rhs_and_jacobian(xh, tm, ch_p, tables, f_he=0.0811)
        rm, _, _ = hyrec_emla_rhs_and_jacobian(xh, tm, ch_m, tables, f_he=0.0811)
        assert_allclose(tans[key], (rp - rm) / (2.0 * h_s), rtol=1e-5, atol=1e-7)
    assert np.all(np.isfinite(rhs0))


def test_tilt_channel_separation_and_anisotropic_sobolev_order() -> None:
    # 1) Compare physical 4-channel separation vs forbidden H -> Gamma H across two |beta| amplitudes
    zs = np.linspace(1500.0, 800.0, 15)
    c1 = compare_against_forbidden_global_gamma_H(zs, beta_const=[0.08, -0.04, 0.03])
    c2 = compare_against_forbidden_global_gamma_H(zs, beta_const=[0.16, -0.08, 0.06])
    # Must differ genuinely and scale ~ O(beta^2) (~factor of ~4 when beta doubles)
    assert c1["max_rel_xe_diff_phys_vs_forbidden"] > 1e-3
    ratio = c2["max_rel_xe_diff_phys_vs_forbidden"] / c1["max_rel_xe_diff_phys_vs_forbidden"]
    assert 3.0 < ratio < 5.0

    # 2a) Optically thick Sobolev cancellation theorem: P_esc ~ 1/tau_S linear in K(n) => O(sigma^2) vanishes!
    H0 = 3.0e-13
    S_unit = pstf_rank2(np.diag([-1.0, 0.4, 0.6])) * H0
    eps_small = 1e-2
    ch_thick_0 = channel_expansion_from_tilted_kinematics(H0, [0.0, 0.0, 0.0], None, H0 * 3.0, 200.0, 0.5, 3000.0)
    ch_thick_p = channel_expansion_from_tilted_kinematics(H0, [0.0, 0.0, 0.0], eps_small * S_unit, H0 * 3.0, 200.0, 0.5, 3000.0)
    assert abs(ch_thick_p.lya_escape_expansion_s - ch_thick_0.lya_escape_expansion_s) / H0 < 1e-13

    # 2b) Physical moderate optical depth tau_S ~ 1.5 (n1s ~ 3.35e-6 cm^-3, H0 = 3e-13 s^-1):
    # nonlinear P_esc(tau_S) yields quadratic O(sigma^2) shift with zero O(sigma^1) odd part!
    n_mod = 3.35e-6  # physical dimensionless tau_S = A_LyA * n1s / (LYA_FACT * H0) ~ 1.50
    eps_mod = 0.08
    ch0 = channel_expansion_from_tilted_kinematics(H0, [0.0, 0.0, 0.0], None, H0 * 3.0, n_mod, 1.0, 3000.0)
    ch_p = channel_expansion_from_tilted_kinematics(H0, [0.0, 0.0, 0.0], eps_mod * S_unit, H0 * 3.0, n_mod, 1.0, 3000.0)
    ch_m = channel_expansion_from_tilted_kinematics(H0, [0.0, 0.0, 0.0], -eps_mod * S_unit, H0 * 3.0, n_mod, 1.0, 3000.0)
    ch_2 = channel_expansion_from_tilted_kinematics(H0, [0.0, 0.0, 0.0], 2.0 * eps_mod * S_unit, H0 * 3.0, n_mod, 1.0, 3000.0)
    d1 = abs(ch_p.lya_escape_expansion_s - ch0.lya_escape_expansion_s)
    d2 = abs(ch_2.lya_escape_expansion_s - ch0.lya_escape_expansion_s)
    odd_part = abs(ch_p.lya_escape_expansion_s - ch_m.lya_escape_expansion_s)
    assert d1 / H0 > 1e-5
    assert odd_part <= 0.1 * d1  # quadratic scaling (small cubic O(sigma^3) residual at eps=0.08)
    assert 3.4 < d2 / d1 < 4.5  # quadratic O(sigma^2) scaling!


def test_reionization_visibility_and_clocked_chemistry_bridge() -> None:
    tables = load_hyrec_atomic_tables()
    zs = np.linspace(1500.0, 0.0, 301)
    reion = ReionizationParameters(z_reion_H=7.67, delta_z_H=0.5, z_reion_HeII=3.5, delta_z_HeII=0.5, include_HeII=True)
    hist = integrate_tilted_recombination(zs, tables=tables, reionization=reion)
    assert hist.x_e[-1] > 1.0  # reionized near z=0
    # Visibility normalization: int g dN + exp(-tau_max) == 1 across monotonic grid
    dN = np.diff(hist.N_grid)
    g_mid = 0.5 * (hist.visibility[:-1] + hist.visibility[1:])
    vis_integral = float(np.sum(g_mid * dN)) + float(np.exp(-hist.kappa[0]))
    assert_allclose(vis_integral, 1.0, atol=2e-3)

    z_cells = np.linspace(1250.0, 950.0, 13)
    n_c = len(z_cells) - 1
    betas = np.tile([0.05, -0.02, 0.01], (n_c, 1))
    dirs = np.tile([0.0, 0.0, 1.0], (n_c, 1))
    chem = to_clocked_chemistry_inputs(
        z_cells, hist, tables, beta_by_cell=betas, photon_direction_by_cell=dirs, comoving_hydrogen_m3=0.19
    )
    assert np.all(chem.population >= 0.0)
    assert_allclose(chem.population.sum(axis=1), 1.0, atol=1e-13)
    assert np.all(chem.delta_optical_depth > 0.0)
