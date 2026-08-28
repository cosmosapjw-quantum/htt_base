from __future__ import annotations

from pathlib import Path
import subprocess
import sys


def test_clean_checkout_replay_entrypoint_bootstraps_repository_imports(tmp_path: Path) -> None:
    root = Path(__file__).resolve().parents[2]
    script = root / "scripts/observed_runs/replay_planck_paired300_irrep_carrier.py"
    result = subprocess.run(
        [sys.executable, str(script), "--help"],
        cwd=tmp_path,
        text=True,
        capture_output=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr
    assert "--output-dir" in result.stdout
    assert "--frozen-scalar-package" in result.stdout
