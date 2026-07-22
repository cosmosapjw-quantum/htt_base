"""PR-124 preflight acceptance tests (audit §10 items 1-14).

The numbered tests map 1:1 to acceptance criteria in
docs/audits/shared_context_cas_harness_final_audit_20260717/
FINAL_AUDIT_AND_REPAIR_RECOMMENDATION.md §10. Tests run the real harness
scripts and hooks as subprocesses against a disposable git repo under
tmp_path (the scripts resolve their data root via `git rev-parse
--show-toplevel`), so enforcement is exercised end-to-end, not via mocks.
MA-01 adds one end-to-end lifecycle regression ahead of those frozen checks.
"""
from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPTS = REPO_ROOT / ".agent-harness" / "scripts"
HOOKS = REPO_ROOT / ".codex" / "hooks"
CONTEXT_VERSION = "test-context-version"


def _run(
    cmd: list[str],
    cwd: Path,
    input_text: str | None = None,
    env: dict[str, str] | None = None,
):
    return subprocess.run(
        cmd, cwd=cwd, input=input_text, env=env,
        text=True, capture_output=True, check=False,
    )


def _script(name: str) -> str:
    return str(SCRIPTS / name)


def _harness_cli(repo: Path, name: str, *args: str):
    return _run([sys.executable, _script(name), *args], cwd=repo)


def _init_tmp_repo(
    tmp_path: Path,
    *,
    active: bool = True,
    context_version: str = CONTEXT_VERSION,
) -> Path:
    repo = tmp_path / "repo"
    (repo / ".agent-harness" / "context" / "roles").mkdir(parents=True)
    (repo / ".agent-harness" / "generated").mkdir(parents=True)
    (repo / ".agent-harness" / "templates").mkdir(parents=True)
    (repo / ".codex" / "agents").mkdir(parents=True)
    assert _run(["git", "init", "-q"], cwd=repo).returncode == 0

    for template in (REPO_ROOT / ".agent-harness" / "templates").glob("*.json"):
        (repo / ".agent-harness" / "templates" / template.name).write_bytes(
            template.read_bytes()
        )

    for name, sandbox in (
        ("context_mapper", "workspace-write"),
        ("cas_sympy", "workspace-write"),
        ("adjudicator", "workspace-write"),
    ):
        (repo / ".codex" / "agents" / f"{name}.toml").write_text(
            f'name = "{name}"\ndescription = "test profile"\n'
            f'sandbox_mode = "{sandbox}"\n',
            encoding="utf-8",
        )

    (repo / ".agent-harness" / "context" / "roles" / "context_mapper.md").write_text(
        "# role\n", encoding="utf-8"
    )
    (repo / "input.txt").write_text("input-v1\n", encoding="utf-8")
    index = {
        "schema_version": 1,
        "context_version": context_version,
        "max_injected_chars": 24000,
        "shared_files": [],
        "file_hashes": {},
        "role_files": {
            "context_mapper": [".agent-harness/context/roles/context_mapper.md"]
        },
    }
    (repo / ".agent-harness" / "context" / "CONTEXT_INDEX.json").write_text(
        json.dumps(index, indent=2) + "\n", encoding="utf-8"
    )
    (repo / ".agent-harness" / "context" / "CLAIM_REGISTRY.jsonl").write_text(
        json.dumps(
            {
                "claim_id": "C-001",
                "statement": "Disposable harness test claim.",
                "status": "test_only",
            }
        )
        + "\n",
        encoding="utf-8",
    )
    (repo / ".agent-harness" / "generated" / "CONTEXT_PACK.md").write_text(
        "# Canonical Shared Context Pack\ncontent\n", encoding="utf-8"
    )
    if not active:
        return repo

    active_pointer = repo / ".agent-harness" / "runtime" / "ACTIVE_RUN"
    active_pointer.parent.mkdir(parents=True)
    active_pointer.write_text("run-1\n", encoding="utf-8")
    run_dir = repo / ".agent-harness" / "runs" / "run-1"
    for sub in ("assignments", "results", "launches"):
        (run_dir / sub).mkdir(parents=True)
    plan = {
        "schema_version": 1,
        "run_id": "run-1",
        "work_unit_id": "PR-TEST",
        "context_version": context_version,
        "budget": {
            "max_concurrent": 4,
            "max_total": 8,
            "max_total_per_work_unit": 16,
            "max_depth": 2,
        },
    }
    (run_dir / "RUN_PLAN.json").write_text(
        json.dumps(plan, indent=2) + "\n", encoding="utf-8"
    )
    return repo


def test_clean_clone_init_validate_close_and_dangling_recovery(
    tmp_path: Path,
) -> None:
    empty_context_sha = hashlib.sha256(b"").hexdigest()
    repo = _init_tmp_repo(
        tmp_path,
        active=False,
        context_version=empty_context_sha,
    )

    validated = _harness_cli(repo, "validate_harness.py")
    assert validated.returncode == 0, validated.stdout + validated.stderr
    assert json.loads(validated.stdout)["active_run"] is None

    initialized = _harness_cli(
        repo,
        "init_run.py",
        "--run-id",
        "ma01-lifecycle",
        "--work-unit",
        "MA-01",
    )
    assert initialized.returncode == 0, initialized.stdout + initialized.stderr
    active_pointer = repo / ".agent-harness" / "runtime" / "ACTIVE_RUN"
    assert active_pointer.read_text(encoding="utf-8") == "ma01-lifecycle\n"

    refused_overwrite = _harness_cli(
        repo,
        "init_run.py",
        "--run-id",
        "ma01-overwrite",
        "--work-unit",
        "MA-01",
    )
    assert refused_overwrite.returncode != 0
    assert "Active run already exists" in refused_overwrite.stderr
    assert not (repo / ".agent-harness" / "runs" / "ma01-overwrite").exists()

    active_validation = _harness_cli(repo, "validate_harness.py")
    assert active_validation.returncode == 0
    assert json.loads(active_validation.stdout)["active_run"] == "ma01-lifecycle"

    closed = _harness_cli(
        repo,
        "close_run.py",
        "--run-id",
        "ma01-lifecycle",
    )
    assert closed.returncode == 0, closed.stdout + closed.stderr
    close_payload = json.loads(closed.stdout)
    assert close_payload["closed_run"] == "ma01-lifecycle"
    assert close_payload["run_directory_deleted"] is False
    assert not active_pointer.exists()
    assert (repo / ".agent-harness/runs/ma01-lifecycle/RUN_SUMMARY.json").is_file()

    post_close = _harness_cli(repo, "validate_harness.py")
    assert post_close.returncode == 0
    assert json.loads(post_close.stdout)["active_run"] is None

    active_pointer.write_text("missing-run\n", encoding="utf-8")
    dangling = _harness_cli(repo, "validate_harness.py")
    assert dangling.returncode == 1
    dangling_payload = json.loads(dangling.stdout)
    assert dangling_payload["state_errors"] == [
        {
            "code": "DANGLING_ACTIVE_RUN",
            "message": "The active-run pointer has no valid matching RUN_PLAN.json target.",
            "pointer": ".agent-harness/runtime/ACTIVE_RUN",
            "run_id": "missing-run",
        }
    ]
    assert "Traceback" not in dangling.stdout + dangling.stderr

    abandoned = _harness_cli(repo, "close_run.py", "--abandon")
    assert abandoned.returncode == 0, abandoned.stdout + abandoned.stderr
    abandon_payload = json.loads(abandoned.stdout)
    assert abandon_payload["abandoned"] is True
    assert abandon_payload["run_directory_deleted"] is False
    assert not active_pointer.exists()


def _register_assignment(
    repo: Path,
    assignment_id: str = "A-001",
    *,
    live_input: bool = False,
) -> Path:
    completed = _run(
        [
            sys.executable,
            _script("new_assignment.py"),
            "--assignment-id", assignment_id,
            "--agent-type", "context_mapper",
            "--task", "bounded test task",
            "--risk-tier", "R1",
            "--claim-id", "C-001",
            "--live-input" if live_input else "--required-input", "input.txt",
            "--allowed-tool", "read",
            "--required-output", "result envelope",
        ],
        cwd=repo,
    )
    assert completed.returncode == 0, completed.stdout + completed.stderr
    return repo / ".agent-harness" / "runs" / "run-1" / "assignments" / f"{assignment_id}.json"


