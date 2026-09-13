#!/usr/bin/env python3
"""Create missing state files only. Never overwrite existing evidence."""
from __future__ import annotations

import argparse
from datetime import date
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
FILES = {
    "RUN_STATE.md": """# RUN_STATE.md

DATE: {date}

OWNER / ACTUAL_MODEL / HARNESS_VERSION: / / 4.0.0

CURRENT_LAYER: diagnose

TASK / ACCEPTANCE:

EXISTING_AUTHORIZATION / PROTECTED_INVARIANTS:

SOURCE_IDENTITY / AUTHORITY_PROVENANCE:

CURRENT_HYPOTHESIS / SUPPORTING_EVIDENCE:

LAST_ACTUAL_COMMAND / EXIT / OUTPUT_PATH:

LAST_VALIDATION / REQUIRED_UNEVALUATED_CHECKS:

FIRST_FAILURE_AND_REPAIRS:

BUDGET_REMAINING_IF_EXPLICIT:

CLAIM_CEILING:

BLOCKER_CLASS / OBSERVED_FAILURE / UNRESOLVED_CAUSE:

NEXT_MINIMAL_ACTION:
""",
    "DECISION_LOG.md": "# DECISION_LOG.md\n",
    "FAILURE_LOG.md": "# FAILURE_LOG.md\n",
}


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Create missing state files while preserving all existing files."
    )
    parser.add_argument("--root", type=Path, default=ROOT, help="existing target directory")
    args = parser.parse_args()
    if not args.root.is_dir():
        parser.error("--root must be an existing directory")

    for rel, template in FILES.items():
        path = args.root / rel
        try:
            # Exclusive creation also preserves empty files and symlinks.
            with path.open("x", encoding="utf-8") as stream:
                stream.write(template.format(date=date.today().isoformat()))
        except FileExistsError:
            print(f"keep  {rel}")
        except OSError as exc:
            print(f"cannot create {rel}: {exc}", file=sys.stderr)
            return 1
        else:
            print(f"write {rel}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
