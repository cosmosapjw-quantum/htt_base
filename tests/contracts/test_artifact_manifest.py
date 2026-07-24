from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

from common.artifact_manifest import (
    REQUIRED_ARTIFACT_FIELDS,
    REQUIRED_PROVENANCE_FIELDS,
    build_quarantine_report,
    render_quarantine_markdown,
    validate_manifest_payload,
)
from common.sky_support import build_sky_support_from_mask


REPO_ROOT = Path(__file__).resolve().parents[2]


def _manifest_payload(
    path: str = "figures/ready.png",
    **overrides: object,
) -> dict[str, object]:
    payload: dict[str, object] = {
        "artifact_id": path.replace("/", "."),
        "artifact_path": path,
        "owner": "COMMON",
        "implementation_scope": "common",
        "claim_tier": "diagnostic_only",
        "production_status": "diagnostic_only",
        "created_by": "test-suite",
        "git_commit": "test",
        "config_hash": "cfg",
        "input_hashes": ["input"],
        "code_version": "0.0-test",
        "schema_version": "pr011",
        "caveats": ["test manifest only"],
        "transfer_source": "none",
        "sky_support_status": "not_directional",
        "null_mock_status": "not_statistical",
        "generating_command": "test-suite",
        "git_commit_or_worktree_state": "test",
    }
    payload.update(overrides)
    return payload


def test_required_artifact_fields_match_pr011_metadata_contract() -> None:
    assert REQUIRED_ARTIFACT_FIELDS == (
        "owner",
        "implementation_scope",
        "claim_tier",
        "config_hash",
        "input_hashes",
        "caveats",
    )
    assert REQUIRED_PROVENANCE_FIELDS == (
        "transfer_source",
        "sky_support_status",
        "null_mock_status",
        "generating_command",
        "git_commit_or_worktree_state",
    )


def test_validate_manifest_payload_accepts_canonical_artifact_manifest() -> None:
    issues = validate_manifest_payload(
        _manifest_payload(owner="TSC", implementation_scope="tsc"),
        manifest_path=Path("figures/legacy.manifest.json"),
    )

    assert issues == ()


def test_validate_manifest_payload_reports_missing_required_metadata() -> None:
    payload = _manifest_payload()
    del payload["input_hashes"]
    payload["caveats"] = []
    del payload["transfer_source"]

    issues = validate_manifest_payload(payload, manifest_path=Path("bad.manifest.json"))

    issue_codes = [issue.code for issue in issues]
    assert issue_codes[:3] == [
        "missing_required_field",
        "empty_required_field",
        "missing_required_field",
    ]
    assert "invalid_artifact_manifest" in issue_codes
    assert "input_hashes" in issues[0].detail
    assert "caveats" in issues[1].detail
    assert "transfer_source" in issues[2].detail


def test_validate_manifest_payload_rejects_external_transfer_marked_native() -> None:
    issues = validate_manifest_payload(
        _manifest_payload(
            "figures/external.png",
            transfer_source="native_solver",
            passed_gates=[],
        ),
        manifest_path=Path("external.manifest.json"),
    )

    assert [issue.code for issue in issues] == ["native_transfer_without_gate"]


def test_morphology_atlas_gate_does_not_validate_native_transfer() -> None:
    issues = validate_manifest_payload(
        _manifest_payload(
            "figures/morphology.png",
            transfer_source="BASS_native_validated",
            passed_gates=["native_morphology_atlas"],
        ),
        manifest_path=Path("morphology.manifest.json"),
    )

    assert [issue.code for issue in issues] == ["native_transfer_without_gate"]


def test_directional_manifest_requires_sky_support_metadata() -> None:
    issues = validate_manifest_payload(
        _manifest_payload(
            "figures/directional.png",
            sky_support_status="directional",
        ),
        manifest_path=Path("directional.manifest.json"),
    )

    assert [issue.code for issue in issues] == ["invalid_sky_support_metadata"]
    assert "sky_support" in issues[0].detail


