#!/usr/bin/env python3
"""C1: Harmonic long-epoch (z_emit=1600) 13-case universal Lie-sky atlas (FLRW + 12 Bianchi families)."""
from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import tarfile
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import numpy as np

from scripts.r111.c1_visibility_hyrec import cosmology_anchors, load_rec_csv, sha256_file, write_hyrec_tsv
from scripts.r111.c3_long_highl_atlas import COMMON_SHEAR, FAMILIES_LIE

ROOT = Path(__file__).resolve().parents[2]
BASS_BIN = Path("/home/cosmosapjw/Downloads/htt_r114/bin/homogeneous_sky_r114")
RAW_ROOT = Path("/home/cosmosapjw/Downloads/htt_r114/c1_atlas")
TARBALL_PATH = RAW_ROOT / "C1_HARMONIC_L32_MODES.tar.gz"
OUT_JSON = (
    ROOT
    / "docs/research_program/observational_publication_20261015/"
    / "R114_LOCAL_UNIVERSAL_LIE_SKY_20261125/C1_HARMONIC_LONG_ATLAS.json"
)
F_NU = (0.227107317660239 * 3.03821934419124) / (1.0 + 0.227107317660239 * 3.03821934419124)

CASES_ORDER = ["FLRW", *FAMILIES_LIE.keys()]
ZERO_TILT_CASES = {"FLRW", "I", "IX"}
COFLOW_FAMILIES = [f for f in FAMILIES_LIE if f not in ZERO_TILT_CASES]

RUN_SPECS: dict[str, list[str]] = {
    "r_s1000": ["--route", "rays", "--steps", "1000", "--nmu", "28", "--nphi", "64"],
    "r_s2000": ["--route", "rays", "--steps", "2000", "--nmu", "28", "--nphi", "64"],
    "h16_s500": ["--route", "harmonic", "--harmonic-lmax", "16", "--steps", "500", "--nmu", "8", "--nphi", "16"],
    "h16_s1000": ["--route", "harmonic", "--harmonic-lmax", "16", "--steps", "1000", "--nmu", "8", "--nphi", "16"],
    "h16_s2000": ["--route", "harmonic", "--harmonic-lmax", "16", "--steps", "2000", "--nmu", "8", "--nphi", "16"],
    "h24_s2000": ["--route", "harmonic", "--harmonic-lmax", "24", "--steps", "2000", "--nmu", "8", "--nphi", "16"],
    "h32_s2000": ["--route", "harmonic", "--harmonic-lmax", "32", "--steps", "2000", "--nmu", "8", "--nphi", "16"],
}


def parse_some_float(text: str | None) -> float | None:
    if text is None or not text.startswith("Some("):
        return None
    return float(text[5:-1])


def parse_vec_some(text: str | None) -> list[float] | None:
    if text is None or text == "None":
        return None
    inner = text[5:-1] if text.startswith("Some(") else text
    return json.loads(inner)


def read_modes_dict(path: Path) -> dict[tuple[int, int], list[float]]:
    out: dict[tuple[int, int], list[float]] = {}
    with path.open("r", encoding="utf-8") as f:
        f.readline()
        for line in f:
            parts = line.split()
            if parts:
                out[(int(parts[0]), int(parts[1]))] = [float(x) for x in parts[2:8]]
    return out


def max_mode_rel(
    a: dict[tuple[int, int], list[float]],
    b: dict[tuple[int, int], list[float]],
    lmin: int,
    lmax: int,
    ref_scale: dict[tuple[int, int], list[float]] | None = None,
) -> tuple[float, float]:
    keys = [k for k in a if lmin <= k[0] <= lmax and k in b]
    src = ref_scale if ref_scale is not None else a
    scale = max(abs(x) for k in keys for x in src[k])
    diff = max(abs(x - y) for k in keys for x, y in zip(a[k], b[k]))
    if scale == 0.0:
        return diff, 0.0
    return diff, diff / scale


