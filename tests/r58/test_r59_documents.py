"""M4.b: MANUSCRIPT.md and CLAIM_TABLE.csv are exactly what scripts/r58/build_r59_outputs.py renders (nothing is written)."""
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
PKG = ROOT / "docs/research_program/observational_publication_20261015/R58_MIXED_TENSOR_CONVERGENCE_20261117"


@pytest.fixture(scope="module")
def rendered():
    spec = importlib.util.spec_from_file_location("r59_outputs", ROOT / "scripts/r58/build_r59_outputs.py")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module.render(ROOT)


@pytest.mark.parametrize("name", ["MANUSCRIPT.md", "CLAIM_TABLE.csv"])
def test_committed_document_equals_the_builder_output(rendered, name):
    committed = (PKG / name).read_bytes()
    assert committed == rendered[name].encode("utf-8"), f"{name} is stale or hand-edited: run python scripts/r58/build_r59_outputs.py"
