from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import yaml

from common.status_snapshot import (
    build_status_bundle,
    render_status_matrix,
    validate_status_matrix_matches_snapshot,
    write_status_artifacts,
)


REPO_ROOT = Path(__file__).resolve().parents[2]


def _write_fixture(tmp_path: Path) -> tuple[Path, Path]:
    backlog = {
        "policy": {"topological_order": ["PR-000", "PR-010", "PR-012"]},
        "prs": [
            {
                "id": "PR-000",
                "title": "Intake",
                "owner": "COMMON",
                "depends": [],
                "scope": "pre-solver",
            },
            {
                "id": "PR-010",
                "title": "Ownership firewall",
                "owner": "COMMON",
                "depends": ["PR-000"],
                "scope": "pre-solver",
            },
            {
                "id": "PR-012",
                "title": "Status snapshot",
                "owner": "COMMON",
                "depends": ["PR-010"],
                "scope": "pre-solver",
            },
            {
                "id": "PR-099",
                "title": "Legacy reproduction row",
                "owner": "TSC",
                "depends": ["PR-012"],
                "scope": "legacy",
            },
            {
                "id": "PR-098",
                "title": "External transfer registry row",
                "owner": "BASS_PY",
                "depends": ["PR-012"],
                "scope": "pre-solver",
            },
            {
                "id": "PR-100",
                "title": "Generated manuscript status row",
                "owner": "MANUSCRIPT",
                "depends": ["PR-012"],
                "scope": "pre-solver",
            },
        ],
    }
    status = {
        "completed": ["PR-000", "PR-010"],
        "blocked": [],
        "in_progress": "PR-012",
    }
    backlog_path = tmp_path / "pr_backlog.yaml"
    status_path = tmp_path / "pr_status.yaml"
    backlog_path.write_text(yaml.safe_dump(backlog), encoding="utf-8")
    status_path.write_text(yaml.safe_dump(status), encoding="utf-8")
    return backlog_path, status_path


def test_status_bundle_is_generated_from_dag_status_files(tmp_path: Path) -> None:
    backlog_path, status_path = _write_fixture(tmp_path)

    bundle = build_status_bundle(
        backlog_path=backlog_path,
        status_path=status_path,
        source_commit="abc123",
    )

    assert bundle.metadata["source"] == "common.status_snapshot"
    assert bundle.metadata["total_prs"] == 6
    assert bundle.metadata["completed_prs"] == 2
    assert [row["artifact_id"] for row in bundle.status_rows] == [
        "codex_dag.PR-000",
        "codex_dag.PR-010",
        "codex_dag.PR-012",
        "codex_dag.PR-098",
        "codex_dag.PR-099",
        "codex_dag.PR-100",
    ]
    assert bundle.status_rows[0]["implemented"] is True
    assert bundle.status_rows[2]["implemented"] is False
    assert all(row["production_validated"] is False for row in bundle.status_rows)
    assert bundle.status_rows[3]["owner"] == "BASS"
    assert bundle.status_rows[3]["implementation_scope"] == "bass_py"
    assert bundle.status_rows[4]["owner"] == "TSC_LEGACY"
    assert bundle.status_rows[4]["implementation_scope"] == "tsc_legacy"
    assert bundle.status_rows[5]["owner"] == "COMMON"
    assert "not scientific readiness" in bundle.claim_rows[0]["forbidden_claims"][0]
    assert bundle.metadata["transfer_source"] == "none"
    assert bundle.metadata["config_hash"]
    assert bundle.metadata["input_hashes"]
    assert bundle.metadata["caveats"]
    assert "common.status_snapshot" in bundle.metadata["generating_command"]


def test_directional_certificate_pr_notes_preserve_support_statuses(tmp_path: Path) -> None:
    backlog = {
        "prs": [
            {
                "id": "PR-100",
                "title": "MIO directional coherence certificate with covariance status",
                "owner": "MIO",
                "depends": ["PR-013", "PR-040", "PR-076"],
                "scope": "pre-solver",
                "files": [
                    "htt/mio/coherence/directional.py",
                    "htt/mio/interface/mio_certificate.py",
                    "tests/mio/test_directional_coherence_certificate.py",
                ],
                "dod": [
                    "MIO coherence certificate records covariance/sky support/null status",
                    "Diagnostic-only status if covariance incomplete",
                ],
            }
        ],
    }
    status = {"completed": ["PR-100"], "blocked": [], "in_progress": None}
    backlog_path = tmp_path / "pr_backlog.yaml"
    status_path = tmp_path / "pr_status.yaml"
    backlog_path.write_text(yaml.safe_dump(backlog), encoding="utf-8")
    status_path.write_text(yaml.safe_dump(status), encoding="utf-8")

    bundle = build_status_bundle(
        backlog_path=backlog_path,
        status_path=status_path,
        source_commit="abc123",
    )

    notes = bundle.claim_rows[0]["notes"]
    assert "covariance_status=certificate_readiness_recorded" in notes
    assert "null_mock_status=certificate_readiness_recorded" in notes
    assert (
        "sky_support_status=directional_certificate_readiness_recorded" in notes
    )
    assert "null_mock_status=not_statistical" not in notes
    assert "sky_support_status=not_directional" not in notes


