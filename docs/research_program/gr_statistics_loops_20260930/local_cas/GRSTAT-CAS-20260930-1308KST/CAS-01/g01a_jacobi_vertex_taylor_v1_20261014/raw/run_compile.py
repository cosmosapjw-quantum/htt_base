"""Pinned compile harness (modelled on CAS-10 g10a raw/run_compile.py):
snapshot exact source, record argv/cwd/exit/hashes/UTC, keep every attempt, timeout 900 s."""
import hashlib, json, pathlib, shutil, subprocess, sys
from datetime import datetime, timezone
T = pathlib.Path(__file__).resolve().parent.parent
RAW, IMP = T / "raw", T / "raw" / "imports"
ORACLE = "/home/cosmosapjw/lean_oracles/viii_oracle"
M05 = T.parent.parent / "CAS-07" / "determinant_distance_bridge_v1_20261007" / "lean" / "Main.lean"
M05_SHA = None  # recorded, not asserted: reviewed hash is taken from the CAS-07 SOURCE_MANIFEST
ORACLE_OLEANS = {
    "CAS07M01Accepted.olean": "83acab45987909a490f90af775cc0f3ce538de3a5e04ed5a04abc311d9c15ca2",
    "CAS07M04Accepted.olean": "81e374aa492d6528188225df432f1036dd460f168f31aa15e544289b46c8182a",
    "CAS07C02Accepted.olean": "67344c6d91e2abfcdc8bae9329f55a3d659438bd61a34cb91d3670e3123bb2c0",
}
h = lambda b: hashlib.sha256(b).hexdigest()
LP = f"LEAN_PATH={IMP}:{ORACLE}:$LEAN_PATH"
MOD = T / "lean" / "G01AJacobiVertex.lean"
STEPS = {
  "import_m05": (IMP / "CAS07M05Accepted.lean", f"{LP} lean -R {IMP} -o {IMP}/CAS07M05Accepted.olean {IMP}/CAS07M05Accepted.lean"),
  "module": (MOD, f"{LP} lean -R {T/'lean'} -o {IMP}/G01AJacobiVertex.olean {MOD}"),
  "audit": (RAW / "AxiomAudit.lean", f"{LP} lean -R {RAW} {RAW/'AxiomAudit.lean'}"),
}
for name in sys.argv[1:]:
    src, cmd = STEPS[name]
    if name == "import_m05":
        IMP.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(M05, src)
        assert h(M05.read_bytes()) == h(src.read_bytes())
    for f, d in ORACLE_OLEANS.items():
        assert h(pathlib.Path(ORACLE, f).read_bytes()) == d, ("ORACLE_OLEAN_MISMATCH", f)
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
           "source_sha256": h(data), "stdout_sha256": h(out), "stderr_sha256": h(err),
           "oracle_oleans_sha256": ORACLE_OLEANS}
    if name == "import_m05":
        rec["copied_from"] = str(M05); rec["copied_from_sha256"] = h(M05.read_bytes())
    stem.with_suffix(".json").write_text(json.dumps(rec, indent=1) + "\n"); print(name, "exit", rc)
    if rc: print(out.decode()[-6000:], err.decode()[-2000:]); sys.exit(rc)
