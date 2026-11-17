"""Receipt and result bindings of the R58/R59 cards (referee repair B1.c, M4.c, M1).

Not part of the unmutated suite of scripts/r58/r58_mutation_receipt.py and not a receipt source: these tests compare
receipts and committed results with the current code, so a stale receipt or a drifted result fails the card's test command.
"""
from __future__ import annotations

import hashlib
import importlib.util
import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
PKG = ROOT / "docs/research_program/observational_publication_20261015/R58_MIXED_TENSOR_CONVERGENCE_20261117"
R54 = ROOT / "docs/research_program/observational_publication_20261015/R54_TENSOR_FRAME_TOMOGRAPHY_20261116"


def _module(rel: str, name: str):
    spec = importlib.util.spec_from_file_location(name, ROOT / rel)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_r54_receipt_sources_unchanged_since_the_r54_receipt():
    """B1.c: R58/R59 list htt/htt/htt/infer in their files; a change of an R54 receipt source without a new R54 receipt
    (python scripts/r54/build_r54_contract.py mutation-receipt) fails here, as in tests/r54 (same hash comparison)."""
    builder = _module("scripts/r54/build_r54_contract.py", "r54_builder_for_r58")
    receipt = json.loads((R54 / "MUTATION_GATE_RECEIPT.json").read_text())
    assert receipt["all_killed"] is True and receipt["unmutated_suite_exit_code"] == 0
    assert set(receipt["sources_sha256"]) == set(builder.RECEIPT_SOURCES)
    for rel, digest in receipt["sources_sha256"].items():
        assert _sha(ROOT / rel) == digest, f"{rel} changed after the R54 receipt: run scripts/r54/build_r54_contract.py mutation-receipt"


def test_r58_mutation_receipt_is_current_and_complete():
    gates = _module("scripts/r58/r58_mutation_receipt.py", "r58_mutation_receipt")
    receipt = json.loads((PKG / "MUTATION_GATE_RECEIPT.json").read_text())
    assert receipt["unmutated_suite_exit_code"] == 0 and receipt["all_killed"] is True
    assert receipt["unmutated_suite"] == list(gates.SUITE)
    assert [r["id"] for r in receipt["gates"]] == [g[0] for g in gates.GATES]
    for row, gate in zip(receipt["gates"], gates.GATES):
        assert row["status"] == "KILLED" and row["pytest_exit_code"] == 1, row["id"]
        assert (row["file"], row["pattern"], row["mutation"], row["test"]) == gate[1:5], row["id"]
    assert set(receipt["sources_sha256"]) == set(gates.SOURCES)
    for rel, digest in receipt["sources_sha256"].items():
        assert _sha(ROOT / rel) == digest, f"{rel} changed after the R58 receipt: run scripts/r58/r58_mutation_receipt.py"


def test_axis_diagnostics_are_bound_to_the_committed_fit(tmp_path):
    """M1: AXIS_DIAGNOSTICS.json is what the script computes from the committed fit (no refit), and the independent
    recomputation of D1, D2 and D4 agrees."""
    diag = _module("scripts/r58/build_r58_axis_diagnostics.py", "r58_axis_diagnostics")
    cmp = _module("scripts/r58/compare_r59_native_replay.py", "r59_compare_for_axes")
    committed = json.loads((PKG / "RESULTS/AXIS_DIAGNOSTICS.json").read_text())
    assert committed["source_fit"]["sha256"] == _sha(PKG / "RESULTS/OWNED_TENSOR_RESULT.json")
    fresh = json.loads(json.dumps(diag.clean(diag.compute(ROOT)), allow_nan=False))
    out = cmp.compare_json(committed, fresh)
    assert not out["numeric_outside_tolerance"], out["numeric_outside_tolerance"][:5]
    assert not out["only_reference"] and not out["only_replay"] and not out["nonnumeric_differences"]
    assert len(committed["reference_axes"]) == 8                       # closed reference family
    checker = _module("scripts/r58/check_r58_independent.py", "r58_independent_for_axes")
    report = checker.check_axis_diagnostics(ROOT, tmp_path / "check.json")
    assert report["status"] == "D1_D2_D4_INDEPENDENTLY_REPRODUCED"
    stored = json.loads((PKG / "RESULTS/AXIS_DIAGNOSTICS_INDEPENDENT_CHECK.json").read_text())
    assert stored["status"] == report["status"] and stored["inputs_sha256"] == report["inputs_sha256"]


@pytest.mark.parametrize("phrase", ["detection", "significant alignment", "caused by", "Virgo infall"])
def test_axis_diagnostics_carry_no_detection_language(phrase):
    text = (PKG / "RESULTS/AXIS_DIAGNOSTICS.json").read_text()
    assert phrase not in text
