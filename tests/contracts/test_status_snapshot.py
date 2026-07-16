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
    assert bundle.metadata["pending_prs"] == 3
    assert bundle.metadata["dormant_external_prs"] == 0
    assert bundle.metadata["skipped_prs"] == 0
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
    assert all(row["smoke_tested"] is False for row in bundle.status_rows)
    assert bundle.status_rows[0]["orchestration_state"] == "completed"
    assert bundle.status_rows[2]["orchestration_state"] == "in_progress"
    assert bundle.status_rows[3]["orchestration_state"] == "pending"
    assert all(row["production_validated"] is False for row in bundle.status_rows)
    assert all(
        row["artifact_readiness"] in {"generated", "missing"}
        for row in bundle.status_rows
    )
    assert all("allowed_use" in row for row in bundle.status_rows)
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


def test_status_bundle_preserves_orthogonal_orchestration_states(
    tmp_path: Path,
) -> None:
    pr_ids = [f"PR-{number:03d}" for number in range(1, 7)]
    backlog = {
        "policy": {"topological_order": pr_ids},
        "prs": [
            {
                "id": pr_id,
                "title": f"Card {pr_id}",
                "owner": "COMMON",
                "depends": [],
                "scope": "pre-solver",
            }
            for pr_id in pr_ids
        ],
    }
    status = {
        "completed": ["PR-001"],
        "blocked": ["PR-002"],
        "skipped": ["PR-003"],
        "in_progress": "PR-004",
        "pending": ["PR-005"],
        "dormant_external": ["PR-006"],
        "execution_resolutions": {
            "PR-001": {
                "resolution": "COMPLETED_SUCCESS",
                "receipt": "docs/PR_DELTAS/pr-001.md",
            }
        },
    }
    backlog_path = tmp_path / "pr_backlog.yaml"
    status_path = tmp_path / "pr_status.yaml"
    backlog_path.write_text(yaml.safe_dump(backlog), encoding="utf-8")
    status_path.write_text(yaml.safe_dump(status), encoding="utf-8")

    bundle = build_status_bundle(
        backlog_path=backlog_path,
        status_path=status_path,
        source_commit="abc123",
    )

    states = {
        row["artifact_id"]: row["orchestration_state"] for row in bundle.status_rows
    }
    assert states == {
        "codex_dag.PR-001": "completed",
        "codex_dag.PR-002": "blocked",
        "codex_dag.PR-003": "skipped",
        "codex_dag.PR-004": "in_progress",
        "codex_dag.PR-005": "pending",
        "codex_dag.PR-006": "dormant_external",
    }
    assert bundle.metadata["completed_prs"] == 1
    assert bundle.metadata["blocked_prs"] == 1
    assert bundle.metadata["skipped_prs"] == 1
    assert bundle.metadata["in_progress_prs"] == 1
    assert bundle.metadata["pending_prs"] == 1
    assert bundle.metadata["dormant_external_prs"] == 1
    assert bundle.metadata["execution_resolution_count"] == 1
    assert bundle.metadata["execution_resolution_prs"] == ["PR-001"]

    completed_row = bundle.status_rows[0]
    assert completed_row["claim_tier"] == "diagnostic_only"
    assert completed_row["production_validated"] is False
    matrix = render_status_matrix(bundle)
    assert "| Dormant external PRs | 1 |" in matrix
    assert "| `dormant_external` | 1 |" in matrix
    assert "| `pending` | 1 |" in matrix
    assert "| `in_progress` | 1 |" in matrix
    assert "| `skipped` | 1 |" in matrix
    for required_metadata in (
        "| Owner | `COMMON` |",
        "| Implementation scope | `common` |",
        "| Input hashes |",
        "| Sky support status | `not_directional` |",
        "| Null/mock status | `not_statistical` |",
        "| Caveats |",
        "| Generating command |",
    ):
        assert required_metadata in matrix
    validate_status_matrix_matches_snapshot(matrix, bundle.status_snapshot_payload())


