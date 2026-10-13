"""Pinned compile harness (modelled on CAS-10/g10a_restspace_positivity_v1_20261013/raw/run_compile.py).

Every attempt snapshots the exact source, records argv/cwd/exit/UTC time/source+stdout+stderr
sha256, and keeps .stdout/.stderr. Attempts are never deleted; numbering is monotone.
Usage: python3 run_compile.py <step> [<step> ...]   steps: planck interface envelope closure audit probe:<file>
"""
import hashlib, json, pathlib, subprocess, sys
from datetime import datetime, timezone

T = pathlib.Path(__file__).resolve().parent.parent
RAW, IMP, LEAN, PROBES = T / "raw", T / "raw" / "imports", T / "lean", T / "raw" / "probes"
ORACLE = "/home/cosmosapjw/lean_oracles/viii_oracle"
h = lambda b: hashlib.sha256(b).hexdigest()


def module_step(mod):
    src = LEAN / f"{mod}.lean"
    return src, f"LEAN_PATH={IMP}:$LEAN_PATH lean -R {LEAN} -o {IMP}/{mod}.olean {src}", IMP / f"{mod}.olean"


STEPS = {
    "planck": module_step("PlanckIR"),
    "interface": module_step("G12DInterface"),
    "envelope": module_step("G12DUVIntegrabilityEnvelope"),
    "closure": module_step("G12DCardClosure"),
    "audit": (RAW / "AxiomAudit.lean", f"LEAN_PATH={IMP}:$LEAN_PATH lean -R {RAW} {RAW / 'AxiomAudit.lean'}", None),
}

for name in sys.argv[1:]:
    if name.startswith("probe:"):
        p = PROBES / name.split(":", 1)[1]
        src, cmd, olean = p, f"LEAN_PATH={IMP}:$LEAN_PATH lean -R {PROBES} {p}", None
        tag = "probe_" + p.stem
    else:
        src, cmd, olean = STEPS[name]
        tag = name
    n = len(list(RAW.glob("compile_*.json"))) + 1
    stem = RAW / f"compile_{n:02d}_{tag}"
    data = src.read_bytes()
    (RAW / (stem.name + ".source.lean")).write_bytes(data)
    argv = ["lake", "env", "bash", "-c", cmd]
    t0 = datetime.now(timezone.utc).isoformat()
    try:
        r = subprocess.run(argv, cwd=ORACLE, capture_output=True, timeout=900)
        out, err, rc = r.stdout, r.stderr, r.returncode
    except subprocess.TimeoutExpired as e:
        out, err, rc = e.stdout or b"", e.stderr or b"", 124
    t1 = datetime.now(timezone.utc).isoformat()
    (RAW / (stem.name + ".stdout")).write_bytes(out)
    (RAW / (stem.name + ".stderr")).write_bytes(err)
    rec = {"attempt": n, "step": name, "argv": argv, "cwd": ORACLE, "started_utc": t0, "finished_utc": t1,
           "exit_code": rc, "source_path": str(src), "source_sha256": h(data),
           "source_snapshot": stem.name + ".source.lean",
           "stdout_path": stem.name + ".stdout", "stderr_path": stem.name + ".stderr",
           "stdout_sha256": h(out), "stderr_sha256": h(err),
           "olean_path": str(olean) if olean else None,
           "olean_sha256": h(olean.read_bytes()) if (olean and rc == 0 and olean.exists()) else None}
    (RAW / (stem.name + ".json")).write_text(json.dumps(rec, indent=1) + "\n")
    print(name, "attempt", n, "exit", rc)
    if rc:
        print(out.decode(errors="replace")[-6000:], err.decode(errors="replace")[-3000:])
        sys.exit(rc)
