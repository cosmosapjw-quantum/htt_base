"""Execute the SymPy axis anew and preserve one immutable raw record per run."""

import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
from datetime import datetime, timezone


REPO = Path("/home/cosmosapjw/Dropbox/bianchi/htt_base")
HERE = Path(__file__).resolve().parent
CONTRACT = REPO / "docs/research_program/gr_statistics_loops_20260930/local_cas/GRSTAT-CAS-20260930-1308KST/CAS-05/neutral_admission_20261003/EXECUTION_CONTRACT_V3.json"
NEUTRAL = CONTRACT.with_name("NEUTRAL_INPUT.json")
COMMON = REPO / "docs/research_program/gr_statistics_loops_20260930/cas/COMMON_SPEC.md"
EXPECTED = {CONTRACT: "a67bf54921c80d35865d28dfce86d0ff9670270a807d5f2f45f25e3e7029537f",
            NEUTRAL: "0868c1f15226e71926dad034319b85c73a9ca9c7d3c72064e06ff65d0112b27b",
            COMMON: "4714827e52acf3cb149f4014ac50ab2aa995dd4a0526f6b26ac7257807fe1897"}


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def now():
    return datetime.now(timezone.utc).isoformat()


def main():
    hashes = {str(p): sha(p) for p in (*EXPECTED, HERE / "axis.py", HERE / "run.py")}
    for path, digest in EXPECTED.items():
        if hashes[str(path)] != digest:
            raise RuntimeError(f"frozen input hash changed: {path}")
    existing = sorted(HERE.glob("raw-[0-9][0-9][0-9].json"))
    number = 1 + max((int(p.stem[-3:]) for p in existing), default=0)
    raw_path = HERE / f"raw-{number:03d}.json"
    argv = [sys.executable, "-B", str(HERE / "axis.py")]
    started_at = now()
    try:
        completed = subprocess.run(argv, cwd=REPO, capture_output=True, text=True,
                                   timeout=1800, check=False)
        exit_code, stdout, stderr = completed.returncode, completed.stdout, completed.stderr
        timeout = False
    except subprocess.TimeoutExpired as exc:
        exit_code = None
        stdout = exc.stdout.decode() if isinstance(exc.stdout, bytes) else (exc.stdout or "")
        stderr = exc.stderr.decode() if isinstance(exc.stderr, bytes) else (exc.stderr or "")
        timeout = True
    completed_at = now()
    version = subprocess.run([sys.executable, "-B", "-c", "import sys,sympy;print(sys.version);print(sympy.__version__);print(sympy.__file__)"],
                             cwd=REPO, capture_output=True, text=True, check=False)
    raw = {"started_at": started_at, "completed_at": completed_at,
           "argv": argv, "cwd": str(REPO), "exit_code": exit_code,
           "timed_out": timeout, "stdout": stdout, "stderr": stderr,
           "version_argv": [sys.executable, "-B", "-c", "import sys,sympy;print(sys.version);print(sympy.__version__);print(sympy.__file__)"],
           "version_exit": version.returncode, "version_stdout": version.stdout,
           "version_stderr": version.stderr, "source_input_hashes": hashes}
    with raw_path.open("x") as stream:
        json.dump(raw, stream, indent=2, sort_keys=True)
        stream.write("\n")
    try:
        payload = json.loads(stdout)
    except json.JSONDecodeError:
        payload = {"checks": {key: False for key in
                             ("CAS-05-C01", "CAS-05-C02", "CAS-05-C03")},
                   "domain_assumption_diff": [], "counterexample": None,
                   "execution_error": "axis stdout was not one JSON object"}
    checks = payload.get("checks", {})
    status = "PASS" if (exit_code == 0 and not timeout and
                        set(checks) == {"CAS-05-C01", "CAS-05-C02", "CAS-05-C03"}
                        and all(type(v) is bool and v for v in checks.values())
                        and payload.get("domain_assumption_diff") == []
                        and payload.get("counterexample") is None) else "FAIL"
    envelope = {"axis": "sympy", "status": status,
                "contract_sha256": hashes[str(CONTRACT)],
                "commands": [{"argv": argv, "cmd": " ".join(argv),
                              "cwd": str(REPO), "exit": exit_code,
                              "raw": str(raw_path)},
                             {"argv": raw["version_argv"],
                              "cmd": " ".join(raw["version_argv"]),
                              "cwd": str(REPO), "exit": version.returncode}],
                "completed_at": completed_at, "evidence_class": "exact",
                "checks": checks, "domain_assumption_diff": payload.get("domain_assumption_diff"),
                "counterexample": payload.get("counterexample"),
                "evidence": payload.get("evidence"),
                "source_input_hashes": hashes,
                "raw": str(raw_path), "sympy_version": payload.get("sympy_version"),
                "runtime_identity": {"native_profile": "cuhg_gpt6_sol_worker",
                                     "model": "gpt-6-sol", "effort": "high",
                                     "child_id": "01a101c3-966c-7cf1-b082-4d4883218b0c"},
                "claim_scope": "finite CAS-05 C01-C03 components only; no full theorem or scientific admission"}
    (HERE / "result.json").write_text(json.dumps(envelope, indent=2, sort_keys=True) + "\n")
    print(json.dumps(payload, sort_keys=True))
    return 0 if status == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
