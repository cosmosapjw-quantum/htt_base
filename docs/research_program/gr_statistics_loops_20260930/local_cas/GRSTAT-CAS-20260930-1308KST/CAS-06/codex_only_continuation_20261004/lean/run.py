#!/usr/bin/env python3
"""Execute the frozen Lean scalar subtarget and emit an observed axis envelope."""

from __future__ import annotations

import hashlib
import json
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[7]
CONTRACT = HERE.parent / "C03_SCALAR_CONTRACT.json"
COMMON = REPO / "docs/research_program/gr_statistics_loops_20260930/cas/COMMON_SPEC.md"
FORMAL = REPO / "formal_mathlib"
SOURCE = HERE / "Proof.lean"
CONTRACT_SHA = "7742ee4abac523eabc466435f115de88228a957a3dbed946fa5311f99ab07c27"
COMMON_SHA = "4714827e52acf3cb149f4014ac50ab2aa995dd4a0526f6b26ac7257807fe1897"
TOOLCHAIN_SHA = "efac0b94923b2d8b6840cd35be9177ad0fc5ab2332f4f4311c98712cee92fdee"
MANIFEST_SHA = "bc86de9aed83fc38b0850702d6879ed6f3c97eedb7d1d69d643160731179d6ed"
MATHLIB_REV = "fabf563a7c95a166b8d7b6efca11c8b4dc9d911f"
PROOF_SHA = "83352ea65bb391d2bd17bf4e25e6149dc5f1cff14f75c28de1a7f30b1d12f46e"
THEOREMS = (
    "positive_branch", "pressure_hasDerivAt", "first_hasDerivAt",
    "pressure_deriv", "first_deriv", "pressure_second_deriv",
    "energy_identity", "denominator_factor", "exponent_pos",
    "exponent_gap_pos", "denominator_pos", "ratio_identity",
    "energy_deriv_identity", "deriv_denominator_pos", "deriv_ratio_identity",
)
ALLOWED_AXIOMS = {"propext", "Classical.choice", "Quot.sound"}


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> int:
    input_hashes = {
        "contract": sha(CONTRACT),
        "common_spec": sha(COMMON),
        "formal_toolchain": sha(REPO / "formal/lean-toolchain"),
        "mathlib_toolchain": sha(FORMAL / "lean-toolchain"),
        "mathlib_manifest": sha(FORMAL / "lake-manifest.json"),
        "proof_source": sha(SOURCE),
    }
    contract = json.loads(CONTRACT.read_text())
    manifest = json.loads((FORMAL / "lake-manifest.json").read_text())
    mathlib_revs = [p.get("rev") for p in manifest.get("packages", []) if p.get("name") == "mathlib"]
    identities_ok = (
        input_hashes["contract"] == CONTRACT_SHA
        and input_hashes["common_spec"] == COMMON_SHA
        and input_hashes["formal_toolchain"] == TOOLCHAIN_SHA
        and input_hashes["mathlib_toolchain"] == TOOLCHAIN_SHA
        and input_hashes["mathlib_manifest"] == MANIFEST_SHA
        and input_hashes["proof_source"] == PROOF_SHA
        and mathlib_revs == [MATHLIB_REV]
        and contract["target"]["exact_test_obligations"] == ["CAS-06-C03-SCALAR"]
        and contract["semantics"]["branches"] == ["positive-real power X^s=exp(s log X)"]
    )
    source = SOURCE.read_text()
    forbidden_source = bool(re.search(r"(?m)^\s*(?:sorry|admit|axiom)\b|\bby\s+sorry\b", source))
    version_argv = ["lake", "env", "lean", "--version"]
    version = subprocess.run(version_argv, cwd=FORMAL, text=True, capture_output=True, timeout=60)
    (HERE / "toolchain_version.stdout.log").write_text(version.stdout)
    (HERE / "toolchain_version.stderr.log").write_text(version.stderr)
    version_command = {
        "argv": version_argv, "cwd": str(FORMAL), "timeout_seconds": 60,
        "exit_code": version.returncode,
        "stdout_path": str(HERE / "toolchain_version.stdout.log"),
        "stderr_path": str(HERE / "toolchain_version.stderr.log"),
    }
    version_ok = version.returncode == 0 and "Lean (version 4.31.0," in version.stdout
    argv = ["lake", "env", "lean", str(SOURCE)]
    command = {"argv": argv, "cwd": str(FORMAL), "timeout_seconds": 3500}
    try:
        done = subprocess.run(argv, cwd=FORMAL, text=True, capture_output=True, timeout=3500)
        exit_code = done.returncode
        stdout, stderr = done.stdout, done.stderr
    except subprocess.TimeoutExpired as exc:
        exit_code = 124
        stdout = (exc.stdout or b"").decode(errors="replace") if isinstance(exc.stdout, bytes) else (exc.stdout or "")
        stderr = (exc.stderr or b"").decode(errors="replace") if isinstance(exc.stderr, bytes) else (exc.stderr or "")
        stderr += "\nTIMEOUT after 3500 seconds\n"
    (HERE / "final.stdout.log").write_text(stdout)
    (HERE / "final.stderr.log").write_text(stderr)
    command["exit_code"] = exit_code
    command["stdout_path"] = str(HERE / "final.stdout.log")
    command["stderr_path"] = str(HERE / "final.stderr.log")
    found = {}
    for name, raw in re.findall(r"'CAS06Scalar\.([^']+)' depends on axioms: \[([^\]]*)\]", stdout):
        found[name] = {part.strip() for part in raw.split(",") if part.strip()}
    axioms_ok = set(found) == set(THEOREMS) and all(v <= ALLOWED_AXIOMS for v in found.values())
    no_compiler_errors = "error" not in stdout.lower() and "error" not in stderr.lower()
    passed = identities_ok and version_ok and not forbidden_source and exit_code == 0 and axioms_ok and no_compiler_errors
    completed_at = datetime.now(timezone.utc).isoformat()
    payload = {
        "checks": {"CAS-06-C03-SCALAR": passed},
        "domain_assumption_diff": [],
        "counterexample": None,
    }
    evidence = {
        "axis": "lean", "status": "PASS" if passed else "FAIL",
        "contract_sha256": input_hashes["contract"],
        "commands": [version_command, command], "evidence_class": "exact", "completed_at": completed_at,
        "statement_alignment": {
            "component": "CAS-06-C03-SCALAR",
            "domain": "Pstar>0, X>0, 0<alpha<1; s=(1+alpha)/(2alpha)",
            "branch": "X^s=exp(s*log X)",
            "proved": "actual first and second deriv, algebraic E identity, positive denominator, derivative ratio alpha",
            "limits": "scalar calculus only; no metric stress/current, TOV, physical sound propagation, or full C03",
        },
        "source_sha256": input_hashes["proof_source"],
        "input_hashes": input_hashes,
        "mathlib_revision": mathlib_revs,
        "proof_theorems": list(THEOREMS),
        "axioms_by_theorem": {k: sorted(v) for k, v in found.items()},
        "checks_detail": {
            "identities_ok": identities_ok, "version_ok": version_ok,
            "forbidden_source": forbidden_source,
            "axioms_ok": axioms_ok, "no_compiler_errors": no_compiler_errors,
        },
        "actual_validation_payload": payload,
    }
    (HERE / "result.json").write_text(json.dumps(evidence, indent=2, sort_keys=True) + "\n")
    print(json.dumps(payload, separators=(",", ":")))
    return 0 if passed else 1


if __name__ == "__main__":
    sys.exit(main())
