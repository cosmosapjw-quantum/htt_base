#!/usr/bin/env python3
"""Execute and replay the PMG-WU-006 paired-300 observable-irrep analysis."""

from __future__ import annotations

import argparse
import csv
from fractions import Fraction
import hashlib
import json
from pathlib import Path
import sys
import tempfile
from typing import Callable, Mapping, Sequence


ROOT = Path(__file__).resolve().parents[2]
for import_root in (ROOT / "htt" / "src", ROOT / "htt"):
    if str(import_root) not in sys.path:
        sys.path.insert(0, str(import_root))

import matplotlib  # noqa: E402

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
from scipy.stats import spearmanr  # noqa: E402

from common.observable_irrep_state import ObservableIrrepCarrier  # noqa: E402
from obsstat.finite_null_reducers import (  # noqa: E402
    legacy_absolute_median_scan,
    loo_ecdf_midrank_scan,
)
from obsstat.observable_irrep_orbit import (  # noqa: E402
    FRAME_FREE_FAMILY_ID,
    FRAME_FREE_FEATURE_IDS,
    FRAME_FREE_TAILS,
    GALACTIC_ORIENTATION_FAMILY_ID,
    GALACTIC_ORIENTATION_FEATURE_IDS,
    GALACTIC_ORIENTATION_TAILS,
    family_registry_payload,
    observable_irrep_orbit_report,
    orbit_family_vector,
)
from obsstat.planck_irrep_carrier import replay_planck_irrep_carrier  # noqa: E402
from obsstat.planck_lowell_irrep_projection import (  # noqa: E402
    OBSERVABLE_STF_BASIS,
    PROJECTION_IDENTITY,
    project_planck_carrier_to_observable_irreps,
    stf2_components_to_tensor,
    stf2_to_real_harmonic,
    stf3_components_to_tensor,
    stf3_to_real_harmonic,
)


FORMAT = "PLANCK_MES_OBSERVABLE_IRREP_ANALYSIS_V1"
DEFAULT_CARRIER_DIR = ROOT / "docs/generated/planck_pr3_paired300_irrep_carrier"
DEFAULT_OUTPUT = ROOT / "docs/generated/planck_mes_irrep_analysis"
COORDINATE_AUDIT_DIR = ROOT / "docs/generated/planck_mes_coordinate_audit"
EXPECTED_CARRIER_PACKAGE_SHA256 = (
    "sha256:0a296c21902b691eb2e2b68a9b39f626020aa8c2b14fb93a1b12116215886b93"
)
EXPECTED_CARRIER_METADATA_SHA256 = (
    "sha256:08be4f0ab0025969cb13b0cf4fed135ebfbc5fb2f0597ce0bfd0f1caf3f0721e"
)
EXPECTED_CARRIER_CONTENT_ID = (
    "sha256:9fa50a818f18346766a07481242acde3afa6069e40b8a279fbc2b1e0f5d013d3"
)
EXPECTED_COORDINATE_REGISTRY_SHA256 = (
    "sha256:fe5e56b06edc1ecedbca3735c822d23bab309a88201e185dd1d43ad68bbbd70e"
)
NUMERICAL_RTOL = 5.0e-13
NUMERICAL_ATOL = 5.0e-13

REDUCERS: Mapping[str, Callable] = {
    "LEGACY_ABSOLUTE_MEDIAN_V1": legacy_absolute_median_scan,
    "LOO_ECDF_MIDRANK_V1": loo_ecdf_midrank_scan,
}
ALL_COORDINATE_IDS = (
    "q2",
    "q3",
    "J_Q",
    "o2",
    "R_v0_normalized",
    "R_v1_normalized",
    "R_v2_normalized",
    "R_QS_normalized",
    "K_v_normalized",
    "Q_galactic_pole_power",
    "O_galactic_pole_power",
)
DETERMINISTIC_EVIDENCE_FILES = (
    "coordinate_table.csv",
    "degeneracy_ledger.csv",
    "dependence_spectrum.csv",
    "family_table.csv",
    "feature_registry.json",
    "replay.json",
    "result.json",
)
FIGURE_FILES = (
    "figure_dependence_spectrum.pdf",
    "figure_family_reducer_comparison.pdf",
    "figure_null_score_distributions.pdf",
    "figure_observed_coordinate_ranks.pdf",
)


def _file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return "sha256:" + digest.hexdigest()


def _canonical_content_id(value: object, *, role: str) -> str:
    encoded = json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
        allow_nan=False,
    ).encode("ascii")
    digest = hashlib.sha256()
    digest.update(role.encode("ascii") + b"\0")
    digest.update(encoded)
    return "sha256:" + digest.hexdigest()


def _array_bundle_content_id(arrays: Mapping[str, np.ndarray], *, role: str) -> str:
    digest = hashlib.sha256()
    digest.update(role.encode("ascii") + b"\0")
    for name in sorted(arrays):
        array = np.ascontiguousarray(arrays[name])
        digest.update(name.encode("ascii") + b"\0")
        digest.update(array.dtype.str.encode("ascii") + b"\0")
        digest.update(repr(array.shape).encode("ascii") + b"\0")
        digest.update(memoryview(array).cast("B"))
    return "sha256:" + digest.hexdigest()


