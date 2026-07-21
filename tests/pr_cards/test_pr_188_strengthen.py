"""PR-188 gates: hermetic reproduce + load-bearing mutation firewall (R2)."""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
for entry in (str(REPO / "htt"), str(REPO / "htt" / "src")):
    if entry not in sys.path:
        sys.path.insert(0, entry)

import pytest  # noqa: E402

from common.data_root import DataUnavailable, recipe_status, resolve  # noqa: E402

CARD = REPO / "docs/generated/pr188_result_card.json"
SPEC = REPO / "docs/research_program/strengthening/pr188_spec.yaml"


def _card() -> dict:
    return json.loads(CARD.read_text())


def test_spec_bound_and_terminal() -> None:
    c = _card()
    assert c["metadata"]["spec_sha256"] == hashlib.sha256(SPEC.read_bytes()).hexdigest()
    assert c["metadata"]["public_use"] is False
    assert c["metadata"]["independence_gate"] == "OPEN"
    assert "OPEN" in c["metadata"]["external_replication_gate"]
    assert c["terminal"] == "HERMETIC_REPRODUCE_LOAD_BEARING_VERIFIED"


def test_hermetic_reproduce_path_clean() -> None:
    r = _card()["result"]["hermetic_reproduce"]
    assert r["all_byte_stable"] is True
    assert r["reproduce_path_hermetic"] is True
    assert r["private_path_hits_on_reproduce_path"] == []


def test_load_bearing_mutation_firewall() -> None:
    m = _card()["result"]["load_bearing_mutation_suite"]
    assert m["n_load_bearing_mutations"] >= 15
    assert m["all_flipped_to_failure"] is True
    assert m["dead_source_stays_green"] is True


def test_data_recipe_blocks_never_silently_skips() -> None:
    r = _card()["result"]["external_data_recipe"]
    assert r["blocked_exit_on_missing"] == 2
    # a missing artifact under a bogus root raises DataUnavailable, never a skip
    import os
    old = os.environ.get("HTT_DATA_ROOT")
    os.environ["HTT_DATA_ROOT"] = "/nonexistent/data/root"
    try:
        with pytest.raises(DataUnavailable):
            resolve("does/not/exist.npz")
        status = recipe_status([{"relative": "does/not/exist.npz"}])
        assert status["all_present"] is False
        assert status["missing"] == ["does/not/exist.npz"]
    finally:
        if old is None:
            del os.environ["HTT_DATA_ROOT"]
        else:
            os.environ["HTT_DATA_ROOT"] = old


def test_hermeticity_scan_surfaces_backlog() -> None:
    scan = _card()["result"]["hermeticity_scan"]
    # the two sealed data modules are surfaced, not hidden or edited
    assert "htt/obsstat/boost_biposh_residual.py" in scan["private_path_modules"]
    assert "htt/obsstat/k1_evenl_biposh_rank.py" in scan["private_path_modules"]
    assert scan["migration_backlog_count"] >= 2


def test_sources_restored_after_mutation_suite() -> None:
    # the mutated modules must be byte-clean (the suite restores in finally)
    import subprocess
    proc = subprocess.run(
        ["git", "diff", "--stat", "htt/src/common/frame_typed_algebra.py",
         "htt/src/common/dual_axis_claim_state.py"],
        cwd=REPO, capture_output=True, text=True,
    )
    assert proc.stdout.strip() == "", f"sources not restored: {proc.stdout}"
