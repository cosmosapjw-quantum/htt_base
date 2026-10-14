#!/usr/bin/env python3
"""Execute the frozen PORT-CAS-02 Sage/Singular axis; print one gate JSON line."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
import hashlib
import json
import os
import re
import subprocess
import sys
import time
import uuid


HERE = Path(__file__).resolve().parent
CONTRACT = HERE.parent / "EXECUTION_CONTRACT.json"
INPUTS = HERE.parent / "ADMITTED_INPUTS.json"
EXPECTED_CONTRACT = "d62613255f18b2d2d2140cc6d73fbac27f6b2f8ac40ed9b268b9f5fc0fa166af"
EXPECTED_INPUTS = "849f9ebde2894f1deb15ba61452a3cc911d46af960b8630694cfe8cc15e3620a"
EXPECTED_SOURCES = {
    "sage": "df55bca6a7bdb16644aa6e64846d259a9e631fbbde2519c34b6ddf2209c7d079",
    "singular": "471ff792676c77c55680515abb35d42693edff07902a2d98496a12b2ce25feb4",
}
SINGULAR = Path("/home/cosmosapjw/opt/sage/local/bin/Singular")
EXPECTED_SINGULAR_BINARY = "9430832b7c972b6b26d29ded4d91a3e1df8fd87d67f4b8d3f14d8201a75f923c"
LABELS = [
    "null", "S polynomial", "B null contraction", "kernel/eigen 0",
    "kernel/eigen 1", "kernel/eigen 2", "kernel/eigen 3",
    "metric gauge null", "metric gauge B time", "metric gauge B space",
    "tracefree",
]
ZERO_CHECK_EXCEPTIONS = {"numeric_test_S_null", "S_equals_st_g_implies_B_zero"}


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def write_json(path: Path, value: object) -> None:
    staged = path.with_name(path.name + ".tmp-" + uuid.uuid4().hex)
    staged.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n")
    os.replace(staged, path)


def relative(path: Path, repo: Path) -> str:
    return str(path.relative_to(repo))


def execute(label: str, argv: list[str], source: Path, attempt: Path, repo: Path, timeout: float) -> dict:
    began = now()
    timed_out = False
    try:
        process = subprocess.run(argv, cwd=repo, capture_output=True, timeout=timeout)
        stdout, stderr, exit_code = process.stdout, process.stderr, process.returncode
    except subprocess.TimeoutExpired as error:
        stdout, stderr, exit_code = error.stdout or b"", error.stderr or b"", None
        timed_out = True
    stdout_path = attempt / f"{label}.stdout.log"
    stderr_path = attempt / f"{label}.stderr.log"
    stdout_path.write_bytes(stdout)
    stderr_path.write_bytes(stderr)
    executable = Path(argv[0]).resolve()
    receipt = {
        "argv": argv, "started_at": began, "completed_at": now(),
        "exit_code": exit_code, "timed_out": timed_out,
        "executable": str(executable), "executable_sha256": sha256(executable),
        "source": relative(source, repo), "source_sha256": sha256(source),
        "stdout_log": relative(stdout_path, repo), "stdout_sha256": sha256(stdout_path),
        "stderr_log": relative(stderr_path, repo), "stderr_sha256": sha256(stderr_path),
    }
    write_json(attempt / f"{label}.execution.json", receipt)
    return receipt


def probe_singular_version(attempt: Path, repo: Path) -> dict:
    argv = [str(SINGULAR), "--version"]
    process = subprocess.run(argv, cwd=repo, capture_output=True, timeout=30)
    stdout_path = attempt / "singular_version.stdout.log"
    stderr_path = attempt / "singular_version.stderr.log"
    stdout_path.write_bytes(process.stdout)
    stderr_path.write_bytes(process.stderr)
    receipt = {
        "argv": argv, "exit_code": process.returncode,
        "executable": str(SINGULAR.resolve()), "executable_sha256": sha256(SINGULAR),
        "stdout_log": relative(stdout_path, repo), "stdout_sha256": sha256(stdout_path),
        "stderr_log": relative(stderr_path, repo), "stderr_sha256": sha256(stderr_path),
    }
    write_json(attempt / "singular_version.execution.json", receipt)
    if process.returncode or process.stderr or not re.search(rb"version 4\.4\.1 \(44100", process.stdout):
        raise ValueError("Pinned Singular version query failed or disagreed")
    return receipt


def verify_sage(receipt: dict, repo: Path) -> tuple[dict, str]:
    if receipt["timed_out"] or receipt["exit_code"] != 0:
        raise ValueError("Sage execution failed or timed out")
    if (repo / receipt["stderr_log"]).read_bytes():
        raise ValueError("Sage stderr is nonempty")
    data = json.loads((repo / receipt["stdout_log"]).read_text())
    if data.get("axis") != "sage_singular" or data.get("status") != "PASS":
        raise ValueError("Sage did not report PASS for this axis")
    checks = data.get("checks", {})
    required = {
        "g_null_mod_unit", "S_null_polynomial", "B_null_equals_S_mod_unit",
        "q_tracefree", "B_symmetric", "metric_gauge_B",
        "metric_gauge_null_mod_unit", "tracefree_spatial_monopole",
        *(f"kernel_eigen_iff_component_{i}" for i in range(4)),
    }
    if not required <= checks.keys() or any(checks[k] != "0" for k in required):
        raise ValueError("Sage exact residual is missing or nonzero")
    if checks.get("numeric_test_S_null") != "4":
        raise ValueError("Sage numeric test vector disagrees")
    if not checks.get("S_equals_st_g_implies_B_zero", "").startswith("0;"):
        raise ValueError("Sage proportional-metric control is missing")
    if set(checks) != required | ZERO_CHECK_EXCEPTIONS:
        raise ValueError("Unexpected Sage check set")
    return checks, data["sage_version"]


def verify_singular(receipt: dict, repo: Path) -> None:
    if receipt["timed_out"] or receipt["exit_code"] != 0:
        raise ValueError("Singular execution failed or timed out")
    if (repo / receipt["stderr_log"]).read_bytes():
        raise ValueError("Singular stderr is nonempty")
    lines = (repo / receipt["stdout_log"]).read_text().splitlines()
    expected = ["Singular 4.4.1 exact ideal reductions:"]
    for label in LABELS:
        expected.extend((label, "0"))
    expected.append("PASS: null, contraction, kernel/eigen, trace, metric gauge")
    if lines != expected:
        raise ValueError("Singular exact reductions, version marker, or PASS marker disagree")


def main() -> int:
    repo = next(p for p in HERE.parents if (p / ".agent-harness/scripts/cas_gate.py").is_file())
    attempt = HERE / "attempts" / (datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ") + "-" + uuid.uuid4().hex[:8])
    attempt.mkdir(parents=True, exist_ok=False)
    commands: list[dict] = []
    status = "INCONCLUSIVE"
    reason = None
    sage_checks = None
    sage_version = None
    singular_version_receipt = None
    contract_hash = sha256(CONTRACT)
    input_hash = sha256(INPUTS)
    try:
        if contract_hash != EXPECTED_CONTRACT or input_hash != EXPECTED_INPUTS:
            raise ValueError("Frozen contract or admitted-input SHA-256 changed")
        sources = {"sage": HERE / "port_cas02.sage.py", "singular": HERE / "port_cas02.sing"}
        for label, source in sources.items():
            if sha256(source) != EXPECTED_SOURCES[label]:
                raise ValueError(f"Frozen {label} source SHA-256 changed")
        if sha256(SINGULAR) != EXPECTED_SINGULAR_BINARY:
            raise ValueError("Pinned Singular executable SHA-256 changed")
        singular_version_receipt = probe_singular_version(attempt, repo)
        began = time.monotonic()
        sage_argv = ["/usr/local/bin/sage", "-python", relative(sources["sage"], repo)]
        commands.append(execute("sage", sage_argv, sources["sage"], attempt, repo, 1800))
        sage_checks, sage_version = verify_sage(commands[-1], repo)
        remaining = max(0.001, 1800 - (time.monotonic() - began))
        singular_argv = [str(SINGULAR), "-q", relative(sources["singular"], repo)]
        commands.append(execute("singular", singular_argv, sources["singular"], attempt, repo, remaining))
        verify_singular(commands[-1], repo)
        status = "PASS"
    except Exception as error:
        reason = f"{type(error).__name__}: {error}"
        write_json(attempt / "failure.json", {"at": now(), "reason": reason, "status": status})

    if contract_hash == EXPECTED_CONTRACT and input_hash == EXPECTED_INPUTS and commands:
        result = {
            "axis": "sage_singular", "status": status, "evidence_class": "exact",
            "contract_sha256": contract_hash, "admitted_inputs_sha256": input_hash,
            "completed_at": now(), "commands": commands,
            "source_files": [relative(HERE / "port_cas02.sage.py", repo), relative(HERE / "port_cas02.sing", repo)],
            "tool_versions": {"SageMath": sage_version or "UNKNOWN", "Singular": "4.4.1 (44100), Sage-bundled pinned executable"},
            "singular_version_receipt": singular_version_receipt,
            "checks": {"sage": sage_checks, "singular_exact_reductions": LABELS if status == "PASS" else None},
            "alignment": {
                "metric": "diag(-1,1,1,1)", "K": "contravariant (-1,n), n real and n.n=1",
                "S": "covariant symmetric; S0i=-h1_i/2; q symmetric tracefree", "B": "S-st*g",
                "u": "future unit timelike branch assumed for physical use; algebra verified for arbitrary symbolic u",
                "st": "real; eigenpair is assumed when applying kernel identity",
                "metric_gauge": "S to S+a*g and st to st+a",
            },
            "independence_mode": "blind-results-and-derivations", "sibling_scripts_results_read": False,
            "global_launch_id": None, "global_registered_launch": False,
            "requested_model": "UNKNOWN", "requested_effort": "UNKNOWN",
            "observed_model": "UNKNOWN", "observed_effort": "UNKNOWN",
            "lifecycle_status": "BLOCKED_UNREGISTERED_CHILD", "scientific_admission": "HOLD",
            "claim_ceiling": "PORT-CAS-02 finite algebra only; no eigenline existence/uniqueness, geodesicity, finite-distance inference, vorticity recovery, or Bianchi-family claim",
            "notes": ["The kernel/eigen equivalence uses invertibility of g.", "S=st*g within the tracefree parametrization requires st=0; the general matrix control is separate."],
            "attempt_dir": relative(attempt, repo), "failure_reason": reason,
        }
        write_json(HERE / "axis_result.json", result)
        gate_argv = [sys.executable, str(repo / ".agent-harness/scripts/cas_gate.py"), "check-axis", "--contract", relative(CONTRACT, repo), "--result", relative(HERE / "axis_result.json", repo)]
        gate = subprocess.run(gate_argv, cwd=repo, capture_output=True, text=True)
        try:
            gate_result = json.loads(gate.stdout)
        except json.JSONDecodeError:
            gate_result = {"ok": False, "axis": "sage_singular", "status": status, "verification_state": "GATE_ERROR", "claim_promotion_cas_eligible": False}
        if gate.returncode or not gate_result.get("ok"):
            status = "INCONCLUSIVE"
            write_json(attempt / "gate_failure.json", {"exit_code": gate.returncode, "stdout": gate.stdout, "stderr": gate.stderr})
        write_json(attempt / "check_axis.json", gate_result)
        write_json(HERE / "check_axis.json", gate_result)
    else:
        gate_result = {"ok": False, "axis": "sage_singular", "status": status, "verification_state": "FROZEN_INPUT_OR_EXECUTION_BLOCKED", "claim_promotion_cas_eligible": False}
    passed = status == "PASS" and bool(gate_result.get("ok"))
    adjudication_result = {
        "checks": {"PORT-CAS-02": passed},
        "domain_assumption_diff": [],
        "counterexample": None if passed else reason or "axis execution or envelope validation failed",
    }
    print(json.dumps(adjudication_result, separators=(",", ":")))
    return 0 if passed else 2


if __name__ == "__main__":
    raise SystemExit(main())
