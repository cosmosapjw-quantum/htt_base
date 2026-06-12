from __future__ import annotations

import importlib.util
import subprocess
import sys
from pathlib import Path

import yaml


REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPT_PATH = REPO_ROOT / "scripts" / "codex_harness" / "new_pr_delta.py"
TEMPLATE_PATH = REPO_ROOT / "docs" / "PR_DELTAS" / "TEMPLATE.md"


def _load_module():
    spec = importlib.util.spec_from_file_location("new_pr_delta", SCRIPT_PATH)
    assert spec is not None
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def _write_backlog(tmp_path: Path) -> Path:
    backlog = {
        "prs": [
            {
                "id": "PR-999",
                "title": "Fixture delta generator",
                "owner": "COMMON",
                "depends": ["PR-001", "PR-002"],
                "files": [
                    "scripts/codex_harness/new_pr_delta.py",
                    "docs/PR_DELTAS/TEMPLATE.md",
                ],
                "tests": [
                    "python scripts/codex_harness/new_pr_delta.py PR-999 --dry-run",
                    "python -m pytest tests/contracts/test_pr_delta_template.py -q",
                ],
                "dod": ["Delta includes evidence, tests, claim impact, and risks"],
                "kill": "Reject if science-code changes lack PR_DELTA.",
                "level": "L1",
                "scope": "pre-solver",
                "risk": "low",
            }
        ]
    }
    path = tmp_path / "pr_backlog.yaml"
    path.write_text(yaml.safe_dump(backlog), encoding="utf-8")
    return path


def test_template_contains_required_review_sections() -> None:
    template = TEMPLATE_PATH.read_text(encoding="utf-8")

    for heading in [
        "## Goal",
        "## Evidence read",
        "## Web/doc checks",
        "## Subagent divergence",
        "## Chosen plan",
        "## Files changed",
        "## Tests run",
        "## Review findings and fixes",
        "## Claim-tier impact",
        "## Risk log",
        "## Status and artifacts",
        "## Commit",
    ]:
        assert heading in template
    assert "$pr_id" in template
    assert "$web_check_status" in template


def test_render_delta_uses_backlog_card_and_downclaims_status(tmp_path: Path) -> None:
    module = _load_module()
    backlog_path = _write_backlog(tmp_path)

    card = module.load_pr_card(backlog_path, "PR-999")
    rendered = module.render_pr_delta(card, web_check_status="done")

    assert "# PR-999 - Fixture delta generator" in rendered
    assert "- Owner: COMMON" in rendered
    assert "- Depends: PR-001, PR-002" in rendered
    assert "- Risk: low" in rendered
    assert "- WEB_CHECK_STATUS: done" in rendered
    assert "scripts/codex_harness/new_pr_delta.py" in rendered
    assert "python -m pytest tests/contracts/test_pr_delta_template.py -q" in rendered
    assert "This PR delta is project-review metadata" in rendered
    assert "not scientific readiness evidence" in rendered
    assert "transfer_source: none" in rendered
    assert "MIO diagnostic certificate evidence" in rendered
    assert "family-identification evidence" in rendered
    assert "no C5/C6 science" in rendered
    assert "claim." in rendered


def test_render_delta_canonicalizes_legacy_owner_language(tmp_path: Path) -> None:
    module = _load_module()
    backlog_path = _write_fixture_with_owner(tmp_path, owner="TSC")

    card = module.load_pr_card(backlog_path, "PR-998")
    rendered = module.render_pr_delta(card)

    assert "- Owner: TSC_LEGACY" in rendered
    assert "implementation_scope: tsc_legacy" in rendered
    assert "Owner: TSC\n" not in rendered


def test_cli_dry_run_prints_target_and_writes_nothing(tmp_path: Path) -> None:
    backlog_path = _write_backlog(tmp_path)
    output_dir = tmp_path / "deltas"

    completed = subprocess.run(
        [
            sys.executable,
            str(SCRIPT_PATH),
            "PR-999",
            "--backlog",
            str(backlog_path),
            "--dir",
            str(output_dir),
            "--dry-run",
        ],
        cwd=REPO_ROOT,
        check=False,
        capture_output=True,
        text=True,
    )

    assert completed.returncode == 0, completed.stderr
    assert str(output_dir / "pr-999.md") in completed.stdout
    assert "# PR-999 - Fixture delta generator" in completed.stdout
    assert not (output_dir / "pr-999.md").exists()


