"""Pinned compile harness (G06-B): snapshot exact source, record argv/cwd/exit/hashes, keep every attempt.

Modelled on CAS-10/g10a_restspace_positivity_v1_20261013/raw/run_compile.py and the
G06-A harness.  The accepted CAS-06 adopted-successor sources (PR #477) and the reviewed
G06-A module are compiled read-only from their own directories into T/raw/imports
(never edited); the G06-B module imports them.  Attempts are never deleted.
"""
import hashlib, json, pathlib, subprocess, sys
from datetime import datetime, timezone
T = pathlib.Path(__file__).resolve().parent.parent
RAW, IMP = T / "raw", T / "raw" / "imports"
ORACLE = "/home/cosmosapjw/lean_oracles/viii_oracle"
ADOPTED = T.parent / "codex_only_continuation_20261004" / "adopted_successor_v1" / "lean"
G06A = T.parent / "g06a_tov_local_ode_v1_20261013" / "lean"
h = lambda b: hashlib.sha256(b).hexdigest()

def dep(d, mod):
    src = d / f"{mod}.lean"
    return (src, f"LEAN_PATH={IMP}:$LEAN_PATH lean -R {d} -o {IMP}/{mod}.olean {src}")

STEPS = {
  "scalar": dep(ADOPTED, "CAS06ScalarAccepted"),
  "foundation": dep(ADOPTED, "CAS06Foundation"),
  "action": dep(ADOPTED, "C03Action"),
  "bundles": dep(ADOPTED, "CAS06Bundles"),
  "g06a": dep(G06A, "G06ATOV"),
  "main": (T / "lean" / "G06BPXAction.lean",
           f"LEAN_PATH={IMP}:$LEAN_PATH lean -R {T/'lean'} -o {IMP}/G06BPXAction.olean {T/'lean'/'G06BPXAction.lean'}"),
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