def _create_receipt(repo: Path, assignment_id: str = "A-001", **kwargs) -> dict:
    args = [
        sys.executable,
        _script("launch_receipt.py"),
        "create",
        "--assignment-id", assignment_id,
        "--requested-profile", kwargs.get("requested", "context_mapper"),
        "--attested",
    ]
    if kwargs.get("actual"):
        args += ["--actual-profile", kwargs["actual"]]
    completed = _run(args, cwd=repo)
    assert completed.returncode == 0, completed.stdout + completed.stderr
    receipt_path = (
        repo / ".agent-harness" / "runs" / "run-1" / "launches" / f"{assignment_id}.json"
    )
    return json.loads(receipt_path.read_text(encoding="utf-8"))


def _verify(repo: Path, assignment_id: str = "A-001"):
    return _run(
        [
            sys.executable,
            _script("launch_receipt.py"),
            "verify",
            "--assignment-id", assignment_id,
        ],
        cwd=repo,
    )


# --- 1 -----------------------------------------------------------------
def test_stale_effective_context_blocks_launch(tmp_path: Path) -> None:
    repo = _init_tmp_repo(tmp_path)
    assignment_path = _register_assignment(repo)
    _create_receipt(repo)
    assert _verify(repo).returncode == 0

    # (a) assignment file mutated after sealing
    original = assignment_path.read_text(encoding="utf-8")
    assignment_path.write_text(
        original.replace("bounded test task", "mutated task"), encoding="utf-8"
    )
    assert _verify(repo).returncode == 2
    assignment_path.write_text(original, encoding="utf-8")
    assert _verify(repo).returncode == 0

    # (b) explicitly exact input bytes drift after sealing
    (repo / "input.txt").write_text("input-v2 DRIFTED\n", encoding="utf-8")
    assert _verify(repo).returncode == 2
    (repo / "input.txt").write_text("input-v1\n", encoding="utf-8")
    assert _verify(repo).returncode == 0

    # (c) role file changes
    role = repo / ".agent-harness" / "context" / "roles" / "context_mapper.md"
    role.write_text("# role CHANGED\n", encoding="utf-8")
    assert _verify(repo).returncode == 2
    role.write_text("# role\n", encoding="utf-8")
    assert _verify(repo).returncode == 0

    # (d) injection config changes
    index_path = repo / ".agent-harness" / "context" / "CONTEXT_INDEX.json"
    index = json.loads(index_path.read_text(encoding="utf-8"))
    index["max_injected_chars"] = 12000
    index_path.write_text(json.dumps(index, indent=2) + "\n", encoding="utf-8")
    assert _verify(repo).returncode == 2


# --- 2 -----------------------------------------------------------------
def test_profile_registry_fails_on_unknown_duplicate_and_sandbox_conflict(
    tmp_path: Path,
) -> None:
    repo = _init_tmp_repo(tmp_path)
    completed = _run(
        [
            sys.executable,
            _script("new_assignment.py"),
            "--assignment-id", "A-UNK",
            "--agent-type", "not_installed_agent",
            "--task", "t",
            "--risk-tier", "R1",
            "--claim-id", "C-001",
            "--required-input", "input.txt",
            "--allowed-tool", "read",
            "--required-output", "envelope",
        ],
        cwd=repo,
    )
    assert completed.returncode != 0
    assert "not an installed profile" in completed.stdout + completed.stderr

    (repo / ".codex" / "agents" / "zz-dup.toml").write_text(
        'name = "context_mapper"\ndescription = "dup"\nsandbox_mode = "read-only"\n',
        encoding="utf-8",
    )
    completed = _run(
        [
            sys.executable,
            _script("new_assignment.py"),
            "--assignment-id", "A-DUP",
            "--agent-type", "context_mapper",
            "--task", "t",
            "--risk-tier", "R1",
            "--claim-id", "C-001",
            "--required-input", "input.txt",
            "--allowed-tool", "read",
            "--required-output", "envelope",
        ],
        cwd=repo,
    )
    assert completed.returncode != 0
    combined = completed.stdout + completed.stderr
    assert "duplicate" in combined and "CONFLICTING" in combined


# --- 3 -----------------------------------------------------------------
def test_profile_receipt_mismatch_fails_and_absence_downgrades_to_generic(
    tmp_path: Path,
) -> None:
    repo = _init_tmp_repo(tmp_path)
    _register_assignment(repo)

    _create_receipt(repo, requested="context_mapper", actual="cas_sympy")
    completed = _verify(repo)
    assert completed.returncode == 2
    assert "requested profile" in completed.stdout

    receipt_path = (
        repo / ".agent-harness" / "runs" / "run-1" / "launches" / "A-001.json"
    )
    receipt_path.unlink()
    completed = _verify(repo)
    assert completed.returncode == 0
    payload = json.loads(completed.stdout)
    assert payload["verdict"] == "downgraded"
    assert payload["actual_profile"] == "generic_prompted"
    assert payload["correlation_group"] == "parent_llm"


def _write_result(repo: Path, assignment_id: str, extra: dict) -> Path:
    assignment_path = (
        repo
        / ".agent-harness"
        / "runs"
        / "run-1"
        / "assignments"
        / f"{assignment_id}.json"
    )
    assignment = json.loads(assignment_path.read_text(encoding="utf-8"))
    launch_path = (
        repo
        / ".agent-harness"
        / "runs"
        / "run-1"
        / "launches"
        / f"{assignment_id}.json"
    )
    launch = (
        json.loads(launch_path.read_text(encoding="utf-8"))
        if launch_path.is_file()
        else None
    )
    result = {
        "schema_version": 2,
        "run_id": "run-1",
        "assignment_id": assignment_id,
        "context_version": assignment["context_version"],
        "agent_type": "context_mapper",
        "independence_mode": "shared-core",
        "status": "pass",
        "result_path": f".agent-harness/runs/run-1/results/{assignment_id}.json",
        "assignment_sha256": assignment["assignment_sha256"],
        "launch_id": launch.get("launch_id") if launch else None,
        "launch_evidence": "self_declared" if launch else "unverified",
        "execution_evidence": "self_declared",
        "files_read": ["input.txt"],
        "files_read_evidence": "self_declared",
        "started_at": "2026-07-23T00:00:00+00:00",
        "completed_at": "2026-07-23T00:00:01+00:00",
        "tool_versions": {"python": sys.version.split()[0]},
        "commands": [],
        "artifacts": [],
        "findings": [
            {
                "finding_id": "F-001",
                "claim_id": "C-001",
                "verdict": "pass",
                "severity": "low",
                "statement": "Disposable harness finding.",
                "assumptions_used": [],
                "evidence_refs": ["input.txt"],
                "evidence_fingerprint": "fixture:input.txt@v1",
                "counterevidence_refs": [],
                "reproduction": [],
                "confidence": 1.0,
                "unresolved": [],
            }
        ],
        "claim_results": [],
        "errors": [],
    }
    result.update(extra)
    for finding in result.get("findings", []):
        if not isinstance(finding, dict):
            continue
        finding.setdefault("severity", "high")
        finding.setdefault("statement", "Disposable harness finding.")
        finding.setdefault("assumptions_used", [])
        finding.setdefault("evidence_refs", ["input.txt"])
        finding.setdefault("counterevidence_refs", [])
        finding.setdefault("reproduction", [])
        finding.setdefault("confidence", 1.0)
        finding.setdefault("unresolved", [])
    if "status" not in extra and any(
        isinstance(finding, dict) and finding.get("verdict") == "fail"
        for finding in result.get("findings", [])
    ):
        result["status"] = "fail"
    if "claim_results" not in extra:
        finding_ids = [
            finding["finding_id"]
            for finding in result.get("findings", [])
            if isinstance(finding, dict) and finding.get("claim_id") == "C-001"
        ]
        result["claim_results"] = [
            {
                "claim_id": "C-001",
                "outcome": (
                    "findings_present" if finding_ids else "examined_no_findings"
                ),
                "finding_ids": finding_ids,
                "summary": "Disposable terminal claim disposition.",
                **(
                    {}
                    if finding_ids
                    else {
                        "evidence_refs": ["input.txt"],
                    }
                ),
            }
        ]
    path = (
        repo / ".agent-harness" / "runs" / "run-1" / "results" / f"{assignment_id}.json"
    )
    path.write_text(json.dumps(result) + "\n", encoding="utf-8")
    return path


