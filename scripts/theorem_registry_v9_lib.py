"""Unified theorem-registry loader (REV-R170, v9 cycle).

``docs/research_program/THEOREM_REGISTRY.yaml`` is the single source of truth
for theorem/lemma status across the external-audit report, ledgers, and code
contracts. The v9 report builder renders its theorem ledger (including
supersede badges) from this file; the contract test
``tests/contracts/test_theorem_registry_v9.py`` enforces structural validity.

Structural rules enforced by :func:`validate_registry`:

* schema string is ``htt.theorem_registry.v1``;
* entry ids are unique and non-empty;
* ``status`` is one of :data:`ALLOWED_STATUSES`;
* every SUPERSEDED/RETRACTED entry carries ``superseded_by`` resolving to an
  entry whose status is ACTIVE, ACTIVE_CONDITIONAL, or PLANNED (a PLANNED
  successor must carry a ``landing`` revision tag);
* ``supersedes`` back-references resolve and point at SUPERSEDED/RETRACTED
  entries;
* every entry lists at least one source; for non-PLANNED entries at least one
  source must exist on disk, and every code pointer (``htt/``, ``scripts/``,
  ``research_gates/``) must exist (document pointers may be archival paths
  retained for provenance); PLANNED sources land in a later phase;
* ``sharpness_level``, when present, is 1, 2, or 3.
"""
from __future__ import annotations

from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
REGISTRY_PATH = ROOT / "docs/research_program/THEOREM_REGISTRY.yaml"

SCHEMA = "htt.theorem_registry.v1"
ALLOWED_STATUSES = frozenset({
    "ACTIVE", "ACTIVE_CONDITIONAL", "SUPERSEDED", "RETRACTED",
    "WITHHELD", "PLANNED",
})
LIVE_STATUSES = frozenset({"ACTIVE", "ACTIVE_CONDITIONAL", "PLANNED"})


def load_registry(path: Path | None = None) -> dict:
    text = (path or REGISTRY_PATH).read_text()
    data = yaml.safe_load(text)
    if not isinstance(data, dict):
        raise ValueError("theorem registry root must be a mapping")
    return data


def entries_by_id(data: dict) -> dict[str, dict]:
    out: dict[str, dict] = {}
    for entry in data.get("entries", []):
        out[str(entry.get("id"))] = entry
    return out


def validate_registry(data: dict, *, root: Path | None = None) -> list[str]:
    """Return a list of structural issues (empty list == valid)."""
    root = root or ROOT
    issues: list[str] = []
    if data.get("schema") != SCHEMA:
        issues.append(f"schema mismatch: {data.get('schema')!r} != {SCHEMA!r}")
    entries = data.get("entries")
    if not isinstance(entries, list) or not entries:
        return issues + ["entries missing or empty"]

    ids: dict[str, dict] = {}
    for i, entry in enumerate(entries):
        eid = entry.get("id")
        if not eid or not isinstance(eid, str):
            issues.append(f"entry[{i}] missing id")
            continue
        if eid in ids:
            issues.append(f"duplicate id {eid}")
        ids[eid] = entry

    for eid, entry in ids.items():
        status = entry.get("status")
        if status not in ALLOWED_STATUSES:
            issues.append(f"{eid}: bad status {status!r}")
            continue
        if not entry.get("title"):
            issues.append(f"{eid}: missing title")
        if not entry.get("owner"):
            issues.append(f"{eid}: missing owner")
        if not entry.get("claim_tier"):
            issues.append(f"{eid}: missing claim_tier")
        if not entry.get("body_section"):
            issues.append(f"{eid}: missing body_section")

        if status in ("SUPERSEDED", "RETRACTED"):
            succ = entry.get("superseded_by")
            if not succ:
                issues.append(f"{eid}: {status} without superseded_by")
            elif succ not in ids:
                issues.append(f"{eid}: superseded_by {succ!r} unresolved")
            elif ids[succ].get("status") not in LIVE_STATUSES:
                issues.append(
                    f"{eid}: superseded_by {succ} has non-live status "
                    f"{ids[succ].get('status')!r}")

        if status == "PLANNED" and not entry.get("landing"):
            issues.append(f"{eid}: PLANNED without landing revision tag")

        for back in entry.get("supersedes", []) or []:
            if back not in ids:
                issues.append(f"{eid}: supersedes {back!r} unresolved")
            elif ids[back].get("status") not in ("SUPERSEDED", "RETRACTED"):
                issues.append(
                    f"{eid}: supersedes {back} whose status is "
                    f"{ids[back].get('status')!r} (expected SUPERSEDED/RETRACTED)")

        level = entry.get("sharpness_level")
        if level is not None and level not in (1, 2, 3):
            issues.append(f"{eid}: sharpness_level {level!r} not in 1..3")

        sources = entry.get("sources")
        if not sources:
            issues.append(f"{eid}: no sources")
        elif status != "PLANNED":
            existing = [s for s in sources if (root / str(s)).exists()]
            if not existing:
                issues.append(f"{eid}: no source exists on disk")
            for src in sources:
                is_code = str(src).startswith(("htt/", "scripts/",
                                               "research_gates/"))
                if is_code and not (root / str(src)).exists():
                    issues.append(f"{eid}: code source missing on disk: {src}")

    return issues


def ledger_rows(data: dict) -> list[dict]:
    """Flat row dicts for the report ledger: id, title, status, badge,
    owner, body_section — RETRACTED/SUPERSEDED rows carry the successor id."""
    rows = []
    for entry in data.get("entries", []):
        status = entry.get("status", "")
        badge = ""
        if status in ("SUPERSEDED", "RETRACTED"):
            badge = f"{status} by {entry.get('superseded_by', '?')}"
        rows.append({
            "id": entry.get("id"),
            "title": entry.get("title"),
            "status": status,
            "badge": badge,
            "owner": entry.get("owner"),
            "body_section": str(entry.get("body_section", "--")),
            "sharpness_level": entry.get("sharpness_level"),
        })
    return rows
