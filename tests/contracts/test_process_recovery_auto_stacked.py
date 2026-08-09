from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[2]
HARNESS = ROOT / ".agent-harness" / "scripts"
if str(HARNESS) not in sys.path:
    sys.path.insert(0, str(HARNESS))

import _harness  # noqa: E402
from publication_integrity import (  # noqa: E402
    PublicationIntegrityError,
    classify_publication_command,
)


SHA_A = "a" * 40
SHA_B = "b" * 40
HASH_A = "1" * 64
HASH_B = "2" * 64


def _api(name: str):
    value = getattr(_harness, name, None)
    assert callable(value), f"process-recovery API is missing: {name}"
    return value


def _pr(
    lifecycle: str,
    *,
    history: list[str] | None = None,
    base_sha: str | None = None,
    predecessor_pr: str | None = None,
    predecessor_sealed_sha: str | None = None,
    sealed_head: str | None = None,
    pushed_ref: str | None = None,
    pr_url: str | None = None,
) -> dict[str, object]:
    return {
        "lifecycle": lifecycle,
        "lifecycle_history": history or ["PLANNED", lifecycle],
        "base_sha": base_sha,
        "predecessor_pr": predecessor_pr,
        "predecessor_sealed_sha": predecessor_sealed_sha,
        "sealed_head": sealed_head,
        "pushed_ref": pushed_ref,
        "pr_url": pr_url,
        "production_hash": None,
        "dependency_hashes": {},
        "gate_dispositions": {"lifecycle": "DEFERRED"},
        "assurance_budget": {"maximum": 16, "consumed": 0},
    }


def _status(
    *,
    active_pr: str | None,
    pr283: dict[str, object],
    pr284: dict[str, object],
) -> dict[str, object]:
    order = [f"PR-{number}" for number in range(283, 293)]
    prs = {
        "PR-283": pr283,
        "PR-284": pr284,
    }
    previous = "PR-284"
    for number in range(285, 293):
        current = f"PR-{number}"
        prs[current] = _pr(
            "PLANNED",
            history=["PLANNED"],
            predecessor_pr=previous,
        )
        previous = current
    return {
        "in_progress": active_pr,
        "stacked_pr_execution": {
            "schema_version": 1,
            "stack_id": "PROCESS_INFLATION_RECOVERY_PHASE2",
            "execution_mode": "AUTO_STACKED_PR",
            "merge_policy": "HUMAN_ONLY",
            "target_sha": SHA_A,
            "active_implementation_pr": active_pr,
            "pr_order": order,
            "prs": prs,
        },
    }


def test_future_pr_before_predecessor_open_is_ineligible_without_budget_cost() -> None:
    evaluate = _api("evaluate_stack_eligibility")
    status = _status(
        active_pr="PR-283",
        pr283=_pr(
            "SEALED",
            history=[
                "PLANNED",
                "ACTIVE",
                "IMPLEMENTED",
                "VALIDATED",
                "REVIEWED",
                "SEALED",
            ],
            base_sha=SHA_A,
            sealed_head=SHA_B,
        ),
        pr284=_pr(
            "PLANNED",
            history=["PLANNED"],
            predecessor_pr="PR-283",
        ),
    )

    result = evaluate(status, work_unit_id="PR-284", candidate_sha=SHA_B)

    assert result["eligible"] is False
    assert result["disposition"] == "INELIGIBLE"
    assert result["retry_budget_cost"] == 0
    assert result["assurance_budget_cost"] == 0
    assert any("PR_OPEN" in item for item in result["errors"])


@pytest.mark.parametrize(
    "lifecycle",
    ("ACTIVE", "IMPLEMENTED", "VALIDATED", "REVIEWED", "SEALED", "PUSHED"),
)
def test_current_pr_remains_eligible_through_pre_open_lifecycle(
    lifecycle: str,
) -> None:
    evaluate = _api("evaluate_stack_eligibility")
    states = list(_harness.LIFECYCLE_STATES)
    history = states[: states.index(lifecycle) + 1]
    lifecycle_index = states.index(lifecycle)
    status = _status(
        active_pr="PR-283",
        pr283=_pr(
            lifecycle,
            history=history,
            base_sha=SHA_A,
            sealed_head=(
                SHA_B if lifecycle_index >= states.index("SEALED") else None
            ),
            pushed_ref=(
                "refs/heads/recovery/pr283"
                if lifecycle_index >= states.index("PUSHED")
                else None
            ),
        ),
        pr284=_pr("PLANNED", history=["PLANNED"], predecessor_pr="PR-283"),
    )

    result = evaluate(status, work_unit_id="PR-283", candidate_sha=SHA_A)

    assert result["eligible"] is True
    assert result["disposition"] == "PASS"