def test_directional_manifest_accepts_pr040_sky_support_metadata() -> None:
    support = build_sky_support_from_mask(
        [True, False, True, True],
        coordinate_frame="galactic",
        completeness_status="partial_sky",
        selection_mode="zoa_hard_cut",
        mock_coverage_status="not_mocked",
        pixelization="equal_area_ring",
        nside=2,
    )
    issues = validate_manifest_payload(
        _manifest_payload(
            "figures/directional.png",
            sky_support_status="directional",
            sky_support=support.to_metadata(),
        ),
        manifest_path=Path("directional.manifest.json"),
    )

    assert issues == ()


def test_quarantine_report_separates_manifested_and_unmanifested_figures(
    tmp_path: Path,
) -> None:
    figure_dir = tmp_path / "figures"
    figure_dir.mkdir()
    loose = figure_dir / "loose.png"
    ready = figure_dir / "ready.png"
    loose.write_bytes(b"unmanifested")
    ready.write_bytes(b"manifested")
    (figure_dir / "ready.manifest.json").write_text(
        json.dumps(_manifest_payload("figures/ready.png"), indent=2, sort_keys=True)
        + "\n",
        encoding="utf-8",
    )

    report = build_quarantine_report(tmp_path, scan_roots=("figures",))

    assert [figure.path for figure in report.quarantined_figures] == [
        "figures/loose.png"
    ]
    assert [figure.path for figure in report.manifested_figures] == ["figures/ready.png"]
    assert loose.read_bytes() == b"unmanifested"
    assert ready.read_bytes() == b"manifested"


def test_sidecar_must_match_scanned_artifact_path(tmp_path: Path) -> None:
    figure_dir = tmp_path / "figures"
    figure_dir.mkdir()
    ready = figure_dir / "ready.png"
    ready.write_bytes(b"manifested")
    (figure_dir / "ready.manifest.json").write_text(
        json.dumps(_manifest_payload("figures/other.png"), indent=2, sort_keys=True)
        + "\n",
        encoding="utf-8",
    )

    report = build_quarantine_report(tmp_path, scan_roots=("figures",))

    assert [figure.path for figure in report.quarantined_figures] == [
        "figures/ready.png"
    ]
    assert report.manifested_figures == ()
    assert [issue.code for issue in report.manifest_issues] == [
        "artifact_path_mismatch"
    ]


def test_scan_root_cannot_escape_repository(tmp_path: Path) -> None:
    repo_root = tmp_path / "repo"
    repo_root.mkdir()
    outside = tmp_path / "outside"
    outside.mkdir()
    (outside / "owner-local.pdf").write_bytes(b"outside")

    with pytest.raises(
        ValueError,
        match="scan root must remain within the repository root",
    ):
        build_quarantine_report(repo_root, scan_roots=("../outside",))


def test_figure_and_sidecar_symlinks_cannot_escape_repository(
    tmp_path: Path,
) -> None:
    repo_root = tmp_path / "repo"
    figure_dir = repo_root / "figures"
    figure_dir.mkdir(parents=True)
    outside = tmp_path / "outside"
    outside.mkdir()
    outside_figure = outside / "owner-local.pdf"
    outside_figure.write_bytes(b"outside")
    (figure_dir / "linked.pdf").symlink_to(outside_figure)

    with pytest.raises(
        ValueError,
        match="scanned artifact must remain within the repository root",
    ):
        build_quarantine_report(repo_root, scan_roots=("figures",))

    (figure_dir / "linked.pdf").unlink()
    figure = figure_dir / "ready.png"
    figure.write_bytes(b"inside")
    outside_manifest = outside / "ready.manifest.json"
    outside_manifest.write_text(
        json.dumps(_manifest_payload("figures/ready.png")),
        encoding="utf-8",
    )
    (figure_dir / "ready.manifest.json").symlink_to(outside_manifest)

    with pytest.raises(
        ValueError,
        match="manifest sidecar must remain within the repository root",
    ):
        build_quarantine_report(repo_root, scan_roots=("figures",))


