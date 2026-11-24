"""R107 cloud gap register: every open node classified, DAG-consistent, and the committed JSON bound to the builder."""

from __future__ import annotations

import json
from pathlib import Path

from scripts.r107_cloud import gap_register as gr

ROOT = Path(__file__).resolve().parents[2]
COMMITTED = ROOT / "docs/research_program/observational_publication_20261015/R107_CLOUD_SOLVER_DATA_THEORY_20261124/GAP_REGISTER.json"


def test_register_covers_all_open_nodes_and_matches_the_dag():
    out = gr.build()
    assert out["n_nodes"] == 60 and out["n_open"] == 42
    ids = {r["id"] for r in out["rows"]}
    assert ids == set(gr.G)
    for r in out["rows"]:
        assert ("DEPENDENCY" in r["gap_types"]) == bool(r["open_hard_dependencies"]), r["id"]


def test_committed_register_equals_the_builder_output():
    assert json.loads(COMMITTED.read_text(encoding="utf-8")) == gr.build()
