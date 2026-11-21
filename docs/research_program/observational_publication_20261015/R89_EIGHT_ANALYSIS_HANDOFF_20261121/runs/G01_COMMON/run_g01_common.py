#!/usr/bin/env python3
"""R89 G01_COMMON group execution (create-only).

Verifies and binds the 7 foundational scoped-completed nodes (E0, E1, E2, E3,
X01, X02, X03) from immutable historical evidence without mutating R78/R86
states or upgrading physical claims.
"""
from __future__ import annotations

import hashlib
import json
import platform
import resource
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[6]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from htt.obsstat import p1_fast, phy_fast

OUT_DIR = Path(__file__).resolve().parent
OUT_JSON = OUT_DIR / "RESULT.json"

PROG = ROOT / "docs/research_program/observational_publication_20261015"
PUB_DAG = PROG / "PUBLICATION_DAG.json"
R78_DAG = PROG / "R78_UNIFIED_SCIENCE_DAG_20261119/INTEGRATED_DAG.json"
X01_JSON = PROG / "READY_20261016/X01_SOURCE_BINDINGS.json"
X02_MD = PROG / "X02_20261016/X02_NOVELTY_MATRIX.md"
X03_JSON = PROG / "READY_20261016/X03_CLAIM_SELECTION_LEDGER.json"


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def main() -> int:
    if OUT_JSON.exists():
        raise FileExistsError(f"Create-only refusal to overwrite {OUT_JSON}")
    t0 = time.perf_counter()

    anc_e01 = phy_fast.historical_common_anchors()
    anc_2130 = p1_fast.historical_evidence_21_30()
    assert anc_e01["R78_science_nodes_42_sha"] == anc_2130["original_42_nodes_sha256"]
    assert anc_e01["physical_claim_upgrade"] is False
    assert anc_2130["physical_claim_upgrade"] is False

    x01 = json.loads(X01_JSON.read_text(encoding="utf-8"))
    x03 = json.loads(X03_JSON.read_text(encoding="utf-8"))

    elapsed = time.perf_counter() - t0
    input_paths = (PUB_DAG, R78_DAG, X01_JSON, X02_MD, X03_JSON)
    out = {
        "schema": "htt.r89.g01_common_result/1",
        "group_id": "G01_COMMON",
        "node_ids": ["E0", "E1", "E2", "E3", "X01", "X02", "X03"],
        "source_sha256": {str(p.relative_to(ROOT)): _sha256(p) for p in input_paths},
        "runtime": {
            "python": platform.python_version(),
            "elapsed_seconds": float(elapsed),
            "maxrss_kib": int(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss),
        },
        "original_42_nodes_sha256": anc_e01["R78_science_nodes_42_sha"],
        "r78_next_action_id": anc_e01["R78_next_id"],
        "reused_evidence": {
            "E0_state": anc_e01["E0"]["state"],
            "E1_state": anc_e01["E1"]["state"],
            "E2_planck_same_sky_maps": anc_2130["E2_planck_same_sky_maps"],
            "E2_planck_selected_pixels": anc_2130["E2_planck_selected_pixels"],
            "E3_module_sha256": anc_2130["source_sha256"]["E3"],
            "X01_keys": sorted(x01.keys()),
            "X02_bytes": X02_MD.stat().st_size,
            "X03_prospective_new_null": x03["prospective_new_null"]["current_state"],
        },
        "node_verdicts": {
            "E0": "REUSED_SCOPED",
            "E1": "REUSED_SCOPED",
            "E2": "REUSED_SCOPED",
            "E3": "REUSED_SCOPED",
            "X01": "REUSED_SCOPED",
            "X02": "REUSED_SCOPED",
            "X03": "REUSED_SCOPED",
        },
        "physical_claim_upgrade": False,
    }
    OUT_JSON.write_text(json.dumps(out, indent=2, ensure_ascii=False, allow_nan=False) + "\n", encoding="utf-8")
    print(json.dumps({
        "group_id": "G01_COMMON",
        "elapsed_s": round(elapsed, 4),
        "nodes_reused": 7,
        "original_42_sha": anc_e01["R78_science_nodes_42_sha"][:16],
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
