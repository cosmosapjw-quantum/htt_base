"""Run and record the independent Sage/Singular scalar certificate."""

import hashlib
import json
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path("/home/cosmosapjw/Dropbox/bianchi/htt_base")
HERE = Path(__file__).resolve().parent
CONTRACT = HERE.parent / "C03_SCALAR_CONTRACT.json"
COMMON = ROOT / "docs/research_program/gr_statistics_loops_20260930/cas/COMMON_SPEC.md"
EXPECTED_CONTRACT = "7742ee4abac523eabc466435f115de88228a957a3dbed946fa5311f99ab07c27"
EXPECTED_COMMON = "4714827e52acf3cb149f4014ac50ab2aa995dd4a0526f6b26ac7257807fe1897"
SINGULAR = "/home/cosmosapjw/opt/sage/local/bin/Singular"
SAGE = "/usr/local/bin/sage"
OBLIGATION = "CAS-06-C03-SCALAR"
TIMEOUT = 1800


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def rel(path):
    return str(path.relative_to(ROOT))


def run_command(name, argv):
    start = datetime.now(timezone.utc).isoformat()
    try:
        p = subprocess.run(argv, cwd=ROOT, capture_output=True, text=True,
                           timeout=TIMEOUT, check=False)
        stdout, stderr, code, timed_out = p.stdout, p.stderr, p.returncode, False
    except subprocess.TimeoutExpired as exc:
        stdout = (exc.stdout or b"").decode(errors="replace") if isinstance(exc.stdout, bytes) else (exc.stdout or "")
        stderr = (exc.stderr or b"").decode(errors="replace") if isinstance(exc.stderr, bytes) else (exc.stderr or "")
        code, timed_out = None, True
    except OSError as exc:
        stdout, stderr, code, timed_out = "", str(exc), None, False
    out_path, err_path = HERE / f"{name}.stdout.log", HERE / f"{name}.stderr.log"
    out_path.write_text(stdout)
    err_path.write_text(stderr)
    return {
        "name": name, "argv": argv, "cwd": str(ROOT), "exit": code,
        "timeout_seconds": TIMEOUT, "timed_out": timed_out,
        "started_at": start, "completed_at": datetime.now(timezone.utc).isoformat(),
        "stdout_path": rel(out_path), "stderr_path": rel(err_path),
        "stdout_sha256": digest(out_path), "stderr_sha256": digest(err_path),
    }, stdout, stderr


def main():
    sources = [CONTRACT, COMMON, HERE / "run.py", HERE / "engine.py",
               HERE / "certificate.sing", HERE / "PROOF.md"]
    hashes = {rel(p): digest(p) for p in sources}
    commands = []
    issues = []
    checks = {}
    expected = {rel(CONTRACT): EXPECTED_CONTRACT, rel(COMMON): EXPECTED_COMMON}
    for path, wanted in expected.items():
        if hashes[path] != wanted:
            issues.append(f"input hash mismatch: {path}")
    if not issues:
        cmd, stdout, stderr = run_command("singular_origin", [
            SAGE, "-sh", "-c", "command -v Singular; Singular --version"
        ])
        commands.append(cmd)
        if cmd["exit"] != 0 or stdout.splitlines()[0:1] != [SINGULAR]:
            issues.append("Singular did not resolve to the Sage-bundled executable")
        if "version 4.4.1 (44100" not in stdout:
            issues.append("Singular version 4.4.1/44100 not observed")
        if stderr.strip():
            issues.append("Singular origin probe emitted stderr")
    if not issues:
        cmd, stdout, stderr = run_command("sage_engine", [
            SAGE, "-python", rel(HERE / "engine.py")
        ])
        commands.append(cmd)
        try:
            data = json.loads(stdout)
            checks = data["checks"]
            if data["sage_version"] != "10.9":
                issues.append("Sage 10.9 not observed")
            if set(checks) != {
                "first_from_differentiation", "second_from_differentiation",
                "energy_identity", "denominator_factorization",
                "exponent_relation", "ratio_identity",
            } or not all(value is True for value in checks.values()):
                issues.append("Sage exact certificate failed or incomplete")
        except (ValueError, KeyError, TypeError) as exc:
            issues.append(f"Sage output not an exact certificate: {exc}")
        if cmd["exit"] != 0 or stderr.strip():
            issues.append("Sage failed or emitted stderr")
    if not issues:
        cmd, stdout, stderr = run_command("singular_certificate", [
            SAGE, "-sh", "-c", f"Singular -q {rel(HERE / 'certificate.sing')}"
        ])
        commands.append(cmd)
        required_lines = {
            "SINGULAR_CERT_ENERGY_REMAINDER=0",
            "SINGULAR_CERT_RATIO_REMAINDER=0",
            "SINGULAR_CERT_ENERGY_QUOTIENT_CHECK=0",
            "SINGULAR_CERT_RATIO_QUOTIENT_CHECK=0",
            "SINGULAR_CERT_ALL_OK",
        }
        if not required_lines.issubset(set(stdout.splitlines())):
            issues.append("Singular exact numerator/quotient certificates missing")
        if cmd["exit"] != 0 or stderr.strip():
            issues.append("Singular failed or emitted stderr")
        if re.search(r"(?im)^\s*(?:\?|error:|//\s*\*\*)", stdout):
            issues.append("Singular stdout contains an engine error")
    passed = not issues
    result = {
        "axis": "sage_singular",
        "status": "PASS" if passed else "FAIL",
        "evidence_class": "exact",
        "contract_sha256": hashes[rel(CONTRACT)],
        "completed_at": datetime.now(timezone.utc).isoformat(),
        "commands": commands,
        "source_sha256": hashes,
        "checks": checks,
        "domain_assumption_diff": [],
        "counterexample": None,
        "statement_alignment": {
            "component": OBLIGATION,
            "domain": "X>0, Pstar>0, 0<alpha<1; positive-real X^s",
            "positivity": "D=Pstar*s*(2s-1)*X^(s-1)>0 by positive factors",
            "limits": "scalar calculus only; no stress/current/TOV/physical sound speed/full C03",
        },
        "issues": issues,
        "author_runtime": "Codex child; observed model metadata unavailable in this axis",
    }
    (HERE / "result.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    payload = {"checks": {OBLIGATION: passed},
               "domain_assumption_diff": [], "counterexample": None}
    print(json.dumps(payload, sort_keys=True))
    return 0 if passed else 1


if __name__ == "__main__":
    sys.exit(main())
