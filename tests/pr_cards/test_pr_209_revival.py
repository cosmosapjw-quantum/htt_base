"""PR-209 gates: hash-bound legacy inventory + disposition + no-import scan.

P3 decisive falsifier: flipped sha, missing disposition entry, injected legacy
import each kill the gate.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[2]
for entry in (str(REPO / "htt"), str(REPO / "htt" / "src")):
    if entry not in sys.path:
        sys.path.insert(0, entry)

from common.revival_legacy_inventory import (  # noqa: E402
    adjudicate,
    disposition_counts,
    load_ledger,
    scan_no_direct_import,
    verify_inventory,
)

LEDGER = REPO / "docs/generated/revival_legacy_disposition.json"
DROP = REPO / "htt_legacy_revival_round2_20260721"
CARD = REPO / "docs/generated/pr209_result_card.json"
drop_missing = pytest.mark.skipif(not DROP.is_dir(), reason="legacy drop not on disk")


def test_ledger_16_objects_all_dispositions_known():
    ledger = load_ledger(LEDGER)
    assert len(ledger) == 16
    for item in ledger:
        assert adjudicate(item["disposition"]) in {"KEEP", "REBUILD", "MUTATION", "RETIRE"}


@drop_missing
def test_inventory_all_match():
    rows = verify_inventory(load_ledger(LEDGER), DROP)
    assert all(r.matches for r in rows)


@drop_missing
def test_mutation_flipped_sha_is_caught():
    ledger = load_ledger(LEDGER)
    ledger[0] = dict(ledger[0], sha256="00" * 32)
    rows = verify_inventory(ledger, DROP)
    assert not all(r.matches for r in rows)  # kill


def test_inventory_path_escape_is_rejected(tmp_path):
    drop = tmp_path / "drop"
    drop.mkdir()
    outside = tmp_path / "outside.bin"
    outside.write_bytes(b"outside")
    ledger = [{
        "path": "../outside.bin",
        "disposition": "RETIRE_RESULT",
        "sha256": "00" * 32,
    }]
    with pytest.raises(ValueError, match="escapes the drop"):
        verify_inventory(ledger, drop)


def test_inventory_symlink_escape_is_rejected(tmp_path):
    drop = tmp_path / "drop"
    drop.mkdir()
    outside = tmp_path / "outside.bin"
    outside.write_bytes(b"outside")
    (drop / "linked.bin").symlink_to(outside)
    ledger = [{
        "path": "linked.bin",
        "disposition": "RETIRE_RESULT",
        "sha256": "00" * 32,
    }]
    with pytest.raises(ValueError, match="crosses a symlink"):
        verify_inventory(ledger, drop)


def test_mutation_missing_disposition_is_caught():
    ledger = load_ledger(LEDGER)
    bad = dict(ledger[0], disposition="TOTALLY_UNKNOWN")
    with pytest.raises(ValueError):
        adjudicate(bad["disposition"])


def test_zero_direct_legacy_import_in_production():
    assert scan_no_direct_import(REPO) == []


def test_mutation_injected_legacy_import_is_caught(tmp_path):
    root = tmp_path / "htt" / "src"
    root.mkdir(parents=True)
    (root / "evil.py").write_text("from legacy_sources.htt import ssot\n")
    hits = scan_no_direct_import(tmp_path)
    assert any(h["file"].endswith("evil.py") for h in hits)  # kill


def test_disposition_counts_sum_to_total():
    ledger = load_ledger(LEDGER)
    assert sum(disposition_counts(ledger).values()) == len(ledger)


def test_card_terminal_and_check_stable():
    if not CARD.exists():
        pytest.skip("card not yet written")
    card = json.loads(CARD.read_text())
    assert card["pr_id"] == "PR-209"
    assert card["metadata"]["public_use"] is False
    assert card["metadata"]["independence_gate"] == "OPEN"
    if DROP.is_dir():
        assert card["terminal"] == "LEGACY_INVENTORY_HASH_BOUND_ZERO_DIRECT_IMPORT"
