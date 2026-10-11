"""Emit exactly one CAS-07 C03 SymPy result document on stdout."""

from __future__ import annotations

import json
import sys
import traceback

from check import run_checks


def main() -> int:
    try:
        flat = run_checks()
        result = {
            "checks": {key: flat[key] for key in (
                "CAS-07-C03-FD1", "CAS-07-C03-FD2", "CAS-07-C03-FD3")},
            "domain_assumption_diff": flat["domain_assumption_diff"],
            "counterexample": flat["counterexample"],
        }
    except Exception as exc:
        traceback.print_exc(file=sys.stderr)
        result = {
            "checks": {
                "CAS-07-C03-FD1": False,
                "CAS-07-C03-FD2": False,
                "CAS-07-C03-FD3": False,
            },
            "domain_assumption_diff": [],
            "counterexample": {"kind": "execution_error", "detail": str(exc)},
        }
    print(json.dumps(result, sort_keys=True, separators=(",", ":")))
    return 0 if all(result["checks"][key] for key in (
        "CAS-07-C03-FD1", "CAS-07-C03-FD2", "CAS-07-C03-FD3")) else 1


if __name__ == "__main__":
    raise SystemExit(main())
