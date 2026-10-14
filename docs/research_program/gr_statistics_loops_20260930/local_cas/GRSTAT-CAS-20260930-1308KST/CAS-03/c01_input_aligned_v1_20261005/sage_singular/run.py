"""Frozen no-argument C01 Sage/Singular axis entrypoint.

Each invocation keeps source/input copies and full process output under a new
attempt directory. Only this axis writes here.
"""
import datetime
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys

ROOT = Path("/home/cosmosapjw/Dropbox/bianchi/htt_base")
P = ROOT / "docs/research_program/gr_statistics_loops_20260930/local_cas/GRSTAT-CAS-20260930-1308KST/CAS-03/c01_input_aligned_v1_20261005"
HERE = P / "sage_singular"
CONTRACT = P / "EXECUTION_CONTRACT.json"
INPUTS = P / "ADMITTED_INPUTS.json"
COMMON = ROOT / "docs/research_program/gr_statistics_loops_20260930/cas/COMMON_SPEC.md"
EXPECTED = {
    CONTRACT: "4d3a35a731ce79d47490d54843239a5bf3f7c670015916356b95504cf5be6f3f",
    INPUTS: "a5189ee52fc769c284c604a4caf29051f0256973d5c5bf9dc0f439a4acecdb46",
    COMMON: "4714827e52acf3cb149f4014ac50ab2aa995dd4a0526f6b26ac7257807fe1897",
}
SAGE = Path("/home/cosmosapjw/opt/sage/sage")
SINGULAR = Path("/home/cosmosapjw/opt/sage/local/bin/Singular")
SOURCES = [HERE/"run.py", HERE/"c01.sage.py", HERE/"c01.sing"]


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def rel(path):
    return str(path.relative_to(ROOT))


def now():
    return datetime.datetime.now(datetime.timezone.utc).isoformat()


def main():
    HERE.mkdir(exist_ok=True)
    stamp = datetime.datetime.now(datetime.timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
    attempt = HERE / ("attempt_" + stamp)
    attempt.mkdir()
    snapshots = attempt / "snapshots"
    snapshots.mkdir()
    all_sources = [*EXPECTED, *SOURCES]
    before = {rel(p):sha(p) for p in all_sources}
    for p in all_sources:
        dest = snapshots / rel(p)
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(p,dest)
    checks = {"CAS-03-C01":False}
    commands = []
    failures = []
    def execute(label, argv, timeout=1800):
        outp, errp = attempt/(label+".stdout"), attempt/(label+".stderr")
        try:
            p = subprocess.run(argv, cwd=ROOT, capture_output=True, text=True,
                               timeout=timeout, check=False)
            out, err, code = p.stdout, p.stderr, p.returncode
        except subprocess.TimeoutExpired as e:
            out = (e.stdout or b"").decode(errors="replace") if isinstance(e.stdout,bytes) else (e.stdout or "")
            err = (e.stderr or b"").decode(errors="replace") if isinstance(e.stderr,bytes) else (e.stderr or "")
            err += "\nTIMEOUT\n"
            code = 124
        except OSError as e:
            out,err,code = "", repr(e),127
        outp.write_text(out)
        errp.write_text(err)
        command = {"label":label,"argv":[str(x) for x in argv],"cwd":str(ROOT),
                   "exit_code":code,"stdout_path":rel(outp),"stderr_path":rel(errp),
                   "stdout_sha256":sha(outp),"stderr_sha256":sha(errp)}
        commands.append(command)
        return code,out,err
    try:
        for path,want in EXPECTED.items():
            if before[rel(path)] != want:
                failures.append("frozen input SHA mismatch: "+rel(path))
        if not failures:
            sage_version = execute("sage_version",[SAGE,"--version"],30)
            singular_version = execute("singular_version",[SINGULAR,"--version"],30)
            if sage_version[0] or "10.9" not in sage_version[1]:
                failures.append("Sage version or command failed")
            if singular_version[0] or "version 4.4.1" not in singular_version[1] or "44100" not in singular_version[1]:
                failures.append("bundled Singular version or command failed")
            if not failures:
                sage_run = execute("sage",[SAGE,"-python",HERE/"c01.sage.py"])
                singular_run = execute("singular",[SINGULAR,"-q",HERE/"c01.sing"])
                if sage_run[0]:
                    failures.append("Sage nonzero exit")
                if singular_run[0]:
                    failures.append("Singular nonzero exit")
                try:
                    report = json.loads(sage_run[1].strip())
                    if report.get("CAS-03-C01") is not True:
                        failures.append("Sage exact check false")
                except Exception as e:
                    report = None
                    failures.append("Sage report parse failure: "+repr(e))
                # Singular can return zero despite a language error. Require
                # the final marker and inspect all raw stdout/stderr.
                combined = singular_run[1]+"\n"+singular_run[2]
                if "SINGULAR_CERTIFICATE_PASS" not in singular_run[1]:
                    failures.append("Singular proof marker missing")
                if "GROEBNER_NORMAL_FORM=\n0" not in singular_run[1]:
                    failures.append("Singular Groebner normal form not zero")
                if any(word in combined.lower() for word in
                       ["error occurred","not defined","syntax error","fail ","failed"]):
                    failures.append("Singular raw output contains error/failure")
        after = {rel(p):sha(p) for p in all_sources}
        if before != after:
            failures.append("source/input changed during execution")
        for p in all_sources:
            if sha(snapshots/rel(p)) != before[rel(p)]:
                failures.append("attempt snapshot mismatch: "+rel(p))
        checks["CAS-03-C01"] = not failures
        status = "PASS" if checks["CAS-03-C01"] else "FAIL"
        result = {
            "axis":"sage_singular","status":status,
            "contract_sha256":EXPECTED[CONTRACT],"evidence_class":"exact",
            "evidence_description":"Sage exact polynomial and matrix/kernel identities, plus bundled Singular Groebner ideal membership; real positive-root uniqueness argument applies over every admitted rank.",
            "completed_at":now(),"checks":checks,
            "domain_assumption_diff":[],"counterexample":None,
            "commands":commands,"failures":failures,
            "statement_alignment":{
                "component":"CAS-03-C01","mass_shell":"u^T g u=-1, u0>0",
                "definition":"s_t=-u^T S u; B=S-s_t g; S real symmetric",
                "rest_condition":"u=e0 and Bu=0 imply zero time row/column; tr D=0 is zero-expansion",
                "all_ranks":True,"future_chart":"Phi(w)=(sqrt(1+w.w),w), w in ker D",
                "scope_limit":"conditional rest-frame kernel; no universal timelike eigenline existence, IFT, or physical realization"
            },
            "source_input_hashes_before":before,
            "source_input_hashes_after":after,
            "toolchain":{
                "sage_path":str(SAGE),"sage_sha256":sha(SAGE),
                "singular_path":str(SINGULAR),"singular_sha256":sha(SINGULAR),
            },
            "attempt_path":rel(attempt)
        }
        (attempt/"execution.json").write_text(json.dumps(result,indent=2,sort_keys=True)+"\n")
        (HERE/"result.json").write_text(json.dumps(result,indent=2,sort_keys=True)+"\n")
        print(json.dumps({"checks":checks,"status":status,
                          "domain_assumption_diff":[],"counterexample":None,
                          "attempt_path":rel(attempt),"failures":failures},sort_keys=True))
        return 0 if checks["CAS-03-C01"] else 1
    except Exception as e:
        (attempt/"runner_exception.txt").write_text(repr(e)+"\n")
        print(json.dumps({"checks":checks,"status":"FAIL","error":repr(e)}))
        return 1


if __name__ == "__main__":
    sys.exit(main())