def test_second_active_implementation_pr_is_refused() -> None:
    evaluate = _api("evaluate_stack_eligibility")
    status = _status(
        active_pr="PR-283",
        pr283=_pr("ACTIVE", base_sha=SHA_A),
        pr284=_pr(
            "ACTIVE",
            base_sha=SHA_B,
            predecessor_pr="PR-283",
            predecessor_sealed_sha=SHA_B,
        ),
    )

    result = evaluate(status, work_unit_id="PR-284", candidate_sha=SHA_B)

    assert result["eligible"] is False
    assert any("active implementation" in item.lower() for item in result["errors"])


def test_next_pr_must_start_at_exact_recorded_predecessor_sealed_head() -> None:
    evaluate = _api("evaluate_stack_eligibility")
    status = _status(
        active_pr="PR-284",
        pr283=_pr(
            "PR_OPEN",
            history=[
                "PLANNED",
                "ACTIVE",
                "IMPLEMENTED",
                "VALIDATED",
                "REVIEWED",
                "SEALED",
                "PUSHED",
                "PR_OPEN",
            ],
            base_sha=SHA_A,
            sealed_head=SHA_A,
            pushed_ref="refs/heads/recovery/pr283",
            pr_url="https://github.com/example/htt_base/pull/1",
        ),
        pr284=_pr(
            "ACTIVE",
            base_sha=SHA_B,
            predecessor_pr="PR-283",
            predecessor_sealed_sha=SHA_A,
        ),
    )

    result = evaluate(status, work_unit_id="PR-284", candidate_sha=SHA_B)

    assert result["eligible"] is False
    assert any("sealed head" in item.lower() for item in result["errors"])


def _git(repo: Path, *args: str) -> str:
    completed = subprocess.run(
        ["git", *args],
        cwd=repo,
        check=True,
        text=True,
        capture_output=True,
    )
    return completed.stdout.strip()


def test_existing_stable_patch_id_reintroduction_is_refused(tmp_path: Path) -> None:
    reject_duplicates = _api("reject_duplicate_stable_patch_ids")
    repo = tmp_path / "repo"
    repo.mkdir()
    _git(repo, "init", "-q")
    _git(repo, "config", "user.name", "Bootstrap Test")
    _git(repo, "config", "user.email", "bootstrap@example.invalid")
    _git(repo, "commit", "--allow-empty", "-qm", "root")
    (repo / "payload.txt").write_text("salvage\n", encoding="utf-8")
    _git(repo, "add", "payload.txt")
    _git(repo, "commit", "-qm", "introduce logical patch")
    original = _git(repo, "rev-parse", "HEAD")
    _git(repo, "revert", "--no-edit", original)
    base = _git(repo, "rev-parse", "HEAD")
    (repo / "payload.txt").write_text("salvage\n", encoding="utf-8")
    _git(repo, "add", "payload.txt")
    _git(repo, "commit", "-qm", "duplicate logical patch")
    candidate = _git(repo, "rev-parse", "HEAD")

    with pytest.raises(PublicationIntegrityError, match="stable patch"):
        reject_duplicates(repo, base_sha=base, candidate_sha=candidate)


def test_activation_uses_exact_fork_base_not_candidate_tip(tmp_path: Path) -> None:
    resolve_base = _api("resolve_candidate_activation_base")
    repo = tmp_path / "repo"
    repo.mkdir()
    _git(repo, "init", "-q")
    _git(repo, "config", "user.name", "Bootstrap Test")
    _git(repo, "config", "user.email", "bootstrap@example.invalid")
    _git(repo, "commit", "--allow-empty", "-qm", "canonical target")
    base = _git(repo, "rev-parse", "HEAD")
    (repo / "process.txt").write_text("commit A\n", encoding="utf-8")
    _git(repo, "add", "process.txt")
    _git(repo, "commit", "-qm", "process recovery commit")
    candidate = _git(repo, "rev-parse", "HEAD")
    status = _status(
        active_pr="PR-283",
        pr283=_pr("ACTIVE", base_sha=base),
        pr284=_pr("PLANNED", history=["PLANNED"], predecessor_pr="PR-283"),
    )
    status["stacked_pr_execution"]["target_sha"] = base

    assert candidate != base
    assert resolve_base(
        repo,
        status,
        work_unit_id="PR-283",
        candidate_ref="HEAD",
    ) == base


