#!/usr/bin/env python3
"""Run the frozen CAS-13-C03 Wolfram/xAct certificate in this axis directory."""

import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
from datetime import datetime, timezone


AXIS = Path(__file__).resolve().parent
PACKAGE = AXIS.parent
REPO = AXIS.parents[7]
SOURCE_HASHES = {
    PACKAGE / "EXECUTION_CONTRACT.json": "d9b1e59d9e8648e74db64bdf9e7ef82d23e409c9456a5f307fb30dabb0e8e21e",
    PACKAGE / "ADMITTED_INPUTS.json": "916055a8eff4787ff56bd4e7629cef837333890a9dc5c1a9e8a33aa82c1665b4",
    REPO / "docs/research_program/gr_statistics_loops_20260930/cas/TEFF_INTERVAL_SPEC.md": "bc055d391d3231c634a14e146f228d3b8179a043485c41ce08754cdeac4fd0fe",
    REPO / "docs/research_program/gr_statistics_loops_20260930/cas/COMMON_SPEC.md": "4714827e52acf3cb149f4014ac50ab2aa995dd4a0526f6b26ac7257807fe1897",
}


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def invoke(argv: list[str], name: str) -> dict:
    completed = subprocess.run(argv, cwd=AXIS, capture_output=True, check=False)
    stdout = AXIS / f"{name}.stdout.log"
    stderr = AXIS / f"{name}.stderr.log"
    stdout.write_bytes(completed.stdout)
    stderr.write_bytes(completed.stderr)
    return {
        "argv": argv,
        "cwd": str(AXIS),
        "exit_code": completed.returncode,
        "stdout": str(stdout),
        "stdout_sha256": sha256(stdout),
        "stderr": str(stderr),
        "stderr_sha256": sha256(stderr),
    }


def main() -> int:
    commands = []
    counterexample = None
    checks = {"CAS-13-C03": False}
    observed_hashes = {str(path): sha256(path) for path in SOURCE_HASHES}
    source_match = all(observed_hashes[str(path)] == expected
                       for path, expected in SOURCE_HASHES.items())
    cert_path = AXIS / "engine_certificate.json"
    certificate = None
    if source_match:
        commands.append(invoke(["/usr/bin/wolframscript", "-version"], "version"))
        commands.append(invoke(["/usr/bin/wolframscript", "-file",
                                str(AXIS / "verify.wls"), str(cert_path)], "engine"))
        if cert_path.exists():
            certificate = json.loads(cert_path.read_text())
        checks["CAS-13-C03"] = (
            commands[-1]["exit_code"] == 0
            and certificate is not None
            and certificate.get("domain_assumption_diff") == []
            and certificate.get("counterexample") is None
            and bool(certificate.get("checks"))
            and all(value is True for value in certificate["checks"].values())
        )
        if not checks["CAS-13-C03"]:
            counterexample = {
                "reason": "engine_failure_or_failed_check",
                "failed_checks": [] if certificate is None else
                [key for key, value in certificate.get("checks", {}).items() if value is not True],
            }
    else:
        counterexample = {"reason": "immutable_input_hash_mismatch"}

    xact_path = None if certificate is None else certificate.get("details", {}).get("xact_package_file")
    xact_hash = sha256(Path(xact_path)) if xact_path and Path(xact_path).is_file() else None
    result = {
        "axis": "wolfram_xact",
        "contract_id": "GRSTAT-20260930-CAS-13-C03-HERMITE-V1",
        "contract_sha256": observed_hashes[str(PACKAGE / "EXECUTION_CONTRACT.json")],
        "source_input_sha256": observed_hashes,
        "source_input_hashes_match": source_match,
        "checks": checks,
        "domain_assumption_diff": [],
        "counterexample": counterexample,
        "evidence_class": "exact",
        "completed_at": datetime.now(timezone.utc).isoformat(),
        "commands": commands,
        "versions": {
            "wolfram_engine": None if certificate is None else certificate.get("details", {}).get("wolfram_version"),
            "wolframscript_cli": (AXIS / "version.stdout.log").read_text(errors="replace").strip()
            if commands else None,
            "xact_package_file": xact_path,
            "xact_package_sha256": xact_hash,
            "python": sys.version,
        },
        "artifacts": {
            "runner": str(AXIS / "run_axis.py"),
            "runner_sha256": sha256(AXIS / "run_axis.py"),
            "wolfram_source": str(AXIS / "verify.wls"),
            "wolfram_source_sha256": sha256(AXIS / "verify.wls"),
            "engine_certificate": str(cert_path) if cert_path.exists() else None,
            "engine_certificate_sha256": sha256(cert_path) if cert_path.exists() else None,
            "first_failure": {
                name: {"path": str(AXIS / name), "sha256": sha256(AXIS / name)}
                for name in (
                    "first_failure.engine.stdout.log",
                    "first_failure.engine.stderr.log",
                    "first_failure.engine_certificate.json",
                    "first_failure.axis_result.json",
                ) if (AXIS / name).exists()
            },
        },
        "statement_alignment": {
            "lower": "0<a<u<=b and a<=y<=b, with A=a,U=u",
            "upper": "0<a<=d<b and a<=y<=b, with A=b,U=d",
            "denominator": "Delta(A,U)>0 for A,U>0; interior solve also requires A!=U",
            "moment_identity": "probability normalization and fixed m3,m4; two-node equality only if admitted weights match those moments",
            "boundary": "specialize polynomial Q and factorization at U=A by limit; no node or weight 0/0 expression evaluated",
        },
        "scope": "p=5,6 finite Hermite interpolation, factorization, ordered signs, conditional moments, polynomial boundary specialization",
        "claim_ceiling": "finite CAS-13-C03 component only; no node existence, weight feasibility, general-p, full theorem, or scientific admission",
    }
    (AXIS / "axis_result.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"checks": checks, "domain_assumption_diff": [],
                      "counterexample": counterexample}, separators=(",", ":")))
    return 0 if checks["CAS-13-C03"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
