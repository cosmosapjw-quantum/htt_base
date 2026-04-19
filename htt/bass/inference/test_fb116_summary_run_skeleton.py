from __future__ import annotations

from pathlib import Path

import pytest

from bass.background.bianchi_types import ALL_BIANCHI_TYPES
from bass.inference.__main__ import main


@pytest.mark.skip(reason="pending FB-11.6 implementation — skeleton only")
def test_fb116_summary_run_skeleton_contract() -> None:
    repo_root = Path(__file__).resolve().parents[3]
    config_path = repo_root / "configs/fb11_summary.yaml"

    assert config_path.exists()
    assert tuple(ALL_BIANCHI_TYPES) == (
        "I",
        "II",
        "III",
        "IV",
        "V",
        "VI_0",
        "VI_h",
        "VII_0",
        "VII_h",
        "VIII",
        "IX",
    )

    doc = main.__doc__ or ""
    assert "seed=42" in doc
    assert "fb11_summary_table.json" in doc
    assert "fb11_summary_table.md" in doc
