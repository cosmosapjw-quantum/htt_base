"""Pinned compile harness (modelled on CAS-10 g10a): snapshot the exact source,
record argv/cwd/exit/hashes/UTC time, keep every attempt, timeout 900 s."""
import hashlib, json, pathlib, subprocess, sys
from datetime import datetime, timezone
T = pathlib.Path(__file__).resolve().parent.parent
RAW, IMP = T / "raw", T / "raw" / "imports"
ORACLE = "/home/cosmosapjw/lean_oracles/viii_oracle"
RP = pathlib.Path("/home/cosmosapjw/Dropbox/bianchi/htt_base/docs/research_program")
PORT01 = RP / "theory_inference_port_20260930/local_execution/PORT-CAS-01/lorentz_mass_shell_v1_20261008/lean/PortCas01.lean"
CAS17 = RP / "gr_statistics_loops_20260930/local_cas/GRSTAT-CAS-20260930-1308KST/CAS-17/c04_passive_tensor_bridge_v1_20261010/PassiveTensorBridge.lean"
PRIOR = RP / "theory_inference_port_20260930/local_execution/PORT-CAS-06/endpoint_scalar_invariant_v1_20261011/EndpointScalarInvariant.lean"
MAIN = T / "lean" / "P06AOptics.lean"
h = lambda b: hashlib.sha256(b).hexdigest()
def imp(src, mod):
    return (src, f"lean -R {src.parent} -o {IMP}/{mod}.olean {src}")
STEPS = {
  "imp_port01": imp(PORT01, "PortCas01"),
  "imp_cas17": imp(CAS17, "PassiveTensorBridge"),
  "imp_prior": imp(PRIOR, "EndpointScalarInvariant"),
  "main": (MAIN, f"LEAN_PATH={IMP}:$LEAN_PATH lean -R {MAIN.parent} -o {IMP}/P06AOptics.olean {MAIN}"),
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
           "finished_utc": datetime.now(timezone.utc).isoformat(), "exit_code": rc,
           "source_path": str(src), "source_sha256": h(data),
           "stdout_sha256": h(out), "stderr_sha256": h(err)}
    stem.with_suffix(".json").write_text(json.dumps(rec, indent=1) + "\n"); print(name, "exit", rc)
    if rc: print(out.decode()[-6000:], err.decode()[-3000:]); sys.exit(rc)
