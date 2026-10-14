"""Run the frozen CAS-10-C03 v2 SymPy axis and retain its raw evidence."""

import hashlib
import datetime
import json
import pathlib
import subprocess
import sys
import time


HERE = pathlib.Path(__file__).resolve().parent
TASK = HERE.parent
ROOT = pathlib.Path(__file__).resolve().parents[8]
CONTRACT = TASK / "EXECUTION_CONTRACT.json"
INPUTS = TASK / "ADMITTED_INPUTS.json"
COMMON_SPEC = ROOT / "docs/research_program/gr_statistics_loops_20260930/cas/COMMON_SPEC.md"
EXPECTED = {
    CONTRACT: "d64d348c940ea7b37c522fb1043eaa29a6558798104d953fe554b3844ca9811e",
    INPUTS: "d538b90a28b749702209c68e0c73444607295e4b66f2c55d1640d9bd75cf5e53",
    COMMON_SPEC: "4714827e52acf3cb149f4014ac50ab2aa995dd4a0526f6b26ac7257807fe1897",
}


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_json(path, data):
    with path.open("x") as stream:
        stream.write(json.dumps(data, indent=2, sort_keys=True) + "\n")


def print_runner_payload(passed):
    print(json.dumps({
        "checks": {"CAS-10-C03": bool(passed)},
        "domain_assumption_diff": [],
        "counterexample": None,
    }, separators=(",", ":")))


def next_replay_directory():
    # Atomic directory creation reserves a distinct run without touching the
    # original engine logs or any prior replay.
    for number in range(1, 10000):
        candidate = HERE / f"runner_replay_{number:04d}"
        try:
            candidate.mkdir()
            return candidate
        except FileExistsError:
            continue
    raise SystemExit("No available replay directory")


def main():
    if pathlib.Path(sys.executable).resolve() != pathlib.Path("/usr/bin/python3").resolve():
        raise SystemExit("Use /usr/bin/python3")
    if any(sha256(path) != digest for path, digest in EXPECTED.items()):
        raise SystemExit("Frozen contract, inputs or common specification hash mismatch")
    replay = next_replay_directory()
    source = HERE / "proof.py"
    argv = ["/usr/bin/python3", "-B", str(source)]
    started = time.time()
    completed = subprocess.run(argv, cwd=ROOT, capture_output=True, text=True, timeout=1800)
    ended = time.time()
    stdout_path = replay / "engine.stdout.log"
    stderr_path = replay / "engine.stderr.log"
    with stdout_path.open("x") as stream:
        stream.write(completed.stdout)
    with stderr_path.open("x") as stream:
        stream.write(completed.stderr)
    execution = {
        "argv": argv,
        "cwd": str(ROOT),
        "exit_code": completed.returncode,
        "started_unix": started,
        "ended_unix": ended,
        "wall_seconds": ended - started,
        "python_version": sys.version,
        "python_executable": sys.executable,
        "stdout_path": str(stdout_path),
        "stderr_path": str(stderr_path),
        "source_path": str(source),
        "source_sha256": sha256(source),
        "runner_path": str(HERE / "run.py"),
        "runner_sha256": sha256(HERE / "run.py"),
        "input_sha256": {str(path): digest for path, digest in EXPECTED.items()},
    }
    write_json(replay / "execution.json", execution)
    if completed.returncode:
        print_runner_payload(False)
        raise SystemExit(completed.returncode)
    result = json.loads(completed.stdout)
    write_json(replay / "result.json", result)

    axis_result = {
        "schema_version": 2,
        "contract_id": "GRSTAT-20260930-CAS-10-C03-BLOCK-ROTATION-KL-V2",
        "contract_sha256": EXPECTED[CONTRACT],
        "axis": "sympy",
        "status": "PASS" if result["pass"] else "FAIL",
        "payload": {"CAS-10-C03": bool(result["pass"])},
        "evidence_class": "exact",
        "completed_at": datetime.datetime.fromtimestamp(ended, datetime.timezone.utc).isoformat(),
        "commands": [{"argv": argv, "cwd": str(ROOT), "exit_code": completed.returncode}],
        "statement_alignment": "Exact 13D direct sum in ordered blocks (Z0,Z1,m,p,T), with p fourth; real H and positive block scales; sigma_p is the fourth scale. Exact orthogonal rotation, all five block norms, common covariance and KL quadratic checked.",
        "domain_assumption_diff": [],
        "branch_diff": [],
        "source_files": [str(source), str(HERE / "run.py")],
        "source_hashes": {str(source): sha256(source), str(HERE / "run.py"): sha256(HERE / "run.py")},
        "raw_logs": [str(stdout_path), str(stderr_path)],
        "execution": execution,
        "result_path": str(replay / "result.json"),
        "checks": result["checks"],
        "remaining_analytical_obligations": [
            "compressed probability-law equality",
            "test-power conclusion",
            "science",
        ],
        "scientific_admission": "HOLD",
        "runtime_observation": {
            "global_registered_launch_id": None,
            "author_model": "UNKNOWN",
            "author_effort": "UNKNOWN",
            "registration_status": "UNAVAILABLE",
        },
    }
    write_json(replay / "axis_result.json", axis_result)
    print_runner_payload(result["pass"])


if __name__ == "__main__":
    main()