def test_cli_default_backlog_can_render_real_pr_022() -> None:
    completed = subprocess.run(
        [
            sys.executable,
            str(SCRIPT_PATH),
            "PR-022",
            "--dry-run",
            "--web-check-status",
            "done",
        ],
        cwd=REPO_ROOT,
        check=False,
        capture_output=True,
        text=True,
    )

    assert completed.returncode == 0, completed.stderr
    assert "docs/PR_DELTAS/pr-022.md" in completed.stdout
    assert "# PR-022 - PR delta template and review artifact generator" in completed.stdout
    assert "- WEB_CHECK_STATUS: done" in completed.stdout
    assert "transfer_source: none" in completed.stdout


def test_cli_rejects_invalid_web_check_status(tmp_path: Path) -> None:
    backlog_path = _write_backlog(tmp_path)

    completed = subprocess.run(
        [
            sys.executable,
            str(SCRIPT_PATH),
            "PR-999",
            "--backlog",
            str(backlog_path),
            "--web-check-status",
            "invalid",
            "--dry-run",
        ],
        cwd=REPO_ROOT,
        check=False,
        capture_output=True,
        text=True,
    )

    assert completed.returncode == 2
    assert "invalid choice" in completed.stderr


def test_cli_refuses_overwrite_unless_force(tmp_path: Path) -> None:
    backlog_path = _write_backlog(tmp_path)
    output_dir = tmp_path / "deltas"
    output_dir.mkdir()
    output = output_dir / "pr-999.md"
    output.write_text("old", encoding="utf-8")

    blocked = subprocess.run(
        [
            sys.executable,
            str(SCRIPT_PATH),
            "PR-999",
            "--backlog",
            str(backlog_path),
            "--dir",
            str(output_dir),
        ],
        cwd=REPO_ROOT,
        check=False,
        capture_output=True,
        text=True,
    )
    assert blocked.returncode == 1
    assert "already exists" in blocked.stderr
    assert output.read_text(encoding="utf-8") == "old"

    forced = subprocess.run(
        [
            sys.executable,
            str(SCRIPT_PATH),
            "PR-999",
            "--backlog",
            str(backlog_path),
            "--dir",
            str(output_dir),
            "--force",
        ],
        cwd=REPO_ROOT,
        check=False,
        capture_output=True,
        text=True,
    )
    assert forced.returncode == 0, forced.stderr
    assert "# PR-999 - Fixture delta generator" in output.read_text(encoding="utf-8")


def test_cli_rejects_unknown_pr_id(tmp_path: Path) -> None:
    backlog_path = _write_backlog(tmp_path)

    completed = subprocess.run(
        [
            sys.executable,
            str(SCRIPT_PATH),
            "PR-NOPE",
            "--backlog",
            str(backlog_path),
            "--dry-run",
        ],
        cwd=REPO_ROOT,
        check=False,
        capture_output=True,
        text=True,
    )

    assert completed.returncode == 1
    assert "PR-NOPE not found" in completed.stderr


def _write_fixture_with_owner(tmp_path: Path, *, owner: str) -> Path:
    backlog = {
        "prs": [
            {
                "id": "PR-998",
                "title": "Owner normalization fixture",
                "owner": owner,
                "depends": [],
                "files": ["docs/PR_DELTAS/TEMPLATE.md"],
                "tests": ["python -m pytest tests/contracts/test_pr_delta_template.py -q"],
                "dod": ["Owner language is canonical"],
                "kill": "Reject noncanonical owner language.",
                "level": "L1",
                "scope": "pre-solver",
                "risk": "low",
            }
        ]
    }
    path = tmp_path / "owner_backlog.yaml"
    path.write_text(yaml.safe_dump(backlog), encoding="utf-8")
    return path
