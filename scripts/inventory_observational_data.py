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
from common.data_contracts import (  # noqa: E402
    DataAllowedUse,
    DataReadinessLevel,
    DataRole,
    SurveySupport,
    validate_data_readiness,
)


DEFAULT_OUTPUT_JSON = Path("docs/generated/observational_data_inventory.json")
DEFAULT_OUTPUT_MD = Path("docs/generated/observational_data_inventory.md")
DEFAULT_GAP_MD = Path("docs/generated/data_binding_gap_report.md")
GENERATING_COMMAND = "venv/bin/python scripts/inventory_observational_data.py --write"


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
    random_or_mask_path: str = ""
    selection_weight_status: str = "not_bound"
    covariance_status: str = "not_statistical"
    allowed_use: str = ""
    readiness_level: str | None = None
    caveats: tuple[str, ...] = ()


def _repo_relative(path: Path, repo_root: Path) -> str:
    try:
        return path.relative_to(repo_root).as_posix()
    except ValueError:
        return path.as_posix()


def _display_path(path: Path, repo_root: Path) -> str:
    return _repo_relative(path.resolve(), repo_root)


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


def _checksum_for_binding(path: Path, exists: bool) -> str:
    if exists and path.is_file():
        return _sha256(path)
    return "missing_or_directory"


def _canonical_role(candidate: DatasetCandidate) -> DataRole:
    text = f"{candidate.collection} {candidate.data_role} {candidate.dataset_id}".lower()
    if candidate.collection in {"lss.desi_y1", "pecvel.cf4"}:
        return DataRole.RAW_CATALOG
    if "random" in text:
        return DataRole.RANDOM_CATALOG
    if "mask" in text:
        return DataRole.MASK
    if "mock" in text:
        return DataRole.MOCK_CATALOG
    if "covariance" in text or "covmat" in text:
        return DataRole.COVARIANCE
    if "map" in text:
        return DataRole.MAP
    if "catalog" in text or "peculiar_velocity_reconstruction" in text:
        return DataRole.RAW_CATALOG
    return DataRole.HARMONIC_PRODUCT


def _readiness_level(candidate: DatasetCandidate, exists: bool, role: DataRole) -> DataReadinessLevel:
    if not exists:
        return DataReadinessLevel.BLOCKED
    if candidate.readiness_level is not None:
        return DataReadinessLevel(str(candidate.readiness_level))
    text = f"{candidate.collection} {candidate.data_role}".lower()
    if (
        "reference" in text
        or "fixture" in text
        or "metadata" in text
        or "likelihood_data_install" in text
        or candidate.collection == "cmb.theory"
    ):
        return DataReadinessLevel.D0_DERIVED_AUDIT_PAYLOAD
    if role in {DataRole.RAW_CATALOG, DataRole.MAP, DataRole.HARMONIC_PRODUCT}:
        return DataReadinessLevel.D1_PRIMARY_PUBLIC_DATA
    return DataReadinessLevel.D0_DERIVED_AUDIT_PAYLOAD


def _allowed_use(candidate: DatasetCandidate, exists: bool, level: DataReadinessLevel) -> DataAllowedUse:
    if not exists or level == DataReadinessLevel.BLOCKED:
        return DataAllowedUse.BLOCKED_FOR_INFERENCE
    if candidate.allowed_use:
        return DataAllowedUse(str(candidate.allowed_use))
    if level == DataReadinessLevel.D0_DERIVED_AUDIT_PAYLOAD:
        return DataAllowedUse.SCHEMA_CHECK_ONLY
    return DataAllowedUse.DIAGNOSTIC_PLOT_ONLY


