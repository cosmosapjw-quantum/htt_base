#!/usr/bin/env python3
"""Read-only PMG-WU-007 preflight for the official SMICA CMB-only 999 route.

This module performs no scientific scoring. It validates the exact local inventory,
root containment, the special row 00818 FITS structure and digest, and pre/post stat
immutability. It never downloads, repairs, copies, or writes beneath raw roots.
"""
from __future__ import annotations

import argparse
from dataclasses import asdict, dataclass
import hashlib
import json
from pathlib import Path
import re
import stat
import sys
from typing import Any, Mapping, Sequence

FORMAT = "PLANCK_MES_SMICA999_PREFLIGHT_V1"
CMB_PATTERN = re.compile(r"^dx12_v3_smica_cmb_mc_(\d{5})_raw\.fits$")
NOISE_PATTERN = re.compile(r"^dx12_v3_smica_noise_mc_(\d{5})_raw\.fits$")
EXPECTED_CMB_IDS = tuple(f"{i:05d}" for i in range(1000) if i != 970)
EXPECTED_NOISE_IDS = tuple(f"{i:05d}" for i in range(300))
OBSERVED_NAME = "COM_CMB_IQU-smica_2048_R3.00_full.fits"
MASK_NAME = "COM_Mask_CMB-common-Mask-Int_2048_R3.00.fits"
SPECIAL_ID = "00818"
BLOCK = 2880
CARD = 80


class PreflightError(RuntimeError):
    """Fail-closed inventory or I/O contract violation."""


@dataclass(frozen=True)
class StatIdentity:
    path: str
    resolved_path: str
    device: int
    inode: int
    mode: int
    size: int
    mtime_ns: int