def test_cli_rejects_scan_root_outside_repository(tmp_path: Path) -> None:
    repo_root = tmp_path / "repo"
    repo_root.mkdir()
    outside = tmp_path / "outside"
    outside.mkdir()
    (outside / "owner-local.pdf").write_bytes(b"outside")

    completed = subprocess.run(
        [
            sys.executable,
            str(REPO_ROOT / "scripts" / "check_artifact_manifests.py"),
            "--repo-root",
            str(repo_root),
            "--scan-root",
            "../outside",
            "--dry-run",
        ],
        cwd=REPO_ROOT,
        check=False,
        capture_output=True,
        text=True,
    )

    assert completed.returncode == 2
    assert completed.stdout == ""
    assert completed.stderr.strip() == (
        "scan root must remain within the repository root"
    )


def test_render_quarantine_markdown_carries_required_metadata(tmp_path: Path) -> None:
    figure_dir = tmp_path / "figures"
    figure_dir.mkdir()
    (figure_dir / "loose.pdf").write_bytes(b"%PDF-1.4 test")
    report = build_quarantine_report(tmp_path, scan_roots=("figures",))

    markdown = render_quarantine_markdown(
        report,
        repo_root=tmp_path,
        output_path=Path("docs/generated/quarantined_figures.md"),
        generating_command="python scripts/check_artifact_manifests.py --dry-run",
    )

    assert "owner: COMMON" in markdown
    assert "implementation_scope: common" in markdown
    assert "claim_tier: diagnostic_only" in markdown
    assert "transfer_source: none" in markdown
    assert "config_hash:" in markdown
    assert "input_hashes:" in markdown
    assert "caveats:" in markdown
    assert "figures/loose.pdf" in markdown
    assert ("native solver " + "result") not in markdown
    assert ("family " + "identification") not in markdown.lower()


def test_cli_dry_run_quarantines_without_writing_output(tmp_path: Path) -> None:
    figure_dir = tmp_path / "figures"
    figure_dir.mkdir()
    (figure_dir / "loose.svg").write_text("<svg></svg>\n", encoding="utf-8")
    output = tmp_path / "docs" / "generated" / "quarantined_figures.md"

    completed = subprocess.run(
        [
            sys.executable,
            str(REPO_ROOT / "scripts" / "check_artifact_manifests.py"),
            "--repo-root",
            str(tmp_path),
            "--scan-root",
            "figures",
            "--output",
            str(output),
            "--dry-run",
        ],
        cwd=REPO_ROOT,
        check=False,
        capture_output=True,
        text=True,
    )

    assert completed.returncode == 0, completed.stderr
    assert "figures/loose.svg" in completed.stdout
    assert f"--repo-root {tmp_path}" in completed.stdout
    assert f"--output {output}" in completed.stdout
    assert not output.exists()


def test_cli_writes_report_when_not_dry_run(tmp_path: Path) -> None:
    figure_dir = tmp_path / "figures"
    figure_dir.mkdir()
    (figure_dir / "loose.png").write_bytes(b"png")
    output = tmp_path / "docs" / "generated" / "quarantined_figures.md"

    completed = subprocess.run(
        [
            sys.executable,
            str(REPO_ROOT / "scripts" / "check_artifact_manifests.py"),
            "--repo-root",
            str(tmp_path),
            "--scan-root",
            "figures",
            "--output",
            str(output),
        ],
        cwd=REPO_ROOT,
        check=False,
        capture_output=True,
        text=True,
    )

    assert completed.returncode == 0, completed.stderr
    assert output.exists()
    assert "figures/loose.png" in output.read_text(encoding="utf-8")


def test_cli_returns_nonzero_for_invalid_manifest_sidecar(tmp_path: Path) -> None:
    figure_dir = tmp_path / "figures"
    figure_dir.mkdir()
    (figure_dir / "ready.png").write_bytes(b"png")
    (figure_dir / "ready.manifest.json").write_text("{not-json", encoding="utf-8")

    completed = subprocess.run(
        [
            sys.executable,
            str(REPO_ROOT / "scripts" / "check_artifact_manifests.py"),
            "--repo-root",
            str(tmp_path),
            "--scan-root",
            "figures",
            "--dry-run",
        ],
        cwd=REPO_ROOT,
        check=False,
        capture_output=True,
        text=True,
    )

    assert completed.returncode == 1
    assert "invalid_json" in completed.stdout
