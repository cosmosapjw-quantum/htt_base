#!/usr/bin/python3.12
"""No-argument, blind Wolfram+xAct runner for CAS-13-C01."""

import datetime as dt
import hashlib
import json
import pathlib
import subprocess
import sys


BASE = pathlib.Path(__file__).resolve().parent
REPO = pathlib.Path.cwd()
CONTRACT = REPO / "docs/research_program/gr_statistics_loops_20260930/local_cas/GRSTAT-CAS-20260930-1308KST/CAS-13/c01_power_jet_v1_20261008/EXECUTION_CONTRACT.json"
INPUT = REPO / "docs/research_program/gr_statistics_loops_20260930/local_cas/GRSTAT-CAS-20260930-1308KST/CAS-13/c01_power_jet_v1_20261008/ADMITTED_INPUTS.json"
TEFF = REPO / "docs/research_program/gr_statistics_loops_20260930/cas/TEFF_INTERVAL_SPEC.md"
COMMON = REPO / "docs/research_program/gr_statistics_loops_20260930/cas/COMMON_SPEC.md"
EXPECTED = {
    CONTRACT: "a603f1f31004a278095ea6ec4523aff77789bd3c5cf58fa74ee51033b566c638",
    INPUT: "6e29ae54d7e065d784ddf673958b8c9b56a1ebe5532e5a4d8d05aca6f588fa3a",
    TEFF: "bc055d391d3231c634a14e146f228d3b8179a043485c41ce08754cdeac4fd0fe",
    COMMON: "4714827e52acf3cb149f4014ac50ab2aa995dd4a0526f6b26ac7257807fe1897",
}


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def relative(path):
    return str(path.relative_to(REPO))


def main():
    if len(sys.argv) != 1:
        raise SystemExit("run.py takes no arguments")
    hashes = {relative(path): sha(path) for path in EXPECTED}
    aligned = all(hashes[relative(path)] == expected for path, expected in EXPECTED.items())
    source = BASE / "power_jet.wl"
    argv = ["/usr/bin/wolframscript", "-file", str(source)]
    command = {"argv": argv, "cwd": str(REPO), "timeout_seconds": 1800}
    engine = None
    if aligned:
        try:
            proc = subprocess.run(argv, cwd=REPO, capture_output=True, text=True, timeout=1800)
            command["exit_code"] = proc.returncode
            stdout, stderr = proc.stdout, proc.stderr
        except subprocess.TimeoutExpired as exc:
            command["exit_code"] = None
            command["error"] = "timeout"
            stdout = (exc.stdout or b"").decode(errors="replace") if isinstance(exc.stdout, bytes) else (exc.stdout or "")
            stderr = (exc.stderr or b"").decode(errors="replace") if isinstance(exc.stderr, bytes) else (exc.stderr or "")
        (BASE / "wolfram.stdout.log").write_text(stdout)
        (BASE / "wolfram.stderr.log").write_text(stderr)
        for line in reversed(stdout.splitlines()):
            if line.startswith("AXIS_JSON="):
                try:
                    engine = json.loads(line.removeprefix("AXIS_JSON="))
                except json.JSONDecodeError:
                    pass
                break
    else:
        command["exit_code"] = None
        command["error"] = "frozen input hash mismatch"
    passed = bool(aligned and command["exit_code"] == 0 and engine and engine.get("status") == "PASS")
    status = "PASS" if passed else "BLOCKED" if not aligned or engine is None or engine.get("status") == "BLOCKED" else "FAIL"
    output = {
        "schema_version": 2,
        "axis": "wolfram_xact",
        "contract_id": "GRSTAT-20260930-CAS-13-C01-POWER-JET-V1",
        "component": "CAS-13-C01",
        "status": status,
        "contract_sha256": EXPECTED[CONTRACT],
        "input_sha256": EXPECTED[INPUT],
        "source_input_hashes": hashes,
        "domain_assumption_diff": [],
        "counterexample": None,
        "evidence_class": "exact",
        "commands": [{"argv": sys.orig_argv, "cwd": str(REPO), "exit_code": 0 if passed else 1}, command],
        "versions": {"python": sys.version.split()[0], "wolfram": engine.get("wolfram_version") if engine else None,
                     "xact_xtensor": engine.get("xact_xtensor_version") if engine else None,
                     "xact_path": engine.get("xact_path") if engine else None,
                     "xact_version_symbols": engine.get("xact_version_symbols") if engine else None},
        "engine_result": engine,
        "source": relative(source),
        "source_sha256": sha(source),
        "runner": relative(BASE / "run.py"),
        "runner_sha256": sha(BASE / "run.py"),
        "raw_logs": [relative(BASE / "wolfram.stdout.log"), relative(BASE / "wolfram.stderr.log")] if aligned else [],
        "raw_log_sha256": {relative(BASE / name): sha(BASE / name) for name in ("wolfram.stdout.log", "wolfram.stderr.log")} if aligned else {},
        "launch_id": None,
        "lifecycle_status": "BLOCKED_UNREGISTERED_DIRECT_LOCAL_EXECUTION",
        "claim_ceiling": "CAS-13-C01 admitted power-response jet only; no integration, general bandpass, full theorem, or scientific admission",
        "completed_at": dt.datetime.now(dt.timezone.utc).isoformat(),
    }
    (BASE / "axis_result.json").write_text(json.dumps(output, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"checks": {"CAS-13-C01": passed}, "domain_assumption_diff": [], "counterexample": None}, separators=(",", ":")))
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