def _survey_metadata(candidate: DatasetCandidate) -> dict[str, str]:
    text = f"{candidate.collection} {candidate.dataset_id} {candidate.path.as_posix()}".lower()
    if "desi" in text:
        tracer = "unknown"
        for item in ("bgs", "lrg", "qso"):
            if item in text:
                tracer = item.upper()
                break
        region = "NGC" if "ngc" in text else "SGC" if "sgc" in text else "mixed_or_unknown"
        return {
            "survey_name": "DESI",
            "release": "compact_products" if "compact_products" in text else "Y1_indexed",
            "tracer": tracer,
            "sky_region": region,
            "redshift_range": "catalog_bound_not_production_binned",
        }
    if "cf4" in text:
        return {
            "survey_name": "CF4",
            "release": "repo_local_compact",
            "tracer": "peculiar_velocity",
            "sky_region": "all_sky_or_query_bound",
            "redshift_range": "distance_reconstruction_bound",
        }
    if "planck" in text:
        release = "PR3" if "pr3" in text else "Planck2018" if "2018" in text else "repo_reference"
        tracer = "mask" if "mask" in text else "map" if "map" in text or "nside" in text else "bandpower_or_theory"
        return {
            "survey_name": "Planck",
            "release": release,
            "tracer": tracer,
            "sky_region": "full_or_masked_sky",
            "redshift_range": "not_applicable",
        }
    if "act" in text:
        return {
            "survey_name": "ACT",
            "release": "DR4_or_DR6",
            "tracer": "cmb_bandpower",
            "sky_region": "experiment_support_bound",
            "redshift_range": "not_applicable",
        }
    if "spt" in text:
        return {
            "survey_name": "SPT",
            "release": "3G_Y1",
            "tracer": "cmb_bandpower",
            "sky_region": "experiment_support_bound",
            "redshift_range": "not_applicable",
        }
    if "bicep" in text or "keck" in text:
        return {
            "survey_name": "BICEP_Keck",
            "release": "2018",
            "tracer": "cmb_bandpower",
            "sky_region": "experiment_support_bound",
            "redshift_range": "not_applicable",
        }
    survey = candidate.collection.split(".", maxsplit=1)[0] or "repo_local"
    return {
        "survey_name": survey,
        "release": "repo_local",
        "tracer": candidate.dataset_id.rsplit(".", maxsplit=1)[-1],
        "sky_region": "not_directional_or_unbound",
        "redshift_range": "not_applicable_or_unbound",
    }


def _selection_status(candidate: DatasetCandidate, role: DataRole) -> str:
    if candidate.selection_weight_status != "not_bound":
        return candidate.selection_weight_status
    text = f"{candidate.collection} {candidate.dataset_id}".lower()
    if "desi" in text and role == DataRole.RAW_CATALOG:
        return "catalog_weight_columns_present_not_production_certified"
    if role in {DataRole.MAP, DataRole.HARMONIC_PRODUCT, DataRole.MASK}:
        return "not_applicable"
    return "not_bound"


def _survey_support_for_candidate(
    candidate: DatasetCandidate,
    *,
    exists: bool,
    repo_root: Path,
    role: DataRole,
    level: DataReadinessLevel,
) -> SurveySupport:
    survey = _survey_metadata(candidate)
    return SurveySupport(
        **survey,
        data_path=_repo_relative(candidate.path, repo_root),
        checksum=_checksum_for_binding(candidate.path, exists),
        random_or_mask_path=candidate.random_or_mask_path,
        selection_weight_status=_selection_status(candidate, role),
        covariance_status=candidate.covariance_status,
        null_mock_status=candidate.null_mock_status,
        allowed_use=_allowed_use(candidate, exists, level),
        data_role=role,
    )


def _support_with_allowed_use(
    support: SurveySupport,
    allowed_use: DataAllowedUse,
) -> SurveySupport:
    payload = support.to_metadata()
    payload["allowed_use"] = allowed_use.value
    return SurveySupport(**payload)