def parse_cli_val(extra: list[str], flag: str, default: int) -> int:
    if flag in extra:
        return int(extra[extra.index(flag) + 1])
    return default


def inspect_run(case: str, tag: str, extra: list[str], out_dir: Path, wall: float = 0.0) -> dict:
    with (out_dir / "diagnostics.tsv").open("r", encoding="utf-8") as f:
        dhead = f.readline().split()
        diag = np.loadtxt(f)
    dcol = {k: i for i, k in enumerate(dhead)}
    rtxt = dict(line.split("=", 1) for line in (out_dir / "run.txt").read_text(encoding="utf-8").splitlines() if "=" in line)
    cl = np.loadtxt(out_dir / "los_cl.tsv", skiprows=1)

    codazzi_norm = np.sqrt(
        diag[:, dcol["codazzi_x"]] ** 2 + diag[:, dcol["codazzi_y"]] ** 2 + diag[:, dcol["codazzi_z"]] ** 2
    )
    max_gauss = float(np.max(np.abs(diag[:, dcol["gauss"]])))
    fin_gauss = float(diag[-1, dcol["gauss"]])
    max_codazzi = float(np.max(codazzi_norm))
    fin_codazzi = float(codazzi_norm[-1])
    max_jacobi = float(np.max(np.abs(diag[:, dcol["jacobi_norm"]])))
    max_edef = float(np.max(np.abs(diag[:, dcol["collision_energy_defect"]])))
    min_scr = float(np.min(diag[:, dcol["min_screen_eigenvalue"]]))

    def rel_drift(k0: str, k1: str) -> tuple[str | None, str | None, float | None]:
        s0, s1 = rtxt.get(k0), rtxt.get(k1)
        v0, v1 = parse_some_float(s0), parse_some_float(s1)
        if v0 is None or v1 is None:
            return s0, s1, None
        return s0, s1, (0.0 if v0 == 0.0 else abs(v1 - v0) / abs(v0))

    h_i, h_f, h_drift = rel_drift("lie_h_initial", "lie_h_final")
    kh_i, kh_f, kh_drift = rel_drift("lie_kappa_inverse_h_initial", "lie_kappa_inverse_h_final")

    los_modes = np.loadtxt(out_dir / "los_modes.tsv", skiprows=1)
    max_alm_l_ge_1 = float(np.max(np.abs(los_modes[los_modes[:, 0] >= 1, 2:8])))

    return {
        "case": case,
        "tag": tag,
        "route": rtxt["route"],
        "steps": int(rtxt["steps"]),
        "harmonic_lmax": parse_cli_val(extra, "--harmonic-lmax", 0) if "--harmonic-lmax" in extra else None,
        "nmu": int(rtxt["nmu"]),
        "nphi": int(rtxt["nphi"]),
        "wall_seconds": wall,
        "los_seconds": float(rtxt["los_seconds"]),
        "los_threads": int(rtxt["los_threads"]),
        "los_max_landing_error": float(rtxt["los_max_landing_error"]),
        "los_min_intensity": float(rtxt["los_min_intensity"]),
        "los_min_screen_eigenvalue": float(rtxt["los_min_screen_eigenvalue"]),
        "min_forward_screen_eigenvalue": min_scr,
        "max_abs_gauss_residual": max_gauss,
        "final_gauss_residual": fin_gauss,
        "max_codazzi_residual_norm": max_codazzi,
        "final_codazzi_residual_norm": fin_codazzi,
        "max_abs_jacobi_residual": max_jacobi,
        "max_abs_collision_energy_defect": max_edef,
        "lie_type_initial": rtxt["lie_type_initial"],
        "lie_type_final": rtxt["lie_type_final"],
        "lie_type_unchanged": rtxt["lie_type_initial"] == rtxt["lie_type_final"],
        "lie_h_initial": h_i,
        "lie_h_final": h_f,
        "lie_h_rel_drift": h_drift,
        "lie_kappa_inverse_h_initial": kh_i,
        "lie_kappa_inverse_h_final": kh_f,
        "lie_kappa_inverse_h_rel_drift": kh_drift,
        "initial_dust_mode": rtxt["initial_dust_mode"],
        "frames": {
            "photon_energy_beta": parse_vec_some(rtxt.get("frame_photon_energy_beta")),
            "radiation_energy_beta": parse_vec_some(rtxt.get("frame_radiation_energy_beta")),
            "host_beta": parse_vec_some(rtxt.get("frame_host_beta")),
            "spectator_beta": parse_vec_some(rtxt.get("frame_spectator_beta")),
            "local_boost_observer_vs_radiation": parse_vec_some(rtxt.get("local_boost_observer_vs_radiation")),
            "global_tilt_host_vs_normal": parse_vec_some(rtxt.get("global_tilt_host_vs_normal")),
            "global_tilt_host_vs_radiation": parse_vec_some(rtxt.get("global_tilt_host_vs_radiation")),
        },
        "final_hubble_ratio": float(diag[-1, dcol["hubble_ratio"]]),
        "final_proper_depth": float(diag[-1, dcol["proper_depth"]]),
        "max_abs_los_alm_l_ge_1": max_alm_l_ge_1,
        "modes_sha256": sha256_file(out_dir / "modes.tsv"),
        "los_modes_sha256": sha256_file(out_dir / "los_modes.tsv"),
        "diagnostics_sha256": sha256_file(out_dir / "diagnostics.tsv"),
        "los_cl_summary_selected_ells": {
            str(int(row[0])): {
                "TT": float(row[1]),
                "TE": float(row[2]),
                "TB": float(row[3]),
                "EE": float(row[4]),
                "EB": float(row[5]),
                "BB": float(row[6]),
            }
            for row in cl[[1, 2, 3, 4, 8, 16, 32, 64, 128]]
        },
    }


