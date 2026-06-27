"""Contract: the root research-evaluation package is deterministic, self-contained,
and research-content-complete (report + code + tests + result records + prompt),
content-addressed (no git-state churn), and claim-gated.
"""
from __future__ import annotations

import importlib.util
from pathlib import Path
import sys

REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPT = REPO_ROOT / "scripts/build_research_evaluation_package.py"


def _load():
    spec = importlib.util.spec_from_file_location("build_research_evaluation_package", SCRIPT)
    mod = importlib.util.module_from_spec(spec)
    sys.modules["build_research_evaluation_package"] = mod
    spec.loader.exec_module(mod)
    return mod


def _payload():
    mod = _load()
    payload, entries = mod.build_payload(
        repo_root=REPO_ROOT,
        generating_command="python scripts/build_research_evaluation_package.py",
    )
    return mod, payload, entries


def test_builds_passes_gates_and_is_research_complete():
    _mod, payload, entries = _payload()
    assert payload["failed_gates"] == []
    a = payload["required_assertions"]
    assert a["report_pdf_included"] and a["report_tex_included"]
    assert a["research_code_present"] and a["gate_tests_present"] and a["result_records_present"]
    assert a["joint_artifact_included"] and a["results_table_included"] and a["blockers_included"]
    assert a["review_prompt_included"]
    assert len(entries) == payload["archive_entry_count"]


def test_claim_firewall_and_content_addressed():
    _mod, payload, _entries = _payload()
    assert payload["claim_tier"] == "diagnostic_only"
    assert payload["family_identification"] is False
    assert payload["native_solver_result"] is False
    # content-addressed provenance -> no HEAD churn across commits
    assert payload["git_commit_or_worktree_state"] == "content-addressed"
    assert payload["config_hash"].startswith("sha256:")


def test_on_disk_package_is_current():
    mod = _load()
    assert mod.main(["--check"]) == 0


def test_prompt_is_context_independent_and_critical_constructive():
    mod = _load()
    prompt = mod.render_prompt()
    # explains the project from scratch
    assert "no prior knowledge" in prompt.lower()
    assert "from scratch" in prompt.lower()
    # both critical and constructive
    assert "critical" in prompt.lower() and "constructive" in prompt.lower()
    # states the hard claim boundaries
    assert "Bianchi family" in prompt and "native" in prompt.lower()
