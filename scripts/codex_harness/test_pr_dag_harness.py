from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import yaml


REPO_ROOT = Path(__file__).resolve().parents[2]
VALIDATOR = REPO_ROOT / "scripts" / "codex_harness" / "validate_pr_dag.py"
PROGRESS = REPO_ROOT / "scripts" / "codex_harness" / "progress_report.py"


def _write_yaml(path: Path, payload: dict) -> None:
    path.write_text(yaml.safe_dump(payload, sort_keys=False), encoding="utf-8")


def _run(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, *args],
        cwd=REPO_ROOT,
        text=True,
        capture_output=True,
        check=False,
    )


def _backlog_with_policy(order: list[str]) -> dict:
    return {
        "policy": {"topological_order": order},
        "prs": [
            {
                "id": "PR-000",
                "wave": 0,
                "title": "Root",
                "owner": "COMMON",
                "depends": [],
            },
            {
                "id": "PR-001",
                "wave": 0,
                "title": "Packaging",
                "owner": "COMMON",
                "depends": ["PR-000"],
            },
            {
                "id": "PR-002",
                "wave": 0,
                "title": "Taxonomy",
                "owner": "COMMON",
                "depends": ["PR-001"],
            },
            {
                "id": "PR-003",
                "wave": 0,
                "title": "DAG harness",
                "owner": "COMMON",
                "depends": ["PR-000"],
            },
        ],
    }


def test_validate_rejects_policy_order_that_violates_dependency(tmp_path: Path) -> None:
    backlog = tmp_path / "backlog.yaml"
    _write_yaml(backlog, _backlog_with_policy(["PR-003", "PR-001", "PR-000", "PR-002"]))

    completed = _run(str(VALIDATOR), str(backlog))

    assert completed.returncode != 0
    assert "policy.topological_order" in completed.stderr


def test_validate_rejects_non_mapping_policy(tmp_path: Path) -> None:
    backlog = tmp_path / "backlog.yaml"
    payload = _backlog_with_policy(["PR-000", "PR-001", "PR-003", "PR-002"])
    payload["policy"] = []
    _write_yaml(backlog, payload)

    completed = _run(str(VALIDATOR), str(backlog))

    assert completed.returncode != 0
    assert "policy must be a mapping" in completed.stderr


def test_validate_can_write_mermaid_graph_from_backlog(tmp_path: Path) -> None:
    backlog = tmp_path / "backlog.yaml"
    graph = tmp_path / "pr_dag.mmd"
    _write_yaml(backlog, _backlog_with_policy(["PR-000", "PR-001", "PR-003", "PR-002"]))

    completed = _run(str(VALIDATOR), str(backlog), "--write-mermaid", str(graph))

    assert completed.returncode == 0, completed.stderr
    rendered = graph.read_text(encoding="utf-8")
    assert rendered.startswith("flowchart TD\n")
    assert 'PR_000["PR-000<br/>Root"]' in rendered
    assert "PR_000 --> PR_003" in rendered


def test_progress_report_orders_unblocked_by_policy_and_reports_weighted_metrics(
    tmp_path: Path,
) -> None:
    backlog = tmp_path / "backlog.yaml"
    status = tmp_path / "status.yaml"
    _write_yaml(backlog, _backlog_with_policy(["PR-000", "PR-001", "PR-003", "PR-002"]))
    _write_yaml(status, {"completed": ["PR-000", "PR-001"], "blocked": []})

    completed = _run(str(PROGRESS), str(backlog), str(status), "--json")

    assert completed.returncode == 0, completed.stderr
    payload = json.loads(completed.stdout)
    assert payload["unblocked_next"] == ["PR-003", "PR-002"]
    assert payload["critical_path_percent_complete"] == 66.67
    assert "dependency_weighted_percent_complete" in payload
    assert payload["critical_path"] == ["PR-000", "PR-001", "PR-002"]


def test_progress_report_rejects_unknown_status_ids(tmp_path: Path) -> None:
    backlog = tmp_path / "backlog.yaml"
    status = tmp_path / "status.yaml"
    _write_yaml(backlog, _backlog_with_policy(["PR-000", "PR-001", "PR-003", "PR-002"]))
    _write_yaml(status, {"completed": ["PR-999"], "blocked": []})

    completed = _run(str(PROGRESS), str(backlog), str(status), "--json")

    assert completed.returncode != 0
    assert "unknown completed PR ids" in completed.stderr


def test_progress_report_handles_empty_backlog(tmp_path: Path) -> None:
    backlog = tmp_path / "backlog.yaml"
    status = tmp_path / "status.yaml"
    _write_yaml(backlog, {"prs": []})
    _write_yaml(status, {"completed": [], "blocked": []})

    completed = _run(str(PROGRESS), str(backlog), str(status), "--json")

    assert completed.returncode == 0, completed.stderr
    payload = json.loads(completed.stdout)
    assert payload["total"] == 0
    assert payload["percent_complete"] == 0.0
    assert payload["critical_path"] == []
    assert payload["critical_path_percent_complete"] == 0.0
