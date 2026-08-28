"""Fail-closed PMG-WU-005 evidence and review bindings.

This module does not open a Planck map or recompute a scientific row.  It
binds the already executed paired-300 result to the accepted PMG-WU-004
intake, tamper-evident checkpoints, exact portable artifacts, the frozen
scalar package, and one external fresh-review receipt.
"""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
import os
from pathlib import Path
import re
from typing import Mapping, Sequence

import numpy as np


CHECKPOINT_SIDECAR_FORMAT = "PLANCK_PR3_PAIRED300_BOUND_CHECKPOINT_V1"
ARTIFACT_MANIFEST_FORMAT = "PLANCK_PR3_PAIRED300_ARTIFACT_MANIFEST_V1"
PENDING_TERMINAL_STATE = "EXECUTED_PENDING_FRESH_REVIEW"
FRESH_REVIEW_FORMAT = "PLANCK_PR3_PAIRED300_FRESH_REVIEW_V1"
FINAL_TERMINAL_FORMAT = "PLANCK_PR3_PAIRED300_REVIEWED_TERMINAL_V1"
PROCESSED_LEDGER_FORMAT = "PLANCK_PR3_PAIRED300_PROCESSED_INPUT_LEDGER_V1"
_SHA256 = re.compile(r"^sha256:[0-9a-f]{64}$")
_GIT_OID = re.compile(r"^[0-9a-f]{40}$")
_CMB_NAME = re.compile(r"dx12_v3_smica_cmb_mc_(\d{5})_raw\.fits$")
_NOISE_NAME = re.compile(r"dx12_v3_smica_noise_mc_(\d{5})_raw\.fits$")
EXPECTED_CMB_IDS = {f"{index:05d}" for index in range(1000)} - {"00970"}
EXPECTED_PAIRED_IDS = tuple(f"{index:05d}" for index in range(300))
EXPECTED_ROW_IDS = tuple(
    f"FFP10-SMICA-CMBNOISE-{index:05d}" for index in range(300)
)


class EvidenceBindingError(RuntimeError):
    """Raised when an evidence object is missing, mutable, or misattributed."""


@dataclass(frozen=True)
class WU004IntakeAuthority:
    terminal_sha256: str
    selected_manifest_sha256: str
    private_manifest_sha256: str
    observed_smica: dict[str, object]
    temperature_mask: dict[str, object]
    cmb_by_id: dict[str, dict[str, object]]
    noise_by_id: dict[str, dict[str, object]]
    expected_processed_identity: dict[str, str]


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for chunk in iter(lambda: handle.read(8 * 1024 * 1024), b""):
            digest.update(chunk)
    return "sha256:" + digest.hexdigest()


def _strict_sha(value: object, *, label: str) -> str:
    if not isinstance(value, str) or _SHA256.fullmatch(value) is None:
        raise EvidenceBindingError(f"{label} must be one sha256 identity")
    return value


def _strict_git_oid(value: object, *, label: str) -> str:
    if not isinstance(value, str) or _GIT_OID.fullmatch(value) is None:
        raise EvidenceBindingError(f"{label} git identity is malformed")
    return value


def _clone(value: object, *, label: str) -> object:
    try:
        return json.loads(
            json.dumps(
                value,
                sort_keys=True,
                separators=(",", ":"),
                ensure_ascii=True,
                allow_nan=False,
            )
        )
    except (TypeError, ValueError) as exc:
        raise EvidenceBindingError(f"{label} is not canonical JSON") from exc


def _canonical_hash(value: object, *, role: str) -> str:
    encoded = json.dumps(
        _clone(value, label=role),
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
        allow_nan=False,
    ).encode("ascii")
    digest = hashlib.sha256()
    digest.update(role.encode("ascii") + b"\0")
    digest.update(encoded)
    return "sha256:" + digest.hexdigest()


