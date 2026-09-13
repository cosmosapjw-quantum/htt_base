#!/usr/bin/env python3
"""Validate package structure; this is not a scientific or model-performance test."""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
STATE_NAMES = ("RESEARCH_STATE.md", "EVIDENCE_LEDGER.md", "HYPOTHESIS_GRAPH.md", "DECISION_LOG.md", "NEGATIVE_RESULTS.md", "CLOSEOUT.md")
REQUIRED = (
    "README.md", "START_HERE.md", "VERSION", "manifest.json", "PROJECT_INSTRUCTIONS.md",
    "prompts/00_integrated_work_run.md", "prompts/routing/MODEL_AND_EFFORT.md",
    "policies/APPROVAL_BOUNDARIES.md", "policies/EVIDENCE_AND_CITATION.md",
    "policies/STOP_RULES.md", "policies/PHASE_GATES.md",
    "docs/MODEL_ROUTING.md", "docs/MIGRATION_EVIDENCE.md", "docs/MODEL_REGRESSION.md",
    "MODEL_ROUTER.json", "tools/resolve_model.py",
) + tuple(f"{directory}/{name}" for directory in ("state", "templates/state") for name in STATE_NAMES)
LEGACY_SKILLS = (
    "research-contract", "evidence-acquisition", "claim-source-audit", "hypothesis-space",
    "adversarial-review", "physics-math-validation", "verification-design", "research-closeout",
)


def main() -> int:
    errors: list[str] = []
    for rel in REQUIRED:
        path = ROOT / rel
        if not path.is_file():
            errors.append(f"missing: {rel}")
        elif not path.read_text(encoding="utf-8").strip():
            errors.append(f"empty: {rel}")
    for rel in ("manifest.json", "MODEL_ROUTER.json"):
        try:
            data = json.loads((ROOT / rel).read_text(encoding="utf-8"))
        except (OSError, ValueError) as exc:
            errors.append(f"invalid JSON {rel}: {exc}")
            continue
        if not isinstance(data, dict):
            errors.append(f"expected JSON object: {rel}")
            continue
        if rel == "manifest.json":
            version_path = ROOT / "VERSION"
            if version_path.is_file() and data.get("version") != version_path.read_text().strip():
                errors.append("manifest version differs from VERSION")
            if data.get("name") != "physmath-research-harness-gpt6-astra":
                errors.append("manifest name differs from package identity")
            if data.get("empirical_performance") != "NOT_EVALUATED":
                errors.append("this release has no empirical model-performance evaluation")
            entrypoints = data.get("entrypoints")
            if not isinstance(entrypoints, list) or not entrypoints:
                errors.append("manifest entrypoints must be a nonempty list")
            else:
                for rel_entry in entrypoints:
                    if not isinstance(rel_entry, str) or not (ROOT / rel_entry).is_file():
                        errors.append(f"missing manifest entrypoint: {rel_entry}")
    for name in LEGACY_SKILLS:
        path = ROOT / ".agents" / "skills" / name / "SKILL.md"
        if not path.is_file():
            errors.append(f"missing preserved skill: {name}")
            continue
        value = path.read_text(encoding="utf-8")
        if not re.search(r"^---\s*\nname:\s*\S+\s*\ndescription:\s*.+?\n---", value, re.S):
            errors.append(f"invalid preserved skill frontmatter: {name}")
    if errors:
        print("Research harness package validation failed:", file=sys.stderr)
        for err in errors:
            print(f"- {err}", file=sys.stderr)
        return 1
    print("PASS — PACKAGING_ONLY: required files, JSON, manifest consistency, preserved skill frontmatter.")
    print("Scientific validity, execution provenance, and model performance are NOT_EVALUATED by this check.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
