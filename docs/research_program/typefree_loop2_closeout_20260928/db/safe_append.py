#!/usr/bin/env python3
"""Create a corrected Loop 2 SQLite copy without ever mutating its source.

The historical migration scripts remain immutable evidence.  This successor
reserves every output before copying, rejects path/inode aliases, verifies the
published final Loop 2 input, appends correction/review rows transactionally,
and emits a deterministic gzip plus a measured receipt.
"""
from __future__ import annotations

import argparse
import gzip
import hashlib
import json
import os
import shutil
import sqlite3
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Mapping, Sequence


PUBLISHED_GZIP_SHA256 = "393bdfa1a8a61a3aba54a2c64db38b93d7258e7d4802717d8b6c61fcb468c676"
PUBLISHED_SQLITE_SHA256 = "0460375149587695b629a1eaea0d8a3287d58f58bb7c40b2888c580522ec7817"
PINNED_COMMIT = "de3ab20219c46c2b14f1d2ec6bb87508c331634d"
CHUNK = 4 * 1024 * 1024


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(CHUNK), b""):
            digest.update(block)
    return digest.hexdigest()


def _path_key(path: Path) -> str:
    return os.path.normcase(str(path.parent.resolve(strict=False) / path.name))


def _reject_aliases(source: Path, outputs: Sequence[Path]) -> None:
    if source.is_symlink() or not source.is_file():
        raise ValueError("source must be an existing non-symlink regular file")
    source_key = _path_key(source)
    seen = {source_key}
    for output in outputs:
        key = _path_key(output)
        if key in seen:
            raise ValueError(f"same-path alias refused: {output}")
        seen.add(key)
        if os.path.lexists(output):
            try:
                if os.path.samefile(source, output):
                    raise ValueError(f"source inode alias refused: {output}")
            except FileNotFoundError:
                pass
            raise FileExistsError(f"refusing existing output: {output}")


def _reserve(paths: Sequence[Path]) -> dict[Path, int]:
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL
    if hasattr(os, "O_NOFOLLOW"):
        flags |= os.O_NOFOLLOW
    created: list[Path] = []
    descriptors: dict[Path, int] = {}
    try:
        for path in paths:
            path.parent.mkdir(parents=True, exist_ok=True)
            fd = os.open(path, flags, 0o644)
            descriptors[path] = fd
            created.append(path)
        return descriptors
    except BaseException:
        for fd in descriptors.values():
            os.close(fd)
        for path in created:
            path.unlink(missing_ok=True)
        raise


def _copy_source(source: Path, output_fd: int) -> None:
    with source.open("rb") as raw:
        magic = raw.read(2)
        raw.seek(0)
        stream = gzip.GzipFile(fileobj=raw, mode="rb") if magic == b"\x1f\x8b" else raw
        with stream, os.fdopen(os.dup(output_fd), "wb") as target:
            shutil.copyfileobj(stream, target, length=CHUNK)
            target.flush()
            os.fsync(target.fileno())


def _quote(name: str) -> str:
    return '"' + name.replace('"', '""') + '"'


def _encode_value(value: object) -> bytes:
    if value is None:
        return b"N;"
    if isinstance(value, bytes):
        return b"B" + str(len(value)).encode() + b":" + value + b";"
    raw = str(value).encode("utf-8", "surrogatepass")
    return type(value).__name__.encode() + b":" + str(len(raw)).encode() + b":" + raw + b";"


def database_snapshot(connection: sqlite3.Connection) -> dict[str, object]:
    schema = connection.execute(
        "SELECT type,name,tbl_name,sql FROM sqlite_master ORDER BY type,name"
    ).fetchall()
    tables = [row[1] for row in schema if row[0] == "table" and not row[1].startswith("sqlite_")]
    rowsets: dict[str, dict[str, object]] = {}
    for table in tables:
        digest = hashlib.sha256()
        count = 0
        # The source is first copied byte-for-byte, so scan order is stable for
        # this before/after comparison.  Do not assume rowid: FTS5 shadow
        # tables include WITHOUT ROWID objects.
        for row in connection.execute(f"SELECT * FROM {_quote(table)}"):
            count += 1
            for value in row:
                digest.update(_encode_value(value))
            digest.update(b"\n")
        rowsets[table] = {"rows": count, "sha256": digest.hexdigest()}
    schema_bytes = json.dumps(schema, ensure_ascii=False, separators=(",", ":")).encode()
    return {"schema_sha256": hashlib.sha256(schema_bytes).hexdigest(), "tables": rowsets}


def _load_rows(path: Path, key: str) -> list[Mapping[str, object]]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    rows = payload[key]
    if not isinstance(rows, list) or not rows:
        raise ValueError(f"{path}: {key} must be a non-empty list")
    return rows


def _append(connection: sqlite3.Connection, corrections: list[Mapping[str, object]], reviews: list[Mapping[str, object]]) -> None:
    connection.execute("BEGIN IMMEDIATE")
    connection.execute(
        """CREATE TABLE loop2_corrections (
        correction_id TEXT PRIMARY KEY, pinned_commit TEXT NOT NULL,
        supersedes_path TEXT NOT NULL, supersedes_sha256 TEXT NOT NULL,
        statement TEXT NOT NULL, status TEXT NOT NULL,
        artifact_path TEXT NOT NULL, artifact_sha256 TEXT NOT NULL,
        caveat TEXT NOT NULL)"""
    )
    connection.execute(
        """CREATE TABLE loop2_closeout_reviews (
        review_id TEXT PRIMARY KEY, reviewer_role TEXT NOT NULL,
        status TEXT NOT NULL, scope TEXT NOT NULL,
        artifact_path TEXT NOT NULL, artifact_sha256 TEXT NOT NULL,
        caveat TEXT NOT NULL)"""
    )
    for row in corrections:
        connection.execute(
            "INSERT INTO loop2_corrections VALUES (?,?,?,?,?,?,?,?,?)",
            (
                row["correction_id"], PINNED_COMMIT, row["supersedes_path"],
                row["supersedes_sha256"], row["statement"], row["status"],
                row["artifact_path"], row["artifact_sha256"], row["caveat"],
            ),
        )
    for row in reviews:
        connection.execute(
            "INSERT INTO loop2_closeout_reviews VALUES (?,?,?,?,?,?,?)",
            tuple(row[key] for key in (
                "review_id", "reviewer_role", "status", "scope",
                "artifact_path", "artifact_sha256", "caveat",
            )),
        )
    connection.commit()


