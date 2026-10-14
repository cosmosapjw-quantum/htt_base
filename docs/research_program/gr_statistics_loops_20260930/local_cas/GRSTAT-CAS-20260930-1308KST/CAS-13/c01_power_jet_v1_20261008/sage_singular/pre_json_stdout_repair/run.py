#!/usr/bin/python3.12
"""CAS-13-C01 Sage/Singular axis. Run with /usr/bin/python3.12 -B from repo root."""

import hashlib
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path.cwd()
HERE = Path(__file__).resolve().parent
CONTRACT = HERE.parent / "EXECUTION_CONTRACT.json"
INPUT = HERE.parent / "ADMITTED_INPUTS.json"
SAGE = Path("/usr/local/bin/sage")
SINGULAR = Path("/home/cosmosapjw/opt/sage/local/bin/Singular")
EXPECTED = {
    CONTRACT: "a603f1f31004a278095ea6ec4523aff77789bd3c5cf58fa74ee51033b566c638",
    INPUT: "6e29ae54d7e065d784ddf673958b8c9b56a1ebe5532e5a4d8d05aca6f588fa3a",
    ROOT / "docs/research_program/gr_statistics_loops_20260930/cas/TEFF_INTERVAL_SPEC.md": "bc055d391d3231c634a14e146f228d3b8179a043485c41ce08754cdeac4fd0fe",
    ROOT / "docs/research_program/gr_statistics_loops_20260930/cas/COMMON_SPEC.md": "4714827e52acf3cb149f4014ac50ab2aa995dd4a0526f6b26ac7257807fe1897",
}


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def execute(label, argv, timeout=1800):
    proc = subprocess.run(argv, cwd=ROOT, text=True, capture_output=True, timeout=timeout)
    (HERE / f"{label}.stdout.log").write_text(proc.stdout)
    (HERE / f"{label}.stderr.log").write_text(proc.stderr)
    return {"argv": [str(item) for item in argv], "cwd": str(ROOT), "exit_code": proc.returncode,
            "stdout": proc.stdout, "stderr": proc.stderr,
            "stdout_path": str(HERE / f"{label}.stdout.log"),
            "stderr_path": str(HERE / f"{label}.stderr.log")}


def main():
    commands = []
    findings = []
    try:
        if ROOT != Path("/home/cosmosapjw/Dropbox/bianchi/htt_base"):
            raise RuntimeError(f"unexpected cwd: {ROOT}")
        for path, expected in EXPECTED.items():
            actual = sha256(path)
            if actual != expected:
                raise RuntimeError(f"frozen input mismatch: {path}: {actual}")

        sage_version = execute("sage_version", [SAGE, "-v"], 60)
        singular_version = execute("singular_version", [SINGULAR, "--version"], 60)
        commands.extend((sage_version, singular_version))
        if sage_version["exit_code"] or "SageMath version 10.9" not in sage_version["stdout"]:
            raise RuntimeError("Sage 10.9 version check failed")
        if singular_version["exit_code"] or "version 4.4.1 (44100" not in singular_version["stdout"]:
            raise RuntimeError("pinned Singular 4.4.1 version check failed")

        sage = execute("sage", [SAGE, "-python", HERE / "power_jet.sage.py"])
        commands.append(sage)
        if sage["exit_code"] or sage["stderr"].strip() or "SAGE_CHECKS_PASS" not in sage["stdout"]:
            raise RuntimeError("Sage check failed; inspect raw stdout/stderr")

        singular = execute("singular", [SINGULAR, "-q", HERE / "power_jet.sing"])
        commands.append(singular)
        if singular["exit_code"] or singular["stderr"].strip() or "error" in singular["stdout"].lower():
            raise RuntimeError("Singular returned an exit/error signal; inspect raw stdout/stderr")
        for key in ("jet_value", "jet_first", "jet_second", "q_third", "unit_factor"):
            if f"{key}=0" not in singular["stdout"].splitlines():
                raise RuntimeError(f"Singular {key} did not return exact zero")
        if "factorization=p*(p-3)*(p-4)" not in singular["stdout"].splitlines():
            raise RuntimeError("Singular factorization marker absent")
        findings = ["Sage positive-real branch derivative identities and exact jets passed",
                    "Sage 320-bit numerical controls passed for p=5,y=4/5; p=6,y=6/5; and p=9/2,y=9/10",
                    "Singular 4.4.1 exact coefficient identities and unit mismatch factorization passed"]
        status = "PASS"
    except Exception as exc:
        status = "FAIL"
        findings.append(f"{type(exc).__name__}: {exc}")

    result = {
        "schema_version": 2,
        "axis": "sage_singular",
        "status": status,
        "contract_id": "GRSTAT-20260930-CAS-13-C01-POWER-JET-V1",
        "contract_sha256": EXPECTED[CONTRACT],
        "input_sha256": EXPECTED[INPUT],
        "completed_at": datetime.now(timezone.utc).isoformat(),
        "evidence_class": "exact",
        "launch_id": None,
        "lifecycle_status": "BLOCKED_NO_GLOBAL_REGISTERED_LAUNCH",
        "observed_model": "UNKNOWN",
        "observed_effort": "UNKNOWN",
        "domain": {"p": "real p>4", "y": "real y>0", "branch": "y^p=exp(p log y)", "units": "dimensionless"},
        "scope": "CAS-13-C01 finite power-response jet only",
        "findings": findings,
        "tool_versions": {"sage": "10.9" if len(commands) > 0 and commands[0]["exit_code"] == 0 else "UNKNOWN",
                          "singular": "4.4.1 (44100)" if len(commands) > 1 and commands[1]["exit_code"] == 0 else "UNKNOWN"},
        "commands": [{key: value for key, value in command.items() if key not in ("stdout", "stderr")} for command in commands],
        "source_artifacts": {str(path): sha256(path) for path in (HERE / "power_jet.sage.py", HERE / "power_jet.sing", HERE / "run.py")},
        "limitations": ["No Taylor remainder/integration, general bandpass, node/weight feasibility, extremizer theorem, or scientific admission", "Lifecycle blocked without global registered launch"],
    }
    (HERE / "axis_result.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print("CAS-13-C01 true" if status == "PASS" else "CAS-13-C01 false")
    if status != "PASS":
        print("; ".join(findings), file=sys.stderr)
    return 0 if status == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
