"""Fast tests of the pre-existing-input receipt helper (scripts/r108/radio_input_receipts.py; used by the gaia lane too)."""
import json

import pytest

from scripts.r108 import radio_input_receipts as RI


def _entry(tmp_path, name, text):
    p = tmp_path / name
    p.write_text(text)
    return dict(id=f"PRE:{name}", name=name, path=str(p), bytes=p.stat().st_size, sha256=RI.sha256(p), status=RI.PRE)


def test_append_is_idempotent_and_fails_closed_on_changed_input(tmp_path):
    rec = tmp_path / "RECEIPTS.jsonl"
    rec.write_text(json.dumps({"id": "D11", "name": "strip.vot", "sha256": "ab"}) + "\n")
    e = _entry(tmp_path, "a.json", "{}")
    r1 = RI.append_receipts(rec, [e], "test")
    assert r1["appended"] == ["PRE:a.json"]
    r2 = RI.append_receipts(rec, [e], "test")
    assert r2["appended"] == [] and r2["skipped_already_present"] == ["PRE:a.json"]
    lines = [json.loads(x) for x in rec.read_text().splitlines()]
    assert len(lines) == 2 and lines[0]["id"] == "D11" and lines[1]["recorded_by"] == "test"
    changed = dict(e, sha256="0" * 64)
    with pytest.raises(ValueError):
        RI.append_receipts(rec, [changed], "test")


def test_dry_run_writes_nothing(tmp_path):
    rec = tmp_path / "RECEIPTS.jsonl"
    rec.write_text("")
    RI.append_receipts(rec, [_entry(tmp_path, "b.json", "[]")], "test", dry_run=True)
    assert rec.read_text() == ""
