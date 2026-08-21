"""Direct API and CLI quarantine tests for the invalidated PR-151 producers."""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import subprocess
import sys

import pytest


ROOT = Path(__file__).resolve().parents[2]


def _module(filename: str):
    spec = importlib.util.spec_from_file_location(filename.removesuffix(".py"), ROOT / "scripts" / filename)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


@pytest.mark.parametrize("filename", ("desi_dipole_mock_significance.py", "desi_exact_selection_card.py"))
def test_PR151_API_and_cli_are_typed_nonexecution_paths(filename: str) -> None:
    module = _module(filename)
    with pytest.raises(module.InvalidatedHistoricalProducerError, match="invalidated"):
        module.measure()
    result = subprocess.run((sys.executable, "-B", str(ROOT / "scripts" / filename), "--check"), check=False, capture_output=True, text=True)
    assert result.returncode == 7
    receipt = json.loads(result.stdout)
    assert receipt["execution_state"] == module.INVALIDATION_STATUS
    assert receipt["observed_data_executed"] is False
    assert receipt["scientific_result_emitted"] is False
