#!/usr/bin/python3
"""Run the sealed Sage/Singular certificates; retain every actual invocation.

The success payload refers to the complete argument in proof.md, supported by
the executed certificates. It does not mean a proof-assistant kernel checked
the spectral theorem or the arbitrary-dimension lifting.
"""

from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import time


ROOT = Path("/home/cosmosapjw/Dropbox/bianchi/htt_base")
HERE = Path(__file__).resolve().parent
CONTRACT = ROOT / "docs/research_program/gr_statistics_loops_20260930/cas11_c02_local_start_20260930/contracts/CAS11-C02-FINITE-GRAM.json"
BRIEF = CONTRACT.parent.parent / "NEUTRAL_AXIS_BRIEF.md"
EXPECTED_CONTRACT_SHA256 = "c66d7d00bf60786417336873dfeb97f5602d0e60a110c110ebacd9dff824b47a"
SAGE = "/usr/local/bin/sage"
SINGULAR = "/usr/bin/Singular"
ALGEBRA_NAMES = {
    "null_mode_slack", "epsilon_zero_slack", "positive_range", "positive_energy",
    "positive_mp_one", "positive_mp_two", "zero_range", "zero_energy",
    "zero_mp_one", "zero_mp_two", "dot_energy", "sum_base", "sum_step",
    "bound_contradiction",
}
SIGN_NAMES = {"null_mode_sign", "bound_sign"}
SOURCE_NAMES = ("run_axis.py", "engine.py", "certificates.sing", "proof.md", "coverage.json")


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_json(path, value):
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n")


def utc_now():
    return datetime.now(timezone.utc).isoformat()