def _spectroscopic_gate_required(candidate: DatasetCandidate, role: DataRole) -> bool:
    text = f"{candidate.collection} {candidate.dataset_id}".lower()
    return "desi" in text and role == DataRole.RAW_CATALOG


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
        role = _canonical_role(candidate)
        readiness_level = _readiness_level(candidate, exists, role)
        support = _survey_support_for_candidate(
            candidate,
            exists=exists,
            repo_root=repo_root,
            role=role,
            level=readiness_level,
        )
        readiness = validate_data_readiness(
            support,
            readiness_level,
            intended_use="diagnostic_inventory",
        )
        if (
            not readiness.allowed
            and support.allowed_use != DataAllowedUse.BLOCKED_FOR_INFERENCE
        ):
            support = _support_with_allowed_use(
                support,
                DataAllowedUse.BLOCKED_FOR_INFERENCE,
            )
            readiness = validate_data_readiness(
                support,
                readiness_level,
                intended_use="diagnostic_inventory",
            )
        production_blockers: tuple[str, ...] = ()
        if _spectroscopic_gate_required(candidate, role):
            production_blockers = validate_data_readiness(
                support,
                DataReadinessLevel.D1_PRIMARY_PUBLIC_DATA,
                intended_use="spectroscopic_dipole_production",
            ).blockers
        d2_blockers: tuple[str, ...] = ()
        if role == DataRole.RAW_CATALOG:
            d2_blockers = validate_data_readiness(
                support,
                DataReadinessLevel.D2_MATCHED_MOCKS,
                intended_use="matched_mock_promotion_check",
            ).blockers
        binding_gap_reasons = list(
            dict.fromkeys(
                [
                    *readiness.blockers,
                    *production_blockers,
                    *d2_blockers,
                ]
            )
        )
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
                "legacy_data_role": candidate.data_role,
                "data_role": role.value,
                "survey_support": support.to_metadata(),
                "data_readiness": readiness.to_metadata(),
                "data_readiness_level": readiness.requested_level.value,
                "data_readiness_allowed": readiness.allowed,
                "allowed_use": support.allowed_use.value,
                "selection_weight_status": support.selection_weight_status,
                "covariance_status": support.covariance_status,
                "random_or_mask_path": support.random_or_mask_path,
                "binding_gap_reasons": binding_gap_reasons,
                "spectroscopic_dipole_blockers": list(production_blockers),
                "matched_mock_promotion_blockers": list(d2_blockers),
                "claim_ceiling": "blocked" if not readiness.allowed else candidate.claim_ceiling,
                "transfer_source": candidate.transfer_source,
                "sky_support_status": "blocked_missing_data" if not exists else candidate.sky_support_status,
                "null_mock_status": candidate.null_mock_status,
                "caveats": [
                    *candidate.caveats,
                    "present_does_not_imply_inference_readiness",
                    "data_binding_readiness_is_not_htt_evidence",
                ],
            }
        )
    return rows


