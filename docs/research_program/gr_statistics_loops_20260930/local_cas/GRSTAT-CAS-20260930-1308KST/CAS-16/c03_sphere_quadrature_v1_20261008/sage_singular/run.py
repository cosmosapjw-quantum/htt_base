"""No-argument, isolated Sage/Singular executor for frozen CAS-16-C03."""

import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import traceback
from datetime import datetime, timezone
from math import comb


HERE = Path(__file__).resolve().parent
COMPONENT = HERE.parent
REPO = next(p for p in HERE.parents if (p / "AGENTS.md").is_file())
CONTRACT = COMPONENT / "EXECUTION_CONTRACT.json"
INPUTS = COMPONENT / "ADMITTED_INPUTS.json"
COMMON = REPO / "docs/research_program/gr_statistics_loops_20260930/cas/COMMON_SPEC.md"
SINGULAR = Path("/home/cosmosapjw/opt/sage/local/bin/Singular")
CONTRACT_SHA = "d36ffedcbeb64c201671e78e42be41ea9b6d160d148d7aadf51134a9dfbe068c"
INPUTS_SHA = "6c536bf89687f6f4f8aaeec90154e1c9cf20b994870e789faa3cff5d5735ac82"
COMMON_SHA = "4714827e52acf3cb149f4014ac50ab2aa995dd4a0526f6b26ac7257807fe1897"


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def coefficient0(a, b):
    d = a + b
    return sum(comb(a, k) * comb(b, l) * (-1) ** l
               for k in range(a + 1) for l in range(b + 1)
               if d - 2 * (k + l) == 0)


def generate_singular():
    lines = [
        "// Independent quotient-ring checks for the fixed finite grid.",
        "ring r=0,(u,v,p,q,t),dp;",
        "ideal I=u^2-70,7*v^2-10,u*v-10,9*p^2-5+2*v,9*q^2-5-2*v,t^9-1;",
        "ideal G=std(I);",
        "int failures=0;",
    ]
    for k in range(9):
        if k % 2:
            # Paired nodes cancel; verify the symbolic pair sum exactly.
            expr = f"((322+13u)/900)*(p^{k}-p^{k})+((322-13u)/900)*(q^{k}-q^{k})"
            target = "0"
        else:
            center = "128/225+" if k == 0 else ""
            expr = center + f"2*((322+13u)/900*p^{k}+(322-13u)/900*q^{k})"
            target = f"2/{k+1}"
        lines.append(f"if (reduce(({expr})-({target}),G)!=0) {{ failures=failures+1; print(\"GL5_FAIL_{k}\"); }}")
    for a in range(9):
        for b in range(9-a):
            d = a+b
            expected = coefficient0(a,b)
            lines.append(f"poly az_{a}_{b}=reduce((t+t^8)^{a}*(t-t^8)^{b},G);")
            lines.append(f"if (subst(az_{a}_{b},t,0)!={expected}) {{ failures=failures+1; print(\"AZ_FAIL_{a}_{b}\"); }}")
    # The N=8 quotient aliases the degree-eight Fourier endpoints.
    lines.extend([
        "ideal J=t^8-1; ideal H=std(J);",
        "poly az8=reduce((t+t^7)^8,H);",
        "if (subst(az8,t,0)!=72) { failures=failures+1; print(\"AZ8_FAIL\"); }",
        "if (72-70!=2) { failures=failures+1; print(\"AZ8_DIFFERENCE_FAIL\"); }",
        "if (failures==0) { print(\"SINGULAR_PASS GL5=9 AZ9=45 AZ8=1\"); }",
        "else { print(\"SINGULAR_FAIL\"); }",
        "exit;",
    ])
    path = HERE / "verify.sing"
    source = "\n".join(lines) + "\n"
    if path.exists():
        if path.read_text(encoding="utf-8") != source:
            raise RuntimeError("Refusing to replace divergent Singular source")
    else:
        path.write_text(source, encoding="utf-8")
    return path


def run(argv, stem, timeout=1800):
    proc = subprocess.run(argv, cwd=HERE, capture_output=True, timeout=timeout)
    out = HERE / f"{stem}.stdout.log"
    err = HERE / f"{stem}.stderr.log"
    if out.exists() or err.exists():
        raise RuntimeError(f"Preserving pre-existing raw logs: {stem}")
    out.write_bytes(proc.stdout)
    err.write_bytes(proc.stderr)
    return {"cmd": argv, "exit": proc.returncode, "stdout": out.name,
            "stdout_sha256": digest(out), "stderr": err.name, "stderr_sha256": digest(err)}


