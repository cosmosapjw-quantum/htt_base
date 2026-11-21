#!/usr/bin/env python3
"""R89 G05_PLANCK group execution (create-only).

Reuses L01/L02 scoped evidence, runs R83 p2p3_fast rank intervals on the
8-pair pilot AND binds the /mnt/extdrive/workdir 300-realization paired SMICA
CMB+Noise MC ensemble + 100 PR4 Commander low-ell EB MCs + SMICA split noise
arrays, while keeping SQ-CMB-NULL BLOCKED_INPUT and L03-L06 BLOCKED_DEPENDENCY.
"""
from __future__ import annotations

import hashlib
import json
import platform
import resource
import sys
import time
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[6]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from htt.obsstat import p2p3_fast

OUT_DIR = Path(__file__).resolve().parent
OUT_JSON = OUT_DIR / "RESULT.json"

PROG = ROOT / "docs/research_program/observational_publication_20261015"
L02_ACT = PROG / "CONTINUATION_20261018/L02_EXECUTION_20261018/results/L02_ACTUAL_STATISTICS.json"
L03_PILOT = PROG / "CONTINUATION_20261018/L03_EXECUTION_20261018/results/L02_ON_EIGHT_PAIR_PILOT.json"
R70_RES = PROG / "R70_P2_KINETIC_LIE_LOWELL_20261119/RESULTS.json"
R23_CMB = PROG / "CONTINUOUS_RESEARCH_20261023/execution/R23-CMB/RESULT.json"

