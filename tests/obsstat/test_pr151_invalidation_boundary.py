from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[2]


@pytest.mark.parametrize("filename", ("desi_dipole_mock_significance.py", "desi_exact_selection_card.py"))
def test_PR151_historical_measure_is_quarantined_before_payload_access(filename: str) -> None:
    spec = importlib.util.spec_from_file_location("invalidated_pr151", ROOT / "scripts" / filename)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    with pytest.raises(module.InvalidatedHistoricalProducerError, match="invalidated"):
        module.measure()
