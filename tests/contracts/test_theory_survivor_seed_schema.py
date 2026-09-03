from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def test_registered_survivor_seed_rows_have_exact_schema_and_kind_counts() -> None:
    path = (
        ROOT
        / "docs"
        / "research_program"
        / "theory_promotion"
        / "closeout"
        / "REGISTERED_SURVIVOR_SEED.json"
    )
    seed = json.loads(path.read_text(encoding="utf-8"))
    broad_schema = {
        "candidate_id",
        "source_kind",
        "survivor_class",
        "triage_disposition",
    }
    scoped_schema = broad_schema | {"parent_candidate_id"}
    counts = {"BROAD_ROW": 0, "SCOPED_CHILD": 0}

    for row in seed["rows"]:
        assert set(row) in (broad_schema, scoped_schema)
        kind = row["source_kind"]
        assert kind in counts
        counts[kind] += 1
        if kind == "BROAD_ROW":
            assert "parent_candidate_id" not in row
        else:
            assert row["parent_candidate_id"]

    assert counts == {"BROAD_ROW": 32, "SCOPED_CHILD": 5}
