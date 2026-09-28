"""Deterministic artifact writer for PMG-WU-011 Task-7C.

The artifact layer is kept separate from the source-band construction so that
matrix generation, serialization, plots, and verification can be audited
independently.  It emits synthetic local-observer response diagnostics only.
"""

from __future__ import annotations

import csv
from dataclasses import dataclass
import hashlib
import io
import json
from pathlib import Path
import re
from typing import TYPE_CHECKING, Mapping
import zipfile

import numpy as np

if TYPE_CHECKING:  # pragma: no cover - typing only
    from .processed_boost_nuisance_span import Task7CAtlas


_ARTIFACT_SCHEMA = "HTT_WU011_TASK7C_ARTIFACT_SET_V1"
_SAFE_KEY_RE = re.compile(r"[^A-Za-z0-9_.-]+")
_EXPECTED_ARTIFACTS = (
    "terminal.json",
    "summary.json",
    "directional_nuisance_span.csv",
    "source_block_norms.csv",
    "cutoff_convergence.csv",
    "matrices.npz",
    "survivor_rank_vs_cutoff.png",
    "surviving_fraction_vs_cutoff.png",
    "principal_angle_vs_cutoff.png",
    "source_block_decay.png",
    "resolution_comparison.png",
)


def _processed_error(message: str) -> Exception:
    from .processed_boost_response import ProcessedBoostError

    return ProcessedBoostError(message)


def _canonical_json(payload: Mapping[str, object]) -> bytes:
    return json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
        allow_nan=False,
    ).encode("ascii")


def _write_json(path: Path, payload: Mapping[str, object]) -> None:
    path.write_bytes(_canonical_json(payload) + b"\n")


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _safe_key(value: str) -> str:
    key = _SAFE_KEY_RE.sub("_", value).strip("_")
    if not key:
        raise _processed_error("Task-7C matrix key became empty")
    return key


def _write_csv(path: Path, fieldnames: tuple[str, ...], rows: list[dict[str, object]]) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, lineterminator="\n")
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def _npy_bytes(array: np.ndarray) -> bytes:
    stream = io.BytesIO()
    np.lib.format.write_array(
        stream,
        np.ascontiguousarray(array),
        allow_pickle=False,
    )
    return stream.getvalue()


def _write_deterministic_npz(path: Path, arrays: Mapping[str, np.ndarray]) -> None:
    with zipfile.ZipFile(
        path,
        mode="w",
        compression=zipfile.ZIP_DEFLATED,
        compresslevel=9,
    ) as archive:
        for key in sorted(arrays):
            info = zipfile.ZipInfo(f"{_safe_key(key)}.npy")
            info.date_time = (1980, 1, 1, 0, 0, 0)
            info.compress_type = zipfile.ZIP_DEFLATED
            info.create_system = 3
            info.external_attr = 0o644 << 16
            archive.writestr(info, _npy_bytes(arrays[key]))


