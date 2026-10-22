"""Pinned compile harness (modelled on CAS-10 g10a raw/run_compile.py):
snapshot exact source, record argv/cwd/exit/hashes/UTC, keep every attempt, timeout 900 s.
Imports the accepted CAS-01 C01-C04 Lean source unchanged (byte-identical copy, hash asserted)."""
import hashlib, json, pathlib, shutil, subprocess, sys
from datetime import datetime, timezone
T = pathlib.Path(__file__).resolve().parent.parent
RAW, IMP = T / "raw", T / "raw" / "imports"
ORACLE = "/home/cosmosapjw/lean_oracles/viii_oracle"
C04 = T.parent / "completion" / "rerun_20261003" / "lean" / "Main.lean"
C04_SHA = "a24b349982cb5401d8086b3432caf76b1f277793c056083276eb30bcde72e9b7"  # accepted rerun source
h = lambda b: hashlib.sha256(b).hexdigest()
LP = f"LEAN_PATH={IMP}:$LEAN_PATH"
MOD = T / "lean" / "G01BTimelikeFlow.lean"
STEPS = {
  "import_c04": (IMP / "CAS01C04Accepted.lean", f"{LP} lean -R {IMP} -o {IMP}/CAS01C04Accepted.olean {IMP}/CAS01C04Accepted.lean"),
  "module": (MOD, f"{LP} lean -R {T/'lean'} -o {IMP}/G01BTimelikeFlow.olean {MOD}"),
  "audit": (RAW / "AxiomAudit.lean", f"{LP} lean -R {RAW} {RAW/'AxiomAudit.lean'}"),
}
for name in sys.argv[1:]:
    src, cmd = STEPS[name]
    if name == "import_c04":
        IMP.mkdir(parents=True, exist_ok=True)
        assert h(C04.read_bytes()) == C04_SHA, "C04_SOURCE_HASH_MISMATCH"
        shutil.copyfile(C04, src)
        assert h(src.read_bytes()) == C04_SHA
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
           "source_path": str(src), "source_sha256": h(data), "stdout_sha256": h(out), "stderr_sha256": h(err)}
    if name == "import_c04":
        rec["copied_from"] = str(C04); rec["copied_from_sha256"] = C04_SHA
    olean = {"import_c04": IMP / "CAS01C04Accepted.olean", "module": IMP / "G01BTimelikeFlow.olean"}.get(name)
    if olean is not None and rc == 0 and olean.exists():
        rec["olean_sha256"] = h(olean.read_bytes())
    stem.with_suffix(".json").write_text(json.dumps(rec, indent=1) + "\n"); print(name, "exit", rc)
    for line in out.decode(errors="replace").splitlines() + err.decode(errors="replace").splitlines():
        if "error:" in line: print(line)
    if rc: print(out.decode(errors="replace")[-6000:], err.decode(errors="replace")[-2000:]); sys.exit(rc)
