"""Frozen R25 finite-frame auxiliary support and joint residual consumer."""
from __future__ import annotations

import csv
import hashlib
import json
import math
import traceback
from collections import Counter
from pathlib import Path

import numpy as np
from scipy.optimize import linprog

HERE = Path(__file__).resolve().parent
OBS = HERE.parent.parent
CONTRACT = HERE.parent / "R25-DISTANCE-AUXILIARY-OVERLAP_INPUT.json"
LEDGER = Path("/mnt/extdrive/workdir/htt_open_data/cf4/D02_HI_CF4_20261018/TARGET_JOIN_AND_OOF.csv")
R23 = OBS / "CONTINUOUS_RESEARCH_20261023/execution/R23-DISTANCE/RELEASED_ROWS.csv"
DIST = OBS / "METHOD_EXECUTION_20261023/distance"
DIRECTION = DIST / "DIRECTION_JOIN.csv"
OOF = DIST / "OOF_ROWS.csv"
FITS = DIST / "RESULT.json"
SOURCE_HASHES = {
    CONTRACT: "2dfa96e815659ef53f03290f88afb3a2bd213b505856cbacd7adeeb127b2520f",
    LEDGER: "c32885cd2f081ec1bcedfcb98ef18c8c53245c12ac4a5fabb64d68b27a75f48d",
    R23: "c7912bd7dd983cdcdf47408a89da9f2b76887a0cc37fd9b5a9a8e83e03d3fe20",
    DIRECTION: "4e6e9c991ecdf2fda2a403f68a4ea5d744e244c73478eef1c70efbf007852b9a",
    OOF: "6fd8356e041e1ece186b79bf1506b04af5411e17e6c31a489a1f66da977a3c40",
    FITS: "330066f4a8605caa9874f192a938d4ef1d84cf8933bdd3e6059a40b011c28bd0",
}
TASK = "R25-DISTANCE-AUXILIARY-OVERLAP"
PACKET = "374acda1a171699f5e544a9cf1d58f6e26f78eccbe536de04b59f22f6df8dd3a"
AGENT = "/root/rc_374acda1a171699f"
CELLS = [(v, i, b) for v in "ULMH" for i in (False, True) for b in (False, True)]
STF_BASIS = np.array([
    np.diag([1., -1., 0.]) / math.sqrt(2),
    np.diag([-1., -1., 2.]) / math.sqrt(6),
    [[0., 1/math.sqrt(2), 0.], [1/math.sqrt(2), 0., 0.], [0., 0., 0.]],
    [[0., 0., 1/math.sqrt(2)], [0., 0., 0.], [1/math.sqrt(2), 0., 0.]],
    [[0., 0., 0.], [0., 0., 1/math.sqrt(2)], [0., 1/math.sqrt(2), 0.]],
])