def _plot_payload(atlas: "Task7CAtlas", target: Path) -> None:
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    primary = atlas.cases[0]

    def _series(attribute: str):
        result: dict[str, tuple[list[int], list[float]]] = {}
        for direction_id in sorted({item.direction_id for item in primary.directional_results}):
            rows = sorted(
                (
                    item
                    for item in primary.directional_results
                    if item.direction_id == direction_id
                ),
                key=lambda item: item.source_cutoff,
            )
            x = [item.source_cutoff for item in rows]
            if attribute == "rank":
                y = [float(item.geometry.surviving_rank) for item in rows]
            elif attribute == "fraction":
                y = [item.geometry.surviving_frobenius_fraction for item in rows]
            elif attribute == "angle":
                y = [item.geometry.minimum_principal_angle_degrees for item in rows]
            else:  # pragma: no cover - internal dispatch guard
                raise ValueError(attribute)
            result[direction_id] = (x, y)
        return result

    for filename, attribute, ylabel, title in (
        (
            "survivor_rank_vs_cutoff.png",
            "rank",
            "Surviving low-source rank",
            "Task-7C survivor rank versus source cutoff",
        ),
        (
            "surviving_fraction_vs_cutoff.png",
            "fraction",
            "Surviving Frobenius fraction",
            "Task-7C surviving response fraction",
        ),
        (
            "principal_angle_vs_cutoff.png",
            "angle",
            "Minimum principal angle (deg)",
            "Task-7C low/high image principal angle",
        ),
    ):
        plt.figure(figsize=(7.2, 4.8))
        for direction_id, (x, y) in _series(attribute).items():
            plt.plot(x, y, marker="o", label=direction_id)
        plt.xlabel("High-source cutoff L")
        plt.ylabel(ylabel)
        plt.title(title)
        plt.legend(ncol=2)
        plt.tight_layout()
        plt.savefig(target / filename, dpi=180, metadata={"Software": "htt_base Task-7C"})
        plt.close()

    largest_cutoff = max(primary.source_cutoffs)
    selected = primary.result("D111", largest_cutoff)
    plt.figure(figsize=(7.2, 4.8))
    plt.plot(
        [item.source_ell for item in selected.block_norms],
        [item.metric_frobenius_norm for item in selected.block_norms],
        marker="o",
        label="Frobenius norm",
    )
    plt.plot(
        [item.source_ell for item in selected.block_norms],
        [item.metric_operator_norm for item in selected.block_norms],
        marker="o",
        label="Operator norm",
    )
    plt.xlabel("Source multipole ell")
    plt.ylabel("Directional metric norm")
    plt.title("Task-7C source-block decay (D111)")
    plt.legend()
    plt.tight_layout()
    plt.savefig(
        target / "source_block_decay.png",
        dpi=180,
        metadata={"Software": "htt_base Task-7C"},
    )
    plt.close()

    case_labels: list[str] = []
    case_values: list[float] = []
    for case in atlas.cases:
        cutoff = max(case.source_cutoffs)
        fractions = [
            case.result(direction_id, cutoff).geometry.surviving_frobenius_fraction
            for direction_id in sorted({item.direction_id for item in case.directional_results})
        ]
        case_labels.append(case.case_id)
        case_values.append(float(np.median(fractions)))
    plt.figure(figsize=(8.2, 4.8))
    plt.plot(range(len(case_labels)), case_values, marker="o")
    plt.xticks(range(len(case_labels)), case_labels, rotation=25, ha="right")
    plt.ylabel("Median surviving Frobenius fraction")
    plt.title("Task-7C registered operator/resolution controls")
    plt.tight_layout()
    plt.savefig(
        target / "resolution_comparison.png",
        dpi=180,
        metadata={"Software": "htt_base Task-7C"},
    )
    plt.close()


@dataclass(frozen=True)
class Task7CArtifactBundle:
    target: Path
    files: tuple[str, ...]
    manifest_sha256: str


