#!/usr/bin/python3.12
"""No-argument, evidence-preserving execution of the independent C02 axis."""

import datetime as dt
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import time
import uuid


ROOT = Path("/home/cosmosapjw/Dropbox/bianchi/htt_base")
V = ROOT / "docs/research_program/gr_statistics_loops_20260930/local_cas/GRSTAT-CAS-20260930-1308KST/CAS-07/c02_input_aligned_v1_20261005"
OWN = V / "sage_singular"
CONTRACT = V / "EXECUTION_CONTRACT.json"
INPUTS = V / "ADMITTED_INPUTS.json"
COMMON = ROOT / "docs/research_program/gr_statistics_loops_20260930/cas/COMMON_SPEC.md"
SAGE = Path("/home/cosmosapjw/opt/sage/sage")
SINGULAR = Path("/home/cosmosapjw/opt/sage/local/bin/Singular")
EXPECTED = {
    str(CONTRACT): "367ea2b4221c2ef10c93d1c49ef75d40d0f030bf79ec429a0fe1dbfeb44c219a",
    str(INPUTS): "84e20f628abcc4879446c6987dec21416934dece1c94e23076d6ce491939e6b0",
    str(COMMON): "4714827e52acf3cb149f4014ac50ab2aa995dd4a0526f6b26ac7257807fe1897",
    str(SINGULAR): "9430832b7c972b6b26d29ded4d91a3e1df8fd87d67f4b8d3f14d8201a75f923c",
}
SNAPSHOT = [CONTRACT, INPUTS, COMMON, SAGE, SINGULAR, OWN / "run.py", OWN / "proof_sage.py", OWN / "proof_singular.sing", OWN / "PROOF.md"]
SHA = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()


def utcnow():
    return dt.datetime.now(dt.timezone.utc).isoformat()


def memory_state():
    fields = {}
    for line in Path("/proc/meminfo").read_text().splitlines():
        if line.startswith(("MemAvailable:", "SwapFree:", "SwapTotal:")):
            key, value = line.split(":", 1)
            fields[key] = value.strip()
    return fields


def command(argv, label, attempt, deadline, env=None):
    remaining = deadline - time.monotonic()
    if remaining <= 0:
        raise TimeoutError("1800-second total wall limit reached before " + label)
    started = utcnow()
    begin = time.monotonic()
    proc = subprocess.run(argv, cwd=ROOT, env=env, text=True, stdout=subprocess.PIPE,
                          stderr=subprocess.PIPE, timeout=remaining, check=False)
    (attempt / (label + ".stdout.log")).write_text(proc.stdout)
    (attempt / (label + ".stderr.log")).write_text(proc.stderr)
    return {"label": label, "argv": [str(a) for a in argv], "cwd": str(ROOT),
            "exit_code": proc.returncode, "started_at": started,
            "completed_at": utcnow(), "elapsed_seconds": time.monotonic() - begin,
            "stdout_path": str(attempt / (label + ".stdout.log")),
            "stderr_path": str(attempt / (label + ".stderr.log")),
            "stdout_sha256": SHA(attempt / (label + ".stdout.log")),
            "stderr_sha256": SHA(attempt / (label + ".stderr.log"))}


