"""Execute the frozen Sage/Singular axis; no arguments emit the minimal gate JSON."""

import hashlib
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[5]
CONTRACT = HERE.parent / "EXECUTION_CONTRACT.json"
INPUTS = HERE.parent / "ADMITTED_INPUTS.json"
SAGE = "/usr/local/bin/sage"
SINGULAR = "/home/cosmosapjw/opt/sage/local/bin/Singular"
CONTRACT_SHA = "1085005167c4bfeeb2ec6c7199f94c73d2b0651b381bcce00fdc05275f090169"
INPUTS_SHA = "e6c66e6a944ee4f67c591d54281f5c3577d32852f66084767a5a6fec215d2992"


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def singular_source():
    b = ("b1", "b2", "b3")

    def entry(i, j, sign):
        if i == j == 0:
            return "g"
        if i == 0:
            return f"({sign}*g*{b[j-1]})"
        if j == 0:
            return f"({sign}*g*{b[i-1]})"
        delta = "1" if i == j else "0"
        return f"({delta}+h*{b[i-1]}*{b[j-1]})"

    lines = ["// PORT-CAS-01 exact polynomial ideal reductions, Sage-bundled Singular 4.4.1",
             "ring r=0,(b1,b2,b3,g,h),dp;",
             "poly s=b1^2+b2^2+b3^2;",
             "ideal J=g^2*(1-s)-1,h*(g+1)-g^2;",
             "ideal G=std(J);", "int fail=0;"]
    polynomials = []
    for i in range(4):
        for j in range(4):
            terms = [f"({-1 if k == 0 else 1}*{entry(k,i,1)}*{entry(k,j,1)})" for k in range(4)]
            target = -1 if i == j == 0 else (1 if i == j else 0)
            polynomials.append("+".join(terms) + f"-({target})")
    for i in range(4):
        for j in range(4):
            terms = [f"({entry(i,k,1)}*{entry(k,j,-1)})" for k in range(4)]
            polynomials.append("+".join(terms) + f"-({1 if i == j else 0})")
    polynomials.append("-g^2+g^2*(b1^2+b2^2+b3^2)+1")
    assert len(polynomials) == 33
    for n, polynomial in enumerate(polynomials):
        lines.extend((f"poly p{n}={polynomial};", f"poly q{n}=reduce(p{n},G);",
                      f'if (q{n} != 0) {{ print("FAIL residual {n}"); print(q{n}); fail=1; }}'))
    lines += ['if (fail == 0) { print("PORT_CAS_01_PASS count=33"); }']
    return "\n".join(lines) + "\n"


def run(label, argv):
    try:
        proc = subprocess.run(argv, cwd=HERE, capture_output=True, timeout=1800)
        code = proc.returncode
        out, err = proc.stdout, proc.stderr
    except subprocess.TimeoutExpired as exc:
        code = 124
        out, err = exc.stdout or b"", (exc.stderr or b"") + b"\nTIMEOUT 1800s\n"
    (HERE / f"{label}.stdout.log").write_bytes(out)
    (HERE / f"{label}.stderr.log").write_bytes(err)
    return {"argv": argv, "exit": code, "stdout_path": str(HERE / f"{label}.stdout.log"),
            "stderr_path": str(HERE / f"{label}.stderr.log"),
            "stdout_sha256": sha(HERE / f"{label}.stdout.log"),
            "stderr_sha256": sha(HERE / f"{label}.stderr.log")}, out.decode(errors="replace"), err.decode(errors="replace")


def main():
    if len(sys.argv) != 1:
        raise SystemExit("run_axis.py takes no arguments")
    if sha(CONTRACT) != CONTRACT_SHA or sha(INPUTS) != INPUTS_SHA:
        raise SystemExit("frozen contract/input hash mismatch")
    singular_script = HERE / "singular_verify.sing"
    source = singular_source()
    if singular_script.exists() and singular_script.read_text() != source:
        raise SystemExit("existing Singular source differs from generated source")
    singular_script.write_text(source)
    commands = []
    observations = {}
    for label, argv in (("sage_version", [SAGE, "--version"]),
                        ("singular_version", [SINGULAR, "--version"]),
                        ("sage_exact", [SAGE, "-python", str(HERE / "sage_verify.py")]),
                        ("singular_exact", [SINGULAR, "-q", str(singular_script)])):
        record, out, err = run(label, argv)
        commands.append(record)
        observations[label] = {"stdout": out, "stderr": err, "exit": record["exit"]}
    sage_ok = (observations["sage_version"]["exit"] == 0 and
               "SageMath version 10.9" in observations["sage_version"]["stdout"] and
               observations["sage_exact"]["exit"] == 0 and
               '"all_zero": true' in observations["sage_exact"]["stdout"])
    singular_ok = (observations["singular_version"]["exit"] == 0 and
                   "version 4.4.1" in observations["singular_version"]["stdout"] and
                   observations["singular_exact"]["exit"] == 0 and
                   "PORT_CAS_01_PASS count=33" in observations["singular_exact"]["stdout"] and
                   "FAIL residual" not in observations["singular_exact"]["stdout"])
    errors = [k for k, ok in (("sage_exact", sage_ok), ("singular_exact", singular_ok)) if not ok]
    result = {
        "axis": "sage_singular", "status": "PASS" if not errors else "BLOCKED",
        "contract_sha256": CONTRACT_SHA, "admitted_inputs_sha256": INPUTS_SHA,
        "evidence_class": "exact", "completed_at": datetime.now(timezone.utc).isoformat(),
        "checks": {"PORT-CAS-01": not errors}, "domain_assumption_diff": [], "counterexample": None,
        "statement_alignment": {
            "metric": "33 exact residuals include 16 metric entries",
            "inverse": "16 inverse entries",
            "mass_shell": "u0=g>0; one exact polynomial residual",
            "converse": "s=1-1/zeta0^2<1; positive sqrt yields gamma=zeta0 for zeta0>=1",
            "excluded": "s=1 boundary and past branch excluded",
        },
        "versions": {"sage": observations["sage_version"]["stdout"].strip(),
                     "singular": "4.4.1 (44100)" if singular_ok else "unverified"},
        "executables": {SAGE: sha(SAGE), SINGULAR: sha(SINGULAR)},
        "source_hashes": {"sage_verify.py": sha(HERE / "sage_verify.py"),
                          "singular_verify.sing": sha(singular_script), "run_axis.py": sha(__file__)},
        "commands": commands, "errors": errors,
        "launch_id": None, "global_registered_launch": False,
        "observed_model": "UNKNOWN", "observed_effort": "UNKNOWN",
        "lifecycle_status": "BLOCKED", "scientific_admission": "HOLD",
        "claim_ceiling": "PORT-CAS-01 finite algebra only",
    }
    (HERE / "axis_result.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"checks": result["checks"], "domain_assumption_diff": [],
                      "counterexample": None}, separators=(",", ":")))
    return 0 if not errors else 2


if __name__ == "__main__":
    raise SystemExit(main())
