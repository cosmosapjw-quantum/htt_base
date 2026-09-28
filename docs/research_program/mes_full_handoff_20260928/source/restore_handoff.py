#!/usr/bin/env python3
"""Verify a manifest-bound HTT/MES handoff; restore only with explicit options.

Python standard library only. Does not clone, modify a repository, execute
archived programs, unpack a database, or recurse through arbitrary archives.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import shutil
import stat
import sys
import tempfile
from datetime import datetime, timezone
import zipfile

REQUIRED_ROLES = {
    "research_backup", "early_archive_backup", "catalog_backup",
    "i1_checkpoint", "i2_checkpoint",
}
CATALOG_MEMBER = "history/HTT_CATALOG_SCAN_57ecfe21_PORTABLE.zip"
MAX_ARCHIVE_BYTES = 2 * 1024**3
MAX_MEMBER_BYTES = 512 * 1024**2
MAX_MEMBERS = 100_000


class HandoffError(Exception):
    pass


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def safe_relative(name: str, *, directory: bool = False) -> PurePosixPath:
    if not isinstance(name, str) or not name or "\\" in name or "\x00" in name:
        raise HandoffError(f"Unsafe relative path: {name!r}")
    trimmed = name[:-1] if directory and name.endswith("/") else name
    parts = trimmed.split("/")
    if any(part in ("", ".", "..") or ":" in part for part in parts):
        raise HandoffError(f"Unsafe relative path: {name!r}")
    path = PurePosixPath(trimmed)
    if path.is_absolute():
        raise HandoffError(f"Absolute path rejected: {name!r}")
    return path


def checked_file(root: Path, relative: str) -> Path:
    path = root.joinpath(*safe_relative(relative).parts)
    for candidate in (path, *path.parents):
        if candidate == root:
            break
        if candidate.is_symlink():
            raise HandoffError(f"Symlink rejected: {candidate}")
    if not path.is_file():
        raise HandoffError(f"Missing regular file: {relative}")
    return path


def load_and_verify(root: Path, manifest_name: str) -> tuple[dict, dict, list]:
    manifest_path = checked_file(root, manifest_name)
    with manifest_path.open(encoding="utf-8") as handle:
        manifest = json.load(handle)
    if manifest.get("schema_version") != 1 or not isinstance(manifest.get("files"), list):
        raise HandoffError("Manifest requires schema_version=1 and files array")
    roles, verified, seen = {}, [], set()
    for entry in manifest["files"]:
        if not isinstance(entry, dict):
            raise HandoffError("Manifest file entry is not an object")
        relative = entry.get("path")
        identity = str(safe_relative(relative)).casefold()
        if identity in seen:
            raise HandoffError(f"Duplicate manifest path: {relative}")
        seen.add(identity)
        expected_size, expected_hash = entry.get("size_bytes"), entry.get("sha256")
        if type(expected_size) is not int or expected_size < 0:
            raise HandoffError(f"Invalid size_bytes: {relative}")
        if not isinstance(expected_hash, str) or len(expected_hash) != 64 or any(
                c not in "0123456789abcdef" for c in expected_hash):
            raise HandoffError(f"Invalid SHA-256: {relative}")
        path = checked_file(root, relative)
        if path.stat().st_size != expected_size:
            raise HandoffError(f"Size mismatch: {relative}")
        actual_hash = sha256(path)
        if actual_hash != expected_hash:
            raise HandoffError(f"SHA-256 mismatch: {relative}")
        role = entry.get("role", "support_file")
        if role in REQUIRED_ROLES:
            if role in roles:
                raise HandoffError(f"Duplicate required role: {role}")
            roles[role] = path
        elif role != "support_file":
            raise HandoffError(f"Unknown role: {role!r}")
        verified.append({"path": relative, "role": role,
                         "size_bytes": expected_size, "sha256": actual_hash})
    missing = REQUIRED_ROLES - set(roles)
    if missing:
        raise HandoffError("Missing required roles: " + ", ".join(sorted(missing)))
    return manifest, roles, verified


def inspect_zip(archive: Path) -> list[zipfile.ZipInfo]:
    """Check paths and entry kinds before creating any extraction output."""
    with zipfile.ZipFile(archive) as handle:
        infos = handle.infolist()
        if len(infos) > MAX_MEMBERS:
            raise HandoffError(f"Too many archive members: {archive.name}")
        if sum(info.file_size for info in infos) > MAX_ARCHIVE_BYTES:
            raise HandoffError(f"Archive exceeds 2 GiB extraction limit: {archive.name}")
        seen, files = set(), set()
        for info in infos:
            name = safe_relative(info.filename, directory=info.is_dir())
            key = str(name).casefold()
            if key in seen:
                raise HandoffError(f"Duplicate archive member: {info.filename}")
            seen.add(key)
            if info.flag_bits & 1:
                raise HandoffError(f"Encrypted archive member: {info.filename}")
            mode = info.external_attr >> 16
            kind = stat.S_IFMT(mode)
            if kind not in (0, stat.S_IFREG, stat.S_IFDIR):
                raise HandoffError(f"Non-regular archive member: {info.filename}")
            if kind == stat.S_IFDIR and not info.is_dir():
                raise HandoffError(f"Inconsistent directory member: {info.filename}")
            if info.file_size > MAX_MEMBER_BYTES:
                raise HandoffError(f"Member exceeds 512 MiB limit: {info.filename}")
            if name.suffix.lower() in (".db", ".sqlite", ".sqlite3"):
                raise HandoffError(f"Database extraction is disabled: {info.filename}")
            if not info.is_dir():
                files.add(key)
        for info in infos:
            name = safe_relative(info.filename, directory=info.is_dir())
            if any(str(parent).casefold() in files for parent in name.parents if str(parent) != "."):
                raise HandoffError(f"File/directory collision: {info.filename}")
        return infos


def extract_zip(archive: Path, destination: Path) -> dict:
    infos = inspect_zip(archive)
    destination.mkdir(parents=True, exist_ok=False)
    files, total = 0, 0
    with zipfile.ZipFile(archive) as handle:
        for info in infos:
            target = destination.joinpath(*safe_relative(
                info.filename, directory=info.is_dir()).parts)
            if info.is_dir():
                target.mkdir(parents=True, exist_ok=True)
                continue
            target.parent.mkdir(parents=True, exist_ok=True)
            # Exclusive creation is an additional no-overwrite guard.
            with handle.open(info, "r") as source, target.open("xb") as output:
                shutil.copyfileobj(source, output, length=1024 * 1024)
            if target.stat().st_size != info.file_size:
                raise HandoffError(f"Extracted size mismatch: {info.filename}")
            files += 1
            total += info.file_size
    return {"files": files, "uncompressed_bytes": total}


def restore(roles: dict, destination: Path, include_catalog: bool, base_receipt: dict) -> dict:
    destination = destination.absolute()
    if os.path.lexists(destination):
        raise HandoffError(f"Destination already exists; refusing overwrite: {destination}")
    if not destination.parent.is_dir():
        raise HandoffError(f"Destination parent must already exist: {destination.parent}")
    plan = [
        ("research_backup", "research_backup"),
        ("early_archive_backup", "early_archive_backup"),
        ("i1_checkpoint", "checkpoints/I1"),
        ("i2_checkpoint", "checkpoints/I2"),
    ]
    if include_catalog:
        plan.append(("catalog_backup", "catalog_backup"))
    for role, _ in plan:
        inspect_zip(roles[role])
    stage = Path(tempfile.mkdtemp(prefix=f".{destination.name}.incomplete-",
                                  dir=destination.parent))
    try:
        summaries = {}
        for role, relative in plan:
            summaries[relative] = extract_zip(roles[role], stage / relative)
        if include_catalog:
            portable = stage / "catalog_backup" / CATALOG_MEMBER
            if not portable.is_file():
                raise HandoffError(f"Expected catalog payload missing: {CATALOG_MEMBER}")
            summaries["catalog_exports"] = extract_zip(portable, stage / "catalog_exports")
        receipt = dict(base_receipt, status="RESTORED", destination=str(destination),
                       restored=summaries, catalog_extracted=include_catalog,
                       nested_archive_recursion=False, repository_mutated=False,
                       database_restored=False)
        # mkdir reserves the final path without replacing any existing object.
        # Move only the children; any concurrent collision fails instead of overwriting.
        destination.mkdir(exist_ok=False)
        for item in stage.iterdir():
            final = destination / item.name
            if os.path.lexists(final):
                raise HandoffError(f"Unexpected destination collision: {final}")
            os.rename(item, final)
        stage.rmdir()
        # Success becomes visible only after every payload has been published.
        # A failed payload move leaves no authoritative success receipt, even
        # when the filesystem enumerates a receipt before other entries.
        pending_receipt = destination / ".RESTORE_RECEIPT.pending.json"
        with pending_receipt.open("x", encoding="utf-8") as output:
            json.dump(receipt, output, ensure_ascii=False, indent=2)
            output.write("\n")
        final_receipt = destination / "RESTORE_RECEIPT.json"
        if os.path.lexists(final_receipt):
            raise HandoffError(f"Unexpected destination collision: {final_receipt}")
        os.rename(pending_receipt, final_receipt)
        return receipt
    except Exception as error:
        raise HandoffError(
            f"Restore failed; inspect partial staging path {stage} and partial "
            f"destination {destination}; no successful restore is declared: {error}") from error


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--bundle-root", type=Path, default=Path(__file__).resolve().parent.parent)
    parser.add_argument("--manifest", default="DELIVERY_MANIFEST.json")
    parser.add_argument("--restore", action="store_true", help="Explicitly authorize extraction")
    parser.add_argument("--destination", type=Path, help="New, non-existing restoration directory")
    parser.add_argument("--catalog", action="store_true", help="Also expand the portable catalog exports")
    args = parser.parse_args(argv)
    if args.restore and args.destination is None:
        parser.error("--restore requires --destination")
    if not args.restore and (args.destination is not None or args.catalog):
        parser.error("--destination and --catalog require --restore")
    try:
        root = args.bundle_root.resolve(strict=True)
        _, roles, verified = load_and_verify(root, args.manifest)
        receipt = {
            "status": "VERIFIED_ARCHIVE_BYTES_ONLY", "schema_version": 1,
            "created_utc": datetime.now(timezone.utc).isoformat(),
            "bundle_root": str(root), "manifest_sha256": sha256(root / args.manifest),
            "verified_files": verified,
            "warning": "Byte identity does not establish scientific validity or source authority.",
        }
        if args.restore:
            receipt = restore(roles, args.destination, args.catalog, receipt)
        print(json.dumps(receipt, ensure_ascii=False, indent=2))
        return 0
    except (HandoffError, OSError, ValueError, zipfile.BadZipFile, RuntimeError) as error:
        print(json.dumps({"status": "FAILED", "error": str(error)}, ensure_ascii=False), file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
