#!/usr/bin/env python3
"""Run and package the independent Sage + Singular CAS-03-C02 axis."""

from __future__ import annotations

import datetime as dt
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
from typing import Any


ROOT = Path(__file__).resolve().parents[8]
AXIS = Path(__file__).resolve().parent
TASK = AXIS.parent
CONTRACT = TASK / "EXECUTION_CONTRACT.json"
ADMITTED = TASK / "ADMITTED_INPUTS.json"
COMMON = ROOT / "docs/research_program/gr_statistics_loops_20260930/cas/COMMON_SPEC.md"
SAGE = Path("/usr/local/bin/sage")
SINGULAR = Path("/home/cosmosapjw/opt/sage/local/bin/Singular")

EXPECTED_HASHES = {
    "EXECUTION_CONTRACT.json": "feb9aa499860fe3beb6b2d671227c69fcad9cbafde2b6a7f806a95e80211da66",
    "ADMITTED_INPUTS.json": "14e2c2843ff9791656488613ced678198d9f37beb246d8c15b6fba6530af03d1",
    "COMMON_SPEC.md": "4714827e52acf3cb149f4014ac50ab2aa995dd4a0526f6b26ac7257807fe1897",
    "Singular": "9430832b7c972b6b26d29ded4d91a3e1df8fd87d67f4b8d3f14d8201a75f923c",
}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def relative(path: Path) -> str:
    return str(path.relative_to(ROOT))


def execute(argv: list[str], attempt: Path, stem: str) -> dict[str, Any]:
    completed = subprocess.run(argv, cwd=ROOT, capture_output=True, check=False)
    stdout_path = attempt / f"{stem}.stdout.raw"
    stderr_path = attempt / f"{stem}.stderr.raw"
    stdout_path.write_bytes(completed.stdout)
    stderr_path.write_bytes(completed.stderr)
    return {
        "argv": argv,
        "cwd": str(ROOT),
        "exit_code": completed.returncode,
        "stdout_log": relative(stdout_path),
        "stdout_sha256": sha256(stdout_path),
        "stderr_log": relative(stderr_path),
        "stderr_sha256": sha256(stderr_path),
        "stdout_text": completed.stdout.decode("utf-8", errors="replace"),
        "stderr_text": completed.stderr.decode("utf-8", errors="replace"),
    }


def public_execution(record: dict[str, Any]) -> dict[str, Any]:
    return {key: value for key, value in record.items() if not key.endswith("_text")}


def marker_map(text: str) -> dict[str, str]:
    markers: dict[str, str] = {}
    for line in text.splitlines():
        if "=" in line:
            key, value = line.split("=", 1)
            markers[key.strip()] = value.strip()
    return markers


