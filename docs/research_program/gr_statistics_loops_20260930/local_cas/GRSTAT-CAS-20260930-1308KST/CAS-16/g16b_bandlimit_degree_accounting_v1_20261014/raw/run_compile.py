"""Pinned compile harness (modelled on CAS-10/g10a raw/run_compile.py): snapshot exact source,
record argv/cwd/exit/hashes/UTC time, keep every attempt (never deleted), timeout 900 s.
Import steps compile the accepted CAS16-C03 sources UNCHANGED (read in place) into raw/imports."""
import hashlib, json, pathlib, subprocess, sys
from datetime import datetime, timezone
T = pathlib.Path(__file__).resolve().parent.parent
RAW, IMP = T / "raw", T / "raw" / "imports"
ORACLE = "/home/cosmosapjw/lean_oracles/viii_oracle"
C03 = T.parent / "c03_cartesian_bridge_v1_20261009" / "lean"
MOD = T / "lean" / "G16BBandlimit.lean"
h = lambda b: hashlib.sha256(b).hexdigest()
def imp(name):
    return (C03 / f"{name}.lean", f"LEAN_PATH={IMP}:$LEAN_PATH lean -R {C03} -o {IMP}/{name}.olean {C03/(name + '.lean')}")
STEPS = {
  "imp_sphere": imp("SphereQuadrature"),
  "imp_modes": imp("AngularModes"),
  "imp_angular": imp("AngularBridge"),
  "imp_radial": imp("RadialBridge"),
  "imp_full": imp("FullBridge"),
  "main": (MOD, f"LEAN_PATH={IMP}:$LEAN_PATH lean -R {T/'lean'} -o {IMP}/G16BBandlimit.olean {MOD}"),
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
    rec = {"step": name, "argv": argv, "cwd": ORACLE, "started_utc": t0,
           "finished_utc": datetime.now(timezone.utc).isoformat(), "exit_code": rc, "source_path": str(src),
           "source_sha256": h(data), "stdout_sha256": h(out), "stderr_sha256": h(err)}
    stem.with_suffix(".json").write_text(json.dumps(rec, indent=1) + "\n"); print(name, "exit", rc)
    if rc: print(out.decode()[-6000:], err.decode()[-2000:]); sys.exit(rc)
