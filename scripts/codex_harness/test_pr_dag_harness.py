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


def test_progress_report_rejects_completed_skipped_overlap(tmp_path: Path) -> None:
    backlog = tmp_path / "backlog.yaml"
    status = tmp_path / "status.yaml"
    _write_yaml(backlog, _backlog_with_policy(["PR-000", "PR-001", "PR-003", "PR-002"]))
    _write_yaml(status, {"completed": ["PR-000"], "skipped": ["PR-000"], "blocked": []})

    completed = _run(str(PROGRESS), str(backlog), str(status), "--json")

    assert completed.returncode != 0
    assert "both completed and skipped" in completed.stderr


def test_progress_report_tracks_skipped_without_counting_completion(
    tmp_path: Path,
) -> None:
    backlog = tmp_path / "backlog.yaml"
    status = tmp_path / "status.yaml"
    _write_yaml(backlog, _backlog_with_policy(["PR-000", "PR-001", "PR-003", "PR-002"]))
    _write_yaml(status, {"completed": ["PR-000"], "skipped": ["PR-001"], "blocked": []})

    completed = _run(str(PROGRESS), str(backlog), str(status), "--json")

    assert completed.returncode == 0, completed.stderr
    payload = json.loads(completed.stdout)
    assert payload["completed"] == 1
    assert payload["skipped"] == ["PR-001"]
    assert payload["skipped_count"] == 1
    assert "PR-001" not in payload["unblocked_next"]
    assert "PR-002" not in payload["unblocked_next"]


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


def test_progress_report_writes_scoreboard_when_checkpoint_not_due(
    tmp_path: Path,
) -> None:
    backlog = tmp_path / "backlog.yaml"
    status = tmp_path / "status.yaml"
    scoreboard = tmp_path / "progress_scoreboard.md"
    _write_yaml(backlog, _linear_backlog(5))
    _write_yaml(
        status,
        {
            "completed": [f"PR-{index:03d}" for index in range(4)],
            "skipped": ["PR-004"],
            "blocked": [],
        },
    )

    completed = _run(
        str(PROGRESS),
        str(backlog),
        str(status),
        "--checkpoint-every",
        "5",
        "--write-scoreboard",
        str(scoreboard),
    )

    assert completed.returncode == 0, completed.stderr
    rendered = scoreboard.read_text(encoding="utf-8")
    assert "Completed PRs: 4/5 = 80.0%" in rendered
    assert "Skipped PRs: PR-004" in rendered
    assert "Checkpoint due: no" in rendered
    assert "not scientific readiness evidence" in rendered


def _linear_backlog(count: int) -> dict:
    ids = [f"PR-{index:03d}" for index in range(count)]
    return {
        "policy": {"topological_order": ids},
        "prs": [
            {
                "id": pr_id,
                "wave": 0,
                "title": f"Step {index}",
                "owner": "COMMON",
                "depends": [] if index == 0 else [ids[index - 1]],
            }
            for index, pr_id in enumerate(ids)
        ],
    }


def test_progress_report_writes_checkpoint_artifact_when_due(tmp_path: Path) -> None:
    backlog = tmp_path / "backlog.yaml"
    status = tmp_path / "status.yaml"
    checkpoint_dir = tmp_path / "checkpoints"
    _write_yaml(backlog, _linear_backlog(5))
    _write_yaml(status, {"completed": [f"PR-{index:03d}" for index in range(5)], "blocked": []})

    completed = _run(
        str(PROGRESS),
        str(backlog),
        str(status),
        "--checkpoint-every",
        "5",
        "--write-checkpoint-dir",
        str(checkpoint_dir),
    )

    assert completed.returncode == 0, completed.stderr
    checkpoint = checkpoint_dir / "checkpoint_005.md"
    assert checkpoint.exists()
    rendered = checkpoint.read_text(encoding="utf-8")
    assert "Completed PRs: 5/5 = 100.0%" in rendered
    assert "Replan required: no" in rendered
    assert "not scientific readiness evidence" in rendered