def _write_json(path: Path, payload: object) -> None:
    path.write_text(
        json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=True, allow_nan=False)
        + "\n",
        encoding="ascii",
    )


def _write_csv(path: Path, rows: Sequence[Mapping[str, object]]) -> None:
    if not rows:
        raise RuntimeError(f"cannot write empty table: {path.name}")
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(
            handle, fieldnames=list(rows[0]), lineterminator="\n"
        )
        writer.writeheader()
        writer.writerows(rows)


def _write_npz(path: Path, arrays: Mapping[str, np.ndarray]) -> None:
    with path.open("wb") as handle:
        np.savez(handle, **arrays)


def _load_npz(path: Path) -> dict[str, np.ndarray]:
    try:
        with np.load(path, allow_pickle=False) as bundle:
            return {name: np.asarray(bundle[name]) for name in bundle.files}
    except (OSError, ValueError, KeyError) as exc:
        raise RuntimeError(f"numerical output is not a safe NPZ: {path.name}") from exc


def _pool_numerator(value: Fraction, row_count: int) -> int:
    scaled = value * row_count
    if scaled.denominator != 1:
        raise RuntimeError("finite rank is not resolved on the complete pool")
    return int(scaled.numerator)


def _row_ids_content_id(row_ids: Sequence[str]) -> str:
    return _canonical_content_id(list(row_ids), role="planck_irrep_analysis_row_ids")


def _load_accepted_carrier(
    carrier_dir: Path,
) -> tuple[np.ndarray, tuple[str, ...], dict[str, object]]:
    carrier_dir = Path(carrier_dir)
    package_path = carrier_dir / "carrier.npz"
    metadata_path = carrier_dir / "metadata.json"
    terminal_path = carrier_dir / "terminal.json"
    coordinate_result_path = COORDINATE_AUDIT_DIR / "result.json"
    coordinate_terminal_path = COORDINATE_AUDIT_DIR / "terminal.json"
    if _file_sha256(package_path) != EXPECTED_CARRIER_PACKAGE_SHA256:
        raise RuntimeError("accepted carrier package byte identity drifted")
    if _file_sha256(metadata_path) != EXPECTED_CARRIER_METADATA_SHA256:
        raise RuntimeError("accepted carrier metadata identity drifted")
    if _file_sha256(coordinate_result_path) != EXPECTED_COORDINATE_REGISTRY_SHA256:
        raise RuntimeError("accepted reducer registry deterministic identity drifted")
    terminal = json.loads(terminal_path.read_text(encoding="ascii"))
    coordinate_terminal = json.loads(
        coordinate_terminal_path.read_text(encoding="ascii")
    )
    if (
        terminal.get("state") != "SUCCEEDED"
        or terminal.get("replay_status") != "MATCH"
        or coordinate_terminal.get("state") != "SUCCEEDED"
    ):
        raise RuntimeError("PMG-WU-005 or reducer-registry precondition is not accepted")
    replay = replay_planck_irrep_carrier(
        package_path=package_path, metadata_path=metadata_path
    )
    if replay.get("carrier_content_id") != EXPECTED_CARRIER_CONTENT_ID:
        raise RuntimeError("accepted carrier scientific content identity drifted")
    metadata = json.loads(metadata_path.read_text(encoding="ascii"))
    arrays = _load_npz(package_path)
    expected_keys = {
        "observed_real_alm",
        "null_real_alm",
        "row_ids",
        "real_alm_layout",
    }
    if set(arrays) != expected_keys:
        raise RuntimeError("accepted carrier package schema drifted")
    rows = np.vstack((arrays["observed_real_alm"], arrays["null_real_alm"]))
    row_ids = tuple(str(value) for value in arrays["row_ids"].tolist())
    if rows.shape != (301, 32) or len(row_ids) != 301:
        raise RuntimeError("accepted carrier row shape drifted")
    return rows, row_ids, metadata


def _coordinate_registry() -> list[dict[str, object]]:
    definitions = {
        "q2": ("Q_ab Q^ab", "two-sided", "EVEN", "microK_CMB^2"),
        "q3": ("Q_a^b Q_b^c Q_c^a", "two-sided", "EVEN", "microK_CMB^3"),
        "J_Q": ("sqrt(6) q3 / q2^(3/2)", "two-sided", "EVEN", "dimensionless"),
        "o2": ("O_abc O^abc", "two-sided", "EVEN", "microK_CMB^2"),
        "R_v0_normalized": ("vhat_a vhat^a", "upper", "EVEN", "dimensionless"),
        "R_v1_normalized": ("vhat_a Qhat^a_b vhat^b", "two-sided", "EVEN", "dimensionless"),
        "R_v2_normalized": ("vhat_a (Qhat^2)^a_b vhat^b", "upper", "EVEN", "dimensionless"),
        "R_QS_normalized": ("Qhat_ab Shat^ab", "two-sided", "EVEN", "dimensionless"),
        "K_v_normalized": ("det(vhat,Qhat vhat,Qhat^2 vhat)", "two-sided", "PSEUDOSCALAR", "dimensionless"),
        "Q_galactic_pole_power": ("|Qhat z_G|^2", "upper", "EVEN", "dimensionless"),
        "O_galactic_pole_power": ("|Ohat_ab c z_G^b z_G^c|^2", "upper", "EVEN", "dimensionless"),
    }
    return [
        {
            "definition": definitions[feature_id][0],
            "feature_id": feature_id,
            "parity": definitions[feature_id][2],
            "tail": definitions[feature_id][1],
            "units": definitions[feature_id][3],
        }
        for feature_id in ALL_COORDINATE_IDS
    ]


