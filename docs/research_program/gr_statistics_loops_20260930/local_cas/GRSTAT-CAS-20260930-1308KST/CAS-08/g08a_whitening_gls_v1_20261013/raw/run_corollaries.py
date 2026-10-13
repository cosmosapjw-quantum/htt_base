"""Lead harness for the post-review corollary file; same receipt fields as run_compile.py."""
import hashlib, json, pathlib, subprocess, sys
from datetime import datetime, timezone
T = pathlib.Path(__file__).resolve().parent.parent; RAW = T / "raw"; IMP = RAW / "imports"
ORACLE = "/home/cosmosapjw/lean_oracles/viii_oracle"; h = lambda b: hashlib.sha256(b).hexdigest()
STEPS = {"cor": (T/"lean"/"G08ACorollaries.lean", f"LEAN_PATH={IMP}:$LEAN_PATH lean -R {T/'lean'} -o {IMP}/G08ACorollaries.olean {T/'lean'/'G08ACorollaries.lean'}"),
         "audit": (RAW/"CorollaryAudit.lean", f"LEAN_PATH={IMP}:$LEAN_PATH lean -R {RAW} {RAW/'CorollaryAudit.lean'}")}
for name in sys.argv[1:]:
    src, cmd = STEPS[name]; n = len(list(RAW.glob("corollary_*.json"))) + 1; stem = RAW / f"corollary_{n:02d}_{name}"
    data = src.read_bytes(); (RAW / f"{stem.name}.source.lean").write_bytes(data)
    argv = ["lake", "env", "bash", "-c", cmd]; t0 = datetime.now(timezone.utc).isoformat()
    r = subprocess.run(argv, cwd=ORACLE, capture_output=True, timeout=900)
    stem.with_suffix(".stdout").write_bytes(r.stdout); stem.with_suffix(".stderr").write_bytes(r.stderr)
    stem.with_suffix(".json").write_text(json.dumps({"step": name, "argv": argv, "cwd": ORACLE, "started_utc": t0, "exit_code": r.returncode,
        "source_path": str(src), "source_sha256": h(data), "stdout_sha256": h(r.stdout), "stderr_sha256": h(r.stderr)}, indent=1) + "\n")
    print(name, "exit", r.returncode)
    if r.returncode: print(r.stdout.decode()[-2500:], r.stderr.decode()[-1500:]); sys.exit(1)
