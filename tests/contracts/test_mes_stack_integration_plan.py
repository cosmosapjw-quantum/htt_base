from __future__ import annotations
import json
from pathlib import Path
import subprocess
import sys
import yaml

ROOT = Path(__file__).resolve().parents[2]
PKG = ROOT / "docs/codex_handoff/mes_stack_integration"

def test_mes_stack_integration_validator_passes() -> None:
    result = subprocess.run(
        [sys.executable, "scripts/validate_mes_stack_integration_plan.py"],
        cwd=ROOT, check=True, capture_output=True, text=True,
    )
    payload = json.loads(result.stdout)
    assert payload["status"] == "PASS"
    assert payload["merge_parents"] == [
        "4733a4c6dbc638372dee7f99ac38f39dba56d933",
        "5a3825f903546891fd90e3d708481707d59babf4",
    ]
    assert payload["work_units"] == [f"MSI-WU-{i:03d}" for i in range(9)]
    assert payload["canonical_DAG_changed"] is False
    assert payload["science_code_changed"] is False

def test_pr_disposition_ledger_blocks_bulk_merge() -> None:
    ledger = yaml.safe_load((PKG / "PR_DISPOSITION_LEDGER.yaml").read_text())
    by_pr = {row["github_pr"]: row for row in ledger["dispositions"]}
    assert by_pr[403]["action"] == "PRESERVE; DO_NOT_BULK_MERGE"
    assert by_pr[404]["action"] == "USE_AS_IMPLEMENTATION_CONTRACT; DO_NOT_BULK_MERGE"
    assert "DO_NOT_MERGE" in by_pr[387]["action"]
    assert "DO_NOT_MERGE" in by_pr[388]["action"]
    assert by_pr[411]["state"] == "MERGE_PARENT_EXACT_PACKAGE_IMPORTED"

def test_handoff_preserves_core_methodology_and_boundaries() -> None:
    text = (PKG / "CODEX_HANDOFF.md").read_text().lower()
    for required in (
        "generic planck 12-feature result is a benchmark control",
        "pr-321 hsc sacc is not a directional low-z lane",
        "do not bulk merge",
        "planck alone cannot identify local boost versus global tilt",
        "another_planning_successor: forbidden",
    ):
        assert required in text

def test_source_import_manifest_covers_pr411_pr404_pr403() -> None:
    manifest = yaml.safe_load((PKG / "SOURCE_IMPORT_MANIFEST.yaml").read_text())
    sources = {row["source"] for row in manifest["imports"]}
    assert sources == {"PR411", "PR404", "PR403"}
    assert len(manifest["imports"]) == 21
