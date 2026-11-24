#!/usr/bin/env python3
"""C3: Twelve-family long-epoch native LoS atlas (l <= 128) with 3-axis convergence checks."""
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

from scripts.r111.c1_visibility_hyrec import (
    BASS_BIN,
    cosmology_anchors,
    sha256_file,
)

ROOT = Path(__file__).resolve().parents[2]
C1_TSV = Path("/home/cosmosapjw/Downloads/htt_r111/c1_hyrec_1600/hyrec_xe_1600.tsv")
RAW_ROOT = Path("/home/cosmosapjw/Downloads/htt_r111/c3_atlas")
TARBALL_PATH = RAW_ROOT / "C3_HIGHL_ATLAS_MODES.tar.gz"
OUT_JSON = (
    ROOT
    / "docs/research_program/observational_publication_20261015/"
    / "R111_LOCAL_HIGHL_NATIVE_20261124/C3_LONG_HIGHL_ATLAS.json"
)

# Common traceless symmetric shear tensor with Sigma in 1e-4..1e-3
# max|S_ij| = 5.0e-4, ||S||_F = 6.883e-4, sqrt(S:S/6) = 2.810e-4.
COMMON_SHEAR = "0.0003 0.0002 -0.0005 0.00015 0.0001 0.00012"

# Twelve Bianchi families with small Lie data (|A|, |N| <= 0.02 at z_emit), N A = 0,
# zero Codazzi flux (I, IX) or Codazzi coflow. Diagonal IV is (0, 0, 0.01).
FAMILIES_LIE: dict[str, tuple[str, str, str, str]] = {
    "I": ("0 0 0 0 0 0", "0 0 0", "I", "I"),
    "II": ("0.01 0 0 0 0 0", "0 0 0", "II", "II"),
    "III": ("0 0.01 -0.01 0 0 0", "0.01 0 0", "III", "III"),
    "IV": ("0 0 0.01 0 0 0", "0.01 0 0", "IV", "IV"),
    "V": ("0 0 0 0 0 0", "0.01 0 0", "V", "V"),
    "VI0": ("0 0.01 -0.01 0 0 0", "0 0 0", "VI_0", "VI0"),
    "VIh": ("0 0.01 -0.01 0 0 0", "0.005 0 0", "VI_h", "VIh"),
    "VIstar": ("0 0.012 -0.012 0 0 0", "0.004 0 0", "VI*_-1/9", "VIstar"),
    "VII0": ("0 0.01 0.01 0 0 0", "0 0 0", "VII_0", "VII0"),
    "VIIh": ("0 0.01 0.01 0 0 0", "0.005 0 0", "VII_h", "VIIh"),
    "VIII": ("-0.01 0.01 0.01 0 0 0", "0 0 0", "VIII", "VIII"),
    "IX": ("0.01 0.01 0.01 0 0 0", "0 0 0", "IX", "IX"),
}

# Single-axis convergence grid around canonical (steps=4000, nmu=14, nphi=36, los=129x258)
GRID_CONFIGS: dict[str, tuple[int, int, int, int, int]] = {
    "s2000_m14_los129": (2000, 14, 36, 129, 258),
    "s4000_m14_los129": (4000, 14, 36, 129, 258),
    "s4000_m10_los129": (4000, 10, 24, 129, 258),
    "s4000_m20_los129": (4000, 20, 52, 129, 258),
    "s4000_m14_los256": (4000, 14, 36, 256, 512),
}
EXTRA_STEP_CONFIGS: dict[str, dict[str, tuple[int, int, int, int, int]]] = {
    "VI0": {"s8000_m14_los129": (8000, 14, 36, 129, 258)},
}