def write_task7c_artifacts(atlas: "Task7CAtlas", target: str | Path) -> Task7CArtifactBundle:
    """Write and checksum the deterministic Task-7C evidence surface."""

    from .processed_boost_nuisance_span import Task7CAtlas

    if type(atlas) is not Task7CAtlas:
        raise _processed_error("Task-7C artifact writer requires an exact atlas")
    target_path = Path(target)
    if target_path.exists() and any(target_path.iterdir()):
        raise _processed_error("Task-7C artifact target must be absent or empty")
    target_path.mkdir(parents=True, exist_ok=True)

    claim_boundary = {
        "raw_planck_execution": False,
        "observed_rank": False,
        "empirical_beta_fit": False,
        "boost_subtraction": False,
        "global_tilt": False,
        "polarization_result": False,
        "bianchi_attribution": False,
        "claim_promotion": False,
        "merge_authorized": False,
    }
    terminal_payload = {
        "schema": _ARTIFACT_SCHEMA,
        "source_revision": atlas.source_revision,
        "profile": atlas.profile,
        "terminal": atlas.terminal.value,
        "atlas_content_id": atlas.content_id,
        "claim_boundary": claim_boundary,
    }
    _write_json(target_path / "terminal.json", terminal_payload)

    summary_payload = atlas.scalar_record()
    summary_payload["case_records"] = [
        {
            "case_id": case.case_id,
            "nside": case.nside,
            "processing_lmax": case.processing_lmax,
            "mask_kind": case.mask_kind,
            "transfer_kind": case.transfer_kind,
            "source_cutoffs": list(case.source_cutoffs),
            "operator_id": case.operator_id,
            "jacobian_id": case.jacobian_id,
            "content_id": case.content_id,
        }
        for case in atlas.cases
    ]
    _write_json(target_path / "summary.json", summary_payload)

    directional_rows: list[dict[str, object]] = []
    block_rows: list[dict[str, object]] = []
    arrays: dict[str, np.ndarray] = {}
    for case in atlas.cases:
        for result in case.directional_results:
            directional_rows.append(
                {
                    "case_id": case.case_id,
                    "nside": case.nside,
                    "processing_lmax": case.processing_lmax,
                    "direction_id": result.direction_id,
                    "source_cutoff": result.source_cutoff,
                    "low_rank": result.geometry.low_rank,
                    "high_rank": result.geometry.high_rank,
                    "surviving_rank": result.geometry.surviving_rank,
                    "surviving_frobenius_fraction": repr(
                        result.geometry.surviving_frobenius_fraction
                    ),
                    "minimum_principal_angle_degrees": repr(
                        result.geometry.minimum_principal_angle_degrees
                    ),
                    "maximum_principal_angle_degrees": repr(
                        result.geometry.maximum_principal_angle_degrees
                    ),
                    "last_block_frobenius_fraction": repr(
                        result.last_block_frobenius_fraction
                    ),
                    "last_block_operator_fraction": repr(
                        result.last_block_operator_fraction
                    ),
                    "numerical_floor_control": int(result.numerical_floor_control),
                    "content_id": result.content_id,
                }
            )
            for block in result.block_norms:
                block_rows.append(
                    {
                        "case_id": case.case_id,
                        "direction_id": result.direction_id,
                        "source_cutoff": result.source_cutoff,
                        "source_ell": block.source_ell,
                        "metric_frobenius_norm": repr(block.metric_frobenius_norm),
                        "metric_operator_norm": repr(block.metric_operator_norm),
                        "block_id": block.block_id,
                    }
                )
            prefix = _safe_key(
                f"{case.case_id}_{result.direction_id}_L{result.source_cutoff}"
            )
            arrays[f"{prefix}_low"] = result.low_matrix
            arrays[f"{prefix}_high"] = result.high_matrix
            arrays[f"{prefix}_surviving_low"] = result.geometry.surviving_low_matrix
            arrays[f"{prefix}_nuisance_projector"] = result.geometry.nuisance_projector

    _write_csv(
        target_path / "directional_nuisance_span.csv",
        (
            "case_id",
            "nside",
            "processing_lmax",
            "direction_id",
            "source_cutoff",
            "low_rank",
            "high_rank",
            "surviving_rank",
            "surviving_frobenius_fraction",
            "minimum_principal_angle_degrees",
            "maximum_principal_angle_degrees",
            "last_block_frobenius_fraction",
            "last_block_operator_fraction",
            "numerical_floor_control",
            "content_id",
        ),
        directional_rows,
    )
    _write_csv(
        target_path / "source_block_norms.csv",
        (
            "case_id",
            "direction_id",
            "source_cutoff",
            "source_ell",
            "metric_frobenius_norm",
            "metric_operator_norm",
            "block_id",
        ),
        block_rows,
    )
    _write_csv(
        target_path / "cutoff_convergence.csv",
        (
            "direction_id",
            "lower_cutoff",
            "upper_cutoff",
            "lower_high_rank",
            "upper_high_rank",
            "lower_surviving_rank",
            "upper_surviving_rank",
            "lower_surviving_fraction",
            "upper_surviving_fraction",
            "upper_last_frobenius_fraction",
            "upper_last_operator_fraction",
        ),
        [
            {
                "direction_id": record.direction_id,
                "lower_cutoff": record.lower_cutoff,
                "upper_cutoff": record.upper_cutoff,
                "lower_high_rank": record.lower_high_rank,
                "upper_high_rank": record.upper_high_rank,
                "lower_surviving_rank": record.lower_surviving_rank,
                "upper_surviving_rank": record.upper_surviving_rank,
                "lower_surviving_fraction": repr(record.lower_surviving_fraction),
                "upper_surviving_fraction": repr(record.upper_surviving_fraction),
                "upper_last_frobenius_fraction": repr(
                    record.upper_last_frobenius_fraction
                ),
                "upper_last_operator_fraction": repr(
                    record.upper_last_operator_fraction
                ),
            }
            for record in atlas.convergence_records
        ],
    )
    _write_deterministic_npz(target_path / "matrices.npz", arrays)
    _plot_payload(atlas, target_path)

    for filename in _EXPECTED_ARTIFACTS:
        if not (target_path / filename).is_file():
            raise _processed_error(f"Task-7C artifact is absent: {filename}")
    manifest_lines = [
        f"{_sha256(target_path / filename)}  {filename}"
        for filename in sorted(_EXPECTED_ARTIFACTS)
    ]
    manifest_path = target_path / "SHA256SUMS"
    manifest_path.write_text("\n".join(manifest_lines) + "\n", encoding="ascii")
    return Task7CArtifactBundle(
        target=target_path,
        files=tuple(sorted(_EXPECTED_ARTIFACTS + ("SHA256SUMS",))),
        manifest_sha256=_sha256(manifest_path),
    )


