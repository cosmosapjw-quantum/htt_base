from __future__ import annotations

import hashlib
import json
from pathlib import Path

import numpy as np
import pytest

from obsstat.planck_paired300_evidence import (
    ARTIFACT_MANIFEST_FORMAT,
    CHECKPOINT_SIDECAR_FORMAT,
    PENDING_TERMINAL_STATE,
    EvidenceBindingError,
    finalize_terminal_after_fresh_review,
    load_wu004_intake_authority,
    replay_bound_checkpoint,
    validate_processed_input_ledger,
    verify_portable_artifact_manifest,
    write_bound_checkpoint,
    write_pending_terminal,
    write_portable_artifact_manifest,
)


def _sha256(path: Path) -> str:
    return "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()


def _write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")


def _stat(seed: int) -> dict[str, int]:
    return {
        "device": 7,
        "inode": 10_000 + seed,
        "size": 1_000_000 + seed,
        "mtime_ns": 2_000_000 + seed,
    }


def _entry(path: str, *, route: str, seed: int, partial: bool = False) -> dict[str, object]:
    payload: dict[str, object] = {
        "path": path,
        "resolved_path": path,
        "stat_identity": _stat(seed),
        "product_identity": Path(path).name,
        "release_identity": "TEST_RELEASE",
        "sidecars": [],
        "checksum": None,
        "checksum_status": "DEFERRED_UNTIL_FIRST_SCIENTIFIC_READ",
        "route_eligibility": route,
    }
    if partial:
        payload["partial"] = True
    return payload


def _make_wu004_authority(tmp_path: Path):
    portable = tmp_path / "portable"
    private_path = tmp_path / "private" / "intake_manifest.json"
    raw = "/authority/raw"

    cmb = [
        _entry(
            f"{raw}/planck_ffp10/smica/cmb_mc/dx12_v3_smica_cmb_mc_{index:05d}_raw.fits",
            route="SMICA_CMB_POOL",
            seed=index,
        )
        for index in range(1000)
        if index != 970
    ]
    noise = [
        _entry(
            f"{raw}/planck_ffp10/smica/noise_mc/dx12_v3_smica_noise_mc_{index:05d}_raw.fits",
            route="SMICA_NOISE_POOL",
            seed=2_000 + index,
        )
        for index in range(300)
    ]
    commander = [
        _entry(
            f"{raw}/planck_ffp10/commander/cmb_mc/dx12_v3_commander_cmb_mc_{index:05d}_raw.fits",
            route="COMMANDER_DESCRIPTIVE_ONLY",
            seed=3_000 + index,
        )
        for index in range(3)
    ]
    partial = [
        _entry(
            f"{raw}/planck_ffp10/commander/cmb_mc/dx12_v3_commander_cmb_mc_{index:05d}_raw.fits.partial",
            route="QUARANTINED_BEFORE_FITS_OPEN",
            seed=4_000 + index,
            partial=True,
        )
        for index in range(3, 7)
    ]
    private = {
        "format": "PLANCK_MES_IRREP_PRIVATE_INTAKE_MANIFEST_V1",
        "raw_root": raw,
        "entry_count": len(cmb) + len(noise) + len(commander) + len(partial),
        "entries": [*cmb, *noise, *commander, *partial],
        "hash_policy": "ONLY_00818_HASHED_DURING_INTAKE",
    }
    _write_json(private_path, private)

    observed = _entry(
        f"{raw}/planck_data/COM_CMB_IQU-smica_2048_R3.00_full.fits",
        route="DOWNSTREAM_SELECTED_HASH_ON_FIRST_SCIENTIFIC_READ",
        seed=8_001,
    )
    commander_observed = _entry(
        f"{raw}/planck_data/COM_CMB_IQU-commander_2048_R3.00_full.fits",
        route="DOWNSTREAM_SELECTED_HASH_ON_FIRST_SCIENTIFIC_READ",
        seed=8_002,
    )
    mask = _entry(
        f"{raw}/planck_data/COM_Mask_CMB-common-Mask-Int_2048_R3.00.fits",
        route="DOWNSTREAM_SELECTED_HASH_ON_FIRST_SCIENTIFIC_READ",
        seed=8_003,
    )
    row_818 = dict(cmb[818])
    row_818["route_eligibility"] = "ADMITTED_ROW_00818"
    row_818["sha256"] = "sha256:" + "8" * 64
    row_818["checksum"] = row_818["sha256"]
    row_818["checksum_status"] = "STREAMING_SHA256_VERIFIED_AT_INTAKE"

    selected = {
        "format": "PLANCK_MES_IRREP_SELECTED_INPUT_MANIFEST_V1",
        "inputs": [observed, commander_observed, mask, row_818],
        "row_00818": {
            "state": "ADMITTED_SEMANTICALLY",
            "path": row_818["path"],
            "sha256": row_818["sha256"],
            "stat_identity": row_818["stat_identity"],
        },
        "private_manifest_sha256": _sha256(private_path),
    }
    summary = {
        "format": "PLANCK_MES_IRREP_INTAKE_SUMMARY_V1",
        "work_unit": "PMG-WU-004",
        "raw_data_mutation": False,
        "smica_cmb_mc": {"count": 999, "missing_ids": ["00970"], "state": "EXACT"},
        "smica_noise_mc": {"count": 300, "missing_ids": [], "state": "EXACT"},
    }
    route = {
        "format": "PLANCK_MES_IRREP_ROUTE_RECEIPT_V1",
        "smica_paired300": "ELIGIBLE_AFTER_WU004",
    }
    _write_json(portable / "intake_summary.json", summary)
    _write_json(portable / "route_receipt.json", route)
    _write_json(portable / "selected_input_manifest.json", selected)
    terminal = {
        "format": "PLANCK_MES_IRREP_INTAKE_TERMINAL_V1",
        "work_unit": "PMG-WU-004",
        "state": "SUCCEEDED",
        "raw_data_mutation": False,
        "real_host_execution": True,
        "private_manifest_path": str(private_path),
        "private_manifest_sha256": _sha256(private_path),
        "objective_artifact_sha256": {
            "intake_summary.json": _sha256(portable / "intake_summary.json"),
            "route_receipt.json": _sha256(portable / "route_receipt.json"),
            "selected_input_manifest.json": _sha256(portable / "selected_input_manifest.json"),
        },
        "next_executable_action": "PMG-WU-005",
        "unresolved_blockers": [],
    }
    _write_json(portable / "terminal.json", terminal)
    authority = load_wu004_intake_authority(
        portable_dir=portable,
        private_manifest_path=private_path,
    )
    return portable, private_path, authority