def inspect_run(fam: str, cfg_name: str, cfg: tuple[int, int, int, int, int], wall: float = 0.0) -> dict:
    steps, nmu, nphi, los_nt, los_np = cfg
    out_dir = RAW_ROOT / "runs" / fam / cfg_name

    diag = np.loadtxt(out_dir / "diagnostics.tsv", skiprows=1)
    rtxt = dict(
        line.split("=", 1) for line in (out_dir / "run.txt").read_text().splitlines() if "=" in line
    )
    cl = np.loadtxt(out_dir / "los_cl.tsv", skiprows=1)
    max_gauss = float(np.max(np.abs(diag[:, 4])))
    fin_gauss = float(diag[-1, 4])
    max_codazzi = float(np.max(np.abs(diag[:, 5:8])))
    max_jacobi = float(np.max(np.abs(diag[:, 8])))
    max_edef = float(np.max(np.abs(diag[:, 17])))
    min_scr = float(np.min(diag[:, 14]))
    # Parse inverse_h to verify preservation
    h_init = rtxt["lie_kappa_inverse_h_initial"]
    h_fin = rtxt["lie_kappa_inverse_h_final"]
    h_rel_drift = None
    if h_init.startswith("Some(") and h_fin.startswith("Some("):
        v0 = float(h_init[5:-1])
        v1 = float(h_fin[5:-1])
        h_rel_drift = 0.0 if v0 == 0.0 else abs(v1 - v0) / abs(v0)

    rec = {
        "steps": steps,
        "nmu": nmu,
        "nphi": nphi,
        "los_ntheta": los_nt,
        "los_nphi": los_np,
        "wall_seconds": wall,
        "los_seconds": float(rtxt["los_seconds"]),
        "los_max_landing_error": float(rtxt["los_max_landing_error"]),
        "los_min_intensity": float(rtxt["los_min_intensity"]),
        "los_min_screen_eigenvalue": float(rtxt["los_min_screen_eigenvalue"]),
        "min_forward_screen_eigenvalue": min_scr,
        "max_abs_hamiltonian_residual": max_gauss,
        "final_hamiltonian_residual": fin_gauss,
        "max_abs_codazzi_residual": max_codazzi,
        "max_abs_jacobi_residual": max_jacobi,
        "max_abs_collision_energy_defect": max_edef,
        "lie_type_initial": rtxt["lie_type_initial"],
        "lie_type_final": rtxt["lie_type_final"],
        "lie_type_unchanged": rtxt["lie_type_initial"] == rtxt["lie_type_final"],
        "lie_kappa_inverse_h_initial": h_init,
        "lie_kappa_inverse_h_final": h_fin,
        "h_rel_drift": h_rel_drift,
        "initial_dust_mode": rtxt["initial_dust_mode"],
        "initial_host_beta": [float(x) for x in diag[0, 18:21]],
        "final_hubble_ratio": float(diag[-1, 1]),
        "final_proper_depth": float(diag[-1, 16]),
        "los_modes_sha256": sha256_file(out_dir / "los_modes.tsv"),
        "modes_sha256": sha256_file(out_dir / "modes.tsv"),
        "diagnostics_sha256": sha256_file(out_dir / "diagnostics.tsv"),
        "cl_summary_selected_ells": {
            str(int(row[0])): {
                "TT": float(row[1]),
                "EE": float(row[4]),
                "BB": float(row[6]),
            }
            for row in cl[[2, 3, 4, 8, 16, 32, 64, 128]]
        },
    }
    return rec


def run_one(task: tuple[str, str, tuple[int, int, int, int, int], Path, dict[str, float], int]) -> tuple[str, str, dict]:
    fam, cfg_name, cfg, lie_path, anc, rayon_threads = task
    steps, nmu, nphi, los_nt, los_np = cfg
    out_dir = RAW_ROOT / "runs" / fam / cfg_name
    if out_dir.exists():
        shutil.rmtree(out_dir)
    cmd = [
        str(BASS_BIN), "--out", str(out_dir),
        "--lie-ic", str(lie_path),
        "--feedback", "recoil",
        "--dust-fraction", repr(anc["dust_fraction"]),
        "--omega-lambda", repr(anc["omega_lambda_emit"]),
        "--ionization", str(C1_TSV),
        "--n-h-emit-m3", repr(anc["n_h_emit_m3"]),
        "--h-emit-s", repr(anc["h_emit_s"]),
        "--duration", repr(anc["duration"]),
        "--steps", str(steps),
        "--nmu", str(nmu),
        "--nphi", str(nphi),
        "--lmax", "4",
        "--los-lmax", "128",
        "--los-ntheta", str(los_nt),
        "--los-nphi", str(los_np),
        "--collision", "sdirk2",
        "--lie-update", "congruence",
    ]
    env = dict(os.environ)
    env["RAYON_NUM_THREADS"] = str(rayon_threads)
    t0 = time.perf_counter()
    subprocess.run(cmd, check=True, capture_output=True, text=True, env=env)
    wall = time.perf_counter() - t0
    return fam, cfg_name, inspect_run(fam, cfg_name, cfg, wall=wall)


