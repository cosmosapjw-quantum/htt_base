"""Single deterministic CAS-15-C03 Sage/Singular content gate and receipt writer."""
import hashlib
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = next(p for p in HERE.parents if (p / "AGENTS.md").is_file())
CONTRACT = HERE.parent / "EXECUTION_CONTRACT.json"
ADMITTED = HERE.parent / "ADMITTED_INPUTS.json"
COMMON = REPO / "docs/research_program/gr_statistics_loops_20260930/cas/COMMON_SPEC.md"
SINGULAR = Path("/home/cosmosapjw/opt/sage/local/bin/Singular")


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def command(argv, stem):
    proc = subprocess.run(argv, cwd=HERE, capture_output=True, check=False)
    out = HERE / f"{stem}.stdout.log"
    err = HERE / f"{stem}.stderr.log"
    out.write_bytes(proc.stdout)
    err.write_bytes(proc.stderr)
    receipt = {
        "argv": [str(a) for a in argv], "cwd": str(HERE), "exit_code": proc.returncode,
        "stdout_path": str(out.relative_to(REPO)), "stdout_sha256": digest(out),
        "stderr_path": str(err.relative_to(REPO)), "stderr_sha256": digest(err),
    }
    (HERE / f"{stem}.command.json").write_text(json.dumps(receipt, indent=2) + "\n")
    return proc, receipt


def require(condition, description, checks):
    checks.append({"name": description, "pass": bool(condition)})
    if not condition:
        raise AssertionError(description)


def main():
    checks = []
    commands = []
    contract = json.loads(CONTRACT.read_text())
    admitted = json.loads(ADMITTED.read_text())
    require(contract["identity"]["contract_id"] ==
            "GRSTAT-20260930-CAS-15-C03-COMMUTATOR-INVERSE-V1", "contract identity", checks)
    require(admitted["component"] == "CAS-15-C03", "admitted component", checks)
    require(contract["independence"]["mode"] == "blind-results-and-derivations", "blind mode", checks)
    source_hashes = {e["path"]: e["sha256"] for e in contract["identity"]["source_input_hashes"]}
    for source in (ADMITTED, COMMON):
        rel = str(source.relative_to(REPO))
        require(digest(source) == source_hashes[rel], f"source sha256 {rel}", checks)
    require(digest(SINGULAR) == contract["toolchain_binding"]["singular"]["binary_sha256"],
            "pinned Singular binary sha256", checks)

    sv, receipt = command(["sage", "--version"], "sage.version")
    commands.append(receipt)
    require(sv.returncode == 0 and b"SageMath version 10.9" in sv.stdout and not sv.stderr,
            "Sage 10.9 version and clean stderr", checks)
    gv, receipt = command([str(SINGULAR), "--version"], "singular.version")
    commands.append(receipt)
    require(gv.returncode == 0 and b"version 4.4.1 (44100" in gv.stdout and not gv.stderr,
            "Singular 4.4.1/44100 version and clean stderr", checks)

    sage, receipt = command(["sage", "-python", "finite.py"], "sage.final")
    commands.append(receipt)
    sage_lines = sage.stdout.decode("utf-8", errors="replace").splitlines()
    require(sage.returncode == 0 and not sage.stderr and sage_lines == [
        "SAGE_COMMUTATOR_POLYNOMIAL_AND_RANK_OK",
        "SAGE_LEAST_SQUARES_PROJECTION_AND_INVERSE_OK",
        "SAGE_C03_EXACT_CONTENT_OK",
    ], "Sage exact polynomial/projection content and stderr", checks)

    singular, receipt = command([str(SINGULAR), "-q", "commutator.sing"], "singular.final")
    commands.append(receipt)
    singular_text = singular.stdout.decode("utf-8", errors="replace")
    require(singular.returncode == 0 and not singular.stderr and
            singular_text.count("CAS15_C03_SINGULAR_CONTENT_OK") == 1 and
            "FAIL" not in singular_text and "?" not in singular_text and
            "determinant=\n" in singular_text and "rank3_ideal=\n" in singular_text and
            "rank2_ideal=\n" in singular_text and "rank1_ideal=\n" in singular_text and
            "m1*m2-m1*m3-m2*m3+m3^2" in singular_text and
            "m2-m3,\nm1-m3,\nm1-m2" in singular_text,
            "Singular substantive determinant/minor ideals and clean stderr/content", checks)

    artifacts = {p.name: digest(p) for p in (
        HERE / "finite.py", HERE / "commutator.sing", HERE / "DERIVATION.md",
        HERE / "run.py", HERE / "sage.final.stdout.log", HERE / "sage.final.stderr.log",
        HERE / "singular.final.stdout.log", HERE / "singular.final.stderr.log",
    )}
    gate = {
        "component": "CAS-15-C03", "axis": "sage_singular", "status": "PASS",
        "contract_sha256": digest(CONTRACT), "checks": checks,
        "source_sha256": {"EXECUTION_CONTRACT.json": digest(CONTRACT),
                          "ADMITTED_INPUTS.json": digest(ADMITTED), "COMMON_SPEC.md": digest(COMMON)},
        "artifacts_sha256": artifacts, "commands": commands,
        "scope": "finite commutator inverse, gap, least-squares perturbation and ordered Weyl gap only",
        "domain_assumption_diff": [], "counterexample": None,
        "lifecycle": {"global_registered_launch_id": None, "authority": "UNAVAILABLE",
                      "observed_model": "UNKNOWN", "observed_effort": "UNKNOWN",
                      "status": "BLOCKED_UNREGISTERED"},
        "scientific_admission": "HOLD",
    }
    (HERE / "gate.json").write_text(json.dumps(gate, indent=2, sort_keys=True) + "\n")
    result = {
        "axis": "sage_singular", "status": "PASS", "evidence_class": "exact",
        "contract_sha256": digest(CONTRACT),
        "completed_at": datetime.now(timezone.utc).isoformat(),
        "commands": commands, "checks": checks,
        "domain_assumption_diff": [], "counterexample": None,
        "gate_path": str((HERE / "gate.json").relative_to(REPO)),
        "gate_sha256": digest(HERE / "gate.json"),
        "source_artifacts_sha256": artifacts,
        "runtime": gate["lifecycle"], "scientific_admission": "HOLD",
        "claim_ceiling": contract["identity"]["claim_ceiling"],
        "remaining": contract["full_theorem_boundary"]["remaining"],
    }
    (HERE / "axis_result.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"checks": {"CAS-15-C03": True},
                      "domain_assumption_diff": [], "counterexample": None},
                     separators=(",", ":")))


if __name__ == "__main__":
    main()
