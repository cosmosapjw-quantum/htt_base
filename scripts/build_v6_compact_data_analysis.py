#!/usr/bin/env python3
"""Build v6 compact-data acquisition and analysis cards.

This script records the data-facing work that follows the v6 no-download
cards: compact public-data acquisition status, local compact product summaries,
and acceptance checks. It does not create likelihoods, posteriors, evidence
terms, Bianchi family identification, or native low-ell solver claims.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import shlex
import sys
import tarfile
from pathlib import Path
from typing import Any

import numpy as np


REPO_ROOT = Path(__file__).resolve().parents[1]
GEN = REPO_ROOT / "docs" / "generated"
OUT_JSON = GEN / "v6_compact_data_analysis.json"
OUT_MD = GEN / "v6_compact_data_analysis.md"
SCRIPT_PATH = "scripts/build_v6_compact_data_analysis.py"

NO_DOWNLOAD_CARDS = "docs/generated/v6_no_download_research_cards.json"
NO_DOWNLOAD_FIGURE_PACK = "docs/generated/v6_no_download_figure_pack.json"
REPORT_DATA_PACK = "docs/generated/report_data_analysis_figure_pack.json"
EXISTING_COMPACT_INVENTORY = "docs/generated/v6_existing_compact_download_inventory.json"
APPROVAL_COMPACT_INVENTORY = "docs/generated/v6_approval_compact_download_inventory.json"
ACT_DR6_MANIFEST = "workdir/raw/act_data/act_dr6_02_acquisition_manifest.json"
ACT_DR6_LENSING_MANIFEST = "workdir/raw/act_dr6_lensing/act_dr6_lensing_acquisition_manifest.json"
ACT_DR6_LENSING_DOWNLOAD_DIR = "workdir/downloads/act_dr6_lensing"
ACT_DR6_LENSING_ARCHIVES = (
    ("act_dr6_lensing_likelihood_archive", "workdir/downloads/act_dr6_lensing/ACT_dr6_likelihood_v1.2.tgz"),
    ("act_dr6_lensing_maps_archive", "workdir/downloads/act_dr6_lensing/dr6_lensing_release.tar.gz"),
)

COMPACT_PRODUCTS = (
    ("planck_tt_binned", "workdir/obs_bundle/cmb/powerspectra/planck_pr3_tt_binned.npz"),
    ("planck_lensing", "workdir/obs_bundle/cmb/lensing/planck_pr3_lensing.npz"),
    ("camb_lensing_reference", "workdir/obs_bundle/cmb/theory/camb_planck2018_lensing_refs.npz"),
    ("act_dr4_compact", "workdir/obs_bundle/cmb/powerspectra/act_dr4.npz"),
    ("spt3g_y1_compact", "workdir/obs_bundle/cmb/powerspectra/spt3g_y1.npz"),
    ("bicep_keck_2018_bb", "workdir/obs_bundle/cmb/powerspectra/bicep_keck_2018_bb.npz"),
    ("act_dr6_tt", "workdir/htt_extracted/act_dr6_tt_bandpowers.npz"),
    ("act_dr6_te", "workdir/htt_extracted/act_dr6_te_bandpowers.npz"),
    ("act_dr6_ee", "workdir/htt_extracted/act_dr6_ee_bandpowers.npz"),
    ("desi_bgs_ngc", "workdir/compact_products/desi/BGS_ANY_NGC_clustering_extended.npz"),
    ("desi_bgs_sgc", "workdir/compact_products/desi/BGS_ANY_SGC_clustering_extended.npz"),
    ("desi_lrg_ngc", "workdir/compact_products/desi/LRG_NGC_clustering_extended.npz"),
    ("desi_lrg_sgc", "workdir/compact_products/desi/LRG_SGC_clustering_extended.npz"),
    ("desi_qso_ngc", "workdir/compact_products/desi/QSO_NGC_clustering_extended.npz"),
    ("desi_qso_sgc", "workdir/compact_products/desi/QSO_SGC_clustering_extended.npz"),
    ("cf4_query_batch", "workdir/compact_products/cf4/query_batch.npz"),
    ("cf4_full_groups", "workdir/obs_bundle/pecvel/cf4_full/cf4_groups.npz"),
)

REQUIRED_NO_DOWNLOAD_CARDS = {
    "component_source_matrix",
    "identified_set_card",
    "denominator_sensitivity_table",
    "response_class_ledger",
    "exceedance_calibration_card",
    "depth_gap_card",
    "optical_ansatz_readiness",
}


def _repo_relative(path: Path) -> str:
    try:
        return path.resolve().relative_to(REPO_ROOT.resolve()).as_posix()
    except ValueError:
        return path.as_posix()


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(chunk)
    return "sha256:" + h.hexdigest()


def _json_hash(value: Any) -> str:
    encoded = json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode("utf-8")
    return "sha256:" + hashlib.sha256(encoded).hexdigest()


def _load_json(relative: str) -> dict[str, Any]:
    path = REPO_ROOT / relative
    if not path.exists():
        return {}
    payload = json.loads(path.read_text(encoding="utf-8"))
    return payload if isinstance(payload, dict) else {}


def _input_hashes(paths: tuple[str, ...]) -> list[str]:
    rows: list[str] = []
    for relative in paths:
        path = REPO_ROOT / relative
        if path.exists() and path.is_file():
            digest = _sha256(path)
        elif path.exists() and path.is_dir():
            file_rows = [
                f"{_repo_relative(child)}:{_sha256(child)}"
                for child in sorted(path.rglob("*"))
                if child.is_file()
            ]
            digest = _json_hash(file_rows)
        else:
            digest = "missing"
        rows.append(f"{relative}:{digest}")
    return rows


def _command(argv: list[str] | None = None) -> str:
    raw = sys.argv[1:] if argv is None else argv
    args = [arg for arg in raw if arg != "--check"]
    return shlex.join(["python", SCRIPT_PATH, *args])


def _array_profile(arr: np.ndarray) -> dict[str, Any]:
    row: dict[str, Any] = {
        "shape": [int(dim) for dim in arr.shape],
        "dtype": str(arr.dtype),
    }
    if arr.size and np.issubdtype(arr.dtype, np.number):
        finite = np.asarray(arr, dtype=float)
        finite = finite[np.isfinite(finite)]
        if finite.size:
            row.update(
                {
                    "min": float(np.min(finite)),
                    "max": float(np.max(finite)),
                    "median": float(np.median(finite)),
                }
            )
    return row


def _npz_profile(relative: str) -> dict[str, Any]:
    path = REPO_ROOT / relative
    if not path.exists():
        return {"present": False, "path": relative}
    profile: dict[str, Any] = {
        "present": True,
        "path": relative,
        "size_bytes": int(path.stat().st_size),
        "sha256": _sha256(path),
    }
    try:
        with np.load(path, allow_pickle=False) as data:
            arrays = {key: _array_profile(np.asarray(data[key])) for key in data.files}
            profile["n_arrays"] = len(arrays)
            profile["arrays"] = arrays
            if {"ell", "dl"} <= set(data.files):
                ell = np.asarray(data["ell"], dtype=float)
                dl = np.asarray(data["dl"], dtype=float)
                profile["bandpower_summary"] = {
                    "n_points": int(ell.size),
                    "ell_min": float(np.nanmin(ell)) if ell.size else None,
                    "ell_max": float(np.nanmax(ell)) if ell.size else None,
                    "dl_median": float(np.nanmedian(dl)) if dl.size else None,
                }
            if {"ra", "dec", "z"} <= set(data.files):
                z = np.asarray(data["z"], dtype=float)
                profile["catalog_summary"] = {
                    "n_rows": int(z.size),
                    "z_min": float(np.nanmin(z)) if z.size else None,
                    "z_median": float(np.nanmedian(z)) if z.size else None,
                    "z_max": float(np.nanmax(z)) if z.size else None,
                }
    except Exception as exc:  # noqa: BLE001 - profile records read failures.
        profile["read_error"] = f"{type(exc).__name__}:{exc}"
    return profile


def _archive_profile(relative: str, max_members: int = 20) -> dict[str, Any]:
    path = REPO_ROOT / relative
    if not path.exists():
        return {"present": False, "path": relative}
    profile: dict[str, Any] = {
        "present": True,
        "path": relative,
        "size_bytes": int(path.stat().st_size),
        "sha256": _sha256(path),
    }
    try:
        sampled: list[dict[str, Any]] = []
        with tarfile.open(path, "r|*") as archive:
            for idx, member in enumerate(archive):
                if idx >= max_members:
                    break
                sampled.append(
                    {
                        "name": member.name,
                        "size_bytes": int(member.size),
                        "type": "file" if member.isfile() else "dir" if member.isdir() else "other",
                    }
                )
        profile["archive_summary"] = {
            "format": "tar_stream_probe",
            "sample_member_count": len(sampled),
            "sample_members": sampled,
            "member_count_is_sample_only": True,
        }
    except Exception as exc:  # noqa: BLE001 - archive probe failures are recorded.
        profile["archive_read_error"] = f"{type(exc).__name__}:{exc}"
    return profile


def _product_rows() -> list[dict[str, Any]]:
    rows = []
    for label, relative in COMPACT_PRODUCTS:
        row = {"label": label, **_npz_profile(relative)}
        rows.append(row)
    for label, relative in ACT_DR6_LENSING_ARCHIVES:
        row = {"label": label, **_archive_profile(relative)}
        rows.append(row)
    return rows


def _download_inventory_summary(relative: str) -> dict[str, Any]:
    inv = _load_json(relative)
    if not inv:
        return {"path": relative, "present": False}
    items = inv.get("items", [])
    by_status: dict[str, int] = {}
    for item in items if isinstance(items, list) else []:
        status = str(item.get("status", "unknown")) if isinstance(item, dict) else "unknown"
        by_status[status] = by_status.get(status, 0) + 1
    return {
        "path": relative,
        "present": True,
        "known_additional_gb": inv.get("known_additional_gb"),
        "unknown_size_count": inv.get("unknown_size_count"),
        "within_cap_for_known_sizes": inv.get("within_cap_for_known_sizes"),
        "by_status": by_status,
        "items": items,
    }


def _manifest_summary(relative: str) -> dict[str, Any]:
    payload = _load_json(relative)
    path = REPO_ROOT / relative
    if not payload:
        return {"path": relative, "present": False}
    files = payload.get("local_files", [])
    return {
        "path": relative,
        "present": True,
        "stage": payload.get("stage"),
        "claim_tier": payload.get("claim_tier"),
        "local_file_count": len(files) if isinstance(files, list) else None,
        "local_total_bytes": sum(int(item.get("size_bytes", 0)) for item in files if isinstance(item, dict)),
        "sha256": _sha256(path) if path.exists() else None,
    }


def _local_files_under(relative: str) -> list[str]:
    root = REPO_ROOT / relative
    if not root.exists():
        return []
    return sorted(
        _repo_relative(path)
        for path in root.rglob("*")
        if path.is_file()
    )


def _acceptance_checks(product_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    no_download = _load_json(NO_DOWNLOAD_CARDS)
    cards = no_download.get("cards", {}) if isinstance(no_download.get("cards"), dict) else {}
    no_download_pack = _load_json(NO_DOWNLOAD_FIGURE_PACK)
    report_pack = _load_json(REPORT_DATA_PACK)
    existing_inv = _load_json(EXISTING_COMPACT_INVENTORY)
    approval_inv = _load_json(APPROVAL_COMPACT_INVENTORY)

    present_labels = {row["label"] for row in product_rows if row.get("present")}
    lensing_inventory_items = [
        item.get("item_id")
        for item in approval_inv.get("items", [])
        if isinstance(item, dict) and item.get("stage") == "act_dr6_lensing"
    ]
    lensing_manifest = _manifest_summary(ACT_DR6_LENSING_MANIFEST)
    lensing_manifest_present = bool(lensing_manifest.get("present"))
    lensing_acquired = (
        lensing_manifest_present
        and int(lensing_manifest.get("local_file_count") or 0) > 0
    )
    lensing_local_files = _local_files_under(ACT_DR6_LENSING_DOWNLOAD_DIR)
    lensing_deferred_cleanly = not lensing_manifest_present and not lensing_local_files
    required_downloads = [
        "act_dr6_tt",
        "act_dr6_te",
        "act_dr6_ee",
    ]
    checks = [
        {
            "id": "no_download_cards_complete",
            "passed": REQUIRED_NO_DOWNLOAD_CARDS <= set(cards),
            "evidence": sorted(set(cards) & REQUIRED_NO_DOWNLOAD_CARDS),
        },
        {
            "id": "no_download_meta_figures_quarantined",
            "passed": no_download_pack.get("report_use_policy") == "not_report_facing_internal_meta_quarantine",
            "evidence": no_download_pack.get("report_use_policy"),
        },
        {
            "id": "existing_compact_inventory_has_no_known_new_bytes",
            "passed": existing_inv.get("known_additional_gb") == 0.0,
            "evidence": existing_inv.get("known_additional_gb"),
        },
        {
            "id": "approval_compact_inventory_within_3gb_cap",
            "passed": bool(approval_inv.get("within_cap_for_known_sizes"))
            and float(approval_inv.get("known_additional_gb", 99.0)) <= 3.0,
            "evidence": {
                "known_additional_gb": approval_inv.get("known_additional_gb"),
                "within_cap_for_known_sizes": approval_inv.get("within_cap_for_known_sizes"),
            },
        },
        {
            "id": "act_dr6_bandpowers_extracted",
            "passed": set(required_downloads) <= present_labels,
            "evidence": sorted(label for label in required_downloads if label in present_labels),
        },
        {
            "id": "act_dr6_acquisition_manifest_present",
            "passed": (REPO_ROOT / ACT_DR6_MANIFEST).is_file(),
            "evidence": ACT_DR6_MANIFEST,
        },
        {
            "id": "act_dr6_lensing_acquired_or_deferred_cleanly",
            "passed": bool(lensing_inventory_items) and (lensing_acquired or lensing_deferred_cleanly),
            "evidence": {
                "inventory_item_ids": sorted(str(item) for item in lensing_inventory_items),
                "manifest_present": lensing_manifest_present,
                "manifest_local_file_count": lensing_manifest.get("local_file_count"),
                "manifest_local_total_bytes": lensing_manifest.get("local_total_bytes"),
                "local_download_files": lensing_local_files,
                "status": "acquired" if lensing_acquired else "deferred_after_size_probe",
            },
        },
        {
            "id": "report_data_pack_contains_compact_figures",
            "passed": {
                "fig_data_compact_cmb_high_ell_products.png",
                "fig_data_compact_lensing_bandpower_covariance.png",
            }
            <= {row.get("file_name") for row in report_pack.get("figures", []) if isinstance(row, dict)},
            "evidence": [row.get("file_name") for row in report_pack.get("figures", []) if isinstance(row, dict)],
        },
    ]
    for row in checks:
        row["claim_effect"] = "acceptance_or_provenance_only_not_scientific_inference"
    return checks


def build_payload(command: str) -> dict[str, Any]:
    source_paths = (
        NO_DOWNLOAD_CARDS,
        NO_DOWNLOAD_FIGURE_PACK,
        REPORT_DATA_PACK,
        EXISTING_COMPACT_INVENTORY,
        APPROVAL_COMPACT_INVENTORY,
        ACT_DR6_MANIFEST,
        ACT_DR6_LENSING_MANIFEST,
        ACT_DR6_LENSING_DOWNLOAD_DIR,
        SCRIPT_PATH,
    )
    product_rows = _product_rows()
    acceptance = _acceptance_checks(product_rows)
    present_count = sum(1 for row in product_rows if row.get("present"))
    lensing_acquired = (REPO_ROOT / ACT_DR6_LENSING_MANIFEST).is_file()
    lensing_status = "acquired" if lensing_acquired else "deferred_after_size_probe"
    lensing_caveat = (
        "ACT DR6 lensing support products are acquired, manifest-bound, and archive-profiled as external public data; "
        "no lensing likelihood, posterior, evidence, p-value, native-solver output, or family-identification claim is run."
        if lensing_acquired
        else "ACT DR6 temperature/polarization SACC bandpowers are acquired; ACT DR6 lensing support products are size-probed and remain deferred unless their manifest is present."
    )
    payload = {
        "artifact_id": "common.v6_compact_data_analysis",
        "artifact_path": _repo_relative(OUT_JSON),
        "owner": "COMMON/OBSSTAT/DL_PIPELINE",
        "implementation_scope": "external_data_acquisition_and_obsstat_diagnostics",
        "claim_tier": "diagnostic_only",
        "transfer_source": "external_public_data_and_external_reference",
        "sky_support_status": "mixed_dataset_bound",
        "null_mock_status": "not_promoted_to_inference_null",
        "config_hash": _json_hash(
            {
                "compact_products": COMPACT_PRODUCTS,
                "required_no_download_cards": sorted(REQUIRED_NO_DOWNLOAD_CARDS),
                "source_paths": source_paths,
            }
        ),
        "input_hashes": _input_hashes(source_paths),
        "caveats": [
            "Acquisition and compact-product diagnostics only.",
            "No native low-ell solver output is represented.",
            "No posterior odds, evidence, p-value, or Bianchi family-identification claim is made.",
            "DESI random/mask support remains separate unless explicit support files are locally bound.",
            lensing_caveat,
        ],
        "generating_command": command,
        "git_commit_or_worktree_state": "content-addressed",
        "download_inventory": {
            "existing_compact": _download_inventory_summary(EXISTING_COMPACT_INVENTORY),
            "approval_compact": _download_inventory_summary(APPROVAL_COMPACT_INVENTORY),
            "act_dr6_acquisition": _manifest_summary(ACT_DR6_MANIFEST),
            "act_dr6_lensing_acquisition": _manifest_summary(ACT_DR6_LENSING_MANIFEST),
        },
        "summary": {
            "compact_product_rows": len(product_rows),
            "present_compact_products": present_count,
            "missing_compact_products": len(product_rows) - present_count,
            "acceptance_passed": sum(1 for row in acceptance if row["passed"]),
            "acceptance_total": len(acceptance),
            "act_dr6_lensing_status": lensing_status,
        },
        "compact_products": product_rows,
        "acceptance_checks": acceptance,
    }
    return payload


def render_markdown(payload: dict[str, Any]) -> str:
    summary = payload["summary"]
    lines = [
        "# V6 Compact Data Analysis",
        "",
        "owner: COMMON/OBSSTAT/DL_PIPELINE",
        "implementation_scope: external_data_acquisition_and_obsstat_diagnostics",
        "claim_tier: diagnostic_only",
        "transfer_source: external_public_data_and_external_reference",
        "sky_support_status: mixed_dataset_bound",
        "null_mock_status: not_promoted_to_inference_null",
        f"config_hash: `{payload['config_hash']}`",
        "caveats:",
        "- Acquisition and compact-product diagnostics only.",
        "- No native low-ell solver output, evidence, posterior odds, p-value, or family-identification claim is made.",
        "- DESI random/mask support remains separate unless explicit support files are locally bound.",
        f"- ACT DR6 lensing status: `{summary.get('act_dr6_lensing_status')}`.",
        f"generating_command: {payload['generating_command']}",
        "git_commit_or_worktree_state: content-addressed",
        "",
        "## Summary",
        "",
        f"- Compact product rows: {summary['compact_product_rows']}",
        f"- Present compact products: {summary['present_compact_products']}",
        f"- Missing compact products: {summary['missing_compact_products']}",
        f"- Acceptance checks: {summary['acceptance_passed']}/{summary['acceptance_total']} passed",
        "",
        "## Download Inventory",
        "",
        "| Inventory | Known additional GB | Unknown sizes | Status summary |",
        "| --- | ---: | ---: | --- |",
    ]
    for label in ("existing_compact", "approval_compact"):
        inv = payload["download_inventory"][label]
        lines.append(
            f"| `{label}` | {float(inv.get('known_additional_gb') or 0.0):.3f} | "
            f"{inv.get('unknown_size_count')} | `{inv.get('by_status')}` |"
        )
    lines.extend(
        [
            "",
            "## Compact Products",
            "",
            "| Label | Present | Size MB | Key summary |",
            "| --- | ---: | ---: | --- |",
        ]
    )
    for row in payload["compact_products"]:
        size = row.get("size_bytes")
        summary_text = ""
        if "bandpower_summary" in row:
            bp = row["bandpower_summary"]
            summary_text = f"bandpowers n={bp.get('n_points')}, ell={bp.get('ell_min')}..{bp.get('ell_max')}"
        elif "catalog_summary" in row:
            cat = row["catalog_summary"]
            summary_text = f"catalog rows={cat.get('n_rows')}, z_median={cat.get('z_median')}"
        elif "archive_summary" in row:
            archive = row["archive_summary"]
            summary_text = f"archive sample_members={archive.get('sample_member_count')}"
        else:
            summary_text = f"arrays={row.get('n_arrays')}"
        lines.append(
            f"| `{row['label']}` | `{row.get('present')}` | "
            f"{(float(size) / 1024**2) if size else 0.0:.2f} | {summary_text} |"
        )
    lines.extend(
        [
            "",
            "## Acceptance Checks",
            "",
            "| Check | Passed | Evidence |",
            "| --- | ---: | --- |",
        ]
    )
    for check in payload["acceptance_checks"]:
        evidence = json.dumps(check.get("evidence"), sort_keys=True, default=str)
        if len(evidence) > 180:
            evidence = evidence[:177] + "..."
        lines.append(f"| `{check['id']}` | `{check['passed']}` | `{evidence}` |")
    lines.append("")
    return "\n".join(lines)


def write_outputs(payload: dict[str, Any], markdown: str) -> None:
    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUT_JSON.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    OUT_MD.write_text(markdown, encoding="utf-8")


def check_outputs(payload: dict[str, Any], markdown: str) -> int:
    stale: list[str] = []
    expected_json = json.dumps(payload, indent=2, sort_keys=True) + "\n"
    if not OUT_JSON.exists() or OUT_JSON.read_text(encoding="utf-8") != expected_json:
        stale.append(_repo_relative(OUT_JSON))
    if not OUT_MD.exists() or OUT_MD.read_text(encoding="utf-8") != markdown:
        stale.append(_repo_relative(OUT_MD))
    if stale:
        print("stale v6 compact data analysis artifacts:", file=sys.stderr)
        for path in stale:
            print(f"  {path}", file=sys.stderr)
        return 1
    print("v6 compact data analysis artifacts are current")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="fail if generated files are stale")
    args = parser.parse_args(argv)

    payload = build_payload(_command([]))
    markdown = render_markdown(payload)
    if args.check:
        return check_outputs(payload, markdown)
    write_outputs(payload, markdown)
    print(f"wrote {_repo_relative(OUT_JSON)}")
    print(f"wrote {_repo_relative(OUT_MD)}")
    print(
        "   acceptance "
        f"{payload['summary']['acceptance_passed']}/{payload['summary']['acceptance_total']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