def _processed_record(entry: dict[str, object], *, digest_digit: str) -> dict[str, object]:
    return {
        "path": entry["path"],
        "resolved_path": entry["resolved_path"],
        "stat_identity": entry["stat_identity"],
        "sha256": "sha256:" + digest_digit * 64,
    }


def test_wu004_authority_binds_all_portable_and_private_manifests(tmp_path: Path) -> None:
    portable, private_path, authority = _make_wu004_authority(tmp_path)
    assert authority.private_manifest_sha256 == _sha256(private_path)
    assert authority.selected_manifest_sha256 == _sha256(
        portable / "selected_input_manifest.json"
    )
    private_path.write_text(private_path.read_text() + " ")
    with pytest.raises(EvidenceBindingError, match="private manifest identity"):
        load_wu004_intake_authority(
            portable_dir=portable,
            private_manifest_path=private_path,
        )


def test_processed_input_ledger_must_match_exact_accepted_paths_and_stats(tmp_path: Path) -> None:
    _, _, authority = _make_wu004_authority(tmp_path)
    ledger = {
        "format": "PLANCK_PR3_PAIRED300_PROCESSED_INPUT_LEDGER_V1",
        "wu004_terminal_sha256": authority.terminal_sha256,
        "wu004_selected_manifest_sha256": authority.selected_manifest_sha256,
        "wu004_private_manifest_sha256": authority.private_manifest_sha256,
        "observed_map": _processed_record(authority.observed_smica, digest_digit="1"),
        "common_mask": _processed_record(authority.temperature_mask, digest_digit="2"),
        "rows": [
            {
                "row_id": f"FFP10-SMICA-CMBNOISE-{index:05d}",
                "cmb": _processed_record(authority.cmb_by_id[f"{index:05d}"], digest_digit="3"),
                "noise": _processed_record(authority.noise_by_id[f"{index:05d}"], digest_digit="4"),
            }
            for index in range(300)
        ],
    }
    report = validate_processed_input_ledger(ledger=ledger, authority=authority)
    assert report["state"] == "MATCH_ACCEPTED_WU004_INTAKE"
    assert report["row_count"] == 301
    ledger["rows"][17]["cmb"]["stat_identity"]["size"] += 1
    with pytest.raises(EvidenceBindingError, match="accepted intake identity"):
        validate_processed_input_ledger(ledger=ledger, authority=authority)


