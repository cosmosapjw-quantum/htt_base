#!/usr/bin/env python3
"""Read-only W2 convention and active-source check.

The former PR-186 result-card writer was retired with the pre-current report
surface. This entrypoint retains the directly useful mathematical regression
without recreating a tracked historical card.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


REPO = Path(__file__).resolve().parents[2]
for entry in (str(REPO / "htt"), str(REPO / "htt" / "src")):
    if entry not in sys.path:
        sys.path.insert(0, entry)

from common.w2_convention import (  # noqa: E402
    ceiling_conversion_symbolic,
    scan_active_sources,
    vorticity_tensor_vector_identity,
)


def check_payload() -> dict[str, object]:
    numeric = vorticity_tensor_vector_identity(100_000)
    symbolic = ceiling_conversion_symbolic()
    scan = scan_active_sources(REPO)
    ok = bool(
        numeric["ok"]
        and symbolic["ok"]
        and symbolic["tensor_vector_forms_equal"]
        and symbolic["wrong_over_right_ratio"] == "3"
        and scan["clean"]
    )
    return {
        "mode": "check",
        "ok": ok,
        "read_only": True,
        "scientific_effect": "none",
        "claim_promotion": False,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true", required=True)
    parser.parse_args(argv)
    payload = check_payload()
    print(json.dumps(payload, sort_keys=True))
    return 0 if payload["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
