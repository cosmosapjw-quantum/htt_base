"""Pinned compile harness: snapshot exact source, record argv/cwd/exit/hashes, keep every attempt (never delete)."""
import hashlib, json, pathlib, subprocess, sys
from datetime import datetime, timezone
T = pathlib.Path(__file__).resolve().parent.parent
RAW, IMP = T / "raw", T / "raw" / "imports"
ORACLE = "/home/cosmosapjw/lean_oracles/viii_oracle"
C01 = T.parent / "c01_bregman_three_point_v2_20261008" / "lean" / "BregmanThreePoint.lean"
WRAP = T / "lean" / "G11AIntegralBregman.lean"
h = lambda b: hashlib.sha256(b).hexdigest()
STEPS = {
  "c01": (C01, f"lean -R {C01.parent} -o {IMP}/BregmanThreePoint.olean {C01}"),
  "wrapper": (WRAP, f"LEAN_PATH={IMP}:$LEAN_PATH lean -R {WRAP.parent} -o {IMP}/G11AIntegralBregman.olean {WRAP}"),
  "audit": (RAW / "AxiomAudit.lean", f"LEAN_PATH={IMP}:$LEAN_PATH lean -R {RAW} {RAW/'AxiomAudit.lean'}"),
}
IMP.mkdir(parents=True, exist_ok=True)
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
    t1 = datetime.now(timezone.utc).isoformat()
    stem.with_suffix(".stdout").write_bytes(out); stem.with_suffix(".stderr").write_bytes(err)
    rec = {"step": name, "argv": argv, "cwd": ORACLE, "started_utc": t0, "finished_utc": t1, "exit_code": rc,
           "source_path": str(src), "source_sha256": h(data), "stdout_sha256": h(out), "stderr_sha256": h(err)}
    stem.with_suffix(".json").write_text(json.dumps(rec, indent=1) + "\n"); print(name, "exit", rc)
    if rc: print(out.decode()[-6000:], err.decode()[-2000:]); sys.exit(rc)