def _stop_hook(repo: Path, envelope: dict, trailing: str = ""):
    marker = f"HARNESS_RESULT: {json.dumps(envelope)}"
    return _run(
        [sys.executable, str(HOOKS / "subagent_stop_validate.py")],
        cwd=repo,
        input_text=json.dumps(
            {"last_assistant_message": f"work done\n{marker}{trailing}"}
        ),
    )


def _result_envelope(
    assignment_id: str = "A-001",
    status: str = "pass",
    context_version: str = CONTEXT_VERSION,
) -> dict:
    return {
        "assignment_id": assignment_id,
        "context_version": context_version,
        "status": status,
        "result_path": (
            f".agent-harness/runs/run-1/results/{assignment_id}.json"
        ),
    }


def _reseal_assignment(path: Path, mutate) -> dict:
    assignment = json.loads(path.read_text(encoding="utf-8"))
    mutate(assignment)
    assignment.pop("assignment_sha256", None)
    assignment["assignment_sha256"] = hashlib.sha256(
        json.dumps(assignment, sort_keys=True, ensure_ascii=False).encode("utf-8")
    ).hexdigest()
    path.write_text(json.dumps(assignment) + "\n", encoding="utf-8")
    return assignment


def _run_result_consumer(repo: Path, consumer: str, envelope: dict):
    if consumer == "stop_hook":
        completed = _stop_hook(repo, envelope)
        return completed, completed.stdout + completed.stderr
    if consumer == "merge":
        completed = _harness_cli(repo, "merge_results.py")
        merged = (
            repo / ".agent-harness" / "runs" / "run-1" / "MERGED_RESULTS.json"
        )
        output = completed.stdout + completed.stderr
        if merged.is_file():
            output += merged.read_text(encoding="utf-8")
        return completed, output
    completed = _harness_cli(repo, "validate_harness.py")
    return completed, completed.stdout + completed.stderr


# --- 4 -----------------------------------------------------------------
def test_blind_assignment_sibling_read_and_undeclared_scan_blocked(
    tmp_path: Path,
) -> None:
    repo = _init_tmp_repo(tmp_path)
    _register_assignment(repo)
    sibling = ".agent-harness/runs/run-1/results/A-OTHER.json"
    _write_result(repo, "A-001", {"files_read": ["input.txt", sibling]})
    envelope = {
        "assignment_id": "A-001",
        "context_version": CONTEXT_VERSION,
        "status": "pass",
        "result_path": ".agent-harness/runs/run-1/results/A-001.json",
    }
    completed = _stop_hook(repo, envelope)
    payload = json.loads(completed.stdout)
    assert payload["decision"] == "block"
    assert "blind-results violation" in payload["reason"]

    _write_result(repo, "A-001", {"files_read": ["input.txt", f"./{sibling}"]})
    completed = _stop_hook(repo, envelope)
    payload = json.loads(completed.stdout)
    assert payload["decision"] == "block"
    assert "not canonical repository-relative" in payload["reason"]

    # The same read is accepted once explicitly allowed by the assignment.
    assignment_path = (
        repo / ".agent-harness" / "runs" / "run-1" / "assignments" / "A-001.json"
    )
    assignment = json.loads(assignment_path.read_text(encoding="utf-8"))
    assignment["allowed_sibling_results"] = [sibling]
    assignment.pop("assignment_sha256")
    assignment["assignment_sha256"] = hashlib.sha256(
        json.dumps(assignment, sort_keys=True, ensure_ascii=False).encode("utf-8")
    ).hexdigest()
    assignment_path.write_text(json.dumps(assignment) + "\n", encoding="utf-8")
    _write_result(repo, "A-001", {"files_read": ["input.txt", sibling]})
    completed = _stop_hook(repo, envelope)
    assert completed.stdout.strip() == "", completed.stdout


# --- 5 -----------------------------------------------------------------
def test_hook_injected_context_reread_is_duplicate_delivery(tmp_path: Path) -> None:
    repo = _init_tmp_repo(tmp_path)
    _register_assignment(repo)

    start = _run(
        [sys.executable, str(HOOKS / "subagent_start_context.py")],
        cwd=repo,
        input_text=json.dumps({"agent_type": "context_mapper"}),
    )
    contract = json.loads(start.stdout)["hookSpecificOutput"]["additionalContext"]
    assert "MUST NOT re-read CONTEXT_PACK.md" in contract
    deliveries = (
        repo / ".agent-harness" / "runs" / "run-1" / "launches" / "deliveries.jsonl"
    )
    record = json.loads(deliveries.read_text(encoding="utf-8").splitlines()[0])
    assert record["truncated"] is False and record["mode"] == "hook_injected"

    _write_result(
        repo,
        "A-001",
        {"files_read": [".agent-harness/generated/CONTEXT_PACK.md"]},
    )
    envelope = {
        "assignment_id": "A-001",
        "context_version": CONTEXT_VERSION,
        "status": "pass",
        "result_path": ".agent-harness/runs/run-1/results/A-001.json",
    }
    completed = _stop_hook(repo, envelope)
    payload = json.loads(completed.stdout)
    assert payload["decision"] == "block"
    assert "duplicate-delivery violation" in payload["reason"]


# --- 6 -----------------------------------------------------------------
def test_empty_tier1_assignment_registration_fails(tmp_path: Path) -> None:
    repo = _init_tmp_repo(tmp_path)
    completed = _run(
        [
            sys.executable,
            _script("new_assignment.py"),
            "--assignment-id", "A-EMPTY",
            "--agent-type", "unknown_agent_type",
            "--task", "t",
            "--risk-tier", "R1",
        ],
        cwd=repo,
    )
    assert completed.returncode != 0
    combined = completed.stdout + completed.stderr
    assert "REFUSED" in combined
    for token in (
        "claim_ids",
        "not an installed profile",
        "required_inputs",
        "allowed_tools",
        "required_outputs",
    ):
        assert token in combined, f"missing fail-closed error for {token}"
    assert not (
        repo / ".agent-harness" / "runs" / "run-1" / "assignments" / "A-EMPTY.json"
    ).exists()


# --- 7 -----------------------------------------------------------------
def test_dedup_same_tuple_different_refs_merges_and_unions_refs(
    tmp_path: Path,
) -> None:
    repo = _init_tmp_repo(tmp_path)
    for aid in ("A-001", "A-002"):
        _register_assignment(repo, aid)
    fingerprint = "doi:10.0000/example#disposable-finding"
    for aid, refs in (("A-001", ["ref/a.py:1"]), ("A-002", ["ref/b.py:9"])):
        _write_result(
            repo,
            aid,
            {
                "findings": [
                    {
                        "finding_id": f"F-{aid}",
                        "claim_id": "C-001",
                        "verdict": "fail",
                        "statement": (
                            "The disposable finding is present."
                            if aid == "A-001"
                            else "This is a paraphrase of the disposable finding."
                        ),
                        "evidence_fingerprint": fingerprint,
                        "evidence_refs": refs,
                    }
                ]
            },
        )
    completed = _run([sys.executable, _script("merge_results.py")], cwd=repo)
    assert completed.returncode == 0, completed.stdout + completed.stderr
    merged = json.loads(
        (
            repo / ".agent-harness" / "runs" / "run-1" / "MERGED_RESULTS.json"
        ).read_text(encoding="utf-8")
    )
    assert merged["raw_finding_count"] == 2
    assert merged["unique_finding_count"] == 1
    row = merged["findings"][0]
    assert row["evidence_refs"] == ["ref/a.py:1", "ref/b.py:9"]
    assert row["duplicate_count"] == 2

    # A different scoped identity preserves a distinct proposition and avoids
    # a false conflict even when its verdict differs.
    _write_result(
        repo,
        "A-002",
        {
            "findings": [
                {
                    "finding_id": "F-DISTINCT",
                    "claim_id": "C-001",
                    "verdict": "pass",
                    "statement": "A distinct finding about the same source.",
                    "evidence_fingerprint": "doi:10.0000/example#other-finding",
                    "evidence_refs": ["ref/b.py:9"],
                }
            ]
        },
    )
    completed = _run([sys.executable, _script("merge_results.py")], cwd=repo)
    assert completed.returncode == 0, completed.stdout + completed.stderr
    merged = json.loads(
        (
            repo / ".agent-harness" / "runs" / "run-1" / "MERGED_RESULTS.json"
        ).read_text(encoding="utf-8")
    )
    assert merged["unique_finding_count"] == 2

    # Opposite verdicts on the same evidence auto-conflict (no majority).
    _write_result(
        repo,
        "A-002",
        {
            "findings": [
                {
                    "finding_id": "F-OPP",
                    "claim_id": "C-001",
                    "verdict": "pass",
                    "statement": "The disposable claim does not fail.",
                    "evidence_fingerprint": fingerprint,
                }
            ]
        },
    )
    completed = _run([sys.executable, _script("merge_results.py")], cwd=repo)
    assert completed.returncode != 0
    merged = json.loads(
        (
            repo / ".agent-harness" / "runs" / "run-1" / "MERGED_RESULTS.json"
        ).read_text(encoding="utf-8")
    )
    assert merged["conflicts"], "opposite verdicts must populate conflicts"
    assert len(merged["conflicts"][0]["statements"]) == 2


