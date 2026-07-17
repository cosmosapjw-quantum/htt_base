"""PR-124 preflight acceptance tests (audit §10 items 1-14).

Each test maps 1:1 to a numbered acceptance criterion in
docs/audits/shared_context_cas_harness_final_audit_20260717/
FINAL_AUDIT_AND_REPAIR_RECOMMENDATION.md §10. Tests run the real harness
scripts and hooks as subprocesses against a disposable git repo under
tmp_path (the scripts resolve their data root via `git rev-parse
--show-toplevel`), so enforcement is exercised end-to-end, not via mocks.
"""
from __future__ import annotations

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


def _run(cmd: list[str], cwd: Path, input_text: str | None = None):
    return subprocess.run(
        cmd, cwd=cwd, input=input_text, text=True, capture_output=True, check=False
    )


def _script(name: str) -> str:
    return str(SCRIPTS / name)


def _init_tmp_repo(tmp_path: Path) -> Path:
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
        "context_version": CONTEXT_VERSION,
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
    (repo / ".agent-harness" / "generated" / "CONTEXT_PACK.md").write_text(
        "# Canonical Shared Context Pack\ncontent\n", encoding="utf-8"
    )
    (repo / ".agent-harness" / "ACTIVE_RUN").write_text("run-1\n", encoding="utf-8")
    run_dir = repo / ".agent-harness" / "runs" / "run-1"
    for sub in ("assignments", "results", "launches"):
        (run_dir / sub).mkdir(parents=True)
    plan = {
        "schema_version": 1,
        "run_id": "run-1",
        "work_unit_id": "PR-TEST",
        "context_version": CONTEXT_VERSION,
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


def _register_assignment(repo: Path, assignment_id: str = "A-001") -> Path:
    completed = _run(
        [
            sys.executable,
            _script("new_assignment.py"),
            "--assignment-id", assignment_id,
            "--agent-type", "context_mapper",
            "--task", "bounded test task",
            "--risk-tier", "R1",
            "--claim-id", "C-001",
            "--required-input", "input.txt",
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

    # (b) required input bytes drift after sealing
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
    result = {
        "schema_version": 1,
        "run_id": "run-1",
        "assignment_id": assignment_id,
        "context_version": CONTEXT_VERSION,
        "agent_type": "context_mapper",
        "status": "pass",
        "findings": [
            {
                "finding_id": "F-001",
                "claim_id": "C-001",
                "verdict": "pass",
                "evidence_fingerprint": "sha256:" + "1" * 64,
            }
        ],
        "errors": [],
    }
    result.update(extra)
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
    assert "Blind-results violation" in payload["reason"]

    # The same read is accepted once explicitly allowed by the assignment.
    assignment_path = (
        repo / ".agent-harness" / "runs" / "run-1" / "assignments" / "A-001.json"
    )
    assignment = json.loads(assignment_path.read_text(encoding="utf-8"))
    assignment["allowed_sibling_results"] = [sibling]
    assignment_path.write_text(json.dumps(assignment) + "\n", encoding="utf-8")
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
    assert "Duplicate-delivery violation" in payload["reason"]


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
    fingerprint = "sha256:" + "2" * 64
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
def test_cas_aggregate_requires_all_four_axes(tmp_path: Path) -> None:
    repo = _init_tmp_repo(tmp_path)
    contract = _write_contract(repo)
    sha = _sha256(contract)
    axes = ("wolfram_xact", "sympy", "sage_singular", "lean")
    results = [_axis_result(repo, axis, sha) for axis in axes]

    completed = _run(
        [
            sys.executable, _script("cas_gate.py"), "adjudicate",
            "--contract", contract.name, "--results", *(r.name for r in results),
        ],
        cwd=repo,
    )
    assert completed.returncode == 0
    assert json.loads(completed.stdout)["aggregate_status"] == "CAS_4AXIS_PASS"

    completed = _run(
        [
            sys.executable, _script("cas_gate.py"), "adjudicate",
            "--contract", contract.name,
            "--results", *(r.name for r in results[:3]),
        ],
        cwd=repo,
    )
    assert completed.returncode == 2
    payload = json.loads(completed.stdout)
    assert payload["aggregate_status"] == "CAS_BLOCKED"
    assert payload["missing_axes"] == ["lean"]


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
    assert payload["aggregate_status"] == "CAS_PASS_WITH_REGISTERED_EXCEPTION"


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
