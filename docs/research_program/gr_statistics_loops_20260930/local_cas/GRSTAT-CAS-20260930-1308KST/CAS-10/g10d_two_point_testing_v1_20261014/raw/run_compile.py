"""Pinned compile harness for G10-D (modelled on g10a/g10b raw/run_compile.py).

Every attempt snapshots the exact source to raw/compile_NN_<step>.source.lean and writes
.json (argv, cwd, exit code, source sha256, UTC time, stdout/stderr sha256), .stdout, .stderr.
Attempts are never deleted. Timeout 900 s.
Usage: python3 run_compile.py <step> [<step> ...]
  steps: c01 c03 p12 g10b g10c main audit probe:<file in raw/probes>
"""
import hashlib, json, pathlib, subprocess, sys
from datetime import datetime, timezone

T = pathlib.Path(__file__).resolve().parent.parent
RAW, IMP, LEAN = T / "raw", T / "raw" / "imports", T / "lean"
ORACLE = "/home/cosmosapjw/lean_oracles/viii_oracle"
REUSED = LEAN / "reused"
h = lambda b: hashlib.sha256(b).hexdigest()


def lp(cmd):
    return f"LEAN_PATH={IMP}:$LEAN_PATH {cmd}"


def reused(mod):
    return (REUSED / f"{mod}.lean", lp(f"lean -R {REUSED} -o {IMP}/{mod}.olean {REUSED / (mod + '.lean')}"))


STEPS = {
    "c01": reused("CAS10C01"),
    "c03": reused("CAS10C03"),
    "p12": reused("P12GaussianLaw"),
    "g10b": reused("G10BGaussianKL"),
    "g10c": reused("G10CSmoothCutoff"),
    "main": (LEAN / "G10DTwoPoint.lean",
             lp(f"lean -R {LEAN} -o {IMP}/G10DTwoPoint.olean {LEAN / 'G10DTwoPoint.lean'}")),
    "audit": (RAW / "AxiomAudit.lean", lp(f"lean -R {RAW} {RAW / 'AxiomAudit.lean'}")),
}

for name in sys.argv[1:]:
    if name.startswith("probe:"):
        src = (RAW / "probes" / name.split(":", 1)[1]).resolve()
        cmd = lp(f"lean -R {src.parent} {src}")
        label = "probe_" + src.stem
    else:
        src, cmd = STEPS[name]
        label = name
    n = len(list(RAW.glob("compile_*.json"))) + 1
    stem = RAW / f"compile_{n:02d}_{label}"
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
    stem.with_suffix(".stdout").write_bytes(out)
    stem.with_suffix(".stderr").write_bytes(err)
    rec = {"step": label, "argv": argv, "cwd": ORACLE, "started_utc": t0, "finished_utc": t1,
           "exit_code": rc, "source_path": str(src), "source_sha256": h(data),
           "stdout_sha256": h(out), "stderr_sha256": h(err)}
    stem.with_suffix(".json").write_text(json.dumps(rec, indent=1) + "\n")
    print(label, "exit", rc)
    if rc:
        print(out.decode()[-8000:], err.decode()[-2000:])
        sys.exit(rc)
