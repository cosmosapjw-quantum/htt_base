#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
run_all.py — execute the formalism experiment program end to end.

Each experiment imports the dependency-free reference_formalism.py, so this runs
anywhere with a standard Python 3.10+ interpreter (no third-party packages).

Order: E1 cancellation null, E2 F fail-closed coverage, E3 Pi threshold bias,
E4 G_F matched-null boost-vs-tilt, E5 comparator multiverse, E6/E7 firewall fuzz
+ leakage audit.
"""
from __future__ import annotations

import importlib
import sys
import traceback

MODULES = [
    ("E1", "exp01_cancellation_null"),
    ("E2", "exp02_F_failclosed_coverage"),
    ("E3", "exp03_Pi_threshold_bias"),
    ("E4", "exp04_GF_matched_null_boost_vs_tilt"),
    ("E5", "exp05_comparator_sensitivity"),
    ("E6/E7", "semantic_firewall_fuzz"),
]


def main() -> int:
    failures = 0
    for tag, name in MODULES:
        print("\n" + "#" * 78)
        print(f"# {tag}: {name}")
        print("#" * 78)
        try:
            mod = importlib.import_module(name)
            mod.main()
        except Exception:  # noqa: BLE001
            failures += 1
            print(f"[ERROR] {name} failed:")
            traceback.print_exc()
    print("\n" + "=" * 78)
    print(f"run_all complete: {len(MODULES) - failures}/{len(MODULES)} ok"
          + ("" if failures == 0 else f", {failures} FAILED"))
    print("=" * 78)
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
