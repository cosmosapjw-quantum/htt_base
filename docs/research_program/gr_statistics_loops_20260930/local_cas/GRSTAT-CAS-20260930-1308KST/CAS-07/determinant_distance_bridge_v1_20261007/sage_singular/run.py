#!/usr/bin/env python3
"""Stdlib runner for the Sage+Singular CAS-07 M05 axis."""

from __future__ import annotations

import hashlib
import json
import os
import pathlib
import re
import subprocess
import sys
from datetime import datetime, timezone


HERE = pathlib.Path(__file__).resolve().parent
REPO = next(parent for parent in (HERE, *HERE.parents) if (parent / ".git").exists())
BRIDGE = HERE.parent
CONTRACT = BRIDGE / "EXECUTION_CONTRACT.json"
INPUTS = BRIDGE / "ADMITTED_INPUTS.json"
COMMON_SPEC = REPO / "docs/research_program/gr_statistics_loops_20260930/cas/COMMON_SPEC.md"
SAGE = pathlib.Path("/home/cosmosapjw/opt/sage/sage")
SINGULAR = pathlib.Path("/home/cosmosapjw/opt/sage/local/bin/Singular")

EXPECTED_HASHES = {
    CONTRACT: "24e3ae1e11d2a75335cd7fac436e8d1656100dc7877672d08464a4612a19348e",
    INPUTS: "22fbf2a3fcc428d25f8e9fb0d6e1866c8057ebc7e76dd4ad248bd144300a5a75",
    COMMON_SPEC: "4714827e52acf3cb149f4014ac50ab2aa995dd4a0526f6b26ac7257807fe1897",
    SINGULAR: "9430832b7c972b6b26d29ded4d91a3e1df8fd87d67f4b8d3f14d8201a75f923c",
}