def verify_task7c_artifacts(target: str | Path) -> dict[str, object]:
    """Verify every manifest entry and the typed Task-7C terminal."""

    target_path = Path(target)
    manifest_path = target_path / "SHA256SUMS"
    if not manifest_path.is_file():
        raise _processed_error("Task-7C SHA256SUMS is absent")
    entries: dict[str, str] = {}
    for raw_line in manifest_path.read_text(encoding="ascii").splitlines():
        digest, separator, filename = raw_line.partition("  ")
        if not separator or len(digest) != 64 or filename in entries:
            raise _processed_error("Task-7C manifest syntax is invalid")
        entries[filename] = digest
    if set(entries) != set(_EXPECTED_ARTIFACTS):
        raise _processed_error("Task-7C manifest file registry differs")
    for filename, expected in entries.items():
        path = target_path / filename
        if not path.is_file() or _sha256(path) != expected:
            raise _processed_error(f"Task-7C artifact hash mismatch: {filename}")

    terminal = json.loads((target_path / "terminal.json").read_text(encoding="ascii"))
    summary = json.loads((target_path / "summary.json").read_text(encoding="ascii"))
    for field in ("source_revision", "profile", "terminal"):
        if terminal.get(field) != summary.get(field):
            raise _processed_error(f"Task-7C terminal/summary field differs: {field}")
    if terminal.get("atlas_content_id") != summary.get("content_id"):
        raise _processed_error("Task-7C atlas content identity differs")

    with np.load(target_path / "matrices.npz", allow_pickle=False) as matrices:
        if not matrices.files:
            raise _processed_error("Task-7C matrix archive is empty")
        for key in matrices.files:
            value = matrices[key]
            if value.ndim != 2 or not np.all(np.isfinite(value)):
                raise _processed_error("Task-7C matrix archive contains invalid data")
    png_signature = b"\x89PNG\r\n\x1a\n"
    for filename in _EXPECTED_ARTIFACTS:
        if filename.endswith(".png") and not (target_path / filename).read_bytes().startswith(
            png_signature
        ):
            raise _processed_error(f"Task-7C PNG signature differs: {filename}")
    return {
        "schema": _ARTIFACT_SCHEMA,
        "source_revision": terminal["source_revision"],
        "profile": terminal["profile"],
        "terminal": terminal["terminal"],
        "atlas_content_id": terminal["atlas_content_id"],
        "manifest_entries": len(entries),
        "manifest_sha256": _sha256(manifest_path),
    }


__all__ = [
    "Task7CArtifactBundle",
    "verify_task7c_artifacts",
    "write_task7c_artifacts",
]
