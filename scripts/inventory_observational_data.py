#!/usr/bin/env python3
"""Inventory repo-local observational datasets for manuscript figure planning."""
from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
import zipfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable

import numpy as np


REPO_ROOT = Path(__file__).resolve().parents[1]
COMMON_ROOT = REPO_ROOT / "htt" / "src"
if str(COMMON_ROOT) not in sys.path:
    sys.path.insert(0, str(COMMON_ROOT))

from common.artifact_manifest import validate_manifest_payload  # noqa: E402


DEFAULT_OUTPUT_JSON = Path("docs/generated/observational_data_inventory.json")
DEFAULT_OUTPUT_MD = Path("docs/generated/observational_data_inventory.md")


@dataclass(frozen=True)
class DatasetCandidate:
    dataset_id: str
    collection: str
    path: Path
    data_role: str
    claim_ceiling: str
    transfer_source: str = "none"
    sky_support_status: str = "not_directional"
    null_mock_status: str = "not_statistical"
    caveats: tuple[str, ...] = ()


def _repo_relative(path: Path, repo_root: Path) -> str:
    try:
        return path.relative_to(repo_root).as_posix()
    except ValueError:
        return path.as_posix()


def _sha256(path: Path) -> str:
    return "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()


def _stable_hash(payload: Any) -> str:
    encoded = json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")
    return "sha256:" + hashlib.sha256(encoded).hexdigest()


def _git_state(repo_root: Path) -> str:
    try:
        commit = subprocess.check_output(
            ["git", "rev-parse", "--short", "HEAD"],
            cwd=repo_root,
            text=True,
            stderr=subprocess.DEVNULL,
        ).strip()
        dirty = subprocess.run(
            ["git", "status", "--short"],
            cwd=repo_root,
            text=True,
            capture_output=True,
            check=False,
        ).stdout.strip()
    except (OSError, subprocess.CalledProcessError):
        return "git_state_unavailable"
    return f"{commit}+dirty" if dirty else commit


def _json_scalar(value: Any) -> Any:
    if isinstance(value, np.dtype):
        return str(value)
    if isinstance(value, np.integer):
        return int(value)
    if isinstance(value, np.floating):
        return float(value)
    if isinstance(value, np.ndarray):
        return value.tolist()
    if isinstance(value, Path):
        return value.as_posix()
    return value


def _npz_headers(path: Path) -> dict[str, dict[str, Any]]:
    out: dict[str, dict[str, Any]] = {}
    try:
        with zipfile.ZipFile(path) as zf:
            for member in sorted(zf.namelist()):
                if not member.endswith(".npy"):
                    continue
                key = Path(member).stem
                with zf.open(member) as handle:
                    version = np.lib.format.read_magic(handle)
                    if version == (1, 0):
                        shape, fortran_order, dtype = np.lib.format.read_array_header_1_0(handle)
                    elif version == (2, 0):
                        shape, fortran_order, dtype = np.lib.format.read_array_header_2_0(handle)
                    else:
                        shape, fortran_order, dtype = np.lib.format._read_array_header(handle, version)  # type: ignore[attr-defined]
                out[key] = {
                    "shape": [int(dim) for dim in shape],
                    "dtype": str(dtype),
                    "fortran_order": bool(fortran_order),
                }
    except (OSError, zipfile.BadZipFile, ValueError) as exc:
        out["_error"] = {"error": type(exc).__name__, "detail": str(exc)}
    return out


def _json_summary(path: Path) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return {"error": type(exc).__name__, "detail": str(exc)}
    if isinstance(payload, dict):
        return {
            "json_type": "dict",
            "top_level_keys": list(payload.keys())[:40],
            "n_top_level_keys": len(payload),
        }
    if isinstance(payload, list):
        return {
            "json_type": "list",
            "n_items": len(payload),
            "first_item_type": type(payload[0]).__name__ if payload else None,
        }
    return {"json_type": type(payload).__name__}


