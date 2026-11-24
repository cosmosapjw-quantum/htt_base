"""R108 S1-S3: line-of-sight family atlas, native truncation audit and convergence axes.

Solver settings are those of R106: stage-rate Thomson collisions, substep depth cap 0.25,
|Delta ln rate| <= 0.25, adaptive Picard (minimum 4 sweeps, picard_rtol 1e-6),
epsilon 2e-4 (0 for FLRW), substeps_per_cell 2, record_history with the R108 optical
substep source nodes (history_substep_tau_max 40).

Tasks (family x native ell_max x cells):
  S1  ell_max 8, cells 192 and 384, all eight family settings
      (FLRW, I, V, VII_h +1, VII_h -1, VI_h, VI_-1/9, IX); LoS on HEALPix Nside 64
      (lmax 128) and 128 (lmax 256); ray step 0.02.
  S3  extra axes on the ell_max 8 runs: cells 768 (Nside 64), ray step 0.01 at
      384 cells (Nside 64); Nside 64 versus 128 at 384 cells.
  S2  native ell_max 4, 6, 12 at 192 cells (the ell_max 8 run is shared): low-ell LoS on a
      Gauss-Legendre sphere (24 rings) projected to ell <= 6.

Per task the script writes ~/Downloads/htt_r108/atlas/runs/<tag>.json (config, solver
residuals, runtime, max RSS, low-ell LoS versus native) and, for HEALPix products,
~/Downloads/htt_r108/atlas/alm/<tag>_ns<N>_st<step>.npz (T, E, B, V alm in healpy
ordering and C_ell); ``summarize`` collects them into R108 ATLAS.json, TRUNCATION.json
and CONVERGENCE.json with the SHA-256 of every npz.

Units: native quarter-intensity increments (T channel (I/Ibar - 1)/4); C_ell of those
increments (multiply T by 4 for Delta I / I).  Numerical evidence only: no family
attribution, no likelihood.

Usage:
  PYTHONPATH=.:htt:htt/src OPENBLAS_NUM_THREADS=1 python -m scripts.r108.s1_family_atlas run --workers 10
  PYTHONPATH=.:htt:htt/src python -m scripts.r108.s1_family_atlas summarize
"""

from __future__ import annotations

import argparse
import json
import time
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

import numpy as np

from scripts.r108.common import OUT_DIR, maxrss_mb, sha256_file, solver_identity, write_json

WORK = Path.home() / "Downloads/htt_r108/atlas"
FAMILIES = (("FLRW", 1), ("I", 1), ("V", 1), ("VII_h", 1), ("VII_h", -1), ("VI_h", 1), ("VI_-1/9", 1), ("IX", 1))
CAP = 0.25
EPSILON = 2e-4


def tag_of(family: str, hand: int, L: int, cells: int, variant: str = "") -> str:
    fam = family.replace("/", "_").replace("-", "m")
    return f"{fam}_h{'p' if hand > 0 else 'm'}_L{L}_c{cells}" + (f"_{variant}" if variant else "")


def los_products(L: int, cells: int, variant: str = "") -> list[tuple[int, float]]:
    """(Nside, ray step) HEALPix products for a run; empty for the S2-only truncation runs.

    The R108 review (S-1) found the 0.02/0.01 ray-step axis unexercised at 384 cells: the
    optical-substep source nodes are at most 0.0096 e-folds apart, so both settings take one
    RK4 step per node interval.  The ``stepaxis`` variant re-solves the 384-cell runs and uses
    steps 0.005 and 0.0025, below the node spacing.
    """
    if variant == "stepaxis":
        return [(64, 0.005), (64, 0.0025)]
    if L != 8:
        return []
    if cells == 192:
        return [(64, 0.02), (128, 0.02)]
    if cells == 384:
        return [(64, 0.02), (64, 0.01), (128, 0.02)]
    if cells == 768:
        return [(64, 0.02)]
    return []


def tasks() -> list[tuple]:
    out = []
    for fam, hand in FAMILIES:
        for cells in (192, 384, 768):
            out.append((fam, hand, 8, cells, ""))
        for L in (4, 6, 12):
            out.append((fam, hand, L, 192, ""))
        out.append((fam, hand, 8, 384, "stepaxis"))
    cost = {4: 0.4, 6: 0.7, 8: 1.0, 12: 3.0}
    return sorted(out, key=lambda t: -cost[t[2]] * t[3] * (2.0 if t[4] else 1.0))