def run_job(task: tuple[str, str, list[str], Path | None, Path, dict[str, float], int]) -> tuple[str, str, dict]:
    case, tag, extra, lie_path, tsv_path, anc, rayon_threads = task
    out_dir = RAW_ROOT / "runs" / case / tag
    if out_dir.exists():
        shutil.rmtree(out_dir)
    cmd = [
        str(BASS_BIN),
        "--out", str(out_dir),
        "--duration", repr(anc["duration"]),
        "--feedback", "recoil",
        "--collision", "sdirk2",
        "--lie-update", "congruence",
        "--omega-lambda", repr(anc["omega_lambda_emit"]),
        "--dust-fraction", repr(anc["dust_fraction"]),
        "--baryon-fraction", "0.157",
        "--neutrino-fraction", repr(F_NU),
        "--ionization", str(tsv_path),
        "--n-h-emit-m3", repr(anc["n_h_emit_m3"]),
        "--h-emit-s", repr(anc["h_emit_s"]),
        "--observer-frame", "host",
        "--lmax", "4",
        "--los-lmax", "128",
        "--los-ntheta", "160",
        "--los-nphi", "320",
    ]
    if case == "FLRW":
        cmd += ["--family", "FLRW", "--shear", "0"]
    else:
        assert lie_path is not None
        cmd += ["--lie-ic", str(lie_path)]
    cmd += extra

    env = dict(os.environ)
    env["RAYON_NUM_THREADS"] = str(rayon_threads)
    t0 = time.perf_counter()
    subprocess.run(cmd, check=True, capture_output=True, text=True, env=env)
    wall = time.perf_counter() - t0
    rec = inspect_run(case, tag, extra, out_dir, wall=wall)
    print(
        f"Done {case:6s} {tag:10s}: {wall:6.2f}s los={rec['los_seconds']:5.2f}s "
        f"G={rec['max_abs_gauss_residual']:.2e} C={rec['max_codazzi_residual_norm']:.2e} type={rec['lie_type_final']}",
        flush=True,
    )
    return case, tag, rec


