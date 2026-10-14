"""Pinned compile harness for G05-B (modelled on CAS-10 g10a raw/run_compile.py).

Every attempt snapshots the exact source to raw/compile_NN_<step>.source.lean and writes
.json (argv, cwd, exit code, source sha256, UTC start/finish, stdout/stderr sha256, olean sha256),
.stdout, .stderr.  Attempts are never deleted.  Timeout 900 s.
Usage: python3 raw/run_compile.py <step> [<step> ...]
"""
import hashlib, json, pathlib, subprocess, sys
from datetime import datetime, timezone

T = pathlib.Path(__file__).resolve().parent.parent
RAW, IMP, LEAN = T / "raw", T / "raw" / "imports", T / "lean"
ORACLE = "/home/cosmosapjw/lean_oracles/viii_oracle"
CAS = T.parent.parent  # .../GRSTAT-CAS-20260930-1308KST
h = lambda b: hashlib.sha256(b).hexdigest()

# reused, reviewed sources (imported UNCHANGED; compiled into raw/imports)
IMPORTS = {
    "c03": CAS / "CAS-05" / "v3_execution_20261003" / "lean" / "CAS05C03.lean",
    "conf": CAS / "CAS-05" / "g05a_neighborhood_strict_dec_v1_20261013" / "lean" / "G05AConformalDEC.lean",
    "cub": CAS / "CAS-05" / "g05a_neighborhood_strict_dec_v1_20261013" / "lean" / "G05BCubicDEC.lean",
    "proof04": CAS / "CAS-04" / "completion_20261003" / "lean" / "Proof.lean",
    "g04a": CAS / "CAS-04" / "g04a_smooth_eigenline_v1_20261013" / "lean" / "G04AEigenline.lean",
}
# this package's modules
OWN = ["G05BJet", "G05BIFT", "G05BSymm", "G05BGerm"]


def step(name):
    if name in IMPORTS:
        src = IMPORTS[name]
        mod = src.stem
        cmd = f"LEAN_PATH={IMP}:$LEAN_PATH lean -R {src.parent} -o {IMP}/{mod}.olean {src}"
        return src, cmd, IMP / f"{mod}.olean"
    if name in OWN:
        src = LEAN / f"{name}.lean"
        cmd = f"LEAN_PATH={IMP}:$LEAN_PATH lean -R {LEAN} -o {IMP}/{name}.olean {src}"
        return src, cmd, IMP / f"{name}.olean"
    if name == "audit":
        src = RAW / "AxiomAudit.lean"
        return src, f"LEAN_PATH={IMP}:$LEAN_PATH lean -R {RAW} {src}", None
    if name.startswith("probe:"):
        src = RAW / "probes" / (name.split(":", 1)[1] + ".lean")
        return src, f"LEAN_PATH={IMP}:$LEAN_PATH lean -R {src.parent} {src}", None
    raise SystemExit(f"unknown step {name}")


for name in sys.argv[1:]:
    src, cmd, olean = step(name)
    n = len(list(RAW.glob("compile_*.json"))) + 1
    tag = name.replace(":", "_")
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
    rec = {"step": name, "argv": argv, "cwd": ORACLE, "started_utc": t0, "finished_utc": t1,
           "exit_code": rc, "source_path": str(src), "source_sha256": h(data),
           "stdout_sha256": h(out), "stderr_sha256": h(err)}
    if olean is not None and rc == 0 and olean.exists():
        rec["olean_path"] = str(olean)
        rec["olean_sha256"] = h(olean.read_bytes())
    (RAW / (stem.name + ".json")).write_text(json.dumps(rec, indent=1) + "\n")
    print(name, "exit", rc, stem.name)
    if rc:
        print(out.decode(errors="replace")[-6000:], err.decode(errors="replace")[-2000:])
        sys.exit(rc)
