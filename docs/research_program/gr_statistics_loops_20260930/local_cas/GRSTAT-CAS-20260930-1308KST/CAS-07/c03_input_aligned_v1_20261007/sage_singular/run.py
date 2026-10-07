"""Execute the blind C03 Sage/Singular axis and retain exact raw receipts."""

import hashlib
import json
from pathlib import Path
import re
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[8]
HERE = Path(__file__).resolve().parent
INPUT = HERE.parent
SINGULAR = Path("/home/cosmosapjw/opt/sage/local/bin/Singular")
EXPECTED = {
    "EXECUTION_CONTRACT.json": "a65d1f9c9c64a149f554855be39400755cb2aee394440d813877a6fcd6e25b6d",
    "ADMITTED_INPUTS.json": "8e87c30466c362dc85071c64fd722933fa5e170d8128f81de29d859a045aa827",
    "COMMON_SPEC.md": "4714827e52acf3cb149f4014ac50ab2aa995dd4a0526f6b26ac7257807fe1897",
    "Singular": "9430832b7c972b6b26d29ded4d91a3e1df8fd87d67f4b8d3f14d8201a75f923c",
}
IDS = ("CAS-07-C03-FD1", "CAS-07-C03-FD2", "CAS-07-C03-FD3")


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def call(name, argv, timeout=600):
    start = time.monotonic()
    try:
        proc = subprocess.run(argv, cwd=HERE, capture_output=True, timeout=timeout,
                              text=True, errors="replace", check=False)
        out, err, rc = proc.stdout, proc.stderr, proc.returncode
        failure = None
    except subprocess.TimeoutExpired as exc:
        out = exc.stdout.decode(errors="replace") if isinstance(exc.stdout, bytes) else (exc.stdout or "")
        err = exc.stderr.decode(errors="replace") if isinstance(exc.stderr, bytes) else (exc.stderr or "")
        rc, failure = None, "timeout"
    except OSError as exc:
        out, err, rc, failure = "", repr(exc), None, "os_error"
    (HERE / (name + ".stdout.log")).write_text(out)
    (HERE / (name + ".stderr.log")).write_text(err)
    return {"argv": [str(x) for x in argv], "cwd": str(HERE), "exit_code": rc,
            "failure": failure, "wall_seconds": round(time.monotonic() - start, 6),
            "stdout_sha256": sha(HERE / (name + ".stdout.log")),
            "stderr_sha256": sha(HERE / (name + ".stderr.log"))}


def main():
    paths = {
        "EXECUTION_CONTRACT.json": INPUT / "EXECUTION_CONTRACT.json",
        "ADMITTED_INPUTS.json": INPUT / "ADMITTED_INPUTS.json",
        "COMMON_SPEC.md": ROOT / "docs/research_program/gr_statistics_loops_20260930/cas/COMMON_SPEC.md",
        "Singular": SINGULAR,
        "check.py": HERE / "check.py",
        "denominators.sing": HERE / "denominators.sing",
        "run.py": HERE / "run.py",
    }
    hashes = {key: sha(path) for key, path in paths.items()}
    sealed = all(hashes[key] == value for key, value in EXPECTED.items())
    commands = {}
    commands["sage_version"] = call("sage_version", ["/usr/local/bin/sage", "--version"])
    commands["singular_version"] = call("singular_version", [str(SINGULAR), "--version"])
    sage_version = (HERE / "sage_version.stdout.log").read_text()
    singular_version = (HERE / "singular_version.stdout.log").read_text()
    versions_ok = (commands["sage_version"]["exit_code"] == 0 and
                   "SageMath version 10.9" in sage_version and
                   commands["singular_version"]["exit_code"] == 0 and
                   "version 4.4.1 (44100" in singular_version and
                   str(SINGULAR) in singular_version)
    if sealed and versions_ok:
        commands["sage_check"] = call("sage_check", ["/usr/local/bin/sage", "-python", str(HERE / "check.py")])
        commands["singular_check"] = call("singular_check", [str(SINGULAR), "-q", str(HERE / "denominators.sing")])
    else:
        for name in ("sage_check", "singular_check"):
            (HERE / (name + ".stdout.log")).write_text("")
            (HERE / (name + ".stderr.log")).write_text("preflight hash/version mismatch\n")
            commands[name] = {"argv": [], "cwd": str(HERE), "exit_code": None,
                              "failure": "preflight_mismatch"}

    sage_raw = (HERE / "sage_check.stdout.log").read_text()
    sing_raw = (HERE / "singular_check.stdout.log").read_text()
    sing_err = (HERE / "singular_check.stderr.log").read_text()
    diagnostic = re.search(r"(?im)(?:^|\s)(?:error|fatal|warning|not defined|unknown identifier|syntax error)(?:\s|:|\b)", sing_raw + "\n" + sing_err)
    try:
        sage_data = json.loads(sage_raw)
        sage_checks = sage_data["checks"]
        sage_shape_ok = set(sage_checks) == set(IDS) and all(type(v) is bool for v in sage_checks.values())
    except (ValueError, KeyError, TypeError):
        sage_data, sage_checks, sage_shape_ok = None, {}, False
    singular_markers = {
        "FD2_M_REMAINDER": "CAS-07-C03-FD2",
        "FD2_H_REMAINDER": "CAS-07-C03-FD2",
        "FD3_M_REMAINDER": "CAS-07-C03-FD3",
        "FD3_H_REMAINDER": "CAS-07-C03-FD3",
    }
    lines = sing_raw.splitlines()
    singular_values = {key: [line.split("=", 1)[1].strip() for line in lines
                             if line.startswith(key + "=")] for key in singular_markers}
    singular_ok = (commands["singular_check"]["exit_code"] == 0 and
                   diagnostic is None and not sing_err.strip() and
                   all(values == ["0"] for values in singular_values.values()))
    common_ok = sealed and versions_ok and sage_shape_ok and commands["sage_check"]["exit_code"] == 0
    checks = {
        "CAS-07-C03-FD1": bool(common_ok and sage_checks.get("CAS-07-C03-FD1") is True),
        "CAS-07-C03-FD2": bool(common_ok and singular_ok and sage_checks.get("CAS-07-C03-FD2") is True),
        "CAS-07-C03-FD3": bool(common_ok and singular_ok and sage_checks.get("CAS-07-C03-FD3") is True),
    }
    result = {
        "checks": checks, "domain_assumption_diff": [], "counterexample": None,
        "contract_sha256": hashes["EXECUTION_CONTRACT.json"],
        "input_sha256": hashes["ADMITTED_INPUTS.json"],
        "source_and_binary_sha256": hashes,
        "tool_versions": {"sage": sage_version.strip(),
                          "singular_first_line": singular_version.splitlines()[0] if singular_version else ""},
        "executable_paths": {"sage": "/usr/local/bin/sage", "singular": str(SINGULAR)},
        "global_authority": "UNAVAILABLE", "global_launch_id": None,
        "actual_author_model": "UNKNOWN", "actual_author_effort": "UNKNOWN",
        "independence_mode": "blind-results-and-derivations",
        "commands": commands, "singular_remainders": singular_values,
        "singular_raw_diagnostic_found": diagnostic.group(0) if diagnostic else None,
        "sage_detail": sage_data,
        "claim_ceiling": "exact conditional finite FD1/FD2/FD3 algebra only",
        "scientific_admission": "HOLD",
    }
    (HERE / "execution.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps(result, sort_keys=True))
    return 0 if all(checks.values()) else 1


if __name__ == "__main__":
    sys.exit(main())
