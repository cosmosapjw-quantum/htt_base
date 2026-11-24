"""R108 FRAME lane provenance: pre-existing input receipts (RCPT-1), offline receipt replay, identity blocks (C3)."""
from __future__ import annotations

import hashlib
import io
import json
from pathlib import Path

import numpy as np
import pytest

from scripts.r108.frame_input_receipts import RECEIPTS, existing_pairs, lane_inputs, record_pre_existing
from scripts.r108.frame_registry_build import ReceiptReplay

REPO = Path(__file__).resolve().parents[2]
FRAME = REPO / "docs/research_program/observational_publication_20261015/R108_LOS_ATLAS_DATA_20261124/FRAME"
WRITERS = {"CATALOGUE_FRAME_REGISTRY.json": "scripts/r108/frame_registry_build.py",
           "CF4_BULK_HDIPOLE_JOINT.json": "scripts/r108/frame_cf4_joint.py",
           "LIE_FLUX_FRAMES.json": "scripts/r108/frame_lie_flux.py",
           "W1TF_BULK_HDIPOLE_JOINT.json": "scripts/r108/frame_w1tf_joint.py",
           "W1TF_CATALOGUE_PROBE.json": "scripts/r108/frame_w1tf_probe.py"}


def _sha(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def test_record_pre_existing_is_idempotent(tmp_path):
    f = tmp_path / "raw.dat"
    f.write_bytes(b"abc\n")
    rec = tmp_path / "RECEIPTS.jsonl"
    rec.write_text(json.dumps({"id": "remote", "sha256": "x", "status": 200}) + "\n")
    lines = record_pre_existing(rec, {str(f): {"kind": "pre_existing_input", "read_by": ["s.py"]}})
    assert len(lines) == 1 and lines[0]["appended_now"] and lines[0]["sha256"] == _sha(b"abc\n")
    assert lines[0]["bytes"] == 4 and lines[0]["fetched_at_utc"] is None
    again = record_pre_existing(rec, {str(f): {"kind": "pre_existing_input", "read_by": ["s.py"]}})
    assert not again[0]["appended_now"]
    assert len(rec.read_text().splitlines()) == 2
    f.write_bytes(b"changed\n")  # a new content is a new input and gets its own line
    record_pre_existing(rec, {str(f): {"kind": "pre_existing_input", "read_by": ["s.py"]}})
    assert existing_pairs(rec) == {(str(f), _sha(b"abc\n")), (str(f), _sha(b"changed\n"))}


def _votable_bytes(n_rows: int) -> bytes:
    from astropy.io.votable.tree import Field, Resource, VOTableFile
    try:
        from astropy.io.votable.tree import TableElement
    except ImportError:  # astropy < 6
        from astropy.io.votable.tree import Table as TableElement
    vot = VOTableFile()
    res = Resource(); vot.resources.append(res)
    t = TableElement(vot, ID="T_1_table1", name="T/1/table1"); res.tables.append(t)
    t.fields.extend([Field(vot, name="PGC", datatype="int"), Field(vot, name="HRV", datatype="double", unit="km/s")])
    t.create_arrays(n_rows)
    for i in range(n_rows):
        t.array[i] = (i + 1, 100.0 * (i + 1))
    buf = io.BytesIO(); vot.to_xml(buf)
    return buf.getvalue()


def test_receipt_replay_verifies_sha_and_replays_latest_success_or_recorded_failure(tmp_path):
    good = tmp_path / "a.vot"; good.write_bytes(_votable_bytes(3))
    q = "-source=T/1/table1\n-out.max=unlimited\n-out.all\n"
    rows = [
        {"id": "vizier_T_1_table1", "name": "astroquery.vizier T/1/table1", "status": 200, "query": q,
         "saved": str(good), "sha256": _sha(good.read_bytes())},
        {"id": "vizier_T_2", "name": "astroquery.vizier T/2", "status": "failed", "errors": ["attempt 1: boom"]},
        {"kind": "pre_existing_input", "name": "astroquery.vizier T/1/table1", "path": "x", "sha256": "y"},
    ]
    rec = tmp_path / "RECEIPTS.jsonl"
    rec.write_text("".join(json.dumps(r) + "\n" for r in rows))
    rp = ReceiptReplay(rec)
    out = rp.vizier("T/1/table1", row_limit=-1)
    assert out["ok"] and out["tables"][0]["rows"] == 3 and out["receipt"]["saved"] == str(good)
    fail = rp.vizier("T/2")
    assert not fail["ok"] and fail["errors"] == ["attempt 1: boom"]
    assert not rp.vizier("T/1/table1", row_limit=1)["ok"]  # a different query is not replayed from this receipt
    good.write_bytes(_votable_bytes(4))  # saved bytes no longer match the receipt
    with pytest.raises(ValueError, match="SHA-256 mismatch"):
        ReceiptReplay(rec).vizier("T/1/table1", row_limit=-1)


@pytest.mark.parametrize("name,writer", sorted(WRITERS.items()))
def test_frame_outputs_carry_identity(name, writer):
    """Review-2 C3: every FRAME result names git state, command and the writer script's SHA-256."""
    p = FRAME / name
    if not p.exists():
        pytest.skip(f"{name} not built")
    d = json.loads(p.read_text())
    assert d["git"]["head"] and isinstance(d["git"]["dirty_code_paths"], list)
    assert writer.split("/")[-1].replace(".py", "") in d["command"]
    assert d["code_sha256"][writer]
    assert d.get("label") or d.get("labels")


def test_every_frame_lane_input_has_a_receipt():
    """Review-2 RCPT-1: each pre-existing input the lane reads has a receipt line with its current SHA-256."""
    if not RECEIPTS.exists():
        pytest.skip("lane receipts not present on this machine")
    have = existing_pairs(RECEIPTS)
    from scripts.r108.common import sha256_file
    missing = []
    for path in lane_inputs():
        if not Path(path).exists():
            pytest.skip(f"raw input {path} not mounted")
        if (str(Path(path)), sha256_file(path)) not in have:
            missing.append(path)
    assert not missing, missing
    # every remote file saved by the lane has a fetch receipt with a matching SHA-256
    remote = [json.loads(ln) for ln in RECEIPTS.read_text().splitlines() if ln.strip()]
    for r in remote:
        if r.get("saved") and Path(r["saved"]).exists() and r.get("sha256") and not str(r.get("kind", "")).startswith("pre"):
            assert sha256_file(r["saved"]) == r["sha256"], r["saved"]
    assert np.all([("path" in r and "sha256" in r) for r in remote if str(r.get("kind", "")).startswith("pre")])
