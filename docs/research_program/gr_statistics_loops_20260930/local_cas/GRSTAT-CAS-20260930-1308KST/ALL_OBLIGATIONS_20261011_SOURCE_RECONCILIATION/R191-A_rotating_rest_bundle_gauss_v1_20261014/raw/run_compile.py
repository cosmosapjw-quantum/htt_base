"""Pinned compile harness: snapshot exact source, record argv/cwd/exit/hashes, keep every attempt.

Modelled on GRSTAT CAS-10 g10a_restspace_positivity_v1_20261013/raw/run_compile.py.
Imported reviewed sources (P03-A and its imports) are compiled unchanged from their original paths.
"""
import hashlib, json, pathlib, subprocess, sys
from datetime import datetime, timezone
T = pathlib.Path(__file__).resolve().parent.parent
RAW, IMP = T / "raw", T / "raw" / "imports"
ORACLE = "/home/cosmosapjw/lean_oracles/viii_oracle"
PORT = pathlib.Path("/home/cosmosapjw/Dropbox/bianchi/htt_base/docs/research_program/theory_inference_port_20260930/local_execution")
REST = PORT / "PORT-CAS-03" / "velocity_jet_rest_bridge_v1_20261011" / "VelocityJetRest.lean"
PORT01 = PORT / "PORT-CAS-01" / "lorentz_mass_shell_v1_20261008" / "lean" / "PortCas01.lean"
P03A = PORT / "PORT-CAS-03" / "velocity_jet_decomposition_v1_20261014" / "lean" / "VelocityJetDecomposition.lean"
MAIN = T / "lean" / "RotatingRestBundleGauss.lean"
PROBE = RAW / "probes" / "Probe.lean"
h = lambda b: hashlib.sha256(b).hexdigest()
STEPS = {
  "rest": (REST, f"lean -R {REST.parent} -o {IMP}/VelocityJetRest.olean {REST}"),
  "port01": (PORT01, f"lean -R {PORT01.parent} -o {IMP}/PortCas01.olean {PORT01}"),
  "p03a": (P03A, f"LEAN_PATH={IMP}:$LEAN_PATH lean -R {P03A.parent} -o {IMP}/VelocityJetDecomposition.olean {P03A}"),
  "main": (MAIN, f"LEAN_PATH={IMP}:$LEAN_PATH lean -R {MAIN.parent} -o {IMP}/RotatingRestBundleGauss.olean {MAIN}"),
  "probe": (PROBE, f"LEAN_PATH={IMP}:$LEAN_PATH lean -R {PROBE.parent} {PROBE}"),
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
    rec = {"step": name, "argv": argv, "cwd": ORACLE, "started_utc": t0, "exit_code": rc, "source_path": str(src),
           "source_sha256": h(data), "stdout_sha256": h(out), "stderr_sha256": h(err)}
    stem.with_suffix(".json").write_text(json.dumps(rec, indent=1) + "\n"); print(name, "exit", rc)
    for line in (out + err).decode(errors="replace").splitlines():
        if "error:" in line:
            print(line)
    if rc: print(out.decode(errors="replace")[-8000:], err.decode(errors="replace")[-2000:]); sys.exit(rc)