def test_shared_stack_assignment_count_spans_git_worktrees(tmp_path: Path) -> None:
    count_assignments = _api("shared_stack_assignment_count")
    active_runs = _api("shared_active_stack_runs")
    repo = tmp_path / "repo"
    peer = tmp_path / "peer"
    repo.mkdir()
    _git(repo, "init", "-q")
    _git(repo, "config", "user.name", "Bootstrap Test")
    _git(repo, "config", "user.email", "bootstrap@example.invalid")
    _git(repo, "commit", "--allow-empty", "-qm", "canonical target")
    _git(repo, "worktree", "add", "--detach", str(peer), "HEAD")
    for index, worktree in enumerate((repo, peer), start=1):
        run_id = f"phase2-run-{index}"
        run_dir = worktree / ".agent-harness" / "runs" / run_id
        assignments = run_dir / "assignments"
        assignments.mkdir(parents=True)
        (run_dir / "RUN_PLAN.json").write_text(
            json.dumps(
                {
                    "run_id": run_id,
                    "work_unit_id": "PR-283",
                    "stack_id": "PROCESS_INFLATION_RECOVERY_PHASE2",
                    "execution_mode": "AUTO_STACKED_PR",
                }
            ),
            encoding="utf-8",
        )
        (assignments / f"assignment-{index}.json").write_text("{}\n", encoding="utf-8")
    runtime = peer / ".agent-harness" / "runtime"
    runtime.mkdir(parents=True)
    (runtime / "ACTIVE_RUN").write_text("phase2-run-2\n", encoding="utf-8")

    assert count_assignments(
        repo,
        stack_id="PROCESS_INFLATION_RECOVERY_PHASE2",
        work_unit_id="PR-283",
    ) == 2
    assert active_runs(
        repo,
        stack_id="PROCESS_INFLATION_RECOVERY_PHASE2",
    ) == [
        {
            "worktree": str(peer.resolve()),
            "run_id": "phase2-run-2",
            "work_unit_id": "PR-283",
        }
    ]


def test_sealed_production_mutation_invalidates_seal() -> None:
    evaluate = _api("evaluate_evidence_freshness")

    result = evaluate(
        {"production_hash": HASH_A, "dependency_hashes": {"PR-282": HASH_A}},
        {"production_hash": HASH_B, "dependency_hashes": {"PR-282": HASH_A}},
    )

    assert result["seal_valid"] is False
    assert result["substantive_rerun_required"] is True
    assert result["reason"] == "PRODUCTION_HASH_CHANGED"


def test_receipt_only_change_reuses_substantive_assurance() -> None:
    evaluate = _api("evaluate_evidence_freshness")
    key = {"production_hash": HASH_A, "dependency_hashes": {"PR-282": HASH_B}}

    result = evaluate(key, dict(key))

    assert result == {
        "seal_valid": True,
        "substantive_rerun_required": False,
        "stale_dependencies": [],
        "reason": "EVIDENCE_KEY_UNCHANGED",
    }


def test_lifecycle_transitions_are_adjacent_and_auto_merge_is_refused() -> None:
    validate_transition = _api("validate_lifecycle_transition")
    validate_mode = _api("validate_execution_mode")

    validate_transition("PLANNED", "ACTIVE")
    with pytest.raises(PublicationIntegrityError, match="illegal lifecycle"):
        validate_transition("ACTIVE", "VALIDATED")
    with pytest.raises(PublicationIntegrityError, match="AUTO_MERGE"):
        validate_mode("AUTO_MERGE")
    assert classify_publication_command("gh pr merge 12 --merge")[0] is True


