"""Machine-readable and plot-based audit artifacts for Task-7C controls."""

from __future__ import annotations

import csv
import hashlib
import json
import math
from pathlib import Path
from typing import Mapping

import numpy as np

from .processed_boost_matched_control_adjudication import (
    MatchedControlAdjudicationError,
    adjudicate_rank_records,
)


_ARTIFACT_SCHEMA = "HTT_WU011_TASK7C_MATCHED_CONTROL_ADJUDICATION_ARTIFACT_V1"
_EXPECTED_FILES = (
    "adjudication.json",
    "nominal_rank_table.csv",
    "decision_status_matrix.png",
    "saturation_margin_vs_cutoff.png",
)


class MatchedControlArtifactError(ValueError):
    """Raised when adjudication artifacts are incomplete or inconsistent."""


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _canonical_json(payload: Mapping[str, object]) -> bytes:
    return json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
        allow_nan=False,
    ).encode("ascii")


def _read_rows(path: Path) -> list[dict[str, object]]:
    if not path.is_file():
        raise MatchedControlArtifactError("rank-sensitivity CSV is absent")
    with path.open("r", encoding="utf-8", newline="") as handle:
        rows = [dict(row) for row in csv.DictReader(handle)]
    if not rows:
        raise MatchedControlArtifactError("rank-sensitivity CSV is empty")
    return rows


def _as_float(value: object, *, label: str) -> float:
    try:
        result = float(value)
    except (TypeError, ValueError) as exc:
        raise MatchedControlArtifactError(f"{label} is not finite") from exc
    if not math.isfinite(result):
        raise MatchedControlArtifactError(f"{label} is not finite")
    return result


def _as_int(value: object, *, label: str) -> int:
    try:
        result = int(value)
    except (TypeError, ValueError) as exc:
        raise MatchedControlArtifactError(f"{label} is not an integer") from exc
    return result


def _parse_optional_bool(value: object) -> bool | None:
    if value in (None, ""):
        return None
    normalized = str(value).strip().lower()
    if normalized == "true":
        return True
    if normalized == "false":
        return False
    raise MatchedControlArtifactError("decision flag is not boolean")


def _matrix_key(source_case_id: str, direction_id: str, cutoff: int) -> str:
    return f"{source_case_id}_{direction_id}_L{cutoff}_high"


