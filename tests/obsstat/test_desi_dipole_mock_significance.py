"""The pre-formalism EXT-DESI producer is invalidated fail-closed."""
from __future__ import annotations

import importlib.util
from pathlib import Path
import sys


REPO = Path(__file__).resolve().parents[2]
SCRIPT = REPO / "scripts/desi_dipole_mock_significance.py"
OUT = REPO / "docs/generated/desi_dipole_mock_card.json"


def _load_module():
    spec = importlib.util.spec_from_file_location(
        "desi_dipole_mock_significance", SCRIPT)
    mod = importlib.util.module_from_spec(spec)
    sys.modules["desi_dipole_mock_significance"] = mod
    spec.loader.exec_module(mod)
    return mod


def test_preformalism_result_is_absent_and_producer_refuses() -> None:
    assert not OUT.exists()
    mod = _load_module()
    assert mod.INVALIDATION_STATUS == \
        "INVALIDATED_PENDING_FORMALISM_REVALIDATION"
    assert mod.main([]) == 7
    assert mod.main(["--check"]) == 7
    assert not OUT.exists()