def _low_ell_compare(op, native_state, opo, vec, ell_max_cmp: int) -> dict:
    out = {}
    for ch in ("T", "E", "B"):
        for ell in range(0 if ch == "T" else 2, ell_max_cmp + 1):
            if (ell, 0) not in op.idx[ch] or (ell, 0) not in opo.idx[ch]:
                continue
            nat = np.array([native_state[op.idx[ch][(ell, m)]] for m in range(-ell, ell + 1)])
            los = np.array([vec[opo.idx[ch][(ell, m)]] for m in range(-ell, ell + 1)])
            peak = float(np.max(np.abs(nat)))
            out[f"{ch}{ell}"] = {"max_abs_native": peak, "max_abs_diff": float(np.max(np.abs(los - nat))),
                                 "max_rel_diff": (float(np.max(np.abs(los - nat))) / peak) if peak > 0 else None,
                                 "native": [[float(z.real), float(z.imag)] for z in nat],
                                 "los": [[float(z.real), float(z.imag)] for z in los]}
    return out


def run_task(task) -> str:
    family, hand, L, cells, variant = (tuple(task) + ("",))[:5]
    tag = tag_of(family, hand, L, cells, variant)
    out_json = WORK / "runs" / f"{tag}.json"
    if out_json.exists():
        return f"{tag} exists"
    from bass.transport.coupled_einstein_boltzmann import CoupledSolverConfig, solve_coupled_einstein_boltzmann
    from bass.transport.general_bianchi_transfer import gl_sphere_grid
    from bass.transport.general_lie_stokes import GeneralLieStokesOperator, stokes_maps_to_vector, vector_to_alm_dict
    from bass.transport.hybrid_los_transfer import (healpix_directions, history_from_coupled_result, los_alm_healpix,
                                                    los_sky, native_alm_to_healpix)

    identity = solver_identity()  # code the worker imports (R108 review S-6)
    op = GeneralLieStokesOperator(L)
    cfg = CoupledSolverConfig(n_cells=cells, ell_max=L, n_picard=4, epsilon=0.0 if family == "FLRW" else EPSILON,
                              handedness=hand, max_substep_depth=CAP, record_history=True)
    t0 = time.perf_counter()
    res = solve_coupled_einstein_boltzmann(family, cfg, lie_op=op)
    solve_s = time.perf_counter() - t0
    hist = history_from_coupled_result(res, op=op)
    dN = np.diff(hist.N)
    rec = {"tag": tag, "family": family, "handedness": hand, "ell_max": L, "n_cells": cells, "variant": variant,
           "identity": identity, "max_node_spacing": float(dN.max()), "min_node_spacing": float(dN.min()),
           "config": {k: getattr(cfg, k) for k in ("n_cells", "ell_max", "n_picard", "epsilon", "handedness",
                                                   "max_substep_depth", "stage_rate_collision", "max_substep_log_rate",
                                                   "picard_rtol", "max_picard", "substeps_per_cell",
                                                   "history_substep_tau_max", "include_moving_correction",
                                                   "stage_velocity_collision", "curvature", "z_initial")},
           "op_n_gl_theta": op.n_gl_theta, "solve_seconds": solve_s,
           "picard_iterations_used": res.picard_iterations_used,
           "picard_pi_local_rel_change": res.picard_pi_local_rel_change,
           "max_hamiltonian": res.max_hamiltonian_residual, "max_codazzi": res.max_codazzi_residual,
           "max_jacobi": res.max_jacobi_residual, "max_stokes_reality": res.max_stokes_reality_err,
           "total_optical_depth": res.total_optical_depth, "n_source_nodes": int(hist.N.size),
           "n_substep_nodes": hist.provenance.get("n_substep_nodes"),
           "native_cl": {ch: np.asarray(res.cl_final[ch]).tolist() for ch in "TEBV"}, "products": {}}
    # low-ell LoS on a Gauss-Legendre sphere: S2 truncation table and the native comparison
    n_gl, L_out = 24, min(L, 6)
    _, _, d, _ = gl_sphere_grid(n_gl)
    t1 = time.perf_counter()
    sky = los_sky(hist, d.reshape(-1, 3), max_step=0.02)
    opo = GeneralLieStokesOperator(L_out)
    vec = stokes_maps_to_vector(np.stack([sky.T, sky.Q, sky.U, sky.V], -1), opo.idx, opo.dim, L=L_out, n_gl_theta=n_gl)
    rec["gl_low_ell"] = {"n_gl": n_gl, "L_out": L_out, "seconds": time.perf_counter() - t1,
                         "diagnostics": {k: sky.diagnostics[k] for k in ("source_ell_max", "max_source_truncation",
                                                                        "top_shell_relative_norm",
                                                                        "initial_state_weight_max")},
                         "compare": _low_ell_compare(op, res.final_state, opo, vec, L_out),
                         "los_vector": [[float(z.real), float(z.imag)] for z in vec]}
    native_alm = vector_to_alm_dict(res.final_state, op.idx)
    for nside, step in los_products(L, cells, variant):
        t2 = time.perf_counter()
        sky = los_sky(hist, healpix_directions(nside), max_step=step)
        los_s = time.perf_counter() - t2
        lmax = 2 * nside
        alm = los_alm_healpix(sky, nside, lmax)
        import healpy as hp

        cl = {ch: hp.alm2cl(alm[ch]) for ch in ("T", "E", "B", "V")}
        cmp = {}
        for ch in ("T", "E", "B"):
            nat = native_alm_to_healpix(native_alm[ch], lmax)
            for ell in range(0 if ch == "T" else 2, 5):
                ids = [hp.Alm.getidx(lmax, ell, m) for m in range(0, ell + 1)]
                peak = float(np.max(np.abs(nat[ids])))
                cmp[f"{ch}{ell}"] = (float(np.max(np.abs(alm[ch][ids] - nat[ids])) / peak) if peak > 0 else None)
        flrw_max = None
        if family == "FLRW":
            flrw_max = float(max(np.max(np.abs(alm["T"][1:])), np.max(np.abs(alm["E"])), np.max(np.abs(alm["B"])),
                                 np.max(np.abs(alm["V"]))))
        npz = WORK / "alm" / f"{tag}_ns{nside}_st{step}.npz"
        npz.parent.mkdir(parents=True, exist_ok=True)
        np.savez_compressed(npz, T=alm["T"], E=alm["E"], B=alm["B"], V=alm["V"], lmax=lmax,
                            cl_T=cl["T"], cl_E=cl["E"], cl_B=cl["B"], cl_V=cl["V"])
        rec["products"][f"ns{nside}_st{step}"] = {
            "nside": nside, "lmax": lmax, "max_step": step, "los_seconds": los_s,
            "diagnostics": {k: sky.diagnostics[k] for k in ("source_ell_max", "max_source_truncation",
                                                           "top_shell_relative_norm", "n_nodes")},
            "healpix_vs_native_low_ell_rel": cmp, "flrw_max_abs_alm_except_monopole": flrw_max,
            "rk4_steps_per_node_interval": [int(np.ceil(dN.min() / step)), int(np.ceil(dN.max() / step))],
            "npz": str(npz), "npz_sha256": sha256_file(npz)}
    rec["maxrss_MB"] = maxrss_mb()
    rec["wall_seconds"] = time.perf_counter() - t0
    write_json(out_json, rec)
    return f"{tag} done {rec['wall_seconds']:.0f}s"


