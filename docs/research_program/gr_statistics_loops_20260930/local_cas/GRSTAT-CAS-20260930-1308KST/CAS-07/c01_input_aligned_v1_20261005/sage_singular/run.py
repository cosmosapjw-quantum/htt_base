"""Run and retain independent Sage/Singular CAS-07-C01 evidence."""
import datetime
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import time

REPO = Path("/home/cosmosapjw/Dropbox/bianchi/htt_base")
BASE = REPO / "docs/research_program/gr_statistics_loops_20260930/local_cas/GRSTAT-CAS-20260930-1308KST/CAS-07/c01_input_aligned_v1_20261005"
OWN = BASE / "sage_singular"
CONTRACT = BASE / "EXECUTION_CONTRACT.json"
ADMITTED = BASE / "ADMITTED_INPUTS.json"
COMMON = REPO / "docs/research_program/gr_statistics_loops_20260930/cas/COMMON_SPEC.md"
SAGE = Path("/home/cosmosapjw/opt/sage/sage")
SINGULAR = Path("/home/cosmosapjw/opt/sage/local/bin/Singular")
EXPECTED = {
    CONTRACT: "e5342381440cb6456ad27add75a9d23faa52a01b1a0f5998599e3026452a9f1a",
    ADMITTED: "30bbb6fce513eedfd98a693c2acbf3308363a7098a7938f4b5abf7e9282b2e39",
    COMMON: "4714827e52acf3cb149f4014ac50ab2aa995dd4a0526f6b26ac7257807fe1897",
}

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def hashes(paths):
    return {str(path): sha(path) for path in paths}

def rel(path):
    return str(path.relative_to(REPO)) if path.is_relative_to(REPO) else str(path)

def write_json(path, obj):
    path.write_text(json.dumps(obj, indent=2, sort_keys=True) + "\n")

def run(name, argv, attempt):
    started = datetime.datetime.now(datetime.timezone.utc).isoformat()
    begin = time.monotonic()
    try:
        p = subprocess.run(argv, cwd=REPO, capture_output=True, text=True, timeout=1800)
        rc, out, err, timeout = p.returncode, p.stdout, p.stderr, False
    except subprocess.TimeoutExpired as exc:
        rc = None
        out = exc.stdout.decode(errors="replace") if isinstance(exc.stdout, bytes) else (exc.stdout or "")
        err = exc.stderr.decode(errors="replace") if isinstance(exc.stderr, bytes) else (exc.stderr or "")
        timeout = True
    (attempt / (name + ".stdout")).write_text(out)
    (attempt / (name + ".stderr")).write_text(err)
    return {
        "argv": list(map(str, argv)), "cwd": str(REPO), "exit_code": rc,
        "timeout": timeout, "started_at": started,
        "duration_seconds": round(time.monotonic() - begin, 6),
        "stdout_path": rel(attempt / (name + ".stdout")),
        "stderr_path": rel(attempt / (name + ".stderr")),
    }, out, err

def marker(text, key):
    match = re.search(rf"{key}_BEGIN\s*\n(.*?)\n{key}_END", text, re.S)
    return match.group(1).strip() if match else None

