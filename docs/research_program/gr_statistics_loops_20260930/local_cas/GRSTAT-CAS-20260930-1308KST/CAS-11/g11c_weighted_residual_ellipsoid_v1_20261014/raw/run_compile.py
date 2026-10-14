"""Pinned compile harness (G11-C), modelled on CAS-10/g10a_restspace_positivity_v1_20261013/raw/run_compile.py.

Every attempt snapshots the exact source to raw/compile_NN_<step>.source.lean and writes .json (argv, cwd,
exit code, source sha256, UTC start/finish, stdout/stderr sha256, olean hashes in raw/imports before the run),
.stdout and .stderr.  Attempts are never deleted.  Timeout 900 s.

Reused reviewed sources are compiled UNCHANGED from their original repository paths into raw/imports.
"""
import hashlib, json, pathlib, subprocess, sys
from datetime import datetime, timezone

T = pathlib.Path(__file__).resolve().parent.parent
RAW, IMP, PROBES = T / "raw", T / "raw" / "imports", T / "raw" / "probes"
CAS11 = T.parent
LOCAL = CAS11.parent.parent  # .../local_cas
ORACLE = "/home/cosmosapjw/lean_oracles/viii_oracle"
h = lambda b: hashlib.sha256(b).hexdigest()
LP = f"LEAN_PATH={IMP}:$LEAN_PATH"

REUSED = {
    # module name: source path (imported unchanged)
    "BregmanThreePoint": CAS11 / "c01_bregman_three_point_v2_20261008" / "lean" / "BregmanThreePoint.lean",
    "G11AIntegralBregman": CAS11 / "g11a_integral_bregman_v1_20261013" / "lean" / "G11AIntegralBregman.lean",
    "G11AGuarded": CAS11 / "g11a_integral_bregman_v1_20261013" / "lean" / "G11AGuarded.lean",
    "G11BHessianEnvelope": CAS11 / "g11b_hessian_envelope_energy_v1_20261013" / "lean" / "G11BHessianEnvelope.lean",
    "FiniteGram": LOCAL / "GRSTAT-CAS11-C02-20260930T090559Z" / "lean" / "FiniteGram.lean",
    "WeightedProjection": LOCAL / "GRSTAT-CAS11-C03-20261001T020800Z" / "lean" / "WeightedProjection.lean",
}
MAIN = T / "lean" / "G11CWeightedEllipsoid.lean"

STEPS = {}
for mod, src in REUSED.items():
    STEPS["dep_" + mod] = (src, f"{LP} lean -R {src.parent} -o {IMP}/{mod}.olean {src}")
STEPS["main"] = (MAIN, f"{LP} lean -R {MAIN.parent} -o {IMP}/G11CWeightedEllipsoid.olean {MAIN}")
STEPS["audit"] = (RAW / "AxiomAudit.lean", f"{LP} lean -R {RAW} {RAW / 'AxiomAudit.lean'}")


def probe_step(name):
    src = PROBES / f"{name}.lean"
    return (src, f"{LP} lean -R {PROBES} {src}")


IMP.mkdir(parents=True, exist_ok=True)
for name in sys.argv[1:]:
    src, cmd = STEPS[name] if name in STEPS else probe_step(name)
    n = len(list(RAW.glob("compile_*.json"))) + 1
    stem = RAW / f"compile_{n:02d}_{name}"
    data = src.read_bytes()
    (RAW / (stem.name + ".source.lean")).write_bytes(data)
    imports = {p.name: h(p.read_bytes()) for p in sorted(IMP.glob("*.olean"))}
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
    rec = {"step": name, "argv": argv, "cwd": ORACLE, "started_utc": t0, "finished_utc": t1, "exit_code": rc,
           "timeout_seconds": 900, "source_path": str(src), "source_sha256": h(data),
           "stdout_sha256": h(out), "stderr_sha256": h(err), "imported_olean_sha256_before_run": imports}
    stem.with_suffix(".json").write_text(json.dumps(rec, indent=1) + "\n")
    print(name, "exit", rc)
    if rc:
        print(out.decode()[-12000:], err.decode()[-3000:])
        sys.exit(rc)