def pair_convergence(coarse_dir: Path, fine_dir: Path) -> dict:
    mc = np.loadtxt(coarse_dir / "los_modes.tsv", skiprows=1)
    mf = np.loadtxt(fine_dir / "los_modes.tsv", skiprows=1)
    cf = np.loadtxt(fine_dir / "los_cl.tsv", skiprows=1)
    ells = mc[:, 0].astype(int)
    sky_max = float(np.max(cf[1:, [1, 4, 6]]))
    res = {}
    for ch_idx, (ch, cl_col) in enumerate([("T", 1), ("E", 4), ("B", 6)]):
        cl_vals = cf[:, cl_col]
        cl_max = float(np.max(cl_vals[1:]))  # exclude l=0 monopole
        parity_null = cl_max <= 1e-12 * sky_max
        if cl_max <= 0.0 or parity_null:
            res[ch] = {
                "cl_max": cl_max,
                "sky_max_cl": sky_max,
                "parity_null_zero_channel": bool(parity_null),
                "active_ell_count": 0,
                "active_ells_range": None,
                "global_rel_change": 0.0,
                "max_per_ell_rel_change": 0.0,
                "passed_1e3": True,
            }
            continue
        active_ells = sorted(int(row[0]) for row in cf[1:] if row[cl_col] > 1e-12 * cl_max)
        mask = np.isin(ells, active_ells)
        u = mc[mask, 2 + 2 * ch_idx] + 1j * mc[mask, 3 + 2 * ch_idx]
        v = mf[mask, 2 + 2 * ch_idx] + 1j * mf[mask, 3 + 2 * ch_idx]
        glob = float(np.linalg.norm(u - v) / np.linalg.norm(v))
        worst_l = active_ells[0]
        worst_val = 0.0
        for l in active_ells:
            ml = ells == l
            ul = mc[ml, 2 + 2 * ch_idx] + 1j * mc[ml, 3 + 2 * ch_idx]
            vl = mf[ml, 2 + 2 * ch_idx] + 1j * mf[ml, 3 + 2 * ch_idx]
            nv = float(np.linalg.norm(vl))
            if nv > 0.0:
                val = float(np.linalg.norm(ul - vl) / nv)
                if val >= worst_val:
                    worst_val = val
                    worst_l = l
        res[ch] = {
            "cl_max": cl_max,
            "sky_max_cl": sky_max,
            "parity_null_zero_channel": False,
            "active_ell_count": len(active_ells),
            "active_ells_range": [active_ells[0], active_ells[-1]],
            "global_rel_change": glob,
            "max_per_ell_rel_change": worst_val,
            "worst_ell": int(worst_l),
            "passed_1e3": bool(glob <= 1e-3 and worst_val <= 1e-3),
        }
    return res


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--summarize-only", action="store_true")
    cli = ap.parse_args()

    if not C1_TSV.exists():
        raise FileNotFoundError(f"Run C1 first; missing {C1_TSV}")
    (RAW_ROOT / "lie_ics").mkdir(parents=True, exist_ok=True)
    (RAW_ROOT / "runs").mkdir(parents=True, exist_ok=True)
    anc = cosmology_anchors(1600)

    tasks = []
    for fam, (n6, a3, _exp_type, _) in FAMILIES_LIE.items():
        lie_path = RAW_ROOT / "lie_ics" / f"{fam}.lie"
        lie_path.write_text(f"shear {COMMON_SHEAR}\nn {n6}\na {a3}\n", encoding="utf-8")
        cfgs = dict(GRID_CONFIGS)
        cfgs.update(EXTRA_STEP_CONFIGS.get(fam, {}))
        for cfg_name, cfg in cfgs.items():
            tasks.append((fam, cfg_name, cfg, lie_path, anc, 4))

    t_all = time.perf_counter()
    results_grid: dict[str, dict[str, dict]] = {fam: {} for fam in FAMILIES_LIE}
    if cli.summarize_only:
        prev = json.loads(OUT_JSON.read_text(encoding="utf-8")) if OUT_JSON.exists() else {}
        prev_fams = prev.get("families", {})
        for fam, cfg_name, cfg, *_ in tasks:
            old_wall = prev_fams.get(fam, {}).get("runs", {}).get(cfg_name, {}).get("wall_seconds", 0.0)
            if fam == "VI0" and cfg_name == "s8000_m14_los129" and float(old_wall) == 0.0:
                old_wall = 752.82
            results_grid[fam][cfg_name] = inspect_run(fam, cfg_name, cfg, wall=float(old_wall))
        initial_60_wall = float(prev.get("initial_60run_wall_seconds", prev.get("total_wall_seconds", 0.0)))
        vi0_8000_wall = float(results_grid["VI0"]["s8000_m14_los129"]["wall_seconds"])
        total_wall = initial_60_wall + vi0_8000_wall
    else:
        with ThreadPoolExecutor(max_workers=6) as ex:
            for fam, cfg_name, rec in ex.map(run_one, tasks):
                results_grid[fam][cfg_name] = rec
                print(
                    f"Done {fam:6s} {cfg_name:18s}: {rec['wall_seconds']:.2f}s "
                    f"max|G|={rec['max_abs_hamiltonian_residual']:.2e} type={rec['lie_type_final']}",
                    flush=True,
                )
        total_wall = time.perf_counter() - t_all
        initial_60_wall = total_wall
        vi0_8000_wall = float(results_grid["VI0"]["s8000_m14_los129"]["wall_seconds"])

    family_summaries = {}
    all_conv_pass = True
    all_type_pass = True
    all_h_pass = True
    for fam, (_, _, exp_type, _) in FAMILIES_LIE.items():
        rdir = RAW_ROOT / "runs" / fam
        conv = {
            "steps_2000_to_4000": pair_convergence(rdir / "s2000_m14_los129", rdir / "s4000_m14_los129"),
            "mesh_10x24_to_14x36": pair_convergence(rdir / "s4000_m10_los129", rdir / "s4000_m14_los129"),
            "mesh_14x36_to_20x52": pair_convergence(rdir / "s4000_m14_los129", rdir / "s4000_m20_los129"),
            "los_129x258_to_256x512": pair_convergence(rdir / "s4000_m14_los129", rdir / "s4000_m14_los256"),
        }
        finest_step_key = "steps_2000_to_4000"
        if fam in EXTRA_STEP_CONFIGS and "s8000_m14_los129" in EXTRA_STEP_CONFIGS[fam]:
            conv["steps_4000_to_8000"] = pair_convergence(
                rdir / "s4000_m14_los129", rdir / "s8000_m14_los129"
            )
            finest_step_key = "steps_4000_to_8000"
        finest_pairs = (
            finest_step_key,
            "mesh_14x36_to_20x52",
            "los_129x258_to_256x512",
        )
        fam_conv_pass = all(conv[p][ch]["passed_1e3"] for p in finest_pairs for ch in "TEB")
        fam_type_pass = all(
            rec["lie_type_unchanged"] and rec["lie_type_final"] == exp_type
            for rec in results_grid[fam].values()
        )
        fam_h_pass = all(
            rec["h_rel_drift"] is None or rec["h_rel_drift"] <= 1e-12
            for rec in results_grid[fam].values()
        )
        all_conv_pass &= fam_conv_pass
        all_type_pass &= fam_type_pass
        all_h_pass &= fam_h_pass
        family_summaries[fam] = {
            "expected_type": exp_type,
            "lie_ic": {"shear": COMMON_SHEAR, "n": FAMILIES_LIE[fam][0], "a": FAMILIES_LIE[fam][1]},
            "runs": results_grid[fam],
            "convergence": conv,
            "finest_pairs_passed_1e3": fam_conv_pass,
            "types_unchanged": fam_type_pass,
            "h_invariant_preserved": fam_h_pass,
        }

    # Package converged canonical templates compatible with commander_native.py
    # (VI0 uses converged s8000_m14_los129; all other 11 families use s4000_m14_los129)
    canonical_configs = {
        fam: ("s8000_m14_los129" if fam == "VI0" else "s4000_m14_los129")
        for fam in FAMILIES_LIE
    }
    with tarfile.open(TARBALL_PATH, "w:gz") as tar:
        for fam, cfg_name in canonical_configs.items():
            folder = RAW_ROOT / "runs" / fam / cfg_name
            for fn in ("modes.tsv", "los_modes.tsv", "cl.tsv", "los_cl.tsv", "diagnostics.tsv", "run.txt"):
                tar.add(folder / fn, arcname=f"recoil_{fam}/{fn}")

    out = {
        "schema": "htt.r111.c3_long_highl_atlas/1",
        "claim_ceiling": "deterministic 12-family single-history LoS l<=128 atlas; no ensemble covariance or family attribution",
        "binary_sha256": sha256_file(BASS_BIN),
        "ionization_table": str(C1_TSV),
        "ionization_sha256": sha256_file(C1_TSV),
        "cosmology_anchors": anc,
        "common_shear_6": COMMON_SHEAR,
        "canonical_config": "s4000_m14_los129 (VI0 uses converged s8000_m14_los129)",
        "canonical_configs": canonical_configs,
        "los_lmax": 128,
        "total_runs": len(tasks),
        "initial_60run_wall_seconds": initial_60_wall,
        "vi0_s8000_wall_seconds": vi0_8000_wall,
        "total_wall_seconds": total_wall,
        "tarball": str(TARBALL_PATH),
        "tarball_sha256": sha256_file(TARBALL_PATH),
        "families": family_summaries,
        "acceptance": {
            "all_12_families_finest_pairs_le_1e3": all_conv_pass,
            "all_61_runs_types_unchanged": all_type_pass,
            "all_61_runs_h_preserved": all_h_pass,
            "max_abs_hamiltonian_residual_across_all_runs": max(
                rec["max_abs_hamiltonian_residual"]
                for fam in FAMILIES_LIE
                for rec in results_grid[fam].values()
            ),
        },
    }
    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUT_JSON.write_text(json.dumps(out, indent=2) + "\n", encoding="utf-8")
    print(f"Wrote {OUT_JSON} and {TARBALL_PATH} in {total_wall:.1f}s")
    print(json.dumps(out["acceptance"], indent=2))


if __name__ == "__main__":
    main()
