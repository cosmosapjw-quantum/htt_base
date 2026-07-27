from __future__ import annotations

import hashlib
import importlib.util
import json
import shutil
import subprocess
import sys
import tomllib
from pathlib import Path

import pytest


REPO_ROOT = Path(__file__).resolve().parents[2]
REQUIRED_AGENT_NAMES = {
    "adjudicator",
    "cas_lean",
    "cas_sage_singular",
    "cas_sympy",
    "cas_wolfram_xact",
    "claim_gate_reviewer",
    "claim_lane_reviewer",
    "code_cartographer",
    "context_mapper",
    "convergence_director",
    "docs_citation_auditor",
    "harness_engineer",
    "physics_stat_auditor",
    "regression_tester",
    "web_crag_researcher",
}
REQUIRED_SKILL_NAMES = {
    "htt-dag-orchestrator",
    "htt-harness-engineering",
    "htt-physmath-audit",
}
READ_ONLY_AGENT_NAMES = {
    "claim_gate_reviewer",
    "claim_lane_reviewer",
    "code_cartographer",
    "convergence_director",
    "docs_citation_auditor",
    "harness_engineer",
    "physics_stat_auditor",
    "web_crag_researcher",
}
REQUIRED_INSTALL_SNIPPETS = {
    "AGENTS.md",
    ".agents/skills",
    ".codex/agents",
    ".codex/rules/default.rules",
    "python scripts/codex_harness/verify_skill_layout.py .",
    "codex execpolicy check --pretty --rules .codex/rules/default.rules -- python -m pytest -q",
    "python scripts/codex_harness/validate_codex_config_shape.py .",
    "Do not copy these files into user-global Codex locations",
}


def _run_codex_policy(command: list[str]) -> subprocess.CompletedProcess[str]:
    codex = shutil.which("codex")
    if codex is None:
        pytest.skip(
            "Codex CLI executable not installed; cannot validate execpolicy rules"
        )
    return subprocess.run(
        [
            codex,
            "execpolicy",
            "check",
            "--pretty",
            "--rules",
            str(REPO_ROOT / ".codex" / "rules" / "default.rules"),
            "--",
            *command,
        ],
        cwd=REPO_ROOT,
        text=True,
        capture_output=True,
        check=False,
    )


def _strictest_decision(output: str) -> str:
    payload = json.loads(output)
    decision = payload.get("decision") or payload.get("strictest_decision")
    assert isinstance(decision, str), payload
    return decision


def _skill_names(root: Path) -> set[str]:
    return {
        path.parent.name for path in (root / ".agents" / "skills").glob("*/SKILL.md")
    }


def _reported_skill_names(output: str) -> set[str]:
    return {
        line.removeprefix("- ").strip()
        for line in output.splitlines()
        if line.startswith("- ")
    }


def test_agents_md_stays_terse_and_names_repo_boundaries() -> None:
    agents_md = REPO_ROOT / "AGENTS.md"
    assert agents_md.exists()
    assert agents_md.stat().st_size < 32 * 1024
    text = agents_md.read_text(encoding="utf-8")
    for snippet in [
        "Do not implement or simulate the future external low-ell Bianchi Boltzmann solver",
        "MIO owns model-family-independent diagnostics",
        "HTT owns model-dependent likelihoods",
        "Bianchi family identified",
    ]:
        assert snippet in text


