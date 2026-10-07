#!/usr/bin/env python3
"""Execute the frozen CAS-15 C04 Wolfram/xTensor finite algebra axis."""

from __future__ import annotations

import hashlib
import json
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
UNIT = HERE.parent
CONTRACT = UNIT / "EXECUTION_CONTRACT.json"
INPUTS = UNIT / "ADMITTED_INPUTS.json"
SOURCE = HERE / "verify.wl"
CERT = HERE / "certificate.engine.json"
STDOUT = HERE / "wolfram.stdout.log"
STDERR = HERE / "wolfram.stderr.log"
RESULT = HERE / "result.json"
EXPECTED_CONTRACT = "67422619e47fda896d7516d48e980ec693d878f3c63e5d61e0c151ffaef65ed8"
EXPECTED_INPUTS = "1b98962616a8a43aca614c18a7e69304653c84f0d1b54846a81811642d2491d8"
INTERNAL_CHECKS = (
    "generic_gram_kernel",
    "axisymmetric_one_axis",
    "two_nonparallel_pd_rank3",
    "isotropic_parallel_one_axis_controls",
)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def save(path: Path, obj: object) -> None:
    path.write_text(json.dumps(obj, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def main() -> int:
    contract_sha = sha256(CONTRACT)
    inputs_sha = sha256(INPUTS)
    if (contract_sha, inputs_sha) != (EXPECTED_CONTRACT, EXPECTED_INPUTS):
        payload = {
            "status": "MISALIGNED_ASSUMPTIONS",
            "checks": {"CAS-15-C04": False},
            "domain_assumption_diff": ["frozen contract or admitted input SHA mismatch"],
            "counterexample": None,
            "result_path": str(RESULT),
        }
        print(json.dumps(payload, separators=(",", ":")))
        return 2

    binary = shutil.which("wolframscript")
    argv = [binary or "wolframscript", "-file", str(SOURCE), str(CERT)]
    if CERT.exists():
        CERT.unlink()
    try:
        proc = subprocess.run(argv, cwd=HERE, text=True, capture_output=True, timeout=1800)
        exit_code = proc.returncode
        out, err = proc.stdout, proc.stderr
        resource_failure = False
    except subprocess.TimeoutExpired as exc:
        exit_code = 124
        out = (exc.stdout or b"").decode("utf-8", "replace") if isinstance(exc.stdout, bytes) else (exc.stdout or "")
        err = (exc.stderr or b"").decode("utf-8", "replace") if isinstance(exc.stderr, bytes) else (exc.stderr or "")
        resource_failure = True
    STDOUT.write_text(out, encoding="utf-8")
    STDERR.write_text(err, encoding="utf-8")

    certificate = None
    certificate_error = None
    if CERT.exists():
        try:
            certificate = json.loads(CERT.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, UnicodeDecodeError) as exc:
            certificate_error = repr(exc)
    actual_checks = certificate.get("checks", {}) if isinstance(certificate, dict) else {}
    all_checks = set(actual_checks) == set(INTERNAL_CHECKS) and all(
        actual_checks.get(name) is True for name in INTERNAL_CHECKS
    )
    passed = exit_code == 0 and all_checks and certificate_error is None
    if passed:
        status = "PASS"
    elif resource_failure:
        status = "BLOCKED_RESOURCE_LIMIT"
    else:
        status = "FAIL"

    result = {
        "axis": "wolfram_xact",
        "status": status,
        "contract_sha256": contract_sha,
        "input_sha256": inputs_sha,
        "source_sha256": sha256(SOURCE),
        "runner_sha256": sha256(Path(__file__)),
        "evidence_class": "exact",
        "completed_at": datetime.now(timezone.utc).isoformat(),
        "checks": {"CAS-15-C04": passed},
        "domain_assumption_diff": [],
        "counterexample": None,
        "internal_checks": actual_checks,
        "certificate_error": certificate_error,
        "certificate_path": str(CERT) if CERT.exists() else None,
        "certificate_sha256": sha256(CERT) if CERT.exists() else None,
        "tool_versions": {
            "wolfram": certificate.get("wolfram_version") if isinstance(certificate, dict) else None,
            "xTensor": certificate.get("xtensor_version") if isinstance(certificate, dict) else None,
        },
        "commands": [{
            "argv": argv,
            "cwd": str(HERE),
            "exit_code": exit_code,
            "stdout_path": str(STDOUT),
            "stdout_sha256": sha256(STDOUT),
            "stderr_path": str(STDERR),
            "stderr_sha256": sha256(STDERR),
        }],
        "statement_alignment": {
            "space": "real Euclidean R3, real symmetric M, real skew W",
            "axisymmetric_domain": "unit n and beta != 0 for rank 2 and the one-axis iff",
            "two_axis_domain": "unit axes, beta1 beta2 != 0, s != 0 after orthogonal rotation",
            "branch": "no square root or complex branch",
            "basis": "Frobenius-orthonormal E1,E2,E3",
            "scope": "finite C04 commutant only; no photon transport or spacetime derivative",
        },
        "proof_explanation": (
            "The Wolfram certificate checks q=w^T G w equals the finite stack sum of Frobenius "
            "squares for generic symmetric channels, so ker G is exactly the common skew "
            "commutant. For unit n, G_axis=beta^2(I-n n^T) and [M,W]n=-beta Wn; "
            "the one-axis kernel is span(n). Rotate n1 to e3 and n2 to (s,0,c) "
            "with s^2+c^2=1 and s!=0. The exact certificate gives "
            "det G=beta1^2 beta2^2(beta1^2+beta2^2)s^2 and "
            "w^T G w=beta1^2(w1^2+w2^2)+beta2^2((c w1-s w3)^2+w2^2), "
            "strictly positive for nonzero real w."
        ),
        "launch_id": None,
        "authority_status": "UNAVAILABLE_PER_OWNER_DIRECT_LOCAL_EXECUTION",
        "observed_model": "UNKNOWN",
        "observed_effort": "UNKNOWN",
        "scientific_admission": "HOLD",
    }
    save(RESULT, result)
    payload = {
        "status": status,
        "checks": {"CAS-15-C04": passed},
        "domain_assumption_diff": [],
        "counterexample": None,
        "result_path": str(RESULT),
    }
    print(json.dumps(payload, separators=(",", ":")))
    return 0 if passed else 2


if __name__ == "__main__":
    sys.exit(main())