def build_inventory(
    repo_root: Path = REPO_ROOT,
    *,
    command: str = "",
    artifact_path: str = DEFAULT_OUTPUT_JSON.as_posix(),
    git_state_override: str | None = None,
) -> dict[str, Any]:
    candidates = [
        *_obs_bundle_candidates(repo_root),
        *_compact_candidates(repo_root),
        *_reference_candidates(repo_root),
        *_cobaya_candidates(repo_root),
    ]
    rows = _candidate_rows(candidates, repo_root)
    present = sum(1 for row in rows if row["present"])
    missing = len(rows) - present
    readiness_counts: dict[str, int] = {}
    role_counts: dict[str, int] = {}
    allowed_use_counts: dict[str, int] = {}
    for row in rows:
        readiness_counts[str(row["data_readiness_level"])] = (
            readiness_counts.get(str(row["data_readiness_level"]), 0) + 1
        )
        role_counts[str(row["data_role"])] = role_counts.get(str(row["data_role"]), 0) + 1
        allowed_use_counts[str(row["allowed_use"])] = (
            allowed_use_counts.get(str(row["allowed_use"]), 0) + 1
        )
    config_hash = _stable_hash(
        {
            "script": "scripts/inventory_observational_data.py",
            "candidate_count": len(rows),
            "paths": [row["path"] for row in rows],
            "schema_version": "common.observational_data_inventory.v2",
            "data_binding_schema": "common.data_contracts.v1",
            "readiness_counts": readiness_counts,
            "role_counts": role_counts,
        }
    )
    git_state = git_state_override or _git_state(repo_root)
    manifest = {
        "artifact_id": "common.observational_data_inventory",
        "artifact_path": artifact_path,
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
        "schema_version": "common.observational_data_inventory.v2",
        "data_binding_schema": "common.data_contracts.v1",
        "caveats": [
            "Inventory records repo-local data availability only.",
            "It does not create inference evidence or native solver validation.",
            "Missing indexed datasets remain blocked until the source file is present.",
            "Present data does not imply spectroscopic dipole production readiness.",
            "D0/D1 data-readiness rows are diagnostic-only unless matched randoms, covariance, and null/mock support are bound downstream.",
        ],
        "promotion_blockers": [
            "matched_randoms_or_masks_not_bound_for_spectroscopic_dipole",
            "publication_grade_covariance_not_bound",
            "matched_null_mocks_not_bound",
            "htt_rank_ppc_loocv_gates_not_bound",
            "native_morphology_atlas_not_available",
        ],
        "transfer_source": "mixed_none_and_external_reference",
        "sky_support_status": "not_directional",
        "null_mock_status": "not_statistical",
        "generating_command": command or "python scripts/inventory_observational_data.py",
        "git_commit_or_worktree_state": git_state,
    }
    issues = validate_manifest_payload(
        manifest,
        manifest_path=artifact_path,
        expected_artifact_path=artifact_path,
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
            "data_readiness_counts": dict(sorted(readiness_counts.items())),
            "data_role_counts": dict(sorted(role_counts.items())),
            "allowed_use_counts": dict(sorted(allowed_use_counts.items())),
            "rows_with_binding_gaps": sum(1 for row in rows if row["binding_gap_reasons"]),
            "spectroscopic_dipole_blocked_rows": sum(
                1 for row in rows if row["spectroscopic_dipole_blockers"]
            ),
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
            f"- Rows with binding gaps: `{summary['rows_with_binding_gaps']}`",
            f"- Spectroscopic dipole blocked rows: `{summary['spectroscopic_dipole_blocked_rows']}`",
            "- Claim boundary: diagnostic inventory only; no native low-ell solver output or family identification.",
            "- Present does not imply inference readiness.",
            "",
            "## Readiness Counts",
            "",
            "| Readiness | Count |",
            "| --- | ---: |",
        ]
    )
    for label, count in summary["data_readiness_counts"].items():
        lines.append(f"| `{label}` | `{count}` |")
    lines.extend(
        [
            "",
            "## Candidate Rows",
            "",
            "| Dataset | Collection | Present | Role | Legacy role | Readiness | Allowed use | Claim ceiling | Sky support | Null/mock | Gaps | Shape hint |",
            "| --- | --- | ---: | --- | --- | --- | --- | --- | --- | --- | --- | --- |",
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
                    f"`{row['legacy_data_role']}`",
                    f"`{row['data_readiness_level']}`",
                    f"`{row['allowed_use']}`",
                    f"`{row['claim_ceiling']}`",
                    f"`{row['sky_support_status']}`",
                    f"`{row['null_mock_status']}`",
                    "`" + ",".join(row["binding_gap_reasons"][:3]) + "`",
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
            "- D0/D1 rows remain diagnostic-only and are blocked from spectroscopic dipole production unless matched randoms or masks, covariance status, and null/mock support are explicitly present.",
            "- Covariance, null, PPC, LOOCV, or look-elsewhere language must be tied to explicit generated artifacts.",
        ]
    )
    return "\n".join(lines) + "\n"