def test_repo_scoped_skill_layout_is_valid() -> None:
    completed = subprocess.run(
        [sys.executable, "scripts/codex_harness/verify_skill_layout.py", "."],
        cwd=REPO_ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    assert completed.returncode == 0, completed.stdout + completed.stderr
    expected = _skill_names(REPO_ROOT)
    assert REQUIRED_SKILL_NAMES <= expected
    assert f"{len(expected)} skills OK" in completed.stdout
    assert _reported_skill_names(completed.stdout) == expected


def test_shared_context_packet_is_merged_and_versioned() -> None:
    fragment = (REPO_ROOT / "AGENTS.md.fragment").read_text(encoding="utf-8").strip()
    agents_text = (REPO_ROOT / "AGENTS.md").read_text(encoding="utf-8").strip()
    assert fragment
    assert agents_text.endswith(fragment)
    assert agents_text.count(fragment) == 1
    assert "fragment has no independent authority" in fragment
    assert "canonical `docs/codex_handoff/pr_status.yaml`" in agents_text
    assert (
        "`docs/codex_handoff/pr_backlog.yaml` or "
        "`machine_readable/pr_backlog.yaml`"
    ) not in agents_text

    compatibility = (REPO_ROOT / "CLAUDE.md").read_text(encoding="utf-8")
    assert len(compatibility) < 8192
    assert "SSoT Master" not in compatibility
    assert "Update this file at the end of every session" not in compatibility
    for pointer in (
        "AGENTS.md",
        ".agent-harness/context/CONTEXT_INDEX.json",
        ".agent-harness/generated/CONTEXT_PACK.md",
        "docs/codex_handoff/pr_backlog.yaml",
        "docs/codex_handoff/pr_status.yaml",
    ):
        assert pointer in compatibility
    assert "TCA pre-phase" in compatibility
    section5 = compatibility.split(
        "## 5. Physics-parameter compatibility anchors", 1
    )[1].split("## 6. Compatibility prohibitions", 1)[0]
    for anchor in (
        "ln B(FLRW_tilt)=+26.40",
        "β=1.360e-3",
        "F_Bayes=0.093±0.025",
        "D_2=1002.086744",
    ):
        assert anchor in section5

    index = json.loads(
        (REPO_ROOT / ".agent-harness/context/CONTEXT_INDEX.json").read_text(
            encoding="utf-8"
        )
    )
    assert index["shared_files"] == index["pack_files"] == [
        ".agent-harness/context/SYMBOLS.md",
        ".agent-harness/context/FROZEN_DECISIONS.md",
    ]
    assert not set(index["shared_files"]) & set(index["reference_only_files"])

    historical = (
        REPO_ROOT / ".agent-harness/context/SHARED_CONTEXT.md"
    ).read_text(encoding="utf-8")
    assert len(historical) < 1024
    assert "no longer carries global scientific or execution authority" in historical
    readme = (REPO_ROOT / ".agent-harness/README.md").read_text(encoding="utf-8")
    contract_template = (
        REPO_ROOT / ".agent-harness/templates/CAS_CONTRACT.json"
    ).read_text(encoding="utf-8")
    assert "--required-input .agent-harness/context/SHARED_CONTEXT.md" not in readme
    assert ".agent-harness/context/SHARED_CONTEXT.md" not in contract_template
    assert "REPLACE_WITH_GOVERNING_SPEC_PATH" in contract_template

    scientific_contract = (
        REPO_ROOT / "harness/physmath-coding-gpt56/SCIENTIFIC_CONTRACT.md"
    ).read_text(encoding="utf-8")
    research_state = (
        REPO_ROOT / "harness/physmath-research-gpt56/state/RESEARCH_STATE.md"
    ).read_text(encoding="utf-8")
    assert "SSoT authority:" not in scientific_contract
    assert "on conflict those win" not in scientific_contract
    assert "non-authoritative compatibility index" in scientific_contract
    assert "execution status: docs/codex_handoff/pr_status.yaml" in research_state

    config = tomllib.loads(
        (REPO_ROOT / ".codex/config.toml").read_text(encoding="utf-8")
    )
    assert config["project_doc_max_bytes"] == 65536
    assert config["approvals_reviewer"] == "user"
    assert config["features"]["hooks"] is True
    assert config["agents"] == {
        "max_threads": 4,
        "max_depth": 2,
        "job_max_runtime_seconds": 1800,
    }

    hooks = json.loads((REPO_ROOT / ".codex/hooks.json").read_text(encoding="utf-8"))
    assert set(hooks["hooks"]) == {
        "SessionStart",
        "SubagentStart",
        "SubagentStop",
        "PreToolUse",
    }


def test_shared_context_harness_and_stop_hook_fail_closed(tmp_path: Path) -> None:
    validated = subprocess.run(
        [sys.executable, ".agent-harness/scripts/validate_harness.py"],
        cwd=REPO_ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    assert validated.returncode == 0, validated.stdout + validated.stderr
    assert json.loads(validated.stdout)["ok"] is True

    harness = tmp_path / ".agent-harness"
    (harness / "context").mkdir(parents=True)
    (harness / "runtime").mkdir(parents=True)
    (tmp_path / ".codex" / "agents").mkdir(parents=True)
    (tmp_path / ".codex" / "agents" / "context_mapper.toml").write_text(
        'name = "context_mapper"\ndescription = "test profile"\n'
        'sandbox_mode = "read-only"\n',
        encoding="utf-8",
    )
    (harness / "runtime" / "ACTIVE_RUN").write_text(
        "test-run\n", encoding="utf-8"
    )
    (harness / "context/CONTEXT_INDEX.json").write_text(
        json.dumps({"context_version": "test-version"}) + "\n",
        encoding="utf-8",
    )
    (harness / "context/CLAIM_REGISTRY.jsonl").write_text(
        json.dumps({"claim_id": "C-001", "statement": "Test claim."}) + "\n",
        encoding="utf-8",
    )
    context_index = harness / "context/CONTEXT_INDEX.json"
    assignment = {
        "schema_version": 2,
        "run_id": "test-run",
        "assignment_id": "A-001",
        "agent_type": "context_mapper",
        "context_version": "test-version",
        "independence_mode": "shared-core",
        "discovery_mode": "targeted",
        "independence_rationale": None,
        "risk_tier": "R1",
        "claim_ids": ["C-001"],
        "required_inputs": [
            {
                "path": ".agent-harness/context/CONTEXT_INDEX.json",
                "sha256": hashlib.sha256(context_index.read_bytes()).hexdigest(),
            }
        ],
        "allowed_tools": ["read"],
        "required_outputs": ["result envelope"],
        "allowed_sibling_results": [],
        "result_path": ".agent-harness/runs/test-run/results/A-001.json",
    }
    assignment["assignment_sha256"] = hashlib.sha256(
        json.dumps(assignment, sort_keys=True, ensure_ascii=False).encode("utf-8")
    ).hexdigest()
    assignment_path = harness / "runs/test-run/assignments/A-001.json"
    assignment_path.parent.mkdir(parents=True)
    (harness / "runs/test-run/RUN_PLAN.json").write_text(
        json.dumps({"run_id": "test-run"}) + "\n", encoding="utf-8"
    )
    assignment_path.write_text(json.dumps(assignment) + "\n", encoding="utf-8")
    blocked = subprocess.run(
        [sys.executable, str(REPO_ROOT / ".codex/hooks/subagent_stop_validate.py")],
        cwd=tmp_path,
        input=json.dumps({"last_assistant_message": "missing envelope"}),
        text=True,
        capture_output=True,
        check=False,
    )
    assert blocked.returncode == 0, blocked.stdout + blocked.stderr
    assert json.loads(blocked.stdout)["decision"] == "block"
    assert "HARNESS_RESULT" in json.loads(blocked.stdout)["reason"]

    result = harness / "runs/test-run/results/A-001.json"
    result.parent.mkdir(parents=True)
    result_payload = {
        "schema_version": 2,
        "run_id": "test-run",
        "assignment_id": "A-001",
        "context_version": "test-version",
        "agent_type": "context_mapper",
        "independence_mode": "shared-core",
        "status": "pass",
        "result_path": ".agent-harness/runs/test-run/results/A-001.json",
        "assignment_sha256": assignment["assignment_sha256"],
        "launch_id": None,
        "launch_evidence": "unverified",
        "execution_evidence": "self_declared",
        "files_read": [".agent-harness/context/CONTEXT_INDEX.json"],
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
                "statement": "Test finding.",
                "assumptions_used": [],
                "evidence_refs": [
                    ".agent-harness/context/CONTEXT_INDEX.json"
                ],
                "evidence_fingerprint": "sha256:" + "1" * 64,
                "counterevidence_refs": [],
                "reproduction": [],
                "confidence": 1.0,
                "unresolved": [],
            }
        ],
        "claim_results": [
            {
                "claim_id": "C-001",
                "outcome": "findings_present",
                "finding_ids": ["F-001"],
                "summary": "Test claim disposition.",
            }
        ],
        "errors": [],
    }
    result.write_text(json.dumps(result_payload) + "\n", encoding="utf-8")
    marker = {
        "assignment_id": "A-001",
        "context_version": "test-version",
        "status": "pass",
        "result_path": ".agent-harness/runs/test-run/results/A-001.json",
    }
    accepted = subprocess.run(
        [sys.executable, str(REPO_ROOT / ".codex/hooks/subagent_stop_validate.py")],
        cwd=tmp_path,
        input=json.dumps(
            {"last_assistant_message": f"HARNESS_RESULT: {json.dumps(marker)}"}
        ),
        text=True,
        capture_output=True,
        check=False,
    )
    assert accepted.returncode == 0, accepted.stdout + accepted.stderr
    assert accepted.stdout == ""

    unregistered_result = harness / "runs/test-run/results/A-404.json"
    unregistered_result.write_text(
        json.dumps(
            {
                **result_payload,
                "assignment_id": "A-404",
            }
        )
        + "\n",
        encoding="utf-8",
    )
    unregistered_marker = {
        **marker,
        "assignment_id": "A-404",
        "result_path": ".agent-harness/runs/test-run/results/A-404.json",
    }
    unregistered = subprocess.run(
        [sys.executable, str(REPO_ROOT / ".codex/hooks/subagent_stop_validate.py")],
        cwd=tmp_path,
        input=json.dumps(
            {
                "last_assistant_message": f"HARNESS_RESULT: {json.dumps(unregistered_marker)}"
            }
        ),
        text=True,
        capture_output=True,
        check=False,
    )
    assert json.loads(unregistered.stdout)["decision"] == "block"
    assert "registered assignment" in json.loads(unregistered.stdout)["reason"]

    result.write_text("{}\n", encoding="utf-8")
    empty_result = subprocess.run(
        [sys.executable, str(REPO_ROOT / ".codex/hooks/subagent_stop_validate.py")],
        cwd=tmp_path,
        input=json.dumps(
            {"last_assistant_message": f"HARNESS_RESULT: {json.dumps(marker)}"}
        ),
        text=True,
        capture_output=True,
        check=False,
    )
    assert json.loads(empty_result.stdout)["decision"] == "block"
    assert "Invalid result artifact" in json.loads(empty_result.stdout)["reason"]

    result.write_text(json.dumps(result_payload) + "\n", encoding="utf-8")
    mismatched_marker = {**marker, "status": "fail"}
    mismatched = subprocess.run(
        [sys.executable, str(REPO_ROOT / ".codex/hooks/subagent_stop_validate.py")],
        cwd=tmp_path,
        input=json.dumps(
            {
                "last_assistant_message": f"HARNESS_RESULT: {json.dumps(mismatched_marker)}"
            }
        ),
        text=True,
        capture_output=True,
        check=False,
    )
    assert json.loads(mismatched.stdout)["decision"] == "block"
    assert "status does not match" in json.loads(mismatched.stdout)["reason"]

    unsafe_marker = {
        **marker,
        "assignment_id": "../A-001",
        "result_path": ".agent-harness/runs/test-run/results/A-001.json",
    }
    unsafe = subprocess.run(
        [sys.executable, str(REPO_ROOT / ".codex/hooks/subagent_stop_validate.py")],
        cwd=tmp_path,
        input=json.dumps(
            {"last_assistant_message": f"HARNESS_RESULT: {json.dumps(unsafe_marker)}"}
        ),
        text=True,
        capture_output=True,
        check=False,
    )
    assert json.loads(unsafe.stdout)["decision"] == "block"
    assert "unsafe" in json.loads(unsafe.stdout)["reason"]


