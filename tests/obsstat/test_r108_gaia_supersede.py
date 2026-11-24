"""Fast tests of scripts/r108/gaia_supersede.py (temporary files only)."""
import json

import pytest

from scripts.r108 import gaia_supersede as S
from scripts.r108.common import sha256_file


def test_supersede_moves_byte_identically_and_writes_pointer(tmp_path):
    old = tmp_path / "CAL_V1.json"
    new = tmp_path / "CAL.json"
    old.write_text(json.dumps({"schema": "calibration/1", "a": 0.757}))
    new.write_text(json.dumps({"schema": "calibration/2", "a": 1.635}))
    log = tmp_path / "x.log"
    log.write_text("log\n")
    sha_old = sha256_file(old)
    rec, pointer = S.supersede(old, new, "estimator biased", moved_name="CAL_V1_moved.json", evidence=[log])
    moved = tmp_path / "superseded" / "CAL_V1_moved.json"
    assert not old.exists() and moved.exists() and sha256_file(moved) == sha_old
    assert sorted(p.name for p in tmp_path.glob("*.json")) == ["CAL.json"]
    p = json.loads(pointer.read_text())
    assert p["status"] == "SUPERSEDED" and p["superseded_by_sha256"] == sha256_file(new)
    assert p["superseded_schema"] == "calibration/1" and p["evidence"][0]["sha256"] == sha256_file(log)
    old.write_text("{}")
    with pytest.raises(FileExistsError):
        S.supersede(old, new, "again", moved_name="CAL_V1_moved.json")
