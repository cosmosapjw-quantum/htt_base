#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = [
    "rotation_covariance_test.py",
    "lowell_shell_poles_demo.py",
    "local_boost_global_tilt_benchmark.py",
    "remote_fields_demo.py",
    "coherent_fraction_demo.py",
    "plugin_probe.py",
    "pole_response_rank_demo.py",
    "binning_stability_demo.py",
    "shell_kernel_conservation_demo.py",
    "adaptive_scan_evalue_demo.py",
]


def main() -> int:
    out = {}
    failed = []
    for name in SCRIPTS:
        p = ROOT / "experiments" / name
        proc = subprocess.run([sys.executable, str(p)], cwd=ROOT, text=True, capture_output=True)
        try:
            payload = json.loads(proc.stdout)
        except json.JSONDecodeError:
            payload = {"raw_stdout": proc.stdout, "stderr": proc.stderr}
        out[name] = {"exit_code": proc.returncode, "payload": payload}
        if proc.returncode != 0:
            failed.append(name)
    path = ROOT / "outputs" / "reference_results.json"
    path.write_text(json.dumps(out, indent=2, sort_keys=True), encoding="utf-8")
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    summary = {"status": "PASS" if not failed else "FAIL", "scripts": len(SCRIPTS), "failed": failed, "output": str(path.relative_to(ROOT)), "sha256": digest}
    print(json.dumps(summary, indent=2))
    return 0 if not failed else 2


if __name__ == "__main__":
    raise SystemExit(main())