def run(args) -> None:
    (WORK / "runs").mkdir(parents=True, exist_ok=True)
    ident = WORK / "IDENTITY.json"
    if not ident.exists():
        write_json(ident, solver_identity())
    todo = [t for t in tasks() if not (WORK / "runs" / f"{tag_of(*t)}.json").exists()]
    print(f"{len(todo)} tasks to run", flush=True)
    with ProcessPoolExecutor(max_workers=args.workers) as ex:
        futs = {ex.submit(run_task, t): t for t in todo}
        for f, t in futs.items():
            try:
                print(f.result(), flush=True)
            except Exception as e:  # recorded, never silently dropped
                err = WORK / "runs" / f"{tag_of(*t)}.error.txt"
                err.write_text(f"{type(e).__name__}: {e}\n")
                print(f"{tag_of(*t)} FAILED {type(e).__name__}: {e}", flush=True)


AMP_FLOOR = 1e-6   # modes below this fraction of the run's largest low-ell native amplitude are not compared
CL_FLOOR = 1e-12   # C_ell below this fraction of the run's largest C_ell (T, E, B; ell >= 2) are not compared
ACCEPT = 1e-3


def _floored(compare: dict, rel_by_mode: dict | None = None, ell_max: int = 4) -> dict:
    """Relative errors only on modes whose native amplitude is >= AMP_FLOOR x the run's largest low-ell mode.

    R108 review S-3: modes at rounding level (e.g. Bianchi I B3, native 7e-15 against T2 7e-5) gave
    meaningless relative values; the absolute difference and the native amplitude are kept.
    """
    peaks = {k: v["max_abs_native"] for k, v in compare.items() if int(k[1:]) <= ell_max}
    top = max(peaks.values()) if peaks else 0.0
    out, below = {}, []
    for k, pk in peaks.items():
        rel = compare[k]["max_rel_diff"] if rel_by_mode is None else rel_by_mode.get(k)
        if top <= 0.0 or pk < AMP_FLOOR * top:
            below.append(k)
            continue
        out[k] = {"rel": rel, "abs": None if rel is None else rel * pk, "native_amplitude": pk}
    valid = [(k, v["rel"]) for k, v in out.items() if v["rel"] is not None]
    worst = max(valid, key=lambda kv: kv[1]) if valid else (None, None)
    return {"max_rel": worst[1], "argmax": worst[0], "largest_native_amplitude": top,
            "amplitude_floor": AMP_FLOOR, "below_floor": sorted(below), "modes": out}


