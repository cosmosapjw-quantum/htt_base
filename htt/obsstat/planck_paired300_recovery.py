"""Map-free recovery of the executed PMG-WU-005 carrier evidence.

The 301 maps have already been processed.  This module validates the private
execution ledger against PMG-WU-004, binds portable outputs and the frozen
scalar NPZ, classifies legacy checkpoints as non-authoritative when they were
not reused, and requires an external review receipt before final success.
"""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import re
import shutil
from typing import Mapping

from .planck_irrep_carrier import replay_planck_irrep_carrier
from .planck_paired300_evidence import (
    EvidenceBindingError,
    EXPECTED_ROW_IDS,
    finalize_terminal_after_fresh_review,
    load_wu004_intake_authority,
    validate_processed_input_ledger,
    verify_portable_artifact_manifest,
    write_pending_terminal,
    write_portable_artifact_manifest,
)


_SHA256 = re.compile(r"^sha256:[0-9a-f]{64}$")
PRE_REVIEW_ARTIFACTS = {
    "carrier": "carrier.npz",
    "metadata": "metadata.json",
    "scalar_closure": "scalar_closure.json",
    "input_identity_receipt": "input_identity_receipt.json",
    "leakage_receipt": "leakage_receipt.json",
    "replay": "replay.json",
}


class RecoveryError(RuntimeError):
    """Raised when the preserved result cannot be safely recovered."""


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for chunk in iter(lambda: handle.read(8 * 1024 * 1024), b""):
            digest.update(chunk)
    return "sha256:" + digest.hexdigest()


def _load_json(path: Path, *, label: str) -> dict[str, object]:
    try:
        value = json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise RecoveryError(f"{label} is not readable JSON") from exc
    if not isinstance(value, dict):
        raise RecoveryError(f"{label} must be a mapping")
    return value


def _write_new_json(path: Path, payload: Mapping[str, object]) -> None:
    path = Path(path)
    if path.exists() or path.is_symlink():
        raise RecoveryError(f"refusing to overwrite recovery evidence: {path}")
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.{os.getpid()}.tmp")
    try:
        temporary.write_text(
            json.dumps(
                payload,
                sort_keys=True,
                separators=(",", ":"),
                ensure_ascii=True,
                allow_nan=False,
            )
            + "\n",
            encoding="ascii",
        )
        os.replace(temporary, path)
    finally:
        temporary.unlink(missing_ok=True)


def _record(entry: Mapping[str, object]) -> dict[str, object]:
    return {
        "path": entry.get("path"),
        "resolved_path": entry.get("path"),
        "stat_identity": {
            key: entry.get(key) for key in ("device", "inode", "size", "mtime_ns")
        },
        "sha256": entry.get("sha256"),
    }


def ledger_from_private_execution_manifest(
    *,
    execution_manifest: Mapping[str, object],
    authority,
) -> tuple[dict[str, object], dict[str, object]]:
    """Convert the flat private manifest into the exact role/row graph."""

    if (
        execution_manifest.get("format")
        != "PLANCK_PR3_PAIRED300_PRIVATE_EXECUTION_MANIFEST_V1"
        or execution_manifest.get("row_count") != 301
        or execution_manifest.get("row_ids")
        != ["PLANCK-PR3-SMICA-OBSERVED", *EXPECTED_ROW_IDS]
        or execution_manifest.get("raw_data_mutation") is not False
        or not isinstance(execution_manifest.get("selected_input_identities"), list)
    ):
        raise RecoveryError("private execution manifest contract drifted")
    selected = execution_manifest["selected_input_identities"]
    observed = [entry for entry in selected if entry.get("role") == "observed_smica"]
    masks = [entry for entry in selected if entry.get("role") == "temperature_mask"]
    cmb = {entry.get("row_id"): entry for entry in selected if entry.get("role") == "cmb"}
    noise = {
        entry.get("row_id"): entry for entry in selected if entry.get("role") == "noise"
    }
    if (
        len(selected) != 602
        or len(observed) != 1
        or len(masks) != 1
        or set(cmb) != set(EXPECTED_ROW_IDS)
        or set(noise) != set(EXPECTED_ROW_IDS)
    ):
        raise RecoveryError("private execution role/row set is not exact")
    ledger = {
        "format": "PLANCK_PR3_PAIRED300_PROCESSED_INPUT_LEDGER_V1",
        "wu004_terminal_sha256": authority.terminal_sha256,
        "wu004_selected_manifest_sha256": authority.selected_manifest_sha256,
        "wu004_private_manifest_sha256": authority.private_manifest_sha256,
        "observed_map": _record(observed[0]),
        "common_mask": _record(masks[0]),
        "rows": [
            {
                "row_id": row_id,
                "cmb": _record(cmb[row_id]),
                "noise": _record(noise[row_id]),
            }
            for row_id in EXPECTED_ROW_IDS
        ],
    }
    report = validate_processed_input_ledger(ledger=ledger, authority=authority)
    return ledger, report


