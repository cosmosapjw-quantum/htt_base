"""Pinned compile harness (P12-A): snapshot exact source per attempt, record argv/cwd/exit/hashes
and produced olean hashes; never delete prior attempts; timeout 900 s."""
import hashlib, json, pathlib, subprocess, sys
from datetime import datetime, timezone
T = pathlib.Path(__file__).resolve().parent.parent
RAW, IMP = T / "raw", T / "raw" / "imports"
ORACLE = "/home/cosmosapjw/lean_oracles/viii_oracle"
h = lambda b: hashlib.sha256(b).hexdigest()
STEPS = {
  "stmt": (RAW / "StatementCheck.lean", f"lean -R {RAW} {RAW/'StatementCheck.lean'}"),
  "main": (T / "lean" / "P12GaussianLaw.lean",
           f"lean -R {T/'lean'} -o {IMP}/P12GaussianLaw.olean {T/'lean'/'P12GaussianLaw.lean'}"),
  "audit": (RAW / "AxiomAudit.lean", f"LEAN_PATH={IMP}:$LEAN_PATH lean -R {RAW} {RAW/'AxiomAudit.lean'}"),
}
def olean_hashes():
    return {str(p): h(p.read_bytes()) for p in sorted(IMP.glob("*.olean"))}
for name in sys.argv[1:]:
    src, cmd = STEPS[name]
    n = len(list(RAW.glob("compile_*.json"))) + 1
    stem = RAW / f"compile_{n:02d}_{name}"
    data = src.read_bytes(); (stem.parent / (stem.name + ".source.lean")).write_bytes(data)
    argv = ["lake", "env", "bash", "-c", cmd]; t0 = datetime.now(timezone.utc).isoformat()
    pre = olean_hashes()
    try:
        r = subprocess.run(argv, cwd=ORACLE, capture_output=True, timeout=900); out, err, rc = r.stdout, r.stderr, r.returncode
    except subprocess.TimeoutExpired as e:
        out, err, rc = e.stdout or b"", e.stderr or b"", 124
    stem.with_suffix(".stdout").write_bytes(out); stem.with_suffix(".stderr").write_bytes(err)
    rec = {"step": name, "argv": argv, "cwd": ORACLE, "started_utc": t0,
           "finished_utc": datetime.now(timezone.utc).isoformat(), "exit_code": rc,
           "source_path": str(src), "source_sha256": h(data), "stdout_sha256": h(out), "stderr_sha256": h(err),
           "olean_sha256_before": pre, "olean_sha256_after": olean_hashes()}
    stem.with_suffix(".json").write_text(json.dumps(rec, indent=1) + "\n"); print(name, "exit", rc)
    if rc: print(out.decode()[-6000:], err.decode()[-2000:]); sys.exit(rc)
