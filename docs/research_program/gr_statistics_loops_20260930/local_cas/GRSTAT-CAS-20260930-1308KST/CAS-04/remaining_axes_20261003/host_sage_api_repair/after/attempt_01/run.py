"""Bounded CAS-04 Sage/Singular runner; stdout is one JSON payload."""
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
from datetime import datetime, timezone

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[7]
CONTRACT = ROOT / "docs/research_program/gr_statistics_loops_20260930/local_cas/GRSTAT-CAS-20260930-1308KST/CAS-04/EXECUTION_CONTRACT.json"
SPEC = ROOT / "docs/research_program/gr_statistics_loops_20260930/cas/COMMON_SPEC.md"
EXPECTED_CONTRACT = "058da4a8716fd06bc67100b8490df88a6783b780ac0ff66bf1221a02ab7e8741"
EXPECTED_SPEC = "4714827e52acf3cb149f4014ac50ab2aa995dd4a0526f6b26ac7257807fe1897"
OBLIGATIONS = [f"CAS-04-C{i:02d}" for i in range(1,5)]
TIMEOUT = 1800


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def utc():
    return datetime.now(timezone.utc).isoformat()


def invoke(label, argv):
    began = utc()
    timed_out = False
    launch_error = None
    try:
        done = subprocess.run(argv, cwd=HERE, capture_output=True,
                              timeout=TIMEOUT, check=False)
        code, out, err = done.returncode, done.stdout, done.stderr
    except subprocess.TimeoutExpired as exc:
        code, out, err, timed_out = None, exc.stdout or b"", exc.stderr or b"", True
    except OSError as exc:
        code, out, err, launch_error = None, b"", b"", str(exc)
    (HERE / f"{label}.stdout.log").write_bytes(out)
    (HERE / f"{label}.stderr.log").write_bytes(err)
    return {
        "argv": argv, "cwd": str(HERE), "started_at": began,
        "completed_at": utc(), "exit_code": code, "timed_out": timed_out,
        "launch_error": launch_error, "timeout_seconds": TIMEOUT,
        "stdout_path": f"{label}.stdout.log", "stderr_path": f"{label}.stderr.log",
        "stdout_sha256": digest(HERE / f"{label}.stdout.log"),
        "stderr_sha256": digest(HERE / f"{label}.stderr.log"),
    }


def main():
    issues = []
    for label, path, expected in [("contract", CONTRACT, EXPECTED_CONTRACT),
                                  ("common_spec", SPEC, EXPECTED_SPEC)]:
        actual = digest(path)
        if actual != expected:
            issues.append(f"{label} SHA mismatch: {actual}")
    commands = []
    checks = {key: False for key in OBLIGATIONS}
    sage_data = None
    singular_markers = {}
    if not issues:
        commands.append(invoke("sage", ["sage", "-python", str(HERE / "engine.py")]))
        commands.append(invoke("singular", ["Singular", "-q", str(HERE / "singular_cert.sing")]))
        if commands[0]["exit_code"] == 0:
            try:
                sage_data = json.loads((HERE / "sage.stdout.log").read_text())
                if set(sage_data["checks"]) != set(OBLIGATIONS):
                    issues.append("Sage checks do not exactly match obligations")
            except (ValueError, KeyError, TypeError) as exc:
                issues.append(f"Sage JSON parse/schema: {exc}")
        else:
            issues.append("Sage engine failed or timed out")
        if commands[1]["exit_code"] == 0:
            for line in (HERE / "singular.stdout.log").read_text().splitlines():
                if "=" in line:
                    k, value = line.split("=", 1)
                    singular_markers[k.strip()] = value.strip()
            for key in ["SAT_EQUAL", "INVERSE_PRODUCT", "TWELVE_ROW_RESIDUALS"]:
                if singular_markers.get(key) != "1":
                    issues.append(f"Singular certificate {key} != 1")
        else:
            issues.append("Singular engine failed or timed out")
        if sage_data and not issues:
            checks = sage_data["checks"]
    payload = {"checks": checks, "domain_assumption_diff": [], "counterexample": None}
    status = "PASS" if not issues and all(checks.values()) else "INCONCLUSIVE" if issues else "FAIL"
    result = {
        "axis": "sage_singular", "status": status,
        "contract_sha256": EXPECTED_CONTRACT,
        "common_spec_sha256": EXPECTED_SPEC,
        "evidence_class": "exact", "completed_at": utc(),
        "commands": commands, "payload": payload, "issues": issues,
        "singular_markers": singular_markers,
        "sage_version": sage_data.get("sage_version") if sage_data else None,
        "singular_version_code": sage_data.get("singular_version_code") if sage_data else None,
        "source_sha256": {name: digest(HERE / name) for name in ["run.py", "engine.py", "singular_cert.sing"]},
        "claim_ceiling": "specified_mathematical_component_only_no_scientific_admission",
        "author_runtime": "native Codex child; observed model/effort unavailable to process",
        "shared_llm_family": "OpenAI GPT family; cross-axis independence limited to blind inputs",
    }
    (HERE / "AXIS_RESULT.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    sys.stdout.write(json.dumps(payload, sort_keys=True) + "\n")
    if status != "PASS":
        sys.exit(2)


if __name__ == "__main__":
    main()