def _array_digest(value: np.ndarray, *, role: str) -> str:
    array = np.ascontiguousarray(value)
    digest = hashlib.sha256()
    digest.update(role.encode("ascii") + b"\0")
    digest.update(array.dtype.str.encode("ascii") + b"\0")
    digest.update(repr(array.shape).encode("ascii") + b"\0")
    digest.update(memoryview(array).cast("B"))
    return "sha256:" + digest.hexdigest()


def _load_json(path: Path, *, label: str) -> dict[str, object]:
    try:
        value = json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise EvidenceBindingError(f"{label} is not readable JSON") from exc
    if not isinstance(value, dict):
        raise EvidenceBindingError(f"{label} must be a mapping")
    return value


def _atomic_json(path: Path, payload: Mapping[str, object]) -> None:
    path = Path(path)
    if path.exists() or path.is_symlink():
        raise EvidenceBindingError(f"refusing to overwrite evidence: {path}")
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.parent.is_symlink():
        raise EvidenceBindingError("evidence output parent cannot be a symlink")
    temporary = path.with_name(f".{path.name}.{os.getpid()}.tmp")
    try:
        with temporary.open("xb") as handle:
            handle.write(
                (
                    json.dumps(
                        payload,
                        sort_keys=True,
                        separators=(",", ":"),
                        ensure_ascii=True,
                        allow_nan=False,
                    )
                    + "\n"
                ).encode("ascii")
            )
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
    finally:
        temporary.unlink(missing_ok=True)


def _atomic_npz(path: Path, arrays: Mapping[str, np.ndarray]) -> None:
    path = Path(path)
    if path.exists() or path.is_symlink():
        raise EvidenceBindingError(f"refusing to overwrite checkpoint: {path}")
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.{os.getpid()}.tmp")
    try:
        with temporary.open("xb") as handle:
            np.savez(handle, **arrays)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
    finally:
        temporary.unlink(missing_ok=True)


def _stat_projection(value: object, *, label: str) -> dict[str, int]:
    if not isinstance(value, Mapping):
        raise EvidenceBindingError(f"{label} stat identity is missing")
    result: dict[str, int] = {}
    for key in ("device", "inode", "size", "mtime_ns"):
        item = value.get(key)
        if type(item) is not int:
            raise EvidenceBindingError(f"{label} stat identity is malformed")
        result[key] = item
    return result


def _processed_projection(value: Mapping[str, object], *, label: str) -> dict[str, object]:
    path = value.get("path")
    resolved = value.get("resolved_path")
    if not isinstance(path, str) or not isinstance(resolved, str) or path != resolved:
        raise EvidenceBindingError(f"{label} accepted path identity is malformed")
    return {
        "path": path,
        "resolved_path": resolved,
        "stat_identity": _stat_projection(value.get("stat_identity"), label=label),
    }


def _processed_hash(value: Mapping[str, object], *, label: str) -> str:
    return _canonical_hash(
        _processed_projection(value, label=label),
        role="wu004_accepted_processed_input",
    )


def _entry_index(entries: object) -> tuple[
    dict[str, dict[str, object]], dict[str, dict[str, object]]
]:
    if not isinstance(entries, list):
        raise EvidenceBindingError("WU-004 private manifest entries are missing")
    cmb: dict[str, dict[str, object]] = {}
    noise: dict[str, dict[str, object]] = {}
    for raw in entries:
        if not isinstance(raw, Mapping):
            raise EvidenceBindingError("WU-004 private manifest entry is malformed")
        entry = dict(_clone(raw, label="WU-004 private entry"))
        name = entry.get("product_identity")
        route = entry.get("route_eligibility")
        if not isinstance(name, str):
            raise EvidenceBindingError("WU-004 product identity is missing")
        match = _CMB_NAME.fullmatch(name)
        if match and route == "SMICA_CMB_POOL":
            cmb[match.group(1)] = entry
            continue
        match = _NOISE_NAME.fullmatch(name)
        if match and route == "SMICA_NOISE_POOL":
            noise[match.group(1)] = entry
    if set(cmb) != EXPECTED_CMB_IDS or set(noise) != set(EXPECTED_PAIRED_IDS):
        raise EvidenceBindingError("WU-004 private inventory identity set drifted")
    return cmb, noise