def _write_gzip(source: Path, target_fd: int) -> None:
    with os.fdopen(os.dup(target_fd), "wb") as raw:
        with gzip.GzipFile(filename="", mode="wb", fileobj=raw, mtime=0, compresslevel=6) as zipped:
            with source.open("rb") as handle:
                shutil.copyfileobj(handle, zipped, length=CHUNK)
        raw.flush()
        os.fsync(raw.fileno())


@dataclass(frozen=True)
class MigrationSpec:
    source_sha256: str
    sqlite_sha256: str
    failure_stage: str | None = None


def migrate(source: Path, output: Path, gzip_output: Path, receipt: Path,
            corrections_path: Path, reviews_path: Path,
            spec: MigrationSpec) -> dict[str, object]:
    source, output, gzip_output, receipt = map(Path, (source, output, gzip_output, receipt))
    outputs = (output, gzip_output, receipt)
    _reject_aliases(source, outputs)
    before_stat = source.stat()
    before_sha = sha256(source)
    if before_sha != spec.source_sha256:
        raise ValueError(f"source SHA-256 mismatch: {before_sha}")
    reserved = _reserve(outputs)
    try:
        _copy_source(source, reserved[output])
        if sha256(output) != spec.sqlite_sha256:
            raise ValueError("decompressed SQLite SHA-256 mismatch")
        if spec.failure_stage == "after_copy":
            raise RuntimeError("injected failure after copy")
        connection = sqlite3.connect(output)
        try:
            if connection.execute("PRAGMA integrity_check").fetchone()[0] != "ok":
                raise ValueError("source copy failed SQLite integrity_check")
            before_snapshot = database_snapshot(connection)
            corrections = _load_rows(corrections_path, "corrections")
            reviews = _load_rows(reviews_path, "reviews")
            _append(connection, corrections, reviews)
            if connection.execute("PRAGMA integrity_check").fetchone()[0] != "ok":
                raise ValueError("corrected database failed integrity_check")
            after_snapshot = database_snapshot(connection)
        finally:
            connection.close()
        preserved = {
            name: details for name, details in after_snapshot["tables"].items()
            if name not in {"loop2_corrections", "loop2_closeout_reviews"}
        }
        if before_snapshot["tables"] != preserved:
            raise ValueError("historical table rows changed")
        _write_gzip(output, reserved[gzip_output])
        after_stat = source.stat()
        after_sha = sha256(source)
        source_unchanged = (
            before_sha == after_sha
            and before_stat.st_size == after_stat.st_size
            and before_stat.st_ino == after_stat.st_ino
            and before_stat.st_dev == after_stat.st_dev
        )
        if not source_unchanged:
            raise ValueError("source identity changed during migration")
        result = {
            "format": "TYPEFREE_LOOP2_SAFE_APPEND_RECEIPT_V1",
            "pinned_commit": PINNED_COMMIT,
            "source": {"path": str(source), "sha256_before": before_sha, "sha256_after": after_sha,
                       "bytes": before_stat.st_size, "inode": before_stat.st_ino,
                       "device": before_stat.st_dev, "unchanged_measured": True},
            "output": {"path": str(output), "sha256": sha256(output), "bytes": output.stat().st_size},
            "gzip": {"path": str(gzip_output), "sha256": sha256(gzip_output), "bytes": gzip_output.stat().st_size,
                     "mtime": 0, "embedded_filename": ""},
            "historical_snapshot_before": before_snapshot,
            "historical_rows_preserved": True,
            "correction_rows": len(corrections),
            "review_rows": len(reviews),
            "integrity_check": "ok",
            "command": sys.argv,
        }
        with os.fdopen(os.dup(reserved[receipt]), "wb") as handle:
            handle.write(json.dumps(result, ensure_ascii=False, sort_keys=True, indent=2).encode("utf-8") + b"\n")
            handle.flush()
            os.fsync(handle.fileno())
        return result
    except BaseException:
        for path in outputs:
            path.unlink(missing_ok=True)
        raise
    finally:
        for fd in reserved.values():
            os.close(fd)


def self_check() -> int:
    print(json.dumps({"status": "PASS", "known_source_sha256": PUBLISHED_GZIP_SHA256,
                      "known_sqlite_sha256": PUBLISHED_SQLITE_SHA256}, sort_keys=True))
    return 0


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--gzip-output", type=Path)
    parser.add_argument("--receipt", type=Path)
    parser.add_argument("--corrections", type=Path)
    parser.add_argument("--reviews", type=Path)
    parser.add_argument("--self-check", action="store_true")
    args = parser.parse_args(argv)
    if args.self_check:
        return self_check()
    required = (args.source, args.output, args.gzip_output, args.receipt, args.corrections, args.reviews)
    if any(value is None for value in required):
        parser.error("all migration paths are required unless --self-check is used")
    result = migrate(*required, spec=MigrationSpec(PUBLISHED_GZIP_SHA256, PUBLISHED_SQLITE_SHA256))
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
