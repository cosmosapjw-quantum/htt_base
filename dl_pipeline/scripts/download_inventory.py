#!/usr/bin/env python3
"""Download planning helpers for the BASS data pipeline.

This module is deliberately free of project imports so that the copied
``dl_pipeline`` folder remains runnable without a git checkout or installed
package.  It handles only acquisition metadata: URL resolution, size probes,
local presence checks, and manifest payloads.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from html.parser import HTMLParser
import hashlib
import json
import os
import subprocess
from pathlib import Path
import tarfile
from typing import Any, Iterable
from urllib.parse import urljoin
import urllib.error
import urllib.request


DEFAULT_DOWNLOAD_CAP_BYTES = 50 * 1024**3
USER_AGENT = "htt-base-dl-pipeline/1.0"


@dataclass(frozen=True)
class DownloadSpec:
    stage: str
    item_id: str
    dst: Path
    url: str | None = None
    source_page: str | None = None
    filename: str | None = None
    optional: bool = False
    expected_size_bytes: int | None = None
    caveats: tuple[str, ...] = ()


@dataclass(frozen=True)
class DownloadProbe:
    stage: str
    item_id: str
    url: str | None
    source_page: str | None
    filename: str | None
    destination: str
    optional: bool
    expected_size_bytes: int | None
    remote_size_bytes: int | None
    local_size_bytes: int | None
    additional_bytes: int | None
    status: str
    caveats: tuple[str, ...]


class _HrefParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.hrefs: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag.lower() != "a":
            return
        for key, value in attrs:
            if key.lower() == "href" and value:
                self.hrefs.append(value)


def _read_url_text(url: str) -> str:
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(req, timeout=60) as response:
        return response.read().decode("utf-8", errors="replace")


def extract_named_href(html: str, filename: str) -> str | None:
    parser = _HrefParser()
    parser.feed(html)
    for href in parser.hrefs:
        if href.rsplit("/", 1)[-1] == filename:
            return href
    for href in parser.hrefs:
        if filename in href:
            return href
    return None


def resolve_download_url(spec: DownloadSpec, *, fetch_pages: bool = True) -> str | None:
    if spec.url:
        return spec.url
    if not spec.source_page or not spec.filename or not fetch_pages:
        return None
    html = _read_url_text(spec.source_page)
    href = extract_named_href(html, spec.filename)
    if href is None:
        return None
    return urljoin(spec.source_page, href)


def _content_length_from_range(value: str | None) -> int | None:
    if not value or "/" not in value:
        return None
    try:
        return int(value.rsplit("/", 1)[1])
    except ValueError:
        return None


def remote_size_bytes(url: str) -> int | None:
    req = urllib.request.Request(url, method="HEAD", headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(req, timeout=60) as response:
            value = response.headers.get("Content-Length")
            return int(value) if value is not None else None
    except urllib.error.HTTPError as exc:
        if exc.code not in {403, 405, 501}:
            raise

    req = urllib.request.Request(
        url,
        headers={"User-Agent": USER_AGENT, "Range": "bytes=0-0"},
    )
    with urllib.request.urlopen(req, timeout=60) as response:
        value = response.headers.get("Content-Range")
        return _content_length_from_range(value)


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def sha256_jsonable(value: Any) -> str:
    payload = json.dumps(value, sort_keys=True, ensure_ascii=False, default=str).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def git_worktree_state(start: Path) -> dict[str, Any]:
    probe = start if start.is_dir() else start.parent
    try:
        top = subprocess.run(
            ["git", "-C", str(probe), "rev-parse", "--show-toplevel"],
            check=True, capture_output=True, text=True, timeout=10,
        ).stdout.strip()
        commit = subprocess.run(
            ["git", "-C", top, "rev-parse", "HEAD"],
            check=True, capture_output=True, text=True, timeout=10,
        ).stdout.strip()
        status = subprocess.run(
            ["git", "-C", top, "status", "--short"],
            check=True, capture_output=True, text=True, timeout=10,
        ).stdout.splitlines()
        return {
            "status": "available",
            "repo_root": top,
            "commit": commit,
            "dirty": bool(status),
            "status_short": status,
        }
    except Exception as exc:  # noqa: BLE001 - git may be absent in copied folders.
        return {
            "status": "unavailable",
            "reason": f"{type(exc).__name__}:{exc}",
        }


def _coerce_expected_size(value: Any) -> int | None:
    if value is None:
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _download_entry(stage: str, root: Path, entry: dict[str, Any]) -> DownloadSpec:
    dst = root / str(entry["out"])
    return DownloadSpec(
        stage=stage,
        item_id=str(entry.get("id") or Path(str(entry["out"])).name),
        dst=dst,
        url=entry.get("url"),
        source_page=entry.get("page"),
        filename=entry.get("filename"),
        optional=bool(entry.get("optional", False)),
        expected_size_bytes=_coerce_expected_size(entry.get("expected_size_bytes")),
        caveats=tuple(str(v) for v in entry.get("caveats", ())),
    )


def iter_stage_download_specs(
    sources: dict[str, Any],
    stage_ids: Iterable[str],
    root: Path,
) -> list[DownloadSpec]:
    specs: list[DownloadSpec] = []
    for stage in stage_ids:
        meta = sources.get(stage, {})
        for entry in meta.get("downloads", []):
            specs.append(_download_entry(stage, root, entry))

        if stage == "planck_pr3":
            files = meta.get("files", {})
            for group, base_key in (
                ("spectra", "base_cosmoparams"),
                ("theory", "base_cosmoparams"),
                ("masks", "base_masks"),
                ("maps_optional_large", "base_maps"),
            ):
                base = meta.get(base_key)
                for fname in files.get(group, []):
                    specs.append(
                        DownloadSpec(
                            stage=stage,
                            item_id=f"planck_pr3_{fname}",
                            url=f"{base}/{fname}" if base else None,
                            dst=root / "raw" / "planck_data" / fname,
                        )
                    )

        if stage == "desi_y1":
            base = meta.get("base")
            for fname in meta.get("files", []):
                specs.append(
                    DownloadSpec(
                        stage=stage,
                        item_id=f"desi_y1_{fname}",
                        url=f"{base}/{fname}" if base else None,
                        dst=root / "raw" / "desi" / fname,
                    )
                )
            for fname in meta.get("support_probe_files", []):
                specs.append(
                    DownloadSpec(
                        stage=stage,
                        item_id=f"desi_y1_support_{fname}",
                        url=f"{base}/{fname}" if base else None,
                        dst=root / "raw" / "desi_support" / fname,
                        optional=True,
                        caveats=("probe_only_until_separate_approval",),
                    )
                )

        if stage == "cf4" and meta.get("download_url") and meta.get("expected_filename"):
            specs.append(
                DownloadSpec(
                    stage=stage,
                    item_id="cf4_grid",
                    url=str(meta["download_url"]),
                    dst=root / "raw" / "cf4" / str(meta["expected_filename"]),
                    optional=True,
                )
            )

        if stage == "cf4_full":
            base = meta.get("base")
            if base:
                specs.append(
                    DownloadSpec(
                        stage=stage,
                        item_id="cf4_full_ReadMe",
                        url=f"{base}/ReadMe",
                        dst=root / "raw" / "cf4_full" / "ReadMe",
                    )
                )
                for table in meta.get("tables", []):
                    specs.append(
                        DownloadSpec(
                            stage=stage,
                            item_id=f"cf4_full_{table}.gz",
                            url=f"{base}/{table}.gz",
                            dst=root / "raw" / "cf4_full" / f"{table}.gz",
                        )
                    )
    return specs


def build_download_inventory(
    sources: dict[str, Any],
    root: Path,
    stage_ids: Iterable[str],
    *,
    max_download_bytes: int = DEFAULT_DOWNLOAD_CAP_BYTES,
    probe_network: bool = True,
) -> dict[str, Any]:
    probes: list[DownloadProbe] = []
    known_additional = 0
    unknown_count = 0

    for spec in iter_stage_download_specs(sources, stage_ids, root):
        caveats = list(spec.caveats)
        url = None
        remote_size = None
        status = "needs_download"
        try:
            url = resolve_download_url(spec, fetch_pages=probe_network)
            if url and probe_network:
                remote_size = remote_size_bytes(url)
        except Exception as exc:  # noqa: BLE001 - inventory records probe failures.
            status = "probe_failed"
            caveats.append(f"probe_failed:{type(exc).__name__}:{exc}")

        expected_size = spec.expected_size_bytes
        size_for_budget = remote_size if remote_size is not None else expected_size
        local_size = spec.dst.stat().st_size if spec.dst.exists() else None
        if spec.dst.exists():
            additional = 0
            if size_for_budget is not None and local_size != size_for_budget:
                status = "local_size_mismatch"
                caveats.append("local_size_differs_from_remote_or_expected")
            elif status != "probe_failed":
                status = "present"
        elif size_for_budget is None:
            additional = None
            unknown_count += 1
            if status != "probe_failed":
                status = "size_unknown"
        else:
            additional = size_for_budget
            known_additional += additional

        probes.append(
            DownloadProbe(
                stage=spec.stage,
                item_id=spec.item_id,
                url=url,
                source_page=spec.source_page,
                filename=spec.filename,
                destination=str(spec.dst),
                optional=spec.optional,
                expected_size_bytes=expected_size,
                remote_size_bytes=remote_size,
                local_size_bytes=local_size,
                additional_bytes=additional,
                status=status,
                caveats=tuple(caveats),
            )
        )

    return {
        "schema_version": "download_inventory.v1",
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "root": str(root),
        "stage_ids": list(stage_ids),
        "cap_bytes": max_download_bytes,
        "cap_gb": max_download_bytes / 1024**3,
        "known_additional_bytes": known_additional,
        "known_additional_gb": known_additional / 1024**3,
        "unknown_size_count": unknown_count,
        "within_cap_for_known_sizes": known_additional <= max_download_bytes,
        "metadata": {
            "owner": "DL_PIPELINE",
            "implementation_scope": "external_data_acquisition",
            "claim_tier": "input_provenance_only",
            "transfer_source": "external_public_data",
            "config_hash": sha256_jsonable({"stage_ids": list(stage_ids), "sources": sources}),
            "input_hashes": [],
            "sky_support_status": "not_evaluated_by_download_stage",
            "null_mock_status": "not_evaluated_by_download_stage",
            "git_worktree_state": git_worktree_state(root),
            "caveats": [
                "download inventory is not a scientific result",
                "external public data are not native solver outputs",
                "MIO/HTT posterior or evidence claims are not created here",
            ],
        },
        "items": [asdict(probe) for probe in probes],
    }


def write_inventory_outputs(inventory: dict[str, Any], json_path: Path) -> tuple[Path, Path]:
    json_path.parent.mkdir(parents=True, exist_ok=True)
    md_path = json_path.with_suffix(".md")
    json_path.write_text(json.dumps(inventory, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    lines = [
        "# Download Inventory",
        "",
        f"- created_utc: `{inventory['created_utc']}`",
        f"- root: `{inventory['root']}`",
        f"- cap_gb: `{inventory['cap_gb']:.2f}`",
        f"- known_additional_gb: `{inventory['known_additional_gb']:.3f}`",
        f"- unknown_size_count: `{inventory['unknown_size_count']}`",
        f"- within_cap_for_known_sizes: `{inventory['within_cap_for_known_sizes']}`",
        "",
        "| stage | item | status | additional MB | destination |",
        "|---|---|---:|---:|---|",
    ]
    for item in inventory["items"]:
        additional = item.get("additional_bytes")
        add_mb = "unknown" if additional is None else f"{additional / 1024**2:.1f}"
        lines.append(
            "| {stage} | {item_id} | {status} | {add_mb} | `{destination}` |".format(
                stage=item["stage"],
                item_id=item["item_id"],
                status=item["status"],
                add_mb=add_mb,
                destination=item["destination"],
            )
        )
    md_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return json_path, md_path


def safe_extract_tar(archive: Path, dst: Path) -> list[Path]:
    dst.mkdir(parents=True, exist_ok=True)
    extracted: list[Path] = []
    with tarfile.open(archive, "r:*") as tf:
        for member in tf.getmembers():
            target = (dst / member.name).resolve()
            if os.path.commonpath([str(dst.resolve()), str(target)]) != str(dst.resolve()):
                raise ValueError(f"unsafe tar member path: {member.name}")
        tf.extractall(dst)
        for member in tf.getmembers():
            if member.isfile():
                extracted.append(dst / member.name)
    return extracted


def write_acquisition_manifest(
    manifest_path: Path,
    *,
    stage: str,
    source_items: list[dict[str, Any]],
    local_files: Iterable[Path],
    generating_command: str,
) -> Path:
    files = []
    for path in local_files:
        if path.exists() and path.is_file():
            files.append(
                {
                    "path": str(path),
                    "size_bytes": path.stat().st_size,
                    "sha256": sha256_file(path),
                }
            )
    payload = {
        "schema_version": "external_acquisition_manifest.v1",
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "stage": stage,
        "owner": "DL_PIPELINE",
        "implementation_scope": "external_data_acquisition",
        "claim_tier": "input_provenance_only",
        "transfer_source": "external_public_data",
        "config_hash": sha256_jsonable(source_items),
        "input_hashes": [entry["sha256"] for entry in files],
        "sky_support_status": "not_evaluated_by_download_stage",
        "null_mock_status": "not_evaluated_by_download_stage",
        "git_worktree_state": git_worktree_state(manifest_path),
        "caveats": [
            "download manifest records acquisition only",
            "no native solver, family-identification, posterior, or evidence claim is made",
        ],
        "generating_command": generating_command,
        "source_items": source_items,
        "local_files": files,
    }
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return manifest_path
