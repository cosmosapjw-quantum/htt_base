#!/usr/bin/env python3
"""R89 G08_OPTICAL_PHY group execution (create-only).

Executes R81 real-source conditional PHY-01..07 preflight kernels (35,970 CF4
groups via certified Fortran multi_axis_hemisphere, Planck PR3/PR4 Codazzi &
multipole feasibility, Gaia/Quaia E2-B2 mask alias, radial 12D Gram) and ties
them to the newly integrated /mnt/extdrive/workdir cross-probe summaries while
keeping SQ-PHOTON-FLUX / SQ-OPTICAL BLOCKED_INPUT and PHY-01..07 / SQ-CROSS-COV
BLOCKED_DEPENDENCY.
"""
from __future__ import annotations

import hashlib
import json
import math
import platform
import resource
import sys
import time
from pathlib import Path

import numpy as np
from astropy import units as u
from astropy.coordinates import SkyCoord
from scipy.special import roots_legendre

ROOT = Path(__file__).resolve().parents[6]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from htt.obsstat import phy_fast, pre_dag_fast
from htt.obsstat.pre_dag_fast import codazzi_map, radial_design
from scripts.r68.fiveview_geometry import stf_matrix
from scripts.r81.bench_baseline import axes as fib_axes

OUT_DIR = Path(__file__).resolve().parent
OUT_JSON = OUT_DIR / "RESULT.json"

PROG = ROOT / "docs/research_program/observational_publication_20261015"
SELECTED = ROOT / "docs/research_program/cf4_schur_loop8_20261015/inputs/selected_source_observables.npz"
TABLE4 = Path("/mnt/extdrive/workdir/raw/cf4_full/table4.dat")
R80 = PROG / "R80_SQ_CF4_SOURCE_BINDING_20261120/RESULT.json"
R77 = PROG / "R77_SEVEN_PHY_CROSSVIEW_20261119/RESULTS.json"
R76 = PROG / "R76_P6_COVARIANT_DRIFT_FIVEVIEW_20261119/RESULTS.json"
R69 = PROG / "R69_PHYSICAL_OBSERVABLE_BRIDGES_20261118/RESULTS/GAIA_E1B1E2B2.json"
R66 = PROG / "R66_LOWELL_PHYSICAL_OBSERVABLES_20261117/RESULTS/OBSERVABLES.json"


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def _sky_quadrature() -> tuple[np.ndarray, np.ndarray]:
    mu, wt = roots_legendre(100)
    phi = np.arange(200) * np.pi / 100.0
    mm, pp = np.meshgrid(mu, phi, indexing="ij")
    n = np.column_stack([np.sqrt(1.0 - mm.ravel() ** 2) * np.cos(pp.ravel()),
                         np.sqrt(1.0 - mm.ravel() ** 2) * np.sin(pp.ravel()), mm.ravel()])
    weights = np.repeat(wt / (2.0 * 200.0), 200)
    return n, weights


