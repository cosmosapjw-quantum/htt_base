from __future__ import annotations

import copy
import json
from pathlib import Path
import subprocess
import sys

import yaml


ROOT = Path(__file__).resolve().parents[2]
BACKLOG = ROOT / "docs/codex_handoff/pr_backlog.yaml"
STATUS = ROOT / "docs/codex_handoff/pr_status.yaml"
PREFIX_RECEIPT = (
    ROOT / "docs/generated/mes_stack_implementation/dag_prefix_receipt.json"
)

EXPECTED_IDS = [f"PR-{number}" for number in range(322, 331)]
EXPECTED_ALIASES = [f"MSI-WU-{number:03d}" for number in range(9)]
EXPECTED_DEPENDENCIES = {
    "PR-322": [],
    "PR-323": ["PR-322"],
    "PR-324": ["PR-322"],
    "PR-325": ["PR-323", "PR-324"],
    "PR-326": ["PR-323", "PR-325"],
    "PR-327": ["PR-324", "PR-325", "PR-326"],
    "PR-328": ["PR-323", "PR-326"],
    "PR-329": ["PR-327", "PR-328"],
    "PR-330": ["PR-327", "PR-328"],
}


def _yaml(path: Path) -> dict[str, object]:
    payload = yaml.safe_load(path.read_text(encoding="utf-8"))
    assert isinstance(payload, dict)
    return payload


def _run(backlog: Path, status: Path = STATUS) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [
            sys.executable,
            "scripts/codex_harness/validate_pr_dag.py",
            str(backlog),
            "--status",
            str(status),
            "--strict-rescue-slice",
        ],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )


def test_mes_work_units_are_one_atomic_append_only_slice() -> None:
    backlog = _yaml(BACKLOG)
    cards = backlog["prs"]
    assert isinstance(cards, list)
    mes_cards = cards[-len(EXPECTED_IDS) :]

    assert [card["id"] for card in mes_cards] == EXPECTED_IDS
    assert [card["planning_alias"] for card in mes_cards] == EXPECTED_ALIASES
    assert {card["id"]: card["depends"] for card in mes_cards} == (
        EXPECTED_DEPENDENCIES
    )
    assert all(card["execution_authorization"] == "EXPLICIT_USER_AUTHORIZED" for card in mes_cards)
    assert all(card["claim_tier_ceiling"] == "diagnostic_only" for card in mes_cards)
    assert all(card["public_use"] is False for card in mes_cards)


def test_prefix_receipt_and_strict_validator_are_current() -> None:
    receipt = json.loads(PREFIX_RECEIPT.read_text(encoding="utf-8"))
    assert receipt["prefix_count"] == 264
    assert receipt["prefix_first_id"] == "PR-000"
    assert receipt["prefix_last_id"] == "PR-321"
    result = _run(BACKLOG)
    assert result.returncode == 0, result.stdout + result.stderr
    assert "OK: 273 PRs, DAG valid" in result.stdout


def test_old_prefix_mutation_is_rejected(tmp_path: Path) -> None:
    payload = copy.deepcopy(_yaml(BACKLOG))
    payload["prs"][263]["title"] = "mutated historical title"
    mutated = tmp_path / "mutated-backlog.yaml"
    mutated.write_text(
        yaml.safe_dump(payload, sort_keys=False, allow_unicode=True),
        encoding="utf-8",
    )

    result = _run(mutated)
    assert result.returncode == 1
    assert "MES implementation DAG prefix" in result.stderr