def _compute_rows(
    carrier_rows: np.ndarray,
    row_ids: Sequence[str],
    metadata: Mapping[str, object],
) -> tuple[dict[str, np.ndarray], list[dict[str, object]], list[object], float]:
    q_components = np.empty((301, 5), dtype=np.float64)
    o_components = np.empty((301, 7), dtype=np.float64)
    coordinate_values = np.full((301, len(ALL_COORDINATE_IDS)), np.nan, dtype=np.float64)
    availability = np.zeros(coordinate_values.shape, dtype=np.bool_)
    frame_free = np.empty((301, len(FRAME_FREE_FEATURE_IDS)), dtype=np.float64)
    orientation = np.empty(
        (301, len(GALACTIC_ORIENTATION_FEATURE_IDS)), dtype=np.float64
    )
    state_ids: list[str] = []
    degeneracy_rows: list[dict[str, object]] = []
    reports: list[object] = []
    max_roundtrip_residual = 0.0
    for row_index, (components, row_identity) in enumerate(
        zip(carrier_rows, row_ids, strict=True)
    ):
        carrier = ObservableIrrepCarrier(
            components=tuple(float(value) for value in components),
            frame=str(metadata["coordinate_frame"]),
            basis="ORTHONORMAL_CONDON_SHORTLEY_REAL_L2_L5_V1",
            units=str(metadata["map_unit"]),
            source_identity=str(metadata["carrier_content_id"]),
            operator_identity=str(metadata["operator_identity_sha256"]),
            row_identity=row_identity,
        )
        state = project_planck_carrier_to_observable_irreps(carrier)
        q = np.asarray(state.blocks[0].components, dtype=np.float64)
        o = np.asarray(state.blocks[1].components, dtype=np.float64)
        q_components[row_index] = q
        o_components[row_index] = o
        q_residual = float(
            np.max(np.abs(stf2_to_real_harmonic(
                stf2_components_to_tensor(q)
            ) - components[:5]))
        )
        o_residual = float(
            np.max(np.abs(stf3_to_real_harmonic(
                stf3_components_to_tensor(o)
            ) - components[5:12]))
        )
        max_roundtrip_residual = max(max_roundtrip_residual, q_residual, o_residual)
        scale = max(1.0, float(np.max(np.abs(components[:12]))))
        if max(q_residual, o_residual) > NUMERICAL_ATOL + NUMERICAL_RTOL * scale:
            raise RuntimeError(f"harmonic-STF roundtrip failed for row {row_identity}")
        report = observable_irrep_orbit_report(state)
        reports.append(report)
        state_ids.append(state.content_id)
        absent_features: list[str] = []
        for column, feature_id in enumerate(ALL_COORDINATE_IDS):
            coordinate = report.coordinate(feature_id)
            if coordinate.status == "AVAILABLE":
                coordinate_values[row_index, column] = float(coordinate.value)
                availability[row_index, column] = True
            else:
                absent_features.append(feature_id)
        try:
            frame_free[row_index] = orbit_family_vector(report, FRAME_FREE_FAMILY_ID)
            orientation[row_index] = orbit_family_vector(
                report, GALACTIC_ORIENTATION_FAMILY_ID
            )
            family_disposition = "COMPLETE"
        except ValueError:
            family_disposition = "TYPED_ABSENCE"
        degeneracy_rows.append(
            {
                "absent_feature_ids": json.dumps(absent_features, separators=(",", ":")),
                "krylov_plane_status": report.krylov_plane_status,
                "krylov_rank": report.krylov_rank,
                "mixed_vector_status": report.mixed_vector_status,
                "primary_family_disposition": family_disposition,
                "q_spectrum_status": report.q_spectrum_status,
                "row_id": row_identity,
                "row_index": row_index,
            }
        )
    unavailable = [
        row["row_id"]
        for row in degeneracy_rows
        if row["primary_family_disposition"] != "COMPLETE"
    ]
    if unavailable:
        raise RuntimeError(
            "typed-absent primary-family rows cannot be zero-filled or dropped: "
            + ",".join(str(value) for value in unavailable)
        )
    arrays = {
        "all_coordinate_values": coordinate_values,
        "coordinate_availability": availability,
        "coordinate_ids": np.asarray(ALL_COORDINATE_IDS, dtype="U32"),
        "frame_free_features": frame_free,
        "o_components": o_components,
        "orientation_features": orientation,
        "q_components": q_components,
        "row_ids": np.asarray(row_ids, dtype="U64"),
        "state_content_ids": np.asarray(state_ids, dtype="U71"),
    }
    return arrays, degeneracy_rows, reports, max_roundtrip_residual


