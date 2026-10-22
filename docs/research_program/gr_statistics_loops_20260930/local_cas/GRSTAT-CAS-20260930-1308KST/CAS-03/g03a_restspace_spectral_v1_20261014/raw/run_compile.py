"""Pinned compile harness (modelled on CAS-10 g10a raw/run_compile.py).

Every attempt snapshots the exact source, records argv/cwd/exit/hashes/UTC time, keeps stdout/stderr,
and is never deleted. Imported accepted sources are compiled UNCHANGED from their original paths.
"""
import hashlib, json, pathlib, subprocess, sys
from datetime import datetime, timezone

T = pathlib.Path(__file__).resolve().parent.parent
RAW, IMP = T / "raw", T / "raw" / "imports"
ORACLE = "/home/cosmosapjw/lean_oracles/viii_oracle"
CAS = T.parent.parent  # .../GRSTAT-CAS-20260930-1308KST
C01 = CAS / "CAS-03" / "c01_input_aligned_v1_20261005" / "lean" / "C01.lean"
PROOF = CAS / "CAS-04" / "completion_20261003" / "lean" / "Proof.lean"
G04A = CAS / "CAS-04" / "g04a_smooth_eigenline_v1_20261013" / "lean" / "G04AEigenline.lean"
MAIN = T / "lean" / "G03ARestspace.lean"
SIG = RAW / "probes" / "Sig.lean"
AUDIT = RAW / "AxiomAudit.lean"
LP = f"LEAN_PATH={IMP}:$LEAN_PATH"
h = lambda b: hashlib.sha256(b).hexdigest()
STEPS = {
    "c01": (C01, f"lean -R {C01.parent} -o {IMP}/C01.olean {C01}", IMP / "C01.olean"),
    "proof": (PROOF, f"lean -R {PROOF.parent} -o {IMP}/Proof.olean {PROOF}", IMP / "Proof.olean"),
    "g04a": (G04A, f"{LP} lean -R {G04A.parent} -o {IMP}/G04AEigenline.olean {G04A}", IMP / "G04AEigenline.olean"),
    "sig": (SIG, f"{LP} lean -R {SIG.parent} {SIG}", None),
    "main": (MAIN, f"{LP} lean -R {MAIN.parent} -o {IMP}/G03ARestspace.olean {MAIN}", IMP / "G03ARestspace.olean"),
    "audit": (AUDIT, f"{LP} lean -R {RAW} {AUDIT}", None),
}
for name in sys.argv[1:]:
    src, cmd, olean = STEPS[name]
    n = len(list(RAW.glob("compile_*.json"))) + 1
    stem = RAW / f"compile_{n:02d}_{name}"
    data = src.read_bytes()
    (stem.parent / (stem.name + ".source.lean")).write_bytes(data)
    argv = ["lake", "env", "bash", "-c", cmd]
    t0 = datetime.now(timezone.utc).isoformat()
    try:
        r = subprocess.run(argv, cwd=ORACLE, capture_output=True, timeout=900)
        out, err, rc = r.stdout, r.stderr, r.returncode
    except subprocess.TimeoutExpired as e:
        out, err, rc = e.stdout or b"", e.stderr or b"", 124
    stem.with_suffix(".stdout").write_bytes(out)
    stem.with_suffix(".stderr").write_bytes(err)
    rec = {"step": name, "argv": argv, "cwd": ORACLE, "started_utc": t0,
           "finished_utc": datetime.now(timezone.utc).isoformat(), "exit_code": rc,
           "source_path": str(src), "source_sha256": h(data),
           "stdout_sha256": h(out), "stderr_sha256": h(err)}
    if olean is not None and rc == 0 and olean.exists():
        rec["olean_sha256"] = h(olean.read_bytes())
    stem.with_suffix(".json").write_text(json.dumps(rec, indent=1) + "\n")
    print(name, "exit", rc)
    if rc:
        print(out.decode()[-6000:], err.decode()[-3000:])
        sys.exit(rc)