def main():
    if len(sys.argv) != 1:
        raise RuntimeError("run.py accepts no arguments")
    for path, expected in [(CONTRACT, CONTRACT_SHA), (INPUTS, INPUTS_SHA), (COMMON, COMMON_SHA)]:
        if digest(path) != expected:
            raise RuntimeError(f"Frozen input hash mismatch: {path}")
    sage = Path(shutil.which("sage") or "")
    if not sage.is_file() or not SINGULAR.is_file():
        raise RuntimeError("Required CAS executable missing")
    singular_source = generate_singular()
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
    commands = []
    commands.append(run([str(sage), "--version"], f"sage_version_{stamp}", 30))
    commands.append(run([str(SINGULAR), "--version"], f"singular_version_{stamp}", 30))
    commands.append(run([str(sage), "-python", "verify.sage.py"], f"sage_verify_{stamp}"))
    commands.append(run([str(SINGULAR), "-q", "verify.sing"], f"singular_verify_{stamp}"))
    sage_version = (HERE / commands[0]["stdout"]).read_text(errors="replace")
    singular_version = (HERE / commands[1]["stdout"]).read_text(errors="replace")
    sage_out = (HERE / commands[2]["stdout"]).read_text(errors="replace")
    singular_out = (HERE / commands[3]["stdout"]).read_text(errors="replace")
    errors = []
    if any(c["exit"] != 0 for c in commands):
        errors.append("nonzero command exit")
    if "SageMath version 10.9" not in sage_version:
        errors.append("Sage version mismatch")
    if "4.4.1 (44100" not in singular_version:
        errors.append("Singular version mismatch")
    try:
        sage_result = json.loads(sage_out)
    except json.JSONDecodeError:
        sage_result = {}
        errors.append("Sage stdout is not exactly one JSON result")
    if sage_result.get("status") != "PASS" or sage_result.get("monomials_exact") != 165:
        errors.append("Sage exact certificate did not pass")
    if "SINGULAR_PASS GL5=9 AZ9=45 AZ8=1" not in singular_out:
        errors.append("Singular certificate did not pass")
    if any(s in singular_out.lower() for s in ["error", "not defined", "singular_fail", "// **", "? "]):
        errors.append("Singular reported a diagnostic")
    if any((HERE / c["stderr"]).stat().st_size for c in commands):
        errors.append("nonempty stderr; inspect raw logs")
    result = {
        "axis": "sage_singular", "status": "PASS" if not errors else "FAIL",
        "contract_sha256": CONTRACT_SHA, "evidence_class": "exact",
        "completed_at": datetime.now(timezone.utc).isoformat(), "commands": commands,
        "inputs": {str(CONTRACT.relative_to(REPO)): CONTRACT_SHA,
                   str(INPUTS.relative_to(REPO)): INPUTS_SHA,
                   str(COMMON.relative_to(REPO)): COMMON_SHA},
        "source_artifacts": {"run.py": digest(HERE / "run.py"),
                             "verify.sage.py": digest(HERE / "verify.sage.py"),
                             "verify.sing": digest(singular_source)},
        "executable_artifacts": {"sage_path": str(sage.resolve()),
                                 "sage_sha256": digest(sage.resolve()),
                                 "singular_path": str(SINGULAR.resolve()),
                                 "singular_sha256": digest(SINGULAR.resolve())},
        "tool_versions": {"sage": sage_version.strip().splitlines()[0],
                          "singular": singular_version.strip().splitlines()[0]},
        "alignment": {"scope": "CAS-16-C03 finite scalar monomials only",
                      "coordinate_domain": "-1<=mu<=1; 0<=phi<2*pi",
                      "sphere_map": "x=sqrt(1-mu^2)cos(phi), y=sqrt(1-mu^2)sin(phi), z=mu",
                      "sqrt_branch": "nonnegative real", "measure": "dmu dphi",
                      "normalization": "Q=(1/2)GL5 weights times (1/9) azimuth sum",
                      "exponents": "natural a,b,c; a+b+c<=8",
                      "claim_ceiling": "finite scalar product-grid component; no DP06 admission"},
        "checked": sage_result, "singular_stdout": singular_out.strip(), "errors": errors,
        "launch_id": None, "global_harness_used": False,
        "observed_model": "UNKNOWN", "observed_effort": "UNKNOWN",
        "lifecycle": "BLOCKED_NO_GLOBAL_REGISTERED_LAUNCH",
        "scientific_admission": "HOLD", "aggregate_eligibility": "HOLD",
    }
    gate = {"checks": {"CAS-16-C03": not errors},
            "domain_assumption_diff": [],
            "counterexample": {"execution_errors": errors} if errors else None}
    result["gate_payload"] = gate
    target = HERE / "axis_result.json"
    if target.exists():
        prior = target.read_bytes()
        archive = HERE / f"axis_result.previous-{hashlib.sha256(prior).hexdigest()}.json"
        if archive.exists():
            if archive.read_bytes() != prior:
                raise RuntimeError("Existing result archive differs from prior envelope")
        else:
            with archive.open("xb") as stream:
                stream.write(prior)
        result["prior_axis_result_archive"] = archive.name
    replacement = HERE / f"axis_result.{stamp}.tmp"
    with replacement.open("x", encoding="utf-8") as stream:
        stream.write(json.dumps(result, indent=2, sort_keys=True) + "\n")
    os.replace(replacement, target)
    return gate, 0 if not errors else 1


if __name__ == "__main__":
    try:
        payload, exit_code = main()
    except Exception as exc:
        traceback.print_exc(file=sys.stderr)
        payload = {"checks": {"CAS-16-C03": False},
                   "domain_assumption_diff": [f"execution exception: {type(exc).__name__}: {exc}"],
                   "counterexample": None}
        exit_code = 1
    print(json.dumps(payload, sort_keys=True))
    raise SystemExit(exit_code)
