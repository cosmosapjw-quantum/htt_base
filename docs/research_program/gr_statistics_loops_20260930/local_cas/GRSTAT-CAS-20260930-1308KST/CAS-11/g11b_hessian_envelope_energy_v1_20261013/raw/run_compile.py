"""Pinned compile harness (G11-B): snapshot exact source per attempt, record argv/cwd/exit/hashes and the
hashes of every imported G11-A olean; keep every attempt (never delete); timeout 900 s."""
import hashlib, json, pathlib, subprocess, sys
from datetime import datetime, timezone
T = pathlib.Path(__file__).resolve().parent.parent
RAW, IMP = T / "raw", T / "raw" / "imports"
G11A_IMP = T.parent / "g11a_integral_bregman_v1_20261013" / "raw" / "imports"
ORACLE = "/home/cosmosapjw/lean_oracles/viii_oracle"
MAIN = T / "lean" / "G11BHessianEnvelope.lean"
h = lambda b: hashlib.sha256(b).hexdigest()
LP = f"LEAN_PATH={IMP}:{G11A_IMP}:$LEAN_PATH"
STEPS = {
  "main": (MAIN, f"{LP} lean -R {MAIN.parent} -o {IMP}/G11BHessianEnvelope.olean {MAIN}"),
  "audit": (RAW / "AxiomAudit.lean", f"{LP} lean -R {RAW} {RAW/'AxiomAudit.lean'}"),
}
IMP.mkdir(parents=True, exist_ok=True)
for name in sys.argv[1:]:
    src, cmd = STEPS[name]
    n = len(list(RAW.glob("compile_*.json"))) + 1
    stem = RAW / f"compile_{n:02d}_{name}"
    data = src.read_bytes(); (RAW / (stem.name + ".source.lean")).write_bytes(data)
    imports = {p.name: h(p.read_bytes()) for p in sorted(G11A_IMP.glob("*.olean"))}
    imports.update({"(own) " + p.name: h(p.read_bytes()) for p in sorted(IMP.glob("*.olean"))})
    argv = ["lake", "env", "bash", "-c", cmd]; t0 = datetime.now(timezone.utc).isoformat()
    try:
        r = subprocess.run(argv, cwd=ORACLE, capture_output=True, timeout=900); out, err, rc = r.stdout, r.stderr, r.returncode
    except subprocess.TimeoutExpired as e:
        out, err, rc = e.stdout or b"", e.stderr or b"", 124
    t1 = datetime.now(timezone.utc).isoformat()
    stem.with_suffix(".stdout").write_bytes(out); stem.with_suffix(".stderr").write_bytes(err)
    rec = {"step": name, "argv": argv, "cwd": ORACLE, "started_utc": t0, "finished_utc": t1, "exit_code": rc,
           "source_path": str(src), "source_sha256": h(data), "stdout_sha256": h(out), "stderr_sha256": h(err),
           "imported_olean_sha256_before_run": imports}
    stem.with_suffix(".json").write_text(json.dumps(rec, indent=1) + "\n"); print(name, "exit", rc)
    if rc: print(out.decode()[-8000:], err.decode()[-2000:]); sys.exit(rc)
