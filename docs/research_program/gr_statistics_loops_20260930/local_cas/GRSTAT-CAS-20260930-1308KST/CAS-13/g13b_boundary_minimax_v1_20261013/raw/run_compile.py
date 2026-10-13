"""Pinned compile harness for G13-B (modelled on CAS-10/g10a_restspace_positivity_v1_20261013/raw/run_compile.py).

Every attempt snapshots the exact source, records argv/cwd/exit/UTC time/hashes and keeps
stdout/stderr. Attempts are never deleted; numbering continues across invocations.
Usage: python3 run_compile.py <step> [<step> ...]
  steps: imp_c04 | imp_g13a | main | audit | probe:<name>  (probe compiles raw/probes/<name>.lean)
"""
import hashlib, json, pathlib, subprocess, sys
from datetime import datetime, timezone

T = pathlib.Path(__file__).resolve().parent.parent
RAW, IMP = T / "raw", T / "raw" / "imports"
ORACLE = "/home/cosmosapjw/lean_oracles/viii_oracle"
CAS13 = T.parent
C04 = CAS13 / "lean" / "Main.lean"                       # reviewed C04 source, imported unchanged
G13A = CAS13 / "g13a_measure_extremizer_bridge_v1_20261011" / "MeasureExtremizerBridge.lean"  # reviewed G13-A
MAIN = T / "lean" / "G13BBoundaryMinimax.lean"
h = lambda b: hashlib.sha256(b).hexdigest()
LP = f"LEAN_PATH={IMP}:$LEAN_PATH"
STEPS = {
    "imp_c04": (C04, f"lean -R {C04.parent} -o {IMP}/Main.olean {C04}"),
    "imp_g13a": (G13A, f"lean -R {G13A.parent} -o {IMP}/MeasureExtremizerBridge.olean {G13A}"),
    "main": (MAIN, f"{LP} lean -R {MAIN.parent} -o {IMP}/G13BBoundaryMinimax.olean {MAIN}"),
    "audit": (RAW / "AxiomAudit.lean", f"{LP} lean -R {RAW} {RAW / 'AxiomAudit.lean'}"),
}


def step(name):
    if name.startswith("probe:"):
        p = RAW / "probes" / (name.split(":", 1)[1] + ".lean")
        return p, f"{LP} lean -R {p.parent} {p}"
    return STEPS[name]


for name in sys.argv[1:]:
    src, cmd = step(name)
    n = len(list(RAW.glob("compile_*.json"))) + 1
    tag = name.replace(":", "_")
    stem = RAW / f"compile_{n:02d}_{tag}"
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
    (stem.parent / (stem.name + ".stdout")).write_bytes(out)
    (stem.parent / (stem.name + ".stderr")).write_bytes(err)
    rec = {"step": name, "argv": argv, "cwd": ORACLE, "started_utc": t0, "finished_utc": t1,
           "exit_code": rc, "source_path": str(src), "source_sha256": h(data),
           "stdout_sha256": h(out), "stderr_sha256": h(err), "timeout_s": 900}
    (stem.parent / (stem.name + ".json")).write_text(json.dumps(rec, indent=1) + "\n")
    print(name, "attempt", n, "exit", rc)
    if rc:
        print(out.decode(errors="replace")[-6000:], err.decode(errors="replace")[-3000:])
        sys.exit(rc)
