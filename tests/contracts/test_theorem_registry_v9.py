"""Contract: unified theorem registry (REV-R170, v9 cycle).

docs/research_program/THEOREM_REGISTRY.yaml is the single source of truth for
theorem status. This contract pins:

* structural validity (schema, unique ids, status enum, supersession
  resolution, on-disk sources for non-PLANNED entries);
* the four v8-review supersessions (P26 -> T1p, P31 -> T3-full,
  P35 -> T4p, P36 -> T2G) and the T2p per-endpoint-iff retraction;
* the existence-level lemma reinterpretation (L-T2-EXIST stays ACTIVE);
* sharpness-level tags on the T3/P31 realization family.
"""
from __future__ import annotations

import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
LIB = ROOT / "scripts/theorem_registry_v9_lib.py"


def _load_lib():
    spec = importlib.util.spec_from_file_location("theorem_registry_v9_lib", LIB)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_registry_structurally_valid():
    lib = _load_lib()
    data = lib.load_registry()
    issues = lib.validate_registry(data)
    assert issues == [], "\n".join(issues)


def test_v8_review_supersessions_pinned():
    lib = _load_lib()
    ids = lib.entries_by_id(lib.load_registry())

    assert ids["P26"]["status"] == "SUPERSEDED"
    assert ids["P26"]["superseded_by"] == "T1p"

    assert ids["P31"]["status"] == "SUPERSEDED"
    assert ids["P31"]["superseded_by"] == "T3-full"

    assert ids["P35"]["status"] == "SUPERSEDED"
    assert ids["P35"]["superseded_by"] == "T4p"

    assert ids["P36"]["status"] == "RETRACTED"
    assert ids["P36"]["superseded_by"] == "T2G"

    # The per-endpoint iff itself is retracted; the sealed computation
    # survives only as the existence-level lemma.
    assert ids["T2p"]["status"] == "RETRACTED"
    assert ids["T2p"]["superseded_by"] == "T2G"
    assert ids["L-T2-EXIST"]["status"] == "ACTIVE"


def test_sharpness_levels_on_realization_family():
    lib = _load_lib()
    ids = lib.entries_by_id(lib.load_registry())
    assert ids["P31"]["sharpness_level"] == 1
    assert ids["T3-lin"]["sharpness_level"] == 1
    assert ids["T3-full"]["sharpness_level"] == 2
    assert ids["T3-int"]["sharpness_level"] == 1
    # Nobody reaches dynamical (level-3) sharpness.
    for entry in ids.values():
        assert entry.get("sharpness_level") != 3


def test_ledger_rows_carry_supersede_badges():
    lib = _load_lib()
    rows = {r["id"]: r for r in lib.ledger_rows(lib.load_registry())}
    assert rows["P36"]["badge"] == "RETRACTED by T2G"
    assert rows["P26"]["badge"] == "SUPERSEDED by T1p"
    assert rows["P31"]["badge"] == "SUPERSEDED by T3-full"
    assert rows["P35"]["badge"] == "SUPERSEDED by T4p"
    # ACTIVE rows carry no badge.
    assert rows["P18"]["badge"] == ""
