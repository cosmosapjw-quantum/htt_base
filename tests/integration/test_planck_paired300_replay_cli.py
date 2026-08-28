from __future__ import annotations

from pathlib import Path
import subprocess
import sys


def _run_help(script: Path, *, cwd: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(script), "--help"],
        cwd=cwd,
        text=True,
        capture_output=True,
        check=False,
    )


def test_clean_checkout_replay_entrypoint_bootstraps_repository_imports(tmp_path: Path) -> None:
    root = Path(__file__).resolve().parents[2]
    script = root / "scripts/observed_runs/replay_planck_paired300_irrep_carrier.py"
    result = _run_help(script, cwd=tmp_path)
    assert result.returncode == 0, result.stderr
    assert "--output-dir" in result.stdout
    assert "--frozen-scalar-package" in result.stdout
    assert "--fresh-review-receipt" in result.stdout


def test_legacy_export_cli_no_longer_offers_self_attested_finalizer(tmp_path: Path) -> None:
    root = Path(__file__).resolve().parents[2]
    script = root / "scripts/observed_runs/export_planck_paired300_irrep_carrier.py"
    result = _run_help(script, cwd=tmp_path)
    assert result.returncode == 0, result.stderr
    assert "--finalize-reviewed" not in result.stdout
