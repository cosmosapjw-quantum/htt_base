"""Contract: the stale mixed K1/K5/K6 figure is legacy-only under PR-120."""
from __future__ import annotations

from pathlib import Path
import subprocess
import sys

REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPT = REPO_ROOT / "scripts" / "make_blocker_discharge_figures.py"
ACTIVE = REPO_ROOT / "figures/current/fig_blocker_discharges"
LEGACY = REPO_ROOT / "legacy/cf4_p0/figures/current/fig_blocker_discharges"


def test_check_mode_is_current():
    result = subprocess.run(
        [sys.executable, str(SCRIPT), "--check"],
        cwd=REPO_ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    assert result.returncode == 0, result.stdout + result.stderr


def test_exact_historical_figure_is_legacy_only():
    for suffix in (".png", ".source.json", ".manifest.json"):
        assert not Path(str(ACTIVE) + suffix).exists()
        assert Path(str(LEGACY) + suffix).is_file()