def sha(path):
    h = hashlib.sha256()
    with Path(path).open("rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def rows(path):
    with path.open(newline="") as f:
        return list(csv.DictReader(f))


def dump(path, obj):
    path.write_text(json.dumps(obj, indent=2, sort_keys=True, allow_nan=False) + "\n")


def cell(row):
    v = int(row["Vhel"])
    klass = "U" if v == -1 else "L" if v < 5000 else "M" if v < 10000 else "H"
    assert v == -1 or v >= 0, (row["pgc"], v)
    return klass, row["incl_available"] == "True", row["Bmag_available"] == "True"


def lp(A, b):
    res = linprog(np.zeros(A.shape[1]), A_eq=A, b_eq=b, bounds=(0, None),
                  method="highs", options={"time_limit": 10,
                  "primal_feasibility_tolerance": 1e-9})
    return {"status": int(res.status), "message": res.message,
            "max_primal_error": None if res.x is None else float(np.max(np.abs(A @ res.x-b)))}


def run():
    contract = json.loads(CONTRACT.read_text())
    assert contract["task_id"] == TASK
    for p, expected in SOURCE_HASHES.items():
        actual = sha(p)
        assert actual == expected, (str(p), expected, actual)

    target = rows(LEDGER)
    released = rows(R23)
    directions = rows(DIRECTION)
    oof = rows(OOF)
    assert len(target) == 628 and len(released) == 274 and len(directions) == 274
    target_by = {int(r["pgc"]): r for r in target}
    released_by = {int(r["pgc"]): r for r in released}
    direction_by = {int(r["pgc"]): r for r in directions}
    assert len(target_by) == 628 and len(released_by) == 274 and len(direction_by) == 274
    assert set(released_by) <= set(target_by) and set(direction_by) == set(released_by)
    assert Counter(r["outcome"] for r in released) == {
        "accepted": 269, "other_quality": 1, "confused": 3, "nondetection": 1}
    assert all(target_by[k]["outcome"] == released_by[k]["outcome"] for k in released_by)

    tc = Counter(cell(r) for r in target)
    oc = Counter(cell(target_by[k]) for k in released_by)
    assert sum(tc.values()) == 628 and sum(oc.values()) == 274
    supported = {c for c in CELLS if oc[c] > 0}
    assert len(supported) == 5
    supported_ids = {k for k, r in target_by.items() if cell(r) in supported}
    assert len(supported_ids) == 625
    assert set(target_by)-supported_ids == {3974920, 4120921, 1095542}
    pgcs = np.array(sorted(released_by), dtype=np.int64)
    cidx = np.array([CELLS.index(cell(target_by[int(k)])) for k in pgcs])
    all_counts = np.array([tc[c] for c in CELLS], dtype=int)
    observed_counts = np.array([oc[c] for c in CELLS], dtype=int)
    H = np.zeros((16, 274))
    H[cidx, np.arange(274)] = 1
    assert np.array_equal(H.sum(axis=1).astype(int), observed_counts)
    unsupported = [j for j in range(16) if tc[CELLS[j]] and not oc[CELLS[j]]]
    assert len(unsupported) == 3
    witnesses = []
    for j in unsupported:
        lam = np.zeros(16)
        lam[j] = -1
        assert np.all(H.T @ lam == 0)
        gap = float((all_counts / 628) @ lam)
        assert gap == -1/628
        witnesses.append({"cell": list(CELLS[j]), "target_pgc": [k for k, r in target_by.items() if cell(r) == CELLS[j]],
                          "lambda_nonzero_index": j, "lambda_value": -1,
                          "observed_dot_exact": 0, "target_dot_rational": "-1/628"})

    supported_j = [j for j in range(16) if observed_counts[j] > 0]
    H5 = H[supported_j]
    b5 = all_counts[supported_j] / 625
    weights = np.array([tc[CELLS[j]] / (625 * oc[CELLS[j]]) for j in cidx])
    assert np.all(weights > 0) and abs(weights.sum()-1) <= 1e-12
    assert np.max(np.abs(H5 @ weights-b5)) <= 1e-12
    ess = float(1 / (weights @ weights))
    assert abs(ess-271.53708568525417) < 1e-9
    assert abs(weights.min()-0.0021333333333333334) < 1e-15
    assert abs(weights.max()-0.0064) < 1e-15

    velocity = np.array([int(target_by[int(k)]["Vhel"]) for k in pgcs])
    z = (velocity-7500)/5000
    H10 = np.vstack((H5, H5*z))
    zb = np.array([sum((int(r["Vhel"])-7500)/5000 for r in target if cell(r) == CELLS[j])/625
                   for j in supported_j])
    b10 = np.r_[b5, zb]
    high = CELLS.index(("H", True, True))
    assert tc[CELLS[high]] == 4 and oc[CELLS[high]] == 1
    high_target = [int(r["Vhel"]) for r in target if cell(r) == CELLS[high]]
    high_observed = [int(target_by[int(k)]["Vhel"]) for k in pgcs if cidx[np.where(pgcs == k)[0][0]] == high]
    assert high_observed == [10161] and sum(high_target)-4*10161 == 2547
    witness_column = np.where(cidx == high, velocity-10161, 0)
    assert np.array_equal(witness_column, np.zeros(274, dtype=int))
    assert sum(high_target)-4*10161 == 2547
    # Negative functional has zero observed value and target -2547/(625*5000).
    fine_gap = -2547/(625*5000)
    assert abs(fine_gap + 0.00081504) < 1e-15
    lp_checks = {
        "full628": lp(H, all_counts/628),
        "supported625_coarse": lp(H5, b5),
        "supported625_fine": lp(H10, b10),
    }
    assert lp_checks["full628"]["status"] == 2
    assert lp_checks["supported625_coarse"]["status"] == 0
    assert lp_checks["supported625_fine"]["status"] == 2

    # The per-PGC atomic carrier binds all twelve retained scenarios/models.
    labels = sorted({(r["scenario"], r["model"]) for r in oof})
    assert len(labels) == 12 and len(oof) == 12*274
    index = {pair: j for j, pair in enumerate(labels)}
    residual = np.full((274, 12), np.nan)
    pgc_index = {int(k): i for i, k in enumerate(pgcs)}
    for r in oof:
        i = pgc_index[int(r["pgc"])]
        j = index[(r["scenario"], r["model"])]
        assert np.isnan(residual[i, j]), (i, j)
        residual[i, j] = float(r["OOF_signed_residual_mag"])
    assert np.isfinite(residual).all()
    n = np.empty((274, 3))
    for i, k in enumerate(pgcs):
        d = direction_by[int(k)]
        ra, dec = math.radians(float(d["ra_J2000_deg"])), math.radians(float(d["dec_J2000_deg"]))
        n[i] = [math.cos(dec)*math.cos(ra), math.cos(dec)*math.sin(ra), math.sin(dec)]
    assert np.isfinite(n).all() and np.max(np.abs(np.linalg.norm(n, axis=1)-1)) <= 1e-12
    stf = np.einsum("ni,nj->nij", n, n)-np.eye(3)/3
    assert np.max(np.abs(np.trace(stf, axis1=1, axis2=2))) <= 1e-12
    tensor = residual[:, :, None, None]*stf[:, None, :, :]
    vec = residual[:, :, None]*n[:, None, :]
    coords = np.concatenate((residual[:, :, None], vec, tensor.reshape(274, 12, 9)), axis=2)
    # Independent direct matrix/basis reconstruction and fixed cyclic rotation.
    basis_coeff = np.einsum("nmij,kij->nmk", tensor, STF_BASIS)
    reconstructed = np.einsum("nmk,kij->nmij", basis_coeff, STF_BASIS)
    max_basis_error = float(np.max(np.abs(tensor-reconstructed)))
    tol = 1e-10*(1+float(np.max(np.abs(tensor))))
    assert max_basis_error <= tol
    R = np.array([[0., 0., 1.], [1., 0., 0.], [0., 1., 0.]])
    rn = n @ R.T
    rotated_direct = residual[:, :, None, None]*(np.einsum("ni,nj->nij", rn, rn)[:, None]-np.eye(3)/3)
    rotated_existing = np.einsum("ai,nmij,bj->nmab", R, tensor, R)
    max_rotation_error = float(np.max(np.abs(rotated_direct-rotated_existing)))
    assert max_rotation_error <= tol
    assert np.max(np.abs(residual[:, :, None]*rn[:, None, :] - vec @ R.T)) <= tol

    np.savez_compressed(HERE/"joint_tensor_atomic.npz", pgc=pgcs, weights=weights,
                        input_Vhel_km_s=velocity, cell_index=cidx, direction_J2000=n,
                        residual_mag=residual, vector_mag=vec, stf_tensor_mag=tensor,
                        independent_coordinates_mag=np.concatenate((residual[:, :, None], vec, basis_coeff), axis=2),
                        full_coordinates_mag=coords,
                        scenario=np.array([x[0] for x in labels]), model=np.array([x[1] for x in labels]))
    fits = json.loads(FITS.read_text())
    fitted_refs = []
    for scenario, model in labels:
        ff = fits["scenarios"][scenario]["models"][model]["full_fit"]
        fitted_refs.append({"scenario": scenario, "model": model,
                            "source": str(FITS), "json_pointer": f"/scenarios/{scenario}/models/{model}/full_fit",
                            "column_names_raw_units": fits["scenarios"][scenario]["models"][model]["column_names_raw_units"],
                            "coefficient_raw_units": ff["coefficient_raw_units"],
                            "coefficient_covariance_raw_units": ff["coefficient_covariance_raw_units"]})
    windows = {}
    for name, mask in [("global", np.ones(274, dtype=bool))] + [(v, np.array([CELLS[j][0] == v for j in cidx])) for v in "LMH"]:
        assert mask.any()
        u = np.mean(coords[mask], axis=0)
        p = np.einsum("n,nmk->mk", weights[mask], coords[mask])/weights[mask].sum()
        windows[name] = {"n": int(mask.sum()), "empirical_mass": float(mask.mean()),
                         "calibrated_mass": float(weights[mask].sum()),
                         "uniform_mean_full13": u.tolist(), "weighted_mean_full13": p.tolist(),
                         "difference_full13": (p-u).tolist()}
    cell_rows = [{"velocity": c[0], "incl_available": c[1], "Bmag_available": c[2],
                  "target": tc[c], "observed": oc[c], "undefined": tc[c]-oc[c],
                  "supported": oc[c] > 0} for c in CELLS]
    result = {
        "task_id": TASK, "packet_id": PACKET, "input_identity": "sha256:"+SOURCE_HASHES[CONTRACT],
        "scope": "exploratory finite-frame auxiliary geometry; no population outcome law",
        "source_hashes": {str(p): h for p, h in SOURCE_HASHES.items()},
        "cohort": {"target": 628, "observed": 274, "undefined": 354,
                   "quality_observed_only": dict(Counter(r["outcome"] for r in released)),
                   "quality_undefined": "UNKNOWN", "cells": cell_rows},
        "full628": {"status": "EXACT_INFEASIBLE", "witnesses": witnesses,
                    "lp_secondary": lp_checks["full628"]},
        "supported625": {"status": "STRICTLY_POSITIVE_COARSE_CALIBRATION",
                         "changed_estimand": True, "observed": 274, "undefined": 351,
                         "weights_rule": "N_c/(625*n_c)", "weight_sum": float(weights.sum()),
                         "min_weight": float(weights.min()), "max_weight": float(weights.max()),
                         "concentration_ESS": ess, "ESS_meaning": "weight concentration only",
                         "max_balance_error": float(np.max(np.abs(H5@weights-b5))),
                         "lp_secondary": lp_checks["supported625_coarse"]},
        "supported625_fine": {"status": "EXACT_INFEASIBLE_EVEN_SIGNED",
                              "sole_high_observed_Vhel_km_s": 10161,
                              "high_target_Vhel_km_s": high_target,
                              "integer_target_gap": 2547,
                              "negative_scaled_target_gap": fine_gap,
                              "negative_scaled_target_gap_rational": "-2547/(625*5000)",
                              "observed_functional_all_zero": True,
                              "lp_secondary": lp_checks["supported625_fine"]},
        "joint_carrier": {"path": str(HERE/"joint_tensor_atomic.npz"),
                          "shape": [274, 12, 13], "independent_coordinates": 9,
                          "coordinates": "scalar, 3-vector, row-major full 3x3 STF",
                          "units": "magnitude residual times dimensionless direction factors",
                          "shared_weights": True, "source_fits": fitted_refs,
                          "max_basis_error": max_basis_error,
                          "max_cyclic_rotation_error": max_rotation_error,
                          "tensor_tolerance": tol,
                          "windows": windows},
        "functional_bundle": {"x": "Full joint scalar/vector/STF empirical carrier in NPZ",
                              "F": "Support unchanged under positive weights; occupancy is measure-dependent",
                              "Q": "UNKNOWN physical anchor", "Pi": "finite empirical atomic law only; physical Pi UNKNOWN",
                              "G_F": "input heliocentric velocity L/M/H windows only; no true-depth gap"},
        "claim_status": "CONDITIONAL_CANDIDATE_PENDING_INDEPENDENT_REVIEW",
        "original_acceptance": "HOLD",
        "missing_outcome_law": "UNKNOWN",
    }
    dump(HERE/"RESULT.json", result)
    make_figure(tc, oc, labels, windows)
    report = ("# R25 auxiliary overlap\n\n"
              "The 628-target indicator system is exactly infeasible: three target cells have no observed distance. "
              "Deleting those cells defines a different 625-target estimand, with 274 strictly positive calibrated weights "
              f"(concentration ESS {ess:.6f}, range {weights.min():.8g}–{weights.max():.8g}). "
              "Fine within-cell velocity balance is again exactly infeasible: the sole observed high-cell velocity "
              "is 10161 km/s, while the four targets sum to 2547 km/s above four times that value.\n\n"
              "The joint NPZ preserves every residual's scalar, direction vector and full STF tensor for all 12 "
              "scenario/model pairs on the same 274 PGCs. RESULT.json gives uniform and calibrated global and L/M/H "
              "window means, masses, differences, and original coefficient/covariance references. The figure shows "
              "observed support and the resulting scalar mean shifts.\n\n"
              "The undefined 354 outcomes, including 351 in supported cells, remain unmeasured. Observed quality "
              "counts 269+1+3+1 apply only to 274. These weights encode auxiliary overlap and do not identify "
              "the missing tensor law, a physical Pi, true depth, or a native Bianchi result. Original acceptance "
              "remains HOLD pending independent review.\n")
    (HERE/"REPORT.md").write_text(report)
    manifest = {"task_id": TASK, "packet_id": PACKET,
                "input_identity": "sha256:"+SOURCE_HASHES[CONTRACT],
                "sources": {str(p): h for p, h in SOURCE_HASHES.items()},
                "files": {p.name: {"sha256": sha(p), "bytes": p.stat().st_size}
                          for p in [HERE/"compute.py", HERE/"RESULT.json", HERE/"joint_tensor_atomic.npz",
                                    HERE/"figure.png", HERE/"REPORT.md"]}}
    dump(HERE/"MANIFEST.json", manifest)
    print(json.dumps({"status": "candidate_complete", "full": "infeasible", "coarse": "positive",
                      "fine": "infeasible", "ess": ess, "models": len(labels),
                      "manifest_sha256": sha(HERE/"MANIFEST.json")}))


def make_figure(tc, oc, labels, windows):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    fig, axes = plt.subplots(1, 2, figsize=(12, 4.5), layout="constrained")
    names = [f"{c[0]}/{int(c[1])}/{int(c[2])}" for c in CELLS]
    x = np.arange(16)
    axes[0].bar(x, [oc[c] for c in CELLS], label="observed distance", color="#276c95")
    axes[0].bar(x, [tc[c]-oc[c] for c in CELLS], bottom=[oc[c] for c in CELLS],
                label="undefined distance", color="#d8a65d")
    axes[0].set_xticks(x, names, rotation=75, ha="right", fontsize=7)
    axes[0].set_ylabel("628 target counts")
    axes[0].legend(fontsize=8)
    axes[0].set_title("Three target cells have zero observed support")
    raw = np.array(windows["global"]["uniform_mean_full13"])[:, 0]
    cal = np.array(windows["global"]["weighted_mean_full13"])[:, 0]
    axes[1].plot(np.arange(12), raw, "o", label="uniform 274", color="#276c95")
    axes[1].plot(np.arange(12), cal, "s", label="calibrated 625 frame", color="#ac593d")
    for j in range(12):
        axes[1].plot([j, j], [raw[j], cal[j]], color="#999999", lw=0.8)
    axes[1].axhline(0, lw=0.7, color="black")
    axes[1].set_xticks(np.arange(12), [f"a{s.split('_')[1]}/b{s.split('_')[3]}\n{m[0]}" for s, m in labels], fontsize=6)
    axes[1].set_ylabel("global mean signed residual (mag)")
    axes[1].set_title("Shared weights transport all 12 residual arrays")
    axes[1].legend(fontsize=8)
    fig.savefig(HERE/"figure.png", dpi=180)
    plt.close(fig)


if __name__ == "__main__":
    try:
        run()
    except Exception:
        failure = traceback.format_exc()
        first = HERE/"FIRST_FAILURE.txt"
        if not first.exists():
            first.write_text(failure)
        print(failure, end="")
        raise
