"""Pinned compile harness (P05-A): snapshot exact source, record argv/cwd/exit/hashes, keep every attempt.

Modelled on GRSTAT CAS-10 g10a_restspace_positivity_v1_20261013/raw/run_compile.py.
Usage: python3 run_compile.py <step> [<step> ...]
  steps: import_gap | main | audit | probe:<name>   (probe sources live in raw/probes/<name>.lean)
Attempts are numbered globally and never deleted.
"""
import hashlib, json, pathlib, subprocess, sys, time
from datetime import datetime, timezone

T = pathlib.Path(__file__).resolve().parent.parent
RAW, IMP, PROBES = T / "raw", T / "raw" / "imports", T / "raw" / "probes"
ORACLE = "/home/cosmosapjw/lean_oracles/viii_oracle"
GAP = T.parent / "eigenframe_gap_bridge_v1_20261011" / "EigenframeGap.lean"
MAIN = T / "lean" / "OrbitCurvatureEigenframe.lean"
AUDIT = RAW / "AxiomAudit.lean"
h = lambda b: hashlib.sha256(b).hexdigest()


def step(name):
    if name == "import_gap":
        return GAP, f"lean -R {GAP.parent} -o {IMP}/EigenframeGap.olean {GAP}"
    if name == "main":
        return MAIN, f"LEAN_PATH={IMP}:$LEAN_PATH lean -R {MAIN.parent} -o {IMP}/OrbitCurvatureEigenframe.olean {MAIN}"
    if name == "audit":
        return AUDIT, f"LEAN_PATH={IMP}:$LEAN_PATH lean -R {RAW} {AUDIT}"
    if name.startswith("probe:"):
        src = PROBES / (name.split(":", 1)[1] + ".lean")
        return src, f"LEAN_PATH={IMP}:$LEAN_PATH lean -R {PROBES} {src}"
    raise SystemExit(f"unknown step {name}")


IMP.mkdir(parents=True, exist_ok=True)
for name in sys.argv[1:]:
    src, cmd = step(name)
    tag = name.replace(":", "-")
    n = len(list(RAW.glob("compile_*.json"))) + 1
    stem = RAW / f"compile_{n:02d}_{tag}"
    data = src.read_bytes()
    (RAW / f"compile_{n:02d}_{tag}.source.lean").write_bytes(data)
    argv = ["lake", "env", "bash", "-c", cmd]
    t0 = datetime.now(timezone.utc).isoformat(); c0 = time.monotonic()
    try:
        r = subprocess.run(argv, cwd=ORACLE, capture_output=True, timeout=900)
        out, err, rc = r.stdout, r.stderr, r.returncode
    except subprocess.TimeoutExpired as e:
        out, err, rc = e.stdout or b"", e.stderr or b"", 124
    dur = time.monotonic() - c0
    (RAW / f"compile_{n:02d}_{tag}.stdout").write_bytes(out)
    (RAW / f"compile_{n:02d}_{tag}.stderr").write_bytes(err)
    rec = {"schema": "htt.raw-command-result.v1", "attempt": n, "step": name, "argv": argv, "cwd": ORACLE,
           "started_utc": t0, "duration_seconds": round(dur, 3), "exit_code": rc, "timeout_seconds": 900,
           "source_path": str(src), "source_sha256": h(data),
           "stdout_sha256": h(out), "stderr_sha256": h(err)}
    (RAW / f"compile_{n:02d}_{tag}.json").write_text(json.dumps(rec, indent=1) + "\n")
    print(name, "attempt", n, "exit", rc, f"{dur:.1f}s")
    if rc:
        print(out.decode(errors="replace")[-6000:], err.decode(errors="replace")[-3000:])
        sys.exit(rc)
    else:
        print(out.decode(errors="replace")[-6000:])
