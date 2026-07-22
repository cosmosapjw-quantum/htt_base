#!/usr/bin/env python3
"""Verify structure, machine-readable cards, hashes and self-containment."""
from __future__ import annotations

import hashlib
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def main() -> int:
    errors: list[str] = []
    required = [
        "README.md",
        "MANIFEST.json",
        "HOSTILE_ADVOCATE_MATRIX.json",
        "PR_GATE_MATRIX.json",
        "docs/01_HOSTILE_REFEREE_STEELMAN_EXTERNAL_FUSION.md",
        "docs/02_ADVOCATE_STEELMAN_UPGRADE_EXTERNAL_FUSION.md",
        "docs/03_EXTERNAL_FUSION_PR_ROADMAP_20260722.md",
        "docs/04_PUBLICATION_READINESS_MASTER_CHECKLIST_EXTERNAL_FUSION.md",
        "docs/05_REDSHIFT_DEPTH_LOWELL_POLE_PROGRAM.md",
        "docs/08_THEOREM_PROOF_BACKLOG_EXTERNAL_FUSION.md",
        "configs/external_ecosystem_ledger.json",
        "configs/data_recipes.json",
        "configs/lowell_pole_program.json",
        "schemas/plugin_receipt.schema.json",
        "schemas/pole_bundle.schema.json",
        "schemas/solver_delivery_receipt.schema.json",
        "context/reference/LONG_HORIZON_RESCUE_PR_ROADMAP_20260714.md",
        "context/reference/external_audit_research_report_v10.pdf",
    ]
    for rel in required:
        if not (ROOT / rel).is_file():
            errors.append(f"missing required file: {rel}")

    cards = sorted((ROOT / "pr_cards").glob("pr-*.json"))
    if len(cards) != 36:
        errors.append(f"expected 36 PR cards, found {len(cards)}")
    ids = []
    for p in cards:
        try:
            card = json.loads(p.read_text(encoding="utf-8"))
        except Exception as exc:
            errors.append(f"invalid JSON {p.name}: {exc}")
            continue
        ids.append(card.get("id"))
        if len(card.get("pass_gates", [])) < 8:
            errors.append(f"{p.name}: fewer than 8 pass gates")
        if len(card.get("fail_gates", [])) < 6:
            errors.append(f"{p.name}: fewer than 6 fail gates")
        if card.get("track") == "II" and not card.get("native_solver_required"):
            errors.append(f"{p.name}: Track II lacks native_solver_required")
    expected = list(range(247, 283))
    if ids != expected:
        errors.append("PR ids are not the complete ordered PR-247..PR-282 range")

    # All JSON files must parse.  MANIFEST is checked after generation below.
    for p in ROOT.rglob("*.json"):
        if p.name == "MANIFEST.json":
            continue
        try:
            json.loads(p.read_text(encoding="utf-8"))
        except Exception as exc:
            errors.append(f"invalid JSON {p.relative_to(ROOT)}: {exc}")

    # No compiled/cache files are allowed in a release bundle.
    for p in ROOT.rglob("*"):
        if p.is_file() and (p.suffix in {".pyc", ".pyo"} or "__pycache__" in p.parts or ".pytest_cache" in p.parts):
            errors.append(f"cache/compiled file present: {p.relative_to(ROOT)}")

    # Source and planning files must not depend on prior /mnt/data paths.
    bad_pattern = re.compile(r"/mnt/(?:data|sn\d+|home)|/home/oai")
    for p in ROOT.rglob("*"):
        if not p.is_file() or p.suffix.lower() not in {".py", ".md", ".json", ".toml", ".txt", ".yaml", ".yml"}:
            continue
        if p.resolve() == Path(__file__).resolve():
            continue
        text = p.read_text(encoding="utf-8", errors="ignore")
        if bad_pattern.search(text):
            errors.append(f"external absolute path found: {p.relative_to(ROOT)}")

    manifest_path = ROOT / "MANIFEST.json"
    if manifest_path.exists():
        try:
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            for row in manifest.get("files", []):
                p = ROOT / row["path"]
                if not p.is_file():
                    errors.append(f"manifest file missing: {row['path']}")
                elif sha256(p) != row["sha256"]:
                    errors.append(f"manifest hash mismatch: {row['path']}")
        except Exception as exc:
            errors.append(f"manifest invalid: {exc}")

    status = "PASS" if not errors else "FAIL"
    print(json.dumps({
        "status": status,
        "root": str(ROOT),
        "pr_cards": len(cards),
        "errors": errors,
    }, indent=2))
    return 0 if not errors else 2


if __name__ == "__main__":
    raise SystemExit(main())