def main():
    if len(sys.argv) != 1 or Path.cwd().resolve() != ROOT:
        raise SystemExit("run.py accepts no arguments and must run at frozen repo root")
    deadline = time.monotonic() + 1800
    attempt = OWN / "attempts" / (dt.datetime.now(dt.timezone.utc).strftime("%Y%m%dT%H%M%SZ") + "_" + uuid.uuid4().hex[:10])
    attempt.mkdir(parents=True, exist_ok=False)
    snapshot_dir = attempt / "snapshots"
    snapshot_dir.mkdir()
    pre = {str(p): SHA(p) for p in SNAPSHOT}
    for p in SNAPSHOT:
        shutil.copy2(p, snapshot_dir / (hashlib.sha256(str(p).encode()).hexdigest()[:12] + "_" + p.name))
    record = {"axis": "sage_singular", "status": "INCONCLUSIVE",
              "contract_sha256": EXPECTED[str(CONTRACT)], "evidence_class": "exact",
              "checks": {"CAS-07-C02": False}, "domain_assumption_diff": [], "counterexample": None,
              "completed_at": None, "commands": [], "details": {}, "attempt_path": str(attempt),
              "source_input_tool_sha256_before": pre,
              "memory_before": memory_state()}
    failures = []
    try:
        for p, expected in EXPECTED.items():
            if pre[p] != expected:
                raise AssertionError(f"frozen identity mismatch {p}: {pre[p]} != {expected}")
        env = os.environ.copy()
        env["PATH"] = str(SINGULAR.parent) + os.pathsep + env.get("PATH", "")
        jobs = [
            ([str(SAGE), "--version"], "sage_version"),
            ([str(SINGULAR), "--version"], "singular_version"),
            ([str(SAGE), "-python", str(OWN / "proof_sage.py")], "sage_proof"),
            ([str(SINGULAR), "-q", str(OWN / "proof_singular.sing")], "singular_proof"),
        ]
        for argv, label in jobs:
            if int(memory_state().get("MemAvailable", "0 kB").split()[0]) < 16 * 1024 * 1024:
                raise RuntimeError("MemAvailable below 16 GiB before " + label)
            result = command(argv, label, attempt, deadline, env)
            record["commands"].append(result)
            output = Path(result["stdout_path"]).read_text()
            error = Path(result["stderr_path"]).read_text()
            if result["exit_code"] != 0:
                raise RuntimeError(label + " exit " + str(result["exit_code"]))
            if label == "sage_version" and "SageMath version 10.9" not in output:
                raise RuntimeError("Sage version mismatch")
            if label == "singular_version" and ("version 4.4.1" not in output or "44100" not in output or str(SINGULAR) not in output):
                raise RuntimeError("bundled Singular path/version mismatch")
            if label == "sage_proof":
                lines = [json.loads(x) for x in output.splitlines() if x.startswith("{")]
                certs = [x for x in lines if "certificate" in x]
                if len(certs) != 8 or any(x.get("zero") is not True or x.get("residual") != "0" for x in certs):
                    raise RuntimeError("Sage polynomial certificate count or residual mismatch")
                if not any(x.get("sage_exact_certificates") == 8 and x.get("all_zero") is True for x in lines):
                    raise RuntimeError("Sage completion marker mismatch")
                record["details"]["sage_certificates"] = certs
            if label == "singular_proof":
                markers = ["CERT lagrange=0", "CERT gram=0", "CERT gramdet=0", "CERT detsplit=0", "CERT witness=0", "ALL_SINGULAR_CERTIFICATES_ZERO"]
                if any(output.count(marker) != 1 for marker in markers):
                    raise RuntimeError("Singular certificate marker missing or duplicated")
                if re.search(r"(?im)(^\s*\?|\berror\b|\bundefined\b|\bsyntax\b|\bFAIL\b)", output + "\n" + error):
                    raise RuntimeError("Singular raw diagnostic indicates error")
                record["details"]["singular_markers"] = markers
        record["details"]["universal_bridge"] = {
            "norm": "Euclidean induced supremum, homogeneous to all-vector bound",
            "cauchy": "Lagrange SOS identity yields |p|<=sqrt(nq)<=r n",
            "gram": "exact upper and lower gap decompositions for every real vector",
            "singular_values": "real symmetric spectral theorem on D^T D; each eigenvector inherits squared bounds",
            "positive_branch": "symmetric part positive definite; det witness and skew-square identity derive detD>0",
            "root": "det(D^T D)=detD^2 and product of nonnegative singular values = detD>0",
            "scope": "arbitrary real 2x2 D, s>0, 0<=eta<1, no symmetry restriction",
        }
        record["status"] = "PASS"
        record["checks"]["CAS-07-C02"] = True
    except Exception as exc:
        failures.append(repr(exc))
    finally:
        post = {str(p): SHA(p) for p in SNAPSHOT}
        record["source_input_tool_sha256_after"] = post
        record["memory_after"] = memory_state()
        for p in pre:
            if post[p] != pre[p]:
                failures.append("identity drift: " + p)
        if failures:
            record["status"] = "INCONCLUSIVE"
            record["checks"]["CAS-07-C02"] = False
        record["details"]["first_failures"] = failures
        record["completed_at"] = utcnow()
        (attempt / "result.json").write_text(json.dumps(record, indent=2, sort_keys=True) + "\n")
        (OWN / "result.json").write_text(json.dumps(record, indent=2, sort_keys=True) + "\n")
        print(json.dumps({"axis": record["axis"], "status": record["status"], "contract_sha256": record["contract_sha256"],
                          "checks": record["checks"], "domain_assumption_diff": record["domain_assumption_diff"],
                          "counterexample": record["counterexample"], "attempt_path": str(attempt), "first_failures": failures}, sort_keys=True))
    return 0 if record["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
