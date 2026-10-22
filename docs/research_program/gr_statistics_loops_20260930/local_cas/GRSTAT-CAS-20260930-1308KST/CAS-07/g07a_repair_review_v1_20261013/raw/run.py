"""Compile exact sources under the pinned oracle; keep argv, cwd, exit, hashes, stdout/stderr."""
import hashlib, json, pathlib, subprocess, sys
from datetime import datetime, timezone
D = pathlib.Path(__file__).resolve().parent
ORACLE = "/home/cosmosapjw/lean_oracles/viii_oracle"
SRC = D.parent.parent / "c01_input_aligned_v1_20261005" / "lean" / "CAS07C01.lean"
h = lambda p: hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest()
steps = [
  ("build_CAS07C01", f"lean -R {SRC.parent} -o {D}/imports/CAS07C01.olean {SRC}", SRC),
  ("axiom_audit", f"LEAN_PATH={D}/imports:$LEAN_PATH lean -R {D} {D}/AxiomAudit.lean", D / "AxiomAudit.lean"),
]
for name, cmd, src in steps:
    argv = ["lake", "env", "bash", "-c", cmd]
    t0 = datetime.now(timezone.utc).isoformat()
    try:
        r = subprocess.run(argv, cwd=ORACLE, capture_output=True, timeout=900)
        out, err, rc = r.stdout, r.stderr, r.returncode
    except subprocess.TimeoutExpired as e:
        out, err, rc = e.stdout or b"", e.stderr or b"", 124
    (D / f"{name}.stdout").write_bytes(out); (D / f"{name}.stderr").write_bytes(err)
    rec = {"step": name, "argv": argv, "cwd": ORACLE, "started_utc": t0, "exit_code": rc,
           "source_path": str(src), "source_sha256": h(src),
           "stdout_sha256": hashlib.sha256(out).hexdigest(), "stderr_sha256": hashlib.sha256(err).hexdigest()}
    (D / f"{name}.json").write_text(json.dumps(rec, indent=1) + "\n")
    print(name, "exit", rc)
    if rc != 0: sys.exit(rc)
