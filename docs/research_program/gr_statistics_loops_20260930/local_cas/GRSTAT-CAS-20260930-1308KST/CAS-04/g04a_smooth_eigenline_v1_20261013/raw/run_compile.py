"""Pinned compile harness (modelled on CAS-10 g10a run_compile.py): snapshot exact source per attempt,
record argv/cwd/exit/hashes, never delete, timeout 900 s."""
import hashlib, json, pathlib, subprocess, sys
from datetime import datetime, timezone
T = pathlib.Path(__file__).resolve().parent.parent
RAW, IMP = T / "raw", T / "raw" / "imports"
ORACLE = "/home/cosmosapjw/lean_oracles/viii_oracle"
PROOF = T.parent / "completion_20261003" / "lean" / "Proof.lean"  # accepted scoped CAS-04 Lean, imported unchanged
MAINF = T / "lean" / "G04AEigenline.lean"
h = lambda b: hashlib.sha256(b).hexdigest()
STEPS = {
  "proof": (PROOF, f"lean -R {PROOF.parent} -o {IMP}/Proof.olean {PROOF}"),
  "main": (MAINF, f"LEAN_PATH={IMP}:$LEAN_PATH lean -R {T/'lean'} -o {IMP}/G04AEigenline.olean {MAINF}"),
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
    rec = {"step": name, "argv": argv, "cwd": ORACLE, "started_utc": t0, "exit_code": rc, "source_path": str(src),
           "source_sha256": h(data), "stdout_sha256": h(out), "stderr_sha256": h(err)}
    if name in ("proof", "main"):
        ol = IMP / ("Proof.olean" if name == "proof" else "G04AEigenline.olean")
        rec["olean_sha256"] = h(ol.read_bytes()) if (rc == 0 and ol.exists()) else None
    stem.with_suffix(".json").write_text(json.dumps(rec, indent=1) + "\n"); print(name, "exit", rc)
    if rc: print(out.decode()[-6000:], err.decode()[-2000:]); sys.exit(rc)
