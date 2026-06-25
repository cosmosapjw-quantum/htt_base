#!/usr/bin/env python3
from __future__ import annotations

import argparse
import ast
import json
from pathlib import Path

FORBIDDEN = (
    "truth_engine",
    "flrw_cl_toy",
    "forward.htt_bridge",
    "forward.mio_bridge",
    "inference.atlas",
    "atlas_export",
)
NEW = (
    "htt/htt/htt/common/stf_canonical.py",
    "htt/htt/htt/common/multicomponent_blocks.py",
    "htt/bass/observer/congruence_ssot.py",
    "htt/htt/htt/departure/multicomponent_response.py",
    "htt/bass/background/bi_continuation/moments.py",
    "htt/bass/background/bi_continuation/dynamics.py",
    "htt/mio/formalism/physical_pushforward.py",
    "htt/htt/htt/integration/pr04_canonical_bridge.py",
)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo", type=Path, required=True)
    args = ap.parse_args()

    bad: list[dict[str, str]] = []
    for rel in NEW:
        path = args.repo / rel
        if not path.exists():
            bad.append({"file": rel, "issue": "missing"})
            continue
        tree = ast.parse(path.read_text(), filename=str(path))
        names: list[str] = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                names.extend(alias.name for alias in node.names)
            elif isinstance(node, ast.ImportFrom):
                names.append(node.module or "")
        for name in names:
            if any(token in name for token in FORBIDDEN):
                bad.append({"file": rel, "import": name})

    print(json.dumps({"status": "PASS" if not bad else "FAIL", "findings": bad}, indent=2))
    return 1 if bad else 0


if __name__ == "__main__":
    raise SystemExit(main())