def load_wu004_intake_authority(
    *,
    portable_dir: Path,
    private_manifest_path: Path,
) -> WU004IntakeAuthority:
    """Load and cross-bind every accepted PMG-WU-004 evidence object."""

    portable_dir = Path(portable_dir)
    private_manifest_path = Path(private_manifest_path)
    summary_path = portable_dir / "intake_summary.json"
    route_path = portable_dir / "route_receipt.json"
    selected_path = portable_dir / "selected_input_manifest.json"
    terminal_path = portable_dir / "terminal.json"
    summary = _load_json(summary_path, label="WU-004 intake summary")
    route = _load_json(route_path, label="WU-004 route receipt")
    selected = _load_json(selected_path, label="WU-004 selected manifest")
    terminal = _load_json(terminal_path, label="WU-004 terminal")
    private = _load_json(private_manifest_path, label="WU-004 private manifest")

    if (
        terminal.get("format") != "PLANCK_MES_IRREP_INTAKE_TERMINAL_V1"
        or terminal.get("work_unit") != "PMG-WU-004"
        or terminal.get("state") != "SUCCEEDED"
        or terminal.get("real_host_execution") is not True
        or terminal.get("raw_data_mutation") is not False
        or terminal.get("next_executable_action") != "PMG-WU-005"
        or terminal.get("unresolved_blockers") != []
    ):
        raise EvidenceBindingError("WU-004 terminal is not accepted authority")
    hashes = terminal.get("objective_artifact_sha256")
    expected = {
        "intake_summary.json": _sha256(summary_path),
        "route_receipt.json": _sha256(route_path),
        "selected_input_manifest.json": _sha256(selected_path),
    }
    if hashes != expected:
        raise EvidenceBindingError("WU-004 portable manifest identity drifted")
    private_sha = _sha256(private_manifest_path)
    if (
        terminal.get("private_manifest_sha256") != private_sha
        or selected.get("private_manifest_sha256") != private_sha
    ):
        raise EvidenceBindingError("WU-004 private manifest identity drifted")
    if (
        summary.get("format") != "PLANCK_MES_IRREP_INTAKE_SUMMARY_V1"
        or summary.get("smica_cmb_mc")
        != {"count": 999, "missing_ids": ["00970"], "state": "EXACT"}
        or summary.get("smica_noise_mc")
        != {"count": 300, "missing_ids": [], "state": "EXACT"}
        or route.get("smica_paired300") != "ELIGIBLE_AFTER_WU004"
        or private.get("format")
        != "PLANCK_MES_IRREP_PRIVATE_INTAKE_MANIFEST_V1"
    ):
        raise EvidenceBindingError("WU-004 intake semantic authority drifted")

    cmb, noise = _entry_index(private.get("entries"))
    inputs = selected.get("inputs")
    if not isinstance(inputs, list):
        raise EvidenceBindingError("WU-004 selected inputs are missing")
    by_product = {
        entry.get("product_identity"): dict(_clone(entry, label="selected input"))
        for entry in inputs
        if isinstance(entry, Mapping)
    }
    observed = by_product.get("COM_CMB_IQU-smica_2048_R3.00_full.fits")
    mask = by_product.get("COM_Mask_CMB-common-Mask-Int_2048_R3.00.fits")
    if not isinstance(observed, dict) or not isinstance(mask, dict):
        raise EvidenceBindingError("WU-004 observed SMICA or mask identity is missing")

    identity: dict[str, str] = {
        "observed_map": _processed_hash(observed, label="observed SMICA"),
        "common_mask": _processed_hash(mask, label="temperature mask"),
    }
    for identifier in EXPECTED_PAIRED_IDS:
        identity[f"cmb:{identifier}"] = _processed_hash(
            cmb[identifier], label=f"CMB {identifier}"
        )
        identity[f"noise:{identifier}"] = _processed_hash(
            noise[identifier], label=f"noise {identifier}"
        )
    return WU004IntakeAuthority(
        terminal_sha256=_sha256(terminal_path),
        selected_manifest_sha256=_sha256(selected_path),
        private_manifest_sha256=private_sha,
        observed_smica=observed,
        temperature_mask=mask,
        cmb_by_id=cmb,
        noise_by_id=noise,
        expected_processed_identity=identity,
    )