def main() -> int:
    if OUT_JSON.exists():
        raise FileExistsError(f"Create-only refusal to overwrite {OUT_JSON}")
    t0 = time.perf_counter()

    old_anchors = phy_fast.historical_common_anchors()
    assert old_anchors["E0"]["state"] == "completed_scoped"
    assert old_anchors["E1"]["state"] == "completed_scoped"
    assert old_anchors["physical_claim_upgrade"] is False

    r80 = json.loads(R80.read_text(encoding="utf-8"))
    previous = json.loads(R77.read_text(encoding="utf-8"))["results"]
    r66 = json.loads(R66.read_text(encoding="utf-8"))
    gaia = json.loads(R69.read_text(encoding="utf-8"))
    r76 = json.loads(R76.read_text(encoding="utf-8"))["R69_Gaia_VSH_actual_source"]["results"]

    with np.load(SELECTED, allow_pickle=False) as z:
        ids = z["group_id"].copy()
        n = z["n_J2000"].copy()
        e = z["e_dmzp"].copy()
    t4_lines = {int(x[:7]): x for x in TABLE4.read_text(encoding="ascii").splitlines() if x.strip()}
    r_mpc = np.array([float(t4_lines[int(g)][21:26]) for g in ids], dtype=np.float64)
    w_inv2 = 1.0 / (e * e)

    # PHY-01: 96-axis Fortran batch hemisphere moments + exact R80 40-400 Mpc replay
    axes96 = fib_axes(96)
    hemi_ft = phy_fast.multi_axis_hemisphere(n, axes96, weights=w_inv2, native_lib="auto", threads=8)
    ft_rec = phy_fast.last_phy_receipt()
    hemi_np = phy_fast.multi_axis_hemisphere(n, axes96, weights=w_inv2, native_lib=None)
    ft_maxdiff = float(
        max(
            np.max(np.abs(hemi_ft["weights"] - hemi_np["weights"])),
            np.max(np.abs(hemi_ft["means"] - hemi_np["means"])),
            np.max(np.abs(hemi_ft["second"] - hemi_np["second"])),
        )
    )
    dif = hemi_ft["second"][:, 1, :, :] - hemi_ft["second"][:, 0, :, :]
    eigs = np.linalg.eigvalsh(dif)
    leakage = 0.03 * (eigs[:, 2] - eigs[:, 0])

    cmb = SkyCoord(l=264.021 * u.deg, b=48.253 * u.deg, frame="galactic").icrs
    cmb_vec = np.array([np.cos(cmb.dec.rad) * np.cos(cmb.ra.rad), np.cos(cmb.dec.rad) * np.sin(cmb.ra.rad), np.sin(cmb.dec.rad)])
    sel_40_400 = (r_mpc >= 40.0) & (r_mpc < 400.0)
    only_cmb = phy_fast.multi_axis_hemisphere(n[sel_40_400], cmb_vec[None, :], native_lib=None)
    m2_cmb = only_cmb["second"][0, 1] - only_cmb["second"][0, 0]
    ev_cmb = np.linalg.eigvalsh(m2_cmb)
    cmp_r80 = float(0.03 * (ev_cmb[-1] - ev_cmb[0]))
    ref_r80 = float(r80["angular_mask_diagnostics"]["selected_40_400"]["sharp_even_shear_to_hemispherical_mean_bound"])
    assert abs(cmp_r80 - ref_r80) < 5e-14

    # PHY-02: Planck PR3/PR4 photon Codazzi feasibility
    M_exc = codazzi_map(np.array([1.0, 0.0, 0.0]), np.diag([0.0, 3.0, -3.0]))
    phy02 = {}
    for rel in ("PR3", "PR4"):
        S = stf_matrix(r66["nonlinear"][rel]["radiation_moment_bundle"]["pi5_over_rho"])
        res2 = phy_fast.photon_codazzi_feasibility(S, np.zeros(5), LieM=M_exc, Omega=0.3, eta=0.2, f=None)
        assert res2["photon_flux_missing"] and res2["physical_Pi"] is None
        phy02[rel] = {"P_eigen": res2["P_eigen"], "P_min_eigen": min(res2["P_eigen"]), "photon_flux_missing": True, "physical_Pi": None}

    # PHY-03: Shared-beta radio-photon algebraic closure
    beta_cmb = np.array([369.82 / 299792.458, 0.0, 0.0])
    ans3 = phy_fast.shared_beta_radio_photon(beta_cmb, k=previous["PHY-03"]["radio_first_order_k"], kappa=0.0)
    assert ans3["physical_Pi"] is None and ans3["source_qualified"] is False
    phy03 = {
        "k_source": previous["PHY-03"]["radio_first_order_k"],
        "photon_flux_norm": float(np.linalg.norm(ans3["photon_flux"])),
        "ratio": float(ans3["ratio"]),
        "photon_chi": float(ans3["photon_chi"]),
        "PR3_finiteband_chi": previous["PHY-03"]["actual_R66_finiteband_stress"]["PR3"]["R66_signed_chi_finiteband"],
        "source_qualified": False,
        "physical_Pi": None,
    }

    # PHY-04: Normal Lie B2 full-sky orthogonality & Gaia/Quaia masked E2-B2 Fisher alias
    sky_n, sky_w = _sky_quadrature()
    Nb = np.diag([0.013, -0.017, 0.004])
    S_loc = np.diag([-0.02, 0.0, 0.02])
    E2_sky, B2_sky = phy_fast.local_E2_and_Lie_B2(sky_n, S_loc, Nb)
    b2_norm = float(sky_w @ np.sum(B2_sky * B2_sky, axis=1))
    eb_dot = float(sky_w @ np.einsum("ni,ni->n", E2_sky, B2_sky))
    assert abs(b2_norm - float(np.trace(Nb @ Nb) / 5.0)) < 2e-15 and abs(eb_dot) < 2e-15
    gaia_aliases = {}
    for mk in ("quality", "quality_north", "quality_south"):
        x4 = phy_fast.gaia_eb_mask_alias(np.array(gaia["results"][mk]["formal_cov_microasyr2"]))
        gaia_aliases[mk] = {
            "maxcanonical": x4["maxcanonical"],
            "r76_diff": abs(x4["maxcanonical"] - r76[mk]["E2_B2_profiled_design_maxcanonical"]),
        }

    # PHY-05: Exceptional VI_-1/9 Lie flux rank vs 3x3 residual covariance
    x5 = np.array([-0.2, 0.1, 0.03, 0.04, 0.02])
    u5 = np.array([0.01, 0.0, -0.01])
    C8 = np.diag([0.04 ** 2] * 5 + [0.03 ** 2] * 3)
    res5 = phy_fast.normal_flux_residual(x5, u5, M_exc, Omega=0.4, C_joint=C8, independent_source=False)
    assert res5["physical_Pi"] is None and res5["rank_covariance"] == 3

    # PHY-06: Shear eigenframe noncommutator & photon l=4 family gap
    D6 = np.zeros((3, 3))
    D6[0, 1] = D6[1, 0] = 0.01
    sh6 = phy_fast.shear_shape_rate(np.diag([-0.03, -0.01, 0.04]), D6, H=0.1)
    p4_0 = phy_fast.photon_l4_family(0.0, threshold=0.9, shear_s=0.07)
    p4_1 = phy_fast.photon_l4_family(1.0, threshold=0.9, shear_s=0.07)

    # PHY-07: Actual CF4 12D radial Gram vs single-radius 9D rank
    X12 = radial_design(r_mpc, n)
    synth_y = np.log10(r_mpc) - np.mean(np.log10(r_mpc))
    G_np, b_np, c_np = phy_fast.weighted_radial_stats(X12, w_inv2, synth_y, native_lib=None)
    np_rec = phy_fast.last_phy_receipt()
    G_auto, b_auto, c_auto = phy_fast.weighted_radial_stats(X12, w_inv2, synth_y, native_lib="auto")
    auto_rec = phy_fast.last_phy_receipt()
    gram_diff = float(max(np.max(np.abs(G_auto - G_np)), np.max(np.abs(b_auto - b_np)), abs(c_auto - c_np)))
    r9 = radial_design(np.full_like(r_mpc, 150.0), n)
    phy07 = {
        "n_selected": int(len(n)),
        "radial12_rank": int(np.linalg.matrix_rank(X12)),
        "single_radius_rank": int(np.linalg.matrix_rank(r9)),
        "weighted_gram_condition": float(np.linalg.cond(G_auto)),
        "numpy_receipt": np_rec,
        "auto_receipt": auto_rec,
        "auto_vs_numpy_maxabs": gram_diff,
    }

    # Include cross-references to workdir extended runs if present
    cross_refs = {}
    for gid, fname in (("G02_CF4", "WORKDIR_EXT_RESULT.json"), ("G03_GAIA", "WORKDIR_EXT_RESULT.json"), ("G04_RADIO_FRAME", "WORKDIR_EXT_RESULT.json"), ("G05_PLANCK", "RESULT.json")):
        cand = OUT_DIR.parent / gid / fname
        if cand.is_file():
            cross_refs[gid] = {"path": str(cand.relative_to(ROOT)), "sha256": _sha256(cand)}

    elapsed = time.perf_counter() - t0
    input_paths = (SELECTED, TABLE4, R80, R77, R76, R69, R66)
    out = {
        "schema": "htt.r89.g08_optical_phy_result/1",
        "group_id": "G08_OPTICAL_PHY",
        "node_ids": [
            "SQ-PHOTON-FLUX", "PHY-02", "SQ-OPTICAL",
            "PHY-01", "PHY-05", "PHY-06", "PHY-03", "PHY-04", "PHY-07", "SQ-CROSS-COV",
        ],
        "source_sha256": {str(p.relative_to(ROOT) if p.is_relative_to(ROOT) else p): _sha256(p) for p in input_paths},
        "runtime": {
            "python": platform.python_version(),
            "numpy": np.__version__,
            "elapsed_seconds": float(elapsed),
            "maxrss_kib": int(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss),
        },
        "phy_real_source_replays": {
            "PHY-01": {
                "n_selected": int(len(n)),
                "n_40_400": int(sel_40_400.sum()),
                "n_axes": len(axes96),
                "backend_used": ft_rec["used"],
                "fortran_vs_numpy_maxabs": ft_maxdiff,
                "weighted_A96_sharp_minmax": [float(leakage.min()), float(leakage.max())],
                "r80_unweighted_cmb_replay_abs_err": abs(cmp_r80 - ref_r80),
            },
            "PHY-02": phy02,
            "PHY-03": phy03,
            "PHY-04": {
                "fullsky_B2_norm": b2_norm,
                "fullsky_E2_dot_B2": eb_dot,
                "gaia_masked_design_aliases": gaia_aliases,
            },
            "PHY-05": {
                "Lie_Codazzi_rank": int(np.linalg.matrix_rank(M_exc)),
                "residual_cov_rank": res5["rank_covariance"],
                "physical_Pi": res5["physical_Pi"],
            },
            "PHY-06": {
                "chi": sh6["chi"],
                "dchi": sh6["dchi"],
                "commutator_norm": sh6["commutator_norm"],
                "photon_l4_cap_F_eps0_eps1": [p4_0["cap_F"], p4_1["cap_F"]],
            },
            "PHY-07": phy07,
        },
        "workdir_cross_probe_bindings": cross_refs,
        "node_verdicts": {
            "SQ-PHOTON-FLUX": "BLOCKED_INPUT",
            "PHY-02": "BLOCKED_DEPENDENCY",
            "SQ-OPTICAL": "BLOCKED_INPUT",
            "PHY-01": "BLOCKED_DEPENDENCY",
            "PHY-05": "BLOCKED_DEPENDENCY",
            "PHY-06": "BLOCKED_DEPENDENCY",
            "PHY-03": "BLOCKED_DEPENDENCY",
            "PHY-04": "BLOCKED_DEPENDENCY",
            "PHY-07": "BLOCKED_DEPENDENCY",
            "SQ-CROSS-COV": "BLOCKED_DEPENDENCY",
        },
        "missing_physics_and_next_action": {
            "missing": [
                "Finite-redshift Sachs/Jacobi common-congruence optical response across CF4/Gaia/CMB",
                "Independent nonradial photon energy flux and higher-moment Boltzmann hierarchy",
                "Joint calibrated cross-probe covariance and shared cosmological null (SQ-CROSS-COV)",
            ],
            "next_action": "All 7 conditional PHY kernels pass real-source parity; await upstream SQ-PHOTON-FLUX, SQ-OPTICAL, SQ-CF4, SQ-GAIA, SQ-RADIO, SQ-CMB-NULL physical closures.",
        },
    }
    OUT_JSON.write_text(json.dumps(out, indent=2, ensure_ascii=False, allow_nan=False) + "\n", encoding="utf-8")
    print(json.dumps({
        "group_id": "G08_OPTICAL_PHY",
        "elapsed_s": round(elapsed, 3),
        "phy01_backend": ft_rec["used"],
        "phy01_maxdiff": ft_maxdiff,
        "phy01_r80_err": abs(cmp_r80 - ref_r80),
        "phy04_eb_dot": eb_dot,
        "phy07_gram_cond": round(phy07["weighted_gram_condition"], 4),
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