def main():
    if Path.cwd().resolve() != ROOT.resolve():
        raise RuntimeError("This axis must run from the exact bound repository root")
    if not HERE.is_relative_to(ROOT):
        raise RuntimeError("Axis source escaped the bound repository")
    if digest(CONTRACT) != EXPECTED_CONTRACT_SHA256:
        raise RuntimeError("Frozen contract SHA-256 mismatch")
    coverage = json.loads((HERE / "coverage.json").read_text())
    if coverage["contract_sha256"] != EXPECTED_CONTRACT_SHA256:
        raise RuntimeError("Coverage is not aligned to the frozen contract")
    if coverage["unresolved_mathematical_gaps"] or not coverage["complete_universal_argument"]:
        raise RuntimeError("INCONCLUSIVE: the proof coverage has an unresolved gap")
    if set(coverage["machine_certificates"]["algebra_names"]) != ALGEBRA_NAMES:
        raise RuntimeError("Certificate specification mismatch")
    if set(coverage["machine_certificates"]["sign_names"]) != SIGN_NAMES:
        raise RuntimeError("Sign-certificate specification mismatch")

    token = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S.%fZ") + "-" + str(os.getpid())
    observed = HERE / "observations" / token
    observed.mkdir(parents=True, exist_ok=False)
    sources = {str(HERE / name): digest(HERE / name) for name in SOURCE_NAMES}
    sources[str(CONTRACT)] = digest(CONTRACT)
    sources[str(BRIEF)] = digest(BRIEF)
    seal = {
        "sealed_at_utc": utc_now(),
        "sealed_before_any_engine_process": True,
        "source_sha256": sources,
        "contract_sha256": EXPECTED_CONTRACT_SHA256,
        "runner_argv": [sys.executable, *sys.argv],
        "cwd": str(ROOT),
        "run_id": "GRSTAT-CAS11-C02-20260930T090559Z",
        "task_id": "GRSTAT-CAS11-C02-20260930T090559Z-sage_singular",
    }
    seal_path = observed / "pre_execution_source_seal.json"
    write_json(seal_path, seal)
    record = {
        "started_at_utc": utc_now(),
        "pre_execution_seal_path": str(seal_path.relative_to(ROOT)),
        "pre_execution_seal_sha256": digest(seal_path),
        "cwd": str(ROOT),
        "runner_argv": [sys.executable, *sys.argv],
        "commands": [],
        "status": "RUNNING",
    }
    record_path = observed / "invocation.json"
    write_json(record_path, record)

    def execute(label, argv):
        started = utc_now()
        clock = time.monotonic()
        stdout_path = observed / (label + ".stdout.txt")
        stderr_path = observed / (label + ".stderr.txt")
        command = {"label": label, "argv": argv, "cwd": str(ROOT), "started_at_utc": started}
        try:
            completed = subprocess.run(argv, cwd=ROOT, capture_output=True, timeout=240, check=False)
            stdout_path.write_bytes(completed.stdout)
            stderr_path.write_bytes(completed.stderr)
            command.update({"exit_code": completed.returncode, "elapsed_seconds": time.monotonic() - clock})
        except subprocess.TimeoutExpired as error:
            stdout_path.write_bytes(error.stdout or b"")
            stderr_path.write_bytes(error.stderr or b"")
            command.update({"exit_code": None, "error": "TimeoutExpired", "elapsed_seconds": time.monotonic() - clock})
            record["commands"].append(command)
            write_json(record_path, record)
            raise
        command.update({
            "stdout_path": str(stdout_path.relative_to(ROOT)),
            "stderr_path": str(stderr_path.relative_to(ROOT)),
            "stdout_sha256": digest(stdout_path),
            "stderr_sha256": digest(stderr_path),
        })
        record["commands"].append(command)
        write_json(record_path, record)
        if completed.returncode != 0:
            raise RuntimeError(label + " failed with exit " + str(completed.returncode))
        return completed.stdout.decode("utf-8", errors="replace")

    try:
        execute("sage_version", [SAGE, "--version"])
        execute("singular_version", [SINGULAR, "--version"])
        result_path = observed / "sage_certificates.json"
        execute("sage", [SAGE, "-python", str(HERE / "engine.py"), str(result_path)])
        singular_stdout = execute("singular", [SINGULAR, str(HERE / "certificates.sing")])
        sage_result = json.loads(result_path.read_text())
        algebra = sage_result["algebra_certificates"]
        signs = sage_result["ordered_polynomial_certificates"]
        if len(algebra) != len(ALGEBRA_NAMES) or {c["name"] for c in algebra} != ALGEBRA_NAMES:
            raise RuntimeError("Incomplete Sage algebra certificate set")
        if len(signs) != len(SIGN_NAMES) or {c["name"] for c in signs} != SIGN_NAMES:
            raise RuntimeError("Incomplete Sage sign certificate set")
        if not all(c["passed"] is True for c in algebra + signs):
            raise RuntimeError("Sage certificate failure")
        singular_lines = [line.strip() for line in singular_stdout.splitlines() if line.strip().startswith("CERT|")]
        expected_lines = {"CERT|" + name + "|PASS" for name in ALGEBRA_NAMES}
        if len(singular_lines) != len(expected_lines) or set(singular_lines) != expected_lines:
            raise RuntimeError("Incomplete or failed actual Singular certificate set")
        if any(line.lstrip().startswith("?") for line in singular_stdout.splitlines()):
            raise RuntimeError("Singular emitted an error diagnostic")
        if "SINGULAR_VERSION|" not in singular_stdout:
            raise RuntimeError("Actual Singular execution version was not observed")
        if any(digest(Path(path)) != value for path, value in sources.items()):
            raise RuntimeError("Sealed source changed during execution")
        result = {
            "checks": {"CAS11-C02-FINITE-GRAM": True},
            "domain_assumption_diff": [],
            "counterexample": None,
        }
        record.update({
            "status": "COMPLETED_UNIVERSAL_ARGUMENT_WITH_ENGINE_CERTIFICATES",
            "finished_at_utc": utc_now(),
            "formal_kernel_proof": False,
            "standard_mathematical_dependencies": coverage["standard_mathematical_dependencies"],
            "algebra_certificate_count_per_engine": len(ALGEBRA_NAMES),
            "ordered_polynomial_certificate_count_sage": len(SIGN_NAMES),
            "runner_payload": result,
        })
        write_json(record_path, record)
        write_json(observed / "runner_result.json", result)
        print(json.dumps(result, sort_keys=True))
        return 0
    except Exception as error:
        record.update({"status": "INCONCLUSIVE_EXECUTION", "finished_at_utc": utc_now(), "error": repr(error)})
        write_json(record_path, record)
        print("INCONCLUSIVE: " + str(error) + "; raw evidence: " + str(observed), file=sys.stderr)
        return 1


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as error:
        print("INCONCLUSIVE before engine execution: " + repr(error), file=sys.stderr)
        raise SystemExit(1)