def test_finding_ledger_does_not_treat_paraphrase_as_new_work(
    tmp_path: Path,
) -> None:
    repo = _init_tmp_repo(tmp_path)
    _register_assignment(repo)
    fingerprint = "doi:10.0000/example#bound-x"
    _write_result(
        repo,
        "A-001",
        {
            "findings": [
                {
                    "finding_id": "F-ORIGINAL",
                    "claim_id": "C-001",
                    "verdict": "fail",
                    "statement": "The estimator violates bound X.",
                    "evidence_fingerprint": fingerprint,
                }
            ]
        },
    )
    completed = _run([sys.executable, _script("merge_results.py")], cwd=repo)
    assert completed.returncode == 0, completed.stdout + completed.stderr
    merged_rel = ".agent-harness/runs/run-1/MERGED_RESULTS.json"
    completed = _run(
        [
            sys.executable,
            _script("finding_ledger.py"),
            "record",
            "--merged",
            merged_rel,
            "--resolution-commit",
            "a" * 40,
        ],
        cwd=repo,
    )
    assert completed.returncode == 0, completed.stdout + completed.stderr

    result_path = repo / ".agent-harness" / "runs" / "run-1" / "results" / "A-001.json"
    result = json.loads(result_path.read_text(encoding="utf-8"))
    result["findings"][0]["statement"] = "Bound X is broken by the estimator."
    result_path.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    completed = _run([sys.executable, _script("merge_results.py")], cwd=repo)
    assert completed.returncode == 0, completed.stdout + completed.stderr
    merged = json.loads((repo / merged_rel).read_text(encoding="utf-8"))
    assert merged["findings"][0]["previously_resolved"]["resolution_commit"] == "a" * 40

    completed = _run(
        [
            sys.executable,
            _script("finding_ledger.py"),
            "record",
            "--merged",
            merged_rel,
            "--resolution-commit",
            "b" * 40,
        ],
        cwd=repo,
    )
    assert completed.returncode == 0, completed.stdout + completed.stderr
    assert "recorded 0 resolved findings" in completed.stdout
    ledger = repo / ".agent-harness" / "ledger" / "FINDING_LEDGER.jsonl"
    assert len(ledger.read_text(encoding="utf-8").splitlines()) == 1


# --- 8 -----------------------------------------------------------------
def test_stop_hook_rejects_trailing_text_symlink_and_identity_mismatch(
    tmp_path: Path,
) -> None:
    repo = _init_tmp_repo(tmp_path)
    _register_assignment(repo)
    _write_result(repo, "A-001", {})
    envelope = {
        "assignment_id": "A-001",
        "context_version": CONTEXT_VERSION,
        "status": "pass",
        "result_path": ".agent-harness/runs/run-1/results/A-001.json",
    }

    completed = _stop_hook(repo, envelope, trailing="\nextra prose after marker")
    payload = json.loads(completed.stdout)
    assert payload["decision"] == "block"

    results_dir = repo / ".agent-harness" / "runs" / "run-1" / "results"
    real = results_dir / "A-001.json"
    hidden = repo / "hidden-target.json"
    hidden.write_bytes(real.read_bytes())
    real.unlink()
    real.symlink_to(hidden)
    completed = _stop_hook(repo, envelope)
    payload = json.loads(completed.stdout)
    assert payload["decision"] == "block"
    assert "symlink" in payload["reason"]
    real.unlink()
    _write_result(repo, "A-001", {})

    _create_receipt(repo)
    completed = _stop_hook(repo, {**envelope, "launch_id": "spoofed-launch-id"})
    payload = json.loads(completed.stdout)
    assert payload["decision"] == "block"
    assert "launch" in payload["reason"].lower()


def _write_contract(repo: Path) -> Path:
    contract = json.loads(
        (REPO_ROOT / ".agent-harness" / "templates" / "CAS_CONTRACT.json").read_text(
            encoding="utf-8"
        )
    )
    contract["identity"]["source_input_hashes"] = []
    path = repo / "CAS-TEST.json"
    path.write_text(json.dumps(contract, indent=2) + "\n", encoding="utf-8")
    return path


def _sha256(path: Path) -> str:
    import hashlib

    return hashlib.sha256(path.read_bytes()).hexdigest()


def _axis_result(
    repo: Path, axis: str, contract_sha: str, status: str = "PASS",
    completed_at: str = "2026-07-17T10:00:00+00:00",
) -> Path:
    payload = {
        "schema_version": 1,
        "axis": axis,
        "contract_id": "CAS-001",
        "contract_sha256": contract_sha,
        "status": status,
        "commands": [{"cmd": f"{axis} verification", "exit": 0}],
        "tool_versions": {},
        "source_output_hashes": [],
        "domain_assumption_diff": [],
        "evidence_class": "exact",
        "counterexample": None,
        "completed_at": completed_at,
    }
    path = repo / f"axis-{axis}.json"
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    return path


def _fake_cas_probe_env(repo: Path) -> dict[str, str]:
    """Make parent-owned engine probes pass without installing CAS engines."""

    fake_bin = repo / "fake-cas-bin"
    fake_bin.mkdir()
    scripts = {
        "wolframscript": "#!/bin/sh\nprintf 'Wolfram fake\\nXACT_LOAD_OK\\n'\n",
        "sage": "#!/bin/sh\nprintf 'SageMath fake with Singular\\n'\n",
        "lean": "#!/bin/sh\nprintf 'Lean fake\\n'\n",
    }
    for name, source in scripts.items():
        path = fake_bin / name
        path.write_text(source, encoding="utf-8")
        path.chmod(0o755)

    (repo / "formal").mkdir()
    (repo / "formal" / "lean-toolchain").write_text(
        "leanprover/lean4:test\n", encoding="utf-8"
    )
    (repo / "sympy.py").write_text(
        """__version__ = "test"
class Expr:
    def __pow__(self, other): return self
    def __sub__(self, other): return self
    def __rsub__(self, other): return self
    def __add__(self, other): return self
    def __mul__(self, other): return self
    def __eq__(self, other): return True
def symbols(name): return Expr()
def factor(value): return Expr()
""",
        encoding="utf-8",
    )
    return dict(os.environ, PATH=f"{fake_bin}:{os.environ.get('PATH', '')}")


def _write_runner_case(
    repo: Path, mode: str = "pass",
) -> tuple[Path, Path, dict[str, str]]:
    """Create one tiny observed-process CAS case without a real CAS engine."""

    contract_path = _write_contract(repo)
    contract = json.loads(contract_path.read_text(encoding="utf-8"))
    contract["target"]["exact_test_obligations"] = ["identity"]
    contract["target"]["expected_exact_values"] = {"value": "2"}
    contract_path.write_text(
        json.dumps(contract, indent=2) + "\n", encoding="utf-8"
    )

    axis_program = repo / "tiny_axis.py"
    axis_program.write_text(
        """import json
import sys
import time

mode = sys.argv[2]
payload = {
    "checks": {"identity": True},
    "domain_assumption_diff": [],
    "computed": {"value": "2"},
    "counterexample": None,
    # These child-authored authority claims must be ignored by the runner.
    "axis": "wolfram_xact",
    "status": "FAIL",
    "commands": [{"cmd": "fabricated", "exit": 0}],
}
if mode == "timeout":
    time.sleep(2)
elif mode == "missing_obligation":
    payload["checks"] = {}
elif mode == "false_check":
    payload["checks"]["identity"] = False
elif mode == "expected_mismatch":
    payload["computed"]["value"] = "3"
elif mode == "missing_counterexample":
    payload.pop("counterexample")
elif mode == "missing_computed":
    payload.pop("computed")
print(json.dumps(payload))
if mode == "nonzero":
    raise SystemExit(7)
""",
        encoding="utf-8",
    )
    axes = ("wolfram_xact", "sympy", "sage_singular", "lean")
    duplicate_argv = [sys.executable, axis_program.name, "shared", "pass"]
    run_spec = {
        "schema_version": 1,
        "axes": {
            axis: {
                "argv": duplicate_argv if mode == "duplicate_argv" else [
                    str(repo / "missing-axis-binary")
                    if axis == "sympy" and mode == "missing_binary"
                    else sys.executable,
                    axis_program.name,
                    axis,
                    mode if axis == "sympy" else "pass",
                ],
                "cwd": ".",
                "timeout_seconds": 1 if axis == "sympy" and mode == "timeout" else 10,
            }
            for axis in axes
        },
    }
    run_spec_path = repo / "CAS-RUN.json"
    run_spec_path.write_text(
        json.dumps(run_spec, indent=2) + "\n", encoding="utf-8"
    )
    return contract_path, run_spec_path, _fake_cas_probe_env(repo)


