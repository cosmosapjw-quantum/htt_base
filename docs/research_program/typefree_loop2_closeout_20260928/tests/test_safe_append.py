from __future__ import annotations

import gzip
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import sqlite3
import sys

import pytest


MODULE_PATH = Path(__file__).parents[1] / "db" / "safe_append.py"
SPEC = importlib.util.spec_from_file_location("loop2_safe_append", MODULE_PATH)
assert SPEC and SPEC.loader
safe = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = safe
SPEC.loader.exec_module(safe)


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def fixture(tmp_path: Path) -> tuple[Path, Path, Path, safe.MigrationSpec]:
    tmp_path.mkdir(parents=True, exist_ok=True)
    raw = tmp_path / "source.sqlite"
    con = sqlite3.connect(raw)
    con.execute("CREATE TABLE history (id INTEGER PRIMARY KEY, value TEXT NOT NULL)")
    con.executemany("INSERT INTO history(value) VALUES (?)", [("alpha",), ("beta",)])
    con.execute("CREATE TABLE loop2_evidence (claim_id TEXT PRIMARY KEY, caveat TEXT)")
    con.execute("INSERT INTO loop2_evidence VALUES ('TF-P2','historical')")
    con.commit(); con.close()
    compressed = tmp_path / "source.sqlite.gz"
    with compressed.open("wb") as handle:
        with gzip.GzipFile(filename="", mode="wb", fileobj=handle, mtime=0) as zipped:
            zipped.write(raw.read_bytes())
    corrections = tmp_path / "corrections.json"
    reviews = tmp_path / "reviews.json"
    artifact = tmp_path / "artifact.md"; artifact.write_text("evidence\n")
    row_hash = digest(artifact)
    corrections.write_text(json.dumps({"corrections": [{
        "correction_id":"F1", "supersedes_path":"old.md", "supersedes_sha256":"0"*64,
        "statement":"bounded-domain correction", "status":"DERIVED",
        "artifact_path":"artifact.md", "artifact_sha256":row_hash, "caveat":"finite dimensional"
    }]}))
    reviews.write_text(json.dumps({"reviews": [{
        "review_id":"R1", "reviewer_role":"independent", "status":"PASS",
        "scope":"F1-F3", "artifact_path":"review.json", "artifact_sha256":"1"*64,
        "caveat":"not four-axis admission"
    }]}))
    return compressed, corrections, reviews, safe.MigrationSpec(digest(compressed), digest(raw))


def run(tmp_path: Path, failure_stage: str | None = None):
    source, corrections, reviews, spec = fixture(tmp_path)
    spec = safe.MigrationSpec(spec.source_sha256, spec.sqlite_sha256, failure_stage)
    return source, safe.migrate(source, tmp_path/"out.sqlite", tmp_path/"out.sqlite.gz",
                                tmp_path/"receipt.json", corrections, reviews, spec)


def test_rejects_original_and_output_same_path(tmp_path: Path) -> None:
    source, corrections, reviews, spec = fixture(tmp_path)
    before = digest(source)
    with pytest.raises(ValueError, match="same-path"):
        safe.migrate(source, source, tmp_path/"out.gz", tmp_path/"receipt.json", corrections, reviews, spec)
    assert digest(source) == before


@pytest.mark.parametrize("kind", ["symlink", "hardlink"])
def test_rejects_source_alias(tmp_path: Path, kind: str) -> None:
    source, corrections, reviews, spec = fixture(tmp_path)
    alias = tmp_path / "alias.sqlite.gz"
    alias.symlink_to(source) if kind == "symlink" else os.link(source, alias)
    before = digest(source)
    with pytest.raises((ValueError, FileExistsError)):
        safe.migrate(source, alias, tmp_path/"out.gz", tmp_path/"receipt.json", corrections, reviews, spec)
    assert digest(source) == before


def test_existing_late_output_collision_is_preflight(tmp_path: Path) -> None:
    source, corrections, reviews, spec = fixture(tmp_path)
    gzip_output = tmp_path / "out.sqlite.gz"; gzip_output.write_bytes(b"keep")
    before = digest(source)
    with pytest.raises(FileExistsError):
        safe.migrate(source, tmp_path/"out.sqlite", gzip_output, tmp_path/"receipt.json", corrections, reviews, spec)
    assert not (tmp_path/"out.sqlite").exists()
    assert gzip_output.read_bytes() == b"keep"
    assert digest(source) == before


def test_injected_failure_cleans_only_created_outputs(tmp_path: Path) -> None:
    source, corrections, reviews, spec = fixture(tmp_path)
    before = digest(source)
    with pytest.raises(RuntimeError, match="injected"):
        safe.migrate(source, tmp_path/"out.sqlite", tmp_path/"out.sqlite.gz", tmp_path/"receipt.json",
                     corrections, reviews, safe.MigrationSpec(spec.source_sha256, spec.sqlite_sha256, "after_copy"))
    assert digest(source) == before
    assert not any((tmp_path/name).exists() for name in ("out.sqlite", "out.sqlite.gz", "receipt.json"))


def test_normal_append_preserves_history_schema_and_rows(tmp_path: Path) -> None:
    source, result = run(tmp_path)
    assert result["source"]["unchanged_measured"] is True
    assert result["historical_rows_preserved"] is True
    con = sqlite3.connect(tmp_path/"out.sqlite")
    assert con.execute("SELECT * FROM history ORDER BY id").fetchall() == [(1,"alpha"),(2,"beta")]
    assert con.execute("SELECT count(*) FROM loop2_evidence").fetchone() == (1,)
    assert con.execute("SELECT count(*) FROM loop2_corrections").fetchone() == (1,)
    assert con.execute("SELECT count(*) FROM loop2_closeout_reviews").fetchone() == (1,)
    assert con.execute("PRAGMA integrity_check").fetchone() == ("ok",)
    con.close()
    first = (tmp_path/"out.sqlite.gz").read_bytes()
    # A second independent destination from the same source is byte deterministic.
    _, corrections, reviews, spec = fixture(tmp_path/"second")
    safe.migrate(tmp_path/"second/source.sqlite.gz", tmp_path/"second/out.sqlite",
                 tmp_path/"second/out.sqlite.gz", tmp_path/"second/receipt.json", corrections, reviews, spec)
    assert first == (tmp_path/"second/out.sqlite.gz").read_bytes()
