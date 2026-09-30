#!/usr/bin/python3
"""Run the sealed Wolfram certificates; stdout is one success JSON or empty.

The complete proof is mixed analytic/CAS.  The engine does not formalize the
spectral theorem, induction rule, or the entire arbitrary-n matrix statement.
Those boundaries are recorded in PROOF.md and coverage.json and never hidden
by the runner protocol.
"""

import datetime
import hashlib
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import time

HERE = Path(__file__).resolve().parent
ROOT = Path("/home/cosmosapjw/Dropbox/bianchi/htt_base")
CONTRACT = ROOT / "docs/research_program/gr_statistics_loops_20260930/cas11_c02_local_start_20260930/contracts/CAS11-C02-FINITE-GRAM.json"
CONTRACT_SHA = "c66d7d00bf60786417336873dfeb97f5602d0e60a110c110ebacd9dff824b47a"
REQUIRED_CERTIFICATES = {
    "null_coordinate", "zero_epsilon_coordinate", "spectral_reciprocal_penrose",
    "coordinate_range_and_quadratics", "finite_sum_identity_step",
    "finite_sum_nonnegative_step", "finite_sum_zero_step", "terminal_scalar_bound",
    "zero_matrix_target", "zero_epsilon_terminal",
}


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_json(path, value):
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n")


