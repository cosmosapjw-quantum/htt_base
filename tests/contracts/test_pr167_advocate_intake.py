"""PR-167 receipt, parallel status, and typed-lane contract tests."""

from __future__ import annotations

import copy
import json
import subprocess
import sys
from pathlib import Path

import pytest
import yaml

from scripts.codex_harness import intake_advocate_track, pr167_intake_contract


REPO = Path(__file__).resolve().parents[2]
BACKLOG = REPO / "docs/codex_handoff/pr_backlog.yaml"
STATUS = REPO / "docs/codex_handoff/pr_status.yaml"
RECEIPT = REPO / "docs/generated/pr167_pre_intake_semantic_receipt.json"
INTAKE = REPO / "scripts/codex_harness/intake_advocate_track.py"
PROGRESS = REPO / "scripts/codex_harness/progress_report.py"


def _yaml(path: Path) -> dict:
    payload = yaml.safe_load(path.read_text(encoding="utf-8"))
    assert isinstance(payload, dict)
    return payload


def _run(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, *args],
        cwd=REPO,
        text=True,
        capture_output=True,
        check=False,
    )


def _write_yaml(path: Path, payload: dict) -> None:
    path.write_text(yaml.safe_dump(payload, sort_keys=False), encoding="utf-8")


def _post_pr167_snapshot(tmp_path: Path) -> tuple[Path, Path]:
    spec = intake_advocate_track._load_mapping(intake_advocate_track.SPEC)
    cards = intake_advocate_track.parse_advocate_cards(
        intake_advocate_track.ROADMAP.read_text(encoding="utf-8"),
        spec,
    )
    baseline_backlog = yaml.safe_load(
        intake_advocate_track._baseline_file_text(
            str(spec["baseline_commit"]),
            intake_advocate_track.BACKLOG_YAML,
        )
    )
    baseline_status = yaml.safe_load(
        intake_advocate_track._baseline_file_text(
            str(spec["baseline_commit"]),
            intake_advocate_track.STATUS_YAML,
        )
    )
    backlog = intake_advocate_track.materialize_backlog(
        baseline_backlog,
        cards,
        spec,
    )
    status = intake_advocate_track.materialize_status(baseline_status, cards)
    status["in_progress"] = None
    status["completed"].append("PR-167")
    status["execution_resolutions"]["PR-167"] = {
        "resolution": "COMPLETED_SUCCESS",
        "receipt": "docs/PR_DELTAS/pr-167.md",
        "resolved_on": "2026-07-19",
        "scientific_status_effect": "none",
        "scientific_status_after": "OPEN",
    }
    backlog_path = tmp_path / "backlog.yaml"
    status_path = tmp_path / "status.yaml"
    _write_yaml(backlog_path, backlog)
    _write_yaml(status_path, status)
    return backlog_path, status_path


def test_dedicated_intake_check_and_mirrors_are_exact() -> None:
    completed = _run(str(INTAKE), "--check")
    assert completed.returncode == 0, completed.stderr
    assert "PR-167..PR-183" in completed.stdout
    assert BACKLOG.read_bytes() == (REPO / "machine_readable/pr_backlog.yaml").read_bytes()
    assert STATUS.read_bytes() == (REPO / "machine_readable/pr_status.yaml").read_bytes()


def test_receipt_preserves_all_113_old_card_semantics_and_only_pr151_migrates() -> None:
    backlog = _yaml(BACKLOG)
    status = _yaml(STATUS)
    receipt = json.loads(RECEIPT.read_text(encoding="utf-8"))
    pr167_intake_contract.validate_pre_intake_receipt(
        receipt,
        backlog=backlog,
        status=status,
        expected_baseline_commit="fe7abb6aa01fdfaf0440956bd8727ddc9e1be8e7",
        expected_backlog_sha256="9693706872a5e13514c0eb3e4ca9dab9a281359edac4cda9877d26dae8c68f07",
        expected_status_sha256="fcd81fc2d904ff8ed360f1055688bb122b4006ea1ca0e570c0b39cf6486f8759",
    )
    assert receipt["preserved_card_count"] == 113
    assert len(receipt["card_semantic_sha256"]) == 113
    assert receipt["pre_intake_status_projection"]["PR-151"] == "in_progress"
    assert status["background_in_progress"] == ["PR-151"]


def test_receipt_rejects_old_card_semantic_mutation() -> None:
    backlog = _yaml(BACKLOG)
    receipt = json.loads(RECEIPT.read_text(encoding="utf-8"))
    mutated = copy.deepcopy(backlog)
    mutated["prs"][0]["title"] += " mutated"
    with pytest.raises(ValueError, match="semantic hash drift"):
        pr167_intake_contract.validate_pre_intake_receipt(
            receipt, backlog=mutated
        )