# --- 9 -----------------------------------------------------------------
def test_cas_contract_change_invalidates_all_axis_receipts(tmp_path: Path) -> None:
    repo = _init_tmp_repo(tmp_path)
    contract = _write_contract(repo)
    sha = _sha256(contract)
    axes = ("wolfram_xact", "sympy", "sage_singular", "lean")
    results = [_axis_result(repo, axis, sha) for axis in axes]
    for result in results:
        completed = _run(
            [
                sys.executable, _script("cas_gate.py"), "check-axis",
                "--contract", contract.name, "--result", result.name,
            ],
            cwd=repo,
        )
        assert completed.returncode == 0, completed.stdout

    mutated = json.loads(contract.read_text(encoding="utf-8"))
    mutated["semantics"]["assumptions"] = ["k > 0 added after the fact"]
    contract.write_text(json.dumps(mutated, indent=2) + "\n", encoding="utf-8")
    for result in results:
        completed = _run(
            [
                sys.executable, _script("cas_gate.py"), "check-axis",
                "--contract", contract.name, "--result", result.name,
            ],
            cwd=repo,
        )
        assert completed.returncode == 2
        assert "stale" in completed.stdout


# --- 10 ----------------------------------------------------------------
def test_cas_serialized_pass_envelopes_are_not_promotion_evidence(
    tmp_path: Path,
) -> None:
    repo = _init_tmp_repo(tmp_path)
    contract = _write_contract(repo)
    sha = _sha256(contract)
    axes = ("wolfram_xact", "sympy", "sage_singular", "lean")
    results = [_axis_result(repo, axis, sha) for axis in axes]

    # Even plausible runner-looking fields remain self-authored once loaded
    # from disk.  Only the process-owning run-adjudicate path has authority.
    for result in results:
        envelope = json.loads(result.read_text(encoding="utf-8"))
        envelope.update(
            {
                "evidence_origin": "runner_observed_local_subprocess",
                "claim_promotion_cas_eligible": True,
                "execution_evidence": {
                    "exit_code": 0,
                    "timed_out": False,
                },
            }
        )
        result.write_text(json.dumps(envelope, indent=2) + "\n", encoding="utf-8")

    completed = _run(
        [
            sys.executable, _script("cas_gate.py"), "adjudicate",
            "--contract", contract.name, "--results", *(r.name for r in results),
        ],
        cwd=repo,
    )
    assert completed.returncode == 2
    payload = json.loads(completed.stdout)
    assert payload["aggregate_status"] == "CAS_BLOCKED"
    assert payload["claim_promotion_cas_eligible"] is False
    assert "UNVERIFIED_EXECUTION" in json.dumps(payload)

    # Compatibility mode reports the frozen label separately, but remains
    # blocked and cannot satisfy the claim-promotion CAS component.
    completed = _run(
        [
            sys.executable, _script("cas_gate.py"), "adjudicate",
            "--historical-replay",
            "--contract", contract.name, "--results", *(r.name for r in results),
        ],
        cwd=repo,
    )
    assert completed.returncode == 2
    payload = json.loads(completed.stdout)
    assert payload["aggregate_status"] == "CAS_BLOCKED"
    assert payload["historical_aggregate_status"] == "CAS_4AXIS_PASS"
    assert payload["claim_promotion_cas_eligible"] is False
    assert payload["claim_promotion_cas_requirement"] == "NOT_SATISFIED"

    completed = _run(
        [
            sys.executable, _script("cas_gate.py"), "adjudicate",
            "--historical-replay",
            "--contract", contract.name,
            "--results", *(r.name for r in results[:3]),
        ],
        cwd=repo,
    )
    assert completed.returncode == 2
    payload = json.loads(completed.stdout)
    assert payload["aggregate_status"] == "CAS_BLOCKED"
    assert payload["missing_axes"] == ["lean"]


def test_cas_run_adjudicate_satisfies_only_the_cas_execution_component(
    tmp_path: Path,
) -> None:
    repo = _init_tmp_repo(tmp_path)
    contract, run_spec, env = _write_runner_case(repo)
    completed = _run(
        [
            sys.executable, _script("cas_gate.py"), "run-adjudicate",
            "--contract", contract.name,
            "--run-spec", run_spec.name,
        ],
        cwd=repo,
        env=env,
    )
    assert completed.returncode == 0, completed.stdout + completed.stderr
    payload = json.loads(completed.stdout)
    assert payload["aggregate_status"] == "CAS_4AXIS_PASS"
    assert set(payload["axis_statuses"].values()) == {"PASS"}
    assert payload["claim_promotion_cas_eligible"] is True
    assert payload["claim_promotion_cas_requirement"] == "SATISFIED"
    assert payload["evidence_origin"] == "runner_observed_local_subprocess"
    assert all(
        row["preflight_probe"]["status"] == "PASS"
        for row in payload["execution_evidence"].values()
    )
    assert len({
        tuple(row["argv"])
        for row in payload["execution_evidence"].values()
    }) == 4

    observed = payload["execution_evidence"]["sympy"]
    assert observed["argv"] == [sys.executable, "tiny_axis.py", "sympy", "pass"]
    assert observed["exit_code"] == 0
    assert observed["timed_out"] is False
    assert observed["payload"]["checks"] == {"identity": True}
    assert "status" not in observed["payload"]
    assert "commands" not in observed["payload"]
    assert "identity" in observed["stdout_tail"]


@pytest.mark.parametrize(
    "mode",
    [
        "nonzero",
        "timeout",
        "missing_binary",
        "duplicate_argv",
        "missing_obligation",
        "false_check",
        "expected_mismatch",
        "missing_counterexample",
        "missing_computed",
    ],
)
def test_cas_run_adjudicate_rejects_unobserved_or_failed_work(
    tmp_path: Path, mode: str,
) -> None:
    repo = _init_tmp_repo(tmp_path)
    contract, run_spec, env = _write_runner_case(repo, mode)
    completed = _run(
        [
            sys.executable, _script("cas_gate.py"), "run-adjudicate",
            "--contract", contract.name,
            "--run-spec", run_spec.name,
        ],
        cwd=repo,
        env=env,
    )
    assert completed.returncode == 2
    payload = json.loads(completed.stdout)
    assert payload["aggregate_status"] != "CAS_4AXIS_PASS"
    assert payload["claim_promotion_cas_eligible"] is False
    assert payload["claim_promotion_cas_requirement"] == "NOT_SATISFIED"
    if mode in {"missing_counterexample", "missing_computed"}:
        missing = mode.removeprefix("missing_")
        assert missing not in payload["execution_evidence"]["sympy"]["payload"]
        assert "missing required keys" in json.dumps(payload)
    if mode == "duplicate_argv":
        assert "reuse the same full argv" in json.dumps(payload)


def test_cas_run_adjudicate_rejects_reduced_axis_contract(tmp_path: Path) -> None:
    repo = _init_tmp_repo(tmp_path)
    contract_path, run_spec, env = _write_runner_case(repo)
    contract = json.loads(contract_path.read_text(encoding="utf-8"))
    contract["required_axes"] = ["sympy"]
    contract_path.write_text(json.dumps(contract, indent=2) + "\n", encoding="utf-8")
    completed = _run(
        [
            sys.executable, _script("cas_gate.py"), "run-adjudicate",
            "--contract", contract_path.name, "--run-spec", run_spec.name,
        ],
        cwd=repo,
        env=env,
    )
    payload = json.loads(completed.stdout)
    assert completed.returncode == 2
    assert payload["aggregate_status"] == "CAS_BLOCKED"
    assert payload["claim_promotion_cas_eligible"] is False
    assert "reduced axis sets" in json.dumps(payload)