def _text_table_summary(path: Path) -> dict[str, Any]:
    try:
        with path.open("r", encoding="utf-8", errors="replace") as handle:
            lines = [line.rstrip("\n") for _, line in zip(range(8), handle)]
        n_lines = sum(1 for _ in path.open("r", encoding="utf-8", errors="replace"))
    except OSError as exc:
        return {"error": type(exc).__name__, "detail": str(exc)}
    return {
        "n_lines": n_lines,
        "head": lines,
    }


def _schema_for_path(path: Path) -> dict[str, Any]:
    suffix = path.suffix.lower()
    if not path.exists():
        return {}
    if suffix == ".npz":
        headers = _npz_headers(path)
        row_count = None
        first_key = next((key for key in headers if not key.startswith("_")), None)
        if first_key is not None and headers[first_key].get("shape"):
            row_count = headers[first_key]["shape"][0]
        return {
            "format": "npz",
            "arrays": headers,
            "n_arrays": len([key for key in headers if not key.startswith("_")]),
            "row_count_hint": row_count,
        }
    if suffix == ".json":
        return {"format": "json", **_json_summary(path)}
    if suffix in {".csv", ".dat", ".txt", ".covmat", ".dataset", ".ini"}:
        return {"format": suffix.removeprefix("."), **_text_table_summary(path)}
    return {"format": suffix.removeprefix(".") or "unknown"}


def _obs_bundle_candidates(repo_root: Path) -> list[DatasetCandidate]:
    root = repo_root / "workdir" / "obs_bundle"
    index_path = root / "INDEX.json"
    if not index_path.exists():
        return []
    index = json.loads(index_path.read_text(encoding="utf-8"))
    candidates: list[DatasetCandidate] = []
    for collection, payload in index.items():
        if collection.startswith("_") or not isinstance(payload, dict):
            continue
        for dataset_id, meta in payload.items():
            if dataset_id.startswith("_") or not isinstance(meta, dict):
                continue
            rel_path = meta.get("path")
            if not rel_path:
                continue
            data_role = "external_observation"
            if collection == "cmb.theory":
                data_role = "external_reference_theory"
            elif collection == "scalars":
                data_role = "compiled_observational_scalar"
            elif collection == "cmb.maps":
                data_role = "external_observation_map"
            elif collection == "cmb.masks":
                data_role = "external_observation_mask"
            sky_status = "not_directional"
            if collection in {"cmb.maps", "cmb.masks", "lss.desi_y1"}:
                sky_status = "sky_support_recorded" if (root / rel_path).exists() else "blocked_missing_data"
            candidates.append(
                DatasetCandidate(
                    dataset_id=dataset_id,
                    collection=collection,
                    path=root / str(rel_path),
                    data_role=data_role,
                    claim_ceiling="diagnostic_only",
                    sky_support_status=sky_status,
                    caveats=(
                        "repo_local_observation_bundle_entry",
                        "not_native_low_ell_solver_output",
                        "does_not_identify_bianchi_family",
                    ),
                )
            )
    return candidates


