"""R108 A8 (H05): VizieR metadata probe of the CF4 W1 Tully-Fisher release J/ApJ/902/145 (Kourkchi+2020).

Purpose
    Record which tables the CfA VizieR mirror serves for J/ApJ/902/145 and each table's fields (name, UCD,
    description), the metadata from which frame_w1tf_joint.py takes its table1 (PGC, HRV, QWflag) and
    table4 (Vls, Vcmb, f, DM-W1) columns. Replaces the earlier inline probe, which carried no identity block
    (review-2 C3). Metadata only: no estimate is made.

Inputs
    default (--replay-receipts): the VOTable saved by the R108 fetch of J/ApJ/902/145 and named by its line in
        ~/Downloads/htt_r108/frame/RECEIPTS.jsonl (SHA-256 verified; no network)
    --fetch: a new astroquery.vizier fetch (CfA mirror) with a new receipt line

Usage
    PYTHONPATH=.:htt:htt/src .venv/bin/python -m scripts.r108.frame_w1tf_probe \
        --output docs/research_program/observational_publication_20261015/R108_LOS_ATLAS_DATA_20261124/FRAME/W1TF_CATALOGUE_PROBE.json
    Deterministic in replay mode.
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

from scripts.r108.common import OUT_DIR, REPO, git_state, sha256_file, write_json
from scripts.r108.frame_registry_build import Receipts, ReceiptReplay, vizier_votable

HOME = Path.home()
CATALOG = "J/ApJ/902/145"
OUTFILE = OUT_DIR / "FRAME/W1TF_CATALOGUE_PROBE.json"
CODE = ("scripts/r108/frame_w1tf_probe.py", "scripts/r108/frame_registry_build.py", "scripts/r108/common.py")


def summarise(meta: dict) -> dict:
    """The probe record: tables with rows returned and (name, UCD, description) per field."""
    if not meta.get("ok"):
        return {"catalog": CATALOG, "ok": False, "errors": meta.get("errors"), "receipt": meta.get("receipt"),
                "tables": []}
    return {"catalog": CATALOG, "ok": True, "errors": None, "receipt": meta["receipt"],
            "tables": [{"name": t["name"], "description": t["description"], "rows_returned": t["rows"],
                        "fields": [[f["name"], f["ucd"], f["description"]] for f in t["fields"]]}
                       for t in meta["tables"]]}


def run(downloads: Path, output: Path, fetch: bool = False) -> dict:
    t0 = time.perf_counter()
    rc = Receipts(downloads)
    if fetch:
        meta = vizier_votable(rc, downloads, CATALOG)
        mode = "fetched (astroquery.vizier, CfA mirror)"
    else:
        meta = ReceiptReplay(rc.path).vizier(CATALOG)
        mode = "replayed from RECEIPTS.jsonl (saved bytes, SHA-256 verified; no network)"
    rec = summarise(meta)
    saved = Path(rec["receipt"]["saved"]) if rec.get("receipt") and rec["receipt"].get("saved") else None
    payload = {
        "schema": "htt.r108.frame.w1tf_catalogue_probe/1",
        "node": "H05 (W1 Tully-Fisher release metadata for frame_w1tf_joint.py)",
        "label": "NUMERICAL (metadata record of the release's tables and fields; no estimate)",
        "git": git_state(), "command": " ".join(sys.argv),
        "code_sha256": {c: sha256_file(REPO / c) for c in CODE},
        "mode": mode,
        "inputs": {"receipts": str(rc.path),
                   "votable": ({"path": str(saved), "sha256": sha256_file(saved)} if saved and saved.is_file() else None)},
        **rec,
        "runtime_s": time.perf_counter() - t0,
    }
    write_json(output, payload)
    return payload


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--downloads", type=Path, default=HOME / "Downloads/htt_r108/frame")
    ap.add_argument("--output", type=Path, default=OUTFILE)
    ap.add_argument("--fetch", action="store_true", help="fetch from VizieR instead of replaying the receipt")
    a = ap.parse_args(argv)
    p = run(a.downloads.expanduser(), a.output, fetch=a.fetch)
    print(json.dumps({"ok": p["ok"], "mode": p["mode"], "tables": [(t["name"], t["rows_returned"], len(t["fields"]))
                                                                    for t in p["tables"]],
                      "receipt_sha256": (p.get("receipt") or {}).get("sha256")}, indent=1))
    return 0 if p["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
