#!/usr/bin/env python3
"""Runner-owned Sage and pinned Singular replay for observed adjudication."""

import hashlib
import json
import pathlib
import subprocess

here = pathlib.Path(__file__).resolve().parent
singular = pathlib.Path("/home/cosmosapjw/opt/sage/local/bin/Singular")
expected_singular_sha = "9430832b7c972b6b26d29ded4d91a3e1df8fd87d67f4b8d3f14d8201a75f923c"

sage = subprocess.run(
    ["sage", "-python", str(here / "c03_inverse_truncation.py")],
    cwd=here,
    capture_output=True,
    text=True,
    check=False,
)
sing = subprocess.run(
    [str(singular), "-q", str(here / "c03_inverse_truncation.sing")],
    cwd=here,
    capture_output=True,
    text=True,
    check=False,
)
for name, proc in (("sage.runner", sage), ("singular.runner", sing)):
    (here / f"{name}.stdout.log").write_text(proc.stdout, encoding="utf-8")
    (here / f"{name}.stderr.log").write_text(proc.stderr, encoding="utf-8")
singular_sha = hashlib.sha256(singular.read_bytes()).hexdigest()
sage_ok = sage.returncode == 0 and not sage.stderr.strip() and "RESULT exact finite CAS-03-C03 identities and controls PASS" in sage.stdout
sing_ok = (
    sing.returncode == 0
    and not sing.stderr.strip()
    and singular_sha == expected_singular_sha
    and "TOTAL_FAILURES 0" in sing.stdout
    and "FAIL " not in sing.stdout
    and "?" not in sing.stdout
)
ok = sage_ok and sing_ok
print(json.dumps({
    "status": "PASS" if ok else "FAIL",
    "checks": {"CAS-03-C03": ok},
    "domain_assumption_diff": [],
    "counterexample": None if ok else "Sage or pinned Singular replay did not satisfy all exact checks",
    "result_path": str(here / "result.json"),
}, separators=(",", ":")))
raise SystemExit(0 if ok else 1)
