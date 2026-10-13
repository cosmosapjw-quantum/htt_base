"""L2-W1-A compile harness: snapshot exact source per attempt; keep argv, cwd, exit, hashes, UTC, stdout/stderr.
Usage: python3 run_compile.py {build|audit}. Attempts are numbered compile_NN and never deleted."""
import hashlib, json, pathlib, shutil, subprocess, sys
from datetime import datetime, timezone
D = pathlib.Path(__file__).resolve().parent
T = D.parent
ORACLE = "/home/cosmosapjw/lean_oracles/viii_oracle"
LEAN_DIR = T / "lean"
SRC = LEAN_DIR / "L2W1KernelBound.lean"
AUDIT = D / "AxiomAudit.lean"
IMP = D / "imports"
sha = lambda b: hashlib.sha256(b).hexdigest()

def next_n():
    ns = [int(p.name[8:10]) for p in D.glob("compile_[0-9][0-9].json")]
    return max(ns, default=0) + 1

def run(kind):
    IMP.mkdir(exist_ok=True)
    if kind == "build":
        src = SRC
        cmd = f"lean -R {LEAN_DIR} -o {IMP}/L2W1KernelBound.olean {SRC}"
    elif kind == "audit":
        src = AUDIT
        cmd = f"LEAN_PATH={IMP}:$LEAN_PATH lean -R {D} {AUDIT}"
    else:
        sys.exit(f"unknown step {kind}")
    n = next_n(); tag = f"compile_{n:02d}"
    data = src.read_bytes()
    (D / f"{tag}.source.lean").write_bytes(data)
    argv = ["lake", "env", "bash", "-c", cmd]
    t0 = datetime.now(timezone.utc).isoformat()
    try:
        r = subprocess.run(argv, cwd=ORACLE, capture_output=True, timeout=900)
        out, err, rc = r.stdout, r.stderr, r.returncode
    except subprocess.TimeoutExpired as e:
        out, err, rc = e.stdout or b"", e.stderr or b"", 124
    t1 = datetime.now(timezone.utc).isoformat()
    (D / f"{tag}.stdout").write_bytes(out); (D / f"{tag}.stderr").write_bytes(err)
    rec = {"attempt": tag, "step": kind, "argv": argv, "cwd": ORACLE, "timeout_s": 900,
           "started_utc": t0, "finished_utc": t1, "exit_code": rc,
           "source_path": str(src), "source_snapshot": f"{tag}.source.lean", "source_sha256": sha(data),
           "stdout_sha256": sha(out), "stderr_sha256": sha(err)}
    if kind == "build" and rc == 0:
        ol = IMP / "L2W1KernelBound.olean"
        rec["olean_sha256"] = sha(ol.read_bytes()) if ol.exists() else None
    (D / f"{tag}.json").write_text(json.dumps(rec, indent=1) + "\n")
    print(tag, kind, "exit", rc)
    sys.stdout.write(out.decode(errors="replace")); sys.stdout.write(err.decode(errors="replace"))
    return rc

if __name__ == "__main__":
    sys.exit(run(sys.argv[1] if len(sys.argv) > 1 else "build"))
