"""Pinned compile harness (modelled on CAS-10/g10a_restspace_positivity_v1_20261013/raw/run_compile.py
and the G12-E harness): snapshot exact source, record argv/cwd/exit/hashes, keep every attempt,
timeout 900 s.  Usage: python3 run_compile.py <step> [<step> ...]; step = module name | audit | probe:<file>."""
import hashlib, json, pathlib, subprocess, sys
from datetime import datetime, timezone
T = pathlib.Path(__file__).resolve().parent.parent
RAW, IMP = T / "raw", T / "raw" / "imports"
ORACLE = "/home/cosmosapjw/lean_oracles/viii_oracle"
CAS = T.parent.parent  # GRSTAT-CAS-20260930-1308KST
SRC = {
  "BregmanThreePoint": CAS / "CAS-11/c01_bregman_three_point_v2_20261008/lean/BregmanThreePoint.lean",
  "G11AIntegralBregman": CAS / "CAS-11/g11a_integral_bregman_v1_20261013/lean/G11AIntegralBregman.lean",
  "G11AGuarded": CAS / "CAS-11/g11a_integral_bregman_v1_20261013/lean/G11AGuarded.lean",
  "PlanckIR": CAS / "CAS-12/g12d_reexecution_closeout_v1_20261014/lean/PlanckIR.lean",
  "G12DInterface": CAS / "CAS-12/g12d_reexecution_closeout_v1_20261014/lean/G12DInterface.lean",
  "G12DUVIntegrabilityEnvelope": CAS / "CAS-12/g12d_reexecution_closeout_v1_20261014/lean/G12DUVIntegrabilityEnvelope.lean",
  "G12DCardClosure": CAS / "CAS-12/g12d_reexecution_closeout_v1_20261014/lean/G12DCardClosure.lean",
  "OscillatoryDerivative": CAS / "CAS-12/c04_oscillatory_derivative_bridge_v1_20261011/OscillatoryDerivative.lean",
  "G12EMomentNull": CAS / "CAS-12/g12e_moment_null_counterexample_v1_20261014/lean/G12EMomentNull.lean",
  "G12ECounterexample": CAS / "CAS-12/g12e_moment_null_counterexample_v1_20261014/lean/G12ECounterexample.lean",
  "G12FFisherBudget": T / "lean" / "G12FFisherBudget.lean",
  "G12FInstances": T / "lean" / "G12FInstances.lean",
}
h = lambda b: hashlib.sha256(b).hexdigest()
def step(name):
    if name == "audit":
        src = RAW / "AxiomAudit.lean"
        return src, f"LEAN_PATH={IMP}:$LEAN_PATH lean -R {RAW} {src}", None
    if name.startswith("probe:"):
        src = RAW / "probes" / name.split(":", 1)[1]
        return src, f"LEAN_PATH={IMP}:$LEAN_PATH lean -R {src.parent} {src}", None
    src = SRC[name]; ol = IMP / f"{name}.olean"
    return src, f"LEAN_PATH={IMP}:$LEAN_PATH lean -R {src.parent} -o {ol} {src}", ol
for name in sys.argv[1:]:
    src, cmd, ol = step(name)
    n = len(list(RAW.glob("compile_*.json"))) + 1
    tag = name.replace(":", "_").replace(".lean", "")
    stem = RAW / f"compile_{n:02d}_{tag}"
    data = src.read_bytes(); (RAW / (stem.name + ".source.lean")).write_bytes(data)
    argv = ["lake", "env", "bash", "-c", cmd]; t0 = datetime.now(timezone.utc).isoformat()
    try:
        r = subprocess.run(argv, cwd=ORACLE, capture_output=True, timeout=900); out, err, rc = r.stdout, r.stderr, r.returncode
    except subprocess.TimeoutExpired as e:
        out, err, rc = e.stdout or b"", e.stderr or b"", 124
    t1 = datetime.now(timezone.utc).isoformat()
    (RAW / (stem.name + ".stdout")).write_bytes(out); (RAW / (stem.name + ".stderr")).write_bytes(err)
    rec = {"attempt": n, "step": name, "argv": argv, "cwd": ORACLE, "started_utc": t0, "finished_utc": t1,
           "exit_code": rc, "source_path": str(src), "source_sha256": h(data),
           "source_snapshot": stem.name + ".source.lean",
           "stdout_sha256": h(out), "stderr_sha256": h(err),
           "olean_path": str(ol) if ol else None,
           "olean_sha256": h(ol.read_bytes()) if (ol and rc == 0 and ol.exists()) else None}
    (RAW / (stem.name + ".json")).write_text(json.dumps(rec, indent=1) + "\n"); print(name, "exit", rc)
    if rc: print(out.decode()[-8000:], err.decode()[-2000:]); sys.exit(rc)