def _validate_processed_record(
    value: object,
    *,
    expected_hash: str,
    label: str,
) -> None:
    if not isinstance(value, Mapping):
        raise EvidenceBindingError(f"{label} processed record is missing")
    _strict_sha(value.get("sha256"), label=f"{label} execution content")
    if _processed_hash(value, label=label) != expected_hash:
        raise EvidenceBindingError(f"{label} differs from accepted intake identity")


def validate_processed_input_ledger(
    *,
    ledger: Mapping[str, object],
    authority: WU004IntakeAuthority,
) -> dict[str, object]:
    """Require the exact observed/mask/300-CMB/300-noise role graph."""

    if (
        not isinstance(ledger, Mapping)
        or ledger.get("format") != PROCESSED_LEDGER_FORMAT
        or ledger.get("wu004_terminal_sha256") != authority.terminal_sha256
        or ledger.get("wu004_selected_manifest_sha256")
        != authority.selected_manifest_sha256
        or ledger.get("wu004_private_manifest_sha256")
        != authority.private_manifest_sha256
    ):
        raise EvidenceBindingError("processed ledger WU-004 authority binding drifted")
    _validate_processed_record(
        ledger.get("observed_map"),
        expected_hash=authority.expected_processed_identity["observed_map"],
        label="observed map",
    )
    _validate_processed_record(
        ledger.get("common_mask"),
        expected_hash=authority.expected_processed_identity["common_mask"],
        label="common mask",
    )
    rows = ledger.get("rows")
    if not isinstance(rows, list) or len(rows) != 300:
        raise EvidenceBindingError("processed ledger must contain exact 300 paired rows")
    for index, row in enumerate(rows):
        if not isinstance(row, Mapping) or row.get("row_id") != EXPECTED_ROW_IDS[index]:
            raise EvidenceBindingError("processed ledger row identity/order drifted")
        identifier = EXPECTED_PAIRED_IDS[index]
        _validate_processed_record(
            row.get("cmb"),
            expected_hash=authority.expected_processed_identity[f"cmb:{identifier}"],
            label=f"CMB row {identifier}",
        )
        _validate_processed_record(
            row.get("noise"),
            expected_hash=authority.expected_processed_identity[f"noise:{identifier}"],
            label=f"noise row {identifier}",
        )
    projection = _clone(ledger, label="processed input ledger")
    return {
        "state": "MATCH_ACCEPTED_WU004_INTAKE",
        "row_count": 301,
        "selected_regular_file_count": 602,
        "content_id": _canonical_hash(
            projection,
            role="planck_paired300_processed_input_ledger",
        ),
    }