# --- 11 ----------------------------------------------------------------
def test_cas_exception_must_be_preregistered_and_not_self_approved(
    tmp_path: Path,
) -> None:
    repo = _init_tmp_repo(tmp_path)
    contract_path = _write_contract(repo)
    contract = json.loads(contract_path.read_text(encoding="utf-8"))

    def adjudicate(exception: dict):
        contract["exceptions_adjudication"]["preregistered_exceptions"] = [exception]
        contract_path.write_text(
            json.dumps(contract, indent=2) + "\n", encoding="utf-8"
        )
        sha = _sha256(contract_path)
        axes = ("wolfram_xact", "sympy", "sage_singular")
        results = [_axis_result(repo, axis, sha) for axis in axes]
        results.append(
            _axis_result(
                repo, "lean", sha, status="BLOCKED_PLATFORM_OR_LICENSE"
            )
        )
        return _run(
            [
                sys.executable, _script("cas_gate.py"), "adjudicate",
                "--historical-replay",
                "--contract", contract_path.name,
                "--results", *(r.name for r in results),
            ],
            cwd=repo,
        )

    base = {
        "axis": "lean",
        "reason_class": "platform",
        "bounded_probe": "lean --version -> 127",
        "unique_capability_lost": True,
        "substitute_obligation": "record scope mismatch",
        "claim_downgrade": "no formal-proof credit",
        "expiry_retry": "next host",
    }

    post_hoc = dict(base, approver="adjudicator",
                    registered_at="2026-07-17T23:59:59+00:00")
    completed = adjudicate(post_hoc)
    payload = json.loads(completed.stdout)
    assert payload["aggregate_status"] == "CAS_BLOCKED"
    assert any("post-hoc" in err for err in payload["errors"])

    self_approved = dict(base, approver="cas_lean",
                         registered_at="2026-07-17T00:00:00+00:00")
    completed = adjudicate(self_approved)
    payload = json.loads(completed.stdout)
    assert payload["aggregate_status"] == "CAS_BLOCKED"
    assert any("self-approved" in err for err in payload["errors"])

    valid = dict(base, approver="adjudicator",
                 registered_at="2026-07-17T00:00:00+00:00")
    completed = adjudicate(valid)
    payload = json.loads(completed.stdout)
    assert completed.returncode == 2
    assert payload["aggregate_status"] == "CAS_BLOCKED"
    assert payload["historical_aggregate_status"] == (
        "CAS_PASS_WITH_REGISTERED_EXCEPTION"
    )


# --- 12 ----------------------------------------------------------------
def test_cas_preflight_emits_receipt_per_axis(tmp_path: Path) -> None:
    repo = _init_tmp_repo(tmp_path)
    completed = _run(
        [sys.executable, _script("cas_gate.py"), "preflight", "--axis", "sympy"],
        cwd=repo,
    )
    receipt_path = (
        repo / ".agent-harness" / "receipts" / "cas_preflight" / "sympy.json"
    )
    assert receipt_path.is_file()
    receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
    assert receipt["axis"] == "sympy"
    assert receipt["commands"] and "exit" in receipt["commands"][0]
    assert "NOT claim validation" in receipt["scope"]

    # A missing engine yields a BLOCKED receipt, never a silent skip.
    # Shadow wolframscript with a not-installed stub while keeping git and
    # the rest of PATH intact (the scripts resolve the repo via git).
    override = tmp_path / "override-bin"
    override.mkdir(exist_ok=True)
    stub = override / "wolframscript"
    stub.write_text("#!/bin/sh\nexit 127\n", encoding="utf-8")
    stub.chmod(0o755)
    env = dict(os.environ, PATH=f"{override}:{os.environ.get('PATH', '')}")
    completed = subprocess.run(
        [sys.executable, _script("cas_gate.py"), "preflight", "--axis", "wolfram_xact"],
        cwd=repo,
        env=env,
        text=True,
        capture_output=True,
        check=False,
    )
    assert completed.returncode == 2
    receipt = json.loads(
        (
            repo / ".agent-harness" / "receipts" / "cas_preflight" / "wolfram_xact.json"
        ).read_text(encoding="utf-8")
    )
    assert receipt["status"].startswith("BLOCKED_")


# --- 13 ----------------------------------------------------------------
def test_exact_test_receipt_reuse_and_invalidation(tmp_path: Path) -> None:
    repo = _init_tmp_repo(tmp_path)
    source = repo / "mod.py"
    source.write_text("VALUE = 1\n", encoding="utf-8")
    test_file = repo / "test_mod.py"
    test_file.write_text(
        "import mod\n\ndef test_value():\n    assert mod.VALUE == 1\n",
        encoding="utf-8",
    )
    base = [
        sys.executable, _script("test_receipt.py"),
    ]
    selector_args = [
        "--selector", "test_mod.py",
        "--path", "mod.py",
        "--path", "test_mod.py",
        "--seed", "0",
        "--python", sys.executable,
    ]
    first = _run(base + ["run", *selector_args], cwd=repo)
    assert first.returncode == 0, first.stdout + first.stderr
    assert "PASS" in first.stdout

    second = _run(base + ["run", *selector_args], cwd=repo)
    assert second.returncode == 0
    assert "REUSED" in second.stdout

    check = _run(base + ["check", *selector_args], cwd=repo)
    assert check.returncode == 0

    source.write_text("VALUE = 1  # changed comment\n", encoding="utf-8")
    check = _run(base + ["check", *selector_args], cwd=repo)
    assert check.returncode == 1
    rerun = _run(base + ["run", *selector_args], cwd=repo)
    assert "REUSED" not in rerun.stdout


# --- 14 ----------------------------------------------------------------
def test_context_rebuild_same_content_leaves_tracked_files_unchanged() -> None:
    index_path = REPO_ROOT / ".agent-harness" / "context" / "CONTEXT_INDEX.json"
    pack_path = REPO_ROOT / ".agent-harness" / "generated" / "CONTEXT_PACK.md"
    index_before = index_path.read_bytes()
    pack_before = pack_path.read_bytes()

    completed = _run(
        [sys.executable, _script("build_context_pack.py")], cwd=REPO_ROOT
    )
    assert completed.returncode == 0, completed.stdout + completed.stderr
    assert "Unchanged" in completed.stdout, completed.stdout

    assert index_path.read_bytes() == index_before
    assert pack_path.read_bytes() == pack_before

    # Scope the git check to the two files the builder owns — unrelated
    # working-tree edits elsewhere under context/ must not fail this test.
    status = _run(
        ["git", "status", "--porcelain",
         ".agent-harness/context/CONTEXT_INDEX.json",
         ".agent-harness/generated/CONTEXT_PACK.md"],
        cwd=REPO_ROOT,
    )
    dirty = [
        line
        for line in status.stdout.splitlines()
        if not line.startswith("??")
    ]
    assert dirty == [], f"context rebuild dirtied builder-owned files: {dirty}"


# --- MA-03 strict result-validation kernel ----------------------------
@pytest.mark.parametrize(
    ("mutation", "needle"),
    [
        ("unsealed_change", "assignment_sha256 does not match"),
        ("unknown_claim", "claim_id is not registered"),
        ("foreign_run_claim", "claim_id is not registered"),
        ("duplicate_claim", "claim_ids must be unique"),
    ],
)
def test_ma03_assignment_seal_and_claim_registration_fail_closed(
    tmp_path: Path,
    mutation: str,
    needle: str,
) -> None:
    repo = _init_tmp_repo(tmp_path)
    assignment_path = _register_assignment(repo)
    if mutation == "unsealed_change":
        assignment = json.loads(assignment_path.read_text(encoding="utf-8"))
        assignment["task"] = "changed after registration"
        assignment_path.write_text(json.dumps(assignment) + "\n", encoding="utf-8")
    elif mutation == "unknown_claim":
        _reseal_assignment(
            assignment_path,
            lambda assignment: assignment.update(claim_ids=["C-UNKNOWN"]),
        )
    elif mutation == "foreign_run_claim":
        _reseal_assignment(
            assignment_path,
            lambda assignment: assignment.update(claim_ids=["RUN-other-run-AUDIT"]),
        )
    else:
        _reseal_assignment(
            assignment_path,
            lambda assignment: assignment.update(claim_ids=["C-001", "C-001"]),
        )

    completed = _harness_cli(repo, "validate_harness.py")
    assert completed.returncode == 1
    assert needle in completed.stdout + completed.stderr