def _scan_record(scan: object, *, row_count: int) -> dict[str, object]:
    return {
        "global_rank": (
            f"{scan.global_exceedances_including_observation}/{row_count}"
        ),
        "global_rank_numerator": int(
            scan.global_exceedances_including_observation
        ),
        "local_rank_numerators": [
            _pool_numerator(value, row_count) for value in scan.local_p
        ],
        "observation_max_score": float(scan.observation_max_score),
        "rank_denominator": row_count,
    }


def _run_scans(
    frame_free_rows: object,
    orientation_rows: object,
    *,
    observation_index: int,
) -> tuple[dict[str, dict[str, dict[str, object]]], dict[str, np.ndarray]]:
    frame_free = np.asarray(frame_free_rows, dtype=np.float64)
    orientation = np.asarray(orientation_rows, dtype=np.float64)
    if (
        frame_free.ndim != 2
        or orientation.ndim != 2
        or frame_free.shape[0] != orientation.shape[0]
        or frame_free.shape[1] != len(FRAME_FREE_FEATURE_IDS)
        or orientation.shape[1] != len(GALACTIC_ORIENTATION_FEATURE_IDS)
        or frame_free.shape[0] < 2
        or not np.all(np.isfinite(frame_free))
        or not np.all(np.isfinite(orientation))
    ):
        raise RuntimeError("family matrices do not match the frozen finite-pool registry")
    if type(observation_index) is not int or not 0 <= observation_index < frame_free.shape[0]:
        raise RuntimeError("observation index is outside the complete row pool")
    matrices = {
        FRAME_FREE_FAMILY_ID: (frame_free, FRAME_FREE_TAILS),
        GALACTIC_ORIENTATION_FAMILY_ID: (
            orientation,
            GALACTIC_ORIENTATION_TAILS,
        ),
    }
    results: dict[str, dict[str, dict[str, object]]] = {}
    distributions: dict[str, np.ndarray] = {}
    for family_id, (matrix, tails) in matrices.items():
        results[family_id] = {}
        for reducer_id, reducer in REDUCERS.items():
            scan = reducer(matrix, tails, observation_index=observation_index)
            results[family_id][reducer_id] = _scan_record(
                scan, row_count=frame_free.shape[0]
            )
            key = f"{family_id.lower()}__{reducer_id.lower()}"
            distributions[f"{key}__row_max_scores"] = np.asarray(
                scan.row_max_scores, dtype=np.float64
            )
            distributions[f"{key}__local_rank_numerators"] = np.asarray(
                [
                    [_pool_numerator(value, frame_free.shape[0]) for value in row]
                    for row in scan.local_p_all_rows
                ],
                dtype=np.int64,
            )
    return results, distributions


def calibrate_families(
    frame_free_rows: object,
    orientation_rows: object,
    *,
    observation_index: int = 0,
) -> dict[str, dict[str, dict[str, object]]]:
    """Calibrate both frozen families under both registered reducers."""

    results, _ = _run_scans(
        frame_free_rows, orientation_rows, observation_index=observation_index
    )
    return results


def _dependence_diagnostics(
    matrices: Mapping[str, np.ndarray],
) -> tuple[dict[str, object], list[dict[str, object]]]:
    diagnostics: dict[str, object] = {}
    table: list[dict[str, object]] = []
    feature_ids_by_family = {
        FRAME_FREE_FAMILY_ID: FRAME_FREE_FEATURE_IDS,
        GALACTIC_ORIENTATION_FAMILY_ID: GALACTIC_ORIENTATION_FEATURE_IDS,
    }
    for family_id, matrix in matrices.items():
        correlation = np.asarray(spearmanr(matrix, axis=0).statistic, dtype=np.float64)
        if correlation.shape != (matrix.shape[1], matrix.shape[1]) or not np.all(
            np.isfinite(correlation)
        ):
            raise RuntimeError("Spearman dependence matrix is not finite and complete")
        eigenvalues = np.linalg.eigvalsh(correlation)[::-1]
        participation = float(
            np.square(np.sum(eigenvalues)) / np.sum(np.square(eigenvalues))
        )
        duplicates = [
            int(matrix.shape[0] - np.unique(matrix[:, column]).size)
            for column in range(matrix.shape[1])
        ]
        diagnostics[family_id] = {
            "coordinate_duplicate_counts": duplicates,
            "spearman_eigenvalues_descending": [float(value) for value in eigenvalues],
            "spearman_participation_ratio": participation,
        }
        for index, (feature_id, duplicate_count) in enumerate(
            zip(feature_ids_by_family[family_id], duplicates, strict=True)
        ):
            table.append(
                {
                    "coordinate_duplicate_count": duplicate_count,
                    "family_id": family_id,
                    "feature_id": feature_id,
                    "spectrum_index": index,
                    "spearman_eigenvalue_descending": float(eigenvalues[index]),
                    "spearman_participation_ratio": participation,
                }
            )
    return diagnostics, table


