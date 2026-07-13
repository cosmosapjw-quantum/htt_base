from __future__ import annotations

import json
import shutil
import subprocess
import sys
import tomllib
from pathlib import Path

import pytest


REPO_ROOT = Path(__file__).resolve().parents[2]
REQUIRED_AGENT_NAMES = {
    "claim_gate_reviewer",
    "code_cartographer",
    "convergence_director",
    "docs_citation_auditor",
    "harness_engineer",
    "physics_stat_auditor",
    "regression_tester",
}
REQUIRED_SKILL_NAMES = {
    "htt-dag-orchestrator",
    "htt-harness-engineering",
    "htt-physmath-audit",
}
READ_ONLY_AGENT_NAMES = {
    "claim_gate_reviewer",
    "code_cartographer",
    "convergence_director",
    "docs_citation_auditor",
    "physics_stat_auditor",
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
        pytest.skip("Codex CLI executable not installed; cannot validate execpolicy rules")
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
        path.parent.name
        for path in (root / ".agents" / "skills").glob("*/SKILL.md")
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


def test_custom_agent_configs_are_well_formed_and_named() -> None:
    agent_dir = REPO_ROOT / ".codex" / "agents"
    agents = {}
    for path in sorted(agent_dir.glob("*.toml")):
        data = tomllib.loads(path.read_text(encoding="utf-8"))
        agents[data["name"]] = data
        assert data["description"]
        assert data["sandbox_mode"] in {"read-only", "workspace-write"}
        assert data["model_reasoning_effort"] in {"medium", "high"}
        assert data["developer_instructions"].strip()
        assert data["nickname_candidates"]

    assert REQUIRED_AGENT_NAMES <= set(agents)
    for name in READ_ONLY_AGENT_NAMES:
        assert agents[name]["sandbox_mode"] == "read-only"


def test_gitignore_allows_versioned_codex_assets_but_ignores_project_config() -> None:
    checks = [
        (["git", "check-ignore", "-q", ".codex/agents/code-cartographer.toml"], 1),
        (["git", "check-ignore", "-q", ".codex/rules/default.rules"], 1),
        (["git", "check-ignore", "-q", ".codex/config.toml"], 0),
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
    assert harness_command.returncode == 0, harness_command.stdout + harness_command.stderr
    assert _strictest_decision(harness_command.stdout) == "allow"

    forbidden_command = _run_codex_policy(["rm", "-rf", "/tmp/foo"])
    assert forbidden_command.returncode == 0, forbidden_command.stdout + forbidden_command.stderr
    assert _strictest_decision(forbidden_command.stdout) == "forbidden"


def test_execpolicy_rejects_unmatched_rule_examples(tmp_path: Path) -> None:
    codex = shutil.which("codex")
    if codex is None:
        pytest.skip("Codex CLI executable not installed; cannot validate execpolicy rules")
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


def test_project_codex_config_shape_validator_accepts_no_config_and_rejects_bad_agents(
    tmp_path: Path,
) -> None:
    no_config = tmp_path / "no_config"
    no_config.mkdir()
    accepted = subprocess.run(
        [sys.executable, str(REPO_ROOT / "scripts/codex_harness/validate_codex_config_shape.py"), str(no_config)],
        cwd=REPO_ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    assert accepted.returncode == 0, accepted.stdout + accepted.stderr
    assert "no project-local .codex/config.toml present" in accepted.stdout

    bad_config = tmp_path / "bad_config" / ".codex"
    bad_config.mkdir(parents=True)
    (bad_config / "config.toml").write_text(
        """
[agents]
max_threads = 6
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
    assert "scalar values under [agents]" in rejected.stdout


def test_installer_copies_repo_scoped_assets_without_project_config(tmp_path: Path) -> None:
    codex = shutil.which("codex")
    if codex is None:
        pytest.skip("Codex CLI executable not installed; cannot validate installed rules")
    target = tmp_path / "installed"
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
        ".agents/skills/htt-dag-orchestrator/SKILL.md",
        ".codex/agents/code-cartographer.toml",
        ".codex/rules/default.rules",
        "docs/codex_handoff/pr_backlog.yaml",
        "scripts/codex_harness/verify_skill_layout.py",
        "harness_templates/vendor/physmath-gpt56/3.1.0/coding/manifest.json",
        "harness_templates/vendor/physmath-gpt56/3.1.0/research/manifest.json",
    ]:
        assert (target / path).exists(), path
    assert not (target / ".codex/config.toml").exists()
    assert not (target / "docs/codex_handoff/codex_handoff").exists()
    assert not (target / "docs/codex_handoff/PR_DELTAS").exists()
    assert not (target / "docs/codex_handoff/generated").exists()

    installed_skills = subprocess.run(
        ["python", str(target / "scripts/codex_harness/verify_skill_layout.py"), str(target)],
        cwd=REPO_ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    assert installed_skills.returncode == 0, installed_skills.stdout + installed_skills.stderr
    expected = _skill_names(REPO_ROOT)
    assert REQUIRED_SKILL_NAMES <= expected
    assert f"{len(expected)} skills OK" in installed_skills.stdout
    assert _reported_skill_names(installed_skills.stdout) == expected

    for mode, expected_message in [
        ("coding", "Coding harness validation passed."),
        ("research", "Research harness validation passed."),
    ]:
        validator = "validate_harness.py" if mode == "coding" else "validate_workspace.py"
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
    assert clean_reinstall.returncode == 0, clean_reinstall.stdout + clean_reinstall.stderr

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
    assert "Refusing to overwrite a divergent physmath vendor snapshot" in contaminated.stderr

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
    assert installed_policy.returncode == 0, installed_policy.stdout + installed_policy.stderr
    assert _strictest_decision(installed_policy.stdout) == "allow"


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
