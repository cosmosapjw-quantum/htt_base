#!/usr/bin/env python3
"""Fail-closed gateway to the historical v7 EGS result-table builder.

The value-bearing implementation and its outputs are quarantined below
``legacy/cf4_p0``.  No legacy Python is read or executed at import time.
Direct execution requires explicit, hash-bound legacy reproduction and can
never write an active ``docs/generated/egs_results_table`` artifact.
"""
from __future__ import annotations

import argparse
from pathlib import Path
import sys
from types import ModuleType


REPO_ROOT = Path(__file__).resolve().parents[1]
COMMON_ROOT = REPO_ROOT / "htt/src"
if str(COMMON_ROOT) not in sys.path:
    sys.path.insert(0, str(COMMON_ROOT))

from common.cf4_p0_quarantine import require_legacy_reproduction  # noqa: E402


LEGACY_SCRIPT = "legacy/cf4_p0/scripts/build_egs_results_table.py"
LEGACY_OUTPUTS = (
    "legacy/cf4_p0/tables/egs_results_table.json",
    "legacy/cf4_p0/tables/egs_results_table.md",
)


def _load_legacy_module() -> ModuleType:
    path = REPO_ROOT / LEGACY_SCRIPT
    module = ModuleType("cf4_p0_legacy_egs_results_table_v7")
    # Preserve the historical active location for repo-root discovery while
    # compiling the inventory-pinned legacy bytes.
    module.__file__ = str(REPO_ROOT / "scripts/build_egs_results_table.py")
    module.__package__ = ""
    sys.modules[module.__name__] = module
    exec(compile(path.read_bytes(), str(path), "exec"), module.__dict__)
    module.REPO_ROOT = REPO_ROOT
    module.GEN = REPO_ROOT / "legacy/cf4_p0/tables"
    module.OUT_JSON = REPO_ROOT / LEGACY_OUTPUTS[0]
    module.OUT_MD = REPO_ROOT / LEGACY_OUTPUTS[1]
    return module


def _verified_legacy_module() -> ModuleType:
    """Load frozen code only after its inventory pin has been authenticated."""

    require_legacy_reproduction(
        enabled=True,
        artifact_path=LEGACY_SCRIPT,
        repo_root=REPO_ROOT,
    )
    module = _load_legacy_module()
    require_legacy_reproduction(
        enabled=True,
        artifact_path=LEGACY_SCRIPT,
        repo_root=REPO_ROOT,
    )
    return module


# Compatibility functions are lazy so importing either gateway cannot execute
# frozen Python before the pin gate. They are legacy-reproduction surfaces only.
def _rows(*args, **kwargs):
    return _verified_legacy_module()._rows(*args, **kwargs)


def _payload(*args, **kwargs):
    return _verified_legacy_module()._payload(*args, **kwargs)


def _markdown(*args, **kwargs):
    return _verified_legacy_module()._markdown(*args, **kwargs)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--legacy-reproduction", action="store_true")
    args = parser.parse_args(argv)
    if not args.legacy_reproduction:
        print(
            "v7 EGS table is legacy_reproduction_only; no active table is emitted",
            file=sys.stderr,
        )
        return 2

    pinned = (LEGACY_SCRIPT, *LEGACY_OUTPUTS)
    for relative in pinned:
        require_legacy_reproduction(
            enabled=True,
            artifact_path=relative,
            repo_root=REPO_ROOT,
        )
    try:
        legacy = _load_legacy_module()
        legacy_args = ["--check"] if args.check else []
        return int(legacy.main(legacy_args))
    finally:
        for relative in pinned:
            require_legacy_reproduction(
                enabled=True,
                artifact_path=relative,
                repo_root=REPO_ROOT,
            )


if __name__ == "__main__":
    raise SystemExit(main())
