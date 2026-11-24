#!/usr/bin/env python3
"""C1: Extend HYREC x_e to z_emit >= 1600 and validate visibility depth & tight-coupling start."""
from __future__ import annotations

import hashlib
import json
import math
import shutil
import subprocess
import time
from pathlib import Path

import numpy as np
from scipy.integrate import quad
from scipy.interpolate import CubicSpline

ROOT = Path(__file__).resolve().parents[2]
REC_REPO = Path("/home/cosmosapjw/Dropbox/bianchi/rec_bianchi")
BASS_REPO = Path("/home/cosmosapjw/worktrees/bass-r109-native-20261124")
BASS_BIN = BASS_REPO / "_rustcore/target/release/examples/homogeneous_sky"

REC_COMMIT = "4cffa8a0abdb104a40cac17cfc65593bec909fb3"
REC_FILE = "research/rec_r3o_grid_frontiers_20261019/reused_h_trace_001/producer_inputs/independent_integer_z_history.csv"
BASS_H2_COMMIT = "9f10e114"
BASS_H2_FILE = "research/typeii_hyrec2_history_20261102/HYREC2_FLRW_XE_TM_8000.dat"

RAW_ROOT = Path("/home/cosmosapjw/Downloads/htt_r111/c1_hyrec_1600")
OUT_JSON = (
    ROOT
    / "docs/research_program/observational_publication_20261015/"
    / "R111_LOCAL_HIGHL_NATIVE_20261124/C1_VISIBILITY_COVERAGE.json"
)

# HyRec / BASS r109 cosmology anchors (m_H hydrogen-mass convention)
NH0_HYREC = 11.223846333047 * 0.0224 * (1.0 - 0.2454)
NH0_AX08_MP = 0.189819845071
OMH2 = 0.14309694000000003
ODEH2 = 0.31113726660800006
WR = 4.48162687719e-7 * (2.7255**4) * (1.0 + 0.227107317660239 * 3.03821934419124)
C_SIGMA_T = 299792458.0 * 6.6524587051e-29
H0_UNIT = 3.2407792896393e-18


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    return sha256_bytes(path.read_bytes())


def hubble_s(z: float) -> float:
    zp1 = 1.0 + z
    return H0_UNIT * math.sqrt(OMH2 * (zp1**3) + ODEH2 + WR * (zp1**4))


def cosmology_anchors(z_emit: int) -> dict[str, float]:
    zp1 = 1.0 + z_emit
    om_m = OMH2 * (zp1**3)
    om_r = WR * (zp1**4)
    tot = om_m + om_r + ODEH2
    return {
        "z_emit": float(z_emit),
        "duration": math.log1p(z_emit),
        "n_h0_m3": NH0_HYREC,
        "n_h_emit_m3": NH0_HYREC * (zp1**3),
        "h_emit_s": hubble_s(float(z_emit)),
        "omega_lambda_emit": ODEH2 / tot,
        "dust_fraction": om_m / (om_m + om_r),
        "omega_matter_emit": om_m / tot,
        "omega_radiation_emit": om_r / tot,
    }


def load_rec_csv() -> tuple[dict[int, float], str]:
    raw = subprocess.check_output(["git", "-C", str(REC_REPO), "show", f"{REC_COMMIT}:{REC_FILE}"])
    sha = sha256_bytes(raw)
    rows: dict[int, float] = {}
    for line in raw.decode("utf-8").strip().splitlines()[1:]:
        z_s, xe_s, *_ = line.split(",")
        rows[int(z_s)] = float(xe_s)
    return rows, sha


def load_bass_hyrec2_dat() -> tuple[dict[int, float], str]:
    raw = subprocess.check_output(
        ["git", "-C", str(BASS_REPO), "show", f"{BASS_H2_COMMIT}:{BASS_H2_FILE}"]
    )
    sha = sha256_bytes(raw)
    rows: dict[int, float] = {}
    for line in raw.decode("utf-8").strip().splitlines():
        if line.startswith("#") or not line.strip():
            continue
        p = line.split()
        rows[int(p[0])] = float(p[1])
    return rows, sha