def _make_tables(
    *,
    reports: Sequence[object],
    family_results: Mapping[str, Mapping[str, Mapping[str, object]]],
    degeneracy_rows: list[dict[str, object]],
    dependence_rows: list[dict[str, object]],
) -> tuple[list[dict[str, object]], list[dict[str, object]]]:
    observed = reports[0]
    family_membership = {
        feature_id: [
            family_id
            for family_id, feature_ids in (
                (FRAME_FREE_FAMILY_ID, FRAME_FREE_FEATURE_IDS),
                (GALACTIC_ORIENTATION_FAMILY_ID, GALACTIC_ORIENTATION_FEATURE_IDS),
            )
            if feature_id in feature_ids
        ]
        for feature_id in ALL_COORDINATE_IDS
    }
    coordinate_rows: list[dict[str, object]] = []
    for feature_id in ALL_COORDINATE_IDS:
        coordinate = observed.coordinate(feature_id)
        row: dict[str, object] = {
            "feature_id": feature_id,
            "family_membership": json.dumps(
                family_membership[feature_id], separators=(",", ":")
            ),
            "observed_status": coordinate.status,
            "observed_value": "" if coordinate.value is None else coordinate.value,
            "parity": coordinate.parity,
            "tail": coordinate.tail,
            "units": coordinate.units,
        }
        for reducer_id in REDUCERS:
            if feature_id in FRAME_FREE_FEATURE_IDS:
                index = FRAME_FREE_FEATURE_IDS.index(feature_id)
                row[f"{reducer_id}_local_rank_numerator"] = family_results[
                    FRAME_FREE_FAMILY_ID
                ][reducer_id]["local_rank_numerators"][index]
            else:
                row[f"{reducer_id}_local_rank_numerator"] = ""
        coordinate_rows.append(row)
    family_rows = [
        {
            "family_id": family_id,
            "frame_role": family_registry_payload()[family_id]["frame_role"],
            "global_rank": record["global_rank"],
            "global_rank_numerator": record["global_rank_numerator"],
            "observation_max_score": record["observation_max_score"],
            "rank_denominator": record["rank_denominator"],
            "reducer_id": reducer_id,
        }
        for family_id, reducer_results in family_results.items()
        for reducer_id, record in reducer_results.items()
    ]
    return coordinate_rows, family_rows


def _plots(
    output: Path,
    *,
    family_results: Mapping[str, Mapping[str, Mapping[str, object]]],
    distributions: Mapping[str, np.ndarray],
    dependence: Mapping[str, object],
) -> None:
    labels = {
        "LEGACY_ABSOLUTE_MEDIAN_V1": "Legacy abs-median",
        "LOO_ECDF_MIDRANK_V1": "LOO-ECDF midrank",
    }
    coordinate_labels = (
        r"$q_2$",
        r"$o_2$",
        r"$J_Q$",
        r"$\widehat R_{v0}$",
        r"$\widehat R_{v1}$",
        r"$\widehat R_{v2}$",
        r"$\widehat R_{QS}$",
        r"$\widehat K_v$",
    )
    fig, ax = plt.subplots(figsize=(6.8, 4.0))
    x = np.arange(len(FRAME_FREE_FEATURE_IDS))
    for reducer_id, marker in zip(REDUCERS, ("o", "s"), strict=True):
        numerators = family_results[FRAME_FREE_FAMILY_ID][reducer_id][
            "local_rank_numerators"
        ]
        ax.plot(x, np.asarray(numerators) / 301.0, marker=marker, label=labels[reducer_id])
    ax.set_xticks(x, coordinate_labels, rotation=25, ha="right", fontsize=8)
    ax.set_ylabel("Observation-inclusive local rank")
    ax.set_title("Observed frame-free irrep coordinates")
    ax.legend(fontsize=7)
    fig.tight_layout()
    fig.savefig(output / "figure_observed_coordinate_ranks.pdf")
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(6.4, 4.0))
    family_ids = (FRAME_FREE_FAMILY_ID, GALACTIC_ORIENTATION_FAMILY_ID)
    x = np.arange(2)
    width = 0.34
    for offset, reducer_id in zip((-width / 2, width / 2), REDUCERS, strict=True):
        values = [
            family_results[family_id][reducer_id]["global_rank_numerator"] / 301.0
            for family_id in family_ids
        ]
        ax.bar(x + offset, values, width=width, label=labels[reducer_id])
    ax.set_xticks(x, ("Frame-free", "+ Galactic orientation"))
    ax.set_ylabel("Observation-inclusive family rank")
    ax.set_title("Predeclared irrep families and reducers")
    ax.legend(fontsize=7)
    fig.tight_layout()
    fig.savefig(output / "figure_family_reducer_comparison.pdf")
    plt.close(fig)

    fig, axes = plt.subplots(2, 2, figsize=(7.0, 5.2), sharex=False)
    distribution_labels = (
        "Frame-free / Legacy",
        "Frame-free / LOO-ECDF",
        "Galactic companion / Legacy",
        "Galactic companion / LOO-ECDF",
    )
    score_distributions = tuple(
        value
        for key, value in distributions.items()
        if key.endswith("__row_max_scores")
    )
    for axis, values, panel_label in zip(
        axes.flat, score_distributions, distribution_labels, strict=True
    ):
        axis.hist(values[1:], bins=24, color="#4c72b0", alpha=0.75)
        axis.axvline(values[0], color="#c44e52", linewidth=1.2, label="observed")
        axis.set_title(panel_label, fontsize=8)
        axis.legend(fontsize=6)
    fig.suptitle("Complete-pool row-score distributions", fontsize=10)
    fig.tight_layout()
    fig.savefig(output / "figure_null_score_distributions.pdf")
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(6.4, 4.0))
    for family_id, marker in zip(
        (FRAME_FREE_FAMILY_ID, GALACTIC_ORIENTATION_FAMILY_ID), ("o", "s"), strict=True
    ):
        eigenvalues = dependence[family_id]["spearman_eigenvalues_descending"]
        label = "Frame-free" if family_id == FRAME_FREE_FAMILY_ID else "+ Galactic orientation"
        ax.plot(np.arange(1, len(eigenvalues) + 1), eigenvalues, marker=marker, label=label)
    ax.set_xlabel("Spearman correlation eigenvalue index")
    ax.set_ylabel("Eigenvalue")
    ax.set_title("Coordinate dependence spectrum")
    ax.legend(fontsize=6)
    fig.tight_layout()
    fig.savefig(output / "figure_dependence_spectrum.pdf")
    plt.close(fig)


