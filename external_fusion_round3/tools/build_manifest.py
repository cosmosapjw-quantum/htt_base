#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EXCLUDE = {"MANIFEST.json"}


def digest(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()

rows = []
for p in sorted(ROOT.rglob("*")):
    if not p.is_file() or p.name in EXCLUDE:
        continue
    if p.suffix in {".pyc", ".pyo"} or "__pycache__" in p.parts or ".pytest_cache" in p.parts:
        continue
    rows.append({"path": p.relative_to(ROOT).as_posix(), "bytes": p.stat().st_size, "sha256": digest(p)})
manifest = {
    "schema": "htt.external_fusion_round3_manifest.v1",
    "bundle": ROOT.name,
    "file_count": len(rows),
    "total_bytes": sum(x["bytes"] for x in rows),
    "files": rows,
}
(ROOT / "MANIFEST.json").write_text(json.dumps(manifest, indent=2, sort_keys=True), encoding="utf-8")
print(json.dumps({"status": "WROTE", "files": len(rows), "path": "MANIFEST.json"}, indent=2))