def write_hyrec_tsv(rows: dict[int, float], z_emit: int, out_path: Path) -> tuple[np.ndarray, np.ndarray]:
    zs = np.arange(z_emit, -1, -1, dtype=np.int64)
    etas = np.log((1.0 + z_emit) / (1.0 + zs.astype(np.float64)))
    etas[0] = 0.0
    xes = np.array([rows[int(z)] for z in zs], dtype=np.float64)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", encoding="utf-8") as f:
        f.write("eta\txe_per_H\n")
        for eta, xe in zip(etas, xes):
            f.write(f"{eta:.17e}\t{xe:.17e}\n")
    return etas, xes


def flrw_piecewise_eta_tau(
    etas: np.ndarray,
    xes: np.ndarray,
    z_emit: int,
    z_split: float = 1100.0,
) -> dict[str, float]:
    n_h_emit = NH0_HYREC * ((1.0 + z_emit) ** 3)
    eta_split = math.log((1.0 + z_emit) / (1.0 + z_split))
    gl_x, gl_w = np.polynomial.legendre.leggauss(16)

    def seg_int(a: float, b: float) -> float:
        mid, half = 0.5 * (a + b), 0.5 * (b - a)
        pts = mid + half * gl_x
        vals = np.empty_like(pts)
        for k, p in enumerate(pts):
            z = (1.0 + z_emit) * math.exp(-float(p)) - 1.0
            xe = float(np.interp(p, etas, xes))
            nh = n_h_emit * math.exp(-3.0 * float(p))
            vals[k] = C_SIGMA_T * nh * xe / hubble_s(z)
        return float(half * np.sum(gl_w * vals))

    tau_total = 0.0
    tau_above_split = 0.0
    for i in range(len(etas) - 1):
        a, b = float(etas[i]), float(etas[i + 1])
        s = seg_int(a, b)
        tau_total += s
        if b <= eta_split + 1e-13:
            tau_above_split += s
        elif a < eta_split < b:
            tau_above_split += seg_int(a, eta_split)
    return {
        "tau_emit_to_0": tau_total,
        "tau_emit_to_split": tau_above_split,
        "tau_split_to_0": tau_total - tau_above_split,
    }


def flrw_cubic_z_tau(rows: dict[int, float], z_emit: int, z_split: float = 1100.0) -> dict[str, float]:
    zs = np.arange(0, z_emit + 1, dtype=np.float64)
    ys = np.array([rows[int(z)] for z in zs], dtype=np.float64)
    cs = CubicSpline(zs, ys)

    def integrand(z: float) -> float:
        return C_SIGMA_T * NH0_HYREC * float(cs(z)) * ((1.0 + z) ** 2) / hubble_s(z)

    tau_above, err_above = quad(integrand, z_split, float(z_emit), limit=2000, epsabs=1e-12, epsrel=1e-12)
    tau_below, err_below = quad(integrand, 0.0, z_split, limit=2000, epsabs=1e-12, epsrel=1e-12)
    return {
        "tau_emit_to_0": tau_above + tau_below,
        "tau_emit_to_split": tau_above,
        "tau_split_to_0": tau_below,
        "quad_err_bound": max(err_above, err_below),
    }


def run_bass(out_dir: Path, args: list[str]) -> tuple[float, np.ndarray, dict[str, str]]:
    if out_dir.exists():
        shutil.rmtree(out_dir)
    cmd = [str(BASS_BIN), "--out", str(out_dir), *args]
    t0 = time.perf_counter()
    subprocess.run(cmd, check=True, capture_output=True, text=True)
    wall = time.perf_counter() - t0
    diag = np.loadtxt(out_dir / "diagnostics.tsv", skiprows=1)
    rtxt = dict(
        line.split("=", 1) for line in (out_dir / "run.txt").read_text().splitlines() if "=" in line
    )
    return wall, diag, rtxt


