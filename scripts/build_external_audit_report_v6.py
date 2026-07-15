#!/usr/bin/env python3
"""Fail-closed PR-120 gate for the frozen v6.1 external-audit report.

The shipped report, PDF, ZIP, and value-bearing builder are immutable
historical evidence under ``legacy/cf4_p0``.  This active path deliberately
does not rebuild or republish that CF4 P0 descendant.
"""
from __future__ import annotations

import argparse
from pathlib import Path
import sys


REPO = Path(__file__).resolve().parents[1]
LEGACY_ROOT = (
    REPO
    / "legacy/cf4_p0/packages/external_reports/"
    "external_audit_research_report_20260709_v6_1"
)
LEGACY_BUILDER = REPO / "legacy/cf4_p0/scripts/build_external_audit_report_v6.py"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    parser.parse_args(argv)
    missing = [
        path.relative_to(REPO).as_posix()
        for path in (LEGACY_ROOT, LEGACY_BUILDER)
        if not path.exists()
    ]
    if missing:
        print("missing frozen v6.1 evidence: " + ", ".join(missing), file=sys.stderr)
        return 1
    print(
        "v6.1 external report is legacy_reproduction_only; active rebuild withheld "
        "by the PR-120 CF4 P0 quarantine",
        file=sys.stderr,
    )
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