WORKDIR = Path("/mnt/extdrive/workdir")
PAIRED300_DIR = WORKDIR / "analysis/planck_mes_irrep/paired300_carrier"
PR4_MC_DIR = WORKDIR / "htt_open_data/r36_pr4_actual/analysis"
SMICA_CMB_MC_DIR = WORKDIR / "raw/planck_ffp10/smica/cmb_mc"
SMICA_NOISE_MC_DIR = WORKDIR / "raw/planck_ffp10/smica/noise_mc"
D04_SPLIT_NPZ = WORKDIR / "htt_open_data/provenance/D04_SPLIT_NOISE_SELECTED_IQU_00000_20261018.npz"
L01_QU_DIR = WORKDIR / "htt_open_data/provenance/L01_SMICA_WINDOWED_QU_L128"
L01_POL_K = WORKDIR / "htt_open_data/provenance/L01_NATIVE_PR3_POL_K64x90_v2_common.npz"
R27_EIGHT = WORKDIR / "htt_open_data/r27_eight_map_saved_tensor_comparison_numeric/receipt_tail_closeout/DESCRIPTIVE_RESULT.json"


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def main() -> int:
    if OUT_JSON.exists():
        raise FileExistsError(f"Create-only refusal to overwrite {OUT_JSON}")
    t0 = time.perf_counter()

    # 1. Historical R83 Planck science gate + 8-pair pilot family rank interval
    hist = p2p3_fast.historical_planck_science_status()
    assert hist["L03_complete_source_matched_null_qualified"] is False
    assert hist["R78_original_science_states_changed"] is False

    l03_doc = json.loads(L03_PILOT.read_text(encoding="utf-8"))
    pair_ids = list(l03_doc["independent_pair_ids"])
    variants = sorted({r["variant"] for r in l03_doc["rows"]})
    row_map = {(r["simulation_id"], r["variant"]): r for r in l03_doc["rows"]}
    flds = ("T", "E", "B")
    metrics = ("quadrupole_shape", "octupole_concentration", "QO_contraction", "chirality")
    # Build (8, 5, 12) tensor over nested fields[T|E|B]["O3_summaries"][metric]; treat pair_ids[0] as pseudo-obs vs pair_ids[1:]
    feat_arr = np.empty((len(pair_ids), len(variants), len(flds) * len(metrics)), dtype=np.float64)
    for i, pid in enumerate(pair_ids):
        for j, var in enumerate(variants):
            f_dict = row_map[(pid, var)]["fields"]
            vals = []
            for fld in flds:
                o3 = f_dict[fld]["O3_summaries"]
                for met in metrics:
                    vals.append(float(abs(o3[met])))
            feat_arr[i, j] = vals
    pilot8_family = p2p3_fast.family_rank_interval(
        feat_arr[0], feat_arr[1:], simulation_ids=pair_ids[1:], null_qualified=False
    )
    # Also compute scalar T quadrupole shape working rank on sum_noise_1.00 matching test_r83_p2p3_fast
    t_quad_vals = np.array(
        [abs(row_map[(uid, "sum_noise_1.00")]["fields"]["T"]["SO3_signed"]["quadrupole_shape"]) for uid in pair_ids],
        dtype=np.float64,
    )
    pilot8_t_quad_rank = p2p3_fast.working_rank_interval(
        float(t_quad_vals[0]), t_quad_vals[1:], simulation_ids=pair_ids[1:], null_qualified=False
    )
    pilot8_family["scalar_T_quad_sum_noise_1p00_rank"] = pilot8_t_quad_rank
    pilot8_family["pseudo_observation_note"] = "pair_ids[0] used as pseudo-observation against remaining 7 pilot pairs (matching test_r83_p2p3_fast), purely code arithmetic."

    # Fallback/explicit check using pilot scalar norms via working_rank_interval
    l02_doc = json.loads(L02_ACT.read_text(encoding="utf-8"))
    r70_doc = json.loads(R70_RES.read_text(encoding="utf-8"))
    r23_cmb = json.loads(R23_CMB.read_text(encoding="utf-8"))

    # 2. Paired 300 FFP10 SMICA CMB+Noise MC carrier ensemble on /mnt/extdrive/workdir
    p300_man = json.loads((PAIRED300_DIR / "execution_manifest.json").read_text(encoding="utf-8"))
    all_row_ids = list(p300_man["row_ids"])
    assert len(all_row_ids) == 301 and all_row_ids[0] == "PLANCK-PR3-SMICA-OBSERVED"
    row_ids = all_row_ids[1:]
    assert len(row_ids) == 300
    with np.load(PAIRED300_DIR / "observed.npz", allow_pickle=False) as zo:
        obs_feat = np.asarray(zo["features"], dtype=np.float64)
        obs_carr = np.asarray(zo["carrier"], dtype=np.float64)

    sim_feat = np.empty((len(row_ids), len(obs_feat)), dtype=np.float64)
    sim_carr = np.empty((len(row_ids), len(obs_carr)), dtype=np.float64)
    for i, rid in enumerate(row_ids):
        # filenames are null-00000.npz .. null-00299.npz corresponding to row_ids order or 00000..00299
        fpath = PAIRED300_DIR / f"null-{i:05d}.npz"
        with np.load(fpath, allow_pickle=False) as zn:
            sim_feat[i] = np.asarray(zn["features"], dtype=np.float64)
            sim_carr[i] = np.asarray(zn["carrier"], dtype=np.float64)

    obs_feat_l2 = float(np.linalg.norm(obs_feat))
    sim_feat_l2 = np.linalg.norm(sim_feat, axis=1)
    rank_feat_l2 = p2p3_fast.working_rank_interval(obs_feat_l2, sim_feat_l2, simulation_ids=row_ids, null_qualified=False)

    obs_carr_l2 = float(np.linalg.norm(obs_carr))
    sim_carr_l2 = np.linalg.norm(sim_carr, axis=1)
    rank_carr_l2 = p2p3_fast.working_rank_interval(obs_carr_l2, sim_carr_l2, simulation_ids=row_ids, null_qualified=False)

    # Feature-wise standardized empirical Mahalanobis & individual feature rank intervals
    sim_mean_c = np.mean(sim_carr, axis=0)
    sim_cov_c = np.cov(sim_carr, rowvar=False)
    eigs_c = np.linalg.eigvalsh(sim_cov_c)
    inv_cov_c = np.linalg.pinv(sim_cov_c, rcond=1e-10)
    dc_obs = obs_carr - sim_mean_c
    t2_obs = float(dc_obs @ inv_cov_c @ dc_obs)
    dc_sim = sim_carr - sim_mean_c[None, :]
    t2_sim = np.einsum("ni,ij,nj->n", dc_sim, inv_cov_c, dc_sim)
    rank_t2 = p2p3_fast.working_rank_interval(t2_obs, t2_sim, simulation_ids=row_ids, null_qualified=False)

    per_feature_ranks = [
        {
            "feature_index": j,
            "observed": float(obs_feat[j]),
            "mc_mean": float(np.mean(sim_feat[:, j])),
            "mc_std": float(np.std(sim_feat[:, j], ddof=1)),
            **p2p3_fast.working_rank_interval(float(abs(obs_feat[j])), np.abs(sim_feat[:, j]), simulation_ids=row_ids, null_qualified=False),
        }
        for j in range(len(obs_feat))
    ]

    # 3. 100 Planck PR4 NPIPE Commander low-ell EB MCs (mc_0300..0399)
    with np.load(PR4_MC_DIR / "observed_lowell_EB.npz", allow_pickle=False) as zp:
        pr4_obs_E = float(np.sum(np.abs(zp["E"]) ** 2))
        pr4_obs_B = float(np.sum(np.abs(zp["B"]) ** 2))
    pr4_mc_files = sorted(PR4_MC_DIR.glob("mc_*_lowell_EB.npz"))
    pr4_mc_E = np.empty(len(pr4_mc_files), dtype=np.float64)
    pr4_mc_B = np.empty(len(pr4_mc_files), dtype=np.float64)
    pr4_ids = [f.stem for f in pr4_mc_files]
    for i, f in enumerate(pr4_mc_files):
        with np.load(f, allow_pickle=False) as zm:
            pr4_mc_E[i] = float(np.sum(np.abs(zm["E"]) ** 2))
            pr4_mc_B[i] = float(np.sum(np.abs(zm["B"]) ** 2))
    pr4_rank_E = p2p3_fast.working_rank_interval(pr4_obs_E, pr4_mc_E, simulation_ids=pr4_ids, null_qualified=False)
    pr4_rank_B = p2p3_fast.working_rank_interval(pr4_obs_B, pr4_mc_B, simulation_ids=pr4_ids, null_qualified=False)

    # 4. Split-noise HM/OE contrasts & windowed QU polarization operators + FFP10 raw FITS census
    with np.load(D04_SPLIT_NPZ, allow_pickle=False) as zd:
        splits = [str(s) for s in zd["splits"]]
        iqu = np.asarray(zd["selected_IQU_K_CMB"], dtype=np.float64)
        tmask = np.asarray(zd["T_mask"], dtype=bool)
        pmask = np.asarray(zd["P_mask"], dtype=bool)
        smap = {s.upper(): idx for idx, s in enumerate(splits)}
        hm_diff_T_rms = float(np.sqrt(np.mean((iqu[smap["HM1"], 0, tmask] - iqu[smap["HM2"], 0, tmask]) ** 2)))
        oe_diff_T_rms = float(np.sqrt(np.mean((iqu[smap["OE1"], 0, tmask] - iqu[smap["OE2"], 0, tmask]) ** 2)))
        hm_diff_Q_rms = float(np.sqrt(np.mean((iqu[smap["HM1"], 1, pmask] - iqu[smap["HM2"], 1, pmask]) ** 2)))
        oe_diff_Q_rms = float(np.sqrt(np.mean((iqu[smap["OE1"], 1, pmask] - iqu[smap["OE2"], 1, pmask]) ** 2)))

    qu_norms = {}
    for tag in ("full", "hm1", "hm2", "oe1", "oe2"):
        with np.load(L01_QU_DIR / f"{tag}.npz", allow_pickle=False) as zq:
            qu_norms[tag] = {"E_l2": float(np.linalg.norm(zq["E"])), "B_l2": float(np.linalg.norm(zq["B"]))}
    with np.load(L01_QU_DIR / "hm1.npz") as z1, np.load(L01_QU_DIR / "hm2.npz") as z2:
        qu_hm_E_diff = float(np.linalg.norm(z1["E"] - z2["E"]))
        qu_hm_B_diff = float(np.linalg.norm(z1["B"] - z2["B"]))
    with np.load(L01_QU_DIR / "oe1.npz") as z1, np.load(L01_QU_DIR / "oe2.npz") as z2:
        qu_oe_E_diff = float(np.linalg.norm(z1["E"] - z2["E"]))
        qu_oe_B_diff = float(np.linalg.norm(z1["B"] - z2["B"]))

    n_smica_cmb_fits = len(list(SMICA_CMB_MC_DIR.glob("*.fits")))
    n_smica_noise_fits = len(list(SMICA_NOISE_MC_DIR.glob("*.fits")))

    elapsed = time.perf_counter() - t0
    input_paths = (
        L02_ACT,
        L03_PILOT,
        R70_RES,
        R23_CMB,
        PAIRED300_DIR / "execution_manifest.json",
        PAIRED300_DIR / "observed.npz",
        PR4_MC_DIR / "observed_lowell_EB.npz",
        D04_SPLIT_NPZ,
        L01_QU_DIR / "full.npz",
        L01_POL_K,
    )
    out = {
        "schema": "htt.r89.g05_planck_result/1",
        "group_id": "G05_PLANCK",
        "node_ids": ["L01", "SQ-CMB-NULL", "L03", "L02", "L04", "L05", "L06"],
        "source_sha256": {str(p.relative_to(ROOT) if p.is_relative_to(ROOT) else p): _sha256(p) for p in input_paths},
        "runtime": {
            "python": platform.python_version(),
            "numpy": np.__version__,
            "elapsed_seconds": float(elapsed),
            "maxrss_kib": int(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss),
        },
        "reused_scoped_L01_L02": {
            "historical_status": hist,
            "l02_signed_field_rows": len(l02_doc["field_rows"]),
            "r70_theory_keys": list(r70_doc.keys()),
            "pilot8_family_rank": pilot8_family,
        },
        "paired300_smica_cmbnoise_mc": {
            "mc_count": len(row_ids),
            "carrier_dim": int(len(obs_carr)),
            "feature_dim": int(len(obs_feat)),
            "raw_smica_cmb_mc_fits_count": n_smica_cmb_fits,
            "raw_smica_noise_mc_fits_count": n_smica_noise_fits,
            "feature_l2_rank": rank_feat_l2,
            "carrier_l2_rank": rank_carr_l2,
            "carrier_mahalanobis_t2_obs": t2_obs,
            "carrier_cov_eig_minmax": [float(eigs_c.min()), float(eigs_c.max())],
            "carrier_t2_rank": rank_t2,
            "per_feature_abs_ranks": per_feature_ranks,
            "null_scope_note": "Single-pipeline SMICA FFP10 paired 300 MC diagnostic; NOT a joint multi-component (Commander/NILC/SEVEM/PR4) end-to-end calibrated null.",
        },
        "pr4_commander_100mc_lowell_eb": {
            "mc_count": len(pr4_mc_files),
            "observed_E_power": pr4_obs_E,
            "observed_B_power": pr4_obs_B,
            "E_power_rank": pr4_rank_E,
            "B_power_rank": pr4_rank_B,
        },
        "split_noise_and_windowed_polarization": {
            "d04_t_mask_pixels": int(tmask.sum()),
            "d04_p_mask_pixels": int(pmask.sum()),
            "d04_hm_diff_T_rms_K_CMB": hm_diff_T_rms,
            "d04_oe_diff_T_rms_K_CMB": oe_diff_T_rms,
            "d04_hm_diff_Q_rms_K_CMB": hm_diff_Q_rms,
            "d04_oe_diff_Q_rms_K_CMB": oe_diff_Q_rms,
            "l01_qu_l128_norms": qu_norms,
            "l01_qu_l128_hm_diff": {"E_l2": qu_hm_E_diff, "B_l2": qu_hm_B_diff},
            "l01_qu_l128_oe_diff": {"E_l2": qu_oe_E_diff, "B_l2": qu_oe_B_diff},
            "r23_cmb_diagnostic_status": r23_cmb.get("status"),
        },
        "node_verdicts": {
            "L01": "REUSED_SCOPED",
            "L02": "REUSED_SCOPED",
            "SQ-CMB-NULL": "BLOCKED_INPUT",
            "L03": "BLOCKED_DEPENDENCY",
            "L04": "BLOCKED_DEPENDENCY",
            "L05": "BLOCKED_DEPENDENCY",
            "L06": "BLOCKED_DEPENDENCY",
        },
        "missing_physics_and_next_action": {
            "missing": [
                "Full release-matched multi-pipeline T+E+B exchangeable signal+noise+foreground MC ensemble across SMICA/Commander/NILC/SEVEM",
                "Calibrated physical CMB rarity/p-value null for joint family statistics (cannot promote 9 processing variants or SMICA-only 300-pair carrier to SQ-CMB-NULL)",
            ],
            "next_action": "Obtain calibrated multi-component PR3/PR4 end-to-end simulation ensemble before promoting SQ-CMB-NULL / L03-L06.",
        },
    }
    OUT_JSON.write_text(json.dumps(out, indent=2, ensure_ascii=False, allow_nan=False) + "\n", encoding="utf-8")
    print(json.dumps({
        "group_id": "G05_PLANCK",
        "elapsed_s": round(elapsed, 3),
        "paired300_carrier_t2_rank": rank_t2["rank_interval"],
        "paired300_feat_l2_rank": rank_feat_l2["rank_interval"],
        "pr4_100mc_E_rank": pr4_rank_E["rank_interval"],
        "pr4_100mc_B_rank": pr4_rank_B["rank_interval"],
        "raw_smica_fits": [n_smica_cmb_fits, n_smica_noise_fits],
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
