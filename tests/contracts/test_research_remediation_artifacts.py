from __future__ import annotations

import importlib.util
import json
from collections import Counter
from pathlib import Path

import pytest
import yaml


REPO = Path(__file__).resolve().parents[2]
SCRIPT = REPO / "scripts/codex_harness/validate_research_remediation.py"
SPEC = importlib.util.spec_from_file_location("validate_research_remediation", SCRIPT)
assert SPEC is not None and SPEC.loader is not None
remediation = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(remediation)


def _yaml(path: Path) -> dict[str, object]:
    payload = yaml.safe_load(path.read_text(encoding="utf-8"))
    assert isinstance(payload, dict)
    return payload


def test_generated_active_finding_root_is_exactly_102_open_zero_rescued() -> None:
    state = _yaml(remediation.STATE)

    assert state == remediation.build_state()
    assert state["census"] == {
        "finding_count": 102,
        "known_open_and_audit_gap_count": 69,
        "new_open_count": 33,
        "scientific_status_counts": {"OPEN": 102},
        "rescued_count": 0,
    }
    findings = state["findings"]
    assert len(findings) == 102
    assert {row["scientific_status"] for row in findings} == {"OPEN"}
    assert {row["execution_resolution"] for row in findings} == {None}
    assert all(row["response_disposition_is_scientific_status"] is False for row in findings)
    assert all(row["remediation_pr_ids"] for row in findings)
    assert Counter(row["response_disposition"] for row in findings) == {
        "rebuild_required": 56,
        "downclaimed": 43,
        "abandoned": 3,
    }


def test_authority_roots_are_hash_bound_and_history_is_not_rewritten() -> None:
    state = _yaml(remediation.STATE)
    roots = {row["path"]: row for row in state["authority_roots"]}

    assert all(row["immutable"] is True for row in roots.values())
    assert roots[str(remediation.CRITICISM_MATRIX.relative_to(REPO))]["sha256"] == (
        remediation._sha256(remediation.CRITICISM_MATRIX)
    )
    assert roots[str(remediation.FINAL_REFEREE_REPORT.relative_to(REPO))]["role"] == (
        "immutable_historical_referee_prose_non_authoritative_for_current_counts"
    )
    assert remediation._sha256(remediation.CHECKPOINT_065) == (
        remediation.EXPECTED_CHECKPOINT_065_SHA256
    )
    backlog_input = (
        f"{remediation.BACKLOG.relative_to(REPO)}:{remediation._sha256(remediation.BACKLOG)}"
    )
    assert backlog_input in state["input_hashes"]


@pytest.mark.parametrize(
    "path_name",
    ["CRITICISM_MATRIX", "ATOMIC_LEDGER", "ROOT_ADJUDICATIONS"],
)
def test_write_cannot_bless_mutated_frozen_authority(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    path_name: str,
) -> None:
    source = getattr(remediation, path_name)
    mutated = tmp_path / source.name
    mutated.write_bytes(source.read_bytes() + b"\n")
    monkeypatch.setattr(remediation, path_name, mutated)

    with pytest.raises(ValueError, match="frozen authority"):
        remediation.write_all()


def test_proposal_crosswalk_supersedes_both_old_namespaces_once() -> None:
    crosswalk = _yaml(remediation.CROSSWALK)
    rows = crosswalk["rows"]
    proposal_ids = [row["proposal_id"] for row in rows]

    assert crosswalk == remediation.build_crosswalk()
    assert len(proposal_ids) == len(set(proposal_ids))
    assert set(proposal_ids) == {
        *remediation.AUD_CROSSWALK,
        *remediation.OLD_PR_CROSSWALK,
    }
    assert all(row["superseded_by"] for row in rows)
    assert all(
        119 <= int(pr_id.split("-")[1]) <= 166
        for row in rows
        for pr_id in row["superseded_by"]
    )


def test_reconciliation_preserves_pr118_seal_and_user_data_constraint() -> None:
    payload = json.loads(remediation.RECONCILIATION.read_text(encoding="utf-8"))

    assert payload == remediation.build_reconciliation()
    assert payload["post_intake"]["total_prs"] == 113
    assert payload["post_intake"]["completed_prs"] == 66
    assert payload["post_intake"]["forbidden_advocate_slice_present"] is False
    assert payload["scientific_authority"]["rescued_count"] == 0
    assert payload["immutable_history"] == {
        "pr118_seal_commit": remediation.EXPECTED_PR118_SEAL_COMMIT,
        "manifest_regenerated": False,
        "checkpoint_065_sha256": remediation.EXPECTED_CHECKPOINT_065_SHA256,
    }
    assert payload["user_execution_constraint"] == {
        "pr3_e2e_download": "complete",
        "pr4_download": "not_started",
        "pr4_data_analysis": "skip_entirely_at_PR-150",
    }


def test_reconciliation_is_independent_of_future_live_dag_status(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    frozen = remediation.build_reconciliation()
    status = _yaml(remediation.STATUS)
    status["completed"] = [*status["completed"], "PR-120"]
    status["pending"] = [pr_id for pr_id in status["pending"] if pr_id != "PR-120"]
    status["in_progress"] = "PR-121"
    future_status = tmp_path / "pr_status.yaml"
    future_status.write_text(yaml.safe_dump(status, sort_keys=False), encoding="utf-8")
    backlog = _yaml(remediation.BACKLOG)
    backlog["live_update_marker"] = "PR-120-plus"
    future_backlog = tmp_path / "pr_backlog.yaml"
    future_backlog.write_text(yaml.safe_dump(backlog, sort_keys=False), encoding="utf-8")
    monkeypatch.setattr(remediation, "STATUS", future_status)
    monkeypatch.setattr(remediation, "BACKLOG", future_backlog)

    assert remediation.build_reconciliation() == frozen


def test_full_validator_does_not_reinterpret_future_status_as_pr119_closeout(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    status = _yaml(remediation.STATUS)
    status["completed"] = [*status["completed"], "PR-120"]
    status["pending"] = [pr_id for pr_id in status["pending"] if pr_id != "PR-120"]
    status["in_progress"] = "PR-121"
    future_status = tmp_path / "pr_status.yaml"
    future_status.write_text(yaml.safe_dump(status, sort_keys=False), encoding="utf-8")
    monkeypatch.setattr(remediation, "STATUS", future_status)

    remediation.validate_all()


def test_write_refuses_to_overwrite_tampered_reconciliation(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    payload = remediation.build_reconciliation()
    payload["scientific_authority"]["rescued_count"] = 3
    tampered = tmp_path / "pr119_intake_reconciliation.json"
    tampered.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    monkeypatch.setattr(remediation, "RECONCILIATION", tampered)

    with pytest.raises(ValueError, match="refusing overwrite"):
        remediation.write_all()


def test_full_remediation_validator_accepts_only_the_final_pr119_transaction() -> None:
    remediation.validate_all()
