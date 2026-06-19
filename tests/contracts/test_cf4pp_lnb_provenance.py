import json
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
REPORT = ROOT / "docs/generated/cf4pp_lnb_provenance_report.json"
REPORT_MD = ROOT / "docs/generated/cf4pp_lnb_provenance_report.md"
SCRIPT = ROOT / "scripts/reproduce_cf4pp_lnb.py"


def _run(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(SCRIPT), *args],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )


def test_cf4pp_lnb_report_check_mode_passes():
    result = subprocess.run(
        ["venv/bin/python", "scripts/reproduce_cf4pp_lnb.py", "--check"],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    assert result.returncode == 0, result.stdout + result.stderr


def test_cf4pp_lnb_is_either_reproduced_or_quarantined():
    payload = json.loads(REPORT.read_text(encoding="utf-8"))

    assert payload["schema_version"] == "htt.cf4pp_lnb_provenance.v1"
    assert payload["owner"] == "HTT"
    assert payload["implementation_scope"] == "cf4pp_lnb_provenance_gate"
    assert payload["claim_tier"] in {
        "blocked",
        "diagnostic_only",
        "transfer_conditional",
    }
    assert payload["status"] in {
        "reproduced_with_bound_inputs",
        "quarantined_untraceable",
    }
    assert payload["config_hash"].startswith("sha256:")
    assert payload["input_hashes"]
    assert payload["generating_command"] == (
        "venv/bin/python scripts/reproduce_cf4pp_lnb.py --write"
    )
    assert payload["null_mock_status"]
    assert payload["covariance_status"]

    if payload["status"] == "reproduced_with_bound_inputs":
        assert isinstance(payload["lnB_cf4pp"], float)
        assert payload["accepted_source"]
        assert payload["bound_result_config_hash"]
        assert payload["bound_result_input_hashes"]
    else:
        assert payload["claim_tier"] == "blocked"
        assert payload["lnB_cf4pp"] is None
        assert payload["accepted_source"] is None
        assert payload["bound_result_config_hash"] is None
        assert payload["bound_result_input_hashes"] == []
        assert "not used in manuscript headline" in payload["caveats"]
        rejection_reasons = {
            reason
            for candidate in payload["rejected_candidates"]
            for reason in candidate["rejection_reasons"]
        }
        assert {
            "target_lnb_absent",
            "missing_bound_config_or_input_hashes",
        } & rejection_reasons


def test_source_override_accepts_only_bound_cf4pp_record(tmp_path: Path):
    bound = tmp_path / "bound.json"
    bound.write_text(
        json.dumps(
            {
                "label": "CF4++ sensitivity",
                "lnB_cf4pp": 44.0,
                "config_hash": "sha256:bound-config",
                "input_hashes": ["sha256:bound-input"],
                "generating_command": "python rerun.py --cf4pp",
                "claim_tier": "transfer_conditional",
                "transfer_source": "legacy_external_transfer_or_unbound",
            }
        ),
        encoding="utf-8",
    )

    result = _run("--json", "--source-json", str(bound))
    assert result.returncode == 0, result.stdout + result.stderr
    payload = json.loads(result.stdout)
    assert payload["status"] == "reproduced_with_bound_inputs"
    assert payload["lnB_cf4pp"] == 44.0
    assert payload["accepted_source"]["source_path"].endswith("bound.json")

    unbound = tmp_path / "unbound.json"
    unbound.write_text(
        json.dumps({"label": "CF4++ sensitivity", "lnB_cf4pp": 44.0}),
        encoding="utf-8",
    )

    result = _run("--json", "--source-json", str(unbound))
    assert result.returncode == 0, result.stdout + result.stderr
    payload = json.loads(result.stdout)
    assert payload["status"] == "quarantined_untraceable"
    assert payload["lnB_cf4pp"] is None
    assert "missing_bound_config_or_input_hashes" in (
        payload["rejected_candidates"][0]["rejection_reasons"]
    )


def test_source_override_cannot_write_or_check_production_reports(tmp_path: Path):
    source = tmp_path / "bound.json"
    source.write_text(
        json.dumps(
            {
                "label": "CF4++ sensitivity",
                "lnB_cf4pp": 44.0,
                "config_hash": "sha256:bound-config",
                "input_hashes": ["sha256:bound-input"],
                "generating_command": "python rerun.py --cf4pp",
                "claim_tier": "transfer_conditional",
                "transfer_source": "legacy_external_transfer_or_unbound",
            }
        ),
        encoding="utf-8",
    )

    for mode in ["--write", "--check"]:
        result = _run(mode, "--source-json", str(source))
        assert result.returncode == 2
        assert "--source-json is only allowed with --json" in result.stderr


def test_blocked_bound_source_remains_quarantined(tmp_path: Path):
    source = tmp_path / "blocked.json"
    source.write_text(
        json.dumps(
            {
                "label": "CF4++ sensitivity",
                "lnB_cf4pp": 44.0,
                "config_hash": "sha256:blocked-config",
                "input_hashes": ["sha256:blocked-input"],
                "generating_command": "python rerun.py --cf4pp",
                "claim_tier": "blocked",
                "transfer_source": "legacy_external_transfer_or_unbound",
            }
        ),
        encoding="utf-8",
    )

    result = _run("--json", "--source-json", str(source))
    assert result.returncode == 0, result.stdout + result.stderr
    payload = json.loads(result.stdout)
    assert payload["status"] == "quarantined_untraceable"
    assert payload["lnB_cf4pp"] is None
    assert "unsupported_claim_tier" in (
        payload["rejected_candidates"][0]["rejection_reasons"]
    )


def test_markdown_report_carries_required_artifact_metadata():
    payload = json.loads(REPORT.read_text(encoding="utf-8"))
    markdown = REPORT_MD.read_text(encoding="utf-8")

    for field in [
        "owner",
        "implementation_scope",
        "claim_tier",
        "transfer_source",
        "config_hash",
        "input_hashes",
        "sky_support_status",
        "covariance_status",
        "null_mock_status",
        "generating_command",
        "git_commit_or_worktree_state",
        "status",
    ]:
        assert f"{field}:" in markdown
    for item in payload["input_hashes"]:
        assert item in markdown


def test_manuscript_does_not_print_unbound_cf4pp_lnb_values():
    combined = "\n".join(
        (ROOT / path).read_text(encoding="utf-8")
        for path in [
            "docs/manuscript/ch07_results.tex",
            "docs/manuscript/ch08_robustness.tex",
            "docs/manuscript/ch09_discussion.tex",
        ]
    )

    for token in ["+44.0", "+44", "+105.8", "+106"]:
        assert token not in combined
    assert "CF4++" in combined
    assert "quarantined" in combined
    assert "dedicated rerun" in combined
