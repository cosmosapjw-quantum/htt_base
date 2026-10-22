"""G17-D pinned compile harness (modelled on CAS-10 g10a run_compile.py).
Every attempt snapshots the exact source, records argv/cwd/exit/hashes/UTC times,
keeps stdout/stderr, never deletes attempts. Timeout 900 s.
Usage: python3 run_compile.py <step> [<step> ...]; probe steps: probe:<path-under-raw/probes>"""
import hashlib, json, pathlib, subprocess, sys
from datetime import datetime, timezone
T = pathlib.Path(__file__).resolve().parent.parent
RAW, IMP, PROBES = T / "raw", T / "raw" / "imports", T / "raw" / "probes"
ORACLE = "/home/cosmosapjw/lean_oracles/viii_oracle"
CAS17 = T.parent
C01 = CAS17 / "c01_gram_tilt_bridge_v1_20261010" / "lean" / "C01.lean"
C04 = CAS17 / "c04_passive_tensor_bridge_v1_20261010" / "PassiveTensorBridge.lean"
MAIN = T / "lean" / "G17DOrbitTilt.lean"
h = lambda b: hashlib.sha256(b).hexdigest()
def lp(cmd): return f"LEAN_PATH={IMP}:$LEAN_PATH {cmd}"
STEPS = {
  "imp_c01": (C01, lp(f"lean -R {C01.parent} -o {IMP}/C01.olean {C01}"), IMP / "C01.olean"),
  "imp_c04": (C04, lp(f"lean -R {C04.parent} -o {IMP}/PassiveTensorBridge.olean {C04}"), IMP / "PassiveTensorBridge.olean"),
  "main": (MAIN, lp(f"lean -R {MAIN.parent} -o {IMP}/G17DOrbitTilt.olean {MAIN}"), IMP / "G17DOrbitTilt.olean"),
  "audit": (RAW / "AxiomAudit.lean", lp(f"lean -R {RAW} {RAW/'AxiomAudit.lean'}"), None),
}
def step(name):
    if name.startswith("probe:"):
        src = PROBES / name.split(":", 1)[1]
        return src, lp(f"lean -R {PROBES} {src}"), None, "probe_" + src.stem
    src, cmd, ol = STEPS[name]
    return src, cmd, ol, name
for arg in sys.argv[1:]:
    src, cmd, olean, label = step(arg)
    n = len(list(RAW.glob("compile_*.json"))) + 1
    stem = RAW / f"compile_{n:02d}_{label}"
    data = src.read_bytes(); (RAW / (stem.name + ".source.lean")).write_bytes(data)
    argv = ["lake", "env", "bash", "-c", cmd]; t0 = datetime.now(timezone.utc).isoformat()
    try:
        r = subprocess.run(argv, cwd=ORACLE, capture_output=True, timeout=900); out, err, rc = r.stdout, r.stderr, r.returncode
    except subprocess.TimeoutExpired as e:
        out, err, rc = e.stdout or b"", e.stderr or b"", 124
    t1 = datetime.now(timezone.utc).isoformat()
    (RAW / (stem.name + ".stdout")).write_bytes(out); (RAW / (stem.name + ".stderr")).write_bytes(err)
    rec = {"step": label, "argv": argv, "cwd": ORACLE, "started_utc": t0, "finished_utc": t1, "exit_code": rc,
           "source_path": str(src), "source_sha256": h(data), "stdout_sha256": h(out), "stderr_sha256": h(err)}
    if olean is not None and rc == 0 and olean.exists():
        rec["olean_path"] = str(olean); rec["olean_sha256"] = h(olean.read_bytes())
    (RAW / (stem.name + ".json")).write_text(json.dumps(rec, indent=1) + "\n")
    print(label, "exit", rc)
    txt = out.decode(errors="replace") + err.decode(errors="replace")
    for line in txt.splitlines():
        if "error:" in line: print("ERRLINE", line)
    if rc: print(txt[-4000:]); sys.exit(rc)