def main() -> None:
    RAW_ROOT.mkdir(parents=True, exist_ok=True)
    rows, rec_sha = load_rec_csv()
    h2_rows, h2_sha = load_bass_hyrec2_dat()

    h2_diffs = [abs(rows[z] - h2_rows[z]) for z in range(1, 1601)]
    cross_check = {
        "bass_commit": BASS_H2_COMMIT,
        "bass_file": BASS_H2_FILE,
        "bass_file_sha256": h2_sha,
        "z_range": [1, 1600],
        "max_abs_d_xe": max(h2_diffs),
        "xe_at_z1600_rec": rows[1600],
        "xe_at_z1600_bass_h2": h2_rows[1600],
        "xe_at_z1100_rec": rows[1100],
        "xe_at_z1100_bass_h2": h2_rows[1100],
        "xe_at_z1_rec": rows[1],
        "xe_at_z1_bass_h2": h2_rows[1],
    }

    tsv_1600 = RAW_ROOT / "hyrec_xe_1600.tsv"
    etas_1600, xes_1600 = write_hyrec_tsv(rows, 1600, tsv_1600)
    anc_1600 = cosmology_anchors(1600)

    pw_1600 = flrw_piecewise_eta_tau(etas_1600, xes_1600, 1600, 1100.0)
    cs_1600 = flrw_cubic_z_tau(rows, 1600, 1100.0)

    # 1. FLRW step-convergence sweep to z=0 (steps = 1024..32768)
    flrw_sweep = []
    exact_h_ratio_0 = hubble_s(0.0) / anc_1600["h_emit_s"]
    exact_omega_r_0 = WR / (OMH2 + ODEH2 + WR)
    exact_omega_m_0 = OMH2 / (OMH2 + ODEH2 + WR)
    for steps in (1024, 2048, 4096, 8192, 16384, 32768):
        rdir = RAW_ROOT / f"flrw_sdirk2_{steps}"
        wall, diag, _ = run_bass(
            rdir,
            [
                "--family", "I", "--shear", "0.0",
                "--duration", repr(anc_1600["duration"]),
                "--steps", str(steps),
                "--nmu", "6", "--nphi", "12", "--lmax", "2",
                "--feedback", "recoil", "--collision", "sdirk2",
                "--lie-update", "congruence",
                "--omega-lambda", repr(anc_1600["omega_lambda_emit"]),
                "--dust-fraction", repr(anc_1600["dust_fraction"]),
                "--ionization", str(tsv_1600),
                "--n-h-emit-m3", repr(anc_1600["n_h_emit_m3"]),
                "--h-emit-s", repr(anc_1600["h_emit_s"]),
            ],
        )
        fin = diag[-1]
        depth_0 = float(fin[16])
        abs_pw = abs(depth_0 - pw_1600["tau_emit_to_0"])
        abs_cs = abs(depth_0 - cs_1600["tau_emit_to_0"])
        flrw_sweep.append({
            "steps": steps,
            "wall_seconds": wall,
            "proper_depth_0": depth_0,
            "abs_err_vs_piecewise_eta": abs_pw,
            "rel_err_vs_piecewise_eta": abs_pw / pw_1600["tau_emit_to_0"],
            "abs_err_vs_cubic_z": abs_cs,
            "rel_err_vs_cubic_z": abs_cs / cs_1600["tau_emit_to_0"],
            "hubble_ratio_0": float(fin[1]),
            "hubble_ratio_rel_err": abs(float(fin[1]) - exact_h_ratio_0) / exact_h_ratio_0,
            "omega_radiation_0": float(fin[2]),
            "omega_dust_0": float(fin[3]),
            "max_abs_gauss": float(np.max(np.abs(diag[:, 4]))),
            "max_abs_collision_energy_defect": float(np.max(np.abs(diag[:, 17]))),
            "diagnostics_sha256": sha256_file(rdir / "diagnostics.tsv"),
        })

    # 2. Direct z=1600 -> 1100 depth verification run (duration = ln(1601/1101))
    dur_1100 = math.log(1601.0 / 1101.0)
    wall_1100, diag_1100, _ = run_bass(
        RAW_ROOT / "flrw_1600_to_1100",
        [
            "--family", "I", "--shear", "0.0",
            "--duration", repr(dur_1100),
            "--steps", "4096",
            "--nmu", "6", "--nphi", "12", "--lmax", "2",
            "--feedback", "recoil", "--collision", "sdirk2",
            "--lie-update", "congruence",
            "--omega-lambda", repr(anc_1600["omega_lambda_emit"]),
            "--dust-fraction", repr(anc_1600["dust_fraction"]),
            "--ionization", str(tsv_1600),
            "--n-h-emit-m3", repr(anc_1600["n_h_emit_m3"]),
            "--h-emit-s", repr(anc_1600["h_emit_s"]),
        ],
    )
    depth_1100 = float(diag_1100[-1, 16])

    # 3. Tight-coupling start & SDIRK2 long-run stability:
    # (a) Isotropic FLRW with nonzero opposed dust beta = 1e-3: initial normal radiation flux=0
    #     relaxes across tau(1600->1100)=31.42 toward baryon-frame equilibrium flux/E ~ (4/3)*beta_host.
    wall_tc, diag_tc, _ = run_bass(
        RAW_ROOT / "flrw_opposed_beta1e3_sdirk2",
        [
            "--family", "I", "--shear", "0.0",
            "--dust-beta", "1e-3,0,0",
            "--duration", repr(anc_1600["duration"]),
            "--steps", "4096",
            "--nmu", "8", "--nphi", "16", "--lmax", "4",
            "--feedback", "recoil", "--collision", "sdirk2",
            "--lie-update", "congruence",
            "--omega-lambda", repr(anc_1600["omega_lambda_emit"]),
            "--dust-fraction", repr(anc_1600["dust_fraction"]),
            "--ionization", str(tsv_1600),
            "--n-h-emit-m3", repr(anc_1600["n_h_emit_m3"]),
            "--h-emit-s", repr(anc_1600["h_emit_s"]),
        ],
    )
    # Sample rows at eta=0 (z=1600), z~1400, z~1100, z=0
    eta_z1400 = math.log(1601.0 / 1401.0)
    eta_z1100 = math.log(1601.0 / 1101.0)
    tc_samples = {}
    for label, target_eta in [("z1600_init", 0.0), ("z1400", eta_z1400), ("z1100", eta_z1100), ("z0_final", anc_1600["duration"])]:
        idx = int(np.argmin(np.abs(diag_tc[:, 0] - target_eta)))
        row = diag_tc[idx]
        z_eff = 1601.0 * math.exp(-float(row[0])) - 1.0
        flux_x = float(row[11])
        beta_x = float(row[18])
        eq_flux_x = (4.0 / 3.0) * beta_x
        tc_samples[label] = {
            "eta": float(row[0]),
            "z_approx": z_eff,
            "proper_depth": float(row[16]),
            "host_beta_x": beta_x,
            "flux_x_over_E": flux_x,
            "expected_baryon_iso_flux_x_over_E": eq_flux_x,
            "residual_from_baryon_isotropy": abs(flux_x - eq_flux_x),
            "min_screen_eigenvalue": float(row[14]),
        }

    # (b) Extended z_emit = 1650 check (tau(1650 -> 1600) and FLRW depth + tight-coupling)
    tsv_1650 = RAW_ROOT / "hyrec_xe_1650.tsv"
    etas_1650, xes_1650 = write_hyrec_tsv(rows, 1650, tsv_1650)
    anc_1650 = cosmology_anchors(1650)
    pw_1650 = flrw_piecewise_eta_tau(etas_1650, xes_1650, 1650, 1600.0)
    wall_1650_flrw, diag_1650_flrw, _ = run_bass(
        RAW_ROOT / "flrw_1650_sdirk2_32768",
        [
            "--family", "I", "--shear", "0.0",
            "--duration", repr(anc_1650["duration"]),
            "--steps", "32768",
            "--nmu", "6", "--nphi", "12", "--lmax", "2",
            "--feedback", "recoil", "--collision", "sdirk2",
            "--lie-update", "congruence",
            "--omega-lambda", repr(anc_1650["omega_lambda_emit"]),
            "--dust-fraction", repr(anc_1650["dust_fraction"]),
            "--ionization", str(tsv_1650),
            "--n-h-emit-m3", repr(anc_1650["n_h_emit_m3"]),
            "--h-emit-s", repr(anc_1650["h_emit_s"]),
        ],
    )
    wall_1650_tc, diag_1650_tc, _ = run_bass(
        RAW_ROOT / "flrw_1650_opposed_beta1e3_sdirk2",
        [
            "--family", "I", "--shear", "0.0",
            "--dust-beta", "1e-3,0,0",
            "--duration", repr(anc_1650["duration"]),
            "--steps", "4096",
            "--nmu", "8", "--nphi", "16", "--lmax", "4",
            "--feedback", "recoil", "--collision", "sdirk2",
            "--lie-update", "congruence",
            "--omega-lambda", repr(anc_1650["omega_lambda_emit"]),
            "--dust-fraction", repr(anc_1650["dust_fraction"]),
            "--ionization", str(tsv_1650),
            "--n-h-emit-m3", repr(anc_1650["n_h_emit_m3"]),
            "--h-emit-s", repr(anc_1650["h_emit_s"]),
        ],
    )
    eta_1650_to_1600 = math.log(1651.0 / 1601.0)
    idx_1600_in_1650 = int(np.argmin(np.abs(diag_1650_tc[:, 0] - eta_1650_to_1600)))
    r_1600 = diag_1650_tc[idx_1600_in_1650]
    tc_z1650_at_1600 = {
        "eta": float(r_1600[0]),
        "proper_depth_1650_to_1600": float(r_1600[16]),
        "host_beta_x": float(r_1600[18]),
        "flux_x_over_E": float(r_1600[11]),
        "expected_baryon_iso_flux_x_over_E": (4.0 / 3.0) * float(r_1600[18]),
        "residual_from_baryon_isotropy": abs(float(r_1600[11]) - (4.0 / 3.0) * float(r_1600[18])),
        "exp_minus_tau_1650_to_1600": math.exp(-pw_1650["tau_emit_to_split"]),
    }

    # (c) Long-run Codazzi coflow VIIh stability: backward-euler vs sdirk2 at steps=2000 & 4000
    lie_viih = RAW_ROOT / "viih_stability.lie"
    lie_viih.write_text("shear 0.0003 0.0002 -0.0005 0.00015 0.0001 0.00012\nn 0 0.01 0.01 0 0 0\na 0.005 0 0\n")
    scheme_runs = {}
    for scheme in ("backward-euler", "sdirk2"):
        for steps in (2000, 4000):
            rdir = RAW_ROOT / f"viih_{scheme}_{steps}"
            wall, diag, rtxt = run_bass(
                rdir,
                [
                    "--lie-ic", str(lie_viih),
                    "--feedback", "recoil",
                    "--dust-fraction", repr(anc_1600["dust_fraction"]),
                    "--omega-lambda", repr(anc_1600["omega_lambda_emit"]),
                    "--ionization", str(tsv_1600),
                    "--n-h-emit-m3", repr(anc_1600["n_h_emit_m3"]),
                    "--h-emit-s", repr(anc_1600["h_emit_s"]),
                    "--duration", repr(anc_1600["duration"]),
                    "--steps", str(steps),
                    "--nmu", "10", "--nphi", "24", "--lmax", "4",
                    "--los-lmax", "32",
                    "--collision", scheme,
                    "--lie-update", "congruence",
                ],
            )
            modes = np.loadtxt(rdir / "los_modes.tsv", skiprows=1)
            scheme_runs[f"{scheme}_{steps}"] = {
                "wall_seconds": wall,
                "proper_depth_0": float(diag[-1, 16]),
                "max_abs_gauss": float(np.max(np.abs(diag[:, 4]))),
                "max_abs_codazzi": float(np.max(np.abs(diag[:, 5:8]))),
                "max_abs_jacobi": float(np.max(np.abs(diag[:, 8]))),
                "min_screen_eigenvalue": float(np.min(diag[:, 14])),
                "max_abs_collision_energy_defect": float(np.max(np.abs(diag[:, 17]))),
                "los_min_intensity": float(rtxt["los_min_intensity"]),
                "los_min_screen_eigenvalue": float(rtxt["los_min_screen_eigenvalue"]),
                "los_max_landing_error": float(rtxt["los_max_landing_error"]),
                "los_modes_sha256": sha256_file(rdir / "los_modes.tsv"),
                "_modes": modes,
            }

    def rel_l2(k1: str, k2: str) -> dict[str, float]:
        m1 = scheme_runs[k1]["_modes"]
        m2 = scheme_runs[k2]["_modes"]
        out = {}
        for i, ch in enumerate("TEB"):
            u = m1[:, 2 + 2 * i] + 1j * m1[:, 3 + 2 * i]
            v = m2[:, 2 + 2 * i] + 1j * m2[:, 3 + 2 * i]
            out[ch] = float(np.linalg.norm(u - v) / np.linalg.norm(v))
        return out

    stability_diffs = {
        "backward_euler_2000_to_4000": rel_l2("backward-euler_2000", "backward-euler_4000"),
        "sdirk2_2000_to_4000": rel_l2("sdirk2_2000", "sdirk2_4000"),
        "be4000_vs_sdirk2_4000": rel_l2("backward-euler_4000", "sdirk2_4000"),
    }
    for v in scheme_runs.values():
        v.pop("_modes", None)

    best_step = flrw_sweep[-1]
    assert best_step["abs_err_vs_piecewise_eta"] <= 1e-6
    assert best_step["rel_err_vs_cubic_z"] <= 1e-6
    assert abs(depth_1100 - pw_1600["tau_emit_to_split"]) <= 1e-6

    out = {
        "schema": "htt.r111.c1_visibility_coverage/1",
        "claim_ceiling": "deterministic background/visibility quadrature check; no ensemble statistics or family claim",
        "binary_sha256": sha256_file(BASS_BIN),
        "rec_source": {
            "repo": str(REC_REPO),
            "commit": REC_COMMIT,
            "file": REC_FILE,
            "sha256": rec_sha,
        },
        "hyrec_1600_table": {
            "path": str(tsv_1600),
            "sha256": sha256_file(tsv_1600),
            "n_rows": len(etas_1600),
            "z_emit": 1600,
            "eta_min": float(etas_1600[0]),
            "eta_max": float(etas_1600[-1]),
            "xe_at_1600": float(xes_1600[0]),
            "xe_at_0": float(xes_1600[-1]),
        },
        "cross_check_vs_bass_hyrec2_8000": cross_check,
        "cosmology_anchors": anc_1600,
        "nh0_mass_convention_note": {
            "hyrec_mH_m3": NH0_HYREC,
            "ax08_mp_m3": NH0_AX08_MP,
            "relative_difference_mp_over_mH_minus_1": (NH0_AX08_MP / NH0_HYREC) - 1.0,
        },
        "independent_flrw_quadrature": {
            "piecewise_eta_16pt_gl": pw_1600,
            "cubic_z_spline_quad": cs_1600,
            "exact_endpoints": {
                "hubble_ratio_0": exact_h_ratio_0,
                "omega_radiation_0": exact_omega_r_0,
                "omega_dust_0": exact_omega_m_0,
            },
        },
        "bass_flrw_step_convergence": flrw_sweep,
        "bass_1600_to_1100_check": {
            "steps": 4096,
            "wall_seconds": wall_1100,
            "duration": dur_1100,
            "proper_depth": depth_1100,
            "abs_err_vs_piecewise_eta": abs(depth_1100 - pw_1600["tau_emit_to_split"]),
            "rel_err_vs_piecewise_eta": abs(depth_1100 - pw_1600["tau_emit_to_split"]) / pw_1600["tau_emit_to_split"],
        },
        "tight_coupling_start_baryon_relaxation": {
            "wall_seconds": wall_tc,
            "steps": 4096,
            "initial_dust_beta": [1e-3, 0.0, 0.0],
            "samples": tc_samples,
            "exp_minus_tau_1600_to_1100": math.exp(-pw_1600["tau_emit_to_split"]),
        },
        "extended_z1650_control": {
            "hyrec_1650_sha256": sha256_file(tsv_1650),
            "cosmology_anchors": anc_1650,
            "quadrature_piecewise_eta": pw_1650,
            "bass_flrw_32768_seconds": wall_1650_flrw,
            "bass_flrw_32768_depth": float(diag_1650_flrw[-1, 16]),
            "bass_flrw_32768_abs_err": abs(float(diag_1650_flrw[-1, 16]) - pw_1650["tau_emit_to_0"]),
            "tc_z1650_opposed_seconds": wall_1650_tc,
            "tc_at_z1600_snapshot": tc_z1650_at_1600,
        },
        "long_run_sdirk2_stability_viih": {
            "runs": scheme_runs,
            "relative_mode_differences": stability_diffs,
        },
        "acceptance": {
            "flrw_depth_to_z0_abs_err_32768": best_step["abs_err_vs_piecewise_eta"],
            "flrw_depth_to_z0_rel_err_32768": best_step["rel_err_vs_piecewise_eta"],
            "flrw_depth_1e6_passed": bool(best_step["abs_err_vs_piecewise_eta"] <= 1e-6),
            "long_run_sdirk2_stable_positive_screen": bool(
                all(v["min_screen_eigenvalue"] > 0.0 and v["los_min_intensity"] > 0.0 for v in scheme_runs.values())
            ),
        },
    }
    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUT_JSON.write_text(json.dumps(out, indent=2) + "\n", encoding="utf-8")
    print(f"Wrote {OUT_JSON}")
    print(json.dumps(out["acceptance"], indent=2))


if __name__ == "__main__":
    main()