def test_ma03_result_remains_bound_to_the_original_assignment(tmp_path: Path) -> None:
    empty_context_sha = hashlib.sha256(b"").hexdigest()
    repo = _init_tmp_repo(tmp_path, context_version=empty_context_sha)
    assignment_path = _register_assignment(repo)
    _write_result(repo, "A-001", {})
    _reseal_assignment(
        assignment_path,
        lambda assignment: assignment.update(task="changed after result"),
    )

    completed = _harness_cli(repo, "validate_harness.py")
    assert completed.returncode == 1
    assert "result assignment_sha256 does not match" in completed.stdout


def test_ma03_assignment_inputs_must_stay_canonical_and_repo_relative(
    tmp_path: Path,
) -> None:
    repo = _init_tmp_repo(tmp_path)
    outside = tmp_path / "outside.txt"
    outside.write_text("must not be registered\n", encoding="utf-8")
    completed = _run(
        [
            sys.executable,
            _script("new_assignment.py"),
            "--assignment-id",
            "A-ESCAPE",
            "--agent-type",
            "context_mapper",
            "--task",
            "bounded test task",
            "--risk-tier",
            "R1",
            "--claim-id",
            "C-001",
            "--required-input",
            "../outside.txt",
            "--allowed-tool",
            "read",
            "--required-output",
            "result envelope",
        ],
        cwd=repo,
    )
    assert completed.returncode != 0
    assert "path must be canonical and repository-relative" in (
        completed.stdout + completed.stderr
    )


def test_ma03_live_input_explicitly_downgrades_exact_replay(
    tmp_path: Path,
) -> None:
    empty_context_sha = hashlib.sha256(b"").hexdigest()
    repo = _init_tmp_repo(tmp_path, context_version=empty_context_sha)
    assignment_path = _register_assignment(repo, live_input=True)
    assignment = json.loads(assignment_path.read_text(encoding="utf-8"))
    assert assignment["required_inputs"] == [{"path": "input.txt"}]

    (repo / "input.txt").write_text("scientifically equivalent revision\n")
    completed = _harness_cli(repo, "validate_harness.py")
    assert completed.returncode == 0
    assert "hash mismatch" not in completed.stdout + completed.stderr


def test_ma03_run_local_question_does_not_inflate_claim_registry(
    tmp_path: Path,
) -> None:
    repo = _init_tmp_repo(tmp_path)
    completed = _run(
        [
            sys.executable,
            _script("new_assignment.py"),
            "--assignment-id",
            "A-RUN-LOCAL",
            "--agent-type",
            "context_mapper",
            "--task",
            "bounded process review",
            "--risk-tier",
            "R1",
            "--claim-id",
            "RUN-run-1-MA03-EXACTNESS",
            "--required-input",
            "input.txt",
            "--allowed-tool",
            "read",
            "--required-output",
            "result envelope",
        ],
        cwd=repo,
    )
    assert completed.returncode == 0, completed.stdout + completed.stderr
    registry = (
        repo / ".agent-harness" / "context" / "CLAIM_REGISTRY.jsonl"
    ).read_text(encoding="utf-8")
    assert "RUN-run-1-MA03-EXACTNESS" not in registry


def test_ma03_run_local_question_cannot_enter_cross_run_ledger(
    tmp_path: Path,
) -> None:
    repo = _init_tmp_repo(tmp_path)
    merged = repo / "run-local-merged.json"
    merged.write_text(
        json.dumps(
            {
                "findings": [
                    {
                        "claim_id": "RUN-run-1-MA03-EXACTNESS",
                        "evidence_fingerprint": "scope:ma03-exactness",
                        "verdict": "fail",
                        "statement": "Run-local process finding.",
                    }
                ]
            }
        )
        + "\n",
        encoding="utf-8",
    )
    completed = _harness_cli(
        repo,
        "finding_ledger.py",
        "record",
        "--merged",
        merged.name,
        "--resolution-commit",
        "deadbeef",
    )
    assert completed.returncode != 0
    assert "cannot enter the cross-run finding ledger" in (
        completed.stdout + completed.stderr
    )
    ledger = repo / ".agent-harness" / "ledger" / "FINDING_LEDGER.jsonl"
    assert not ledger.exists() or "RUN-" not in ledger.read_text(encoding="utf-8")


@pytest.mark.parametrize("consumer", ["stop_hook", "merge", "standalone"])
def test_ma03_all_result_consumers_share_strict_rejection(
    tmp_path: Path,
    consumer: str,
) -> None:
    repo = _init_tmp_repo(tmp_path)
    _register_assignment(repo)
    _write_result(repo, "A-001", {"claim_results": []})

    completed, output = _run_result_consumer(repo, consumer, _result_envelope())
    if consumer == "stop_hook":
        assert json.loads(completed.stdout)["decision"] == "block"
    elif consumer == "merge":
        assert completed.returncode != 0
    else:
        assert completed.returncode == 1

    assert "claim_results must cover every assigned claim exactly once" in output


@pytest.mark.parametrize("consumer", ["stop_hook", "merge", "standalone"])
def test_ma03_all_result_consumers_reject_missing_finding_severity(
    tmp_path: Path,
    consumer: str,
) -> None:
    repo = _init_tmp_repo(tmp_path)
    _register_assignment(repo)
    result_path = _write_result(repo, "A-001", {})
    result = json.loads(result_path.read_text(encoding="utf-8"))
    result["findings"][0].pop("severity")
    result_path.write_text(json.dumps(result) + "\n", encoding="utf-8")

    completed, output = _run_result_consumer(repo, consumer, _result_envelope())
    if consumer == "stop_hook":
        assert json.loads(completed.stdout)["decision"] == "block"
    else:
        assert completed.returncode != 0
    assert "severity must be one of" in output


@pytest.mark.parametrize("consumer", ["stop_hook", "merge", "standalone"])
def test_ma03_artifacts_cannot_bypass_blind_sibling_isolation(
    tmp_path: Path,
    consumer: str,
) -> None:
    repo = _init_tmp_repo(tmp_path)
    _register_assignment(repo, "A-001")
    _register_assignment(repo, "A-002")
    sibling = _write_result(repo, "A-002", {})
    sibling_ref = sibling.relative_to(repo).as_posix()
    artifact = {
        "path": sibling_ref,
        "sha256": hashlib.sha256(sibling.read_bytes()).hexdigest(),
        "bytes": sibling.stat().st_size,
        "producer": "test",
        "command_fingerprint": "sha256:" + "6" * 64,
    }
    _write_result(repo, "A-001", {"artifacts": [artifact]})

    completed, output = _run_result_consumer(repo, consumer, _result_envelope())
    if consumer == "stop_hook":
        assert json.loads(completed.stdout)["decision"] == "block"
    else:
        assert completed.returncode != 0
    assert "blind-results violation: unallowed sibling result" in output


@pytest.mark.parametrize(
    ("mutation", "needle"),
    [
        ("empty_claim_results", "cover every assigned claim exactly once"),
        ("pass_with_errors", "pass result must not contain reported errors"),
        ("pass_with_fail_finding", "pass result must not contain a fail finding"),
        ("pass_with_inconclusive", "pass result must contain only pass findings"),
        ("fail_without_fail_finding", "fail result must contain at least one"),
        ("missing_fingerprint", "requires a bounded stable evidence_fingerprint"),
        ("invalid_fingerprint", "requires a bounded stable evidence_fingerprint"),
        ("unbound_no_findings", "evidence_refs must not be empty"),
    ],
)
def test_ma03_incomplete_or_ambiguous_results_fail_closed(
    tmp_path: Path,
    mutation: str,
    needle: str,
) -> None:
    repo = _init_tmp_repo(tmp_path)
    _register_assignment(repo)
    result_path = _write_result(repo, "A-001", {})
    result = json.loads(result_path.read_text(encoding="utf-8"))
    if mutation == "empty_claim_results":
        result["claim_results"] = []
    elif mutation == "pass_with_errors":
        result["errors"] = ["self-reported execution error"]
    elif mutation == "pass_with_fail_finding":
        result["findings"][0]["verdict"] = "fail"
    elif mutation == "pass_with_inconclusive":
        result["findings"][0]["verdict"] = "inconclusive"
    elif mutation == "fail_without_fail_finding":
        result["status"] = "fail"
    elif mutation == "unbound_no_findings":
        result["findings"] = []
        result["claim_results"] = [
            {
                "claim_id": "C-001",
                "outcome": "examined_no_findings",
                "finding_ids": [],
                "summary": "Unbound no-findings assertion.",
                "evidence_refs": [],
            }
        ]
    elif mutation == "missing_fingerprint":
        result["findings"][0].pop("evidence_fingerprint")
    else:
        result["findings"][0]["evidence_fingerprint"] = "invalid\nidentity"
    result_path.write_text(json.dumps(result) + "\n", encoding="utf-8")

    completed = _harness_cli(repo, "validate_harness.py")
    assert completed.returncode == 1
    assert needle in completed.stdout + completed.stderr