def test_directional_certificate_notes_do_not_match_title_only(tmp_path: Path) -> None:
    backlog = {
        "prs": [
            {
                "id": "PR-999",
                "title": "MIO directional coherence certificate with covariance status",
                "owner": "MIO",
                "depends": [],
                "scope": "pre-solver",
                "files": ["docs/not-the-certificate.md"],
                "dod": ["Title text should not control generated status notes"],
            }
        ],
    }
    status = {"completed": ["PR-999"], "blocked": [], "in_progress": None}
    backlog_path = tmp_path / "pr_backlog.yaml"
    status_path = tmp_path / "pr_status.yaml"
    backlog_path.write_text(yaml.safe_dump(backlog), encoding="utf-8")
    status_path.write_text(yaml.safe_dump(status), encoding="utf-8")

    bundle = build_status_bundle(
        backlog_path=backlog_path,
        status_path=status_path,
        source_commit="abc123",
    )

    notes = bundle.claim_rows[0]["notes"]
    assert "covariance_status=certificate_readiness_recorded" not in notes
    assert "null_mock_status=not_statistical" in notes
    assert "sky_support_status=not_directional" in notes


def test_write_status_artifacts_writes_json_and_markdown(tmp_path: Path) -> None:
    backlog_path, status_path = _write_fixture(tmp_path)
    output = tmp_path / "generated" / "status_snapshot.json"

    written = write_status_artifacts(
        output,
        backlog_path=backlog_path,
        status_path=status_path,
        source_commit="abc123",
    )

    assert written.status_snapshot_path == output
    assert written.claim_ledger_path == output.with_name("claim_ledger.json")
    assert written.status_matrix_path == output.with_name("status_matrix.md")
    snapshot = json.loads(output.read_text(encoding="utf-8"))
    claim_ledger = json.loads(written.claim_ledger_path.read_text(encoding="utf-8"))
    status_matrix = written.status_matrix_path.read_text(encoding="utf-8")
    assert snapshot["metadata"]["completed_prs"] == 2
    assert len(snapshot["rows"]) == 6
    assert len(claim_ledger["rows"]) == 6
    assert "Manual status counts are prohibited" in status_matrix
    validate_status_matrix_matches_snapshot(status_matrix, snapshot)


def test_status_matrix_validation_blocks_manual_count_drift(tmp_path: Path) -> None:
    backlog_path, status_path = _write_fixture(tmp_path)
    bundle = build_status_bundle(
        backlog_path=backlog_path,
        status_path=status_path,
        source_commit="abc123",
    )
    matrix = render_status_matrix(bundle)
    corrupted = matrix.replace("| Completed PRs | 2 |", "| Completed PRs | 99 |")

    validate_status_matrix_matches_snapshot(matrix, bundle.status_snapshot_payload())
    try:
        validate_status_matrix_matches_snapshot(
            corrupted,
            bundle.status_snapshot_payload(),
        )
    except ValueError as exc:
        assert "generated status matrix count mismatch" in str(exc)
    else:  # pragma: no cover
        raise AssertionError("manual status count drift was not blocked")


def test_cli_writes_default_companion_artifacts(tmp_path: Path) -> None:
    backlog_path, status_path = _write_fixture(tmp_path)
    output = tmp_path / "generated" / "status_snapshot.json"

    completed = subprocess.run(
        [
            sys.executable,
            "-m",
            "common.status_snapshot",
            "--backlog",
            str(backlog_path),
            "--status",
            str(status_path),
            "--source-commit",
            "abc123",
            "--write",
            str(output),
        ],
        cwd=REPO_ROOT,
        check=False,
        capture_output=True,
        text=True,
    )

    assert completed.returncode == 0, completed.stderr
    assert "status_snapshot.json" in completed.stdout
    assert output.exists()
    assert output.with_name("claim_ledger.json").exists()
    assert output.with_name("status_matrix.md").exists()