def test_intake_check_rejects_missing_receipt(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(intake_advocate_track, "RECEIPT", tmp_path / "missing.json")
    spec = intake_advocate_track._load_mapping(intake_advocate_track.SPEC)
    cards = intake_advocate_track.parse_advocate_cards(
        intake_advocate_track.ROADMAP.read_text(encoding="utf-8"), spec
    )
    with pytest.raises(ValueError, match="receipt is missing"):
        intake_advocate_track.check_materialized(spec, cards)


@pytest.mark.parametrize(
    ("mutator", "message"),
    [
        (
            lambda value: value["background_in_progress"].append("PR-167"),
            "overlap",
        ),
        (
            lambda value: value["execution_lane"].__setitem__(
                "PR-171", "hypothesis_only"
            ),
            "execution_lane",
        ),
        (
            lambda value: (
                value["dormant_external"].remove("PR-183"),
                value["pending"].append("PR-183"),
            ),
            "activation_state",
        ),
    ],
)
def test_progress_status_schema_fails_closed(
    tmp_path: Path, mutator, message: str
) -> None:
    status = _yaml(STATUS)
    mutator(status)
    path = tmp_path / "status.yaml"
    _write_yaml(path, status)
    completed = _run(str(PROGRESS), str(BACKLOG), str(path), "--json")
    assert completed.returncode != 0
    assert message in completed.stderr


def test_hypothesis_only_cards_are_reported_but_not_auto_scheduled(
    tmp_path: Path,
) -> None:
    backlog_path, status_path = _post_pr167_snapshot(tmp_path)
    completed = _run(
        str(PROGRESS),
        str(backlog_path),
        str(status_path),
        "--json",
    )
    assert completed.returncode == 0, completed.stderr
    report = json.loads(completed.stdout)
    assert report["unblocked_next"][:5] == [
        "PR-168",
        "PR-169",
        "PR-170",
        "PR-171",
        "PR-172",
    ]
    assert report["hypothesis_only_unblocked"] == [
        "PR-174",
        "PR-182",
    ]
    assert not set(report["hypothesis_only_unblocked"]) & set(
        report["unblocked_next"]
    )
    assert "PR-183" in report["dormant_external"]


def _move_foreground(status: dict, pr_id: str) -> None:
    previous = status["in_progress"]
    status["in_progress"] = pr_id
    status["pending"].remove(pr_id)
    if previous is not None:
        status["pending"].append(previous)


def test_hypothesis_only_card_cannot_be_moved_to_foreground(tmp_path: Path) -> None:
    backlog_path, status_path = _post_pr167_snapshot(tmp_path)
    status = _yaml(status_path)
    _move_foreground(status, "PR-174")
    _write_yaml(status_path, status)
    completed = _run(
        str(PROGRESS),
        str(backlog_path),
        str(status_path),
        "--json",
    )
    assert completed.returncode != 0
    assert "defensible and execution-authorized" in completed.stderr


def test_hypothesis_only_or_nonacquisition_card_cannot_run_in_background(
    tmp_path: Path,
) -> None:
    backlog_path, status_path = _post_pr167_snapshot(tmp_path)
    baseline_status = _yaml(status_path)
    for pr_id in ("PR-174", "PR-172"):
        status = copy.deepcopy(baseline_status)
        if status["in_progress"] == pr_id:
            status["in_progress"] = None
        status["background_in_progress"] = [pr_id]
        status["background_execution_contracts"] = {
            pr_id: {
                "kind": "acquisition",
                "allowed_phase": "acquire",
                "partial_scientific_use": "forbidden",
            }
        }
        if pr_id in status["pending"]:
            status["pending"].remove(pr_id)
        if pr_id in status["blocked"]:
            status["blocked"].remove(pr_id)
        status["execution_resolutions"].pop(pr_id, None)
        status["pending"].append("PR-151")
        path = tmp_path / f"{pr_id}.yaml"
        _write_yaml(path, status)
        completed = _run(
            str(PROGRESS),
            str(backlog_path),
            str(path),
            "--json",
        )
        assert completed.returncode != 0
        assert (
            "defensible and execution-authorized" in completed.stderr
            or "lacks PR-167 acquisition authorization" in completed.stderr
        )


def test_dependency_blocked_card_cannot_be_moved_to_foreground(
    tmp_path: Path,
) -> None:
    status = _yaml(STATUS)
    _move_foreground(status, "PR-155")
    path = tmp_path / "status.yaml"
    _write_yaml(path, status)
    completed = _run(str(PROGRESS), str(BACKLOG), str(path), "--json")
    assert completed.returncode != 0
    assert "incomplete dependency contracts" in completed.stderr
