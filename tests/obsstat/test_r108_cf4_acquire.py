"""Fast offline tests for scripts/r108/cf4_acquire.py (VOTable row parsing, receipts, no-overwrite, https-only)."""
import argparse
import io
import json

import numpy as np
import pytest

from scripts.r108 import cf4_acquire as m


def _votable_bytes(n):
    from astropy.io.votable import from_table
    from astropy.table import Table
    t = Table(dict(a=np.arange(n), b=np.linspace(0, 1, n)))
    buf = io.BytesIO()
    from_table(t).to_xml(buf)
    return buf.getvalue()


def test_votable_rows_counts_and_flags():
    info = m.votable_rows(_votable_bytes(7))
    assert list(info["tables"].values()) == [7]
    assert info["stdb_error"] is False
    bad = _votable_bytes(0).replace(b"<RESOURCE", b"<!-- STDB_ERR --><RESOURCE", 1)
    assert m.votable_rows(bad)["stdb_error"] is True


def test_new_target_refuses_overwrite(tmp_path):
    t = m._new_target(tmp_path, "D99", "x.vot")
    t.write_bytes(b"raw")
    with pytest.raises(FileExistsError):
        m._new_target(tmp_path, "D99", "x.vot")
    with pytest.raises(ValueError):
        m._new_target(tmp_path, "D99", "../x.vot")


def test_https_refuses_plain_http_and_records_receipt(tmp_path):
    a = argparse.Namespace(item="D99", name="f.txt", url="http://example.invalid/f.txt", directory=tmp_path,
                           max_bytes=10, expected_bytes=None, sha256=None, timeout=1.)
    assert m.cmd_https(a) == 2
    rec = json.loads((tmp_path / "RECEIPTS.jsonl").read_text().splitlines()[-1])
    assert rec["status"] == "FAILED_EXCEPTION" and rec["bytes"] == 0 and "non-https" in rec["error"]
    assert not (tmp_path / "D99" / "f.txt").exists()
