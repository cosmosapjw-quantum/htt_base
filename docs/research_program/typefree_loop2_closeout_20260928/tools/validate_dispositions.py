#!/usr/bin/env python3
import json
from pathlib import Path


HERE = Path(__file__).resolve().parents[1]
payload = json.loads((HERE / "PR_DISPOSITION.json").read_text(encoding="utf-8"))
rows = payload["pull_requests"]
numbers = [row["number"] for row in rows]
allowed = {"MERGED", "ALREADY_INTEGRATED_CLOSED", "SUPERSEDED_CLOSED", "OPEN_HOLD", "OUT_OF_SCOPE"}
assert len(rows) == 57 and len(set(numbers)) == 57
assert set(row["disposition"] for row in rows) <= allowed
assert payload["canonical_dag_cards"] == 211
assert all(row["reason"] and len(row["audited_head"]) == 40 and len(row["current_head"]) == 40 for row in rows)
print("PASS: 57 unique PR dispositions; canonical DAG=211")