def write_matched_control_adjudication_artifacts(
    *,
    rank_sensitivity_csv: str | Path,
    matrices_npz: str | Path,
    target: str | Path,
    nominal_control_factor: float = 5.0,
) -> dict[str, object]:
    """Adjudicate one receipt and render ambiguity instead of hiding it."""

    rank_path = Path(rank_sensitivity_csv)
    matrix_path = Path(matrices_npz)
    target_path = Path(target)
    if target_path.exists() and any(target_path.iterdir()):
        raise MatchedControlArtifactError(
            "matched-control adjudication target must be absent or empty"
        )
    target_path.mkdir(parents=True, exist_ok=True)

    rows = _read_rows(rank_path)
    try:
        adjudication = adjudicate_rank_records(
            rows,
            nominal_control_factor=nominal_control_factor,
        )
    except MatchedControlAdjudicationError as exc:
        raise MatchedControlArtifactError(
            f"matched-control adjudication failed: {exc}"
        ) from exc

    nominal = [
        row
        for row in rows
        if _as_float(
            row["control_safety_factor"],
            label="control safety factor",
        )
        == nominal_control_factor
    ]
    if not nominal:
        raise MatchedControlArtifactError("nominal matched-control slice is absent")

    if not matrix_path.is_file():
        raise MatchedControlArtifactError("Task-7C matrix archive is absent")
    archive = np.load(matrix_path, allow_pickle=False)
    table: list[dict[str, object]] = []
    for row in nominal:
        direction = str(row["direction_id"])
        cutoff = _as_int(row["source_cutoff"], label="source cutoff")
        source_case_id = str(row.get("source_case_id", ""))
        key = _matrix_key(source_case_id, direction, cutoff)
        if key not in archive.files:
            raise MatchedControlArtifactError(
                f"Task-7C source matrix is absent: {key}"
            )
        matrix = np.asarray(archive[key], dtype=np.float64)
        singular = np.linalg.svd(matrix, compute_uv=False)
        if singular.size != matrix.shape[0] or not np.all(np.isfinite(singular)):
            raise MatchedControlArtifactError("Task-7C singular spectrum is invalid")
        threshold = _as_float(row["high_threshold"], label="high threshold")
        if threshold <= 0.0:
            raise MatchedControlArtifactError("high threshold is not positive")
        margin = float(singular[-1] / threshold)
        status = str(row["rank_status"])
        containment = _parse_optional_bool(row["containment_witness"])
        if status == "AMBIGUOUS":
            decision_label = "A"
            decision_code = 0
        elif containment is True:
            decision_label = "C"
            decision_code = 2
        elif containment is False:
            decision_label = "S"
            decision_code = 1
        else:
            raise MatchedControlArtifactError("resolved row has no containment flag")
        table.append(
            {
                "direction_id": direction,
                "source_cutoff": cutoff,
                "control_safety_factor": nominal_control_factor,
                "rank_status": status,
                "high_rank": _as_int(row["high_rank"], label="high rank"),
                "surviving_rank": row["surviving_rank"],
                "augmented_rank_increment": row["augmented_rank_increment"],
                "containment_witness": row["containment_witness"],
                "smallest_singular_value": repr(float(singular[-1])),
                "high_threshold": repr(threshold),
                "smallest_singular_over_threshold": repr(margin),
                "control_operator_norm": row["control_operator_norm"],
                "cutsky_operator_norm": row["cutsky_operator_norm"],
                "control_to_cutsky_operator_ratio": row[
                    "control_to_cutsky_operator_ratio"
                ],
                "decision_label": decision_label,
                "decision_code": decision_code,
            }
        )

    table.sort(key=lambda item: (int(item["source_cutoff"]), str(item["direction_id"])))
    margins = [float(item["smallest_singular_over_threshold"]) for item in table]
    best_index = int(np.argmax(margins))
    best = table[best_index]
    summary = dict(adjudication.to_payload())
    summary.update(
        {
            "artifact_schema": _ARTIFACT_SCHEMA,
            "nominal_smallest_singular_over_threshold_max": max(margins),
            "nominal_smallest_singular_over_threshold_min": min(margins),
            "best_saturation_margin": {
                "direction_id": best["direction_id"],
                "source_cutoff": best["source_cutoff"],
                "margin": float(best["smallest_singular_over_threshold"]),
            },
            "full_row_saturation_certified_by_current_threshold": all(
                margin > 2.0 for margin in margins
            ),
            "decision_labels": {
                "A": "rank ambiguous",
                "S": "resolved survivor present",
                "C": "resolved containment candidate",
            },
            "scientific_terminal_authorized": False,
            "claim_promotion": False,
        }
    )
    (target_path / "adjudication.json").write_bytes(
        _canonical_json(summary) + b"\n"
    )

    fieldnames = tuple(table[0])
    with (target_path / "nominal_rank_table.csv").open(
        "w",
        encoding="utf-8",
        newline="",
    ) as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, lineterminator="\n")
        writer.writeheader()
        writer.writerows(table)

    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    directions = tuple(dict.fromkeys(str(item["direction_id"]) for item in table))
    cutoffs = tuple(sorted({int(item["source_cutoff"]) for item in table}))
    matrix = np.full((len(directions), len(cutoffs)), np.nan, dtype=np.float64)
    labels = np.full((len(directions), len(cutoffs)), "", dtype=object)
    index = {
        (str(item["direction_id"]), int(item["source_cutoff"])): item
        for item in table
    }
    for i, direction in enumerate(directions):
        for j, cutoff in enumerate(cutoffs):
            item = index.get((direction, cutoff))
            if item is None:
                continue
            matrix[i, j] = int(item["decision_code"])
            labels[i, j] = str(item["decision_label"])

    plt.figure(figsize=(7.2, 4.8))
    image = plt.imshow(matrix, aspect="auto", vmin=0, vmax=2)
    plt.colorbar(image, ticks=(0, 1, 2), label="Decision code: 0=A, 1=S, 2=C")
    plt.xticks(range(len(cutoffs)), cutoffs)
    plt.yticks(range(len(directions)), directions)
    plt.xlabel("High-source cutoff L")
    plt.ylabel("Boost direction")
    plt.title(f"Task-7C matched-control rank decisions (s_ctrl={nominal_control_factor:g})")
    for i in range(len(directions)):
        for j in range(len(cutoffs)):
            if labels[i, j]:
                plt.text(j, i, labels[i, j], ha="center", va="center")
    plt.tight_layout()
    plt.savefig(
        target_path / "decision_status_matrix.png",
        dpi=180,
        metadata={"Software": "htt_base Task-7C matched-control adjudication"},
    )
    plt.close()

    plt.figure(figsize=(7.2, 4.8))
    for direction in directions:
        selected = [item for item in table if item["direction_id"] == direction]
        plt.semilogy(
            [int(item["source_cutoff"]) for item in selected],
            [float(item["smallest_singular_over_threshold"]) for item in selected],
            marker="o",
            label=direction,
        )
    plt.axhline(1.0, linestyle="--", label="threshold crossing")
    plt.axhline(2.0, linestyle=":", label="outside ambiguity shell")
    plt.xlabel("High-source cutoff L")
    plt.ylabel("Smallest singular value / high-rank threshold")
    plt.title(f"Task-7C full-row saturation margin (s_ctrl={nominal_control_factor:g})")
    plt.legend(ncol=2)
    plt.tight_layout()
    plt.savefig(
        target_path / "saturation_margin_vs_cutoff.png",
        dpi=180,
        metadata={"Software": "htt_base Task-7C matched-control adjudication"},
    )
    plt.close()

    manifest = target_path / "SHA256SUMS"
    manifest.write_text(
        "\n".join(
            f"{_sha256(target_path / filename)}  {filename}"
            for filename in sorted(_EXPECTED_FILES)
        )
        + "\n",
        encoding="ascii",
    )
    return {
        "terminal": adjudication.terminal.value,
        "content_id": adjudication.content_id,
        "manifest_sha256": _sha256(manifest),
        "nominal_ambiguous_count": adjudication.nominal_ambiguous_count,
        "nominal_resolved_count": adjudication.nominal_resolved_count,
        "best_saturation_margin": float(best["smallest_singular_over_threshold"]),
    }