def test_status_bundle_uses_gate_outputs_for_artifact_promotion_axes(
    tmp_path: Path,
) -> None:
    backlog_path, status_path = _write_fixture(tmp_path)
    gate_outputs_path = tmp_path / "artifact_gate_outputs.yaml"
    gate_outputs_path.write_text(
        yaml.safe_dump(
            {
                "pr_overrides": {
                    "PR-010": {
                        "claim_tier": "conditional",
                        "artifact_readiness": "validation_candidate",
                        "artifact_mode": "external_audit_conditioned",
                        "allowed_use": "paper_appendix",
                        "manuscript_used": True,
                        "caption_policy": ["must_state_transfer_conditional"],
                        "promotion_blockers": ["native_solver_validation_absent"],
                        "science_promotion_gates": {
                            "native_solver_validation": "fail",
                        },
                        "publication_gates": {
                            "paper_main": "fail",
                        },
                    }
                }
            }
        ),
        encoding="utf-8",
    )

    bundle = build_status_bundle(
        backlog_path=backlog_path,
        status_path=status_path,
        gate_outputs_path=gate_outputs_path,
        source_commit="abc123",
    )

    row = next(
        row for row in bundle.status_rows if row["artifact_id"] == "codex_dag.PR-010"
    )
    assert row["claim_tier"] == "conditional"
    assert row["artifact_readiness"] == "validation_candidate"
    assert row["artifact_mode"] == "external_audit_conditioned"
    assert row["allowed_use"] == "paper_appendix"
    assert row["manuscript_used"] is True
    assert row["production_validated"] is False
    assert row["caption_policy"] == ["must_state_transfer_conditional"]
    assert row["promotion_blockers"] == ["native_solver_validation_absent"]
    assert row["science_promotion_gates"] == {"native_solver_validation": "fail"}
    assert row["publication_gates"] == {"paper_main": "fail"}
    assert any(
        "artifact_gate_outputs.yaml" in item for item in bundle.metadata["input_hashes"]
    )


def test_status_bundle_downgrades_unverified_legacy_smoke_readiness(
    tmp_path: Path,
) -> None:
    backlog_path, status_path = _write_fixture(tmp_path)
    gate_outputs_path = tmp_path / "artifact_gate_outputs.yaml"
    gate_outputs_path.write_text(
        yaml.safe_dump(
            {
                "pr_overrides": {
                    "PR-010": {
                        "artifact_readiness": "smoke_tested",
                    }
                }
            }
        ),
        encoding="utf-8",
    )

    bundle = build_status_bundle(
        backlog_path=backlog_path,
        status_path=status_path,
        gate_outputs_path=gate_outputs_path,
        source_commit="abc123",
    )

    row = next(
        row for row in bundle.status_rows if row["artifact_id"] == "codex_dag.PR-010"
    )
    assert row["smoke_tested"] is False
    assert row["artifact_readiness"] == "generated"
    assert "exact_test_execution_receipt_not_bound" in row["promotion_blockers"]
    assert all(
        row["artifact_readiness"] != "smoke_tested" or row["smoke_tested"] is True
        for row in bundle.status_rows
    )


def test_status_snapshot_uses_python310_compatible_utc_timestamp(
    tmp_path: Path,
) -> None:
    backlog_path, status_path = _write_fixture(tmp_path)

    bundle = build_status_bundle(
        backlog_path=backlog_path,
        status_path=status_path,
        source_commit="abc123",
    )

    assert str(bundle.metadata["generated_on"]).endswith("+00:00")
    source = (REPO_ROOT / "htt/src/common/status_snapshot.py").read_text(
        encoding="utf-8"
    )
    assert "from datetime import UTC" not in source
    assert "datetime.now(UTC)" not in source


def test_directional_certificate_pr_notes_preserve_support_statuses(
    tmp_path: Path,
) -> None:
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
    assert "sky_support_status=directional_certificate_readiness_recorded" in notes
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


def test_redshift_certificate_pr_notes_preserve_bridge_statuses(tmp_path: Path) -> None:
    backlog = {
        "prs": [
            {
                "id": "PR-101",
                "title": "Redshift-binned coherence and G_F certificate bridge",
                "owner": "MIO",
                "depends": ["PR-055", "PR-100"],
                "scope": "pre-solver",
                "files": [
                    "htt/mio/coherence/redshift_binned.py",
                    "tests/mio/test_redshift_binned_coherence.py",
                ],
                "dod": [
                    "Depth-bin covariance and selection metadata required for production-grade G/coherence",
                    "Descriptive fallback is explicit",
                ],
            }
        ],
    }
    status = {"completed": ["PR-101"], "blocked": [], "in_progress": None}
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
    assert "covariance_status=redshift_bin_certificate_readiness_recorded" in notes
    assert "null_mock_status=redshift_bin_certificate_readiness_recorded" in notes
    assert "sky_support_status=redshift_bin_certificate_readiness_recorded" in notes
    assert "selection_status=redshift_bin_selection_metadata_required" in notes
    assert "g_f_bridge_status=diagnostic_bridge_metadata_recorded" in notes
    assert "null_mock_status=not_statistical" not in notes
    assert "sky_support_status=not_directional" not in notes