def _run_cl_top(c: dict) -> float:
    return max(float(np.max(np.abs(np.asarray(c[f"cl_{ch}"])[2:]))) for ch in ("T", "E", "B"))


def _cl_change(a: dict, b: dict, ell_cut: int) -> dict:
    """Max relative C_ell change per spectrum where C_ell(b) > CL_FLOOR x the run's largest C_ell."""
    top = _run_cl_top(b)
    out = {}
    for ch in ("T", "E", "B"):
        ca, cb = np.asarray(a[f"cl_{ch}"]), np.asarray(b[f"cl_{ch}"])
        n = min(ca.size, cb.size, ell_cut + 1)
        ca, cb = ca[:n], cb[:n]
        ell = np.arange(n)
        mask = (ell >= (1 if ch == "T" else 2)) & (np.abs(cb) > CL_FLOOR * top)
        rel = np.abs(ca[mask] - cb[mask]) / np.abs(cb[mask]) if top > 0 else np.array([])
        out[ch * 2] = {"max_rel_change": float(rel.max()) if rel.size else None,
                       "argmax_ell": int(ell[mask][rel.argmax()]) if rel.size else None,
                       "n_ell_compared": int(mask.sum()), "peak_cl": float(np.max(np.abs(cb[2:]))) if n > 2 else 0.0,
                       "run_peak_cl": top, "cl_floor": CL_FLOOR}
    return out


def _cells_order(c1: dict, c2: dict, c3: dict, ell_cut: int) -> dict:
    """Observed ratio of successive C_ell changes (192->384->768) and Richardson remaining-error estimates."""
    top = _run_cl_top(c3)
    out = {}
    for ch in ("T", "E", "B"):
        a, b, c = (np.asarray(x[f"cl_{ch}"])[:ell_cut + 1] for x in (c1, c2, c3))
        ell = np.arange(c.size)
        mask = (ell >= (1 if ch == "T" else 2)) & (np.abs(c) > CL_FLOOR * top)
        rows = []
        for l in ell[mask]:
            d1, d2 = a[l] - b[l], b[l] - c[l]
            if d2 == 0.0:
                continue
            r = d1 / d2
            if r > 1.0:
                e768 = abs(d2) / (r - 1.0) / abs(c[l])
                rows.append((int(l), float(r), float(np.log2(r)), e768, abs(d2) * r / (r - 1.0) / abs(c[l]), True))
            else:
                rows.append((int(l), float(r), None, None, None, False))
        asym = [x for x in rows if x[5]]
        out[ch * 2] = {"n_ell": len(rows), "n_non_asymptotic": len(rows) - len(asym),
                       "non_asymptotic_ells": [x[0] for x in rows if not x[5]][:20],
                       "max_richardson_rel_error_384": max((x[4] for x in asym), default=None),
                       "max_richardson_rel_error_768": max((x[3] for x in asym), default=None),
                       "median_observed_order": float(np.median([x[2] for x in asym])) if asym else None}
    return out


