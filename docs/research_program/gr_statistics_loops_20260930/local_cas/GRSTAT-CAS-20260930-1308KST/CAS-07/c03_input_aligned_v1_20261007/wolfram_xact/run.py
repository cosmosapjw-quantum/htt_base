#!/usr/bin/env python3
"""Execute this one frozen Wolfram axis and retain its complete local evidence."""
import hashlib
import json
import subprocess
import sys
from pathlib import Path


HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[7]
CONTRACT = HERE.parent / "EXECUTION_CONTRACT.json"
ADMITTED = HERE.parent / "ADMITTED_INPUTS.json"
COMMON = ROOT / "docs/research_program/gr_statistics_loops_20260930/cas/COMMON_SPEC.md"
EXPECTED = {
    CONTRACT: "a65d1f9c9c64a149f554855be39400755cb2aee394440d813877a6fcd6e25b6d",
    ADMITTED: "8e87c30466c362dc85071c64fd722933fa5e170d8128f81de29d859a045aa827",
    COMMON: "4714827e52acf3cb149f4014ac50ab2aa995dd4a0526f6b26ac7257807fe1897",
}


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    hashes = {str(p): sha(p) for p in EXPECTED}
    matched = all(hashes[str(p)] == expected for p, expected in EXPECTED.items())
    argv = ["/usr/local/Wolfram/WolframEngine/15.0/Executables/WolframKernel", "-noprompt", "-script", str(HERE / "check.wl")]
    report = {
        "axis": "wolfram_xact",
        "execution_launch": {"kind": "native_agent", "task": "/root/cas07_c03_wolfram",
                             "requested_role": "cas_wolfram_xact", "global_launch_id": None,
                             "observed_model": None, "observed_effort": None},
        "contract_sha256": hashes[str(CONTRACT)],
        "input_hashes": hashes,
        "source_hashes": {"check.wl": sha(HERE / "check.wl"), "run.py": sha(HERE / "run.py")},
        "argv": argv,
        "executable_path": str(Path(argv[0]).resolve()),
        "executable_sha256": sha(Path(argv[0]).resolve()),
        "input_hashes_matched": matched,
    }
    if not matched:
        report.update(status="BLOCKED_INPUT_HASH_MISMATCH", checks={}, domain_assumption_diff=[], counterexample=None)
    else:
        try:
            proc = subprocess.run(argv, cwd=HERE, capture_output=True, text=True, timeout=1800)
            (HERE / "stdout.log").write_text(proc.stdout)
            (HERE / "stderr.log").write_text(proc.stderr)
            report.update(exit_code=proc.returncode, stdout_path=str(HERE / "stdout.log"), stderr_path=str(HERE / "stderr.log"),
                          stdout_sha256=sha(HERE / "stdout.log"), stderr_sha256=sha(HERE / "stderr.log"))
            lines = [line[len("AXIS_JSON:"):] for line in proc.stdout.splitlines() if line.startswith("AXIS_JSON:")]
            if len(lines) == 1:
                payload = json.loads(lines[0])
                report.update(payload)
                report["status"] = "PASS" if (
                    proc.returncode == 0
                    and all(v["pass"] for v in payload["checks"].values())
                    and payload["xact"]["pass"]
                    and all(payload["boundary_cases"].values())
                ) else "FAIL"
            else:
                report.update(status="FAIL_MISSING_UNIQUE_RESULT", checks={}, domain_assumption_diff=[], counterexample=None)
        except subprocess.TimeoutExpired as exc:
            (HERE / "stdout.log").write_bytes(exc.stdout or b"")
            (HERE / "stderr.log").write_bytes(exc.stderr or b"")
            report.update(status="BLOCKED_TIMEOUT", exit_code=None, checks={}, domain_assumption_diff=[], counterexample=None,
                          stdout_sha256=sha(HERE / "stdout.log"), stderr_sha256=sha(HERE / "stderr.log"))
    (HERE / "result.json").write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    gate_envelope = {
        "checks": {key: bool(value["pass"]) for key, value in report["checks"].items()},
        "domain_assumption_diff": report["domain_assumption_diff"],
        "counterexample": report["counterexample"],
    }
    json.dump(gate_envelope, sys.stdout, sort_keys=True)
    sys.stdout.write("\n")
    return 0 if report["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
