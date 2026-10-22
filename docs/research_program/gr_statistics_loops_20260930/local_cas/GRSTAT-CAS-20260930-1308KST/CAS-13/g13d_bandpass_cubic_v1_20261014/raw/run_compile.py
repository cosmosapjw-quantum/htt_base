"""Pinned compile harness for G13-D (modelled on CAS-10/g10a_restspace_positivity_v1_20261013/raw/run_compile.py
and CAS-13/g13c_general_p_extremizer_v1_20261014/raw/run_compile.py).

Every attempt snapshots the exact source, records argv/cwd/exit/UTC time/hashes and keeps
stdout/stderr. Attempts are never deleted; numbering continues across invocations.
Every 'error:' line of a failing attempt is printed.
Usage: python3 run_compile.py <step> [<step> ...]
  steps: imp_g13a | imp_powerjet | main | audit | probe:<name>  (probe compiles raw/probes/<name>.lean)
"""
import hashlib, json, pathlib, subprocess, sys
from datetime import datetime, timezone

T = pathlib.Path(__file__).resolve().parent.parent
RAW, IMP = T / "raw", T / "raw" / "imports"
ORACLE = "/home/cosmosapjw/lean_oracles/viii_oracle"
CAS13 = T.parent
# reviewed G13-A source, imported unchanged
G13A = CAS13 / "g13a_measure_extremizer_bridge_v1_20261011" / "MeasureExtremizerBridge.lean"
# PR #501 (commit 00384ac1) CAS-13-C01 power-response jet source, imported unchanged
PJ = CAS13 / "c01_power_jet_v1_20261008" / "lean" / "PowerJet.lean"
MAIN = T / "lean" / "G13DBandpassCubic.lean"
h = lambda b: hashlib.sha256(b).hexdigest()
LP = f"LEAN_PATH={IMP}:$LEAN_PATH"
STEPS = {
    "imp_g13a": (G13A, f"lean -R {G13A.parent} -o {IMP}/MeasureExtremizerBridge.olean {G13A}"),
    "imp_powerjet": (PJ, f"lean -R {PJ.parent} -o {IMP}/PowerJet.olean {PJ}"),
    "main": (MAIN, f"{LP} lean -R {MAIN.parent} -o {IMP}/G13DBandpassCubic.olean {MAIN}"),
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
    txt = out.decode(errors="replace") + err.decode(errors="replace")
    errs = [l for l in txt.splitlines() if "error:" in l]
    for l in errs:
        print("  ", l)
    if rc:
        print(txt[-8000:])
        sys.exit(rc)
