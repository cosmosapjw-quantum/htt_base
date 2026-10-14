"""Pinned compile harness (modelled on CAS-10 g10a .../raw/run_compile.py):
snapshot the exact source, record argv/cwd/exit/hashes/UTC time, keep every attempt
(including probes and failures), timeout 900 s.
Usage: python3 run_compile.py STEP [STEP ...]   with STEP in imp_port01 imp_cas17 imp_prior
imp_optics main audit, or probe:<name> (compiles raw/probes/<name>.lean, no olean)."""
import hashlib, json, pathlib, subprocess, sys
from datetime import datetime, timezone
T = pathlib.Path(__file__).resolve().parent.parent
RAW, IMP = T / "raw", T / "raw" / "imports"
ORACLE = "/home/cosmosapjw/lean_oracles/viii_oracle"
RP = pathlib.Path("/home/cosmosapjw/Dropbox/bianchi/htt_base/docs/research_program")
PORT01 = RP / "theory_inference_port_20260930/local_execution/PORT-CAS-01/lorentz_mass_shell_v1_20261008/lean/PortCas01.lean"
CAS17 = RP / "gr_statistics_loops_20260930/local_cas/GRSTAT-CAS-20260930-1308KST/CAS-17/c04_passive_tensor_bridge_v1_20261010/PassiveTensorBridge.lean"
PRIOR = RP / "theory_inference_port_20260930/local_execution/PORT-CAS-06/endpoint_scalar_invariant_v1_20261011/EndpointScalarInvariant.lean"
OPTICS = RP / "theory_inference_port_20260930/local_execution/PORT-CAS-06/endpoint_optical_invariants_v1_20261014/lean/P06AOptics.lean"
MAIN = T / "lean" / "P06ASphere.lean"
h = lambda b: hashlib.sha256(b).hexdigest()
def dep(src, mod):
    return (src, f"LEAN_PATH={IMP}:$LEAN_PATH lean -R {src.parent} -o {IMP}/{mod}.olean {src}", IMP / f"{mod}.olean")
STEPS = {
  "imp_port01": dep(PORT01, "PortCas01"),
  "imp_cas17": dep(CAS17, "PassiveTensorBridge"),
  "imp_prior": dep(PRIOR, "EndpointScalarInvariant"),
  "imp_optics": dep(OPTICS, "P06AOptics"),
  "main": dep(MAIN, "P06ASphere"),
  "audit": (RAW / "AxiomAudit.lean", f"LEAN_PATH={IMP}:$LEAN_PATH lean -R {RAW} {RAW/'AxiomAudit.lean'}", None),
}
for name in sys.argv[1:]:
    if name.startswith("probe:"):
        p = RAW / "probes" / (name.split(":", 1)[1] + ".lean")
        src, cmd, olean = p, f"LEAN_PATH={IMP}:$LEAN_PATH lean -R {p.parent} {p}", None
        tag = "probe_" + name.split(":", 1)[1]
    else:
        (src, cmd, olean), tag = STEPS[name], name
    n = len(list(RAW.glob("compile_*.json"))) + 1
    stem = RAW / f"compile_{n:02d}_{tag}"
    data = src.read_bytes(); (stem.parent / (stem.name + ".source.lean")).write_bytes(data)
    argv = ["lake", "env", "bash", "-c", cmd]; t0 = datetime.now(timezone.utc).isoformat()
    try:
        r = subprocess.run(argv, cwd=ORACLE, capture_output=True, timeout=900); out, err, rc = r.stdout, r.stderr, r.returncode
    except subprocess.TimeoutExpired as e:
        out, err, rc = e.stdout or b"", e.stderr or b"", 124
    stem.with_suffix(".stdout").write_bytes(out); stem.with_suffix(".stderr").write_bytes(err)
    rec = {"step": tag, "argv": argv, "cwd": ORACLE, "started_utc": t0,
           "finished_utc": datetime.now(timezone.utc).isoformat(), "exit_code": rc,
           "source_path": str(src), "source_sha256": h(data),
           "stdout_sha256": h(out), "stderr_sha256": h(err)}
    if olean is not None and rc == 0 and olean.exists():
        rec["olean_path"] = str(olean); rec["olean_sha256"] = h(olean.read_bytes())
    stem.with_suffix(".json").write_text(json.dumps(rec, indent=1) + "\n"); print(tag, "exit", rc)
    if rc: print(out.decode()[-8000:], err.decode()[-3000:]); sys.exit(rc)