def main() -> int:
    timestamp = dt.datetime.now(dt.timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
    attempt = AXIS / f"attempt_{timestamp}"
    attempt.mkdir(parents=True, exist_ok=False)

    actual_hashes = {
        "EXECUTION_CONTRACT.json": sha256(CONTRACT),
        "ADMITTED_INPUTS.json": sha256(ADMITTED),
        "COMMON_SPEC.md": sha256(COMMON),
        "Singular": sha256(SINGULAR),
        "proof.sage": sha256(AXIS / "proof.sage"),
        "proof.sing": sha256(AXIS / "proof.sing"),
        "run.py": sha256(Path(__file__)),
    }
    failures = [
        f"hash mismatch for {name}: expected {expected}, got {actual_hashes.get(name)}"
        for name, expected in EXPECTED_HASHES.items()
        if actual_hashes.get(name) != expected
    ]

    version_sage = execute([str(SAGE), "--version"], attempt, "sage_version")
    version_singular = execute([str(SINGULAR), "--version"], attempt, "singular_version")
    sage_run = execute([str(SAGE), "-python", str(AXIS / "proof.sage")], attempt, "sage_proof")
    singular_run = execute([str(SINGULAR), "-q", str(AXIS / "proof.sing")], attempt, "singular_proof")

    sage_report: dict[str, Any] = {}
    if sage_run["exit_code"] != 0:
        failures.append(f"Sage proof exited {sage_run['exit_code']}")
    else:
        try:
            sage_report = json.loads(sage_run["stdout_text"])
        except json.JSONDecodeError as exc:
            failures.append(f"Sage stdout was not the exact JSON report: {exc}")
    if sage_report.get("CAS-03-C02") is not True:
        failures.append("Sage exact CAS-03-C02 check did not pass")

    singular_markers = marker_map(singular_run["stdout_text"])
    expected_ranks = {
        "RANK_ZZZ": "0",
        "RANK_NZZ": "1",
        "RANK_ZNZ": "1",
        "RANK_NNZ": "2",
        "RANK_ZZN": "1",
        "RANK_NZN": "2",
        "RANK_ZNN": "2",
        "RANK_NNN": "3",
        "RANK_REPEATED_NONZERO": "2",
        "RANK_ALL_ZERO": "0",
    }
    if singular_run["exit_code"] != 0:
        failures.append(f"Singular proof exited {singular_run['exit_code']}")
    if singular_markers.get("DIFF_REMAINDER") != "0":
        failures.append("Singular hyperbolic-ideal difference remainder was not zero")
    if singular_markers.get("DIFF_SPHERE_REMAINDER") != "0":
        failures.append("Singular combined-ideal difference remainder was not zero")
    for key, expected in expected_ranks.items():
        if singular_markers.get(key) != expected:
            failures.append(f"Singular {key} expected {expected}, got {singular_markers.get(key)!r}")
    if singular_markers.get("SINGULAR_PROOF_DONE") != "1":
        failures.append("Singular proof completion marker missing")
    if version_sage["exit_code"] != 0:
        failures.append("Sage version probe failed")
    if "SageMath version 10.9" not in version_sage["stdout_text"]:
        failures.append("Sage 10.9 version binding not observed")
    if version_singular["exit_code"] != 0:
        failures.append("Singular version probe failed")
    if "version 4.4.1" not in version_singular["stdout_text"]:
        failures.append("Singular 4.4.1 version binding not observed")

    passed = not failures
    contract_json = json.loads(CONTRACT.read_text(encoding="utf-8"))
    completed_at = dt.datetime.now(dt.timezone.utc).isoformat().replace("+00:00", "Z")
    result = {
        "schema_version": 2,
        "task_id": "GRSTAT-CAS-20260930-1308KST-CAS-03-C02-V1-SAGE-SINGULAR",
        "component": "CAS-03-C02",
        "axis": "sage_singular",
        "status": "PASS" if passed else "FAIL",
        "evidence_class": "exact",
        "checks": {"CAS-03-C02": passed},
        "contract_sha256": actual_hashes["EXECUTION_CONTRACT.json"],
        "completed_at": completed_at,
        "commands": [
            public_execution(version_sage),
            public_execution(version_singular),
            public_execution(sage_run),
            public_execution(singular_run),
        ],
        "contract": {
            "id": contract_json["identity"]["contract_id"],
            "version": contract_json["identity"]["contract_version"],
            "path": relative(CONTRACT),
            "sha256": actual_hashes["EXECUTION_CONTRACT.json"],
        },
        "statement_alignment": {
            "difference": "epsilon*(sinh(chi)^2+2*sinh(chi)*cosh(chi)*n1+sinh(chi)^2*n1^2)",
            "chi_zero_spatial_block": "diag(epsilon,b2,b3)",
            "rank_kernel_strata": "all 8 exact zero/nonzero strata; nullity equals number of zero entries",
            "controls": ["chi=0", "all coefficients zero", "repeated nonzero"],
            "equivalence_relation": "exact equality over reals",
        },
        "domain_assumption_diff": [],
        "branch_alignment": "real hyperbolic branch represented exactly by q^2-h^2=1",
        "invariants": {
            "hyperbolic_identity": sage_report.get("family", {}).get("hyperbolic_remainder"),
            "sphere_relation_remainder": sage_report.get("family", {}).get("hyperbolic_and_sphere_remainder"),
            "rank_strata_count": len(sage_report.get("rank_strata", [])),
            "singular_markers": singular_markers,
        },
        "toolchain": {
            "sage": {
                "expected_version": "10.9",
                "binary": str(SAGE),
                "version_probe": public_execution(version_sage),
            },
            "singular": {
                "expected_version": "4.4.1/44100",
                "binary": str(SINGULAR),
                "binary_sha256": actual_hashes["Singular"],
                "version_probe": public_execution(version_singular),
            },
        },
        "execution": {
            "attempt_id": attempt.name,
            "attempt_dir": relative(attempt),
            "sage": public_execution(sage_run),
            "singular": public_execution(singular_run),
        },
        "source_hashes": {
            relative(CONTRACT): actual_hashes["EXECUTION_CONTRACT.json"],
            relative(ADMITTED): actual_hashes["ADMITTED_INPUTS.json"],
            relative(COMMON): actual_hashes["COMMON_SPEC.md"],
            relative(AXIS / "proof.sage"): actual_hashes["proof.sage"],
            relative(AXIS / "proof.sing"): actual_hashes["proof.sing"],
            relative(Path(__file__)): actual_hashes["run.py"],
            str(SINGULAR): actual_hashes["Singular"],
        },
        "exact_results": {
            "sage": sage_report,
            "singular": singular_markers,
        },
        "failures": failures,
        "independence": {
            "mode": "blind-results-and-derivations",
            "inputs_read": [relative(CONTRACT), relative(ADMITTED), relative(COMMON)],
            "sibling_results_read": False,
            "author_model": "UNKNOWN",
            "author_effort": "UNKNOWN",
        },
        "launch": None,
        "runtime_observation": "UNKNOWN",
        "claim_ceiling": "CAS-03-C02 finite geodesic family component only",
        "remaining_obligations": ["CAS03 C03", "eigenfield existence/IFT", "science"],
        "scientific_admission": "HOLD",
    }
    result_path = AXIS / "result.json"
    result_path.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    evidence_hashes = {
        relative(path): sha256(path)
        for path in sorted(attempt.iterdir())
        if path.is_file()
    }
    evidence_hashes[relative(result_path)] = sha256(result_path)
    (AXIS / "SHA256SUMS.json").write_text(
        json.dumps(evidence_hashes, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(json.dumps({
        "status": result["status"],
        "checks": result["checks"],
        "domain_assumption_diff": [],
        "counterexample": None,
        "result_path": relative(result_path),
    }, separators=(",", ":")))
    return 0 if passed else 1


if __name__ == "__main__":
    sys.exit(main())
