"""Plain-Python gate entrypoint for the pinned Sage/Singular C04 certificate."""

import json
import subprocess
import sys
import traceback
from pathlib import Path


HERE = Path(__file__).resolve().parent
SAGE = Path("/usr/local/bin/sage")


def repo_root():
    for parent in HERE.parents:
        if (parent / ".git").exists():
            return parent
    raise RuntimeError("repository root unavailable")


def main():
    child = subprocess.run(
        [str(SAGE), "-python", str(HERE / "sage_impl.py")],
        cwd=repo_root(), capture_output=True, text=True, timeout=1800, check=False,
    )
    (HERE / "sage_impl.stdout.log").write_text(child.stdout)
    (HERE / "sage_impl.stderr.log").write_text(child.stderr)
    try:
        payload = json.loads(child.stdout)
        good = (child.returncode == 0 and child.stderr == "" and
                payload["checks"] == {"CAS-02-C04": True} and
                payload["domain_assumption_diff"] == [] and
                payload["counterexample"] is None)
    except (ValueError, KeyError, TypeError):
        good = False
    result = {"checks": {"CAS-02-C04": good},
              "domain_assumption_diff": [], "counterexample": None}
    print(json.dumps(result, separators=(",", ":"), sort_keys=True))
    return 0 if good else 2


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception:
        (HERE / "wrapper.error.log").write_text(traceback.format_exc())
        # Keep the gate's stdout a single document and its stderr empty.
        print(json.dumps({"checks": {"CAS-02-C04": False},
                          "domain_assumption_diff": [], "counterexample": None},
                         separators=(",", ":"), sort_keys=True))
        sys.exit(2)
