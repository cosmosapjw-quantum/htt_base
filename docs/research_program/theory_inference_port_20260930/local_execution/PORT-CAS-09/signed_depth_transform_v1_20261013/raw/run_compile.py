"""P09-A compile harness: snapshot exact source, run one frozen Lean argv, keep every attempt.

Usage: python3 run_compile.py <step> [<step> ...]   steps: main | audit
Each invocation gets the next global index NN (never overwriting earlier attempts) and writes
compile_NN_<step>.source.lean (pre-execution snapshot), .stdout, .stderr, .json receipts.
Modelled on gr_statistics_loops_20260930/local_cas/GRSTAT-CAS-20260930-1308KST/CAS-10/
g10a_restspace_positivity_v1_20261013/raw/run_compile.py. Timeout 900 s. Nothing is deleted.
"""
import hashlib, json, pathlib, re, shutil, subprocess, sys
from datetime import datetime, timezone

T = pathlib.Path(__file__).resolve().parent.parent
RAW, IMP = T / "raw", T / "raw" / "imports"
IMP.mkdir(exist_ok=True)
ORACLE = "/home/cosmosapjw/lean_oracles/viii_oracle"
TIMEOUT_S = 900
LP = f"LEAN_PATH={IMP}:$LEAN_PATH"
MAIN = T / "lean" / "P09SignedDepth.lean"
AUDIT = RAW / "AxiomAudit.lean"
STEPS = {
    "main": (MAIN, f"{LP} lean -R {T/'lean'} -o {IMP/'P09SignedDepth.olean'} {MAIN}",
             IMP / "P09SignedDepth.olean"),
    "audit": (AUDIT, f"{LP} lean -R {RAW} {AUDIT}", None),
}
h = lambda b: hashlib.sha256(b).hexdigest()


def import_hashes():
    return {str(p): h(p.read_bytes()) for p in sorted(IMP.glob("*.olean"))}


def next_index():
    used = [int(m.group(1)) for p in RAW.glob("compile_*.json")
            if (m := re.fullmatch(r"compile_(\d+)_\w+\.json", p.name))]
    return max(used, default=0) + 1


for name in sys.argv[1:]:
    src, cmd, olean = STEPS[name]
    n = next_index()
    stem = f"compile_{n:02d}_{name}"
    data = src.read_bytes()
    (RAW / f"{stem}.source.lean").write_bytes(data)
    argv = ["lake", "env", "bash", "-c", cmd]
    before = import_hashes()
    t0 = datetime.now(timezone.utc).isoformat()
    try:
        r = subprocess.run(argv, cwd=ORACLE, capture_output=True, timeout=TIMEOUT_S)
        out, err, rc, to = r.stdout, r.stderr, r.returncode, False
    except subprocess.TimeoutExpired as e:
        out, err, rc, to = e.stdout or b"", e.stderr or b"", 124, True
    t1 = datetime.now(timezone.utc).isoformat()
    (RAW / f"{stem}.stdout").write_bytes(out)
    (RAW / f"{stem}.stderr").write_bytes(err)
    rec = {"index": n, "step": name, "argv": argv, "lake_resolved": shutil.which("lake"), "cwd": ORACLE,
           "started_utc": t0, "finished_utc": t1, "timeout_seconds": TIMEOUT_S, "timed_out": to,
           "exit_code": rc, "source_path": str(src), "source_snapshot": f"{stem}.source.lean",
           "source_sha256": h(data), "stdout_sha256": h(out), "stderr_sha256": h(err),
           "olean_out": str(olean) if olean else None,
           "olean_sha256_after": h(olean.read_bytes()) if olean and rc == 0 and olean.exists() else None,
           "import_sha256_before": before, "import_sha256_after": import_hashes()}
    (RAW / f"{stem}.json").write_text(json.dumps(rec, indent=1) + "\n")
    print(f"{stem}: exit={rc} source_sha256={rec['source_sha256']}", flush=True)
    if rc or out:
        print(out.decode(errors="replace")[-12000:], err.decode(errors="replace")[-3000:])
    if rc:
        sys.exit(rc)