def prepare_recovery_evidence(
    *,
    output_dir: Path,
    frozen_scalar_package_path: Path,
    frozen_scalar_metadata_path: Path,
    wu004_portable_dir: Path,
    wu004_private_manifest_path: Path,
    execution_manifest_path: Path,
    checkpoint_dir: Path,
    private_evidence_dir: Path,
    base_git_head: str,
    implementation_git_head: str,
) -> dict[str, object]:
    """Prepare reviewable evidence without opening a raw map or checkpoint row."""

    output_dir = Path(output_dir)
    authority = load_wu004_intake_authority(
        portable_dir=Path(wu004_portable_dir),
        private_manifest_path=Path(wu004_private_manifest_path),
    )
    execution = _load_json(execution_manifest_path, label="private execution manifest")
    ledger, ledger_report = ledger_from_private_execution_manifest(
        execution_manifest=execution,
        authority=authority,
    )
    private_evidence_dir = Path(private_evidence_dir)
    private_evidence_dir.mkdir(parents=True, exist_ok=True)
    ledger_path = private_evidence_dir / "processed_input_ledger.json"
    _write_new_json(ledger_path, ledger)

    reused = execution.get("checkpoint_reused_count")
    if type(reused) is not int or reused < 0:
        raise RecoveryError("checkpoint reuse count is malformed")
    checkpoint_files = sorted(Path(checkpoint_dir).glob("*.npz"))
    if len(checkpoint_files) != 301:
        raise RecoveryError("preserved checkpoint inventory is not exact 301 rows")
    if reused != 0:
        raise RecoveryError(
            "unreviewed checkpoint evidence contributed to the scientific result"
        )
    checkpoint_disposition = {
        "format": "PLANCK_PR3_PAIRED300_CHECKPOINT_DISPOSITION_V1",
        "checkpoint_count": 301,
        "checkpoint_reused_count": 0,
        "result_dependency": False,
        "authority": "NONAUTHORITATIVE_POSTHOC_BOUND_NOT_REUSABLE",
        "required_future_action": (
            "Use the new bound-checkpoint writer or recompute a row before any future reuse"
        ),
        "raw_maps_reopened": False,
    }
    checkpoint_disposition_path = private_evidence_dir / "checkpoint_disposition.json"
    _write_new_json(checkpoint_disposition_path, checkpoint_disposition)

    frozen_metadata = _load_json(
        frozen_scalar_metadata_path, label="frozen scalar metadata"
    )
    declared_frozen_sha = frozen_metadata.get("package_sha256")
    if not isinstance(declared_frozen_sha, str) or _SHA256.fullmatch(
        declared_frozen_sha
    ) is None:
        raise RecoveryError("frozen scalar metadata lacks package SHA")
    if _sha256(Path(frozen_scalar_package_path)) != declared_frozen_sha:
        raise RecoveryError("frozen scalar NPZ byte authority drifted")
    carrier_metadata = _load_json(output_dir / "metadata.json", label="carrier metadata")
    if carrier_metadata.get("scalar_feature_package_sha256") != declared_frozen_sha:
        raise RecoveryError("carrier metadata does not bind the frozen scalar NPZ")
    replay = replay_planck_irrep_carrier(
        package_path=output_dir / "carrier.npz",
        metadata_path=output_dir / "metadata.json",
    )
    if replay.get("state") != "REPLAY_MATCH":
        raise RecoveryError("carrier replay did not match")

    manifest_path = output_dir / "artifact_manifest.json"
    manifest = write_portable_artifact_manifest(
        manifest_path=manifest_path,
        output_root=output_dir,
        artifact_paths={
            role: output_dir / filename for role, filename in PRE_REVIEW_ARTIFACTS.items()
        },
        frozen_scalar_package_path=Path(frozen_scalar_package_path),
        expected_frozen_scalar_sha256=declared_frozen_sha,
    )
    verified = verify_portable_artifact_manifest(
        manifest_path=manifest_path,
        output_root=output_dir,
        frozen_scalar_package_path=Path(frozen_scalar_package_path),
    )
    objective_hashes = {
        filename: _sha256(output_dir / filename)
        for filename in PRE_REVIEW_ARTIFACTS.values()
    }
    objective_hashes[manifest_path.name] = _sha256(manifest_path)
    pending_path = output_dir / "terminal.pending.json"
    pending = write_pending_terminal(
        path=pending_path,
        work_unit="PMG-WU-005",
        base_git_head=base_git_head,
        implementation_git_head=implementation_git_head,
        artifact_manifest_content_id=str(manifest["content_id"]),
        objective_output_sha256=objective_hashes,
    )
    return {
        "state": "READY_FOR_EXTERNAL_FRESH_REVIEW",
        "processed_input_ledger": ledger_report,
        "checkpoint_disposition_sha256": _sha256(checkpoint_disposition_path),
        "artifact_manifest": verified,
        "pending_terminal_sha256": _sha256(pending_path),
        "pending_terminal": pending,
        "raw_maps_reopened": False,
    }


