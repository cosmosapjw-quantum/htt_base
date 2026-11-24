"""R108 gaia lane: move a superseded result JSON into a 'superseded/' subfolder and write a pointer sidecar (GAIA-4 review).

Purpose
    A superseded output is kept only if it is marked superseded. The file itself is not edited (result JSONs are written by
    their scripts only); it is moved byte-identically to <results-dir>/superseded/<new name> and a sidecar
    <new name without .json>.POINTER.json records: original path, SHA-256 (checked unchanged by the move), the superseding
    file and its SHA-256, the reason, and evidence pointers (logs). Globbing <results-dir>/*.json no longer returns it.
Inputs: --old (the superseded JSON), --new (the superseding JSON), --reason, optional --evidence paths.
Units: none.
Usage (repo root):
    python3 -m scripts.r108.gaia_supersede --old GAIA/SCAN_NULL_CALIBRATION_V1_SUPERSEDED.json --new GAIA/SCAN_NULL_CALIBRATION.json \
        --moved-name SCAN_NULL_CALIBRATION_V1.json --reason "..." [--evidence LOG ...]
No randomness.
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import shutil
import sys
from pathlib import Path

from scripts.r108.common import sha256_file


def supersede(old, new, reason, moved_name=None, evidence=(), recorded_by="scripts/r108/gaia_supersede.py"):
    old, new = Path(old), Path(new)
    if not old.is_file() or not new.is_file():
        raise FileNotFoundError(f"missing {old if not old.is_file() else new}")
    dest_dir = old.parent / "superseded"
    dest_dir.mkdir(exist_ok=True)
    dest = dest_dir / (moved_name or old.name)
    pointer = dest.with_name(dest.stem + ".POINTER.json")
    if dest.exists() or pointer.exists():
        raise FileExistsError(f"refusing to overwrite {dest} / {pointer}")
    sha_old = sha256_file(old)
    try:
        schema = json.loads(old.read_text()).get("schema")
    except (json.JSONDecodeError, AttributeError):
        schema = None
    shutil.move(str(old), str(dest))
    if sha256_file(dest) != sha_old:
        raise RuntimeError("superseded file changed during the move")
    rec = {"schema": "htt.r108.superseded_pointer/1", "status": "SUPERSEDED", "superseded_file": str(dest),
           "superseded_sha256": sha_old, "superseded_schema": schema, "original_path": str(old),
           "superseded_by": str(new), "superseded_by_sha256": sha256_file(new),
           "superseded_by_schema": json.loads(new.read_text()).get("schema"), "reason": reason,
           "evidence": [{"path": str(Path(e).expanduser()), "sha256": sha256_file(Path(e).expanduser())} for e in evidence],
           "recorded_at_utc": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
           "recorded_by": f"{recorded_by} (sha256 {sha256_file(Path(__file__))})",
           "use": "do not read amplitudes from the superseded file; use superseded_by"}
    pointer.write_text(json.dumps(rec, indent=1) + "\n")
    return rec, pointer


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--old", type=Path, required=True)
    ap.add_argument("--new", type=Path, required=True)
    ap.add_argument("--reason", required=True)
    ap.add_argument("--moved-name", default=None)
    ap.add_argument("--evidence", nargs="*", default=())
    a = ap.parse_args(argv)
    rec, pointer = supersede(a.old, a.new, a.reason, a.moved_name, a.evidence)
    print(json.dumps({"pointer": str(pointer), **{k: rec[k] for k in ("superseded_file", "superseded_sha256", "superseded_by_sha256")}}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