def _npz(runs: dict, tag: str, key: str):
    r = runs.get(tag)
    if r is None or key not in r["products"]:
        return None
    return dict(np.load(r["products"][key]["npz"]))


def summarize(args) -> None:
    runs = {p.stem: json.loads(p.read_text()) for p in sorted((WORK / "runs").glob("*.json"))}
    errors = {p.name: p.read_text().strip() for p in sorted((WORK / "runs").glob("*.error.txt"))}
    ident = json.loads((WORK / "IDENTITY.json").read_text())
    ell_cut = int(1.2 * 64)
    atlas, trunc, conv = [], [], []
    for fam, hand in FAMILIES:
        for cells in (192, 384, 768):
            r = runs.get(tag_of(fam, hand, 8, cells))
            if r is None:
                continue
            comp = r["gl_low_ell"]["compare"]
            atlas.append({k: r[k] for k in ("tag", "family", "handedness", "ell_max", "n_cells", "solve_seconds",
                                            "wall_seconds", "maxrss_MB", "picard_iterations_used", "max_hamiltonian",
                                            "max_codazzi", "max_jacobi", "n_source_nodes", "n_substep_nodes")}
                         | {"identity": r.get("identity", "atlas IDENTITY.json (written when the run started)"),
                            "gl_low_ell_vs_native": _floored(comp),
                            "products": {k: {**{kk: v[kk] for kk in ("nside", "lmax", "max_step", "los_seconds",
                                                                     "flrw_max_abs_alm_except_monopole", "npz",
                                                                     "npz_sha256", "diagnostics")},
                                             "healpix_low_ell_vs_native": _floored(comp, v["healpix_vs_native_low_ell_rel"])}
                                         for k, v in r["products"].items()}})
        # S2: LoS(L) versus native(L), native(L) versus native(12), LoS(L) versus LoS(12) at ell <= L/2
        ref = runs.get(tag_of(fam, hand, 12, 192))
        row = {"family": fam, "handedness": hand, "cells": 192, "by_L": {}}
        for L in (4, 6, 8, 12):
            r = runs.get(tag_of(fam, hand, L, 192))
            if r is None:
                continue
            comp = r["gl_low_ell"]["compare"]
            ent = {"los_vs_native": _floored(comp, ell_max=L // 2)}
            if ref is not None:
                rc = ref["gl_low_ell"]["compare"]
                pk = {k: rc[k]["max_abs_native"] for k in rc if int(k[1:]) <= L // 2}
                top = max(pk.values()) if pk else 0.0
                nv, lv, below = {}, {}, []
                for k, v in comp.items():
                    if int(k[1:]) > L // 2 or k not in rc:
                        continue
                    if top <= 0.0 or pk[k] < AMP_FLOOR * top:
                        below.append(k)
                        continue
                    nat_L, nat_R = np.array(v["native"]), np.array(rc[k]["native"])
                    los_L, los_R = np.array(v["los"]), np.array(rc[k]["los"])
                    nv[k] = float(np.max(np.hypot(*(nat_L - nat_R).T)) / pk[k])
                    lv[k] = float(np.max(np.hypot(*(los_L - los_R).T)) / pk[k])
                ent["native_L_vs_native_12"] = {"max_rel": max(nv.values(), default=None), "modes": nv}
                ent["los_L_vs_los_12"] = {"max_rel": max(lv.values(), default=None), "modes": lv}
                ent["below_floor"] = sorted(below)
            row["by_L"][str(L)] = ent
        n8 = row["by_L"].get("8", {}).get("native_L_vs_native_12", {}).get("max_rel")
        row["L8_native_truncation_exceeds_1e-3_at_ell_le_4"] = None if n8 is None else bool(n8 > 1e-3)
        trunc.append(row)
        # S3 axes on C_ell
        c192, c384, c768 = (_npz(runs, tag_of(fam, hand, 8, c), "ns64_st0.02") for c in (192, 384, 768))
        n128 = _npz(runs, tag_of(fam, hand, 8, 384), "ns128_st0.02")
        stag = tag_of(fam, hand, 8, 384, "stepaxis")
        s005, s0025 = (_npz(runs, stag, f"ns64_st{st}") for st in (0.005, 0.0025))
        if fam == "FLRW":
            conv.append({"family": fam, "handedness": hand,
                         "flrw_max_abs_alm_except_monopole": {tag_of(fam, hand, 8, c): {k: v["flrw_max_abs_alm_except_monopole"]
                                                                                      for k, v in runs[tag_of(fam, hand, 8, c)]["products"].items()}
                                                              for c in (192, 384, 768) if tag_of(fam, hand, 8, c) in runs},
                         "note": "no anisotropy: relative C_ell changes are not defined"})
            continue
        axes = {}
        if c192 is not None and c384 is not None:
            axes["cells_192_vs_384"] = _cl_change(c192, c384, ell_cut)
        if c384 is not None and c768 is not None:
            axes["cells_384_vs_768"] = _cl_change(c384, c768, ell_cut)
        if c192 is not None and c384 is not None and c768 is not None:
            axes["cells_order_richardson"] = _cells_order(c192, c384, c768, ell_cut)
        if s005 is not None and s0025 is not None:
            sr = runs[stag]
            axes["step_0.005_vs_0.0025"] = {**_cl_change(s005, s0025, ell_cut),
                                            "rk4_steps_per_node_interval": {k: v["rk4_steps_per_node_interval"]
                                                                            for k, v in sr["products"].items()},
                                            "max_node_spacing": sr["max_node_spacing"]}
            n_sub = [int(np.ceil(sr["max_node_spacing"] / st)) for st in (0.02, 0.01)]
            axes["step_0.02_vs_0.01"] = {"exercised": n_sub[0] != n_sub[1], "rk4_steps_at_max_node_spacing": n_sub,
                                         "note": "both settings take one RK4 step per node interval at 384 cells "
                                                 "(R108 review S-1); superseded by step_0.005_vs_0.0025"}
        if c384 is not None and n128 is not None:
            axes["nside_64_vs_128"] = _cl_change(c384, n128, ell_cut)
        fails = []
        for ax in ("cells_384_vs_768", "step_0.005_vs_0.0025", "nside_64_vs_128"):
            for sp, v in axes.get(ax, {}).items():
                if isinstance(v, dict) and v.get("max_rel_change") is not None and v["max_rel_change"] > ACCEPT:
                    fails.append(f"{ax}:{sp}")
        conv.append({"family": fam, "handedness": hand, "axes": axes, "above_1e-3": fails})
    common = {"identity_at_atlas_start": ident, "settings": {"cap": CAP, "epsilon": EPSILON, "families": FAMILIES},
              "floors": {"amplitude": AMP_FLOOR, "cl": CL_FLOOR},
              "units": "native quarter-intensity increments; C_ell dimensionless", "errors": errors,
              "claim": "numerical evidence only; no family attribution, no likelihood"}
    write_json(OUT_DIR / "SOLVER" / "S1_ATLAS.json", {"schema": "htt.r108.s1_atlas.2", **common, "runs": atlas})
    write_json(OUT_DIR / "SOLVER" / "S2_TRUNCATION.json", {"schema": "htt.r108.s2_truncation.2", **common,
                                                            "threshold_L8_ell_le_4": 1e-3, "rows": trunc})
    write_json(OUT_DIR / "SOLVER" / "S3_CONVERGENCE.json", {"schema": "htt.r108.s3_convergence.2", **common,
                                                             "acceptance": "each axis <= 1e-3 where C_ell > CL_FLOOR x the run's largest C_ell, ell <= 1.2 Nside",
                                                             "rows": conv})


def main() -> None:
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    r = sub.add_parser("run")
    r.add_argument("--workers", type=int, default=10)
    sub.add_parser("summarize")
    a = ap.parse_args()
    run(a) if a.cmd == "run" else summarize(a)


if __name__ == "__main__":
    main()