def _compact_candidates(repo_root: Path) -> list[DatasetCandidate]:
    compact = repo_root / "workdir" / "compact_products"
    candidates: list[DatasetCandidate] = []
    for path in sorted((compact / "desi").glob("*_clustering_extended.npz")):
        dataset_id = "compact.desi." + path.stem.replace("_clustering_extended", "").lower()
        candidates.append(
            DatasetCandidate(
                dataset_id=dataset_id,
                collection="compact_products.desi",
                path=path,
                data_role="external_observation_catalog",
                claim_ceiling="diagnostic_only",
                sky_support_status="sky_support_recorded",
                caveats=(
                    "DESI extended compact catalog with weights and direction vectors",
                    "diagnostic survey and depth analysis only without matched production null promotion",
                ),
            )
        )
    for path in sorted((compact / "cf4").glob("query_*.npz")):
        candidates.append(
            DatasetCandidate(
                dataset_id="compact.cf4." + path.stem,
                collection="compact_products.cf4",
                path=path,
                data_role="external_peculiar_velocity_reconstruction",
                claim_ceiling="diagnostic_only",
                sky_support_status="coordinate_frame_annotated",
                caveats=(
                    "CF4 supergalactic reconstruction sample",
                    "diagnostic velocity and density field analysis only",
                ),
            )
        )
    for path in sorted((compact / "cf4").glob("*.json")):
        candidates.append(
            DatasetCandidate(
                dataset_id="compact.cf4." + path.stem,
                collection="compact_products.cf4",
                path=path,
                data_role="external_peculiar_velocity_metadata",
                claim_ceiling="diagnostic_only",
                caveats=("CF4 query metadata or adaptive target report",),
            )
        )
    for path in (
        compact / "act_dr4_compact.npz",
        compact / "spt3g_y1_compact.npz",
        compact / "camb_planck2018_lensing_refs.npz",
        compact / "dipole_scalar_observations.json",
    ):
        if path.exists():
            role = "external_observation"
            if path.name.startswith("camb"):
                role = "external_reference_theory"
            if path.suffix == ".json":
                role = "compiled_observational_scalar"
            candidates.append(
                DatasetCandidate(
                    dataset_id="compact." + path.stem,
                    collection="compact_products",
                    path=path,
                    data_role=role,
                    claim_ceiling="diagnostic_only",
                    caveats=("compact product fallback for observation-bundle figures",),
                )
            )
    return candidates


def _reference_candidates(repo_root: Path) -> list[DatasetCandidate]:
    paths = [
        repo_root / "data" / "camb_ref_planck2018.npz",
        *(repo_root / "data" / "class_massive_neutrino_fixtures").glob("*.npz"),
        repo_root / "htt" / "bass" / "recombination" / "fixtures" / "recombination_ref_planck2018.csv",
        repo_root / "htt" / "bass" / "recombination" / "fixtures" / "recombination_ref_planck2018_z1e10.csv",
    ]
    return [
        DatasetCandidate(
            dataset_id="reference." + path.with_suffix("").name,
            collection="repo_reference_fixtures",
            path=path,
            data_role="external_reference_or_validation_fixture",
            claim_ceiling="diagnostic_only",
            transfer_source="external_reference",
            caveats=(
                "validation or benchmark fixture, not observed-data inference",
                "not native low-ell solver output",
            ),
        )
        for path in sorted(path for path in paths if path.exists())
    ]


def _cobaya_candidates(repo_root: Path) -> list[DatasetCandidate]:
    root = repo_root / "workdir" / "cobaya_packages" / "data"
    candidates: list[DatasetCandidate] = []
    if not root.exists():
        return candidates
    groups = {
        "cobaya.bicep_keck_2018": root / "bicep_keck_2018",
        "cobaya.planck_supp_data_and_covmats": root / "planck_supp_data_and_covmats",
    }
    for dataset_id, path in groups.items():
        if path.exists():
            n_files = sum(1 for item in path.rglob("*") if item.is_file())
            candidates.append(
                DatasetCandidate(
                    dataset_id=dataset_id,
                    collection="cobaya_packages.data",
                    path=path,
                    data_role="external_likelihood_data_install",
                    claim_ceiling="diagnostic_only",
                    caveats=(
                        f"directory install with {n_files} files",
                        "use through packaged obs bundle or explicit parser only",
                    ),
                )
            )
    return candidates


