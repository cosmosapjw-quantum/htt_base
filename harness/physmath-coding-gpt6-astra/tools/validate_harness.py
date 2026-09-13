#!/usr/bin/env python3
"""Validate package metadata/structure, not project science or model quality."""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REQUIRED = (
    "AGENTS.md", "START_HERE.md", "SCIENTIFIC_CONTRACT.md",
    "VALIDATION_MATRIX.md", "PLANS.md", "RUN_STATE.md", "DECISION_LOG.md",
    "FAILURE_LOG.md", "README.md", "VERSION", "manifest.json",
    "prompts/00_ultralight.md", "prompts/01_deep_once.md",
    "MODEL_ROUTER.json", "SOURCE_PROVENANCE.json", "tools/resolve_model.py",
    "docs/MODEL_ROUTING.md", "docs/MIGRATION_EVIDENCE.md", "docs/MODEL_REGRESSION.md",
    "tests/test_model_router.py", "tests/test_package_tools.py",
)
PHASES = (
    "00_task_contract", "01_reproduction_acceptance", "02_repository_localization",
    "03_bounded_solution_design", "04_execution_plan", "05_implementation",
    "06_software_validation", "07_scientific_validation",
    "08_numerical_reproducibility", "09_independent_diff_review",
    "10_promote_revert_closeout",
)
SKILLS = (
    "independent-diff-review", "numerical-validation", "reproducibility-closeout",
    "research-code-task", "scientific-validation",
)


def validate(root: Path) -> dict:
    errors: list[str] = []
    contents: dict[str, str] = {}
    required = list(REQUIRED)
    required += [f"prompts/phases/{phase}.md" for phase in PHASES]
    required += [f".agents/skills/{skill}/SKILL.md" for skill in SKILLS]
    root = root.resolve()
    for rel in required:
        path = root / rel
        try:
            if not path.resolve().is_relative_to(root):
                errors.append(f"required path escapes package: {rel}")
                continue
            text = path.read_text(encoding="utf-8")
            if not text.strip():
                errors.append(f"missing or empty: {rel}")
            contents[rel] = text
        except (OSError, UnicodeError) as exc:
            errors.append(f"unreadable {rel}: {exc}")

    manifest = None
    if "manifest.json" in contents:
        try:
            manifest = json.loads(contents["manifest.json"])
            if not isinstance(manifest, dict):
                errors.append("manifest must be a JSON object")
                manifest = None
        except json.JSONDecodeError as exc:
            errors.append(f"invalid manifest JSON: {exc.msg}")
    if manifest is not None:
        for key, expected in (
            ("name", "physmath-coding-harness-gpt6-astra"),
            ("version", "4.0.0"), ("model_family", "gpt-6-astra"),
        ):
            if manifest.get(key) != expected:
                errors.append(f"manifest {key} must be {expected!r}")
        if contents.get("VERSION", "").strip() != manifest.get("version"):
            errors.append("VERSION and manifest version disagree")
        entrypoints = manifest.get("entrypoints")
        if not isinstance(entrypoints, list) or not entrypoints:
            errors.append("manifest entrypoints must be a nonempty list")
        else:
            for rel in entrypoints:
                if not isinstance(rel, str) or not rel:
                    errors.append("manifest entrypoint must be a nonempty relative path")
                    continue
                path = root / rel
                if Path(rel).is_absolute() or not path.resolve().is_relative_to(root):
                    errors.append(f"entrypoint escapes package: {rel}")
                elif not path.is_file():
                    errors.append(f"missing entrypoint: {rel}")
        for key in ("scientific_acceptance", "model_performance"):
            if manifest.get(key) != "NOT_EVALUATED":
                errors.append(f"release manifest {key} must remain NOT_EVALUATED")
        if manifest.get("identity_is_authority") is not False:
            errors.append("manifest identity_is_authority must be false")

    agents = contents.get("AGENTS.md", "")
    for heading in ("## Task contract", "## Validation ladder", "## Completion bar"):
        if heading not in agents:
            errors.append(f"AGENTS.md missing heading: {heading}")
    for name in SKILLS:
        rel = f".agents/skills/{name}/SKILL.md"
        text = contents.get(rel, "")
        if text and not re.search(r"^---\s*\nname:\s*\S+\s*\ndescription:\s*.+?\n---", text, re.S):
            errors.append(f"invalid skill frontmatter: {rel}")
    return {
        "package_structure": "FAIL" if errors else "PASS",
        "scientific_acceptance": "NOT_EVALUATED",
        "model_performance": "NOT_EVALUATED",
        "authority_verification": "NOT_PERFORMED_BY_STRUCTURE_VALIDATOR",
        "errors": errors,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--json", action="store_true", help="emit machine-readable results")
    args = parser.parse_args()
    result = validate(args.root)
    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    elif result["errors"]:
        print("Coding harness package structure: FAIL", file=sys.stderr)
        for error in result["errors"]:
            print(f"- {error}", file=sys.stderr)
    else:
        print("Coding harness package structure: PASS")
        print("Scientific acceptance and model performance: NOT_EVALUATED")
        print("Source authority is not established by this structure check.")
    return 1 if result["errors"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