def verify_matched_control_adjudication_artifacts(
    target: str | Path,
) -> dict[str, object]:
    """Verify hashes, scope locks, and the typed adjudication payload."""

    target_path = Path(target)
    manifest = target_path / "SHA256SUMS"
    if not manifest.is_file():
        raise MatchedControlArtifactError("adjudication SHA256SUMS is absent")
    entries: dict[str, str] = {}
    for line in manifest.read_text(encoding="ascii").splitlines():
        digest, separator, filename = line.partition("  ")
        if not separator or len(digest) != 64 or filename in entries:
            raise MatchedControlArtifactError("adjudication manifest syntax is invalid")
        entries[filename] = digest
    if set(entries) != set(_EXPECTED_FILES):
        raise MatchedControlArtifactError("adjudication manifest registry differs")
    for filename, digest in entries.items():
        path = target_path / filename
        if not path.is_file() or _sha256(path) != digest:
            raise MatchedControlArtifactError(f"adjudication hash mismatch: {filename}")
    payload = json.loads((target_path / "adjudication.json").read_text(encoding="ascii"))
    if payload.get("artifact_schema") != _ARTIFACT_SCHEMA:
        raise MatchedControlArtifactError("adjudication artifact schema differs")
    if payload.get("scientific_terminal_authorized") is not False:
        raise MatchedControlArtifactError("adjudication promoted a scientific terminal")
    if payload.get("claim_promotion") is not False:
        raise MatchedControlArtifactError("adjudication promoted a claim")
    return {
        "terminal": payload["terminal"],
        "content_id": payload["content_id"],
        "manifest_sha256": _sha256(manifest),
        "nominal_ambiguous_count": payload["nominal_ambiguous_count"],
        "nominal_resolved_count": payload["nominal_resolved_count"],
        "best_saturation_margin": payload["best_saturation_margin"]["margin"],
        "manifest_entries": len(entries),
    }


__all__ = [
    "MatchedControlArtifactError",
    "verify_matched_control_adjudication_artifacts",
    "write_matched_control_adjudication_artifacts",
]