def harmonic_pair_convergence(coarse_dir: Path, fine_dir: Path) -> dict:
    """Compare C_l (TT, TE, EE, BB) AND complex los_modes (T, E, B) where C_l > 1e-12 * max C_l."""
    mc = np.loadtxt(coarse_dir / "los_modes.tsv", skiprows=1)
    mf = np.loadtxt(fine_dir / "los_modes.tsv", skiprows=1)
    cf = np.loadtxt(fine_dir / "los_cl.tsv", skiprows=1)
    ca = np.loadtxt(coarse_dir / "los_cl.tsv", skiprows=1)
    ells_m = mc[:, 0].astype(int)

    sky_max_l2 = float(np.max(cf[2:, [1, 4, 6]]))
    sky_max_l1 = float(np.max(cf[1:, [1, 4, 6]]))
    thresh_l2 = max(1e-12 * sky_max_l2, 1e-25)
    thresh_l1 = max(1e-12 * sky_max_l1, 1e-25)

    cl_changes = {}
    for col_idx, name in ((1, "TT"), (2, "TE"), (4, "EE"), (6, "BB")):
        l_start = 1 if name == "TT" else 2
        active_l2 = [int(cf[l, 0]) for l in range(l_start, len(cf)) if abs(cf[l, col_idx]) > thresh_l2]
        active_l1 = [int(cf[l, 0]) for l in range(l_start, len(cf)) if abs(cf[l, col_idx]) > thresh_l1]
        if sky_max_l2 <= 1e-25 or not active_l2:
            cl_changes[name] = {
                "parity_null_zero_channel": True,
                "active_ells_l2_thresh": [],
                "max_rel_change_cl": 0.0,
                "max_rel_change_cl_l1_thresh": 0.0,
                "passed_1e6": True,
                "passed_1e6_or_sub_ulp_floor": True,
            }
            continue
        rels_l2 = [abs(cf[l, col_idx] - ca[l, col_idx]) / abs(cf[l, col_idx]) for l in active_l2]
        rels_l1 = [abs(cf[l, col_idx] - ca[l, col_idx]) / abs(cf[l, col_idx]) for l in active_l1] if active_l1 else [0.0]
        worst_idx = int(np.argmax(rels_l2))
        worst_l = active_l2[worst_idx]
        max_delta_over_sky = max(abs(cf[l, col_idx] - ca[l, col_idx]) / sky_max_l2 for l in active_l2)
        strict_ok = bool(max(rels_l2) <= 1e-6)
        above_ulp_ok = all(
            (abs(cf[l, col_idx] - ca[l, col_idx]) / abs(cf[l, col_idx]) <= 1e-6)
            or (abs(cf[l, col_idx] - ca[l, col_idx]) <= 1e-15 * sky_max_l2)
            for l in active_l2
        )
        cl_changes[name] = {
            "parity_null_zero_channel": False,
            "active_ell_count": len(active_l2),
            "active_ells_range": [active_l2[0], active_l2[-1]],
            "max_rel_change_cl": float(max(rels_l2)),
            "worst_ell": int(worst_l),
            "worst_delta_cl_over_sky_max_cl": float(abs(cf[worst_l, col_idx] - ca[worst_l, col_idx]) / sky_max_l2),
            "max_delta_cl_over_sky_max_cl": float(max_delta_over_sky),
            "max_rel_change_cl_l1_thresh": float(max(rels_l1)),
            "passed_1e6": strict_ok,
            "passed_1e6_or_sub_ulp_floor": bool(above_ulp_ok),
        }

    mode_changes = {}
    for ch_idx, (ch, cl_col) in enumerate([("T", 1), ("E", 4), ("B", 6)]):
        l_start = 1 if ch == "T" else 2
        active = [int(cf[l, 0]) for l in range(l_start, len(cf)) if cf[l, cl_col] > thresh_l2]
        if sky_max_l2 <= 1e-25 or not active:
            mode_changes[ch] = {
                "parity_null_zero_channel": True,
                "active_ell_count": 0,
                "global_rel_change": 0.0,
                "max_per_ell_rel_change": 0.0,
                "passed_global_1e6": True,
            }
            continue
        mask = np.isin(ells_m, active)
        u = mc[mask, 2 + 2 * ch_idx] + 1j * mc[mask, 3 + 2 * ch_idx]
        v = mf[mask, 2 + 2 * ch_idx] + 1j * mf[mask, 3 + 2 * ch_idx]
        glob = float(np.linalg.norm(u - v) / np.linalg.norm(v))
        worst_l = active[0]
        worst_val = 0.0
        for l in active:
            ml = ells_m == l
            ul = mc[ml, 2 + 2 * ch_idx] + 1j * mc[ml, 3 + 2 * ch_idx]
            vl = mf[ml, 2 + 2 * ch_idx] + 1j * mf[ml, 3 + 2 * ch_idx]
            nv = float(np.linalg.norm(vl))
            if nv > 0.0:
                val = float(np.linalg.norm(ul - vl) / nv)
                if val >= worst_val:
                    worst_val = val
                    worst_l = l
        mode_changes[ch] = {
            "parity_null_zero_channel": False,
            "active_ell_count": len(active),
            "active_ells_range": [active[0], active[-1]],
            "global_rel_change": glob,
            "max_per_ell_rel_change": worst_val,
            "worst_ell": int(worst_l),
            "passed_global_1e6": bool(glob <= 1e-6),
        }

    return {
        "sky_max_cl_l_ge_2": sky_max_l2,
        "sky_max_cl_l_ge_1": sky_max_l1,
        "cl_rel_changes": cl_changes,
        "mode_rel_changes": mode_changes,
        "passed_cl_1e6": bool(all(v["passed_1e6"] for v in cl_changes.values())),
        "passed_cl_1e6_or_sub_ulp_floor": bool(all(v["passed_1e6_or_sub_ulp_floor"] for v in cl_changes.values())),
        "passed_global_mode_1e6": bool(all(v["passed_global_1e6"] for v in mode_changes.values())),
    }


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--summarize-only", action="store_true")
    cli = ap.parse_args()

    RAW_ROOT.mkdir(parents=True, exist_ok=True)
    rows, rec_sha = load_rec_csv()
    tsv_path = RAW_ROOT / "hyrec_xe_1600.tsv"
    write_hyrec_tsv(rows, 1600, tsv_path)
    anc = cosmology_anchors(1600)

    (RAW_ROOT / "lie_ics").mkdir(parents=True, exist_ok=True)
    (RAW_ROOT / "runs").mkdir(parents=True, exist_ok=True)
    lie_paths: dict[str, Path | None] = {"FLRW": None}
    for fam, (n6, a3, _, _) in FAMILIES_LIE.items():
        lp = RAW_ROOT / "lie_ics" / f"{fam}.lie"
        lp.write_text(f"shear {COMMON_SHEAR}\nn {n6}\na {a3}\n", encoding="utf-8")
        lie_paths[fam] = lp

    tasks = []
    for case in CASES_ORDER:
        for tag, extra in RUN_SPECS.items():
            tasks.append((case, tag, extra, lie_paths[case], tsv_path, anc, 4))

    t_all = time.perf_counter()
    results: dict[str, dict[str, dict]] = {case: {} for case in CASES_ORDER}
    if cli.summarize_only:
        prev = json.loads(OUT_JSON.read_text(encoding="utf-8")) if OUT_JSON.exists() else {}
        prev_cases = prev.get("cases", {})
        for case, tag, extra, *_ in tasks:
            old_wall = float(prev_cases.get(case, {}).get("runs", {}).get(tag, {}).get("wall_seconds", 0.0))
            results[case][tag] = inspect_run(case, tag, extra, RAW_ROOT / "runs" / case / tag, wall=old_wall)
        total_wall = float(prev.get("total_wall_seconds", 0.0))
    else:
        tag_priority = {"h32_s2000": 0, "h24_s2000": 1, "r_s2000": 2, "h16_s2000": 3, "h16_s1000": 4, "r_s1000": 5, "h16_s500": 6}
        ordered_tasks = sorted(tasks, key=lambda t: (tag_priority[t[1]], t[0]))
        with ThreadPoolExecutor(max_workers=6) as ex:
            for case, tag, rec in ex.map(run_job, ordered_tasks):
                results[case][tag] = rec
        total_wall = time.perf_counter() - t_all

    case_summaries = {}
    aniso_cl_lpair_pass = True
    aniso_cl_above_ulp_pass = True
    passed_cl_count = 0
    failed_cl_details = []
    aniso_glob_mode_pass = True
    coflow_rg_pass = True
    non_ix_aniso_both_routes_rg_pass = True
    flrw_abs_rg_pass = True
    zero_tilt_s2k_max_rel = 0.0
    h16_step_order2_pass = True
    all_types_pass = True
    all_h_pass = True
    all_screens_pos = True

    for case in CASES_ORDER:
        rdir = RAW_ROOT / "runs" / case
        runs_c = results[case]
        exp_type = "I" if case == "FLRW" else FAMILIES_LIE[case][2]

        m_r1k_d = read_modes_dict(rdir / "r_s1000/modes.tsv")
        m_h5c_d = read_modes_dict(rdir / "h16_s500/modes.tsv")
        m_h1k_d = read_modes_dict(rdir / "h16_s1000/modes.tsv")
        m_r2k_d = read_modes_dict(rdir / "r_s2000/modes.tsv")
        m_h2k_d = read_modes_dict(rdir / "h16_s2000/modes.tsv")

        m_r1k_l = read_modes_dict(rdir / "r_s1000/los_modes.tsv")
        m_h5c_l = read_modes_dict(rdir / "h16_s500/los_modes.tsv")
        m_h1k_l = read_modes_dict(rdir / "h16_s1000/los_modes.tsv")
        m_r2k_l = read_modes_dict(rdir / "r_s2000/los_modes.tsv")
        m_h2k_l = read_modes_dict(rdir / "h16_s2000/los_modes.tsv")

        abs_d1, rel_d1 = max_mode_rel(m_r1k_d, m_h1k_d, 1, 4)
        abs_d2, rel_d2 = max_mode_rel(m_r2k_d, m_h2k_d, 1, 4)
        abs_l1, rel_l1 = max_mode_rel(m_r1k_l, m_h1k_l, 1, 128)
        abs_l2, rel_l2 = max_mode_rel(m_r2k_l, m_h2k_l, 1, 128)

        _, h_step_d_500_1k = max_mode_rel(m_h5c_d, m_h1k_d, 1, 4, ref_scale=m_h2k_d)
        _, h_step_d_1k_2k = max_mode_rel(m_h1k_d, m_h2k_d, 1, 4, ref_scale=m_h2k_d)
        _, h_step_l_500_1k = max_mode_rel(m_h5c_l, m_h1k_l, 1, 128, ref_scale=m_h2k_l)
        _, h_step_l_1k_2k = max_mode_rel(m_h1k_l, m_h2k_l, 1, 128, ref_scale=m_h2k_l)

        ratio_d = (rel_d1 / rel_d2) if rel_d2 > 0.0 else None
        ratio_l = (rel_l1 / rel_l2) if rel_l2 > 0.0 else None
        h_ratio_d = (h_step_d_500_1k / h_step_d_1k_2k) if h_step_d_1k_2k > 0.0 else None
        h_ratio_l = (h_step_l_500_1k / h_step_l_1k_2k) if h_step_l_1k_2k > 0.0 else None

        lpair_16_24 = harmonic_pair_convergence(rdir / "h16_s2000", rdir / "h24_s2000")
        lpair_24_32 = harmonic_pair_convergence(rdir / "h24_s2000", rdir / "h32_s2000")

        type_ok = all(r["lie_type_unchanged"] and r["lie_type_final"] == exp_type for r in runs_c.values())
        h_ok = all(
            (r["lie_h_rel_drift"] is None or r["lie_h_rel_drift"] <= 1e-12)
            and (r["lie_kappa_inverse_h_rel_drift"] is None or r["lie_kappa_inverse_h_rel_drift"] <= 1e-12)
            for r in runs_c.values()
        )
        scr_ok = all(r["min_forward_screen_eigenvalue"] > 0.0 and r["los_min_intensity"] > 0.0 for r in runs_c.values())

        all_types_pass &= type_ok
        all_h_pass &= h_ok
        all_screens_pos &= scr_ok
        if case != "FLRW":
            strict_ok = lpair_16_24["passed_cl_1e6"] and lpair_24_32["passed_cl_1e6"]
            ulp_ok = lpair_16_24["passed_cl_1e6_or_sub_ulp_floor"] and lpair_24_32["passed_cl_1e6_or_sub_ulp_floor"]
            aniso_cl_lpair_pass &= strict_ok
            aniso_cl_above_ulp_pass &= ulp_ok
            if strict_ok:
                passed_cl_count += 1
            else:
                for p_name, p_dict in (("h16_to_h24", lpair_16_24), ("h24_to_h32", lpair_24_32)):
                    for ch_name, info in p_dict["cl_rel_changes"].items():
                        if not info["passed_1e6"]:
                            failed_cl_details.append({
                                "case": case,
                                "pair": p_name,
                                "channel": ch_name,
                                "worst_ell": info["worst_ell"],
                                "max_rel_change_cl": info["max_rel_change_cl"],
                                "worst_delta_cl_over_sky_max_cl": info["worst_delta_cl_over_sky_max_cl"],
                            })
            aniso_glob_mode_pass &= (lpair_16_24["passed_global_mode_1e6"] and lpair_24_32["passed_global_mode_1e6"])
            h16_step_order2_pass &= (
                h_ratio_d is not None and 3.5 <= h_ratio_d <= 4.5
                and h_ratio_l is not None and 3.5 <= h_ratio_l <= 4.5
            )
        if case in COFLOW_FAMILIES:
            coflow_rg_pass &= (rel_d1 > 1e-9 and ratio_d is not None and 3.5 <= ratio_d <= 4.5)
        if case != "FLRW" and case != "IX":
            non_ix_aniso_both_routes_rg_pass &= (
                ratio_d is not None and 3.5 <= ratio_d <= 4.5
                and ratio_l is not None and 3.5 <= ratio_l <= 4.5
            )
        if case == "FLRW":
            flrw_abs_rg_pass &= (max(abs_d1, abs_d2, abs_l1, abs_l2) <= 1e-13)
        elif case in ZERO_TILT_CASES:
            zero_tilt_s2k_max_rel = max(zero_tilt_s2k_max_rel, rel_d2, rel_l2)

        case_summaries[case] = {
            "expected_type": exp_type,
            "zero_tilt_case": case in ZERO_TILT_CASES,
            "lie_ic": None if case == "FLRW" else {"shear": COMMON_SHEAR, "n": FAMILIES_LIE[case][0], "a": FAMILIES_LIE[case][1]},
            "runs": runs_c,
            "route_gap_s1000_to_s2000": {
                "direct_l1_4": {"abs_s1000": abs_d1, "rel_s1000": rel_d1, "abs_s2000": abs_d2, "rel_s2000": rel_d2, "halving_ratio": ratio_d},
                "los_l1_128": {"abs_s1000": abs_l1, "rel_s1000": rel_l1, "abs_s2000": abs_l2, "rel_s2000": rel_l2, "halving_ratio": ratio_l},
            },
            "harmonic16_step_convergence": {
                "direct_l1_4": {"rel_500_1000": h_step_d_500_1k, "rel_1000_2000": h_step_d_1k_2k, "order2_ratio": h_ratio_d},
                "los_l1_128": {"rel_500_1000": h_step_l_500_1k, "rel_1000_2000": h_step_l_1k_2k, "order2_ratio": h_ratio_l},
            },
            "harmonic_l_pair_convergence": {
                "h16_to_h24": lpair_16_24,
                "h24_to_h32": lpair_24_32,
            },
            "types_unchanged": type_ok,
            "h_invariant_preserved": h_ok,
            "all_screens_positive": scr_ok,
        }

    with tarfile.open(TARBALL_PATH, "w:gz") as tar:
        for case in CASES_ORDER:
            folder = RAW_ROOT / "runs" / case / "h32_s2000"
            for fn in ("modes.tsv", "los_modes.tsv", "cl.tsv", "los_cl.tsv", "diagnostics.tsv", "lie_constants.tsv", "species.tsv", "run.txt"):
                tar.add(folder / fn, arcname=f"recoil_{case}/{fn}")

    flrw_runs = results["FLRW"]
    flrw_iso_max_alm = max(r["max_abs_los_alm_l_ge_1"] for r in flrw_runs.values())

    out = {
        "schema": "htt.r114.c1_harmonic_long_atlas/1",
        "claim_ceiling": "deterministic 13-case (FLRW + 12 Bianchi) single-history harmonic+ray LoS l<=128 atlas; no ensemble covariance or family attribution",
        "binary_sha256": sha256_file(BASS_BIN),
        "rec_source_csv_sha256": rec_sha,
        "ionization_table": str(tsv_path),
        "ionization_sha256": sha256_file(tsv_path),
        "neutrino_fraction_hyrec": F_NU,
        "cosmology_anchors": anc,
        "common_shear_6": COMMON_SHEAR,
        "run_specs": RUN_SPECS,
        "total_standard_runs": len(tasks),
        "total_wall_seconds": total_wall,
        "tarball": str(TARBALL_PATH),
        "tarball_sha256": sha256_file(TARBALL_PATH),
        "cases": case_summaries,
        "acceptance": {
            "strict_cl_l_pairs_le_1e6_all_12": aniso_cl_lpair_pass,
            "strict_cl_l_pairs_le_1e6_passed_count": passed_cl_count,
            "strict_cl_l_pairs_le_1e6_failed_cases": failed_cl_details,
            "all_12_anisotropic_cl_l_pairs_le_1e6_above_f64_sub_ulp_floor": aniso_cl_above_ulp_pass,
            "all_12_anisotropic_global_mode_l_pairs_le_1e6": aniso_glob_mode_pass,
            "all_10_coflow_families_route_gap_ratio_order2": coflow_rg_pass,
            "all_11_non_ix_anisotropic_direct_and_los_route_gap_order2": non_ix_aniso_both_routes_rg_pass,
            "flrw_abs_route_gap_le_1e13": flrw_abs_rg_pass,
            "zero_tilt_anisotropic_s2000_max_rel_route_gap": zero_tilt_s2k_max_rel,
            "zero_tilt_anisotropic_s2000_route_gap_le_2e10": zero_tilt_s2k_max_rel <= 2e-10,
            "all_12_anisotropic_h16_s500_s1000_s2000_order2": h16_step_order2_pass,
            "flrw_isotropic_max_abs_alm_l_ge_1": flrw_iso_max_alm,
            "flrw_isotropic_zero_le_1e13": flrw_iso_max_alm <= 1e-13,
            "all_13_cases_types_unchanged": all_types_pass,
            "all_13_cases_h_preserved": all_h_pass,
            "all_screens_positive": all_screens_pos,
            "max_abs_gauss_residual_across_all_runs": max(
                r["max_abs_gauss_residual"] for c in CASES_ORDER for r in results[c].values()
            ),
            "max_codazzi_residual_across_all_runs": max(
                r["max_codazzi_residual_norm"] for c in CASES_ORDER for r in results[c].values()
            ),
            "max_abs_jacobi_residual_across_all_runs": max(
                r["max_abs_jacobi_residual"] for c in CASES_ORDER for r in results[c].values()
            ),
        },
    }
    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUT_JSON.write_text(json.dumps(out, indent=2) + "\n", encoding="utf-8")
    print(f"C1 COMPLETE in {total_wall:.1f}s -> {OUT_JSON}")
    print(json.dumps(out["acceptance"], indent=2))


if __name__ == "__main__":
    main()