def write_bound_checkpoint(
    *,
    checkpoint_path: Path,
    sidecar_path: Path,
    arrays: Mapping[str, object],
    completed_row_ids: Sequence[str],
    processed_input_ledger_content_id: str,
    operator_identity_sha256: str,
) -> dict[str, object]:
    """Write a numeric checkpoint whose sidecar binds exact bytes and arrays."""

    if set(arrays) != {"features", "carrier"}:
        raise EvidenceBindingError("checkpoint arrays must be features and carrier")
    numeric = {name: np.asarray(value) for name, value in arrays.items()}
    rows = tuple(completed_row_ids)
    if (
        not rows
        or len(set(rows)) != len(rows)
        or numeric["features"].dtype != np.dtype("float64")
        or numeric["carrier"].dtype != np.dtype("float64")
        or numeric["features"].shape != (len(rows), 12)
        or numeric["carrier"].shape != (len(rows), 32)
        or not np.all(np.isfinite(numeric["features"]))
        or not np.all(np.isfinite(numeric["carrier"]))
    ):
        raise EvidenceBindingError("checkpoint numerical payload contract drifted")
    ledger_id = _strict_sha(
        processed_input_ledger_content_id,
        label="processed input ledger content",
    )
    operator_id = _strict_sha(operator_identity_sha256, label="operator identity")
    _atomic_npz(Path(checkpoint_path), numeric)
    payload: dict[str, object] = {
        "format": CHECKPOINT_SIDECAR_FORMAT,
        "checkpoint_filename": Path(checkpoint_path).name,
        "checkpoint_sha256": _sha256(Path(checkpoint_path)),
        "completed_row_ids": list(rows),
        "processed_input_ledger_content_id": ledger_id,
        "operator_identity_sha256": operator_id,
        "arrays": {
            name: {
                "dtype": value.dtype.str,
                "shape": list(value.shape),
                "content_id": _array_digest(value, role=f"checkpoint_{name}"),
            }
            for name, value in sorted(numeric.items())
        },
    }
    payload["content_id"] = _canonical_hash(payload, role="paired300_checkpoint_sidecar")
    _atomic_json(Path(sidecar_path), payload)
    return payload


def replay_bound_checkpoint(
    *, checkpoint_path: Path, sidecar_path: Path
) -> dict[str, object]:
    sidecar = _load_json(Path(sidecar_path), label="checkpoint sidecar")
    if (
        sidecar.get("format") != CHECKPOINT_SIDECAR_FORMAT
        or sidecar.get("checkpoint_filename") != Path(checkpoint_path).name
        or sidecar.get("checkpoint_sha256") != _sha256(Path(checkpoint_path))
    ):
        raise EvidenceBindingError("checkpoint byte identity drifted")
    expected_content = dict(sidecar)
    content_id = expected_content.pop("content_id", None)
    if content_id != _canonical_hash(
        expected_content, role="paired300_checkpoint_sidecar"
    ):
        raise EvidenceBindingError("checkpoint sidecar content identity drifted")
    try:
        with np.load(checkpoint_path, allow_pickle=False) as bundle:
            if set(bundle.files) != {"features", "carrier"}:
                raise EvidenceBindingError("checkpoint keys drifted")
            arrays = {name: np.asarray(bundle[name]) for name in bundle.files}
    except (OSError, ValueError, KeyError) as exc:
        raise EvidenceBindingError("checkpoint is not a safe numeric NPZ") from exc
    for name, value in arrays.items():
        expected = sidecar.get("arrays", {}).get(name)
        if (
            not isinstance(expected, Mapping)
            or expected.get("dtype") != value.dtype.str
            or expected.get("shape") != list(value.shape)
            or expected.get("content_id")
            != _array_digest(value, role=f"checkpoint_{name}")
        ):
            raise EvidenceBindingError("checkpoint numerical content identity drifted")
    return {
        "state": "CHECKPOINT_MATCH",
        "content_id": content_id,
        "completed_row_count": len(sidecar.get("completed_row_ids", [])),
    }


