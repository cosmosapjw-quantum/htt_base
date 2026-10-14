"""Print exactly one JSON document for the CAS-07 M02 SymPy axis."""

from __future__ import annotations

import json
import traceback

from check import check


if __name__ == "__main__":
    try:
        result = check()
        print(json.dumps(result, sort_keys=True, separators=(",", ":")))
        raise SystemExit(0 if all(result["checks"].values()) else 1)
    except Exception as exc:
        traceback.print_exc()
        print(json.dumps({
            "checks": {
                "CAS-07-M02-REMAINDER-IDENTITY": False,
                "CAS-07-M02-REMAINDER-BOUND": False,
            },
            "domain_assumption_diff": [],
            "counterexample": None,
            "execution_error": f"{type(exc).__name__}: {exc}",
        }, sort_keys=True, separators=(",", ":")))
        raise SystemExit(1)
