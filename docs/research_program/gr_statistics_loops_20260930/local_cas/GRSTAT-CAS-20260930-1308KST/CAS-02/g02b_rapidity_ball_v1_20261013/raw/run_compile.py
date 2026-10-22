"""Pinned compile harness (modelled on CAS-10/g10a_restspace_positivity_v1_20261013/raw/run_compile.py):
snapshot exact source, record argv/cwd/exit/hashes/UTC time, keep every attempt, timeout 900 s."""
import hashlib, json, pathlib, subprocess, sys
from datetime import datetime, timezone
T = pathlib.Path(__file__).resolve().parent.parent
RAW, IMP = T / "raw", T / "raw" / "imports"
ORACLE = "/home/cosmosapjw/lean_oracles/viii_oracle"
CAS02 = T.parent
CAS02_SRC = CAS02 / "c01_c03_input_aligned_v1_20261005" / "lean" / "Cas02.lean"
C04_SRC = CAS02 / "c04_inverse_bound_v1_20261008" / "lean_clean" / "InverseBound.lean"
MAIN = T / "lean" / "G02BRapidityBall.lean"
h = lambda b: hashlib.sha256(b).hexdigest()
STEPS = {
  "cas02": (CAS02_SRC, f"lean -R {CAS02_SRC.parent} -o {IMP}/Cas02.olean {CAS02_SRC}"),
  "c04": (C04_SRC, f"lean -R {C04_SRC.parent} -o {IMP}/InverseBound.olean {C04_SRC}"),
  "main": (MAIN, f"LEAN_PATH={IMP}:$LEAN_PATH lean -R {MAIN.parent} -o {IMP}/G02BRapidityBall.olean {MAIN}"),
  "audit": (RAW / "AxiomAudit.lean", f"LEAN_PATH={IMP}:$LEAN_PATH lean -R {RAW} {RAW/'AxiomAudit.lean'}"),
}
for name in sys.argv[1:]:
    src, cmd = STEPS[name]
    n = len(list(RAW.glob("compile_*.json"))) + 1
    stem = RAW / f"compile_{n:02d}_{name}"
    data = src.read_bytes(); (stem.parent / (stem.name + ".source.lean")).write_bytes(data)
    argv = ["lake", "env", "bash", "-c", cmd]; t0 = datetime.now(timezone.utc).isoformat()
    try:
        r = subprocess.run(argv, cwd=ORACLE, capture_output=True, timeout=900); out, err, rc = r.stdout, r.stderr, r.returncode
    except subprocess.TimeoutExpired as e:
        out, err, rc = e.stdout or b"", e.stderr or b"", 124
    stem.with_suffix(".stdout").write_bytes(out); stem.with_suffix(".stderr").write_bytes(err)
    rec = {"step": name, "argv": argv, "cwd": ORACLE, "started_utc": t0,
           "finished_utc": datetime.now(timezone.utc).isoformat(), "exit_code": rc, "source_path": str(src),
           "source_sha256": h(data), "stdout_sha256": h(out), "stderr_sha256": h(err)}
    stem.with_suffix(".json").write_text(json.dumps(rec, indent=1) + "\n"); print(name, "exit", rc)
    if rc: print(out.decode()[-6000:], err.decode()[-2000:]); sys.exit(rc)
