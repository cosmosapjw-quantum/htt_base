"""Pinned compile harness: snapshot exact source, record argv/cwd/exit/hashes, keep every attempt.

Modelled on CAS-10/g10a_restspace_positivity_v1_20261013/raw/run_compile.py (and the G09-A copy).
Usage: python3 run_compile.py import|main|probe|audit [...]
  import = compile the reviewed G09-A module UNCHANGED from its own path into raw/imports
  main   = compile lean/G09BRankDesign.lean into raw/imports
  probe  = scratch exploration file raw/probes/Probe.lean (retained like every attempt)
  audit  = raw/AxiomAudit.lean
Never deletes attempts.  Prints every 'error:' line of a failing compile.
"""
import hashlib, json, pathlib, subprocess, sys
from datetime import datetime, timezone

T = pathlib.Path(__file__).resolve().parent.parent
RAW, IMP = T / "raw", T / "raw" / "imports"
ORACLE = "/home/cosmosapjw/lean_oracles/viii_oracle"
G09A_DIR = T.parent / "g09a_definition_recovery_v1_20261014" / "lean"
G09A_SRC = G09A_DIR / "G09ADefinitions.lean"
SRC = T / "lean" / "G09BRankDesign.lean"
h = lambda b: hashlib.sha256(b).hexdigest()
STEPS = {
    "import": (G09A_SRC, f"LEAN_PATH={IMP}:$LEAN_PATH lean -R {G09A_DIR} -o {IMP}/G09ADefinitions.olean {G09A_SRC}"),
    "main": (SRC, f"LEAN_PATH={IMP}:$LEAN_PATH lean -R {T/'lean'} -o {IMP}/G09BRankDesign.olean {SRC}"),
    "probe": (RAW / "probes" / "Probe.lean", f"LEAN_PATH={IMP}:$LEAN_PATH lean {RAW/'probes'/'Probe.lean'}"),
    "audit": (RAW / "AxiomAudit.lean", f"LEAN_PATH={IMP}:$LEAN_PATH lean -R {RAW} {RAW/'AxiomAudit.lean'}"),
}
IMP.mkdir(parents=True, exist_ok=True)
for name in sys.argv[1:]:
    src, cmd = STEPS[name]
    n = len(list(RAW.glob("compile_*.json"))) + 1
    stem = RAW / f"compile_{n:02d}_{name}"
    data = src.read_bytes()
    (stem.parent / (stem.name + ".source.lean")).write_bytes(data)
    argv = ["lake", "env", "bash", "-c", cmd]
    t0 = datetime.now(timezone.utc).isoformat()
    try:
        r = subprocess.run(argv, cwd=ORACLE, capture_output=True, timeout=900)
        out, err, rc = r.stdout, r.stderr, r.returncode
    except subprocess.TimeoutExpired as e:
        out, err, rc = e.stdout or b"", e.stderr or b"", 124
    t1 = datetime.now(timezone.utc).isoformat()
    stem.with_suffix(".stdout").write_bytes(out)
    stem.with_suffix(".stderr").write_bytes(err)
    rec = {"step": name, "argv": argv, "cwd": ORACLE, "started_utc": t0, "finished_utc": t1,
           "exit_code": rc, "timeout_seconds": 900, "source_path": str(src),
           "source_sha256": h(data), "stdout_sha256": h(out), "stderr_sha256": h(err)}
    stem.with_suffix(".json").write_text(json.dumps(rec, indent=1) + "\n")
    print(name, "exit", rc, "->", stem.name)
    errs = [l for l in (out + err).decode(errors="replace").splitlines() if "error" in l]
    for l in errs:
        print("  ", l)
    if rc:
        print(out.decode(errors="replace")[-8000:], err.decode(errors="replace")[-2000:])
        sys.exit(rc)
