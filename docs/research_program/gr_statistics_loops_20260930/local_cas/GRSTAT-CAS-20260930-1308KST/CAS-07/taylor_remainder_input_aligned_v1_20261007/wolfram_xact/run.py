#!/usr/bin/env python3
"""Run only the frozen CAS-07 M02 Wolfram/xTensor axis from the repository root."""

import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import time


HERE = Path(__file__).resolve().parent
ROOT = Path.cwd().resolve()
BASE = Path("docs/research_program/gr_statistics_loops_20260930/local_cas/GRSTAT-CAS-20260930-1308KST/CAS-07/taylor_remainder_input_aligned_v1_20261007")
EXPECTED = {
    BASE / "EXECUTION_CONTRACT.json": "eacc294fa147bd4cabaf295c76f29814b461cae2c8d10eb0a44fdbe2254e0799",
    BASE / "ADMITTED_INPUTS.json": "18bfcfb302209caaeac08df72137040ea0939826c551045e7f798d86921db125",
    Path("docs/research_program/gr_statistics_loops_20260930/cas/COMMON_SPEC.md"): "4714827e52acf3cb149f4014ac50ab2aa995dd4a0526f6b26ac7257807fe1897",
}
CHECK_IDS = (
    "CAS-07-M02-REMAINDER-IDENTITY",
    "CAS-07-M02-REMAINDER-BOUND",
)


def sha256(path):
    h = hashlib.sha256()
    with Path(path).open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def artifact(command):
    named = shutil.which(command)
    if not named:
        return {"command": command, "path": None, "sha256": None}
    path = Path(named).resolve()
    return {"command": command, "path": str(path), "sha256": sha256(path)}


def main():
    result = {
        "axis": "wolfram_xact",
        "contract_id": "GRSTAT-20260930-CAS-07-M02-TAYLOR-REMAINDER-V1",
        "checks": {name: False for name in CHECK_IDS},
        "domain_assumption_diff": [],
        "counterexample": None,
        "status": "BLOCKED",
        "actual_model": "UNKNOWN",
        "actual_effort": "UNKNOWN",
        "global_launch_id": None,
        "source_hashes": {},
        "artifacts": {},
    }
    try:
        for rel, expected in EXPECTED.items():
            path = ROOT / rel
            actual = sha256(path)
            result["source_hashes"][str(rel)] = actual
            if actual != expected:
                raise RuntimeError(f"frozen input hash mismatch: {rel}: {actual}")
        if HERE != (ROOT / BASE / "wolfram_xact"):
            raise RuntimeError("must execute from repository root with the assigned axis path")
        script = HERE / "check.wl"
        result["artifacts"]["check.wl"] = sha256(script)
        result["artifacts"]["run.py"] = sha256(__file__)
        result["artifacts"]["wolframscript"] = artifact("wolframscript")
        result["artifacts"]["WolframKernel"] = artifact("WolframKernel")
        if result["artifacts"]["wolframscript"]["path"] is None:
            raise RuntimeError("wolframscript executable unavailable")
        argv = ["wolframscript", "-file", str(script)]
        start = time.monotonic()
        try:
            process = subprocess.run(argv, cwd=ROOT, capture_output=True, text=True, timeout=1800)
            out, err, code = process.stdout, process.stderr, process.returncode
        except subprocess.TimeoutExpired as ex:
            out = ex.stdout.decode(errors="replace") if isinstance(ex.stdout, bytes) else (ex.stdout or "")
            err = ex.stderr.decode(errors="replace") if isinstance(ex.stderr, bytes) else (ex.stderr or "")
            code = "TIMEOUT"
        (HERE / "run.stdout.log").write_text(out)
        (HERE / "run.stderr.log").write_text(err)
        result["execution"] = {"argv": argv, "cwd": str(ROOT), "exit_code": code,
                               "wall_seconds": round(time.monotonic() - start, 6),
                               "stdout_path": str(HERE / "run.stdout.log"),
                               "stderr_path": str(HERE / "run.stderr.log")}
        result["artifacts"]["run.stdout.log"] = sha256(HERE / "run.stdout.log")
        result["artifacts"]["run.stderr.log"] = sha256(HERE / "run.stderr.log")
        lines = [line.split("=", 1)[1] for line in out.splitlines()
                 if line.startswith("CAS07_RESULT_JSON=")]
        if len(lines) != 1:
            raise RuntimeError(f"expected one CAS result line, saw {len(lines)}")
        cas = json.loads(lines[0])
        result["engine_version"] = cas.get("engine_version")
        result["xTensor_version"] = cas.get("xTensor_version")
        xfile = cas.get("xTensor_package_file")
        if isinstance(xfile, str) and Path(xfile).is_file():
            result["artifacts"]["xTensor_package_file"] = {"path": xfile, "sha256": sha256(xfile)}
        result["details"] = cas.get("details")
        result["xTensor_expression"] = cas.get("xTensor_expression")
        result["proof_schema"] = cas.get("proof_schema")
        if code == 0 and set(cas.get("checks", {})) == set(CHECK_IDS) and all(
            cas["checks"][name] is True for name in CHECK_IDS
        ) and all(value is True for value in cas.get("details", {}).values()) and err == "":
            result["checks"] = {name: True for name in CHECK_IDS}
            result["status"] = "PASS_FINITE_COMPONENT"
        else:
            result["status"] = "FAIL_OR_INCONCLUSIVE"
            result["error"] = "CAS check false, nonzero exit, or stderr diagnostics; inspect raw logs"
    except Exception as ex:
        result["error"] = f"{type(ex).__name__}: {ex}"
    encoded = json.dumps(result, sort_keys=True, separators=(",", ":"))
    (HERE / "result.json").write_text(encoded + "\n")
    sys.stdout.write(encoded + "\n")
    return 0 if result["status"] == "PASS_FINITE_COMPONENT" else 1


if __name__ == "__main__":
    raise SystemExit(main())