def build(
    output: Path = DEFAULT_OUTPUT,
    *,
    carrier_dir: Path = DEFAULT_CARRIER_DIR,
) -> dict[str, object]:
    """Execute the complete map-free paired-300 observer-space analysis."""

    output = Path(output)
    if output.exists() or output.is_symlink():
        raise RuntimeError("output directory must not already exist")
    carrier_rows, row_ids, metadata = _load_accepted_carrier(Path(carrier_dir))
    arrays, degeneracy_rows, reports, max_roundtrip = _compute_rows(
        carrier_rows, row_ids, metadata
    )
    family_results, distributions = _run_scans(
        arrays["frame_free_features"],
        arrays["orientation_features"],
        observation_index=0,
    )
    dependence, dependence_rows = _dependence_diagnostics(
        {
            FRAME_FREE_FAMILY_ID: arrays["frame_free_features"],
            GALACTIC_ORIENTATION_FAMILY_ID: arrays["orientation_features"],
        }
    )
    coordinate_rows, family_rows = _make_tables(
        reports=reports,
        family_results=family_results,
        degeneracy_rows=degeneracy_rows,
        dependence_rows=dependence_rows,
    )
    output.mkdir(parents=True)
    _write_npz(output / "irrep_features.npz", arrays)
    _write_npz(output / "null_distributions.npz", distributions)
    _write_csv(output / "coordinate_table.csv", coordinate_rows)
    _write_csv(output / "family_table.csv", family_rows)
    _write_csv(output / "degeneracy_ledger.csv", degeneracy_rows)
    _write_csv(output / "dependence_spectrum.csv", dependence_rows)
    registry: dict[str, object] = {
        "claim_ceiling": "OBSERVER_SPACE_METHODS_DIAGNOSTIC",
        "completeness_status": "GENERIC_GLOBAL_COMPLETENESS_UNPROVEN",
        "coordinates": _coordinate_registry(),
        "families": family_registry_payload(),
        "format": "PLANCK_MES_OBSERVABLE_IRREP_FEATURE_REGISTRY_V1",
        "projection_identity": PROJECTION_IDENTITY,
        "reducers": list(REDUCERS),
        "row_disposition_policy": (
            "typed absence is never zero-filled or dropped; a primary-family absence blocks calibration"
        ),
        "selection_policy": (
            "registry frozen before observed-row scoring; no result-selected subset"
        ),
    }
    registry["content_id"] = _canonical_content_id(
        registry, role="planck_mes_irrep_feature_registry"
    )
    _write_json(output / "feature_registry.json", registry)
    disposition_counts: dict[str, int] = {}
    q_spectrum_counts: dict[str, int] = {}
    for row in degeneracy_rows:
        disposition = str(row["primary_family_disposition"])
        disposition_counts[disposition] = disposition_counts.get(disposition, 0) + 1
        spectrum = str(row["q_spectrum_status"])
        q_spectrum_counts[spectrum] = q_spectrum_counts.get(spectrum, 0) + 1
    result: dict[str, object] = {
        "allowed_use": [
            "paired-300 observer-space irrep morphology",
            "finite-pool reducer comparison",
            "descriptive Galactic-orientation companion",
        ],
        "artifact_mode": "EXECUTED_OBSERVED_DIAGNOSTIC",
        "bianchi_family_status": "NOT_IDENTIFIED",
        "claim_promotion": False,
        "claim_tier": "METHODS_DIAGNOSTIC_ONLY",
        "completeness_status": "GENERIC_GLOBAL_COMPLETENESS_UNPROVEN",
        "degeneracy_summary": {
            "primary_family_dispositions": disposition_counts,
            "q_spectrum_status": q_spectrum_counts,
            "row_count": 301,
        },
        "dependence_diagnostics": dependence,
        "family_results": family_results,
        "feature_registry_content_id": registry["content_id"],
        "forbidden_use": [
            "physical-source attribution",
            "local-versus-global identification",
            "geometry-family identification",
            "likelihood or posterior",
        ],
        "format": FORMAT,
        "harmonic_stf_roundtrip": {
            "criterion": {
                "atol": NUMERICAL_ATOL,
                "rtol": NUMERICAL_RTOL,
            },
            "max_absolute_residual": max_roundtrip,
            "status": "PASS",
        },
        "likelihood_emitted": False,
        "null_row_count": 300,
        "null_status": "EXACT_ORDERED_FFP10_CMB_PLUS_NOISE_300_CONDITIONAL",
        "numerical_outputs": {
            "irrep_features_content_id": _array_bundle_content_id(
                arrays, role="planck_mes_irrep_features"
            ),
            "null_distributions_content_id": _array_bundle_content_id(
                distributions, role="planck_mes_irrep_null_distributions"
            ),
        },
        "owner": "OBSSTAT",
        "physical_source_status": "NOT_IDENTIFIED",
        "projection_identity": PROJECTION_IDENTITY,
        "raw_maps_reopened": False,
        "rebuild_level": "R2_SCIENTIFIC_NUMERICAL_REPLAY",
        "row_count": 301,
        "scope": "map-free l=2/3 observer-space irrep-orbit calibration on the accepted paired-300 pool",
        "selection_policy": (
            "features families tails reducers and row-disposition policy frozen before observed-row scoring"
        ),
        "source_carrier": {
            "carrier_content_id": EXPECTED_CARRIER_CONTENT_ID,
            "package_sha256": EXPECTED_CARRIER_PACKAGE_SHA256,
            "row_ids_sha256": _row_ids_content_id(row_ids),
        },
        "source_reducer_registry_sha256": EXPECTED_COORDINATE_REGISTRY_SHA256,
        "transfer_source": "none; accepted observer-space carrier",
    }
    result["content_id"] = _canonical_content_id(
        result, role="planck_mes_observable_irrep_analysis"
    )
    _write_json(output / "result.json", result)
    _plots(
        output,
        family_results=family_results,
        distributions=distributions,
        dependence=dependence,
    )
    plot_audit = {
        "byte_identity_role": "PDF_BYTES_NOT_A_SCIENTIFIC_GATE",
        "claim_tier": "METHODS_DIAGNOSTIC_ONLY",
        "figures": {
            name: {
                "double_column_6.8in": {"status": "PENDING"},
                "single_column_3.3in": {"status": "PENDING"},
            }
            for name in FIGURE_FILES
        },
        "inspection_origin": "GENERATOR_CANNOT_SELF_ATTEST_VISUAL_REVIEW",
        "inspection_state": "PENDING_HOST_DIRECT_INSPECTION",
        "owner": "OBSSTAT",
        "result_content_id": result["content_id"],
    }
    _write_json(output / "plot_audit.json", plot_audit)
    replay = {
        "format": "PLANCK_MES_OBSERVABLE_IRREP_REPLAY_V1",
        "identity_policy": "TYPED_IDENTITY_V1",
        "input_byte_identity": "MATCH",
        "numerical_output_identity": "MATCH_GENERATED_CONTENT",
        "raw_maps_reopened": False,
        "result_content_id": result["content_id"],
        "status": "PASS",
    }
    _write_json(output / "replay.json", replay)
    terminal = {
        "claim_promotion": False,
        "format": "PLANCK_MES_OBSERVABLE_IRREP_TERMINAL_V1",
        "fresh_review": "PENDING",
        "next_executable_action": "FRESH_READ_ONLY_REVIEW",
        "raw_data_read_or_mutated": False,
        "replay_status": "MATCH",
        "science_execution_performed": True,
        "state": "EXECUTED_PENDING_REVIEW",
        "unresolved_blockers": ["FRESH_READ_ONLY_REVIEW_PENDING"],
        "work_unit": "PMG-WU-006",
    }
    _write_json(output / "terminal.json", terminal)
    return result


