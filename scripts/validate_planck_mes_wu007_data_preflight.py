#!/usr/bin/env python3
"""Read-only data-acquisition closure and PMG-WU-007 transition preflight.

This command performs metadata-only checks. It never opens FITS payloads,
never downloads data, and never writes beneath the raw/download source roots.
It separates three states that must not be conflated:

* remote acquisition completeness;
* local ``obs_bundle`` placement/conversion gaps; and
* scientific claim admission for the PMG-WU-005 -> 006 -> 007 chain.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import sys
from typing import Iterable, Mapping, Sequence


REPO_ROOT = Path(__file__).resolve().parents[1]
FORMAT = "PLANCK_MES_WU007_DATA_PREFLIGHT_V1"
OPERATOR_REPORT_TIME = "2026-08-29T00:21:00+09:00"
KNOWN_MISSING_SMICA_CMB_ID = 970
EXPECTED_SMICA_CMB_IDS = frozenset(range(1000)) - {KNOWN_MISSING_SMICA_CMB_ID}
EXPECTED_SMICA_NOISE_IDS = frozenset(range(300))
EXPECTED_COMMANDER_COMPLETE_IDS = frozenset(range(3))
ALLOWED_COMMANDER_PARTIAL_IDS = frozenset(range(3, 7))


class PreflightError(RuntimeError):
    """Raised when a read-only preflight invariant is violated."""


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(8 * 1024 * 1024), b""):
            digest.update(chunk)
    return "sha256:" + digest.hexdigest()


def _regular_file(path: Path, *, label: str) -> Path:
    path = Path(path)
    if (
        not path.is_absolute()
        or path.is_symlink()
        or not path.is_file()
        or path.resolve() != path
        or path.stat().st_size <= 0
    ):
        raise PreflightError(f"{label} is not one absolute regular non-empty file: {path}")
    return path


def _regular_directory(path: Path, *, label: str) -> Path:
    path = Path(path)
    if (
        not path.is_absolute()
        or path.is_symlink()
        or not path.is_dir()
        or path.resolve() != path
    ):
        raise PreflightError(f"{label} is not one absolute regular directory: {path}")
    return path


def _collect_ids(
    root: Path,
    *,
    pattern: re.Pattern[str],
    label: str,
) -> dict[int, Path]:
    root = _regular_directory(root, label=f"{label} root")
    rows: dict[int, Path] = {}
    for candidate in root.iterdir():
        match = pattern.fullmatch(candidate.name)
        if match is None:
            continue
        index = int(match.group(1))
        if index in rows:
            raise PreflightError(f"{label} contains duplicate ID {index:05d}")
        rows[index] = _regular_file(candidate, label=f"{label} {index:05d}")
    return rows


def _require_exact_ids(
    rows: Mapping[int, Path],
    expected: frozenset[int],
    *,
    label: str,
) -> None:
    actual = frozenset(rows)
    missing = sorted(expected - actual)
    unexpected = sorted(actual - expected)
    if missing or unexpected:
        pieces: list[str] = []
        if missing:
            pieces.append("missing=" + ",".join(f"{value:05d}" for value in missing))
        if unexpected:
            pieces.append(
                "unexpected=" + ",".join(f"{value:05d}" for value in unexpected)
            )
        raise PreflightError(f"{label} ID surface drifted: {' '.join(pieces)}")


def inspect_planck_wu007_inputs(workdir: Path) -> dict[str, object]:
    """Check the exact WU-007 Planck inventory without opening FITS payloads."""

    workdir = _regular_directory(Path(workdir), label="workdir")
    raw = _regular_directory(workdir / "raw", label="raw root")
    planck = _regular_directory(raw / "planck_data", label="Planck data root")
    smica_cmb_root = raw / "planck_ffp10/smica/cmb_mc"
    smica_noise_root = raw / "planck_ffp10/smica/noise_mc"
    commander_root = raw / "planck_ffp10/commander/cmb_mc"

    observed = {
        "smica": _regular_file(
            planck / "COM_CMB_IQU-smica_2048_R3.00_full.fits",
            label="observed SMICA",
        ),
        "commander": _regular_file(
            planck / "COM_CMB_IQU-commander_2048_R3.00_full.fits",
            label="observed Commander",
        ),
        "temperature_mask": _regular_file(
            planck / "COM_Mask_CMB-common-Mask-Int_2048_R3.00.fits",
            label="temperature mask",
        ),
    }

    smica_cmb = _collect_ids(
        smica_cmb_root,
        pattern=re.compile(r"dx12_v3_smica_cmb_mc_(\d{5})_raw\.fits"),
        label="SMICA CMB",
    )
    _require_exact_ids(smica_cmb, EXPECTED_SMICA_CMB_IDS, label="SMICA CMB")
    if KNOWN_MISSING_SMICA_CMB_ID in smica_cmb:
        raise PreflightError("SMICA CMB 00970 must remain the registered known-missing ID")

    smica_noise = _collect_ids(
        smica_noise_root,
        pattern=re.compile(r"dx12_v3_smica_noise_mc_(\d{5})_raw\.fits"),
        label="SMICA noise",
    )
    _require_exact_ids(
        smica_noise,
        EXPECTED_SMICA_NOISE_IDS,
        label="SMICA noise",
    )

    commander_complete = _collect_ids(
        commander_root,
        pattern=re.compile(r"dx12_v3_commander_cmb_mc_(\d{5})_raw\.fits"),
        label="Commander complete CMB",
    )
    _require_exact_ids(
        commander_complete,
        EXPECTED_COMMANDER_COMPLETE_IDS,
        label="Commander complete CMB",
    )
    commander_partial = _collect_ids(
        commander_root,
        pattern=re.compile(
            r"dx12_v3_commander_cmb_mc_(\d{5})_raw\.fits\.partial"
        ),
        label="Commander partial CMB",
    )
    unexpected_partial = sorted(set(commander_partial) - ALLOWED_COMMANDER_PARTIAL_IDS)
    if unexpected_partial:
        raise PreflightError(
            "Commander partial quarantine contains unexpected IDs: "
            + ",".join(f"{value:05d}" for value in unexpected_partial)
        )
    if set(commander_complete) & ALLOWED_COMMANDER_PARTIAL_IDS:
        raise PreflightError("Commander partial IDs were promoted to complete FITS files")

    return {
        "access_mode": "METADATA_ONLY_NO_FITS_PAYLOAD_OPEN",
        "observed_inputs": {
            role: {
                "filename": path.name,
                "byte_size": path.stat().st_size,
            }
            for role, path in observed.items()
        },
        "smica_cmb": {
            "count": len(smica_cmb),
            "expected_count": 999,
            "known_missing_ids": ["00970"],
            "state": "EXACT_RELEASED_SURFACE",
        },
        "smica_noise": {
            "count": len(smica_noise),
            "expected_count": 300,
            "state": "EXACT_RELEASED_SURFACE",
        },
        "commander": {
            "complete_ids": [f"{value:05d}" for value in sorted(commander_complete)],
            "partial_quarantine_ids": [
                f"{value:05d}" for value in sorted(commander_partial)
            ],
            "partial_open_authorized": False,
            "finite_rank_authorized": False,
            "state": "THREE_COMPLETE_DESCRIPTIVE_ROWS",
        },
    }


def _deduplicate_paths(paths: Iterable[Path]) -> tuple[Path, ...]:
    values: dict[str, Path] = {}
    for path in paths:
        try:
            resolved = path.resolve(strict=True)
        except FileNotFoundError:
            continue
        values[str(resolved)] = resolved
    return tuple(values[key] for key in sorted(values))


def _find_unique_named_file(
    name: str,
    *,
    roots: Sequence[Path],
    excluded_root: Path,
) -> Path | None:
    direct: list[Path] = []
    recursive: list[Path] = []
    excluded = excluded_root.resolve(strict=False)
    for root in roots:
        root = Path(root).resolve(strict=False)
        candidate = root / name
        if candidate.is_file() and not candidate.is_symlink():
            direct.append(candidate)
    found = _deduplicate_paths(direct)
    if not found:
        for root in roots:
            root = Path(root).resolve(strict=False)
            if not root.is_dir() or root.is_symlink():
                continue
            for candidate in root.rglob(name):
                try:
                    resolved = candidate.resolve(strict=True)
                except FileNotFoundError:
                    continue
                if resolved == excluded or resolved.is_relative_to(excluded):
                    continue
                if candidate.is_file() and not candidate.is_symlink():
                    recursive.append(candidate)
        found = _deduplicate_paths(recursive)
    if not found:
        return None
    if len(found) > 1:
        hashes = {_sha256(path) for path in found}
        if len(hashes) != 1:
            raise PreflightError(
                f"ambiguous nonidentical scalar sources for {name}: "
                + ",".join(str(path) for path in found)
            )
    return found[0]


def _first_regular(candidates: Sequence[Path]) -> Path | None:
    for path in candidates:
        if path.is_file() and not path.is_symlink() and path.stat().st_size > 0:
            return path.resolve()
    return None


def inspect_obs_bundle_local_gaps(
    *,
    workdir: Path,
    repo_root: Path,
    scalar_roots: Sequence[Path] = (),
) -> dict[str, object]:
    """Classify the known 12 inventory gaps as present, local, or unresolved."""

    workdir = _regular_directory(Path(workdir), label="workdir")
    repo_root = _regular_directory(Path(repo_root), label="repository root")
    obs_bundle = workdir / "obs_bundle"

    targets: list[tuple[str, Path, Sequence[Path] | None, str | None]] = []
    for spectrum in ("tt", "te", "ee"):
        targets.append(
            (
                f"act.dr6.{spectrum}",
                obs_bundle / f"cmb/powerspectra/act_dr6_{spectrum}.npz",
                (
                    workdir / f"htt_extracted/act_dr6_{spectrum}_bandpowers.npz",
                    workdir / f"compact_products/act_dr6_{spectrum}_bandpowers.npz",
                ),
                None,
            )
        )

    desi = (
        ("desi.bgs.ngc", "BGS_ANY_NGC", "bgs_ngc"),
        ("desi.bgs.sgc", "BGS_ANY_SGC", "bgs_sgc"),
        ("desi.lrg.ngc", "LRG_NGC", "lrg_ngc"),
        ("desi.lrg.sgc", "LRG_SGC", "lrg_sgc"),
        ("desi.qso.ngc", "QSO_NGC", "qso_ngc"),
        ("desi.qso.sgc", "QSO_SGC", "qso_sgc"),
    )
    for dataset_id, source_stem, destination_stem in desi:
        targets.append(
            (
                dataset_id,
                obs_bundle / f"lss/desi_y1/{destination_stem}.npz",
                (
                    workdir
                    / f"compact_products/desi/{source_stem}_clustering_extended.npz",
                    workdir
                    / f"compact_products/desi/{source_stem}_clustering_minimal.npz",
                ),
                None,
            )
        )

    scalar_names = (
        ("scalars.obs_defaults", "obs_defaults.json", "obs_defaults.json"),
        (
            "scalars.obs_defaults_watkins2023",
            "obs_defaults_watkins2023.json",
            "obs_defaults_watkins2023.json",
        ),
        (
            "scalars.obs_defaults_courtois2025",
            "obs_defaults_CF4pp.json",
            "obs_defaults_courtois2025.json",
        ),
    )
    search_roots = tuple(
        dict.fromkeys(
            Path(value).resolve(strict=False)
            for value in (*scalar_roots, repo_root, workdir, workdir.parent)
        )
    )
    for dataset_id, source_name, destination_name in scalar_names:
        targets.append(
            (
                dataset_id,
                obs_bundle / f"scalars/{destination_name}",
                None,
                source_name,
            )
        )

    rows: list[dict[str, object]] = []
    counts = {
        "PRESENT": 0,
        "LOCAL_PLACEMENT_REQUIRED": 0,
        "UNRESOLVED_LOCAL_SOURCE": 0,
    }
    for dataset_id, destination, candidates, scalar_name in targets:
        if destination.is_file() and not destination.is_symlink():
            state = "PRESENT"
            source = destination.resolve()
        else:
            if scalar_name is not None:
                source = _find_unique_named_file(
                    scalar_name,
                    roots=search_roots,
                    excluded_root=obs_bundle,
                )
            else:
                source = _first_regular(tuple(candidates or ()))
            state = (
                "LOCAL_PLACEMENT_REQUIRED"
                if source is not None
                else "UNRESOLVED_LOCAL_SOURCE"
            )
        counts[state] += 1
        rows.append(
            {
                "dataset_id": dataset_id,
                "destination": str(destination),
                "source": None if source is None else str(source),
                "state": state,
            }
        )

    unresolved = counts["UNRESOLVED_LOCAL_SOURCE"]
    return {
        "target_count": len(rows),
        "present_count": counts["PRESENT"],
        "local_placement_required_count": counts["LOCAL_PLACEMENT_REQUIRED"],
        "unresolved_local_source_count": unresolved,
        "remote_download_required_count": 0 if unresolved == 0 else None,
        "classification": (
            "NO_REMOTE_DOWNLOAD_REQUIRED_LOCAL_PLACEMENT_ONLY"
            if unresolved == 0
            else "BLOCKED_UNRESOLVED_LOCAL_SOURCE_NOT_CLASSIFIED_AS_DOWNLOAD"
        ),
        "rows": rows,
    }


def _load_json(path: Path, *, label: str) -> dict[str, object]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise PreflightError(f"{label} is not readable JSON: {path}") from exc
    if not isinstance(value, dict):
        raise PreflightError(f"{label} must be a JSON mapping")
    return value


def inspect_repository_transition(repo_root: Path) -> dict[str, object]:
    """Read durable PMG terminals without promoting the upstream chain."""

    repo_root = _regular_directory(Path(repo_root), label="repository root")
    wu004 = _load_json(
        repo_root / "docs/generated/planck_mes_irrep_inventory/terminal.json",
        label="PMG-WU-004 terminal",
    )
    wu006 = _load_json(
        repo_root / "docs/generated/planck_mes_irrep_analysis/terminal.json",
        label="PMG-WU-006 terminal",
    )
    if (
        wu004.get("work_unit") != "PMG-WU-004"
        or wu004.get("state") != "SUCCEEDED"
        or wu004.get("next_executable_action") != "PMG-WU-005"
    ):
        raise PreflightError("PMG-WU-004 accepted terminal drifted")
    if (
        wu006.get("work_unit") != "PMG-WU-006"
        or wu006.get("state") != "SUCCEEDED"
        or wu006.get("replay_status") != "MATCH"
        or wu006.get("raw_data_read_or_mutated") is not False
    ):
        raise PreflightError("PMG-WU-006 branch-local execution terminal drifted")
    return {
        "wu004": {
            "state": "ACCEPTED",
            "correct_precondition_path": (
                "docs/generated/planck_mes_irrep_inventory/terminal.json"
            ),
        },
        "wu006": {
            "state": "EXECUTED_CONDITIONALLY_VALID",
            "branch_local_terminal": "SUCCEEDED_REPLAY_MATCH",
            "upstream_admission": "PENDING_PMG_WU005_REBIND",
        },
        "wu007": {
            "execution_permission": "EXPLORATORY_NONAUTHORITATIVE",
            "claim_admission": "BLOCKED_PENDING_PMG_WU005_REBIND",
            "required_terminal_state_before_rebind": (
                "EXECUTED_EXPLORATORY_NONAUTHORITATIVE"
            ),
        },
    }


def build_preflight(
    *,
    workdir: Path,
    repo_root: Path,
    scalar_roots: Sequence[Path] = (),
) -> dict[str, object]:
    planck = inspect_planck_wu007_inputs(workdir)
    obs_bundle = inspect_obs_bundle_local_gaps(
        workdir=workdir,
        repo_root=repo_root,
        scalar_roots=scalar_roots,
    )
    transition = inspect_repository_transition(repo_root)
    unresolved = int(obs_bundle["unresolved_local_source_count"])
    return {
        "format": FORMAT,
        "operator_report_time": OPERATOR_REPORT_TIME,
        "state": "PASS" if unresolved == 0 else "BLOCKED_LOCAL_SOURCE_GAP",
        "download": {
            "mandatory_remote_download_count": 0 if unresolved == 0 else None,
            "active_downloads": 0 if unresolved == 0 else None,
            "eta_minutes": 0 if unresolved == 0 else None,
            "classification": (
                "COMPLETE"
                if unresolved == 0
                else "NOT_REOPENED_UNRESOLVED_LOCAL_SOURCE"
            ),
        },
        "planck_wu007": planck,
        "obs_bundle": obs_bundle,
        "transition": transition,
        "raw_data_mutation": False,
        "tracked_repository_mutation": False,
    }


def _write_output(path: Path, payload: Mapping[str, object], *, workdir: Path) -> None:
    path = Path(path)
    raw = (Path(workdir) / "raw").resolve()
    resolved_parent = path.parent.resolve(strict=False)
    if resolved_parent == raw or resolved_parent.is_relative_to(raw):
        raise PreflightError("preflight output beneath the raw source root is forbidden")
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.{os.getpid()}.tmp")
    encoded = (
        json.dumps(payload, indent=2, sort_keys=True, allow_nan=False) + "\n"
    ).encode("utf-8")
    try:
        with temporary.open("xb") as handle:
            handle.write(encoded)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
    finally:
        temporary.unlink(missing_ok=True)


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--workdir", type=Path, required=True)
    parser.add_argument("--repo-root", type=Path, default=REPO_ROOT)
    parser.add_argument("--scalar-root", type=Path, action="append", default=[])
    parser.add_argument("--json-output", type=Path)
    args = parser.parse_args(argv)
    try:
        payload = build_preflight(
            workdir=args.workdir.resolve(),
            repo_root=args.repo_root.resolve(),
            scalar_roots=tuple(path.resolve() for path in args.scalar_root),
        )
        if args.json_output is not None:
            _write_output(
                args.json_output.resolve(), payload, workdir=args.workdir.resolve()
            )
    except Exception as exc:
        print(
            json.dumps(
                {
                    "format": FORMAT,
                    "state": "BLOCKED",
                    "error_type": type(exc).__name__,
                    "error": str(exc),
                },
                sort_keys=True,
            ),
            file=sys.stderr,
        )
        return 3
    print(json.dumps(payload, indent=2, sort_keys=True, allow_nan=False))
    return 0 if payload["state"] == "PASS" else 3


if __name__ == "__main__":
    raise SystemExit(main())