def test_stack_status_authority_requires_one_serial_active_pr() -> None:
    validate = _api("validate_stacked_execution_status")
    status = _status(
        active_pr="PR-283",
        pr283=_pr("ACTIVE", base_sha=SHA_A),
        pr284=_pr(
            "PLANNED",
            history=["PLANNED"],
            predecessor_pr="PR-283",
        ),
    )

    assert validate(status) == []

    status["stacked_pr_execution"]["prs"]["PR-285"]["lifecycle"] = "ACTIVE"
    status["stacked_pr_execution"]["prs"]["PR-285"]["lifecycle_history"] = [
        "PLANNED",
        "ACTIVE",
    ]
    errors = validate(status)
    assert any("exactly one" in item.lower() for item in errors)


def test_stack_status_allows_terminal_state_after_pr292_open() -> None:
    validate = _api("validate_stacked_execution_status")
    status = _status(
        active_pr="PR-283",
        pr283=_pr("ACTIVE", base_sha=SHA_A),
        pr284=_pr("PLANNED", history=["PLANNED"], predecessor_pr="PR-283"),
    )
    stack = status["stacked_pr_execution"]
    previous_sha = SHA_A
    for pr_id in stack["pr_order"]:
        record = stack["prs"][pr_id]
        record.update(
            {
                "lifecycle": "PR_OPEN",
                "lifecycle_history": list(_harness.LIFECYCLE_STATES),
                "base_sha": previous_sha,
                "predecessor_sealed_sha": (
                    None if pr_id == "PR-283" else previous_sha
                ),
                "sealed_head": SHA_B,
                "pushed_ref": f"refs/heads/recovery/{pr_id.lower()}",
                "pr_url": f"https://github.com/example/htt_base/pull/{pr_id[3:]}",
            }
        )
        previous_sha = SHA_B
    stack["active_implementation_pr"] = None
    status["in_progress"] = None

    assert validate(status) == []


def test_status_loader_requires_synchronized_execution_mirrors() -> None:
    load = _api("load_stacked_execution_status")

    status = load(ROOT)

    assert status["in_progress"] == "PR-283"
    assert (
        status["stacked_pr_execution"]["execution_mode"]
        == "AUTO_STACKED_PR"
    )


def test_run_execution_fields_bind_the_active_status_authority() -> None:
    validate = _api("validate_run_execution_fields")
    status = _api("load_stacked_execution_status")(ROOT)
    authority = status["stacked_pr_execution"]["prs"]["PR-283"]
    authority_budget = authority["assurance_budget"]
    plan = {
        "work_unit_id": "PR-283",
        "execution_mode": "AUTO_STACKED_PR",
        "lifecycle_state": authority["lifecycle"],
        "stack_id": "PROCESS_INFLATION_RECOVERY_PHASE2",
        "activation_base_sha": "ff9ef9f45747e559c5343b463cf010dfc3a7432a",
        "predecessor_pr": None,
        "predecessor_sealed_sha": None,
        "production_hash": None,
        "dependency_hashes": {},
        "gate_disposition": "PASS",
        "assurance_budget": dict(authority_budget),
    }

    assert validate(plan, repo=ROOT) == []

    stale_budget = dict(plan)
    stale_budget["assurance_budget"] = {
        **authority_budget,
        "consumed": authority_budget["consumed"] + 1,
    }
    assert any(
        "assurance_budget differs" in item
        for item in validate(stale_budget, repo=ROOT)
    )

    future = dict(plan)
    future.update(
        {
            "work_unit_id": "PR-284",
            "lifecycle_state": "PLANNED",
            "predecessor_pr": "PR-283",
        }
    )
    errors = validate(future, repo=ROOT)
    assert any("active implementation" in item.lower() for item in errors)


def test_dag_cli_reports_selected_eligibility_separately() -> None:
    command = [
        sys.executable,
        "scripts/codex_harness/validate_pr_dag.py",
        "docs/codex_handoff/pr_backlog.yaml",
        "--status",
        "docs/codex_handoff/pr_status.yaml",
        "--work-unit",
        "PR-283",
        "--candidate-ref",
        "HEAD",
    ]
    eligible = subprocess.run(
        command,
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    assert eligible.returncode == 0, eligible.stdout + eligible.stderr
    assert "eligibility=ELIGIBLE" in eligible.stdout

    command[command.index("PR-283")] = "PR-284"
    deferred = subprocess.run(
        command,
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    assert deferred.returncode == 2
    assert "INELIGIBLE/DEFERRED" in deferred.stdout
    assert "retry_budget=0 assurance_budget=0" in deferred.stdout