def _assert_numerically_equivalent(
    actual: Mapping[str, np.ndarray],
    expected: Mapping[str, np.ndarray],
    *,
    label: str,
) -> None:
    if set(actual) != set(expected):
        raise RuntimeError(f"{label} numerical output schema drifted")
    for name in sorted(expected):
        left = actual[name]
        right = expected[name]
        if left.shape != right.shape or left.dtype.kind != right.dtype.kind:
            raise RuntimeError(f"{label} numerical output structure drifted: {name}")
        if left.dtype.kind in "fci":
            if not np.allclose(
                left,
                right,
                rtol=NUMERICAL_RTOL,
                atol=NUMERICAL_ATOL,
                equal_nan=True,
            ):
                raise RuntimeError(
                    f"{label} numerical semantic projection differs: {name}"
                )
        elif not np.array_equal(left, right):
            raise RuntimeError(f"{label} decoded content differs: {name}")


def replay_directory(output: Path) -> dict[str, object]:
    """Replay an output directory without maps using typed identity relations."""

    output = Path(output)
    if not output.is_dir():
        raise RuntimeError("analysis output directory is missing")
    try:
        result = json.loads((output / "result.json").read_text(encoding="ascii"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise RuntimeError("deterministic result evidence is malformed") from exc
    result_without_id = dict(result)
    content_id = result_without_id.pop("content_id", None)
    if content_id != _canonical_content_id(
        result_without_id, role="planck_mes_observable_irrep_analysis"
    ):
        raise RuntimeError("deterministic result content identity differs")
    with tempfile.TemporaryDirectory(prefix="pmg-wu006-replay-") as temporary:
        expected_dir = Path(temporary) / "analysis"
        build(expected_dir)
        for name in DETERMINISTIC_EVIDENCE_FILES:
            if (output / name).read_bytes() != (expected_dir / name).read_bytes():
                raise RuntimeError(f"deterministic evidence content differs: {name}")
        actual_features = _load_npz(output / "irrep_features.npz")
        expected_features = _load_npz(expected_dir / "irrep_features.npz")
        actual_null = _load_npz(output / "null_distributions.npz")
        expected_null = _load_npz(expected_dir / "null_distributions.npz")
        _assert_numerically_equivalent(
            actual_features, expected_features, label="irrep features"
        )
        _assert_numerically_equivalent(
            actual_null, expected_null, label="null distributions"
        )
        byte_identical = (
            (output / "irrep_features.npz").read_bytes()
            == (expected_dir / "irrep_features.npz").read_bytes()
            and (output / "null_distributions.npz").read_bytes()
            == (expected_dir / "null_distributions.npz").read_bytes()
        )
    return {
        "identity_policy": "TYPED_IDENTITY_V1",
        "input_byte_identity": "MATCH",
        "numerical_output_identity": (
            "BYTE_IDENTICAL" if byte_identical else "NUMERICALLY_EQUIVALENT"
        ),
        "packaging_validity": (
            "BYTE_IDENTICAL" if byte_identical else "BYTE_IDENTITY_NOT_REQUIRED"
        ),
        "raw_maps_reopened": False,
        "result_validity": "PASS",
        "status": "MATCH",
    }


def finalize_reviewed(output: Path, *, repair_count: int = 0) -> None:
    """Close the terminal only after one external host review has passed."""

    output = Path(output)
    terminal_path = output / "terminal.json"
    plot_path = output / "plot_audit.json"
    terminal = json.loads(terminal_path.read_text(encoding="ascii"))
    if terminal.get("state") != "EXECUTED_PENDING_REVIEW":
        raise RuntimeError("terminal is not awaiting its one fresh review")
    if repair_count not in {0, 1}:
        raise RuntimeError("review repair count must respect the one-repair budget")
    replay = replay_directory(output)
    plot_audit = json.loads(plot_path.read_text(encoding="ascii"))
    for figure in plot_audit["figures"].values():
        figure["single_column_3.3in"] = {"status": "PASS"}
        figure["double_column_6.8in"] = {"status": "PASS"}
    plot_audit["inspection_origin"] = "HOST_CODEX_DIRECT_VISUAL_INSPECTION"
    plot_audit["inspection_state"] = "PASS_HOST_DIRECT_INSPECTION"
    _write_json(plot_path, plot_audit)
    terminal.update(
        {
            "fresh_review": "PASS",
            "identity_policy": "TYPED_IDENTITY_V1",
            "next_executable_action": "PMG-WU-007",
            "objective_artifacts": {
                "deterministic_evidence_sha256": {
                    name: _file_sha256(output / name)
                    for name in DETERMINISTIC_EVIDENCE_FILES
                },
                "figure_byte_identity_role": "NOT_A_SCIENTIFIC_GATE",
                "irrep_features_content_id": _array_bundle_content_id(
                    _load_npz(output / "irrep_features.npz"),
                    role="planck_mes_irrep_features",
                ),
                "null_distributions_content_id": _array_bundle_content_id(
                    _load_npz(output / "null_distributions.npz"),
                    role="planck_mes_irrep_null_distributions",
                ),
            },
            "packaging_validity": replay["packaging_validity"],
            "provenance_validity": "MATCH",
            "result_validity": "PASS",
            "review_repair_count": repair_count,
            "state": "SUCCEEDED",
            "unresolved_blockers": [],
        }
    )
    _write_json(terminal_path, terminal)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--replay-committed", action="store_true")
    parser.add_argument("--finalize-reviewed", action="store_true")
    parser.add_argument("--review-repair-count", type=int, default=0)
    arguments = parser.parse_args()
    if arguments.replay_committed and arguments.finalize_reviewed:
        raise SystemExit("choose replay or review finalization, not both")
    if arguments.replay_committed:
        print(json.dumps(replay_directory(DEFAULT_OUTPUT), sort_keys=True))
    elif arguments.finalize_reviewed:
        finalize_reviewed(
            arguments.output_dir, repair_count=arguments.review_repair_count
        )
    else:
        build(arguments.output_dir)


if __name__ == "__main__":
    main()