def render_gap_report(
    payload: dict[str, Any],
    *,
    artifact_path: str = DEFAULT_GAP_MD.as_posix(),
) -> str:
    manifest = payload["manifest"]
    summary = payload["summary"]
    rows = payload["rows"]
    gap_rows = [row for row in rows if row["binding_gap_reasons"]]
    lines = [
        "# Data Binding Gap Report",
        "",
        "owner: COMMON",
        "implementation_scope: common",
        "claim_tier: diagnostic_only",
        f"transfer_source: {manifest['transfer_source']}",
        f"sky_support_status: {manifest['sky_support_status']}",
        f"null_mock_status: {manifest['null_mock_status']}",
        f"config_hash: `{manifest['config_hash']}`",
        f"schema_version: `{manifest['schema_version']}`",
        f"data_binding_schema: `{manifest['data_binding_schema']}`",
        f"generating_command: `{manifest['generating_command']}`",
        f"git_commit_or_worktree_state: `{manifest['git_commit_or_worktree_state']}`",
        f"artifact_path: {artifact_path}",
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
            "promotion_blockers:",
            *[f"- {blocker}" for blocker in manifest["promotion_blockers"]],
            "",
            "## Summary",
            "",
            f"- Dataset candidates: `{summary['dataset_candidates']}`",
            f"- Present: `{summary['present']}`",
            f"- Missing: `{summary['missing']}`",
            f"- Rows with binding gaps: `{summary['rows_with_binding_gaps']}`",
            f"- Spectroscopic dipole blocked rows: `{summary['spectroscopic_dipole_blocked_rows']}`",
            "",
            "## Residual Risk",
            "",
            (
                "This data-binding report records catalog/support metadata completeness only. "
                "It does not create HTT likelihoods, posterior odds, evidence terms, MIO "
                "certificates, native solver checks, or Bianchi family-identification claims. "
                "Rows with D0/D1 readiness remain diagnostic-only and are blocked from "
                "spectroscopic dipole production unless matched randoms or masks, covariance "
                "status, and null/mock support are explicitly present."
            ),
            "",
            "## Gap Rows",
            "",
            "| Dataset | Role | Readiness | Allowed use | Gap reasons | Spectroscopic blockers | D2 blockers |",
            "| --- | --- | --- | --- | --- | --- | --- |",
        ]
    )
    for row in gap_rows:
        lines.append(
            "| "
            + " | ".join(
                [
                    f"`{row['dataset_id']}`",
                    f"`{row['data_role']}`",
                    f"`{row['data_readiness_level']}`",
                    f"`{row['allowed_use']}`",
                    "`" + ",".join(row["binding_gap_reasons"]) + "`",
                    "`" + ",".join(row["spectroscopic_dipole_blockers"]) + "`",
                    "`" + ",".join(row["matched_mock_promotion_blockers"]) + "`",
                ]
            )
            + " |"
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
    parser.add_argument("--gap-md", type=Path, default=DEFAULT_GAP_MD)
    parser.add_argument("--write", action="store_true")
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args(argv)
    if sum(bool(flag) for flag in (args.write, args.check, args.dry_run)) > 1:
        parser.error("--write, --check, and --dry-run are mutually exclusive")

    repo_root = args.repo_root.resolve()
    output_json = args.output_json if args.output_json.is_absolute() else repo_root / args.output_json
    output_md = args.output_md if args.output_md.is_absolute() else repo_root / args.output_md
    gap_md = args.gap_md if args.gap_md.is_absolute() else repo_root / args.gap_md
    output_json_display = _display_path(output_json, repo_root)
    gap_md_display = _display_path(gap_md, repo_root)
    command = GENERATING_COMMAND
    git_state_override = None
    if args.check and output_json.exists():
        try:
            existing_payload = json.loads(output_json.read_text(encoding="utf-8"))
            existing_manifest = existing_payload.get("manifest", {})
            if isinstance(existing_manifest, dict):
                existing_state = existing_manifest.get("git_commit_or_worktree_state")
                if isinstance(existing_state, str) and existing_state.strip():
                    git_state_override = existing_state
        except json.JSONDecodeError:
            git_state_override = None
    payload = build_inventory(
        repo_root,
        command=command,
        artifact_path=output_json_display,
        git_state_override=git_state_override,
    )
    markdown = render_markdown(payload)
    gap_markdown = render_gap_report(payload, artifact_path=gap_md_display)
    json_text = json.dumps(payload, indent=2, sort_keys=True, default=_json_scalar) + "\n"

    if args.dry_run:
        print(
            "observational inventory: "
            f"{payload['summary']['present']} present, "
            f"{payload['summary']['missing']} missing, "
            f"{payload['summary']['dataset_candidates']} candidates, "
            f"{payload['summary']['rows_with_binding_gaps']} rows with binding gaps"
        )
        return 0

    if args.check:
        mismatches = []
        expected = (
            (output_json, json_text),
            (output_md, markdown),
            (gap_md, gap_markdown),
        )
        for path, text in expected:
            if not path.exists() or path.read_text(encoding="utf-8") != text:
                mismatches.append(_display_path(path, repo_root))
        if mismatches:
            print("stale observational data inventory outputs:")
            for path in mismatches:
                print(f"- {path}")
            return 1
        print("observational data inventory outputs pass check")
        return 0

    output_json.parent.mkdir(parents=True, exist_ok=True)
    output_md.parent.mkdir(parents=True, exist_ok=True)
    gap_md.parent.mkdir(parents=True, exist_ok=True)
    output_json.write_text(json_text, encoding="utf-8")
    output_md.write_text(markdown, encoding="utf-8")
    gap_md.write_text(gap_markdown, encoding="utf-8")
    print(f"wrote {_display_path(output_json, repo_root)}")
    print(f"wrote {_display_path(output_md, repo_root)}")
    print(f"wrote {_display_path(gap_md, repo_root)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(run())
