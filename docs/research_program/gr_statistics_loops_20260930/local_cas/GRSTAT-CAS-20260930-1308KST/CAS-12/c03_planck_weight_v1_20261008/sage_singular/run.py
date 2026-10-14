"""Run and retain the independent CAS-12-C03 Sage/Singular axis evidence."""

import hashlib
import json
import re
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path


HERE = Path(__file__).resolve().parent
REPO = Path("/home/cosmosapjw/Dropbox/bianchi/htt_base")
CONTRACT = HERE.parent / "EXECUTION_CONTRACT.json"
INPUTS = HERE.parent / "ADMITTED_INPUTS.json"
COMMON = REPO / "docs/research_program/gr_statistics_loops_20260930/cas/COMMON_SPEC.md"
SINGULAR = Path("/home/cosmosapjw/opt/sage/local/bin/Singular")
FROZEN_HASHES = {
    CONTRACT: "1950de303557d1b805f17a45dc478011bd24e73f06f5444b2ebf9cc3ce06c4a4",
    INPUTS: "22967352d8773a6324fc413d0da748081af52b1a63907af1f3d80119438a2a63",
    COMMON: "4714827e52acf3cb149f4014ac50ab2aa995dd4a0526f6b26ac7257807fe1897",
}


def sha(path):
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def save_json(path, value):
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def run_command(label, argv, commands):
    result = subprocess.run(argv, cwd=HERE, capture_output=True, timeout=1800, check=False)
    stdout_name = f"{label}.stdout.log"
    stderr_name = f"{label}.stderr.log"
    (HERE / stdout_name).write_bytes(result.stdout)
    (HERE / stderr_name).write_bytes(result.stderr)
    commands.append({
        "argv": [str(arg) for arg in argv],
        "cwd": str(HERE),
        "exit": result.returncode,
        "exit_code": result.returncode,
        "stdout_log": stdout_name,
        "stderr_log": stderr_name,
    })
    return result


def require(condition, description):
    if not condition:
        raise RuntimeError(description)


def main():
    commands = []
    execution = {
        "component": "CAS-12-C03",
        "axis": "sage_singular",
        "source_hashes": {},
        "input_hashes": {},
        "executable_artifacts": {},
        "initial_false_exit_failure": {
            "singular_exit_code": 0,
            "observed_error_text": True,
            "stdout_log": "initial_failure_singular.stdout.log",
            "stderr_log": "initial_failure_singular.stderr.log",
            "sage_exit_code": 1,
            "sage_stderr_log": "initial_failure_sage.stderr.log",
        },
    }
    failure = None
    try:
        for path, expected in FROZEN_HASHES.items():
            observed = sha(path)
            execution["input_hashes"][str(path)] = observed
            require(observed == expected, f"frozen input hash mismatch: {path}")
        for name in ("run.py", "certificate.py", "certificate.sing"):
            execution["source_hashes"][name] = sha(HERE / name)

        sage = shutil.which("sage")
        require(sage is not None, "sage executable unavailable")
        require(SINGULAR.is_file(), "pinned Singular executable unavailable")
        for name, path in (("sage", Path(sage)), ("singular", SINGULAR)):
            resolved = path.resolve()
            execution["executable_artifacts"][name] = {
                "invoked_path": str(path), "resolved_path": str(resolved),
                "sha256": sha(resolved),
            }

        sage_version = run_command("sage_version", [sage, "--version"], commands)
        require(sage_version.returncode == 0, "Sage version command failed")
        require(b"SageMath version 10.9" in sage_version.stdout, "Sage 10.9 binding missing")

        singular_version = run_command("singular_version", [str(SINGULAR), "--version"], commands)
        require(singular_version.returncode == 0, "Singular version command failed")
        require(b"version 4.4.1 (44100" in singular_version.stdout,
                "pinned Singular 4.4.1/44100 binding missing")

        sage_run = run_command("sage_certificate", [sage, "-python", "certificate.py"], commands)
        require(sage_run.returncode == 0, "Sage certificate failed")
        require(not sage_run.stderr, "Sage certificate emitted stderr")
        sage_lines = sage_run.stdout.decode("utf-8").splitlines()
        require(len(sage_lines) == 1, "Sage certificate emitted unexpected stdout")
        sage_data = json.loads(sage_lines[0])
        require(sage_data.get("sage_certificate") == "PASS", "Sage pass marker absent")
        require(sage_data.get("formal_scaled_coefficients_x0_to_x7") ==
                ["1", "0", "-1/12", "0", "1/240", "0", "-1/6048", "0"],
                "Sage exact coefficient mismatch")
        require(sage_data.get("exp_sinh_residual") == "0", "Sage identity mismatch")
        require(sage_data.get("right_limit_x2W") == "1", "Sage right limit mismatch")
        require(len(sage_data.get("numeric_vectors", [])) == 2,
                "Sage numeric diagnostic vectors missing")

        singular_run = run_command(
            "singular_certificate", [str(SINGULAR), "-q", "certificate.sing"], commands
        )
        singular_out = singular_run.stdout.decode("utf-8", errors="replace")
        singular_err = singular_run.stderr.decode("utf-8", errors="replace")
        require(singular_run.returncode == 0, "Singular certificate process failed")
        require(not singular_err.strip(), "Singular certificate emitted stderr")
        require(not re.search(r"(?im)^\s*\?|error occurred|failed|not defined", singular_out),
                "Singular reported an error despite zero exit")
        require(singular_out.splitlines() == [
            "CAS-12-C03 Singular Q[x] remainder mod x^8:",
            "0", "SINGULAR_CERTIFICATE_PASS",
        ], "Singular exact residual certificate mismatch")
    except Exception as exc:
        failure = f"{type(exc).__name__}: {exc}"

    execution["commands"] = commands
    execution["completed_at"] = datetime.now(timezone.utc).isoformat()
    execution["failure"] = failure
    save_json(HERE / "execution.json", execution)
    save_json(HERE / "axis_result.json", {
        "axis": "sage_singular",
        "status": "PASS" if failure is None else "FAIL",
        "contract_sha256": FROZEN_HASHES[CONTRACT],
        "commands": commands,
        "evidence_class": "exact",
        "completed_at": execution["completed_at"],
        "domain_assumption_diff": [],
        "counterexample": None if failure is None else failure,
        "scope": "CAS-12-C03 formal Laurent coefficient and stated right limit only",
    })
    print(json.dumps({
        "checks": {"CAS-12-C03": failure is None},
        "domain_assumption_diff": [],
        "counterexample": None if failure is None else failure,
    }, separators=(",", ":")))
    return 0 if failure is None else 1


if __name__ == "__main__":
    sys.exit(main())
