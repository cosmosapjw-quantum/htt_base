"""P07-A compile harness. Usage: python3 run_compile.py {build|audit}.
Each attempt gets the next free index NN; exact source snapshot at
compile_NN.source.lean; compile_NN.{json,stdout,stderr}. Never deletes."""
import hashlib, json, pathlib, shutil, subprocess, sys
from datetime import datetime, timezone
D = pathlib.Path(__file__).resolve().parent
T = D.parent
ORACLE = "/home/cosmosapjw/lean_oracles/viii_oracle"
SRC = T / "lean" / "P07MeasureExceedance.lean"
AUD = D / "AxiomAudit.lean"
IMP = D / "imports"
sha = lambda b: hashlib.sha256(b).hexdigest()
mode = sys.argv[1] if len(sys.argv) > 1 else "build"
n = 1
while (D / f"compile_{n:02d}.json").exists():
    n += 1
NN = f"compile_{n:02d}"
IMP.mkdir(exist_ok=True)
if mode == "build":
    src = SRC
    cmd = f"lean -R {SRC.parent} -o {IMP}/P07MeasureExceedance.olean {SRC}"
else:
    src = AUD
    cmd = f"LEAN_PATH={IMP}:$LEAN_PATH lean -R {D} {AUD}"
snap = D / f"{NN}.source.lean"
shutil.copyfile(src, snap)
argv = ["lake", "env", "bash", "-c", cmd]
t0 = datetime.now(timezone.utc).isoformat()
try:
    r = subprocess.run(argv, cwd=ORACLE, capture_output=True, timeout=900)
    out, err, rc = r.stdout, r.stderr, r.returncode
except subprocess.TimeoutExpired as e:
    out, err, rc = e.stdout or b"", e.stderr or b"", 124
t1 = datetime.now(timezone.utc).isoformat()
(D / f"{NN}.stdout").write_bytes(out); (D / f"{NN}.stderr").write_bytes(err)
rec = {"attempt": NN, "mode": mode, "argv": argv, "cwd": ORACLE,
       "started_utc": t0, "finished_utc": t1, "exit_code": rc, "timeout_s": 900,
       "source_path": str(src), "source_snapshot": str(snap),
       "source_sha256": sha(snap.read_bytes()),
       "stdout_sha256": sha(out), "stderr_sha256": sha(err)}
if mode == "build":
    ol = IMP / "P07MeasureExceedance.olean"
    rec["olean_sha256"] = sha(ol.read_bytes()) if ol.exists() and rc == 0 else None
(D / f"{NN}.json").write_text(json.dumps(rec, indent=1) + "\n")
print(NN, mode, "exit", rc)
sys.stdout.write(out.decode(errors="replace")); sys.stdout.write(err.decode(errors="replace"))
sys.exit(rc)
