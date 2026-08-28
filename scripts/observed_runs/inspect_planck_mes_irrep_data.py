#!/usr/bin/env python3
"""Read-only, content-bound PMG-WU-004 intake of local Planck products."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import warnings

import numpy as np
from astropy.io import fits


BASE_GIT_HEAD = "03f002d97deb31648f47a9a5bdc0e7706354909e"
REQUIRED_PLANCK = (
    "COM_CMB_IQU-smica_2048_R3.00_full.fits",
    "COM_CMB_IQU-commander_2048_R3.00_full.fits",
    "COM_Mask_CMB-common-Mask-Int_2048_R3.00.fits",
)
EXPECTED_CMB = {f"{index:05d}" for index in range(1000)} - {"00970"}
EXPECTED_NOISE = {f"{index:05d}" for index in range(300)}
EXPECTED_COMMANDER_COMPLETE = {"00000", "00001", "00002"}
EXPECTED_COMMANDER_PARTIAL = {"00003", "00004", "00005", "00006"}


class IntakeBlocked(RuntimeError):
    """Typed stop for a violated PMG-WU-004 intake invariant."""


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(8 * 1024 * 1024), b""):
            digest.update(chunk)
    return "sha256:" + digest.hexdigest()


def stat_identity(path: Path) -> dict[str, int]:
    value = path.stat(follow_symlinks=False)
    return {
        "device": value.st_dev,
        "inode": value.st_ino,
        "size": value.st_size,
        "mtime_ns": value.st_mtime_ns,
    }


def _source_root_identity(path: Path) -> dict[str, object]:
    value = path.stat(follow_symlinks=False)
    return {
        "path": str(path),
        "device": value.st_dev,
        "inode": value.st_ino,
        "size": value.st_size,
        "mtime_ns": value.st_mtime_ns,
    }


def _contained(path: Path, root: Path) -> Path:
    resolved_root = root.resolve(strict=True)
    try:
        resolved = path.resolve(strict=True)
    except FileNotFoundError as exc:
        raise IntakeBlocked(f"required input is missing: {path}") from exc
    if not resolved.is_relative_to(resolved_root):
        raise IntakeBlocked(f"symlink escape refused: {path} -> {resolved}")
    if not resolved.is_file():
        raise IntakeBlocked(f"input is not a regular file: {path}")
    return resolved


def _ids(directory: Path, pattern: re.Pattern[str]) -> tuple[set[str], list[Path]]:
    found: set[str] = set()
    paths: list[Path] = []
    for path in directory.iterdir():
        match = pattern.fullmatch(path.name)
        if match:
            found.add(match.group(1))
            paths.append(path)
    return found, sorted(paths)


def adjudicate_00818(path: Path) -> dict[str, object]:
    """Admit row 00818 from FITS semantics and content, never byte size alone."""

    before = stat_identity(path)
    digest = _sha256(path)
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        try:
            with fits.open(
                path, mode="readonly", memmap=True, lazy_load_hdus=True,
                checksum=False, ignore_missing_end=True,
            ) as bundle:
                if len(bundle) != 2 or not isinstance(bundle[1], fits.BinTableHDU):
                    raise IntakeBlocked("00818 FITS structure is not PRIMARY+BINTABLE")
                table = bundle[1]
                header = table.header
                columns = list(table.columns.names or [])
                required_columns = ["INTENSITY", "Q-POLARISATION", "U-POLARISATION"]
                if columns != required_columns:
                    raise IntakeBlocked("00818 FITS semantic columns differ")
                if (
                    header.get("NSIDE") != 2048
                    or header.get("ORDERING") != "RING"
                    or header.get("INDXSCHM") != "IMPLICIT"
                ):
                    raise IntakeBlocked("00818 FITS HEALPix semantics differ")
                info = bundle.fileinfo(1)
                payload_bytes = (
                    int(header["NAXIS1"]) * int(header["NAXIS2"])
                    + int(header.get("PCOUNT", 0))
                )
                payload_end = int(info["datLoc"]) + payload_bytes
                expected_padded_end = int(info["datLoc"]) + int(info["datSpan"])
                if before["size"] < payload_end:
                    raise IntakeBlocked("00818 FITS payload is truncated")
                indices = sorted({0, int(header["NAXIS2"]) // 2, int(header["NAXIS2"]) - 1})
                sample = np.concatenate(
                    [np.asarray(table.data[name][indices], dtype=float) for name in required_columns]
                )
                if not np.all(np.isfinite(sample)):
                    raise IntakeBlocked("00818 FITS finite payload sample failed")
        except IntakeBlocked:
            raise
        except Exception as exc:
            raise IntakeBlocked(f"00818 semantic FITS open failed: {exc}") from exc
    after = stat_identity(path)
    if after != before:
        raise IntakeBlocked("00818 source mutated during read-only adjudication")
    return {
        "state": "ADMITTED_SEMANTICALLY",
        "decision_basis": "FITS_STRUCTURE_HEADERS_PAYLOAD_FINITE_SAMPLE_AND_STREAMING_DIGEST",
        "path": str(path),
        "sha256": digest,
        "stat_identity": before,
        "columns": required_columns,
        "nside": 2048,
        "ordering": "RING",
        "index_scheme": "IMPLICIT",
        "payload_end_byte": payload_end,
        "expected_padded_end_byte": expected_padded_end,
        "terminal_padding_shortfall_bytes": max(0, expected_padded_end - before["size"]),
        "finite_sample_count": int(sample.size),
        "warnings": [str(item.message) for item in caught],
    }


def _write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + ".tmp")
    temporary.write_text(json.dumps(payload, indent=2, sort_keys=True, allow_nan=False) + "\n")
    os.replace(temporary, path)


def _manifest_entry(path: Path, raw_root: Path, *, route: str) -> dict[str, object]:
    resolved = _contained(path, raw_root)
    sidecars = [
        str(candidate)
        for suffix in (".sha256", ".sha256sum")
        if (candidate := Path(str(path) + suffix)).is_file()
    ]
    return {
        "path": str(path),
        "resolved_path": str(resolved),
        "stat_identity": stat_identity(path),
        "product_identity": path.name,
        "release_identity": "Planck PR3 R3.00" if "COM_" in path.name else "FFP10 dx12_v3",
        "sidecars": sidecars,
        "checksum": None,
        "checksum_status": "DEFERRED_UNTIL_FIRST_SCIENTIFIC_READ",
        "route_eligibility": route,
    }


def inspect_planck_mes_irrep_data(
    *, workdir: Path, portable_output: Path, private_output: Path,
    verify_selected: bool,
) -> dict[str, object]:
    workdir = Path(workdir)
    raw = workdir / "raw"
    if not raw.is_dir() or raw.is_symlink():
        raise IntakeBlocked("raw root missing or symlinked")
    raw_resolved = raw.resolve(strict=True)
    for output in (Path(portable_output), Path(private_output)):
        resolved_parent = output.parent.resolve(strict=False)
        if resolved_parent == raw_resolved or resolved_parent.is_relative_to(raw_resolved):
            raise IntakeBlocked("output beneath raw source root is forbidden")

    planck = raw / "planck_data"
    cmb_dir = raw / "planck_ffp10/smica/cmb_mc"
    noise_dir = raw / "planck_ffp10/smica/noise_mc"
    commander_dir = raw / "planck_ffp10/commander/cmb_mc"
    for directory in (planck, cmb_dir, noise_dir, commander_dir):
        if not directory.is_dir() or directory.is_symlink():
            raise IntakeBlocked(f"required inventory directory invalid: {directory}")
    guarded_roots = [raw, planck, cmb_dir, noise_dir, commander_dir]
    roots_before = [_source_root_identity(path) for path in guarded_roots]

    selected_paths = [_contained(planck / name, raw) for name in REQUIRED_PLANCK]
    cmb_ids, cmb_paths = _ids(cmb_dir, re.compile(r"dx12_v3_smica_cmb_mc_(\d{5})_raw\.fits"))
    noise_ids, noise_paths = _ids(noise_dir, re.compile(r"dx12_v3_smica_noise_mc_(\d{5})_raw\.fits"))
    complete_ids, complete_paths = _ids(commander_dir, re.compile(r"dx12_v3_commander_cmb_mc_(\d{5})_raw\.fits"))
    partial_ids, partial_paths = _ids(commander_dir, re.compile(r"dx12_v3_commander_cmb_mc_(\d{5})_raw\.fits\.partial"))
    if cmb_ids != EXPECTED_CMB or noise_ids != EXPECTED_NOISE:
        raise IntakeBlocked("BLOCKED_INVALID_FFP10_INVENTORY: SMICA ID set differs")
    if complete_ids != EXPECTED_COMMANDER_COMPLETE or partial_ids != EXPECTED_COMMANDER_PARTIAL:
        raise IntakeBlocked("BLOCKED_INVALID_FFP10_INVENTORY: Commander ID set differs")

    row_00818_path = cmb_dir / "dx12_v3_smica_cmb_mc_00818_raw.fits"
    row_00818 = adjudicate_00818(row_00818_path) if verify_selected else {
        "state": "NOT_VERIFIED", "decision_basis": "NONE"
    }
    selected_entries = [
        _manifest_entry(path, raw, route="DOWNSTREAM_SELECTED_HASH_ON_FIRST_SCIENTIFIC_READ")
        for path in selected_paths
    ]
    selected_entries.append(_manifest_entry(row_00818_path, raw, route="ADMITTED_ROW_00818"))
    selected_entries[-1]["sha256"] = row_00818.get("sha256")
    selected_entries[-1]["checksum"] = row_00818.get("sha256")
    selected_entries[-1]["checksum_status"] = "STREAMING_SHA256_VERIFIED_AT_INTAKE"

    npipe_root = raw / "planck_npipe_pr4"
    npipe_payloads = sorted(path for path in npipe_root.rglob("*") if path.is_file()) if npipe_root.is_dir() else []
    hsc_root = raw / "hsc_kids"
    hsc_payloads = sorted(path for path in hsc_root.rglob("*") if path.is_file()) if hsc_root.is_dir() else []
    forbidden_hsc = [path for path in hsc_payloads if re.search(r"(?:^|[_-])(hsc|sacc)(?:[_\-.]|$)", path.name, re.I)]
    if forbidden_hsc:
        raise IntakeBlocked("hsc_kids unexpectedly contains HSC/SACC payload")

    summary = {
        "format": "PLANCK_MES_IRREP_INTAKE_SUMMARY_V1",
        "work_unit": "PMG-WU-004",
        "raw_root": str(raw),
        "smica_cmb_mc": {"count": len(cmb_ids), "missing_ids": sorted({f"{i:05d}" for i in range(1000)} - cmb_ids), "state": "EXACT"},
        "smica_noise_mc": {"count": len(noise_ids), "missing_ids": sorted(EXPECTED_NOISE - noise_ids), "state": "EXACT"},
        "commander_cmb_mc": {"complete_ids": sorted(complete_ids), "quarantined_partial_ids": sorted(partial_ids), "finite_null_eligible": False},
        "row_00818": row_00818,
        "planck_npipe_pr4": {"payload_count": len(npipe_payloads), "state": "BLOCKED_MISSING_DATA" if not npipe_payloads else "PRESENT_UNEXPECTEDLY"},
        "hsc_kids": {"payload_count": len(hsc_payloads), "admitted_hsc_sacc_count": len(forbidden_hsc), "state": "UNAVAILABLE_KIDS_ONLY"},
        "raw_data_mutation": False,
        "science_rank_generated": False,
        "claim_promotion": False,
    }
    if npipe_payloads:
        raise IntakeBlocked("NPIPE payload is present contrary to registered absent route")

    private_entries = [
        _manifest_entry(path, raw, route="SMICA_CMB_POOL") for path in cmb_paths
    ] + [
        _manifest_entry(path, raw, route="SMICA_NOISE_POOL") for path in noise_paths
    ] + [
        _manifest_entry(path, raw, route="COMMANDER_DESCRIPTIVE_ONLY") for path in complete_paths
    ] + [
        {
            **_manifest_entry(path, raw, route="QUARANTINED_BEFORE_FITS_OPEN"),
            "partial": True,
        }
        for path in partial_paths
    ]
    private_manifest = {
        "format": "PLANCK_MES_IRREP_PRIVATE_INTAKE_MANIFEST_V1",
        "raw_root": str(raw),
        "entry_count": len(private_entries),
        "entries": private_entries,
        "hash_policy": "ONLY_00818_HASHED_DURING_INTAKE",
    }
    _write_json(Path(private_output), private_manifest)
    Path(private_output).chmod(0o600)
    private_sha = _sha256(Path(private_output))

    portable_output = Path(portable_output)
    _write_json(portable_output / "intake_summary.json", summary)
    selected_manifest = {
        "format": "PLANCK_MES_IRREP_SELECTED_INPUT_MANIFEST_V1",
        "inputs": selected_entries,
        "row_00818": row_00818,
        "private_manifest_sha256": private_sha,
    }
    _write_json(portable_output / "selected_input_manifest.json", selected_manifest)
    route = {
        "format": "PLANCK_MES_IRREP_ROUTE_RECEIPT_V1",
        "smica_paired300": "ELIGIBLE_AFTER_WU004",
        "commander": "DESCRIPTIVE_COMPLETE_00000_TO_00002_ONLY",
        "commander_partial": "QUARANTINED",
        "planck_npipe_pr4": "BLOCKED_MISSING_DATA",
        "hsc_or_sacc_under_hsc_kids": "UNAVAILABLE_KIDS_ONLY",
    }
    _write_json(portable_output / "route_receipt.json", route)

    post_entries = [stat_identity(path) for path in selected_paths + [row_00818_path]]
    pre_entries = [entry["stat_identity"] for entry in selected_entries]
    if post_entries != pre_entries:
        raise IntakeBlocked("selected source stat identity mutated during intake")
    roots_after = [_source_root_identity(path) for path in guarded_roots]
    if roots_after != roots_before:
        raise IntakeBlocked("guarded Planck source-root metadata mutated during intake")
    terminal = {
        "format": "PLANCK_MES_IRREP_INTAKE_TERMINAL_V1",
        "work_unit": "PMG-WU-004",
        "state": "EXECUTED_PENDING_REVIEW",
        "base_git_head": BASE_GIT_HEAD,
        "real_host_execution": True,
        "private_manifest_path": str(private_output),
        "private_manifest_sha256": private_sha,
        "pre_post_immutability_receipt": {
            "state": "MATCH",
            "guarded_source_roots": roots_before,
            "selected_source_files": pre_entries,
        },
        "raw_data_mutation": False,
        "science_rank_generated": False,
        "claim_promotion": False,
        "next_executable_action": "FRESH_READ_ONLY_REVIEW",
        "unresolved_blockers": ["FRESH_READ_ONLY_REVIEW_PENDING"],
    }
    _write_json(portable_output / "terminal.json", terminal)
    return {"state": "SUCCEEDED", "summary": summary, "private_manifest_sha256": private_sha}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--workdir", type=Path, required=True)
    parser.add_argument("--execute", action="store_true")
    parser.add_argument("--portable-output", type=Path, default=Path("docs/generated/planck_mes_irrep_inventory"))
    parser.add_argument("--private-output", type=Path)
    args = parser.parse_args()
    if not args.execute:
        raise SystemExit("--execute is required")
    private = args.private_output or args.workdir / "analysis/planck_mes_irrep/intake_manifest.json"
    result = inspect_planck_mes_irrep_data(
        workdir=args.workdir, portable_output=args.portable_output,
        private_output=private, verify_selected=True,
    )
    print(json.dumps(result, sort_keys=True))


if __name__ == "__main__":
    main()