def write_portable_artifact_manifest(
    *,
    manifest_path: Path,
    output_root: Path,
    artifact_paths: Mapping[str, Path],
    frozen_scalar_package_path: Path,
    expected_frozen_scalar_sha256: str,
) -> dict[str, object]:
    """Bind every pre-review portable artifact and the exact frozen NPZ."""

    output_root = Path(output_root).resolve()
    expected_frozen = _strict_sha(
        expected_frozen_scalar_sha256,
        label="frozen scalar package authority",
    )
    if _sha256(Path(frozen_scalar_package_path)) != expected_frozen:
        raise EvidenceBindingError("frozen scalar package byte identity drifted")
    if not artifact_paths or len(set(artifact_paths)) != len(artifact_paths):
        raise EvidenceBindingError("portable artifact role set is malformed")
    artifacts: dict[str, object] = {}
    seen: set[Path] = set()
    for role, raw_path in sorted(artifact_paths.items()):
        path = Path(raw_path)
        resolved = path.resolve(strict=True)
        if (
            not isinstance(role, str)
            or not role
            or path.is_symlink()
            or not resolved.is_file()
            or not resolved.is_relative_to(output_root)
            or resolved in seen
        ):
            raise EvidenceBindingError("portable artifact path/role is unsafe")
        seen.add(resolved)
        artifacts[role] = {
            "filename": resolved.name,
            "byte_size": resolved.stat().st_size,
            "sha256": _sha256(resolved),
        }
    payload: dict[str, object] = {
        "format": ARTIFACT_MANIFEST_FORMAT,
        "frozen_scalar_package_filename": Path(frozen_scalar_package_path).name,
        "frozen_scalar_package_sha256": expected_frozen,
        "artifacts": artifacts,
    }
    payload["content_id"] = _canonical_hash(payload, role="paired300_artifact_manifest")
    _atomic_json(Path(manifest_path), payload)
    return payload


def verify_portable_artifact_manifest(
    *,
    manifest_path: Path,
    output_root: Path,
    frozen_scalar_package_path: Path,
) -> dict[str, object]:
    manifest = _load_json(Path(manifest_path), label="portable artifact manifest")
    if manifest.get("format") != ARTIFACT_MANIFEST_FORMAT:
        raise EvidenceBindingError("portable artifact manifest format drifted")
    content = dict(manifest)
    content_id = content.pop("content_id", None)
    if content_id != _canonical_hash(content, role="paired300_artifact_manifest"):
        raise EvidenceBindingError("portable artifact manifest content drifted")
    frozen_sha = _strict_sha(
        manifest.get("frozen_scalar_package_sha256"),
        label="frozen scalar package authority",
    )
    if (
        manifest.get("frozen_scalar_package_filename")
        != Path(frozen_scalar_package_path).name
        or _sha256(Path(frozen_scalar_package_path)) != frozen_sha
    ):
        raise EvidenceBindingError("frozen scalar package byte identity drifted")
    root = Path(output_root).resolve()
    artifacts = manifest.get("artifacts")
    if not isinstance(artifacts, Mapping) or not artifacts:
        raise EvidenceBindingError("portable artifact identity set is missing")
    for role, record in artifacts.items():
        if not isinstance(role, str) or not isinstance(record, Mapping):
            raise EvidenceBindingError("portable artifact record is malformed")
        path = root / str(record.get("filename"))
        if (
            path.is_symlink()
            or not path.is_file()
            or path.resolve().parent != root
            or record.get("byte_size") != path.stat().st_size
            or record.get("sha256") != _sha256(path)
        ):
            raise EvidenceBindingError(f"portable artifact identity drifted: {role}")
    return {
        "state": "ARTIFACTS_MATCH",
        "content_id": content_id,
        "artifact_count": len(artifacts),
        "frozen_scalar_package_sha256": frozen_sha,
    }


