"""R107 cloud acquisition manifest: schema, DAG binding and the no-clobber, bounded fetch semantics."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

from scripts.r107_cloud import acquisition as acq

ROOT = Path(__file__).resolve().parents[2]
NODE60 = ROOT / "docs/research_program/observational_publication_20261015/R105_RESEARCH_20261124/NODE60_EXECUTION.json"


def test_items_are_unique_typed_and_bound_to_dag_nodes():
    nodes = {n["id"] for n in json.loads(NODE60.read_text())["nodes"]}
    ids = [it["id"] for it in acq.ITEMS]
    assert len(ids) == len(set(ids))
    for it in acq.ITEMS:
        assert it["kind"] in acq.KINDS and it["priority"] in ("P0", "P1", "P2")
        assert it["nodes"] and set(it["nodes"]) <= nodes, it["id"]
        assert it["purpose"] and it["citation"] and it["verification"] and it["checked"]
        if it["kind"] == "https_file":
            assert it["files"] and all(f["url"].startswith("https://") for f in it["files"])
        if it["kind"] == "existing_fetcher":
            assert "scripts." in it["command"]
        if it["kind"] == "tap_query":
            assert it["adql"].upper().startswith("SELECT")


def test_plan_counts_known_bytes_and_budget():
    out = acq.plan(["D00", "D06"], 10 ** 6)
    assert out["known_bytes"] == 272000 + 1700 + 17797 + 25191 + 103017
    assert out["within_budget_for_known_sizes"] is True
    assert any(r.get("kind") == "existing_fetcher" for r in out["rows"])
    assert acq.plan(["D09"], 10 ** 6)["within_budget_for_known_sizes"] is False


def _spec(tmp_path, data: bytes, **over):
    src = tmp_path / "src.bin"
    src.write_bytes(data)
    spec = {"name": "product.bin", "url": src.as_uri(), "expected_bytes": len(data), "sha256": hashlib.sha256(data).hexdigest()}
    spec.update(over)
    return spec


def test_fetch_publishes_once_and_never_clobbers(tmp_path):
    data = b"r107 payload" * 100
    dest = tmp_path / "dest"
    rec = acq.fetch_file(_spec(tmp_path, data), dest, 10 ** 6, allow_file_urls=True)
    assert rec["status"] == "FETCHED" and rec["bytes"] == len(data) and (dest / "product.bin").read_bytes() == data
    again = acq.fetch_file(_spec(tmp_path, data), dest, 10 ** 6, allow_file_urls=True)
    assert again["status"] == "REUSED_EXISTING" and again["downloaded"] is False
    (dest / "product.bin").write_bytes(b"different")
    with pytest.raises(FileExistsError):
        acq.fetch_file(_spec(tmp_path, data), dest, 10 ** 6, allow_file_urls=True)
    assert (dest / "product.bin").read_bytes() == b"different"


def test_fetch_rejects_digest_size_budget_and_scheme_violations(tmp_path):
    data = b"x" * 4096
    with pytest.raises(ValueError, match="SHA-256"):
        acq.fetch_file(_spec(tmp_path, data, sha256="0" * 64), tmp_path / "a", 10 ** 6, allow_file_urls=True)
    with pytest.raises(ValueError, match="cap"):
        acq.fetch_file(_spec(tmp_path, data, expected_bytes=None, sha256=None), tmp_path / "b", 100, allow_file_urls=True)
    with pytest.raises(ValueError, match="budget"):
        acq.fetch_file(_spec(tmp_path, data), tmp_path / "c", 100, allow_file_urls=True)
    with pytest.raises(ValueError, match="non-https"):
        acq.fetch_file(_spec(tmp_path, data), tmp_path / "d", 10 ** 6)
    for sub in ("a", "b", "c", "d"):
        assert not (tmp_path / sub / "product.bin").exists()


def test_dry_run_is_the_default(capsys):
    assert acq.main(["fetch", "--items", "D01", "--directory", "/nonexistent", "--max-bytes", "10"]) == 0
    assert "dry run" in capsys.readouterr().err
