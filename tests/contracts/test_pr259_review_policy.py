from __future__ import annotations

import json
from pathlib import Path

from scripts.codex_harness import run_pr259_chronology


REPO_ROOT = Path(__file__).resolve().parents[2]
POLICY_PATH = (
    REPO_ROOT
    / "docs/research_program/stat_foundations/pr259_publication_policy.json"
)


def _policy_commands() -> dict[str, dict[str, object]]:
    payload = json.loads(POLICY_PATH.read_text(encoding="utf-8"))
    return {row["id"]: row for row in payload["required_commands"]}


def test_policy_routes_pytest_through_portable_source_layout_runner() -> None:
    commands = _policy_commands()
    runner = "scripts/codex_harness/run_pr259_chronology.py"

    assert commands["pr259-focused"]["argv"] == [
        "{python}",
        "-B",
        runner,
        "focused",
    ]
    assert commands["pr259-smoke"]["argv"] == [
        "{python}",
        "-B",
        runner,
        "smoke",
    ]


def test_runner_binds_current_worktree_source_roots_and_focused_tests() -> None:
    assert run_pr259_chronology.REPO == REPO_ROOT
    assert run_pr259_chronology.SOURCE_PATHS == (
        REPO_ROOT,
        REPO_ROOT / "htt/src",
        REPO_ROOT / "htt",
    )
    assert run_pr259_chronology.FOCUSED_TESTS == (
        "tests/contracts/test_pr124_cas_lineage.py",
        "tests/contracts/test_mes_successor_registry.py",
        "tests/contracts/test_pr259_review_policy.py",
    )