def finalize_recovery_evidence(
    *,
    output_dir: Path,
    frozen_scalar_package_path: Path,
    fresh_review_receipt_path: Path,
) -> dict[str, object]:
    """Copy one external receipt and produce a reviewed terminal."""

    output_dir = Path(output_dir)
    verify_portable_artifact_manifest(
        manifest_path=output_dir / "artifact_manifest.json",
        output_root=output_dir,
        frozen_scalar_package_path=Path(frozen_scalar_package_path),
    )
    review = _load_json(fresh_review_receipt_path, label="fresh review receipt")
    copied_review = output_dir / "fresh_review.json"
    _write_new_json(copied_review, review)
    final_path = output_dir / "terminal.reviewed.json"
    final = finalize_terminal_after_fresh_review(
        pending_terminal_path=output_dir / "terminal.pending.json",
        review_receipt_path=copied_review,
        final_terminal_path=final_path,
    )
    return {
        "state": "REVIEWED_TERMINAL_READY",
        "terminal": final,
        "fresh_review_sha256": _sha256(copied_review),
        "reviewed_terminal_sha256": _sha256(final_path),
        "raw_maps_reopened": False,
    }


def install_reviewed_terminal(
    *, output_dir: Path, private_archive_dir: Path
) -> dict[str, object]:
    """Archive the rejected self-attested terminal and install the reviewed one."""

    output_dir = Path(output_dir)
    current = output_dir / "terminal.json"
    reviewed = output_dir / "terminal.reviewed.json"
    if not current.is_file() or not reviewed.is_file():
        raise RecoveryError("terminal installation inputs are missing")
    private_archive_dir = Path(private_archive_dir)
    private_archive_dir.mkdir(parents=True, exist_ok=True)
    rejected = private_archive_dir / "terminal.pre_review_rejected.json"
    if rejected.exists() or rejected.is_symlink():
        raise RecoveryError("rejected terminal archive already exists")
    shutil.move(str(current), str(rejected))
    shutil.move(str(reviewed), str(current))
    return {
        "state": "REVIEWED_TERMINAL_INSTALLED",
        "terminal_sha256": _sha256(current),
        "rejected_terminal_sha256": _sha256(rejected),
        "raw_maps_reopened": False,
    }