def test_progress_report_checkpoint_detects_no_progress_since_previous_checkpoint(
    tmp_path: Path,
) -> None:
    backlog = tmp_path / "backlog.yaml"
    status = tmp_path / "status.yaml"
    checkpoint_dir = tmp_path / "checkpoints"
    checkpoint_dir.mkdir()
    _write_yaml(backlog, _linear_backlog(5))
    _write_yaml(status, {"completed": [f"PR-{index:03d}" for index in range(5)], "blocked": []})
    (checkpoint_dir / "checkpoint_004.md").write_text(
        '<!-- checkpoint_meta {"completed": 5, "percent_complete": 100.0} -->\n',
        encoding="utf-8",
    )

    completed = _run(
        str(PROGRESS),
        str(backlog),
        str(status),
        "--checkpoint-every",
        "5",
        "--write-checkpoint-dir",
        str(checkpoint_dir),
    )

    assert completed.returncode == 0, completed.stderr
    rendered = (checkpoint_dir / "checkpoint_005.md").read_text(encoding="utf-8")
    assert "Replan required: yes" in rendered
    assert "Adversarial replan entry" in rendered


def test_progress_report_does_not_write_checkpoint_when_not_due(tmp_path: Path) -> None:
    backlog = tmp_path / "backlog.yaml"
    status = tmp_path / "status.yaml"
    checkpoint_dir = tmp_path / "checkpoints"
    _write_yaml(backlog, _linear_backlog(5))
    _write_yaml(status, {"completed": [f"PR-{index:03d}" for index in range(4)], "blocked": []})

    completed = _run(
        str(PROGRESS),
        str(backlog),
        str(status),
        "--checkpoint-every",
        "5",
        "--write-checkpoint-dir",
        str(checkpoint_dir),
    )

    assert completed.returncode == 0, completed.stderr
    assert "Checkpoint due: False" in completed.stdout
    assert not checkpoint_dir.exists()


def test_progress_report_json_stays_valid_when_writing_checkpoint(tmp_path: Path) -> None:
    backlog = tmp_path / "backlog.yaml"
    status = tmp_path / "status.yaml"
    checkpoint_dir = tmp_path / "checkpoints"
    _write_yaml(backlog, _linear_backlog(5))
    _write_yaml(status, {"completed": [f"PR-{index:03d}" for index in range(5)], "blocked": []})

    completed = _run(
        str(PROGRESS),
        str(backlog),
        str(status),
        "--checkpoint-every",
        "5",
        "--write-checkpoint-dir",
        str(checkpoint_dir),
        "--json",
    )

    assert completed.returncode == 0, completed.stderr
    payload = json.loads(completed.stdout)
    assert payload["checkpoint_due"] is True
    assert payload["checkpoint_artifact"].endswith("checkpoint_005.md")
    assert payload["replan_required"] is False


def test_progress_report_json_marks_due_checkpoint_without_write_dir(
    tmp_path: Path,
) -> None:
    backlog = tmp_path / "backlog.yaml"
    status = tmp_path / "status.yaml"
    _write_yaml(backlog, _linear_backlog(5))
    _write_yaml(status, {"completed": [f"PR-{index:03d}" for index in range(5)], "blocked": []})

    completed = _run(
        str(PROGRESS),
        str(backlog),
        str(status),
        "--checkpoint-every",
        "5",
        "--json",
    )

    assert completed.returncode == 0, completed.stderr
    payload = json.loads(completed.stdout)
    assert payload["checkpoint_due"] is True
    assert payload["checkpoint_artifact"] is None
    assert "rerun with --write-checkpoint-dir" in payload["replan_reason"]


def test_progress_report_rejects_malformed_previous_checkpoint_metadata(
    tmp_path: Path,
) -> None:
    backlog = tmp_path / "backlog.yaml"
    status = tmp_path / "status.yaml"
    checkpoint_dir = tmp_path / "checkpoints"
    checkpoint_dir.mkdir()
    _write_yaml(backlog, _linear_backlog(5))
    _write_yaml(status, {"completed": [f"PR-{index:03d}" for index in range(5)], "blocked": []})
    (checkpoint_dir / "checkpoint_004.md").write_text(
        "<!-- checkpoint_meta not-json -->\n",
        encoding="utf-8",
    )

    completed = _run(
        str(PROGRESS),
        str(backlog),
        str(status),
        "--checkpoint-every",
        "5",
        "--write-checkpoint-dir",
        str(checkpoint_dir),
    )

    assert completed.returncode != 0
    assert "malformed checkpoint metadata" in completed.stderr
