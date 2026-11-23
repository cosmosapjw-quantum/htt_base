"""Tests for R100 Part F (strict 60-node overlay inheritance, unchanged R78/R99/42 gates, fail-closed CLI)."""
from __future__ import annotations

import copy
import json
import pytest

from scripts.r99 import program_preparation as r99_prep
from scripts.r100 import program_preparation as r100_prep


def test_r100_overlay_preserves_60_nodes_129_edges_and_immutable_42():
    """R100 preparation must inherit frozen R99/R78 pins verbatim without relaxing any blocker or gate."""
    data = r100_prep.build()
    assert data["next_id"] == "SQ-CF4"
    assert data["counts"]["nodes"] == 60
    assert data["counts"]["edges"] == 129
    assert data["counts"]["new_science_nodes_promoted"] == 0
    assert data["counts"]["original_scoped_completed"] == 18
    assert data["inherited_overlay_sha256"] == r100_prep.R99_OVERLAY_SHA256
    assert data["original_42_payload_sha256"] == r100_prep.ORIGINAL_42_SHA256

    dag = r99_prep.read(r100_prep.R78_DIR / "INTEGRATED_DAG.json")
    original = r99_prep.read(r100_prep.BASE / "PUBLICATION_DAG.json")["nodes"]
    closure = r99_prep.verify_contract(dag, data, original)
    assert len(closure) == 60
    sq_cf4 = next(n for n in data["nodes"] if n["id"] == "SQ-CF4")
    assert sq_cf4["science_status"] == "SCIENCE_BLOCKED"
    assert "D01" in sq_cf4["direct_blockers"]

    altered = copy.deepcopy(dag)
    altered["nodes"][0]["acceptance"] += " relaxed"
    with pytest.raises(ValueError, match="original 42"):
        r99_prep.verify_contract(altered, data, original)


def test_r100_program_preparation_cli_fail_closed(tmp_path, monkeypatch):
    """CLI --check detects saved overlay drift and science --node SQ-CF4 fails closed with exit code 3."""
    sample = {
        "nodes": [
            {
                "id": "E0",
                "science_status": "INHERITED_COMPLETED_SCOPED",
                "r100_lane_tags": ["SOURCE_QUALIFIED"],
                "direct_blockers": [],
                "all_blockers_including_dependencies": [],
            },
            {
                "id": "SQ-CF4",
                "science_status": "SCIENCE_BLOCKED",
                "r100_lane_tags": ["BLOCKED_DATA", "MODEL_CONDITIONAL"],
                "direct_blockers": ["D01", "D02", "M01", "A01"],
                "all_blockers_including_dependencies": ["D01", "D02", "M01", "A01"],
            },
        ],
        "blockers": {"D01": {"category": "DATA", "current_defect": "c", "cycle_delta": "d"}},
        "counts": {"new_science_nodes_promoted": 0},
        "next_id": "SQ-CF4",
    }
    monkeypatch.setattr(r100_prep, "build", lambda: sample)
    monkeypatch.setattr(r100_prep, "OUT", tmp_path)
    assert r100_prep.main(["prepare"]) == 0
    assert r100_prep.main(["--check"]) == 0
    assert r100_prep.main(["science", "--node", "E0"]) == 0
    assert r100_prep.main(["science", "--node", "SQ-CF4"]) == 3
    (tmp_path / r100_prep.FILE).write_text("{}")
    with pytest.raises(ValueError, match="diverges"):
        r100_prep.main(["--check"])