def _candidate_rows(candidates: Iterable[DatasetCandidate], repo_root: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for candidate in candidates:
        exists = candidate.path.exists()
        rel_path = _repo_relative(candidate.path, repo_root)
        schema = _schema_for_path(candidate.path) if exists and candidate.path.is_file() else {}
        if exists and candidate.path.is_dir():
            schema = {
                "format": "directory",
                "n_files": sum(1 for item in candidate.path.rglob("*") if item.is_file()),
                "size_bytes": sum(item.stat().st_size for item in candidate.path.rglob("*") if item.is_file()),
            }
        size = candidate.path.stat().st_size if exists and candidate.path.is_file() else None
        rows.append(
            {
                "dataset_id": candidate.dataset_id,
                "collection": candidate.collection,
                "path": rel_path,
                "present": exists,
                "size_bytes": size,
                "sha256": _sha256(candidate.path) if exists and candidate.path.is_file() else None,
                "schema": schema,
                "data_role": candidate.data_role,
                "claim_ceiling": "blocked" if not exists else candidate.claim_ceiling,
                "transfer_source": candidate.transfer_source,
                "sky_support_status": "blocked_missing_data" if not exists else candidate.sky_support_status,
                "null_mock_status": candidate.null_mock_status,
                "caveats": list(candidate.caveats),
            }
        )
    return rows


def build_inventory(repo_root: Path = REPO_ROOT, *, command: str = "") -> dict[str, Any]:
    candidates = [
        *_obs_bundle_candidates(repo_root),
        *_compact_candidates(repo_root),
        *_reference_candidates(repo_root),
        *_cobaya_candidates(repo_root),
    ]
    rows = _candidate_rows(candidates, repo_root)
    present = sum(1 for row in rows if row["present"])
    missing = len(rows) - present
    config_hash = _stable_hash(
        {
            "script": "scripts/inventory_observational_data.py",
            "candidate_count": len(rows),
            "paths": [row["path"] for row in rows],
            "schema_version": "common.observational_data_inventory.v1",
        }
    )
    git_state = _git_state(repo_root)
    manifest = {
        "artifact_id": "common.observational_data_inventory",
        "artifact_path": DEFAULT_OUTPUT_JSON.as_posix(),
        "owner": "COMMON",
        "implementation_scope": "common",
        "claim_tier": "diagnostic_only",
        "production_status": "diagnostic_only",
        "created_by": "scripts/inventory_observational_data.py",
        "git_commit": git_state.split("+", maxsplit=1)[0],
        "config_hash": config_hash,
        "input_hashes": [
            f"{row['path']}:{row['sha256'] or 'missing_or_directory'}"
            for row in rows
        ],
        "code_version": git_state,
        "schema_version": "common.observational_data_inventory.v1",
        "caveats": [
            "Inventory records repo-local data availability only.",
            "It does not create inference evidence or native solver validation.",
            "Missing indexed datasets remain blocked until the source file is present.",
        ],
        "transfer_source": "mixed_none_and_external_reference",
        "sky_support_status": "not_directional",
        "null_mock_status": "not_statistical",
        "generating_command": command or "python scripts/inventory_observational_data.py",
        "git_commit_or_worktree_state": git_state,
    }
    issues = validate_manifest_payload(
        manifest,
        manifest_path=DEFAULT_OUTPUT_JSON,
        expected_artifact_path=DEFAULT_OUTPUT_JSON.as_posix(),
    )
    if issues:
        rendered = "; ".join(f"{issue.code}: {issue.detail}" for issue in issues)
        raise ValueError(f"invalid inventory manifest: {rendered}")
    return {
        "manifest": manifest,
        "summary": {
            "dataset_candidates": len(rows),
            "present": present,
            "missing": missing,
            "collections": sorted({str(row["collection"]) for row in rows}),
            "claim_boundary": "diagnostic_inventory_only",
        },
        "rows": rows,
    }


def render_markdown(payload: dict[str, Any]) -> str:
    manifest = payload["manifest"]
    summary = payload["summary"]
    rows = payload["rows"]
    lines = [
        "# Observational Data Inventory",
        "",
        f"owner: {manifest['owner']}",
        f"implementation_scope: {manifest['implementation_scope']}",
        f"claim_tier: {manifest['claim_tier']}",
        f"transfer_source: {manifest['transfer_source']}",
        f"sky_support_status: {manifest['sky_support_status']}",
        f"null_mock_status: {manifest['null_mock_status']}",
        f"config_hash: `{manifest['config_hash']}`",
        "input_hashes:",
    ]
    for item in manifest["input_hashes"][:80]:
        lines.append(f"- `{item}`")
    omitted = max(0, len(manifest["input_hashes"]) - 80)
    if omitted:
        lines.append(f"- `{omitted} additional input hashes omitted from markdown view`")
    lines.extend(
        [
            "caveats:",
            *[f"- {caveat}" for caveat in manifest["caveats"]],
            f"generating_command: `{manifest['generating_command']}`",
            f"git_commit_or_worktree_state: `{manifest['git_commit_or_worktree_state']}`",
            f"artifact_path: {manifest['artifact_path']}",
            "",
            "## Summary",
            "",
            f"- Dataset candidates: `{summary['dataset_candidates']}`",
            f"- Present: `{summary['present']}`",
            f"- Missing: `{summary['missing']}`",
            "- Claim boundary: diagnostic inventory only; no native low-ell solver output or family identification.",
            "",
            "## Candidate Rows",
            "",
            "| Dataset | Collection | Present | Role | Path | Claim ceiling | Sky support | Null/mock | Shape hint |",
            "| --- | --- | ---: | --- | --- | --- | --- | --- | --- |",
        ]
    )
    for row in rows:
        schema = row.get("schema") or {}
        shape_hint = ""
        if isinstance(schema, dict):
            if schema.get("format") == "npz":
                first = next(iter(schema.get("arrays", {}).values()), {})
                if isinstance(first, dict):
                    shape_hint = str(first.get("shape", ""))
            elif "n_files" in schema:
                shape_hint = f"{schema['n_files']} files"
            elif "n_lines" in schema:
                shape_hint = f"{schema['n_lines']} lines"
        lines.append(
            "| "
            + " | ".join(
                [
                    f"`{row['dataset_id']}`",
                    f"`{row['collection']}`",
                    "`yes`" if row["present"] else "`no`",
                    f"`{row['data_role']}`",
                    f"`{row['path']}`",
                    f"`{row['claim_ceiling']}`",
                    f"`{row['sky_support_status']}`",
                    f"`{row['null_mock_status']}`",
                    f"`{shape_hint}`",
                ]
            )
            + " |"
        )
    lines.extend(
        [
            "",
            "## Plot Planning Boundary",
            "",
            "- Present observation datasets may support diagnostic and publication-candidate figures only after sidecar manifests are generated.",
            "- Missing indexed datasets are excluded from generated plot lists until present.",
            "- Covariance, null, PPC, LOOCV, or look-elsewhere language must be tied to explicit generated artifacts.",
        ]
    )
    return "\n".join(lines) + "\n"


def _command(argv: list[str] | None) -> str:
    args = [sys.argv[0], *(argv if argv is not None else sys.argv[1:])]
    return " ".join(args)


def run(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, default=REPO_ROOT)
    parser.add_argument("--output-json", type=Path, default=DEFAULT_OUTPUT_JSON)
    parser.add_argument("--output-md", type=Path, default=DEFAULT_OUTPUT_MD)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args(argv)

    repo_root = args.repo_root.resolve()
    command = _command(argv)
    payload = build_inventory(repo_root, command=command)
    markdown = render_markdown(payload)

    if args.dry_run:
        print(
            "observational inventory: "
            f"{payload['summary']['present']} present, "
            f"{payload['summary']['missing']} missing, "
            f"{payload['summary']['dataset_candidates']} candidates"
        )
        return 0

    output_json = args.output_json if args.output_json.is_absolute() else repo_root / args.output_json
    output_md = args.output_md if args.output_md.is_absolute() else repo_root / args.output_md
    output_json.parent.mkdir(parents=True, exist_ok=True)
    output_json.write_text(
        json.dumps(payload, indent=2, sort_keys=True, default=_json_scalar) + "\n",
        encoding="utf-8",
    )
    output_md.write_text(markdown, encoding="utf-8")
    print(f"wrote {output_json.relative_to(repo_root)}")
    print(f"wrote {output_md.relative_to(repo_root)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(run())
