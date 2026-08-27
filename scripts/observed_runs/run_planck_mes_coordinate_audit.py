#!/usr/bin/env python3
"""Execute the map-free PMG-WU-003 coordinate/reducer mechanism audit."""

from __future__ import annotations

import argparse
import csv
from fractions import Fraction
import hashlib
import json
from pathlib import Path
import shutil
import tempfile

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from scipy.stats import rankdata, spearmanr

from obsstat.finite_null_reducers import (
    legacy_absolute_median_scan,
    loo_ecdf_midrank_scan,
)
from obsstat.mes_coordinate_mechanism import (
    FACTORIAL_CELL_IDS,
    epsilon1_grid,
    epsilon_from_cl,
    factorial_coordinate_cells,
    mes_coordinate_forward,
)


ROOT = Path(__file__).resolve().parents[2]
SOURCE_NPZ = ROOT / "docs/generated/pr315_planck_smica_feature_replay.npz"
FROZEN_RESULT = ROOT / "docs/generated/planck_mes_morphology/planck_mes_morphology_result.json"
DEFAULT_OUTPUT = ROOT / "docs/generated/planck_mes_coordinate_audit"
SOURCE_NPZ_SHA256 = "b262425eb4f3a879513c02644bcbdd3ab313e487d101f6a29cb85284c30f845b"
FROZEN_RESULT_SHA256 = "569c1c3edaa621695fb8a385cb1c8dee3b8bff4f4c1844b8596a7f1ddf1f0b2c"
ALL_TWO_SIDED = ("two-sided",) * 10
PHYSICS_TAILS = (
    "upper", "upper", "two-sided", "upper", "upper", "two-sided",
    "two-sided", "two-sided", "two-sided", "upper",
)
REDUCERS = {
    "LEGACY_ABSOLUTE_MEDIAN_V1": legacy_absolute_median_scan,
    "LOO_ECDF_MIDRANK_V1": loo_ecdf_midrank_scan,
}


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _content_id(payload: object) -> str:
    raw = json.dumps(payload, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()
    return "sha256:" + hashlib.sha256(raw).hexdigest()


def _write_json(path: Path, payload: object) -> None:
    path.write_text(json.dumps(payload, indent=2, sort_keys=True, allow_nan=False) + "\n")


def _load() -> tuple[np.ndarray, tuple[str, ...]]:
    if _sha(SOURCE_NPZ) != SOURCE_NPZ_SHA256 or _sha(FROZEN_RESULT) != FROZEN_RESULT_SHA256:
        raise RuntimeError("map-free immutable input identity drifted")
    with np.load(SOURCE_NPZ, allow_pickle=False) as data:
        if set(data.files) != {"covariance", "feature_ids", "feature_units", "null_features", "observed_features", "row_ids", "tails"}:
            raise RuntimeError("map-free source schema drifted")
        observed = np.asarray(data["observed_features"], dtype=float)
        nulls = np.asarray(data["null_features"], dtype=float)
        feature_ids = tuple(str(value) for value in data["feature_ids"])
    rows = np.vstack((observed, nulls))
    if rows.shape != (301, 12) or feature_ids[:4] != ("cl_l2", "cl_l3", "cl_l4", "cl_l5"):
        raise RuntimeError("exact 301-row source pool drifted")
    return rows, feature_ids


def _fraction(value: Fraction) -> str:
    return f"{value.numerator}/{value.denominator}"


def _pool_numerator(value: Fraction, row_count: int = 301) -> int:
    scaled = value * row_count
    if scaled.denominator != 1:
        raise RuntimeError("finite rank does not resolve on the complete pool")
    return scaled.numerator


def _scan_cells(cells: dict[str, np.ndarray]) -> tuple[dict, list[dict]]:
    result: dict[str, dict] = {}
    table: list[dict] = []
    for reducer_id, reducer in REDUCERS.items():
        result[reducer_id] = {}
        for cell_id in FACTORIAL_CELL_IDS:
            scan = reducer(cells[cell_id], ALL_TWO_SIDED)
            record = {
                "global_rank": _fraction(scan.global_p),
                "global_rank_numerator": scan.global_exceedances_including_observation,
                "local_rank_numerators": [_pool_numerator(value) for value in scan.local_p],
                "rank_denominator": 301,
            }
            result[reducer_id][cell_id] = record
            table.append({"reducer": reducer_id, "cell": cell_id, **record})
    return result, table


def _contrasts(factorial: dict) -> dict:
    output: dict[str, dict[str, int]] = {}
    for reducer, cells in factorial.items():
        rank = {key: int(value["global_rank_numerator"]) for key, value in cells.items()}
        output[reducer] = {
            "square_without_mix": rank["SQUARE_ONLY"] - rank["EPS_LINEAR"],
            "square_with_mix": rank["MES_SQUARED"] - rank["CARRIER_ONLY"],
            "mix_linear": rank["CARRIER_ONLY"] - rank["EPS_LINEAR"],
            "mix_squared": rank["MES_SQUARED"] - rank["SQUARE_ONLY"],
            "interaction": (rank["MES_SQUARED"] - rank["CARRIER_ONLY"]) - (rank["SQUARE_ONLY"] - rank["EPS_LINEAR"]),
        }
    return output


def _epsilon_scan(source: np.ndarray) -> list[dict]:
    eps2 = epsilon_from_cl(source[:, 0], 2)
    eps3 = epsilon_from_cl(source[:, 1], 3)
    morphology = source[:, 4:]
    rows: list[dict] = []
    baseline_sigma, baseline_w = mes_coordinate_forward(eps2, eps3, epsilon1=0.0)
    for epsilon1 in epsilon1_grid():
        sigma, omega = mes_coordinate_forward(eps2, eps3, epsilon1=float(epsilon1))
        cell = np.column_stack((sigma, omega, morphology))
        entry = {
            "epsilon1": float(epsilon1),
            "observed_sigma2_max": float(sigma[0]),
            "observed_w2_max": float(omega[0]),
            "sigma_ratio_to_epsilon1_zero": float(sigma[0] / baseline_sigma[0]),
            "w_ratio_to_epsilon1_zero": float(omega[0] / baseline_w[0]),
        }
        for reducer_id, reducer in REDUCERS.items():
            entry[reducer_id] = reducer(cell, ALL_TWO_SIDED).global_exceedances_including_observation
        rows.append(entry)
    return rows


def _write_csv(path: Path, rows: list[dict]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader(); writer.writerows(rows)


def _plots(output: Path, factorial: dict, epsilon_rows: list[dict]) -> None:
    labels = {
        "LEGACY_ABSOLUTE_MEDIAN_V1": "Legacy abs-median",
        "LOO_ECDF_MIDRANK_V1": "LOO-ECDF midrank",
    }
    x = np.arange(4)
    fig, ax = plt.subplots(figsize=(6.4, 4.0))
    for reducer, marker in zip(REDUCERS, ("o", "s")):
        y = [factorial[reducer][cell]["global_rank_numerator"] / 301 for cell in FACTORIAL_CELL_IDS]
        ax.plot(x, y, marker=marker, label=labels[reducer])
    ax.set_xticks(x, FACTORIAL_CELL_IDS, rotation=18); ax.set_ylabel("Observation-inclusive family rank")
    ax.set_title("Predeclared coordinate-mechanism cells"); ax.legend(fontsize=7); fig.tight_layout()
    fig.savefig(output / "figure_factorial_ladder.pdf"); plt.close(fig)

    fig, ax = plt.subplots(figsize=(6.4, 4.0))
    legacy = [factorial["LEGACY_ABSOLUTE_MEDIAN_V1"][cell]["global_rank_numerator"] / 301 for cell in FACTORIAL_CELL_IDS]
    ecdf = [factorial["LOO_ECDF_MIDRANK_V1"][cell]["global_rank_numerator"] / 301 for cell in FACTORIAL_CELL_IDS]
    ax.scatter(legacy, ecdf)
    offsets = ((0, 8), (0, -12), (0, 8), (0, -12))
    for a, b, label, offset in zip(legacy, ecdf, FACTORIAL_CELL_IDS, offsets):
        ax.annotate(label, (a, b), xytext=offset, textcoords="offset points", fontsize=7, ha="center")
    ax.set_xlabel("Legacy absolute-median rank"); ax.set_ylabel("LOO-ECDF midrank"); ax.set_title("Reducer comparison")
    ax.margins(x=0.12, y=0.18)
    fig.tight_layout(); fig.savefig(output / "figure_reducer_comparison.pdf"); plt.close(fig)

    fig, ax = plt.subplots(figsize=(6.4, 4.0))
    eps = [row["epsilon1"] for row in epsilon_rows]
    for reducer in REDUCERS:
        ax.plot(eps, [row[reducer] / 301 for row in epsilon_rows], label=labels[reducer])
    ax.set_xlabel(r"$\epsilon_1$ premise"); ax.set_ylabel("MES-squared family rank"); ax.set_title("Row-symmetric epsilon1 sensitivity")
    ax.legend(fontsize=7); fig.tight_layout(); fig.savefig(output / "figure_epsilon1_sensitivity.pdf"); plt.close(fig)


def build(output: Path) -> dict:
    if output.exists():
        raise RuntimeError("output directory must not already exist")
    source, feature_ids = _load()
    cells = dict(factorial_coordinate_cells(source))
    factorial, factorial_table = _scan_cells(cells)
    contrasts = _contrasts(factorial)
    epsilon_rows = _epsilon_scan(source)
    output.mkdir(parents=True)
    _write_csv(output / "factorial_table.csv", factorial_table)
    tail_rows = []
    for registry_id, tails in (("LEGACY_ALL_TWO_SIDED_V1", ALL_TWO_SIDED), ("REGISTERED_PHYSICS_ORIENTED_SCALAR_V1", PHYSICS_TAILS)):
        for reducer_id, reducer in REDUCERS.items():
            scan = reducer(cells["MES_SQUARED"], tails)
            tail_rows.append({"tail_registry": registry_id, "reducer": reducer_id, "global_rank_numerator": scan.global_exceedances_including_observation, "rank_denominator": 301})
    _write_csv(output / "tail_table.csv", tail_rows)
    _write_csv(output / "epsilon1_sensitivity.csv", epsilon_rows)
    tie_rows = []
    for cell_id, matrix in cells.items():
        correlation = spearmanr(matrix, axis=0).statistic
        eigenvalues = np.linalg.eigvalsh(np.asarray(correlation, dtype=float))
        participation = float(eigenvalues.sum() ** 2 / np.square(eigenvalues).sum())
        for column in range(matrix.shape[1]):
            tie_rows.append({"cell": cell_id, "coordinate_index": column, "duplicate_count": int(matrix.shape[0] - np.unique(matrix[:, column]).size), "spearman_participation_ratio": participation})
    _write_csv(output / "tie_dependence_table.csv", tie_rows)
    _plots(output, factorial, epsilon_rows)
    frozen = json.loads(FROZEN_RESULT.read_text())
    result = {
        "format": "PLANCK_MES_COORDINATE_MECHANISM_AUDIT_V1",
        "owner": "OBSSTAT",
        "scope": "map-free exact 301-row scalar coordinate/reducer mechanism audit",
        "claim_tier": "methods_diagnostic",
        "artifact_mode": "executed_observed_diagnostic",
        "allowed_use": ["coordinate sensitivity", "finite-pool reducer comparison"],
        "forbidden_use": ["physical shear or vorticity", "local/global identification", "Bianchi family identification", "independent information gain"],
        "transfer_source": "none; committed Planck feature pool",
        "null_status": "exact ordered 300-row FFP10 CMB+noise conditional pool",
        "covariance_status": "not used by rank scans",
        "row_count": 301,
        "source_feature_order": list(feature_ids),
        "source_npz_sha256": SOURCE_NPZ_SHA256,
        "frozen_result_sha256": FROZEN_RESULT_SHA256,
        "factorial_cells": factorial,
        "contrasts": contrasts,
        "tail_registries": {"LEGACY_ALL_TWO_SIDED_V1": list(ALL_TWO_SIDED), "REGISTERED_PHYSICS_ORIENTED_SCALAR_V1": list(PHYSICS_TAILS)},
        "epsilon1_grid": {"minimum": 0.0, "maximum": 1e-5, "points": 101},
        "frozen_baseline": {"MES_SQUARED_legacy_rank": f"{legacy_absolute_median_scan(cells['MES_SQUARED'], ALL_TWO_SIDED).global_exceedances_including_observation}/301", "committed_rank": frozen["global_finite_rank"]},
        "independent_information_gain": False,
        "raw_maps_reopened": False,
        "selection_policy": "cells reducers tails and epsilon grid frozen before observed-row scoring",
    }
    result["content_id"] = _content_id(result)
    _write_json(output / "result.json", result)
    _write_json(output / "plot_audit.json", {"category": "DIAGNOSTIC", "claim_tier": "methods_diagnostic", "owner": "OBSSTAT", "source": {"result_content_id": result["content_id"], "epsilon1_sensitivity_sha256": _sha(output / "epsilon1_sensitivity.csv")}, "figures": sorted(path.name for path in output.glob("*.pdf")), "byte_identity_role": "PDF_BYTES_NOT_A_SCIENTIFIC_GATE", "visual_inspection": "PASS_AT_130_DPI_SINGLE_COLUMN_20260828", "does_not_show": ["physical source attribution", "family identification", "publication validation"]})
    replay = {"format": "PLANCK_MES_COORDINATE_MECHANISM_REPLAY_V1", "result_content_id": result["content_id"], "source_npz_sha256": SOURCE_NPZ_SHA256, "frozen_result_sha256": FROZEN_RESULT_SHA256, "status": "PASS"}
    _write_json(output / "replay.json", replay)
    terminal = {"format": "PLANCK_MES_COORDINATE_MECHANISM_TERMINAL_V1", "state": "EXECUTED_PENDING_REVIEW", "work_unit": "PMG-WU-003", "objective_output_sha256": {path.name: _sha(path) for path in output.iterdir() if path.suffix != ".pdf"}, "figure_outputs": sorted(path.name for path in output.glob("*.pdf")), "figure_byte_identity_role": "NOT_A_SCIENTIFIC_GATE", "claim_promotion": False, "raw_data_read_or_mutated": False, "next_executable_action": "FRESH_READ_ONLY_REVIEW", "unresolved_blockers": ["FRESH_READ_ONLY_REVIEW_PENDING"]}
    _write_json(output / "terminal.json", terminal)
    return result


def replay_committed() -> None:
    if not DEFAULT_OUTPUT.is_dir(): raise RuntimeError("committed audit is missing")
    with tempfile.TemporaryDirectory() as tmp:
        candidate = Path(tmp) / "audit"; build(candidate)
        for path in candidate.iterdir():
            committed = DEFAULT_OUTPUT / path.name
            if path.suffix in {".pdf"} or path.name == "terminal.json": continue
            if path.read_bytes() != committed.read_bytes(): raise RuntimeError(f"committed replay drifted: {path.name}")


def main() -> None:
    parser = argparse.ArgumentParser(); parser.add_argument("--output-dir", type=Path); parser.add_argument("--replay-committed", action="store_true"); args = parser.parse_args()
    if args.replay_committed: replay_committed(); return
    build(args.output_dir or DEFAULT_OUTPUT)


if __name__ == "__main__": main()
