#!/usr/bin/env python3
"""PR-120 gate for the quarantined historical blocker-discharge figure.

The three-panel figure mixed a stale CF4 P0 numerical consumer into a current
K1/K5/K6 surface.  The exact historical pixels and sidecars remain below
``legacy/cf4_p0``; this active command creates no figure.
"""
from __future__ import annotations

import argparse
from pathlib import Path
import sys


REPO = Path(__file__).resolve().parents[1]
ACTIVE = tuple(
    REPO / "figures/current" / f"fig_blocker_discharges{suffix}"
    for suffix in (".png", ".source.json", ".manifest.json")
)
LEGACY = tuple(
    REPO / "legacy/cf4_p0/figures/current" / f"fig_blocker_discharges{suffix}"
    for suffix in (".png", ".source.json", ".manifest.json")
)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    parser.parse_args(argv)
    active = [path.relative_to(REPO).as_posix() for path in ACTIVE if path.exists()]
    missing = [path.relative_to(REPO).as_posix() for path in LEGACY if not path.is_file()]
    if active or missing:
        if active:
            print("active blocker-discharge artifacts must be absent: " + ", ".join(active), file=sys.stderr)
        if missing:
            print("missing legacy blocker-discharge artifacts: " + ", ".join(missing), file=sys.stderr)
        return 1
    print("blocker-discharge figure quarantined; active figure absent")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