def write_pending_terminal(
    *,
    path: Path,
    work_unit: str,
    base_git_head: str,
    implementation_git_head: str,
    implementation_git_tree: str,
    artifact_manifest_content_id: str,
    objective_output_sha256: Mapping[str, str],
) -> dict[str, object]:
    if work_unit != "PMG-WU-005":
        raise EvidenceBindingError("pending terminal work unit drifted")
    base_git_head = _strict_git_oid(base_git_head, label="pending terminal base")
    implementation_git_head = _strict_git_oid(
        implementation_git_head,
        label="pending terminal implementation head",
    )
    implementation_git_tree = _strict_git_oid(
        implementation_git_tree,
        label="pending terminal implementation tree",
    )
    manifest_id = _strict_sha(
        artifact_manifest_content_id,
        label="artifact manifest content",
    )
    outputs = {
        str(name): _strict_sha(value, label=f"objective output {name}")
        for name, value in sorted(objective_output_sha256.items())
    }
    payload: dict[str, object] = {
        "format": "PLANCK_PR3_PAIRED300_PENDING_TERMINAL_V1",
        "work_unit": work_unit,
        "state": PENDING_TERMINAL_STATE,
        "base_git_head": base_git_head,
        "implementation_git_head": implementation_git_head,
        "implementation_git_tree": implementation_git_tree,
        "artifact_manifest_content_id": manifest_id,
        "objective_output_sha256": outputs,
        "real_host_execution": True,
        "replay_status": "MATCH",
        "scalar_closure": "MATCH",
        "raw_data_mutation": False,
        "claim_promotion": False,
        "unresolved_blockers": ["FRESH_READ_ONLY_REVIEW_PENDING"],
        "next_executable_action": "FRESH_READ_ONLY_REVIEW",
    }
    _atomic_json(Path(path), payload)
    return payload


def finalize_terminal_after_fresh_review(
    *,
    pending_terminal_path: Path,
    review_receipt_path: Path,
    final_terminal_path: Path,
) -> dict[str, object]:
    pending = _load_json(Path(pending_terminal_path), label="pending terminal")
    review = _load_json(Path(review_receipt_path), label="fresh review receipt")
    if (
        pending.get("format") != "PLANCK_PR3_PAIRED300_PENDING_TERMINAL_V1"
        or pending.get("state") != PENDING_TERMINAL_STATE
    ):
        raise EvidenceBindingError("pending terminal is not reviewable")
    if (
        review.get("format") != FRESH_REVIEW_FORMAT
        or review.get("state") != "PASS"
        or review.get("P0") != 0
        or review.get("P1") != 0
        or review.get("independent_read_only_first_pass") is not True
        or type(review.get("repair_rounds_used")) is not int
        or not 0 <= review["repair_rounds_used"] <= 1
        or review.get("artifact_manifest_content_id")
        != pending.get("artifact_manifest_content_id")
    ):
        raise EvidenceBindingError("fresh review does not establish zero P0/P1")
    try:
        pending_head = _strict_git_oid(
            pending.get("implementation_git_head"),
            label="pending implementation head",
        )
        pending_tree = _strict_git_oid(
            pending.get("implementation_git_tree"),
            label="pending implementation tree",
        )
        review_head = _strict_git_oid(
            review.get("candidate_git_head"),
            label="fresh review candidate head",
        )
        review_tree = _strict_git_oid(
            review.get("candidate_git_tree"),
            label="fresh review candidate tree",
        )
    except EvidenceBindingError as exc:
        raise EvidenceBindingError(
            "fresh review candidate git identity differs"
        ) from exc
    if review_head != pending_head or review_tree != pending_tree:
        raise EvidenceBindingError("fresh review candidate git identity differs")
    final = {
        "format": FINAL_TERMINAL_FORMAT,
        "work_unit": "PMG-WU-005",
        "state": "SUCCEEDED",
        "base_git_head": pending["base_git_head"],
        "implementation_git_head": pending_head,
        "implementation_git_tree": pending_tree,
        "artifact_manifest_content_id": pending["artifact_manifest_content_id"],
        "objective_output_sha256": pending["objective_output_sha256"],
        "fresh_review_receipt_sha256": _sha256(Path(review_receipt_path)),
        "fresh_review": "PASS",
        "P0_remaining": 0,
        "P1_remaining": 0,
        "review_repair_count": review["repair_rounds_used"],
        "real_host_execution": True,
        "replay_status": "MATCH",
        "scalar_closure": "MATCH",
        "raw_data_mutation": False,
        "claim_promotion": False,
        "unresolved_blockers": [],
        "next_executable_action": "PMG-WU-006",
    }
    _atomic_json(Path(final_terminal_path), final)
    return final
