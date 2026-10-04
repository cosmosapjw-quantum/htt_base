#!/usr/bin/python3.12
"""Execute the independent C01 Wolfram/xTensor certificate with raw evidence."""

import datetime as dt
import hashlib
import json
import re
import shutil
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[8]
HERE = Path(__file__).resolve().parent
P = HERE.parent
CONTRACT = P / "EXECUTION_CONTRACT.json"
INPUTS = P / "ADMITTED_INPUTS.json"
COMMON = ROOT / "docs/research_program/gr_statistics_loops_20260930/cas/COMMON_SPEC.md"
SOURCE = HERE / "proof.wl"
RUNNER = Path(__file__).resolve()
EXPECTED = {
    CONTRACT: "4d3a35a731ce79d47490d54843239a5bf3f7c670015916356b95504cf5be6f3f",
    INPUTS: "a5189ee52fc769c284c604a4caf29051f0256973d5c5bf9dc0f439a4acecdb46",
    COMMON: "4714827e52acf3cb149f4014ac50ab2aa995dd4a0526f6b26ac7257807fe1897",
}
TASK = "GRSTAT-CAS-20260930-1308KST-CAS-03"


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def save_json(path: Path, value: dict) -> None:
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def main() -> int:
    before = {str(p.relative_to(ROOT)): sha(p) for p in (*EXPECTED, SOURCE, RUNNER)}
    attempts = HERE / "attempts"
    attempts.mkdir(exist_ok=True)
    n = 1
    while (attempts / f"attempt_{n:03d}").exists():
        n += 1
    evidence = attempts / f"attempt_{n:03d}"
    evidence.mkdir()
    shutil.copy2(SOURCE, evidence / "proof.wl")
    shutil.copy2(RUNNER, evidence / "run.py")
    argv = [
        "cuhg-telemetry", "run", "--project", "repo", "--task", TASK,
        "--", "wolframscript", "-file", str(SOURCE),
    ]
    start = dt.datetime.now(dt.timezone.utc)
    try:
        proc = subprocess.run(argv, cwd=ROOT, capture_output=True, text=True,
                              errors="replace", timeout=1800, check=False)
        code, stdout, stderr, timed_out = proc.returncode, proc.stdout, proc.stderr, False
    except subprocess.TimeoutExpired as exc:
        code = None
        stdout = exc.stdout.decode(errors="replace") if isinstance(exc.stdout, bytes) else (exc.stdout or "")
        stderr = exc.stderr.decode(errors="replace") if isinstance(exc.stderr, bytes) else (exc.stderr or "")
        timed_out = True
    end = dt.datetime.now(dt.timezone.utc)
    (evidence / "stdout.log").write_text(stdout, encoding="utf-8")
    (evidence / "stderr.log").write_text(stderr, encoding="utf-8")
    after = {str(p.relative_to(ROOT)): sha(p) for p in (*EXPECTED, SOURCE, RUNNER)}
    markers = [m.end() for m in re.finditer("C01_RESULT_JSON=", stdout)]
    payload = None
    parse_error = None
    try:
        if len(markers) != 1:
            raise ValueError(f"expected one result marker, got {len(markers)}")
        payload, _ = json.JSONDecoder().raw_decode(stdout[markers[0]:].lstrip())
    except (ValueError, json.JSONDecodeError) as exc:
        parse_error = str(exc)
    messages = re.findall(r"\b[A-Za-z][A-Za-z0-9`]*::[A-Za-z][A-Za-z0-9]*", stdout + "\n" + stderr)
    check = (payload or {}).get("checks", {}).get("CAS-03-C01")
    subchecks = (payload or {}).get("subchecks", {})
    input_ok = all(before[str(p.relative_to(ROOT))] == wanted for p, wanted in EXPECTED.items())
    stable = before == after
    passed = (code == 0 and not timed_out and input_ok and stable and not messages
              and parse_error is None and check is True and bool(subchecks)
              and all(value is True for value in subchecks.values())
              and payload.get("domain_assumption_diff") == []
              and payload.get("counterexample") is None)
    errors = []
    if not input_ok:
        errors.append("frozen input hash mismatch")
    if not stable:
        errors.append("source or input changed during execution")
    if code != 0:
        errors.append(f"engine exit {code}")
    if timed_out:
        errors.append("engine timeout at 1800 seconds")
    if messages:
        errors.append("Wolfram messages: " + ", ".join(sorted(set(messages))))
    if parse_error:
        errors.append("result parse: " + parse_error)
    if check is not True:
        errors.append("C01 check did not return true")
    if any(value is not True for value in subchecks.values()):
        errors.append("one or more subchecks did not return true")
    if payload and payload.get("domain_assumption_diff") != []:
        errors.append("domain assumption difference")
    if payload and payload.get("counterexample") is not None:
        errors.append("counterexample returned")
    command = {
        "argv": argv, "cwd": str(ROOT), "exit_code": code,
        "timed_out": timed_out, "started_at": start.isoformat(),
        "completed_at": end.isoformat(), "wall_seconds": (end - start).total_seconds(),
    }
    attempt = {
        "command": command, "source_input_sha256_before": before,
        "source_input_sha256_after": after, "expected_sha256":
        {str(p.relative_to(ROOT)): h for p, h in EXPECTED.items()},
        "payload": payload, "wolfram_messages": messages,
        "errors": errors, "stdout_sha256": sha(evidence / "stdout.log"),
        "stderr_sha256": sha(evidence / "stderr.log"),
        "source_snapshot_sha256": sha(evidence / "proof.wl"),
        "runner_snapshot_sha256": sha(evidence / "run.py"),
    }
    save_json(evidence / "execution.json", attempt)
    result = {
        "axis": "wolfram_xact", "status": "PASS" if passed else "INCONCLUSIVE",
        "contract_sha256": EXPECTED[CONTRACT], "evidence_class": "exact",
        "completed_at": end.isoformat(), "commands": [command],
        "engine": {
            "wolfram_version": re.findall(r"^WOLFRAM_VERSION=(.*)$", stdout, re.M),
            "xtensor_version": re.findall(r"^XTENSOR_VERSION=(.*)$", stdout, re.M),
            "actual_argv": argv, "exit_code": code,
        },
        "checks": (payload or {}).get("checks", {"CAS-03-C01": False}),
        "subchecks": subchecks,
        "domain_assumption_diff": (payload or {}).get("domain_assumption_diff", []),
        "counterexample": (payload or {}).get("counterexample"),
        "statement_alignment": "Exact finite C01 mass-shell eigen equivalence, unique coefficient, symmetric rest block, and positive future kernel chart for every spatial kernel rank.",
        "limitations": (payload or {}).get("limitations", ["Execution incomplete; no mathematical PASS."]),
        "attempt": str(evidence.relative_to(ROOT)),
        "source_input_sha256_before": before,
        "source_input_sha256_after": after,
        "errors": errors,
    }
    save_json(HERE / "result.json", result)
    print(json.dumps({"checks": result["checks"],
                      "domain_assumption_diff": result["domain_assumption_diff"],
                      "counterexample": result["counterexample"],
                      "status": result["status"], "attempt": result["attempt"],
                      "errors": errors}, sort_keys=True))
    return 0 if passed else 2


if __name__ == "__main__":
    raise SystemExit(main())