def test_bound_checkpoint_sidecar_detects_numeric_payload_tamper(tmp_path: Path) -> None:
    checkpoint = tmp_path / "checkpoint.npz"
    sidecar = tmp_path / "checkpoint.json"
    arrays = {
        "features": np.arange(36, dtype=np.float64).reshape(3, 12),
        "carrier": np.arange(96, dtype=np.float64).reshape(3, 32),
    }
    metadata = write_bound_checkpoint(
        checkpoint_path=checkpoint,
        sidecar_path=sidecar,
        arrays=arrays,
        completed_row_ids=("OBS", "ROW0", "ROW1"),
        processed_input_ledger_content_id="sha256:" + "5" * 64,
        operator_identity_sha256="sha256:" + "6" * 64,
    )
    assert metadata["format"] == CHECKPOINT_SIDECAR_FORMAT
    replay = replay_bound_checkpoint(
        checkpoint_path=checkpoint,
        sidecar_path=sidecar,
    )
    assert replay["state"] == "CHECKPOINT_MATCH"
    with np.load(checkpoint, allow_pickle=False) as bundle:
        tampered = {name: np.asarray(bundle[name]).copy() for name in bundle.files}
    tampered["carrier"][1, 7] += 1.0
    np.savez(checkpoint, **tampered)
    with pytest.raises(EvidenceBindingError, match="checkpoint byte identity"):
        replay_bound_checkpoint(
            checkpoint_path=checkpoint,
            sidecar_path=sidecar,
        )


def test_portable_manifest_enforces_frozen_npz_and_every_declared_artifact(tmp_path: Path) -> None:
    root = tmp_path / "output"
    root.mkdir()
    roles = {}
    for name in (
        "carrier.npz",
        "metadata.json",
        "scalar_closure.json",
        "input_identity_receipt.json",
        "leakage_receipt.json",
        "replay.json",
    ):
        path = root / name
        path.write_bytes((name + "\n").encode())
        roles[name.removesuffix(".json").removesuffix(".npz")] = path
    frozen = tmp_path / "frozen_scalar.npz"
    frozen.write_bytes(b"frozen\n")
    manifest = root / "artifact_manifest.json"
    payload = write_portable_artifact_manifest(
        manifest_path=manifest,
        output_root=root,
        artifact_paths=roles,
        frozen_scalar_package_path=frozen,
        expected_frozen_scalar_sha256=_sha256(frozen),
    )
    assert payload["format"] == ARTIFACT_MANIFEST_FORMAT
    assert verify_portable_artifact_manifest(
        manifest_path=manifest,
        output_root=root,
        frozen_scalar_package_path=frozen,
    )["state"] == "ARTIFACTS_MATCH"
    (root / "metadata.json").write_bytes(b"tampered\n")
    with pytest.raises(EvidenceBindingError, match="portable artifact identity"):
        verify_portable_artifact_manifest(
            manifest_path=manifest,
            output_root=root,
            frozen_scalar_package_path=frozen,
        )


def test_terminal_cannot_succeed_before_matching_zero_finding_review(tmp_path: Path) -> None:
    pending_path = tmp_path / "terminal.pending.json"
    final_path = tmp_path / "terminal.json"
    content_id = "sha256:" + "7" * 64
    pending = write_pending_terminal(
        path=pending_path,
        work_unit="PMG-WU-005",
        base_git_head="a" * 40,
        implementation_git_head="b" * 40,
        artifact_manifest_content_id=content_id,
        objective_output_sha256={"carrier.npz": "sha256:" + "8" * 64},
    )
    assert pending["state"] == PENDING_TERMINAL_STATE
    assert "P0_remaining" not in pending and "P1_remaining" not in pending
    bad_review = tmp_path / "review.bad.json"
    _write_json(
        bad_review,
        {
            "format": "PLANCK_PR3_PAIRED300_FRESH_REVIEW_V1",
            "state": "BLOCKED_BY_P1",
            "P0": 0,
            "P1": 1,
            "artifact_manifest_content_id": content_id,
            "independent_read_only_first_pass": True,
            "repair_rounds_used": 1,
        },
    )
    with pytest.raises(EvidenceBindingError, match="zero P0/P1"):
        finalize_terminal_after_fresh_review(
            pending_terminal_path=pending_path,
            review_receipt_path=bad_review,
            final_terminal_path=final_path,
        )
    good_review = tmp_path / "review.good.json"
    _write_json(
        good_review,
        {
            "format": "PLANCK_PR3_PAIRED300_FRESH_REVIEW_V1",
            "state": "PASS",
            "P0": 0,
            "P1": 0,
            "artifact_manifest_content_id": content_id,
            "independent_read_only_first_pass": True,
            "repair_rounds_used": 1,
        },
    )
    final = finalize_terminal_after_fresh_review(
        pending_terminal_path=pending_path,
        review_receipt_path=good_review,
        final_terminal_path=final_path,
    )
    assert final["state"] == "SUCCEEDED"
    assert final["P0_remaining"] == 0 and final["P1_remaining"] == 0