def test_ma03_typed_no_findings_is_a_complete_positive_result(tmp_path: Path) -> None:
    empty_context_sha = hashlib.sha256(b"").hexdigest()
    repo = _init_tmp_repo(tmp_path, context_version=empty_context_sha)
    _register_assignment(repo)
    result_path = _write_result(repo, "A-001", {"findings": []})
    result = json.loads(result_path.read_text(encoding="utf-8"))
    assert result["claim_results"] == [
        {
            "claim_id": "C-001",
            "outcome": "examined_no_findings",
            "finding_ids": [],
            "summary": "Disposable terminal claim disposition.",
            "evidence_refs": ["input.txt"],
        }
    ]
    assert (
        _stop_hook(
            repo, _result_envelope(context_version=empty_context_sha)
        ).stdout.strip()
        == ""
    )
    assert _harness_cli(repo, "validate_harness.py").returncode == 0
    assert _harness_cli(repo, "merge_results.py").returncode == 0
    merged = json.loads(
        (
            repo / ".agent-harness" / "runs" / "run-1" / "MERGED_RESULTS.json"
        ).read_text(encoding="utf-8")
    )
    assert merged["process_status"] == "STRUCTURALLY_VALID"
    assert merged["claim_gate_status"] == "NOT_EVALUATED"


@pytest.mark.parametrize(
    ("mutation", "needle"),
    [
        ("hash", "sha256 does not match artifact bytes"),
        ("size", "bytes does not match artifact size"),
        ("command", "command_fingerprint must be a bounded stable identity"),
        ("escape", "must stay inside the repository"),
    ],
)
def test_ma03_artifact_references_are_content_verified(
    tmp_path: Path,
    mutation: str,
    needle: str,
) -> None:
    repo = _init_tmp_repo(tmp_path)
    _register_assignment(repo)
    artifact = repo / "artifact.bin"
    artifact.write_bytes(b"verified artifact\n")
    reference = {
        "path": "artifact.bin",
        "sha256": hashlib.sha256(artifact.read_bytes()).hexdigest(),
        "bytes": artifact.stat().st_size,
        "producer": "test",
    }
    if mutation == "hash":
        reference["sha256"] = "0" * 64
    elif mutation == "size":
        reference["bytes"] += 1
    elif mutation == "command":
        reference["command_fingerprint"] = "invalid\nidentity"
    else:
        reference["path"] = "../outside.bin"
    _write_result(repo, "A-001", {"artifacts": [reference]})

    completed = _harness_cli(repo, "validate_harness.py")
    assert completed.returncode == 1
    assert needle in completed.stdout + completed.stderr


def test_ma03_artifact_command_identity_is_optional(tmp_path: Path) -> None:
    empty_context_sha = hashlib.sha256(b"").hexdigest()
    repo = _init_tmp_repo(tmp_path, context_version=empty_context_sha)
    _register_assignment(repo)
    artifact = repo / "artifact.bin"
    artifact.write_bytes(b"verified artifact\n")
    reference = {
        "path": "artifact.bin",
        "sha256": hashlib.sha256(artifact.read_bytes()).hexdigest(),
        "bytes": artifact.stat().st_size,
        "producer": "test",
    }
    _write_result(repo, "A-001", {"artifacts": [reference]})

    completed = _harness_cli(repo, "validate_harness.py")
    assert completed.returncode == 0, completed.stdout + completed.stderr


def test_ma03_evidence_store_rejects_a_poisoned_existing_blob(tmp_path: Path) -> None:
    repo = _init_tmp_repo(tmp_path)
    source = repo / "raw.log"
    source.write_bytes(b"expected raw evidence\n")
    digest = hashlib.sha256(source.read_bytes()).hexdigest()
    blob = repo / ".agent-harness" / "evidence" / "sha256" / digest[:2] / digest
    blob.parent.mkdir(parents=True)
    blob.write_bytes(b"poisoned bytes\n")

    completed = _harness_cli(
        repo,
        "evidence_store.py",
        "put",
        source.name,
        "--producer",
        "test",
    )
    assert completed.returncode != 0
    assert "content-addressed evidence blob is poisoned" in (
        completed.stdout + completed.stderr
    )


def test_ma03_launch_evidence_cannot_self_promote_to_platform_authentication(
    tmp_path: Path,
) -> None:
    repo = _init_tmp_repo(tmp_path)
    _register_assignment(repo)
    receipt = _create_receipt(repo)
    assert receipt["evidence_origin"] == "self_declared"
    _write_result(repo, "A-001", {})
    envelope = {**_result_envelope(), "launch_id": receipt["launch_id"]}
    assert _stop_hook(repo, envelope).stdout.strip() == ""

    receipt_path = (
        repo / ".agent-harness" / "runs" / "run-1" / "launches" / "A-001.json"
    )
    receipt["evidence_origin"] = "platform_authenticated"
    receipt_path.write_text(json.dumps(receipt) + "\n", encoding="utf-8")
    completed = _stop_hook(repo, envelope)
    payload = json.loads(completed.stdout)
    assert payload["decision"] == "block"
    assert "platform-owned verifier" in payload["reason"]


@pytest.mark.parametrize(
    ("mutation", "needle"),
    [
        ("profile", "does not match assigned agent_type"),
        ("fork", "fork_mode does not match"),
        ("sandbox", "sandbox does not match installed profile"),
        ("delivery", "context_delivery_mode is invalid"),
        ("attested_type", "attested must be boolean"),
    ],
)
def test_ma03_launch_receipt_binds_assignment_execution_fields(
    tmp_path: Path,
    mutation: str,
    needle: str,
) -> None:
    repo = _init_tmp_repo(tmp_path)
    _register_assignment(repo)
    receipt = _create_receipt(repo)
    _write_result(repo, "A-001", {})
    if mutation == "profile":
        receipt["requested_profile"] = "cas_sympy"
        receipt["actual_profile"] = "cas_sympy"
    elif mutation == "fork":
        receipt["fork_mode"] = "all"
    elif mutation == "sandbox":
        receipt["sandbox"] = "read-only"
    elif mutation == "delivery":
        receipt["context_delivery_mode"] = "side_channel"
    else:
        receipt["attested"] = "yes"
    receipt_path = (
        repo / ".agent-harness" / "runs" / "run-1" / "launches" / "A-001.json"
    )
    receipt_path.write_text(json.dumps(receipt) + "\n", encoding="utf-8")

    envelope = {**_result_envelope(), "launch_id": receipt["launch_id"]}
    completed = _stop_hook(repo, envelope)
    payload = json.loads(completed.stdout)
    assert payload["decision"] == "block"
    assert needle in payload["reason"]


def test_ma03_historical_merge_is_read_only(tmp_path: Path) -> None:
    repo = _init_tmp_repo(tmp_path)
    historical = repo / ".agent-harness" / "HISTORICAL_RUNS.json"
    historical.write_text(
        json.dumps({"schema_version": 1, "runs": ["run-1"]}) + "\n",
        encoding="utf-8",
    )
    merged = repo / ".agent-harness" / "runs" / "run-1" / "MERGED_RESULTS.json"
    sentinel = b'{"historical":"frozen"}\n'
    merged.write_bytes(sentinel)

    completed = _harness_cli(repo, "merge_results.py")
    assert completed.returncode != 0
    assert "read-only" in completed.stdout + completed.stderr
    assert merged.read_bytes() == sentinel
