#!/usr/bin/env python3
"""Execute the independent CAS-05-v3 Wolfram/xCoba axis on every invocation."""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys
from datetime import datetime, timezone


ROOT = Path("/home/cosmosapjw/Dropbox/bianchi/htt_base")
HERE = Path(__file__).resolve().parent
SOURCE = HERE / "axis.wl"
INPUTS = {
    "contract": (
        ROOT / "docs/research_program/gr_statistics_loops_20260930/local_cas/"
        "GRSTAT-CAS-20260930-1308KST/CAS-05/neutral_admission_20261003/"
        "EXECUTION_CONTRACT_V3.json",
        "a67bf54921c80d35865d28dfce86d0ff9670270a807d5f2f45f25e3e7029537f",
    ),
    "neutral": (
        ROOT / "docs/research_program/gr_statistics_loops_20260930/local_cas/"
        "GRSTAT-CAS-20260930-1308KST/CAS-05/neutral_admission_20261003/"
        "NEUTRAL_INPUT.json",
        "0868c1f15226e71926dad034319b85c73a9ca9c7d3c72064e06ff65d0112b27b",
    ),
    "common": (
        ROOT / "docs/research_program/gr_statistics_loops_20260930/cas/COMMON_SPEC.md",
        "4714827e52acf3cb149f4014ac50ab2aa995dd4a0526f6b26ac7257807fe1897",
    ),
}
OBLIGATIONS = ("CAS-05-C01", "CAS-05-C02", "CAS-05-C03")


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> int:
    command = ["wolframscript", "-file", str(SOURCE)]
    completed_at = datetime.now(timezone.utc).isoformat()
    run_dir = HERE / "runs" / (datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ") + f"-{os.getpid()}")
    run_dir.mkdir(parents=True, exist_ok=False)
    hashes = {name: {"path": str(path), "sha256": sha(path), "expected_sha256": expected}
              for name, (path, expected) in INPUTS.items()}
    hashes["axis_source"] = {"path": str(SOURCE), "sha256": sha(SOURCE)}
    drift = [name for name, item in hashes.items()
             if "expected_sha256" in item and item["sha256"] != item["expected_sha256"]]
    raw_out = ""
    raw_err = ""
    exit_code = None
    parsed = None
    failure = None
    if drift:
        failure = "Frozen input SHA-256 mismatch: " + ", ".join(drift)
    else:
        try:
            process = subprocess.run(command, cwd=ROOT, capture_output=True, text=True,
                                     timeout=1800, check=False)
            raw_out, raw_err, exit_code = process.stdout, process.stderr, process.returncode
            matches = re.findall(r"AXIS_JSON_START(.*?)AXIS_JSON_END", raw_out, flags=re.DOTALL)
            if len(matches) != 1:
                failure = f"Expected one engine JSON marker pair, found {len(matches)}"
            else:
                parsed = json.loads(matches[0])
        except subprocess.TimeoutExpired as exc:
            raw_out = (exc.stdout or b"").decode(errors="replace") if isinstance(exc.stdout, bytes) else (exc.stdout or "")
            raw_err = (exc.stderr or b"").decode(errors="replace") if isinstance(exc.stderr, bytes) else (exc.stderr or "")
            failure = "Wolfram process exceeded 1800 seconds"
            exit_code = 124
        except (OSError, json.JSONDecodeError) as exc:
            failure = f"Execution or JSON parse failed: {exc}"
    (run_dir / "stdout.txt").write_text(raw_out)
    (run_dir / "stderr.txt").write_text(raw_err)
    checks = (parsed or {}).get("checks", {})
    if set(checks) != set(OBLIGATIONS) or any(type(value) is not bool for value in checks.values()):
        failure = failure or "Engine returned malformed component checks"
        checks = {name: False for name in OBLIGATIONS}
    if exit_code != 0:
        failure = failure or f"Engine exited {exit_code}"
    assumption_diff = (parsed or {}).get("domain_assumption_diff", [])
    if drift:
        assumption_diff = assumption_diff + [failure]
    counterexample = (parsed or {}).get("counterexample")
    if failure or not all(checks.values()):
        counterexample = counterexample or failure or "One or more exact component residuals failed"
    status = "PASS" if not failure and all(checks.values()) and not assumption_diff and counterexample is None else "FAIL"
    completed_at = datetime.now(timezone.utc).isoformat()
    envelope = {
        "axis": "wolfram_xact",
        "contract_id": "GRSTAT-20260930-CAS-05-V3-NEUTRAL",
        "contract_version": 3,
        "contract_sha256": INPUTS["contract"][1],
        "status": status,
        "evidence_class": "exact",
        "completed_at": completed_at,
        "checks": checks,
        "domain_assumption_diff": assumption_diff,
        "counterexample": counterexample,
        "computed": (parsed or {}).get("computed", {}),
        "commands": [{"argv": command, "cmd": " ".join(command), "cwd": str(ROOT), "exit": exit_code,
                      "timeout_seconds": 1800}],
        "toolchain_version": ((parsed or {}).get("computed") or {}).get("engine"),
        "source_and_input_hashes": hashes,
        "raw_stdout": str(run_dir / "stdout.txt"),
        "raw_stderr": str(run_dir / "stderr.txt"),
        "run_dir": str(run_dir),
        "author_runtime": {"actor": "current Codex child", "observed_model_id": None,
                           "observed_effort": None},
        "claim_ceiling": "finite CAS-05 C01-C03 only; no full theorem or scientific admission",
    }
    (run_dir / "result.json").write_text(json.dumps(envelope, indent=2, sort_keys=True) + "\n")
    temp = HERE / f"result.json.tmp.{os.getpid()}"
    temp.write_text(json.dumps(envelope, indent=2, sort_keys=True) + "\n")
    os.replace(temp, HERE / "result.json")
    payload = {"checks": checks, "domain_assumption_diff": assumption_diff,
               "counterexample": counterexample, "computed": envelope["computed"],
               "axis": envelope["axis"], "contract_sha256": envelope["contract_sha256"],
               "result_path": str(HERE / "result.json")}
    sys.stdout.write(json.dumps(payload, separators=(",", ":")) + "\n")
    return 0 if status == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