def test_shared_context_result_merge_never_collapses_missing_fingerprints(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    scripts = REPO_ROOT / ".agent-harness/scripts"
    monkeypatch.syspath_prepend(str(scripts))
    spec = importlib.util.spec_from_file_location(
        "shared_context_merge_results",
        scripts / "merge_results.py",
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    first = {
        "finding_id": "HARN-001",
        "claim_id": "C-HARNESS-INSTALL",
        "verdict": "fail",
    }
    second = {
        "finding_id": "HARN-002",
        "claim_id": "C-HARNESS-INSTALL",
        "verdict": "fail",
    }
    assert module.canonical_key(first) != module.canonical_key(second)


def test_custom_agent_configs_are_well_formed_and_named() -> None:
    agent_dir = REPO_ROOT / ".codex" / "agents"
    # Fail-closed duplicate detection (PR-124 preflight, audit H1): the old
    # `agents[data["name"]] = data` dict silently let a later file mask an
    # earlier one with the same internal name, which hid a real
    # sandbox_mode conflict between harness-engineer.toml and
    # harness_engineer.toml. Collect rows first, then assert uniqueness.
    rows: list[tuple[str, str, str]] = []
    agents = {}
    for path in sorted(agent_dir.glob("*.toml")):
        data = tomllib.loads(path.read_text(encoding="utf-8"))
        rows.append((data["name"], path.name, data["sandbox_mode"]))
        agents[data["name"]] = data
        assert data["description"]
        assert data["sandbox_mode"] in {"read-only", "workspace-write"}
        assert data["model_reasoning_effort"] in {"low", "medium", "high", "xhigh"}
        assert data["developer_instructions"].strip()
        if "nickname_candidates" in data:
            assert isinstance(data["nickname_candidates"], list)
            assert data["nickname_candidates"]

    names = [name for name, _, _ in rows]
    duplicates = sorted({name for name in names if names.count(name) > 1})
    assert not duplicates, (
        "duplicate agent profile names (one file per name is required): "
        f"{[(n, f, s) for n, f, s in rows if n in duplicates]}"
    )

    assert REQUIRED_AGENT_NAMES <= set(agents)
    for name in READ_ONLY_AGENT_NAMES:
        assert agents[name]["sandbox_mode"] == "read-only"


def test_profile_registry_rejects_duplicates_and_matches_disk() -> None:
    scripts = REPO_ROOT / ".agent-harness/scripts"
    spec = importlib.util.spec_from_file_location(
        "shared_context_profile_registry",
        scripts / "profile_registry.py",
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    registry = module.load_profile_registry(REPO_ROOT)
    assert REQUIRED_AGENT_NAMES <= set(registry)
    toml_files = sorted((REPO_ROOT / ".codex" / "agents").glob("*.toml"))
    assert len(registry) == len(toml_files)

    # Synthetic duplicate with a sandbox conflict must raise.
    import tempfile

    with tempfile.TemporaryDirectory() as tmp:
        agent_dir = Path(tmp) / ".codex" / "agents"
        agent_dir.mkdir(parents=True)
        (agent_dir / "a-dup.toml").write_text(
            'name = "dup_agent"\ndescription = "x"\nsandbox_mode = "workspace-write"\n',
            encoding="utf-8",
        )
        (agent_dir / "dup_agent.toml").write_text(
            'name = "dup_agent"\ndescription = "x"\nsandbox_mode = "read-only"\n',
            encoding="utf-8",
        )
        with pytest.raises(module.ProfileRegistryError, match="duplicate"):
            module.load_profile_registry(Path(tmp))


def test_gitignore_separates_versioned_codex_assets_from_runtime_state() -> None:
    checks = [
        (["git", "check-ignore", "-q", ".codex/agents/code-cartographer.toml"], 1),
        (["git", "check-ignore", "-q", ".codex/rules/default.rules"], 1),
        (["git", "check-ignore", "-q", ".codex/config.toml"], 1),
        (["git", "check-ignore", "-q", ".codex/hooks.json"], 1),
        (["git", "check-ignore", "-q", ".codex/hooks/session_start_context.py"], 1),
        (["git", "check-ignore", "-q", ".agent-harness/runtime/ACTIVE_RUN"], 0),
        (["git", "check-ignore", "-q", ".agent-harness/ACTIVE_RUN"], 0),
    ]
    for command, expected_returncode in checks:
        completed = subprocess.run(
            command,
            cwd=REPO_ROOT,
            text=True,
            capture_output=True,
            check=False,
        )
        assert completed.returncode == expected_returncode, (
            command,
            completed.stdout,
            completed.stderr,
        )

    tracked_pointer = subprocess.run(
        ["git", "ls-files", "--error-unmatch", ".agent-harness/ACTIVE_RUN"],
        cwd=REPO_ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    assert tracked_pointer.returncode == 1, tracked_pointer.stdout


def test_execpolicy_rules_load_and_match_pr_card_commands() -> None:
    pytest_command = _run_codex_policy(["python", "-m", "pytest", "-q"])
    assert pytest_command.returncode == 0, pytest_command.stdout + pytest_command.stderr
    assert _strictest_decision(pytest_command.stdout) == "allow"

    harness_command = _run_codex_policy(
        [
            "python",
            "scripts/codex_harness/validate_pr_dag.py",
            "docs/codex_handoff/pr_backlog.yaml",
        ]
    )
    assert harness_command.returncode == 0, (
        harness_command.stdout + harness_command.stderr
    )
    assert _strictest_decision(harness_command.stdout) == "allow"

    forbidden_command = _run_codex_policy(["rm", "-rf", "/tmp/foo"])
    assert forbidden_command.returncode == 0, (
        forbidden_command.stdout + forbidden_command.stderr
    )
    assert _strictest_decision(forbidden_command.stdout) == "forbidden"


def test_execpolicy_rejects_unmatched_rule_examples(tmp_path: Path) -> None:
    codex = shutil.which("codex")
    if codex is None:
        pytest.skip(
            "Codex CLI executable not installed; cannot validate execpolicy rules"
        )
    bad_rules = tmp_path / "bad.rules"
    bad_rules.write_text(
        """
prefix_rule(
    pattern = ["python", "scripts/codex_harness"],
    decision = "allow",
    justification = "Intentionally bad broad harness prefix.",
    match = ["python scripts/codex_harness/validate_pr_dag.py docs/codex_handoff/pr_backlog.yaml"],
)
""".strip(),
        encoding="utf-8",
    )
    completed = subprocess.run(
        [
            codex,
            "execpolicy",
            "check",
            "--pretty",
            "--rules",
            str(bad_rules),
            "--",
            "python",
            "-m",
            "pytest",
            "-q",
        ],
        cwd=REPO_ROOT,
        text=True,
        capture_output=True,
        check=False,
    )

    assert completed.returncode != 0
    assert "unmatched examples" in completed.stderr


def test_project_codex_config_shape_validator_accepts_supported_globals_and_rejects_bad_agents(
    tmp_path: Path,
) -> None:
    no_config = tmp_path / "no_config"
    no_config.mkdir()
    accepted = subprocess.run(
        [
            sys.executable,
            str(REPO_ROOT / "scripts/codex_harness/validate_codex_config_shape.py"),
            str(no_config),
        ],
        cwd=REPO_ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    assert accepted.returncode == 0, accepted.stdout + accepted.stderr
    assert "no project-local .codex/config.toml present" in accepted.stdout

    good_config = tmp_path / "good_config" / ".codex"
    good_config.mkdir(parents=True)
    (good_config / "config.toml").write_text(
        """
project_doc_max_bytes = 65536
approvals_reviewer = "user"

[features]
hooks = true

[agents]
max_threads = 4
max_depth = 2
job_max_runtime_seconds = 1800
""".lstrip(),
        encoding="utf-8",
    )
    supported = subprocess.run(
        [
            sys.executable,
            str(REPO_ROOT / "scripts/codex_harness/validate_codex_config_shape.py"),
            str(tmp_path / "good_config"),
        ],
        cwd=REPO_ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    assert supported.returncode == 0, supported.stdout + supported.stderr
    assert "supported shared-context harness fields" in supported.stdout

    bad_config = tmp_path / "bad_config" / ".codex"
    bad_config.mkdir(parents=True)
    (bad_config / "config.toml").write_text(
        """
[agents]
max_threads = "many"
""".lstrip(),
        encoding="utf-8",
    )
    rejected = subprocess.run(
        [
            sys.executable,
            str(REPO_ROOT / "scripts/codex_harness/validate_codex_config_shape.py"),
            str(tmp_path / "bad_config"),
        ],
        cwd=REPO_ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    assert rejected.returncode == 1, rejected.stdout + rejected.stderr
    assert "agents.max_threads must be int" in rejected.stdout


def test_installer_copies_repo_scoped_assets_with_project_harness_config(
    tmp_path: Path,
) -> None:
    codex = shutil.which("codex")
    if codex is None:
        pytest.skip(
            "Codex CLI executable not installed; cannot validate installed rules"
        )
    target = tmp_path / "installed"
    target.mkdir(parents=True)
    initialized = subprocess.run(
        ["git", "init", "-q"],
        cwd=target,
        text=True,
        capture_output=True,
        check=False,
    )
    assert initialized.returncode == 0, initialized.stdout + initialized.stderr
    completed = subprocess.run(
        ["bash", "scripts/install_codex_handoff.sh", str(target)],
        cwd=REPO_ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    assert completed.returncode == 0, completed.stdout + completed.stderr
    assert "Installed v4 Codex handoff skillset" in completed.stdout

    for path in [
        "AGENTS.md",
        "AGENTS.md.fragment",
        ".agents/skills/htt-dag-orchestrator/SKILL.md",
        ".codex/agents/code-cartographer.toml",
        ".codex/config.toml",
        ".codex/hooks.json",
        ".codex/hooks/session_start_context.py",
        ".codex/rules/default.rules",
        ".claude/settings.json",
        ".agents/hooks.json",
        ".agents/rules/publication-integrity.md",
        ".prguard/.gitignore",
        ".agent-harness/README.md",
        ".agent-harness/generated/CONTEXT_PACK.md",
        ".agent-harness/scripts/candidate_seal.py",
        ".agent-harness/scripts/pr_inventory.py",
        ".agent-harness/scripts/pr_publication_gate.py",
        ".agent-harness/scripts/provider_publication_hook.py",
        ".agent-harness/scripts/publication_integrity.py",
        ".agent-harness/scripts/validate_harness.py",
        ".agent-harness/templates/CANDIDATE_SEAL.json",
        ".agent-harness/templates/INTEGRATION_RECEIPT.json",
        ".agent-harness/templates/PR_INVENTORY.json",
        ".agent-harness/templates/PUBLISH_AUTHORIZATION.json",
        ".agent-harness/templates/REVIEW_COVERAGE.json",
        ".agent-harness/templates/RESULT_ENVELOPE.json",
        "docs/codex_handoff/pr_backlog.yaml",
        "docs/harness/OVERNIGHT_CONTROLLER_PUBLICATION_CONTRACT.md",
        "docs/harness/PUBLICATION_INTEGRITY.md",
        "docs/research_program/long_horizon_rescue/pr247_publication_policy.json",
        "docs/research_program/long_horizon_rescue/pr247_spec.yaml",
        "scripts/codex_harness/verify_skill_layout.py",
        "harness_templates/vendor/physmath-gpt56/3.1.0/coding/manifest.json",
        "harness_templates/vendor/physmath-gpt56/3.1.0/research/manifest.json",
    ]:
        assert (target / path).exists(), path
    assert (
        target / "docs/codex_handoff/pr_backlog.yaml"
    ).read_bytes() == (
        REPO_ROOT / "docs/codex_handoff/pr_backlog.yaml"
    ).read_bytes()
    for name in (
        "pr_backlog.yaml",
        "pr_backlog.json",
        "pr_status.yaml",
        "authorized_principals.yaml",
        "research_remediation_state.yaml",
    ):
        canonical = target / "docs/codex_handoff" / name
        mirror = target / "machine_readable" / name
        assert canonical.is_file(), name
        assert mirror.is_file(), name
        assert mirror.read_bytes() == canonical.read_bytes(), name
    assert not (target / "docs/codex_handoff/codex_handoff").exists()
    assert not (target / "docs/codex_handoff/PR_DELTAS").exists()
    assert not (target / "docs/codex_handoff/generated").exists()
    assert not (target / ".agent-harness/ACTIVE_RUN").exists()
    assert not (target / ".agent-harness/runtime/ACTIVE_RUN").exists()
    assert not (target / ".agent-harness/runs").exists()

    installed_skills = subprocess.run(
        [
            "python",
            str(target / "scripts/codex_harness/verify_skill_layout.py"),
            str(target),
        ],
        cwd=REPO_ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    assert installed_skills.returncode == 0, (
        installed_skills.stdout + installed_skills.stderr
    )
    expected = _skill_names(REPO_ROOT)
    assert REQUIRED_SKILL_NAMES <= expected
    assert f"{len(expected)} skills OK" in installed_skills.stdout
    assert _reported_skill_names(installed_skills.stdout) == expected

    installed_config = subprocess.run(
        [
            sys.executable,
            str(target / "scripts/codex_harness/validate_codex_config_shape.py"),
            str(target),
        ],
        cwd=target,
        text=True,
        capture_output=True,
        check=False,
    )
    assert installed_config.returncode == 0, (
        installed_config.stdout + installed_config.stderr
    )

    installed_harness = subprocess.run(
        [sys.executable, str(target / ".agent-harness/scripts/validate_harness.py")],
        cwd=target,
        text=True,
        capture_output=True,
        check=False,
    )
    assert installed_harness.returncode == 0, (
        installed_harness.stdout + installed_harness.stderr
    )

    for mode, expected_message in [
        ("coding", "Coding harness validation passed."),
        ("research", "Research harness validation passed."),
    ]:
        validator = (
            "validate_harness.py" if mode == "coding" else "validate_workspace.py"
        )
        validated = subprocess.run(
            [
                sys.executable,
                str(
                    target
                    / "harness_templates/vendor/physmath-gpt56/3.1.0"
                    / mode
                    / "tools"
                    / validator
                ),
            ],
            cwd=target,
            text=True,
            capture_output=True,
            check=False,
        )
        assert validated.returncode == 0, validated.stdout + validated.stderr
        assert expected_message in validated.stdout

    clean_reinstall = subprocess.run(
        ["bash", "scripts/install_codex_handoff.sh", str(target)],
        cwd=REPO_ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    assert clean_reinstall.returncode == 0, (
        clean_reinstall.stdout + clean_reinstall.stderr
    )

    rogue = target / "harness_templates/vendor/physmath-gpt56/3.1.0/coding/ROGUE.txt"
    rogue.write_text("unreceipted\n", encoding="utf-8")
    contaminated = subprocess.run(
        ["bash", "scripts/install_codex_handoff.sh", str(target)],
        cwd=REPO_ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    assert contaminated.returncode == 1
    assert (
        "Refusing to overwrite a divergent physmath vendor snapshot"
        in contaminated.stderr
    )

    installed_policy = subprocess.run(
        [
            codex,
            "execpolicy",
            "check",
            "--pretty",
            "--rules",
            str(target / ".codex/rules/default.rules"),
            "--",
            "python",
            "-m",
            "pytest",
            "-q",
        ],
        cwd=target,
        text=True,
        capture_output=True,
        check=False,
    )
    assert installed_policy.returncode == 0, (
        installed_policy.stdout + installed_policy.stderr
    )
    assert _strictest_decision(installed_policy.stdout) == "allow"


def test_installer_refuses_divergent_merge_only_assets_without_partial_overwrite(
    tmp_path: Path,
) -> None:
    policy_target = tmp_path / "policy-target"
    (policy_target / ".codex").mkdir(parents=True)
    local_policy = "LOCAL_POLICY_MARKER\n"
    local_config = 'model = "intentional-model"\n'
    (policy_target / "AGENTS.md").write_text(local_policy, encoding="utf-8")
    (policy_target / ".codex/config.toml").write_text(
        local_config,
        encoding="utf-8",
    )
    policy_refusal = subprocess.run(
        ["bash", "scripts/install_codex_handoff.sh", str(policy_target)],
        cwd=REPO_ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    assert policy_refusal.returncode == 1
    assert "divergent merge-only asset (AGENTS.md)" in policy_refusal.stderr
    assert (policy_target / "AGENTS.md").read_text(encoding="utf-8") == local_policy
    assert (policy_target / ".codex/config.toml").read_text(
        encoding="utf-8"
    ) == local_config
    assert not (policy_target / "agent.md").exists()

    config_target = tmp_path / "config-target"
    (config_target / ".codex").mkdir(parents=True)
    (config_target / "AGENTS.md").write_bytes((REPO_ROOT / "AGENTS.md").read_bytes())
    (config_target / ".codex/config.toml").write_text(
        local_config,
        encoding="utf-8",
    )
    config_refusal = subprocess.run(
        ["bash", "scripts/install_codex_handoff.sh", str(config_target)],
        cwd=REPO_ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    assert config_refusal.returncode == 1
    assert "divergent merge-only asset (.codex/config.toml)" in config_refusal.stderr
    assert (config_target / ".codex/config.toml").read_text(
        encoding="utf-8"
    ) == local_config
    assert not (config_target / "agent.md").exists()


def test_claim_scanners_handle_explicit_agent_skill_paths(tmp_path: Path) -> None:
    safe_skill = tmp_path / ".agents" / "skills" / "demo" / "SKILL.md"
    safe_skill.parent.mkdir(parents=True)
    safe_skill.write_text(
        """
---
name: demo
description: Demo skill.
---

# Family Identification Demo Heading

This is a DIAGNOSTIC_ONLY skill note.
External AniCLASS transfer cannot be silently described as native solver evidence.
Transfer adapters or AniCLASS/native comparison requires transfer provenance.
""".lstrip(),
        encoding="utf-8",
    )

    forbidden = subprocess.run(
        [
            sys.executable,
            ".agents/skills/htt-claim-provenance-ledger/scripts/check_forbidden_claims.py",
            str(safe_skill),
        ],
        cwd=REPO_ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    assert forbidden.returncode == 0, forbidden.stdout + forbidden.stderr

    status = subprocess.run(
        [
            sys.executable,
            ".agents/skills/htt-claim-provenance-ledger/scripts/check_claim_status.py",
            str(safe_skill),
        ],
        cwd=REPO_ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    assert status.returncode == 0, status.stdout + status.stderr


def test_install_doc_lists_repo_scoped_assets_and_verification_commands() -> None:
    install_doc = REPO_ROOT / "docs" / "codex_handoff" / "INSTALL.md"
    assert install_doc.exists()
    text = install_doc.read_text(encoding="utf-8")
    for snippet in REQUIRED_INSTALL_SNIPPETS:
        assert snippet in text