def test_survey_systematic_null_pr_notes_preserve_gate_statuses(tmp_path: Path) -> None:
    backlog = {
        "prs": [
            {
                "id": "PR-062",
                "title": "Survey-axis and selection-response null models",
                "owner": "HTT",
                "depends": ["PR-043", "PR-061"],
                "scope": "pre-solver",
                "files": [
                    "htt/htt/htt/nulls/selection_response_depth.py",
                    "htt/htt/htt/nulls/survey_axis_coherence.py",
                    "tests/htt/test_survey_nulls.py",
                ],
                "dod": [
                    "Survey/systematic nulls can mimic direction/depth signals in calibration",
                    "Selection metadata is carried through",
                ],
            }
        ],
    }
    status = {"completed": ["PR-062"], "blocked": [], "in_progress": None}
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
    assert "null_mock_status=survey_systematic_null_fpr_recorded" in notes
    assert "covariance_status=survey_systematic_null_fpr_recorded" in notes
    assert "sky_support_status=survey_systematic_null_fpr_recorded" in notes
    assert "selection_status=selection_metadata_hash_required" in notes
    assert "survey_axis_status=survey_axis_hash_required_when_present" in notes
    assert "claim_scope=dag_row_not_artifact_payload" in notes
    assert "null_mock_status=not_statistical" not in notes
    assert "sky_support_status=not_directional" not in notes


def test_redshift_certificate_notes_do_not_match_title_only(tmp_path: Path) -> None:
    backlog = {
        "prs": [
            {
                "id": "PR-999",
                "title": "Redshift-binned coherence and G_F certificate bridge",
                "owner": "MIO",
                "depends": [],
                "scope": "pre-solver",
                "files": ["docs/not-the-certificate.md"],
                "dod": [
                    "Depth-bin covariance and selection metadata required for production-grade G/coherence",
                    "Descriptive fallback is explicit",
                ],
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
    assert "covariance_status=redshift_bin_certificate_readiness_recorded" not in notes
    assert "g_f_bridge_status=diagnostic_bridge_metadata_recorded" not in notes
    assert "null_mock_status=not_statistical" in notes
    assert "sky_support_status=not_directional" in notes


def test_flrw_tension_gate_pr_notes_preserve_null_predictive_statuses(
    tmp_path: Path,
) -> None:
    backlog = {
        "prs": [
            {
                "id": "PR-102",
                "title": "FLRW tension diagnostic with null predictive distribution gate",
                "owner": "MIO",
                "depends": ["PR-076", "PR-100"],
                "scope": "pre-solver",
                "files": [
                    "htt/mio/tension/flrw_tension.py",
                    "tests/mio/test_flrw_tension_gate.py",
                ],
                "dod": [
                    "PPP/tension metrics require calibrated null predictive distribution",
                    "No PPP claim without null mocks",
                ],
            }
        ],
    }
    status = {"completed": ["PR-102"], "blocked": [], "in_progress": None}
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
    assert "null_mock_status=flrw_null_predictive_gate_recorded" in notes
    assert "covariance_status=flrw_null_predictive_gate_recorded" in notes
    assert "sky_support_status=flrw_null_predictive_gate_recorded" in notes
    assert "look_elsewhere_status=flrw_null_predictive_gate_recorded" in notes
    assert "tail_probability_status=descriptive_until_null_gate_passes" in notes
    assert "null_mock_status=not_statistical" not in notes
    assert "sky_support_status=not_directional" not in notes


def test_flrw_tension_gate_notes_do_not_match_title_only(tmp_path: Path) -> None:
    backlog = {
        "prs": [
            {
                "id": "PR-999",
                "title": "FLRW tension diagnostic with null predictive distribution gate",
                "owner": "MIO",
                "depends": [],
                "scope": "pre-solver",
                "files": ["docs/not-the-flrw-gate.md"],
                "dod": [
                    "PPP/tension metrics require calibrated null predictive distribution",
                    "No PPP claim without null mocks",
                ],
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
    assert "null_mock_status=flrw_null_predictive_gate_recorded" not in notes
    assert "tail_probability_status=descriptive_until_null_gate_passes" not in notes
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


def test_status_matrix_validation_accepts_legacy_snapshot_without_new_counts() -> None:
    legacy_snapshot = {
        "metadata": {
            "total_prs": 3,
            "completed_prs": 1,
            "blocked_prs": 0,
            "in_progress_prs": 1,
            "pending_prs": 1,
        }
    }
    legacy_matrix = """\
| Metric | Value |
| --- | ---: |
| Total PRs | 3 |
| Completed PRs | 1 |
| Blocked PRs | 0 |
| In progress | 1 |
| Pending PRs | 1 |
"""

    validate_status_matrix_matches_snapshot(legacy_matrix, legacy_snapshot)


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