def _json_dump(path: Path, payload: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _sha256(path: Path, chunk_size: int = 8 * 1024 * 1024) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while chunk := handle.read(chunk_size):
            digest.update(chunk)
    return digest.hexdigest()


def _content_id(payload: Mapping[str, Any]) -> str:
    raw = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()
    return "sha256:" + hashlib.sha256(raw).hexdigest()


def _is_relative_to(path: Path, root: Path) -> bool:
    try:
        path.relative_to(root)
        return True
    except ValueError:
        return False


def _require_contained_file(path: Path, root: Path) -> Path:
    resolved = path.resolve(strict=True)
    root_resolved = root.resolve(strict=True)
    if not _is_relative_to(resolved, root_resolved):
        raise PreflightError(f"symlink/root escape: {path} -> {resolved}")
    st = resolved.stat()
    if not stat.S_ISREG(st.st_mode):
        raise PreflightError(f"not a regular file: {path}")
    return resolved


def _stat_identity(path: Path, root: Path) -> StatIdentity:
    resolved = _require_contained_file(path, root)
    st = resolved.stat()
    return StatIdentity(
        path=str(path),
        resolved_path=str(resolved),
        device=int(st.st_dev),
        inode=int(st.st_ino),
        mode=int(st.st_mode),
        size=int(st.st_size),
        mtime_ns=int(st.st_mtime_ns),
    )


def _parse_card_value(raw: str) -> Any:
    value = raw.split("/", 1)[0].strip()
    if not value:
        return None
    if value.startswith("'"):
        end = value.find("'", 1)
        return value[1:end if end >= 0 else None].rstrip()
    if value in {"T", "F"}:
        return value == "T"
    normalized = value.replace("D", "E")
    try:
        if any(token in normalized for token in ".Ee"):
            return float(normalized)
        return int(normalized)
    except ValueError:
        return value


def _read_header(handle) -> tuple[dict[str, Any], int]:
    cards: list[str] = []
    consumed = 0
    found_end = False
    while not found_end:
        block = handle.read(BLOCK)
        if len(block) != BLOCK:
            raise PreflightError("truncated FITS header")
        consumed += BLOCK
        try:
            text = block.decode("ascii")
        except UnicodeDecodeError as exc:
            raise PreflightError("non-ASCII FITS header") from exc
        for offset in range(0, BLOCK, CARD):
            card = text[offset : offset + CARD]
            cards.append(card)
            if card.startswith("END"):
                found_end = True
                break
        if consumed > 1024 * BLOCK:
            raise PreflightError("unbounded FITS header")
    values: dict[str, Any] = {}
    for card in cards:
        keyword = card[:8].strip()
        if not keyword or keyword in {"COMMENT", "HISTORY", "END"}:
            continue
        if len(card) >= 10 and card[8] == "=":
            values[keyword] = _parse_card_value(card[10:])
    return values, consumed


def inspect_fits_structure(path: Path, root: Path, max_hdus: int = 32) -> dict[str, Any]:
    """Inspect FITS HDU structure without interpreting the scientific map payload."""
    resolved = _require_contained_file(path, root)
    size = resolved.stat().st_size
    hdus: list[dict[str, Any]] = []
    with resolved.open("rb") as handle:
        for index in range(max_hdus):
            if handle.tell() == size:
                break
            if handle.tell() > size:
                raise PreflightError("FITS cursor exceeded file size")
            header, header_bytes = _read_header(handle)
            if index == 0 and header.get("SIMPLE") is not True:
                raise PreflightError("FITS primary header lacks SIMPLE=T")
            bitpix = int(header.get("BITPIX", 0))
            naxis = int(header.get("NAXIS", 0))
            if naxis < 0 or naxis > 999:
                raise PreflightError(f"invalid NAXIS={naxis}")
            dimensions = [int(header.get(f"NAXIS{i}", 0)) for i in range(1, naxis + 1)]
            if any(value < 0 for value in dimensions):
                raise PreflightError("negative FITS axis length")
            pcount = int(header.get("PCOUNT", 0))
            gcount = int(header.get("GCOUNT", 1))
            elements = 0 if naxis == 0 else 1
            for value in dimensions:
                elements *= value
            data_bytes = (abs(bitpix) // 8) * elements + pcount
            data_bytes *= max(gcount, 1)
            padded = ((data_bytes + BLOCK - 1) // BLOCK) * BLOCK
            hdu = {
                "index": index,
                "xtension": header.get("XTENSION", "PRIMARY"),
                "bitpix": bitpix,
                "naxis": naxis,
                "dimensions": dimensions,
                "pcount": pcount,
                "gcount": gcount,
                "header_bytes": header_bytes,
                "data_bytes": data_bytes,
            }
            hdus.append(hdu)
            next_pos = handle.tell() + padded
            if next_pos > size:
                raise PreflightError("FITS data extent exceeds file size")
            handle.seek(next_pos)
    if not hdus:
        raise PreflightError("FITS file has no HDU")
    total_extent = sum(
        item["header_bytes"] + ((item["data_bytes"] + BLOCK - 1) // BLOCK) * BLOCK
        for item in hdus
    )
    if total_extent > size:
        raise PreflightError("invalid FITS total extent")
    if not any(item["naxis"] > 0 or str(item["xtension"]).strip() for item in hdus):
        raise PreflightError("FITS file has no data-bearing or extension HDU")
    return {
        "format": "FITS_STRUCTURE_RECEIPT_V1",
        "file_size": size,
        "hdu_count": len(hdus),
        "hdus": hdus,
    }


def _enumerate_ids(directory: Path, pattern: re.Pattern[str]) -> tuple[dict[str, Path], list[str]]:
    found: dict[str, Path] = {}
    duplicates: list[str] = []
    for entry in directory.iterdir():
        match = pattern.match(entry.name)
        if not match:
            continue
        row_id = match.group(1)
        if row_id in found:
            duplicates.append(row_id)
        found[row_id] = entry
    return found, sorted(set(duplicates))


def _require_no_partial_files(directory: Path) -> None:
    partials = sorted(
        entry.name for entry in directory.iterdir()
        if ".partial" in entry.name or entry.name.endswith(".part")
    )
    if partials:
        raise PreflightError(f"partial files present in Planck FFP10 route: {partials[:8]}")


def _compare_exact_ids(found: Mapping[str, Path], expected: Sequence[str], label: str) -> None:
    found_ids = set(found)
    expected_ids = set(expected)
    missing = sorted(expected_ids - found_ids)
    extra = sorted(found_ids - expected_ids)
    if missing or extra:
        raise PreflightError(f"{label} inventory mismatch: missing={missing[:12]} extra={extra[:12]}")


def _require_output_location(path: Path, *, workdir: Path, raw_root: Path, label: str) -> Path:
    resolved_parent = path.parent.resolve(strict=False)
    raw_resolved = raw_root.resolve(strict=True)
    if _is_relative_to(resolved_parent, raw_resolved):
        raise PreflightError(f"{label} is inside raw root: {path}")
    if label == "private output":
        analysis = (workdir / "analysis").resolve(strict=False)
        if not _is_relative_to(resolved_parent, analysis):
            raise PreflightError(f"private output must be below workdir/analysis: {path}")
    return path


def build_preflight(*, workdir: Path, output_dir: Path, private_output: Path, execute: bool) -> dict[str, Any]:
    workdir = workdir.resolve(strict=True)
    raw_root = (workdir / "raw").resolve(strict=True)
    ffp10 = (raw_root / "planck_ffp10").resolve(strict=True)
    planck_data = (raw_root / "planck_data").resolve(strict=True)
    if not _is_relative_to(ffp10, raw_root) or not _is_relative_to(planck_data, raw_root):
        raise PreflightError("declared Planck roots escape raw root")
    if not ffp10.is_dir() or not planck_data.is_dir():
        raise PreflightError("required Planck raw directories are absent")
    _require_output_location(output_dir / "preflight_summary.json", workdir=workdir, raw_root=raw_root, label="portable output")
    _require_output_location(private_output, workdir=workdir, raw_root=raw_root, label="private output")

    cmb, cmb_duplicates = _enumerate_ids(ffp10, CMB_PATTERN)
    noise, noise_duplicates = _enumerate_ids(ffp10, NOISE_PATTERN)
    if cmb_duplicates or noise_duplicates:
        raise PreflightError(f"duplicate IDs: cmb={cmb_duplicates[:8]} noise={noise_duplicates[:8]}")
    _compare_exact_ids(cmb, EXPECTED_CMB_IDS, "SMICA CMB")
    _compare_exact_ids(noise, EXPECTED_NOISE_IDS, "SMICA noise availability")
    _require_no_partial_files(ffp10)
    if "00970" in cmb:
        raise PreflightError("known-missing CMB row 00970 must not be synthesized or admitted")
    if SPECIAL_ID not in cmb:
        raise PreflightError("required special row 00818 is missing")

    observed = planck_data / OBSERVED_NAME
    mask = planck_data / MASK_NAME
    selected_paths = [observed, mask] + [cmb[row_id] for row_id in EXPECTED_CMB_IDS]
    before = [_stat_identity(path, raw_root) for path in selected_paths]

    special_path = cmb[SPECIAL_ID]
    special_structure = inspect_fits_structure(special_path, raw_root)
    special_digest = _sha256(_require_contained_file(special_path, raw_root))

    after = [_stat_identity(path, raw_root) for path in selected_paths]
    if before != after:
        raise PreflightError("selected raw input metadata changed during preflight")

    selected_manifest = {
        "format": "PLANCK_MES_SMICA999_SELECTED_INPUTS_V1",
        "null_ensemble": "FFP10_SMICA_CMB_ONLY_999",
        "row_order": ["PLANCK-PR3-SMICA-OBSERVED"] + [f"FFP10-SMICA-CMB-{row_id}" for row_id in EXPECTED_CMB_IDS],
        "observation": asdict(before[0]),
        "mask": asdict(before[1]),
        "null_rows": [
            {"row_id": row_id, **asdict(identity)}
            for row_id, identity in zip(EXPECTED_CMB_IDS, before[2:], strict=True)
        ],
        "noise_files_available_but_not_routed": len(noise),
        "noise_files_selected": 0,
    }
    selected_manifest["content_id"] = _content_id(selected_manifest)

    route_receipt = {
        "format": "PLANCK_MES_SMICA999_ROUTE_RECEIPT_V1",
        "observation_source": "REUSE_ACCEPTED_ONE_PASS_OBSERVATION_CARRIER",
        "null_product": "SMICA_CMB_ONLY",
        "null_count": 999,
        "expected_id_rule": "00000..00999 excluding only 00970",
        "known_missing": ["00970"],
        "row_00818": {
            "status": "ADMITTED_BY_FITS_STRUCTURE_AND_STREAMING_SHA256",
            "sha256": special_digest,
            "fits": special_structure,
        },
        "paired_noise_selected": 0,
        "downloads_performed": 0,
        "full_raw_tree_hash_performed": False,
        "scientific_rank_generated": False,
        "primary_replacement": False,
    }
    route_receipt["content_id"] = _content_id(route_receipt)

    summary = {
        "format": FORMAT,
        "state": "PREFLIGHT_SUCCEEDED" if execute else "DRY_RUN_VALIDATED",
        "work_unit": "PMG-WU-007",
        "real_host_preflight": bool(execute),
        "cmb_complete_count": len(cmb),
        "noise_available_count": len(noise),
        "noise_selected_count": 0,
        "special_row": SPECIAL_ID,
        "known_missing": ["00970"],
        "selected_input_manifest_content_id": selected_manifest["content_id"],
        "route_receipt_content_id": route_receipt["content_id"],
        "raw_data_mutation": False,
        "scientific_rank_generated": False,
        "wu007_scientific_execution_started": False,
        "next_executable_action": "IMPLEMENT_AND_EXECUTE_PMG-WU-007",
    }
    summary["content_id"] = _content_id(summary)

    private_manifest = {
        "format": "PLANCK_MES_SMICA999_PRIVATE_PREFLIGHT_V1",
        "portable_summary_content_id": summary["content_id"],
        "selected_inputs": [asdict(item) for item in before],
        "special_row_sha256": special_digest,
        "pre_post_stat_identity_match": True,
        "raw_data_mutation": False,
    }
    private_manifest["content_id"] = _content_id(private_manifest)

    if execute:
        output_dir.mkdir(parents=True, exist_ok=True)
        _json_dump(output_dir / "preflight_summary.json", summary)
        _json_dump(output_dir / "route_receipt.json", route_receipt)
        _json_dump(output_dir / "selected_input_manifest.json", selected_manifest)
        terminal = {
            "format": "PLANCK_MES_SMICA999_PREFLIGHT_TERMINAL_V1",
            "work_unit": "PMG-WU-007",
            "state": "PRECONDITION_SUCCEEDED",
            "real_host_preflight": True,
            "scientific_execution_state": "NOT_STARTED",
            "scientific_rank_generated": False,
            "raw_data_mutation": False,
            "downloads_performed": 0,
            "unresolved_blockers": [],
            "next_executable_action": "IMPLEMENT_AND_EXECUTE_PMG-WU-007",
            "objective_output_content_ids": {
                "preflight_summary.json": summary["content_id"],
                "route_receipt.json": route_receipt["content_id"],
                "selected_input_manifest.json": selected_manifest["content_id"],
            },
        }
        _json_dump(output_dir / "preflight_terminal.json", terminal)
        private_output.parent.mkdir(parents=True, exist_ok=True)
        _json_dump(private_output, private_manifest)
    return {
        "summary": summary,
        "route_receipt": route_receipt,
        "selected_input_manifest": selected_manifest,
        "private_manifest": private_manifest,
    }


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--workdir", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--private-output", type=Path, required=True)
    parser.add_argument("--execute", action="store_true")
    args = parser.parse_args(argv)
    try:
        result = build_preflight(
            workdir=args.workdir,
            output_dir=args.output_dir,
            private_output=args.private_output,
            execute=args.execute,
        )
    except (OSError, PreflightError) as exc:
        print(json.dumps({"status": "BLOCKED", "error": str(exc)}, indent=2), file=sys.stderr)
        return 1
    print(json.dumps(result["summary"], indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