def main():
    if Path.cwd().resolve() != ROOT:
        raise RuntimeError("Invoke from the exact assigned repository root")
    if digest(CONTRACT) != CONTRACT_SHA:
        raise RuntimeError("Frozen contract SHA mismatch")
    sources = [HERE / name for name in ("verify.wls", "run_axis.py", "PROOF.md", "coverage.json")]
    coverage = json.loads((HERE / "coverage.json").read_text())
    if coverage["contract_sha256"] != CONTRACT_SHA or coverage["mathematical_coverage"] != "complete_via_explicit_standard_dependencies":
        raise RuntimeError("Incomplete or misaligned proof coverage; no success payload")
    stamp = datetime.datetime.now(datetime.timezone.utc).strftime("%Y%m%dT%H%M%S.%fZ")
    attempt = HERE / "runs" / stamp
    attempt.mkdir(parents=True, exist_ok=False)
    argv = ["/usr/bin/wolframscript", "-file", str(HERE / "verify.wls")]
    seal = {
        "sealed_before_invocation_utc": stamp,
        "contract_path": str(CONTRACT.relative_to(ROOT)),
        "contract_sha256": CONTRACT_SHA,
        "source_sha256": {str(path.relative_to(ROOT)): digest(path) for path in sources},
        "argv": argv,
        "cwd": str(ROOT),
        "launcher_sha256": digest(Path(argv[0]).resolve()),
        "run_id": "GRSTAT-CAS11-C02-20260930T090559Z",
        "task_id": "GRSTAT-CAS11-C02-20260930T090559Z-wolfram_xact",
        "launch_id": "cl_3fab06c7436bdf993d31693de87bfe31",
        "prior_author_high_water": 570219,
        "cumulative_total_tokens": "NOT_MEASURED",
        "native_author_attempt": 2,
        "requested_runtime": "gpt-6-astra/ultra",
        "observed_runtime": "NOT_MEASURED_BY_THIS_RUNNER",
    }
    write_json(attempt / "source_seal.json", seal)
    started = time.monotonic()
    with (attempt / "engine.stdout").open("wb") as stdout, (attempt / "engine.stderr").open("wb") as stderr:
        process = subprocess.Popen(argv, cwd=ROOT, stdout=stdout, stderr=stderr, start_new_session=True)
        timed_out = False
        try:
            exit_code = process.wait(timeout=300)
        except subprocess.TimeoutExpired:
            timed_out = True
            os.killpg(process.pid, signal.SIGTERM)
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                os.killpg(process.pid, signal.SIGKILL)
                process.wait()
            exit_code = process.returncode
        finally:
            # Reap only this invocation's process group, including an xPerm
            # helper if it outlives normal kernel shutdown.
            try:
                os.killpg(process.pid, signal.SIGTERM)
            except ProcessLookupError:
                pass
    invocation = {
        "argv": argv, "cwd": str(ROOT), "launcher_pid": process.pid,
        "exit_code": exit_code, "timed_out": timed_out,
        "elapsed_seconds": time.monotonic() - started,
        "source_hashes_unchanged": all(digest(path) == seal["source_sha256"][str(path.relative_to(ROOT))] for path in sources),
        "stdout_sha256": digest(attempt / "engine.stdout"),
        "stderr_sha256": digest(attempt / "engine.stderr"),
    }
    write_json(attempt / "invocation.json", invocation)
    lines = (attempt / "engine.stdout").read_text(errors="replace").splitlines()
    reports = [line.removeprefix("C02_ENGINE_REPORT=") for line in lines if line.startswith("C02_ENGINE_REPORT=")]
    failure = None
    if exit_code != 0 or timed_out:
        failure = "Engine did not complete successfully"
    elif not invocation["source_hashes_unchanged"]:
        failure = "Source changed during execution"
    elif len(reports) != 1:
        failure = "Expected one engine certificate report"
    else:
        report = json.loads(reports[0])
        write_json(attempt / "engine_report.json", report)
        certs = report.get("certificates", {})
        if report.get("contract_sha256") != CONTRACT_SHA or set(certs) != REQUIRED_CERTIFICATES:
            failure = "Misaligned engine certificate set"
        elif report.get("all_certificates_passed") is not True or any(c.get("passed") is not True or c.get("result") != "True" for c in certs.values()):
            failure = "Incomplete exact certificate coverage"
        else:
            engine_pid = report["engine"]["process_id"]
            # wolframscript may return just before the OS reaps its kernel.
            # Allow that already-exiting process to disappear, without
            # confusing a transient PID with a persistent service.
            cleanup_started = time.monotonic()
            while True:
                try:
                    os.kill(engine_pid, 0)
                except ProcessLookupError:
                    invocation["kernel_reaped"] = True
                    break
                if time.monotonic() - cleanup_started >= 3:
                    invocation["kernel_reaped"] = False
                    break
                time.sleep(0.05)
            invocation["kernel_reap_wait_seconds"] = time.monotonic() - cleanup_started
            if not invocation["kernel_reaped"]:
                failure = "Wolfram kernel still live after invocation"
            dependencies = {}
            for key in ("kernel_executable", "xact_xTensor_source", "xact_xPerm_source"):
                path = Path(report["engine"][key])
                dependencies[key] = {"path": str(path), "sha256": digest(path)}
                if key.startswith("xact_"):
                    main_source = path.parent.parent / (key.removeprefix("xact_").removesuffix("_source") + ".m")
                    if main_source.is_file():
                        dependencies[key + "_main"] = {"path": str(main_source), "sha256": digest(main_source)}
            write_json(attempt / "engine_dependencies.json", dependencies)
            write_json(attempt / "invocation.json", invocation)
    if failure:
        write_json(attempt / "failure.json", {"status": "INCONCLUSIVE", "reason": failure})
        print(f"INCONCLUSIVE: {failure}; evidence: {attempt}", file=sys.stderr)
        return 1
    payload = {"checks": {"CAS11-C02-FINITE-GRAM": True}, "domain_assumption_diff": [], "counterexample": None}
    serialized = json.dumps(payload, separators=(",", ":"))
    (attempt / "runner.stdout").write_text(serialized + "\n")
    (attempt / "runner.stderr").write_text("")
    write_json(HERE / "latest_run.json", {"attempt": str(attempt.relative_to(ROOT)), "status": "PASS_WITH_EXPLICIT_ANALYTIC_DEPENDENCIES", "full_theorem_kernel_formalization": False})
    print(serialized)
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as exc:
        print(f"INCONCLUSIVE: {type(exc).__name__}: {exc}", file=sys.stderr)
        sys.exit(1)