def sha256(path: pathlib.Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def sha256_if_exists(path: pathlib.Path) -> str | None:
    return sha256(path) if path.is_file() else None


def run(argv: list[str]) -> subprocess.CompletedProcess[str]:
    try:
        return subprocess.run(
            argv,
            cwd=REPO,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=1800,
            check=False,
        )
    except subprocess.TimeoutExpired as error:
        stdout = error.stdout or ""
        stderr = error.stderr or ""
        if isinstance(stdout, bytes):
            stdout = stdout.decode(errors="replace")
        if isinstance(stderr, bytes):
            stderr = stderr.decode(errors="replace")
        stderr += f"\nTIMEOUT after {error.timeout} seconds\n"
        return subprocess.CompletedProcess(argv, 124, stdout, stderr)
    except OSError as error:
        return subprocess.CompletedProcess(
            argv,
            127,
            "",
            f"{type(error).__name__}: {error}\n",
        )


def write_raw(name: str, completed: subprocess.CompletedProcess[str]) -> None:
    (HERE / f"{name}.stdout.log").write_text(completed.stdout, encoding="utf-8")
    (HERE / f"{name}.stderr.log").write_text(completed.stderr, encoding="utf-8")


def atomic_write_json(path: pathlib.Path, payload: dict[str, object]) -> None:
    temporary = path.with_name(f".{path.name}.{os.getpid()}.tmp")
    with temporary.open("w", encoding="utf-8") as stream:
        json.dump(payload, stream, indent=2, sort_keys=True)
        stream.write("\n")
        stream.flush()
        os.fsync(stream.fileno())
    os.replace(temporary, path)


def current_source_and_log_hashes() -> dict[str, str | None]:
    names = [
        "PROOF.md",
        "determinant_distance_bridge.sage",
        "determinant_distance_bridge.sage.py",
        "polynomial_controls.sing",
        "run.py",
        "run.executed_6113c518.py",
        "run_receipt.json",
        "sage.stdout.log",
        "sage.stderr.log",
        "sage_version.stdout.log",
        "sage_version.stderr.log",
        "singular.stdout.log",
        "singular.stderr.log",
        "singular_version.stdout.log",
        "singular_version.stderr.log",
        "first_attempt.run_receipt.json",
        "first_attempt.sage.stdout.log",
        "first_attempt.sage.stderr.log",
        "first_attempt.singular.stdout.log",
        "first_attempt.singular.stderr.log",
        "result.pre_review_repair.json",
    ]
    return {name: sha256_if_exists(HERE / name) for name in names}


def build_current_result(
    receipt: dict[str, object],
    status: str,
    runner_exit_code: int,
    failure_reasons: list[str],
) -> dict[str, object]:
    result_path = HERE / "result.json"
    predecessor_result_sha256 = sha256_if_exists(result_path)
    timestamp = str(receipt["timestamp_utc"])
    return {
        "schema": "htt.cas07.m05.sage-singular-result.v1",
        "component": "CAS-07-M05-DETERMINANT-DISTANCE-BRIDGE",
        "axis": "sage_singular",
        "status": status,
        "execution_timestamp_utc": timestamp,
        "evidence_rebound_at_utc": timestamp,
        "repair_reason": "Result generated atomically from the current execution receipt and logs.",
        "engine_rerun": True,
        "predecessor_result_sha256": predecessor_result_sha256,
        "routing": {
            "execution_mode": "OWNER_AUTHORIZED_DIRECT_LOCAL_FALLBACK",
            "fallback_role": "owner-authorized Codex fallback for the Sage+Singular axis",
            "launch_id": None,
            "authority_status": "UNAVAILABLE",
            "observed_model": "UNKNOWN",
            "observed_effort": "UNKNOWN",
            "global_harness_used": False,
            "owner_instruction": "전역 하네스 없이 진행해줘",
            "prior_dedicated_role_attempt": {
                "role": "cas_sage_singular",
                "status": "PRE_EXECUTION_REFUSAL",
                "scientific_execution_occurred": False,
                "reason": "hidden registration requirement could not be met; global descriptor absent",
            },
        },
        "frozen_identity": {
            "contract_sha256": EXPECTED_HASHES[CONTRACT],
            "admitted_inputs_sha256": EXPECTED_HASHES[INPUTS],
            "common_spec_sha256": EXPECTED_HASHES[COMMON_SPEC],
        },
        "toolchain": {
            "sage": {"path": str(SAGE), "version": "10.9"},
            "singular": {
                "path": str(SINGULAR),
                "version": "4.4.1/44100",
                "binary_sha256": EXPECTED_HASHES[SINGULAR],
            },
        },
        "execution": {
            "command": [
                "/usr/bin/python3.12",
                "-B",
                str((HERE / "run.py").relative_to(REPO)),
            ],
            "cwd": str(REPO),
            "runner_exit_code": runner_exit_code,
            "sage_exit_code": sage_run.returncode,
            "singular_exit_code": singular_run.returncode,
            "sage_version_exit_code": sage_version.returncode,
            "singular_version_exit_code": singular_version.returncode,
            "sage_stderr_empty": not sage_run.stderr.strip(),
            "singular_stderr_empty": not singular_run.stderr.strip(),
            "singular_error_lines": singular_error_lines,
            "failure_reasons": failure_reasons,
        },
        "checks": dict(receipt["checks"]),
        "domain_assumption_diff": list(receipt["domain_assumption_diff"]),
        "counterexample": receipt["counterexample"],
        "proof_scope": {
            "accepted_interfaces": ["CAS-07-M01", "CAS-07-M04", "CAS-07-C02"],
            "determinant_premise_added": False,
            "symmetry_or_commutation_added": False,
            "numeric_only_proof": False,
            "k_zero_included": True,
            "arbitrary_nonsymmetric_2x2_scope_preserved": True,
        },
        "source_and_evidence_sha256": current_source_and_log_hashes(),
        "first_failure": {
            "preserved": True,
            "stage": "Sage source startup",
            "sage_exit_code": 1,
            "singular_exit_code": 0,
            "error": "ValueError: Symbolic Ring: domain must be one of 'complex', 'real', 'positive' or 'integer'",
            "repair": "changed the Sage symbolic variable domain from the invalid SR object to the declared positive domain",
            "scientific_effect": "none; the failed attempt did not reach the symbolic branch check",
        },
        "claim_ceiling": "determinant_and_distance_bridge_only_no_full_theorem_or_science",
        "dependency_publication_status": "M04_PUBLISHED_R1_CAS_4AXIS_PASS_AND_PASS_ANALYTIC_COMPONENT_REVIEW_PR484_COMMIT_20fc02b187010e9fc5e9d6a3e6f98342a91c914a",
        "parent_adjudication_status": "NOT_PERFORMED_BY_AXIS",
        "scientific_admission": "HOLD",
    }


hashes = {str(path): sha256_if_exists(path) for path in EXPECTED_HASHES}
hashes_match = all(hashes[str(path)] == expected for path, expected in EXPECTED_HASHES.items())

sage_version = run([str(SAGE), "--version"])
singular_version = run([str(SINGULAR), "--version"])
sage_run = run([str(SAGE), str(HERE / "determinant_distance_bridge.sage")])
singular_run = run([str(SINGULAR), "-q", str(HERE / "polynomial_controls.sing")])

write_raw("sage", sage_run)
write_raw("singular", singular_run)
write_raw("sage_version", sage_version)
write_raw("singular_version", singular_version)

singular_error_lines = [
    line
    for line in (singular_run.stdout + "\n" + singular_run.stderr).splitlines()
    if re.match(r"^\s*\?", line) or "error occurred" in line.lower()
]
diagnostics_clean = (
    sage_run.returncode == 0
    and singular_run.returncode == 0
    and not sage_run.stderr.strip()
    and not singular_run.stderr.strip()
    and not singular_error_lines
)

sage_markers = {
    "SAGE_REWRITE_EXACT=true",
    "SAGE_C02_PREMISE_GAP_IDENTITY=true",
    "SAGE_ARBITRARY_NONSYMMETRIC_SCOPE=true",
    "SAGE_K0_CONTROL=true",
}
singular_markers = {
    "SINGULAR_REWRITE_EXACT=true",
    "SINGULAR_C02_PREMISE_GAP_IDENTITY=true",
    "SINGULAR_ARBITRARY_NONSYMMETRIC_SCOPE=true",
    "SINGULAR_K0_CONTROL=true",
}
algebra_ok = sage_markers.issubset(set(sage_run.stdout.splitlines())) and singular_markers.issubset(
    set(singular_run.stdout.splitlines())
)

input_load_error = None
try:
    with INPUTS.open(encoding="utf-8") as stream:
        admitted = json.load(stream)
except (OSError, json.JSONDecodeError) as error:
    admitted = {"accepted_dependencies": []}
    input_load_error = f"{type(error).__name__}: {error}"
dependency_statements = {
    item["component"]: item["statement"] for item in admitted["accepted_dependencies"]
}
interfaces_bound = set(dependency_statements) == {"CAS-07-M01", "CAS-07-M04", "CAS-07-C02"}
m01_bound = "0<=eta_K(s)<=eta_K(L)<1" in dependency_statements.get("CAS-07-M01", "")
m04_bound = "||D(s)-s Id||op<=f_K(s)-s" in dependency_statements.get("CAS-07-M04", "")
c02_statement = dependency_statements.get("CAS-07-C02", "")
c02_sign_bound = "det(D)>0" in c02_statement
c02_distance_bound = "positive sqrt(det(D)) lies in the same interval" in c02_statement
c02_scope_bound = "arbitrary real 2x2 D" in c02_statement

version_ok = (
    sage_version.returncode == 0
    and "SageMath version 10.9" in sage_version.stdout
    and singular_version.returncode == 0
    and "version 4.4.1 (44100" in singular_version.stdout
)

rewrite = hashes_match and version_ok and diagnostics_clean and algebra_ok
premise = rewrite and interfaces_bound and m01_bound and m04_bound
determinant_sign = premise and c02_scope_bound and c02_sign_bound
distance_bound = determinant_sign and c02_distance_bound
domain_assumption_diff: list[str] = []
counterexample = None
passed = rewrite and premise and determinant_sign and distance_bound
status = "PASS" if passed else "FAIL"
runner_exit_code = 0 if passed else 1
failure_reasons: list[str] = []
if not hashes_match:
    failure_reasons.append("FROZEN_IDENTITY_MISMATCH_OR_MISSING_INPUT")
if input_load_error is not None:
    failure_reasons.append(f"ADMITTED_INPUT_LOAD_ERROR: {input_load_error}")
if not version_ok:
    failure_reasons.append("PINNED_TOOLCHAIN_VERSION_CHECK_FAILED")
if sage_run.returncode != 0:
    failure_reasons.append(f"SAGE_EXIT_{sage_run.returncode}")
if singular_run.returncode != 0:
    failure_reasons.append(f"SINGULAR_EXIT_{singular_run.returncode}")
if not diagnostics_clean:
    failure_reasons.append("ENGINE_DIAGNOSTICS_NOT_CLEAN")
if not algebra_ok:
    failure_reasons.append("EXACT_ALGEBRA_MARKERS_INCOMPLETE")
if not interfaces_bound:
    failure_reasons.append("ACCEPTED_INTERFACE_SET_MISMATCH")
if not m01_bound:
    failure_reasons.append("M01_INTERFACE_BINDING_FAILED")
if not m04_bound:
    failure_reasons.append("M04_INTERFACE_BINDING_FAILED")
if not c02_scope_bound:
    failure_reasons.append("C02_SCOPE_BINDING_FAILED")
if not c02_sign_bound:
    failure_reasons.append("C02_DETERMINANT_BINDING_FAILED")
if not c02_distance_bound:
    failure_reasons.append("C02_DISTANCE_BINDING_FAILED")

receipt = {
    "schema": "htt.cas07.m05.sage-singular-run-receipt.v1",
    "timestamp_utc": datetime.now(timezone.utc).isoformat(),
    "status": status,
    "runner_exit_code": runner_exit_code,
    "argv": {
        "sage": [str(SAGE), str(HERE / "determinant_distance_bridge.sage")],
        "singular": [str(SINGULAR), "-q", str(HERE / "polynomial_controls.sing")],
    },
    "cwd": str(REPO),
    "returncodes": {
        "sage": sage_run.returncode,
        "singular": singular_run.returncode,
        "sage_version": sage_version.returncode,
        "singular_version": singular_version.returncode,
    },
    "hashes": hashes,
    "hashes_match": hashes_match,
    "version_ok": version_ok,
    "diagnostics_clean": diagnostics_clean,
    "singular_error_lines": singular_error_lines,
    "failure_reasons": failure_reasons,
    "checks": {
        "CAS-07-M05-REWRITE": rewrite,
        "CAS-07-M05-C02-PREMISE": premise,
        "CAS-07-M05-DETERMINANT-SIGN": determinant_sign,
        "CAS-07-M05-DISTANCE-BOUND": distance_bound,
    },
    "domain_assumption_diff": domain_assumption_diff,
    "counterexample": counterexample,
}
atomic_write_json(HERE / "run_receipt.json", receipt)
current_result = build_current_result(receipt, status, runner_exit_code, failure_reasons)
atomic_write_json(HERE / "result.json", current_result)

stdout_document = {
    "status": status,
    "checks": receipt["checks"],
    "domain_assumption_diff": domain_assumption_diff,
    "counterexample": counterexample,
    "result_path": str((HERE / "result.json").relative_to(REPO)),
}
print(json.dumps(stdout_document, sort_keys=True))

sys.exit(runner_exit_code)