def main():
    OWN.mkdir(parents=True, exist_ok=True)
    numbered = [int(p.name.split("_")[1]) for p in OWN.glob("attempt_[0-9][0-9][0-9]") if p.is_dir()]
    attempt = OWN / f"attempt_{max(numbered, default=0)+1:03d}"
    attempt.mkdir(exist_ok=False)
    source_paths = [OWN / "run.py", OWN / "sage_component.py", OWN / "singular_component.sing"]
    input_paths = list(EXPECTED)
    tool_paths = [SAGE, SINGULAR]
    before = {"source": hashes(source_paths), "input": hashes(input_paths), "executable": hashes(tool_paths)}
    write_json(attempt / "hashes_before.json", before)
    commands = []
    failures = []
    if any(before["input"][str(p)] != digest for p, digest in EXPECTED.items()):
        failures.append("frozen_input_hash_mismatch")
    sage_data = {}
    singular_data = {}
    for name, argv in [
        ("sage", [str(SAGE), "-python", str(OWN / "sage_component.py")]),
        ("singular", [str(SINGULAR), "-q", str(OWN / "singular_component.sing")]),
    ]:
        command, out, err = run(name, argv, attempt)
        commands.append(command)
        if command["timeout"] or command["exit_code"] != 0:
            failures.append(f"{name}_execution_failed_or_timed_out")
        if name == "sage":
            try:
                sage_data = json.loads(out.strip())
            except (ValueError, TypeError):
                failures.append("sage_output_not_single_json")
            if err.strip():
                failures.append("sage_stderr_nonempty_inspect_raw")
        else:
            singular_data = {
                "version": marker(out, "SINGULAR_VERSION"),
                "ode_residual": marker(out, "ODE_RESIDUAL"),
                "integral_residual": marker(out, "INTEGRAL_RESIDUAL"),
            }
            if singular_data != {"version": "44100", "ode_residual": "0", "integral_residual": "0"}:
                failures.append("singular_version_or_algebra_certificate_mismatch")
            if err.strip() or "?" in out or "error" in out.lower():
                failures.append("singular_diagnostic_inspect_raw")
    after = {"source": hashes(source_paths), "input": hashes(input_paths), "executable": hashes(tool_paths)}
    write_json(attempt / "hashes_after.json", after)
    if before != after:
        failures.append("source_input_or_executable_drift")
    checks = sage_data.get("checks", {})
    if not checks or not all(value is True for value in checks.values()):
        failures.append("sage_exact_component_check_failed")
    if sage_data.get("expressions", {}).get("integral_residual") != "0":
        failures.append("sage_integral_residual_not_zero")
    status = "PASS" if not failures else "INCONCLUSIVE"
    completed_at = datetime.datetime.now(datetime.timezone.utc).isoformat()
    result = {
        "axis": "sage_singular", "status": status,
        "contract_sha256": EXPECTED[CONTRACT], "evidence_class": "exact",
        "completed_at": completed_at,
        "checks": {"CAS-07-C01": status == "PASS"},
        "details": {"sage": sage_data, "singular": singular_data},
        "domain_assumption_diff": [], "counterexample": None,
        "commands": commands,
        "source_hashes_before": {rel(Path(p)): h for p,h in before["source"].items()},
        "source_hashes_after": {rel(Path(p)): h for p,h in after["source"].items()},
        "input_hashes_before": {rel(Path(p)): h for p,h in before["input"].items()},
        "input_hashes_after": {rel(Path(p)): h for p,h in after["input"].items()},
        "executable_hashes_before": before["executable"],
        "executable_hashes_after": after["executable"],
        "tool_pins": {"sage_path": str(SAGE), "singular_path": str(SINGULAR),
                      "sage_version": sage_data.get("sage_version"),
                      "singular_version_code": singular_data.get("version")},
        "statement_alignment": "Exact CAS-07-C01 scalar hyperbolic branch, initial values, ODE, actual interval integral and separate Kc=0 fixed-s right limit; no C02/C03 or Jacobi/physical theorem claim.",
        "raw_failures": failures,
        "attempt_path": rel(attempt),
        "author_runtime": {"requested": "gpt-6-sol high", "observed": "unknown"},
        "usage": "unknown",
    }
    write_json(attempt / "result.json", result)
    write_json(OWN / "result.json", result)
    print(json.dumps({"checks": {"CAS-07-C01": status == "PASS"},
                      "details": {"sage": checks, "singular": singular_data, "raw_failures": failures},
                      "domain_assumption_diff": [], "counterexample": None}, sort_keys=True))
    return 0 if status == "PASS" else 1

if __name__ == "__main__":
    sys.exit(main())
