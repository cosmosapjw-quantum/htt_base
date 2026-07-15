#!/usr/bin/env python3
"""Fail-closed gateway to the historical v8 EGS result-table builder.

The value-bearing implementation and output pair live only under
``legacy/cf4_p0``.  The active v9 successor reads the hash-bound frozen JSON in
order to apply the PR-120 quarantine overlay; importing this gateway never
executes legacy Python. Direct execution is legacy-only and cannot recreate an
active v8 table.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
from types import ModuleType


REPO_ROOT = Path(__file__).resolve().parents[1]
COMMON_ROOT = REPO_ROOT / "htt/src"
if str(COMMON_ROOT) not in sys.path:
    sys.path.insert(0, str(COMMON_ROOT))

from common.cf4_p0_quarantine import require_legacy_reproduction  # noqa: E402


LEGACY_SCRIPT = "legacy/cf4_p0/scripts/build_egs_results_table_v8.py"
LEGACY_OUTPUTS = (
    "legacy/cf4_p0/tables/egs_results_table_v8.json",
    "legacy/cf4_p0/tables/egs_results_table_v8.md",
)


def _load_legacy_module() -> ModuleType:
    path = REPO_ROOT / LEGACY_SCRIPT
    module = ModuleType("cf4_p0_legacy_egs_results_table_v8")
    module.__file__ = str(REPO_ROOT / "scripts/build_egs_results_table_v8.py")
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


def _v8_rows(*args, **kwargs):
    return _verified_legacy_module()._v8_rows(*args, **kwargs)


def _markdown(*args, **kwargs):
    return _verified_legacy_module()._markdown(*args, **kwargs)


def _payload() -> dict:
    """Return the exact frozen v8 payload for the active v9 overlay.

    Re-running the historical builder would resolve its auxiliary inputs through
    a modern active checkout and would therefore no longer be a frozen read.  The
    successor consumes the hash-bound legacy JSON directly and verifies the pin
    both before and after reading it.
    """

    relative = LEGACY_OUTPUTS[0]
    require_legacy_reproduction(
        enabled=True,
        artifact_path=relative,
        repo_root=REPO_ROOT,
    )
    payload = json.loads((REPO_ROOT / relative).read_text(encoding="utf-8"))
    require_legacy_reproduction(
        enabled=True,
        artifact_path=relative,
        repo_root=REPO_ROOT,
    )
    if (
        not isinstance(payload, dict)
        or payload.get("schema") != "htt.egs.results_table.v8"
    ):
        raise ValueError("frozen v8 EGS result table has an invalid schema")
    return payload


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--legacy-reproduction", action="store_true")
    args = parser.parse_args(argv)
    if not args.legacy_reproduction:
        print(
            "v8 EGS table is legacy_reproduction_only; no active table is emitted",
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
